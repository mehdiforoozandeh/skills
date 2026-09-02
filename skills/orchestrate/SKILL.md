---
name: orchestrate
description: >-
  Run a multi-step task end to end as a foreman: a planner writes a plan file with
  non-overlapping chunks, builder subagents build the chunks in their own git worktrees,
  and the orchestrator only briefs, reads return slips and diffs, merges, and re-briefs.
  The orchestrator never does big chunks of work itself, so its context stays fresh for
  the whole run. Does not stop until every acceptance criterion passes, or a chunk hits
  its retry cap. Routes every spawn through the dispatch skill. Use when the user wants a
  task done end to end by a group of subagents, not by the main loop.
  Triggers: /orchestrate, "orchestrate this", "run this end to end with subagents",
  "be the foreman", "delegate the whole thing and just review", "keep your context fresh".
license: MIT
metadata:
  author: Mehdi Foroozandeh
  version: "1.0"
---

# orchestrate: brief, review, merge, repeat

You are the foreman. You do not build. A planner writes the plan, builders build the
chunks, and you keep the task moving until it is done. Your context is the scarce
resource: every repo file you open, every transcript you skim, every test suite you run
inline pushes you toward the dumb zone, the point where a long context makes you slower
and worse. Everything below exists to keep you out of it.

Load the `dispatch` skill before the first spawn, and run its quota gate. Dispatch picks
the model tier for every agent below. This skill picks what each agent does.

Two facts about the harness, verified on this machine, shape the mechanics:

- The Agent tool's `isolation: "worktree"` option only works when the session's working
  directory is inside the repo. You create worktrees yourself instead, with `git worktree
  add`, so the base branch is explicit and you know every branch name. They live outside
  the repo, under `<repo parent>/.orchestrate-wt/<repo name>/<id>`, so test discovery
  and `git status` in the repo never see them.
- A subagent can read any absolute path on the machine, including the plan file in the
  main checkout. So briefs point at the plan file and paste only the chunk's own lines.

## The loop

```
plan → wave 1 builders → review + merge → wave 2 builders → ... → verify → report
```

Each step ends on a checkable condition. Do not move on before it holds.

### 1. Plan into a file

Spawn one planner. It runs on `fable`: the user wrote that into this skill, which is the
naming dispatch requires. If someone else installs this skill, they change this line.
The planner reads the repo. You do not. Its output is one file:

```
<repo root>/.orchestrate/plan.md
```

Brief the planner with the goal, the repo path, the plan format below, the plan rules
below, and the ground truth it must verify first: the current branch and its origin,
`git branch -a` for anything that already does part of the work, and that the test
runner passes today. Tell it to run each per-chunk Test command form once against the
existing suite, so an environment defect surfaces in planning and not in every builder.

Tell the planner to return only the chunk table: id, wave, owned files, test command,
one line per chunk. The full plan stays in the file.

**Plan format.** One section per chunk:

```
## Goal
<one paragraph>

## Acceptance criteria
- <a command and its expected result, one per line>

## Chunks
### C1 <name>   wave 1
Goal: <one sentence>
Owns: <exact file paths, exclusive within the wave>
Interfaces: <signatures or contracts other chunks rely on, pinned here>
Depends on: <chunk ids or none>
Test: <command, run with the repo root as working directory>

## Decisions needed
<none, or one line per decision only the user can make>

## Log
<empty; you append to it>
```

**Plan rules.** These are checkable. Reject a plan that breaks one, send it back once
with the broken rule named, and stop if the second plan breaks one too.

- File sets are disjoint within a wave. Two chunks in one wave never own the same file.
- A chunk touching a file another chunk owns goes in a later wave.
- Every interface shared across chunks is pinned in the plan, so builders never need to
  talk to each other.
- Every chunk is one agent, one sitting, no questions.
- Every acceptance criterion is a command with an expected result, not a sentence.
- Owned test files are named by path, never as a directory.

**Commit policy.** Builders commit on their chunk branches, and merging a chunk creates
a commit on the working branch. CLAUDE.md forbids commits unless the user asked. So the
plan summary you post ends with one ask: permission for builders to commit on `chunk/*`
branches and for you to merge them into the working branch, local only, no push. If the
user's request already granted it ("commits ok", "merge as you go"), skip the ask.
Nothing else in this skill waits for the user.

If the repo is on its default branch, create a working branch first, named
`orchestrate/<short task slug>`, and merge into that. CLAUDE.md asks for it.

**Done when:** the plan file exists, passes every rule, the Decisions needed section is
empty or answered, you have posted a five-line summary to the user, and the commit policy
is granted.

### 2. Spawn a wave

For every chunk in the wave, create a worktree on a new branch cut from the working
branch, then spawn one builder in the background:

```
git -C <repo> worktree add -b chunk/<id> <repo parent>/.orchestrate-wt/<repo name>/<id> <working branch>
Agent({ description: "<id> <name> [<tier>]", model: <per dispatch>,
        run_in_background: true, prompt: <brief> })
```

Builders write and run, so dispatch puts them in the Build lane. Dispatch's grok lane
does not apply to builders here: grok runs through Bash, and the slip and the task
notification below need the Agent tool.

**The brief.** To write it, read only the chunk's own section of the plan file, for
example `sed -n '/^### C1 /,/^### C2 /p' <plan>`, never the whole file. Every builder
brief contains, in this order:

1. The chunk id, the absolute worktree path, its branch, and what it was cut from.
2. The absolute path of the plan file in the main checkout, and which sections to read
   first: Goal and the chunk's own section.
