---
name: df-resume
description: Resumes interrupted Dark Factory work by reading story state, specs, review notes, and evidence folders to determine the next safe phase. Use when a session ended early, work was partially completed, or the user asks to continue an existing story.
---

# DF Resume

## Goal

Recover the current story state from disk instead of relying on chat memory.

## Workflow

1. Find active stories under `docs/specs/`.
2. Read each `state.md`.
3. Identify the most recent in-progress story or ask the user which one to resume.
4. Read the supporting artifacts for that story:
   - `spec.md`
   - review notes
   - evidence files
5. Confirm the repository state matches the recorded phase.
6. Dispatch to the correct next skill.

## Rules

- Treat `state.md` as the primary resume source.
- If the repo state and `state.md` disagree, stop and reconcile first.
- Prefer the safest next action over the fastest one.
- Update `last_updated` when resuming.

## Handoff

Resume into the phase named in `state.md`.
