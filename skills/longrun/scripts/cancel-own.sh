#!/usr/bin/env bash
# cancel-own.sh <cluster> cancel|hold|release <jobid...>
# Cancels, holds or releases jobs of this run only: each id must belong to the current
# user and carry a job name starting with job_prefix from the nearest .longrun/config.
set -euo pipefail
here="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"; . "$here/lib.sh"
[[ $# -ge 3 ]] || { echo "usage: cancel-own.sh <cluster> cancel|hold|release <jobid...>" >&2; exit 2; }
cluster="$1"; action="$2"; shift 2
case "$action" in cancel) cmd="scancel";; hold) cmd="scontrol hold";; release) cmd="scontrol release";; *) echo "action must be cancel, hold or release" >&2; exit 2;; esac
[[ "$cluster" =~ ^[A-Za-z0-9_-]+$ ]] || { echo "bad cluster name" >&2; exit 2; }
for j in "$@"; do [[ "$j" =~ ^[0-9]+(_[0-9]+)?$ ]] || { echo "bad job id: $j" >&2; exit 2; }; done
root="$(find_root "$PWD")" || { echo "no .longrun/ above $PWD" >&2; exit 1; }
prefix="$(conf "$root" job_prefix)"; exec_cmd="$(conf "$root" cluster_exec)"
[[ ${#prefix} -ge 3 && "$prefix" =~ ^[A-Za-z0-9_.-]+$ ]] || { echo "job_prefix in .longrun/config must be 3+ safe characters" >&2; exit 1; }
[[ -n "$exec_cmd" ]] || { echo "cluster_exec is empty in .longrun/config" >&2; exit 1; }
ids="$*"
remote="ok=''; for j in $ids; do n=\$(squeue -h -u \$USER -j \$j -o %j 2>/dev/null | head -1); case \"\$n\" in $prefix*) ok=\"\$ok \$j\";; *) echo \"skip \$j (name '\$n' lacks prefix $prefix or job not yours)\";; esac; done; [ -n \"\$ok\" ] && $cmd \$ok && echo \"$action:\$ok\"; true"
read -r -a ex <<< "$exec_cmd"
"${ex[@]}" "$cluster" "$remote"
"$here/log.sh" --root "$root" "cancel-own.sh $action on $cluster: $ids"
