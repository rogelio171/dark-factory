---
name: df-implement
description: Implements a story through a strict red-green-refactor TDD loop using the existing spec, making only the minimum code changes needed and recording progress in small checkpoints. Use when a story is in the implementation phase and `spec.md` already defines the slices and acceptance criteria.
---

# DF Implement

## Goal

Complete the story with minimal, human-readable changes that satisfy the acceptance criteria.

## Inputs

- `docs/specs/<ticket>/spec.md` (slices, testing strategy, acceptance criteria).
- `docs/specs/<ticket>/state.md`.
- Nearby tests and existing project patterns (per `wiki/patterns/`).

## Preconditions

- `state.md` is `status: implementing`.
- `spec.md` exists and lists at least one vertical slice.
- The branch is checked out and clean.

## Workflow

1. Read `spec.md`, `state.md`, and nearby tests.
2. Pick one thin vertical slice from the spec.
3. Write one failing test for one external behavior (Red).
4. Make the minimum code change to pass it (Green).
5. Re-run the test and any directly relevant checks.
6. Refactor only while green.
7. Record progress in `state.md` and commit in a small, related chunk.
8. Move to the next slice.

## Delegation Model

The main agent coordinates slice selection, state updates, and final synthesis. Prefer subagents or agent teams for context-heavy implementation support.

- Delegate test discovery and nearby-pattern research before each non-trivial slice.
- Use specialist subagents to inspect failing tests, type errors, or unfamiliar modules and return focused fix recommendations.
- If the runtime supports write-capable agent teams, delegate isolated slice implementation to a worker and have the coordinator review the diff before committing.
- If only the main agent can edit, keep edits narrow and use subagents for exploration and validation so the main context stays small.

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

## Handoff

When all slices are green and acceptance criteria are covered, advance `state.md` to `status: reviewing` and invoke `df-review`.

## Files

- For detailed TDD guidance, see [REFERENCE.md](REFERENCE.md).
