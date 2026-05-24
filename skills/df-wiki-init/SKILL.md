---
name: df-wiki-init
description: Creates or refreshes the Dark Factory project wiki for new or existing codebases using Karpathy-style persistent wiki patterns. Use when a project has no wiki, needs initial repo analysis, or the user asks to bootstrap documentation from the codebase.
---

# DF Wiki Init

## Goal

Create `wiki/` as the durable project knowledge layer, or refresh it after meaningful drift.

## Inputs

- The target repository's source tree.
- The templates under `templates/` in this skill (`schema.md`, `index.md`, `log.md`).

## Preconditions

- The agent is operating inside the target repository's root.
- Either `wiki/` does not exist (new bootstrap) or the user explicitly asked for a refresh.

## Workflow

### New project mode

1. Create `wiki/`, `wiki/architecture/`, `wiki/patterns/`, `wiki/stack/`, and `wiki/entities/`.
2. Copy the template files from `templates/schema.md`, `templates/index.md`, and `templates/log.md`.
3. Add an initial `wiki/log.md` entry describing the bootstrap.

### Existing project mode

1. Read the codebase in broad strokes, using subagents or agent teams by default for non-trivial repositories.
2. Run `df detect-tooling --json --no-write` to get deterministic stack, module, and validation-command candidates.
3. Identify:
   - stack and tooling
   - architecture boundaries
   - testing approach
   - naming and file conventions
   - domain entities and workflows
4. Create or update wiki pages in the correct directories.
5. Invoke `df-project-profile` if `wiki/project-profile.md` is missing or the repo layout changed.
6. Update `wiki/index.md` and append `wiki/log.md`.

## Delegation Model

The main agent coordinates wiki creation and keeps the final wiki concise. For existing codebases, delegate exploration to subagents or agent teams instead of loading the whole repository into the main context.

- Use parallel exploration subagents for stack/tooling, architecture boundaries, testing patterns, and domain entities.
- Ask each subagent to return durable wiki-ready findings with file paths and confidence notes.
- The coordinator synthesizes overlapping findings, writes the wiki pages, and records the bootstrap or refresh in `wiki/log.md`.
- If the repository is small enough for one pass, the coordinator may do the work directly but should still keep findings concise and durable.


## Observability

- Read `run_id` from `state.md`. If missing, run `df observability run start <TICKET-ID> --write-state`.
- Open a phase session: `df observability session start --run-id "$RUN_ID" --skill df-wiki-init --role coordinator`.
- Record every user message, assistant response, and tool/MCP call via `df observability message record` or `df observability batch`.
- Record external snapshots after Jira, GitHub, or CI interactions relevant to this phase.
- Close the session with `df observability session end --session-id "$DF_SESSION_ID"` before handoff.
- Full contract: `df-observability`.

## Outputs

- A populated `wiki/` tree following `wiki/schema.md`.
- A dated entry in `wiki/log.md` describing the bootstrap or refresh.

## Rules

- Read `wiki/schema.md` after creating it and follow it for all future wiki maintenance.
- Prefer durable pages like `api-boundaries.md` over ticket-shaped pages.
- Keep the wiki concise enough to scan, but complete enough for another agent to continue work.
- If the repo is very large, summarize by subsystem instead of trying to mirror every file.
- Prefer subagents or agent teams for repository exploration; the main agent should coordinate and synthesize.
- For multi-module repositories, treat module boundaries and validation commands as first-class wiki knowledge.

## Handoff

When the wiki is in place, return to the orchestrator. The next phase is normally `df-story-intake` for a fresh story, or whatever phase the active story already occupies.

## Files

- Templates live in `templates/`.
- Module scope is recorded in `wiki/project-profile.md` by `df-project-profile`.
