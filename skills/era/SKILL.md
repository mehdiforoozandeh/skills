---
name: era
description: >-
  Run ERA-style empirical-software search (Google ERA / Flat UCB Tree Search) to
  evolve whole programs toward a scalar objective. Use for software/algorithm
  DESIGN: an LLM writes and rewrites complete candidate programs, a sandbox scores
  each, and a flat PUCT bandit (FUTS) keeps a population and decides which to
  improve next — escaping local optima and returning a diverse portfolio of
  winners. Domain-agnostic. Triggers: ERA, FUTS, Flat UCB Tree Search, empirical
  software search, evolutionary program search, generate_fn/execute_fn.
license: MIT
metadata:
  author: Mehdi Foroozandeh
  version: "1.0"
  notice: "Bundles scaffold/futs.py from google-research/era under Apache-2.0; see NOTICE."
---

# ERA — empirical-software search via Flat UCB Tree Search

Faithful port of Google Research's **ERA** ([Nature 2026](https://www.nature.com/articles/s41586-026-10658-6),
[repo](https://github.com/google-research/era)): an AI system that helps write
high-quality empirical software. An LLM proposes whole candidate **programs**, a
sandbox **scores** each, and a flat **PUCT bandit** (FUTS) decides which existing
solution to improve next — keeping a *population* and escaping local optima
instead of greedily climbing one trajectory. The candidate **is the source code**;
ERA evolves the algorithm/model/pipeline, not a config.

**What ERA is for:** optimizing a problem that already has (a) a runnable seed
program, (b) a fast automated scalar score, (c) a fixed problem definition. It
evolves the code *within* that frame — it does not invent the frame. Skip ERA for
problems with no automated score, or a single known change (just make it).

## The engine (`scaffold/futs.py` — FROZEN, vendored verbatim)

`futs.py` is vendored **verbatim** from `google-research/era`
(`implementation/futs.py`, commit `eb56676ce0a9b22b0c357c218de09ac61e94fc4b`,
Apache-2.0). It is the neutral judge — **never edit it during a search** (that
invalidates all node scores and cross-run comparison).

Primitives:
```python
Problem(description)         # the problem statement + interface + scoring contract
Solution(program)            # a complete, self-contained program (source text)
Node(index, parent_index, solution, score, num_visits, rank_score, puct)
search(problem, init_sol, init_score, generate_fn, execute_fn, num_iterations, c_puct=1.0)
generate_fn: (problem, parent_solution, parent_score) -> Solution
execute_fn:  (problem, solution) -> float
```

**PUCT selection** each iteration picks the node maximising
`rank_score + c_puct · (1/N) · √(total_visits) / (1 + num_visits)`, where
`rank_score = rank/(N−1)` ∈ [0,1] is the node's score normalised by rank, the
prior is uniform `1/N`, and a new node's visit **backpropagates up its ancestors**
(`backpropagate_visit`). "Flat" = one global pool ranked by score; the only tree
structure is parent links + ancestor visit-backprop. The `1/N` prior is
load-bearing: a constant prior makes exploration grow unbounded and never converge.

## Concurrency + logging (`scaffold/futs_batched.py` — labeled extension)

Upstream ships only the sequential `search()` with no node hook. This **separate,
non-upstream** module adds, reusing the frozen primitives unchanged:
- `search(..., on_node=...)` — identical behaviour to `futs.search` plus a per-node
  callback (for live `tree.json`). Parity is asserted in `selftest.py`.
- `batched_search(..., batch_size)` — selects B parents per round via **virtual
  visits** so B candidates are **executed concurrently** (B independent SLURM jobs).
  Generation stays sequential (one LLM call each); only execution is parallel.
  `batch_size=1` reduces to the sequential path.

## The pieces you author (per problem)

Copy `scaffold/` to a working dir. Only `problem.py` + `config.yaml` change.

| File | Role |
|------|------|
| `problem.py` | `get_problem() -> (Problem, initial_solution, initial_score)`. Start from `problem_template.py`. The `Problem.description` states the problem, the data/interface, the rules + fixed budget, and the **exact scoring contract**. `initial_solution` is a real runnable seed program (anchors the root); `initial_score=None` makes the driver score it once, or pass a float. **No baseline?** Ship a stub printing `ERA_SCORE: -1e9` and cold-start. |
| `config.yaml` | backend, exec_mode, `num_iterations`, `batch_size`, `c_puct`, SLURM knobs, paths. |
| `generate.py` / `execute.py` | The generic generator/executor (below). Rarely need edits. |

**Scoring contract.** Every candidate program must run under the fixed budget and
print exactly one line `ERA_SCORE: <float>` (higher = better). Crash / OOM /
timeout / missing footer → executor returns `-1e9` and FUTS abandons the node.
Define one clear objective in the problem and don't change it mid-search (it
invalidates cross-node comparison). The candidate runs in its own temp workdir;
it must be **self-contained** (no editing the scaffold or shared files).

