#!/usr/bin/env bash
# log.sh [--root <repo root>] "<text>"
# Appends "- <UTC time> <text>" to .longrun/LOG.md. Rotates to .longrun/log/ above 60 KB.
set -euo pipefail
here="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"; . "$here/lib.sh"
if [[ "${1:-}" == "--root" ]]; then root="$2"; shift 2; else root="$(find_root "$PWD")" || { echo "log.sh: no .longrun/ above $PWD" >&2; exit 1; }; fi
[[ $# -ge 1 ]] || { echo 'usage: log.sh "<text>"' >&2; exit 2; }
log="$root/.longrun/LOG.md"
if [[ -f "$log" && $(wc -c < "$log") -gt 61440 ]]; then
  mkdir -p "$root/.longrun/log"; old="$root/.longrun/log/LOG-$(date -u +%Y%m%dT%H%M%SZ).md"
  mv "$log" "$old"
  printf '# Log\n\nAppend-only. Written only by scripts/log.sh. Previous part: log/%s\n' "$(basename "$old")" > "$log"
fi
printf -- '- %s %s\n' "$(date -u +%Y-%m-%dT%H:%MZ)" "$*" >> "$log"
