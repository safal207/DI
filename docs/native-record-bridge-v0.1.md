# Native Record Bridge v0.1

Status: **experimental, opt-in integration proof**

This fixture demonstrates one pinned, provider-neutral path across the original
record shapes of four independent projects:

```text
DIF ConfirmedIntent
→ DI Feasibility Check
→ DRP Record
→ TIP Record + Review
→ observed next state
```

It does **not** create a fifth protocol. DIF, DI, DRP, and TIP remain
authoritative for their own record shapes, validators, versions, and lifecycle
rules.

## Why this exists

DI's existing cross-stack envelope is deliberately a reduced projection. It
preserves a small identity/continuity chain, but it does not contain complete
canonical DIF, DRP, or TIP records and it does not invoke every upstream
validator.

The native-record bridge adds a separate, opt-in proof over **one** pinned
fixture:

1. keep the full original records;
2. pin the exact source commits and trees;
3. bind each projection to the raw body hash of its original record;
4. validate each original record with its native validation boundary;
5. check cross-record identity and content links;
6. derive the existing DI v0.1 envelope from the full bodies;
7. validate that derived projection with the existing DI envelope rules.

The original reduced envelope remains unchanged.

## Pinned snapshot

`integration/native-record-bridge/v0.1/manifest.json` pins the exact snapshot.

The current experimental stack uses the **merged Phase 1 hardening revisions**:

- DI main `e6dba82590f3470b1f9bfa56ca5132f60eb661b5` (merged PR #27);
- DIF main `a5a8d330a6308a4c7990be2a4d46211cc030d05d` (merged PR #43);
- DRP canonical main `92e63d7d4eeb55f8eb61956da002dc8951bab1c6`;
- TIP main `6b272febd048cf8e218417b3c0506c7fa4fa43fa` (merged PR #8).

The merge commits retain the same trees as their reviewed hardening heads for
this snapshot. These are compatibility pins for this fixture, not a claim that
those revisions form a permanently versioned ecosystem release.

## Provider-neutral scenario

The full DIF record confirms this intent:

```text
Recover the authoritative outcome of one ambiguous payment operation
without creating a second financial effect.
```

The DI record allows an authoritative state read, blocks a blind new mutation,
and permits a retry only under explicit constraints after authoritative
evidence proves that no committed effect exists.

The DRP record canonically uses:

```text
status = complete
```

It records the decision to read authoritative state before any new mutation.
The bridge requires this full DRP `decision` to equal DI's
`recommended_next_step` exactly; matching IDs alone are not enough.

The TIP record starts from:

```text
commit_state_unknown
```

and reviews the evidence-backed transition to:

```text
established_transaction_state
→ SUCCESS_CONFIRMED
```

No external payment provider is named or contacted.

## Native validation boundaries

The bridge intentionally reports the validation mode for each original record.

### DIF

The full ConfirmedIntent is checked against the exact pinned Draft 2020-12
schema with the schema-selected `jsonschema` validator and a `FormatChecker`.

This is **schema-only** validation. This fixture does not invent a canonical DIF
semantic validator that the pinned repository does not provide for the full
ConfirmedIntent artifact.

### DI

The full Feasibility Check is validated through DI's actual
`scripts/validate-fixtures.py` module and
`schemas/feasibility-check.schema.json`.

### DRP

The full record is passed to the pinned native reference validator:

```text
tools/drp_validator.py
```

### TIP

The full record is passed to the pinned native CLI:

```text
python -m tip validate
```

## Body binding

Every full record and the expected reduced projection has a raw-byte SHA-256 in
the manifest.

The validator checks those hashes before trusting cross-record links. Therefore
changing a record body while preserving its ID does not preserve bridge
validity.

This distinguishes `same ID` from `same exact supplied record`.

## Narrow DRP status mapping

DRP's canonical status vocabulary and DI's envelope vocabulary are different.
This fixture allows exactly one local projection:

```text
DRP complete
→ DI envelope committed
```

It is **not** a global equivalence. The mapping is accepted only when:

- the raw DRP body matches its manifest hash;
- the DRP record is not superseded;
- the DRP decision exactly equals `DI.recommended_next_step`;
- DRP metadata binds the exact DIF intent ID and DI check ID;
- TIP's action summary exactly equals the DRP decision.

A different DRP status is rejected by this bridge even if that status is valid
inside DRP itself.

## Projection

The validator derives the existing DI v0.1 envelope from the full bodies:

```text
DIF.id                 → envelope.dif.intent_id
DI.check_id             → envelope.di.feasibility_id
DRP.record_id           → envelope.drp.record_id
TIP.id                  → envelope.tip.transition_id
TIP.review.evidence     → envelope.review.evidence_references
TIP.review.next_state   → envelope.review.next_state
```

The derived object must equal
`integration/native-record-bridge/v0.1/projection-envelope.json`, and it must
pass the existing DI envelope schema and semantic checks. The projection file
therefore cannot silently become a second source of truth.

## Run locally

Local bridge rules, without upstream checkouts:

```bash
python -m unittest discover -s tests -p 'test_native_record_bridge.py' -v
python scripts/validate-native-record-bridge.py --pretty
```

Full native validation requires the exact pinned checkouts under:

```text
.upstream/
  DIF/
  DRP/
  TIP/
```

Then run:

```bash
python scripts/validate-native-record-bridge.py \
  --upstream-root .upstream \
  --pretty
```

The dedicated GitHub Actions workflow creates those pinned checkouts
automatically and checks that the merged DI hardening baseline is in the branch
ancestry.

## What PASS means

For this exact fixture and pinned snapshot, PASS means:

- original record bodies match their manifest hashes;
- the DI record passes DI validation;
- when upstream checkouts are supplied, DIF/DRP/TIP pass the declared native
  validation boundaries;
- explicitly checked cross-record identities and content agree;
- DRP's recorded decision is exactly the DI recommended next step;
- the reduced envelope is derived from the full records and passes DI's existing
  envelope rules.

## What PASS does not mean

PASS does not prove:

- that evidence references are authentic or truthful;
- actual human identity, authenticated consent, or consent outside the record;
- execution permission or authority;
- external provider behavior or exactly-once execution;
- production safety or causal correctness;
- external adoption or endorsement;
- that four repositories have merged into one protocol.

The report keeps `evidence_authenticity` and `execution_authority` as
`not_evaluated` for this provider-neutral fixture.

## Assurance

Regression cases cover missing originals, same-ID body substitution, false
human confirmation, intent drift, unsupported DRP status mapping, DRP
identity/decision drift, lost TIP source references, TIP action drift, missing
review evidence, unobserved next state, stale projection, upstream pin drift,
relative-checkout path resolution, and failing native-validator subprocesses.

The bridge should grow only when a new interoperability rule has a negative case
that proves the drift can be detected.
