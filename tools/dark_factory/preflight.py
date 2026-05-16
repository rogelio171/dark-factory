from __future__ import annotations

import argparse
import json
import re
import time
from pathlib import Path

from .state import read_state, write_state_file
from .utils import (
    command_exists,
    merge_base,
    now_utc,
    repo_root,
    run,
    tail_lines,
    write_atomic,
)

COMMIT_RE = re.compile(
    r"^(feat|fix|docs|style|refactor|perf|test|build|ci|chore|revert)(\([a-z0-9-]+\))?(!)?: .{1,72}$"
)


def skipped_stage(name: str, cwd: Path, reason: str) -> dict:
    return {
        "name": name,
        "command": "",
        "cwd": str(cwd),
        "status": "skipped",
        "duration_ms": 0,
        "exit_code": None,
        "tail": "",
        "skipped_reason": reason,
    }


def run_stage(name: str, command: str, cwd: Path, allow_warning: bool = False) -> dict:
    if not command:
        return skipped_stage(name, cwd, f"no {name} tooling detected")
    start = time.monotonic()
    proc = run(command, cwd=cwd, shell=True)
    duration = int((time.monotonic() - start) * 1000)
    output = "\n".join(part for part in (proc.stdout, proc.stderr) if part)
    status = "passed" if proc.returncode == 0 else ("warning" if allow_warning else "failed")
    return {
        "name": name,
        "command": command,
        "cwd": str(cwd),
        "status": status,
        "duration_ms": duration,
        "exit_code": proc.returncode,
        "tail": tail_lines(output, 50),
        "skipped_reason": None,
    }


def commit_lint_stage(root: Path, base_sha: str) -> dict:
    proc = run(["git", "log", "--format=%s", f"{base_sha}..HEAD"], cwd=root)
    subjects = [] if proc.returncode != 0 else [line for line in proc.stdout.splitlines() if line.strip()]
    failures = [subject for subject in subjects if not COMMIT_RE.match(subject)]
    return {
        "name": "commit-lint",
        "command": "git log --format=%s <merge-base>..HEAD",
        "cwd": str(root),
        "status": "failed" if failures else "passed",
        "duration_ms": 0,
        "exit_code": 1 if failures else 0,
        "tail": "\n".join(failures),
        "skipped_reason": None,
    }


def security_stages(root: Path, working_root: Path) -> list[dict]:
    stages: list[dict] = []
    if command_exists("gitleaks"):
        stages.append(run_stage("secret-scan", "gitleaks detect --source . --no-git -v", root))
    else:
        stages.append(skipped_stage("secret-scan", root, "gitleaks not installed"))

    if (working_root / "package-lock.json").exists():
        stages.append(run_stage("dependency-audit", "npm audit --omit=dev --json", working_root, allow_warning=True))
    elif (working_root / "pnpm-lock.yaml").exists():
        stages.append(run_stage("dependency-audit", "pnpm audit --prod --json", working_root, allow_warning=True))
    elif command_exists("pip-audit") and (working_root / "pyproject.toml").exists():
        stages.append(run_stage("dependency-audit", "pip-audit --format json", working_root, allow_warning=True))
    else:
        stages.append(
            skipped_stage(
                "dependency-audit",
                working_root,
                "no supported dependency audit tooling detected",
            )
        )
    return stages


def summarize(stages: list[dict]) -> str:
    if any(stage["status"] == "failed" for stage in stages):
        return "failed"
    if any(stage["status"] == "warning" for stage in stages):
        return "passed-with-warnings"
    return "passed"


def preflight(args: argparse.Namespace) -> int:
    root = repo_root()
    state_file, state, body = read_state(args.ticket, root)
    working_root_value = str(state.get("working_root") or root)
    working_root = Path(working_root_value)
    if not working_root.is_absolute():
        working_root = root / working_root
    commands = state.get("validation_commands", {})
    if not isinstance(commands, dict):
        commands = {}
    merge_base_sha = merge_base(root, args.diff_base)

    stages = [
        run_stage("lint", str(commands.get("lint") or ""), working_root),
        run_stage("typecheck", str(commands.get("typecheck") or ""), working_root),
        run_stage("test", str(commands.get("test") or ""), working_root),
        run_stage("build", str(commands.get("build") or ""), working_root),
    ]
    stages.extend(security_stages(root, working_root))
    stages.append(commit_lint_stage(root, merge_base_sha))

    summary = summarize(stages)
    blockers = [
        f"{stage['name']} stage failed: {stage['tail'].splitlines()[-1] if stage['tail'] else 'see output'}"
        for stage in stages
        if stage["status"] == "failed"
    ]
    head = run(["git", "rev-parse", "HEAD"], cwd=root).stdout.strip()
    result = {
        "ticket": state.get("ticket", args.ticket),
        "branch": state.get("branch", ""),
        "ran_at": now_utc(),
        "repo_root": str(root),
        "working_root": str(working_root),
        "target_modules": state.get("target_modules", []),
        "merge_base": merge_base_sha,
        "head": head,
        "summary": summary,
        "stages": stages,
        "blockers": blockers,
    }

    preflight_path = state.get("preflight_path") or f"docs/specs/{state_file.parent.name}/preflight.json"
    output_path = root / str(preflight_path)
    write_atomic(output_path, json.dumps(result, indent=2) + "\n")

    state["status"] = "preflight"
    state["phase_detail"] = "preflight green" if summary != "failed" else f"preflight failed: {blockers[0] if blockers else 'unknown'}"
    state["last_updated"] = now_utc()
    write_state_file(state_file, state, body, root)
    print(output_path)
    return 0 if summary != "failed" else 1


def commit_lint(args: argparse.Namespace) -> int:
    root = repo_root()
    result = commit_lint_stage(root, merge_base(root, args.diff_base))
    print(json.dumps(result, indent=2))
    return 0 if result["status"] == "passed" else 1


def add_parser(subparsers) -> None:
    preflight_parser = subparsers.add_parser("preflight", help="Run local CI mirror and write preflight.json")
    preflight_parser.add_argument("ticket")
    preflight_parser.add_argument("--diff-base", default=None)
    preflight_parser.set_defaults(func=preflight)

    commit_parser = subparsers.add_parser("commit-lint", help="Lint commit subjects in the branch range")
    commit_parser.add_argument("--diff-base", default=None)
    commit_parser.set_defaults(func=commit_lint)
