#!/bin/bash
set -euo pipefail

usage() {
  cat <<'EOF'
Usage: install.sh [--with-github] [--runtime cursor|claude|generic] [--target PATH] [--dry-run] [--force] [PATH]

Installs Dark Factory skills into PATH/.agents/skills/.

Options:
  --target PATH   Target project directory.
  --dry-run       Show what would change without writing files.
  --force         Allow suspicious targets without project markers.
  --runtime NAME  Runtime surface to validate in df doctor. One of:
                  cursor, claude, generic. Defaults to generic.
  --with-github   After install, print the follow-up command to scaffold the
                  GitHub-side automation via the df-github-init skill.
  -h, --help      Show this help.

Arguments:
  PATH            Target project directory (defaults to the current directory).

Behavior:
  - Refuses /, $HOME, and targets without project markers unless --force is set.
  - Idempotent. A skill is only re-copied if its content hash changed since
    the last install.
  - Replaces changed skills atomically instead of deleting in place.
  - Writes .agents/skills/.dark-factory-version with the source repo HEAD SHA.
  - Writes .agents/skills/.<skill-name>.sha for per-skill change detection.
EOF
}

WITH_GITHUB=0
DRY_RUN=0
FORCE=0
RUNTIME="generic"
TARGET=""

while (($#)); do
  case "$1" in
    --with-github)
      WITH_GITHUB=1
      shift
      ;;
    --target)
      [[ $# -ge 2 ]] || { echo "--target requires a path" >&2; exit 2; }
      TARGET="$2"
      shift 2
      ;;
    --dry-run)
      DRY_RUN=1
      shift
      ;;
    --force)
      FORCE=1
      shift
      ;;
    --runtime)
      [[ $# -ge 2 ]] || { echo "--runtime requires cursor, claude, or generic" >&2; exit 2; }
      case "$2" in
        cursor|claude|generic)
          RUNTIME="$2"
          ;;
        *)
          echo "Invalid runtime: $2" >&2
          usage >&2
          exit 2
          ;;
      esac
      shift 2
      ;;
    -h|--help)
      usage
      exit 0
      ;;
    --)
      shift
      if [[ $# -gt 0 ]]; then
        [[ -z "$TARGET" ]] || { echo "Target specified more than once" >&2; exit 2; }
        TARGET="$1"
      fi
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

TARGET="$(cd "$TARGET" && pwd -P)"
DEST="$TARGET/.agents/skills"
DEST_BIN="$TARGET/.agents/bin"
DEST_LIB="$TARGET/.agents/lib"

has_project_marker() {
  [[ -d "$TARGET/.git" ]] ||
  [[ -f "$TARGET/package.json" ]] ||
  [[ -f "$TARGET/pyproject.toml" ]] ||
  [[ -f "$TARGET/go.mod" ]] ||
  [[ -f "$TARGET/Cargo.toml" ]] ||
  [[ -f "$TARGET/pnpm-workspace.yaml" ]] ||
  [[ -f "$TARGET/turbo.json" ]] ||
  [[ -f "$TARGET/nx.json" ]] ||
  [[ -d "$TARGET/.cursor" ]]
}

if [[ "$FORCE" -ne 1 ]]; then
  if [[ "$TARGET" == "/" || "$TARGET" == "$HOME" ]]; then
    echo "Refusing suspicious target without --force: $TARGET" >&2
    exit 1
  fi
  if ! has_project_marker; then
    echo "Refusing target without project markers. Use --force if this is intentional: $TARGET" >&2
    exit 1
  fi
fi

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

echo "Dark Factory install target: $TARGET"
echo "Skills destination: $DEST"
echo "Runtime: $RUNTIME"
if [[ "$DRY_RUN" -eq 1 ]]; then
  echo "Dry run: no files will be changed."
else
  mkdir -p "$DEST"
  mkdir -p "$DEST_BIN" "$DEST_LIB"
fi

INSTALLED=0
SKIPPED=0

for skill_dir in "$SCRIPT_DIR"/skills/*; do
  [[ -d "$skill_dir" ]] || continue
  skill_name="$(basename "$skill_dir")"
  new_sha="$(skill_hash "$skill_dir")"
  sha_file="$DEST/.${skill_name}.sha"

  if [[ -f "$sha_file" && -d "$DEST/$skill_name" ]]; then
    old_sha="$(< "$sha_file")"
    if [[ "$old_sha" == "$new_sha" ]]; then
      echo "Skipping unchanged skill: $skill_name"
      SKIPPED=$((SKIPPED + 1))
      continue
    fi
  fi

  if [[ "$DRY_RUN" -eq 1 ]]; then
    echo "Would install skill: $skill_name"
    INSTALLED=$((INSTALLED + 1))
    continue
  fi

  tmp_dir="$DEST/.${skill_name}.tmp.$$"
  old_dir="$DEST/.${skill_name}.old.$$"
  rm -rf "$tmp_dir" "$old_dir"
  cp -R "$skill_dir" "$tmp_dir"
  if [[ -d "$DEST/$skill_name" ]]; then
    mv "$DEST/$skill_name" "$old_dir"
  fi
  mv "$tmp_dir" "$DEST/$skill_name"
  rm -rf "$old_dir"
  printf '%s\n' "$new_sha" > "$sha_file"
  echo "Installed skill: $skill_name"
  INSTALLED=$((INSTALLED + 1))
done

if [[ "$DRY_RUN" -eq 1 ]]; then
  echo "Would install df CLI: $DEST_BIN/df"
  echo "Would install Python package: $DEST_LIB/dark_factory"
else
  if [[ ! -f "$SCRIPT_DIR/bin/df" || ! -d "$SCRIPT_DIR/tools/dark_factory" ]]; then
    echo "Missing Dark Factory CLI source (bin/df or tools/dark_factory)" >&2
    exit 1
  fi
  cp "$SCRIPT_DIR/bin/df" "$DEST_BIN/df"
  chmod +x "$DEST_BIN/df"
  tmp_lib="$DEST_LIB/.dark_factory.tmp.$$"
  old_lib="$DEST_LIB/.dark_factory.old.$$"
  rm -rf "$tmp_lib" "$old_lib"
  cp -R "$SCRIPT_DIR/tools/dark_factory" "$tmp_lib"
  if [[ -d "$DEST_LIB/dark_factory" ]]; then
    mv "$DEST_LIB/dark_factory" "$old_lib"
  fi
  mv "$tmp_lib" "$DEST_LIB/dark_factory"
  rm -rf "$old_lib"
  echo "Installed df CLI: $DEST_BIN/df"
fi

if git -C "$SCRIPT_DIR" rev-parse HEAD >/dev/null 2>&1; then
  SOURCE_SHA="$(git -C "$SCRIPT_DIR" rev-parse HEAD)"
else
  SOURCE_SHA="unknown"
fi

if [[ "$DRY_RUN" -ne 1 ]]; then
  cat > "$DEST/.dark-factory-version" <<EOF
source_repo: $SCRIPT_DIR
source_sha: $SOURCE_SHA
installed_at: $(date -u +%Y-%m-%dT%H:%M:%SZ)
target: $TARGET
runtime: $RUNTIME
EOF
fi

echo "Dark Factory: installed $INSTALLED skill(s), skipped $SKIPPED unchanged skill(s) at $DEST"
echo "Dark Factory CLI: $DEST_BIN/df"

if (( WITH_GITHUB == 1 )); then
  cat <<EOF

Next step:
  Run df-github-init in the target repo to scaffold .github/ automation:

    cd "$TARGET"
    # then in your agent:
    Use df-github-init to set up PR workflows, CODEOWNERS, and Copilot instructions.
EOF
fi
