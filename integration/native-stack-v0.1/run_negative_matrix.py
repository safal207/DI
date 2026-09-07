#!/usr/bin/env python3
"""Run the native-stack unittest matrix with explicit external checkout roots."""
from __future__ import annotations

import argparse
import importlib.util
import sys
import unittest
from pathlib import Path

HERE = Path(__file__).resolve().parent
TEST_FILE = HERE / "test_native_stack_bridge.py"


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--dif-root", required=True)
    parser.add_argument("--drp-root", required=True)
    parser.add_argument("--tip-root", required=True)
    parser.add_argument("-v", "--verbose", action="store_true")
    args = parser.parse_args()

    spec = importlib.util.spec_from_file_location("native_stack_negative_tests", TEST_FILE)
    if spec is None or spec.loader is None:
        print(f"cannot import {TEST_FILE}", file=sys.stderr)
        return 2
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)

    # The test class deliberately parses these values in setUpClass so the same
    # tests can also be embedded by another unittest runner without global state.
    sys.argv = [
        str(TEST_FILE),
        "--dif-root", args.dif_root,
        "--drp-root", args.drp_root,
        "--tip-root", args.tip_root,
    ]
    suite = unittest.defaultTestLoader.loadTestsFromModule(module)
    result = unittest.TextTestRunner(verbosity=2 if args.verbose else 1).run(suite)
    return 0 if result.wasSuccessful() else 1


if __name__ == "__main__":
    raise SystemExit(main())
