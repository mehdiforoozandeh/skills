---
name: quiz-me
description: >-
  Test whether the user's mental model still matches work that already exists — code the
  agent wrote, a PRD, a plan, a document tree — usually because they delegated it, skimmed
  it, or were away while it was built. Derives a tree from the artifact, then asks one
  multiple-choice question at a time: general framing first, then hard into the decision
  points, with distractors drawn from the alternatives actually rejected, or from the
  conventional choice this artifact departed from.
  Every wrong answer is triaged — did the agent drift from the user's intent (→ punch list),
  or is it a gap in the user's knowledge (→ explained)? Needs an artifact that already
  exists: for a subject nothing was built for use `tutor`, and for a plain re-orientation
  with no questions asked use `catchup`. Triggers: /quiz-me, "quiz me on what we built",
  "test me on this plan", "grill me on the code you wrote", "do I actually understand what
  we built", "am I still in sync with what you wrote", "I approved that without reading it".
license: MIT
metadata:
  author: Mehdi Foroozandeh
  version: "1.1"
---

# quiz-me — is your model still the artifact's model?

A lot got built while the user steered at a distance. Reading all of it defeats the point of
delegating; assuming they're current is how drift survives. quiz-me tests the delta.

The ground truth is an **artifact**, which is the only reason this works: the answer key is
checkable on disk, so a wrong answer can mean the *artifact* is wrong and not the user.

## Target — what's under test

- **No argument** → the work of the current session. Derive the tree and the answer key from
  the **current state of the files** — re-read what changed. Your recollection is not the
  artifact: edits get reverted, failing tests force silent rewrites, context gets compacted.
  The transcript supplies the *rejected alternatives*; it is never the answer key. If the
  session produced no durable artifact, say so — drift findings are weak without one.
- **With an argument** → that target, cold. A file, a directory, a PRD, a document subtree, a
  diff, a branch. Nothing needs to be in context.
- **Ambiguous** → ask once, in one line.

Before question 1, state the scope in one line and name the two affordances: `D — not sure`,
and that saying **object** at any point flags a choice the user dislikes. **Don't show the
tree** — its structure telegraphs the answers.

## Build the tree first

Derive it breadth-first: every top-level area, drilling only where a decision is visible.
Build wider than you will ask, so you know where to go when an answer goes wrong and can
report honestly what you never touched.

**Size the quiz to the tree, not to the budget.** A 3-question quiz on a 3-decision artifact
is a complete quiz — never promote a non-decision to fill a quota. If the target is too large
to cover in one pass, name the subtree you *can* cover and get agreement instead of sampling
silently. If it is empty, missing, too thin, or holds no decisions at all, say so and stop.

## Two kinds of question, and where their options come from

- **Fact questions** — there was only ever one answer. A miss is always a gap. Distractors are
  plausible variants.
- **Decision questions** — the artifact made a choice where another was live. A miss can mean
  drift, and everything rests on where the wrong options come from.

Two sources, in priority order.

**1. Recovered alternatives — best.** An option counts as recovered only if **you can point to
where it was rejected**. Dig for it: reverted commits; code that lived a few commits and
vanished; a dependency added then removed; commented-out config; comments of the form "we don't
use X because"; PR review threads; design docs; this session's transcript. *Deleted code is the
richest vein and the easiest to forget to look at.* A recovered distractor is worth most,
because a miss says exactly which option the user believed was there.

**2. The conventional default — always available.** Most rejections were never written down;
the reasoning lived in a conversation and evaporated. So where nothing is recoverable, make the
wrong option **what most projects would do here** — what the user would assume if they weren't
watching. Most projects retry, cache, put auth in middleware. Where this artifact went the
other way, the question quietly asks whether they noticed.

That is not a downgrade. Drift *is* the gap between what the user assumed and what exists, and
absent information they assume the default — so a miss on a conventional distractor localizes
as well as a miss on a recovered one.

**Never invent a third kind.** An option that is neither recovered nor the conventional default
is noise, and noise makes a wrong answer mean only "they didn't know." And never present an
option as having been *considered* unless it was recovered: the conventional default is offered
as an option, never as history.

