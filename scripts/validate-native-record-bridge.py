#!/usr/bin/env python3
"""Validate one pinned full-record bridge across DIF -> DI -> DRP -> TIP."""

from __future__ import annotations

import argparse
import importlib.util
import json
from pathlib import Path
import sys
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from native_bridge_io import (  # noqa: E402
    BridgeHarnessError, load_bundle, load_json, section,
    validate_upstream_native, verify_body_binding, verify_host_ancestor,
    verify_upstream_pins, native_command,
)
_native_command_result = native_command
from native_bridge_rules import cross_record_errors, validate_projection  # noqa: E402

DEFAULT_BRIDGE_DIR = ROOT / "integration" / "native-record-bridge" / "v0.1"


def _load_di_validator(root: Path):
    path = root / "scripts" / "validate-fixtures.py"
    if not path.exists():
        raise BridgeHarnessError(f"DI validator is missing: {path}")
    spec = importlib.util.spec_from_file_location("di_bridge_validate_fixtures", path)
    if spec is None or spec.loader is None:
        raise BridgeHarnessError(f"cannot import DI validator: {path}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    try:
        spec.loader.exec_module(module)
    except Exception as exc:
        raise BridgeHarnessError(f"cannot import DI validator: {exc}") from exc
    return module


def validate_di_native(record: dict[str, Any], root: Path):
    module = _load_di_validator(root)
    try:
        schema = module.load_json(root / "schemas" / "feasibility-check.schema.json")
        errors = module.validate(record, schema)
    except Exception as exc:
        raise BridgeHarnessError(f"DI native validation machinery failed: {exc}") from exc
    if not isinstance(errors, list):
        raise BridgeHarnessError("DI native validator returned a non-list error result")
    return section([str(item) for item in errors], mode="native-local-schema"), module


def validate_bridge(
    bridge_dir: Path = DEFAULT_BRIDGE_DIR, *,
    root: Path = ROOT, upstream_root: Path | None = None
) -> dict[str, Any]:
    manifest, records, paths = load_bundle(bridge_dir)
    body = verify_body_binding(manifest, paths)
    host = verify_host_ancestor(manifest, root)
    native = {
        key: {"status": "not_evaluated", "reason": "no --upstream-root supplied"}
        for key in ("dif", "drp", "tip")
    }
    report: dict[str, Any] = {
        "report_version": "0.1", "bridge_id": manifest.get("bridge_id"),
        "status": "PASS", "host_pin": host, "native_record_validity": native,
        "body_binding": body,
        "cross_record_consistency": {"status": "not_evaluated", "errors": []},
        "projection_consistency": {"status": "not_evaluated", "errors": []},
        "evidence_authenticity": {
            "status": "not_evaluated",
            "reason": "provider-neutral evidence references are identifiers only; their truth is not authenticated here",
        },
        "execution_authority": {
            "status": "not_evaluated",
            "reason": "this bridge validates records and mappings; it grants no execution authority",
        },
        "non_claims": manifest.get("non_claims", []),
    }

    di_result, di_module = validate_di_native(records["di"], root)
    report["native_record_validity"]["di"] = di_result
    if body["status"] == "fail":
        report["status"] = "FAIL"
        return report

    cross = cross_record_errors(manifest, records)
    report["cross_record_consistency"] = section(cross)
    if cross:
        report["status"] = "FAIL"
        return report

    try:
        envelope_schema = di_module.load_json(
            root / "schemas" / "decision-transition-envelope.schema.json"
        )
        projection = validate_projection(
            manifest, records, di_module, envelope_schema
        )
    except Exception as exc:
        raise BridgeHarnessError(
            f"DI projection validation machinery failed: {exc}"
        ) from exc
    report["projection_consistency"] = projection
    if projection["status"] == "fail":
        report["status"] = "FAIL"
        return report

    if upstream_root is not None:
        report["native_record_validity"].update(
            validate_upstream_native(manifest, records, paths, upstream_root)
        )

    for value in report["native_record_validity"].values():
        if isinstance(value, dict) and value.get("status") == "fail":
            report["status"] = "FAIL"
    if host.get("status") == "fail":
        report["status"] = "FAIL"
    return report


def parse_args(argv: list[str] | None = None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--bridge-dir", type=Path, default=DEFAULT_BRIDGE_DIR)
    parser.add_argument("--upstream-root", type=Path)
    parser.add_argument("--pretty", action="store_true")
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    try:
        report = validate_bridge(
            args.bridge_dir, root=ROOT, upstream_root=args.upstream_root
        )
    except BridgeHarnessError as exc:
        report = {
            "report_version": "0.1", "status": "HARNESS_FAIL",
            "errors": [str(exc)],
            "non_claims": [
                "A harness failure is not a semantic rejection and proves no record invalid."
            ],
        }
        print(json.dumps(report, ensure_ascii=False, indent=2 if args.pretty else None))
        return 2
    print(json.dumps(report, ensure_ascii=False, indent=2 if args.pretty else None))
    return 0 if report["status"] == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
