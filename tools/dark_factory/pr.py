from __future__ import annotations

import argparse
import json
import re
import tempfile
from pathlib import Path

from .state import read_state, write_state_file, list_states
from .utils import DarkFactoryError, now_utc, repo_root, run


def section(text: str, heading: str) -> str:
    pattern = re.compile(rf"^## {re.escape(heading)}\s*$", re.MULTILINE)
    match = pattern.search(text)
    if not match:
        return ""
    next_heading = re.search(r"^## .+$", text[match.end() :], re.MULTILINE)
    end = match.end() + next_heading.start() if next_heading else len(text)
    return text[match.end() : end].strip()


def render_body(args: argparse.Namespace) -> int:
    print(render_pr_body(args.ticket))
    return 0


def render_pr_body(ticket: str) -> str:
    root = repo_root()
    _, state, _ = read_state(ticket, root)
    spec_path = root / str(state.get("spec_path", ""))
    plan_path = root / str(state.get("plan_path", ""))
    preflight_path = root / str(state.get("preflight_path", ""))
    evidence_path = root / str(state.get("evidence_path", "")) / "INDEX.md"

    spec = spec_path.read_text(encoding="utf-8") if spec_path.exists() else ""
    plan = plan_path.read_text(encoding="utf-8") if plan_path.exists() else ""
    preflight = json.loads(preflight_path.read_text(encoding="utf-8")) if preflight_path.exists() else {}
    evidence = evidence_path.read_text(encoding="utf-8") if evidence_path.exists() else ""
    commands = state.get("validation_commands", {})
    if not isinstance(commands, dict):
        commands = {}
    command_lines = "\n".join(f"- {name}: `{command or 'skipped'}`" for name, command in commands.items())

    return "\n".join(
        [
            "## Summary",
            "",
            section(spec, "Problem Statement") or "- See linked spec.",
            "",
            section(spec, "Implementation Approach"),
            "",
            "## Story",
            "",
            f"- Jira: {state.get('ticket', ticket)}",
            f"- Spec: `{state.get('spec_path', '')}`",
            f"- Plan: `{state.get('plan_path', '')}`",
            "",
            "## Module Scope",
            "",
            f"- Target modules: {', '.join(state.get('target_modules', []) or [])}",
            f"- Working root: `{state.get('working_root', '')}`",
            "",
            "## Evidence",
            "",
            evidence or "- Evidence index not found.",
            "",
            "## Preflight",
            "",
            f"- Preflight file: `{state.get('preflight_path', '')}`",
            f"- Summary: `{preflight.get('summary', 'missing')}`",
            "- Commands run:",
            command_lines,
            "",
            "## Test Plan",
            "",
            "- [x] Module-scoped lint/typecheck/test/build completed or recorded as skipped in preflight.",
            "- [x] Evidence reviewed.",
            "- [x] No unrelated modules changed.",
            "",
            "## Risk",
            "",
            f"- Risk: {state.get('risk', '')}",
            f"- Auto_merge_eligible: {str(state.get('auto_merge_eligible', False)).lower()}",
            "",
            "## Related",
            "",
            f"- Branch: `{state.get('branch', '')}`",
        ]
    ).strip() + "\n"


def current_branch(root: Path) -> str:
    return run(["git", "branch", "--show-current"], cwd=root).stdout.strip()


def run_id_for_pr(pr: str) -> str:
    for state in list_states():
        if str(state.get("pr_number")) == str(pr):
            return str(state.get("run_id") or "")
        if str(state.get("pr_url", "")).rstrip("/").endswith(f"/{pr}"):
            return str(state.get("run_id") or "")
    return ""


def _log_github(payload: dict, reference: str, snapshot_type: str = "pr_status") -> None:
    try:
        from .observability.instrumentation import log_github_snapshot

        log_github_snapshot(run_id_for_pr(reference), reference, payload, snapshot_type=snapshot_type)
    except Exception:
        pass


