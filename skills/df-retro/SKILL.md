---
name: df-retro
description: Mines the observability store across all stories for recurring blockers, flaky validation commands, and risk-model drift signals, then folds the findings into durable wiki pages so later stories benefit from what earlier ones learned. Use when a retro cadence is due (roughly every 10 merges, or monthly) or when the user asks to review Dark Factory's own delivery health.
---

# DF Retro

## Goal

Close the loop from individual story outcomes back into project knowledge, so patterns that only show up across many stories (not within one) get fixed instead of silently recurring.

## Inputs

- `df observability report --since <window>` for run/failure/blocked counts.
- `df observability query --category risk.revert --since <window>` for risk-model drift signals recorded by `df-story-intake`.
- `docs/specs/*/state.md` for current `blocked_reason` text (read-only).
- `wiki/log.md` for the merge history since the last retro.
- `wiki/retro-log.md` for the date of the last retro run (created by this skill on first run).

## Preconditions

- `df observability doctor` passes (the observability store exists and is writable).
- At least one delivery run has completed or been blocked since the last retro window; if not, say so and stop instead of writing empty findings.

## Workflow

1. Read `wiki/retro-log.md` for the last retro date; if it does not exist, use a 30-day window and treat this as the first retro.
2. Run `df observability report --since <window>` for aggregate counts: runs by status, failures by category, blocked runs, phase transition counts.
3. Run `df observability query --category risk.revert --since <window>` for every risk-model drift signal recorded since the last retro.
4. For each `risk.revert` event, resolve the affected paths from the referenced ticket's `spec.md` module scope (if the story dir still exists) and update `wiki/patterns/risk-model-drift.md` per the format in [REFERENCE.md](REFERENCE.md), deduplicating by path.
5. Group `blocked_reason` text across current `status: blocked` stories and any `blocked` runs from the report; for any reason that recurs 2+ times, write or refresh an entry in `wiki/patterns/recurring-blockers.md`.
6. For `failures_by_category` entries dominated by `preflight.*` or `ci.*`, list them as candidates for a `wiki/project-profile.md` refresh or a real fix, and flag them to the user; do not edit `wiki/project-profile.md` from this skill.
7. Summarize the pages touched and any finding that needs a human decision.
8. Append a dated entry to `wiki/retro-log.md`: the window covered, counts from the report, and links to every page touched this pass.

## Delegation Model

This is mostly deterministic aggregation over `df observability` output, not broad exploration, so the coordinator can run most of it directly.

- When a `risk.revert` event's root cause is not obvious from `spec.md` and the merged diff alone, delegate the diagnosis to a subagent that reads the diff, the original review notes, and the failure; the coordinator decides what (if anything) goes into `wiki/patterns/risk-model-drift.md`.
- The coordinator owns every write to `wiki/patterns/` and `wiki/retro-log.md`; a subagent only researches and reports back.

## Observability

- `df-retro` is fleet-level, not ticket-scoped, so it has no `run_id` to attach to. Record the pass directly as an event instead: `df observability event record --category retro.run --action summarize --status success --summary "<window>: <n> patterns updated"`.
- Record external snapshots only if the retro queries GitHub or Jira directly (it normally does not; it reads local artifacts and the observability store).
- Full contract: `df-observability`.

## Outputs

- `wiki/patterns/risk-model-drift.md`, created or refreshed with deduplicated path entries.
- `wiki/patterns/recurring-blockers.md`, created or refreshed with recurring blocker patterns.
- `wiki/retro-log.md`, appended with this pass's summary.
- A user-facing summary naming every finding that needs a human decision.

## Rules

- Do not modify any `docs/specs/<ticket>/` file; retro reads story state, it never mutates it.
- Do not retroactively change `risk` or `auto_merge_eligible` on an in-flight or already-merged story; `wiki/patterns/risk-model-drift.md` only affects `df-spec`'s classification on the *next* story that touches that path.
- Deduplicate by path or blocker signature; do not append a new line every retro pass for the same recurring issue, refresh the existing one's count and last-seen date instead.
- If the observability window has no new runs, no blockers, and no `risk.revert` events, say so explicitly and skip writing pages; an empty retro is a valid outcome.

## Handoff

`df-retro` is not part of the ticket-to-done phase chain. When finished, return control to the user or the `dark-factory` orchestrator with the summary; no specific next skill is required.

## Files

- Page formats and the `risk.revert` convention: [REFERENCE.md](REFERENCE.md).
