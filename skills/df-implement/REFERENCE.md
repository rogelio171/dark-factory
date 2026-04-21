# DF Implement Reference

## Red-Green-Refactor

### Red

- Choose one behavior from the current slice.
- Write one test that expresses that behavior.
- Confirm the test fails for the right reason.

### Green

- Change as little production code as possible.
- Prefer extending existing modules over inventing new abstractions.
- Re-run the smallest relevant test set first, then broader checks.

### Refactor

- Only refactor after the test is green.
- Remove duplication and sharpen names.
- Keep the public behavior unchanged.

## Slice Heuristics

Good slices are:

- end-to-end enough to verify
- narrow enough for one focused test cycle
- easy to explain in `state.md`

Avoid:

- all tests first
- all implementation first
- speculative abstractions
- unrelated cleanup mixed into a slice

## Checkpoint Notes

After each slice, record:

- what behavior now works
- what test proves it
- what is next