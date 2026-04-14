---
name: dark-factory
description: Orchestrates the Dark Factory delivery workflow from wiki bootstrap through Jira completion using state files and phase-specific skills. Use when the user says dark factory, start a story, work on a Jira ticket, resume delivery, or wants the full ticket-to-done workflow.
---

# Dark Factory

## Quick Start

Use this skill as the entry point.

1. Identify the target ticket or active story.
2. Check whether project knowledge already exists in `wiki/`.
3. Check for story state in `docs/specs/<ticket-slug>/state.md`.
4. Dispatch to the next phase skill.

## Workflow

1. If `wiki/` is missing, use `df-wiki-init`.
2. If no story is active, use `df-story-intake`.
3. If requirements are unclear, use `df-clarify`.
4. If no detailed spec exists, use `df-spec`.
5. Implement through `df-implement`.
6. Run the review loop with `df-review`.
7. Gather evidence with `df-evidence`.
8. Create the PR and update Jira with `df-ship`.
9. If work was interrupted, use `df-resume`.

## Rules

- Read `docs/specs/*/state.md` before choosing a phase.
- Advance one phase at a time and keep the state file current.
- Stop and ask the user if a required external integration is unavailable.
- Prefer existing wiki pages over rediscovering the same context.
- Keep implementation minimal and acceptance-criteria driven.

## Files

- For the full state model and phase rules, see [REFERENCE.md](REFERENCE.md).
