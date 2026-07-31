---
name: quiz-me
description: >-
  Test whether the user's mental model still matches work that already exists — code the
  agent wrote, a PRD, a plan, a document tree. Derives a tree from the artifact, then asks
  one multiple-choice question at a time: general framing questions first, then hard into
  the decision points, with distractors drawn from the alternatives that were genuinely
  considered and rejected. Every wrong answer is triaged — did the agent drift from the
  user's intent (→ punch list), or is it a gap in the user's knowledge (→ explained)? Use
  when a lot has been built or planned and the user doesn't want to read all of it.
  Triggers: /quiz-me, "quiz me", "quiz me on this", "test me on this", "do I actually
  understand what we built", "am I still in sync with the code".
license: MIT
metadata:
  author: Mehdi Foroozandeh
  version: "1.0"
---

# quiz-me — is your model still the artifact's model?

A lot got built while you were steering at a distance. Reading all of it defeats the point
of delegating; assuming you're current is how drift survives. quiz-me tests the delta: it
derives a tree from what actually exists, asks you about it one question at a time, and
treats every miss as evidence — either the artifact went somewhere you didn't intend, or
your picture has gone stale. It tells you which.

The ground truth here is an **artifact**, which is what makes this skill possible: the
answer key is checkable, and a wrong answer can mean the *artifact* is wrong.

## When it fires

`/quiz-me`, optionally with a target. Natural cues: "quiz me on this", "test me on the
plan", "do I actually understand what we built", "am I still in sync".

## Target — what's under test

- **No argument** → the work of the current session: what was built, decided, or written
  in this conversation.
- **With an argument** → that target, cold. A file, a directory, a PRD, a subtree of a
  document store, a diff, a branch. Read your way to a tree; nothing needs to be in context.
- **Ambiguous** → ask once, in one line, then proceed.

Say the scope in one line before question 1 — *"Quizzing you on the auth rewrite, 14
decision points"* — but **do not show the tree**. In this skill the structure telegraphs
the answers.

## Build the tree first, thoroughly

Before asking anything, derive the full tree from the target: the general shape at the
root, decisions and their dependents in the middle, specifics at the leaves. Build it
**exhaustively even though you will only ask about part of it** — you need the whole map
to know where to go when an answer goes wrong, and to report honestly what you never
touched.

The tree is derived from whatever you read. Don't assume any particular structure in the
target; if it already carries an explicit hierarchy, use it, and if it doesn't, infer one.

## Two kinds of question

- **Fact questions** — there was only ever one answer. A miss is always a gap.
- **Decision questions** — a live alternative existed and something was chosen over it. A
  miss can mean drift.

Open with a few fact questions to set the frame, then **bias hard toward decision points**
as it narrows. That's where the user's attention is worth spending; drift can only live there.

## Distractors carry the signal

This is the load-bearing mechanic. **Distractors on a decision question must be the
alternatives that were actually considered and rejected** — never plausible-sounding noise.

Noise distractors make a wrong answer mean only "he didn't know." Real rejected
alternatives make a wrong answer say *which* option he assumed was there, so the drift
signal arrives already localized. On fact questions, distractors are plausible variants;
there is nothing to localize.

On a session target the rejected alternatives are usually sitting in the transcript. On a
cold target they often aren't recorded anywhere and you'll have to **infer** them — when you
do, say so on the reveal. An inferred distractor still tests comprehension, but a miss
against it is weaker evidence of drift than a miss against a choice that was really made.

If a decision genuinely had no live alternative, it isn't a decision question. Demote it.

## Asking

One question at a time. Options labeled `A`–`C`, plus a final **`D — not sure`** so a lucky
guess never gets recorded as knowledge. Wait for the answer. Never ask two at once, never
pre-empt the next question, never explain before asking.

## After the answer

**Right** → one line restating why it's right, then the next question. No ceremony.

**Wrong, or "not sure"** → give the ground truth and the reason for it in two or three
lines, then **triage it back to the user**, because you cannot make this call yourself —
you know what was built, not what was wanted:

> *"That's what we did and why. Is that what you wanted?"*

- **"No, I wanted X"** → **drift.** Record it. This is the valuable outcome.
- **"Fine, I just didn't know"** → **gap.** Move on; nothing to fix.
- **`D — not sure`** → gap by definition. Skip the triage question.

**On every decision-question reveal**, whether right or wrong, close with a compact
`— object?`. A *correct* answer hides drift too: the user can know the choice, hate it, and
sail through. That flag is the only way that cell surfaces. Don't offer it on fact
questions — there's nothing to object to.

## Traversal — driven by the triage, not the score

The same wrong answer means two opposite moves:

- **Gap → go up.** Missing a specific usually means the frame above it is missing; more
  siblings at that depth just manufactures more misses. Re-establish the parent, then descend.
- **Drift → go down**, into that decision's dependents. Drift propagates: everything built
  on a choice the user rejects is suspect, and worth checking one at a time.

## Length

Budget **10–12 questions** on a clean run. Overrun deliberately when answers are going badly,
but by cause:

- **Drift extension is safe** — a decision has finitely many dependents, it terminates on its
  own, and every extra question is actionable. Keep going until the affected subtree is clear.
- **Gap extension runs away.** If the gap rate is still high once the budget is spent, stop
  quizzing and say so plainly: *"You're not behind on details, you're missing the frame."*
  Offer to walk the artifact instead of testing it, or to hand off to `tutor`. Question 40
  teaches nothing question 12 didn't.

## What it leaves behind

- **Clean run** → chat only. Close with the score and, always, **what the tree contains that
  was never touched**. Never let a budget silently read as full coverage.
- **Any drift or objection** → write a file next to the target (or in the OS temp dir for a
  session target) listing each one: the question, what the user expected, what exists, and
  where. That's a punch list to act on, and it shouldn't die in the scrollback.

## Example

> **Scope** — the crawler rewrite from this session, 11 decision points.
>
> **Q3.** When a fetch fails mid-batch, what happens to the rest of the batch?
> **A** — the whole batch is retried from the start
> **B** — the batch continues, the failure is collected and reported at the end
> **C** — the batch aborts and the partial results are discarded
> **D** — not sure
>
> *user: A*
>
> **B.** Failures are collected and surfaced after the batch finishes. We looked at whole-batch
> retry (your A) and dropped it — the fetches aren't idempotent, so a retry double-posts.
> Was that the call you wanted? — object?
>
> *user: no, I assumed we'd retry. I want retries.*
>
> **Drift.** Logged. That choice has two dependents — the checkpoint format and the CLI's
> exit code — so the next few questions go there.
