from __future__ import annotations

import argparse
import fnmatch
import json
import re
from pathlib import Path

from .utils import DarkFactoryError, repo_root, run


HIGH_PATTERNS = [
    r"(^|/)migrations/",
    r"\.sql$",
    r"(^|/)(infra|terraform|k8s|helm)/",
    r"(^|/)Dockerfile$",
    r"(^|/)docker-compose\.ya?ml$",
    r"^\.github/workflows/",
    r"(^|/)(auth|security|crypto)/",
    r"(secret|secrets|secret-manager)",
    r"(openapi\.ya?ml|openapi\.json|\.proto$|schema\.graphql$)",
    r"(^|/)(billing|payments|pii)/",
]


MEDIUM_PATTERNS = [
    r"(^|/)packages/.+/(src|lib)/",
    r"(^|/)libs?/",
    r"(^|/)shared/",
]


def changed_files(root: Path, base_ref: str) -> list[str]:
    proc = run(["git", "diff", "--name-only", f"{base_ref}...HEAD"], cwd=root)
    if proc.returncode != 0:
        proc = run(["git", "diff", "--name-only", base_ref], cwd=root)
    if proc.returncode != 0:
        raise DarkFactoryError(proc.stderr.strip() or "could not read changed files")
    return [line.strip() for line in proc.stdout.splitlines() if line.strip()]


def codeowner_patterns(root: Path) -> list[str]:
    path = root / ".github" / "CODEOWNERS"
    if not path.exists():
        return []
    patterns: list[str] = []
    for line in path.read_text(encoding="utf-8").splitlines():
        stripped = line.strip()
        if not stripped or stripped.startswith("#"):
            continue
        parts = stripped.split()
        if len(parts) >= 2:
            patterns.append(parts[0])
    return patterns


def codeowner_matches(path: str, patterns: list[str]) -> bool:
    for pattern in patterns:
        normalized = pattern.lstrip("/")
        if normalized.endswith("/"):
            if path.startswith(normalized):
                return True
        elif fnmatch.fnmatch(path, normalized) or fnmatch.fnmatch(path, f"**/{normalized}"):
            return True
    return False


def classify_paths(paths: list[str], owner_patterns: list[str]) -> tuple[str, list[str]]:
    reasons: list[str] = []
    risk = "low"
    for path in paths:
        for pattern in HIGH_PATTERNS:
            if re.search(pattern, path, re.IGNORECASE):
                reasons.append(f"high:{path}:{pattern}")
                risk = "high"
    if risk == "high":
        return risk, reasons

    for path in paths:
        if codeowner_matches(path, owner_patterns):
            reasons.append(f"medium:{path}:CODEOWNERS")
            risk = "medium"
        for pattern in MEDIUM_PATTERNS:
            if re.search(pattern, path, re.IGNORECASE):
                reasons.append(f"medium:{path}:{pattern}")
                risk = "medium"
    if not reasons:
        reasons.append("low:no high or medium risk path triggers")
    return risk, reasons


def classify_risk(args: argparse.Namespace) -> int:
    root = repo_root()
    paths = changed_files(root, args.diff_base)
    risk, reasons = classify_paths(paths, codeowner_patterns(root))
    result = {
        "risk": risk,
        "auto_merge_eligible": bool(risk == "low" and args.tests_cover_acceptance_criteria),
        "reasons": reasons,
        "changed_files": paths,
    }
    print(json.dumps(result, indent=2))
    return 0


def add_parser(subparsers) -> None:
    parser = subparsers.add_parser("classify-risk", help="Classify change risk from changed paths")
    parser.add_argument("--diff-base", default="origin/main")
    parser.add_argument(
        "--tests-cover-acceptance-criteria",
        action="store_true",
        help="Allow auto_merge_eligible when path risk is low",
    )
    parser.set_defaults(func=classify_risk)
