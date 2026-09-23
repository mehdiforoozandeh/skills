---
name: bitesize
description: >-
  Small-step research mode: the opposite of a big upfront plan. The agent and the user
  take one small step (a "bite") at a time toward a stated end goal. Each bite: the agent
  frames where we are against the goal, lays out 2–3 possible next steps with cost, what
  each would teach, and a lean; the user asks questions until satisfied and MAKES the
  decision (often something not on the list); the agent or its subagents run only that
  step and report the outcome, what it means for the goal, and doubts. Messages capped at
  450 words. Use for scientific research, or any work where the user wants to steer every
  step, learn as they go, and keep a quick feedback loop instead of trusting a long
  autonomous run. Triggers: /bitesize, "one step at a time", "small steps", "let me make
  the calls", "don't plan it all out", "step by step with me".
license: MIT
metadata:
  author: Mehdi Foroozandeh
  version: "1.0"
---

# bitesize — one small step, the user decides, then the next

The failure this mode exists to prevent: a small or medium task turns into a big plan
full of steps, tests and checks, the agent runs off with it, and the user loses track of
what is happening. For research that is costly. The user learns less, catches wrong turns
later, and ends up trusting results they did not steer.

In this mode the user is not in the loop to **approve** the agent's decisions. The user is
in the loop to **make** them. The agent's job is to make the problem and the choices clear
enough that the user can decide well, then to execute exactly what was decided.

A **bite** is one step that answers one question or finishes one task, and whose outcome
fits in one short message. If it would not fit, it is two bites.

## Start: the goal

Before the first bite, ask the user for the end goal of the session. Not the next task —
the thing all the tasks are for. Do not start without it. If the user's answer is vague,
ask once more to make it concrete (what would "done" look like?).

The goal is the anchor for everything below. It is what stops the session from sliding
into side tasks while the important work waits.

## The loop

**1 · Frame.** Where we are, in a few lines: what we know now, what is still open. Always
include 1–2 sentences that restate the goal and say how the next bite moves toward it.
If bites are running in parallel, name every open one.

**2 · Choices.** 2–3 candidate next steps. For each: what it is, what it costs (time,
compute, effort), and what we would learn or have after it. Then the agent's lean, marked
as a lean. These are recommendations only — the user may pick one, change one, or propose
something that is not on the list. Treat the user's own idea as a first-class choice, not
a deviation.

The choices go **only** in the "What I need from you" block, as its numbered items — not
also in the body. The frame is the body; the decision is the block.

