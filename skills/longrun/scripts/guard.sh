#!/usr/bin/env bash
# PreToolUse hook (Edit|Write|MultiEdit|NotebookEdit). Denies writes to the PI's
# instructions folder named by protected= in the nearest .longrun/config.
here="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"; . "$here/lib.sh"
input="$(cat)"
f="$(hook_field "$input" 'd.get("tool_input",{}).get("file_path") or d.get("tool_input",{}).get("notebook_path")')"
[[ -n "$f" ]] || exit 0
dir="$(dirname "$f")"; while [[ ! -d "$dir" && "$dir" != "/" ]]; do dir="$(dirname "$dir")"; done
root="$(find_root "$dir")" || exit 0
prot="$(conf "$root" protected)"; [[ -n "$prot" ]] || exit 0
pdir="$(cd "$root/$prot" 2>/dev/null && pwd -P)" || exit 0
real="$(cd "$dir" && pwd -P)/${f#"$dir"/}"
case "$real/" in
  "$pdir"/*)
    printf '{"hookSpecificOutput":{"hookEventName":"PreToolUse","permissionDecision":"deny","permissionDecisionReason":"%s is in the PI instructions folder, which is read-only in this longrun run. Propose the change to the PI as a diff; the PI applies it, and DECISIONS.md records what it supersedes."}}\n' "$f"
    ;;
esac
exit 0
