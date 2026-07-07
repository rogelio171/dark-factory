from __future__ import annotations

import hashlib
import re
from pathlib import Path

from .config import ObservabilityConfig, load_config

SECRET_PATTERNS = [
    r"(?i)(api[_-]?key|secret|token|password|authorization)\s*[:=]\s*\S+",
    r"(?i)Bearer\s+[A-Za-z0-9\-._~+/]+=*",
    r"-----BEGIN [A-Z ]+ PRIVATE KEY-----[\s\S]*?-----END [A-Z ]+ PRIVATE KEY-----",
    r"(?i)gho_[A-Za-z0-9]{20,}",
    r"(?i)ghp_[A-Za-z0-9]{20,}",
    r"(?i)ghu_[A-Za-z0-9]{20,}",
    r"(?i)ghs_[A-Za-z0-9]{20,}",
    r"(?i)ghr_[A-Za-z0-9]{20,}",
    r"(?i)sk-[A-Za-z0-9]{20,}",
    r"(?i)AKIA[0-9A-Z]{16}",
]

# Broad email/phone matching mangles ordinary tool output (any ten-digit
# number looks like a phone), so contact-info redaction only applies when
# compliance.strict_pii is enabled.
CONTACT_PATTERNS = [
    r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b",
    r"\b\d{3}[-.\s]?\d{3}[-.\s]?\d{4}\b",
]

REDACTED = "[REDACTED]"

_pattern_cache: dict[tuple[bool, str, int], list[re.Pattern[str]]] = {}


def _load_patterns(config: ObservabilityConfig, root: Path | None) -> list[re.Pattern[str]]:
    path = Path(config.redaction.patterns_file)
    if not path.is_absolute() and root is not None:
        path = root / config.redaction.patterns_file
    strict_pii = bool(config.compliance.strict_pii)
    mtime = path.stat().st_mtime_ns if path.exists() else -1
    key = (strict_pii, str(path), mtime)
    cached = _pattern_cache.get(key)
    if cached is not None:
        return cached

    patterns = [re.compile(pattern) for pattern in SECRET_PATTERNS]
    if strict_pii:
        patterns.extend(re.compile(pattern) for pattern in CONTACT_PATTERNS)
    if mtime != -1:
        for line in path.read_text(encoding="utf-8").splitlines():
            stripped = line.strip()
            if stripped and not stripped.startswith("#"):
                patterns.append(re.compile(stripped))
    _pattern_cache.clear()
    _pattern_cache[key] = patterns
    return patterns


def redact_text(text: str, config: ObservabilityConfig | None = None, root: Path | None = None) -> str:
    if not text:
        return text
    config = config or load_config(root)
    if not config.redaction.enabled:
        return text
    result = text
    for pattern in _load_patterns(config, root):
        result = pattern.sub(REDACTED, result)
    max_bytes = config.redaction.max_content_bytes
    encoded = result.encode("utf-8")
    if len(encoded) > max_bytes:
        truncated = encoded[:max_bytes].decode("utf-8", errors="ignore")
        result = truncated + "\n[TRUNCATED]"
    return result


def content_hash(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()
