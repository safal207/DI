# DI v0.5 Stabilization Notes

Status: **release candidate**

No Git tag or GitHub Release has been created yet. A public marker should be created only after the stabilization changes merge into `main` and the full workflow succeeds on that exact merge commit.

## Baseline evidence

The v0.5 implementation was merged into `main` as:

```text
6a544c91fdb139ba377f239181b965c631733c0d
```

The `Validate DI fixtures` workflow completed successfully for that commit in run `32935534981`.

This stabilization pass adds documentation alignment, a corrected contributor example, and a pinned credential-boundary workflow. Those changes require a new green `main` workflow before any release marker is justified.

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

The release candidate includes:

- stable `logical_operation_id` and `effect_key` records;
- ordered commit-outcome observations;
- authoritative resolution of ambiguous commit state;
- safe next-action rules for `committed`, `not_committed`, and `still_unknown`;
- state-effect evidence before success closure;
- `ambiguous-commit-v0.5` CLI conformance profile;
- mutation-based negative checks for effect-key drift, contradictory resolution, duplicate committed effects, unsafe retries, and unsupported success claims.

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

DI remains a protocol and conformance repository, not an execution engine, transaction coordinator, lock service, or provider runtime.

## Release gate

A `v0.5-draft` marker is justified only when all of the following are true:

```text
stabilization PR merged
AND
full main workflow success
AND
credential-boundary workflow success
AND
README / ROADMAP / conformance docs agree
AND
no known release-blocking regression remains
```
