#!/usr/bin/env python3
"""Worked ERA example — California Housing regression.

Faithful to the spirit of google-research/era's `playground_s3e1` end-to-end
example: a Kaggle-style tabular regression where the candidate is a WHOLE
self-contained program (data load -> features -> model -> evaluate -> score),
and ERA evolves the program to lower held-out RMSE.

Run this example:
    cp examples/regression/problem.py ./problem.py
    # set exec_mode: interactive in config.yaml (runs locally; no GPU/SLURM)
    python run.py --config config.yaml

Baseline below is a plain LinearRegression; expect ERA to discover feature
engineering + gradient boosting and climb the score.
"""
from __future__ import annotations

from futs import Problem, Solution

DESCRIPTION = """\
# Task: minimise held-out RMSE on the California Housing regression dataset.

You write a single self-contained Python program that:
  1. loads the dataset via `sklearn.datasets.fetch_california_housing()`,
  2. splits it with `train_test_split(..., test_size=0.2, random_state=0)`
     (KEEP this split fixed so candidates are comparable),
  3. trains any model / feature pipeline you like on the train split,
  4. predicts the test split and computes RMSE.

## Rules
- Self-contained: only stdlib, numpy, pandas, scikit-learn (assume installed).
- Do NOT change the split seed or test_size. No external data, no internet.
- Keep runtime modest (a few minutes on CPU).

## Scoring contract — the program MUST end by printing EXACTLY one line:
    ERA_SCORE: <float>
HIGHER is better; report the NEGATIVE test RMSE:
    ERA_SCORE = -sqrt(mean((y_pred - y_test)**2))
If the program fails or RMSE is non-finite, print `ERA_SCORE: -1e9`.
"""

BASELINE_PROGRAM = '''\
"""California Housing baseline for ERA — plain linear regression."""
import math
import numpy as np
from sklearn.datasets import fetch_california_housing
from sklearn.model_selection import train_test_split
from sklearn.linear_model import LinearRegression

try:
    X, y = fetch_california_housing(return_X_y=True)
    Xtr, Xte, ytr, yte = train_test_split(X, y, test_size=0.2, random_state=0)
    model = LinearRegression().fit(Xtr, ytr)
    pred = model.predict(Xte)
    rmse = math.sqrt(float(np.mean((pred - yte) ** 2)))
    score = -rmse if math.isfinite(rmse) else -1e9
except Exception as exc:  # any failure -> abandon node
    print(f"# failed: {exc!r}")
    score = -1e9
print(f"ERA_SCORE: {score:.6f}")
'''

INITIAL_SCORE = None  # driver scores the baseline once to anchor the root


def get_problem():
    return Problem(DESCRIPTION), Solution(BASELINE_PROGRAM), INITIAL_SCORE