**3 · The user decides.** The user asks as many questions as they want before they
choose. Answer each one under `terse` rules: three sentences at most, sized to the
question, one word when one word is the answer. If they ask for depth ("explain
properly", "walk me through it"), give the full answer within the 450-word cap, then go
back to short. Every answer ends with the "What I need from you" block, restating the open
choice so the decision never gets lost in the questions.

Do not start the bite until the user has decided.

**4 · Run.** The agent, or its subagents, run the chosen bite — that bite only. No
extra steps, no "while I was there". While it runs:

- **Mechanical fixes: fix them and tell.** A typo, a wrong path, re-running a job that
  died for an unrelated reason. Name each fix in the report.
- **Science-affecting choices: stop and bring them back as a decision.** A parameter, a
  threshold, a data subset, a metric, dropping samples, swapping a method. Test: if a
  reviewer would ask "why did you choose that?", it is the user's call.
- **A new dependency or environment change: always stop and ask.**

**Long jobs** (a SLURM job, an hours-long training run): send one line — submitted, job
id, expected finish — then watch the job yourself and report when it ends. Do not poll
the user with updates. The user may start a parallel bite while waiting; the agent never
proposes one, because two threads at once is how priorities get lost.

**5 · Report.** No fixed template — a repo cleanup and a benchmark result need different
reports. But always say, briefly:

- **the outcome** — what happened, with the real numbers when there are numbers;
- **what it means for the goal** — marked as interpretation, not as fact;
- **doubts** — whatever could make it wrong: small n, a confound, a bug risk, a fix made
  mid-run.

Then **stop**. Do not attach the next frame and choices to a result — the next options
would steer how the user reads it. Let them react first: the "What I need from you" block
asks only for their read of the result (with crux, the acceptance question below), never
for the next choice. The one exception: a task bite
with no scientific result (cleanup, setup, a refactor) rolls straight into the next
frame, because there is nothing to interpret.

Then back to 1.

## Drift

**A bite that doesn't serve the goal.** If the user picks a step the agent thinks is a
side task, or a result tempts toward something interesting but off-goal, flag it once,
in one sentence: *"This is a side task — it doesn't move us toward X, and Y is still
waiting. Still want it?"* Then do what the user decides. No second push.

**A goal that looks wrong.** If a result suggests the goal itself is off, say plainly why
the old goal looks shaky. Do not propose a new goal. Restating the goal is the user's
move.

**Done.** When the goal looks met, say why in the frame. The user decides whether it is
done. Never close the session on your own.

## Size

**450 words per message, hard ceiling** — about three minutes of dense reading. Count
everything from the first word to the end of the "What I need from you" block. The normal
frame or report is 100–200 words; the ceiling is for the rare dense bite, not a target.

If a message would go over, the bite was too big. Split the bite; don't compress the
prose. A message over two paragraphs is already a warning sign.

**Exempt:** anything the user explicitly asks to see — code, a diff, a figure, an in-depth
explanation. The next message is back under the cap.
**Not exempt:** anything the agent chose to add — a code dump, a long log excerpt, a table
nobody asked for.
**Not shown at all by default:** the agent's own work products — scripts, files, logging.
They live on disk, not in chat.

## Crux, if present

If crux is installed and the repo has a crux vault, log everything there, following the
`crux` skill's own rules (load it). Science goes in the tree, tasks go in the taskhub.
Do it **silently**: never mention crux, the vault, node ids, or crux process terms in
chat. The user should be able to work in bitesize for weeks without noticing crux runs.

- **The session goal** is the question the bites serve. Match it to an existing question
  in the tree, or open one from the user's own statement of the goal.
- **A task bite** is a taskhub item — add it, close it with its output linked.
- **An experiment bite** needs its bar set before it runs. Fold it into the choice: when
  the user picks an experiment, add one line — *"we'll count it as support if X; the
  boring explanation we're ruling out is Y."* The user's OK on the pick covers that line.
  Record it as the hypothesis, its checks and its null.
- **Accepting a conclusion** is a plain science question inside the report: *"Do you buy
  that this supports X?"* A conversational yes is the sign-off; record it silently. Never
  record a conclusion or verdict the user did not accept.

If there is no vault, log nothing. The conversation is the record.

## What breaks the mode

- Writing a multi-step plan. The plan is one bite long.
- Running two steps when one was chosen.
- Starting a bite before the user decided.
- Deciding a science-affecting choice mid-run instead of bringing it back.
- Choices in the body **and** in the block.
- The next frame and choices stuck to a scientific result.
- Pushing twice on a drift flag.
- Proposing a new goal.
- A 600-word report. Split the bite.
- Mentioning crux.

## Activation

`/bitesize` or any trigger turns it on, and it **stays on** every turn until the user
says "stop bitesize" or "normal mode". Do not drift back into long plans after a few
turns.

## Calibration

Goal: *"find out whether the denoiser's gain on held-out cell types is real or a
leakage artifact."*

Wrong — a plan:
> Here's the full plan: (1) audit the split for donor overlap, (2) rebuild splits by
> donor, (3) retrain all three models, (4) run the ablation grid, (5) write the eval
> harness… (400 more words)

Right — a frame, then the block:
> The gain is +0.08 Pearson on held-out cell types. We don't yet know if any held-out
> cells share donors with training — if they do, the gain could be donor identity leaking
> through, which would make it not real for the goal.
>
> **What I need from you**
> **(i)** Next bite? **(a)** Count donor overlap between train and held-out — 5 min, tells
> us whether leakage is even possible. **(b)** Retrain on a donor-disjoint split — ~6 h
> GPU, answers it directly. My lean: (a); if overlap is zero, (b) is wasted.

Right — a report, then stop:
> 11 of 14 held-out cell types share at least one donor with training (range 1–4 donors).
> So leakage is possible, not shown — overlap alone doesn't mean the model uses donor
> identity. Doubt: donor ids come from the metadata sheet, and two donors have
> inconsistent labels there.
>
> **What I need from you**
> **(i)** Your read of this — does it change what you want to test next?
