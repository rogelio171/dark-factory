from __future__ import annotations

import json
import sqlite3
import uuid
from typing import Any

from ..utils import DarkFactoryError, now_utc, repo_root
from .config import load_config
from .db import connect, detect_runtime, row_to_dict
from .redaction import content_hash, redact_text


def new_id() -> str:
    return str(uuid.uuid4())


def _json(value: Any) -> str:
    if isinstance(value, str):
        return value
    return json.dumps(value, ensure_ascii=False)


def start_run(
    ticket: str,
    *,
    story_slug: str = "",
    runtime: str | None = None,
    runtime_session_id: str = "",
    current_phase: str = "intake",
    run_id: str | None = None,
) -> dict:
    root = repo_root()
    run_id = run_id or new_id()
    runtime = runtime or detect_runtime()
    started_at = now_utc()
    connection = connect(root)
    try:
        connection.execute(
            """
            INSERT INTO delivery_runs(
                run_id, ticket, story_slug, repo_root, runtime, runtime_session_id,
                started_at, status, current_phase, correlation_id
            ) VALUES (?, ?, ?, ?, ?, ?, ?, 'active', ?, ?)
            """,
            (
                run_id,
                ticket,
                story_slug,
                str(root),
                runtime,
                runtime_session_id,
                started_at,
                current_phase,
                run_id,
            ),
        )
        connection.commit()
    finally:
        connection.close()
    record_event(
        run_id=run_id,
        category="workflow.phase",
        action="run.start",
        ticket=ticket,
        phase=current_phase,
        summary=f"Started delivery run for {ticket}",
        input_json={"ticket": ticket, "story_slug": story_slug, "runtime": runtime},
    )
    return {"run_id": run_id, "ticket": ticket, "started_at": started_at}


def end_run(run_id: str, *, status: str = "complete", current_phase: str = "") -> dict:
    ended_at = now_utc()
    connection = connect()
    try:
        connection.execute(
            """
            UPDATE delivery_runs
            SET ended_at = ?, status = ?, current_phase = COALESCE(NULLIF(?, ''), current_phase)
            WHERE run_id = ?
            """,
            (ended_at, status, current_phase, run_id),
        )
        row = connection.execute(
            "SELECT ticket, current_phase FROM delivery_runs WHERE run_id = ?", (run_id,)
        ).fetchone()
        connection.commit()
    finally:
        connection.close()
    ticket = str(row["ticket"]) if row else ""
    phase = current_phase or (str(row["current_phase"]) if row else "")
    record_event(
        run_id=run_id,
        category="workflow.phase",
        action="run.end",
        ticket=ticket,
        phase=phase,
        status=status,
        summary=f"Ended delivery run with status {status}",
        output_json={"status": status, "ended_at": ended_at},
    )
    return {"run_id": run_id, "status": status, "ended_at": ended_at}


