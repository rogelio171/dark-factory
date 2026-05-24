---
name: df-project-profile
description: Detects repository modules, manifests, validation commands, and safe working roots for Dark Factory target projects. Use when `wiki/project-profile.md` is missing or stale, before Jira story intake, or when a repository may contain multiple modules.
---

# DF Project Profile

## Goal

Create or refresh `wiki/project-profile.md` so every later phase knows the intended repo root, module boundaries, and validation scope.

## Inputs

- The target repository source tree.
- Existing `wiki/` pages when present.
- Package and workspace manifests in the repository.

## Preconditions

- The agent is operating inside the target repository root.
- `wiki/` exists, or `df-wiki-init` is running and will create it first.

## Workflow

1. Confirm the agent is at the target repository root with `git rev-parse --show-toplevel`.
2. Run `df detect-tooling --json --no-write` to get the deterministic module and command inventory.
3. For a single-module repo, run `df detect-tooling` to write `wiki/project-profile.md`.
4. For a monorepo, ask the user which module(s) Dark Factory should target by default, then run `df detect-tooling --module <module-path>`.
5. Review the generated `wiki/project-profile.md` for scope accuracy; edit only decisions that require human context.
6. Append `wiki/log.md` with the profile date and notable scope decisions.


## Observability

- Read `run_id` from `state.md`. If missing, run `df observability run start <TICKET-ID> --write-state`.
- Open a phase session: `df observability session start --run-id "$RUN_ID" --skill df-project-profile --role coordinator`.
- Record every user message, assistant response, and tool/MCP call via `df observability message record` or `df observability batch`.
- Record external snapshots after Jira, GitHub, or CI interactions relevant to this phase.
- Close the session with `df observability session end --session-id "$DF_SESSION_ID"` before handoff.
- Full contract: `df-observability`.

## Outputs

- `wiki/project-profile.md` with module boundaries and validation commands.
- Updated `wiki/log.md` entry describing the profile refresh.

## Rules

- Do not assume root-level commands apply to nested modules.
- Do not choose a default module in a monorepo without user confirmation.
- Prefer existing project scripts over inferred generic commands.
- If multiple modules share generated files or common packages, record that relationship explicitly.
- Keep `wiki/project-profile.md` concise; use bullets and tables when useful.

## Handoff

Return to the orchestrator. The next phase is normally `df-story-intake` for a fresh story, or the active story's current status.

## Output Template

```markdown
# Project Profile

## Repository

- Repo root: `<absolute-path>`
- Default working root: `<absolute-or-relative-path>`
- Layout: `single-module | multi-module | polyglot`
- Profile updated: `<YYYY-MM-DDTHH:MM:SSZ>`

## Modules

| Module | Tooling | Command root | Validation commands |
| --- | --- | --- | --- |
| `packages/app` | Node/package.json | `packages/app` | `npm test`, `npm run lint` |

## Default Story Scope

- Target modules: `packages/app`
- Do not touch: `packages/admin`
- Scope notes:

## Preflight Defaults

- Lint:
- Typecheck:
- Test:
- Build:
```
