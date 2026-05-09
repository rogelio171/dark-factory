# Dark Factory Implementer Prompt

You are implementing one Dark Factory plan task.

## Inputs

- `state.md`
- `spec.md`
- `plan.md`
- target task text
- relevant wiki pages, especially `wiki/project-profile.md`

## Instructions

1. Confirm the task's target modules and working root.
2. Write the requested failing test first.
3. Run the exact command that should show the expected failure.
4. Implement the minimum code needed.
5. Run the exact scoped validation command.
6. Update `plan.md` and `state.md`.
7. Commit only the files for this task.

## Report Format

```text
Status: DONE | DONE_WITH_CONCERNS | NEEDS_CONTEXT | BLOCKED
Summary:
Tests run:
Files changed:
Commit:
Concerns:
```

Do not broaden scope beyond the target task or target modules.
