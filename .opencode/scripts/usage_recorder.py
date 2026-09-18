#!/usr/bin/env python3
"""Local AI-factory usage recorder, normalizer, aggregator, and reporter.

Implements the "Usage reporting contract" and "Usage checkpoint schema" in
`.opencode/rules/workflow.md`. Standard library only. Reads and writes only
`.opencode/` markdown checkpoints on disk: no network, provider, Jenkins,
Bitbucket, JIRA, PACT, database, or git calls.

Usage:
  python3 .opencode/scripts/usage_recorder.py report --plan <plan.md>
  python3 .opencode/scripts/usage_recorder.py record --plan <plan.md> \
      --input <record.json>   # or '-' for stdin

Exit code 0 = success, 1 = usage/IO error, 2 = idempotency conflict.
"""

from __future__ import annotations

import argparse
import json
import math
import os
import re
import sys
import tempfile
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

SCHEMA_VERSION = 1

STAGES = ("feature-planner", "implementer", "validator", "release-manager")
TELEMETRY_STATUSES = ("exact", "partial", "unavailable", "conflict")
SOURCES = ("runtime", "manual", "derived")
PRICING_SOURCES = ("table", "provider", "unavailable")
REASONS = (
    "runtime_did_not_expose_usage",
    "provider_omitted_usage",
    "malformed_usage_payload",
    "pricing_unavailable",
    "recording_failed",
)

RECORD_FIELDS = (
    "invocation_id",
    "stage",
    "session_id",
    "iteration",
    "started_at",
    "completed_at",
    "input_tokens",
    "output_tokens",
    "total_tokens",
    "estimated_usd",
    "currency",
    "telemetry_status",
    "unavailable_reason",
    "provider",
    "model",
    "pricing_version",
    "pricing_effective_at",
    "input_usd_per_million",
    "output_usd_per_million",
    "pricing_source",
    "source",
    "recorded_at",
)

TOKEN_KEY_ALIASES = {
    "input_tokens": ("input_tokens", "prompt_tokens", "input", "in_tokens"),
    "output_tokens": ("output_tokens", "completion_tokens", "output", "out_tokens"),
    "total_tokens": ("total_tokens", "total", "tokens"),
}

BLOCK_START = "```yaml"
BLOCK_END = "```"
BLOCK_KEY = "usage_reporting:"

MILLION = 1_000_000


class UsageError(Exception):
    """Raised for invalid recorder input or unusable checkpoint content."""


class ConflictError(UsageError):
    """Raised when an invocation key repeats with a different payload."""


# --------------------------------------------------------------------------
# Normalization
# --------------------------------------------------------------------------


def _utc_now() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _clean_str(value: Any) -> str | None:
    if value is None:
        return None
    text = str(value).strip()
    return text or None


def _coerce_int(value: Any) -> tuple[int | None, bool]:
    """Return (value, malformed). Unknown is None and is never zero."""
    if value is None:
        return None, False
    if isinstance(value, bool):
        return None, True
    if isinstance(value, float):
        if not math.isfinite(value) or value < 0 or value != int(value):
            return None, True
        return int(value), False
    if isinstance(value, int):
        return (value, False) if value >= 0 else (None, True)
    if isinstance(value, str):
        text = value.strip()
        if not text or text.lower() in {"null", "none", "unknown"}:
            return None, False
        try:
            return _coerce_int(int(text))
        except ValueError:
            return None, True
    return None, True


def _coerce_rate(value: Any) -> tuple[float | None, bool]:
    if value is None:
        return None, False
    if isinstance(value, bool):
        return None, True
    if isinstance(value, (int, float)):
        number = float(value)
        if not math.isfinite(number) or number < 0:
            return None, True
        return number, False
    if isinstance(value, str):
        text = value.strip()
        if not text or text.lower() in {"null", "none", "unknown"}:
            return None, False
        try:
            return _coerce_rate(float(text))
        except ValueError:
            return None, True
    return None, True


