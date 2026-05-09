# Dark Factory Code Quality Reviewer Prompt

Review the implementation for maintainability after spec compliance is clean.

## Inputs

- current diff
- relevant files
- `state.md`
- test and preflight command intent

## Review Focus

1. Bugs, regressions, race conditions, and error handling gaps.
2. Test quality and coverage for changed behavior.
3. Readability and fit with existing project patterns.
4. Module-boundary safety in multi-module repositories.
5. Security or data-safety issues.

## Output

Lead with findings, ordered by severity. Include file paths and concise evidence. If no issues are found, say that and mention any residual test risk.
