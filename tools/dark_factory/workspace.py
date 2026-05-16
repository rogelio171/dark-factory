from __future__ import annotations

import argparse
import json
from pathlib import Path

from .state import read_state, write_state_file
from .utils import DarkFactoryError, now_utc, repo_root, run


def git_output(args: list[str], root: Path) -> str:
    proc = run(["git", *args], cwd=root)
    return proc.stdout.strip() if proc.returncode == 0 else ""


def detect_workspace(args: argparse.Namespace) -> int:
    root = repo_root()
    common_dir = git_output(["rev-parse", "--git-common-dir"], root)
    git_dir = git_output(["rev-parse", "--git-dir"], root)
    superproject = git_output(["rev-parse", "--show-superproject-working-tree"], root)
    is_worktree = bool(common_dir and git_dir and Path(git_dir).name != Path(common_dir).name)
    result = {
        "repo_root": str(root),
        "workspace_path": str(root),
        "working_root": str(root),
        "workspace_isolated": bool(is_worktree and not superproject),
        "is_submodule": bool(superproject),
        "git_dir": git_dir,
        "git_common_dir": common_dir,
    }
    print(json.dumps(result, indent=2))
    return 0


def create_workspace(args: argparse.Namespace) -> int:
    root = repo_root()
    if not args.ticket:
        raise DarkFactoryError("--ticket is required")
    if not args.worktree:
        raise DarkFactoryError("workspace create currently requires --worktree")
    state_file, state, body = read_state(args.ticket, root)
    branch = str(state.get("branch") or args.ticket)
    parent = root / ".worktrees"
    parent.mkdir(exist_ok=True)
    target = parent / branch
    proc = run(["git", "worktree", "add", str(target), branch], cwd=root)
    if proc.returncode != 0:
        raise DarkFactoryError(proc.stderr.strip() or "git worktree add failed")
    state["workspace_path"] = str(target)
    state["workspace_isolated"] = True
    state["last_updated"] = now_utc()
    write_state_file(state_file, state, body, root)
    print(target)
    return 0


def add_parser(subparsers) -> None:
    parser = subparsers.add_parser("workspace", help="Detect or create a story workspace")
    nested = parser.add_subparsers(dest="workspace_command", required=True)
    detect = nested.add_parser("detect")
    detect.set_defaults(func=detect_workspace)
    create = nested.add_parser("create")
    create.add_argument("--ticket", required=True)
    create.add_argument("--worktree", action="store_true")
    create.set_defaults(func=create_workspace)
