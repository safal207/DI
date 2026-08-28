# External Provider Sandbox Evidence Runbook

Status: **ready-to-run procedure; no provider credential is stored here**

The deterministic sandbox proves that the DI v0.5 method and validator operate
as intended. The next evidence level is a provider test-mode or sandbox trace.

This runbook defines that step without pretending it has already occurred.

## Preconditions

A run begins only when all of the following are true:

- the provider offers an approved sandbox or test mode;
- the account owner authorizes the selected mutation flow;
- test-only credentials are supplied through an approved secret mechanism;
- no credential is committed, printed into reports, or copied into public
  discussions;
- the expected idempotency, lookup, retry, and terminal-state contract is known;
- stop conditions and prohibited actions are written down;
- no production customer funds or production state are involved.

## Selected scenario

Use one mutation where duplicate effects matter, for example:

```text
create test payment
→ lose or ignore the first acknowledgement
→ preserve the original operation identity and effect key
→ recover authoritative commit state
→ decide whether replay is allowed
→ observe the terminal state effect
```

## Evidence to capture

Capture references, not secrets:

1. logical operation ID;
2. stable idempotency/effect key hash or redacted identifier;
3. request parameter fingerprint;
4. provider request or correlation ID;
5. local transport outcome;
6. authoritative lookup or provider-event result;
7. committed provider effect ID in test mode;
8. terminal state and observation timestamp;
9. every retry decision and its justification;
10. proof that no second mutation identity was created.

## Procedure

### 1. Freeze the intended operation

Record:

```text
one intended test effect
amount / asset / recipient in test mode
stable logical_operation_id
stable effect_key
```

### 2. Submit once

Send the authorized test mutation with the stable effect key.

The harness may deliberately discard the local success response or terminate
its own read path after dispatch. It must not falsify or alter the provider's
state.

### 3. Treat the local result as ambiguous

```text
no trusted acknowledgement
→ local commit state = UNKNOWN
```

Do not infer `not_committed` from a timeout or client-side exception.

### 4. Recover authoritative state

Use the strongest provider-supported public/test-mode mechanism, such as:

- lookup by provider operation ID;
- lookup by stable effect key;
- same-key replay with documented semantics;
- signed provider event;
- sandbox ledger or transaction query.

Record which source is considered authoritative and why.

### 5. Apply the next-action gate

```text
committed
→ ACCEPT_EXISTING_EFFECT or STOP

not_committed
→ RETRY_SAME_EFFECT_KEY or STOP

still_unknown
→ STOP or HUMAN_ESCALATION
```

A new key is not a retry of the same represented operation.

### 6. Observe the state effect

Record the terminal test-mode state separately from the fact that a request was
dispatched.

```text
execution receipt != state-effect receipt
```

### 7. Translate to a DI trace

Map only observed facts into the v0.5 shape. Keep these labels separate:

- provider guarantee;
- observed provider fact;
- local runtime fact;
- DI inference;
- unresolved assumption.

### 8. Validate and mutate

Run:

```bash
python scripts/di-conformance.py \
  path/to/redacted-provider-trace.json \
  --profile ambiguous-commit-v0.5 \
  --pretty
```

Then mutate the redacted trace to verify that effect-key drift, contradictory
resolution, duplicate effects, unsafe retry, and missing state evidence fail.

## Required outputs

```text
redacted provider trace
+ machine-readable PASS/FAIL report
+ reproduction notes
+ evidence inventory
+ unresolved assumptions
+ explicit claim boundary
```

## Publication rule

A provider may be named only when attribution is accurate and the evidence is
safe to publish.

A public case must never imply that the provider:

- uses DI;
- endorses DI;
- was comprehensively audited;
- guarantees exactly-once behavior beyond its documented contract;
- approved publication when it did not.

The safe default is an anonymized case until provider naming and evidence
boundaries are reviewed.

## Current status

```text
deterministic provider-neutral sandbox → complete
live provider sandbox trace           → not yet captured
```

The second line requires externally supplied test access. Its absence does not
invalidate the deterministic case, but it limits the claim to local executable
and conformance evidence.
