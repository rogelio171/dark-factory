# Dark Factory Reference

## State Model

Each story lives under `docs/specs/<ticket-slug>/` and should contain:

- `spec.md`: durable PRD and execution checklist.
- `state.md`: current workflow phase and resume metadata.
- `evidence/`: screenshots and related proof.
- `reviews/`: review notes and follow-up findings.

Suggested state frontmatter:

```yaml
---
ticket: OFRS2-12345
title: add-dark-mode-toggle
branch: OFRS2-12345-add-dark-mode-toggle
status: intake
phase_detail: ""
started: 2026-04-13
last_updated: 2026-04-13T14:30:00Z
---
```

## Phase Order

1. `intake`
2. `clarifying`
3. `specifying`
4. `implementing`
5. `reviewing`
6. `evidencing`
7. `shipping`
8. `complete`

## Dispatch Rules

- If no `wiki/` exists, run `df-wiki-init` before story work.
- If no `state.md` exists for the ticket, run `df-story-intake`.
- If `status: clarifying`, run `df-clarify`.
- If `status: specifying`, run `df-spec`.
- If `status: implementing`, run `df-implement`.
- If `status: reviewing`, run `df-review`.
- If `status: evidencing`, run `df-evidence`.
- If `status: shipping`, run `df-ship`.

## Resume Rules

- Trust `state.md` as the source of truth.
- Read the latest `spec.md`, review notes, and evidence log before continuing.
- If the repository state conflicts with `state.md`, stop and reconcile before proceeding.

## External Dependencies

- Atlassian Rovo MCP for Jira access.
- Playwright MCP for browser validation and screenshots.
- `gh` for pull request creation.

If any required tool is unavailable, stop and ask the user to fix the environment instead of improvising a different workflow.
