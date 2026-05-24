from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from ..state import find_story_dir, list_states, read_state, write_state_file
from ..utils import DarkFactoryError, repo_root
from .config import config_as_json, load_config, save_default_config
from .db import SCHEMA_VERSION, config_path, db_path, ensure_gitignore, ensure_initialized, schema_version, connect
from .export import export_data
from .prune import prune
from .query import format_tail_line, get_run, get_session, query_events, report, stats, tail_events
from .record import (
    end_run,
    end_session,
    get_active_run_for_ticket,
    new_id,
    record_batch,
    record_event,
    record_message,
    record_snapshot,
    start_run,
    start_session,
)


def _print_json(data: object) -> None:
    print(json.dumps(data, indent=2))


def init_cmd(args: argparse.Namespace) -> int:
    path = ensure_initialized(force=args.force)
    print(path)
    return 0


def doctor_cmd(args: argparse.Namespace) -> int:
    root = repo_root()
    failures = 0
    checks: list[tuple[str, bool, str]] = []
    try:
        ensure_initialized()
        checks.append(("observability-db", db_path(root).exists(), str(db_path(root))))
        connection = connect(root)
        version = schema_version(connection)
        connection.close()
        checks.append(("observability-schema", version == SCHEMA_VERSION, f"schema_version={version}"))
        checks.append(("observability-config", config_path(root).exists(), str(config_path(root))))
        test_path = observability_writable(root)
        checks.append(("observability-writable", test_path, "append test event"))
        gitignore = root / ".gitignore"
        ignored = gitignore.exists() and "# Dark Factory observability" in gitignore.read_text(encoding="utf-8")
        checks.append(("gitignore", ignored, "observability paths gitignored"))
    except Exception as exc:
        checks.append(("observability-init", False, str(exc)))
    for name, passed, detail in checks:
        print(f"{'ok' if passed else 'missing'}\t{name}\t{detail}")
        failures += 0 if passed else 1
    return 1 if failures else 0


def observability_writable(root: Path) -> bool:
    try:
        record_event(
            category="system.health",
            action="doctor.ping",
            summary="observability doctor ping",
            event_id=new_id(),
        )
        return True
    except Exception:
        return False


def run_start_cmd(args: argparse.Namespace) -> int:
    story_slug = args.story_slug
    if not story_slug and args.ticket:
        try:
            story_slug = find_story_dir(args.ticket, repo_root()).name
        except DarkFactoryError:
            story_slug = args.ticket
    result = start_run(
        args.ticket,
        story_slug=story_slug,
        runtime=args.runtime,
        runtime_session_id=args.runtime_session_id or "",
        current_phase=args.phase,
        run_id=args.run_id,
    )
    if args.write_state:
        try:
            state_file, data, body = read_state(args.ticket)
            data["run_id"] = result["run_id"]
            data["observability_enabled"] = True
            write_state_file(state_file, data, body)
        except DarkFactoryError:
            pass
    _print_json(result)
    return 0


def run_end_cmd(args: argparse.Namespace) -> int:
    _print_json(end_run(args.run_id, status=args.status, current_phase=args.phase or ""))
    return 0


def session_start_cmd(args: argparse.Namespace) -> int:
    _print_json(
        start_session(
            args.run_id,
            skill_name=args.skill or "",
            agent_role=args.role or "",
            runtime=args.runtime,
            model=args.model or "",
            parent_session_id=args.parent_session_id or "",
            metadata=json.loads(args.metadata) if args.metadata else None,
            session_id=args.session_id,
        )
    )
    return 0


def session_end_cmd(args: argparse.Namespace) -> int:
    _print_json(end_session(args.session_id))
    return 0


