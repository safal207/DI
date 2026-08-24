# DI Conformance Test Kit v0.3

Status: Draft developer interface

## Goal

The internal validators prove that DI's own fixtures are coherent.

The Conformance Test Kit exposes that logic as a simple interface for **external traces**:

```text
external AI / workflow trace
↓
DI conformance profile
↓
PASS or FAIL
↓
structured errors
```

Supported profiles:

```text
end-to-end-integrity-v0.2
multi-agent-dispatch-v0.3
lease-split-brain-v0.4
```

The profiles are additive in scope:

```text
v0.2 → decision-to-evidence integrity
v0.3 → multi-agent ownership continuity
v0.4 → lease expiry + fencing against stale executors
```

## CLI

Default full-chain profile:

```bash
python scripts/di-conformance.py path/to/trace.json --pretty
```

Explicit v0.2 profile:

```bash
python scripts/di-conformance.py path/to/trace.json \
  --profile end-to-end-integrity-v0.2 \
  --pretty
```

Multi-agent dispatch profile:

```bash
python scripts/di-conformance.py path/to/multi-agent-trace.json \
  --profile multi-agent-dispatch-v0.3 \
  --pretty
```

Lease / split-brain profile:

```bash
python scripts/di-conformance.py path/to/lease-trace.json \
  --profile lease-split-brain-v0.4 \
  --pretty
```

A conforming trace exits `0`.

A non-conforming trace exits `1`.

## PASS report

Shape:

```json
{
  "report_version": "0.1",
  "profile": "lease-split-brain-v0.4",
  "input_file": "path/to/lease-trace.json",
  "status": "PASS",
  "error_count": 0,
  "errors": []
}
```

## FAIL report

Example shape:

```json
{
  "report_version": "0.1",
  "profile": "lease-split-brain-v0.4",
  "input_file": "path/to/lease-trace.json",
  "status": "FAIL",
  "error_count": 2,
  "errors": [
    "$.dispatch_attempt_receipts: exactly one attempt may be accepted, got 2",
    "$.execution_receipt.dispatch_fencing_token: must bind to accepted attempt fencing token"
  ]
}
```

The exact number and combination of errors depends on the supplied trace.

## Report schema

Machine-readable output is described by:

```text
schemas/conformance-report.schema.json
```

## Profile: end-to-end-integrity-v0.2

Reference trace:

```text
fixtures/valid-end-to-end-integrity-v0.2.json
```

Implementation:

```text
scripts/validate-end-to-end-integrity.py
```

A PASS means that, according to the supplied trace:

```text
intent identity is preserved
AND
chosen path was feasible and evaluated
AND
committed path was revalidated
AND
TIP did not substitute another path
AND
recovery action stayed bound to execution mode
AND
use-time authority stayed bound to the decision
AND
single-use authority was consumed before dispatch
AND
execution stayed bound to the consumed dispatch
AND
observed effect matched the TIP target
AND
review used the accepted fresh state generation
```

## Profile: multi-agent-dispatch-v0.3

Reference trace:

```text
fixtures/valid-multi-agent-dispatch-takeover-v0.3.json
```

Implementation:

```text
scripts/validate-multi-agent-dispatch.py
```

A PASS means that, according to the supplied trace:

```text
one recovery decision was bound to one consumed dispatch
AND
ownership started with one generation-1 claim
AND
every ownership change was an explicit linear transfer
AND
ownership generations increased exactly by one
AND
the dispatch_id remained stable across worker changes
AND
execution was performed by the latest recorded owner
AND
execution bound to the latest ownership event and generation
```

The central v0.3 law is:

```text
new worker != new permission
```

See:

```text
docs/multi-agent-dispatch-integrity-v0.3.md
schemas/dispatch-ownership-event.schema.json
```

## Profile: lease-split-brain-v0.4

Reference trace:

```text
fixtures/valid-lease-split-brain-recovery-v0.4.json
```

Implementation:

```text
scripts/validate-lease-split-brain.py
```

This profile reuses the v0.3 ownership validator and adds lease/fencing semantics.

A PASS means that, according to the supplied trace:

```text
v0.3 ownership continuity still holds
AND
every represented ownership epoch has lease evidence
AND
lease-expiry takeover occurs only after predecessor expiry
AND
fencing tokens strictly advance across represented lease epochs
AND
stale worker attempts are rejected
AND
exactly one dispatch attempt is accepted
AND
the accepted attempt belongs to the latest owner and current lease
AND
execution binds to that exact lease, fencing token, and accepted attempt
AND
execution occurs inside the current lease window
```

The central v0.4 law is:

```text
worker belief != side-effect admission
```

A newer fencing token must make older execution epochs rejectable.

See:

```text
docs/lease-split-brain-integrity-v0.4.md
schemas/dispatch-lease-receipt.schema.json
schemas/dispatch-attempt-receipt.schema.json
```

## What a PASS does not mean

PASS does not independently prove:

```text
external evidence is truthful
runtime database operations were atomic
a distributed lock or lease service actually enforced the trace
provider APIs behaved exactly as claimed
human intent was ethically obtained outside the represented DIF confirmation
```

Those are evidence, runtime, coordination, or upstream protocol boundaries.

In particular:

```text
ownership event chain != distributed mutex
lease receipt != runtime lease implementation
fencing evidence != proof the side-effect owner enforced fencing atomically
```

## Integration pattern

A CI pipeline can treat the command as a gate:

```text
produce trace.json
↓
di-conformance.py trace.json --profile <profile>
↓
exit 0 → continue
exit 1 → block / inspect errors
```

An agent evaluator can store the JSON report next to the trace as an auditable conformance artifact.

## Profile design rule

New profiles should reuse canonical invariants rather than fork their semantics.

That is why v0.4 imports and reuses the v0.3 ownership validator before applying lease/fencing checks.

A narrow profile may prove one seam without claiming that every upstream or downstream property was independently verified.

## Core idea

```text
protocol documents
↓
validators
↓
conformance profiles
↓
external traces
↓
portable PASS / FAIL evidence
```

The profile ladder now reaches a genuinely distributed failure mode: a stale executor may still be alive, but it must not be admissible once a newer fencing epoch exists.
