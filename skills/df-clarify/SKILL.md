---
name: df-clarify
description: Clarifies a Jira story by combining ticket details, wiki context, and the df-grill-me interview loop, then records resolved decisions for downstream implementation. Use when a story is ambiguous, acceptance criteria are incomplete, or the next safe step is not obvious.
---

# DF Clarify

## Goal

Decide whether a story is already clear enough to specify, or needs targeted interviewing first.

## Workflow

1. Read the Jira story and current `state.md`.
2. Read relevant wiki pages before asking the user anything.
3. Identify the real gaps:
   - missing behavior
   - unclear edge cases
   - unclear UX or business rules
   - unclear validation or rollout expectations
4. If the gaps are small, summarize them and proceed to `df-spec`.
5. If the gaps are material, invoke `df-grill-me`.
6. Record the resolved answers in `state.md` and later in `spec.md`.

## Rules

- Do not interview the user just because a ticket is short.
- Ask only what is needed to implement safely.
- Prefer wiki-backed answers over speculative questions.
- Update the story phase to `clarifying` while this skill is active.

## Handoff

When the story is clear, the next skill is `df-spec`.
