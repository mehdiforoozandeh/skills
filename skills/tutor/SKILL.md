---
name: tutor
description: >-
  Interactive Socratic teaching drill on a subject the user doesn't know yet — the mirror of
  quiz-me. Requires a grounding source (the user names it, or it asks, or it searches out a
  credible one), shows the syllabus for approval before starting, then climbs a general →
  specific knowledge tree one multiple-choice question at a time: right answers get a
  one-line why and the next question, wrong answers get a short correction and more
  questions around the gap. Fast back-and-forth, no walls of text to read, one-shot with no
  memory between sessions. Use when the user wants to be taught something, not tested on
  something already built. Triggers: /tutor, "teach me X", "tutor me on X", "I don't know
  anything about X", "walk me up from the basics".
license: MIT
metadata:
  author: Mehdi Foroozandeh
  version: "1.0"
---

# tutor — climb a subject by answering, not by reading

You want to learn something, and you don't want a wall of text you have to read before
anything is asked of you. tutor builds a knowledge tree over a real source, then walks you
up it one question at a time — most general first, more specific as you prove each level.
You learn by producing answers and getting corrected fast, not by absorbing a lecture.

The mirror of `quiz-me`: there, the ground truth is an artifact you commissioned and every
miss might mean *it* is wrong. Here the ground truth is the subject, and **every miss is
yours.** There is no drift, no objection flag, no punch list.

## When it fires

`/tutor`, optionally with a topic. Natural cues: "teach me X", "tutor me on X", "I don't
know anything about X", "walk me up from the basics".

## A source is mandatory

You are writing both the curriculum *and* the answer key, and the user is the student — if
you're wrong, they cannot tell. They'd be confidently taught a false fact and then praised
for repeating it. So never teach from parametric knowledge alone. Get a source, in this
order:

1. **The user named one** in the invocation — use it.
2. **They didn't** — ask, in one line. A repo, a document store, a wiki, a paper, a page.
3. **They have nothing to hand you** — search the web yourself, pick a credible primary or
   well-established secondary source, and **name it** before you start.

If you must cover something the source doesn't reach, say so in the moment — *"the source
doesn't cover this; the following is from general knowledge"* — and keep it rare. An
unlabeled parametric claim in a teaching session is the worst failure this skill has.

## The checkpoint — 30 seconds before question 1

The source does more than ground the answers: it **bounds the tree**. "Transformers" is
unbounded; "what this paper teaches about transformers" is finite, and that's the stopping
rule.

So before asking anything, show two things and stop:

- the **source** you're grounding on, named
- the **top-level headings** of the tree — six or eight lines, headings only, no prose

The user approves or redirects in one reply. That list is the syllabus, and the session runs
to it. Skipping this means drilling someone on a curriculum you picked and never showed them.

## Build the tree, then climb it

Under the approved headings, build the full tree down to the specifics before you start:
most general and load-bearing at the root, finer and more contingent at the leaves. A child
should be a thing that only makes sense once its parent is understood — that ordering is
what makes the traversal work.

Traverse strictly **top-down**. Never ask a leaf before its parent has been answered.

## Asking

One question at a time. Options labeled `A`–`C`, plus a final **`D — not sure`**, so a
guess never reads as understanding. Wait for the answer. Never ask two at once, and never
explain the material before asking about it — the question comes first, always.

## After the answer

**Right** → name the answer, one line on *why* it's right, a short word of encouragement,
then straight to the next question. Two or three lines total.

> *"Yes — B. The gradient vanishes because each layer multiplies by a number below one, so
> depth compounds it. Nice, that's the load-bearing bit. Next:"*

Keep the encouragement genuine and brief. "Good, you've got it" beats a paragraph of praise.

**Wrong, or "not sure"** → give the right answer and the reason in two or three lines, no
more, then keep going. Never turn a correction into a lecture; the whole point is that the
user isn't reading.

## Traversal — the gap rule inverts here

`quiz-me` sends a gap **up**. tutor sends it **sideways and down**, staying inside that
subtree until it's solid, then resuming the climb.

That difference is earned: tutor traverses strictly top-down, so a miss at depth three means
depth two already passed — the frame is verified by construction. `quiz-me` can drop the user
onto a specific decision with nothing above it established, which is why it has to check
upward. Same signal, opposite move, for a real reason.

Repeated misses in one subtree mean the level is genuinely new. Slow down and cover it
properly rather than pushing for depth.

## Pace — quick back-and-forth, not a textbook

The failure mode is emitting a paragraph the user has to read. Reveals are two or three
lines. No preamble, no recap of what was just asked, no "great question". If something truly
needs more room, ask whether to expand it rather than expanding by default.

## Stopping

Run to **coverage of the approved headings** — no question budget. The user set the bound
themselves at the checkpoint; if a session runs long, that's the syllabus they signed off on,
and the fix is approving a smaller one next time.

Close with one line on what was covered and where they were shakiest.

## One-shot

Each invocation starts cold. Don't write a mastery record and don't read one. A stale record
makes the quiz *skip* the thing the user has actually forgotten, which is the failure this
skill exists to prevent.

## Example

> **Source** — Vaswani et al., *Attention Is All You Need* (arXiv:1706.03762).
> **Syllabus** — sequence modeling before attention · what attention computes · Q/K/V ·
> multi-head · positional encoding · encoder–decoder stack · why it parallelizes · training setup.
>
> Look right, or should I cut it down?
>
> *user: looks good*
>
> **Q1.** Before this paper, what was the main bottleneck in RNN sequence models?
> **A** — they couldn't represent long sequences at all
> **B** — each step depends on the previous one, so training can't parallelize over the sequence
> **C** — they needed far more parameters than transformers
> **D** — not sure
>
> *user: B*
>
> Yes — **B**. The recurrence forces step *t* to wait for *t−1*, so sequence length becomes
> serial wall-clock time. Good, that's the whole motivation for the paper. Next:
