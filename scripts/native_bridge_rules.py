"""Cross-record and projection rules for the DI native-record bridge."""

from __future__ import annotations

from typing import Any

from native_bridge_io import canonical_json_bytes, section


def cross_record_errors(
    manifest: dict[str, Any], records: dict[str, Any]
) -> list[str]:
    errors: list[str] = []
    dif, di, drp, tip = (records[key] for key in ("dif", "di", "drp", "tip"))
    statement = dif.get("statement")

    if dif.get("confirmedByHuman") is not True:
        errors.append("DIF confirmedByHuman must be literal true")
    if di.get("request") != statement:
        errors.append("DI request must exactly equal DIF statement")
    if di.get("inferred_intent") != statement:
        errors.append("DI inferred_intent must exactly equal DIF statement")

    metadata = drp.get("metadata")
    if not isinstance(metadata, dict):
        errors.append("DRP metadata must bind the upstream record identities")
        metadata = {}
    if metadata.get("dif_intent_id") != dif.get("id"):
        errors.append("DRP metadata.dif_intent_id must exactly match DIF id")
    if metadata.get("di_check_id") != di.get("check_id"):
        errors.append("DRP metadata.di_check_id must exactly match DI check_id")
    if metadata.get("selected_di_action") != di.get("recommended_next_step"):
        errors.append("DRP metadata.selected_di_action must equal DI recommended_next_step")

    mapping = manifest.get("status_mapping", {}).get("drp_to_projection", {})
    source_status = mapping.get("source_status")
    if drp.get("status") != source_status:
        errors.append(
            f"DRP status {drp.get('status')!r} is unsupported by this bridge; "
            f"expected the explicitly mapped {source_status!r}"
        )
    if "supersedes_record_id" in drp:
        errors.append("this bridge does not map a superseded DRP record")
    if drp.get("decision") != di.get("recommended_next_step"):
        errors.append("DRP decision must exactly equal DI recommended_next_step")

    cause = tip.get("cause")
    supporting = cause.get("supporting_signals") if isinstance(cause, dict) else None
    drp_signal, di_signal = f"drp:{drp.get('record_id')}", f"di:{di.get('check_id')}"
    if not isinstance(supporting, list) or drp_signal not in supporting:
        errors.append(f"TIP cause.supporting_signals must contain {drp_signal!r}")
    if not isinstance(supporting, list) or di_signal not in supporting:
        errors.append(f"TIP cause.supporting_signals must contain {di_signal!r}")

    action = tip.get("action")
    if (action.get("summary") if isinstance(action, dict) else None) != drp.get("decision"):
        errors.append("TIP action.summary must exactly equal DRP decision")

    expected = manifest.get("expected", {})
    transition = tip.get("transition")
    if not isinstance(transition, dict):
        errors.append("TIP transition must be an object")
        transition = {}
    if transition.get("from") != expected.get("starting_state"):
        errors.append("TIP transition.from must match manifest expected.starting_state")
    if transition.get("to") != expected.get("target_state"):
        errors.append("TIP transition.to must match manifest expected.target_state")
    if tip.get("status") != "reviewed":
        errors.append("TIP status must be reviewed for this closed bridge fixture")

    review = tip.get("review")
    if not isinstance(review, dict):
        errors.append("TIP reviewed record must include a review object")
        review = {}
    evidence = review.get("evidence")
    if not isinstance(evidence, list) or not evidence:
        errors.append("TIP review.evidence must contain at least one reference")
    next_state = review.get("next_state")
    if not isinstance(next_state, str) or not next_state or next_state == "UNOBSERVED":
        errors.append("TIP review.next_state must be a concrete observed state")
    elif next_state != expected.get("next_state"):
        errors.append("TIP review.next_state must match manifest expected.next_state")
    return errors


def derive_projection(
    manifest: dict[str, Any], records: dict[str, Any]
) -> dict[str, Any]:
    dif, di, drp, tip = (records[key] for key in ("dif", "di", "drp", "tip"))
    feasible = di.get("feasible_actions", [])
    di_status = "conditional" if any(
        isinstance(item, dict) and item.get("status") != "allowed"
        for item in feasible
    ) else "feasible"
    review = tip.get("review", {})
    mapping = manifest["status_mapping"]["drp_to_projection"]
    return {
        "envelope_version": "0.1",
        "envelope_id": "dti.native-record-bridge.payment-recovery.001",
        "dif": {
            "intent_id": dif.get("id"), "status": "confirmed",
            "summary": dif.get("statement"),
            "human_confirmed": dif.get("confirmedByHuman"),
        },
        "di": {
            "feasibility_id": di.get("check_id"),
            "intent_id": dif.get("id"), "status": di_status,
            "allowed_paths": [
                item.get("action") for item in feasible if isinstance(item, dict)
            ],
            "blocked_paths": [
                item.get("action") for item in di.get("blocked_actions", [])
                if isinstance(item, dict)
            ],
            "constraints": di.get("constraints", []),
        },
        "drp": {
            "record_id": drp.get("record_id"),
            "feasibility_id": di.get("check_id"),
            "decision_summary": drp.get("decision"),
            "status": mapping.get("projected_status"),
        },
        "tip": {
            "transition_id": tip.get("id"),
            "decision_record_id": drp.get("record_id"),
            "starting_state": tip.get("transition", {}).get("from"),
            "target_state": tip.get("transition", {}).get("to"),
            "action_summary": tip.get("action", {}).get("summary"),
            "status": tip.get("status"),
        },
        "review": {
            "transition_id": tip.get("id"), "status": "reviewed",
            "evidence_references": review.get("evidence", []),
            "next_state": review.get("next_state"),
        },
    }


def validate_projection(
    manifest: dict[str, Any], records: dict[str, Any],
    di_module: Any, envelope_schema: dict[str, Any]
) -> dict[str, Any]:
    errors: list[str] = []
    derived = derive_projection(manifest, records)
    if canonical_json_bytes(derived) != canonical_json_bytes(records["projection"]):
        errors.append("derived projection does not match projection-envelope.json")
    errors.extend(di_module.validate(derived, envelope_schema))
    errors.extend(di_module.validate_envelope_semantics(derived))
    return section(errors, derived_projection=derived)
