#!/usr/bin/env python3
"""Fixture-only QA for the AI-factory usage recorder.

Stdlib `unittest`; no network, no provider calls, no application code, and no
prompt/response data. Run with:

    python3 -m unittest discover -s .opencode/scripts -p 'test_usage_recorder.py'
"""

from __future__ import annotations

import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import usage_recorder as ur

SESSION = "qa-session-0001"


def identity(invocation_id: str, stage: str = "implementer", iteration: int = 0, **kw):
    base = {
        "invocation_id": invocation_id,
        "stage": stage,
        "session_id": SESSION,
        "iteration": iteration,
        "provider": "github-copilot",
        "model": "github-copilot/test-model",
        "recorded_at": "2026-01-01T00:00:00Z",
    }
    base.update(kw)
    return base


PRICING = {
    "input_usd_per_million": 2.0,
    "output_usd_per_million": 8.0,
    "currency": "USD",
    "pricing_version": "qa-1",
    "pricing_effective_at": "2026-01-01T00:00:00Z",
    "pricing_source": "table",
}


class TestExactTelemetry(unittest.TestCase):
    """Chunk-4 matrix row 1 (positive baseline) — C2, C5."""

    def test_exact_tokens_and_deterministic_estimate(self):
        rec = ur.normalize_invocation(
            {"input_tokens": 1_000_000, "output_tokens": 500_000},
            identity("inv-exact"),
            PRICING,
        )
        self.assertEqual(rec["telemetry_status"], "exact")
        self.assertEqual(rec["total_tokens"], 1_500_000)
        self.assertEqual(rec["estimated_usd"], 6.0)
        self.assertEqual(rec["currency"], "USD")
        self.assertEqual(rec["pricing_version"], "qa-1")
        # Deterministic: same input yields the same estimate.
        again = ur.normalize_invocation(
            {"input_tokens": 1_000_000, "output_tokens": 500_000},
            identity("inv-exact"),
            PRICING,
        )
        self.assertEqual(rec["estimated_usd"], again["estimated_usd"])

    def test_allow_list_drops_sensitive_raw_keys(self):
        rec = ur.normalize_invocation(
            {
                "input_tokens": 10,
                "output_tokens": 5,
                "prompt": "secret prompt",
                "response": "secret response",
                "api_key": "xxx",
            },
            identity("inv-allowlist"),
            PRICING,
        )
        self.assertEqual(set(rec) - set(ur.RECORD_FIELDS), set())
        self.assertNotIn("prompt", rec)
        self.assertNotIn("api_key", rec)


class TestPartialAndUnavailable(unittest.TestCase):
    """Partial / absent telemetry — C2, C4."""

    def test_partial_tokens_yield_no_estimate(self):
        rec = ur.normalize_invocation(
            {"input_tokens": 1000}, identity("inv-partial"), PRICING
        )
        self.assertEqual(rec["telemetry_status"], "partial")
        self.assertEqual(rec["input_tokens"], 1000)
        self.assertIsNone(rec["output_tokens"])
        self.assertIsNone(rec["total_tokens"])
        self.assertIsNone(rec["estimated_usd"])

    def test_absent_usage_keeps_identity_and_marks_unavailable(self):
        rec = ur.normalize_invocation(None, identity("inv-absent"), None)
        self.assertEqual(rec["telemetry_status"], "unavailable")
        self.assertEqual(rec["unavailable_reason"], "runtime_did_not_expose_usage")
        self.assertIsNone(rec["input_tokens"])
        self.assertIsNone(rec["estimated_usd"])
        self.assertEqual(rec["model"], "github-copilot/test-model")
        self.assertEqual(rec["pricing_source"], "unavailable")

    def test_missing_rates_do_not_fabricate_cost(self):
        rec = ur.normalize_invocation(
            {"input_tokens": 100, "output_tokens": 100},
            identity("inv-norates"),
            {"pricing_source": "unavailable"},
        )
        self.assertEqual(rec["telemetry_status"], "exact")
        self.assertIsNone(rec["estimated_usd"])
        self.assertIsNone(rec["currency"])


