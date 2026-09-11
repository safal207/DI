# DI multilingual discovery

DI now has five repository-native discovery documents that explain the same evidence-bound ambiguous-payment recovery case in natural problem language while preserving the same technical tokens, evidence numbers, and claim boundaries.

| Language | Repository discovery page |
|---|---|
| English | [Payment timeout recovery](docs/i18n/payment-recovery.en.md) |
| Русский | [Восстановление платежа после таймаута](docs/i18n/payment-recovery.ru.md) |
| Deutsch | [Zahlungs-Timeout-Wiederherstellung](docs/i18n/payment-recovery.de.md) |
| Español | [Recuperación de pagos tras un timeout](docs/i18n/payment-recovery.es.md) |
| 简体中文 | [支付超时恢复](docs/i18n/payment-recovery.zh.md) |

## Canonical technical language

Localized explanations do not translate or weaken normative identifiers such as:

`PASS`, `RISK`, `UNKNOWN`, `NOT_COMMITTED`, `ACCEPT_EXISTING_EFFECT`, `DUPLICATE_EFFECT_RISK`, `DIF`, `DI`, `DRP`, and `TIP`.

The evidence-bound reference result also stays the same across languages:

- stored effects: `1`
- duplicate effects: `0`
- unsafe mutations rejected: `6 / 6`

## Architecture milestone

The first canonical native-record integration of `DIF → DI → DRP → TIP` was accepted into DI `main` through PR #33 on 2026-09-11. This is an internal architecture milestone: it validates selected record shapes, pinned versions, body binding, and cross-record consistency. It is not external product validation, provider endorsement, production-safety proof, evidence authentication, or execution authority.

## Live demo boundary

The current public interactive demo remains:

https://di-ambiguous-payment-recovery.lovable.app

As of this document, only the currently verified live route should be advertised. The prepared `/ru`, `/de`, `/es`, and `/zh` Lovable routes are **not claimed as published** until the hosting project can be edited, redeployed, and smoke-tested. The current blocker is hosting-workspace credits, not a protocol dependency.

## Discovery principles

These documents use natural phrases that people actually search for—payment timeout recovery, payment idempotency, duplicate-payment prevention, AI-agent payment safety and their localized equivalents—without keyword stuffing or deprecated `meta keywords` tricks.

GitHub remains the source of truth for schemas, validators, evidence, and canonical integration artifacts.
