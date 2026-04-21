---
name: df-review
description: Runs a subagent-based code review loop against the current story spec, fixing blocking findings until the implementation is clean enough to move to evidence collection. Use when implementation is complete enough for review or the user wants a spec-aware review pass.
---

# DF Review

## Goal

Find and fix issues before evidence collection and PR creation.

## Inputs

- `docs/specs/<ticket>/spec.md` (acceptance criteria, vertical slices, testing strategy).
- `docs/specs/<ticket>/state.md`.
- The current branch diff vs. the merge base.

## Preconditions

- `state.md` is `status: reviewing`.
- All slices in `spec.md` are checked off and tests are green.

## Workflow

1. Read `spec.md`, `state.md`, and the current diff.
2. Launch a review subagent with the spec, the diff, and the acceptance criteria.
3. Categorize findings:
   - critical: must fix now
   - suggestion: should improve if low risk
   - optional: nice to have
4. Save the categorized findings under `docs/specs/<ticket>/reviews/<n>.md`.
5. Fix the critical findings.
6. Re-run tests and relevant checks.
7. Launch a fresh review subagent.
8. Repeat until no critical findings remain.

## Outputs

- One review note per pass under `docs/specs/<ticket>/reviews/`.
- Code fixes for every critical finding.
- Updated `state.md` with the pass count and outstanding suggestions.

## Rules

- Review against the spec, not just code style.
- Save findings under `docs/specs/<ticket>/reviews/`.
- Do not ignore failing tests while closing review issues.
- If a requested fix would expand scope, stop and ask the user.
- Do not collapse multiple critical findings into one fix commit; keep changes scoped.

## Handoff

When the review loop is clean (no critical findings, optional findings noted), advance `state.md` to `status: evidencing` and invoke `df-evidence`.
