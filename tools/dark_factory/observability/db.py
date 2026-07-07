from __future__ import annotations

import os
import sqlite3
from pathlib import Path

from ..utils import repo_root, run

SCHEMA_VERSION = "1"
GITIGNORE_ENTRIES = [
    ".agents/dark-factory/observability.db",
    ".agents/dark-factory/observability.db-wal",
    ".agents/dark-factory/observability.db-shm",
    ".agents/dark-factory/exports/",
]


def observability_dir(root: Path | None = None) -> Path:
    return (root or repo_root()) / ".agents" / "dark-factory"


def db_path(root: Path | None = None) -> Path:
    return observability_dir(root) / "observability.db"


def config_path(root: Path | None = None) -> Path:
    return observability_dir(root) / "observability.toml"


def connect(root: Path | None = None) -> sqlite3.Connection:
    directory = observability_dir(root)
    directory.mkdir(parents=True, exist_ok=True)
    connection = sqlite3.connect(db_path(root), timeout=30.0)
    connection.row_factory = sqlite3.Row
    connection.execute("PRAGMA foreign_keys = ON")
    connection.execute("PRAGMA journal_mode = WAL")
    return connection


def apply_schema(connection: sqlite3.Connection) -> None:
    schema_file = Path(__file__).resolve().parent / "schema.sql"
    connection.executescript(schema_file.read_text(encoding="utf-8"))
    connection.execute(
        "INSERT OR REPLACE INTO schema_meta(key, value) VALUES ('schema_version', ?)",
        (SCHEMA_VERSION,),
    )
    connection.commit()


def schema_version(connection: sqlite3.Connection) -> str | None:
    try:
        row = connection.execute(
            "SELECT value FROM schema_meta WHERE key = 'schema_version'"
        ).fetchone()
    except sqlite3.OperationalError:
        return None
    return str(row["value"]) if row else None


def ensure_initialized(root: Path | None = None, force: bool = False) -> Path:
    from .config import save_default_config

    root = root or repo_root()
    save_default_config(root)
    path = db_path(root)
    if force and path.exists():
        path.unlink()
        for suffix in ("-wal", "-shm"):
            sidecar = Path(str(path) + suffix)
            if sidecar.exists():
                sidecar.unlink()
    connection = connect(root)
    try:
        current = schema_version(connection)
        if current != SCHEMA_VERSION:
            apply_schema(connection)
    finally:
        connection.close()
    ensure_gitignore(root)
    return path


def ensure_gitignore(root: Path | None = None) -> None:
    root = root or repo_root()
    gitignore = root / ".gitignore"
    existing = gitignore.read_text(encoding="utf-8") if gitignore.exists() else ""
    marker = "# Dark Factory observability"
    if marker in existing:
        return
    # An existing pattern (e.g. a blanket .agents/ ignore) may already cover
    # the store; ask git instead of duplicating entries.
    check = run(["git", "-C", str(root), "check-ignore", *GITIGNORE_ENTRIES])
    if check.returncode == 0 and len(check.stdout.splitlines()) == len(GITIGNORE_ENTRIES):
        return
    block = "\n".join(
        [
            "",
            marker,
            *GITIGNORE_ENTRIES,
            "",
        ]
    )
    with gitignore.open("a", encoding="utf-8") as handle:
        handle.write(block)


def row_to_dict(row: sqlite3.Row | None) -> dict | None:
    if row is None:
        return None
    return {key: row[key] for key in row.keys()}


def detect_runtime() -> str:
    for env_name in ("DF_RUNTIME", "CURSOR_AGENT", "CLAUDE_CODE", "CODEX_RUNTIME", "GITHUB_COPILOT"):
        value = os.environ.get(env_name, "")
        if value:
            if env_name == "DF_RUNTIME":
                return value.lower()
            if env_name == "CURSOR_AGENT":
                return "cursor"
            if env_name == "CLAUDE_CODE":
                return "claude"
            if env_name == "CODEX_RUNTIME":
                return "codex"
            if env_name == "GITHUB_COPILOT":
                return "copilot"
    return "unknown"
