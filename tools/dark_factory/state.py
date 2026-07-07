from __future__ import annotations

import argparse
import shutil
from pathlib import Path

from .utils import DarkFactoryError, now_utc, repo_root, slugify, today_utc, write_atomic
from .yamlish import dump_simple_yaml, split_frontmatter


PHASES = [
    "intake",
    "workspace",
    "clarifying",
    "specifying",
    "planning",
    "implementing",
    "reviewing",
    "evidencing",
    "preflight",
    "shipping",
    "merging",
    "complete",
]


def skills_dir(root: Path) -> Path:
    installed = root / ".agents" / "skills"
    if (installed / "df-spec" / "templates" / "state-template.md").exists():
        return installed
    return root / "skills"


def state_template_path(root: Path) -> Path:
    return skills_dir(root) / "df-spec" / "templates" / "state-template.md"


def state_key_order(root: Path) -> list[str]:
    template = state_template_path(root)
    if not template.exists():
        return []
    frontmatter, _ = split_frontmatter(template.read_text(encoding="utf-8"))
    return list(frontmatter.keys())


def specs_root(root: Path) -> Path:
    return root / "docs" / "specs"


def story_slug(ticket: str, title: str = "") -> str:
    suffix = slugify(title)
    return f"{ticket}-{suffix}" if suffix else ticket


def find_story_dir(ticket: str, root: Path | None = None) -> Path:
    root = root or repo_root()
    base = specs_root(root)
    if not base.exists():
        raise DarkFactoryError("docs/specs does not exist")

    exact = base / ticket
    if (exact / "state.md").exists():
        return exact

    prefix_matches = [
        candidate
        for candidate in sorted(base.iterdir())
        if candidate.is_dir()
        and candidate.name.startswith(f"{ticket}-")
        and (candidate / "state.md").exists()
    ]
    if len(prefix_matches) == 1:
        return prefix_matches[0]

    matches: list[Path] = []
    for candidate in sorted(base.iterdir()):
        state_file = candidate / "state.md"
        if not state_file.exists():
            continue
        data, _ = split_frontmatter(state_file.read_text(encoding="utf-8"))
        if candidate.name == ticket or candidate.name.startswith(f"{ticket}-"):
            matches.append(candidate)
        elif data.get("ticket") == ticket:
            matches.append(candidate)
    if len(matches) == 1:
        return matches[0]
    if not matches:
        raise DarkFactoryError(f"no story state found for {ticket}")
    raise DarkFactoryError(f"multiple story states match {ticket}: {', '.join(p.name for p in matches)}")


def read_state(ticket: str, root: Path | None = None) -> tuple[Path, dict, str]:
    story_dir = find_story_dir(ticket, root)
    state_file = story_dir / "state.md"
    data, body = split_frontmatter(state_file.read_text(encoding="utf-8"))
    if not data:
        raise DarkFactoryError(f"{state_file} has no frontmatter")
    return state_file, data, body


def write_state_file(path: Path, data: dict, body: str, root: Path | None = None) -> None:
    root = root or repo_root(path)
    key_order = state_key_order(root) or list(data.keys())
    write_atomic(path, "---\n" + dump_simple_yaml(data, key_order) + "---\n" + body)


def list_states(root: Path | None = None) -> list[dict]:
    root = root or repo_root()
    base = specs_root(root)
    if not base.exists():
        return []
    states: list[dict] = []
    for state_file in sorted(base.glob("*/state.md")):
        data, _ = split_frontmatter(state_file.read_text(encoding="utf-8"))
        if data:
            item = dict(data)
            item["path"] = state_file.as_posix()
            states.append(item)
    return states


def init_state(args: argparse.Namespace) -> int:
    root = repo_root()
    title = args.title or slugify(args.ticket)
    slug = args.slug or story_slug(args.ticket, title)
    story_dir = specs_root(root) / slug
    story_dir.mkdir(parents=True, exist_ok=True)
    for subdir in (
        "reviews",
        "evidence/ui",
        "evidence/api",
        "evidence/cli",
        "evidence/unit",
        "evidence/migration",
    ):
        (story_dir / subdir).mkdir(parents=True, exist_ok=True)

    template = state_template_path(root)
    state_file = story_dir / "state.md"
    if template.exists() and not state_file.exists():
        shutil.copyfile(template, state_file)
    elif not state_file.exists():
        write_atomic(state_file, "---\n---\n# Story State\n")

    text = state_file.read_text(encoding="utf-8")
    data, body = split_frontmatter(text)
    branch = args.branch or f"{args.ticket}-{slugify(title)}"
    defaults = {
        "ticket": args.ticket,
        "title": title,
        "branch": branch,
        "status": args.status or "intake",
        "phase_detail": "",
        "blocked_from": "",
        "blocked_reason": "",
        "risk": "low",
        "auto_merge_eligible": False,
        "started": today_utc(),
        "last_updated": now_utc(),
        "repo_root": str(root),
        "working_root": str(root),
        "workspace_path": "",
        "workspace_isolated": False,
        "target_modules": [args.module or "."],
        "validation_commands": {"lint": "", "typecheck": "", "test": "", "build": ""},
        "module_scope_notes": "",
        "spec_path": f"docs/specs/{slug}/spec.md",
        "plan_path": f"docs/specs/{slug}/plan.md",
        "review_path": f"docs/specs/{slug}/reviews",
        "evidence_path": f"docs/specs/{slug}/evidence",
        "preflight_path": f"docs/specs/{slug}/preflight.json",
        "pr_url": "",
        "pr_number": "",
        "merge_sha": "",
        "run_id": "",
        "observability_enabled": True,
    }
    data.update(defaults)
    write_state_file(state_file, data, body, root)
    print(state_file)
    return 0


