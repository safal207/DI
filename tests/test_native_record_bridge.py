#!/usr/bin/env python3
"""Regression tests for the pinned native-record bridge.

The tests import the actual bridge implementation. They mutate temporary copies
of the committed full records; no tracked fixture is rewritten.
"""

from __future__ import annotations

import hashlib
import importlib.util
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest
from unittest import mock

REPO_ROOT = Path(__file__).resolve().parents[1]
SCRIPT_PATH = REPO_ROOT / "scripts" / "validate-native-record-bridge.py"
BASE_BRIDGE_DIR = REPO_ROOT / "integration" / "native-record-bridge" / "v0.1"


def _load_actual_module():
    spec = importlib.util.spec_from_file_location("native_record_bridge", SCRIPT_PATH)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


bridge = _load_actual_module()
import native_bridge_io  # noqa: E402  (loaded from the actual scripts directory above)


class NativeRecordBridgeTest(unittest.TestCase):
    def setUp(self) -> None:
        self._tmp = tempfile.TemporaryDirectory(prefix="native-record-bridge-")
        self.tmp = Path(self._tmp.name)
        self.addCleanup(self._tmp.cleanup)
        self.case = self.tmp / "v0.1"
        shutil.copytree(BASE_BRIDGE_DIR, self.case)

    def _manifest(self) -> dict:
        return json.loads((self.case / "manifest.json").read_text(encoding="utf-8"))

    def _write_manifest(self, manifest: dict) -> None:
        (self.case / "manifest.json").write_text(
            json.dumps(manifest, ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8",
        )

    def _record_path(self, key: str) -> Path:
        manifest = self._manifest()
        return self.case / manifest["artifacts"][key]["path"]

    def _mutate(self, key: str, mutate, *, refresh_hash: bool = True) -> None:
        path = self._record_path(key)
        data = json.loads(path.read_text(encoding="utf-8"))
        mutate(data)
        path.write_text(
            json.dumps(data, ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8",
        )
        if refresh_hash:
            manifest = self._manifest()
            manifest["artifacts"][key]["sha256"] = hashlib.sha256(
                path.read_bytes()
            ).hexdigest()
            self._write_manifest(manifest)

    def _validate(self) -> dict:
        return bridge.validate_bridge(self.case, root=REPO_ROOT, upstream_root=None)

    def test_baseline_full_bridge_passes_locally(self) -> None:
        report = self._validate()
        self.assertEqual(report["status"], "PASS", report)
        self.assertEqual(report["body_binding"]["status"], "pass")
        self.assertEqual(report["cross_record_consistency"]["status"], "pass")
        self.assertEqual(report["projection_consistency"]["status"], "pass")
        self.assertEqual(report["native_record_validity"]["di"]["status"], "pass")
        self.assertEqual(report["native_record_validity"]["dif"]["status"], "not_evaluated")
        self.assertEqual(report["evidence_authenticity"]["status"], "not_evaluated")
        self.assertEqual(report["execution_authority"]["status"], "not_evaluated")

    def test_missing_original_record_is_harness_failure(self) -> None:
        self._record_path("drp").unlink()
        with self.assertRaises(bridge.BridgeHarnessError):
            self._validate()

    def test_same_id_body_substitution_is_caught_by_stale_hash_first(self) -> None:
        self._mutate(
            "dif",
            lambda record: record.__setitem__(
                "statement", record["statement"] + " Changed with the same id."
            ),
            refresh_hash=False,
        )
        report = self._validate()
        self.assertEqual(report["status"], "FAIL")
        self.assertEqual(report["body_binding"]["status"], "fail")
        self.assertEqual(
            report["cross_record_consistency"]["status"], "not_evaluated",
            "body binding must fail before link/content checks are trusted",
        )

    def test_false_human_confirmation_fails_after_body_hash_is_refreshed(self) -> None:
        self._mutate("dif", lambda record: record.__setitem__("confirmedByHuman", False))
        report = self._validate()
        self.assertEqual(report["status"], "FAIL")
        self.assertIn(
            "DIF confirmedByHuman must be literal true",
            report["cross_record_consistency"]["errors"],
        )

    def test_di_intent_text_mismatch_fails(self) -> None:
        self._mutate(
            "di",
            lambda record: record.__setitem__("inferred_intent", "A different inferred intent."),
        )
        report = self._validate()
        self.assertEqual(report["status"], "FAIL")
        self.assertIn(
            "DI inferred_intent must exactly equal DIF statement",
            report["cross_record_consistency"]["errors"],
        )

    def test_unsupported_drp_status_mapping_fails(self) -> None:
        self._mutate("drp", lambda record: record.__setitem__("status", "proposed"))
        report = self._validate()
        self.assertEqual(report["status"], "FAIL")
        self.assertTrue(any(
            "unsupported by this bridge" in error
            for error in report["cross_record_consistency"]["errors"]
        ))

    def test_drp_decision_drift_fails(self) -> None:
        self._mutate(
            "drp",
            lambda record: record.__setitem__("decision", "Blindly submit another payment mutation."),
        )
        report = self._validate()
        self.assertEqual(report["status"], "FAIL")
        self.assertIn(
            "DRP decision must exactly equal DI recommended_next_step",
            report["cross_record_consistency"]["errors"],
        )

    def test_drp_metadata_identity_mismatch_fails(self) -> None:
        def mutate(record):
            record["metadata"]["di_check_id"] = "di.feasibility.WRONG"
        self._mutate("drp", mutate)
        report = self._validate()
        self.assertEqual(report["status"], "FAIL")
        self.assertIn(
            "DRP metadata.di_check_id must exactly match DI check_id",
            report["cross_record_consistency"]["errors"],
        )

    def test_tip_missing_drp_supporting_signal_fails(self) -> None:
        def mutate(record):
            record["cause"]["supporting_signals"] = [
                item for item in record["cause"]["supporting_signals"]
                if not item.startswith("drp:")
            ]
        self._mutate("tip", mutate)
        report = self._validate()
        self.assertEqual(report["status"], "FAIL")
        self.assertTrue(any(
            "TIP cause.supporting_signals must contain 'drp:" in error
            for error in report["cross_record_consistency"]["errors"]
        ))

    def test_tip_action_drift_fails(self) -> None:
        self._mutate(
            "tip",
            lambda record: record["action"].__setitem__(
                "summary", "Issue a new payment mutation immediately."
            ),
        )
        report = self._validate()
        self.assertEqual(report["status"], "FAIL")
        self.assertIn(
            "TIP action.summary must exactly equal DRP decision",
            report["cross_record_consistency"]["errors"],
        )

    def test_tip_empty_review_evidence_fails(self) -> None:
        self._mutate("tip", lambda record: record["review"].__setitem__("evidence", []))
        report = self._validate()
        self.assertEqual(report["status"], "FAIL")
        self.assertIn(
            "TIP review.evidence must contain at least one reference",
            report["cross_record_consistency"]["errors"],
        )

    def test_tip_unobserved_next_state_fails(self) -> None:
        self._mutate(
            "tip",
            lambda record: record["review"].__setitem__("next_state", "UNOBSERVED"),
        )
        report = self._validate()
        self.assertEqual(report["status"], "FAIL")
        self.assertIn(
            "TIP review.next_state must be a concrete observed state",
            report["cross_record_consistency"]["errors"],
        )

    def test_stale_projection_fails_projection_consistency(self) -> None:
        self._mutate(
            "projection",
            lambda record: record["review"].__setitem__(
                "next_state", "STALE_PROJECTION_STATE"
            ),
            refresh_hash=True,
        )
        report = self._validate()
        self.assertEqual(report["status"], "FAIL")
        self.assertEqual(report["body_binding"]["status"], "pass")
        self.assertEqual(report["cross_record_consistency"]["status"], "pass")
        self.assertEqual(report["projection_consistency"]["status"], "fail")
        self.assertIn(
            "derived projection does not match projection-envelope.json",
            report["projection_consistency"]["errors"],
        )

    def test_validation_subprocess_nonzero_is_native_failure(self) -> None:
        result = bridge._native_command_result(
            "synthetic native validator",
            [sys.executable, "-c", "import sys; print('native failed'); sys.exit(7)"],
            cwd=REPO_ROOT,
        )
        self.assertEqual(result["status"], "fail")
        self.assertEqual(result["returncode"], 7)
        self.assertIn("exited with 7", result["errors"][0])
        self.assertNotIn("HARNESS", json.dumps(result))

    def test_relative_upstream_root_resolves_native_validator_paths_once(self) -> None:
        upstream_abs = self.tmp / "relative-upstream"
        for checkout in ("DIF", "DRP", "TIP"):
            (upstream_abs / checkout).mkdir(parents=True, exist_ok=True)
        upstream_rel = Path(os.path.relpath(upstream_abs, Path.cwd()))
        calls: list[tuple[str, list[str], Path]] = []

        def fake_native(label, argv, *, cwd, env=None):
            calls.append((label, argv, cwd))
            return {
                "status": "pass", "errors": [], "returncode": 0,
                "stdout": "", "stderr": "",
            }

        with mock.patch.object(
            native_bridge_io,
            "verify_upstream_pins",
            return_value={"status": "pass", "errors": [], "observed": {}},
        ), mock.patch.object(
            native_bridge_io,
            "validate_dif_schema",
            return_value={"status": "pass", "errors": []},
        ), mock.patch.object(native_bridge_io, "native_command", side_effect=fake_native):
            native_bridge_io.validate_upstream_native(
                self._manifest(),
                {"dif": {}, "drp": {}, "tip": {}},
                {"drp": self._record_path("drp"), "tip": self._record_path("tip")},
                upstream_rel,
            )

        drp_label, drp_argv, drp_cwd = calls[0]
        self.assertEqual(drp_label, "DRP native validator")
        self.assertTrue(drp_cwd.is_absolute())
        validator_path = Path(drp_argv[1])
        self.assertTrue(validator_path.is_absolute())
        self.assertEqual(validator_path.parent.parent, drp_cwd)
        self.assertNotIn(".upstream/DRP/.upstream/DRP", str(validator_path))

    def test_upstream_pin_mismatch_fails_before_native_validation(self) -> None:
        upstream = self.tmp / "upstream"
        upstream.mkdir()
        manifest = self._manifest()
        for key in ("dif", "drp", "tip"):
            repo = upstream / manifest["upstreams"][key]["checkout_dir"]
            repo.mkdir()
            subprocess.run(["git", "init", "-q"], cwd=repo, check=True)
            subprocess.run(["git", "config", "user.email", "bridge@example.invalid"], cwd=repo, check=True)
            subprocess.run(["git", "config", "user.name", "Bridge Test"], cwd=repo, check=True)
            (repo / "x.txt").write_text(key, encoding="utf-8")
            subprocess.run(["git", "add", "x.txt"], cwd=repo, check=True)
            subprocess.run(["git", "commit", "-qm", "fake"], cwd=repo, check=True)
        pins = bridge.verify_upstream_pins(manifest, upstream)
        self.assertEqual(pins["status"], "fail")
        self.assertTrue(any("commit pin mismatch" in error for error in pins["errors"]))

    def test_manifest_mapping_is_narrow_not_global_equivalence(self) -> None:
        manifest = self._manifest()
        mapping = manifest["status_mapping"]["drp_to_projection"]
        self.assertEqual(mapping["source_status"], "complete")
        self.assertEqual(mapping["projected_status"], "committed")
        self.assertIn(manifest["bridge_id"], mapping["scope"])
        self.assertGreaterEqual(len(mapping["preconditions"]), 5)


if __name__ == "__main__":
    unittest.main()
