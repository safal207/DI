# DI Architecture Freeze — v0.5

Status: **active**

Effective checkpoint:

```text
Git tag / prerelease: v0.5-draft
Validated source commit: a35a990c0c3d7715551b1cdaf933a58411f26c2b
```

## Purpose

The v0.2–v0.5 profile ladder is now wide enough to test real systems. The next priority is external evidence, not another speculative layer.

This freeze prevents architecture growth from outrunning validation.

```text
build
→ validate internally
→ publish checkpoint
→ test against external traces
→ change architecture only when evidence requires it
```

## Frozen profile ladder

```text
v0.2 — end-to-end decision-to-evidence integrity
v0.3 — multi-agent dispatch ownership continuity
v0.4 — lease expiry and split-brain fencing
v0.5 — ambiguous commit recovery and stable effect identity
```

The following central laws remain the current checkpoint contract:

```text
capability != permission
new worker != new mutation permission
worker belief != side-effect admission
transport outcome != commit outcome
unknown commit != not committed
retry != new effect identity
```

## Changes allowed during the freeze

The freeze does not stop useful work. The following remain allowed:

- bug fixes that preserve the published claim boundary;
- new positive and negative fixtures for existing profiles;
- mutation tests that prove validators reject unsafe traces;
- external trace adapters that do not copy provider secrets into fixtures;
- documentation corrections and clearer examples;
- stable error codes and machine-readable reports;
- benchmark packs using already-defined invariants;
- security fixes and credential-boundary improvements;
- provider-neutral sandbox tooling;
- real sandbox/test-mode evidence mapped into the existing trace model.

## Changes blocked during the freeze

The following require the v0.6 admission gate:

- a new conformance profile version;
- a new normative architecture layer;
- broadening DI into an execution engine, transaction coordinator, policy engine, lock service, or idempotency store;
- redefining DIF, DRP, or TIP semantics from this repository;
- claiming exactly-once runtime behavior from trace validation alone;
- adding provider-specific guarantees as if they were DI guarantees;
- weakening a current invariant to make an external trace pass.

## v0.6 admission gate

A v0.6 proposal is admitted only when all of the following exist:

1. **External evidence** — a provider sandbox, test-mode, public incident, or reproducible distributed-system trace.
2. **Minimal counterexample** — the smallest trace showing that current v0.2–v0.5 semantics are insufficient.
3. **Current-profile result** — either an unsafe trace incorrectly passes, or a valid integrity property cannot be represented without distortion.
4. **Mutation test** — a test that demonstrates the proposed invariant catches the counterexample.
5. **Boundary statement** — what the new rule proves and what it still cannot prove.
6. **Non-collapse review** — confirmation that the change belongs in DI conformance rather than DIF, DRP, TIP, ContractGraph-QA, or a runtime system.

The admission decision should be recorded in a dedicated issue before schema or validator implementation begins.

## Security exception

A security or evidence-integrity defect may be fixed immediately without waiting for the full admission gate.

The fix must remain narrow and include:

- a regression fixture;
- the affected claim boundary;
- evidence that the fix does not silently broaden conformance claims.

## External validation rule

External companies and products are validation cases, not members of the stack.

```text
public/provider behavior
→ observable trace
→ DI adapter
→ conformance result
→ limitations
```

A named case study must distinguish:

- provider-documented guarantees;
- facts actually observed in the trace;
- DI's interpretation of those facts;
- assumptions that remain outside the evidence.

## Exit condition

The freeze ends only when:

```text
v0.6 admission gate = satisfied
AND
new proposal reviewed against project boundaries
AND
current checkpoint remains reproducible
```

Until then, the correct direction is:

> More evidence, fewer speculative layers.
