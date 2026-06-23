---
name: dialectic
description: >-
  Resolve a hard question by running a three-agent dialectic: a Thesis agent proposes,
  an Antithesis agent attacks/questions, a Synthesis agent sublates (preserves +
  transcends) into a new position that becomes the next round's thesis. Iterates until
  the Synthesis agent declares a clear answer, or escalates to the user at 15 rounds.
  Use when user wants an idea stress-tested to convergence, a genuine truth-seeking
  back-and-forth (not a debate to win), or a tough design/research/conceptual question
  worked from multiple independent minds. Triggers: /dialectic, "run a dialectic on…",
  "thesis/antithesis/synthesis this", "stress-test this to convergence".
license: MIT
metadata:
  author: Mehdi Foroozandeh
  version: "1.0"
---

# dialectic — three independent minds, sublated to convergence

Run a Hegelian/Socratic loop over a question using **three persistent subagents**. The
orchestrator (you) is the conductor: you spawn the three, relay *only distilled messages*
between them, emit a running digest, and detect convergence. Genuine dialectic seeks a
commonly-held truth, not a winner — no rhetoric, no scoring, just position → contradiction
→ sublation.

## The three roles (independent, with per-role memory)

Three roles — Thesis, Antithesis, Synthesis (`subagent_type: general-purpose`). There is
no live persistent agent across rounds; instead you **re-spawn a fresh agent each round
and replay that role's own prior turns into its prompt**, so each role accumulates memory
of *its own* line of argument without ever seeing the others' reasoning.

- **Thesis** — proposes a position and its support.
- **Antithesis** — attacks it: strongest objection, the contradiction, the missing case,
  or a Socratic question that exposes a weak assumption.
- **Synthesis** — *sublates*: keeps what survives, drops what broke, forms a new position.

> Mechanism note: `SendMessage`-based live continuation is unavailable in this harness.
> Re-spawn + own-history-replay is equivalent for this protocol, since roles exchange only
> final messages, never internal thoughts — and you keep a per-role transcript of past
> turns to paste back in.

## The critical isolation rule

The three must be **independent thinkers**. They never see each other's chain of thought,
transcript, or system prompt. The **only** thing that crosses between them is the
distilled final message you relay:

- Thesis → you receive its **claim** (not its reasoning). You pass only the claim to Antithesis.
- Antithesis → you receive its **critique/question**. You pass thesis-claim + critique to Synthesis.
- Synthesis → you receive its **new position**. That becomes the next round's input to Thesis.

Do not paste one agent's internal reasoning into another's prompt. Relay conclusions, not thoughts.

## Round loop

You maintain three running transcripts (one per role), each a list of that role's prior
final messages. Every spawn = a fresh agent given its role prompt + its own transcript + this
round's new input.

1. **Thesis.** Spawn fresh; prompt = Thesis role + Thesis's own prior turns + this round's
   input. Round 1 input: the user's question. Round n>1 input: "Prior synthesis: «X».
   Defend or advance it." → returns a tight `CLAIM:`.
2. **Antithesis.** Spawn fresh; prompt = Antithesis role + Antithesis's own prior turns +
   *only* the thesis claim. → returns the single strongest objection/question (`CRITIQUE:`).
3. **Synthesis.** Spawn fresh; prompt = Synthesis role + Synthesis's own prior turns +
   thesis-claim + antithesis-critique. → returns either:
   - `CONVERGED: <answer>` — when the tension is resolved and the answer is clear, or
   - `NEXT THESIS: <new position>` (becomes next round's thesis input).
4. **Append** each role's return to its transcript. **Digest line** (see below).
5. Loop until `CONVERGED`, or stop at **round 15**.

## Running digest

One tight line per round, emitted as you go so user can watch and interrupt:

```
R1  T: <claim, few words>  →  A: <the hit>  →  S: <the move>
R2  T: …  →  A: …  →  S: …
```

## Convergence & escalation

- **Synthesis self-declares** (`CONVERGED`) → stop, present the final answer plus the
  digest of how it got there.
- **Hit round 15 with no convergence** → stop the loop and hand it to user: show the
  digest and the current synthesis, ask whether to continue, stop, or redirect. Never run
  past 15 rounds unattended.

## Notes

- Calling `/dialectic` is the explicit authorization to spawn agents.
- Run the three **sequentially** within a round (synthesis depends on the other two);
  rounds are inherently serial.
- The role prompt is fixed; only the replayed own-history and the round input change.
  Replay a role's *final messages* (CLAIM/CRITIQUE/position), not any narration around them.