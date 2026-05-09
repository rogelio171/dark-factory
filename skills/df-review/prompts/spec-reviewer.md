# Dark Factory Spec Reviewer Prompt

Review the current diff against the Dark Factory story spec.

## Inputs

- `state.md`
- `spec.md`
- `plan.md`
- current diff
- `wiki/project-profile.md`

## Review Focus

1. Every acceptance criterion is implemented or explicitly deferred.
2. The implementation follows the checked plan tasks.
3. Tests prove the requested public behavior.
4. Changes stay within `target_modules` unless shared modules are recorded in `state.md`.
5. No unrelated behavior was added.

## Output

Group findings by severity:

- `critical`: must fix before evidence or shipping
- `suggestion`: low-risk improvement
- `optional`: nice to have

If there are no critical findings, say so explicitly.
