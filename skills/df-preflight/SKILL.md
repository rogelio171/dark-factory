---
name: df-preflight
description: Mirrors CI locally before opening the PR by running lint, typecheck, test, build, secret scan, dependency audit, and commit-message lint, and writing a structured `preflight.json` for `df-ship` to consume. Use when implementation, review, and evidence are complete and the story is about to be shipped.
---

# DF Preflight

## Goal

Catch every failure that CI would catch, before the PR exists, and write a machine-readable result for `df-ship`.

## Inputs

- `docs/specs/<ticket>/spec.md`
- `docs/specs/<ticket>/state.md` (must have `status: evidencing` or later)
- The current branch's commit range vs. the merge base

## Preconditions

- Implementation is complete and committed.
- `df-evidence` has finished and recorded evidence files.
- The local working tree is clean (no uncommitted changes that would not ship).

## Workflow

1. Detect the project's tooling by reading manifests:
   - JS/TS: `package.json` scripts (`lint`, `typecheck`, `test`, `build`) and the package manager from `pnpm-lock.yaml`, `yarn.lock`, `package-lock.json`, or fallback npm install.
   - Python: `pyproject.toml`, `tox.ini`, `Makefile` targets.
   - Go: `go vet`, `go test ./...`, `go build ./...`.
   - Rust: `cargo fmt --check`, `cargo clippy`, `cargo test`, `cargo build`.
   - Fallback: `Makefile` targets named `lint`, `test`, `build`.
2. Run the detected commands in this order, recording exit code, duration, and the last 50 lines of output for each:
   - lint
   - typecheck
   - test
   - build
3. Run security scans when available:
   - `gitleaks detect --source . --no-git -v` if `gitleaks` is on `PATH`.
   - Dependency audit: `npm audit --omit=dev --json`, `pnpm audit --prod --json`, `pip-audit --format json`, `cargo audit --json`, `bundle audit check --update`. Run only when the corresponding manifest exists.
4. Lint the branch's commit range with conventional-commits rules:
   - Compute base with `git merge-base HEAD origin/<default-branch>`.
   - For each commit in the range, validate `type(scope?): subject` (allowed types: `feat fix docs style refactor perf test build ci chore revert`).
5. Write `docs/specs/<ticket>/preflight.json` (see REFERENCE.md for the schema).
6. Update `state.md`:
   - On all green: `status: preflight` -> ready to call `df-ship`, `phase_detail: "preflight green"`.
   - On any failure: keep `status: preflight`, set `phase_detail: "preflight failed: <stage>"`, list the failures under "Blockers".

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

## Handoff

- Green: invoke `df-ship`.
- Failure: stop and surface the failed stages so the user can route the fix back to `df-implement` or `df-review`.

## Files

- For the `preflight.json` schema and command catalog, see [REFERENCE.md](REFERENCE.md).
