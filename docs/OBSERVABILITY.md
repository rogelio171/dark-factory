# Dark Factory Observability

This document is the compliance and operations reference for Dark Factory's SQLite-backed observability layer. It describes what is recorded, how to query and export it, and how to operate retention and audit workflows in a target repository.

For day-to-day agent recording rules, see the `df-observability` skill. For workflow context, see [WORKFLOW.md](WORKFLOW.md).

## Purpose

Dark Factory delivery spans multiple agents, CLI commands, and external systems (Jira, GitHub, CI). The observability store provides:

- **Audit trail** — reconstruct who/what did what, and when, for a ticket delivery
- **Full agent history** — user messages, assistant responses, and tool/MCP invocations
- **Operational telemetry** — CLI timings, preflight stages, PR polls, CI failure snapshots
- **Delivery metrics** — cycle time, blocked runs, failure rates by category

The store is **local to each target repository**. It is initialized automatically by `install.sh` and is runtime-agnostic (Cursor, Claude Code, Codex, Copilot, or any agent with shell access).

## Layout

After install, each target repo contains:

```text
.agents/dark-factory/
├── observability.toml        # retention + redaction policy (safe to commit)
├── observability.db          # SQLite database (gitignored)
├── observability.db-wal      # WAL files (gitignored)
├── observability.db-shm
├── redaction-patterns.txt    # optional custom regex patterns
└── exports/                  # batch export output (gitignored)
```

Story state links to the store via `run_id` in `docs/specs/<ticket>/state.md`.

## What is recorded

| Source | Recorded automatically | Recorded by agents (required) |
| --- | --- | --- |
| `df` CLI | Every command (`cli.command`), duration, exit code | — |
| Phase transitions | When `df state set … status …` and `run_id` is set | Orchestrator dispatch decisions |
| Preflight | Full `preflight.json` snapshot + per-stage events | — |
| GitHub | PR ship/poll/reconcile, failed CI log snapshots | Review thread actions (via events) |
| Resume | PR reconciliation snapshots | — |
| Story init | Delivery run + `run_id` in state | — |
| Agent chat | — | Full messages via `message record` or `batch` |
| Jira MCP | — | Snapshots after fetch/comment/transition |
| User decisions | — | `workflow.decision` events |
| Exports / prune | Export job metadata | — |

### What is not recorded

- Chat history outside Dark Factory sessions (unless the agent records it)
- GitHub/Jira data that agents never snapshot
- Real-time streaming to external SIEM (batch export only in v1)

## Data model

SQLite schema version **1**. Core tables:

| Table | Purpose |
| --- | --- |
| `delivery_runs` | One row per story execution (`run_id`, ticket, phase, status, runtime) |
| `agent_sessions` | Coordinator/subagent conversation containers |
| `agent_messages` | Full message content, tool inputs/outputs, sequence order |
| `interaction_events` | Structured audit log (OTel-style categories, severity, status) |
| `external_snapshots` | GitHub/Jira/CI/preflight JSON payloads |
| `export_jobs` | Audit of who exported what and when |

Correlation:

- **`run_id`** — root correlation ID for a ticket delivery (stored in `state.md`)
- **`session_id`** — groups messages for one phase or subagent
- **`trace_id` / `span_id`** — on `interaction_events` for cross-event linking

## Configuration

Edit `.agents/dark-factory/observability.toml`:

```toml
[retention]
default_days = 365
agent_messages_days = 365
interaction_events_days = 365
external_snapshots_days = 365

[redaction]
enabled = true
patterns_file = .agents/dark-factory/redaction-patterns.txt
max_content_bytes = 1048576

[export]
default_format = jsonl
include_agent_messages = true
include_snapshots = true

[compliance]
append_only = true
record_cli_commands = true
strict_pii = false
```

| Setting | Default | Notes |
| --- | --- | --- |
| `default_days` | 365 | Fallback retention for tables without a specific override |
| `agent_messages_days` | 365 | Full conversation history |
| `strict_pii` | false | When true, agents should summarize ticket bodies in events only (skill contract) |
| `max_content_bytes` | 1 MiB | Larger payloads truncated with a `[TRUNCATED]` marker |

View effective config:

```bash
df observability config
```

## Redaction and secrets

Redaction runs **at write time** before rows are inserted:

- API keys, tokens, Bearer headers, PEM private keys
- Common GitHub/OpenAI/AWS key patterns
- Email addresses and phone numbers (regex-based)
- Custom patterns in `redaction-patterns.txt`

When content is scrubbed or truncated, a `security.redaction` event may be recorded. Treat exported files as sensitive even after redaction — validate against your org's data classification policy.

## CLI reference

### Health and stats

```bash
df observability init              # bootstrap (install.sh runs this)
df observability doctor            # DB, schema, config, writability, gitignore
df observability stats             # row counts, DB size, oldest record
df observability report --since 30d
```

### Recording (agents and integrations)

```bash
df observability run start <TICKET-ID> --write-state
df observability session start --run-id <UUID> --skill df-implement --role coordinator
df observability message record --session-id <UUID> --role user --content "..."
df observability event record --category workflow.decision --action user.approval --run-id <UUID> --summary "Approved ship"
df observability snapshot record --source github --snapshot-type pr_poll --reference 42 --payload @status.json --run-id <UUID>
df observability batch --file batch.jsonl
df observability session end --session-id <UUID>
df observability run end --run-id <UUID> --status complete
```

Environment variables (optional, runtime-agnostic):

```bash
export DF_RUN_ID="<uuid from state.md>"
export DF_SESSION_ID="<uuid from session start>"
export DF_RUNTIME="cursor"    # cursor | claude | codex | copilot | unknown
```

### Query and debug

