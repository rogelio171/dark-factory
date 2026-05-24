#!/usr/bin/env python3
"""Validate Dark Factory skill-pack structure and generated workflow templates."""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SKILLS_DIR = ROOT / "skills"
WORKFLOW_TEMPLATE_DIR = (
    SKILLS_DIR / "df-github-init" / "templates" / ".github" / "workflows"
)
ROOT_WORKFLOW_DIR = ROOT / ".github" / "workflows"
CLAUDE_PLUGIN_DIR = ROOT / ".claude-plugin"
CLAUDE_PLUGIN_MANIFEST = CLAUDE_PLUGIN_DIR / "plugin.json"
CLAUDE_MARKETPLACE = CLAUDE_PLUGIN_DIR / "marketplace.json"
STATE_TEMPLATE = SKILLS_DIR / "df-spec" / "templates" / "state-template.md"

sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "tools"))

from dark_factory.cli import KNOWN_COMMANDS  # noqa: E402
from dark_factory.yamlish import split_frontmatter  # noqa: E402

REQUIRED_SECTIONS = [
    "# ",
    "## Goal",
    "## Inputs",
    "## Preconditions",
    "## Workflow",
    "## Observability",
    "## Outputs",
    "## Rules",
    "## Handoff",
]

OBSERVABILITY_OPTIONAL_SKILLS = {
    "df-observability",
}

DELEGATION_REQUIRED_SKILLS = {
    "dark-factory",
    "df-wiki-init",
    "df-implement",
    "df-review",
    "df-evidence",
    "df-preflight",
    "df-merge",
}

STATE_SCHEMA_KEYS = {
    "ticket",
    "title",
    "branch",
    "status",
    "phase_detail",
    "risk",
    "auto_merge_eligible",
    "started",
    "last_updated",
    "repo_root",
    "working_root",
    "workspace_path",
    "workspace_isolated",
    "target_modules",
    "validation_commands",
    "module_scope_notes",
    "spec_path",
    "plan_path",
    "review_path",
    "evidence_path",
    "preflight_path",
    "pr_url",
    "pr_number",
    "merge_sha",
    "run_id",
    "observability_enabled",
}


def fail(message: str) -> None:
    print(f"ERROR: {message}", file=sys.stderr)


def parse_frontmatter(path: Path, text: str) -> tuple[dict[str, str], str]:
    if not text.startswith("---\n"):
        raise ValueError("missing opening frontmatter delimiter")

    end = text.find("\n---\n", 4)
    if end == -1:
        raise ValueError("missing closing frontmatter delimiter")

    fields: dict[str, str] = {}
    for line in text[4:end].splitlines():
        if not line.strip():
            continue
        if ":" not in line:
            raise ValueError(f"invalid frontmatter line: {line!r}")
        key, value = line.split(":", 1)
        fields[key.strip()] = value.strip()

    body = text[end + len("\n---\n") :]
    return fields, body


def section_position(body: str, section: str) -> int:
    if section == "# ":
        match = re.search(r"^# .+", body, re.MULTILINE)
    else:
        match = re.search(rf"^{re.escape(section)}\b", body, re.MULTILINE)
    return -1 if match is None else match.start()


def validate_links(skill_dir: Path, body: str) -> list[str]:
    errors: list[str] = []
    for target in re.findall(r"\[[^\]]+\]\(([^)]+)\)", body):
        if "://" in target or target.startswith("#"):
            continue

        relative_target = target.split("#", 1)[0]
        if not relative_target:
            continue

        path = (skill_dir / relative_target).resolve()
        try:
            path.relative_to(skill_dir.resolve())
        except ValueError:
            errors.append(f"link escapes skill directory: {target}")
            continue

        if not path.exists():
            errors.append(f"link target does not exist: {target}")

    return errors


