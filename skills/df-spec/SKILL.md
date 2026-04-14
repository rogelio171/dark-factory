---
name: df-spec
description: Creates a durable story PRD in `docs/specs/` with implementation slices, test intent, and resume-friendly checklists. Use when a Jira story is clear enough to plan implementation or when a detailed `spec.md` is missing.
---

# DF Spec

## Goal

Write `docs/specs/<ticket-slug>/spec.md` so another agent can continue the work without relying on chat history.

## Workflow

1. Read the Jira story, clarification notes, and relevant wiki pages.
2. Create or update `spec.md` from the template.
3. Keep the original acceptance criteria visible and traceable.
4. Break the work into thin vertical slices with checkboxes.
5. Record current progress and the next safe step in `state.md`.

## Rules

- Write for continuation, not just planning.
- Keep implementation decisions concrete but not over-engineered.
- Include testing intent before implementation starts.
- Prefer tracer bullets over big-bang plans.
- Mark the story phase as `specifying` while this skill is active.

## Files

- Use `templates/spec-template.md`.
- Use `templates/state-template.md`.
