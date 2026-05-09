#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

python3 "$ROOT/scripts/validate_skill_pack.py"
bash "$ROOT/scripts/smoke_install.sh"
bash "$ROOT/tests/smoke_install.sh"

echo "All Dark Factory tests passed."