def validate_skill(skill_dir: Path) -> list[str]:
    errors: list[str] = []
    path = skill_dir / "SKILL.md"
    if not path.exists():
        return [f"{skill_dir.name}: missing SKILL.md"]

    text = path.read_text(encoding="utf-8")
    try:
        frontmatter, body = parse_frontmatter(path, text)
    except ValueError as exc:
        return [f"{path.relative_to(ROOT)}: {exc}"]

    name = frontmatter.get("name")
    description = frontmatter.get("description", "")
    if name != skill_dir.name:
        errors.append(f"{path.relative_to(ROOT)}: name must be {skill_dir.name!r}")
    if "Use when" not in description:
        errors.append(f"{path.relative_to(ROOT)}: description must include 'Use when'")

    previous = -1
    for section in REQUIRED_SECTIONS:
        position = section_position(body, section)
        if position == -1:
            if section == "## Observability" and skill_dir.name in OBSERVABILITY_OPTIONAL_SKILLS:
                continue
            errors.append(f"{path.relative_to(ROOT)}: missing required section {section!r}")
            continue
        if position < previous:
            errors.append(f"{path.relative_to(ROOT)}: section {section!r} is out of order")
        previous = position

    for link_error in validate_links(skill_dir, body):
        errors.append(f"{path.relative_to(ROOT)}: {link_error}")

    for command in re.findall(r"`df\s+([a-z][a-z-]*)\b", body):
        if command not in KNOWN_COMMANDS:
            errors.append(
                f"{path.relative_to(ROOT)}: unknown df CLI command {command!r}"
            )

    if skill_dir.name in DELEGATION_REQUIRED_SKILLS:
        lowered = body.lower()
        if "subagent" not in lowered and "agent team" not in lowered:
            errors.append(
                f"{path.relative_to(ROOT)}: heavy-work skill must mention subagents or agent teams"
            )
        if "coordinator" not in lowered and "coordinate" not in lowered:
            errors.append(
                f"{path.relative_to(ROOT)}: heavy-work skill must describe coordinator behavior"
            )

    return errors


def validate_workflow_yaml() -> list[str]:
    errors: list[str] = []
    try:
        import yaml  # type: ignore[import-not-found]
    except ImportError:
        print("WARNING: PyYAML is not installed; skipping workflow YAML parse checks.")
        return errors

    workflow_paths = sorted(WORKFLOW_TEMPLATE_DIR.glob("*.yml"))
    if ROOT_WORKFLOW_DIR.exists():
        workflow_paths.extend(sorted(ROOT_WORKFLOW_DIR.glob("*.yml")))

    for workflow in workflow_paths:
        workflow_text = workflow.read_text(encoding="utf-8")
        if "Configure " in workflow_text and re.search(r"^\s*exit 1\s*$", workflow_text, re.MULTILINE):
            errors.append(
                f"{workflow.relative_to(ROOT)}: placeholder command block must not fail by default"
            )
        try:
            document = yaml.safe_load(workflow_text)
        except yaml.YAMLError as exc:
            errors.append(f"{workflow.relative_to(ROOT)}: invalid YAML: {exc}")
            continue

        if not isinstance(document, dict):
            errors.append(f"{workflow.relative_to(ROOT)}: workflow must be a mapping")
            continue

        # PyYAML's YAML 1.1 resolver treats the key "on" as boolean True.
        if "on" not in document and True not in document:
            errors.append(f"{workflow.relative_to(ROOT)}: missing 'on' trigger")
        if "jobs" not in document:
            errors.append(f"{workflow.relative_to(ROOT)}: missing jobs")

    return errors


def parse_state_template_keys() -> set[str]:
    if not STATE_TEMPLATE.exists():
        return set()
    frontmatter, _ = split_frontmatter(STATE_TEMPLATE.read_text(encoding="utf-8"))
    return set(frontmatter.keys())


