#!/usr/bin/env python3
"""Validate the native DIF -> DI -> DRP -> TIP bridge projection.

This script validates body hashes, explicit cross-record links, and the derived
DI envelope. Native DIF/DRP/TIP validation is run separately by the companion
GitHub workflow against the commits pinned in manifest.json.
"""
from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
import math
from pathlib import Path
import sys
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_BUNDLE = ROOT / "integrations" / "native-stack-v0.1"
DI_VALIDATOR = ROOT / "scripts" / "validate-fixtures.py"
FEASIBILITY_SCHEMA = ROOT / "schemas" / "feasibility-check.schema.json"
ENVELOPE_SCHEMA = ROOT / "schemas" / "decision-transition-envelope.schema.json"
UNOBSERVED = {"", "UNOBSERVED", "UNKNOWN_UNOBSERVED"}


class BridgeError(ValueError):
    pass


def _constant(token: str) -> Any:
    raise BridgeError(f"non-standard JSON literal {token!r} is not accepted")


def _float(token: str) -> float:
    value = float(token)
    if not math.isfinite(value):
        raise BridgeError(f"numeric literal {token!r} is not finite")
    return value


def load_json(path: Path) -> Any:
    try:
        text = path.read_text(encoding="utf-8")
    except (OSError, UnicodeDecodeError) as exc:
        raise BridgeError(f"cannot read UTF-8 JSON {path}: {exc}") from exc
    try:
        return json.loads(text, parse_constant=_constant, parse_float=_float)
    except json.JSONDecodeError as exc:
        raise BridgeError(f"invalid JSON in {path}: {exc}") from exc


def sha256(path: Path) -> str:
    try:
        return hashlib.sha256(path.read_bytes()).hexdigest()
    except OSError as exc:
        raise BridgeError(f"cannot read artifact {path}: {exc}") from exc


