---
name: dispatch
description: >-
  Pick the model tier for every subagent before spawning it, so cheap work runs on cheap
  models: Opus for anything that writes, runs, implements, designs, or carries consequence;
  Sonnet for read-only work like research, reading, and summarizing; a Haiku swarm when
  fanning out more than five agents on a breadth sweep or brainstorm.
  TRIGGER — read BEFORE any subagent spawn, including agents you decided to spawn on your
  own initiative and `agent()` calls inside a Workflow. Do not skip it because the task
  "looks obvious" — the lane is a two-second check and the default is wrong half the time.
  Also fires on /dispatch, "spawn subagents", "fan out", "run these in parallel", "use a
  swarm of agents", "which model should this agent use", "route this to a smaller model".
license: MIT
metadata:
  author: Mehdi Foroozandeh
  version: "1.0"
---

# dispatch — the right worker for the job

A subagent inherits the main loop's model unless you say otherwise. That means a `grep`
across a directory and a database migration both run on Opus, and you pay Opus rates for
both. Most delegated work does not need the best model in the lineup.

The output-token spread is 10× end to end: Haiku $5/M, Sonnet $15/M, Opus $25/M, Fable
$50/M. That spread pays off on volume, not on any single call — so route every spawn, and
never agonize over one.

## The lanes

Ask one question: **does this agent write or run anything?**

| Lane | `model` | When |
|---|---|---|
| **Build** | `opus` | Writes files, edits code, runs commands, implements, designs, works through complex logic, or produces a judgment you'll act on directly |
| **Read** | `sonnet` | Read-only. Search, research, market research, reading, extracting, summarizing, mapping a codebase. **Sonnet never writes.** |
| **Swarm** | `haiku` | Only inside a fan-out of **more than five read-only agents dispatched in one batch**, on a breadth sweep or brainstorm — where coverage matters more than any single agent's answer |

A judgment the parent will act on is Build-lane even when nothing gets written — reconciling
conflicting sources, picking between options, deciding whether something is sound. Plain
extraction and summary stay in Read.

"One batch" means spawned together in a single dispatch. Eight agents run two at a time
across a task are eight Read-lane agents, not a swarm.

**Opus is the ceiling.** Never auto-route to `fable`; a subagent smarter than the parent
means judging output the parent could not have produced. It unlocks only when the user
writes the word — *fable*, or a specific model ID. A capability request ("use the best
model", "this one's hard, go all out") is **not** naming it: that caps at `opus`.

**Haiku exists only in the swarm lane.** A lone Haiku agent is never the right call — if
it's worth one agent, it's worth Sonnet.

## Escalations

Four conditions override the lane and send the work to `opus`:

1. **A lower lane already came back thin, wrong, or hedged.** Retry one lane up. Do not
   re-prompt the same tier with a firmer instruction — the tier was the problem. **This
   escalation stops at `opus`** — it never reaches for `fable`. When an Opus agent comes
   back thin, the model was not the bottleneck: rewrite the brief, split it into narrower
   briefs, or do the work inline. Re-spawning on a *sharper* brief is fine — re-spawning
   the *same* brief is what never works.
2. **You can't tell which lane it is.** Ambiguity resolves upward.
3. **The brief is ambiguous or underspecified.** An agent that must infer the goal needs
   the judgment to infer it well.
4. **A read feeds something security- or correctness-critical you won't re-verify.**
   Read-only does not mean low-stakes.

Everything else stays in its lane. Don't invent a fifth condition mid-task.

## Depth

**Do not set an effort parameter** — subagents inherit the session's effort, and that's
correct. Shape depth through the prompt instead, which costs nothing:

- Swarm agents: *"Answer from the first solid match. Don't verify, don't survey alternatives."*
- Build agents on design or root-cause work: *"Verify by a second method before returning."*
- Read agents: neither — let them work at their natural depth.

## Say what you routed

Two things, both cheap:

- **One line before a batch**, before the spawn calls: *"7 haiku for the sweep, opus for
  the implementation."* When an escalation fired, name it in the same line: *"opus — the
  sonnet pass came back hedged."*
- **A model tag in every agent's `description`**, e.g. `review:auth [opus]`, so the routing
  is visible in the agent list without opening anything.

## Mechanics

Per call on the Agent tool — `model` takes the bare tier name, not a full model ID:

```
Agent({ description: "map auth flow [sonnet]", model: "sonnet", prompt: "..." })
```

Inside a Workflow, the same lanes apply to each `agent()` call:

```js
agent(prompt, { model: 'haiku', label: 'sweep:api [haiku]' })
```

Omitting `model` inherits the main loop. That is a routing decision too — make it on
purpose, not by forgetting.

## What this is not

- **Not for the main loop.** Dispatch routes subagents. Your own model is the user's choice.
- **Not a reason to spawn.** If the work is faster done inline, do it inline. Routing a
  subagent you shouldn't have spawned saves nothing.
- **Not a swarm generator.** Five-plus agents is a *precondition* for Haiku, not a target.
  Don't inflate a fan-out to unlock the cheap tier.

## Quick reference

```
writes / runs / implements / designs / consequential   → opus
judgment you'll act on, even with nothing written      → opus
read-only, single agent                                → sonnet
>5 read-only agents in one batch, breadth sweep        → haiku
unclear · underspecified · read feeding critical
  unverified work                                      → opus
sonnet/haiku came back thin                            → same task, one lane up
opus came back thin                                    → sharpen the brief, same lane
"use the best model" (fable not named)                 → opus
```