def _first_present(raw: dict[str, Any], keys: tuple[str, ...]) -> Any:
    for key in keys:
        if key in raw:
            return raw[key]
    return None


def normalize_invocation(
    raw_usage: dict[str, Any] | None,
    identity: dict[str, Any],
    pricing_snapshot: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Build one allow-listed usage record.

    Only identity, numeric usage, and pricing metadata survive; any other raw
    provider key is dropped so prompts, responses, and secrets never persist.
    """
    invocation_id = _clean_str(identity.get("invocation_id"))
    stage = _clean_str(identity.get("stage"))
    session_id = _clean_str(identity.get("session_id"))
    if not invocation_id or not session_id:
        raise UsageError("identity requires invocation_id and session_id")
    if stage not in STAGES:
        raise UsageError(f"stage must be one of {STAGES}, got {stage!r}")

    iteration, bad_iteration = _coerce_int(identity.get("iteration"))
    if iteration is None or bad_iteration:
        raise UsageError("identity requires a non-negative integer iteration")

    source = _clean_str(identity.get("source")) or "runtime"
    if source not in SOURCES:
        raise UsageError(f"source must be one of {SOURCES}, got {source!r}")

    raw = raw_usage or {}
    if not isinstance(raw, dict):
        raise UsageError("raw_usage must be a mapping or None")

    malformed = False
    tokens: dict[str, int | None] = {}
    for field, aliases in TOKEN_KEY_ALIASES.items():
        value, bad = _coerce_int(_first_present(raw, aliases))
        malformed = malformed or bad
        tokens[field] = value

    if (
        tokens["total_tokens"] is None
        and not malformed
        and tokens["input_tokens"] is not None
        and tokens["output_tokens"] is not None
    ):
        tokens["total_tokens"] = tokens["input_tokens"] + tokens["output_tokens"]

    pricing = pricing_snapshot or {}
    if not isinstance(pricing, dict):
        raise UsageError("pricing_snapshot must be a mapping or None")

    input_rate, bad_in_rate = _coerce_rate(pricing.get("input_usd_per_million"))
    output_rate, bad_out_rate = _coerce_rate(pricing.get("output_usd_per_million"))
    pricing_malformed = bad_in_rate or bad_out_rate
    pricing_source = _clean_str(pricing.get("pricing_source"))
    if pricing_source not in PRICING_SOURCES:
        pricing_source = None
    pricing_version = _clean_str(pricing.get("pricing_version"))
    pricing_effective_at = _clean_str(pricing.get("pricing_effective_at"))
    currency = _clean_str(pricing.get("currency"))

    if pricing_malformed:
        input_rate = None
        output_rate = None
        pricing_source = "unavailable"

    record: dict[str, Any] = {
        "invocation_id": invocation_id,
        "stage": stage,
        "session_id": session_id,
        "iteration": iteration,
        "started_at": _clean_str(identity.get("started_at")),
        "completed_at": _clean_str(identity.get("completed_at")),
        "input_tokens": tokens["input_tokens"],
        "output_tokens": tokens["output_tokens"],
        "total_tokens": tokens["total_tokens"],
        "estimated_usd": None,
        "currency": None,
        "telemetry_status": "unavailable",
        "unavailable_reason": None,
        "provider": _clean_str(identity.get("provider")),
        "model": _clean_str(identity.get("model")),
        "pricing_version": pricing_version,
        "pricing_effective_at": pricing_effective_at,
        "input_usd_per_million": input_rate,
        "output_usd_per_million": output_rate,
        "pricing_source": pricing_source or "unavailable",
        "source": source,
        "recorded_at": _clean_str(identity.get("recorded_at")) or _utc_now(),
    }

    known_dimensions = [
        name
        for name in ("input_tokens", "output_tokens")
        if record[name] is not None
    ]
    if malformed:
        record["input_tokens"] = None
        record["output_tokens"] = None
        record["total_tokens"] = None
        record["telemetry_status"] = "unavailable"
        record["unavailable_reason"] = "malformed_usage_payload"
        return record

    if len(known_dimensions) == 2:
        record["telemetry_status"] = "exact"
    elif known_dimensions or record["total_tokens"] is not None:
        record["telemetry_status"] = "partial"
    else:
        record["telemetry_status"] = "unavailable"
        record["unavailable_reason"] = (
            _clean_str(identity.get("unavailable_reason"))
            or "runtime_did_not_expose_usage"
        )
        if record["unavailable_reason"] not in REASONS:
            record["unavailable_reason"] = "runtime_did_not_expose_usage"
        return record

    cost = _estimate_cost(record)
    if cost is None:
        record["estimated_usd"] = None
        record["currency"] = None
    else:
        record["estimated_usd"] = cost
        record["currency"] = currency or "USD"
    return record


def _estimate_cost(record: dict[str, Any]) -> float | None:
    """Cost only when every needed token dimension and rate is known."""
    if record["pricing_source"] == "unavailable":
        return None
    pairs = (
        ("input_tokens", "input_usd_per_million"),
        ("output_tokens", "output_usd_per_million"),
    )
    total = 0.0
    priced_any = False
    for token_field, rate_field in pairs:
        tokens = record[token_field]
        rate = record[rate_field]
        if tokens is None and rate is None:
            continue
        if tokens is None or rate is None:
            return None
        total += tokens * rate / MILLION
        priced_any = True
    if not priced_any:
        return None
    return round(total, 6)


# --------------------------------------------------------------------------
# Aggregation and merge
# --------------------------------------------------------------------------


def empty_checkpoint() -> dict[str, Any]:
    checkpoint = {"schema_version": SCHEMA_VERSION, "records": []}
    return recompute_totals(checkpoint)


def _blank_totals() -> dict[str, Any]:
    return {
        "records": 0,
        "known_tokens": 0,
        "known_estimated_usd": 0,
        "unknown_token_records": 0,
        "unknown_cost_records": 0,
    }


def _accumulate(bucket: dict[str, Any], record: dict[str, Any]) -> None:
    bucket["records"] += 1
    # Conflict records are never summed: they duplicate an existing invocation
    # key with a differing payload, so their numbers are treated as unknown.
    conflicted = record.get("telemetry_status") == "conflict"
    total = None if conflicted else record.get("total_tokens")
    if isinstance(total, int) and not isinstance(total, bool):
        bucket["known_tokens"] += total
    else:
        bucket["unknown_token_records"] += 1
    cost = None if conflicted else record.get("estimated_usd")
    if isinstance(cost, (int, float)) and not isinstance(cost, bool):
        bucket["known_estimated_usd"] = round(bucket["known_estimated_usd"] + cost, 6)
    else:
        bucket["unknown_cost_records"] += 1


def recompute_totals(checkpoint: dict[str, Any]) -> dict[str, Any]:
    """Recompute all totals from records. Unknown values are never zero-filled."""
    records: list[dict[str, Any]] = list(checkpoint.get("records") or [])
    by_stage: dict[str, Any] = {}
    by_iteration: dict[Any, Any] = {}
    feature_total = _blank_totals()

    for record in records:
        stage = record.get("stage") or "unknown"
        iteration = record.get("iteration")
        _accumulate(by_stage.setdefault(stage, _blank_totals()), record)
        _accumulate(by_iteration.setdefault(iteration, _blank_totals()), record)
        _accumulate(feature_total, record)

    statuses = {r.get("telemetry_status") for r in records}
    if records and statuses == {"exact"}:
        report_status = "exact"
    elif feature_total["records"] and (
        feature_total["unknown_token_records"] < feature_total["records"]
        or feature_total["unknown_cost_records"] < feature_total["records"]
    ):
        report_status = "partial"
    else:
        report_status = "unavailable"

    checkpoint["schema_version"] = checkpoint.get("schema_version") or SCHEMA_VERSION
    checkpoint["records"] = records
    checkpoint["totals_by_stage"] = by_stage
    checkpoint["totals_by_iteration"] = by_iteration
    checkpoint["feature_total"] = feature_total
    checkpoint["known_token_count"] = feature_total["known_tokens"]
    checkpoint["unknown_token_records"] = feature_total["unknown_token_records"]
    checkpoint["known_estimated_usd"] = feature_total["known_estimated_usd"]
    checkpoint["unknown_cost_records"] = feature_total["unknown_cost_records"]
    checkpoint["last_recorded_invocation_id"] = (
        records[-1].get("invocation_id") if records else None
    )
    checkpoint["report_status"] = report_status
    return checkpoint


def _key(record: dict[str, Any]) -> tuple[Any, Any, Any]:
    return (
        record.get("session_id"),
        record.get("iteration"),
        record.get("invocation_id"),
    )


def _comparable(record: dict[str, Any]) -> dict[str, Any]:
    return {k: record.get(k) for k in RECORD_FIELDS if k != "recorded_at"}


def merge_checkpoint(
    checkpoint: dict[str, Any],
    record: dict[str, Any],
    *,
    strict: bool = False,
) -> tuple[dict[str, Any], str]:
    """Append-only, idempotent merge keyed by session_id+iteration+invocation_id.

    Returns (checkpoint, outcome) where outcome is `appended`, `duplicate`, or
    `conflict`. A conflict preserves the original record and never rewrites it.
    """
    checkpoint = dict(checkpoint or {})
    records = list(checkpoint.get("records") or [])
    for existing in records:
        if _key(existing) != _key(record):
            continue
        if _comparable(existing) == _comparable(record):
            checkpoint["records"] = records
            return recompute_totals(checkpoint), "duplicate"
        if strict:
            raise ConflictError(
                f"conflicting payload for invocation_id {record.get('invocation_id')}"
            )
        conflict = dict(record)
        conflict["invocation_id"] = f"{record['invocation_id']}-conflict"
        conflict["telemetry_status"] = "conflict"
        conflict["unavailable_reason"] = "malformed_usage_payload"
        conflict["estimated_usd"] = None
        conflict["currency"] = None
        records.append(conflict)
        checkpoint["records"] = records
        return recompute_totals(checkpoint), "conflict"

    records.append({field: record.get(field) for field in RECORD_FIELDS})
    checkpoint["records"] = records
    return recompute_totals(checkpoint), "appended"


# --------------------------------------------------------------------------
# Rendering
# --------------------------------------------------------------------------


def _fmt(value: Any) -> str:
    if value is None:
        return "unknown"
    return str(value)


def render_usage_report(checkpoint: dict[str, Any]) -> str:
    """Compact operator report. Unknown is reported as unknown, never as zero."""
    checkpoint = recompute_totals(dict(checkpoint or {}))
    total = checkpoint["feature_total"]
    known_tokens = (
        checkpoint["known_token_count"]
        if total["unknown_token_records"] < total["records"] or total["records"] == 0
        else "unknown"
    )
    known_usd = (
        checkpoint["known_estimated_usd"]
        if total["unknown_cost_records"] < total["records"] or total["records"] == 0
        else "unknown"
    )
    lines = [
        "USAGE REPORT (estimate; not billing data)",
        f"report_status: {checkpoint['report_status']}",
        f"records: {total['records']}",
        f"known_tokens: {known_tokens}",
        f"estimated_usd: {known_usd}",
        f"unavailable_records: {total['unknown_token_records']}",
        f"last_recorded_invocation_id: {_fmt(checkpoint['last_recorded_invocation_id'])}",
        "by_stage:",
    ]
    for stage in sorted(checkpoint["totals_by_stage"], key=str):
        bucket = checkpoint["totals_by_stage"][stage]
        lines.append(
            f"  {stage}: records={bucket['records']} "
            f"known_tokens={bucket['known_tokens']} "
            f"known_estimated_usd={bucket['known_estimated_usd']} "
            f"unknown_token_records={bucket['unknown_token_records']} "
            f"unknown_cost_records={bucket['unknown_cost_records']}"
        )
    lines.append("by_iteration:")
    for iteration in sorted(checkpoint["totals_by_iteration"], key=str):
        bucket = checkpoint["totals_by_iteration"][iteration]
        lines.append(
            f"  {iteration}: records={bucket['records']} "
            f"known_tokens={bucket['known_tokens']} "
            f"known_estimated_usd={bucket['known_estimated_usd']} "
            f"unknown_token_records={bucket['unknown_token_records']} "
            f"unknown_cost_records={bucket['unknown_cost_records']}"
        )
    lines.append(f"last_updated: {_utc_now()}")
    return "\n".join(lines)


# --------------------------------------------------------------------------
# Checkpoint block serialization (restricted YAML subset)
# --------------------------------------------------------------------------


def _scalar(value: Any) -> str:
    if value is None:
        return "null"
    if isinstance(value, bool):
        return "true" if value else "false"
    if isinstance(value, (int, float)):
        return str(value)
    text = str(value)
    if re.fullmatch(r"[A-Za-z0-9_./:+@\-]+", text):
        return text
    return json.dumps(text)


def _parse_scalar(text: str) -> Any:
    text = text.strip()
    if text in {"null", "~", ""}:
        return None
    if text in {"true", "false"}:
        return text == "true"
    if text.startswith('"'):
        return json.loads(text)
    try:
        return int(text)
    except ValueError:
        pass
    try:
        return float(text)
    except ValueError:
        return text


def dump_usage_block(checkpoint: dict[str, Any]) -> str:
    """Serialize the checkpoint to the plan §8 fenced YAML block."""
    checkpoint = recompute_totals(dict(checkpoint or {}))
    lines = [BLOCK_START, BLOCK_KEY, f"  schema_version: {checkpoint['schema_version']}"]
    if checkpoint["records"]:
        lines.append("  records:")
        for record in checkpoint["records"]:
            first = True
            for field in RECORD_FIELDS:
                prefix = "    - " if first else "      "
                lines.append(f"{prefix}{field}: {_scalar(record.get(field))}")
                first = False
    else:
        lines.append("  records: []")

    def totals_section(name: str, buckets: dict[Any, Any]) -> None:
        if not buckets:
            lines.append(f"  {name}: {{}}")
            return
        lines.append(f"  {name}:")
        for key in sorted(buckets, key=str):
            bucket = buckets[key]
            lines.append(
                f"    {_scalar(key)}: {{records: {bucket['records']}, "
                f"known_tokens: {bucket['known_tokens']}, "
                f"known_estimated_usd: {bucket['known_estimated_usd']}, "
                f"unknown_token_records: {bucket['unknown_token_records']}, "
                f"unknown_cost_records: {bucket['unknown_cost_records']}}}"
            )

    totals_section("totals_by_stage", checkpoint["totals_by_stage"])
    totals_section("totals_by_iteration", checkpoint["totals_by_iteration"])
    total = checkpoint["feature_total"]
    lines.append("  feature_total:")
    for field in (
        "records",
        "known_tokens",
        "known_estimated_usd",
        "unknown_token_records",
        "unknown_cost_records",
    ):
        lines.append(f"    {field}: {total[field]}")
    lines.append(f"  known_token_count: {checkpoint['known_token_count']}")
    lines.append(f"  unknown_token_records: {checkpoint['unknown_token_records']}")
    lines.append(f"  known_estimated_usd: {checkpoint['known_estimated_usd']}")
    lines.append(f"  unknown_cost_records: {checkpoint['unknown_cost_records']}")
    lines.append(
        f"  last_recorded_invocation_id: "
        f"{_scalar(checkpoint['last_recorded_invocation_id'])}"
    )
    lines.append(f"  report_status: {checkpoint['report_status']}")
    lines.append(BLOCK_END)
    return "\n".join(lines)


def parse_usage_block(text: str) -> dict[str, Any]:
    """Parse the records out of a plan §8 usage block; totals are recomputed."""
    records: list[dict[str, Any]] = []
    current: dict[str, Any] | None = None
    inside = False
    for line in text.splitlines():
        stripped = line.strip()
        if stripped == "records:" or stripped == "records: []":
            inside = stripped == "records:"
            continue
        if inside and re.match(r"^\s*(totals_by_stage|feature_total)\b", line):
            break
        if not inside:
            continue
        if stripped.startswith("- "):
            current = {}
            records.append(current)
            stripped = stripped[2:]
        if current is None or ":" not in stripped:
            continue
        key, _, value = stripped.partition(":")
        key = key.strip()
        if key in RECORD_FIELDS:
            current[key] = _parse_scalar(value)
    checkpoint = {"schema_version": SCHEMA_VERSION, "records": records}
    return recompute_totals(checkpoint)


def read_checkpoint(plan_path: Path) -> dict[str, Any]:
    text = plan_path.read_text(encoding="utf-8")
    if BLOCK_KEY not in text:
        return empty_checkpoint()
    return parse_usage_block(text)


def write_checkpoint(plan_path: Path, checkpoint: dict[str, Any]) -> None:
    """Replace the usage block atomically; a failed write never truncates."""
    text = plan_path.read_text(encoding="utf-8")
    block = dump_usage_block(checkpoint)
    pattern = re.compile(
        r"```yaml\s*\n\s*usage_reporting:.*?\n```",
        re.DOTALL,
    )
    if pattern.search(text):
        new_text = pattern.sub(lambda _m: block, text, count=1)
    else:
        new_text = text.rstrip("\n") + "\n\n" + block + "\n"

    directory = plan_path.parent
    fd, tmp_name = tempfile.mkstemp(dir=directory, suffix=".tmp")
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as stream:
            stream.write(new_text)
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(tmp_name, plan_path)
    except BaseException:
        try:
            os.unlink(tmp_name)
        except OSError:
            pass
        raise


# --------------------------------------------------------------------------
# CLI
# --------------------------------------------------------------------------


def _load_input(source: str) -> dict[str, Any]:
    raw = sys.stdin.read() if source == "-" else Path(source).read_text(encoding="utf-8")
    payload = json.loads(raw)
    if not isinstance(payload, dict):
        raise UsageError("input JSON must be an object")
    return payload


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="command", required=True)

    report = sub.add_parser("report", help="render the operator usage report")
    report.add_argument("--plan", required=True)

    record = sub.add_parser("record", help="normalize and append one invocation")
    record.add_argument("--plan", required=True)
    record.add_argument("--input", required=True, help="JSON file path or '-'")
    record.add_argument("--strict", action="store_true", help="fail on conflict")
    record.add_argument("--dry-run", action="store_true")

    args = parser.parse_args(argv)
    plan_path = Path(args.plan)

    try:
        if args.command == "report":
            print(render_usage_report(read_checkpoint(plan_path)))
            return 0

        payload = _load_input(args.input)
        usage_record = normalize_invocation(
            payload.get("raw_usage"),
            payload.get("identity") or {},
            payload.get("pricing_snapshot"),
        )
        checkpoint = read_checkpoint(plan_path)
        checkpoint, outcome = merge_checkpoint(
            checkpoint, usage_record, strict=args.strict
        )
        if not args.dry_run:
            write_checkpoint(plan_path, checkpoint)
        print(json.dumps({"outcome": outcome, "record": usage_record}, indent=2))
        return 0
    except ConflictError as exc:
        print(f"conflict: {exc}", file=sys.stderr)
        return 2
    except (UsageError, OSError, json.JSONDecodeError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
