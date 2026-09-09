#!/usr/bin/env python3
"""Extra integrity regressions for the native-record bridge trust boundary."""

from __future__ import annotations

import importlib.util
import json
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest

REPO_ROOT = Path(__file__).resolve().parents[1]
SCRIPT_PATH = REPO_ROOT / "scripts" / "validate-native-record-bridge.py"
BASE_BRIDGE_DIR = REPO_ROOT / "integration" / "native-record-bridge" / "v0.1"


def _load_actual_module():
    spec = importlib.util.spec_from_file_location("native_record_bridge_integrity", SCRIPT_PATH)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


bridge = _load_actual_module()


class NativeRecordBridgeIntegrityTest(unittest.TestCase):
    def setUp(self) -> None:
        self._tmp = tempfile.TemporaryDirectory(prefix="native-record-bridge-integrity-")
        self.tmp = Path(self._tmp.name)
        self.addCleanup(self._tmp.cleanup)
        self.case = self.tmp / "v0.1"
        shutil.copytree(BASE_BRIDGE_DIR, self.case)

    def test_non_finite_bridge_json_is_a_harness_failure(self) -> None:
        path = self.case / "records" / "dif-confirmed-intent.json"
        text = path.read_text(encoding="utf-8")
        self.assertIn('"version": 1', text)
        path.write_text(text.replace('"version": 1', '"version": 1e309', 1), encoding="utf-8")

        with self.assertRaises(bridge.BridgeHarnessError) as caught:
            bridge.validate_bridge(self.case, root=REPO_ROOT, upstream_root=None)
        self.assertIn("not finite", str(caught.exception))

    def test_dirty_upstream_is_rejected_even_when_commit_and_tree_match(self) -> None:
        upstream = self.tmp / "upstream"
        upstream.mkdir()
        manifest = json.loads((self.case / "manifest.json").read_text(encoding="utf-8"))

        for key in ("dif", "drp", "tip"):
            checkout = manifest["upstreams"][key]["checkout_dir"]
            repo = upstream / checkout
            repo.mkdir()
            subprocess.run(["git", "init", "-q"], cwd=repo, check=True)
            subprocess.run(["git", "config", "user.email", "bridge@example.invalid"], cwd=repo, check=True)
            subprocess.run(["git", "config", "user.name", "Bridge Test"], cwd=repo, check=True)
            (repo / "tracked.txt").write_text(key, encoding="utf-8")
            subprocess.run(["git", "add", "tracked.txt"], cwd=repo, check=True)
            subprocess.run(["git", "commit", "-qm", "pinned"], cwd=repo, check=True)
            manifest["upstreams"][key]["commit_sha"] = subprocess.check_output(
                ["git", "rev-parse", "HEAD"], cwd=repo, text=True
            ).strip()
            manifest["upstreams"][key]["tree_sha"] = subprocess.check_output(
                ["git", "rev-parse", "HEAD^{tree}"], cwd=repo, text=True
            ).strip()

        # Same HEAD/tree as the manifest, but native code could now be modified.
        (upstream / "DRP" / "untracked-validator.py").write_text(
            "raise SystemExit('modified native checkout')\n", encoding="utf-8"
        )

        result = bridge.verify_upstream_pins(manifest, upstream)
        self.assertEqual(result["status"], "fail", result)
        self.assertTrue(
            any("drp upstream checkout is dirty" in error for error in result["errors"]),
            result,
        )
        self.assertEqual(result["observed"]["drp"]["working_tree"], "dirty")
        self.assertEqual(result["observed"]["dif"]["working_tree"], "clean")
        self.assertEqual(result["observed"]["tip"]["working_tree"], "clean")


if __name__ == "__main__":
    unittest.main()
