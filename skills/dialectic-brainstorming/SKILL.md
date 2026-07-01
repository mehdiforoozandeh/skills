---
name: dialectic-brainstorming
description: >-
  Brainstorm a consequential, no-ground-truth question with a panel of diverse minds, then
  resolve it dialectically. A casting step derives orthogonal thinking-axes for the question
  (each a quality to maximize) and casts one persona per axis; the personas propose and
  cross-critique concrete candidates while a neutral Synthesizer prunes, recombines across
  axes, and holds a frontier — returning a short list, not one winner. Use for naming
  (products, tools, projects), positioning, or any choice of consequence with no objectively
  correct answer where you want many genuinely different perspectives, not one. Triggers:
  /dialectic-brainstorming, "brainstorm this with a diverse panel", "what should we name…",
  "give me a shortlist from multiple perspectives".
---

# dialectic-brainstorming — diverse minds diverge, dialectic converges

A sibling of `dialectic`. Where `dialectic` runs three *structural* roles (thesis/antithesis/
synthesis) to drive one question to a single answer, this skill runs **N diverse persona-minds**
that diverge through *different backgrounds*, then a neutral Synthesizer converges them to a
**short list** via dialectical sublation. Diversity is the engine of divergence; dialectic is
the engine of convergence.

Use it for consequential questions with **no ground-truth answer** — naming, positioning,
"which of these directions", any judgment call where you want many genuinely different minds
rather than one voice averaging over itself.

## Mechanism in one line

Cast orthogonal quality-axes → each persona maximizes its quality with concrete candidates →
they cross-critique → the Synthesizer prunes weak candidates *using the critiques* and
**recombines across axes** (crossover) onto a frontier → return the surviving short list.

## Two modes — pick before casting

Each subagent spawn costs ~27k tokens **flat** (the agent's system prompt + tool schemas
dominate; the brainstorming text is noise next to it). So **spawn count is the cost**, and the
mode is a cost/independence trade:

- **Batched (DEFAULT — low-to-mid-stakes).** A *single* subagent role-plays the whole panel in
  one call: give it all N axes/personas and have it return each persona's `PROPOSE`+`CRITIQUE`
  **independently and divergently** (instruct it explicitly: argue each persona on its own axis,
  do **not** let them agree or blur). Then one Synthesizer spawn. ≈ **2 spawns/round (~55k)**
  regardless of N. Saving vs isolated = the (N−1) persona-spawns you skip each round —
  **measured ~2× at N=3, scaling to ~3× at N=5** (not more; the Synthesizer spawn is unavoidable).
  You lose *true* isolation (one model holds all personas at once) but keep the structure, and in
  testing the personas stayed distinct and the critiques stayed axis-partisan.