class TestMalformedAndInvalid(unittest.TestCase):
    """Chunk-4 matrix row 1 — C5, C7."""

    def test_negative_tokens_are_rejected_as_malformed(self):
        rec = ur.normalize_invocation(
            {"input_tokens": -5, "output_tokens": 10}, identity("inv-neg"), PRICING
        )
        self.assertEqual(rec["telemetry_status"], "unavailable")
        self.assertEqual(rec["unavailable_reason"], "malformed_usage_payload")
        self.assertIsNone(rec["total_tokens"])
        self.assertIsNone(rec["estimated_usd"])

    def test_non_numeric_tokens_are_rejected_as_malformed(self):
        rec = ur.normalize_invocation(
            {"input_tokens": "lots", "output_tokens": 10}, identity("inv-nan"), PRICING
        )
        self.assertEqual(rec["unavailable_reason"], "malformed_usage_payload")
        self.assertIsNone(rec["estimated_usd"])

    def test_malformed_pricing_disables_estimate_only(self):
        rec = ur.normalize_invocation(
            {"input_tokens": 100, "output_tokens": 100},
            identity("inv-badrate"),
            dict(PRICING, input_usd_per_million=-1),
        )
        self.assertEqual(rec["telemetry_status"], "exact")
        self.assertEqual(rec["total_tokens"], 200)
        self.assertIsNone(rec["estimated_usd"])
        self.assertEqual(rec["pricing_source"], "unavailable")

    def test_missing_identity_raises(self):
        with self.assertRaises(ur.UsageError):
            ur.normalize_invocation(None, {"stage": "implementer", "iteration": 0})
        with self.assertRaises(ur.UsageError):
            ur.normalize_invocation(None, identity("inv-x", stage="not-a-stage"))
        with self.assertRaises(ur.UsageError):
            ur.normalize_invocation(None, identity("inv-y", iteration=-1))


class TestMergeIdempotency(unittest.TestCase):
    """Chunk-4 matrix row 2 — C3, C7."""

    def setUp(self):
        self.cp = ur.empty_checkpoint()
        self.rec = ur.normalize_invocation(
            {"input_tokens": 10, "output_tokens": 10}, identity("inv-dup"), PRICING
        )

    def test_append_then_duplicate_is_no_op(self):
        cp, outcome = ur.merge_checkpoint(self.cp, self.rec)
        self.assertEqual(outcome, "appended")
        cp, outcome = ur.merge_checkpoint(cp, dict(self.rec))
        self.assertEqual(outcome, "duplicate")
        self.assertEqual(cp["feature_total"]["records"], 1)

    def test_conflicting_duplicate_preserves_original(self):
        cp, _ = ur.merge_checkpoint(self.cp, self.rec)
        changed = ur.normalize_invocation(
            {"input_tokens": 999, "output_tokens": 10}, identity("inv-dup"), PRICING
        )
        cp, outcome = ur.merge_checkpoint(cp, changed)
        self.assertEqual(outcome, "conflict")
        original = cp["records"][0]
        self.assertEqual(original["input_tokens"], 10)
        self.assertEqual(original["telemetry_status"], "exact")
        conflict = cp["records"][1]
        self.assertEqual(conflict["telemetry_status"], "conflict")
        self.assertIsNone(conflict["estimated_usd"])
        # Conflict numbers are never summed into known totals.
        self.assertEqual(cp["known_token_count"], 20)

    def test_strict_mode_raises_on_conflict(self):
        cp, _ = ur.merge_checkpoint(self.cp, self.rec)
        changed = ur.normalize_invocation(
            {"input_tokens": 999, "output_tokens": 10}, identity("inv-dup"), PRICING
        )
        with self.assertRaises(ur.ConflictError):
            ur.merge_checkpoint(cp, changed, strict=True)


