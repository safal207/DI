"""Integration regressions exercise actual pinned native validators, not copies."""
import copy
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest import mock

import bridge


class NativeBridgeTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.sources = bridge.Sources()
        cls.example = bridge.loads((bridge.HERE / "example.json").read_text(encoding="utf-8"))

    def setUp(self):
        self.bundle = copy.deepcopy(self.example)

    def rejected(self, axis, fragment):
        report = bridge.validate_bundle(self.bundle, self.sources)
        self.assertEqual(report["status"], "FAIL", report)
        self.assertTrue(any(e["axis"] == axis and fragment in e["message"]
                            for e in report["errors"]), report)
        return report

    def test_complete_bundle_and_all_axes_pass(self):
        report = bridge.validate_bundle(self.bundle, self.sources)
        self.assertEqual(report["status"], "PASS", report)
        self.assertEqual(report["native"], {r: "PASS" for r in bridge.ROLES})
        for axis in ("envelope", "binding", "mapping"):
            self.assertEqual(report[axis], "PASS")
        self.assertEqual(report["execution_authority"], "NOT_EVALUATED")
        self.assertEqual(report["evidence_authenticity"], "NOT_EVALUATED")

    def test_missing_original_is_not_a_valid_bundle(self):
        del self.bundle["records"]["DRP"]
        report = self.rejected("input", "complete native record")
        self.assertEqual(report["native"]["DRP"], "NOT_RUN")

    def test_false_confirmation_is_rejected_natively(self):
        self.bundle["records"]["DIF"]["confirmedByHuman"] = False
        report = self.rejected("native.DIF", "True was expected")
        self.assertEqual(report["mapping"], "NOT_RUN")

    def test_drp_invalid_status_uses_native_validator(self):
        self.bundle["records"]["DRP"]["status"] = "committed"
        self.rejected("native.DRP", "status")

    def test_drp_graph_reference_is_checked(self):
        self.bundle["records"]["DRP"]["parent_record_ids"] = ["missing-parent"]
        self.rejected("native.DRP", "does not resolve")

    def test_native_tip_confidence_bounds_are_checked(self):
        self.bundle["records"]["TIP"]["cause"]["confidence"] = 1.1
        self.rejected("native.TIP", "above maximum")

    def test_nonfinite_programmatic_input_is_rejected(self):
        self.bundle["records"]["TIP"]["cause"]["confidence"] = float("nan")
        self.rejected("input", "Out of range float")

    def test_changed_body_same_id_legacy_envelope_still_passes(self):
        original_id = self.bundle["records"]["DRP"]["record_id"]
        self.bundle["records"]["DRP"]["rationale"] = "A different rationale under the same ID."
        self.assertEqual(self.bundle["records"]["DRP"]["record_id"], original_id)
        self.assertEqual(self.sources.envelope_errors(self.bundle["envelope"]), [])
        self.rejected("binding", "native body digest mismatch: DRP")

    def test_projection_change_with_unchanged_original(self):
        self.bundle["envelope"]["drp"]["decision_summary"] = "A different summary."
        self.assertEqual(self.sources.envelope_errors(self.bundle["envelope"]), [])
        self.rejected("mapping", "differs from native record projection")

    def test_rehashed_body_still_needs_consistent_projection(self):
        self.bundle["records"]["DIF"]["statement"] = "A different user intent."
        self.bundle["sha256"]["DIF"] = bridge.digest(self.bundle["records"]["DIF"])
        self.rejected("mapping", "native intent/request/context mismatch")

    def test_missing_tip_evidence_is_not_synthesized(self):
        del self.bundle["records"]["TIP"]["review"]["evidence"]
        self.rejected("mapping", "nonblank evidence")

    def test_blank_tip_evidence_is_rejected(self):
        self.bundle["records"]["TIP"]["review"]["evidence"] = ["  "]
        self.rejected("mapping", "nonblank evidence")

    def test_unobserved_next_state_is_rejected(self):
        self.bundle["records"]["TIP"]["review"]["next_state"] = "UNOBSERVED"
        self.rejected("mapping", "observed next state")

    def test_complete_drp_does_not_automatically_mean_committed(self):
        del self.bundle["records"]["DRP"]["metadata"]["native_bridge"]["commitment_recorded"]
        self.rejected("mapping", "explicit commitment metadata")

    def test_native_valid_draft_status_is_unsupported_mapping(self):
        self.bundle["records"]["DRP"]["status"] = "draft"
        self.rejected("mapping", "unsupported native status")

    def test_conditional_path_does_not_become_allowed(self):
        self.bundle["records"]["DI"]["feasible_actions"][0]["status"] = "requires_human_review"
        self.rejected("mapping", "conditional or unreviewed paths")

    def test_wrong_native_reference(self):
        self.bundle["records"]["DRP"]["metadata"]["native_bridge"]["intent_id"] = "other-intent"
        self.rejected("mapping", "native commitment reference mismatch")

    def test_date_format_checker_is_active(self):
        self.bundle["records"]["DIF"]["createdAt"] = "not-a-date"
        self.rejected("native.DIF", "date-time")

    def test_malformed_bundle_roots(self):
        for value in (None, [], "text", 1, True):
            with self.subTest(value=value):
                self.bundle = value
                self.rejected("input", "bundle requires")

    def test_duplicate_json_keys_and_nonfinite_tokens(self):
        with self.assertRaisesRegex(bridge.InputError, "duplicate JSON key"):
            bridge.loads('{"profile":"one","profile":"two"}')
        for token in ("NaN", "Infinity", "-Infinity", "1e309", "-1e309"):
            with self.subTest(token=token), self.assertRaisesRegex(bridge.InputError, "non-finite"):
                bridge.loads('{"number":' + token + '}')

    def test_missing_dependency_fails_infrastructure(self):
        with tempfile.TemporaryDirectory() as temporary:
            with self.assertRaisesRegex(bridge.SourceError, "pinned Git source unavailable"):
                bridge.Sources(dependency_root=Path(temporary))

    def test_dirty_pinned_source_is_not_loaded(self):
        path = bridge.ROOT / ".native" / "DIF" / "schemas/confirmed-intent.schema.json"
        original = Path.read_bytes
        def changed(p):
            return b"{}" if p == path else original(p)
        with mock.patch.object(Path, "read_bytes", changed):
            with self.assertRaisesRegex(bridge.SourceError, "dirty pinned source"):
                bridge.Sources()

    def test_cli_success_and_bad_input_exit_codes(self):
        with tempfile.TemporaryDirectory() as temporary:
            path = Path(temporary) / "input.json"
            for text, expected in ((json.dumps(self.example), 0), ('{"a":1,"a":2}', 1), ('[]', 1)):
                with self.subTest(expected=expected, text=text[:20]):
                    path.write_text(text, encoding="utf-8")
                    result = subprocess.run([sys.executable, str(bridge.HERE / "bridge.py"), str(path)],
                                            capture_output=True, text=True, timeout=30)
                    self.assertEqual(result.returncode, expected, result.stdout + result.stderr)
                    self.assertNotIn("Traceback", result.stdout + result.stderr)
                    report = json.loads(result.stdout)
                    self.assertEqual(report["status"], "PASS" if expected == 0 else "FAIL")


if __name__ == "__main__":
    unittest.main()
