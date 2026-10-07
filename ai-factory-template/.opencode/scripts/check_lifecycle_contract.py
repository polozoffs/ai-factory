#!/usr/bin/env python3
"""Deterministic static contract checks for the AI-factory lifecycle.

Reads only `.opencode/` markdown contracts from disk. Performs no network,
database, external-system, or git mutation calls, and writes nothing.

Run: python3 .opencode/scripts/check_lifecycle_contract.py
Exit code 0 = all contract assertions hold, 1 = one or more violations.

Portable: this checker asserts only the project-independent factory contract
(lifecycle states, checkpoint schema, transitions, correction routing, session
identity, bounded retries, closure/release gates, command forms, and safety).
Per-feature scope-boundary assertions belong in a feature's own QA plan, not
here.
"""

from __future__ import annotations

import re
import sys
from pathlib import Path

OPENCODE = Path(__file__).resolve().parent.parent

WORKFLOW = "rules/workflow.md"
FACTORY = "agent/factory.md"
IMPLEMENTER = "agent/implementer.md"
VALIDATOR = "agent/validator.md"
RELEASE_MANAGER = "agent/release-manager.md"
CMD_FEATURE = "command/feature.md"
CMD_IMPLEMENT = "command/implement.md"
CMD_VALIDATE = "command/validate.md"

STATES = [
    "PLANNING",
    "AWAITING_PLANNING_APPROVAL",
    "IMPLEMENTING",
    "AWAITING_IMPLEMENTATION_APPROVAL",
    "VALIDATING",
    "FIX_REQUESTED",
    "AWAITING_FINAL_SIGNOFF",
    "ESCALATED",
    "DONE",
]

CHECKPOINT_FIELDS = [
    "slug",
    "spec_path",
    "session_id",
    "iteration",
    "state",
    "completed_chunks",
    "planning_approval",
    "implementation_approval",
    "final_approval",
    "last_handoff_source",
    "retry_count",
    "retry_limit",
    "safe_rollback_point",
    "scope_boundary",
]

# (from-state marker, trigger marker, to-state marker) within one table row.
TRANSITIONS = [
    ("AWAITING_PLANNING_APPROVAL", "planning approval", "IMPLEMENTING"),
    ("IMPLEMENTING", "chunks reported", "AWAITING_IMPLEMENTATION_APPROVAL"),
    ("AWAITING_IMPLEMENTATION_APPROVAL", "validation requested", "VALIDATING"),
    ("VALIDATING", "FAIL", "FIX_REQUESTED"),
    ("VALIDATING", "PASS", "AWAITING_FINAL_SIGNOFF"),
    ("AWAITING_FINAL_SIGNOFF", "fix", "FIX_REQUESTED"),
    ("AWAITING_FINAL_SIGNOFF", "approval", "DONE"),
    ("FIX_REQUESTED", "retry_count < retry_limit", "IMPLEMENTING"),
    ("FIX_REQUESTED", "retry_count == retry_limit", "ESCALATED"),
]

failures: list[str] = []
checks = 0


def read(rel: str) -> str:
    path = OPENCODE / rel
    if not path.is_file():
        failures.append(f"missing contract file: {rel}")
        return ""
    return path.read_text(encoding="utf-8")


def check(condition: bool, message: str) -> None:
    global checks
    checks += 1
    if not condition:
        failures.append(message)


def contains(text: str, needle: str, rel: str, label: str) -> None:
    """Substring check that is insensitive to markdown hard-wrap line breaks."""
    flat = re.sub(r"\s+", " ", text).lower()
    check(
        re.sub(r"\s+", " ", needle).lower() in flat,
        f"{rel}: {label} (missing {needle!r})",
    )


