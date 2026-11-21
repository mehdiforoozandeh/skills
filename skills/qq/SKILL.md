---
name: qq
description: Quick question, quick answer. The reply has no more words than the question. One turn only.
disable-model-invocation: true
license: MIT
metadata:
  author: Mehdi Foroozandeh
  version: "1.0"
---

# qq: quick question, quick answer

**The budget.** Count the words of the question, without the `/qq` token. That count is
the most words the reply may have. A 10-word question gets at most 10 words back. A word
is any run of characters between spaces, so a command, a path or a number counts as one
word each.

**Scope: one turn.** The budget governs this reply only. The next turn returns to normal
length.

**The answer is the whole reply.** No preamble, no restated question, no formatting, no
TL;DR, no "What I need from you" block. The user typed `/qq` to get exactly this.

## Steps

1. Count the question's words. Write nothing yet.
2. Find the answer with the same reading, tool calls and checking as any other answer.
   The budget limits the words, never the work.
3. Draft the answer, count its words, and cut until the count fits the budget.

Done when the reply's word count is at or under the question's.

## What survives the cut

In this order:
1. The direct answer. "Yes." is a complete reply.
2. The fact that decides whether to act: a number, a size, a risk.
3. The exact command, flag or path, whole. A command that does not fit is left out, never
   shortened.
4. A reframe outranks all three: if the question aims at the wrong target, say that.

A risk the user must know (data loss, an irreversible step) takes the budget first. When
the safe answer cannot fit, say so in the budget: "Risky; ask without qq."

Unchecked claims carry one hedge word ("probably"). A precise-sounding detail that was
not verified stays out.

## Calibration

Question, 6 words without `/qq`: "/qq did the scoring jobs finish yet?"
Reply, 5 words: "No: 50 of 62 finished."
