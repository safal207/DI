"""Opt-in, offline native-record consistency check. Not an execution engine."""
from __future__ import annotations

import argparse
import hashlib
import json
import math
from pathlib import Path
import subprocess
import sys
import types

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
ROLES = ("DIF", "DI", "DRP", "TIP")
PROFILE = "native-read-only-recovery-v0.1"
MAX_INPUT = 512 * 1024


class InputError(ValueError):
    pass


class SourceError(RuntimeError):
    pass


def _constant(token):
    raise InputError("non-finite JSON number: " + token)


def _float(token):
    value = float(token)
    if not math.isfinite(value):
        raise InputError("non-finite JSON number: " + token)
    return value


def _pairs(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            raise InputError("duplicate JSON key: " + key)
        result[key] = value
    return result


def loads(text):
    if len(text.encode("utf-8")) > MAX_INPUT:
        raise InputError("input exceeds 512 KiB")
    return json.loads(text, parse_constant=_constant, parse_float=_float,
                      object_pairs_hook=_pairs)


def canonical(value):
    """Python JSON serialization profile, deliberately NOT RFC8785/JCS."""
    return json.dumps(value, sort_keys=True, ensure_ascii=False,
                      separators=(",", ":"), allow_nan=False).encode("utf-8")


def digest(value):
    return hashlib.sha256(canonical(value)).hexdigest()


def git(directory, *args):
    result = subprocess.run(["git", "-C", str(directory), *args],
                            capture_output=True, timeout=20)
    if result.returncode:
        raise SourceError("pinned Git source unavailable: " + str(directory))
    return result.stdout


def verified_bytes(directory, revision, relative):
    """Compare working bytes to the exact pinned Git object, before loading."""
    baseline = git(directory, "show", revision + ":" + relative)
    current = (directory / relative).read_bytes()
    if current != baseline:
        raise SourceError("dirty pinned source: " + relative)
    return current


def _module(name, filename, source):
    module = types.ModuleType(name)
    module.__file__ = str(filename)
    sys.modules[name] = module  # dataclasses needs its module registered.
    # Compile verified source bytes, not an unchecked .pyc cache.
    exec(compile(source, str(filename), "exec"), module.__dict__)
    return module


class Sources:
    """Trusted developer checkout paths; never supplied by the input bundle."""
    def __init__(self, root=ROOT, dependency_root=None):
        root = Path(root).resolve()
        dependency_root = Path(dependency_root or root / ".native").resolve()
        lock = json.loads((HERE / "compatibility.json").read_text(encoding="utf-8"))
        from jsonschema import FormatChecker, validators
        self.format_checker = FormatChecker()
        if self.format_checker.conforms("not-a-date", "date-time"):
            raise SourceError("date-time format checker is unavailable")
        self.schemas, self.modules, self.evidence = {}, {}, {}
        for role in ROLES:
            spec = lock["repositories"][role]
            directory = root if role == "DI" else dependency_root / role
            actual_root = Path(git(directory, "rev-parse", "--show-toplevel").decode().strip())
            if actual_root.resolve() != directory:
                raise SourceError("dependency is not a separate checkout: " + role)
            head = git(directory, "rev-parse", "HEAD").decode().strip()
            if role != "DI" and head != spec["commit"]:
                raise SourceError("pinned revision mismatch: " + role)
            files = {p: verified_bytes(directory, spec["commit"], p) for p in spec["files"]}
            self.evidence[role] = {"repository": spec["repository"],
                                  "source_commit": spec["commit"],
                                  "files_sha256": {p: hashlib.sha256(b).hexdigest()
                                                   for p, b in files.items()}}
            for path, raw in files.items():
                if path.endswith(".schema.json"):
                    schema = loads(raw.decode("utf-8"))
                    validator = validators.validator_for(schema)
                    validator.check_schema(schema)
                    self.schemas[(role, path)] = (schema, validator(schema,
                                                    format_checker=self.format_checker))
            if role in ("DI", "DRP", "TIP"):
                path = spec["module"]
                self.modules[role] = _module("_bridge_native_" + role.lower(),
                                             directory / path, files[path])

    def native_errors(self, role, record):
        if role == "DIF":
            _, validator = self.schemas[(role, "schemas/confirmed-intent.schema.json")]
            return [e.message for e in validator.iter_errors(record)]
        if role == "DI":
            schema, _ = self.schemas[(role, "schemas/feasibility-check.schema.json")]
            return self.modules[role].validate(record, schema)
        if role == "DRP":
            return [e.format() for e in self.modules[role].validate(record).errors]
        schema, _ = self.schemas[(role, "schemas/tip-record.schema.json")]
        native = self.modules[role]
        return native.validate_schema_subset(schema, record) + native.validate_invariants(record)

    def envelope_errors(self, envelope):
        schema, _ = self.schemas[("DI", "schemas/decision-transition-envelope.schema.json")]
        native = self.modules["DI"]
        return native.validate(envelope, schema) + native.validate_envelope_semantics(envelope)


def blank_report():
    return {"profile": PROFILE, "status": "FAIL", "native": {r: "NOT_RUN" for r in ROLES},
            "envelope": "NOT_RUN", "binding": "NOT_RUN", "mapping": "NOT_RUN",
            "evidence_authenticity": "NOT_EVALUATED", "execution_authority": "NOT_EVALUATED",
            "methods": {"DIF": "native schema with format checks",
                        "DI": "native schema subset (feasibility); envelope plus invariants",
                        "DRP": "native reference schema, semantics and graph",
                        "TIP": "native schema subset and invariants"},
            "errors": []}


def fail(report, axis, message):
    report["errors"].append({"axis": axis, "message": message})


def nonblank(value):
    return isinstance(value, str) and bool(value.strip())


def project(records):
    """Narrow explicit mapping, not automatic status conversion or NLP."""
    f, d, r, t = (records[k] for k in ROLES)
    m = r.get("metadata", {}).get("native_bridge")
    if not isinstance(m, dict) or m.get("commitment_recorded") is not True:
        raise InputError("explicit commitment metadata is required")
    if r["status"] != "complete" or t["status"] != "reviewed":
        raise InputError("unsupported native status mapping")
    if f["confirmedByHuman"] is not True or m.get("mode") != "read-only-example":
        raise InputError("unsupported confirmation or mapping mode")
    required = {"intent_id": f["id"], "feasibility_id": d["check_id"], "transition_id": t["id"]}
    if any(m.get(k) != v for k, v in required.items()) or not nonblank(m.get("envelope_id")):
        raise InputError("native commitment reference mismatch")
    if d["request"] != f["statement"] or r["context"] != f["statement"]:
        raise InputError("native intent/request/context mismatch")
    if "inferred_intent" in d and d["inferred_intent"] != f["statement"]:
        raise InputError("native inferred intent mismatch")
    actions = d["feasible_actions"]
    if not actions or any(a["status"] != "allowed" or a.get("conditions") for a in actions):
        raise InputError("conditional or unreviewed paths are not supported by this mapping")
    allowed = [a["action"] for a in actions]
    blocked = [a["action"] for a in d["blocked_actions"]]
    if (r["decision"] not in allowed or r["decision"] in blocked
            or r["decision"] != d["recommended_next_step"]
            or r["decision"] != t["action"]["summary"]):
        raise InputError("selected native action mismatch or blocked action")
    review = t.get("review", {})
    evidence, next_state = review.get("evidence"), review.get("next_state")
    if not isinstance(evidence, list) or not evidence or not all(map(nonblank, evidence)):
        raise InputError("review requires nonblank evidence references")
    if not nonblank(next_state) or next_state.strip().upper() == "UNOBSERVED":
        raise InputError("review requires an observed next state")
    if t["transition"]["from"] != t["state"]["summary"] or next_state != t["transition"]["to"]:
        raise InputError("native transition state mismatch")
    return {"envelope_version": "0.1", "envelope_id": m["envelope_id"],
            "dif": {"intent_id": f["id"], "status": "confirmed", "summary": f["statement"],
                    "human_confirmed": f["confirmedByHuman"]},
            "di": {"feasibility_id": d["check_id"], "intent_id": f["id"], "status": "feasible",
                   "allowed_paths": allowed, "blocked_paths": blocked, "constraints": d["constraints"]},
            "drp": {"record_id": r["record_id"], "feasibility_id": d["check_id"],
                    "decision_summary": r["decision"], "status": "committed"},
            "tip": {"transition_id": t["id"], "decision_record_id": r["record_id"],
                    "starting_state": t["state"]["summary"], "target_state": t["transition"]["to"],
                    "action_summary": t["action"]["summary"], "status": "reviewed"},
            "review": {"transition_id": t["id"], "status": "reviewed",
                       "evidence_references": evidence, "next_state": next_state}}


def validate_bundle(bundle, sources):
    report = blank_report()
    report["validator_sources"] = sources.evidence
    try:
        loads(canonical(bundle).decode("utf-8"))  # also check programmatic numeric inputs.
        if not isinstance(bundle, dict) or set(bundle) != {"profile", "records", "sha256", "envelope"}:
            raise InputError("bundle requires profile, records, sha256 and envelope objects")
        if bundle["profile"] != PROFILE:
            raise InputError("unsupported bridge profile")
        records, hashes, envelope = (bundle[k] for k in ("records", "sha256", "envelope"))
        if (not all(isinstance(x, dict) for x in (records, hashes, envelope))
                or set(records) != set(ROLES) or set(hashes) != set(ROLES)
                or not all(isinstance(x, dict) for x in records.values())):
            raise InputError("four complete native record objects and digests are required")
    except (ValueError, TypeError, RecursionError, UnicodeError) as exc:
        fail(report, "input", str(exc))
        return report
    try:
        for role in ROLES:
            errors = sources.native_errors(role, records[role])
            report["native"][role] = "FAIL" if errors else "PASS"
            for error in errors:
                fail(report, "native." + role, error)
        errors = sources.envelope_errors(envelope)
        report["envelope"] = "FAIL" if errors else "PASS"
        for error in errors:
            fail(report, "envelope", error)
        if report["errors"]:
            return report
        report["binding"] = "PASS"
        for role in ROLES:
            if hashes[role] != digest(records[role]):
                report["binding"] = "FAIL"
                fail(report, "binding", "native body digest mismatch: " + role)
        try:
            expected = project(records)
            report["mapping"] = "PASS" if canonical(expected) == canonical(envelope) else "FAIL"
            if report["mapping"] == "FAIL":
                fail(report, "mapping", "envelope differs from native record projection")
        except (InputError, KeyError, TypeError, AttributeError) as exc:
            report["mapping"] = "FAIL"
            fail(report, "mapping", str(exc))
        if not report["errors"]:
            report["status"] = "PASS"
    except Exception as exc:
        report["status"] = "ERROR"
        fail(report, "infrastructure", type(exc).__name__ + ": " + str(exc))
    return report


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("bundle", type=Path)
    parser.add_argument("--dependencies", type=Path, default=ROOT / ".native")
    args = parser.parse_args(argv)
    report = blank_report()
    try:
        sources = Sources(dependency_root=args.dependencies)
    except Exception as exc:
        report["status"] = "ERROR"
        fail(report, "infrastructure", type(exc).__name__ + ": " + str(exc))
    else:
        try:
            with args.bundle.open("rb") as handle:
                raw = handle.read(MAX_INPUT + 1)
            if len(raw) > MAX_INPUT:
                raise InputError("input exceeds 512 KiB")
            bundle = loads(raw.decode("utf-8"))
            report = validate_bundle(bundle, sources)
        except (OSError, ValueError, UnicodeError, RecursionError) as exc:
            if isinstance(exc, OSError):
                report["status"] = "ERROR"
            fail(report, "input", str(exc))
    print(json.dumps(report, indent=2, ensure_ascii=False, allow_nan=False))
    return {"PASS": 0, "FAIL": 1, "ERROR": 2}[report["status"]]


if __name__ == "__main__":
    raise SystemExit(main())