def main() -> int:
    workflow = read(WORKFLOW)
    factory = read(FACTORY)
    implementer = read(IMPLEMENTER)
    validator = read(VALIDATOR)
    release_manager = read(RELEASE_MANAGER)
    cmd_feature = read(CMD_FEATURE)
    cmd_implement = read(CMD_IMPLEMENT)
    cmd_validate = read(CMD_VALIDATE)

    # 1. Lifecycle states are declared.
    for state in STATES:
        contains(workflow, state, WORKFLOW, f"lifecycle state {state} undeclared")

    # 2. Checkpoint identity fields are declared.
    for field in CHECKPOINT_FIELDS:
        contains(workflow, field, WORKFLOW, f"checkpoint field {field} undeclared")

    # 3. Transition table rows exist with from/trigger/to on one row.
    rows = [line for line in workflow.splitlines() if line.strip().startswith("|")]
    for src, trigger, dst in TRANSITIONS:
        found = any(
            src in row and trigger.lower() in row.lower() and dst in row for row in rows
        )
        check(found, f"{WORKFLOW}: missing transition {src} --{trigger}--> {dst}")

    # 4. Pending implementation approval is never a planning reset.
    contains(
        workflow,
        "not** a replan state",
        WORKFLOW,
        "AWAITING_IMPLEMENTATION_APPROVAL must be marked as not a replan state",
    )
    contains(
        factory,
        "Never treat `AWAITING_IMPLEMENTATION_APPROVAL` as a replan state",
        FACTORY,
        "orchestrator must forbid replan on pending implementation approval",
    )
    contains(
        cmd_validate,
        "implementation approval is still pending",
        CMD_VALIDATE,
        "validation must be allowed while implementation approval is pending",
    )

    # 5. Same-session correction routing via one compact envelope.
    contains(factory, "CORRECTION", FACTORY, "correction envelope undefined")
    contains(factory, "validator-fail", FACTORY, "validator-fail source undefined")
    contains(factory, "user-fix", FACTORY, "user-fix source undefined")
    contains(
        factory,
        "Reject the envelope",
        FACTORY,
        "mismatched session/spec evidence must be rejected",
    )
    contains(
        implementer,
        "correction envelope",
        IMPLEMENTER,
        "implementer must accept a correction envelope",
    )

    # 6. Session/iteration are carried through every stage.
    for rel, text in (
        (FACTORY, factory),
        (IMPLEMENTER, implementer),
        (VALIDATOR, validator),
        (CMD_IMPLEMENT, cmd_implement),
        (CMD_VALIDATE, cmd_validate),
        (CMD_FEATURE, cmd_feature),
    ):
        contains(text, "session_id", rel, "session_id context missing")
        contains(text, "iteration", rel, "iteration context missing")

    # 7. Bounded retries and deterministic escalation.
    check(
        bool(re.search(r"retry_limit`?\s*(is|=)\s*3", workflow)),
        f"{WORKFLOW}: retry_limit must be an explicit finite value (3)",
    )
    check(
        bool(re.search(r"retry_limit`?\s*=\s*3", factory)),
        f"{FACTORY}: orchestrator must enforce retry_limit = 3",
    )
    contains(
        workflow,
        "never auto-replans",
        WORKFLOW,
        "ESCALATED must not auto-replan/auto-retry/release",
    )
    contains(
        factory,
        "safe_rollback_point",
        FACTORY,
        "escalation handoff must state safe_rollback_point",
    )

    # 8. Closure gate: PASS alone never releases.
    contains(
        factory,
        "AWAITING_FINAL_SIGNOFF",
        FACTORY,
        "PASS must transition only to AWAITING_FINAL_SIGNOFF",
    )
    contains(
        factory,
        "invalidate",
        FACTORY,
        "post-PASS user fix must invalidate pass evidence and final approval",
    )
    contains(
        cmd_validate,
        "pass_evidence",
        CMD_VALIDATE,
        "PASS must be recorded as pass_evidence for the session/iteration",
    )
    contains(
        cmd_feature,
        "source: user-fix",
        CMD_FEATURE,
        "post-PASS fix must re-enter the same session as a user-fix correction",
    )

    # 9. Release gate requires matching PASS + explicit final approval.
    for token in ("pass_evidence", "final_approval", "session_id", "iteration"):
        contains(
            release_manager,
            token,
            RELEASE_MANAGER,
            f"release entry gate must require {token}",
        )
    contains(
        release_manager,
        "Never infer approval",
        RELEASE_MANAGER,
        "release-manager must never infer approval",
    )
    contains(
        factory,
        "share the same `session_id`",
        FACTORY,
        "release requires PASS and approval sharing session_id/iteration",
    )
    contains(
        factory,
        "Never infer an approval",
        FACTORY,
        "orchestrator must never infer an approval",
    )

    # 10. Backward-compatible positional command forms are preserved.
    contains(
        workflow,
        "/implement <spec-file> <chunk-id>",
        WORKFLOW,
        "positional /implement form must be preserved",
    )
    contains(
        workflow,
        "/validate [spec-file]",
        WORKFLOW,
        "positional /validate form must be preserved",
    )
    contains(
        cmd_implement,
        "chunk",
        CMD_IMPLEMENT,
        "/implement must still require a chunk id",
    )

    # 11. Safety: no external mutation guidance leaks into the loop contracts.
    forbidden = re.compile(r"\bcurl\s+-X\s*(POST|PUT|DELETE|PATCH)", re.IGNORECASE)
    for rel, text in (
        (FACTORY, factory),
        (IMPLEMENTER, implementer),
        (VALIDATOR, validator),
        (CMD_FEATURE, cmd_feature),
        (CMD_IMPLEMENT, cmd_implement),
        (CMD_VALIDATE, cmd_validate),
    ):
        check(
            not forbidden.search(text),
            f"{rel}: contract must not instruct external mutating calls",
        )

    # 12. release-manager must never push.
    contains(
        release_manager,
        "Never edit application code or push",
        RELEASE_MANAGER,
        "release-manager must never push",
    )

    # 13. Unrelated working-tree changes stay outside the feature boundary.
    contains(
        workflow,
        "Unrelated working-tree changes",
        WORKFLOW,
        "workflow must exclude unrelated working-tree changes from the feature",
    )

    if failures:
        print(f"FAIL: {len(failures)} of {checks} contract assertions failed")
        for item in failures:
            print(f"  - {item}")
        return 1
    print(f"PASS: {checks} lifecycle contract assertions hold")
    return 0


if __name__ == "__main__":
    sys.exit(main())
