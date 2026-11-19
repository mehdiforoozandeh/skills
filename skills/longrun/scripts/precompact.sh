#!/usr/bin/env bash
# PreCompact hook. In a longrun run, prints instructions for the compaction summary.
here="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"; . "$here/lib.sh"
input="$(cat)"
cwd="$(hook_field "$input" 'd.get("cwd")')"
root="$(find_root "${cwd:-$PWD}")" || exit 0
open_ids="$(grep -E '^\| *[A-Za-z0-9._-]+ *\| *P[01] *\|' "$root/.longrun/GOALS.md" 2>/dev/null \
  | grep -viE '\| *(done|dropped)[^|]*\| *[^|]*\| *$' | awk -F'|' '{gsub(/ /,"",$2); printf "%s ", $2}')"
cat <<TXT
This conversation is a longrun run with its record in $root/.longrun/. The summary should:
1. Quote every PI message since the last compaction verbatim, with its time.
2. List the open P0 and P1 ledger rows by ID: ${open_ids:-none recorded}, with one line of status each.
3. List every job id and agent name in flight, what each produces, and where its output lands.
4. List decisions made since the last compaction by their DECISIONS.md id, and any decision not yet written there.
5. List open asks to the PI.
6. Name the files to re-read first: .longrun/STATE.md, .longrun/GOALS.md, .longrun/DECISIONS.md.
Numbers in the summary come from files or command output, with the source named.
TXT
exit 0
