---
name: df-clarify
description: Decides whether a Jira story is already clear enough to specify, or needs targeted interviewing first, by combining ticket text, wiki context, and the `df-grill-me` interview loop. Use when a story is ambiguous, acceptance criteria are incomplete, or the next safe step is not obvious.
---

# DF Clarify

## Goal

End the clarification phase with a story that is safe to spec: either move directly to `df-spec` or capture the missing answers first.

## Inputs

- The Jira ticket (via Atlassian Rovo MCP).
- `docs/specs/<ticket>/state.md`.
- Relevant wiki pages (`wiki/architecture/`, `wiki/patterns/`, `wiki/entities/`).

## Preconditions

- `state.md` exists with `status: intake` or `status: clarifying`.
- The user has indicated they want clarification (or `df-spec` was called and bounced back).

## Workflow

1. Read the Jira story and current `state.md`.
2. Read relevant wiki pages before asking the user anything.
3. Identify the real gaps:
   - missing behavior
   - unclear edge cases
   - unclear UX or business rules
   - unclear validation or rollout expectations
4. If the gaps are small and answerable from wiki + ticket, summarize them in `state.md` under "Decisions" and proceed.
5. If the gaps are material, invoke `df-grill-me` to interview the user one question at a time.
6. Record the resolved answers in `state.md` under "Decisions".

## Outputs

- Updated `state.md` with `status: clarifying` and any captured decisions.
- Notes summarizing the resolved gaps for `df-spec` to inline into the spec.

## Rules

- Do not interview the user just because a ticket is short.
- Ask only what is needed to implement safely.
- Prefer wiki-backed answers over speculative questions.
- Update the story phase to `clarifying` while this skill is active.

## Handoff

When the story is clear enough to plan, advance `state.md` to `status: specifying` and invoke `df-spec`.
