# Capability Boundaries

A capability boundary defines what a system can do, cannot do, or can only do under specific conditions.

## Capability Is Not Permission

A system may be capable of performing an action while still being forbidden, unsafe, inappropriate, or under-specified.

Example:

```text
The system can send an email.
But it may not have permission to send confidential data.
```

## Boundary Types

- technical boundary,
- permission boundary,
- context boundary,
- safety boundary,
- ethical boundary,
- operational boundary,
- legal/compliance boundary,
- human approval boundary.

## Boundary States

```text
allowed
allowed_with_constraints
blocked
unknown
requires_human_review
```

## Principle

> A system should not treat technical capability as sufficient reason to act.

## Minimal Boundary Record

```json
{
  "boundary_id": "cap-boundary-001",
  "type": "permission_boundary",
  "description": "The system can generate a response but cannot send it externally without approval.",
  "state": "requires_human_review"
}
```