def get_state(args: argparse.Namespace) -> int:
    _, data, _ = read_state(args.ticket)
    value = data.get(args.field, "")
    if isinstance(value, (dict, list)):
        import json

        print(json.dumps(value, indent=2))
    else:
        print(value)
    return 0


def set_state(args: argparse.Namespace) -> int:
    import json

    path, data, body = read_state(args.ticket)
    value: object = args.value
    if args.value.startswith("{") or args.value.startswith("["):
        value = json.loads(args.value)
    elif args.value.lower() == "true":
        value = True
    elif args.value.lower() == "false":
        value = False
    data[args.field] = value
    data["last_updated"] = now_utc()
    write_state_file(path, data, body)
    try:
        from .observability.instrumentation import maybe_log_phase_transition

        run_id = str(data.get("run_id") or "")
        maybe_log_phase_transition(args.ticket, args.field, value, run_id=run_id)
    except Exception:
        pass
    print(path)
    return 0


def block_state(args: argparse.Namespace) -> int:
    path, data, body = read_state(args.ticket)
    current_status = str(data.get("status", ""))
    if current_status != "blocked":
        data["blocked_from"] = current_status
    data["blocked_reason"] = args.reason
    data["status"] = "blocked"
    data["last_updated"] = now_utc()
    write_state_file(path, data, body)
    try:
        from .observability.instrumentation import maybe_log_phase_transition

        run_id = str(data.get("run_id") or "")
        maybe_log_phase_transition(args.ticket, "status", "blocked", run_id=run_id)
    except Exception:
        pass
    print(path)
    return 0


def unblock_state(args: argparse.Namespace) -> int:
    path, data, body = read_state(args.ticket)
    if str(data.get("status")) != "blocked":
        raise DarkFactoryError(f"{args.ticket} is not blocked (status={data.get('status')})")
    resume_status = args.status or str(data.get("blocked_from") or "")
    if not resume_status:
        raise DarkFactoryError(
            f"{args.ticket} has no recorded blocked_from phase; pass --status explicitly"
        )
    data["status"] = resume_status
    data["blocked_from"] = ""
    data["blocked_reason"] = ""
    data["last_updated"] = now_utc()
    write_state_file(path, data, body)
    try:
        from .observability.instrumentation import maybe_log_phase_transition

        run_id = str(data.get("run_id") or "")
        maybe_log_phase_transition(args.ticket, "status", resume_status, run_id=run_id)
    except Exception:
        pass
    print(path)
    return 0


def list_state_cmd(args: argparse.Namespace) -> int:
    import json

    states = list_states()
    if args.json:
        print(json.dumps(states, indent=2))
        return 0
    for item in states:
        print(f"{item.get('ticket')} {item.get('status')} {item.get('path')}")
    return 0


def add_parser(subparsers) -> None:
    parser = subparsers.add_parser("state", help="Read and mutate Dark Factory story state")
    nested = parser.add_subparsers(dest="state_command", required=True)

    init = nested.add_parser("init", help="Initialize a story state file")
    init.add_argument("ticket")
    init.add_argument("--title", default="")
    init.add_argument("--slug", default="")
    init.add_argument("--branch", default="")
    init.add_argument("--module", default=".")
    init.add_argument("--status", choices=PHASES + ["blocked"], default="intake")
    init.set_defaults(func=init_state)

    get = nested.add_parser("get", help="Print one state field")
    get.add_argument("ticket")
    get.add_argument("field")
    get.set_defaults(func=get_state)

    set_ = nested.add_parser("set", help="Set one state field")
    set_.add_argument("ticket")
    set_.add_argument("field")
    set_.add_argument("value")
    set_.set_defaults(func=set_state)

    list_ = nested.add_parser("list", help="List story states")
    list_.add_argument("--json", action="store_true")
    list_.set_defaults(func=list_state_cmd)

    block = nested.add_parser(
        "block", help="Mark a story blocked with a durable, resumable reason"
    )
    block.add_argument("ticket")
    block.add_argument("--reason", required=True)
    block.set_defaults(func=block_state)

    unblock = nested.add_parser(
        "unblock", help="Clear status: blocked and resume the prior phase"
    )
    unblock.add_argument("ticket")
    unblock.add_argument(
        "--status",
        default="",
        help="Phase to resume into (defaults to the recorded blocked_from)",
    )
    unblock.set_defaults(func=unblock_state)