def nonempty(value: Any, path: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise BridgeError(f"{path} must be a non-empty string")
    return value


def safe_file(bundle: Path, rel: str) -> Path:
    root = bundle.resolve()
    path = (bundle / rel).resolve()
    try:
        path.relative_to(root)
    except ValueError as exc:
        raise BridgeError(f"artifact path escapes bundle: {rel}") from exc
    if not path.is_file():
        raise BridgeError(f"artifact is missing or not a file: {rel}")
    return path


def artifact_paths(bundle: Path, manifest: dict[str, Any]) -> dict[str, Path]:
    artifacts = manifest.get("artifacts")
    if not isinstance(artifacts, dict):
        raise BridgeError("$.artifacts must be an object")
    out: dict[str, Path] = {}
    for name in ("dif", "di", "drp", "tip", "expected_envelope"):
        entry = artifacts.get(name)
        if not isinstance(entry, dict):
            raise BridgeError(f"$.artifacts.{name} must be an object")
        path = safe_file(bundle, nonempty(entry.get("path"), f"$.artifacts.{name}.path"))
        expected = nonempty(entry.get("sha256"), f"$.artifacts.{name}.sha256")
        actual = sha256(path)
        if actual != expected:
            raise BridgeError(
                f"$.artifacts.{name}.sha256 mismatch: expected {expected}, got {actual}"
            )
        out[name] = path
    return out


def di_validator():
    spec = importlib.util.spec_from_file_location("native_bridge_di_validator", DI_VALIDATOR)
    if spec is None or spec.loader is None:
        raise BridgeError(f"cannot import DI validator: {DI_VALIDATOR}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def derive(manifest: dict[str, Any], dif: dict, di: dict, drp: dict, tip: dict) -> dict:
    links = manifest.get("links")
    mappings = manifest.get("mappings")
    if not isinstance(links, dict) or not isinstance(mappings, dict):
        raise BridgeError("$.links and $.mappings must be objects")

    if dif.get("confirmedByHuman") is not True:
        raise BridgeError("$.dif.confirmedByHuman must be literal true")
    dif_id = nonempty(dif.get("id"), "$.dif.id")
    statement = nonempty(dif.get("statement"), "$.dif.statement")

    di_id = nonempty(di.get("check_id"), "$.di.check_id")
    if di.get("inferred_intent") != statement:
        raise BridgeError("$.di.inferred_intent must exactly equal $.dif.statement")
    d2i = links.get("dif_to_di")
    if not isinstance(d2i, dict) or d2i.get("dif_intent_id") != dif_id or d2i.get("di_check_id") != di_id:
        raise BridgeError("$.links.dif_to_di does not match canonical DIF/DI records")

    feasible = di.get("feasible_actions")
    blocked = di.get("blocked_actions")
    constraints = di.get("constraints")
    if not isinstance(feasible, list) or not feasible:
        raise BridgeError("$.di.feasible_actions must contain at least one path")
    if not isinstance(blocked, list) or not isinstance(constraints, list) or not constraints:
        raise BridgeError("$.di.blocked_actions/constraints are incomplete")
    allowed_paths = [
        nonempty(item.get("action"), f"$.di.feasible_actions[{i}].action")
        for i, item in enumerate(feasible) if isinstance(item, dict)
    ]
    blocked_paths = [
        nonempty(item.get("action"), f"$.di.blocked_actions[{i}].action")
        for i, item in enumerate(blocked) if isinstance(item, dict)
    ]
    if len(allowed_paths) != len(feasible) or len(blocked_paths) != len(blocked):
        raise BridgeError("$.di feasible/blocked actions must be objects")

    d2d = links.get("di_to_drp")
    if not isinstance(d2d, dict):
        raise BridgeError("$.links.di_to_drp must be an object")
    selected = nonempty(d2d.get("selected_path"), "$.links.di_to_drp.selected_path")
    if selected not in allowed_paths:
        raise BridgeError("$.links.di_to_drp.selected_path was not evaluated as feasible")

    drp_id = nonempty(drp.get("record_id"), "$.drp.record_id")
    if d2d.get("di_check_id") != di_id or d2d.get("drp_record_id") != drp_id:
        raise BridgeError("$.links.di_to_drp does not match canonical DI/DRP records")
    metadata = drp.get("metadata")
    bridge_meta = metadata.get("native_stack_bridge_v0_1") if isinstance(metadata, dict) else None
    if not isinstance(bridge_meta, dict):
        raise BridgeError("$.drp.metadata.native_stack_bridge_v0_1 is required")
    if bridge_meta.get("dif_intent_id") != dif_id:
        raise BridgeError("DRP metadata DIF id does not match canonical DIF record")
    if bridge_meta.get("di_check_id") != di_id:
        raise BridgeError("DRP metadata DI check id does not match canonical DI record")
    if bridge_meta.get("selected_path") != selected:
        raise BridgeError("DRP metadata selected path does not match bridge selection")

    drp_map = mappings.get("drp_status")
    mapped_drp = drp_map.get(drp.get("status")) if isinstance(drp_map, dict) else None
    if mapped_drp != "committed":
        raise BridgeError(f"unsupported DRP status mapping {drp.get('status')!r}")

    tip_id = nonempty(tip.get("id"), "$.tip.id")
    d2t = links.get("drp_to_tip")
    if not isinstance(d2t, dict) or d2t.get("drp_record_id") != drp_id or d2t.get("tip_record_id") != tip_id:
        raise BridgeError("$.links.drp_to_tip does not match canonical DRP/TIP records")

    state, transition, action, review = (tip.get(k) for k in ("state", "transition", "action", "review"))
    if not all(isinstance(x, dict) for x in (state, transition, action, review)):
        raise BridgeError("$.tip state/transition/action/review must all be objects")
    starting = nonempty(state.get("summary"), "$.tip.state.summary")
    if transition.get("from") != starting:
        raise BridgeError("$.tip.transition.from must equal $.tip.state.summary")
    target = nonempty(transition.get("to"), "$.tip.transition.to")
    action_summary = nonempty(action.get("summary"), "$.tip.action.summary")

    tip_map = mappings.get("tip_status")
    mapped_tip = tip_map.get(tip.get("status")) if isinstance(tip_map, dict) else None
    if mapped_tip != "reviewed":
        raise BridgeError(f"unsupported TIP status mapping {tip.get('status')!r}")

    evidence = review.get("evidence")
    next_state = review.get("next_state")
    if not isinstance(evidence, list) or not evidence or not all(isinstance(x, str) and x.strip() for x in evidence):
        raise BridgeError("$.tip.review.evidence must contain at least one reference")
    if not isinstance(next_state, str) or next_state in UNOBSERVED:
        raise BridgeError("$.tip.review.next_state must be a concrete observed state")

    bridge_id = nonempty(manifest.get("bridge_id"), "$.bridge_id")
    return {
        "envelope_version": "0.1",
        "envelope_id": bridge_id.replace("native-stack.", "dti.native-"),
        "dif": {"intent_id": dif_id, "status": "confirmed", "summary": statement, "human_confirmed": True},
        "di": {
            "feasibility_id": di_id,
            "intent_id": dif_id,
            "status": "conditional",
            "allowed_paths": allowed_paths,
            "blocked_paths": blocked_paths,
            "constraints": constraints,
        },
        "drp": {
            "record_id": drp_id,
            "feasibility_id": di_id,
            "decision_summary": nonempty(drp.get("decision"), "$.drp.decision"),
            "status": mapped_drp,
        },
        "tip": {
            "transition_id": tip_id,
            "decision_record_id": drp_id,
            "starting_state": starting,
            "target_state": target,
            "action_summary": action_summary,
            "status": mapped_tip,
        },
        "review": {
            "transition_id": tip_id,
            "status": "reviewed",
            "evidence_references": evidence,
            "next_state": next_state,
        },
    }


def validate_bundle(bundle: Path = DEFAULT_BUNDLE) -> dict[str, Any]:
    manifest = load_json(bundle / "manifest.json")
    if not isinstance(manifest, dict) or manifest.get("bridge_version") != "0.1":
        raise BridgeError("manifest must be a v0.1 object")
    paths = artifact_paths(bundle, manifest)
    records = {name: load_json(path) for name, path in paths.items()}
    if not all(isinstance(value, dict) for value in records.values()):
        raise BridgeError("every native bridge artifact root must be an object")

    envelope = derive(manifest, records["dif"], records["di"], records["drp"], records["tip"])
    if envelope != records["expected_envelope"]:
        raise BridgeError("deterministic projection differs from expected-envelope.json")

    validator = di_validator()
    feasibility_schema = load_json(FEASIBILITY_SCHEMA)
    envelope_schema = load_json(ENVELOPE_SCHEMA)
    errors = [
        f"DI native feasibility {e}"
        for e in validator.validate(records["di"], feasibility_schema)
    ]
    errors += [f"DI envelope {e}" for e in validator.validate(envelope, envelope_schema)]
    errors += [f"DI envelope {e}" for e in validator.validate_envelope_semantics(envelope)]

    return {
        "report_version": "0.1",
        "bridge_id": manifest.get("bridge_id"),
        "status": "PASS" if not errors else "FAIL",
        "artifact_hashes": {name: sha256(path) for name, path in paths.items()},
        "errors": errors,
        "claims": {
            "body_hash_binding": True,
            "cross_record_consistency": not errors,
            "evidence_authenticity": False,
            "execution_authority": False,
        },
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--bundle", type=Path, default=DEFAULT_BUNDLE)
    parser.add_argument("--pretty", action="store_true")
    args = parser.parse_args(argv)
    try:
        report = validate_bundle(args.bundle)
    except (BridgeError, OSError, ValueError) as exc:
        report = {"report_version": "0.1", "status": "FAIL", "errors": [str(exc)]}
    print(json.dumps(report, indent=2 if args.pretty else None, sort_keys=True))
    return 0 if report.get("status") == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
