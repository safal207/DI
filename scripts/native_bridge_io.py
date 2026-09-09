"""I/O, pin and native-validator helpers for the DI native-record bridge."""

from __future__ import annotations

import hashlib
import json
import math
import os
from pathlib import Path
import subprocess
import sys
from typing import Any


class BridgeHarnessError(Exception):
    """The bridge could not be evaluated (missing/corrupt inputs or tooling)."""


def _reject_constant(token: str) -> Any:
    raise ValueError(f"non-standard JSON literal {token!r} is not accepted")


def _parse_float(token: str) -> float:
    value = float(token)
    if not math.isfinite(value):
        raise ValueError(f"numeric literal {token!r} is not finite")
    return value


def load_json(path: Path) -> Any:
    if not path.exists():
        raise BridgeHarnessError(f"file does not exist: {path}")
    if not path.is_file():
        raise BridgeHarnessError(f"path is not a file: {path}")
    try:
        text = path.read_text(encoding="utf-8")
    except UnicodeDecodeError as exc:
        raise BridgeHarnessError(f"invalid UTF-8 in {path}: {exc}") from exc
    except OSError as exc:
        raise BridgeHarnessError(f"cannot read {path}: {exc}") from exc
    try:
        return json.loads(
            text,
            parse_constant=_reject_constant,
            parse_float=_parse_float,
        )
    except (json.JSONDecodeError, ValueError) as exc:
        raise BridgeHarnessError(f"invalid JSON in {path}: {exc}") from exc


def canonical_json_bytes(value: Any) -> bytes:
    return json.dumps(
        value, ensure_ascii=False, sort_keys=True, separators=(",", ":")
    ).encode("utf-8")


def sha256_file(path: Path) -> str:
    try:
        return hashlib.sha256(path.read_bytes()).hexdigest()
    except OSError as exc:
        raise BridgeHarnessError(f"cannot hash {path}: {exc}") from exc


def artifact_path(bridge_dir: Path, manifest: dict[str, Any], key: str) -> Path:
    artifacts = manifest.get("artifacts")
    if not isinstance(artifacts, dict) or key not in artifacts:
        raise BridgeHarnessError(f"manifest.artifacts.{key} is missing")
    entry = artifacts[key]
    if not isinstance(entry, dict) or not isinstance(entry.get("path"), str):
        raise BridgeHarnessError(f"manifest.artifacts.{key}.path must be a string")
    candidate = (bridge_dir / entry["path"]).resolve()
    root = bridge_dir.resolve()
    try:
        candidate.relative_to(root)
    except ValueError as exc:
        raise BridgeHarnessError(
            f"artifact path escapes bridge directory: {entry['path']}"
        ) from exc
    return candidate


def load_bundle(
    bridge_dir: Path,
) -> tuple[dict[str, Any], dict[str, Any], dict[str, Path]]:
    manifest = load_json(bridge_dir / "manifest.json")
    if not isinstance(manifest, dict):
        raise BridgeHarnessError("manifest root must be an object")
    records: dict[str, Any] = {}
    paths: dict[str, Path] = {}
    for key in ("dif", "di", "drp", "tip", "projection"):
        path = artifact_path(bridge_dir, manifest, key)
        data = load_json(path)
        if not isinstance(data, dict):
            raise BridgeHarnessError(f"{key} artifact root must be an object")
        paths[key], records[key] = path, data
    return manifest, records, paths


def section(errors: list[str], **extra: Any) -> dict[str, Any]:
    return {"status": "pass" if not errors else "fail", "errors": errors, **extra}


def verify_body_binding(
    manifest: dict[str, Any], paths: dict[str, Path]
) -> dict[str, Any]:
    errors: list[str] = []
    observed: dict[str, str] = {}
    for key in ("dif", "di", "drp", "tip", "projection"):
        expected = manifest["artifacts"][key].get("sha256")
        if not isinstance(expected, str) or len(expected) != 64:
            errors.append(
                f"manifest.artifacts.{key}.sha256 must be a 64-character hex digest"
            )
            continue
        actual = sha256_file(paths[key])
        observed[key] = actual
        if actual != expected:
            errors.append(
                f"{key} body hash mismatch: expected {expected}, observed {actual}"
            )
    return section(errors, observed_sha256=observed)


def run_capture(
    argv: list[str], *, cwd: Path, env: dict[str, str] | None = None
) -> subprocess.CompletedProcess[str]:
    try:
        return subprocess.run(
            argv, cwd=cwd, env=env, capture_output=True, text=True,
            check=False, shell=False
        )
    except OSError as exc:
        raise BridgeHarnessError(f"cannot execute {argv!r}: {exc}") from exc


def git_value(repo_dir: Path, *args: str) -> str:
    result = run_capture(["git", *args], cwd=repo_dir)
    if result.returncode:
        raise BridgeHarnessError(
            f"git {' '.join(args)} failed in {repo_dir}: "
            f"{result.stderr.strip() or result.stdout.strip()}"
        )
    return result.stdout.strip()


