#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
TMP_DIR="$(mktemp -d)"
trap 'rm -rf "$TMP_DIR"' EXIT

target="$TMP_DIR/target"
mkdir -p "$target"
git -C "$target" init -q

bash "$ROOT/install.sh" --target "$target" --dry-run >/tmp/dark-factory-dry-run.log
if [[ -d "$target/.agents" ]]; then
  echo "dry run created .agents" >&2
  exit 1
fi

bash "$ROOT/install.sh" --target "$target" >/tmp/dark-factory-install.log
test -d "$target/.agents/skills/dark-factory"
test -d "$target/.agents/skills/df-preflight"
test -f "$target/.agents/skills/.dark-factory-version"

bash "$ROOT/install.sh" --target "$target" >/tmp/dark-factory-reinstall.log
grep -q "Skipping unchanged skill: dark-factory" /tmp/dark-factory-reinstall.log

plain="$TMP_DIR/plain"
mkdir -p "$plain"
if bash "$ROOT/install.sh" --target "$plain" >/tmp/dark-factory-refuse.log 2>&1; then
  echo "install accepted target without markers" >&2
  exit 1
fi

bash "$ROOT/install.sh" --target "$plain" --force >/tmp/dark-factory-force.log
test -d "$plain/.agents/skills/dark-factory"

echo "smoke_install passed"
