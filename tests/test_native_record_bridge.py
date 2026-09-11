"""Adversarial regressions for the pinned native-record bridge.

The repository-wide DI suite intentionally has no cross-repository checkout or
jsonschema dependency. These tests therefore activate only when the dedicated
native-bridge workflow supplies the three pinned repository roots.
"""

from __future__ import annotations

import hashlib
import importlib.util
import json
import os
from pathlib import Path
import shutil
import tempfile
import unittest


ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "validate_native_record_bridge.py"
bridge = None


class NativeRecordBridgeTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        required = ("DIF_ROOT", "DRP_ROOT", "TIP_ROOT")
        missing = [name for name in required if not os.environ.get(name)]
        if missing:
            raise unittest.SkipTest(
                "native bridge roots are provided only by the dedicated workflow: "
                + ", ".join(missing)
            )
        try:
            import jsonschema  # noqa: F401
        except ImportError as exc:
            raise unittest.SkipTest(
                "jsonschema is an opt-in dependency installed by the native bridge workflow"
            ) from exc

        global bridge
        spec = importlib.util.spec_from_file_location("native_bridge", SCRIPT)
        if spec is None or spec.loader is None:
            raise RuntimeError(f"cannot load {SCRIPT}")
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        bridge = module

        cls.dif_root = Path(os.environ["DIF_ROOT"]).resolve()
        cls.drp_root = Path(os.environ["DRP_ROOT"]).resolve()
        cls.tip_root = Path(os.environ["TIP_ROOT"]).resolve()
        cls.source_bridge = ROOT / "integration" / "native-record-bridge"

    def make_case(self) -> tuple[tempfile.TemporaryDirectory[str], Path]:
        temp = tempfile.TemporaryDirectory()
        target = Path(temp.name) / "native-record-bridge"
        shutil.copytree(self.source_bridge, target)
        return temp, target

    @staticmethod
    def read_json(path: Path):
        return json.loads(path.read_text(encoding="utf-8"))

    @staticmethod
    def write_json(path: Path, value) -> None:
        path.write_text(json.dumps(value, indent=2) + "\n", encoding="utf-8")

    def update_digest(self, case_root: Path, name: str) -> None:
        manifest_path = case_root / "manifest.json"
        manifest = self.read_json(manifest_path)
        record_path = case_root / manifest["records"][name]["path"]
        manifest["records"][name]["sha256"] = hashlib.sha256(record_path.read_bytes()).hexdigest()
        self.write_json(manifest_path, manifest)

    def validate(self, case_root: Path):
        return bridge.validate_bridge(
            case_root / "manifest.json",
            dif_root=self.dif_root,
            di_root=ROOT,
            drp_root=self.drp_root,
            tip_root=self.tip_root,
        )

    def assert_bridge_error(self, expected_code: str, case_root: Path) -> None:
        with self.assertRaises(bridge.BridgeError) as caught:
            self.validate(case_root)
        self.assertEqual(caught.exception.code, expected_code, caught.exception.detail)

    def test_valid_native_bridge_passes_with_explicit_boundaries(self) -> None:
        report = self.validate(self.source_bridge)
        self.assertEqual(report["status"], "PASS")
        self.assertEqual(report["record_validity"]["drp"], "native_cli")
        self.assertEqual(report["record_validity"]["tip"], "native_cli")
        self.assertEqual(report["record_validity"]["dif"], "schema_only")
        self.assertEqual(report["evidence_authenticity"]["status"], "NOT_EVALUATED")
        self.assertEqual(report["execution_authority"]["status"], "NOT_GRANTED")

    def test_changed_body_with_same_id_and_stale_digest_is_rejected(self) -> None:
        temp, case = self.make_case()
        self.addCleanup(temp.cleanup)
        path = case / "records" / "dif-confirmed-intent.json"
        record = self.read_json(path)
        record["statement"] += " silently changed"
        self.write_json(path, record)
        self.assert_bridge_error("record_digest_mismatch", case)

    def test_false_human_confirmation_is_rejected_even_with_fresh_digest(self) -> None:
        temp, case = self.make_case()
        self.addCleanup(temp.cleanup)
        path = case / "records" / "dif-confirmed-intent.json"
        record = self.read_json(path)
        record["confirmedByHuman"] = False
        self.write_json(path, record)
        self.update_digest(case, "dif")
        self.assert_bridge_error("dif_record_invalid", case)

    def test_missing_human_confirmation_is_rejected_even_with_fresh_digest(self) -> None:
        temp, case = self.make_case()
        self.addCleanup(temp.cleanup)
        path = case / "records" / "dif-confirmed-intent.json"
        record = self.read_json(path)
        del record["confirmedByHuman"]
        self.write_json(path, record)
        self.update_digest(case, "dif")
        self.assert_bridge_error("dif_record_invalid", case)

    def test_missing_original_record_is_rejected(self) -> None:
        temp, case = self.make_case()
        self.addCleanup(temp.cleanup)
        (case / "records" / "drp-record.json").unlink()
        self.assert_bridge_error("missing_original_record", case)

    def test_drp_status_is_not_mechanically_mapped_from_di_permission(self) -> None:
        temp, case = self.make_case()
        self.addCleanup(temp.cleanup)
        path = case / "records" / "drp-record.json"
        record = self.read_json(path)
        record["status"] = "proposed"
        self.write_json(path, record)
        self.update_digest(case, "drp")
        self.assert_bridge_error("unsupported_status_mapping", case)

    def test_mismatched_cross_record_reference_is_rejected(self) -> None:
        temp, case = self.make_case()
        self.addCleanup(temp.cleanup)
        path = case / "records" / "drp-record.json"
        record = self.read_json(path)
        record["metadata"]["source_di_check_id"] = "di.payment-recovery.WRONG"
        self.write_json(path, record)
        self.update_digest(case, "drp")
        self.assert_bridge_error("reference_mismatch", case)

    def test_tip_cannot_rephrase_selected_di_conditions(self) -> None:
        temp, case = self.make_case()
        self.addCleanup(temp.cleanup)
        path = case / "records" / "tip-record.json"
        record = self.read_json(path)
        record["state"]["constraints"][1] = (
            "Do not create a fresh payment mutation while the prior commit state is unknown"
        )
        self.write_json(path, record)
        self.update_digest(case, "tip")
        self.assert_bridge_error("reference_mismatch", case)

    def test_unobserved_tip_next_state_cannot_close_bridge(self) -> None:
        temp, case = self.make_case()
        self.addCleanup(temp.cleanup)
        path = case / "records" / "tip-record.json"
        record = self.read_json(path)
        record["review"]["next_state"] = "UNOBSERVED"
        self.write_json(path, record)
        self.update_digest(case, "tip")
        self.assert_bridge_error("unobserved_next_state", case)

    def test_repository_version_mismatch_is_rejected_before_handoff_claims(self) -> None:
        temp, case = self.make_case()
        self.addCleanup(temp.cleanup)
        path = case / "manifest.json"
        manifest = self.read_json(path)
        manifest["repositories"]["dif"]["commit"] = "0" * 40
        self.write_json(path, manifest)
        self.assert_bridge_error("repo_version_mismatch", case)


if __name__ == "__main__":
    unittest.main()
