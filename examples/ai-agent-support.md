# Example: AI Agent Support

## Request

> "Help the user resolve an account issue and send the result to the support system."

---

## DIF Analysis (Inferred Intent)

**What the user is actually trying to solve**:

- The user needs support assistance, not unrestricted autonomous action.
- The user likely expects the agent to understand the issue, structure it, and move it toward resolution.
- The user may not understand which account actions require verification, permission, or human support authority.
- The user wants speed, but the workflow may involve privacy, identity, billing, or security constraints.

**Refined intent**: *"Prepare a safe, structured support resolution path without taking unauthorized account actions or exposing private data."*

---

## DI Feasibility Assessment

### Capabilities Assessment

- ✅ Can summarize user-provided issue details.
- ✅ Can identify likely support categories.
- ✅ Can draft a support note or response.
- ✅ Can list missing information required for escalation.
- ⚠ May not have verified account-system access.
- ⚠ May not know whether the user owns the account.
- ⚠ May not be authorized to submit or modify support records.
- ⚠ May not have current internal support policy details.

### Boundary Assessment

#### Technical Boundary: ⚠ Allowed with Constraints

The agent can transform the user's description into a structured support note, but it may not be connected to the real support system or have write permissions.

**Constraint**: Do not claim the issue was submitted or resolved unless the support system confirms it.

#### Permission Boundary: ⚠ Requires Human Review

Account-related issues often require identity verification and explicit permission.

**Constraint**: Do not change account state, reset credentials, update billing, or access private account data without verified authorization.

#### Context Boundary: ⚠ Allowed with Missing Information

The agent may need additional details such as account identifier, issue category, error message, timestamp, device/browser, or recent actions.

**Constraint**: Ask only for account-safe information. Avoid requesting unnecessary secrets or sensitive data.

#### Safety Boundary: ⚠ Allowed with Constraints

Support workflows may involve security-sensitive actions.

**Constraint**: Escalate identity, billing, access, fraud, or security issues to a human support operator.

#### Operational Boundary: ⚠ Requires System Confirmation

The agent may draft a support note, but final submission depends on the actual support system and role permissions.

**Constraint**: Treat submission as a separate action requiring confirmation.

---

## Limitations

| Limitation | Category | Status | Impact | Mitigation |
|---|---|---|---|---|
| User identity not verified | Missing permission | Blocking for account changes | Cannot safely modify account state | Require human verification or secure support flow |
| Support policy unknown | Knowledge limitation | Constraining | Draft may omit required fields | Mark policy assumptions and request review |
| Support-system write access unknown | Tool limitation | Unknown | Cannot guarantee ticket creation | Prepare note; submit only if tool confirms success |
| Possible sensitive data | Safety limitation | Constraining | Risk of exposing private data | Minimize data, redact secrets, use approved channels |
| Issue category unclear | Missing context | Constraining | Wrong routing or escalation | Ask for safe clarifying details |

---

## Feasible Paths

### Path A: Prepare Support Note for Human Review (Recommended)

**Approach**:

- Summarize the issue.
- Identify missing safe fields.
- Draft a structured support note.
- Mark risk category and escalation need.
- Ask a human operator to approve or submit.

**Trade-offs**:

- ✅ Safe by default.
- ✅ Preserves human authority.
- ✅ Avoids unauthorized account changes.
- ✅ Produces useful support artifact.
- ❌ Slower than full automation.
- ❌ Requires human follow-through.

**Recommended when**:

- account ownership is not verified,
- billing/security/access is involved,
- support permissions are unclear,
- support-system write access is unavailable.

---

### Path B: Submit to Support System with Confirmation

**Approach**:

- Prepare the support note.
- Use an approved support-system tool.
- Submit only non-sensitive required fields.
- Record confirmation ID if the system returns one.

**Trade-offs**:

- ✅ Faster workflow.
- ✅ Produces trackable support artifact.
- ⚠ Requires verified tool access.
- ⚠ Requires permission to submit.
- ❌ Unsafe if identity or approval is missing.

**Recommended when**:

- the tool is approved,
- user identity and permission are verified,
- no prohibited sensitive data is transmitted,
- support submission is logged.

---

### Path C: Direct Account Action

**Approach**:

- Modify account state directly, such as reset, update, unlock, refund, or close.

**Status**: Blocked by default.

**Why blocked**:

- account authority is not verified,
- action may be irreversible or security-sensitive,
- system may lack permission,
- support policies may require human review.

---

## Blocked Actions

- changing account settings without authorization,
- sending private user data to unapproved tools,
- claiming the issue is resolved without verification,
- impersonating support staff,
- bypassing identity checks,
- performing billing, access, or security actions without human approval.

---

## Critical Unknowns

| Unknown | Why It Matters | How to Resolve |
|---|---|---|
| Is the user verified? | Determines whether account-specific actions are allowed | Use approved identity verification flow |
| Is the support tool approved? | Determines whether data can be sent | Check tool allowlist or ask operator |
| What issue category is this? | Determines routing and escalation | Ask for non-sensitive issue details |
| Does the action affect billing/security/access? | Determines risk level | Classify issue before action |

---

## Recommendation

**Primary path**: Path A — Prepare Support Note for Human Review.

**Rationale**:

- It preserves safety and permission boundaries.
- It still creates useful progress.
- It avoids pretending the agent has authority it may not have.
- It separates preparation from commitment.

---

## DRP Readiness

**Ready to decide?** ⚠ **Partially**

Ready to record a decision to prepare a support note.

Not ready to record a decision to submit, modify, or resolve the account issue unless identity, permission, and tool authorization are confirmed.

**Decision to Record**:

- *Prepare a structured support note for human review.*
- *Do not perform direct account actions until authorization is verified.*

---

## Summary

| Aspect | Status |
|---|---|
| Recommended approach | Prepare support note for human review |
| Direct account action | Blocked by default |
| Submission to support tool | Allowed only with verified permission and approved tool |
| Main risk | Unauthorized account action or sensitive data exposure |
| Ready for DRP | Partially |
