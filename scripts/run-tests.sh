#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

python3 "$ROOT/scripts/validate_skill_pack.py"
bash "$ROOT/scripts/smoke_install.sh"
if python3 -c 'import pytest' >/dev/null 2>&1; then
  PYTHONPATH="$ROOT/tools:$ROOT${PYTHONPATH:+:$PYTHONPATH}" python3 -m pytest "$ROOT/tools/dark_factory/tests"
else
  PYTHONPATH="$ROOT/tools:$ROOT${PYTHONPATH:+:$PYTHONPATH}" python3 -m unittest discover -s "$ROOT/tools/dark_factory/tests"
fi

echo "All Dark Factory tests passed."
