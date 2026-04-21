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

## Handoff

When all slices are green and acceptance criteria are covered, advance `state.md` to `status: reviewing` and invoke `df-review`.

## Files

- For detailed TDD guidance, see [REFERENCE.md](REFERENCE.md).
