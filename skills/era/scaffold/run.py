#!/usr/bin/env python3
"""ERA driver — wires Problem + generate_fn + execute_fn into FUTS, logs every
node to tree.json, and reports the top-k diverse portfolio.

Search runs through `futs_batched` (the labeled extension): batch_size>1 uses
`batched_search` (concurrent execution), batch_size==1 uses the logged
sequential `search`. The frozen `futs.py` engine is the reference judge; the
extension reuses its PUCT/rank/backprop primitives unchanged.

Usage (from inside the copied tag dir):
    python run.py --config config.yaml
    python run.py --mock            # in-process self-test (no GPU, no tokens)

`tree.json` is rewritten after every node, so a search is resumable/inspectable
mid-flight and the portfolio survives a crash.
"""
from __future__ import annotations

import argparse
import importlib
import json
import sys
from pathlib import Path

import yaml

import futs
import futs_batched
from execute import Executor
from generate import Generator

HERE = Path(__file__).resolve().parent


def _write_tree(path: Path, nodes: list) -> None:
    path.write_text(json.dumps(nodes, indent=2))


def _portfolio(nodes: list, k: int) -> list:
    ranked = sorted([n for n in nodes if n["score"] > -1e8], key=lambda n: -n["score"])
    seen, out = set(), []
    for n in ranked:
        key = n["program"][:200]
        if key in seen:
            continue
        seen.add(key)
        out.append(n)
        if len(out) >= k:
            break
    return out


def run_real(cfg: dict) -> None:
    mod = importlib.import_module(cfg["problem_module"])
    problem, init_sol, init_score = mod.get_problem()

    gen = Generator(
        backend=cfg.get("backend", "claude"),
        claude_model=cfg.get("claude_model", "opus"),
        cursor_model=cfg.get("cursor_model", "composer"),
        timeout_s=int(cfg.get("generate_timeout_s", 600)),
        cooldown_s=int(cfg.get("cooldown_s", 1800)),
        fallback=bool(cfg.get("fallback", True)),
    )
    ex = Executor(
        run_dir=str(HERE / "runs"),
        python=cfg.get("python", sys.executable),
        exec_mode=cfg.get("exec_mode", "sbatch_per_run"),
        account=cfg.get("account", ""),
        gres=cfg.get("gres", ""),
        cpus=int(cfg.get("cpus", 2)),
        mem=cfg.get("mem", "4G"),
        time_limit=cfg.get("time_limit", "0:30:00"),
        setup_cmds=tuple(cfg.get("setup_cmds", ())),
        max_wall_s=int(cfg.get("max_wall_s", 5400)),
    )

    if init_score is None:
        print("Anchoring root: executing baseline once ...")
        init_score = ex(problem, init_sol)
        print(f"baseline score = {init_score:.6f}")

    tree_path = HERE / "tree.json"
    nodes: list = []

    def on_node(nd: futs.Node) -> None:
        run_dir = HERE / "runs"
        prog_path = ""
        for p in sorted(run_dir.glob("cand*/program.py")):
            if p.read_text() == nd.solution.program:
                prog_path = str(p.relative_to(HERE))
                break
        nodes.append({
            "index": nd.index, "parent_index": nd.parent_index,
            "score": nd.score, "num_visits": nd.num_visits,
            "program_path": prog_path, "program": nd.solution.program,
        })
        _write_tree(tree_path, nodes)

    num_it = int(cfg.get("num_iterations", 20))
    c_puct = float(cfg.get("c_puct", 1.0))
    batch = int(cfg.get("batch_size", 4))

    if batch > 1:
        best_sol, best_score = futs_batched.batched_search(
            problem, init_sol, init_score, gen, ex.run_batch,
            num_iterations=num_it, batch_size=batch, c_puct=c_puct, on_node=on_node,
        )
    else:
        best_sol, best_score = futs_batched.search(
            problem, init_sol, init_score, gen, ex,
            num_iterations=num_it, c_puct=c_puct, on_node=on_node,
        )

    print(f"\nBEST score = {best_score:.6f}")
    k = int(cfg.get("portfolio_k", 5))
    print(f"\nTop-{k} portfolio:")
    for n in _portfolio(nodes, k):
        print(f"  node {n['index']:>3}  score={n['score']:.6f}  {n['program_path']}")


def run_mock() -> int:
    """End-to-end driver test with a trivial numeric problem (optimum at 3.0)."""
    problem = futs.Problem("toy: maximise -(VALUE-3)^2")
    init = futs.Solution("VALUE = 0.0")

    import random
    rng = random.Random(0)

    def gen(_p, parent, _s):
        cur = float(parent.program.split("=")[1])
        return futs.Solution(f"VALUE = {cur + rng.uniform(-2, 2):.4f}")

    def ex_batch(_p, sols):
        return [-(float(s.program.split("=")[1]) - 3.0) ** 2 for s in sols]

    nodes: list = []
    best_sol, best_score = futs_batched.batched_search(
        problem, init, ex_batch(problem, [init])[0], gen, ex_batch,
        num_iterations=60, batch_size=4, c_puct=1.0,
        on_node=lambda nd: nodes.append(nd),
    )
    val = float(best_sol.program.split("=")[1])
    assert best_score > -0.25, (best_score, val)          # converged near optimum
    assert len(nodes) == 1 + 60                            # root + 60 children
    print(f"run.py mock: PASS  (best VALUE={val:.3f}, score={best_score:.4f}, nodes={len(nodes)})")
    return 0


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--config", default="config.yaml")
    ap.add_argument("--mock", action="store_true")
    args = ap.parse_args()
    if args.mock:
        sys.exit(run_mock())
    cfg = yaml.safe_load((HERE / args.config).read_text())
    run_real(cfg)
