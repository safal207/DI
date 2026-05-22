# Limitation Model

DI requires limitations to be explicit.

A limitation is any known condition that prevents, weakens, blocks, or constrains an action.

## Limitation Categories

| Category | Example |
|---|---|
| Missing context | Required user intent is unclear |
| Missing permission | No approval to access or share data |
| Tool limitation | Required tool is unavailable |
| Knowledge limitation | The system lacks reliable information |
| Safety limitation | Action may cause harm |
| Compliance limitation | Action may violate policy or law |
| Reversibility limitation | Action cannot be undone |
| Human boundary | User has not consented or is under pressure |

## Severity Levels

```text
informational
constraining
blocking
unknown
```

## Minimal Limitation Record

```json
{
  "limitation_id": "lim-001",
  "type": "missing_permission",
  "description": "No confirmed permission to share customer data externally.",
  "severity": "blocking",
  "required_resolution": "Obtain explicit human approval."
}
```

## Principle

> Unknown limitations must be represented as unknown, not ignored.
