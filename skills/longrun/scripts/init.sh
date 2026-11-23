#!/usr/bin/env bash
# init.sh <repo root> <instructions folder, relative to repo root> <job prefix> [cluster exec]
# Creates <repo root>/.longrun/ from the templates. Never overwrites an existing file.
set -euo pipefail
here="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
[[ $# -ge 3 ]] || { echo "usage: init.sh <repo root> <instructions folder> <job prefix> [cluster exec]" >&2; exit 2; }
root="$(cd "$1" && pwd -P)"; prot="$2"; prefix="$3"; exec_cmd="${4:-}"
[[ -d "$root/$prot" ]] || { echo "init.sh: $root/$prot is not a folder" >&2; exit 2; }
[[ ${#prefix} -ge 3 ]] || { echo "init.sh: job prefix must be 3+ characters" >&2; exit 2; }
mkdir -p "$root/.longrun/log"
for f in GOALS.md DECISIONS.md STATE.md GLOSSARY.md LOG.md; do
  if [[ -e "$root/.longrun/$f" ]]; then echo "kept $f"; else cp "$here/../templates/$f" "$root/.longrun/$f"; echo "created $f"; fi
done
if [[ -e "$root/.longrun/config" ]]; then echo "kept config"; else
  printf 'protected=%s\njob_prefix=%s\ncluster_exec=%s\npi_files=\n' "$prot" "$prefix" "$exec_cmd" > "$root/.longrun/config"; echo "created config"
fi
py="$HOME/.claude/longrun-venv/bin/python"; [[ -x "$py" ]] || py=/usr/bin/python3
if [[ ! -s "$root/.longrun/pi_vocab.txt" ]]; then (cd "$root" && "$py" "$here/termcheck.py" seed); fi
if [[ ! -s "$HOME/.claude/longrun-data/mesh.txt" ]]; then "$py" "$here/termcheck.py" fetch-lists || echo "init.sh: fetch-lists failed; propose will rely on title counts"; fi
"$here/log.sh" --root "$root" "longrun initialized (protected=$prot, job_prefix=$prefix)"
