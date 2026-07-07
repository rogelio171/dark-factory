from __future__ import annotations

import argparse
import json

from .state import list_states, read_state, write_state_file
from .utils import DarkFactoryError, now_utc, repo_root, run, warn_observability_failure

DISPATCH = {
    "intake": "df-workspace",
    "workspace": "df-clarify",
    "clarifying": "df-clarify",
    "specifying": "df-spec",
    "planning": "df-plan",
    "implementing": "df-implement",
    "reviewing": "df-review",
    "evidencing": "df-evidence",
    "preflight": "df-preflight",
    "shipping": "df-ship",
    "merging": "df-merge",
    "complete": "stop",
    "blocked": "stop",
}


def choose_state(ticket: str | None) -> dict:
    states = list_states()
    if not states:
        raise DarkFactoryError("no active story states found under docs/specs")
    if ticket:
        for state in states:
            if state.get("ticket") == ticket or str(state.get("path", "")).find(ticket) != -1:
                return state
        raise DarkFactoryError(f"no state found for {ticket}")
    active = [state for state in states if state.get("status") not in {"complete"}]
    candidates = active or states
    return sorted(candidates, key=lambda item: str(item.get("last_updated", "")), reverse=True)[0]


def reconcile_pr(state: dict) -> tuple[str, dict | None]:
    pr_number = str(state.get("pr_number") or "")
    pr_url = str(state.get("pr_url") or "")
    if not pr_number and not pr_url:
        return "", None
    proc = run(
        ["gh", "pr", "view", pr_number or pr_url, "--json", "state,mergeable,reviews,statusCheckRollup,mergeCommit"],
        cwd=repo_root(),
    )
    if proc.returncode != 0:
        return "pr_status=unavailable", None
    data = json.loads(proc.stdout)
    if data.get("state") == "MERGED":
        return "pr_status=merged", data
    if data.get("state") == "CLOSED":
        return "pr_status=closed", data
    return f"pr_status={str(data.get('state', 'unknown')).lower()}", data


def resume(args: argparse.Namespace) -> int:
    root = repo_root()
    selected = choose_state(args.ticket)
    ticket = str(selected.get("ticket"))
    state_file, state, body = read_state(ticket, root)
    note, pr_data = reconcile_pr(state)
    if pr_data and pr_data.get("state") == "MERGED" and state.get("status") == "merging":
        state["merge_sha"] = (pr_data.get("mergeCommit") or {}).get("oid", "")
        state["status"] = "complete"
        state["phase_detail"] = "PR merged; run df-wiki-update if not already recorded"
    state["last_updated"] = now_utc()
    write_state_file(state_file, state, body, root)

    try:
        if pr_data:
            from .observability.instrumentation import log_github_snapshot

            run_id = str(state.get("run_id") or "")
            log_github_snapshot(run_id, str(state.get("pr_number") or ""), pr_data, snapshot_type="pr_reconcile")
    except Exception as exc:
        warn_observability_failure("pr reconcile snapshot", exc)

    status = str(state.get("status", "blocked"))
    next_skill = DISPATCH.get(status, "stop")
    if status == "blocked":
        blocked_reason = str(state.get("blocked_reason") or "unspecified")
        blocked_from = str(state.get("blocked_from") or "unknown")
        reason = f"blocked_reason={blocked_reason!r} blocked_from={blocked_from}"
    else:
        reason = note or f"status={status}"
    print(f"next_skill={next_skill} ticket={ticket} status={status} reason={reason}")
    return 0 if next_skill != "stop" or status == "complete" else 1


def add_parser(subparsers) -> None:
    parser = subparsers.add_parser("resume", help="Determine the next safe Dark Factory phase")
    parser.add_argument("--ticket", default=None)
    parser.set_defaults(func=resume)
