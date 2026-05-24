#!/usr/bin/env bash
set -euo pipefail

# Read JSONL from stdin or a file argument and ingest via df observability batch.
TARGET="${DF_TARGET:-.}"
FILE="${1:-}"

if [[ -n "$FILE" ]]; then
  exec "$TARGET/.agents/bin/df" observability batch --file "$FILE"
fi

TMP="$(mktemp)"
trap 'rm -f "$TMP"' EXIT
cat >"$TMP"
exec "$TARGET/.agents/bin/df" observability batch --file "$TMP"
