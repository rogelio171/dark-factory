from __future__ import annotations

import json
import re
from dataclasses import dataclass, field
from pathlib import Path

from .db import config_path, observability_dir


@dataclass
class RetentionConfig:
    default_days: int = 365
    agent_messages_days: int = 365
    interaction_events_days: int = 365
    external_snapshots_days: int = 365
    prune_schedule: str = "weekly"


@dataclass
class RedactionConfig:
    enabled: bool = True
    patterns_file: str = ".agents/dark-factory/redaction-patterns.txt"
    max_content_bytes: int = 1_048_576


@dataclass
class ExportConfig:
    default_format: str = "jsonl"
    include_agent_messages: bool = True
    include_snapshots: bool = True


@dataclass
class RuntimeConfig:
    detect_from_env: bool = True


@dataclass
class ComplianceConfig:
    append_only: bool = True
    record_cli_commands: bool = True
    record_git_operations: bool = True
    strict_pii: bool = False


@dataclass
class ObservabilityConfig:
    retention: RetentionConfig = field(default_factory=RetentionConfig)
    redaction: RedactionConfig = field(default_factory=RedactionConfig)
    export: ExportConfig = field(default_factory=ExportConfig)
    runtime: RuntimeConfig = field(default_factory=RuntimeConfig)
    compliance: ComplianceConfig = field(default_factory=ComplianceConfig)


_SECTION_RE = re.compile(r"^\[([a-z_]+)\]$")
_KV_RE = re.compile(r"^([a-z_]+)\s*=\s*(.+)$")


def _parse_toml_value(raw: str) -> object:
    value = raw.strip()
    if value in {"true", "false"}:
        return value == "true"
    if value.startswith('"') and value.endswith('"'):
        return value[1:-1]
    if re.fullmatch(r"-?\d+", value):
        return int(value)
    return value


def parse_toml(text: str) -> dict[str, dict[str, object]]:
    sections: dict[str, dict[str, object]] = {}
    current = "default"
    sections[current] = {}
    for line in text.splitlines():
        stripped = line.strip()
        if not stripped or stripped.startswith("#"):
            continue
        section_match = _SECTION_RE.match(stripped)
        if section_match:
            current = section_match.group(1)
            sections.setdefault(current, {})
            continue
        kv_match = _KV_RE.match(stripped)
        if kv_match:
            sections.setdefault(current, {})[kv_match.group(1)] = _parse_toml_value(kv_match.group(2))
    return sections


def _apply_section(config: ObservabilityConfig, name: str, values: dict[str, object]) -> None:
    target = getattr(config, name, None)
    if target is None:
        return
    for key, value in values.items():
        if hasattr(target, key):
            setattr(target, key, value)


def load_config(root: Path | None = None) -> ObservabilityConfig:
    path = config_path(root)
    config = ObservabilityConfig()
    if not path.exists():
        return config
    sections = parse_toml(path.read_text(encoding="utf-8"))
    for name, values in sections.items():
        if name == "default":
            continue
        _apply_section(config, name, values)
    return config


def save_default_config(root: Path | None = None) -> Path:
    directory = observability_dir(root)
    directory.mkdir(parents=True, exist_ok=True)
    template = Path(__file__).resolve().parent / "templates" / "observability.toml"
    destination = config_path(root)
    if not destination.exists():
        destination.write_text(template.read_text(encoding="utf-8"), encoding="utf-8")
    patterns_template = Path(__file__).resolve().parent / "templates" / "redaction-patterns.txt"
    patterns_dest = directory / "redaction-patterns.txt"
    if not patterns_dest.exists():
        patterns_dest.write_text(patterns_template.read_text(encoding="utf-8"), encoding="utf-8")
    exports_dir = directory / "exports"
    exports_dir.mkdir(parents=True, exist_ok=True)
    return destination


def config_as_json(config: ObservabilityConfig) -> str:
    return json.dumps(
        {
            "retention": config.retention.__dict__,
            "redaction": config.redaction.__dict__,
            "export": config.export.__dict__,
            "runtime": config.runtime.__dict__,
            "compliance": config.compliance.__dict__,
        },
        indent=2,
    )
