#!/usr/bin/env python3
"""Minimal DI fixture validator.

This script intentionally implements only the small JSON Schema subset needed by
this repository's seed schemas. It uses Python standard library only.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]

CASES = [
    (
        "fixtures/valid-capability.json",
        "schemas/capability.schema.json",
        True,
    ),
    (
        "fixtures/valid-limitation.json",
        "schemas/limitation.schema.json",
        True,
    ),
    (
        "fixtures/valid-feasibility-check.json",
        "schemas/feasibility-check.schema.json",
        True,
    ),
    (
        "fixtures/invalid-feasibility-missing-request.json",
        "schemas/feasibility-check.schema.json",
        False,
    ),
]


def load_json(path: Path) -> Any:
    if not path.exists():
        raise ValueError(f"file does not exist: {path}")
    try:
        with path.open("r", encoding="utf-8") as handle:
            return json.load(handle)
    except json.JSONDecodeError as exc:
        raise ValueError(f"invalid JSON in {path}: {exc}") from exc


def type_matches(value: Any, expected_type: str) -> bool:
    if expected_type == "object":
        return isinstance(value, dict)
    if expected_type == "array":
        return isinstance(value, list)
    if expected_type == "string":
        return isinstance(value, str)
    if expected_type == "boolean":
        return isinstance(value, bool)
    if expected_type == "number":
        return isinstance(value, (int, float)) and not isinstance(value, bool)
    if expected_type == "integer":
        return isinstance(value, int) and not isinstance(value, bool)
    return True


def validate(instance: Any, schema: dict[str, Any], path: str = "$") -> list[str]:
    errors: list[str] = []

    expected_type = schema.get("type")
    if isinstance(expected_type, str) and not type_matches(instance, expected_type):
        return [f"{path}: expected {expected_type}, got {type(instance).__name__}"]

    enum_values = schema.get("enum")
    if enum_values is not None and instance not in enum_values:
        errors.append(f"{path}: value {instance!r} not in enum {enum_values!r}")

    if expected_type == "object" and isinstance(instance, dict):
        required = schema.get("required", [])
        for field in required:
            if field not in instance:
                errors.append(f"{path}: missing required field {field!r}")

        properties = schema.get("properties", {})
        if schema.get("additionalProperties") is False:
            allowed = set(properties.keys())
            for field in instance.keys():
                if field not in allowed:
                    errors.append(f"{path}: unexpected field {field!r}")

        for field, value in instance.items():
            child_schema = properties.get(field)
            if isinstance(child_schema, dict):
                errors.extend(validate(value, child_schema, f"{path}.{field}"))

    if expected_type == "array" and isinstance(instance, list):
        item_schema = schema.get("items")
        if isinstance(item_schema, dict):
            for index, item in enumerate(instance):
                errors.extend(validate(item, item_schema, f"{path}[{index}]"))

    return errors


def run_case(fixture_rel: str, schema_rel: str, expected_pass: bool) -> bool:
    fixture_path = ROOT / fixture_rel
    schema_path = ROOT / schema_rel

    try:
        fixture = load_json(fixture_path)
        schema = load_json(schema_path)
        errors = validate(fixture, schema)
    except ValueError as exc:
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
        print("  - fixture unexpectedly passed validation")
    return False


def main() -> int:
    ok = True
    for fixture_rel, schema_rel, expected_pass in CASES:
        ok = run_case(fixture_rel, schema_rel, expected_pass) and ok
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