## Generator — subscription-authed CLI, with failover

`generate_fn` shells out to a **terminal coding-CLI in headless mode**, billing
your *subscription* (included tokens), never a metered API key. Both run with a
hard timeout and stdin-piped prompt (Cursor's `-p` can hang otherwise).
- **Default: Claude / latest Opus** — `claude -p --model opus --output-format text`.
- **Failover: Cursor / latest Composer** — `cursor-agent -p -m composer --output-format text`.
  On a Claude rolling-limit hit (detected from output), switch for a cooldown,
  then re-probe and switch back once it recovers.
- Check availability: `python generate.py --check`.

## Execution — SLURM job per run (default) or interactive (off-cluster)

- **`sbatch_per_run` (default).** Each candidate is its own short SLURM job; a
  batch is submitted concurrently and harvested as jobs finish. All cluster
  specifics are config-driven: `account`, `gres` (omit for CPU clusters), `cpus`,
  `mem`, `time_limit`, and `setup_cmds` (env/module lines). Nothing cluster-specific
  is hardcoded.
- **`interactive`.** Runs each candidate as a local subprocess — on a held `salloc`
  allocation, or just locally for small problems / the regression example / selftest.

## Running a search

```bash
# from this skill's own directory (where this SKILL.md and scaffold/ live):
cp -r scaffold <workdir> && cd <workdir>
cp examples/regression/problem.py ./problem.py   # or write your own from problem_template.py
python selftest.py            # verify the harness (no GPU/tokens/SLURM)
python generate.py --check    # verify claude / cursor-agent are logged in
python run.py --config config.yaml
```

Output: `tree.json` (every node, rewritten live → resumable/inspectable) and a
printed **top-k diverse portfolio** — a set of strong, distinct programs, not just
the single best. A portfolio winner is a **hypothesis**: scores come off one
evaluation, so confirm a winner with a repeat run before trusting it.

## Worked example

`examples/regression/` — California Housing tabular regression (faithful to the
repo's `playground_s3e1`): the candidate is a whole program (load → features →
model → evaluate), scored by negative held-out RMSE. Runs locally with
`exec_mode: interactive` (no GPU/SLURM). Expect ERA to evolve the linear baseline
into feature engineering + gradient boosting.

## Defaults & knobs

- `c_puct` (default 1.0): lower → greedier exploit (→0 ≈ greedy hill-climb); higher
  → more breadth (too high → random thrash). Collapsing to one lineage → raise it;
  thrashing → lower it.
- `batch_size` (default 4): candidates per round = concurrent jobs (serial in `interactive`).
- `num_iterations`: total candidates generated+executed.
- Whole-program candidates are higher-variance than config knobs — expect many
  `-1e9` (broken imports, shape errors, NaN). Keep the seed clean and the scoring
  contract crisp; raise `c_puct` modestly so the search doesn't abandon the lineages
  that compile.

## Anti-patterns

- Editing `futs.py` (the frozen judge) or putting non-upstream logic inside it —
  extensions go in `futs_batched.py` and reuse its primitives.
- Non-self-contained candidates (editing the scaffold or shared files).
- A composite score with no clear main term, or changing the metric mid-search.
- Treating it as deep MCTS — it is *flat* UCB (one ranked pool; only ancestor
  visit-backprop, no value back-prop).
