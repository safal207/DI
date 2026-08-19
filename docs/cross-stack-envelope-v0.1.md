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

`review.status = reviewed` requires:

```text
TIP.status == reviewed
and
evidence_references is not empty
and
next_state is concrete and observed
```

The validator rejects a claimed reviewed outcome without evidence.

## Closing the loop

A reviewed `next_state` may seed another decision cycle.

The cycle-chain contract makes that continuity explicit:

```text
Cycle 1
DIF → DI → DRP → TIP → Review → Next State
                                  │
                                  ▼
Cycle 2 input_state ──────────────┘
→ DIF → DI → DRP → TIP → Review → Next State
```

The key invariant is deliberately simple:

```text
cycle[n].input_state
==
cycle[n-1].envelope.review.next_state
```

This prevents a new cycle from silently starting from a different reality than the one actually observed in the previous cycle.

The chain validator also requires:

```text
cycle.cycle_id == cycle.envelope.envelope_id
cycle.input_state == cycle.envelope.tip.starting_state
cycle[n].previous_cycle_id == cycle[n-1].cycle_id
```

Every cycle in a closed chain must be reviewed before its state is allowed to seed the next cycle.

## Two-cycle example

The positive fixture models a provider-neutral financial flow.

Cycle 1:

```text
commit_state_unknown
→ recover/read existing transaction
→ evidence
→ SUCCESS_CONFIRMED
```

Cycle 2 must begin from exactly that state:

```text
SUCCESS_CONFIRMED
→ do not pay again
→ read fulfillment/order state
→ evidence
→ FULFILLMENT_CONFIRMED
```

The negative fixture changes the second-cycle input to `PAYMENT_STILL_UNKNOWN` while the first review actually produced `SUCCESS_CONFIRMED`.

The JSON remains structurally plausible, but semantic validation rejects the chain because observed history was replaced by an invented starting state.

## Provider neutrality

The included fixtures use anonymous financial scenarios.

They do not imply that any external provider:

- uses this envelope;
- uses DIF, DI, DRP, or TIP;
- endorses the architecture;
- conforms to these protocols.

External products may be used as validation cases only with accurate attribution.

## Files

Envelope schema:

```text
schemas/decision-transition-envelope.schema.json
```

Cycle-chain schema:

```text
schemas/decision-transition-cycle-chain.schema.json
```

Envelope fixtures include valid pending/reviewed cases and invalid broken-reference/evidence cases.

Cycle-chain fixtures:

```text
fixtures/valid-decision-transition-cycle-chain-two-cycles.json
fixtures/invalid-decision-transition-cycle-chain-state-mismatch.json
```

## Validation

Run:

```bash
python scripts/validate-fixtures.py
```

The repository validator performs:

1. the minimal schema subset used by DI fixtures;
2. cross-stack semantic reference checks for each envelope;
3. nested envelope validation inside a cycle chain;
4. state continuity checks from one reviewed cycle into the next.

## Boundary rule

This integration contract must remain weaker than the canonical protocol contracts:

```text
cross-stack envelope
≠ canonical DIF record
≠ canonical DI record
≠ canonical DRP record
≠ canonical TIP record
```

The cycle-chain contract also does not create a new protocol. It only proves continuity between already separated cycles.

If the envelope conflicts with a canonical project specification, the canonical project's own repository wins.
