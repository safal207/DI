#!/usr/bin/env python3
"""Validate the opt-in native DIF → DI → DRP → TIP bridge.

This script deliberately keeps four questions separate:
1) native/schema record validity;
2) cross-record consistency;
3) evidence authenticity (not evaluated);
4) execution authority (not granted).
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
from typing import Any

from jsonschema import FormatChecker, validators


ROOT = Path(__file__).resolve().parents[1]
BRIDGE_ROOT = ROOT / "integration" / "native-record-bridge"
DEFAULT_MANIFEST = BRIDGE_ROOT / "manifest.json"
UNOBSERVED_STATES = {"", "UNKNOWN", "UNOBSERVED", "PENDING", "NOT_OBSERVED"}


class BridgeError(RuntimeError):
    def __init__(self, code: str, detail: str) -> None:
        super().__init__(detail)
        self.code = code
        self.detail = detail

    def as_dict(self) -> dict[str, str]:
        return {"code": self.code, "detail": self.detail}


def load_json(path: Path, *, missing_code: str = "missing_original_record") -> Any:
    if not path.is_file():
        raise BridgeError(missing_code, f"required JSON file is missing: {path}")
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise BridgeError("record_parse_error", f"cannot read JSON {path}: {exc}") from exc


def git_blob_sha(path: Path) -> str:
    data = path.read_bytes()
    payload = b"blob " + str(len(data)).encode("ascii") + b"\0" + data
    return hashlib.sha1(payload).hexdigest()


def content_sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def git_head(repo_root: Path) -> str:
    proc = subprocess.run(
        ["git", "-C", str(repo_root), "rev-parse", "HEAD"],
        text=True,
        capture_output=True,
    )
    if proc.returncode != 0:
        raise BridgeError("repo_version_mismatch", f"cannot resolve HEAD for {repo_root}: {proc.stderr.strip()}")
    return proc.stdout.strip()


def require_repository_pin(name: str, spec: dict[str, Any], repo_root: Path) -> None:
    expected = str(spec["commit"])
    mode = str(spec.get("pin_mode", "exact"))
    actual = git_head(repo_root)

    if mode == "exact":
        if actual != expected:
            raise BridgeError(
                "repo_version_mismatch",
                f"{name} HEAD {actual} does not equal pinned commit {expected}",
            )
    elif mode == "ancestor":
        proc = subprocess.run(
            ["git", "-C", str(repo_root), "merge-base", "--is-ancestor", expected, actual],
            text=True,
            capture_output=True,
        )
        if proc.returncode != 0:
            raise BridgeError(
                "repo_version_mismatch",
                f"{name} HEAD {actual} does not descend from pinned commit {expected}",
            )
    else:
        raise BridgeError("manifest_invalid", f"unsupported pin_mode {mode!r} for {name}")

    schema_path = repo_root / str(spec["schema_path"])
    if not schema_path.is_file():
        raise BridgeError("schema_missing", f"{name} schema is missing: {schema_path}")
    actual_blob = git_blob_sha(schema_path)
    expected_blob = str(spec["schema_blob_sha"])
    if actual_blob != expected_blob:
        raise BridgeError(
            "schema_version_mismatch",
            f"{name} schema blob {actual_blob} does not equal pinned {expected_blob}",
        )


def validate_schema_record(name: str, record: Any, schema_path: Path) -> None:
    schema = load_json(schema_path, missing_code="schema_missing")
    validator_cls = validators.validator_for(schema)
    validator_cls.check_schema(schema)
    validator = validator_cls(schema, format_checker=FormatChecker())
    errors = sorted(validator.iter_errors(record), key=lambda err: list(err.absolute_path))
    if errors:
        first = errors[0]
        where = ".".join(str(part) for part in first.absolute_path) or "$"
        raise BridgeError(f"{name}_record_invalid", f"{where}: {first.message}")


def run_native(name: str, command: list[str], *, cwd: Path, env: dict[str, str] | None = None) -> None:
    proc = subprocess.run(command, cwd=cwd, env=env, text=True, capture_output=True)
    if proc.returncode != 0:
        output = "\n".join(piece for piece in (proc.stdout.strip(), proc.stderr.strip()) if piece)
        raise BridgeError(f"{name}_record_invalid", output or f"{name} validator exited {proc.returncode}")


def record_paths(manifest: dict[str, Any], bridge_root: Path) -> dict[str, Path]:
    result: dict[str, Path] = {}
    records = manifest.get("records")
    if not isinstance(records, dict):
        raise BridgeError("manifest_invalid", "manifest.records must be an object")
    for name in ("dif", "di", "drp", "tip"):
        spec = records.get(name)
        if not isinstance(spec, dict) or not isinstance(spec.get("path"), str):
            raise BridgeError("manifest_invalid", f"manifest.records.{name}.path is required")
        result[name] = bridge_root / spec["path"]
    return result


def require_record_digests(manifest: dict[str, Any], paths: dict[str, Path]) -> None:
    for name, path in paths.items():
        if not path.is_file():
            raise BridgeError("missing_original_record", f"{name} record is missing: {path}")
        expected = str(manifest["records"][name].get("sha256", ""))
        actual = content_sha256(path)
        if actual != expected:
            raise BridgeError(
                "record_digest_mismatch",
                f"{name} record digest {actual} does not equal manifest digest {expected}",
            )


def require_exact_once(actions: list[dict[str, Any]], action_text: str) -> dict[str, Any]:
    matches = [item for item in actions if isinstance(item, dict) and item.get("action") == action_text]
    if len(matches) != 1:
        raise BridgeError(
            "unsupported_status_mapping",
            f"DI recommended_next_step must match exactly one feasible action; found {len(matches)}",
        )
    return matches[0]


def validate_consistency(
    manifest: dict[str, Any],
    dif: dict[str, Any],
    di: dict[str, Any],
    drp: dict[str, Any],
    tip: dict[str, Any],
) -> None:
    links = manifest["links"]

    if dif.get("id") != links["dif_intent_id"]:
        raise BridgeError("reference_mismatch", "DIF intent ID does not match manifest")
    if dif.get("confirmedByHuman") is not True:
        raise BridgeError("dif_confirmation_missing", "DIF intent is not human-confirmed")

    if di.get("check_id") != links["di_check_id"]:
        raise BridgeError("reference_mismatch", "DI check ID does not match manifest")
    if di.get("request") != dif.get("statement"):
        raise BridgeError("reference_mismatch", "DI request is not the exact confirmed DIF statement")

    recommended = di.get("recommended_next_step")
    feasible = di.get("feasible_actions")
    if not isinstance(recommended, str) or not isinstance(feasible, list):
        raise BridgeError("unsupported_status_mapping", "DI recommended action is malformed")
    selected = require_exact_once(feasible, recommended)
    selected_status = selected.get("status")
    if selected_status not in {"allowed", "allowed_with_constraints"}:
        raise BridgeError(
            "unsupported_status_mapping",
            f"DI selected action has non-committable status {selected_status!r}",
        )
    blocked = {
        item.get("action")
        for item in di.get("blocked_actions", [])
        if isinstance(item, dict)
    }
    if recommended in blocked:
        raise BridgeError("unsupported_status_mapping", "DI recommended action is also blocked")

    if drp.get("record_id") != links["drp_record_id"]:
        raise BridgeError("reference_mismatch", "DRP record ID does not match manifest")
    if drp.get("status") != "complete":
        raise BridgeError(
            "unsupported_status_mapping",
            "this bridge maps DI permission to DRP only through an explicitly complete DRP record",
        )
    if drp.get("decision") != recommended:
        raise BridgeError("reference_mismatch", "DRP decision does not equal DI recommended_next_step")

    metadata = drp.get("metadata")
    if not isinstance(metadata, dict):
        raise BridgeError("reference_mismatch", "DRP metadata is required for bridge references")
    if metadata.get("source_dif_intent_id") != dif.get("id"):
        raise BridgeError("reference_mismatch", "DRP metadata does not bind the exact DIF intent")
    if metadata.get("source_di_check_id") != di.get("check_id"):
        raise BridgeError("reference_mismatch", "DRP metadata does not bind the exact DI check")

    expected_conditions = selected.get("conditions", [])
    if selected_status == "allowed_with_constraints" and metadata.get("di_conditions") != expected_conditions:
        raise BridgeError("reference_mismatch", "DRP metadata does not preserve exact DI conditions")

    if tip.get("id") != links["tip_record_id"]:
        raise BridgeError("reference_mismatch", "TIP record ID does not match manifest")
    action = tip.get("action")
    if not isinstance(action, dict) or action.get("summary") != drp.get("decision"):
        raise BridgeError("reference_mismatch", "TIP action does not equal the canonical DRP decision")

    state = tip.get("state")
    if not isinstance(state, dict):
        raise BridgeError("reference_mismatch", "TIP state is required for bridge continuity")
    tip_constraints = state.get("constraints", [])
    if tip_constraints != expected_conditions:
        raise BridgeError(
            "reference_mismatch",
            "TIP state constraints do not preserve the exact selected DI conditions",
        )
    facts = state.get("known_facts", [])
    if f"Confirmed intent: {dif['id']}" not in facts:
        raise BridgeError("reference_mismatch", "TIP does not cite the supplied DIF intent")
    if f"Decision record: {drp['record_id']}" not in facts:
        raise BridgeError("reference_mismatch", "TIP does not cite the supplied DRP record")

    if tip.get("status") != "reviewed":
        raise BridgeError("unobserved_next_state", "TIP record must be reviewed to close this bridge")
    review = tip.get("review")
    if not isinstance(review, dict):
        raise BridgeError("unobserved_next_state", "TIP review is missing")
    evidence = review.get("evidence")
    if not isinstance(evidence, list) or not evidence:
        raise BridgeError("unobserved_next_state", "reviewed TIP record requires non-empty evidence")
    next_state = review.get("next_state")
    if not isinstance(next_state, str) or next_state.strip().upper() in UNOBSERVED_STATES:
        raise BridgeError("unobserved_next_state", "review next_state is not concrete and observed")


def validate_bridge(
    manifest_path: Path = DEFAULT_MANIFEST,
    *,
    dif_root: Path,
    drp_root: Path,
    tip_root: Path,
    di_root: Path = ROOT,
) -> dict[str, Any]:
    manifest = load_json(manifest_path, missing_code="manifest_missing")
    bridge_root = manifest_path.parent

    repos = manifest.get("repositories")
    if not isinstance(repos, dict):
        raise BridgeError("manifest_invalid", "manifest.repositories must be an object")
    roots = {"dif": dif_root, "di": di_root, "drp": drp_root, "tip": tip_root}
    for name, root in roots.items():
        spec = repos.get(name)
        if not isinstance(spec, dict):
            raise BridgeError("manifest_invalid", f"repository specification missing for {name}")
        require_repository_pin(name, spec, root)

    paths = record_paths(manifest, bridge_root)
    require_record_digests(manifest, paths)

    records = {name: load_json(path) for name, path in paths.items()}

    validate_schema_record("dif", records["dif"], dif_root / repos["dif"]["schema_path"])
    validate_schema_record("di", records["di"], di_root / repos["di"]["schema_path"])

    run_native(
        "drp",
        [sys.executable, str(drp_root / "scripts" / "drp-validate"), str(paths["drp"]), "--json"],
        cwd=drp_root,
    )
    tip_env = dict(os.environ)
    tip_env["PYTHONPATH"] = str(tip_root) + os.pathsep + tip_env.get("PYTHONPATH", "")
    run_native(
        "tip",
        [sys.executable, "-m", "tip", "validate", str(paths["tip"])],
        cwd=tip_root,
        env=tip_env,
    )

    validate_consistency(manifest, records["dif"], records["di"], records["drp"], records["tip"])

    return {
        "status": "PASS",
        "case_id": manifest["case_id"],
        "record_validity": {
            "status": "PASS",
            "dif": "schema_only",
            "di": "schema_only",
            "drp": "native_cli",
            "tip": "native_cli",
        },
        "cross_record_consistency": {"status": "PASS"},
        "evidence_authenticity": {
            "status": "NOT_EVALUATED",
            "reason": "Evidence references are not independently authenticated by this bridge.",
        },
        "execution_authority": {
            "status": "NOT_GRANTED",
            "reason": "A valid bridge does not authorize a live payment or provider call.",
        },
    }


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--manifest", type=Path, default=DEFAULT_MANIFEST)
    parser.add_argument("--dif-root", type=Path, required=True)
    parser.add_argument("--drp-root", type=Path, required=True)
    parser.add_argument("--tip-root", type=Path, required=True)
    parser.add_argument("--di-root", type=Path, default=ROOT)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    try:
        report = validate_bridge(
            args.manifest,
            dif_root=args.dif_root.resolve(),
            di_root=args.di_root.resolve(),
            drp_root=args.drp_root.resolve(),
            tip_root=args.tip_root.resolve(),
        )
    except BridgeError as exc:
        print(json.dumps({"status": "FAIL", "error": exc.as_dict()}, indent=2))
        return 1
    print(json.dumps(report, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
