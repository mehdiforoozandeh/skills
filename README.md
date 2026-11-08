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
| [`dialectic-brainstorming`](skills/dialectic-brainstorming/SKILL.md) | Brainstorms a no-ground-truth question with a panel of diverse, per-question-cast personas (one per orthogonal "quality" axis) that propose and cross-critique concrete candidates; a neutral Synthesizer prunes, recombines across axes (crossover), and returns an annotated short list — not one winner. Batched (cheap default) or isolated (fully independent) modes. | "brainstorm with a panel", "what should we name…", "give me a shortlist" |
| [`hier`](skills/hier/SKILL.md) | Answers as a nested toggle-list tree (or a mermaid diagram for design/architecture) instead of prose, when the shape of the answer is a hierarchy. Slash-only. | `/hier` |
| [`pingpong`](skills/pingpong/SKILL.md) | High-bandwidth collaboration mode: thinks deeply but replies in tight, one-idea-at-a-time turns that invite a reply. | "ping pong on it", "ask me with MCQs", "traverse the tree and ask me", "let's brainstorm", "design this with me" |
| [`terse`](skills/terse/SKILL.md) | Rapid-fire conversation mode for a queue of questions: hard-caps the turn at 3 sentences / ~50 words and *lets content go*, the way a colleague answers across a desk. Keeps commands, numbers and flags exact or omits them entirely; never trades investigation for a shorter answer; overflows only for irreversible-action warnings, which it refuses to soften into reassurance. | `/terse`, "be super brief", "quick answers", "rapid fire", "keep it moving" |
| [`bitesize`](skills/bitesize/SKILL.md) | Small-step research mode, the opposite of a big upfront plan: fixes the end goal first, then works one bite at a time — the agent frames where we are against the goal and lays out 2–3 next steps (cost, what each teaches, a lean); *you* make the call, often off-list; the agent runs only that step and reports outcome, meaning for the goal, and doubts, then stops. Flags drift once, never proposes a new goal, caps every message at 450 words, and logs silently into crux when the repo has a vault. | `/bitesize`, "one step at a time", "small steps", "let me make the calls" |
| [`alacarte`](skills/alacarte/SKILL.md) | `bitesize`'s companion for the second phase of experiment design, once goals and limits are set and only known-option choices remain (loss, architecture, preprocessing, split, metric): maps the design forks upstream-first, then asks each as a clickable MCQ with the agent's recommendation and why; allows several picks when an ablation makes sense (→ arms, with a default and a run count), prunes forks later answers make moot, and ends with a decision record. Runs as one bite inside `bitesize`. | `/alacarte`, "what are my options for X", "walk me through the choices for X" |
| [`mansplain`](skills/mansplain/SKILL.md) | Re-situates something the agent just said that drifted into ungrounded jargon or internal framing — not by dumbing it down (ELI5) but by filling in the missing context (brief backdrop → how it fits → where it lands in *this* conversation) with 1–2 concrete examples. Governed by one rule: say only what you're not sure the user already knows. | `/mansplain`, `/mansplain <term>`, "you lost me", "put that in perspective" |
| [`situate`](skills/situate/SKILL.md) | Re-orients you in one screen: the thread, where we are (incl. decisions made), what's waiting on you, and the next moves. Also resumes after a cluster tunnel drop or usage limit (re-reads status files and job ledgers, checks running jobs, never resubmits a logged job), says what we wait for and whether the laptop must stay open, and hands the project picture to `crux-situate` when the repo has a crux vault. | "where are we", "catch me up", "i just woke up", "what are we waiting for", "tunnel's back up", "limits are reset, continue" |
| [`era`](skills/era/SKILL.md) | Empirical-software search (a faithful port of Google's ERA / Flat UCB Tree Search): an LLM evolves whole candidate programs toward a scalar score, a flat PUCT bandit keeps a population and returns a diverse portfolio of winners. Ships a runnable scaffold + local example. | `era`, "evolutionary program search", `generate_fn/execute_fn` |
| [`quiz-me`](skills/quiz-me/SKILL.md) | Tests whether your mental model still matches work that already exists (code, a PRD, a plan): derives a tree from the artifact, then asks one MCQ at a time — general framing first, then hard into the decision points, with distractors drawn from the alternatives actually rejected — or, where nothing recorded them, from the conventional choice the artifact departed from, which is what you'd have assumed if you weren't watching. Triages every miss into *the agent drifted from your intent* (→ punch list) or *a gap on your side* (→ explained). | `/quiz-me`, "quiz me on this", "do I actually understand what we built", "am I still in sync with the code" |
| [`principles`](skills/principles/SKILL.md) | A growing set of principles for scientific thinking and problem solving, one file per principle under `skills/principles/principles/`, with a one-line index in `SKILL.md`. The agent checks plans and runs against the principles that apply, and adds a new principle when asked. | "plan the experiment", "what should we run next", "add this principle" |
| [`tutor`](skills/tutor/SKILL.md) | `quiz-me`'s mirror, for a subject you don't know yet: demands a grounding source (you name it, it asks, or it searches one out), shows the syllabus for your approval, then climbs a general→specific knowledge tree one MCQ at a time — short corrections, no walls of text to read, one-shot with no memory between sessions. | `/tutor`, "teach me X", "tutor me on X", "walk me up from the basics" |

> **`era` note:** the generator shells out to the `claude` / `cursor-agent` CLIs (subscription-authed), so a full search needs one of those installed; the bundled California-Housing example runs locally with no GPU/SLURM/tokens. The search engine `skills/era/scaffold/futs.py` is vendored from [google-research/era](https://github.com/google-research/era) under Apache-2.0 — see [NOTICE](NOTICE).

### Agent operations

| Skill | What it does | Triggers |
|-------|--------------|----------|
| [`dispatch`](skills/dispatch/SKILL.md) | Picks the model tier for every subagent before spawning it, so cheap work stops running on the expensive model. One question decides the lane — does this agent write or run anything? Opus for writes/runs/design/judgment you'll act on, Sonnet for read-only research and summarizing, a Haiku swarm only inside a >5-agent read-only breadth sweep. Opus is the ceiling; four escalations override the lane, and the retry escalation stops there rather than climbing past it. Routes the model only — effort stays inherited. | `/dispatch`, "spawn subagents", "fan out", "run these in parallel", "which model should this agent use" |
| [`orchestrate`](skills/orchestrate/SKILL.md) | Runs a multi-step task end to end as a foreman: a Fable planner writes a plan file of non-overlapping chunks, builder subagents build them in their own git worktrees, and the foreman only briefs, reads return slips and diffs, merges, logs, and re-briefs. Never does a chunk itself, so its context stays fresh for the whole run. Stops only for a decision that is the user's, a chunk that hit three retries, or a new dependency. Routes every spawn through `dispatch`. | "orchestrate", "orchestreate", "delegate to subagents and verify", "you orchestrate only" |
| [`handoff`](skills/handoff/SKILL.md) | Writes a handoff so a fresh agent session can continue the work: a full `HANDOFF_<date>_<slug>.md` on disk (goal, read-first paths, settled decisions, claims to re-verify, never-do list, traps, state, definition of done, stop condition) and a paste message under 4,000 characters that points to it. Only facts checked against disk or git. | "give me a handoff", "copy paste into a new agent", "fresh context", "new session" |
| [`introspect`](skills/introspect/SKILL.md) | Periodic self-review, run every few months. A script extracts what you typed since the last run; three reader agents in [`agents/`](agents/) (transcripts, instructions and memory, skills) find repeated asks, corrections, conflicts and dead weight; then it walks you through a decision list and applies what you approve (skills changes via PR). Outputs go to `~/workspace-review/<date>/`. | `/introspect [outside source]` (slash-only) |

### Domain workflows

| Skill | What it does | Triggers |
|-------|--------------|----------|
| [`latex-vscode`](skills/latex-vscode/SKILL.md) | Turns VS Code into an Overleaf-equivalent LaTeX setup with the LaTeX Workshop extension: build-on-save, PDF preview, SyncTeX, latexmk/bibtex, LTeX grammar, Live Share. A general local/remote playbook (compile from the CLI, diagnose `latexmk` errors, wire citations) with host-specific facts fenced off in their own section. | `latex`, `.tex`, "compile my paper", "build the pdf", SyncTeX, Overleaf |

## When to use which

The response-mode skills shape *how* an answer arrives. Each owns one axis, so they
compose — e.g. run `pingpong`'s rhythm in `terse`-short beats.

- **`terse`** — you have a *queue* of questions and want to keep firing: three sentences
  even when the full answer needs thirty, because you'll ask for the rest.
- **`pingpong`** — the work is collaborative (designing, deciding together); you want a
  tight back-and-forth, not a finished answer.
- **`bitesize`** — research (or any work) where you want to *make* every next decision
  yourself, one small step at a time toward a stated goal, instead of approving a long plan
  an agent then runs without you. Uses `terse` rules for your clarifying questions.
- **`alacarte`** — the goal is set and what is left is choosing among known options; you
  want to click through each design fork, with a recommendation on each, and pick several
  when you want an ablation. Usually offered from inside `bitesize`.
- **`hier`** — the answer's natural shape is a hierarchy you want to scan.
- **`mansplain`** — I drifted into terms or framing we never grounded and you want it pulled
  back: re-situated in *our* words (backdrop → picture → where we are, + a simple example),
  not explained like you're five. Says only what it's unsure you already know.
- **`dialectic`** — a hard question worth stress-testing to convergence from independent
  angles.
- **`dialectic-brainstorming`** — a consequential, no-right-answer choice (naming, positioning,
  "which direction") where you want many genuinely different minds to *generate and cross-critique*
  options, then a curated shortlist rather than a single verdict. (`dialectic`'s divergent sibling.)
- **`situate`** — you're back after a break, or the work stopped under you (tunnel down,
  usage limit, a job still running), and you need one screen on where things stand.
- **`handoff`** — this session is ending or full, and a fresh agent should pick up the work.
- **`quiz-me`** — a lot got built or planned while you steered at a distance, you don't want
  to read all of it, and you want to find where your picture and the artifact disagree — plus
  whether that's drift on the agent's side or a gap on yours.
- **`tutor`** — you want to be *taught* something you don't know yet, by answering questions
  rather than reading a lecture.
- **`orchestrate`** — a multi-step task you want done end to end by subagents while the main
  agent only plans, briefs, reviews and merges, so its context stays fresh. Pairs with
  `dispatch`, which picks the model for every agent it spawns.

`terse` governs the *ceiling* of a turn, `pingpong` the *shape* of the exchange, `hier` the
*structure* of a single answer. `dialectic` is the *reasoning* mode: it converges a contested
claim. `quiz-me` and `tutor` are the *interrogative* pair — one engine, opposite ground
truth: `quiz-me` tests you against an artifact that can itself be wrong, `tutor` teaches you a subject where every miss
is yours.

## Global CLAUDE.md

[`global-CLAUDE.md`](global-CLAUDE.md) is the `~/.claude/CLAUDE.md` these skills are
written against: response format, the "What I need from you" closing block, scope
bright lines, the check-the-authority rules, and delegating rules that point at
`dispatch`. Copy it to `~/.claude/CLAUDE.md` to use it.

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
