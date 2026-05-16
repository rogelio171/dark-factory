from __future__ import annotations

import argparse
import json
from pathlib import Path

from .state import read_state, write_state_file
from .utils import iter_common_module_roots, now_utc, relpath, repo_root, write_atomic


def package_manager(module: Path, root: Path) -> str:
    for filename, manager in (
        ("pnpm-lock.yaml", "pnpm"),
        ("yarn.lock", "yarn"),
        ("package-lock.json", "npm"),
    ):
        if (module / filename).exists() or (root / filename).exists():
            return manager
    return "npm"


def npm_script_command(manager: str, script: str) -> str:
    if manager == "yarn":
        return f"yarn {script}"
    if manager == "pnpm":
        return f"pnpm {script}"
    if script == "test":
        return "npm test"
    return f"npm run {script}"


def detect_node(module: Path, root: Path) -> tuple[str, dict[str, str]] | None:
    manifest = module / "package.json"
    if not manifest.exists():
        return None
    package = json.loads(manifest.read_text(encoding="utf-8"))
    scripts = package.get("scripts", {}) if isinstance(package, dict) else {}
    manager = package_manager(module, root)
    commands = {
        "lint": npm_script_command(manager, "lint") if "lint" in scripts else "",
        "typecheck": npm_script_command(manager, "typecheck") if "typecheck" in scripts else ("npx tsc --noEmit" if (module / "tsconfig.json").exists() else ""),
        "test": npm_script_command(manager, "test") if "test" in scripts else "",
        "build": npm_script_command(manager, "build") if "build" in scripts else "",
    }
    return f"Node/{manager}", commands


def detect_python(module: Path) -> tuple[str, dict[str, str]] | None:
    manifest = module / "pyproject.toml"
    if not manifest.exists():
        return None
    text = manifest.read_text(encoding="utf-8")
    commands = {
        "lint": "ruff check ." if "ruff" in text else "",
        "typecheck": "mypy ." if "mypy" in text else "",
        "test": "pytest -q",
        "build": "python -m build" if (module / "pyproject.toml").exists() else "",
    }
    return "Python/pyproject", commands


def detect_go(module: Path) -> tuple[str, dict[str, str]] | None:
    if not (module / "go.mod").exists():
        return None
    return "Go", {
        "lint": "go vet ./...",
        "typecheck": "",
        "test": "go test ./...",
        "build": "go build ./...",
    }


def detect_rust(module: Path) -> tuple[str, dict[str, str]] | None:
    if not (module / "Cargo.toml").exists():
        return None
    return "Rust", {
        "lint": "cargo fmt --check && cargo clippy --all-targets -- -D warnings",
        "typecheck": "cargo check --all-targets",
        "test": "cargo test --all",
        "build": "cargo build --all-targets",
    }


def detect_make(module: Path) -> tuple[str, dict[str, str]] | None:
    makefile = module / "Makefile"
    if not makefile.exists():
        return None
    text = makefile.read_text(encoding="utf-8", errors="ignore")
    commands = {}
    for stage in ("lint", "typecheck", "test", "build"):
        commands[stage] = f"make {stage}" if f"{stage}:" in text else ""
    return "Makefile", commands


def detect_modules(root: Path) -> list[dict]:
    modules: list[dict] = []
    seen: set[Path] = set()
    for module in iter_common_module_roots(root):
        if module in seen:
            continue
        seen.add(module)
        detected = (
            detect_node(module, root)
            or detect_python(module)
            or detect_go(module)
            or detect_rust(module)
            or detect_make(module)
        )
        if not detected:
            continue
        tooling, commands = detected
        modules.append(
            {
                "path": "." if module == root else relpath(module, root),
                "tooling": tooling,
                "command_root": "." if module == root else relpath(module, root),
                "validation_commands": commands,
            }
        )
    return modules


def render_profile(root: Path, modules: list[dict]) -> str:
    layout = "single-module" if len(modules) <= 1 else "multi-module"
    default = modules[0]["path"] if modules else "."
    lines = [
        "# Project Profile",
        "",
        "## Repository",
        "",
        f"- Repo root: `{root}`",
        f"- Default working root: `{default}`",
        f"- Layout: `{layout}`",
        f"- Profile updated: `{now_utc()}`",
        "",
        "## Modules",
        "",
        "| Module | Tooling | Command root | Validation commands |",
        "| --- | --- | --- | --- |",
    ]
    for module in modules:
        commands = module["validation_commands"]
        command_text = ", ".join(
            f"{name}: `{command}`" for name, command in commands.items() if command
        ) or "none detected"
        lines.append(
            f"| `{module['path']}` | {module['tooling']} | `{module['command_root']}` | {command_text} |"
        )
    lines.extend(
        [
            "",
            "## Default Story Scope",
            "",
            f"- Target modules: `{default}`",
            "- Do not touch:",
            "- Scope notes:",
            "",
            "## Preflight Defaults",
            "",
        ]
    )
    defaults = modules[0]["validation_commands"] if modules else {}
    for stage in ("lint", "typecheck", "test", "build"):
        lines.append(f"- {stage.capitalize()}: {defaults.get(stage, '')}")
    return "\n".join(lines) + "\n"


def detect_tooling(args: argparse.Namespace) -> int:
    root = repo_root()
    modules = detect_modules(root)
    if args.module:
        modules = [module for module in modules if module["path"] == args.module]
    if args.json:
        print(json.dumps({"modules": modules}, indent=2))
    if not args.no_write:
        profile = render_profile(root, modules)
        write_atomic(root / "wiki" / "project-profile.md", profile)
    if args.ticket and modules:
        state_file, data, body = read_state(args.ticket, root)
        selected = modules[0]
        data["working_root"] = str(root / selected["command_root"]) if selected["command_root"] != "." else str(root)
        data["target_modules"] = [selected["path"]]
        data["validation_commands"] = selected["validation_commands"]
        data["last_updated"] = now_utc()
        write_state_file(state_file, data, body, root)
    return 0


def add_parser(subparsers) -> None:
    parser = subparsers.add_parser("detect-tooling", help="Detect modules and validation commands")
    parser.add_argument("--module", default="")
    parser.add_argument("--ticket", default="")
    parser.add_argument("--json", action="store_true")
    parser.add_argument("--no-write", action="store_true")
    parser.set_defaults(func=detect_tooling)
