---
name: catchup
description: >-
  Brief refresher for resuming a long-running chat after time away. Reads back the
  current conversation and distills one scannable screen — what we're working on, where
  we are (including decisions already made), what's waiting on your call, and the next
  moves. Use when returning to a session after a break (a weekend, a holiday, a few
  days) and needing to re-orient before continuing. Triggers: /catchup, "where were
  we", "catch me up", "refresh me", "where are we", "remind me where we left off".
license: MIT
metadata:
  author: Mehdi Foroozandeh
  version: "1.0"
---

# catchup — back up to speed in one screen

You stepped away from this chat for a while and the details have faded. The full
conversation is still in context; you just need a fast re-orientation before continuing.
catchup scans the transcript and hands back a tight brief: the thread, the current
state, what's blocked on you, and the next moves. Nothing more.

## When it fires

`/catchup`, or natural cues from a returning user: "where were we", "catch me up",
"refresh me", "where are we", "remind me where we left off".

## Scope — read only this conversation

Distill **only the current chat transcript**. Do **not** read git history, memory files,
or project files to build the brief — days may have passed and the repo may have moved,
but catchup reports what *we discussed*, not what the world now looks like. If the user
wants the repo state too, that's a separate ask. Staying transcript-only keeps the brief
honest about shared memory.

If the conversation is short or barely started, say so in one line instead of padding a
four-section brief out of nothing.

## The brief — always these four headers, in this order

1. **Thread** — one line: what we're working on.
2. **Where we are** — current state and the decisions already locked in. Pointers, not
   re-derivation: "we settled on X", not a re-explanation of X.
3. **Waiting on you** — open decisions or items pending *your* call. Always present:
   if nothing is blocked on the user, write "nothing — ball's in my court."
4. **Next** — the trajectory: the next 1–3 concrete moves.

## Length — it's a brief

The whole thing fits one screen (~8–12 lines). Each section ≤2 lines; **Next** ≤3
bullets. Lead with signal, no preamble or "welcome back" filler. The user should absorb
it in one breath and know exactly where to pick up.

## After the brief

End by handing control back in one line — name the move you'd resume with and ask, or
ask which thread to pull. Don't start executing; the brief exists so the user can choose.

## Example

> **Thread** — Designing `catchup`, a session-refresher skill.
> **Where we are** — Scope locked: reads only the transcript, human-facing brief, no
> compaction. Four-section skeleton and a one-screen length budget agreed. Name chosen:
> catchup.
> **Waiting on you** — nothing — ball's in my court.
> **Next** — Write `SKILL.md`, install it to `~/.claude/skills/`, smoke-test the trigger.
>
> Want me to start with the SKILL.md draft?
