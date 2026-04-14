---
name: df-wiki-init
description: Creates or refreshes the Dark Factory project wiki for new or existing codebases using Karpathy-style persistent wiki patterns. Use when a project has no wiki, needs initial repo analysis, or the user asks to bootstrap documentation from the codebase.
---

# DF Wiki Init

## Goal

Create `wiki/` as the durable project knowledge layer.

## New Project Mode

If the project is new or mostly empty:

1. Create `wiki/`, `wiki/architecture/`, `wiki/patterns/`, `wiki/stack/`, and `wiki/entities/`.
2. Copy the template files from `templates/schema.md`, `templates/index.md`, and `templates/log.md`.
3. Add an initial log entry describing the bootstrap.

## Existing Project Mode

If the project already has code:

1. Read the whole codebase in broad strokes using subagents when helpful.
2. Identify:
   - stack and tooling
   - architecture boundaries
   - testing approach
   - naming and file conventions
   - domain entities and workflows
3. Create or update wiki pages in the correct directories.
4. Update `wiki/index.md` and append `wiki/log.md`.

## Rules

- Read `wiki/schema.md` after creating it and follow it for all future wiki maintenance.
- Prefer durable pages like `api-boundaries.md` over ticket-shaped pages.
- Keep the wiki concise enough to scan, but complete enough for another agent to continue work.
- If the repo is very large, summarize by subsystem instead of trying to mirror every file.

## Files

- Templates live in `templates/`.
