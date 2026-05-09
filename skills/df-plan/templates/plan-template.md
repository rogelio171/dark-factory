# <TICKET-ID> - Implementation Plan

## Goal

One sentence describing the behavior this story will deliver.

## Scope

- Working root: `<path>`
- Target modules: `<module-paths>`
- Out-of-scope modules:
- Shared modules affected:

## Validation Commands

Run from `<working-root>` unless specified otherwise.

- Lint: `<command-or-none>`
- Typecheck: `<command-or-none>`
- Test: `<command-or-none>`
- Build: `<command-or-none>`

## Tasks

### Task 1 - <Name>

**Files**

- Test:
- Modify:
- Create:

- [ ] Step 1: Write the failing test

```text
<exact test intent or code>
```

- [ ] Step 2: Verify the test fails for the expected reason

Run: `<command>`
Expected: fails because `<missing behavior>`

- [ ] Step 3: Implement the minimum code

```text
<exact implementation notes or code shape>
```

- [ ] Step 4: Verify the test passes

Run: `<command>`
Expected: passes with no unrelated failures

- [ ] Step 5: Run scoped validation

Run: `<command>`
Expected: passes

- [ ] Step 6: Commit checkpoint

```bash
git add <files>
git commit -m "<ticket-id>: <short behavior>"
```

## Rollback Notes

- Revert strategy:
- Data or migration rollback:

## Completion Checklist

- [ ] All tasks checked off
- [ ] Review notes saved
- [ ] Evidence plan still matches acceptance criteria
- [ ] Preflight commands ready and scoped
