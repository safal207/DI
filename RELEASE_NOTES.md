# DI v0.5 Stabilization Notes

Status: **stabilized — public marker pending**

DI v0.5 is implemented, merged, documented, and validated on `main`. No Git tag or GitHub Release has been created yet, so this file does not claim that a public release marker exists.

## Validated commits and workflow evidence

### v0.5 implementation

The ambiguous-commit recovery layer was merged into `main` as:

```text
6a544c91fdb139ba377f239181b965c631733c0d
```

The full `Validate DI fixtures` workflow completed successfully for that commit:

```text
run 32935534981 — success
```

### v0.5 stabilization

The documentation, contributor-example, and credential-boundary stabilization pass was merged into `main` as:

```text
5b821e7b9f87bf553140859a7c2729c83d6d8cd7
```

Both required workflows completed successfully on that exact merge commit:

```text
Validate DI fixtures
run 32943621652 — success

FCRP Credential Boundary
run 32943622429 — success
```

The credential-boundary caller is pinned to immutable ContractGraph-QA commit:

```text
cc1d1e227bbb1a25776819e6f2829bfb7a66ee58
```

and grants only:

```text
contents: read
```

## Profile ladder

```text
v0.2 — end-to-end decision-to-evidence integrity
v0.3 — multi-agent dispatch ownership continuity
v0.4 — lease expiry and split-brain fencing
v0.5 — ambiguous commit recovery and stable effect identity
```

## What v0.5 adds

v0.5 protects the interval after a correctly admitted executor sends a mutation but before the system knows whether the effect committed.

Central laws:

```text
transport outcome != commit outcome
unknown commit != not committed
retry != new effect identity
one committed logical operation -> one committed effect identity
```

The stabilized checkpoint includes:

- stable `logical_operation_id` and `effect_key` records;
- ordered commit-outcome observations;
- authoritative resolution of ambiguous commit state;
- safe next-action rules for `committed`, `not_committed`, and `still_unknown`;
- state-effect evidence before success closure;
- `ambiguous-commit-v0.5` CLI conformance profile;
- mutation-based negative checks for effect-key drift, contradictory resolution, duplicate committed effects, unsafe retries, and unsupported success claims;
- aligned README and roadmap documentation;
- a corrected and attributed contributor example from PR #9;
- a pinned read-only credential-boundary workflow revalidated from current `main`.

## Validation commands

Run the full repository suite:

```bash
python scripts/validate-fixtures.py
python scripts/validate-recovery-binding.py
python scripts/validate-authority-binding.py
python scripts/validate-authority-consumption.py
python scripts/validate-strategy-binding.py
python scripts/validate-decision-replan.py
python scripts/validate-end-to-end-integrity.py
python scripts/validate-multi-agent-dispatch.py
python scripts/validate-lease-split-brain.py
python scripts/validate-ambiguous-commit.py
```

Run the v0.5 external-trace profile:

```bash
python scripts/di-conformance.py \
  fixtures/valid-ambiguous-commit-recovery-v0.5.json \
  --profile ambiguous-commit-v0.5 \
  --pretty
```

## Scope limits

A DI conformance PASS validates the supplied evidence chain. It does **not** independently prove that:

- an external provider or database behaved truthfully;
- an idempotency store was atomic;
- a distributed lease service enforced fencing at runtime;
- a transaction was exactly-once;
- network evidence was complete;
- the represented human intent was ethically obtained outside the supplied record.

DI remains a protocol and conformance repository, not an execution engine, transaction coordinator, lock service, idempotency store, or provider runtime.

## Release gate status

```text
v0.5 implementation merged                 PASS
stabilization merged                       PASS
full validation on stabilization main      PASS
credential-boundary scan on same main      PASS
documentation aligned                      PASS
known release-blocking regression          NONE OBSERVED
Git tag / GitHub Release                    PENDING
```

A `v0.5-draft` public marker may now be created from a later exact `main` commit only after the final bookkeeping changes also pass both workflows. Until that marker exists, the accurate status remains:

> stabilized checkpoint, public release marker pending.
