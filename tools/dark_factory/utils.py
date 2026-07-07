from __future__ import annotations

import os
import re
import shutil
import subprocess
import sys
import tempfile
from datetime import datetime, timezone
from pathlib import Path
from typing import Iterable


class DarkFactoryError(RuntimeError):
    """Raised for deterministic harness failures."""


_observability_warned = False


def warn_observability_failure(context: str, exc: Exception) -> None:
    """Report a failed observability recording without failing the command.

    Recording stays fail-open, but a broken store must not be invisible:
    print one warning per process instead of swallowing every error.
    """
    global _observability_warned
    if _observability_warned:
        return
    _observability_warned = True
    print(
        f"df: warning: observability recording failed ({context}): {exc}; "
        "run 'df observability doctor' to inspect the store",
        file=sys.stderr,
    )


def now_utc() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def today_utc() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%d")


def repo_root(start: Path | None = None) -> Path:
    cwd = (start or Path.cwd()).resolve()
    try:
        output = subprocess.check_output(
            ["git", "-C", str(cwd), "rev-parse", "--show-toplevel"],
            text=True,
            stderr=subprocess.DEVNULL,
        ).strip()
        return Path(output).resolve()
    except (subprocess.CalledProcessError, FileNotFoundError):
        return cwd


def relpath(path: Path, root: Path | None = None) -> str:
    base = root or repo_root()
    try:
        return path.resolve().relative_to(base.resolve()).as_posix()
    except ValueError:
        return path.as_posix()


def write_atomic(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.NamedTemporaryFile(
        "w", encoding="utf-8", dir=str(path.parent), delete=False
    ) as handle:
        handle.write(content)
        tmp_name = handle.name
    os.replace(tmp_name, path)


def run(
    command: list[str] | str,
    cwd: Path | None = None,
    check: bool = False,
    shell: bool = False,
) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        command,
        cwd=str(cwd) if cwd else None,
        text=True,
        capture_output=True,
        check=check,
        shell=shell,
    )


def command_exists(name: str) -> bool:
    return shutil.which(name) is not None


def slugify(value: str) -> str:
    slug = re.sub(r"[^a-zA-Z0-9]+", "-", value.strip().lower()).strip("-")
    return slug or "story"


def tail_lines(text: str, limit: int = 50) -> str:
    return "\n".join(text.splitlines()[-limit:])


def default_branch(root: Path | None = None) -> str:
    root = root or repo_root()
    proc = run(
        "git symbolic-ref --short refs/remotes/origin/HEAD 2>/dev/null | sed 's@^origin/@@'",
        cwd=root,
        shell=True,
    )
    branch = proc.stdout.strip()
    if branch:
        return branch
    proc = run(["git", "branch", "--show-current"], cwd=root)
    return proc.stdout.strip() or "main"


def merge_base(root: Path, base_ref: str | None = None) -> str:
    ref = base_ref or f"origin/{default_branch(root)}"
    proc = run(["git", "merge-base", "HEAD", ref], cwd=root)
    if proc.returncode != 0:
        raise DarkFactoryError(proc.stderr.strip() or f"could not merge-base {ref}")
    return proc.stdout.strip()


def iter_common_module_roots(root: Path) -> Iterable[Path]:
    yield root
    for name in ("apps", "packages", "services", "libs"):
        parent = root / name
        if not parent.is_dir():
            continue
        for child in sorted(parent.iterdir()):
            if child.is_dir():
                yield child
