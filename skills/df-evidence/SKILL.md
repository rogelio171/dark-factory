---
name: df-evidence
description: Validates completed story behavior with Playwright MCP screenshots and records evidence for each acceptance criterion. Use when implementation and review are done and the story needs proof that the requested behavior works.
---

# DF Evidence

## Goal

Produce reusable proof that the story satisfies the acceptance criteria.

## Workflow

1. Read `spec.md` and the acceptance criteria.
2. Map each criterion to a browser validation step.
3. Use Playwright MCP to open the app and exercise the behavior.
4. Save screenshots under `docs/specs/<ticket>/evidence/`.
5. Create an evidence log that maps each criterion to the screenshot or recording.

## Rules

- Do not claim a criterion is complete without observable proof.
- Use one screenshot per important checkpoint when possible.
- If the app cannot be run or reached, stop and record the blocker.
- Keep evidence file names descriptive and stable.

## Handoff

When evidence is complete, move to `df-ship`.
