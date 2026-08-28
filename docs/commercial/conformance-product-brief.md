# DI Conformance Kit — Product Brief

Status: **open-core product hypothesis**

## Product promise

> Turn a high-risk mutation trace into a portable PASS/FAIL integrity report without pretending to be the runtime that executed it.

## Initial wedge

The first narrow use case is ambiguous mutation recovery:

```text
mutation may commit
→ acknowledgement is lost
→ local state becomes unknown
→ recovery must preserve one effect identity
→ evidence determines the next action
```

Target flows:

- agent payments;
- wallets and transfers;
- refunds;
- order and subscription creation;
- smart-contract relays;
- high-risk tool calls;
- multi-worker job execution.

## User

Primary technical users:

- QA and test architects;
- backend and payments engineers;
- platform / reliability engineers;
- AI-agent infrastructure teams;
- security and assurance reviewers;
- system analysts defining integration contracts.

Economic buyer:

- Head of Engineering;
- VP Platform / Payments;
- CTO of an agentic or financial product;
- quality or risk owner responsible for release confidence.

## Input and output

Input:

```text
trace.json
+ selected conformance profile
```

Output:

```json
{
  "profile": "ambiguous-commit-v0.5",
  "status": "PASS",
  "error_count": 0,
  "errors": []
}
```

A useful enterprise output also includes:

- evidence references;
- provenance;
- stable error codes;
- mutation coverage;
- claim boundary;
- CI decision;
- remediation owner;
- review history.

## Current proof

The repository already contains:

- four additive conformance profiles;
- JSON schemas and semantic validators;
- a CLI with machine-readable reports;
- positive and negative fixtures;
- multi-agent ownership and lease/fencing checks;
- ambiguous-commit recovery rules;
- deterministic sandbox evidence;
- six mutation tests;
- CI reproducibility and credential-boundary gates;
- a published `v0.5-draft` checkpoint.

## MVP

The smallest product is not a dashboard.

It is:

```text
1. trace adapter template
2. local CLI
3. CI action
4. evidence pack
5. human-readable report
```

MVP workflow:

```text
team emits sanitized trace
↓
DI profile validates trace
↓
PASS → release gate may continue
FAIL → stable errors and evidence links
BLOCKED → missing evidence is explicit
```

## Open-core boundary

### Open source

- protocol documents;
- core schemas;
- reference validators;
- CLI;
- canonical fixtures;
- provider-neutral sandbox;
- public benchmark cases.

### Paid

- provider-specific adapters;
- private trace mapping;
- custom conformance profiles only when evidence justifies them;
- managed CI integration;
- evidence retention and audit export;
- release-gate support;
- incident trace analysis;
- enterprise support and training.

The open source layer creates trust and reproducibility. Paid value comes from integration, private evidence, operational adoption, and maintenance.

## Commercial ladder

### Level 1 — paid calibration

```text
USD 1,500–3,000
one flow / one failure surface
```

### Level 2 — implementation sprint

```text
USD 5,000–12,000
adapter + mutation pack + CI gate
```

### Level 3 — managed team plan

```text
USD 2,000–5,000 per month
limited profiles, support, evidence packs
```

### Level 4 — enterprise assurance

```text
USD 10,000–30,000+ per month
private adapters, release gates, incident support, governance
```

These are internal pricing hypotheses to test, not promises of market acceptance.

## Path to scale

Services are the learning engine, not the final ceiling:

```text
paid pilot
→ repeated failure pattern
→ reusable adapter
→ packaged profile
→ CI integration
→ recurring plan
```

A hypothetical USD 1M monthly revenue target could be reached through many mixes, for example:

```text
50 enterprise customers × USD 20,000/month
or
200 team customers × USD 5,000/month
or
enterprise subscriptions + implementation partners + paid pilots
```

This is arithmetic, not a forecast. The next validation target is the first repeatable paid use case, not scale theatre.

## Differentiation

DI should not compete by claiming a universal AI safety platform.

The differentiator is a precise seam:

```text
what was intended
→ what was feasible
→ what was authorized
→ what identity executed
→ what actually committed
→ what state was observed
→ what action is allowed next
```

Compared with generic logging:

- IDs must remain linked;
- lifecycle rules are validated;
- unsafe mutations are tested;
- PASS has an explicit limit;
- missing evidence can produce `BLOCKED` rather than invented certainty.

## Moat hypothesis

Potential compounding assets:

- a library of real failure traces;
- provider adapters;
- mutation packs;
- stable conformance error taxonomy;
- benchmark data;
- integration credibility in high-risk domains;
- cross-provider understanding without leaking private evidence.

The moat is not the JSON schema alone. It is the growing evidence graph and the ability to turn incidents into reusable conformance gates.

## Risks

- teams may not emit trustworthy traces;
- integration cost may exceed perceived value;
- providers already solve part of the problem;
- too many profiles can make the product incoherent;
- a PASS can be misunderstood as runtime proof;
- open-source users may need education before buying;
- enterprise sales cycles may be long.

Mitigations:

- stay narrow;
- sell one bounded failure surface first;
- preserve claim boundaries everywhere;
- require external evidence before new architecture;
- make adapters client-run when secrets are involved;
- measure investigation time and defect prevention in paid pilots.

## Metrics for the first ten pilots

Track:

- percentage of prospects with a qualifying sandbox;
- time to produce first valid trace;
- number of material findings;
- mutations caught;
- adapter reuse rate;
- pilot-to-retainer conversion;
- customer time saved during incident/release review;
- false-positive and blocked-result rate;
- willingness to pay for recurring CI gating.

## Product decision now

```text
BUILD: adapter + CLI + evidence-pack workflow
DO NOT BUILD YET: large dashboard, generic agent platform, broad policy engine
```

The next product milestone is one external team paying to apply the existing v0.5 model to a real sandbox flow.