def start_session(
    run_id: str,
    *,
    skill_name: str = "",
    agent_role: str = "",
    runtime: str | None = None,
    model: str = "",
    parent_session_id: str = "",
    metadata: dict | None = None,
    session_id: str | None = None,
) -> dict:
    session_id = session_id or new_id()
    runtime = runtime or detect_runtime()
    started_at = now_utc()
    connection = connect()
    try:
        connection.execute(
            """
            INSERT INTO agent_sessions(
                session_id, run_id, parent_session_id, agent_role, skill_name,
                runtime, model, started_at, metadata_json
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                session_id,
                run_id,
                parent_session_id,
                agent_role,
                skill_name,
                runtime,
                model,
                started_at,
                _json(metadata or {}),
            ),
        )
        connection.commit()
    finally:
        connection.close()
    record_event(
        run_id=run_id,
        session_id=session_id,
        category="agent.delegation",
        action="session.start",
        summary=f"Started session for {skill_name or agent_role}",
        input_json={"skill_name": skill_name, "agent_role": agent_role},
    )
    return {"session_id": session_id, "run_id": run_id, "started_at": started_at}


def end_session(session_id: str) -> dict:
    ended_at = now_utc()
    connection = connect()
    try:
        row = connection.execute(
            "SELECT run_id, skill_name FROM agent_sessions WHERE session_id = ?", (session_id,)
        ).fetchone()
        connection.execute(
            "UPDATE agent_sessions SET ended_at = ? WHERE session_id = ?",
            (ended_at, session_id),
        )
        connection.commit()
    finally:
        connection.close()
    run_id = str(row["run_id"]) if row else ""
    skill_name = str(row["skill_name"]) if row else ""
    record_event(
        run_id=run_id,
        session_id=session_id,
        category="agent.delegation",
        action="session.end",
        summary=f"Ended session for {skill_name}",
        output_json={"ended_at": ended_at},
    )
    return {"session_id": session_id, "ended_at": ended_at}


def next_message_sequence(connection: sqlite3.Connection, session_id: str) -> int:
    row = connection.execute(
        "SELECT COALESCE(MAX(sequence), 0) + 1 AS next_seq FROM agent_messages WHERE session_id = ?",
        (session_id,),
    ).fetchone()
    return int(row["next_seq"])


def record_message(
    session_id: str,
    *,
    role: str,
    content: str = "",
    tool_name: str = "",
    tool_call_id: str = "",
    tool_input: Any = None,
    tool_output: Any = None,
    token_count: int | None = None,
    metadata: dict | None = None,
    run_id: str | None = None,
    message_id: str | None = None,
) -> dict:
    root = repo_root()
    config = load_config(root)
    message_id = message_id or new_id()
    content = redact_text(content, config, root)
    tool_input_json = redact_text(_json(tool_input or ""), config, root) if tool_input else ""
    tool_output_json = redact_text(_json(tool_output or ""), config, root) if tool_output else ""
    recorded_at = now_utc()
    connection = connect(root)
    try:
        if not run_id:
            row = connection.execute(
                "SELECT run_id FROM agent_sessions WHERE session_id = ?", (session_id,)
            ).fetchone()
            if not row:
                raise DarkFactoryError(f"unknown session_id: {session_id}")
            run_id = str(row["run_id"])
        sequence = next_message_sequence(connection, session_id)
        connection.execute(
            """
            INSERT INTO agent_messages(
                message_id, session_id, run_id, sequence, recorded_at, role, content,
                content_hash, tool_name, tool_call_id, tool_input_json, tool_output_json,
                token_count, metadata_json
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                message_id,
                session_id,
                run_id,
                sequence,
                recorded_at,
                role,
                content,
                content_hash(content),
                tool_name,
                tool_call_id,
                tool_input_json,
                tool_output_json,
                token_count,
                _json(metadata or {}),
            ),
        )
        connection.commit()
    finally:
        connection.close()
    if tool_name:
        record_event(
            run_id=run_id,
            session_id=session_id,
            category="agent.tool",
            action="tool.call",
            summary=f"{role} invoked {tool_name}",
            input_json={"tool_name": tool_name, "tool_call_id": tool_call_id},
            status="success",
        )
    return {
        "message_id": message_id,
        "session_id": session_id,
        "run_id": run_id,
        "sequence": sequence,
        "recorded_at": recorded_at,
    }


def record_event(
    *,
    category: str,
    action: str,
    run_id: str = "",
    session_id: str = "",
    trace_id: str = "",
    span_id: str = "",
    parent_span_id: str = "",
    severity: str = "INFO",
    actor_type: str = "system",
    actor_id: str = "",
    status: str = "success",
    duration_ms: int | None = None,
    ticket: str = "",
    phase: str = "",
    summary: str = "",
    input_json: Any = None,
    output_json: Any = None,
    artifact_refs: list | None = None,
    error_json: Any = None,
    event_id: str | None = None,
) -> dict:
    root = repo_root()
    config = load_config(root)
    event_id = event_id or new_id()
    recorded_at = now_utc()
    input_text = redact_text(_json(input_json or {}), config, root)
    output_text = redact_text(_json(output_json or {}), config, root)
    error_text = redact_text(_json(error_json or ""), config, root) if error_json else ""
    connection = connect(root)
    try:
        connection.execute(
            """
            INSERT INTO interaction_events(
                event_id, run_id, session_id, trace_id, span_id, parent_span_id,
                recorded_at, severity, category, action, actor_type, actor_id, status,
                duration_ms, ticket, phase, summary, input_json, output_json,
                artifact_refs_json, error_json
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                event_id,
                run_id,
                session_id,
                trace_id or run_id,
                span_id or event_id[:16],
                parent_span_id,
                recorded_at,
                severity,
                category,
                action,
                actor_type,
                actor_id,
                status,
                duration_ms,
                ticket,
                phase,
                summary,
                input_text,
                output_text,
                _json(artifact_refs or []),
                error_text,
            ),
        )
        connection.commit()
    finally:
        connection.close()
    return {"event_id": event_id, "recorded_at": recorded_at}


def record_snapshot(
    *,
    source: str,
    snapshot_type: str,
    payload: Any,
    run_id: str = "",
    reference: str = "",
    snapshot_id: str | None = None,
) -> dict:
    root = repo_root()
    config = load_config(root)
    snapshot_id = snapshot_id or new_id()
    captured_at = now_utc()
    payload_text = redact_text(_json(payload), config, root)
    payload_hash = content_hash(payload_text)
    connection = connect(root)
    try:
        connection.execute(
            """
            INSERT INTO external_snapshots(
                snapshot_id, run_id, source, snapshot_type, captured_at,
                reference, payload_json, payload_hash
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                snapshot_id,
                run_id,
                source,
                snapshot_type,
                captured_at,
                reference,
                payload_text,
                payload_hash,
            ),
        )
        connection.commit()
    finally:
        connection.close()
    record_event(
        run_id=run_id,
        category=f"{source}.snapshot",
        action=snapshot_type,
        summary=f"Captured {source} snapshot {snapshot_type}",
        input_json={"reference": reference, "snapshot_id": snapshot_id},
        artifact_refs=[snapshot_id],
    )
    return {"snapshot_id": snapshot_id, "captured_at": captured_at}


