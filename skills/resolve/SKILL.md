---
name: resolve
description: >-
  Resolve a stuck trade-off — "we can't improve A without hurting B" — by finding a
  structural fix that dissolves the conflict instead of trading along it. Names the single
  element that must be two things at once, then looks for the escape across four separations
  (space, time, condition, whole-vs-part), a reparameterization (derive B from A), and a trim.
  Lists only the moves that genuinely apply and is honest when none do — says "genuine
  trade-off, here's how to pick" rather than dressing up "you have to choose" as an escape.
  Use on nascent/stuck design tensions, NOT mature problems where only tuning is left.
  Triggers: /resolve, "resolve this trade-off", "can't improve X without hurting Y",
  "stuck on a trade-off", "break out of this frontier", "the same thing must be both … and …".
license: MIT
metadata:
  author: Mehdi Foroozandeh
  version: "1.0"
---

# resolve — dissolve a trade-off instead of trading it

A trade-off ("improving A worsens B") is usually handled by picking a point on the curve
and tuning. That's right when the curve is fundamental. But often the conflict is an
accident of how the thing is built, and a structural change dissolves it — you get both A
and B. This skill hunts for that change, and is honest when there isn't one.

Two failure modes it exists to prevent, in priority order:
1. **Confabulating a fix on a genuine dead-end** — the worst outcome. Never dress up "you
   have to pick" as an escape.
2. **Padding** — listing moves that don't really apply to look thorough. Two real
   resolutions beat six forced ones. A move that only restates the obvious is not a result.

## When to use it — and when not

- Use it on a genuine two-sided tension you're *stuck* on, especially a fresh design where
  you haven't found the trick yet.
- Skip it when the trade-off is well-charted and only tuning remains — say so and point to
  ordinary optimization. Ceremony on a mature curve loses to plain reasoning.

## The descent

**1. Name it.** State "improving A worsens B" and name the single element **E** that carries
both. If a hard identity binds (e.g. "output bits ≤ input bits", "cost = rate × time"), name
it now — it decides later whether a fix is real or just moves the work around.

**2. Sharpen.** Rewrite as "**E must be both X and not-X**" — concrete and opposite. This is
where the reframe lives. Keep it to one line; it's scaffolding, not the deliverable.

**3. Look for the escape.** Scan these; write down **only the ones that genuinely fit**, one
line why for each. For any that don't apply, a single "space: n/a — nothing varies by
location" is enough. Do not manufacture a candidate to fill a box.

- **Separate in space** — E is X in one place, not-X in another (path, region, instance).
- **Separate in time** — E is X now, not-X later (phases, staging, precompute; or *hide* the
  cost by batching/pipelining). A real later phase, not a reordered single pass.
- **Separate on condition** — E is X when C holds, else not-X: route by a runtime signal or a
  **threshold on the shared metric** (prefer that over a fixed class — it keeps the headline
  behavior universal).
- **Separate whole-vs-parts** — decompose the *requirement itself*: the whole is X, each part
  not-X (per-key, per-tier, per-segment). Also cut on the **unit**: can a cohort/aggregate
  guarantee replace the per-instance one (infer per cohort, not per user)?
- **Reparameterize (the highest-leverage move)** — can **B be derived as a function of A**, or
  of a signal already present, so the two stop being independent dials? Name the exact relation
  and the signal it rides on. (e.g. freshness from a content hash, not a tuned TTL.)
- **Shrink, don't just route** — can the quantity itself get *smaller* (smaller diffs, cheaper
  check, fewer touched parts) so the same budget goes further? Often beats a fancy separation.
- **Trim** — delete a part and show its job survives elsewhere. A fix that adds nothing beats
  one that adds a component. Run this even when a reparam seems to have swallowed it.

## Before you answer

- **Divergence check.** Ask: *what would a sharp expert reach for that this scan missed?* Name
  one resolution from an under-weighted angle, or state honestly that the scan already covers
  the obvious pass. The whole point of the protocol is to beat the obvious pass — if it didn't,
  say so.
- **Dedup.** Two moves that reduce to the same mechanism count as one; name the shared
  principle and drop the duplicate. Don't list both to pad.
- **Price each fix.** Name the cost it trades in — the new resource, failure mode, or
  complexity. A fix with no stated cost is under-examined.
- **Residual.** State what survives every move — the irreducible core, and whether a regime
  exists where all fixes fail at once. If a live trade-off remains, name the metric to choose
  the operating point.

## The honesty gate

Your output is valid only if **one** holds:
- it surfaces a resolution the asker didn't already name, **or**
- it declares **"no clean decoupling — genuine trade-off; here's how to choose,"** and says why.

Real trade-offs are common; "you have to pick" is a complete, correct answer. For a genuine
dead-end:
- State the binding constraint **first**, before any menu, so the list can't be mistaken for an escape.
- Tag each candidate as "routes around the constraint" or "claims to beat it"; kill any
  beat-it claim on its own terms or drop it.
- When the limit is a short provable bound (pigeonhole, an accounting identity), **skip the
  full scan** — state the bound, show why the escape families fail, give the honest pivot.

## Output

- **Contradiction:** A vs B; element E; the "both X and not-X" line; governing identity if any.
- **Resolutions:** only the moves that genuinely apply, each tagged (space / time / condition /
  whole-part / reparam / shrink / trim), concrete, with the cost it trades in.
- **Verdict:** "these N are worth trying, best = … (cost …)" **or** "genuine trade-off — the
  constraint is …; choose by …". Keep the prose plain — model the clarity you'd prescribe.
