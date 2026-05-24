PRAGMA journal_mode = WAL;
PRAGMA foreign_keys = ON;

CREATE TABLE IF NOT EXISTS schema_meta (
    key TEXT PRIMARY KEY,
    value TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS delivery_runs (
    run_id TEXT PRIMARY KEY,
    ticket TEXT NOT NULL,
    story_slug TEXT NOT NULL DEFAULT '',
    repo_root TEXT NOT NULL,
    runtime TEXT NOT NULL DEFAULT 'unknown',
    runtime_session_id TEXT NOT NULL DEFAULT '',
    started_at TEXT NOT NULL,
    ended_at TEXT,
    status TEXT NOT NULL DEFAULT 'active',
    current_phase TEXT NOT NULL DEFAULT '',
    correlation_id TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS agent_sessions (
    session_id TEXT PRIMARY KEY,
    run_id TEXT NOT NULL REFERENCES delivery_runs(run_id),
    parent_session_id TEXT NOT NULL DEFAULT '',
    agent_role TEXT NOT NULL DEFAULT '',
    skill_name TEXT NOT NULL DEFAULT '',
    runtime TEXT NOT NULL DEFAULT 'unknown',
    model TEXT NOT NULL DEFAULT '',
    started_at TEXT NOT NULL,
    ended_at TEXT,
    metadata_json TEXT NOT NULL DEFAULT '{}'
);

CREATE TABLE IF NOT EXISTS agent_messages (
    message_id TEXT PRIMARY KEY,
    session_id TEXT NOT NULL REFERENCES agent_sessions(session_id),
    run_id TEXT NOT NULL REFERENCES delivery_runs(run_id),
    sequence INTEGER NOT NULL,
    recorded_at TEXT NOT NULL,
    role TEXT NOT NULL,
    content TEXT NOT NULL DEFAULT '',
    content_hash TEXT NOT NULL DEFAULT '',
    tool_name TEXT NOT NULL DEFAULT '',
    tool_call_id TEXT NOT NULL DEFAULT '',
    tool_input_json TEXT NOT NULL DEFAULT '',
    tool_output_json TEXT NOT NULL DEFAULT '',
    token_count INTEGER,
    metadata_json TEXT NOT NULL DEFAULT '{}'
);

CREATE TABLE IF NOT EXISTS interaction_events (
    event_id TEXT PRIMARY KEY,
    run_id TEXT NOT NULL DEFAULT '',
    session_id TEXT NOT NULL DEFAULT '',
    trace_id TEXT NOT NULL DEFAULT '',
    span_id TEXT NOT NULL DEFAULT '',
    parent_span_id TEXT NOT NULL DEFAULT '',
    recorded_at TEXT NOT NULL,
    severity TEXT NOT NULL DEFAULT 'INFO',
    category TEXT NOT NULL,
    action TEXT NOT NULL,
    actor_type TEXT NOT NULL DEFAULT 'system',
    actor_id TEXT NOT NULL DEFAULT '',
    status TEXT NOT NULL DEFAULT 'success',
    duration_ms INTEGER,
    ticket TEXT NOT NULL DEFAULT '',
    phase TEXT NOT NULL DEFAULT '',
    summary TEXT NOT NULL DEFAULT '',
    input_json TEXT NOT NULL DEFAULT '{}',
    output_json TEXT NOT NULL DEFAULT '{}',
    artifact_refs_json TEXT NOT NULL DEFAULT '[]',
    error_json TEXT NOT NULL DEFAULT ''
);

CREATE TABLE IF NOT EXISTS external_snapshots (
    snapshot_id TEXT PRIMARY KEY,
    run_id TEXT NOT NULL DEFAULT '',
    source TEXT NOT NULL,
    snapshot_type TEXT NOT NULL,
    captured_at TEXT NOT NULL,
    reference TEXT NOT NULL DEFAULT '',
    payload_json TEXT NOT NULL DEFAULT '{}',
    payload_hash TEXT NOT NULL DEFAULT ''
);

CREATE TABLE IF NOT EXISTS export_jobs (
    export_id TEXT PRIMARY KEY,
    started_at TEXT NOT NULL,
    completed_at TEXT,
    format TEXT NOT NULL,
    filter_json TEXT NOT NULL DEFAULT '{}',
    output_path TEXT NOT NULL DEFAULT '',
    record_count INTEGER NOT NULL DEFAULT 0,
    requested_by TEXT NOT NULL DEFAULT '',
    status TEXT NOT NULL DEFAULT 'running'
);

CREATE INDEX IF NOT EXISTS idx_delivery_runs_ticket ON delivery_runs(ticket);
CREATE INDEX IF NOT EXISTS idx_agent_sessions_run ON agent_sessions(run_id);
CREATE INDEX IF NOT EXISTS idx_agent_messages_session ON agent_messages(session_id, sequence);
CREATE INDEX IF NOT EXISTS idx_agent_messages_run ON agent_messages(run_id, recorded_at);
CREATE INDEX IF NOT EXISTS idx_interaction_events_run ON interaction_events(run_id, recorded_at);
CREATE INDEX IF NOT EXISTS idx_interaction_events_ticket ON interaction_events(ticket, recorded_at);
CREATE INDEX IF NOT EXISTS idx_interaction_events_category ON interaction_events(category, action);
CREATE INDEX IF NOT EXISTS idx_interaction_events_trace ON interaction_events(trace_id);
CREATE INDEX IF NOT EXISTS idx_external_snapshots_run ON external_snapshots(run_id, captured_at);
