from __future__ import annotations

import contextlib
import os
import re
import time
from dataclasses import dataclass
from typing import Iterator

from ..utils import repo_root, warn_observability_failure
from .config import load_config
from .redaction import redact_text
from .record import record_event


@dataclass
class CliResult:
    code: int = 0


def detect_ticket_from_argv(argv: list[str]) -> str:
    ticket_pattern = re.compile(r"^[A-Z][A-Z0-9]+-\d+$")
    for arg in argv:
        if ticket_pattern.match(arg):
            return arg
    return ""


def detect_run_id_from_env() -> str:
    return os.environ.get("DF_RUN_ID", "")


@contextlib.contextmanager
def cli_span(command: str, argv: list[str]) -> Iterator[CliResult]:
    config = load_config()
    result = CliResult()
    if not config.compliance.record_cli_commands:
        yield result
        return
    ticket = detect_ticket_from_argv(argv)
    run_id = detect_run_id_from_env()
    start = time.monotonic()
    status = "success"
    error_json: dict | None = None
    try:
        yield result
        if result.code != 0:
            status = "failure"
            error_json = {"exit_code": result.code}
    except SystemExit as exc:
        result.code = int(exc.code) if isinstance(exc.code, int) else 1
        status = "failure" if result.code != 0 else "success"
        if result.code != 0:
            error_json = {"exit_code": result.code}
        raise
    except Exception as exc:
        result.code = 1
        status = "failure"
        error_json = {"message": str(exc), "type": type(exc).__name__}
        raise
    finally:
        duration_ms = int((time.monotonic() - start) * 1000)
        try:
            config = load_config()
            record_event(
                category="cli.command",
                action=command or "unknown",
                run_id=run_id,
                ticket=ticket,
                actor_type="cli",
                actor_id="df",
                status=status,
                duration_ms=duration_ms,
                summary=redact_text(f"df {command} {' '.join(argv)}".strip(), config, repo_root()),
                input_json={"argv": argv, "command": command},
                output_json={"exit_code": result.code},
                error_json=error_json,
            )
        except Exception as exc:
            warn_observability_failure("cli.command event", exc)


def maybe_log_phase_transition(ticket: str, field: str, value: object, run_id: str = "") -> None:
    if field != "status":
        return
    from .record import get_active_run_for_ticket, update_run_phase

    active = get_active_run_for_ticket(ticket)
    resolved_run_id = run_id or (str(active["run_id"]) if active else "")
    if resolved_run_id:
        update_run_phase(resolved_run_id, str(value), ticket=ticket)


def log_preflight_stages(ticket: str, run_id: str, result: dict) -> None:
    from .record import record_snapshot

    record_snapshot(
        source="preflight",
        snapshot_type="preflight_result",
        payload=result,
        run_id=run_id,
        reference=ticket,
    )
    for stage in result.get("stages", []):
        record_event(
            category="preflight.stage",
            action=str(stage.get("name", "stage")),
            run_id=run_id,
            ticket=ticket,
            status=str(stage.get("status", "unknown")),
            duration_ms=stage.get("duration_ms"),
            summary=f"Preflight stage {stage.get('name')} {stage.get('status')}",
            input_json={"command": stage.get("command"), "cwd": stage.get("cwd")},
            output_json={"exit_code": stage.get("exit_code"), "tail": stage.get("tail")},
        )


def log_github_snapshot(run_id: str, reference: str, payload: dict, snapshot_type: str = "pr_status") -> None:
    from .record import record_snapshot

    record_snapshot(
        source="github",
        snapshot_type=snapshot_type,
        payload=payload,
        run_id=run_id,
        reference=reference,
    )