```bash
df observability tail --ticket OFRS2-123
df observability query --ticket OFRS2-123 --category github.snapshot --json
df observability run-show <run-id>
df observability session show <session-id>
```

## Access by audience

### Engineers (debugging)

Reconstruct a failed or blocked delivery without chat access:

```bash
df observability run-show "$(df state get OFRS2-123 run_id)"
df observability session show <session-id>
df observability query --ticket OFRS2-123 --status failure --json
```

### Compliance / audit

Export a ticket's full record for archival or SIEM ingestion:

```bash
df observability export \
  --ticket OFRS2-123 \
  --format jsonl \
  --output .agents/dark-factory/exports/OFRS2-123-audit.jsonl
```

Export jobs are logged in `export_jobs` (who, when, filter, record count).

Date-range export for periodic audit:

```bash
df observability export \
  --since 2025-01-01 \
  --until 2026-01-01 \
  --format jsonl \
  --output .agents/dark-factory/exports/2025-audit.jsonl
```

### Engineering managers (metrics)

```bash
df observability report --since 30d
df observability report --since 90d
```

Report fields include:

- `runs_by_status` — active, complete, blocked, abandoned
- `median_completion_hours` — intake to `run end`
- `failures_by_category` — CLI, preflight, GitHub, etc.
- `phase_transitions` — bottleneck phases
- `blocked_runs` — count in the window

### Alerting (batch)

No real-time webhook is built in. Use cron to export recent blocked or failed events and pipe to your alerting system:

```bash
df observability export \
  --since 1h \
  --category workflow.phase \
  --status blocked \
  --format jsonl \
  --output .agents/dark-factory/exports/hourly-blocked.jsonl
```

## Export formats

| Format | Use case |
| --- | --- |
| `jsonl` | Default; one JSON object per line (`record_type`: event, message, snapshot, run) |
| `csv` | Interaction events only; spreadsheet or lightweight SIEM |
| `otlp-json` | OpenTelemetry-inspired log records for tools that accept OTLP JSON |

```bash
df observability export --ticket OFRS2-123 --format otlp-json --output export.otlp.json
```

## Retention and prune

Prune deletes rows older than the configured retention window. Always dry-run first:

```bash
df observability prune --dry-run
df observability prune
df observability prune --before 2025-01-01T00:00:00Z
```

Suggested weekly cron (adjust paths and scheduler):

```bash
0 3 * * 0  cd /path/to/repo && .agents/bin/df observability prune
0 4 * * 0  cd /path/to/repo && .agents/bin/df observability export --since 7d --format jsonl --output .agents/dark-factory/exports/weekly.jsonl
```

Prune operations are recorded as `retention.prune` events.

## Audit reconstruction checklist

An auditor should be able to answer, for ticket `OFRS2-123`:

1. **When did work start and end?** — `delivery_runs` via `run-show`
2. **Which phases ran?** — `interaction_events` where `category = workflow.phase`
3. **What did the agent say and do?** — `agent_messages` via `session show`
4. **Which CLI commands ran?** — `interaction_events` where `category = cli.command`
5. **What did CI/preflight report?** — `external_snapshots` + `preflight.json` on disk
6. **What was the PR state over time?** — GitHub snapshots from `df pr poll` / `df ship`
7. **Who exported audit data?** — `export_jobs`

One-command export for handoff:

```bash
df observability export --ticket OFRS2-123 --format jsonl --output audit.jsonl
```

## Migration from pre-observability repos

If stories exist without `run_id` in `state.md`:

```bash
df observability init
df observability migrate-states
```

This creates delivery runs and backfills `run_id`. Historical agent chat before migration will not be present unless exported from the agent runtime separately.

## Runtime adapters (optional)

Skills mandate recording via `df observability`. Optional hooks reduce manual calls:

| Runtime | Template |
| --- | --- |
| Cursor | `.agents/skills/df-observability/templates/cursor-hooks.json` |
| Claude Code | `.agents/skills/df-observability/templates/claude-hooks.json` |
| Generic | `.agents/skills/df-observability/templates/scripts/ingest-stdin.sh` |

Hooks pipe JSONL into `df observability batch`. They supplement — not replace — the skill contract.

## Security and compliance notes

- **Storage location:** local SQLite on the developer/CI machine running Dark Factory. Plan backup/export if policy requires off-machine retention.
- **Git:** `observability.db` is gitignored. Do not force-add it unless your policy explicitly allows encrypted commits.
- **Access control:** file-system permissions on `.agents/dark-factory/` govern who can read exports. Restrict as you would application secrets.
- **Immutability:** event tables are append-only by convention; retention is the only deletion path via `prune`.
- **SOC 2 / ISO 27001:** use export + centralized log storage for long-term immutable archive; local DB is the operational source of truth for 365 days by default.
- **GDPR:** export includes all stored data for a ticket; use `prune` and shorter `agent_messages_days` for erasure requests where applicable.

## Troubleshooting

| Symptom | Check |
| --- | --- |
| No events for a ticket | `run_id` empty in `state.md`? Run `migrate-states` or `run start --write-state` |
| `doctor` fails writability | Permissions on `.agents/dark-factory/` |
| Missing agent messages | Agent did not call `message record` / `batch`; enforce `df-observability` skill |
| DB grows quickly | Lower retention; run `prune`; reduce snapshot frequency |
| Export empty | Wrong ticket/run_id filter; verify with `stats` and `tail` |

## Related documents

- [WORKFLOW.md](WORKFLOW.md) — phase flow and durable artifacts
- [SKILL_CONTRACT.md](SKILL_CONTRACT.md) — required `## Observability` section in skills
- `skills/df-observability/SKILL.md` — agent recording contract
- `skills/df-observability/REFERENCE.md` — batch JSONL schema and hook details
