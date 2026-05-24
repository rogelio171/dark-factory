from __future__ import annotations

import json
from datetime import datetime, timedelta, timezone

from .db import connect, row_to_dict


def _parse_since(value: str | None) -> str | None:
    if not value:
        return None
    if value.endswith("d") and value[:-1].isdigit():
        days = int(value[:-1])
        cutoff = datetime.now(timezone.utc) - timedelta(days=days)
        return cutoff.strftime("%Y-%m-%dT%H:%M:%SZ")
    return value


def query_events(
    *,
    ticket: str | None = None,
    run_id: str | None = None,
    category: str | None = None,
    status: str | None = None,
    since: str | None = None,
    until: str | None = None,
    limit: int = 100,
) -> list[dict]:
    since = _parse_since(since)
    clauses: list[str] = []
    params: list[object] = []
    if ticket:
        clauses.append("ticket = ?")
        params.append(ticket)
    if run_id:
        clauses.append("run_id = ?")
        params.append(run_id)
    if category:
        clauses.append("category = ?")
        params.append(category)
    if status:
        clauses.append("status = ?")
        params.append(status)
    if since:
        clauses.append("recorded_at >= ?")
        params.append(since)
    if until:
        clauses.append("recorded_at <= ?")
        params.append(until)
    where = f"WHERE {' AND '.join(clauses)}" if clauses else ""
    connection = connect()
    try:
        rows = connection.execute(
            f"""
            SELECT * FROM interaction_events
            {where}
            ORDER BY recorded_at DESC
            LIMIT ?
            """,
            (*params, limit),
        ).fetchall()
        return [row_to_dict(row) for row in rows if row_to_dict(row)]
    finally:
        connection.close()


def tail_events(
    *,
    ticket: str | None = None,
    run_id: str | None = None,
    limit: int = 20,
) -> list[dict]:
    return query_events(ticket=ticket, run_id=run_id, limit=limit)


def get_run(run_id: str) -> dict | None:
    connection = connect()
    try:
        run = row_to_dict(connection.execute(
            "SELECT * FROM delivery_runs WHERE run_id = ?", (run_id,)
        ).fetchone())
        if not run:
            return None
        events = connection.execute(
            "SELECT * FROM interaction_events WHERE run_id = ? ORDER BY recorded_at ASC",
            (run_id,),
        ).fetchall()
        sessions = connection.execute(
            "SELECT * FROM agent_sessions WHERE run_id = ? ORDER BY started_at ASC",
            (run_id,),
        ).fetchall()
        snapshots = connection.execute(
            "SELECT snapshot_id, source, snapshot_type, captured_at, reference FROM external_snapshots WHERE run_id = ? ORDER BY captured_at ASC",
            (run_id,),
        ).fetchall()
        run["events"] = [row_to_dict(row) for row in events]
        run["sessions"] = [row_to_dict(row) for row in sessions]
        run["snapshots"] = [row_to_dict(row) for row in snapshots]
        return run
    finally:
        connection.close()


def get_session(session_id: str) -> dict | None:
    connection = connect()
    try:
        session = row_to_dict(connection.execute(
            "SELECT * FROM agent_sessions WHERE session_id = ?", (session_id,)
        ).fetchone())
        if not session:
            return None
        messages = connection.execute(
            "SELECT * FROM agent_messages WHERE session_id = ? ORDER BY sequence ASC",
            (session_id,),
        ).fetchall()
        session["messages"] = [row_to_dict(row) for row in messages]
        return session
    finally:
        connection.close()


def stats() -> dict:
    connection = connect()
    try:
        tables = {
            "delivery_runs": "SELECT COUNT(*) AS count, MIN(started_at) AS oldest, MAX(started_at) AS newest FROM delivery_runs",
            "agent_sessions": "SELECT COUNT(*) AS count FROM agent_sessions",
            "agent_messages": "SELECT COUNT(*) AS count FROM agent_messages",
            "interaction_events": "SELECT COUNT(*) AS count FROM interaction_events",
            "external_snapshots": "SELECT COUNT(*) AS count FROM external_snapshots",
            "export_jobs": "SELECT COUNT(*) AS count FROM export_jobs",
        }
        result: dict[str, object] = {}
        for name, query in tables.items():
            row = connection.execute(query).fetchone()
            result[name] = row_to_dict(row)
        from .db import db_path

        path = db_path()
        result["db_path"] = str(path)
        result["db_size_bytes"] = path.stat().st_size if path.exists() else 0
        return result
    finally:
        connection.close()


def report(*, since: str | None = "30d") -> dict:
    since_ts = _parse_since(since)
    connection = connect()
    try:
        run_clause = "WHERE started_at >= ?" if since_ts else ""
        run_params: tuple[object, ...] = (since_ts,) if since_ts else ()
        runs = connection.execute(
            f"""
            SELECT status, COUNT(*) AS count
            FROM delivery_runs
            {run_clause}
            GROUP BY status
            """,
            run_params,
        ).fetchall()
        event_clause = "WHERE recorded_at >= ?" if since_ts else ""
        failures = connection.execute(
            f"""
            SELECT category, COUNT(*) AS count
            FROM interaction_events
            {event_clause} {"AND" if since_ts else "WHERE"} status = 'failure'
            GROUP BY category
            ORDER BY count DESC
            """,
            run_params,
        ).fetchall()
        blocked = connection.execute(
            f"""
            SELECT COUNT(*) AS count
            FROM delivery_runs
            {run_clause} {"AND" if since_ts else "WHERE"} status = 'blocked'
            """,
            run_params,
        ).fetchone()
        phase_transitions = connection.execute(
            f"""
            SELECT phase, COUNT(*) AS count
            FROM interaction_events
            {event_clause} {"AND" if since_ts else "WHERE"} action = 'phase.transition'
            GROUP BY phase
            ORDER BY count DESC
            """,
            run_params,
        ).fetchall()
        completed = connection.execute(
            f"""
            SELECT started_at, ended_at
            FROM delivery_runs
            {run_clause} {"AND" if since_ts else "WHERE"} status = 'complete' AND ended_at IS NOT NULL
            """,
            run_params,
        ).fetchall()
        durations: list[float] = []
        for row in completed:
            try:
                start = datetime.fromisoformat(str(row["started_at"]).replace("Z", "+00:00"))
                end = datetime.fromisoformat(str(row["ended_at"]).replace("Z", "+00:00"))
                durations.append((end - start).total_seconds())
            except ValueError:
                continue
        median_hours = 0.0
        if durations:
            durations.sort()
            median = durations[len(durations) // 2]
            median_hours = round(median / 3600, 2)
        return {
            "since": since_ts or "all",
            "runs_by_status": {str(row["status"]): int(row["count"]) for row in runs},
            "failures_by_category": {str(row["category"]): int(row["count"]) for row in failures},
            "blocked_runs": int(blocked["count"]) if blocked else 0,
            "phase_transitions": {str(row["phase"]): int(row["count"]) for row in phase_transitions},
            "median_completion_hours": median_hours,
            "completed_runs": len(durations),
        }
    finally:
        connection.close()


def format_tail_line(event: dict) -> str:
    return (
        f"{event.get('recorded_at')} "
        f"[{event.get('severity')}] "
        f"{event.get('category')}.{event.get('action')} "
        f"ticket={event.get('ticket') or '-'} "
        f"status={event.get('status')} "
        f"{event.get('summary')}"
    )