def message_record_cmd(args: argparse.Namespace) -> int:
    if args.stdin:
        payload = json.load(sys.stdin)
        if isinstance(payload, list):
            for item in payload:
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
                )
            _print_json({"recorded": len(payload)})
            return 0
        payload = payload
    else:
        payload = {
            "session_id": args.session_id,
            "role": args.role,
            "content": args.content,
            "tool_name": args.tool_name,
            "tool_call_id": args.tool_call_id,
        }
    _print_json(
        record_message(
            str(payload["session_id"]),
            role=str(payload.get("role", args.role)),
            content=str(payload.get("content", args.content or "")),
            tool_name=str(payload.get("tool_name", args.tool_name or "")),
            tool_call_id=str(payload.get("tool_call_id", args.tool_call_id or "")),
            tool_input=payload.get("tool_input"),
            tool_output=payload.get("tool_output"),
            run_id=payload.get("run_id") or args.run_id,
            metadata=json.loads(args.metadata) if args.metadata else payload.get("metadata"),
        )
    )
    return 0


def event_record_cmd(args: argparse.Namespace) -> int:
    _print_json(
        record_event(
            category=args.category,
            action=args.action,
            run_id=args.run_id or "",
            session_id=args.session_id or "",
            severity=args.severity,
            actor_type=args.actor_type,
            actor_id=args.actor_id or "",
            status=args.status,
            duration_ms=args.duration_ms,
            ticket=args.ticket or "",
            phase=args.phase or "",
            summary=args.summary or "",
            input_json=_load_json_arg(args.input),
            output_json=_load_json_arg(args.output),
            artifact_refs=json.loads(args.artifact_refs) if args.artifact_refs else None,
            error_json=_load_json_arg(args.error),
        )
    )
    return 0


def snapshot_record_cmd(args: argparse.Namespace) -> int:
    payload = _load_payload(args.payload)
    _print_json(
        record_snapshot(
            source=args.source,
            snapshot_type=args.snapshot_type,
            payload=payload,
            run_id=args.run_id or "",
            reference=args.reference or "",
        )
    )
    return 0


def batch_cmd(args: argparse.Namespace) -> int:
    path = Path(args.file)
    if not path.exists():
        raise DarkFactoryError(f"batch file not found: {path}")
    items: list[dict] = []
    if path.suffix == ".json":
        document = json.loads(path.read_text(encoding="utf-8"))
        items = document if isinstance(document, list) else [document]
    else:
        for line in path.read_text(encoding="utf-8").splitlines():
            stripped = line.strip()
            if stripped:
                items.append(json.loads(stripped))
    _print_json(record_batch(items))
    return 0


def query_cmd(args: argparse.Namespace) -> int:
    events = query_events(
        ticket=args.ticket,
        run_id=args.run_id,
        category=args.category,
        status=args.status,
        since=args.since,
        until=args.until,
        limit=args.limit,
    )
    if args.json:
        _print_json(events)
    else:
        for event in reversed(events):
            print(format_tail_line(event))
    return 0


def tail_cmd(args: argparse.Namespace) -> int:
    events = tail_events(ticket=args.ticket, run_id=args.run_id, limit=args.limit)
    for event in reversed(events):
        print(format_tail_line(event))
    return 0


def run_show_cmd(args: argparse.Namespace) -> int:
    data = get_run(args.run_id)
    if not data:
        raise DarkFactoryError(f"run not found: {args.run_id}")
    _print_json(data)
    return 0


def session_show_cmd(args: argparse.Namespace) -> int:
    data = get_session(args.session_id)
    if not data:
        raise DarkFactoryError(f"session not found: {args.session_id}")
    _print_json(data)
    return 0


def export_cmd(args: argparse.Namespace) -> int:
    output = Path(args.output) if args.output else None
    result = export_data(
        ticket=args.ticket,
        run_id=args.run_id,
        since=args.since,
        until=args.until,
        category=args.category,
        status=args.status,
        include_messages=not args.no_messages,
        include_snapshots=not args.no_snapshots,
        fmt=args.format,
        output=output,
        requested_by=args.requested_by,
    )
    _print_json(result)
    return 0


def prune_cmd(args: argparse.Namespace) -> int:
    _print_json(prune(before=args.before, dry_run=args.dry_run))
    return 0


def stats_cmd(args: argparse.Namespace) -> int:
    _print_json(stats())
    return 0


def report_cmd(args: argparse.Namespace) -> int:
    _print_json(report(since=args.since))
    return 0


def config_show_cmd(args: argparse.Namespace) -> int:
    _print_json(json.loads(config_as_json(load_config())))
    return 0