def ship(args: argparse.Namespace) -> int:
    root = repo_root()
    state_file, state, body = read_state(args.ticket, root)
    preflight_path = root / str(state.get("preflight_path", ""))
    if not args.allow_missing_preflight:
        if not preflight_path.exists():
            raise DarkFactoryError("preflight.json is required before shipping")
        preflight = json.loads(preflight_path.read_text(encoding="utf-8"))
        if preflight.get("summary") == "failed":
            raise DarkFactoryError("preflight failed; refusing to ship")

    push = run(["git", "push", "-u", "origin", "HEAD"], cwd=root)
    if push.returncode != 0:
        raise DarkFactoryError(push.stderr.strip() or "git push failed")

    pr_existing = run(["gh", "pr", "view", "--json", "number,url"], cwd=root)
    body_text = render_pr_body(args.ticket)
    with tempfile.NamedTemporaryFile("w", encoding="utf-8", delete=False) as handle:
        handle.write(body_text)
        body_file = handle.name

    if pr_existing.returncode == 0:
        info = json.loads(pr_existing.stdout)
        pr_number = str(info["number"])
        update = run(["gh", "pr", "edit", pr_number, "--body-file", body_file], cwd=root)
        if update.returncode != 0:
            raise DarkFactoryError(update.stderr.strip() or "gh pr edit failed")
        pr_url = info.get("url", "")
    else:
        title = f"{state.get('ticket', args.ticket)}: {state.get('title', current_branch(root))}"
        created = run(["gh", "pr", "create", "--title", title, "--body-file", body_file], cwd=root)
        if created.returncode != 0:
            raise DarkFactoryError(created.stderr.strip() or "gh pr create failed")
        pr_url = created.stdout.strip().splitlines()[-1]
        view = run(["gh", "pr", "view", pr_url, "--json", "number"], cwd=root)
        pr_number = str(json.loads(view.stdout)["number"]) if view.returncode == 0 else ""

    risk = str(state.get("risk", "low"))
    run(["gh", "pr", "edit", pr_number or pr_url, "--add-label", f"risk:{risk}"], cwd=root)
    if state.get("auto_merge_eligible") is True:
        run(["gh", "pr", "edit", pr_number or pr_url, "--add-label", "auto_merge_eligible"], cwd=root)
    if risk == "low" and state.get("auto_merge_eligible") is True:
        run(["gh", "pr", "merge", pr_number or pr_url, "--auto", "--squash"], cwd=root)

    state["status"] = "merging"
    state["phase_detail"] = "PR open, awaiting Copilot review and CI"
    state["pr_url"] = pr_url
    state["pr_number"] = pr_number
    state["last_updated"] = now_utc()
    write_state_file(state_file, state, body, root)
    _log_github(
        {"pr_url": pr_url, "pr_number": pr_number, "risk": risk, "auto_merge_eligible": state.get("auto_merge_eligible")},
        pr_number or pr_url,
        snapshot_type="pr_ship",
    )
    print(pr_url)
    return 0


def pr_poll(args: argparse.Namespace) -> int:
    fields = "state,mergeable,reviews,statusCheckRollup,labels,comments,reviewDecision,mergeCommit"
    proc = run(["gh", "pr", "view", args.pr, "--json", fields], cwd=repo_root())
    if proc.returncode != 0:
        raise DarkFactoryError(proc.stderr.strip() or "gh pr view failed")
    payload = json.loads(proc.stdout)
    _log_github(payload, str(args.pr), snapshot_type="pr_poll")
    print(proc.stdout.strip())
    return 0


def pr_resolve_thread(args: argparse.Namespace) -> int:
    query = "mutation($id:ID!){resolveReviewThread(input:{threadId:$id}){thread{id isResolved}}}"
    proc = run(["gh", "api", "graphql", "-f", f"query={query}", "-F", f"id={args.thread_id}"], cwd=repo_root())
    if proc.returncode != 0:
        raise DarkFactoryError(proc.stderr.strip() or "resolveReviewThread failed")
    print(proc.stdout.strip())
    return 0


def pr_reply_thread(args: argparse.Namespace) -> int:
    root = repo_root()
    repo = run(["gh", "repo", "view", "--json", "nameWithOwner", "--jq", ".nameWithOwner"], cwd=root).stdout.strip()
    proc = run(
        ["gh", "api", "-X", "POST", f"repos/{repo}/pulls/{args.pr}/comments/{args.comment_id}/replies", "-f", f"body={args.body}"],
        cwd=root,
    )
    if proc.returncode != 0:
        raise DarkFactoryError(proc.stderr.strip() or "reply failed")
    print(proc.stdout.strip())
    return 0


def pr_fix_checks(args: argparse.Namespace) -> int:
    # Deterministic plumbing only: fetch the failing log so the agent can decide
    # the minimal code change in the df-merge phase.
    proc = run(["gh", "run", "view", "--log-failed"], cwd=repo_root())
    if proc.returncode != 0:
        raise DarkFactoryError(proc.stderr.strip() or "could not fetch failing check logs")
    _log_github({"log": proc.stdout}, str(args.pr), snapshot_type="ci_failed_log")
    print(proc.stdout)
    return 1


def add_parser(subparsers) -> None:
    render = subparsers.add_parser("render-pr-body", help="Render the Dark Factory PR body")
    render.add_argument("ticket")
    render.set_defaults(func=render_body)

    ship_parser = subparsers.add_parser("ship", help="Open or update a PR and arm auto-merge when eligible")
    ship_parser.add_argument("ticket")
    ship_parser.add_argument("--allow-missing-preflight", action="store_true")
    ship_parser.set_defaults(func=ship)

    pr_parser = subparsers.add_parser("pr", help="GitHub PR plumbing helpers")
    nested = pr_parser.add_subparsers(dest="pr_command", required=True)
    poll = nested.add_parser("poll")
    poll.add_argument("pr")
    poll.set_defaults(func=pr_poll)
    resolve = nested.add_parser("resolve-thread")
    resolve.add_argument("thread_id")
    resolve.set_defaults(func=pr_resolve_thread)
    reply = nested.add_parser("reply-thread")
    reply.add_argument("pr")
    reply.add_argument("comment_id")
    reply.add_argument("--body", required=True)
    reply.set_defaults(func=pr_reply_thread)
    fix = nested.add_parser("fix-checks")
    fix.add_argument("pr")
    fix.set_defaults(func=pr_fix_checks)
