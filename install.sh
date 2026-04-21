#!/bin/bash
set -euo pipefail

usage() {
  cat <<'EOF'
Usage: install.sh [--with-github] [TARGET]

Installs Dark Factory skills into TARGET/.agents/skills/.

Options:
  --with-github   After install, print the follow-up command to scaffold the
                  GitHub-side automation via the df-github-init skill.

Arguments:
  TARGET          Path to the target project (defaults to the current directory).

Behavior:
  - Idempotent. A skill is only re-copied if its content hash changed since
    the last install.
  - Writes .agents/skills/.dark-factory-version with the source repo HEAD SHA.
  - Writes .agents/skills/.<skill-name>.sha for per-skill change detection.
EOF
}

WITH_GITHUB=0
TARGET=""

while (($#)); do
  case "$1" in
    --with-github)
      WITH_GITHUB=1
      shift
      ;;
    -h|--help)
      usage
      exit 0
      ;;
    --)
      shift
      TARGET="${1:-}"
      break
      ;;
    -*)
      echo "Unknown option: $1" >&2
      usage >&2
      exit 2
      ;;
    *)
      if [[ -z "$TARGET" ]]; then
        TARGET="$1"
        shift
      else
        echo "Unexpected argument: $1" >&2
        usage >&2
        exit 2
      fi
      ;;
  esac
done

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
TARGET="${TARGET:-$PWD}"

if [[ ! -d "$TARGET" ]]; then
  echo "Target directory does not exist: $TARGET" >&2
  exit 1
fi

DEST="$TARGET/.agents/skills"
mkdir -p "$DEST"

if command -v shasum >/dev/null 2>&1; then
  HASH_CMD=(shasum -a 256)
elif command -v sha256sum >/dev/null 2>&1; then
  HASH_CMD=(sha256sum)
else
  echo "Need either shasum or sha256sum on PATH" >&2
  exit 1
fi

skill_hash() {
  local dir="$1"
  (cd "$dir" && find . -type f -print0 \
    | LC_ALL=C sort -z \
    | xargs -0 "${HASH_CMD[@]}" \
    | "${HASH_CMD[@]}" \
    | awk '{print $1}')
}

INSTALLED=0
SKIPPED=0

for skill_dir in "$SCRIPT_DIR"/skills/*; do
  [[ -d "$skill_dir" ]] || continue
  skill_name="$(basename "$skill_dir")"
  new_sha="$(skill_hash "$skill_dir")"
  sha_file="$DEST/.${skill_name}.sha"

  if [[ -f "$sha_file" && -d "$DEST/$skill_name" ]]; then
    old_sha="$(cat "$sha_file")"
    if [[ "$old_sha" == "$new_sha" ]]; then
      SKIPPED=$((SKIPPED + 1))
      continue
    fi
  fi

  rm -rf "$DEST/$skill_name"
  cp -R "$skill_dir" "$DEST/$skill_name"
  printf '%s\n' "$new_sha" > "$sha_file"
  INSTALLED=$((INSTALLED + 1))
done

if git -C "$SCRIPT_DIR" rev-parse HEAD >/dev/null 2>&1; then
  SOURCE_SHA="$(git -C "$SCRIPT_DIR" rev-parse HEAD)"
else
  SOURCE_SHA="unknown"
fi

cat > "$DEST/.dark-factory-version" <<EOF
source_repo: $SCRIPT_DIR
source_sha: $SOURCE_SHA
installed_at: $(date -u +%Y-%m-%dT%H:%M:%SZ)
EOF

echo "Dark Factory: installed $INSTALLED skill(s), skipped $SKIPPED unchanged skill(s) at $DEST"

if (( WITH_GITHUB == 1 )); then
  cat <<EOF

Next step:
  Run df-github-init in the target repo to scaffold .github/ automation:

    cd "$TARGET"
    # then in your agent:
    Use df-github-init to set up PR workflows, CODEOWNERS, and Copilot instructions.
EOF
fi
