---
name: handoff
description: >-
  Write a handoff so a fresh agent session can continue this work: a full file on disk
  and a paste message under 4,000 characters that points to it. Triggers: "give me a
  handoff", "copy-pastable handoff", "copy paste into a new agent", "fresh agent",
  "fresh context", "new session", "super short handoff".
license: MIT
metadata:
  author: Mehdi Foroozandeh
  version: "1.0"
---

# handoff — a fresh agent picks up where this one stops

The next agent has none of this conversation. It has only what you write, and it will
trust it. A wrong fact in a handoff is copied, not caught. So a handoff carries only
facts you checked against disk or git in this turn, and it names every claim the next
agent must check again for itself.

## Two forms

Write both, unless the user asks for one.

1. **The file.** The full handoff, on disk. Put it in the project's `notes/` or `plan/`
   folder if one exists, else in the working directory. Name it
   `HANDOFF_<YYYY-MM-DD>_<slug>.md`, with today's date and a 2–4 word slug for the task.
2. **The paste message.** Under 4,000 characters, the `/goal` limit. It states the goal
   in one sentence, gives the absolute path of the file, and says "read it first". Then
   it carries the never-do list and the stop condition, because those must survive even
   if the agent skims the file. Put it in a fenced block so the user can copy it in one
   piece. Count the characters before you send it.

## Before you write: check

Every line in the handoff is a fact you checked in this turn, or it is under
"Verify yourself before trusting". Run the lookups now: `git status`, `git branch -a`,
`git log -1` on each branch you name, `gh pr list` for PRs, `ls` on every path you
name, the job ledger or `squeue`/`sacct` for job ids. A path you did not `ls` does not
go in the handoff.

## The file: sections, in this order

1. **Goal** — one sentence.
2. **Read these first, in order** — absolute paths, each with one line on why.
3. **Settled decisions — do not reopen** — each dated, each with its reason in one line.
4. **Verify yourself before trusting** — claims the next agent must re-check, each with
   where to check it (a file, a command, a branch).
5. **Never do** — actions only the human takes (push, merge, post, authenticate, delete),
   files not to touch, and every job id already logged, with "never resubmit".
6. **Traps** — what went wrong in this session and why, so the next agent does not
   repeat it.
7. **State** — branches, PRs, uncommitted work, running jobs with ids and where to check
   them.
8. **Definition of done** — checkable: a command and its expected result, or a file that
   exists with given content.
9. **Stop condition and what to report** — when to stop and ask, and what the final
   report contains.

A section with nothing in it says "none". It does not disappear.

## Rules

- **Define every internal ID.** A node id, a chunk id, a job id, a coined label: say what
  it is in the same line, or leave it out.
- **Point, do not copy.** A plan, spec, PR or log that already exists on disk goes in by
  path or URL.
- **Agent-facing.** The handoff has no TL;DR, no ELI5 and no "What I need from you"
  block. Those are for the user; the handoff is for an agent.
- **No secrets.** Redact keys, tokens and passwords.

## After writing

Tell the user the file path and give the paste message. Do not start the next agent
yourself.
