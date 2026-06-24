#!/usr/bin/env python3
"""generate_fn for ERA — a pluggable, subscription-authenticated CLI generator.

Shells out to a terminal coding-CLI in headless/print mode so generation is
billed against your *subscription* (included tokens), not a metered API key.
Two backends, subscription-only (no metered API fallback):

  - claude : `claude -p` with the latest Opus  (DEFAULT)
  - cursor : `cursor-agent -p -m composer`     (FAILOVER)

Failover: when Claude hits its rolling session/usage limit, switch to Cursor
(Composer) for a cooldown window, then probe Claude again and switch back once
it recovers. Both run with a hard subprocess timeout and the prompt piped on
stdin (no TTY) — Cursor's `-p` can otherwise hang.

The generator returns a whole program (ERA's `Solution`), extracted from the
model's fenced ```python block. The candidate IS the source code.

Self-tests (no tokens spent):
  python generate.py --selftest      # prompt + code-block extraction
  python generate.py --check         # report which CLIs are installed
"""
from __future__ import annotations

import argparse
import re
import shutil
import subprocess
import sys
import time
from dataclasses import dataclass, field
from typing import List

from futs import Problem, Solution

# Signals that Claude's rolling session / usage limit was hit.
LIMIT_PATTERNS = [
    r"5-?hour limit",
    r"usage limit",
    r"rate limit",
    r"limit reached",
    r"too many requests",
    r"reset[s]? at",
    r"please try again later",
]
_LIMIT_RE = re.compile("|".join(LIMIT_PATTERNS), re.IGNORECASE)
_PY_BLOCK_RE = re.compile(r"```(?:python|py)?\s*\n(.*?)```", re.DOTALL | re.IGNORECASE)


def make_prompt(problem: Problem, parent_solution: Solution, parent_score: float) -> str:
    return f"""{problem.description}

# Current program (score = {parent_score:.6f})
```python
{parent_solution.program}
```

# Your task
Propose ONE improved version of the program above that scores higher on the
stated objective. You have full freedom to redesign the program's algorithm,
structure, models, and methods within the rules in the problem description.
Keep it a single self-contained program that prints the required score footer.

Output ONLY the complete program in a single ```python code block. No prose
before or after the block."""


def extract_program(text: str) -> str:
    """Return the last fenced python block, else the last fenced block, else
    the stripped text."""
    blocks = _PY_BLOCK_RE.findall(text or "")
    if blocks:
        return blocks[-1].strip()
    generic = re.findall(r"```\s*\n(.*?)```", text or "", re.DOTALL)
    if generic:
        return generic[-1].strip()
    return (text or "").strip()


@dataclass
class Generator:
    backend: str = "claude"            # active backend
    claude_model: str = "opus"         # latest Opus alias
    cursor_model: str = "composer"     # latest Composer
    timeout_s: int = 600
    cooldown_s: int = 1800             # how long to stay on Cursor after a limit
    fallback: bool = True
    _cooldown_until: float = field(default=0.0, repr=False)

    # -- subprocess wrappers -------------------------------------------------

    def _cmd(self, backend: str) -> List[str]:
        if backend == "claude":
            return ["claude", "-p", "--model", self.claude_model, "--output-format", "text"]
        if backend == "cursor":
            return ["cursor-agent", "-p", "-m", self.cursor_model, "--output-format", "text"]
        raise ValueError(f"unknown backend: {backend}")

    def _run(self, backend: str, prompt: str):
        """Return (stdout_text, limited: bool, ok: bool)."""
        if shutil.which(self._cmd(backend)[0]) is None:
            return "", False, False
        try:
            proc = subprocess.run(
                self._cmd(backend),
                input=prompt,
                capture_output=True,
                text=True,
                timeout=self.timeout_s,
            )
        except subprocess.TimeoutExpired:
            return "", False, False
        blob = (proc.stdout or "") + "\n" + (proc.stderr or "")
        limited = bool(_LIMIT_RE.search(blob))
        ok = proc.returncode == 0 and bool(extract_program(proc.stdout))
        return proc.stdout, limited, ok

    # -- generation with failover -------------------------------------------

    def _generate_text(self, prompt: str) -> str:
        # Probe Claude again once the cooldown elapsed.
        if self.backend == "cursor" and time.time() >= self._cooldown_until:
            self.backend = "claude"

        out, limited, ok = self._run(self.backend, prompt)
        if ok:
            return out
        if limited and self.backend == "claude" and self.fallback:
            self._cooldown_until = time.time() + self.cooldown_s
            self.backend = "cursor"
            out2, _, ok2 = self._run("cursor", prompt)
            if ok2:
                return out2
            return out2 or out
        return out

    def __call__(self, problem: Problem, parent_solution: Solution, parent_score: float) -> Solution:
        prompt = make_prompt(problem, parent_solution, parent_score)
        text = self._generate_text(prompt)
        return Solution(program=extract_program(text))


# ---------------------------------------------------------------------------
# Self-tests
# ---------------------------------------------------------------------------


def _selftest() -> int:
    sample = (
        "Sure, here is the improved program:\n\n"
        "```python\nVALUE = 3.0\nprint('ERA_SCORE:', -(VALUE-3)**2)\n```\n\nDone."
    )
    prog = extract_program(sample)
    assert "VALUE = 3.0" in prog and "```" not in prog, prog
    # no-fence fallback
    assert extract_program("VALUE = 1") == "VALUE = 1"
    # limit detection
    assert _LIMIT_RE.search("You have reached your 5-hour limit, resets at 4pm")
    assert not _LIMIT_RE.search("training finished")
    # prompt is non-empty and embeds the parent program + score
    p = make_prompt(Problem("OBJ"), Solution("X=1"), -0.5)
    assert "OBJ" in p and "X=1" in p and "-0.500000" in p
    print("generate.py selftest: PASS")
    return 0


def _check() -> int:
    for name in ("claude", "cursor-agent"):
        path = shutil.which(name)
        print(f"  {name:14s} {'OK ' + path if path else 'NOT FOUND'}")
    return 0


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--selftest", action="store_true")
    ap.add_argument("--check", action="store_true")
    args = ap.parse_args()
    if args.check:
        sys.exit(_check())
    sys.exit(_selftest())