def record_batch(items: list[dict]) -> dict:
    counts = {"messages": 0, "events": 0, "snapshots": 0, "runs": 0, "sessions": 0}
    for item in items:
        kind = item.get("type") or item.get("kind")
        if kind == "message":
            record_message(
                str(item["session_id"]),
                role=str(item.get("role", "assistant")),
                content=str(item.get("content", "")),
                tool_name=str(item.get("tool_name", "")),
                tool_call_id=str(item.get("tool_call_id", "")),
                tool_input=item.get("tool_input"),
                tool_output=item.get("tool_output"),
                token_count=item.get("token_count"),
                metadata=item.get("metadata"),
                run_id=item.get("run_id"),
                message_id=item.get("message_id"),
            )
            counts["messages"] += 1
        elif kind == "event":
            record_event(
                category=str(item.get("category", "system")),
                action=str(item.get("action", "record")),
                run_id=str(item.get("run_id", "")),
                session_id=str(item.get("session_id", "")),
                severity=str(item.get("severity", "INFO")),
                actor_type=str(item.get("actor_type", "system")),
                actor_id=str(item.get("actor_id", "")),
                status=str(item.get("status", "success")),
                duration_ms=item.get("duration_ms"),
                ticket=str(item.get("ticket", "")),
                phase=str(item.get("phase", "")),
                summary=str(item.get("summary", "")),
                input_json=item.get("input_json") or item.get("input"),
                output_json=item.get("output_json") or item.get("output"),
                artifact_refs=item.get("artifact_refs"),
                error_json=item.get("error_json"),
                event_id=item.get("event_id"),
            )
            counts["events"] += 1
        elif kind == "snapshot":
            record_snapshot(
                source=str(item.get("source", "unknown")),
                snapshot_type=str(item.get("snapshot_type", "generic")),
                payload=item.get("payload", {}),
                run_id=str(item.get("run_id", "")),
                reference=str(item.get("reference", "")),
                snapshot_id=item.get("snapshot_id"),
            )
            counts["snapshots"] += 1
        elif kind == "run_start":
            start_run(
                str(item["ticket"]),
                story_slug=str(item.get("story_slug", "")),
                runtime=item.get("runtime"),
                runtime_session_id=str(item.get("runtime_session_id", "")),
                current_phase=str(item.get("current_phase", "intake")),
                run_id=item.get("run_id"),
            )
            counts["runs"] += 1
        elif kind == "session_start":
            start_session(
                str(item["run_id"]),
                skill_name=str(item.get("skill_name", "")),
                agent_role=str(item.get("agent_role", "")),
                runtime=item.get("runtime"),
                model=str(item.get("model", "")),
                parent_session_id=str(item.get("parent_session_id", "")),
                metadata=item.get("metadata"),
                session_id=item.get("session_id"),
            )
            counts["sessions"] += 1
    return counts


def get_active_run_for_ticket(ticket: str) -> dict | None:
    connection = connect()
    try:
        row = connection.execute(
            """
            SELECT * FROM delivery_runs
            WHERE ticket = ?
            ORDER BY CASE status WHEN 'active' THEN 0 ELSE 1 END, started_at DESC
            LIMIT 1
            """,
            (ticket,),
        ).fetchone()
        return row_to_dict(row)
    finally:
        connection.close()


def update_run_phase(run_id: str, phase: str, ticket: str = "") -> None:
    connection = connect()
    try:
        connection.execute(
            "UPDATE delivery_runs SET current_phase = ? WHERE run_id = ?",
            (phase, run_id),
        )
        connection.commit()
    finally:
        connection.close()
    record_event(
        run_id=run_id,
        category="workflow.phase",
        action="phase.transition",
        ticket=ticket,
        phase=phase,
        summary=f"Transitioned to phase {phase}",
        input_json={"phase": phase},
    )
