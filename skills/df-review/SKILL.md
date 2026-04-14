---
name: df-review
description: Runs a subagent-based code review loop against the current story spec, fixing blocking findings until the implementation is clean enough to move to evidence collection. Use when implementation is complete enough for review or the user wants a spec-aware review pass.
---

# DF Review

## Goal

Find and fix issues before evidence collection and PR creation.

## Workflow

1. Read `spec.md`, `state.md`, and the current diff.
2. Launch a review subagent with the spec and acceptance criteria.
3. Categorize findings:
   - critical: must fix now
   - suggestion: should improve if low risk
   - optional: nice to have
4. Fix the critical findings.
5. Re-run tests and checks.
6. Launch a fresh review subagent.
7. Repeat until no critical findings remain.

## Rules

- Review against the spec, not just code style.
- Save findings under `docs/specs/<ticket>/reviews/`.
- Do not ignore failing tests while closing review issues.
- If a requested fix would expand scope, stop and ask the user.

## Handoff

When the review loop is clean, move to `df-evidence`.
