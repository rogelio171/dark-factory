#!/bin/bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
TARGET="${1:-$PWD}"
DEST="$TARGET/.agents/skills"

mkdir -p "$DEST"

for skill_dir in "$SCRIPT_DIR"/skills/*; do
  skill_name="$(basename "$skill_dir")"
  rm -rf "$DEST/$skill_name"
  cp -R "$skill_dir" "$DEST/$skill_name"
done

echo "Installed Dark Factory skills to $DEST"
