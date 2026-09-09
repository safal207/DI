from __future__ import annotations

import hashlib
import importlib.util
import json
import shutil
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "validate-native-stack-bridge.py"
BUNDLE = ROOT / "integrations" / "native-stack-v0.1"


def load_bridge():
    spec = importlib.util.spec_from_file_location("native_stack_bridge_test_target", SCRIPT)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


bridge = load_bridge()


class NativeStackBridgeTest(unittest.TestCase):
    def setUp(self) -> None:
        self.tmp = tempfile.TemporaryDirectory(prefix="native-stack-bridge-")
        self.addCleanup(self.tmp.cleanup)
        self.bundle = Path(self.tmp.name) / "bundle"
        shutil.copytree(BUNDLE, self.bundle)

    def _manifest(self) -> dict:
        return json.loads((self.bundle / "manifest.json").read_text(encoding="utf-8"))

    def _write_manifest(self, manifest: dict) -> None:
        (self.bundle / "manifest.json").write_text(
            json.dumps(manifest, indent=2, ensure_ascii=False) + "\n",
            encoding="utf-8",
        )

    def _mutate_json(self, key: str, mutate) -> None:
        manifest = self._manifest()
        entry = manifest["artifacts"][key]
        path = self.bundle / entry["path"]
        data = json.loads(path.read_text(encoding="utf-8"))
        mutate(data)
        path.write_text(
            json.dumps(data, indent=2, ensure_ascii=False) + "\n",
            encoding="utf-8",
        )
        entry["sha256"] = hashlib.sha256(path.read_bytes()).hexdigest()
        self._write_manifest(manifest)

    def _derived(self):
        manifest = bridge.load_json(self.bundle / "manifest.json")
        paths = bridge.artifact_paths(self.bundle, manifest)
        values = {name: bridge.load_json(path) for name, path in paths.items()}
        derived = bridge.derive(
            manifest, values["dif"], values["di"], values["drp"], values["tip"]
        )
        return derived, values["expected_envelope"]

    def test_baseline_projection_matches_committed_expected_envelope(self) -> None:
        derived, expected = self._derived()
        self.assertEqual(derived, expected)

    def test_changed_body_with_same_id_is_rejected_by_hash(self) -> None:
        manifest = self._manifest()
        path = self.bundle / manifest["artifacts"]["dif"]["path"]
        data = json.loads(path.read_text(encoding="utf-8"))
        original_id = data["id"]
        data["statement"] += " altered"
        self.assertEqual(data["id"], original_id)
        path.write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")
        with self.assertRaises(bridge.BridgeError) as ctx:
            bridge.artifact_paths(self.bundle, manifest)
        self.assertIn("sha256 mismatch", str(ctx.exception))

    def test_false_confirmation_is_rejected_even_with_matching_hash(self) -> None:
        self._mutate_json("dif", lambda data: data.__setitem__("confirmedByHuman", False))
        with self.assertRaises(bridge.BridgeError) as ctx:
            self._derived()
        self.assertIn("confirmedByHuman", str(ctx.exception))

    def test_unsupported_drp_status_is_not_inferred_as_commitment(self) -> None:
        self._mutate_json("drp", lambda data: data.__setitem__("status", "proposed"))
        with self.assertRaises(bridge.BridgeError) as ctx:
            self._derived()
        self.assertIn("unsupported DRP status mapping", str(ctx.exception))

    def test_drp_metadata_reference_mismatch_is_rejected(self) -> None:
        def mutate(data):
            data["metadata"]["native_stack_bridge_v0_1"]["di_check_id"] = "wrong-di-id"

        self._mutate_json("drp", mutate)
        with self.assertRaises(bridge.BridgeError) as ctx:
            self._derived()
        self.assertIn("DRP metadata DI check id", str(ctx.exception))

    def test_tip_unobserved_next_state_is_rejected(self) -> None:
        self._mutate_json(
            "tip", lambda data: data["review"].__setitem__("next_state", "UNOBSERVED")
        )
        with self.assertRaises(bridge.BridgeError) as ctx:
            self._derived()
        self.assertIn("concrete observed state", str(ctx.exception))

    def test_tip_state_must_match_transition_from(self) -> None:
        self._mutate_json(
            "tip", lambda data: data["transition"].__setitem__("from", "different_state")
        )
        with self.assertRaises(bridge.BridgeError) as ctx:
            self._derived()
        self.assertIn("transition.from", str(ctx.exception))

    def test_selected_path_must_be_feasible(self) -> None:
        manifest = self._manifest()
        manifest["links"]["di_to_drp"]["selected_path"] = "blind retry"
        self._write_manifest(manifest)
        with self.assertRaises(bridge.BridgeError) as ctx:
            self._derived()
        self.assertIn("was not evaluated as feasible", str(ctx.exception))

    def test_expected_projection_drift_is_detected(self) -> None:
        self._mutate_json(
            "expected_envelope",
            lambda data: data["review"].__setitem__("next_state", "WRONG_STATE"),
        )
        derived, expected = self._derived()
        self.assertNotEqual(derived, expected)

    def test_missing_native_artifact_is_rejected(self) -> None:
        manifest = self._manifest()
        path = self.bundle / manifest["artifacts"]["drp"]["path"]
        path.unlink()
        with self.assertRaises(bridge.BridgeError) as ctx:
            bridge.artifact_paths(self.bundle, manifest)
        self.assertIn("artifact is missing", str(ctx.exception))


if __name__ == "__main__":
    unittest.main()
