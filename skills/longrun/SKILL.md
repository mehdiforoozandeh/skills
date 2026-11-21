---
name: longrun
description: >-
  Run one big goal for days across many compactions: a requirements ledger with
  priority tiers, a capped decisions register, a state page re-injected after every
  compaction, an auditor that checks coverage and drift, and orchestrate as the inner
  loop. Triggers: "long-horizon run", "multi-day run", "work on this for days",
  "longrun", a mega prompt with an instructions folder.
license: MIT
metadata:
  author: Mehdi Foroozandeh
  version: "1.0"
---

# longrun: one goal, many days, a disposable context

The context window is short-term memory. It will be compacted many times, and each
summary loses something. Anything still needed tomorrow lives in `.longrun/`, written in
the same turn it becomes true. The context is disposable; the files are the run.

`orchestrate` is the inner loop (plan, builders, review, merge). This skill sits above
it and owns the goal, the priorities and the memory. Load `orchestrate` and `dispatch`
too.

## The files

`<repo root>/.longrun/`, tracked in git. Each meaning has one home.

| File | Holds | Cap |
|---|---|---|
| `GOALS.md` | The requirements ledger: one row per requirement in the PI's docs, with tier, status and evidence. | none |
| `DECISIONS.md` | Decisions in force, one table row each, with verbatim source, provenance and what each supersedes. | 10 KB |
| `STATE.md` | The state page: the goal now, what is in flight, the next 3 steps, the open asks to the PI. | 5 KB |
| `GLOSSARY.md` | Every term in use that the PI has not used and that is not ordinary English, with a gloss, origin and status. Persistent for the project. | none |
| `pi_vocab.txt`, `pi_phrases.txt` | Every word and two-word phrase the PI typed in chat, in any session. Maintained by a hook. Words in the instructions folder count as the PI's too, read live. | none |
| `LOG.md` | Append-only events, written only by `scripts/log.sh`, which stamps the clock. | 60 KB, rotates |
| `config` | `protected=` (the PI's instructions folder), `job_prefix=`, `cluster_exec=`, `pi_files=` (comma-separated globs of files written for the PI). | |

Hooks (installed globally, active only where `.longrun/` exists):
- After each compaction or resume, `scripts/reinject.sh` prints the state page, the open
  P0 and P1 rows, and the decisions in force.
- Before each compaction, `scripts/precompact.sh` supplies the summary instructions.
- `scripts/guard.sh` denies Edit and Write on the `protected=` folder. The PI's
  documents are the constitution: the agent proposes a diff and the PI applies it.
- `scripts/termcheck.py` (run by the hooks with `~/.claude/longrun-venv/bin/python`)
  checks vocabulary. `UserPromptSubmit` adds the PI's typed words to `pi_vocab.txt`.
  `Stop` checks each reply and sends it back once when it uses an unregistered term.
  `PostToolUse` checks `STATE.md`, the files matched by `pi_files=` in `config`, and
  every edit of `GLOSSARY.md` against the entry rules.

Scripts live in this skill's `scripts/` folder. `<skill>` below means that folder's
parent, `~/.claude/skills/longrun`.

## Kickoff

1. **Create the files.** Run `<skill>/scripts/init.sh <repo root> <instructions folder,
   relative to the repo root> <job prefix> [cluster exec]`. The job prefix is a short
   name that every cluster job of this run starts with (for example `myrun_`). The
   cluster exec is the command that runs a command on the cluster, for example
   `hpc run`. It also seeds `pi_vocab.txt` from every message the PI typed in Claude Code.
   Done when `.longrun/` holds all its files.
2. **Build the ledger.** Spawn one reader agent (dispatch: Read lane) with the
   instructions folder. It writes nothing; it returns ledger rows. One row per sentence
   that asks for something: every end goal, deliverable, named ablation, metric,
   dataset property, comparison and constraint. Each row quotes the sentence and cites
   file:line. You write the rows into `GOALS.md`, each with a recommended tier. Done
   when a second reader, given the docs and the ledger, finds no requirement without a
   row.
3. **Ask once, in one batch** (AskUserQuestion, recommendation first):
   - the tier of each row, as your recommendation for the PI to correct:
     **P0** the run fails without it, **P1** expected, **P2** if time allows,
     **P3** do not build;
   - the time horizon, and the deadline for the first measured result;
   - every metric or rule that cannot be executed as written (a missing unit,
     denominator, clipping or tie rule), each with a recommended fix.
   Write the answers into `GOALS.md`, `DECISIONS.md` (provenance `PI`) and `STATE.md`.
4. **Plan.** Run `orchestrate` step 1. Brief the planner with `GOALS.md`,
   `DECISIONS.md` and the horizon. Every chunk cites the ledger rows it serves. The plan
   fits the horizon and produces a first measured result inside the first day, on a
   cheap proxy if the full scorer is not ready.

Done when every row has a tier, the horizon and first-result deadline are in
`STATE.md`, and every chunk in the plan cites a row.

## Running

**Priority.** Work in tier order. No P2 work starts while a P0 row is open. A P0 row
counts as covered only when a measured result is linked in its evidence column.

**Additions.** A task that serves no ledger row is an addition, whoever proposed it,
the PI included. Before work starts, put one line to the PI: what it displaces, on
which row, at what cost. On a yes, add a row with provenance `PI` or
`agent proposal, approved`.

**Decisions.** A decision enters `DECISIONS.md` in the same step it is made, as one
row. A decision that changes an earlier one marks the earlier row `superseded by <id>`.
A choice that contradicts a decision in force is a question to the PI, never a quiet
deviation.

**Terms.** The PI's vocabulary is every word the PI typed in chat or wrote in the
instructions folder. A term that is neither the PI's, nor registered, nor ordinary English
needs a `GLOSSARY.md` row before its first use in anything the PI reads, or a term the PI
uses instead. Field terms get no exemption: being standard in the field does not make a
term the PI's. Most of all, register an ordinary word used as a new name ("oracle floor",
"replicate ladder", "screening" for a first pass) the first time it names something.
- Row rules: one row per concept, one term per concept, a gloss of 1 to 10 words that
  does not use the term, origin `PI doc`, `agent` or `field`, status `proposed`.
