#!/usr/bin/env bash
#
# sync.sh — keep this Mac's installed skills and CLAUDE.md equal to origin/main.
# Run by a Claude Code SessionStart hook. Silent on success; prints one line on a problem.
#
# 1. If the checkout is on main and clean, fast-forward it from origin (else skip the pull).
# 2. Re-link core skills, agents and CLAUDE.md (fast, local).
# 3. Pull and re-link external skills in the background (slow, network).
# Full output goes to ~/.claude/skills-sync.log.

REPO_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
LOG="$HOME/.claude/skills-sync.log"
export GIT_TERMINAL_PROMPT=0

{
  echo "=== $(date '+%F %T') sync"
  branch="$(git -C "$REPO_DIR" branch --show-current)"
  if [[ "$branch" != "main" ]]; then
    echo "skills-sync: ~/skills is on '$branch', not main; installed skills follow that branch." >&2
  elif [[ -n "$(git -C "$REPO_DIR" status --porcelain)" ]]; then
    echo "skills-sync: ~/skills has uncommitted changes; pull skipped." >&2
  else
    git -C "$REPO_DIR" pull --ff-only -q || echo "skills-sync: git pull failed (see $LOG)." >&2
  fi
  "$REPO_DIR/install.sh" --core >/dev/null || echo "skills-sync: install.sh --core failed (see $LOG)." >&2
} 2> >(tee -a "$LOG") >>"$LOG"

nohup "$REPO_DIR/install.sh" --external >>"$LOG" 2>&1 &
exit 0
