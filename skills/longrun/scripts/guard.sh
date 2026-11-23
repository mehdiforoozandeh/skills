#!/usr/bin/env bash
# PreToolUse hook (Edit|Write|MultiEdit|NotebookEdit|Bash). Denies:
#  - writes to the PI's instructions folder named by protected= in the nearest .longrun/config;
#  - direct writes to .longrun/GLOSSARY.md, pi_vocab.txt and pi_phrases.txt. Only
#    termcheck.py writes those: `propose` adds glossary rows, the UserPromptSubmit hook adds
#    the PI's typed words. An agent cannot admit a term or make a word the PI's.
here="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"; . "$here/lib.sh"
input="$(cat)"
deny() {
  python3 -c 'import json,sys; print(json.dumps({"hookSpecificOutput":{"hookEventName":"PreToolUse","permissionDecision":"deny","permissionDecisionReason":sys.argv[1]}}))' "$1"
  exit 0
}
TERMS_MSG="The glossary and the PI vocabulary files are written only by termcheck.py. To add a term, run: ~/.claude/longrun-venv/bin/python ~/.claude/skills/longrun/scripts/termcheck.py propose \"<term>\" \"<gloss>\". A rejected term is final; use plain words or the PI's words."

cmd="$(hook_field "$input" 'd.get("tool_input",{}).get("command")')"
if [[ -n "$cmd" ]]; then
  find_root "$(hook_field "$input" 'd.get("cwd")')" >/dev/null || exit 0
  # Bash: a command that names a protected run file and could write it is denied, unless
  # it is a single termcheck.py call.
  if grep -qE 'GLOSSARY\.md|pi_vocab\.txt|pi_phrases\.txt' <<<"$cmd"; then
    if grep -qE '^[^;&|]*termcheck\.py[[:space:]]+(propose|check|lint|candidates|seed)\b[^;&|>]*$' <<<"$cmd"; then exit 0; fi
    grep -qE '>|\btee\b|\bsed\b[^|;&]*-i|\bperl\b|\bpython[0-9.]*\b|\bmv\b|\bcp\b|\brm\b|\btruncate\b|\bdd\b|\bed\b|\bex\b|\bawk\b[^|;&]*-i' <<<"$cmd" \
      && deny "$TERMS_MSG"
  fi
  exit 0
fi

f="$(hook_field "$input" 'd.get("tool_input",{}).get("file_path") or d.get("tool_input",{}).get("notebook_path")')"
[[ -n "$f" ]] || exit 0
dir="$(dirname "$f")"; while [[ ! -d "$dir" && "$dir" != "/" ]]; do dir="$(dirname "$dir")"; done
root="$(find_root "$dir")" || exit 0
real="$(cd "$dir" && pwd -P)/${f#"$dir"/}"
lr="$(cd "$root/.longrun" && pwd -P)"
case "$real" in
  "$lr/GLOSSARY.md"|"$lr/pi_vocab.txt"|"$lr/pi_phrases.txt") deny "$TERMS_MSG" ;;
esac
prot="$(conf "$root" protected)"; [[ -n "$prot" ]] || exit 0
pdir="$(cd "$root/$prot" 2>/dev/null && pwd -P)" || exit 0
case "$real/" in
  "$pdir"/*) deny "$f is in the PI instructions folder, which is read-only in this longrun run. Propose the change to the PI as a diff; the PI applies it, and DECISIONS.md records what it supersedes." ;;
esac
exit 0
