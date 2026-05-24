---
name: df-plan
description: Writes `docs/specs/<ticket-slug>/plan.md` with exact TDD implementation tasks, module-scoped commands, and commit checkpoints. Use when `df-spec` is complete and before `df-implement`.
---

# DF Plan

## Goal

Turn `spec.md` into a concrete implementation plan that another agent can execute without guessing.

## Inputs

- `docs/specs/<ticket>/state.md`.
- `docs/specs/<ticket>/spec.md`.
- `wiki/project-profile.md`.

## Preconditions

- `state.md` is `status: planning` or ready to advance from `specifying`.
- `spec.md` is complete enough to identify files, tests, and validation commands.
- Module scope and validation commands are recorded in `state.md`.

## Workflow

1. Read `state.md`, `spec.md`, and `wiki/project-profile.md`.
2. Confirm deterministic fields with `df state get <TICKET-ID> target_modules`, `df state get <TICKET-ID> working_root`, and `df state get <TICKET-ID> validation_commands`.
3. Create or update `plan.md` from `templates/plan-template.md`.
4. Break the work into small tasks that each include:
   - exact files to create or modify
   - one failing test to write first
   - command to verify the failure
   - minimal implementation step
   - command to verify success
   - commit checkpoint
5. Mark `state.md` as `planning` while this skill is active with `df state set <TICKET-ID> status planning`.
6. When the plan is complete, set the next status to `implementing` with `df state set <TICKET-ID> status implementing`.


## Observability

- Read `run_id` from `state.md`. If missing, run `df observability run start <TICKET-ID> --write-state`.
- Open a phase session: `df observability session start --run-id "$RUN_ID" --skill df-plan --role coordinator`.
- Record every user message, assistant response, and tool/MCP call via `df observability message record` or `df observability batch`.
- Record external snapshots after Jira, GitHub, or CI interactions relevant to this phase.
- Close the session with `df observability session end --session-id "$DF_SESSION_ID"` before handoff.
- Full contract: `df-observability`.

## Outputs

- `docs/specs/<ticket>/plan.md` populated from the template.
- Updated `state.md` with `status: implementing` and the next safe task.

## Rules

- Do not use placeholders such as `TBD`, `TODO`, or "write tests".
- Keep commands scoped to `target_modules`.
- Include exact command roots when they differ from repo root.
- Do not start implementation from this skill.
- If the spec is too broad for one plan, stop and ask the user to split it.

## Handoff

When `plan.md` is complete, advance `state.md` to `status: implementing` and invoke `df-implement`.

## Files

- Use `templates/plan-template.md`.
