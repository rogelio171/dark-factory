---
name: df-story-intake
description: Retrieves a Jira story through the Atlassian Rovo MCP server, extracts acceptance criteria, creates the working branch, and initializes the durable story state files. Use when starting work on a Jira ticket, creating a branch from a ticket, or preparing `docs/specs/` for a story.
---

# DF Story Intake

## Goal

Turn a Jira ticket into a local work item with a branch and durable state.

## Inputs

- The Jira ticket ID (provided by the user).
- Atlassian Rovo MCP for the ticket fetch.
- The current default branch of the repository.
- `wiki/project-profile.md` for default module scope.

## Preconditions

- Atlassian Rovo MCP is configured.
- The repository is clean (or any pending changes belong to a different story that has its own state).

## Workflow

1. Retrieve the ticket from Atlassian Rovo MCP.
2. Extract title, description, acceptance criteria, labels, and linked context.
3. Read `wiki/project-profile.md` and identify the likely target module scope.
4. Create the branch as `<TICKET-ID>-<kebab-case-title>` from the default branch.
5. Create `docs/specs/<ticket-slug>/`.
6. Initialize:
   - `state.md` from `df-spec/templates/state-template.md` with the ticket fields filled.
   - empty `reviews/`
   - empty `evidence/` with subdirectories `ui/`, `api/`, `cli/`, `unit/`, `migration/`.
7. Record `status: intake`, the branch name, the `started` date, target modules, and validation commands in `state.md`.

## Outputs

- A new branch `<TICKET-ID>-<kebab-case-title>`.
- `docs/specs/<ticket-slug>/state.md` populated from the template.
- Empty `reviews/` and `evidence/` directory structure.

## Rules

- If Atlassian MCP is not configured, stop and ask the user to configure it.
- Use the Jira title as the branch title unless the user asks for a different short title.
- Preserve the original acceptance criteria wording for the spec workflow.
- Do not guess target modules in a multi-module repo; ask the user or run `df-project-profile`.
- Do not start coding from this skill.

## Handoff

After intake, the next phase should normally be:

- `df-workspace` to record or create the safe workspace.
