#!/usr/bin/env bash
# Sync the devmachine-skills reference copies from the devmachine CLI's own
# docs/ tree, rewriting relative Markdown links along the way.
#
# Usage:
#   sync-skill-references.sh <path-to-cli-docs> [--check]
#
# <path-to-cli-docs> is a checkout of the devmachine-cli repo's docs/
# directory (the directory that directly contains commands.md's parent
# "reference/", "concepts/", "troubleshooting.md", and so on).
#
# --check compares the generated output against what is committed under
# each skill's references/ directory and exits non-zero if anything
# differs. It never writes to the working tree.
set -euo pipefail

usage() {
  echo "usage: $(basename "$0") <path-to-cli-docs> [--check]" >&2
  exit 1
}

DOCS_DIR=""
CHECK=0

for arg in "$@"; do
  case "$arg" in
    --check)
      CHECK=1
      ;;
    -h|--help)
      usage
      ;;
    *)
      if [[ -n "$DOCS_DIR" ]]; then
        usage
      fi
      DOCS_DIR="$arg"
      ;;
  esac
done

[[ -n "$DOCS_DIR" ]] || usage
[[ -d "$DOCS_DIR" ]] || { echo "error: not a directory: $DOCS_DIR" >&2; exit 1; }

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SKILLS_ROOT="$(cd "$SCRIPT_DIR/../packages/devmachine-skills" && pwd)"
DOCS_DIR="$(cd "$DOCS_DIR" && pwd)"

WORK_DIR="$(mktemp -d)"
trap 'rm -rf "$WORK_DIR"' EXIT

python3 "$SCRIPT_DIR/lib/render_references.py" "$DOCS_DIR" "$WORK_DIR"

STATUS=0

sync_skill() {
  local skill_dest="$1"
  local generated="$WORK_DIR/$2"
  local target="$SKILLS_ROOT/$skill_dest/references"

  if [[ "$CHECK" -eq 1 ]]; then
    if [[ ! -d "$target" ]]; then
      echo "MISSING: $target does not exist" >&2
      STATUS=1
      return
    fi
    if ! diff -rq "$generated" "$target" >"$WORK_DIR/diff-$2.txt"; then
      echo "OUT OF DATE: $skill_dest/references" >&2
      cat "$WORK_DIR/diff-$2.txt" >&2
      STATUS=1
    fi
  else
    rm -rf "$target"
    mkdir -p "$(dirname "$target")"
    cp -R "$generated" "$target"
  fi
}

sync_skill "skills/use-devmachine" "use-devmachine"
sync_skill "skills/create-devmachine-package" "create-devmachine-package"
sync_skill "skills/edit-devmachine-boards" "edit-devmachine-boards"

if [[ "$CHECK" -eq 1 ]]; then
  if [[ "$STATUS" -eq 0 ]]; then
    echo "OK: skill references match $DOCS_DIR"
  fi
  exit "$STATUS"
fi

echo "Synced skill references from $DOCS_DIR"
