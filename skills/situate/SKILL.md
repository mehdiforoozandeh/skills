---
name: situate
description: >-
  Re-orient the user in one screen: where we are, what waits on him, next moves. Also
  resumes after a tunnel drop or usage limit. Triggers: "where are we", "catch me up",
  "i just woke up", "what are we waiting for", "what's pending on me", "tunnel's back
  up", "limits are reset, continue".
license: MIT
metadata:
  author: Mehdi Foroozandeh
  version: "1.0"
---

# situate — back up to speed in one screen

The user stepped away, or the work stopped under him: the cluster tunnel dropped, a usage
limit hit, a job is still running. He needs to know where things stand before anything
else happens. situate hands back one screen, then waits for his call.

Pick the branch that fits, then write the brief below.

## Branch 1 — plain re-orientation

The user was away and the details faded. Build the brief from this conversation. The
brief reports what we discussed and decided. If he also wants the current repo or cluster
state, that is the resume branch below.

If the conversation is short or barely started, say so in one line instead of padding a
brief out of nothing.

## Branch 2 — resume after an interruption

The cluster tunnel went down (a command exited 69), or a usage limit stopped the session,
and the user says to continue ("tunnel's back up", "nibi is back up", "limits are reset,
continue"). Time passed, and the conversation is now a stale copy of the world.

1. **Re-read the record on disk.** Status files, logs, job ledgers, plan files, and
   `git status` on every branch in play. These outrank what the conversation says.
2. **Check every running job before acting.** `squeue`/`sacct` through the `hpc`
   command, per the `slurm-hpc` skill. A job may have finished, failed, or still be
   running.
3. **Never resubmit a job id already logged.** A logged job is checked, not re-run. If it
   failed, report it as failed and treat a resubmission as a decision for the user.
4. **Tunnel still down** (exit 69 again): stop. Tell the user to run `hpc up fir` in
   Terminal and wait. Never try to authenticate for him.

Then write the brief from what the checks found, and say which checks you ran.

## Branch 3 — waiting on jobs

When something is still running, the brief also says:

- **What we wait for** — the job ids or processes, and what each produces.
- **ETA** — from the walltime, the elapsed time, or the progress in the log. Say how you
  got it.
- **Laptop** — whether the laptop must stay open. A cluster job runs without it; a process that
  runs on the laptop, or a watcher this session runs, needs it open.

## Crux vault: split the work

If the repo has a crux vault (a `cruxvault/` directory or a `.crux.yaml` marker at the
working directory or any ancestor), the project-level picture comes from the vault, not
from you:

1. Run `crux brief <root> --mode=situate --json`.
2. Spawn the `crux-situate` agent with that output. Load the `dispatch` skill before
   spawning.
3. Write only the conversation-level part yourself: what we were doing in this chat, what
   is waiting on the user, next moves. Put the agent's project picture first, then yours.

## The brief

Always these four headers, in this order:

1. **Thread** — one line: what we are working on.
2. **Where we are** — current state and the decisions already made. Point to them: "we
   settled on X", not a re-explanation of X. On the resume branch, what the checks found.
3. **Waiting on you** — every open decision or item pending the user's call. If nothing
   is, write "nothing; the next move is mine."
4. **Next** — the next 1–3 concrete moves.

Add **Waiting for** (what, ETA, laptop) when jobs are running.

The whole brief fits one screen, about 8–12 lines. Each section is at most 2 lines;
**Next** is at most 3 bullets. Start with the signal, no "welcome back".

## After the brief

Name the move you would resume with and ask, or ask which thread to pull. Do not start
executing: the brief exists so the user can choose.
