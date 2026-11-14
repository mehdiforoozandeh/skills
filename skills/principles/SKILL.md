---
name: principles
description: >-
  Mehdi's principles for scientific thinking and problem solving. Apply when you plan an
  experiment, pick the next run, or spend compute. Also add a new principle on request.
  Triggers: "plan the experiment", "what should we run next", "add this principle",
  "our principles".
license: MIT
metadata:
  author: Mehdi Foroozandeh
  version: "1.0"
---

# principles

Each principle is one file in [`principles/`](principles/). The index below holds one
line per principle. Read the full file of every principle whose line bears on the task.

## Apply

1. Read the index. Pick each principle that bears on the current plan, run or decision.
2. Read the full file of each picked principle.
3. Check the plan against each picked principle's checks. Name each principle by its slug
   when it changes the plan, and say what it changed.

Done when every picked principle has either changed the plan or been named as already met.

## Index

- [`core-before-scale`](principles/core-before-scale.md) -- Find and tune the idea on the
  smallest prototype in fast cycles. Scale only when the problem needs it, and only after
  the prototype is ready.
- [`iterative-deployment`](principles/iterative-deployment.md) -- Deliver a long-running
  research task in iterations of days, in the order a paper is written: Methods first, then
  results, discussion and conclusions, each iteration a result that stands on its own.

## Add a principle

When Mehdi gives a new principle:

1. Pick a short kebab-case slug that names the principle. Check the index for a principle
   with the same meaning; if one exists, extend that file instead.
2. Write `principles/<slug>.md` from the template below. Keep his meaning exactly. Clean
   up wording only.
3. Add one index line: the slug, a link, and a one- or two-sentence summary.
4. Commit on a branch in `~/skills` and push.

Template:

```markdown
# <slug>

## Principle
<the idea, in Mehdi's meaning>

## Why
<the reason it holds>

## Checks
<questions the agent asks of a plan to apply it>
```
