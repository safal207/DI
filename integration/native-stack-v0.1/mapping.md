# Native-stack mapping rules

This file describes the **bridge-only** mapping between the pinned native
artifacts and DI's reduced projection. These rules are not changes to canonical
DIF, DI, DRP, or TIP semantics.

## Identity

```text
DIF ConfirmedIntent.id
= projection.dif.intent_id
= projection.di.intent_id

DI feasibility.check_id
= projection.di.feasibility_id
= projection.drp.feasibility_id

DRP record.record_id
= projection.drp.record_id
= projection.tip.decision_record_id

TIP record.id
= projection.tip.transition_id
= projection.review.transition_id
```

The full DRP record also carries bridge provenance in its permissive `metadata`
object: the upstream DIF and DI IDs plus the downstream TIP ID. This is an
integration reference, not a new native TIP field. The pinned TIP schema has no
`decision_record_id`, so the bridge must not invent one inside a canonical TIP
record.

## Body binding

`manifest.json` stores SHA-256 hashes for each full native record and the
reduced projection. Identity equality alone is insufficient: changing a record
body while keeping the same ID fails the bridge unless the manifest is
deliberately updated.

These hashes bind bytes inside this test package. They do **not** authenticate
who produced the evidence strings referenced by the records.

## DI → DRP status rule

Canonical DRP does not have a `committed` status. For this single proof:

```text
DRP status = complete
→ reduced projection DRP status = committed
```

This is not semantic identity. The rule is allowed only because:

1. the full DRP record passes the pinned native DRP validator;
2. the record's completed decision exactly matches the decision summary in the
   reduced projection;
3. the record links the same DIF/DI/TIP identities in bridge metadata;
4. the selected recovery path is the one represented by the projection.

A valid DRP status such as `proposed` is intentionally rejected by the bridge:
native validity alone does not mean the decision is ready to map to a binding
projection. An invalid status such as `committed` is rejected by DRP itself.

## TIP reviewed boundary

The pinned TIP validator requires concrete review notes for `status=reviewed`,
but DI's reduced reviewed envelope needs an observed result.

Therefore the bridge is deliberately stricter:

```text
TIP status = reviewed
→ review.summary is present
→ review.evidence is non-empty
→ review.next_state is concrete
→ review.next_state = projection.review.next_state
```

The evidence strings remain references only; the bridge does not authenticate
them.

## Separation of claims

The machine report keeps four dimensions separate:

- `validity`: native/schema validation and pinned-file integrity;
- `mapping_consistency`: cross-record identities and bridge mapping rules;
- `evidence_authenticity`: always `not_verified` here;
- `execution_authority`: always `not_claimed` here.

A PASS requires the first two dimensions to pass. It never upgrades the last
two dimensions.
