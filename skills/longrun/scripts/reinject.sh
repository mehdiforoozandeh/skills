#!/usr/bin/env bash
# SessionStart hook (matchers: compact, resume). Prints the state page, the open P0/P1
# ledger rows and the decisions in force, under 9,500 characters. Silent outside a run.
here="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"; . "$here/lib.sh"
input="$(cat)"
cwd="$(hook_field "$input" 'd.get("cwd")')"
root="$(find_root "${cwd:-$PWD}")" || exit 0
L="$root/.longrun"
caps() { local f="$1" cap="$2" n; [[ -f "$L/$f" ]] || return 0; n=$(wc -c < "$L/$f"); (( n > cap )) && echo "Cap exceeded: $f is $n bytes, cap $cap."; return 0; }
{
  echo "This session is a longrun run. Its memory is in $L/. The context was just compacted or resumed; the files below are the current record."
  echo
  echo "== STATE.md =="
  head -c 5200 "$L/STATE.md" 2>/dev/null
  echo
  echo "== Open P0 and P1 rows of GOALS.md =="
  grep -E '^\| *G?[A-Za-z0-9._-]+ *\| *P[01] *\|' "$L/GOALS.md" 2>/dev/null \
    | grep -viE '\| *(done|dropped)[^|]*\| *[^|]*\| *$' | cut -c1-200 | head -c 2200
  echo
  echo "== Decisions in force (DECISIONS.md, ID and decision only) =="
  grep -E '^\| *[A-Za-z]*[0-9]+ *\|' "$L/DECISIONS.md" 2>/dev/null | grep -vi 'superseded' \
    | awk -F'|' '{gsub(/^ +| +$/,"",$2); gsub(/^ +| +$/,"",$3); print $2": "$3}' | cut -c1-160 | head -c 1500
  echo
  caps STATE.md 5120; caps DECISIONS.md 10240
  echo "Full files: $L/GOALS.md, $L/DECISIONS.md, $L/STATE.md, $L/GLOSSARY.md, $L/LOG.md. The longrun skill holds the operating rules; the longrun-auditor agent audits coverage after a compaction."
} | head -c 9500
exit 0
