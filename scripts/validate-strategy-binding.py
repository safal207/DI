#!/usr/bin/env python3
"""Validate the DI -> Strategy -> DRP -> TIP path binding.

The Strategy Bridge is integration glue, not a fifth protocol. DI enumerates
feasible paths, Strategy compares them without committing, DRP selects one path,
and TIP must continue exactly that selected path.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]

CASES = [
    ("fixtures/valid-decision-transition-envelope-v0.2-strategy.json", True),
    ("fixtures/invalid-decision-transition-envelope-v0.2-tip-path-mismatch.json", False),
]


def load_json(path: Path) -> Any:
    with path.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def nonempty_string(value: Any) -> bool:
    return isinstance(value, str) and bool(value.strip())


def validate_strategy_envelope(instance: Any) -> list[str]:
    if not isinstance(instance, dict):
        return ["$: envelope must be an object"]

    errors: list[str] = []

    if instance.get("envelope_version") != "0.2":
        errors.append("$.envelope_version: expected '0.2'")

    dif = instance.get("dif")
    di = instance.get("di")
    strategy = instance.get("strategy")
    drp = instance.get("drp")
    tip = instance.get("tip")
    review = instance.get("review")

    if not all(isinstance(part, dict) for part in (dif, di, strategy, drp, tip, review)):
        errors.append("$: DIF, DI, strategy, DRP, TIP, and review objects are required")
        return errors

    if dif.get("human_confirmed") is not True:
        errors.append("$.dif.human_confirmed: intent must be human-confirmed")

    if di.get("intent_id") != dif.get("intent_id"):
        errors.append("$.di.intent_id: must exactly match $.dif.intent_id")

    feasibility_id = di.get("feasibility_id")
    if not nonempty_string(feasibility_id):
        errors.append("$.di.feasibility_id: required")

    feasible_paths = di.get("feasible_paths")
    if not isinstance(feasible_paths, list) or not feasible_paths:
        errors.append("$.di.feasible_paths: at least one feasible path is required")
        feasible_paths = []

    feasible_ids: list[str] = []
    for index, path in enumerate(feasible_paths):
        p = f"$.di.feasible_paths[{index}]"
        if not isinstance(path, dict):
            errors.append(f"{p}: path must be an object")
            continue
        path_id = path.get("path_id")
        if not nonempty_string(path_id):
            errors.append(f"{p}.path_id: required")
            continue
        if path_id in feasible_ids:
            errors.append(f"{p}.path_id: duplicate path_id {path_id!r}")
        feasible_ids.append(path_id)

    if strategy.get("feasibility_id") != feasibility_id:
        errors.append("$.strategy.feasibility_id: must exactly match $.di.feasibility_id")

    candidate_ids = strategy.get("candidate_path_ids")
    if not isinstance(candidate_ids, list) or not candidate_ids:
        errors.append("$.strategy.candidate_path_ids: at least one candidate path is required")
        candidate_ids = []

    if len(candidate_ids) != len(set(candidate_ids)):
        errors.append("$.strategy.candidate_path_ids: duplicate candidate path ids are not allowed")

    for path_id in candidate_ids:
        if path_id not in feasible_ids:
            errors.append(
                f"$.strategy.candidate_path_ids: candidate {path_id!r} was not produced by DI as feasible"
            )

    recommended = strategy.get("recommended_path_id")
    if recommended not in candidate_ids:
        errors.append("$.strategy.recommended_path_id: recommendation must be one of the candidate paths")

    if not nonempty_string(strategy.get("rationale")):
        errors.append("$.strategy.rationale: non-empty comparison rationale is required")

    if drp.get("feasibility_id") != feasibility_id:
        errors.append("$.drp.feasibility_id: must exactly match $.di.feasibility_id")
    if drp.get("strategy_id") != strategy.get("strategy_id"):
        errors.append("$.drp.strategy_id: must exactly match $.strategy.strategy_id")

    selected = drp.get("selected_path_id")
    if selected not in feasible_ids:
        errors.append("$.drp.selected_path_id: committed path must originate from DI.feasible_paths")
    if selected not in candidate_ids:
        errors.append("$.drp.selected_path_id: committed path must have been evaluated by Strategy")

    if tip.get("decision_record_id") != drp.get("record_id"):
        errors.append("$.tip.decision_record_id: must exactly match $.drp.record_id")

    if tip.get("selected_path_id") != selected:
        errors.append(
            "$.tip.selected_path_id: must exactly match $.drp.selected_path_id; path substitution after commitment is forbidden"
        )

    if review.get("transition_id") != tip.get("transition_id"):
        errors.append("$.review.transition_id: must exactly match $.tip.transition_id")

    return errors


def run_case(fixture_rel: str, expected_pass: bool) -> bool:
    try:
        instance = load_json(ROOT / fixture_rel)
        errors = validate_strategy_envelope(instance)
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
        print("  - fixture unexpectedly passed strategy binding validation")
    return False


def main() -> int:
    ok = True
    for fixture_rel, expected_pass in CASES:
        ok = run_case(fixture_rel, expected_pass) and ok
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
