---
name: df-preflight
description: Mirrors CI locally before opening the PR by running module-scoped lint, typecheck, test, build, secret scan, dependency audit, and commit-message lint, and writing a structured `preflight.json` for `df-ship` to consume. Use when implementation, review, and evidence are complete and the story is about to be shipped.
---

# DF Preflight

## Goal

Catch every failure that CI would catch, before the PR exists, and write a machine-readable result for `df-ship`.

## Inputs

- `docs/specs/<ticket>/spec.md`
- `docs/specs/<ticket>/plan.md`
- `docs/specs/<ticket>/state.md` (must have `status: evidencing` or later)
- `wiki/project-profile.md`
- The current branch's commit range vs. the merge base

## Preconditions

- Implementation is complete and committed.
- `df-evidence` has finished and recorded evidence files.
- The local working tree is clean (no uncommitted changes that would not ship).

## Workflow

1. Read `state.md`, `plan.md`, and `wiki/project-profile.md` to confirm the intended scope.
2. Run `df preflight <TICKET-ID>`.
3. Read `docs/specs/<ticket>/preflight.json`; the CLI records cwd, exit code, duration, output tail, skipped stages, security scans, dependency audits, and `df commit-lint` results.
4. If the command exits non-zero, delegate failure diagnosis and route the fix back to `df-implement` or `df-review`.
5. If the command exits zero, hand off to `df-ship`.

## Delegation Model

The main agent coordinates preflight and writes the final `preflight.json`. Prefer subagents or agent teams for independent command execution and failure diagnosis.

- Delegate broad tooling detection to a subagent when the repository is polyglot or unfamiliar.
- Run independent checks through specialist workers when the runtime supports it, but record results in one coordinator-owned `preflight.json`.
- On failure, use a focused diagnostic subagent to summarize the failing stage, likely cause, and safest next phase.
- The coordinator decides whether failures block shipping and routes fixes back to `df-implement` or `df-review`.

## Outputs

- `docs/specs/<ticket>/preflight.json` with per-stage results.
- Updated `state.md` with the preflight outcome.

## Rules

- Never silently skip a stage that is configured. If a stage is not applicable, record it with `status: "skipped"` and a reason.
- Any `failed` stage blocks `df-ship`; `warning` stages are recorded but do not block.
- Do not modify production code from this skill. If a fix is needed, drop back to `df-implement`.
- Do not fetch from the network beyond what the dependency audit naturally requires.
- Stop and ask the user if `gh auth status` reports the CLI is unauthenticated, since `df-ship` will need it next.
- Prefer subagents or agent teams for tooling detection and diagnostics; the coordinator owns the final preflight decision.
- Avoid whole-repo fallback commands unless `target_modules` says the whole repo is in scope.
- Secret scans may run at repo root, but note that they are intentionally repo-wide in `preflight.json`.

## Handoff

- Green: invoke `df-ship`.
- Failure: stop and surface the failed stages so the user can route the fix back to `df-implement` or `df-review`.

## Files

- For the `preflight.json` schema and command catalog, see [REFERENCE.md](REFERENCE.md).