class TestAggregationAndCorrectionLoops(unittest.TestCase):
    """Stage/iteration grouping — C4, C6."""

    def build(self):
        cp = ur.empty_checkpoint()
        specs = [
            ("inv-p0", "feature-planner", 0, {"input_tokens": 100, "output_tokens": 50}),
            ("inv-i0", "implementer", 0, {"input_tokens": 200, "output_tokens": 100}),
            ("inv-v0", "validator", 0, None),
            ("inv-i1", "implementer", 1, {"input_tokens": 40, "output_tokens": 10}),
        ]
        for inv, stage, it, raw in specs:
            rec = ur.normalize_invocation(raw, identity(inv, stage, it), PRICING)
            cp, _ = ur.merge_checkpoint(cp, rec)
        return cp

    def test_totals_by_stage_iteration_and_feature(self):
        cp = self.build()
        self.assertEqual(cp["feature_total"]["records"], 4)
        self.assertEqual(cp["totals_by_stage"]["implementer"]["records"], 2)
        self.assertEqual(cp["totals_by_iteration"][0]["records"], 3)
        self.assertEqual(cp["totals_by_iteration"][1]["records"], 1)
        # 150 + 300 + 50 known tokens; the unavailable record adds nothing.
        self.assertEqual(cp["known_token_count"], 500)
        self.assertEqual(cp["unknown_token_records"], 1)
        self.assertEqual(cp["report_status"], "partial")

    def test_correction_iteration_keeps_session_and_does_not_double_count(self):
        cp = self.build()
        sessions = {r["session_id"] for r in cp["records"]}
        self.assertEqual(sessions, {SESSION})
        # Re-recording iteration 0 records after a correction is a no-op.
        before = cp["feature_total"]["records"]
        for rec in list(cp["records"]):
            cp, outcome = ur.merge_checkpoint(cp, dict(rec))
            self.assertEqual(outcome, "duplicate")
        self.assertEqual(cp["feature_total"]["records"], before)

    def test_all_unavailable_reports_unknown_not_zero(self):
        cp = ur.empty_checkpoint()
        for inv in ("a", "b"):
            rec = ur.normalize_invocation(None, identity(f"inv-{inv}"), None)
            cp, _ = ur.merge_checkpoint(cp, rec)
        text = ur.render_usage_report(cp)
        self.assertIn("report_status: unavailable", text)
        self.assertIn("known_tokens: unknown", text)
        self.assertIn("estimated_usd: unknown", text)
        self.assertNotIn("known_tokens: 0", text)

    def test_mixed_report_labels_estimate_and_unknown_counts(self):
        text = ur.render_usage_report(self.build())
        self.assertIn("estimate", text.splitlines()[0].lower())
        self.assertIn("known_tokens: 500", text)
        self.assertIn("unavailable_records: 1", text)
        self.assertIn("by_stage:", text)
        self.assertIn("by_iteration:", text)


class TestCheckpointPersistence(unittest.TestCase):
    """Chunk-4 matrix row 2 — atomic write / round-trip, C3, C7."""

    def _plan(self, tmp: Path, block: str | None) -> Path:
        plan = tmp / "plan.md"
        body = "# Plan\n\n## 8. Checkpoint and traceability\n\n- State: IMPLEMENTING\n"
        if block:
            body += f"\n```yaml\n{block}```\n"
        plan.write_text(body, encoding="utf-8")
        return plan

    def test_block_round_trip(self):
        cp = ur.empty_checkpoint()
        rec = ur.normalize_invocation(
            {"input_tokens": 7, "output_tokens": 3}, identity("inv-rt"), PRICING
        )
        cp, _ = ur.merge_checkpoint(cp, rec)
        parsed = ur.parse_usage_block(ur.dump_usage_block(cp))
        self.assertEqual(len(parsed["records"]), 1)
        self.assertEqual(parsed["records"][0]["invocation_id"], "inv-rt")
        self.assertEqual(parsed["records"][0]["total_tokens"], 10)

    def test_write_failure_preserves_prior_checkpoint(self):
        import tempfile

        with tempfile.TemporaryDirectory() as raw_tmp:
            tmp = Path(raw_tmp)
            cp = ur.empty_checkpoint()
            rec = ur.normalize_invocation(
                {"input_tokens": 7, "output_tokens": 3}, identity("inv-keep"), PRICING
            )
            cp, _ = ur.merge_checkpoint(cp, rec)
            plan = self._plan(tmp, ur.dump_usage_block(cp))
            good = plan.read_text(encoding="utf-8")

            # Simulate an atomic-write failure mid-rename.
            original_replace = ur.os.replace

            def boom(*_args, **_kw):
                raise OSError("simulated atomic write failure")

            ur.os.replace = boom
            try:
                cp2, _ = ur.merge_checkpoint(
                    ur.read_checkpoint(plan),
                    ur.normalize_invocation(
                        {"input_tokens": 1, "output_tokens": 1},
                        identity("inv-lost"),
                        PRICING,
                    ),
                )
                with self.assertRaises(OSError):
                    ur.write_checkpoint(plan, cp2)
            finally:
                ur.os.replace = original_replace
            self.assertEqual(
                list(tmp.glob("*.tmp")), [], "temp file cleaned up on failure"
            )
            self.assertEqual(plan.read_text(encoding="utf-8"), good)
            self.assertEqual(
                len(ur.read_checkpoint(plan)["records"]), 1, "prior record survived"
            )

    def test_missing_block_reads_as_empty_not_error(self):
        import tempfile

        with tempfile.TemporaryDirectory() as raw_tmp:
            plan = self._plan(Path(raw_tmp), None)
            cp = ur.read_checkpoint(plan)
            self.assertEqual(cp["records"], [])
            self.assertEqual(cp["report_status"], "unavailable")


if __name__ == "__main__":
    unittest.main()
