# Native Record Bridge v0.1

Status: opt-in integration experiment.

This directory validates **actual canonical-shaped records** from four independent projects without creating a fifth protocol:

```text
DIF ConfirmedIntent
→ DI Feasibility Check
→ DRP Record
→ TIP Record + Review
```

The reduced `decision-transition-envelope` elsewhere in DI remains valid for lightweight continuity checks. This bridge is intentionally stronger and separate: it pins repository commits, consumes full records, invokes canonical validation where available, binds exact bodies by SHA-256, and then checks cross-record handoff conditions.

## Pinned repositories

The exact commits and schema blobs are recorded in `manifest.json`.

The bridge refuses to silently float to newer repository versions. A version upgrade is a deliberate integration change and must update the manifest and tests.

## Validation boundary by project

| Project | Artifact | Validation in this bridge |
|---|---|---|
| DIF | `ConfirmedIntent` | Canonical Draft 2020-12 schema + format check |
| DI | `Feasibility Check` | Canonical Draft 2020-12 schema + format check |
| DRP | DRP record | Native `scripts/drp-validate --json` |
| TIP | TIP record | Native `python -m tip validate` |

DIF and the selected DI artifact do not claim a stronger native semantic validator here. The report says `schema_only` instead of pretending otherwise.

## Mapping preconditions

The bridge does **not** treat statuses as interchangeable.

In particular:

```text
DI feasible action
≠ automatically a DRP complete record
```

For this provider-neutral case, a DRP `complete` record is accepted only when:

1. its `decision` exactly equals `DI.recommended_next_step`;
2. that decision appears exactly once in `DI.feasible_actions`;
3. the DI action is `allowed` or `allowed_with_constraints`;
4. the same decision is not in `DI.blocked_actions`;
5. constrained conditions are copied exactly into DRP metadata;
6. DRP metadata binds the exact DIF intent ID and DI check ID.

The TIP action must then exactly equal the DRP decision, cite the supplied intent and decision record IDs, and preserve the selected DI conditions **verbatim** in `state.constraints`. This prevents a later stage from weakening or rephrasing a constraint while keeping the same identifiers.

## Exact-body binding

`manifest.json` stores a SHA-256 digest for every supplied record.

Changing a record body while preserving its ID is therefore a bridge failure until the manifest is deliberately reviewed and updated.

This is **content identity**, not evidence authenticity.

## Review boundary

The example ends with a reviewed TIP record.

A reviewed bridge requires:

- a native TIP status of `reviewed`;
- non-empty review evidence;
- a concrete observed `next_state`.

Strings such as `UNKNOWN`, `UNOBSERVED`, and `PENDING` cannot close the bridge.

## Four separate report questions

A PASS result intentionally keeps four questions separate:

1. **Record validity** — did the selected native/schema validators accept each record?
2. **Cross-record consistency** — do the supplied records preserve the agreed handoffs?
3. **Evidence authenticity** — **NOT EVALUATED** by this bridge.
4. **Execution authority** — **NOT GRANTED** by this bridge.

A valid bridge never authorizes a real payment or external provider call.

## Run

The GitHub workflow checks out the pinned public repositories and runs:

```bash
python scripts/validate_native_record_bridge.py \
  --dif-root .bridge/DIF \
  --drp-root .bridge/DRP \
  --tip-root .bridge/TIP

DIF_ROOT=.bridge/DIF \
DRP_ROOT=.bridge/DRP \
TIP_ROOT=.bridge/TIP \
python -m unittest tests.test_native_record_bridge -v
```

## Adversarial regressions

The tests require rejection of:

- a changed body with an unchanged ID and stale digest;
- false or missing DIF confirmation;
- a missing original record;
- a DRP status that cannot be mechanically mapped from DI permission;
- mismatched cross-record references;
- a TIP record that rephrases or drops selected DI constraints;
- an unobserved TIP next state;
- a repository-version mismatch.

## Provider neutrality

This example does not imply that any external company uses, implements, endorses, or conforms to DIF, DI, DRP, TIP, or this bridge.