def validate_state_template() -> list[str]:
    errors: list[str] = []
    keys = parse_state_template_keys()
    if not keys:
        return [f"{STATE_TEMPLATE.relative_to(ROOT)}: missing or invalid state frontmatter"]
    missing = sorted(STATE_SCHEMA_KEYS - keys)
    extra = sorted(keys - STATE_SCHEMA_KEYS)
    if missing:
        errors.append(
            f"{STATE_TEMPLATE.relative_to(ROOT)}: missing required state keys: {', '.join(missing)}"
        )
    if extra:
        errors.append(
            f"{STATE_TEMPLATE.relative_to(ROOT)}: unexpected state keys: {', '.join(extra)}"
        )

    referenced = set()
    for skill in SKILLS_DIR.glob("*/SKILL.md"):
        body = skill.read_text(encoding="utf-8")
        referenced.update(re.findall(r"`(?:df state (?:get|set) <TICKET-ID> )?([a-z][a-z0-9_]+)`", body))
    stale = sorted(key for key in referenced if key.endswith("_path") and key not in keys)
    if stale:
        errors.append(
            f"{STATE_TEMPLATE.relative_to(ROOT)}: stale state key references: {', '.join(stale)}"
        )
    return errors


def load_json(path: Path) -> tuple[dict[str, object] | None, str | None]:
    if not path.exists():
        return None, "missing file"

    try:
        document = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        return None, f"invalid JSON: {exc}"

    if not isinstance(document, dict):
        return None, "JSON document must be an object"

    return document, None


def validate_claude_plugin() -> list[str]:
    errors: list[str] = []

    manifest, manifest_error = load_json(CLAUDE_PLUGIN_MANIFEST)
    if manifest_error:
        errors.append(f"{CLAUDE_PLUGIN_MANIFEST.relative_to(ROOT)}: {manifest_error}")
        return errors

    marketplace, marketplace_error = load_json(CLAUDE_MARKETPLACE)
    if marketplace_error:
        errors.append(f"{CLAUDE_MARKETPLACE.relative_to(ROOT)}: {marketplace_error}")
        return errors

    manifest_name = manifest.get("name") if manifest else None
    marketplace_name = marketplace.get("name") if marketplace else None
    plugins = marketplace.get("plugins") if marketplace else None

    if not isinstance(manifest_name, str) or not manifest_name:
        errors.append(f"{CLAUDE_PLUGIN_MANIFEST.relative_to(ROOT)}: missing name")
    if not isinstance(marketplace_name, str) or not marketplace_name:
        errors.append(f"{CLAUDE_MARKETPLACE.relative_to(ROOT)}: missing name")
    elif manifest_name != marketplace_name:
        errors.append(
            f"{CLAUDE_MARKETPLACE.relative_to(ROOT)}: marketplace name must match "
            f"plugin manifest name {manifest_name!r}"
        )

    if not isinstance(plugins, list) or not plugins:
        errors.append(f"{CLAUDE_MARKETPLACE.relative_to(ROOT)}: plugins must be a non-empty array")
        return errors

    matching_entry: dict[str, object] | None = None
    for plugin in plugins:
        if not isinstance(plugin, dict):
            errors.append(f"{CLAUDE_MARKETPLACE.relative_to(ROOT)}: plugin entries must be objects")
            continue
        if plugin.get("name") == manifest_name:
            matching_entry = plugin

    if matching_entry is None:
        errors.append(
            f"{CLAUDE_MARKETPLACE.relative_to(ROOT)}: missing plugin entry named {manifest_name!r}"
        )
        return errors

    source = matching_entry.get("source")
    if not isinstance(source, str) or not source:
        errors.append(
            f"{CLAUDE_MARKETPLACE.relative_to(ROOT)}: plugin {manifest_name!r} "
            "must have a string source"
        )
        return errors

    source_path = (ROOT / source).resolve()
    try:
        source_path.relative_to(ROOT.resolve())
    except ValueError:
        errors.append(
            f"{CLAUDE_MARKETPLACE.relative_to(ROOT)}: plugin source escapes repository: {source}"
        )
        return errors

    if not source_path.is_dir():
        errors.append(
            f"{CLAUDE_MARKETPLACE.relative_to(ROOT)}: plugin source does not exist: {source}"
        )

    return errors


def main() -> int:
    errors: list[str] = []

    for skill_dir in sorted(path for path in SKILLS_DIR.iterdir() if path.is_dir()):
        errors.extend(validate_skill(skill_dir))

    errors.extend(validate_state_template())
    errors.extend(validate_workflow_yaml())
    errors.extend(validate_claude_plugin())

    for error in errors:
        fail(error)

    if errors:
        return 1

    print("Dark Factory skill pack validation passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
