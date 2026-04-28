#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
TMP_DIR="$(mktemp -d)"
trap 'rm -rf "$TMP_DIR"' EXIT

SOURCE="$TMP_DIR/source"
TARGET="$TMP_DIR/target"

mkdir -p "$SOURCE" "$TARGET"
cp -R "$ROOT/install.sh" "$ROOT/skills" "$ROOT/docs" "$ROOT/README.md" "$SOURCE/"

skill_count="$(find "$SOURCE/skills" -mindepth 1 -maxdepth 1 -type d | wc -l | tr -d '[:space:]')"

first_output="$(bash "$SOURCE/install.sh" "$TARGET")"
printf '%s\n' "$first_output"
if ! printf '%s\n' "$first_output" | grep -q "installed ${skill_count} skill(s), skipped 0 unchanged skill(s)"; then
  echo "Initial install did not copy every skill." >&2
  exit 1
fi

second_output="$(bash "$SOURCE/install.sh" "$TARGET")"
printf '%s\n' "$second_output"
if ! printf '%s\n' "$second_output" | grep -q "installed 0 skill(s), skipped ${skill_count} unchanged skill(s)"; then
  echo "Second install was not idempotent." >&2
  exit 1
fi

marker="smoke-test-marker"
printf '\n<!-- %s -->\n' "$marker" >> "$SOURCE/skills/df-clarify/SKILL.md"

third_output="$(bash "$SOURCE/install.sh" "$TARGET")"
printf '%s\n' "$third_output"
if ! printf '%s\n' "$third_output" | grep -q "installed 1 skill(s), skipped $((skill_count - 1)) unchanged skill(s)"; then
  echo "Changed skill was not reinstalled selectively." >&2
  exit 1
fi

if ! grep -q "$marker" "$TARGET/.agents/skills/df-clarify/SKILL.md"; then
  echo "Changed skill content did not reach the target install." >&2
  exit 1
fi

test -f "$TARGET/.agents/skills/.dark-factory-version"

echo "Dark Factory installer smoke test passed."
