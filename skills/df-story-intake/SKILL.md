---
name: df-story-intake
description: Retrieves a Jira story through the Atlassian Rovo MCP Server, extracts acceptance criteria, creates the working branch, and initializes story state files. Use when starting work on a Jira ticket, creating a branch from a ticket, or preparing `docs/specs/` for a story.
---

# DF Story Intake

## Goal

Turn a Jira ticket into a local work item with a branch and durable state.

## Workflow

1. Retrieve the ticket from Atlassian Rovo MCP.
2. Extract the title, description, acceptance criteria, labels, and linked context.
3. Create the branch as `<TICKET-ID>-<kebab-case-title>`.
4. Create `docs/specs/<ticket-slug>/`.
5. Initialize:
   - `state.md`
   - empty `reviews/`
   - empty `evidence/`
6. Record `status: intake` and the branch name in `state.md`.

## Rules

- If Atlassian MCP is not configured, stop and ask the user to configure it.
- Use the Jira title as the branch title unless the user asks for a different short title.
- Preserve the original acceptance criteria wording in the spec workflow.
- Do not start coding from this skill.

## Output

After intake, the next phase should normally be:

- `df-clarify` if the requirements are vague
- `df-spec` if the ticket is already clear