**Let the option count flex.** Two options plus `D` is a complete question. Never pad to fill
out an A–C shape.

**Fact distractors are near-misses**, not filler: each should be true of a *neighbouring* part
of the artifact, so a miss says which part the user confused this one with. A self-refuting
option makes the question free.

**"Why did we do X" questions** work the same way, except the options are the rejected
*rationales*. The same recovery test applies.

**Watch the stem for leaks.** The context that makes a recovered alternative legible often
telegraphs the answer — naming the old rule and the symptom that killed it hands over the fix.
Keep the stem to the question; the history belongs in the reveal.

Open with a few fact questions to set the frame, then bias hard toward decision points. A
decision with no live alternative isn't one — demote it to a fact question.

## Asking

One question at a time; options `A`–`C` plus `D — not sure`. Accept the letter in any case, or
prose that unambiguously names exactly one option — otherwise ask which letter, never guess the
mapping. A question back instead of an answer isn't a miss: answer it in one line and re-ask.
Never ask two at once, and never explain before asking.

## After the answer

**Right** → one line restating why, then the next question. No ceremony.

**Wrong, or `D`** → give the ground truth and its reason in two or three lines, then triage it
back to the user, because you cannot make this call yourself — you know what was built, not
what was wanted:

> *"That's what we did and why. Is that what you wanted?"*

- **"No, I wanted X"** → **drift.** Record it.
- **"Fine, I just didn't know"** → **gap.** Move on.
- **`D`** → gap by definition; skip the triage question.

**When the choice traces to the user's own instruction, cite it before triaging** — *"that's
what we did, because you asked for X — still what you want?"* A "no" there is a **reversal**,
not drift; log it as such. You hold the receipt, so produce it.

A *correct* answer can hide drift too — the user can know a choice, hate it, and sail through.
That is what the standing **object** affordance covers. Do not append an objection prompt to
individual reveals: on a wrong answer it duplicates the triage question, and on a right one it
either doubles the turn count or gets buried under the next question.

## Where to go next, and how far

Budget **10–12 questions** on a clean run, and branch on the triage rather than the score.

- **Gap → go up.** Missing a specific usually means the frame above it is missing; more
  siblings at that depth just manufactures more misses. Re-establish the parent, then descend.
- **Drift → go down**, into that decision's dependents. Drift propagates and every question
  there is actionable, so run past the budget until the affected subtree is clear.
- **First three answers all `D`** → stop early. The tree is above the user's frame, and
  question 12 will teach nothing question 4 didn't.
- **Gap rate still high once the budget is spent** → stop and say it plainly: *"You're not
  behind on details, you're missing the frame."* Offer to walk the artifact, or hand off to
  `tutor` with the artifact as its source and this session's gaps as the syllabus.

## What it leaves behind

- **Clean run** → chat only. Close with the score and **what the tree holds that was never
  touched**. Never let a spent budget silently read as full coverage.
- **Any drift, reversal, or objection** → write `quiz-drift-<target>-<date>.md` in the working
  directory and give the path in the closing line. Per entry: the question, what the user
  expected, what exists, where it lives, and **whether the alternative was recovered or was the
  conventional default**. Without that last field the punch list outlives its own caveat.

## Example

> **Scope** — the crawler rewrite from this session, re-read from disk; 11 decision points.
> Answer with a letter, `D` if unsure, and say **object** any time you dislike a choice.
>
> **Q3.** When a fetch fails mid-batch, what happens to the rest of the batch?
> **A** — the whole batch is retried from the start
> **B** — the batch continues; the failure is collected and reported at the end
> **C** — the batch aborts and partial results are discarded
> **D** — not sure
>
> *user: A*
>
> **B.** Failures are collected and surfaced after the batch finishes. Whole-batch retry (your
> A) was weighed and dropped — the fetches aren't idempotent, so a retry double-posts. Was
> that the call you wanted?
>
> *user: no, I assumed we'd retry. I want retries.*
>
> **Drift**, logged. That choice has two dependents — the checkpoint format and the CLI's exit
> code — so the next questions go there.
