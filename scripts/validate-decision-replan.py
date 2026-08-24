#!/usr/bin/env python3
"""Validate explicit replanning after a committed path becomes invalid or unknown.

A stale decision must not drift into a different TIP path. The old transition is
blocked, DI performs a fresh feasibility assessment, Strategy evaluates the new
candidate set, DRP commits a replacement decision that explicitly supersedes the
old record, and TIP follows the newly selected path.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]

CASES = [
    ("fixtures/valid-decision-replan-chain.json", True),
    ("fixtures/invalid-decision-replan-without-supersession.json", False),
]


def load_json(path: Path) -> Any:
    with path.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def nonempty_string(value: Any) -> bool:
    return isinstance(value, str) and bool(value.strip())


def validate_replan_chain(instance: Any) -> list[str]:
    if not isinstance(instance, dict):
        return ["$: replan chain must be an object"]

    errors: list[str] = []

    if instance.get("chain_version") != "0.1":
        errors.append("$.chain_version: expected '0.1'")

    required_strings = [
        "replan_id",
        "invalidated_decision_record_id",
        "invalidated_path_id",
        "invalidation_revalidation_id",
        "replacement_feasibility_id",
        "replacement_strategy_id",
        "replacement_decision_record_id",
        "supersedes_record_id",
        "replacement_selected_path_id",
        "replacement_tip_transition_id",
        "replacement_tip_path_id",
    ]
    for field in required_strings:
        if not nonempty_string(instance.get(field)):
            errors.append(f"$.{field}: required non-empty string")

    invalidation_status = instance.get("invalidation_status")
    if invalidation_status not in {"invalid", "unknown"}:
        errors.append("$.invalidation_status: replanning requires invalid or unknown path status")

    feasible = instance.get("replacement_feasible_path_ids")
    candidates = instance.get("replacement_candidate_path_ids")
    if not isinstance(feasible, list) or not feasible:
        errors.append("$.replacement_feasible_path_ids: fresh DI must expose at least one feasible path")
        feasible = []
    if not isinstance(candidates, list) or not candidates:
        errors.append("$.replacement_candidate_path_ids: Strategy must evaluate at least one path")
        candidates = []

    if len(feasible) != len(set(feasible)):
        errors.append("$.replacement_feasible_path_ids: duplicate path ids are not allowed")
    if len(candidates) != len(set(candidates)):
        errors.append("$.replacement_candidate_path_ids: duplicate path ids are not allowed")

    for path_id in candidates:
        if path_id not in feasible:
            errors.append(
                f"$.replacement_candidate_path_ids: candidate {path_id!r} was not produced by fresh DI"
            )

    old_decision = instance.get("invalidated_decision_record_id")
    new_decision = instance.get("replacement_decision_record_id")
    if new_decision == old_decision:
        errors.append("$.replacement_decision_record_id: replanning must create a new DRP record")

    if instance.get("supersedes_record_id") != old_decision:
        errors.append(
            "$.supersedes_record_id: replacement DRP must explicitly supersede the invalidated decision"
        )

    selected = instance.get("replacement_selected_path_id")
    if selected not in feasible:
        errors.append("$.replacement_selected_path_id: replacement path must be feasible in fresh DI")
    if selected not in candidates:
        errors.append("$.replacement_selected_path_id: replacement path must have been evaluated by Strategy")

    if selected == instance.get("invalidated_path_id"):
        errors.append(
            "$.replacement_selected_path_id: this reroute chain must not silently reuse the path just invalidated"
        )

    if instance.get("replacement_tip_path_id") != selected:
        errors.append(
            "$.replacement_tip_path_id: TIP must exactly follow the newly committed replacement path"
        )

    evidence = instance.get("evidence_references")
    if not isinstance(evidence, list) or not evidence:
        errors.append("$.evidence_references: replanning requires evidence for invalidation and fresh assessment")

    return errors


def run_case(fixture_rel: str, expected_pass: bool) -> bool:
    try:
        instance = load_json(ROOT / fixture_rel)
        errors = validate_replan_chain(instance)
    except (OSError, json.JSONDecodeError) as exc:
        errors = [str(exc)]

    actual_pass = not errors
    expected_label = "pass" if expected_pass else "fail"

    if actual_pass == expected_pass:
        print(f"PASS {fixture_rel} expected={expected_label}")
        return True

    print(f"FAIL {fixture_rel} expected={expected_label}")
    for error in errors:
        print(f"  - {error}")
    if actual_pass and not expected_pass:
        print("  - fixture unexpectedly passed decision replanning validation")
    return False


def main() -> int:
    ok = True
    for fixture_rel, expected_pass in CASES:
        ok = run_case(fixture_rel, expected_pass) and ok
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
