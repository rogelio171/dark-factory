from __future__ import annotations

import re
from collections.abc import Mapping

_UNESCAPE_RE = re.compile(r'\\(["\\n])')
_UNESCAPE_MAP = {'"': '"', "\\": "\\", "n": "\n"}


def parse_scalar(value: str):
    value = value.strip()
    if value in {"true", "false"}:
        return value == "true"
    if value in {'""', "''"}:
        return ""
    if len(value) >= 2 and value[0] == value[-1] == '"':
        inner = value[1:-1]
        return _UNESCAPE_RE.sub(lambda match: _UNESCAPE_MAP[match.group(1)], inner)
    if len(value) >= 2 and value[0] == value[-1] == "'":
        return value[1:-1]
    return value


def parse_simple_yaml(text: str) -> dict:
    result: dict = {}
    lines = text.splitlines()
    index = 0
    while index < len(lines):
        line = lines[index]
        if not line.strip() or line.lstrip().startswith("#"):
            index += 1
            continue
        if line.startswith(" ") or ":" not in line:
            index += 1
            continue
        key, value = line.split(":", 1)
        key = key.strip()
        value = value.strip()
        if value:
            result[key] = parse_scalar(value)
            index += 1
            continue

        nested: list[str] = []
        index += 1
        while index < len(lines) and (
            not lines[index].strip() or lines[index].startswith(" ")
        ):
            nested.append(lines[index])
            index += 1

        useful = [item for item in nested if item.strip()]
        if not useful:
            result[key] = ""
        elif all(item.strip().startswith("- ") for item in useful):
            result[key] = [parse_scalar(item.strip()[2:]) for item in useful]
        else:
            mapping: dict[str, object] = {}
            for item in useful:
                stripped = item.strip()
                if ":" not in stripped:
                    continue
                child_key, child_value = stripped.split(":", 1)
                mapping[child_key.strip()] = parse_scalar(child_value.strip())
            result[key] = mapping
    return result


def split_frontmatter(text: str) -> tuple[dict, str]:
    if not text.startswith("---\n"):
        return {}, text
    end = text.find("\n---\n", 4)
    if end == -1:
        return {}, text
    frontmatter = parse_simple_yaml(text[4:end])
    body = text[end + len("\n---\n") :]
    return frontmatter, body


def format_scalar(value: object) -> str:
    if value is True:
        return "true"
    if value is False:
        return "false"
    if value is None:
        return '""'
    text = str(value)
    if text == "":
        return '""'
    needs_quoting = (
        any(char in text for char in [":", "#", "\n", '"', "\\"])
        or text.strip() != text
        or text in {"true", "false"}
        or (text[0] == text[-1] == "'" and len(text) >= 2)
    )
    if needs_quoting:
        escaped = text.replace("\\", "\\\\").replace('"', '\\"').replace("\n", "\\n")
        return '"' + escaped + '"'
    return text


def dump_simple_yaml(data: Mapping[str, object], key_order: list[str] | None = None) -> str:
    keys = list(key_order or [])
    keys.extend(key for key in data.keys() if key not in keys)
    lines: list[str] = []
    for key in keys:
        if key not in data:
            continue
        value = data[key]
        if isinstance(value, list):
            lines.append(f"{key}:")
            if value:
                lines.extend(f"  - {format_scalar(item)}" for item in value)
            continue
        if isinstance(value, dict):
            lines.append(f"{key}:")
            for child_key, child_value in value.items():
                lines.append(f"  {child_key}: {format_scalar(child_value)}")
            continue
        lines.append(f"{key}: {format_scalar(value)}")
    return "\n".join(lines) + "\n"


def replace_frontmatter(text: str, data: Mapping[str, object], key_order: list[str]) -> str:
    _, body = split_frontmatter(text)
    return "---\n" + dump_simple_yaml(data, key_order) + "---\n" + body
