---
name: df-implement
description: Implements a story through a strict red-green-refactor TDD loop using the existing spec, making only the minimum code changes needed and recording progress in small checkpoints. Use when a story is in the implementation phase and `spec.md` already defines the slices and acceptance criteria.
---

# DF Implement

## Goal

Complete the story with minimal, human-readable changes that satisfy the acceptance criteria.

## Loop

1. Read `spec.md`, `state.md`, and nearby tests.
2. Pick one thin vertical slice.
3. Write one failing test for one external behavior.
4. Make the minimum code change to pass it.
5. Re-run the test and relevant checks.
6. Refactor only while green.
7. Record progress and move to the next slice.

## Rules

- Never write all tests first.
- Prefer public-behavior tests over implementation-detail tests.
- Make the smallest change that passes.
- Match existing project patterns unless the spec explicitly changes them.
- Update `state.md` after each meaningful slice.

## Commits

- Commit in small, related chunks after green checkpoints.
- Use the ticket ID in the message when possible.
- Do not bundle unrelated cleanup with feature work.

## Files

- For detailed TDD guidance, see [REFERENCE.md](REFERENCE.md).
