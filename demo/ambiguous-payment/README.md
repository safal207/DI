# DI Ambiguous-Payment Client Demo

A mobile-first, static, client-facing presentation of the canonical DI v0.5 ambiguous-payment evidence pack.

## Purpose

The demo answers one question in under 90 seconds:

> Did the payment fail — or did only the response fail?

It compares:

- an illustrative blind-retry risk path; and
- the evidence-backed DI recovery path from the deterministic sandbox.

## Source of truth

The demo is not a second implementation of DI. Its measured safe-path values are generated from:

- `evidence/ambiguous-payment-sandbox/summary.json`
- `evidence/ambiguous-payment-sandbox/mutation-report.json`

Run:

```bash
python scripts/build-client-demo-data.py --check
python scripts/validate-client-demo.py
```

## Local preview

From the repository root:

```bash
python -m http.server 8000
```

Then open:

```text
http://localhost:8000/demo/ambiguous-payment/
```

## GitHub Pages

The repository includes a manual deployment workflow. GitHub Pages must first be enabled with **GitHub Actions** as the publishing source. Then run **Deploy DI client demo** from the Actions tab.

Until Pages is enabled, CI still validates the demo and publishes it as a downloadable workflow artifact.

## Claim boundary

This is a deterministic provider-neutral demonstration. It does not prove external exactly-once behavior, provider endorsement, production safety, global completeness, or the absence of every possible duplicate effect.