- The Stop hook catches rare words and coined labels such as `p16_sv`. It cannot catch
  an ordinary word used as a name; that rule is yours, and the auditor checks it.
- Many flagged terms are ones the PI knows; word frequency cannot predict which. Register
  each anyway, with status `proposed`. At each milestone, show the PI the new `proposed`
  terms as one comma-separated list, ask for the unknown ones, and run
  `termcheck.py settle --unknown <terms>`; the rest become `known`.
- Text for the PI uses glossary terms and plain words; chunk ids, kit ids and dataset
  version codes stay in the plan and the log.

**Probe, then batch.** Before submitting N jobs of a kind, run one at real scale and
read its time, peak memory and output. Set limits from the measurement. Check the
cluster's file and space quota and its reservations before a large submission.

**Numbers.** Every number told to the PI cites the file or command it came from. Every
log line goes through `<skill>/scripts/log.sh "<text>"`, which stamps the real UTC time.

**Asking.** Ask only when a choice reaches the paper's Methods section, contradicts a
decision in force, or adds a term, metric or row. Before asking, check the PI's files
and run any check under 15 minutes. Include the cost of each option. A low-stakes
question unanswered after one ask is decided with the recommendation and logged. While
work is in flight, ask in chat and keep the ask in `STATE.md`; keep every workstream
the question does not block moving.

**Turns.** A turn started by a background notification with no new result ends with
one line. Open asks are listed in full only when the list changes.

**Own jobs.** Cancel or hold this run's own cluster jobs with
`<skill>/scripts/cancel-own.sh <cluster> cancel|hold <jobid...>`. It touches only jobs
whose names start with the run's job prefix.

**Waiting.** Cluster retries and job chains run on the cluster (dependencies,
requeue), so they survive the laptop session.

## Memory discipline

- A fact still needed tomorrow goes to its file in the same turn: a decision to
  `DECISIONS.md`, a count or result to the evidence column of its row, an in-flight job
  to `STATE.md`.
- `STATE.md` is rewritten, never appended. Keep it under its cap.
- After a compaction, the hook prints the state page. Read the files it names before
  acting, then spawn `longrun-auditor`.
- A file over its cap is a defect to fix in the same turn: move history to `LOG.md`,
  collapse superseded decisions.

## Milestones and audits

Spawn the `longrun-auditor` agent after each compaction and at each milestone. It reads
the files and the repo and returns only what changed since its last audit: open P0 and
P1 rows, effort by tier, new terms, contradictions with decisions, and PI requirements
no row covers. Log a one-line summary with `log.sh` (the auditor reads the last one).
Act on its findings; tell the PI only the ones that need the PI.

A milestone report to the PI (the "GOOD NEWS" kind) is one paragraph and carries a
measured result.

## Close-out

1. Deliverables follow the headings, flow and terms of the PI's constitution document.
   Build a checklist from its headings and from the P0 and P1 rows; every item maps to
   a section of the deliverable.
2. A deliverable named after a skill (a deck, a report) is built with that skill and
   its verifier.
3. Open each rendered deliverable in the browser and check that it loads, navigates
   and has no console errors before it is published.
4. The final report lists every P0 and P1 row with its status and evidence. A row not
   done is named, never hidden.
