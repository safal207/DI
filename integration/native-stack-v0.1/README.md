# Native-stack conformance bridge v0.1

Status: **opt-in integration proof**

This directory tests one provider-neutral chain using **full canonical-format
artifacts** for DIF, DI, DRP, and TIP plus DI's existing reduced cross-stack
projection:

```text
full DIF ConfirmedIntent
→ full DI feasibility check
→ full DRP decision record
→ full TIP transition record
→ reduced DI projection envelope
```

It is **not a fifth protocol**. It does not merge the four projects, redefine
their canonical lifecycle states, or make the reduced DI projection canonical.
Each upstream repository remains authoritative for its own record shape and
native semantic rules.

## Exact pins

`manifest.json` pins the repository commits and validator/schema paths used by
this proof. The integration validator refuses an external checkout whose `HEAD`
does not exactly match the pin. The DI base commit is recorded as provenance
and must remain an ancestor of the integration branch, so the bridge does not
self-break when this directory itself is committed.

## What is validated

Run after preparing the pinned external checkouts:

```bash
python -m pip install -r integration/native-stack-v0.1/requirements-integration.txt

python integration/native-stack-v0.1/validate_native_stack.py \
  --dif-root /path/to/DIF \
  --drp-root /path/to/DRP \
  --tip-root /path/to/transition-intelligence-protocol

python integration/native-stack-v0.1/test_native_stack_bridge.py \
  --dif-root /path/to/DIF \
  --drp-root /path/to/DRP \
  --tip-root /path/to/transition-intelligence-protocol -v
```

The baseline check:

- validates the full DIF ConfirmedIntent against the pinned Draft 2020-12
  schema with `FormatChecker`;
- validates the full DI feasibility record and reduced projection through DI's
  existing validator code;
- runs the pinned DRP native validator on the full DRP record;
- runs the pinned TIP native CLI on the full TIP record;
- checks explicit cross-record identity and status mappings;
- checks SHA-256 body bindings so a changed canonical body with an unchanged ID
  is detected;
- requires TIP review evidence and `next_state` before a reviewed TIP record can
  close the DI projection.

The negative matrix mutates one logical boundary at a time and requires a
specific expected error fragment. A generic crash is never a passing negative
test.

## Boundaries

Passing means only that **these exact pinned files** validated and mapped under
the checks above.

It does **not** prove:

- that an evidence reference is authentic, signed, complete, or available;
- that any payment provider uses or endorses these projects;
- settlement finality or universal exactly-once execution;
- execution authority or permission to mutate any external system;
- causal truth of the recorded explanation;
- compatibility of arbitrary future versions of DIF, DI, DRP, or TIP.

No provider adapter, credential, network payment call, or production state is
used by this integration.
