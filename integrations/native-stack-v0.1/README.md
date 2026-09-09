# Native stack bridge v0.1

This directory contains one **provider-neutral interoperability example** across
four independent projects:

```text
DIF ConfirmedIntent
→ DI Feasibility Check
→ DRP Record
→ TIP Record
→ reviewed DI envelope projection
```

It is deliberately **not** a fifth protocol. DIF, DI, DRP, and TIP remain
authoritative for their own native record shapes and semantic rules.

## Why this bridge exists

DI's existing cross-stack envelope intentionally stores reduced projections:

```text
cross-stack envelope
!= canonical DIF record
!= canonical DI record
!= canonical DRP record
!= canonical TIP record
```

That is useful for continuity checks, but ID equality alone cannot prove that the
original native bodies were valid or unchanged. This bridge adds an opt-in test
that carries the complete native records, pins compatible upstream commits,
binds each body by SHA-256, invokes the available native validation surfaces, and
then derives the existing DI envelope deterministically.

## Validation levels

The report keeps these claims separate:

1. **Native record validation**
   - DIF `ConfirmedIntent`: schema-only against DIF's pinned Draft 2020-12 schema.
     DIF does not currently expose a separate semantic validator for this artifact.
   - DI feasibility record: validated with DI's own schema subset implementation.
   - DRP record: validated by DRP's native reference validator.
   - TIP record: validated by TIP's native CLI/reference validator.
2. **Body binding** — SHA-256 must match the manifest. Changing a record body
   while preserving its ID is rejected.
3. **Cross-record consistency** — intent, feasibility, decision, selected path,
   state, review evidence, and next-state links must agree.
4. **Envelope projection** — the derived reduced envelope must exactly equal
   `expected-envelope.json` and pass DI's envelope schema + semantic checks.

The bridge does **not** claim evidence authenticity, provider endorsement,
production safety, or execution authority.

## Explicit mapping boundary

Canonical DRP status `complete` is mapped to envelope status `committed` **only**
for this pinned bridge profile and only after the native DRP record passes its
validator and its bridge metadata binds to the exact DI check and selected
feasible path.

This is not a global statement that:

```text
DRP complete == DI envelope committed
```

No other DRP status is inferred as commitment.

The canonical TIP schema has no DRP `record_id` field. Therefore the
DRP-to-TIP link is carried by the bridge manifest as interface metadata and is
checked against the exact native bodies; the TIP record itself is not silently
extended with non-canonical fields.

## Files

```text
manifest.json
dif-confirmed-intent.json
di-feasibility-check.json
drp-record.json
tip-record.tip.json
expected-envelope.json
requirements.txt
```

## Reproduce

The GitHub workflow checks out the pinned upstream commits, runs DIF schema-only validation, the native DRP and TIP validators, and then runs:

```bash
python -m pip install -r integrations/native-stack-v0.1/requirements.txt
python -m unittest tests.test_native_stack_bridge -v
python scripts/validate-native-stack-bridge.py \
  --bundle integrations/native-stack-v0.1 \
  --pretty
```

A successful report may state that the pinned native records validated and the
bridge was internally consistent. It must not be upgraded into a claim that an
external provider uses these protocols or that a real financial side effect was
executed.
