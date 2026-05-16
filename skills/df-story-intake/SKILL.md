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
3. Run `df detect-tooling --json --no-write` if module scope is not already clear from `wiki/project-profile.md`.
4. If the repo is multi-module and the ticket does not identify the target module, ask the user before continuing.
5. Run `df story init <TICKET-ID> --title "<ticket title>" --module <module-path>` to create the branch, story directory, `state.md`, `reviews/`, and evidence folders.
6. Preserve the raw ticket text and acceptance criteria for `df-spec`; do not summarize away important wording.

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
