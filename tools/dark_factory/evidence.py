from __future__ import annotations

import argparse
from pathlib import Path

from .state import read_state, write_state_file
from .utils import now_utc, repo_root, write_atomic
from .yamlish import parse_simple_yaml

EVIDENCE_KINDS = ("ui", "api", "cli", "unit", "migration")


def sidecar_for(path: Path) -> Path:
    return path.with_suffix(path.suffix + ".yaml")


def evidence_rows(evidence_root: Path) -> list[tuple[str, str, str]]:
    rows: list[tuple[str, str, str]] = []
    for kind in EVIDENCE_KINDS:
        kind_dir = evidence_root / kind
        if not kind_dir.exists():
            continue
        for item in sorted(kind_dir.iterdir()):
            if not item.is_file() or item.name.endswith(".yaml"):
                continue
            sidecar = sidecar_for(item)
            meta = parse_simple_yaml(sidecar.read_text(encoding="utf-8")) if sidecar.exists() else {}
            criterion = str(meta.get("criterion") or meta.get("ac") or item.stem)
            files = str(meta.get("files") or item.relative_to(evidence_root).as_posix())
            rows.append((criterion, kind, files))
    return rows


def write_index(args: argparse.Namespace) -> int:
    root = repo_root()
    state_file, state, body = read_state(args.ticket, root)
    evidence_path = state.get("evidence_path") or f"docs/specs/{state_file.parent.name}/evidence"
    evidence_root = root / str(evidence_path)
    evidence_root.mkdir(parents=True, exist_ok=True)
    rows = evidence_rows(evidence_root)
    lines = [
        f"# Evidence Index for {state.get('ticket', args.ticket)}",
        "",
        "| Criterion | Kind | Files |",
        "| --- | --- | --- |",
    ]
    if rows:
        for criterion, kind, files in rows:
            lines.append(f"| {criterion} | {kind} | {files} |")
    else:
        lines.append("| _No evidence captured yet_ | skipped |  |")
    lines.extend(
        [
            "",
            "## Notes",
            "",
            f"- App version under test: {state.get('branch', '')}",
            "- Environment: local",
            f"- Date: {now_utc()}",
        ]
    )
    index_path = evidence_root / "INDEX.md"
    write_atomic(index_path, "\n".join(lines) + "\n")
    state["status"] = "evidencing"
    state["phase_detail"] = f"evidence indexed: {len(rows)} file(s)"
    state["last_updated"] = now_utc()
    write_state_file(state_file, state, body, root)
    print(index_path)
    return 0 if rows or args.allow_empty else 1


def add_parser(subparsers) -> None:
    parser = subparsers.add_parser("evidence", help="Manage Dark Factory evidence")
    nested = parser.add_subparsers(dest="evidence_command", required=True)
    index = nested.add_parser("index", help="Write evidence/INDEX.md")
    index.add_argument("ticket")
    index.add_argument("--allow-empty", action="store_true")
    index.set_defaults(func=write_index)
