# skills

Agent skills for [Claude Code](https://docs.claude.com/en/docs/claude-code) and other [skills.sh](https://www.skills.sh)-compatible agents, authored by [Mehdi Foroozandeh](https://mehdiforoozandeh.github.io).

These are **response-mode / collaboration skills** — they change *how* the agent thinks and replies, not what tools it has. Each is self-contained in a single `SKILL.md`.

## Install

Install all skills from this repo:

```bash
npx skills add mehdiforoozandeh/skills
```

Or pick one:

```bash
npx skills add mehdiforoozandeh/skills --list      # browse
npx skills add mehdiforoozandeh/skills -s dialectic # install one
```

Add `-g` to install globally (available in every project) instead of into the current project.

## Skills

| Skill | What it does | Triggers |
|-------|--------------|----------|
| [`dialectic`](skills/dialectic/SKILL.md) | Stress-tests a hard question to convergence via a three-agent loop — Thesis proposes, Antithesis attacks, Synthesis sublates into the next round's thesis. | `/dialectic`, "stress-test this to convergence" |
| [`hier`](skills/hier/SKILL.md) | Answers as a nested toggle-list tree (or a mermaid diagram for design/architecture) instead of prose, when the shape of the answer is a hierarchy. | `/hier`, "break this down", "as a hierarchy" |
| [`pingpong`](skills/pingpong/SKILL.md) | High-bandwidth collaboration mode: thinks deeply but replies in tight, one-idea-at-a-time turns that invite a reply. | `/pingpong`, "let's brainstorm", "design this with me" |
| [`brevity`](skills/brevity/SKILL.md) | Concise-and-clear response mode: answer first, every word load-bearing, no preamble/hedging/recap — but keeps full grammar and precision (not caveman fragments). | `/brevity`, "be concise", "no fluff", "get to the point" |
| [`era`](skills/era/SKILL.md) | Empirical-software search (a faithful port of Google's ERA / Flat UCB Tree Search): an LLM evolves whole candidate programs toward a scalar score, a flat PUCT bandit keeps a population and returns a diverse portfolio of winners. Ships a runnable scaffold + local example. | `era`, "evolutionary program search", `generate_fn/execute_fn` |

> **`era` note:** the generator shells out to the `claude` / `cursor-agent` CLIs (subscription-authed), so a full search needs one of those installed; the bundled California-Housing example runs locally with no GPU/SLURM/tokens. The search engine `skills/era/scaffold/futs.py` is vendored from [google-research/era](https://github.com/google-research/era) under Apache-2.0 — see [NOTICE](NOTICE).

## When to use which

The response-mode skills shape *how* an answer arrives. Each owns one axis, so they
compose — e.g. run `pingpong`'s rhythm in `brevity`-tight beats.

- **`brevity`** — there's a question; you want the answer dense, clear, and complete.
- **`pingpong`** — the work is collaborative (designing, deciding together); you want a
  tight back-and-forth, not a finished answer.
- **`hier`** — the answer's natural shape is a hierarchy you want to scan.
- **`dialectic`** — a hard question worth stress-testing to convergence from independent
  angles.

`brevity` governs the *density* of a turn, `pingpong` the *shape* of the exchange, `hier`
the *structure* of a single answer.

## Repository layout

```
skills/<name>/SKILL.md   # one directory per skill (flat catalog)
```

New skills are added as additional `skills/<name>/` folders.

## License

[MIT](LICENSE) © Mehdi Foroozandeh, except `skills/era/scaffold/futs.py`, which is
vendored from [google-research/era](https://github.com/google-research/era) under
Apache-2.0 (see [NOTICE](NOTICE)).
