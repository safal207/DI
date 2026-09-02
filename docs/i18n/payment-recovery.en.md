# Payment timeout recovery, payment idempotency, and duplicate-payment prevention

This page is the English discovery adapter for **Doability Intelligence (DI)** and the provider-neutral ambiguous-payment recovery demo.

A payment API may complete the financial mutation before its response reaches the client. When the acknowledgement is lost, the local state is `UNKNOWN`. That does **not** mean `NOT_COMMITTED`.

The safe sequence is:

```text
one logical operation
→ acknowledgement lost
→ authoritative lookup
→ committed effect recovered
→ ACCEPT_EXISTING_EFFECT
→ 1 stored effect, 0 duplicate effects
```

A blind retry without resolving the first outcome leaves `DUPLICATE_EFFECT_RISK` open.

## Problems this model helps describe

- **payment timeout recovery** — establish authoritative transaction state before another financial action;
- **payment idempotency** — preserve one logical operation and one effect identity across retries;
- **duplicate payment prevention** — block blind retry while the prior commit outcome is unknown;
- **AI agent payment safety** — require evidence before an autonomous agent pays again.

## Decision and transition stack

```text
DIF → clarify human intent
DI  → clarify feasibility, permission, limits, risk, and unknowns
DRP → preserve the committed decision and rationale
TIP → reason about the transition and review the observed result
```

The projects remain independent. The demo is an external validation case, not a claim that a payment provider uses or endorses DI.

## Evidence

The deterministic reference result is `PASS`: one committed effect, zero duplicate effects, and `6 / 6` unsafe mutations rejected.

- [Live English demo](https://di-ambiguous-payment-recovery.lovable.app)
- [Canonical repository](https://github.com/safal207/DI)
- [Evidence pack](https://github.com/safal207/DI/tree/main/evidence/ambiguous-payment-sandbox)
- [Case study](https://github.com/safal207/DI/blob/main/docs/case-study-ambiguous-payment-recovery.md)
