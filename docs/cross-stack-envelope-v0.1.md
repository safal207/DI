# Cross-Stack Decision & Transition Envelope v0.1

Status: Draft integration contract

This document defines a small machine-readable envelope for linking artifacts across four independent projects:

```text
DIF → DI → DRP → TIP → Review
```

The envelope is **not a fifth protocol** and does not redefine any canonical protocol semantics.

Each project remains authoritative for its own artifact shape and lifecycle rules. The envelope only preserves cross-stack identity and handoff continuity.

## Purpose

The prose architecture defines the intended handoffs. This envelope makes the minimum chain inspectable by software:

```text
DIF intent_id
→ DI intent_id + feasibility_id
→ DRP feasibility_id + record_id
→ TIP decision_record_id + transition_id
→ Review transition_id
```

The core goal is to detect silent scope/reference drift between stages.

## Canonical fields

Top level:

- `envelope_version`
- `envelope_id`
- `dif`
- `di`
- `drp`
- `tip`
- `review`

The envelope intentionally stores summaries and references, not complete copies of canonical DIF, DI, DRP, or TIP records.

## Reference invariants

The reference chain must remain exact:

```text
di.intent_id == dif.intent_id

drp.feasibility_id == di.feasibility_id

tip.decision_record_id == drp.record_id

review.transition_id == tip.transition_id
```

A structurally valid JSON object that breaks any of these links is invalid as a cross-stack envelope.

## Confirmation invariant

The v0.1 end-to-end envelope starts only from a confirmed DIF intent:

```text
dif.status == confirmed
and
dif.human_confirmed == true
```

This does not claim that DIF itself requires this exact JSON shape. It means the cross-stack envelope refuses to treat an unconfirmed interpretation as the authoritative intent entering DI.

## Review invariant

`review.status = pending` represents a committed transition whose observed result has not yet been closed.

For a future `review.status = reviewed` envelope, the validator should require evidence references and a concrete next state rather than `UNOBSERVED`.

## Provider neutrality

The included fixture uses an anonymous ambiguous-payment recovery scenario.

It does not imply that any external provider:

- uses this envelope;
- uses DIF, DI, DRP, or TIP;
- endorses the architecture;
- conforms to these protocols.

External products may be used as validation cases only with accurate attribution.

## Files

Schema:

```text
schemas/decision-transition-envelope.schema.json
```

Positive fixture:

```text
fixtures/valid-decision-transition-envelope.json
```

Negative semantic fixture:

```text
fixtures/invalid-decision-transition-envelope-broken-reference.json
```

The negative fixture is intentionally JSON-Schema-valid in shape but breaks the DRP → TIP identity handoff. The repository validator must reject it semantically.

## Validation

Run:

```bash
python scripts/validate-fixtures.py
```

The repository's validator performs both:

1. the minimal schema subset used by DI fixtures;
2. cross-stack semantic reference checks for this envelope.

## Boundary rule

This integration contract must remain weaker than the canonical protocol contracts:

```text
cross-stack envelope
≠ canonical DIF record
≠ canonical DI record
≠ canonical DRP record
≠ canonical TIP record
```

If the envelope conflicts with a canonical project specification, the canonical project's own repository wins.
