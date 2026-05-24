from __future__ import annotations

import argparse
import sys

from . import __version__
from .utils import DarkFactoryError

KNOWN_COMMANDS = {
    "state",
    "detect-tooling",
    "classify-risk",
    "commit-lint",
    "preflight",
    "evidence",
    "render-pr-body",
    "ship",
    "pr",
    "resume",
    "doctor",
    "workspace",
    "story",
    "observability",
}


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="df", description="Dark Factory deterministic harness")
    parser.add_argument("--version", action="version", version=f"dark-factory {__version__}")
    subparsers = parser.add_subparsers(dest="command", required=True)

    from . import doctor, evidence, pr, preflight, resume, risk, state, story, tooling, workspace
    from .observability import cli as observability_cli

    state.add_parser(subparsers)
    doctor.add_parser(subparsers)
    tooling.add_parser(subparsers)
    risk.add_parser(subparsers)
    preflight.add_parser(subparsers)
    evidence.add_parser(subparsers)
    pr.add_parser(subparsers)
    resume.add_parser(subparsers)
    workspace.add_parser(subparsers)
    story.add_parser(subparsers)
    observability_cli.add_parser(subparsers)

    return parser


def main(argv: list[str] | None = None) -> int:
    argv = argv if argv is not None else sys.argv[1:]
    parser = build_parser()
    args = parser.parse_args(argv)
    command = args.command

    try:
        from .observability.db import ensure_initialized

        if command != "observability" or getattr(args, "observability_command", "") != "init":
            ensure_initialized()
    except Exception:
        pass

    from .observability.instrumentation import cli_span

    with cli_span(command, argv) as result:
        try:
            result.code = int(args.func(args) or 0)
            return result.code
        except DarkFactoryError as exc:
            print(f"df: {exc}", file=sys.stderr)
            result.code = 1
            return 1


if __name__ == "__main__":
    raise SystemExit(main())
