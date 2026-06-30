# skills

Agent skills for [Claude Code](https://docs.claude.com/en/docs/claude-code) and other [skills.sh](https://www.skills.sh)-compatible agents, authored by [Mehdi Foroozandeh](https://mehdiforoozandeh.github.io).

Most are **response-mode / collaboration skills** — they change *how* the agent thinks and replies, not what tools it has; a few package **domain workflows** (concrete setups and playbooks). Each is self-contained in a single `SKILL.md`.

> **[`crux`](https://github.com/mehdiforoozandeh/crux)** — an agentic research companion (a scientific-method lab notebook your LLM agent drives). Lives in its own repo: [mehdiforoozandeh/crux](https://github.com/mehdiforoozandeh/crux).

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

## Bootstrap a machine (`install.sh`)

To set up a complete agentic workflow on a new machine, compute cluster, etc. in one
command — my own skills **plus** a curated set of third-party skills:

```bash
git clone https://github.com/mehdiforoozandeh/skills.git ~/skills
~/skills/install.sh
```

This symlinks everything into `~/.claude/skills/` so Claude Code picks it up:

- **core** — my own skills (the `skills/*` folders in this repo)
- **external** — third-party skills declared in [`external-skills.txt`](external-skills.txt),
  cloned to `~/.claude/vendor-skills/` and tracking their default branch

```bash
./install.sh            # core + external   (default)
./install.sh --core     # only my own skills
./install.sh --external # only third-party skills
```

Re-run anytime to pull the latest of everything. The external list is plain text — one
line per entry (`owner/repo  subpath`); a trailing `/` on the subpath installs every
skill in that folder. Edit it to change my selection.

> The script only ever creates or refreshes symlinks it manages — it **never deletes**,
> and leaves any real (hand-placed) folder of the same name untouched. I don't vendor
> third-party `SKILL.md` files into this repo; only the reference to them.

## Skills

### Response-mode & collaboration

| Skill | What it does | Triggers |
|-------|--------------|----------|
| [`dialectic`](skills/dialectic/SKILL.md) | Stress-tests a hard question to convergence via a three-agent loop — Thesis proposes, Antithesis attacks, Synthesis sublates into the next round's thesis. | `/dialectic`, "stress-test this to convergence" |
| [`hier`](skills/hier/SKILL.md) | Answers as a nested toggle-list tree (or a mermaid diagram for design/architecture) instead of prose, when the shape of the answer is a hierarchy. | `/hier`, "break this down", "as a hierarchy" |
| [`pingpong`](skills/pingpong/SKILL.md) | High-bandwidth collaboration mode: thinks deeply but replies in tight, one-idea-at-a-time turns that invite a reply. | `/pingpong`, "let's brainstorm", "design this with me" |
| [`brevity`](skills/brevity/SKILL.md) | Concise-and-clear response mode: answer first, every word load-bearing, no preamble/hedging/recap — but keeps full grammar and precision (not caveman fragments). | `/brevity`, "be concise", "no fluff", "get to the point" |
| [`catchup`](skills/catchup/SKILL.md) | Session refresher for resuming a long chat after time away: scans the current transcript and distills one scannable screen — the thread, where we are (incl. locked decisions), what's waiting on you, and the next moves. Reads only the conversation, not git/files. | `/catchup`, "where were we", "catch me up", "refresh me" |
| [`era`](skills/era/SKILL.md) | Empirical-software search (a faithful port of Google's ERA / Flat UCB Tree Search): an LLM evolves whole candidate programs toward a scalar score, a flat PUCT bandit keeps a population and returns a diverse portfolio of winners. Ships a runnable scaffold + local example. | `era`, "evolutionary program search", `generate_fn/execute_fn` |

> **`era` note:** the generator shells out to the `claude` / `cursor-agent` CLIs (subscription-authed), so a full search needs one of those installed; the bundled California-Housing example runs locally with no GPU/SLURM/tokens. The search engine `skills/era/scaffold/futs.py` is vendored from [google-research/era](https://github.com/google-research/era) under Apache-2.0 — see [NOTICE](NOTICE).

### Domain workflows

| Skill | What it does | Triggers |
|-------|--------------|----------|
| [`latex-vscode`](skills/latex-vscode/SKILL.md) | Turns VS Code into an Overleaf-equivalent LaTeX setup with the LaTeX Workshop extension: build-on-save, PDF preview, SyncTeX, latexmk/bibtex, LTeX grammar, Live Share. A general local/remote playbook (compile from the CLI, diagnose `latexmk` errors, wire citations) with host-specific facts fenced off in their own section. | `latex`, `.tex`, "compile my paper", "build the pdf", SyncTeX, Overleaf |

## When to use which

The response-mode skills shape *how* an answer arrives. Each owns one axis, so they
compose — e.g. run `pingpong`'s rhythm in `brevity`-tight beats.

- **`brevity`** — there's a question; you want the answer dense, clear, and complete.
- **`pingpong`** — the work is collaborative (designing, deciding together); you want a
  tight back-and-forth, not a finished answer.
- **`hier`** — the answer's natural shape is a hierarchy you want to scan.
- **`dialectic`** — a hard question worth stress-testing to convergence from independent
  angles.
- **`catchup`** — you're returning to a long chat after a break and need a fast refresher
  on where things stand before continuing.

`brevity` governs the *density* of a turn, `pingpong` the *shape* of the exchange, `hier`
the *structure* of a single answer.

## Repository layout

```
skills/<name>/SKILL.md   # one directory per skill (flat catalog)
external-skills.txt       # curated third-party skills (references, not vendored)
install.sh                # bootstrap: symlink core + external into ~/.claude/skills
```

New skills are added as additional `skills/<name>/` folders; third-party skills are
added as lines in `external-skills.txt`.

## License

[MIT](LICENSE) © Mehdi Foroozandeh, except `skills/era/scaffold/futs.py`, which is
vendored from [google-research/era](https://github.com/google-research/era) under
Apache-2.0 (see [NOTICE](NOTICE)).
