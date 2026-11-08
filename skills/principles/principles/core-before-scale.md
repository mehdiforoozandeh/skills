# core-before-scale

## Principle
Decouple the core of an idea from its scale. They are two separate axes of the work.

- Most experiments and tests can run on the smallest, most minimal version of the
  components, i.e. a prototype.
- Optimize the prototype first, in many fast cycles.
- Scale only when it is needed: the prototype benefits from scale, or the nature of the
  problem requires experiments at scale.
- When scale is needed, start scaling only after the prototype is ready. Scaling a ready
  prototype is the more straightforward step.

## Why
Scale takes the most time and compute. It is the bottleneck of each work cycle. A smaller
scale gives more cycles per day on the part of the work that decides whether the idea
holds.

## Checks
- What is the smallest data, model and compute that still tests the core idea?
- Does this run test the core, or does it test scale? If both, can the two be split?
- Is the prototype ready, i.e. does it work and is it tuned at small scale?
- Which result does the problem need that only scale can give? If none, do not scale.
