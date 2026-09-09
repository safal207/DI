"""Fail-closed I/O, manifest and reporting helpers for native-stack v0.1."""

from __future__ import annotations

import hashlib
import importlib.util
import json
import math
import re
import subprocess
import sys
from pathlib import Path, PurePosixPath
from typing import Any

DI_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_BRIDGE_DIR = DI_ROOT / "integrations" / "native-stack-v0.1"

DIM_ARTIFACT = "artifact_validity"
DIM_CONSISTENCY = "cross_record_consistency"
DIM_EVIDENCE = "evidence_integrity"

EXPECTED_REPOSITORIES = {
    "dif": "safal207/DIF",
    "drp": "safal207/DRP",
    "tip": "safal207/transition-intelligence-protocol",
}
EXPECTED_ARTIFACTS = {"dif", "di", "drp", "tip", "projection", "evidence"}
HEX40 = re.compile(r"^[0-9a-f]{40}$")
HEX64 = re.compile(r"^[0-9a-f]{64}$")


class HarnessError(RuntimeError):
    """The bridge could not evaluate its inputs at all."""


def _reject_constant(token: str) -> Any:
    raise HarnessError(f"non-standard JSON literal {token!r} is not accepted")


def _parse_float(token: str) -> float:
    value = float(token)
    if not math.isfinite(value):
        raise HarnessError(f"numeric literal {token!r} is not finite")
    return value


def load_json(path: Path, *, label: str) -> Any:
    if not path.exists():
        raise HarnessError(f"{label}: file does not exist: {path}")
    if not path.is_file():
        raise HarnessError(f"{label}: path is not a file: {path}")
    try:
        text = path.read_text(encoding="utf-8")
    except UnicodeDecodeError as exc:
        raise HarnessError(f"{label}: invalid UTF-8: {path}: {exc}") from exc
    except OSError as exc:
        raise HarnessError(f"{label}: cannot read {path}: {exc}") from exc
    try:
        return json.loads(text, parse_constant=_reject_constant, parse_float=_parse_float)
    except json.JSONDecodeError as exc:
        raise HarnessError(f"{label}: invalid JSON in {path}: {exc}") from exc


def git_blob_sha(path: Path) -> str:
    data = path.read_bytes()
    return hashlib.sha1(f"blob {len(data)}\0".encode("ascii") + data).hexdigest()


def sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def require_dict(value: Any, *, label: str) -> dict[str, Any]:
    if not isinstance(value, dict):
        raise HarnessError(f"{label}: object is required")
    return value


