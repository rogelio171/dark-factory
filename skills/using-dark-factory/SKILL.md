---
name: using-dark-factory
description: Explains how to activate Dark Factory safely for Jira-to-PR delivery workflows. Use when a user asks how to use Dark Factory, install the skill pack, start a ticket workflow, or decide whether Dark Factory should handle a task.
---

# Using Dark Factory

## Goal

Help the agent decide whether Dark Factory is the right workflow and start it safely when it is.

## Inputs

- The user's request.
- The current repository path.
- Any visible Jira ticket ID or active Dark Factory story state.

## Preconditions

- Use this guidance only for Dark Factory workflow questions or Jira-to-PR delivery work.

## Workflow

1. Decide whether the request is a Dark Factory workflow.
2. If yes, confirm the agent is in the intended target repository.
3. Run `df doctor --runtime generic` when the CLI is installed; otherwise install the skill pack first.
4. Invoke `dark-factory`.
5. Let the orchestrator check `wiki/`, `wiki/project-profile.md`, and `docs/specs/*/state.md`.
6. If the repo has multiple modules, do not proceed until `df-project-profile` records the target module scope.

## Outputs

- A safe handoff to `dark-factory`, or a concise explanation that the request does not need Dark Factory.

## Rules

Use Dark Factory for traceable delivery work that starts from a Jira story and should end with a PR, evidence, and a Jira update.

Good triggers:

- "Use Dark Factory for OFRS2-12345"
- "Start this Jira ticket"
- "Resume the current Dark Factory story"
- "Run the full ticket-to-done workflow"

Do not auto-run Dark Factory for every coding task. If the user asks for a small edit, ordinary agent workflow is usually better.

## Handoff

When Dark Factory applies, invoke `dark-factory`. Otherwise continue with the ordinary task-specific workflow.

## Expectations

Dark Factory creates durable files in the target repository:

- `wiki/`
- `docs/specs/<ticket-slug>/state.md`
- `docs/specs/<ticket-slug>/spec.md`
- `docs/specs/<ticket-slug>/plan.md`
- `docs/specs/<ticket-slug>/reviews/`
- `docs/specs/<ticket-slug>/evidence/`
- `docs/specs/<ticket-slug>/preflight.json`

Shipping requires review, evidence, and preflight unless the user explicitly accepts a warning state.
