# Example: Personal Productivity Assistant

## Request

> Help me organize my weekly study schedule and improve productivity.

## DIF Analysis (Inferred Intent)

The user appears to want structured study planning, prioritization support, and productivity guidance without silently authorizing the system to operate external accounts or complete work on the user's behalf.

This remains an inferred intent until the user confirms it.

## DI Feasibility Assessment

The request is feasible for planning, prioritization, reminder structuring, conflict detection, and schedule recommendations.

The request is not sufficient authority for autonomous calendar changes, assignment submission, account access, or outbound communication.

## Capabilities

- Create a proposed weekly study schedule.
- Suggest productivity and prioritization techniques.
- Identify conflicts in user-provided availability.
- Break large study goals into reviewable tasks.
- Recommend reminder structures for later user approval.

## Boundary Assessment

The assistant may prepare and revise a plan. It may interact with external systems only when the relevant integration exists and the user has explicitly authorized the exact action.

Technical capability is not automatic permission.

## Limitations

- Cannot guarantee productivity or academic outcomes.
- Cannot force the user to follow the plan.
- Cannot infer missing deadlines or workload as facts.
- Cannot access private academic or calendar systems without an authorized integration.
- Cannot submit assignments or communicate as the user without explicit permission.

## Feasible Paths

- Ask for study goals, deadlines, available hours, and fixed commitments.
- Produce a draft weekly plan for review.
- Offer alternative plans for high-energy and low-energy days.
- Add a review point after several days and revise from observed results.
- Prepare calendar entries or reminders for separate confirmation.

## Blocked Actions

- Automatically submitting assignments.
- Accessing private accounts without authorization.
- Sending messages as the user without confirmation.
- Modifying an external calendar when no authorized integration is available.
- Claiming that the plan will guarantee a result.

## Critical Unknowns

- Current workload and subject priorities.
- Exam and assignment dates.
- Preferred study hours and rest needs.
- Existing schedule conflicts.
- Whether any external calendar action is actually requested and authorized.

## Recommendation

Begin with a lightweight draft schedule based only on confirmed constraints. Let the user approve or correct it before creating any committed plan or external action.

## DRP Readiness

A decision is ready for DRP only after the user confirms the intended plan, its time boundaries, and any authorized external actions.

Until then, DI should classify the schedule as a proposal rather than a commitment.

## Summary

DI can help prepare a useful study plan while preserving a simple boundary:

```text
planning support
!=
authority to act in the user's external systems
```

This example is adapted from the first-time contribution in [PR #9](https://github.com/safal207/DI/pull/9).
