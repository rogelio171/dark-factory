from __future__ import annotations

import csv
import json
from pathlib import Path

from ..utils import now_utc
from .config import load_config
from .db import connect, observability_dir
from .query import _parse_since
from .record import new_id


def export_data(
    *,
    ticket: str | None = None,
    run_id: str | None = None,
    since: str | None = None,
    until: str | None = None,
    category: str | None = None,
    status: str | None = None,
    include_messages: bool | None = None,
    include_snapshots: bool | None = None,
    fmt: str = "jsonl",
    output: Path | None = None,
    requested_by: str = "cli",
) -> dict:
    config = load_config()
    include_messages = config.export.include_agent_messages if include_messages is None else include_messages
    include_snapshots = config.export.include_snapshots if include_snapshots is None else include_snapshots
    since = _parse_since(since)
    export_id = new_id()
    started_at = now_utc()
    if output is None:
        stamp = started_at.replace(":", "").replace("-", "")
        output = observability_dir() / "exports" / f"export-{stamp}.{ 'jsonl' if fmt == 'jsonl' else fmt}"
    output.parent.mkdir(parents=True, exist_ok=True)

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
    record_count = 0
    try:
        connection.execute(
            """
            INSERT INTO export_jobs(
                export_id, started_at, format, filter_json, output_path, requested_by, status
            ) VALUES (?, ?, ?, ?, ?, ?, 'running')
            """,
            (
                export_id,
                started_at,
                fmt,
                json.dumps(
                    {
                        "ticket": ticket,
                        "run_id": run_id,
                        "since": since,
                        "until": until,
                        "category": category,
                        "status": status,
                        "include_messages": include_messages,
                        "include_snapshots": include_snapshots,
                    }
                ),
                str(output),
                requested_by,
            ),
        )
        connection.commit()

        if fmt == "csv":
            record_count = _export_csv(connection, output, where, params, include_messages, include_snapshots, ticket, run_id)
        elif fmt == "otlp-json":
            record_count = _export_otlp_json(connection, output, where, params, include_messages, include_snapshots, ticket, run_id)
        else:
            record_count = _export_jsonl(connection, output, where, params, include_messages, include_snapshots, ticket, run_id)

        completed_at = now_utc()
        connection.execute(
            """
            UPDATE export_jobs
            SET completed_at = ?, record_count = ?, status = 'complete', output_path = ?
            WHERE export_id = ?
            """,
            (completed_at, record_count, str(output), export_id),
        )
        connection.commit()
    except Exception:
        connection.execute(
            "UPDATE export_jobs SET status = 'failed', completed_at = ? WHERE export_id = ?",
            (now_utc(), export_id),
        )
        connection.commit()
        raise
    finally:
        connection.close()

    from .record import record_event

    record_event(
        category="export.batch",
        action="export.complete",
        summary=f"Exported {record_count} records to {output}",
        output_json={"export_id": export_id, "format": fmt, "record_count": record_count},
        artifact_refs=[str(output)],
    )
    return {
        "export_id": export_id,
        "output_path": str(output),
        "record_count": record_count,
        "format": fmt,
    }


def _export_jsonl(
    connection,
    output: Path,
    where: str,
    params: list[object],
    include_messages: bool,
    include_snapshots: bool,
    ticket: str | None,
    run_id: str | None,
) -> int:
    count = 0
    with output.open("w", encoding="utf-8") as handle:
        for row in connection.execute(
            f"SELECT * FROM interaction_events {where} ORDER BY recorded_at ASC",
            params,
        ):
            handle.write(json.dumps({"record_type": "event", **dict(row)}, ensure_ascii=False) + "\n")
            count += 1
        if include_messages:
            msg_clauses = []
            msg_params: list[object] = []
            if run_id:
                msg_clauses.append("run_id = ?")
                msg_params.append(run_id)
            elif ticket:
                msg_clauses.append(
                    "run_id IN (SELECT run_id FROM delivery_runs WHERE ticket = ?)"
                )
                msg_params.append(ticket)
            msg_where = f"WHERE {' AND '.join(msg_clauses)}" if msg_clauses else ""
            for row in connection.execute(
                f"SELECT * FROM agent_messages {msg_where} ORDER BY recorded_at ASC",
                msg_params,
            ):
                handle.write(json.dumps({"record_type": "message", **dict(row)}, ensure_ascii=False) + "\n")
                count += 1
        if include_snapshots:
            snap_clauses = []
            snap_params: list[object] = []
            if run_id:
                snap_clauses.append("run_id = ?")
                snap_params.append(run_id)
            elif ticket:
                snap_clauses.append(
                    "run_id IN (SELECT run_id FROM delivery_runs WHERE ticket = ?)"
                )
                snap_params.append(ticket)
            snap_where = f"WHERE {' AND '.join(snap_clauses)}" if snap_clauses else ""
            for row in connection.execute(
                f"SELECT * FROM external_snapshots {snap_where} ORDER BY captured_at ASC",
                snap_params,
            ):
                handle.write(json.dumps({"record_type": "snapshot", **dict(row)}, ensure_ascii=False) + "\n")
                count += 1
        for row in connection.execute("SELECT * FROM delivery_runs ORDER BY started_at ASC"):
            if ticket and row["ticket"] != ticket:
                continue
            if run_id and row["run_id"] != run_id:
                continue
            handle.write(json.dumps({"record_type": "run", **dict(row)}, ensure_ascii=False) + "\n")
            count += 1
    return count


def _export_csv(connection, output: Path, where: str, params: list[object], *_rest) -> int:
    rows = connection.execute(
        f"SELECT * FROM interaction_events {where} ORDER BY recorded_at ASC",
        params,
    ).fetchall()
    if not rows:
        output.write_text("", encoding="utf-8")
        return 0
    fieldnames = rows[0].keys()
    with output.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        for row in rows:
            writer.writerow(dict(row))
    return len(rows)


def _export_otlp_json(connection, output: Path, where: str, params: list[object], *_rest) -> int:
    resource_logs = []
    for row in connection.execute(
        f"SELECT * FROM interaction_events {where} ORDER BY recorded_at ASC",
        params,
    ):
        resource_logs.append(
            {
                "timeUnixNano": row["recorded_at"],
                "severityText": row["severity"],
                "body": row["summary"],
                "attributes": {
                    "category": row["category"],
                    "action": row["action"],
                    "run_id": row["run_id"],
                    "ticket": row["ticket"],
                    "status": row["status"],
                    "trace_id": row["trace_id"],
                    "span_id": row["span_id"],
                },
            }
        )
    payload = {"resourceLogs": [{"scopeLogs": [{"logRecords": resource_logs}]}]}
    output.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    return len(resource_logs)
