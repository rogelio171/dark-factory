---
title: Dark Factory Wiki Schema
version: 1
owner: llm
---

# Wiki Schema

This wiki is the persistent knowledge layer for a project.

## Principles

- The wiki is maintained by the agent and reviewed by humans.
- Raw sources are read-only inputs: Jira tickets, code, external docs, and notes.
- Wiki pages are durable summaries, not chat transcripts.
- Update existing pages before creating new pages when the topic already exists.
- Prefer links between pages over repeating the same explanation.
- When a new source changes prior understanding, update the affected pages and note the change in `wiki/log.md`.

## Required Files

- `wiki/schema.md`: the rules in this file.
- `wiki/index.md`: catalog of pages with one-line summaries.
- `wiki/log.md`: append-only record of wiki updates and important discoveries.

## Required Directories

- `wiki/architecture/`: system boundaries, data flow, deployment, and integration notes.
- `wiki/patterns/`: coding conventions, testing patterns, naming, and common implementation moves.
- `wiki/stack/`: framework, library, tooling, and runtime notes.
- `wiki/entities/`: domain concepts, business objects, workflows, and terminology.

## Page Conventions

- Use Markdown.
- Keep pages focused on one topic.
- Start pages with a short summary sentence.
- Add links to related pages when relevant.
- Write for continuation: another agent should be able to pick up work from the page alone.

## Update Workflow

1. Read the relevant raw sources.
2. Read `wiki/index.md` to find related pages.
3. Update existing pages that overlap with the new information.
4. Create a new page only when the concept has no natural home.
5. Update `wiki/index.md`.
6. Append a short entry to `wiki/log.md`.

## Suggested Frontmatter

```yaml
---
title: Example Page
summary: One-line summary.
updated: 2026-04-13
sources:
  - jira: OFRS2-12345
  - code: src/features/example.ts
related:
  - ../patterns/testing.md
---
```

## Naming

- Use kebab-case file names.
- Name pages by the durable concept, not the current task.
- Put story-specific work in `docs/specs/`, not in the wiki.
