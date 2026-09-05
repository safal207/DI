#!/usr/bin/env python3
"""Regression tests for the fixture harness in scripts/validate-fixtures.py.

These tests import the ACTUAL script module (no reimplementation) and assert the
distinction the harness must keep:

* semantic rejection - the fixture was read and the rules under test rejected it;
  a case declared ``expected_pass=False`` passes.
* harness failure - the fixture or schema could not be read, decoded or prepared,
  or the validation code crashed; the case must fail regardless of
  ``expected_pass``, and schema validation must not be treated as having run.
"""

from __future__ import annotations

import importlib.util
import io
import os
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

REPO_ROOT = Path(__file__).resolve().parents[1]
SCRIPT_PATH = REPO_ROOT / "scripts" / "validate-fixtures.py"


def _load_actual_module():
    spec = importlib.util.spec_from_file_location("di_validate_fixtures", SCRIPT_PATH)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


harness = _load_actual_module()

VALID_SCHEMA = "schemas/capability.schema.json"
VALID_FIXTURE = "fixtures/valid-capability.json"
NEGATIVE_FIXTURE = "fixtures/invalid-feasibility-missing-request.json"
NEGATIVE_SCHEMA = "schemas/feasibility-check.schema.json"


class HarnessCaseTest(unittest.TestCase):
    def setUp(self) -> None:
        self._tmp = tempfile.TemporaryDirectory(prefix="di-harness-tests-")
        self.tmp = Path(self._tmp.name)
        self.addCleanup(self._tmp.cleanup)
        self.validate_calls: list[tuple] = []

    def rel(self, path: Path) -> str:
        """Path relative to the harness ROOT, so nothing is written into the repo."""
        return os.path.relpath(path, harness.ROOT)

    def write(self, name: str, content: bytes) -> str:
        target = self.tmp / name
        target.write_bytes(content)
        return self.rel(target)

    def run_case(self, fixture_rel: str, schema_rel: str, expected_pass: bool):
        """Run the real run_case, capturing stdout and whether validate() ran."""
        real_validate = harness.validate

        def spy(instance, schema, path="$"):
            self.validate_calls.append((instance, schema, path))
            return real_validate(instance, schema, path)

        buffer = io.StringIO()
        with mock.patch.object(harness, "validate", spy), mock.patch(
            "sys.stdout", buffer
        ):
            result = harness.run_case(fixture_rel, schema_rel, expected_pass)
        return result, buffer.getvalue()

    def assertHarnessFailure(self, result: bool, output: str) -> None:
        self.assertFalse(result, f"expected harness failure, got success:\n{output}")
        self.assertEqual(
            self.validate_calls,
            [],
            "schema validation must not be reached for a preflight failure",
        )
        self.assertNotIn("\nPASS ", "\n" + output)
        self.assertFalse(output.startswith("PASS "), output)

    # --- preflight failures: must fail even when expected_pass=False -----------

    def test_missing_fixture_is_harness_failure(self) -> None:
        for expected_pass in (False, True):
            with self.subTest(expected_pass=expected_pass):
                self.validate_calls.clear()
                result, output = self.run_case(
                    "fixtures/di-harness-nonexistent.json", VALID_SCHEMA, expected_pass
                )
                self.assertHarnessFailure(result, output)
                self.assertIn("file does not exist", output)

    def test_malformed_json_fixture_is_harness_failure(self) -> None:
        rel = self.write("malformed.json", b"{ this is not json ")
        result, output = self.run_case(rel, VALID_SCHEMA, False)
        self.assertHarnessFailure(result, output)
        self.assertIn("invalid JSON", output)

    def test_missing_schema_is_harness_failure(self) -> None:
        result, output = self.run_case(
            NEGATIVE_FIXTURE, "schemas/di-harness-nonexistent.schema.json", False
        )
        self.assertHarnessFailure(result, output)
        self.assertIn("file does not exist", output)

    def test_malformed_schema_is_harness_failure(self) -> None:
        schema_rel = self.write("broken.schema.json", b"{\"type\": ")
        result, output = self.run_case(NEGATIVE_FIXTURE, schema_rel, False)
        self.assertHarnessFailure(result, output)
        self.assertIn("invalid JSON", output)

    def test_non_object_schema_root_is_harness_failure(self) -> None:
        schema_rel = self.write("list.schema.json", b"[]")
        result, output = self.run_case(NEGATIVE_FIXTURE, schema_rel, False)
        self.assertHarnessFailure(result, output)
        self.assertIn("schema root must be a JSON object", output)

    def test_invalid_utf8_fixture_is_harness_failure(self) -> None:
        rel = self.write("invalid-utf8.json", b'{"id": "\xff\xfe"}')
        result, output = self.run_case(rel, VALID_SCHEMA, False)
        self.assertHarnessFailure(result, output)
        self.assertIn("invalid UTF-8", output)

    def test_unreadable_fixture_is_harness_failure(self) -> None:
        real_open = Path.open

        def deny(self_path, *args, **kwargs):
            if self_path.name == Path(NEGATIVE_FIXTURE).name:
                raise PermissionError(13, "Permission denied")
            return real_open(self_path, *args, **kwargs)

        with mock.patch.object(Path, "open", deny):
            result, output = self.run_case(NEGATIVE_FIXTURE, NEGATIVE_SCHEMA, False)
        self.assertHarnessFailure(result, output)
        self.assertIn("cannot read", output)

    # --- failures raised after preflight ---------------------------------------

    def test_nested_schema_load_failure_is_harness_failure(self) -> None:
        chain_case = next(
            case for case in harness.CASES if case[1] == harness.CHAIN_SCHEMA and case[2]
        )
        with mock.patch.object(
            harness, "ENVELOPE_SCHEMA", "schemas/di-harness-nonexistent.schema.json"
        ):
            result, output = self.run_case(chain_case[0], harness.CHAIN_SCHEMA, False)
        self.assertFalse(result, output)
        self.assertIn("HARNESS-FAIL", output)
        self.assertIn("file does not exist", output)

    def test_validation_machinery_error_is_not_a_rejection(self) -> None:
        def boom(instance, schema, path="$"):
            raise ValueError("injected validation failure")

        buffer = io.StringIO()
        with mock.patch.object(harness, "validate", boom), mock.patch(
            "sys.stdout", buffer
        ):
            result = harness.run_case(NEGATIVE_FIXTURE, NEGATIVE_SCHEMA, False)
        output = buffer.getvalue()
        self.assertFalse(result, output)
        self.assertIn("HARNESS-FAIL", output)
        self.assertIn("injected validation failure", output)

    # --- legitimate cases must keep working ------------------------------------

    def test_valid_positive_case_still_passes(self) -> None:
        result, output = self.run_case(VALID_FIXTURE, VALID_SCHEMA, True)
        self.assertTrue(result, output)
        self.assertIn("PASS", output)
        self.assertTrue(self.validate_calls, "validate() must run for a readable case")

    def test_true_schema_negative_still_passes_as_rejection(self) -> None:
        result, output = self.run_case(NEGATIVE_FIXTURE, NEGATIVE_SCHEMA, False)
        self.assertTrue(result, output)
        self.assertIn("PASS", output)
        self.assertTrue(self.validate_calls)

    def test_true_semantic_negative_still_passes_as_rejection(self) -> None:
        semantic_case = next(
            case
            for case in harness.CASES
            if case[1] == harness.MATRIX_SCHEMA and case[2] is False
        )
        result, output = self.run_case(semantic_case[0], semantic_case[1], False)
        self.assertTrue(result, output)
        self.assertIn("PASS", output)

    def test_all_declared_cases_still_hold(self) -> None:
        buffer = io.StringIO()
        with mock.patch("sys.stdout", buffer):
            outcome = harness.main()
        self.assertEqual(outcome, 0, buffer.getvalue())


if __name__ == "__main__":
    unittest.main()
