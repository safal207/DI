# DI Conformance Test Kit v0.1

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

The first profile is:

```text
end-to-end-integrity-v0.2
```

It checks the complete chain from confirmed intent through feasibility, strategy, decision, transition, authority, execution, observed effect, fresh review, and next state.

## CLI

Run:

```bash
python scripts/di-conformance.py path/to/trace.json --pretty
```

Explicit profile:

```bash
python scripts/di-conformance.py path/to/trace.json \
  --profile end-to-end-integrity-v0.2 \
  --pretty
```

A conforming trace exits `0`.

A non-conforming trace exits `1`.

## PASS report

Shape:

```json
{
  "report_version": "0.1",
  "profile": "end-to-end-integrity-v0.2",
  "input_file": "path/to/trace.json",
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
  "profile": "end-to-end-integrity-v0.2",
  "input_file": "path/to/trace.json",
  "status": "FAIL",
  "error_count": 2,
  "errors": [
    "$.envelope.tip.selected_path_id: path substitution after commitment is forbidden",
    "$.execution_receipt.dispatch_id: must exactly match consumed dispatch_id"
  ]
}
```

The exact number and combination of errors depends on the supplied trace.

## Report schema

Machine-readable output is described by:

```text
schemas/conformance-report.schema.json
```

## Canonical reference

The current reference trace is:

```text
fixtures/valid-end-to-end-integrity-v0.2.json
```

The profile implementation reuses:

```text
scripts/validate-end-to-end-integrity.py
```

This avoids maintaining a second, weaker definition of the same invariants.

## What a PASS means

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

It means the **recorded causal chain is internally conformant**.

## What a PASS does not mean

PASS does not independently prove:

```text
external evidence is truthful
runtime database operations were atomic
provider APIs behaved exactly as claimed
human intent was ethically obtained outside the represented DIF confirmation
```

Those are evidence, runtime, or upstream protocol boundaries.

## Integration pattern

A CI pipeline can treat the command as a gate:

```text
produce trace.json
↓
di-conformance.py trace.json
↓
exit 0 → continue
exit 1 → block / inspect errors
```

An agent evaluator can store the JSON report next to the trace as an auditable conformance artifact.

## Future profiles

The CLI intentionally exposes a `--profile` boundary so later profiles can be added without changing the basic interface.

Possible future profiles may cover narrower slices such as:

```text
strategy-path-binding
recovery-authority-binding
state-effect-freshness
```

They should reuse the same canonical invariants rather than fork their semantics.

## Core idea

```text
protocol documents
↓
validators
↓
conformance profile
↓
external trace
↓
portable PASS / FAIL evidence
```

This is the point where the architecture becomes testable by systems outside the repository.
