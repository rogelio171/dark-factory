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
2. Detect project layout:
   - root manifests: `package.json`, `pyproject.toml`, `go.mod`, `Cargo.toml`
   - workspace manifests: `pnpm-workspace.yaml`, `turbo.json`, `nx.json`, `lerna.json`
   - nested module manifests under common roots such as `apps/`, `packages/`, `services/`, and `libs/`
3. For each module, record:
   - path relative to repo root
   - language/tooling
   - likely install, lint, typecheck, test, and build commands
   - whether commands should run from repo root or module root
4. Identify the default story scope:
   - single-module repo: that module
   - monorepo: ask the user which module(s) Dark Factory should target by default
5. Write `wiki/project-profile.md`.
6. Append `wiki/log.md` with the profile date and notable scope decisions.

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
