---
name: dark-factory
description: Orchestrates the Dark Factory delivery workflow from wiki bootstrap through Jira completion using state files and phase-specific skills, including local CI mirror, automated PR babysitting via Copilot review, and post-merge wiki updates. Use when the user says dark factory, start a story, work on a Jira ticket, resume delivery, or wants the full ticket-to-done workflow.
---

# Dark Factory

## Goal

Pick the right phase skill for the current state and dispatch to it, so the user never has to remember which step comes next.

## Inputs

- The user's request (ticket ID, "resume", "start", or a specific phase ask).
- `wiki/` (presence and freshness).
- `docs/specs/*/state.md` for every active story.
- `.github/workflows/pr-checks.yml` (presence indicates `df-github-init` has been run).

## Preconditions

- The agent is operating inside the target repository's root.
- The skill pack is installed under `.agents/skills/`.

## Workflow

1. Identify the target ticket or active story.
2. Check whether project knowledge exists in `wiki/`.
3. Check whether GitHub automation exists in `.github/workflows/pr-checks.yml`.
4. Check for story state in `docs/specs/<ticket-slug>/state.md`.
5. Apply the dispatch rules below to pick the next skill.
6. Advance one phase at a time and keep `state.md` current.

## Dispatch Rules

In order. The first matching condition wins.

1. If `wiki/` is missing, invoke `df-wiki-init`.
2. If `.github/workflows/pr-checks.yml` is missing in the target repo, suggest `df-github-init` (do not auto-run; it requires repo admin).
3. If no `state.md` exists for the requested ticket, invoke `df-story-intake`.
4. If `state.md` is `status: intake` or the user asks to clarify, invoke `df-clarify`.
5. If `state.md` is `status: clarifying` and clarification is complete, invoke `df-spec`.
6. If `state.md` is `status: specifying` and `spec.md` is complete, invoke `df-implement`.
7. If `state.md` is `status: implementing` and slices are checked off, invoke `df-review`.
8. If `state.md` is `status: reviewing` and the review loop is clean, invoke `df-evidence`.
9. If `state.md` is `status: evidencing` and evidence is captured, invoke `df-preflight`.
10. If `state.md` is `status: preflight` and `preflight.json` is `passed` or `passed-with-warnings`:
    - If `risk: low` and `auto_merge_eligible: true`, invoke `df-ship` directly.
    - If `risk: medium` or `risk: high`, stop and ask the user to confirm before invoking `df-ship`.
11. If `state.md` is `status: shipping`, invoke `df-ship` (idempotent: it will edit the existing PR if one exists).
12. If `state.md` is `status: merging`, invoke `df-merge`.
13. If `state.md` is `status: blocked`, surface the blocker and ask the user how to proceed.
14. If `state.md` is `status: complete`, report the merge SHA and stop.
15. If a session was interrupted and the user asks to resume, invoke `df-resume`.

## Delegation Model

The main agent is the workflow coordinator, not the primary worker. Keep the main context focused on phase routing, `state.md`, risk gates, user decisions, and synthesis.

- Prefer subagents or agent teams for broad exploration, implementation research, review, evidence capture, preflight diagnosis, and merge babysitting.
- Launch parallel subagents when separate domains can be investigated independently, then synthesize their findings into the spec, state file, review notes, evidence index, or user-facing summary.
- Do not let the main agent accumulate all repository, implementation, review, and CI context unless the task is trivial or delegation is unavailable.
- Before invoking a phase skill, state whether that phase should use a subagent team and what each worker should return.

## Risk gating

- `risk: high`: never auto-arm merge. `df-ship` will skip `gh pr merge --auto`. Require explicit human approval before transitioning to `merging`.
- `risk: medium`: auto-arm merge only when the user confirms.
- `risk: low` and `auto_merge_eligible: true`: full automation through to merge.

## Outputs

- A clear next-step decision printed to the user before any phase skill runs.
- An updated `state.md` after each transition.

## Rules

- Read `docs/specs/*/state.md` before choosing a phase.
- Advance one phase at a time and keep `state.md` current.
- Stop and ask the user if a required external integration is unavailable (Atlassian Rovo MCP for `df-story-intake`, `gh` for `df-ship`/`df-merge`, Playwright MCP for `df-evidence` UI kind).
- Prefer existing wiki pages over rediscovering the same context.
- Keep implementation minimal and acceptance-criteria driven.
- Prefer subagents or agent teams for context-heavy work; the orchestrator coordinates, records, and synthesizes.
- Never skip `df-preflight`; CI cycles are expensive relative to local mirroring.
- Never skip `df-evidence`; PRs without evidence cannot be auto-merged because the PR template requires the Evidence section.

## Handoff

Hand off to the chosen phase skill. When the workflow reaches `status: complete`, report the merge SHA and the path to the updated wiki entries.

## Files

- For the full state model and phase rules, see [REFERENCE.md](REFERENCE.md).
