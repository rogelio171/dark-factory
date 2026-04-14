---
name: df-ship
description: Creates the GitHub pull request, posts the implementation summary and evidence back to Jira through Atlassian MCP, updates final documentation, and closes the story workflow. Use when review and evidence are complete and the story is ready to ship.
---

# DF Ship

## Goal

Turn finished work into a traceable PR and a complete Jira record.

## Workflow

1. Read `spec.md`, `state.md`, review notes, and evidence outputs.
2. Create or update the PR with `gh`.
3. Summarize:
   - what changed
   - how it was tested
   - which evidence files prove each acceptance criterion
4. Post the summary back to Jira with Atlassian MCP.
5. Update any affected project documentation after the implementation is finalized.
6. Transition the Jira story to the done state when appropriate.

## Rules

- Do not create a PR without a clear test plan.
- Do not close the Jira story without evidence and a summary.
- If the PR still needs approval, leave the story in the shipping phase and note what is pending.
- Keep the PR and Jira summaries aligned with the actual diff.

## Handoff

When PR, Jira, and docs are fully updated, mark the story `complete`.
