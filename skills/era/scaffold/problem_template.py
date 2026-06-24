#!/usr/bin/env python3
"""Blank ERA problem template.

`get_problem()` returns the ERA triple: (Problem, initial_solution, initial_score).

Fill in three things:
  1. DESCRIPTION  — the scientific problem, the data/interface, the rules/budget,
     and the EXACT scoring contract (what `ERA_SCORE` must equal).
  2. BASELINE_PROGRAM — a real, runnable, self-contained program that solves the
     problem and prints `ERA_SCORE: <float>`. This anchors the search root.
       * If you have no baseline, set BASELINE_PROGRAM to a minimal stub that
         prints `ERA_SCORE: -1e9` and set INITIAL_SCORE = -1e9 (cold start).
  3. INITIAL_SCORE — None to have the driver run the baseline once to score the
     root, or a float if you already know it.

The candidate IS this program's source: the LLM rewrites the WHOLE program each
iteration (algorithm, models, features, structure) within the rules above.
"""
from __future__ import annotations

from futs import Problem, Solution

DESCRIPTION = """\
# Task: <one-line problem statement>

You write a single self-contained Python program that <solves X on data at Y>.

## Rules
- <what the program may/may not use; any fixed budget kept constant for comparability>
- The program must be self-contained and print exactly one score line.

## Scoring contract — the program MUST end by printing EXACTLY one line:
    ERA_SCORE: <float>
HIGHER is better: <define the objective precisely>. If the program fails or the
objective is non-finite, print `ERA_SCORE: -1e9`.
"""

BASELINE_PROGRAM = '''\
"""Baseline solution. Replace with a real runnable program for your problem."""
print("ERA_SCORE: -1e9")
'''

INITIAL_SCORE = None  # None -> driver scores the baseline once to anchor the root


def get_problem():
    return Problem(DESCRIPTION), Solution(BASELINE_PROGRAM), INITIAL_SCORE
