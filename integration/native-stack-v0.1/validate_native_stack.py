#!/usr/bin/env python3
"""Validate one opt-in native DIF -> DI -> DRP -> TIP record chain.

This is an integration proof, not a fifth protocol. Canonical repositories
remain authoritative; DI's cross-stack envelope remains a reduced projection.
The validator downloads nothing and performs no external action.
"""
from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
import os
import subprocess
import sys
from pathlib import Path
from typing import Any

BRIDGE = Path(__file__).resolve().parent
DI_ROOT = BRIDGE.parents[1]
DRP_STATUS_TO_PROJECTION = {"complete": "committed"}


class PreparationError(Exception):
    """The bridge could not evaluate its inputs at all."""


class Report:
    def __init__(self) -> None:
        self.validity: list[str] = []
        self.mapping: list[str] = []
        self.checks: list[dict[str, Any]] = []

    def fail(self, dimension: str, message: str) -> None:
        (self.validity if dimension == "validity" else self.mapping).append(message)

    def check(self, name: str, ok: bool, detail: str = "") -> None:
        self.checks.append({"check": name, "ok": ok, "detail": detail})

    @property
    def ok(self) -> bool:
        return not self.validity and not self.mapping


def read_json(path: Path, label: str) -> Any:
    if not path.exists():
        raise PreparationError(f"{label}: missing native record file {path.name}")
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except UnicodeDecodeError as exc:
        raise PreparationError(f"{label}: invalid UTF-8: {exc}") from exc
    except json.JSONDecodeError as exc:
        raise PreparationError(f"{label}: invalid JSON: {exc}") from exc
    except OSError as exc:
        raise PreparationError(f"{label}: cannot read file: {exc}") from exc


