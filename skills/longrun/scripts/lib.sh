# Shared helpers for the longrun scripts. Source, do not run.

# find_root <dir>: print the nearest ancestor of <dir> (inclusive) that holds .longrun/.
find_root() {
  local d
  d="$(cd "${1:-.}" 2>/dev/null && pwd -P)" || return 1
  while [[ -n "$d" && "$d" != "/" ]]; do
    [[ -d "$d/.longrun" ]] && { printf '%s\n' "$d"; return 0; }
    d="$(dirname "$d")"
  done
  return 1
}

# conf <root> <key>: print the value of key=value from .longrun/config.
conf() {
  sed -n "s/^$2=//p" "$1/.longrun/config" 2>/dev/null | tail -1
}

# hook_field <json> <python expression on d>: read one field of hook input.
hook_field() {
  /usr/bin/python3 -c 'import json,sys
d=json.loads(sys.argv[1] or "{}")
try: v=eval(sys.argv[2])
except Exception: v=""
print(v or "")' "$1" "$2"
}
