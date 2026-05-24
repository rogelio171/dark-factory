---
name: df-observability
description: Records full agent events, MCP interactions, CLI activity, and external system snapshots into the SQLite observability store for enterprise audit, debugging, and delivery metrics. Use when starting any Dark Factory phase, after agent turns or tool calls, at phase boundaries, or when exporting audit data.
---

# DF Observability

## Goal

Persist every meaningful interaction during Dark Factory delivery into `.agents/dark-factory/observability.db` so engineers, compliance, managers, and alerting jobs can reconstruct and analyze work without chat history.

## Inputs

- `.agents/dark-factory/observability.db` (created by `df observability init` during install).
- `.agents/dark-factory/observability.toml` (retention and redaction policy).
- `docs/specs/<ticket>/state.md` (`run_id`, `observability_enabled`).
- Optional runtime env vars: `DF_RUNTIME`, `DF_RUN_ID`, `DF_SESSION_ID`.

## Preconditions

- Dark Factory is installed in the target repo (`install.sh` runs `df observability init`).
- The active story has a `run_id` in `state.md`, or you create one before recording.

## Workflow

1. Confirm the store exists: `df observability doctor`.
2. Read `run_id` from `state.md`. If missing:
   - `df observability run start <TICKET-ID> --write-state --phase <current-phase>`
3. At the start of every phase skill:
   - `df observability session start --run-id "$RUN_ID" --skill <skill-name> --role coordinator`
   - Export `DF_SESSION_ID` from the printed JSON for subsequent records in that phase.
4. During the phase, record **every** interaction:
   - User messages and assistant responses (full content).
   - Tool and MCP calls with inputs and outputs.
   - User decisions and risk-gate approvals.
   - File writes and artifact paths.
5. Use single records or batch flush at phase boundaries:
   - `df observability message record --session-id "$DF_SESSION_ID" --role user --content "..."`
   - `df observability event record --run-id "$RUN_ID" --category workflow.decision --action user.approval --summary "..." --input '{"decision":"ship"}'`
   - `df observability batch --file /tmp/df-batch.jsonl` (preferred before handoff).
6. After GitHub/Jira/CI interactions, capture snapshots:
   - `df observability snapshot record --source github --snapshot-type pr_poll --reference "$PR_NUMBER" --payload @status.json --run-id "$RUN_ID"`
7. At phase end:
   - `df observability session end --session-id "$DF_SESSION_ID"`
   - Update `state.md` phase via `df state set` (auto-logs phase transitions when `run_id` is set).
8. When the story completes:
   - `df observability run end --run-id "$RUN_ID" --status complete --phase complete`
9. For audit export (batch):
   - `df observability export --ticket <TICKET-ID> --format jsonl --output .agents/dark-factory/exports/<ticket>.jsonl`
10. For metrics:
   - `df observability report --since 30d`

## Observability

This skill defines the recording contract for all other skills. The coordinator must not skip recording because content is large; redaction and truncation are handled automatically.

## Outputs

- Rows in `delivery_runs`, `agent_sessions`, `agent_messages`, `interaction_events`, and `external_snapshots`.
- Optional export files under `.agents/dark-factory/exports/`.
- Updated `run_id` in `state.md` when `--write-state` is used.

## Rules

- Record full agent content unless `observability.toml` `strict_pii = true` (then summarize ticket bodies in events only).
- Never store raw secrets; the harness redacts common token and key patterns at write time.
- Prefer `df observability batch` before phase handoff to reduce CLI overhead.
- Set `DF_RUNTIME=cursor|claude|codex|copilot` when the runtime exposes no auto-detection.
- Subagent work uses `session start` with `--parent-session-id` pointing at the coordinator session.
- Do not commit `observability.db`; it is gitignored by the installer.
- Batch export is sufficient; real-time streaming is not required.

## Handoff

Return to the active phase skill after recording. On story completion, invoke `df-wiki-update` then `df observability run end`.

## Files

- Event taxonomy, batch JSONL format, runtime adapter templates, and cron examples: [REFERENCE.md](REFERENCE.md).
- Compliance, retention, export, and ops runbooks: `docs/OBSERVABILITY.md` in the skill pack repository.