def load_module(path: Path, name: str):
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise PreparationError(f"cannot import {path}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def git_head(root: Path) -> str:
    run = subprocess.run(
        ["git", "-C", str(root), "rev-parse", "HEAD"],
        capture_output=True,
        text=True,
    )
    if run.returncode:
        raise PreparationError(f"cannot read git HEAD for {root}: {(run.stderr or run.stdout).strip()}")
    return run.stdout.strip()


def git_is_ancestor(root: Path, ancestor: str) -> bool:
    return subprocess.run(
        ["git", "-C", str(root), "merge-base", "--is-ancestor", ancestor, "HEAD"],
        capture_output=True,
        text=True,
    ).returncode == 0


def require_manifest(value: Any) -> dict[str, Any]:
    if not isinstance(value, dict):
        raise PreparationError("manifest root must be an object")
    for field in ("bridge_version", "bridge_id", "di_repository", "external_repositories", "body_hashes", "status_mapping"):
        if field not in value:
            raise PreparationError(f"manifest missing required field {field!r}")
    if value["bridge_version"] != "0.1":
        raise PreparationError("manifest bridge_version must be '0.1'")
    if not isinstance(value["di_repository"], dict):
        raise PreparationError("manifest di_repository must be an object")
    external = value["external_repositories"]
    if not isinstance(external, dict):
        raise PreparationError("manifest external_repositories must be an object")
    for key in ("dif", "drp", "tip"):
        spec = external.get(key)
        if not isinstance(spec, dict):
            raise PreparationError(f"manifest external_repositories.{key} must be an object")
        for field in ("repository", "commit"):
            if not isinstance(spec.get(field), str) or not spec[field]:
                raise PreparationError(f"manifest {key}.{field} must be a non-empty string")
    if not isinstance(value["body_hashes"], dict) or not value["body_hashes"]:
        raise PreparationError("manifest body_hashes must be a non-empty object")
    return value


def check_pins(manifest: dict[str, Any], roots: dict[str, Path], report: Report) -> None:
    base = manifest["di_repository"].get("base_commit")
    if not isinstance(base, str) or not base:
        report.fail("validity", "DI base commit provenance is missing from manifest")
    elif not git_is_ancestor(DI_ROOT, base):
        report.fail("validity", f"DI base commit {base} is not an ancestor of integration HEAD")
    else:
        report.check("pin:di-base-ancestor", True, base)

    for key in ("dif", "drp", "tip"):
        root = roots[key]
        if not root.exists():
            report.fail("validity", f"{key}: external checkout root does not exist: {root}")
            continue
        head = git_head(root)
        expected = manifest["external_repositories"][key]["commit"]
        ok = head == expected
        report.check(f"pin:{key}", ok, head)
        if not ok:
            report.fail("validity", f"{key}: external checkout commit mismatch: HEAD {head} != pinned {expected}")


def check_hashes(manifest: dict[str, Any], bridge: Path, report: Report) -> None:
    for rel, expected in manifest["body_hashes"].items():
        if not isinstance(rel, str) or not isinstance(expected, str):
            report.fail("validity", "manifest body_hashes entries must be string -> string")
            continue
        path = bridge / rel
        if not path.exists():
            report.fail("validity", f"body hash: missing native record file {rel}")
            continue
        actual = sha256(path)
        ok = actual == expected
        report.check(f"body-hash:{rel}", ok, actual)
        if not ok:
            report.fail(
                "validity",
                f"body hash mismatch for {rel}: actual {actual} != manifest {expected}; canonical body changed while identifier may be unchanged",
            )


def validate_dif(manifest: dict[str, Any], root: Path, intent: Any, report: Report) -> None:
    try:
        import jsonschema
        from jsonschema import FormatChecker
    except ImportError as exc:
        raise PreparationError("install requirements-integration.txt for DIF schema validation") from exc
    schema = read_json(root / manifest["external_repositories"]["dif"]["schema"], "DIF schema")
    validator_class = jsonschema.validators.validator_for(schema)
    validator_class.check_schema(schema)
    errors = list(validator_class(schema, format_checker=FormatChecker()).iter_errors(intent))
    for error in errors:
        loc = "$" + "".join(f".{part}" for part in error.path)
        report.fail("validity", f"DIF ConfirmedIntent {loc}: {error.message}")
    report.check("dif:pinned-schema", not errors, f"{len(errors)} error(s)")
    if not isinstance(intent, dict) or intent.get("confirmedByHuman") is not True:
        report.fail("validity", "DIF ConfirmedIntent confirmedByHuman must be literally true")


def validate_di(feasibility: Any, projection: Any, report: Report) -> None:
    module = load_module(DI_ROOT / "scripts/validate-fixtures.py", "native_stack_di_validator")
    feasibility_schema = read_json(DI_ROOT / "schemas/feasibility-check.schema.json", "DI feasibility schema")
    errors = module.validate(feasibility, feasibility_schema)
    for error in errors:
        report.fail("validity", f"DI feasibility {error}")
    report.check("di:feasibility-schema", not errors, f"{len(errors)} error(s)")

    envelope_schema = read_json(DI_ROOT / "schemas/decision-transition-envelope.schema.json", "DI envelope schema")
    envelope_errors = module.validate(projection, envelope_schema)
    envelope_errors.extend(module.validate_envelope_semantics(projection))
    for error in envelope_errors:
        report.fail("validity", f"DI projection {error}")
    report.check("di:projection-schema-and-semantics", not envelope_errors, f"{len(envelope_errors)} error(s)")


def run_native(cmd: list[str], cwd: Path, label: str, report: Report) -> subprocess.CompletedProcess[str]:
    run = subprocess.run(cmd, cwd=str(cwd), capture_output=True, text=True)
    output = (run.stdout + run.stderr).strip()
    report.check(label, run.returncode == 0, f"rc={run.returncode}")
    if run.returncode:
        report.fail("validity", f"{label}: native validator exited {run.returncode}: {output[:3000]}")
    return run


def validate_drp(manifest: dict[str, Any], root: Path, path: Path, report: Report) -> None:
    validator = manifest["external_repositories"]["drp"]["validator"]
    run_native([sys.executable, validator, str(path)], root, "drp:native-validator", report)


def validate_tip(root: Path, path: Path, report: Report) -> None:
    run_native([sys.executable, "-m", "tip", "validate", str(path)], root, "tip:native-cli", report)


def eq(report: Report, label: str, left: Any, right: Any) -> None:
    ok = left == right
    report.check(label, ok)
    if not ok:
        report.fail("mapping", f"{label}: {left!r} != {right!r}")


def check_mapping(intent: dict[str, Any], feasibility: dict[str, Any], drp: dict[str, Any], tip: dict[str, Any], projection: dict[str, Any], report: Report) -> None:
    p_dif = projection.get("dif", {})
    p_di = projection.get("di", {})
    p_drp = projection.get("drp", {})
    p_tip = projection.get("tip", {})
    p_review = projection.get("review", {})

    eq(report, "projection.dif.intent_id must match canonical DIF id", p_dif.get("intent_id"), intent.get("id"))
    eq(report, "projection.di.intent_id must match canonical DIF id", p_di.get("intent_id"), intent.get("id"))
    eq(report, "canonical DI request must match DIF statement", feasibility.get("request"), intent.get("statement"))
    eq(report, "projection.di.feasibility_id must match canonical DI check_id", p_di.get("feasibility_id"), feasibility.get("check_id"))
    eq(report, "projection.drp.feasibility_id must match canonical DI check_id", p_drp.get("feasibility_id"), feasibility.get("check_id"))
    eq(report, "projection.di.allowed_paths must match canonical DI feasible actions", p_di.get("allowed_paths"), [x.get("action") for x in feasibility.get("feasible_actions", [])])
    eq(report, "projection.di.blocked_paths must match canonical DI blocked actions", p_di.get("blocked_paths"), [x.get("action") for x in feasibility.get("blocked_actions", [])])
    eq(report, "projection.drp.record_id must match canonical DRP record_id", p_drp.get("record_id"), drp.get("record_id"))
    eq(report, "projection.drp.decision_summary must match canonical DRP decision", p_drp.get("decision_summary"), drp.get("decision"))

    status = drp.get("status")
    mapped = DRP_STATUS_TO_PROJECTION.get(status)
    if mapped is None:
        report.fail("mapping", f"unsupported DRP status for this bridge: {status!r}; only DRP 'complete' may map to projection 'committed'")
    elif mapped != p_drp.get("status"):
        report.fail("mapping", f"unsupported DRP status mapping: DRP {status!r} maps to {mapped!r}, not {p_drp.get('status')!r}")
    report.check("drp:explicit-status-mapping", mapped is not None and mapped == p_drp.get("status"), f"{status}->{mapped}")

    upstream = (drp.get("metadata") or {}).get("upstream_ids") or {}
    eq(report, "DRP metadata DIF intent id", upstream.get("dif_intent_id"), intent.get("id"))
    eq(report, "DRP metadata DI check id", upstream.get("di_check_id"), feasibility.get("check_id"))
    eq(report, "DRP metadata downstream TIP id", upstream.get("tip_transition_id"), tip.get("id"))

    eq(report, "projection.tip.transition_id must match canonical TIP id", p_tip.get("transition_id"), tip.get("id"))
    eq(report, "projection.review.transition_id must match canonical TIP id", p_review.get("transition_id"), tip.get("id"))
    eq(report, "projection TIP decision reference must equal canonical DRP record_id", p_tip.get("decision_record_id"), drp.get("record_id"))
    transition = tip.get("transition") or {}
    eq(report, "TIP transition.from must match projection starting_state", transition.get("from"), p_tip.get("starting_state"))
    eq(report, "TIP transition.to must match projection target_state", transition.get("to"), p_tip.get("target_state"))
    eq(report, "TIP action.summary must match projection action_summary", (tip.get("action") or {}).get("summary"), p_tip.get("action_summary"))

    if p_tip.get("status") == "reviewed" or p_review.get("status") == "reviewed":
        review = tip.get("review")
        if not isinstance(review, dict):
            report.fail("mapping", "reviewed projection requires a TIP review object")
            return
        evidence = review.get("evidence")
        evidence_ok = isinstance(evidence, list) and bool(evidence) and all(isinstance(x, str) and x.strip() for x in evidence)
        if not evidence_ok:
            report.fail("mapping", "reviewed projection requires nonempty TIP review evidence (bridge is stricter than native TIP minimum)")
        next_state = review.get("next_state")
        next_ok = isinstance(next_state, str) and bool(next_state.strip())
        if not next_ok:
            report.fail("mapping", "reviewed projection requires a concrete TIP review next_state (bridge is stricter than native TIP minimum)")
        if evidence_ok:
            eq(report, "TIP review.evidence must match projection evidence_references", evidence, p_review.get("evidence_references"))
        if next_ok:
            eq(report, "TIP review.next_state must match projection review.next_state", next_state, p_review.get("next_state"))


def payload(manifest: dict[str, Any], report: Report) -> dict[str, Any]:
    return {
        "report_version": "0.1",
        "bridge_id": manifest.get("bridge_id"),
        "result": "PASS" if report.ok else "FAIL",
        "dimensions": {
            "validity": {"status": "pass" if not report.validity else "fail", "errors": report.validity},
            "mapping_consistency": {"status": "pass" if not report.mapping else "fail", "errors": report.mapping},
            "evidence_authenticity": {"status": "not_verified", "note": "Evidence strings are references only; the bridge does not fetch or cryptographically authenticate them."},
            "execution_authority": {"status": "not_claimed", "note": "No execution occurs here; the bridge holds no credential and grants no provider or financial mutation authority."}
        },
        "checks": report.checks,
    }


def validate_bridge(bridge: Path, roots: dict[str, Path]) -> tuple[dict[str, Any], int]:
    report = Report()
    manifest: dict[str, Any] = {"bridge_id": None}
    try:
        manifest = require_manifest(read_json(bridge / "manifest.json", "manifest"))
        check_pins(manifest, roots, report)
        check_hashes(manifest, bridge, report)
        intent = read_json(bridge / "records/confirmed-intent.json", "DIF ConfirmedIntent")
        feasibility = read_json(bridge / "records/di-feasibility.json", "DI feasibility")
        drp = read_json(bridge / "records/drp-record.json", "DRP record")
        tip = read_json(bridge / "records/tip-record.tip.json", "TIP record")
        projection = read_json(bridge / "projection-envelope.json", "DI projection")
        validate_dif(manifest, roots["dif"], intent, report)
        validate_di(feasibility, projection, report)
        validate_drp(manifest, roots["drp"], bridge / "records/drp-record.json", report)
        validate_tip(roots["tip"], bridge / "records/tip-record.tip.json", report)
        check_mapping(intent, feasibility, drp, tip, projection, report)
    except PreparationError as exc:
        report.fail("validity", f"bridge preparation failure: {exc}")
    data = payload(manifest, report)
    return data, 0 if report.ok else 1


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--bridge-dir", default=str(BRIDGE))
    parser.add_argument("--dif-root", default=os.environ.get("DIF_ROOT"))
    parser.add_argument("--drp-root", default=os.environ.get("DRP_ROOT"))
    parser.add_argument("--tip-root", default=os.environ.get("TIP_ROOT"))
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args(argv)
    raw = {"dif": args.dif_root, "drp": args.drp_root, "tip": args.tip_root}
    missing = [f"--{k}-root" for k, v in raw.items() if not v]
    if missing:
        print("ERROR: external checkout roots are required: " + ", ".join(missing), file=sys.stderr)
        print("This integration validator never downloads repositories.", file=sys.stderr)
        return 2
    roots = {k: Path(v).resolve() for k, v in raw.items()}
    data, rc = validate_bridge(Path(args.bridge_dir).resolve(), roots)
    if args.json:
        print(json.dumps(data, indent=2, ensure_ascii=False))
    else:
        for check in data["checks"]:
            print(("OK " if check["ok"] else "FAIL ") + check["check"] + (f" ({check['detail']})" if check["detail"] else ""))
        for dim in ("validity", "mapping_consistency"):
            for error in data["dimensions"][dim]["errors"]:
                print(f"ERROR [{dim}] {error}")
        print("evidence_authenticity: not_verified")
        print("execution_authority: not_claimed")
        print(data["result"])
    return rc


if __name__ == "__main__":
    raise SystemExit(main())
