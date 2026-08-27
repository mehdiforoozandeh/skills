# The grok lane — mechanics

Read this before the first `grok` call of a session. The lane itself is in
`SKILL.md`; this file is how to drive it.

## What it is

`grok` runs a Cursor-hosted Grok 4.6 agent as a subagent, through Bash rather
than the Agent tool. It bills the Cursor subscription, not the Claude
allowance. Only the text it returns enters the parent's context.

Measured on a whole-repo read of `~/crux`: 291k tokens spent on Cursor's meter,
4.7k tokens returned here. That ratio is the entire reason the lane exists.

## The wrapper

`~/.local/bin/grok`

```
grok [-d DIR] [-e EFFORT] [-r] [-b BRIEF_FILE] [-j] "prompt text"

  -d DIR    working directory for the agent    (default: cwd)
  -e LEVEL  low | medium | high | xhigh        (default: high)
  -r        read-only: analysis, no edits
  -b FILE   prepend FILE's contents to the prompt
  -j        raw JSON instead of the answer text
```

stdout is the answer. stderr is one line of timing and token usage. Exit 0 on
success, 1 on agent error, 2 on bad arguments.

**Default to `-r`.** Drop it only when the task is genuinely to write or run
something. A read-only agent cannot damage a working tree you have not
inspected.

## Effort

| Level | Use |
|---|---|
| `xhigh` | Deep analysis where the answer *is* the deliverable — architecture, root cause, "how does this actually work" |
| `high` | Default. Most reads, most drafts |
| `medium` | Mechanical sweeps — find every call site, list every TODO |
| `low` | Smoke tests only |

Higher effort costs Cursor tokens and wall-clock, not Claude tokens. When in
doubt go up, not down — the budget you are protecting is the other one.

## Constraints that shape the brief

- **No stdin.** `echo ... | grok` does not work; the agent sees nothing. The
  prompt is an argument. `-b` exists because of this — it splices a file into
  the argument rather than piping it.
- **Separate process, separate context.** Grok cannot see this conversation.
  Anything you do not write into the brief, it does not know. This is the main
  source of bad grok output — an underspecified brief, not a weak model.
- **It loads `~/.claude/skills`.** `~/.cursor/skills` is symlinked there, so
  grok sees every skill on this machine and will sometimes announce it is
  loading one that does not fit. Add *"Do not load any skill unless I name
  it"* to briefs where that noise would matter.
- **Trust is per directory.** The wrapper passes `--trust` already.

## Writing the brief

A good brief is self-contained and states the shape of the answer:

```
grok -r -e high -d ~/crux -b /tmp/brief.md "..."
```

Four things every brief needs:

1. **The goal**, stated without reference to this conversation.
2. **Where to look** — paths, not hints.
3. **The output shape** — "list of file:line with one sentence each", "a diff",
   "three paragraphs". Unshaped output is the second-biggest source of waste.
4. **What not to do** — do not refactor, do not load skills, do not summarize
   the repo.

## Verify what comes back

Grok's answer is untrusted input. It arrives cheaply, which is the point, but
cheap does not mean checked. Before acting on it:

- Claims about files: open one or two of the cited paths and confirm.
- Code it wrote: run the tests. Never land a grok diff unread.
- Anything feeding a crux verdict, a design decision, or a push: re-derive it
  yourself. That work was never in the grok lane to begin with.

If it comes back thin, the brief was thin. Sharpen the brief and re-run — do not
escalate effort on the same brief and expect a different answer.

## Failure modes

| Symptom | Cause |
|---|---|
| `cursor-agent not on PATH` | Cursor CLI missing or shell not reloaded |
| Hangs past a few minutes | Large repo at `xhigh`. Run it in the background |
| Answer ignores half the brief | Brief too long and unshaped. Split into two calls |
| `CANNOT_WRITE` | `-r` was passed and the task needed to write |
| Auth failure | `cursor-agent login` in a terminal — never on the user's behalf |

Parallel calls are fine: three concurrent agents finished in 8s in testing. Fan
out freely.

## Quota gate

`~/.claude/bin/claude-quota` reports the Claude 5-hour and 7-day windows from a
cache that the statusline writes.

**Known limitation:** the cache is only written when Claude Code invokes the
custom `statusLine` command. In the desktop app it is never invoked — probed
directly on 2026-08-27 across ten renders, zero invocations, no cache file
written since the script was created on 2026-08-22. It may work in a terminal
`claude` session; that is untested.

So `claude-quota` will usually print `NO DATA`. That is the expected state, and
it means **route normally and say the quota is unknown** — never treat it as a
limit signal. See the gate table in `SKILL.md`.

## Privacy

Grok runs on Cursor's servers. Repo contents in the working directory are
visible to it. Fine for code; think before pointing it at anything under a data
agreement.
