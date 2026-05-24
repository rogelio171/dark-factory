---
name: df-implement
description: Implements a story through a strict red-green-refactor TDD loop using the existing spec and implementation plan, making only the minimum code changes needed and recording progress in small checkpoints. Use when a story is in the implementation phase and `spec.md` and `plan.md` already define the slices and acceptance criteria.
---

# DF Implement

## Goal

Complete the story with minimal, human-readable changes that satisfy the acceptance criteria.

## Inputs

- `docs/specs/<ticket>/spec.md` (slices, testing strategy, acceptance criteria).
- `docs/specs/<ticket>/plan.md` (exact TDD tasks, files, commands, and commit checkpoints).
- `docs/specs/<ticket>/state.md`.
- `wiki/project-profile.md` for module boundaries and validation commands.
- Nearby tests and existing project patterns (per `wiki/patterns/`).

## Preconditions

- `state.md` is `status: implementing`.
- `spec.md` exists and lists at least one vertical slice.
- `plan.md` exists and has at least one unchecked implementation task.
- The branch is checked out and clean.

## Workflow

1. Read `spec.md`, `plan.md`, `wiki/project-profile.md`, and deterministic state fields with `df state get`.
2. Pick the next unchecked task from `plan.md`.
3. Write one failing test for one external behavior (Red).
4. Verify the test fails for the expected reason.
5. Make the minimum code change to pass it (Green).
6. Re-run the test and scoped checks from `validation_commands`.
7. Refactor only while green.
8. Check off the completed plan step, record progress with `df state set <TICKET-ID> phase_detail "<checkpoint>"`, and commit in a small, related chunk.
9. Move to the next task.

## Delegation Model

The main agent coordinates slice selection, state updates, and final synthesis. Prefer subagents or agent teams for context-heavy implementation support.

- Delegate test discovery and nearby-pattern research before each non-trivial slice.
- Use specialist subagents to inspect failing tests, type errors, or unfamiliar modules and return focused fix recommendations.
- If the runtime supports write-capable agent teams, delegate isolated slice implementation to a worker and have the coordinator review the diff before committing.
- If only the main agent can edit, keep edits narrow and use subagents for exploration and validation so the main context stays small.


## Observability

- Read `run_id` from `state.md`. If missing, run `df observability run start <TICKET-ID> --write-state`.
- Open a phase session: `df observability session start --run-id "$RUN_ID" --skill df-implement --role coordinator`.
- Record every user message, assistant response, and tool/MCP call via `df observability message record` or `df observability batch`.
- Record external snapshots after Jira, GitHub, or CI interactions relevant to this phase.
- Close the session with `df observability session end --session-id "$DF_SESSION_ID"` before handoff.
- Full contract: `df-observability`.

## Outputs

- Code changes scoped to one slice per cycle.
- Updated `state.md` after each meaningful slice.
- Commits using the ticket ID in the message.

## Rules

- Never write all tests first.
- Prefer public-behavior tests over implementation-detail tests.
- Make the smallest change that passes.
- Match existing project patterns unless the spec explicitly changes them.
- Commit in small, related chunks after green checkpoints.
- Do not bundle unrelated cleanup with feature work.
- Prefer subagents or agent teams for exploration, test discovery, and validation; the coordinator owns slice boundaries and state.
- Do not run whole-repo checks in a multi-module repo unless `state.md` says the whole repo is in scope.
- If `plan.md` is missing or vague, stop and invoke `df-plan`.

## Handoff

When all slices are green and acceptance criteria are covered, advance `state.md` to `status: reviewing` and invoke `df-review`.

## Files

- For detailed TDD guidance, see [REFERENCE.md](REFERENCE.md).
- Prompt template for implementation subagents: `prompts/implementer.md`.
