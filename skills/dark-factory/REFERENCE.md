# Dark Factory Reference

## State Model

Each story lives under `docs/specs/<ticket-slug>/` and should contain:

- `spec.md`: durable PRD and execution checklist.
- `state.md`: current workflow phase and resume metadata (uses the schema below).
- `preflight.json`: machine-readable result of the local CI mirror (written by `df-preflight`).
- `evidence/{ui,api,cli,unit,migration}/`: per-kind evidence files plus an `INDEX.md` map.
- `reviews/`: review notes per pass.

Required `state.md` frontmatter (template at `df-spec/templates/state-template.md`):

```yaml
---
ticket: OFRS2-12345
title: add-dark-mode-toggle
branch: OFRS2-12345-add-dark-mode-toggle
status: intake
phase_detail: ""
risk: low
auto_merge_eligible: false
started: 2026-04-13
last_updated: 2026-04-13T14:30:00Z
spec_path: docs/specs/OFRS2-12345-add-dark-mode-toggle/spec.md
review_path: docs/specs/OFRS2-12345-add-dark-mode-toggle/reviews
evidence_path: docs/specs/OFRS2-12345-add-dark-mode-toggle/evidence
preflight_path: docs/specs/OFRS2-12345-add-dark-mode-toggle/preflight.json
pr_url: ""
pr_number: ""
merge_sha: ""
---
```

## Phase Order

1. `intake`
2. `clarifying`
3. `specifying`
4. `implementing`
5. `reviewing`
6. `evidencing`
7. `preflight`
8. `shipping`
9. `merging`
10. `complete`

`blocked` is a non-linear status set by any phase that hits an unrecoverable problem (security comment, scope expansion, closed PR, non-converging auto-fix loop). `df-resume` reads it and routes back to the right place.

## Dispatch Rules

| `status` | Skill |
| --- | --- |
| `intake` | `df-clarify` (or `df-spec` directly if the ticket is clear) |
| `clarifying` | `df-clarify` |
| `specifying` | `df-spec` |
| `implementing` | `df-implement` |
| `reviewing` | `df-review` |
| `evidencing` | `df-evidence` |
| `preflight` | `df-preflight` (then `df-ship` when green) |
| `shipping` | `df-ship` |
| `merging` | `df-merge` |
| `blocked` | stop; print the blocker and ask the user |
| `complete` | stop; print the merge SHA |

Bootstrap rules (orthogonal to `status`):

- If `wiki/` is missing, run `df-wiki-init` first.
- If `.github/workflows/pr-checks.yml` is missing, suggest `df-github-init` (do not auto-run).

## Risk Gating

`df-spec` writes `risk` and `auto_merge_eligible` into `state.md`. Downstream behavior:

| `risk` | Auto-merge | Required reviewers beyond Copilot |
| --- | --- | --- |
| `low` | Armed by `df-ship` when `auto_merge_eligible: true` | none |
| `medium` | Not armed; requires explicit user confirmation | CODEOWNERS owners on touched paths |
| `high` | Never armed; human approval required pre-`df-ship` | CODEOWNERS owners + named reviewers from `state.md` |

## Resume Rules

- Trust `state.md` as the source of truth.
- Read the latest `spec.md`, review notes, evidence index, and `preflight.json` before continuing.
- If `pr_url` is set, fetch live PR status via `gh pr view` and reconcile.
- If `state.md` says `merging` but `gh pr view` reports `MERGED`, run `df-wiki-update` and advance to `complete` instead of re-running `df-merge`.
- If the repository state conflicts with `state.md`, stop and reconcile before proceeding.

## External Dependencies

- Atlassian Rovo MCP for Jira access (`df-story-intake`, `df-ship`, `df-merge`).
- Playwright MCP for the `ui` evidence kind (`df-evidence`).
- `gh` for pull-request and check operations (`df-ship`, `df-merge`, `df-github-init`, `df-resume`).
- Repo admin token for `df-github-init` branch protection.

If any required tool is unavailable, stop and ask the user to fix the environment instead of improvising a different workflow.
