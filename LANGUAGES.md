# DI multilingual discovery adapters

The DI ambiguous-payment demonstration has five language adapters:

| Language | Discovery document | Static route source | Adapter contract |
|---|---|---|---|
| English | [English](docs/i18n/payment-recovery.en.md) | [`demo/ambiguous-payment/en/`](demo/ambiguous-payment/en/) | [`adapters/en.json`](demo/ambiguous-payment/adapters/en.json) |
| Русский | [Русский](docs/i18n/payment-recovery.ru.md) | [`demo/ambiguous-payment/ru/`](demo/ambiguous-payment/ru/) | [`adapters/ru.json`](demo/ambiguous-payment/adapters/ru.json) |
| Deutsch | [Deutsch](docs/i18n/payment-recovery.de.md) | [`demo/ambiguous-payment/de/`](demo/ambiguous-payment/de/) | [`adapters/de.json`](demo/ambiguous-payment/adapters/de.json) |
| Español | [Español](docs/i18n/payment-recovery.es.md) | [`demo/ambiguous-payment/es/`](demo/ambiguous-payment/es/) | [`adapters/es.json`](demo/ambiguous-payment/adapters/es.json) |
| 简体中文 | [简体中文](docs/i18n/payment-recovery.zh.md) | [`demo/ambiguous-payment/zh/`](demo/ambiguous-payment/zh/) | [`adapters/zh.json`](demo/ambiguous-payment/adapters/zh.json) |

## What remains canonical in every language

Human explanations and search phrasing are localized. Normative technical identifiers are never translated:

```text
PASS
RISK
UNKNOWN
NOT_COMMITTED
ACCEPT_EXISTING_EFFECT
DUPLICATE_EFFECT_RISK
DIF
DI
DRP
TIP
ambiguous-commit-v0.5
```

Measured evidence also remains identical:

```text
stored effects: 1
duplicate effects: 0
unsafe mutations rejected: 6 / 6
```

## Discovery and SEO contract

Every language route carries:

- a unique localized title and description;
- the correct HTML `lang`;
- canonical URL;
- reciprocal `hreflang` for `en`, `ru`, `de`, `es`, `zh-CN`, and `x-default`;
- localized Open Graph metadata;
- `WebApplication` JSON-LD with `inLanguage`;
- a visible language switcher;
- natural problem-language rather than keyword stuffing;
- the public GitHub repository as source of truth;
- the same provider-neutral claim boundary.

The sitemap and robots files are stored under `demo/ambiguous-payment/`.

## Validate

```bash
python scripts/validate-multilingual-demo.py
python scripts/validate-multilingual-demo.py --self-test
python scripts/validate-client-demo.py
```

The language routes are prepared for the existing GitHub Pages deployment workflow. GitHub Pages still requires the repository-level Pages source to be enabled once. Until then, the current live English interactive demo remains:

https://di-ambiguous-payment-recovery.lovable.app
