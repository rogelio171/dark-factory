---
name: df-audit
description: Runs a deterministic process-and-artifact audit at two checkpoints (pre-ship and post-merge) to catch phase drift that a self-reported `state.md` cannot catch on its own, distinct from `df-review`'s code review. Use when `df-ship` is about to open a PR or `df-merge` has just merged one, before either advances `state.md`.
---

# DF Audit

## Goal

Verify that a story's durable artifacts and observability trail actually match what `state.md` claims, before the coordinator commits to shipping or closing out the story.

## Inputs

- `docs/specs/<ticket>/state.md`.
- `docs/specs/<ticket>/spec.md` and `plan.md`.
- `docs/specs/<ticket>/reviews/*.md`.
- `docs/specs/<ticket>/evidence/INDEX.md`.
- `docs/specs/<ticket>/preflight.json`.
- `df observability run-show "$RUN_ID"` (session and event history for the run).
- The `.github/CODEOWNERS` file and the PR's labels, when auditing post-merge.

## Preconditions

- Pre-ship mode: `state.md` is `status: preflight`, `preflight.json` has `summary: passed` or `passed-with-warnings`, and `df-ship` has not yet run for this pass.
- Post-merge mode: `df-merge` has just recorded `merge_sha` and is about to set `status: complete`.

## Workflow

1. Determine mode from the caller (`df-ship` invokes pre-ship mode; `df-merge` invokes post-merge mode).
2. Read `state.md` and the run's observability history with `df observability run-show "$RUN_ID"`.
3. Walk the checklist for the current mode in [REFERENCE.md](REFERENCE.md) and record a pass/fail per item.
4. If every item passes, write `docs/specs/<ticket>/audit/<mode>-<n>.md` marked clean and return control to the caller.
5. If any item fails, write the same file marked not-clean with the specific gap, then route the fix:
   - A missing or incomplete artifact (spec, plan, review, evidence, preflight) routes back to the skill that owns that artifact.
   - A missing observability session close or a state field that contradicts the artifacts is not scope for a subagent; fix it directly by closing the session or correcting the field, then re-run the check.
   - If the gap cannot be resolved without a decision only the user can make (e.g. a CODEOWNERS path shipped without the required reviewer note), run `df state block <TICKET-ID> --reason "audit gap: <summary>"` and stop.
6. Never let the caller advance past a failed audit silently.

## Observability

- Read `run_id` from `state.md`. If missing, run `df observability run start <TICKET-ID> --write-state`.
- Open a phase session: `df observability session start --run-id "$RUN_ID" --skill df-audit --role coordinator`.
- Record the audit verdict as `df observability event record --category audit.finding --action <pre-ship|post-merge> --status <success|failure> --summary "<verdict>"`.
- Record external snapshots only if the audit itself queries GitHub or Jira state directly.
- Close the session with `df observability session end --session-id "$DF_SESSION_ID"` before handoff.
- Full contract: `df-observability`.

## Outputs

- `docs/specs/<ticket>/audit/pre-ship-<n>.md` or `docs/specs/<ticket>/audit/post-merge-<n>.md`, one per audit pass.
- A pass/fail verdict returned to the calling skill.
- Corrected `state.md` fields or artifacts when the gap was a direct fix.

## Rules

- Never mark an audit clean because the code review passed; code review and process audit are separate concerns.
- Never mark an audit clean when an observability session for the run has no `ended_at`.
- Never silently downgrade a failed item to a note; either fix it or block.
- Keep audit notes short and specific: which checklist item failed, the file or field that proves it, and what was done about it.
- This is a deterministic checklist walk, not exploratory work; run it directly rather than delegating it to a subagent unless the repository is large enough that reading the full artifact set would blow the coordinator's context, in which case delegate the read-only gathering step only.

## Handoff

- Pre-ship, clean: return to `df-ship`, which proceeds with opening the PR.
- Pre-ship, not clean: return to the phase skill that owns the missing artifact (`df-spec`, `df-plan`, `df-review`, `df-evidence`, or `df-preflight`).
- Post-merge, clean: return to `df-merge`, which sets `status: complete`.
- Post-merge, not clean: `df-merge` stays in `status: merging` (or `status: blocked` if escalated) until the gap is fixed.

## Files

- Checklist detail: [REFERENCE.md](REFERENCE.md).
