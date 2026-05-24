from __future__ import annotations

from datetime import datetime, timedelta, timezone

from .config import load_config
from .db import connect
from .record import new_id, record_event


def _cutoff(days: int) -> str:
    cutoff = datetime.now(timezone.utc) - timedelta(days=days)
    return cutoff.strftime("%Y-%m-%dT%H:%M:%SZ")


def prune(*, before: str | None = None, dry_run: bool = False) -> dict:
    config = load_config()
    retention = config.retention
    counts = {
        "agent_messages": 0,
        "interaction_events": 0,
        "external_snapshots": 0,
        "export_jobs": 0,
        "delivery_runs": 0,
        "agent_sessions": 0,
    }
    cutoffs = {
        "agent_messages": before or _cutoff(retention.agent_messages_days or retention.default_days),
        "interaction_events": before or _cutoff(retention.interaction_events_days or retention.default_days),
        "external_snapshots": before or _cutoff(retention.external_snapshots_days or retention.default_days),
        "export_jobs": before or _cutoff(retention.default_days),
    }
    connection = connect()
    try:
        if dry_run:
            counts["agent_messages"] = connection.execute(
                "SELECT COUNT(*) FROM agent_messages WHERE recorded_at < ?",
                (cutoffs["agent_messages"],),
            ).fetchone()[0]
            counts["interaction_events"] = connection.execute(
                "SELECT COUNT(*) FROM interaction_events WHERE recorded_at < ?",
                (cutoffs["interaction_events"],),
            ).fetchone()[0]
            counts["external_snapshots"] = connection.execute(
                "SELECT COUNT(*) FROM external_snapshots WHERE captured_at < ?",
                (cutoffs["external_snapshots"],),
            ).fetchone()[0]
            counts["export_jobs"] = connection.execute(
                "SELECT COUNT(*) FROM export_jobs WHERE started_at < ?",
                (cutoffs["export_jobs"],),
            ).fetchone()[0]
            old_runs = connection.execute(
                "SELECT run_id FROM delivery_runs WHERE started_at < ?",
                (cutoffs["interaction_events"],),
            ).fetchall()
            counts["delivery_runs"] = len(old_runs)
            return {"dry_run": True, "cutoffs": cutoffs, "would_delete": counts}

        counts["agent_messages"] = connection.execute(
            "DELETE FROM agent_messages WHERE recorded_at < ?",
            (cutoffs["agent_messages"],),
        ).rowcount
        counts["interaction_events"] = connection.execute(
            "DELETE FROM interaction_events WHERE recorded_at < ?",
            (cutoffs["interaction_events"],),
        ).rowcount
        counts["external_snapshots"] = connection.execute(
            "DELETE FROM external_snapshots WHERE captured_at < ?",
            (cutoffs["external_snapshots"],),
        ).rowcount
        counts["export_jobs"] = connection.execute(
            "DELETE FROM export_jobs WHERE started_at < ?",
            (cutoffs["export_jobs"],),
        ).rowcount
        old_runs = [
            row[0]
            for row in connection.execute(
                "SELECT run_id FROM delivery_runs WHERE started_at < ?",
                (cutoffs["interaction_events"],),
            ).fetchall()
        ]
        for run_id in old_runs:
            connection.execute("DELETE FROM agent_sessions WHERE run_id = ?", (run_id,))
            connection.execute("DELETE FROM delivery_runs WHERE run_id = ?", (run_id,))
        counts["delivery_runs"] = len(old_runs)
        connection.commit()
    finally:
        connection.close()

    record_event(
        category="retention.prune",
        action="prune.complete",
        summary="Pruned observability records",
        output_json={"deleted": counts, "cutoffs": cutoffs},
        event_id=new_id(),
    )
    return {"dry_run": False, "cutoffs": cutoffs, "deleted": counts}
