---
name: df-wiki-update
description: Folds the merged story's lessons into the project wiki by appending new patterns, entities, architecture notes, and a dated log entry, then updating the wiki index. Use when a story has merged or the user wants to refresh the wiki from a recently shipped change.
---

# DF Wiki Update

## Goal

Make sure the wiki accumulates project knowledge after every merge, so the next story benefits from what this one learned.

## Inputs

- `docs/specs/<ticket>/spec.md`
- `docs/specs/<ticket>/state.md` (must be `status: merging` with `merge_sha` populated, or `status: complete`)
- The merge SHA and merged diff (`git show <merge_sha> --stat`)
- The current `wiki/` tree

## Preconditions

- The PR has merged into the default branch.
- `wiki/` exists (otherwise drop back to `df-wiki-init` first).

## Workflow

1. Read `spec.md` and the merged diff summary.
2. Decide what is genuinely new knowledge:
   - A reusable pattern (caching strategy, error-handling shape, validation approach) -> `wiki/patterns/<name>.md`.
   - A new domain entity or a meaningful change to an existing one -> `wiki/entities/<name>.md`.
   - An architecture boundary or integration that was not documented -> `wiki/architecture/<name>.md`.
   - A new tool, library, or framework added to the stack -> `wiki/stack/<name>.md`.
3. Create or update those pages. Keep entries small, durable, and linkable.
4. Append a dated entry to `wiki/log.md`:
   ```markdown
   ## 2026-04-19 - OFRS2-12345 - add dark mode toggle (merged abc1234)
   - New pattern: theme-context (`wiki/patterns/theme-context.md`)
   - Updated entity: user-preferences (`wiki/entities/user-preferences.md`)
   - PR: <pr_url>
   ```
5. Update `wiki/index.md` if any new pages were added.
6. Update `state.md`: set `status: complete` and append a "wiki updates" line under "Resume Notes".

## Outputs

- New or updated files under `wiki/patterns/`, `wiki/entities/`, `wiki/architecture/`, `wiki/stack/`.
- New entry in `wiki/log.md`.
- Updated `wiki/index.md` if the page set changed.
- `state.md` advanced to `status: complete`.

## Rules

- Only add knowledge that will be useful to a different story. Do not mirror the spec into the wiki.
- Prefer durable page names (`api-error-shape.md`) over ticket-shaped names (`OFRS2-12345-notes.md`).
- Do not delete or rename existing wiki pages without an explicit reason in the log entry.
- If nothing is genuinely new, still append a one-line `wiki/log.md` entry recording the merge for traceability and skip the other steps.
- Never run before the merge SHA is known; this skill is post-merge only.

## Handoff

When the wiki is updated and `state.md` is `status: complete`, the story is done. Return control to the user or to the `dark-factory` orchestrator.
