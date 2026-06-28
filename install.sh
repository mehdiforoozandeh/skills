#!/usr/bin/env bash
#
# install.sh — bootstrap my agentic skills onto a machine.
#
# Symlinks skills into ~/.claude/skills/ so Claude Code picks them up:
#   - "core"     = my own skills, the ./skills/* folders in this repo
#   - "external" = third-party skills declared in ./external-skills.txt,
#                  cloned to ~/.claude/vendor-skills/ and tracking their main branch
#
# Usage:
#   ./install.sh            # everything (core + external)   [default]
#   ./install.sh --core     # only my own skills
#   ./install.sh --external # only third-party skills
#
# Safe by design: it only ever creates/refreshes symlinks it manages, and
# never deletes anything. A real (non-symlink) folder of the same name is left
# untouched and reported, so nothing you placed by hand is clobbered.

set -euo pipefail

REPO_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SKILLS_DIR="$HOME/.claude/skills"
VENDOR_DIR="$HOME/.claude/vendor-skills"
MANIFEST="$REPO_DIR/external-skills.txt"

do_core=true
do_external=true
case "${1:-}" in
  --core)     do_external=false ;;
  --external) do_core=false ;;
  ""|--all)   ;;
  -h|--help)  grep '^#' "$0" | sed 's/^# \{0,1\}//'; exit 0 ;;
  *) echo "unknown option: $1 (use --core, --external, --all, or no args)" >&2; exit 2 ;;
esac

mkdir -p "$SKILLS_DIR" "$VENDOR_DIR"

linked=0; skipped=0

# link_skill <source-dir> — symlink a skill folder into SKILLS_DIR by its basename.
link_skill() {
  local src="$1" name dest
  name="$(basename "$src")"
  dest="$SKILLS_DIR/$name"
  if [[ ! -f "$src/SKILL.md" ]]; then
    echo "  ! skip $name — no SKILL.md in $src" >&2; skipped=$((skipped+1)); return
  fi
  if [[ -e "$dest" && ! -L "$dest" ]]; then
    echo "  ! skip $name — a real folder exists at $dest (left untouched)" >&2; skipped=$((skipped+1)); return
  fi
  ln -sfn "$src" "$dest"
  echo "  ✓ $name"; linked=$((linked+1))
}

if $do_core; then
  echo "== core skills (from $REPO_DIR/skills) =="
  if [[ -d "$REPO_DIR/skills" ]]; then
    for d in "$REPO_DIR"/skills/*/; do
      [[ -d "$d" ]] && link_skill "${d%/}"
    done
  else
    echo "  (no ./skills directory found)"
  fi
fi

if $do_external; then
  echo "== external skills (from $MANIFEST) =="
  if [[ ! -f "$MANIFEST" ]]; then
    echo "  (no external-skills.txt — skipping)"
  else
    while read -r repo subpath _rest || [[ -n "$repo" ]]; do
      # strip comments / blanks
      repo="${repo%%#*}"; repo="$(echo "$repo" | xargs)"
      [[ -z "$repo" ]] && continue
      subpath="${subpath%%#*}"; subpath="$(echo "${subpath:-}" | xargs)"

      local_name="${repo//\//-}"
      clone_dir="$VENDOR_DIR/$local_name"

      if [[ -d "$clone_dir/.git" ]]; then
        echo "-- $repo (pull)"; git -C "$clone_dir" pull --ff-only -q || echo "  ! pull failed for $repo" >&2
      else
        echo "-- $repo (clone)"; git clone --depth 1 -q "https://github.com/$repo.git" "$clone_dir" \
          || { echo "  ! clone failed for $repo" >&2; continue; }
      fi

      target="$clone_dir/$subpath"
      if [[ "$subpath" == */ ]]; then          # whole folder: link each skill subdir
        for d in "$target"*/; do
          [[ -d "$d" && -f "${d}SKILL.md" ]] && link_skill "${d%/}"
        done
      else                                      # single skill folder
        link_skill "$target"
      fi
    done < "$MANIFEST"
  fi
fi

echo "== done: $linked linked, $skipped skipped =="
echo "Skills live in $SKILLS_DIR — restart the Claude desktop app to reload."
