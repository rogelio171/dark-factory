from __future__ import annotations

from pathlib import Path

from .utils import command_exists, repo_root, run


def doctor(args) -> int:
    root = repo_root()
    checks: list[tuple[str, bool, str]] = []
    checks.append(("git", command_exists("git"), "git executable"))
    checks.append(("repo", (root / ".git").exists(), f"repo root: {root}"))
    checks.append(("skills", (root / ".agents" / "skills").exists() or (root / "skills").exists(), "skill directory"))
    checks.append(("wiki", (root / "wiki").exists(), "wiki directory"))
    checks.append(("project-profile", (root / "wiki" / "project-profile.md").exists(), "wiki/project-profile.md"))
    try:
        from .observability.db import db_path, schema_version, connect, SCHEMA_VERSION
        from .observability.config import config_path

        checks.append(("observability-db", db_path(root).exists(), str(db_path(root))))
        if db_path(root).exists():
            connection = connect(root)
            version = schema_version(connection)
            connection.close()
            checks.append(("observability-schema", version == SCHEMA_VERSION, f"schema_version={version}"))
        checks.append(("observability-config", config_path(root).exists(), str(config_path(root))))
    except Exception as exc:
        checks.append(("observability", False, str(exc)))
    checks.append(("gh", command_exists("gh"), "GitHub CLI"))
    if command_exists("gh"):
        auth = run(["gh", "auth", "status"], cwd=root)
        checks.append(("gh-auth", auth.returncode == 0, "GitHub CLI authentication"))

    if args.runtime == "cursor":
        checks.append(("cursor-runtime", (root / ".agents" / "skills").exists(), ".agents/skills for Cursor/generic discovery"))
        checks.append(("cursor-bin", (root / ".agents" / "bin" / "df").exists() or (root / "bin" / "df").exists(), "df shim"))
    elif args.runtime == "claude":
        checks.append(("claude-plugin", (root / ".claude-plugin" / "plugin.json").exists() or (root / ".agents" / "skills").exists(), "Claude plugin or generic skills"))

    failures = 0
    for name, passed, detail in checks:
        status = "ok" if passed else "missing"
        print(f"{status}\t{name}\t{detail}")
        failures += 0 if passed else 1
    return 1 if failures else 0


def add_parser(subparsers) -> None:
    parser = subparsers.add_parser("doctor", help="Check Dark Factory harness setup")
    parser.add_argument("--runtime", choices=["cursor", "claude", "generic"], default="generic")
    parser.set_defaults(func=doctor)
