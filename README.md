# Doability Intelligence (DI)

[![Validate DI fixtures](https://github.com/safal207/DI/actions/workflows/validate-fixtures.yml/badge.svg)](https://github.com/safal207/DI/actions/workflows/validate-fixtures.yml)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

**Current checkpoint:** v0.5 stabilization candidate. The implementation is merged and validated; a Git tag or GitHub Release has not yet been created.

DI maps what can and cannot be done before a decision becomes a commitment.

> **Do not promise action until limits are understood.**

По-русски:

> **Не обещай действие, пока не понятны возможности и границы.**

## What DI is

DI is a narrow pre-decision layer for clarifying:

- capabilities;
- permissions;
- limitations;
- constraints;
- risks and unknowns;
- reversible and blocked paths;
- whether a decision is ready to become a commitment.

DI does not execute the action and does not silently turn technical capability into permission.

```text
request
→ capability and limitation mapping
→ feasible / conditional / blocked / unknown
→ decision boundary
```

## Decision and transition integrity stack

DI cooperates with three independent projects:

```text
DIF → clarify human intent
DI  → clarify feasibility and limits
DRP → preserve the committed decision and rationale
TIP → reason about the transition and review the observed result
```

Canonical repositories:

- [DIF / DeepIntent Funnel](https://github.com/safal207/DIF)
- [DI / Doability Intelligence](https://github.com/safal207/DI)
- [DRP / Decision Record Protocol](https://github.com/safal207/DRP)
- [TIP / Transition Intelligence Protocol](https://github.com/safal207/transition-intelligence-protocol)

The projects remain separate:

```text
DIF != DI
DI  != DRP
DRP != TIP
TIP != execution engine
```

The cross-repository architecture is documented in [`docs/decision-transition-integrity-stack.md`](docs/decision-transition-integrity-stack.md).

## Current validated architecture

The repository now contains provider-neutral conformance profiles for a wider evidence chain around DI:

```text
Intent
→ Feasibility
→ Strategy
→ Decision
→ Path Revalidation
→ Transition
→ Use-Time Authority
→ Authority Consumption
→ Dispatch Ownership
→ Lease / Fencing Epoch
→ Dispatch Admission
→ Execution
→ Logical Operation Identity
→ Commit Outcome Resolution
→ State Effect
→ Fresh Review
→ Next State
```

This is evidence and conformance tooling. It is not a production transaction coordinator or distributed runtime.

## Profile ladder

| Profile | Protects against |
|---|---|
| `end-to-end-integrity-v0.2` | intent, path, authority, execution, state-effect, and review drift |
| `multi-agent-dispatch-v0.3` | a new worker silently receiving a new mutation permission |
| `lease-split-brain-v0.4` | a stale worker crossing the side-effect boundary after takeover |
| `ambiguous-commit-v0.5` | a lost acknowledgement being mistaken for a failed commit and creating a second effect |

The v0.5 central laws are:

```text
transport outcome != commit outcome
unknown commit != not committed
retry != new effect identity
one committed logical operation -> one committed effect identity
```

See [`docs/decision-transition-integrity-stack-v0.5.md`](docs/decision-transition-integrity-stack-v0.5.md) and [`docs/ambiguous-commit-integrity-v0.5.md`](docs/ambiguous-commit-integrity-v0.5.md).

## Quick start

The repository uses Python standard-library validators.

Run the full fixture suite:

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

Run a machine-readable conformance check:

```bash
python scripts/di-conformance.py \
  fixtures/valid-ambiguous-commit-recovery-v0.5.json \
  --profile ambiguous-commit-v0.5 \
  --pretty
```

Expected shape:

```json
{
  "error_count": 0,
  "errors": [],
  "profile": "ambiguous-commit-v0.5",
  "status": "PASS"
}
```

The exact report also includes `report_version` and `input_file`.

## What PASS means

A PASS means the supplied trace satisfies the selected profile's structural and semantic invariants.

For v0.5, that includes:

- one stable logical-operation identity;
- one stable effect key across ambiguous recovery;
- ordered commit observations;
- no silent conversion of `unknown` into `not_committed`;
- a next action compatible with the resolved commit state;
- matching state-effect evidence before success closure.

## What PASS does not mean

A PASS does not independently prove that:

- external evidence is truthful;
- a database or provider idempotency store was atomic;
- a lease service enforced fencing at runtime;
- a transaction was exactly-once;
- a distributed lock existed;
- network evidence was complete.

Those remain runtime, evidence, and provider boundaries.

## Key documentation

- [`docs/rfc-0001.md`](docs/rfc-0001.md) — original DI specification seed.
- [`docs/concept.md`](docs/concept.md) — DI concept and boundaries.
- [`docs/relation-to-dif-and-drp.md`](docs/relation-to-dif-and-drp.md) — DI's place between intent and commitment.
- [`docs/decision-transition-integrity-stack.md`](docs/decision-transition-integrity-stack.md) — cross-stack architecture.
- [`docs/conformance-test-kit.md`](docs/conformance-test-kit.md) — CLI profiles and report contract.
- [`docs/lease-split-brain-integrity-v0.4.md`](docs/lease-split-brain-integrity-v0.4.md) — lease and fencing semantics.
- [`docs/ambiguous-commit-integrity-v0.5.md`](docs/ambiguous-commit-integrity-v0.5.md) — lost-acknowledgement recovery.
- [`docs/case-study-stripe-payment-recovery.md`](docs/case-study-stripe-payment-recovery.md) — public-documentation mapping, not a live Stripe integration.
- [`RELEASE_NOTES.md`](RELEASE_NOTES.md) — v0.5 stabilization scope and release gate.
- [`ROADMAP.md`](ROADMAP.md) — current maturity and next priorities.

## Machine-readable artifacts

Important schemas include:

- [`schemas/decision-transition-envelope.schema.json`](schemas/decision-transition-envelope.schema.json)
- [`schemas/recovery-decision-matrix.schema.json`](schemas/recovery-decision-matrix.schema.json)
- [`schemas/use-time-authority-receipt.schema.json`](schemas/use-time-authority-receipt.schema.json)
- [`schemas/authority-consumption-receipt.schema.json`](schemas/authority-consumption-receipt.schema.json)
- [`schemas/dispatch-ownership-event.schema.json`](schemas/dispatch-ownership-event.schema.json)
- [`schemas/dispatch-lease-receipt.schema.json`](schemas/dispatch-lease-receipt.schema.json)
- [`schemas/dispatch-attempt-receipt.schema.json`](schemas/dispatch-attempt-receipt.schema.json)
- [`schemas/logical-operation.schema.json`](schemas/logical-operation.schema.json)
- [`schemas/commit-outcome-receipt.schema.json`](schemas/commit-outcome-receipt.schema.json)
- [`schemas/commit-resolution.schema.json`](schemas/commit-resolution.schema.json)
- [`schemas/state-effect-receipt.schema.json`](schemas/state-effect-receipt.schema.json)
- [`schemas/conformance-report.schema.json`](schemas/conformance-report.schema.json)

See [`MANIFEST.md`](MANIFEST.md) for the current fixture and validator map.

## Examples

- [`examples/ai-agent-support.md`](examples/ai-agent-support.md)
- [`examples/startup-plan.md`](examples/startup-plan.md)
- [`examples/qa-automation.md`](examples/qa-automation.md)
- [`examples/personal-productivity-assistant.md`](examples/personal-productivity-assistant.md) — adapted from the first-time contribution in PR #9.

Examples describe feasibility boundaries. They do not grant real-world authority.

## Credential boundary

The repository also runs a read-only credential-boundary scan through a reusable ContractGraph-QA workflow pinned to an immutable commit. The caller grants only:

```text
contents: read
```

The scan does not add, read, or rotate external credentials. Its purpose is to detect credential material accidentally crossing the tracked repository boundary.

## External validation rule

Companies, providers, and public APIs are validation cases, not members of DI, DIF, DRP, or TIP.

A named case must distinguish clearly between:

```text
public provider guarantee
our inference from that guarantee
observed sandbox evidence
unverified runtime assumption
```

## Project status

- v0.1 seed protocol: complete.
- v0.2 end-to-end integrity: complete.
- v0.3 multi-agent ownership: complete.
- v0.4 lease and split-brain fencing: complete.
- v0.5 ambiguous commit recovery: implemented and validated.
- stabilization and public release marker: in progress.

DI remains intentionally provider-neutral, inspectable, and fail-closed on broken identity chains.

## Contributing

Focused contributions are welcome. Useful areas include:

- realistic positive and negative traces;
- clearer validator errors;
- external sandbox mappings with accurate attribution;
- protocol terminology and documentation consistency;
- narrow conformance profiles that reuse existing invariants.

Start with [`CONTRIBUTING.md`](CONTRIBUTING.md) and the open `good first issue` / `help wanted` tasks.

## License

MIT — see [`LICENSE`](LICENSE).