- **Isolated (HIGH-STAKES only).** The full protocol below — one fresh subagent per persona per
  round, genuine independence (no persona ever sees another's reasoning). Costs ≈ **N+1
  spawns/round**; an N=3, 2-round run ≈ 16 spawns ≈ **430k tokens**. Use only when the decision
  is consequential enough to pay for real independence.

Default to batched. Escalate to isolated only when the user says it's high-stakes or explicitly
wants maximally independent minds.

## 1. Cast once (the divergence skeleton)

Before any brainstorming, analyze the question and derive orthogonal thinking-axes
*relevant to this question* — **3 by default**, 4–5 only if the question genuinely spans that
many distinct qualities. Each axis is defined by **a quality it optimizes**. For "name a CLI
tool": memorability, semantic fit/meaning, distinctiveness/ownability. For a strategy call,
entirely different axes.

Then cast **one persona per axis** — a single-quality maximizer with a concrete, question-fit
background and personality (e.g. a poet for aesthetics, a systems engineer for the technical
axis, a cognitive scientist for human factors, a sharp contrarian for the skeptic axis). The
background is **invented per question**, not fixed; the axis is the skeleton, the persona is
the flesh.

- Axes must be **orthogonal** — if two collapse into the same lens, merge them and add a real
  third.
- **Orthogonal axes do NOT guarantee orthogonal outputs.** Independent personas can still
  converge on the same obvious answer (e.g. every persona proposing the same metaphor). This is
  expected for questions with a strong attractor. Tell each persona to *differentiate from the
  obvious*, have the Synthesizer **de-duplicate** convergent proposals, and treat a full
  collapse as signal that the attractor may genuinely be the answer — not as failure.
- The **roster is frozen** after casting. Cast once, run to convergence. (Adaptive re-casting —
  swapping a dead axis for a live one mid-run — is a deliberate v2 extension, not v1.)
- Emit the roster up front so the user can watch and redirect:
  `AXES: memorability⟨the rapper⟩ · meaning⟨the etymologist⟩ · ownability⟨the trademark lawyer⟩ …`

## 2. The cast

- **N personas** (one per axis), **independent** quality-maximizers: each proposes concrete
  candidates that push *its* quality as far as possible and judges everything from *its* axis.
- **Synthesizer** — one neutral voice above the panel. Not a quality-maximizer; a
  **critique-guided integrator**. It prunes, de-duplicates, recombines across axes, holds the
  frontier, and detects convergence. The only convergence authority (keeps the stop signal clean).

**Frame-hardening (both modes).** Personas and Synthesizer operate in a **pure brainstorming
frame**. Tell each explicitly: *ignore any repository, file, or coding-task context; you are a
brainstorming voice, not a software agent.* Without this, `general-purpose` subagents leak meta
("this is a self-contained task, no codebase work needed"). Keep their output to the
`PROPOSE`/`CRITIQUE`/shortlist format only.

## The isolation rule (isolated mode)

In isolated mode, personas are **independent thinkers**: they never see each other's chain of
thought or system prompt — **only the relayed candidate pool** (conclusions, not reasoning).
No live persistent agent across rounds: **re-spawn a fresh agent each round and replay that
persona's own prior turns** into its prompt, so each accumulates memory of *its own* line
without ever seeing how the others think. Relay candidates and critiques, never internal
reasoning. (In batched mode this is enforced by instruction inside the single call instead.)

(Mechanism note: `SendMessage` live continuation is unavailable in this harness; re-spawn +
own-history replay is equivalent here, since personas exchange only final candidates/critiques.)

Spawn with `subagent_type: general-purpose`. Calling the skill is the authorization to spawn.

## 3. Round loop (default 2 rounds, hard cap 3; early-stop on a stable frontier)

Maintain the **current candidate pool** (each candidate tagged with its provenance — which
axis/axes authored it); in isolated mode also keep one running transcript per persona.

Per round:

1. **Personas — one combined turn each** (isolated: N spawns; batched: 1 spawn covering all).
   Each persona returns, in one turn:
   - `PROPOSE:` 1–3 new concrete candidates that maximize its quality, and
   - `CRITIQUE:` the single sharpest weakness in *other* candidates, judged from its axis.
   (Round 1 has nothing to critique — propose only. The critique is what does the real pruning,
   so a one-round run is the *weak* run; prefer 2 rounds when the decision matters.)
2. **Synthesizer.** Spawn with the full pool + this round's proposals/critiques. It:
   - **prunes** weak candidates — driven by the round's critiques (collisions, dead-on-an-axis),
     plus strict domination where it actually applies, and **de-duplicates** near-identical
     proposals from different personas,
   - **recombines across axes** — crossover: fuse the strengths of candidates from different
     axes into new hybrids (the memorable one's sound + the meaningful one's root), tagging the
     hybrid's provenance with all contributing axes — *this is where the best answers come from*,
   - updates the **frontier**, and emits a one-line digest.
3. **Stop** when the frontier is unchanged from the prior round (no new survivor), or at round 3.

## Running digest

One tight line per round, emitted as you go so the user can watch and interrupt:

```
R1  frontier: «cand-a»⟨mem,own⟩ «cand-b»⟨mean⟩ «cand-c»⟨aes⟩   (+2 new, −3 pruned)
R2  frontier: …
```

## 4. Output — the short list (no voting)

When the frontier stabilizes or the cap is hit, the Synthesizer returns the **short list**: the
surviving candidates, each annotated with **which axes it maximizes and which it sacrifices**,
plus **one line** of recommendation:

```
SHORTLIST
  1. «candidate»  — wins: memorability, ownability   sacrifices: literal meaning
  2. «candidate»  — wins: meaning, pronounceability  sacrifices: distinctiveness
  3. «candidate»  — balanced; no axis loves it, none hates it

PICK (if forced): #1 — strongest on the two axes hardest to fix later; meaning can be supplied by use.
```

No election, no forced winner — the user decides. The one-line pick is advisory and ignorable.
Return inline (these outputs are usually ephemeral; write a file only if the user asks).

## Notes

- **Cost is dominated by spawn count, not output length.** Measured: ~27k tokens per spawn,
  flat, whether the reply is 40 words or 220. Isolated N=3 × 2 rounds ≈ 16 spawns ≈ 430k tokens;
  one isolated round ≈ 4 spawns ≈ 110k; batched ≈ 2 spawns/round. **Default to batched; reserve
  isolated mode for genuinely consequential calls.**
- Crossover is the highest-value step — most picked answers are hybrids the Synthesizer built,
  not raw persona proposals. Protect it.
- In isolated mode run personas **in parallel within a round** (they're independent); the
  Synthesizer runs after. Rounds are serial.
- If the question turns out to **have** a ground-truth answer, or needs research not judgment,
  say so and stop — this skill is for genuine no-right-answer choices.