def verify_host_ancestor(
    manifest: dict[str, Any], root: Path
) -> dict[str, Any]:
    expected = manifest.get("host", {}).get("base_commit_sha")
    if not isinstance(expected, str):
        raise BridgeHarnessError("manifest.host.base_commit_sha is missing")
    try:
        if git_value(root, "rev-parse", "--is-inside-work-tree") != "true":
            return {"status": "not_evaluated", "reason": "git history unavailable"}
    except BridgeHarnessError:
        return {"status": "not_evaluated", "reason": "git history unavailable"}

    available = run_capture(["git", "cat-file", "-e", f"{expected}^{{commit}}"], cwd=root)
    if available.returncode:
        return {
            "status": "not_evaluated",
            "reason": "pinned base commit is not available in this checkout history",
            "base_commit_sha": expected,
        }
    result = run_capture(["git", "merge-base", "--is-ancestor", expected, "HEAD"], cwd=root)
    if result.returncode == 0:
        return {"status": "pass", "base_commit_sha": expected}
    if result.returncode == 1:
        return {
            "status": "fail",
            "base_commit_sha": expected,
            "errors": ["current DI checkout does not contain the pinned bridge base as an ancestor"],
        }
    raise BridgeHarnessError(
        "git merge-base --is-ancestor failed: "
        + (result.stderr.strip() or result.stdout.strip())
    )


def verify_upstream_pins(
    manifest: dict[str, Any], upstream_root: Path
) -> dict[str, Any]:
    errors: list[str] = []
    observed: dict[str, dict[str, str]] = {}
    upstream_root = upstream_root.resolve()
    for key in ("dif", "drp", "tip"):
        entry = manifest.get("upstreams", {}).get(key)
        if not isinstance(entry, dict):
            raise BridgeHarnessError(f"manifest.upstreams.{key} is missing")
        checkout = entry.get("checkout_dir")
        if not isinstance(checkout, str):
            raise BridgeHarnessError(f"manifest.upstreams.{key}.checkout_dir is missing")
        repo_dir = (upstream_root / checkout).resolve()
        if not repo_dir.is_dir():
            raise BridgeHarnessError(f"upstream checkout is missing: {repo_dir}")
        head = git_value(repo_dir, "rev-parse", "HEAD")
        tree = git_value(repo_dir, "rev-parse", "HEAD^{tree}")
        dirty = git_value(repo_dir, "status", "--porcelain", "--untracked-files=all")
        observed[key] = {
            "commit_sha": head,
            "tree_sha": tree,
            "working_tree": "clean" if not dirty else "dirty",
        }
        if head != entry.get("commit_sha"):
            errors.append(
                f"{key} commit pin mismatch: expected {entry.get('commit_sha')}, observed {head}"
            )
        if tree != entry.get("tree_sha"):
            errors.append(
                f"{key} tree pin mismatch: expected {entry.get('tree_sha')}, observed {tree}"
            )
        if dirty:
            errors.append(
                f"{key} upstream checkout is dirty; pinned native code must be executed from an unmodified working tree"
            )
    return section(errors, observed=observed)


def validate_dif_schema(
    record: dict[str, Any], schema_path: Path
) -> dict[str, Any]:
    try:
        from jsonschema import FormatChecker, validators
    except ImportError as exc:
        raise BridgeHarnessError(
            "jsonschema is required for pinned DIF schema validation"
        ) from exc
    schema = load_json(schema_path)
    if not isinstance(schema, dict):
        raise BridgeHarnessError("pinned DIF schema root must be an object")
    try:
        cls = validators.validator_for(schema)
        cls.check_schema(schema)
        errors = sorted(
            cls(schema, format_checker=FormatChecker()).iter_errors(record),
            key=lambda item: str(list(item.path)),
        )
    except Exception as exc:
        raise BridgeHarnessError(f"DIF schema validation machinery failed: {exc}") from exc
    return section(
        [f"{list(err.path)}: {err.message}" for err in errors],
        mode="draft2020-12-schema-with-format-checker",
    )


def native_command(
    label: str, argv: list[str], *, cwd: Path, env: dict[str, str] | None = None
) -> dict[str, Any]:
    result = run_capture(argv, cwd=cwd, env=env)
    errors = [] if result.returncode == 0 else [f"{label} exited with {result.returncode}"]
    return section(
        errors, returncode=result.returncode,
        stdout=result.stdout.strip(), stderr=result.stderr.strip()
    )


def validate_upstream_native(
    manifest: dict[str, Any], records: dict[str, Any],
    paths: dict[str, Path], upstream_root: Path
) -> dict[str, Any]:
    upstream_root = upstream_root.resolve()
    pins = verify_upstream_pins(manifest, upstream_root)
    native: dict[str, Any] = {"upstream_pins": pins}
    if pins["status"] != "pass":
        return native

    upstreams = manifest["upstreams"]
    dif_dir = (upstream_root / upstreams["dif"]["checkout_dir"]).resolve()
    drp_dir = (upstream_root / upstreams["drp"]["checkout_dir"]).resolve()
    tip_dir = (upstream_root / upstreams["tip"]["checkout_dir"]).resolve()

    native["dif"] = validate_dif_schema(
        records["dif"], dif_dir / upstreams["dif"]["schema_path"]
    )
    native["drp"] = native_command(
        "DRP native validator",
        [sys.executable, str(drp_dir / upstreams["drp"]["validator_path"]), str(paths["drp"])],
        cwd=drp_dir,
    )
    env = os.environ.copy()
    env["PYTHONPATH"] = str(tip_dir) + (
        os.pathsep + env["PYTHONPATH"] if env.get("PYTHONPATH") else ""
    )
    native["tip"] = native_command(
        "TIP native validator",
        [sys.executable, "-m", "tip", "validate", str(paths["tip"])],
        cwd=tip_dir, env=env,
    )
    return native