def require_string(value: Any, *, label: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise HarnessError(f"{label}: non-empty string is required")
    return value


def require_keys(obj: dict[str, Any], keys: set[str], *, label: str) -> None:
    missing = sorted(keys - set(obj))
    if missing:
        raise HarnessError(f"{label}: missing required key(s): {', '.join(missing)}")


def safe_relative_path(root: Path, raw: str, *, label: str) -> Path:
    raw = require_string(raw, label=label)
    pure = PurePosixPath(raw)
    if pure.is_absolute() or ".." in pure.parts:
        raise HarnessError(f"{label}: path must stay inside its declared root: {raw!r}")
    candidate = (root / Path(*pure.parts)).resolve()
    try:
        candidate.relative_to(root.resolve())
    except ValueError as exc:
        raise HarnessError(f"{label}: path escapes its declared root: {raw!r}") from exc
    return candidate


def require_safe_relative_string(value: Any, *, label: str) -> str:
    raw = require_string(value, label=label)
    pure = PurePosixPath(raw)
    if pure.is_absolute() or ".." in pure.parts:
        raise HarnessError(f"{label}: path must be relative and may not contain '..': {raw!r}")
    return raw


def safe_file_reference(root: Path, reference: str, *, label: str) -> Path:
    if not isinstance(reference, str) or not reference.startswith("file:"):
        raise HarnessError(f"{label}: repository-local evidence reference must start with 'file:'")
    return safe_relative_path(root, reference[5:], label=label)


def preflight_manifest(raw: Any, bridge_dir: Path) -> dict[str, Any]:
    m = require_dict(raw, label="manifest")
    require_keys(
        m,
        {"manifest_version", "bridge_id", "description", "di_contract",
         "external_repositories", "artifacts", "bindings", "non_claims"},
        label="manifest",
    )
    if m.get("manifest_version") != "0.1":
        raise HarnessError("manifest.manifest_version: expected '0.1'")
    require_string(m.get("bridge_id"), label="manifest.bridge_id")

    di = require_dict(m.get("di_contract"), label="manifest.di_contract")
    require_keys(di, {"repository", "base_commit", "files"}, label="manifest.di_contract")
    if di.get("repository") != "safal207/DI":
        raise HarnessError("manifest.di_contract.repository: expected 'safal207/DI'")
    if not HEX40.fullmatch(str(di.get("base_commit", ""))):
        raise HarnessError("manifest.di_contract.base_commit: 40 lowercase hex characters required")
    files = require_dict(di.get("files"), label="manifest.di_contract.files")
    expected_di_files = {
        "scripts/validate-fixtures.py",
        "schemas/feasibility-check.schema.json",
        "schemas/decision-transition-envelope.schema.json",
    }
    if set(files) != expected_di_files:
        raise HarnessError("manifest.di_contract.files: expected exactly the pinned validator and two schemas")
    for rel, spec in files.items():
        safe_relative_path(DI_ROOT, rel, label=f"manifest.di_contract.files[{rel!r}]")
        blob = require_dict(spec, label=f"manifest.di_contract.files[{rel!r}]").get("git_blob_sha")
        if not isinstance(blob, str) or not HEX40.fullmatch(blob):
            raise HarnessError(f"manifest.di_contract.files[{rel!r}].git_blob_sha: 40 lowercase hex required")

    external = require_dict(m.get("external_repositories"), label="manifest.external_repositories")
    if set(external) != set(EXPECTED_REPOSITORIES):
        raise HarnessError("manifest.external_repositories: expected exactly dif, drp and tip")
    for key, repo in EXPECTED_REPOSITORIES.items():
        spec = require_dict(external.get(key), label=f"manifest.external_repositories.{key}")
        require_keys(spec, {"repository", "commit", "schema_path"},
                     label=f"manifest.external_repositories.{key}")
        if spec.get("repository") != repo:
            raise HarnessError(f"manifest.external_repositories.{key}.repository: expected {repo!r}")
        commit = spec.get("commit")
        if not isinstance(commit, str) or not HEX40.fullmatch(commit):
            raise HarnessError(f"manifest.external_repositories.{key}.commit: 40 lowercase hex required")
        require_safe_relative_string(spec.get("schema_path"),
                                     label=f"manifest.external_repositories.{key}.schema_path")
        if key == "drp":
            require_safe_relative_string(spec.get("validator_path"),
                                         label="manifest.external_repositories.drp.validator_path")
        if key == "tip":
            require_safe_relative_string(spec.get("validator_entrypoint"),
                                         label="manifest.external_repositories.tip.validator_entrypoint")
            args = spec.get("validator_args")
            if not isinstance(args, list) or not args or not all(isinstance(x, str) and x for x in args):
                raise HarnessError("manifest.external_repositories.tip.validator_args: non-empty string array required")

    artifacts = require_dict(m.get("artifacts"), label="manifest.artifacts")
    if set(artifacts) != EXPECTED_ARTIFACTS:
        raise HarnessError("manifest.artifacts: expected exactly dif, di, drp, tip, projection and evidence")
    for key, spec in artifacts.items():
        spec = require_dict(spec, label=f"manifest.artifacts.{key}")
        require_keys(spec, {"path", "sha256"}, label=f"manifest.artifacts.{key}")
        safe_relative_path(bridge_dir, spec.get("path"), label=f"manifest.artifacts.{key}.path")
        digest = spec.get("sha256")
        if not isinstance(digest, str) or not HEX64.fullmatch(digest):
            raise HarnessError(f"manifest.artifacts.{key}.sha256: 64 lowercase hex required")
        if key != "evidence":
            require_string(spec.get("expected_id"), label=f"manifest.artifacts.{key}.expected_id")

    b = require_dict(m.get("bindings"), label="manifest.bindings")
    require_keys(
        b,
        {"intent_text_rule", "selected_action", "selected_action_status",
         "drp_native_status_precondition", "projection_drp_status", "status_relation",
         "evidence_reference", "logical_operation_id",
         "expected_stored_effect_count", "expected_duplicate_effect_count"},
        label="manifest.bindings",
    )
    if b.get("intent_text_rule") != "exact_equality":
        raise HarnessError("manifest.bindings.intent_text_rule: v0.1 requires exact_equality")
    if b.get("status_relation") != "not_equivalent":
        raise HarnessError("manifest.bindings.status_relation: must be 'not_equivalent'")
    if b.get("drp_native_status_precondition") != "complete":
        raise HarnessError("manifest.bindings.drp_native_status_precondition: expected 'complete'")
    if b.get("projection_drp_status") != "committed":
        raise HarnessError("manifest.bindings.projection_drp_status: expected 'committed'")

    ref_path = safe_file_reference(
        bridge_dir,
        require_string(b.get("evidence_reference"), label="manifest.bindings.evidence_reference"),
        label="manifest.bindings.evidence_reference",
    )
    evidence_path = safe_relative_path(
        bridge_dir, artifacts["evidence"]["path"], label="manifest.artifacts.evidence.path"
    )
    if ref_path != evidence_path:
        raise HarnessError("manifest.bindings.evidence_reference: must point to the declared evidence artifact")

    nc = require_dict(m.get("non_claims"), label="manifest.non_claims")
    if nc.get("external_authenticity") != "not_proven":
        raise HarnessError("manifest.non_claims.external_authenticity: expected 'not_proven'")
    if nc.get("execution_authority") != "out_of_scope":
        raise HarnessError("manifest.non_claims.execution_authority: expected 'out_of_scope'")
    if nc.get("provider_endorsement") is not False:
        raise HarnessError("manifest.non_claims.provider_endorsement: expected false")
    return m


def import_module(path: Path, name: str):
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise HarnessError(f"cannot import module from {path}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    try:
        spec.loader.exec_module(module)
    except Exception as exc:
        raise HarnessError(f"cannot import {path}: {type(exc).__name__}: {exc}") from exc
    return module


def git_head(root: Path, *, label: str) -> str:
    if not root.exists() or not root.is_dir():
        raise HarnessError(f"{label}: upstream root does not exist: {root}")
    proc = subprocess.run(["git", "-C", str(root), "rev-parse", "HEAD"],
                          capture_output=True, text=True)
    if proc.returncode:
        raise HarnessError(f"{label}: cannot read checkout HEAD: {(proc.stderr or proc.stdout).strip()}")
    return proc.stdout.strip()


def run_process(command: list[str], *, cwd: Path) -> dict[str, Any]:
    proc = subprocess.run(command, cwd=str(cwd), capture_output=True, text=True)
    return {
        "command": command, "cwd": str(cwd), "returncode": proc.returncode,
        "stdout": proc.stdout, "stderr": proc.stderr,
    }


def fresh_dimension() -> dict[str, Any]:
    return {"status": "pass", "errors": []}


def add_error(block: dict[str, Any], message: str) -> None:
    block["status"] = "fail"
    block["errors"].append(message)


def artifact_path(manifest: dict[str, Any], bridge_dir: Path, key: str) -> Path:
    return safe_relative_path(
        bridge_dir, manifest["artifacts"][key]["path"],
        label=f"manifest.artifacts.{key}.path",
    )