3. The chunk's goal and owned file set, pasted, and the sentence: "Do not create or edit
   any file outside this set. If the task needs one, stop and say so on the slip."
4. The ground truth to verify first, pasted: branch name, base commit, and the files or
   signatures it builds on.
5. The test command, "run it with the worktree as working directory", and "run it before
   you return". Name any environment trap the planner found.
6. The commit step: `git -C <worktree> add <owned files> && git -C <worktree> commit -m
   "<id> <name>"`. Without it the branch is empty and there is nothing to merge.
7. The return slip format below, and: "Return the slip and nothing else. No ELI5, no
   TL;DR, no 'What I need from you' block. The Open line is the only place for an ask."
   Builders inherit the global CLAUDE.md, and without this line they append all three.

The builder cannot see this conversation. Paste what it needs, point only at the plan.

**Done when:** every chunk in the wave has a worktree, a running agent, a line in the
plan's Log, and you have said in one line what you routed, per dispatch.

### 3. Wait without polling

Builders report back through task notifications. Do not poll, do not read their
transcripts, do not run their tests while they run. If nothing is running that you could
act on, end the turn and wait.

### 4. Review a return slip

**The return slip.** Every builder returns exactly this, under 150 words plus the test
output:

```
## <id>: done | partial | blocked
Branch: <name>   Base: <sha and subject>
Commit: <sha>
Files changed: <paths>
Tests: <command> → <pass/fail, counts, failing lines if any>
Deviations from the brief: <none, or what and why>
Open: <none, or what a human must decide>
```

Review is the slip plus the diff, and nothing in the repo beyond the diff:

```
git -C <repo> diff <working branch>...chunk/<id> --shortstat
```

Under 300 changed lines, read the full diff. Over it, or once the diffs you have read
this run add up to 1500 lines, spawn a reviewer with the diff and the brief, read-only,
and act on its verdict. That is a judgment you act on, so dispatch puts it in the Build
lane. Keep the running total in the plan's Log.

**Verdict, one of three:**

- **Accept.** Merge: `git -C <repo> merge --no-edit chunk/<id>`. File sets are disjoint,
  so a conflict means the plan was wrong. Do not resolve it by hand. Send the plan back
  to the planner once with the conflict named. A second conflict is a stop.
- **Send back.** Re-spawn the same chunk in the same worktree with a sharper brief that
  names the defect and says the branch already holds the first attempt: fix on top and
  commit again. Same tier, per dispatch: an agent that came back thin needs a better
  brief, not a firmer one. Count a retry.
- **Stop.** The Open line names a decision only the user can make, or the chunk has hit
  three retries. Finish every other chunk you can, then stop and ask.

An Open line that names an environment defect, not a decision, is yours to settle: a
wrong test command form, a missing directory, a tool on a different path. Amend the plan
file, log the amendment, and tell the next builders in their briefs.

Append one line to the plan's Log for every verdict, retry, and amendment. The Log is
the retry counter and the run's memory. It survives compaction; your context may not.

You never fix a builder's work yourself. One exception: a change under 20 lines where
the brief to delegate it would be longer than the change. Log it when you use it.

**Done when:** every chunk in the wave is merged or stopped, each with a Log line.

### 5. Next wave

Wave N+1 worktrees are cut from the working branch after wave N merged, so they contain
everything wave N built. Return to step 2.

### 6. Verify and report

When the last wave is merged, spawn one verifier with the acceptance criteria, pasted.
It runs every criterion with the repo root as working directory and returns one
pass/fail line per criterion, nothing else. You do not run the suite yourself.

A failed criterion is a new chunk: brief it, run it, review it, verify again. Two verify
rounds is the cap. A criterion still failing after the second round is a stop: report it
as open with the verifier's observed output.

**Done when:** every criterion passes. Then report to the user:

- What shipped, in one paragraph.
- One line per chunk: id, retries, outcome.
- What is uncommitted, and what is left behind: the plan file, the worktrees under
  `<repo parent>/.orchestrate-wt/`, and the `chunk/*` branches. You do not remove them. Give the
  cleanup commands and let the user run them, per the tidy rule in CLAUDE.md.
- The "What I need from you" block, per CLAUDE.md.

## Guardrails

- **No new dependency and no environment change** without asking. A builder that needs
  one says so on its Open line, and that is a stop.
- **No push**, ever, under this skill. Merges are local commits under the commit policy.

## When to use Workflow instead

If the plan is a fixed graph of more than six chunks in two or more waves, and review
can be a reviewer agent rather than you, the Workflow tool runs the same loop
deterministically. Use it only when the user typed `/orchestrate` themselves; a skill
that fired on its own is not the opt-in the Workflow tool requires. Load
`workflow-authoring` first. For anything smaller, the Agent tool and this loop are
enough, and the review stays with you.

## Quick reference

```
planner    → fable, writes .orchestrate/plan.md, returns the chunk table only
builder    → per dispatch (Build lane), own worktree, background, commits on chunk/<id>
reviewer   → per dispatch (Build lane), read-only, only when a diff is over 300 lines
verifier   → per dispatch (Build lane), runs the acceptance criteria, one line each
you        → brief, read slips and diffs, merge, log, re-brief, report

plan breaks a rule            → back to planner once, rule named; twice is a stop
slip: partial or blocked      → sharper brief, same tier, same worktree, count a retry
Open line is an env defect    → amend the plan, log it, tell the next briefs
Open line is a user decision  → finish the rest, stop, ask
three retries on one chunk    → finish the rest, stop, ask
merge conflict                → plan was wrong, back to planner once
criterion fails at the end    → new chunk, then verify again; two rounds is the cap
```
