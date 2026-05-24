# DF Observability Reference

## Batch JSONL envelope

Each line is a JSON object with a `type` field:

```json
{"type":"message","session_id":"...","role":"assistant","content":"...","tool_name":"","metadata":{"phase":"implementing"}}
{"type":"event","run_id":"...","category":"workflow.decision","action":"user.approval","ticket":"OFRS2-1","summary":"Approved ship","status":"success","input_json":{"decision":"ship"}}
{"type":"snapshot","run_id":"...","source":"jira","snapshot_type":"issue_fetch","reference":"OFRS2-1","payload":{"fields":{}}}
{"type":"run_start","ticket":"OFRS2-1","story_slug":"OFRS2-1-add-toggle","current_phase":"intake"}
{"type":"session_start","run_id":"...","skill_name":"df-implement","agent_role":"implementer"}
```

Ingest with:

```bash
df observability batch --file batch.jsonl
```

## Event categories

| Category | When to record |
| --- | --- |
| `workflow.phase` | Phase transitions, run start/end |
| `workflow.decision` | User approvals, clarifications, risk gates |
| `agent.delegation` | Subagent spawn/complete (also use sessions) |
| `agent.tool` | Tool/MCP calls (detail in `agent_messages`) |
| `cli.command` | Auto-recorded by `df` harness |
| `github.pr` / `github.snapshot` | PR poll, ship, thread actions |
| `jira.snapshot` | Issue fetch, comment, transition |
| `preflight.stage` | Auto-recorded by `df preflight` |
| `evidence.capture` | Evidence file written |
| `export.batch` | Auto-recorded on export |
| `retention.prune` | Auto-recorded on prune |

## Runtime adapters (optional)

Any runtime with shell access can pipe hook output into the store:

```bash
# Generic stdin ingest script (templates/scripts/ingest-stdin.sh)
df observability batch --file -
```

Set environment variables for the active delivery:

```bash
export DF_RUN_ID="<uuid from state.md>"
export DF_SESSION_ID="<uuid from session start>"
export DF_RUNTIME="cursor"
```

### Cursor hooks (optional)

See `templates/cursor-hooks.json`. Hooks call `ingest-stdin.sh` with JSONL lines; they are optional because skills also mandate manual recording.

### Claude Code hooks (optional)

See `templates/claude-hooks.json` for PreToolUse/PostToolUse patterns that append JSONL batches.

## Retention and prune

Default retention is 365 days (configurable in `observability.toml`).

```bash
# Weekly cron example
df observability prune
df observability export --since 7d --format jsonl --output .agents/dark-factory/exports/weekly.jsonl
```

## Query examples

```bash
df observability tail --ticket OFRS2-123
df observability query --ticket OFRS2-123 --category github.snapshot --json
df observability run-show <run-id>
df observability session show <session-id>
df observability report --since 90d
```

## Migration for existing stories

```bash
df observability migrate-states
```

Backfills `run_id` into story states that predate observability.

## Related documents

- `docs/OBSERVABILITY.md` in the skill pack repository — compliance and operations guide (retention, export, audit reconstruction, cron)
