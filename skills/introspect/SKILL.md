---
name: introspect
description: >-
  Periodic self-review of how Mehdi works with his agents: read his transcripts since the
  last run, audit CLAUDE.md, memory and skills, then walk him through a decision list and
  apply what he approves. Run every few months. Invoked by Mehdi only: /introspect.
disable-model-invocation: true
argument-hint: "[optional outside source to learn from, e.g. a repo path or URL]"
---

# introspect

You run a review of Mehdi's agent workspace against his own habits. The review finds what he
asks for again and again, what he keeps correcting, and where his instructions, memory and
skills conflict or have gone stale. Then he decides, item by item, and you apply his decisions.
You run in the main session: you start the reader agents and you ask Mehdi the questions.
Subagents can do neither.

Every output goes to `~/workspace-review/<YYYY-MM-DD>/` (call it RUN below).

## 1. Find the last run

- Read `~/workspace-review/LAST_RUN`. It holds the date of the last completed run (YYYY-MM-DD).
  If it is missing, use 90 days ago and say so.
- Read every earlier `decisions.md` under `~/workspace-review/` (newest first). A decision there
  is settled. Do not propose it again unless new evidence contradicts it; if so, cite the
  evidence and the old decision side by side.
- If Mehdi named an outside source in `$ARGUMENTS`, note it for step 3.

## 2. Extract (deterministic)

Run, from any directory:

```
python3 -I ~/.claude/skills/introspect/scripts/extract_user_messages.py --out RUN/extract --since <LAST_RUN>
```

It writes `RUN/extract/messages/<project>.txt` (only what Mehdi typed) and `RUN/extract/usage.json`
(typed slash commands and Skill-tool calls). Read `usage.json` yourself. Note the size of each
messages file.

## 3. Read and audit (parallel)

Load the `dispatch` skill, then start these agents in one batch:

- `introspect-transcripts`, one per project file over about 150 KB, and one for the small files
  together. Pass the file paths and `usage.json`.
- `introspect-instructions`. Pass RUN and the list of earlier decisions.
- `introspect-skills`. Pass RUN, `usage.json` and the list of earlier decisions.
- If Mehdi named an outside source: one read-only agent (Sonnet) that extracts the concrete,
  copyable practices from it, ranked by value for the least added instruction weight.

Save each report to `RUN/research/<agent>.md` as it arrives, so nothing lives only in this context.

Then check the claims that would drive a change: open the file, run the command, or grep the
transcript. Drop or mark any claim you could not confirm.

## 4. Decision list

Write `RUN/decision_list.md`. Each item states the evidence (path, dated quote or count), your
recommendation, and the decision Mehdi must make. Order:

0. Safety: exposed secrets, personal data in the wrong place.
1. Patterns into instructions and skills: repeated corrections and re-explained facts become
   standing rules; repeated requests become skills or trigger phrases; conflicts between
   instructions, memory and skills, each with both sides quoted.
2. Cleanup: dead, broken, duplicate or stale skills, memory files, instruction files, clutter.
3. Enrichment: ideas from the outside source, if one was given.

Keep the global CLAUDE.md lean. Every proposed addition names what it replaces or why the file
can afford it.

## 5. Walk the list with Mehdi

- Tell him the list is ready and give its path. Start with section 0.
- Ask with AskUserQuestion, up to 4 items per batch, recommendation first. Use multi-select where
  options are not exclusive.
- Log every answer at once in `RUN/decisions.md` (item, decision, status).
- If an answer is unclear or only partly given, ask again; never guess an approval.

## 6. Apply

- Global CLAUDE.md: write the new version to `RUN/CLAUDE.new.md`, show Mehdi the changes, and
  overwrite only after his yes. Keep the old copy in RUN. Sync `~/skills/global-CLAUDE.md`
  without the Environment and HPC sections.
- Skills repo (`~/skills`): its skills are linked live, so never edit or switch branches in that
  checkout. Work in a worktree on a new branch, commit, push, open a PR. Mehdi merges.
- Other repos: the same worktree-branch-PR route.
- Memory: edit files and the MEMORY.md index directly.
- Deletions: check for uncommitted work first, rescue it to `RUN/rescued/`, then delete only
  what Mehdi approved.

## 7. Close

- Report: what changed and where; each PR with its link; what waits on Mehdi (merges,
  installs, key rotation); anything not done or not verified.
- After his merges: run `~/skills/install.sh`, and remove by hand any link to a deleted
  skill (install.sh never deletes links).
- Write today's date to `~/workspace-review/LAST_RUN`.
- Update the memory file `workspace-review-<YYYY-MM>.md` with the RUN path, so the next
  session finds the decisions.
