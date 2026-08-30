#!/usr/bin/env python3
"""Build or verify the client-demo data from canonical DI evidence."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
SUMMARY_PATH = ROOT / "evidence/ambiguous-payment-sandbox/summary.json"
MUTATION_PATH = ROOT / "evidence/ambiguous-payment-sandbox/mutation-report.json"
OUTPUT_PATH = ROOT / "demo/ambiguous-payment/demo-data.json"


def load_json(path: Path) -> Any:
    with path.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def build_data(summary: dict[str, Any], mutation: dict[str, Any]) -> dict[str, Any]:
    safe_metrics = [
        {"label": "Committed effects", "value": str(summary["stored_effect_count"]), "tone": "safe"},
        {"label": "Duplicate effects", "value": str(summary["duplicate_effect_count"]), "tone": "safe"},
        {"label": "Acknowledgement lost", "value": "YES" if summary["acknowledgement_lost"] else "NO", "tone": "unknown"},
        {"label": "Authoritative state", "value": str(summary["authoritative_commit_status"]).upper(), "tone": "safe"},
        {"label": "Next action", "value": str(summary["selected_next_action"]), "tone": "safe"},
        {
            "label": "Unsafe mutations rejected",
            "value": f"{mutation['mutations_rejected_as_expected']} / {mutation['mutation_count']}",
            "tone": "safe",
        },
    ]

    return {
        "data_version": "0.1",
        "generated_from": [
            "evidence/ambiguous-payment-sandbox/summary.json",
            "evidence/ambiguous-payment-sandbox/mutation-report.json",
        ],
        "paths": {
            "safe": {
                "id": "safe",
                "title": "DI recovery",
                "verdict": str(summary["conformance_status"]),
                "decision_heading": "Evidence-backed decision:",
                "decision_note": "The committed effect is recovered from authoritative state. A second mutation is blocked.",
                "next_action": str(summary["selected_next_action"]),
                "explanation": "Authoritative evidence found the committed effect, so a second mutation is not permitted.",
                "steps": [
                    {
                        "state": "ONE OPERATION",
                        "title": "Submit one intended payment",
                        "detail": "The request is bound to one logical operation and one stable effect identity.",
                    },
                    {
                        "state": "COMMITTED",
                        "title": "The financial effect exists",
                        "detail": "The deterministic sandbox stores exactly one committed effect.",
                    },
                    {
                        "state": "UNKNOWN",
                        "title": "The acknowledgement is lost",
                        "detail": "The client cannot infer commit outcome from a missing transport response.",
                    },
                    {
                        "state": "LOOKUP",
                        "title": "Recover authoritative state",
                        "detail": "Lookup finds the existing committed effect under the preserved identity.",
                    },
                    {
                        "state": "NO NEW MUTATION",
                        "title": "Accept the existing effect",
                        "detail": "The next action is ACCEPT_EXISTING_EFFECT; duplicate-effect count remains zero.",
                    },
                ],
                "metrics": safe_metrics,
            },
            "unsafe": {
                "id": "unsafe",
                "title": "Blind retry",
                "verdict": "RISK",
                "decision_heading": "Unsupported shortcut:",
                "decision_note": "A missing acknowledgement is treated as failure, and recovery mints a fresh mutation identity.",
                "next_action": "DUPLICATE_EFFECT_RISK",
                "explanation": "The original commit state was never resolved, so a new mutation can create an additional financial effect.",
                "steps": [
                    {
                        "state": "ONE OPERATION",
                        "title": "Submit one intended payment",
                        "detail": "The first request may already have committed at the provider or ledger boundary.",
                    },
                    {
                        "state": "COMMIT POSSIBLE",
                        "title": "The effect may already exist",
                        "detail": "A server-side commit can happen before the response reaches the client.",
                    },
                    {
                        "state": "UNKNOWN",
                        "title": "The acknowledgement is lost",
                        "detail": "Local transport uncertainty is incorrectly treated as proof of failure.",
                    },
                    {
                        "state": "NEW IDENTITY",
                        "title": "Retry as a fresh mutation",
                        "detail": "A new request or effect key no longer represents safe recovery of the same operation.",
                    },
                    {
                        "state": "RISK OPEN",
                        "title": "A second effect can be created",
                        "detail": "Without authoritative resolution, duplicate-effect exposure remains open.",
                    },
                ],
                "metrics": [
                    {"label": "Original commit state", "value": "UNRESOLVED", "tone": "unknown"},
                    {"label": "New mutation identity", "value": "CREATED", "tone": "risk"},
                    {"label": "Acknowledgement lost", "value": "YES", "tone": "unknown"},
                    {"label": "Authoritative lookup", "value": "SKIPPED", "tone": "risk"},
                    {"label": "Next action", "value": "BLIND_RETRY", "tone": "risk"},
                    {"label": "Duplicate-effect risk", "value": "OPEN", "tone": "risk"},
                ],
            },
        },
    }


def serialized(data: dict[str, Any]) -> str:
    return json.dumps(data, indent=2, ensure_ascii=False) + "\n"


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--check", action="store_true", help="fail when committed output is stale")
    args = parser.parse_args()

    try:
        summary = load_json(SUMMARY_PATH)
        mutation = load_json(MUTATION_PATH)
        expected = serialized(build_data(summary, mutation))
    except (OSError, KeyError, TypeError, json.JSONDecodeError) as exc:
        print(f"FAIL build client demo data: {exc}")
        return 1

    if args.check:
        try:
            actual = OUTPUT_PATH.read_text(encoding="utf-8")
        except OSError as exc:
            print(f"FAIL read {OUTPUT_PATH}: {exc}")
            return 1
        if actual != expected:
            print("FAIL demo-data.json is not reproducible from canonical evidence")
            return 1
        print("PASS client demo data matches canonical evidence")
        return 0

    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT_PATH.write_text(expected, encoding="utf-8")
    print(f"WROTE {OUTPUT_PATH.relative_to(ROOT)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
