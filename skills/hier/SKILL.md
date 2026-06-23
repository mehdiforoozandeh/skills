---
name: hier
description: >-
  Hierarchical-outline response mode: answer as a nested-bullet toggle list (a tree),
  not prose. Use when user wants a response structured as a hierarchy — designing a
  project/system from scratch (goal → main components → subcomponents → …), breaking a
  problem down, mapping structure, or any answer where the shape is a tree and they want
  to scan it at a glance. Each node is a few words. Design/architecture hierarchies
  auto-render as a mermaid diagram instead. Triggers: /hier, "give me the outline",
  "as a hierarchy", "as a toggle list", "break this down", "structure this".
license: MIT
metadata:
  author: Mehdi Foroozandeh
  version: "1.0"
---

# hier — answer as a hierarchy, not prose

people think in hierarchies and graphs. Switch the response from paragraphs to a
**nested-bullet tree** they can scan top-down. The structure carries the meaning; words
are labels, not sentences.

## The format

- **Nested bullets, indented by level.** Top bullet = the root (the goal / the whole
  thing). Each level down = a decomposition of its parent.
- **Each node is a few words.** Hard cap: one short sentence; aim for 2–5 words. If a
  node needs explanation, it's really two nodes — split it.
- **Design top-down.** Goal → main components → subcomponents → leaves. Don't start at
  details; start at the root and decompose.
- **No prose around it.** No intro paragraph, no summary after. The tree is the answer.
  At most one short clarifying question at the end if a branch is genuinely ambiguous.

Example shape:

- Goal: imputation harness from scratch
  - Data layer
    - HDF5 slice loader
    - covariate encoder
  - Model
    - conv towers
    - transformer backbone
  - Eval
    - calibration
    - C-index

## When to render mermaid instead

If the hierarchy is a **design / architecture / system structure** (components and how
they nest or connect), render it as a `mermaid` `flowchart TD` or `graph` instead of
bullets — diagram only, no bullet copy beneath it. The diagram *is* the glanceable view.

For non-structural hierarchies (a breakdown of steps, a taxonomy, a list of options),
stay in nested bullets.

## Fallback

Mermaid gets unreadable past **~3 levels deep or many nodes**. When the tree is too big
to render cleanly, drop back to nested bullets — readability beats the diagram.

## What breaks the mode

- Paragraphs, or sentences as bullet items.
- An intro ("Here's the hierarchy:") or a wrap-up summary.
- Nodes that are full explanations instead of labels.
- Bullets *and* a mermaid diagram of the same tree (pick one per the rules above).

## When to break it

If user asks for prose, detail on one node, or code — give it. hier mode is for
conveying structure; expand a branch in normal text when asked, then return to the tree.