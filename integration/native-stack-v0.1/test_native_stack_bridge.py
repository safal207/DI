#!/usr/bin/env python3
"""Negative matrix for the opt-in native-stack bridge.

Each mutation asserts its precondition, changes one logical boundary, updates
that file's manifest hash unless the hash itself is under test, and requires a
specific error fragment. A generic crash never counts as a successful negative.
"""
from __future__ import annotations

import argparse
import copy
import hashlib
import json
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

BRIDGE = Path(__file__).resolve().parent
VALIDATOR = BRIDGE / "validate_native_stack.py"


class NativeStackBridgeTests(unittest.TestCase):
    roots: dict[str, Path]

    @classmethod
    def setUpClass(cls) -> None:
        parser = argparse.ArgumentParser(add_help=False)
        parser.add_argument("--dif-root", required=True)
        parser.add_argument("--drp-root", required=True)
        parser.add_argument("--tip-root", required=True)
        args, remaining = parser.parse_known_args()
        cls.roots = {
            "dif": Path(args.dif_root).resolve(),
            "drp": Path(args.drp_root).resolve(),
            "tip": Path(args.tip_root).resolve(),
        }
        sys.argv = [sys.argv[0], *remaining]

    def invoke(self, bridge: Path) -> subprocess.CompletedProcess[str]:
        return subprocess.run(
            [
                sys.executable,
                str(VALIDATOR),
                "--bridge-dir",
                str(bridge),
                "--dif-root",
                str(self.roots["dif"]),
                "--drp-root",
                str(self.roots["drp"]),
                "--tip-root",
                str(self.roots["tip"]),
            ],
            capture_output=True,
            text=True,
        )

    def copy_bridge(self) -> tuple[tempfile.TemporaryDirectory, Path]:
        tmp = tempfile.TemporaryDirectory(prefix="native-stack-negative-")
        target = Path(tmp.name) / "bridge"
        shutil.copytree(BRIDGE, target, ignore=shutil.ignore_patterns("__pycache__"))
        return tmp, target

    def load(self, bridge: Path, rel: str):
        return json.loads((bridge / rel).read_text(encoding="utf-8"))

    def save(self, bridge: Path, rel: str, value) -> None:
        (bridge / rel).write_text(json.dumps(value, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")

    def refresh_hash(self, bridge: Path, rel: str) -> None:
        manifest = self.load(bridge, "manifest.json")
        self.assertIn(rel, manifest["body_hashes"], f"precondition: {rel} must be hash-bound")
        manifest["body_hashes"][rel] = hashlib.sha256((bridge / rel).read_bytes()).hexdigest()
        self.save(bridge, "manifest.json", manifest)

    def assert_rejected(self, mutate, expected: str) -> None:
        tmp, bridge = self.copy_bridge()
        self.addCleanup(tmp.cleanup)
        mutate(bridge)
        run = self.invoke(bridge)
        output = run.stdout + run.stderr
        self.assertNotEqual(run.returncode, 0, f"mutation unexpectedly passed:\n{output}")
        self.assertIn(expected, output, f"wrong rejection reason (rc={run.returncode}):\n{output}")
        self.assertNotIn("Traceback", output, f"generic crash is not a valid rejection:\n{output}")

    def test_00_baseline_passes(self) -> None:
        run = self.invoke(BRIDGE)
        self.assertEqual(run.returncode, 0, run.stdout + run.stderr)
        self.assertIn("PASS", run.stdout)
        self.assertIn("evidence_authenticity: not_verified", run.stdout)
        self.assertIn("execution_authority: not_claimed", run.stdout)

    def test_dif_false_confirmation_rejected(self) -> None:
        def mutate(b: Path) -> None:
            rel = "records/confirmed-intent.json"
            data = self.load(b, rel)
            self.assertIs(data["confirmedByHuman"], True)
            data["confirmedByHuman"] = False
            self.save(b, rel, data)
            self.refresh_hash(b, rel)
        self.assert_rejected(mutate, "confirmedByHuman must be literally true")

    def test_dif_missing_confirmation_rejected(self) -> None:
        def mutate(b: Path) -> None:
            rel = "records/confirmed-intent.json"
            data = self.load(b, rel)
            self.assertIn("confirmedByHuman", data)
            del data["confirmedByHuman"]
            self.save(b, rel, data)
            self.refresh_hash(b, rel)
        self.assert_rejected(mutate, "confirmedByHuman")

    def test_same_id_changed_body_with_stale_hash_rejected(self) -> None:
        def mutate(b: Path) -> None:
            rel = "records/confirmed-intent.json"
            data = self.load(b, rel)
            original_id = data["id"]
            self.assertTrue(data["sourceSignalIds"])
            data["sourceSignalIds"][0] += ".mutated"
            self.assertEqual(data["id"], original_id)
            self.save(b, rel, data)
            # Deliberately do NOT refresh the manifest hash.
        self.assert_rejected(mutate, "body hash mismatch for records/confirmed-intent.json")

    def test_missing_native_record_rejected(self) -> None:
        def mutate(b: Path) -> None:
            path = b / "records/drp-record.json"
            self.assertTrue(path.is_file())
            path.unlink()
        self.assert_rejected(mutate, "missing native record file drp-record.json")

    def test_external_checkout_commit_mismatch_rejected(self) -> None:
        def mutate(b: Path) -> None:
            manifest = self.load(b, "manifest.json")
            original = manifest["external_repositories"]["dif"]["commit"]
            self.assertNotEqual(original, "0" * 40)
            manifest["external_repositories"]["dif"]["commit"] = "0" * 40
            self.save(b, "manifest.json", manifest)
        self.assert_rejected(mutate, "external checkout commit mismatch")

    def test_drp_invalid_status_rejected_by_native_validator(self) -> None:
        def mutate(b: Path) -> None:
            rel = "records/drp-record.json"
            data = self.load(b, rel)
            self.assertEqual(data["status"], "complete")
            data["status"] = "committed"
            self.save(b, rel, data)
            self.refresh_hash(b, rel)
        self.assert_rejected(mutate, "'status' must be one of")

    def test_drp_valid_but_unsupported_status_rejected_by_bridge(self) -> None:
        def mutate(b: Path) -> None:
            rel = "records/drp-record.json"
            data = self.load(b, rel)
            self.assertEqual(data["status"], "complete")
            data["status"] = "proposed"
            self.save(b, rel, data)
            self.refresh_hash(b, rel)
        self.assert_rejected(mutate, "unsupported DRP status for this bridge")

    def test_drp_missing_required_field_rejected(self) -> None:
        def mutate(b: Path) -> None:
            rel = "records/drp-record.json"
            data = self.load(b, rel)
            self.assertIn("context", data)
            del data["context"]
            self.save(b, rel, data)
            self.refresh_hash(b, rel)
        self.assert_rejected(mutate, "required field 'context' is missing")

    def test_tip_nan_confidence_rejected_by_pinned_tip(self) -> None:
        def mutate(b: Path) -> None:
            rel = "records/tip-record.tip.json"
            path = b / rel
            data = self.load(b, rel)
            self.assertEqual(data["cause"]["confidence"], 0.82)
            text = path.read_text(encoding="utf-8")
            needle = '"confidence": 0.82'
            self.assertEqual(text.count(needle), 1)
            path.write_text(text.replace(needle, '"confidence": NaN'), encoding="utf-8")
            self.refresh_hash(b, rel)
        self.assert_rejected(mutate, "non-standard JSON literal 'NaN'")

    def test_reviewed_tip_missing_evidence_rejected_by_stricter_bridge(self) -> None:
        def mutate(b: Path) -> None:
            rel = "records/tip-record.tip.json"
            data = self.load(b, rel)
            self.assertTrue(data["review"]["evidence"])
            del data["review"]["evidence"]
            self.save(b, rel, data)
            self.refresh_hash(b, rel)
        self.assert_rejected(mutate, "reviewed projection requires nonempty TIP review evidence")

    def test_reviewed_tip_missing_next_state_rejected_by_stricter_bridge(self) -> None:
        def mutate(b: Path) -> None:
            rel = "records/tip-record.tip.json"
            data = self.load(b, rel)
            self.assertEqual(data["review"]["next_state"], "RECOVERY_CONFIRMED")
            del data["review"]["next_state"]
            self.save(b, rel, data)
            self.refresh_hash(b, rel)
        self.assert_rejected(mutate, "reviewed projection requires a concrete TIP review next_state")

    def test_drp_to_tip_bridge_reference_mismatch_rejected(self) -> None:
        def mutate(b: Path) -> None:
            rel = "projection-envelope.json"
            data = self.load(b, rel)
            self.assertEqual(data["tip"]["decision_record_id"], data["drp"]["record_id"])
            data["tip"]["decision_record_id"] = "drp.payment-recovery.native.WRONG"
            self.save(b, rel, data)
            self.refresh_hash(b, rel)
        self.assert_rejected(mutate, "projection TIP decision reference must equal canonical DRP record_id")

    def test_projection_dif_identity_mismatch_rejected(self) -> None:
        def mutate(b: Path) -> None:
            rel = "projection-envelope.json"
            data = self.load(b, rel)
            self.assertEqual(data["dif"]["intent_id"], data["di"]["intent_id"])
            data["dif"]["intent_id"] = "dif.intent.payment-recovery.native.WRONG"
            data["di"]["intent_id"] = "dif.intent.payment-recovery.native.WRONG"
            self.save(b, rel, data)
            self.refresh_hash(b, rel)
        self.assert_rejected(mutate, "projection.dif.intent_id must match canonical DIF id")

    def test_projection_tip_identity_mismatch_rejected(self) -> None:
        def mutate(b: Path) -> None:
            rel = "projection-envelope.json"
            data = self.load(b, rel)
            self.assertEqual(data["tip"]["transition_id"], data["review"]["transition_id"])
            data["tip"]["transition_id"] = "tip.payment-recovery.native.WRONG"
            data["review"]["transition_id"] = "tip.payment-recovery.native.WRONG"
            self.save(b, rel, data)
            self.refresh_hash(b, rel)
        self.assert_rejected(mutate, "projection.tip.transition_id must match canonical TIP id")

    def test_changed_unobserved_next_state_rejected(self) -> None:
        def mutate(b: Path) -> None:
            rel = "records/tip-record.tip.json"
            data = self.load(b, rel)
            self.assertEqual(data["review"]["next_state"], "RECOVERY_CONFIRMED")
            data["review"]["next_state"] = "RECOVERY_STILL_UNKNOWN"
            self.save(b, rel, data)
            self.refresh_hash(b, rel)
        self.assert_rejected(mutate, "TIP review.next_state must match projection review.next_state")


if __name__ == "__main__":
    unittest.main()
