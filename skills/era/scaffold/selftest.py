#!/usr/bin/env python3
"""End-to-end self-test for the ERA scaffold — no GPU, no tokens, no SLURM.

Verifies every harness piece works:
  1. futs        : verbatim FUTS converges on a numeric toy problem
  2. extension   : futs_batched.search matches futs.search (parity) + on_node
  3. batched     : futs_batched.batched_search converges, correct node count
  4. generate    : code-block extraction, prompt build, limit detection
  5. execute     : submit.sh render (gres on/off), footer parsing, REAL subprocess
  6. run         : full driver loop (mock) builds the tree + portfolio
  7. problem     : template get_problem() returns a valid ERA triple

Run:  python selftest.py
"""
from __future__ import annotations

import random
import sys
import tempfile

import futs
import futs_batched
import generate
import execute
import run
import problem_template


def test_futs() -> None:
    p = futs.Problem("maximise -(x-3)^2")
    init = futs.Solution("3.0")
    rng = random.Random(0)

    def gen(_p, parent, _s):
        return futs.Solution(f"{float(parent.program) + rng.uniform(-1, 1):.4f}")

    def ex(_p, sol):
        return -(float(sol.program) - 3.0) ** 2

    best, score = futs.search(p, init, ex(p, init), gen, ex, num_iterations=40, c_puct=0.5)
    assert score > -0.5, (best.program, score)
    print("  [1] futs.search (verbatim) converges ... PASS")


def test_extension_parity() -> None:
    """futs_batched.search must reproduce futs.search exactly (same RNG/gen/ex)."""
    p = futs.Problem("toy")
    init = futs.Solution("0.0")

    def make():
        rng = random.Random(7)
        gen = lambda _p, parent, _s: futs.Solution(f"{float(parent.program) + rng.uniform(-1, 1):.6f}")
        ex = lambda _p, sol: -(float(sol.program) - 3.0) ** 2
        return gen, ex

    g1, e1 = make()
    b1 = futs.search(p, init, e1(p, init), g1, e1, num_iterations=25, c_puct=0.7)
    g2, e2 = make()
    nodes = []
    b2 = futs_batched.search(p, init, e2(p, init), g2, e2, num_iterations=25,
                             c_puct=0.7, on_node=lambda nd: nodes.append(nd))
    assert b1[0].program == b2[0].program and abs(b1[1] - b2[1]) < 1e-12, (b1, b2)
    assert len(nodes) == 1 + 25                       # root + children logged
    print("  [2] futs_batched.search == futs.search .. PASS")


def test_batched() -> None:
    assert run.run_mock() == 0   # batched_search convergence + node count
    print("  [3] futs_batched.batched_search ........ PASS")


def test_generate() -> None:
    assert generate._selftest() == 0
    print("  [4] generate extraction/prompt ......... PASS")


def test_execute() -> None:
    assert execute._dry_run() == 0
    # real subprocess via interactive mode using the current interpreter
    with tempfile.TemporaryDirectory() as d:
        ex = execute.Executor(run_dir=d, python=sys.executable, exec_mode="interactive")
        score = ex(futs.Problem("x"), futs.Solution("print('hi'); print('ERA_SCORE: -0.4438')"))
    assert abs(score - (-0.4438)) < 1e-9, score
    # a crashing program must score FAIL
    with tempfile.TemporaryDirectory() as d:
        ex = execute.Executor(run_dir=d, python=sys.executable, exec_mode="interactive")
        score = ex(futs.Problem("x"), futs.Solution("raise SystemExit(1)"))
    assert score == execute.FAIL_SCORE, score
    print("  [5] execute render+parse+subproc ....... PASS")


def test_run_driver() -> None:
    # run_mock is exercised by [3]; here just confirm portfolio dedup logic.
    nodes = [
        {"index": 1, "score": -1.0, "program": "A"},
        {"index": 2, "score": -0.5, "program": "B"},
        {"index": 3, "score": -0.4, "program": "B"},   # duplicate program
        {"index": 4, "score": -2e9,  "program": "C"},  # failed -> excluded
    ]
    port = run._portfolio(nodes, k=5)
    # best-first; dedup keeps the highest-scoring copy of program "B" (node 3); fails excluded
    assert [n["index"] for n in port] == [3, 1], port
    print("  [6] run.py portfolio (dedup/rank) ...... PASS")


def test_problem() -> None:
    prob, sol, score = problem_template.get_problem()
    assert isinstance(prob, futs.Problem) and "ERA_SCORE" in prob.description
    assert isinstance(sol, futs.Solution) and "ERA_SCORE" in sol.program
    assert score is None or isinstance(score, float)
    assert compile(sol.program, "<baseline>", "exec")   # baseline is valid Python
    print("  [7] problem triple + baseline compiles . PASS")


if __name__ == "__main__":
    print("ERA scaffold selftest")
    test_futs()
    test_extension_parity()
    test_batched()
    test_generate()
    test_execute()
    test_run_driver()
    test_problem()
    print("ALL PASS")
