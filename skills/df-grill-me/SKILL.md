---
name: df-grill-me
description: Interviews the user one question at a time to resolve ambiguity in a plan, design, architecture, or requirement set, while proposing a recommended answer from codebase and wiki context. Use when a plan is unclear, a ticket is underspecified, or the user asks to be grilled on an idea.
---

# DF Grill Me

## Goal

Drive ambiguous work toward shared understanding before implementation starts.

## Method

1. Read the available context first: code, docs, wiki, ticket text, or prior decisions.
2. Ask only the next most important unresolved question.
3. Include a recommended answer with each question.
4. Wait for the answer before moving to the next branch.

## Rules

- Ask one question at a time.
- If the codebase or wiki can answer the question, answer it there instead of asking the user.
- Skip branches that are already clear.
- Keep drilling until the remaining uncertainty is small enough to implement safely.
- Record the resolved decisions where downstream skills can use them.

## Good Targets

- underspecified acceptance criteria
- missing edge-case behavior
- unclear ownership between systems
- ambiguous UX, testing, or rollout expectations
