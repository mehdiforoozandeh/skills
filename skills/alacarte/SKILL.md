---
name: alacarte
description: >-
  Walk the design forks of one part of an experiment or method as clickable
  multiple-choice questions, one fork at a time. Use AFTER the goal, requirements and
  limits are settled (e.g. in a `bitesize` conversation), when what is left is choosing
  among known options: loss function, architecture, preprocessing, split, metric,
  baseline. The agent maps the forks under the scope the user names, orders them
  upstream-first, and asks each with `AskUserQuestion`: every question carries the agent's
  recommendation and why, and allows several picks when testing several options makes
  sense (several = ablation arms). It prunes forks that later answers make moot and ends
  with a decision record. Inside a `bitesize` session, offer it as a candidate bite when
  the next decision is a set of known-option choices. NOT for open-ended goal-setting (use
  `bitesize` or `pingpong`), and NOT for stress-testing a plan (use `grilling`). Triggers:
  /alacarte, "walk me through the choices for X", "what are my options for X", "go through
  the design decisions", "multiple-choice the design", "which loss / architecture /
  preprocessing should I use".
license: MIT
metadata:
  author: Mehdi Foroozandeh
  version: "0.2"
---

# alacarte — pick each design choice off the menu, one fork at a time

Experiment design has two phases. First, the user and the agent talk: goals, requirements,
limits, the main questions. That phase is open-ended, and `bitesize` serves it. Second, what
is left is a set of **forks**: decision points where the options are known and the user must
choose (which loss, which architecture, which normalization). This skill serves the second
phase. Its job is to make each fork fast and clear to decide, and to leave nothing chosen
silently.

A **fork** is one decision with 2–4 real options. An **arm** is an option the user keeps in
an ablation: picking several options at a fork means "test these against each other".

## Step 1 · Scope and ground

The user names one scope: a question ("how do I handle class imbalance?") or one part of
the design ("the preprocessing"). If they named none, ask for it in one line.

Restate, in 2–3 lines, the goal and the hard limits this scope must serve: compute budget,
data, deadline, what the result must show. Take them from the conversation, the repo, or a
crux vault if one is present. If the goal or limits are not settled, say so in one sentence
and suggest finishing that in `bitesize` first; continue only if the user says to.

Find facts yourself: read the code, the data shapes, the config. Ask the user only for
decisions. Done when the scope and its goal are stated and the user has not objected.

## Step 2 · Map the forks

List every fork under the scope, ordered **upstream first**: a fork whose answer changes
the options of another fork comes before it. One line per fork: its name and its options.
Mark forks that are already decided by the goal or the code as **fixed**, with the reason,
so the user can reopen them.

Show the map and ask the user to add, drop, merge or reorder forks. Keep it under 15 lines;
if the scope has more forks than that, it is two scopes — say so and propose the split.
Done when the user accepts the map.

## Step 3 · Walk the forks

Take the first open fork. Ask it with `AskUserQuestion`, **one fork per call**, so the user
clicks an answer:

- `question`: the fork, phrased against the goal, ending with your recommendation and its
  reason in one clause: "Which loss for calibrated per-base predictions? I recommend
  Poisson NLL, because the targets are counts."
- `options`: 2–4 real choices. Put your recommendation first, labeled "(Recommended)", and
  start its `description` with the reason. In every `description`: what the option is, its
  main trade-off **for this goal**, and its cost. If a fork has more than 4 serious
  options, ask the top 3 and name the rest in the question text; "Other" is always
  available.
- `multiSelect`: **true** when testing several options against each other is a sensible
  ablation — the options answer a real question about the goal, and the budget allows
  more than one run. **false** when the options exclude each other by nature, or when
  only one run is affordable. When you recommend an ablation, label every recommended arm
  "(Recommended)" and say in the question why comparing them is worth the extra runs.
- `preview`, when a short code or config snippet makes the difference concrete.

Every question carries a recommendation and its reason; a fork with no lean means you have
not done the legwork yet. If `AskUserQuestion` is not available, write the same thing as
text: options (a)–(d), the recommendation and why, and whether several picks are allowed.

**After each answer:**

- **One option:** record it, with the user's reason if they gave one.
- **Several options (arms):** record the arm set. Ask once which arm is the **default** that
  the other forks assume. State the run count when it grows: "3 loss arms × 2 architecture
  arms = 6 runs." If the count passes what the stated budget allows, say so in one
  sentence; the user decides what to cut.
- **"Not sure" / "later":** mark the fork **deferred**, use your recommendation as a
  placeholder for downstream forks, and say so.
- **A question instead of an answer:** answer under `terse` rules (3 sentences at most),
  then ask the same fork again.
- **An answer that reopens the goal** (e.g. "actually we don't need calibration"): stop the
  walk, say which settled forks it touches, and let the user decide whether to go back to
  phase one.

Then **recompute the map**. Drop forks the answer made moot, add forks it created, and say
so in one line ("Dropped: focal-loss γ, because you chose MSE.").

Between forks, write at most 2 lines of text. The question carries the content.

Done when every fork in the map is chosen, has an arm set, or is marked deferred.

## Step 4 · The decision record

Show the record as one table: fork, choice or arms (default marked), the reason, and
status (chosen / arms / deferred / fixed). Under it, list the deferred forks and the total
run count. Ask the user to confirm it.

After the user confirms:

- **crux vault present:** log the choices following the `crux` skill's rules (load it).
  Arms become the conditions of the hypothesis they serve.
- **otherwise:** write the record to `alacarte-<scope-slug>.md` in the project root and
  give the path.

## Inside bitesize

`bitesize` stays as it is; `alacarte` fits into its loop as one bite.

- **When to offer it.** In the bitesize Choices step, when the next decision splits into
  several known-option choices, one candidate bite is "walk the forks of <part>", with the
  fork count and a rough time. It is offered like any other bite; the user picks it. When
  the next decision is a single known-option fork, skip the offer: ask that one fork
  directly as a Step 3 question, since clicking the answer is the decision.
- **Step 1 is short.** The bitesize goal is the goal. Restate it in one line and go to
  Step 2.
- **The walk is one bite.** Questions during the walk follow Step 3, not the bitesize
  "What I need from you" format, because each `AskUserQuestion` call is itself the ask.
- **The record is the bite's report.** Show the Step 4 table as the report, with doubts
  (deferred forks, a run count over budget). Then stop, as bitesize does after a report.
  Log to crux silently, under bitesize's own crux rules, and never mention crux.
- **Back to bitesize.** After the user reacts to the record, the next turn is a normal
  bitesize frame.

## What breaks the mode

- Two forks in one question. Ask the whole map, one fork at a time.
- A downstream fork asked before the fork it depends on.
- A fork chosen by the agent without being shown. Every non-fixed fork reaches the user.
- A question with no recommendation, or a recommendation with no reason.
- Options that are not real: a straw option, or a duplicate of another under a new name.
- An option described without its trade-off for this goal.
- Paragraphs between questions.
- Arms recorded without a default, or a run count left unstated.
- Turning the walk back into goal-setting without the user's say.

## Activation

`/alacarte <scope>` or any trigger starts it. It ends when the user confirms the record,
or says "stop alacarte".