def migrate_states_cmd(args: argparse.Namespace) -> int:
    updated = 0
    for state in list_states():
        ticket = str(state.get("ticket", ""))
        if state.get("run_id"):
            continue
        story_slug = Path(str(state.get("path", ""))).parent.name
        run = start_run(
            ticket,
            story_slug=story_slug,
            current_phase=str(state.get("status", "intake")),
        )
        state_file, data, body = read_state(ticket)
        data["run_id"] = run["run_id"]
        data["observability_enabled"] = True
        write_state_file(state_file, data, body)
        updated += 1
    _print_json({"updated": updated})
    return 0


def _load_json_arg(value: str | None) -> dict | list | str | None:
    if not value:
        return None
    if value.startswith("@"):
        return json.loads(Path(value[1:]).read_text(encoding="utf-8"))
    return json.loads(value)


def _load_payload(value: str | None) -> dict | list:
    if not value:
        return {}
    if value.startswith("@"):
        return json.loads(Path(value[1:]).read_text(encoding="utf-8"))
    return json.loads(value)


def add_parser(subparsers) -> None:
    parser = subparsers.add_parser("observability", help="Record and query Dark Factory observability data")
    nested = parser.add_subparsers(dest="observability_command", required=True)

    init = nested.add_parser("init", help="Initialize observability database and config")
    init.add_argument("--force", action="store_true")
    init.set_defaults(func=init_cmd)

    nested.add_parser("doctor", help="Check observability setup").set_defaults(func=doctor_cmd)
    nested.add_parser("stats", help="Show observability statistics").set_defaults(func=stats_cmd)

    report_parser = nested.add_parser("report", help="Summarize delivery metrics")
    report_parser.add_argument("--since", default="30d")
    report_parser.set_defaults(func=report_cmd)

    nested.add_parser("config", help="Show observability config").set_defaults(func=config_show_cmd)

    migrate = nested.add_parser("migrate-states", help="Backfill run_id into existing story states")
    migrate.set_defaults(func=migrate_states_cmd)

    run = nested.add_parser("run", help="Delivery run lifecycle")
    run_nested = run.add_subparsers(dest="run_command", required=True)
    run_start = run_nested.add_parser("start")
    run_start.add_argument("ticket")
    run_start.add_argument("--story-slug", default="")
    run_start.add_argument("--runtime", default=None)
    run_start.add_argument("--runtime-session-id", default="")
    run_start.add_argument("--phase", default="intake")
    run_start.add_argument("--run-id", default=None)
    run_start.add_argument("--write-state", action="store_true")
    run_start.set_defaults(func=run_start_cmd)
    run_end = run_nested.add_parser("end")
    run_end.add_argument("--run-id", required=True)
    run_end.add_argument("--status", default="complete")
    run_end.add_argument("--phase", default="")
    run_end.set_defaults(func=run_end_cmd)

    session = nested.add_parser("session", help="Agent session lifecycle")
    session_nested = session.add_subparsers(dest="session_command", required=True)
    sess_start = session_nested.add_parser("start")
    sess_start.add_argument("--run-id", required=True)
    sess_start.add_argument("--skill", default="")
    sess_start.add_argument("--role", default="")
    sess_start.add_argument("--runtime", default=None)
    sess_start.add_argument("--model", default="")
    sess_start.add_argument("--parent-session-id", default="")
    sess_start.add_argument("--metadata", default="")
    sess_start.add_argument("--session-id", default=None)
    sess_start.set_defaults(func=session_start_cmd)
    sess_end = session_nested.add_parser("end")
    sess_end.add_argument("--session-id", required=True)
    sess_end.set_defaults(func=session_end_cmd)
    sess_show = session_nested.add_parser("show")
    sess_show.add_argument("session_id")
    sess_show.set_defaults(func=session_show_cmd)

    message = nested.add_parser("message", help="Record agent messages")
    message_nested = message.add_subparsers(dest="message_command", required=True)
    msg_record = message_nested.add_parser("record")
    msg_record.add_argument("--session-id", default="")
    msg_record.add_argument("--run-id", default="")
    msg_record.add_argument("--role", default="assistant")
    msg_record.add_argument("--content", default="")
    msg_record.add_argument("--tool-name", default="")
    msg_record.add_argument("--tool-call-id", default="")
    msg_record.add_argument("--metadata", default="")
    msg_record.add_argument("--stdin", action="store_true")
    msg_record.set_defaults(func=message_record_cmd)

    event = nested.add_parser("event", help="Record structured interaction events")
    event_nested = event.add_subparsers(dest="event_command", required=True)
    evt_record = event_nested.add_parser("record")
    evt_record.add_argument("--category", required=True)
    evt_record.add_argument("--action", required=True)
    evt_record.add_argument("--run-id", default="")
    evt_record.add_argument("--session-id", default="")
    evt_record.add_argument("--severity", default="INFO")
    evt_record.add_argument("--actor-type", default="agent")
    evt_record.add_argument("--actor-id", default="")
    evt_record.add_argument("--status", default="success")
    evt_record.add_argument("--duration-ms", type=int, default=None)
    evt_record.add_argument("--ticket", default="")
    evt_record.add_argument("--phase", default="")
    evt_record.add_argument("--summary", default="")
    evt_record.add_argument("--input", default="")
    evt_record.add_argument("--output", default="")
    evt_record.add_argument("--artifact-refs", default="")
    evt_record.add_argument("--error", default="")
    evt_record.set_defaults(func=event_record_cmd)

    snapshot = nested.add_parser("snapshot", help="Record external system snapshots")
    snapshot_nested = snapshot.add_subparsers(dest="snapshot_command", required=True)
    snap_record = snapshot_nested.add_parser("record")
    snap_record.add_argument("--source", required=True)
    snap_record.add_argument("--snapshot-type", required=True)
    snap_record.add_argument("--payload", required=True)
    snap_record.add_argument("--run-id", default="")
    snap_record.add_argument("--reference", default="")
    snap_record.set_defaults(func=snapshot_record_cmd)

    batch = nested.add_parser("batch", help="Ingest a JSON or JSONL batch file")
    batch.add_argument("--file", required=True)
    batch.set_defaults(func=batch_cmd)

    query_parser = nested.add_parser("query", help="Query interaction events")
    query_parser.add_argument("--ticket", default=None)
    query_parser.add_argument("--run-id", default=None)
    query_parser.add_argument("--category", default=None)
    query_parser.add_argument("--status", default=None)
    query_parser.add_argument("--since", default=None)
    query_parser.add_argument("--until", default=None)
    query_parser.add_argument("--limit", type=int, default=100)
    query_parser.add_argument("--json", action="store_true")
    query_parser.set_defaults(func=query_cmd)

    tail = nested.add_parser("tail", help="Show recent interaction events")
    tail.add_argument("--ticket", default=None)
    tail.add_argument("--run-id", default=None)
    tail.add_argument("--limit", type=int, default=20)
    tail.set_defaults(func=tail_cmd)

    run_show = nested.add_parser("run-show", help="Show a delivery run timeline")
    run_show.add_argument("run_id")
    run_show.set_defaults(func=run_show_cmd)

    export_parser = nested.add_parser("export", help="Batch export observability data")
    export_parser.add_argument("--ticket", default=None)
    export_parser.add_argument("--run-id", default=None)
    export_parser.add_argument("--since", default=None)
    export_parser.add_argument("--until", default=None)
    export_parser.add_argument("--category", default=None)
    export_parser.add_argument("--status", default=None)
    export_parser.add_argument("--format", default="jsonl", choices=["jsonl", "csv", "otlp-json"])
    export_parser.add_argument("--output", default="")
    export_parser.add_argument("--no-messages", action="store_true")
    export_parser.add_argument("--no-snapshots", action="store_true")
    export_parser.add_argument("--requested-by", default="cli")
    export_parser.set_defaults(func=export_cmd)

    prune_parser = nested.add_parser("prune", help="Delete records older than retention policy")
    prune_parser.add_argument("--before", default=None)
    prune_parser.add_argument("--dry-run", action="store_true")
    prune_parser.set_defaults(func=prune_cmd)
