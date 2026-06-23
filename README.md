# skills

Agent skills for [Claude Code](https://docs.claude.com/en/docs/claude-code) and other [skills.sh](https://www.skills.sh)-compatible agents, authored by [Mehdi Foroozandeh](https://mehdiforoozandeh.github.io).

These are **response-mode / collaboration skills** — they change *how* the agent thinks and replies, not what tools it has. Each is self-contained in a single `SKILL.md`.

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

## Skills

| Skill | What it does | Triggers |
|-------|--------------|----------|
| [`dialectic`](skills/dialectic/SKILL.md) | Stress-tests a hard question to convergence via a three-agent loop — Thesis proposes, Antithesis attacks, Synthesis sublates into the next round's thesis. | `/dialectic`, "stress-test this to convergence" |
| [`hier`](skills/hier/SKILL.md) | Answers as a nested toggle-list tree (or a mermaid diagram for design/architecture) instead of prose, when the shape of the answer is a hierarchy. | `/hier`, "break this down", "as a hierarchy" |
| [`pingpong`](skills/pingpong/SKILL.md) | High-bandwidth collaboration mode: thinks deeply but replies in tight, one-idea-at-a-time turns that invite a reply. | `/pingpong`, "let's brainstorm", "design this with me" |

## Repository layout

```
skills/<name>/SKILL.md   # one directory per skill (flat catalog)
```

New skills are added as additional `skills/<name>/` folders.

## License

[MIT](LICENSE) © Mehdi Foroozandeh
