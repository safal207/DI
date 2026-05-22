# Example: AI Agent Support

## Request

> Help the user resolve an account issue and send the result to the support system.

## Inferred Intent

The user wants the agent to assist with a support workflow and produce a useful resolution path.

## Capabilities

- summarize user-provided context,
- identify likely support categories,
- draft a response,
- prepare a structured support note.

## Limitations

- the agent may not have verified access to the account system,
- the agent may not know the user's identity or permissions,
- the agent may not be allowed to submit changes on behalf of support staff,
- the agent may lack current policy details.

## Constraints

- privacy boundary,
- permission boundary,
- support policy boundary,
- human approval boundary.

## Feasible Actions

- summarize the issue locally,
- ask for missing account-safe details,
- draft a support note for human review,
- recommend escalation if the issue affects billing, identity, or security.

## Blocked Actions

- changing account settings without authorization,
- sending private user data to unapproved tools,
- claiming the issue is resolved without verification,
- impersonating support staff.

## Recommended Next Step

Prepare a structured support note and ask a human operator to approve or complete the action.
