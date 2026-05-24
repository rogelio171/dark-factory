from __future__ import annotations

import argparse
from pathlib import Path

from .state import init_state, story_slug
from .utils import DarkFactoryError, repo_root, run, slugify


def story_init(args: argparse.Namespace) -> int:
    root = repo_root()
    title = args.title or args.ticket
    branch = args.branch or f"{args.ticket}-{slugify(title)}"
    if not args.no_branch:
        current = run(["git", "branch", "--show-current"], cwd=root).stdout.strip()
        if current != branch:
            proc = run(["git", "checkout", "-b", branch], cwd=root)
            if proc.returncode != 0:
                raise DarkFactoryError(proc.stderr.strip() or "git checkout -b failed")
    args.branch = branch
    args.slug = args.slug or story_slug(args.ticket, title)
    result = init_state(args)
    try:
        from .observability.db import ensure_initialized
        from .observability.record import start_run

        ensure_initialized(root)
        run = start_run(
            args.ticket,
            story_slug=args.slug,
            current_phase=str(args.status or "intake"),
        )
        from .state import read_state, write_state_file

        state_file, data, body = read_state(args.ticket, root)
        data["run_id"] = run["run_id"]
        data["observability_enabled"] = True
        write_state_file(state_file, data, body, root)
    except Exception:
        pass
    if args.acceptance:
        source = Path(args.acceptance.removeprefix("@"))
        if not source.is_absolute():
            source = root / source
        if not source.exists():
            raise DarkFactoryError(f"acceptance file not found: {source}")
        story_dir = root / "docs" / "specs" / args.slug
        (story_dir / "acceptance.md").write_text(source.read_text(encoding="utf-8"), encoding="utf-8")
    return result


def add_parser(subparsers) -> None:
    parser = subparsers.add_parser("story", help="Initialize local story artifacts")
    nested = parser.add_subparsers(dest="story_command", required=True)
    init = nested.add_parser("init")
    init.add_argument("ticket")
    init.add_argument("--title", default="")
    init.add_argument("--slug", default="")
    init.add_argument("--branch", default="")
    init.add_argument("--module", default=".")
    init.add_argument("--status", default="intake")
    init.add_argument("--acceptance", default="")
    init.add_argument("--no-branch", action="store_true")
    init.set_defaults(func=story_init)
