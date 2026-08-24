# Reference Case: Stripe Payment Recovery Through DI

Status: External semantics mapping, not a live-account integration

This case maps the DI integrity stack onto documented Stripe payment behavior.
It is based on public Stripe API documentation, not on access to a real Stripe account or production transaction.

## External facts used

Stripe documents two relevant behaviors:

1. The Payment Intents API tracks a payment across its lifecycle. Stripe recommends reusing the same PaymentIntent when an interrupted checkout resumes rather than blindly creating a new one.
2. Stripe supports idempotency keys for safely retrying API requests without accidentally performing the same operation twice. For API v1 POST requests, repeated requests with the same idempotency key return the saved result of the first request once endpoint execution has begun; Stripe also checks reused-key parameters for consistency.

References:

- https://docs.stripe.com/payments/payment-intents
- https://docs.stripe.com/api/idempotent_requests

The DI layer does not replace those guarantees. It governs the decision process around when and how an autonomous system may rely on them.

## Scenario

An agent is recovering a payment operation after a network failure.

```text
agent sends payment mutation
↓
connection fails before the agent trusts the response
↓
local state = COMMIT_STATE_UNKNOWN
```

The dangerous shortcut is:

```text
"I did not see success"
↓
"therefore it failed"
↓
create another payment
```

That inference is invalid.

## DI framing

### DIF — confirmed intent

```text
Complete this one intended purchase.
Do not create a duplicate financial action.
```

### DI — what is feasible?

Possible paths can include:

```text
A. Read/recover the existing PaymentIntent state
B. Replay the same intended mutation under the verified idempotency contract
C. Wait for stronger terminal evidence
```

Blocked path:

```text
blind new payment mutation with a new operation identity
while the previous commit state is unresolved
```

### Strategy — compare the paths

Dimensions:

```text
duplicate risk
latency
provider evidence
reversibility
local knowledge of the original PaymentIntent / idempotency key
```

The Strategy layer can recommend a path, but it does not commit the system to that path.

### DRP — commit the actual path

Example:

```text
selected_path_id = B.idempotent-replay
```

This decision means:

```text
same intended operation
+
verified provider idempotency semantics
+
no silent switch to a new payment identity
```

### Path Revalidation — is B still usable?

Before TIP executes the committed path, the system checks the facts the decision depended on.

For example:

```text
original idempotency key still known?
request parameters still identical?
provider contract still applicable to this request?
selected operation identity still the intended one?
```

If those assumptions become invalid or unknown:

```text
B = invalid / unknown
↓
TIP BLOCKED
↓
return to DI / Strategy / new DRP
```

The agent must not silently invent a new key or switch to a new PaymentIntent and call that the old decision.

## Authority boundary

Provider idempotency answers a provider-side question:

```text
Will this repeated API request create the same provider operation twice?
```

DI use-time authority answers a different system question:

```text
Is this autonomous recovery mutation still authorized now?
```

Both can be necessary.

## Single-use local dispatch

Even with a valid Stripe idempotency key, two local workers can race:

```text
worker A sees recovery authorized
worker B sees recovery authorized
```

A provider idempotency contract can reduce provider-side duplicate mutation risk, but it does not by itself prove that the local autonomous system consumed its own recovery permission exactly once.

DI therefore adds:

```text
Use-Time Authority
↓
Authority Consumption
↓
exact use_token + dispatch_id
↓
Execution Receipt
```

The single-use scope is:

```text
(
  authority_id,
  authority_generation,
  recovery_decision_id,
  bound_execution_mode
)
```

Different local tokens do not manufacture a second recovery permission.

## Execution evidence

After dispatch, the system records what was actually executed:

```text
recovery decision id
execution mode
consumed authority receipt
use token
dispatch id
provider/request evidence
```

A request being dispatched is still not proof that the target payment state was reached.

## State effect

The system separately observes authoritative payment state:

```text
expected target state
vs
observed provider state
```

Only matching observed state with evidence can support the intended outcome claim.

## Fresh review

The final review checks that the observed payment evidence is still the accepted state generation and is recent enough for the review policy.

Only then may the chain produce a proven next state such as:

```text
RECOVERY_CONFIRMED
```

## What Stripe provides vs what DI adds

```text
Stripe PaymentIntent
→ provider payment lifecycle identity

Stripe idempotency
→ provider-side retry semantics

DI
→ feasible-path reasoning
→ explicit path commitment
→ post-commit path revalidation
→ autonomous authority check
→ local single-use dispatch consumption
→ execution / outcome separation
→ evidence freshness
→ auditable next-state claim
```

These are complementary layers rather than competing mechanisms.

## Failure examples DI can expose

```text
1. Agent creates a new PaymentIntent because a response timed out.
   → blocked path / operation identity drift

2. DRP chose idempotent replay, but TIP invents another path.
   → path substitution failure

3. Original idempotency assumptions are no longer known, but execution continues.
   → revalidation failure

4. Two workers consume the same recovery decision with different local tokens.
   → single-use authority failure

5. API call was dispatched, but no authoritative payment state was observed.
   → execution ≠ outcome

6. Old payment evidence is reused after state generation changed.
   → freshness failure
```

## Why this case matters

A mature payment API already provides important safety primitives. The interesting DI question is not whether to recreate those primitives.

It is:

```text
Can an autonomous system prove that it selected,
revalidated, authorized, dispatched, observed,
and reviewed the correct operation as one coherent chain?
```

That is the layer DI is trying to make inspectable.

## Next validation step

A stronger external test would capture a real Stripe test-mode or sandbox trace and translate only observable facts into the DI end-to-end fixture shape.

Until such evidence is collected, this document remains a reference mapping rather than a claim of live Stripe conformance.
