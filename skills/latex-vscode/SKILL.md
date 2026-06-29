---
name: latex-vscode
description: >-
  Set up, compile, preview, and troubleshoot LaTeX in VS Code with the LaTeX
  Workshop extension — an Overleaf-equivalent local/remote workflow (build-on-save,
  PDF preview, SyncTeX, latexmk, bibtex citations, LTeX grammar, Live Share).
  Use whenever working with .tex/.bib files, building a PDF, fixing a
  LaTeX/latexmk compile error, wiring citations/bibliography, or configuring the
  LaTeX Workshop / LTeX / Live Share setup. Triggers: latex, .tex, latexmk,
  pdflatex, lualatex, bibtex, \cite, build the pdf, compile my paper, SyncTeX,
  Overleaf, LaTeX Workshop. NOT for writing prose (use scientific-writing) or
  generating BibTeX entries (use citation-management).
---

# LaTeX in VS Code (Overleaf-equivalent)

Turn VS Code into an Overleaf replacement and operate it from the CLI. The body
below is the general playbook; machine-specific facts are fenced in the last
section. Prefer **checks over assumptions** — verify each tool/path on the host
you're actually on.

## Mental model
LaTeX Workshop (`james-yu.latex-workshop`) is an **orchestrator, not a compiler**.
You need two things:
1. A **TeX distribution** providing `latexmk`, `pdflatex`/`lualatex`, `bibtex`
   (TeX Live / MacTeX / MiKTeX). Verify: `command -v latexmk pdflatex bibtex`.
   If absent, install one (`brew install --cask mactex`, `apt install
   texlive-full`, or an HPC module) — the extension ships none of these.
2. **LaTeX Workshop** + a few companions (LTeX for grammar, Live Share for
   collaboration, Code Spell Checker for spelling).

## Configuration
Settings location depends on context:
- **Local VS Code**: `~/.config/Code/User/settings.json` (Linux),
  `~/Library/Application Support/Code/User/settings.json` (macOS).
- **Remote-SSH / WSL / container**: server-side
  `~/.vscode-server/data/Machine/settings.json` (Machine scope = all folders on
  that host). There is no `~/.config/Code` on a Remote-SSH host.
- **Per-project override**: `.vscode/settings.json` in the workspace.

Recommended settings (the Overleaf build loop):
```jsonc
{
  "latex-workshop.latex.autoBuild.run": "onSave",   // recompile on save
  "latex-workshop.latex.recipe.default": "latexmk", // one recipe: pdflatex+bibtex+reruns
  "latex-workshop.latex.outDir": "%DIR%/build",     // isolate aux files -> clean tree
  "latex-workshop.view.pdf.viewer": "tab",          // PDF in a tab beside source
  "latex-workshop.synctex.afterBuild.enabled": true,// source <-> PDF jump
  "latex-workshop.message.error.show": true,
  "latex-workshop.message.warning.show": false,
  "[latex]": {
    "editor.formatOnSave": true,                    // latexindent (ships with TeX Live)
    "editor.defaultFormatter": "James-Yu.latex-workshop",
    "editor.wordWrap": "on"
  },
  "ltex.language": "en-US",
  "cSpell.language": "en"
}
```
After editing settings or installing an extension: **Developer: Reload Window**.

Install an extension headlessly (works over Remote-SSH too):
```bash
code --install-extension james-yu.latex-workshop
code --install-extension ltex-plus.vscode-ltex-plus      # grammar (maintained LTeX fork)
code --install-extension ms-vsliveshare.vsliveshare      # real-time collab
code --install-extension streetsidesoftware.code-spell-checker
```
On a Remote-SSH host the `code` CLI lives at
`~/.vscode-server/cli/servers/Stable-*/server/bin/remote-cli/code`.

## Project model
One folder = one "project" (like an Overleaf project), each with a `main.tex`.
Keep a template with `main.tex` + `refs.bib`; new paper = copy the folder.

## Compiling from the CLI (what LaTeX Workshop runs)
```bash
cd <project>
latexmk -synctex=1 -interaction=nonstopmode -file-line-error -pdf -outdir=build main.tex
```
- Output: `build/main.pdf`; `build/main.log` (errors); `build/main.bbl`
  (bibliography ran); `build/main.synctex.gz` (sync data).
- `lualatex` (fontspec/unicode-math): add `-lualatex` instead of `-pdf`.
- Clean rebuild: `latexmk -C -outdir=build main.tex`, then rebuild.

## Diagnosing failures
- Non-zero exit = real error. Locate it:
  `grep -nE "^.*:[0-9]+:|! |Undefined|Error" build/main.log | head`
- `Citation 'X' undefined` → key missing in `.bib`, or no `\bibliography{refs}`;
  latexmk reruns the bibtex pass automatically once those are fixed.
- `File 'X.sty' not found` → package not installed. If the TeX install is
  writable, `tlmgr install X`; if read-only (many HPC/shared installs), vendor
  the `.sty` next to `main.tex` or switch packages.
- Hang waiting for input → ensure `-interaction=nonstopmode`.

## Bibliography: bibtex vs biber
`natbib` + `bibtex` works on virtually every TeX install. `biblatex` needs
`biber` — **verify it exists first**: `command -v biber`. If absent, use
natbib/bibtex (latexmk's default recipe handles it).

## Editor workflow (Overleaf → VS Code)
| Overleaf | VS Code here |
|---|---|
| Recompile | Save (`Cmd/Ctrl+S`) — auto-rebuilds |
| PDF pane | Tab beside source (auto, or ▶/PDF icon) |
| Click PDF → source | `Cmd/Ctrl+click` in PDF (reverse SyncTeX) |
| Source → PDF | `Cmd/Ctrl+Alt+J` (forward SyncTeX) |
| Spell/grammar | LTeX+ underlines; fix via `Cmd/Ctrl+.` |
| Collaborate | Live Share sidebar → Share (session-based, via local VS Code) |
| History | Git (Source Control panel) |
| `\cite{`/`\ref{}` complete | Built into LaTeX Workshop, reads the `.bib`/labels |

## Compute Canada (this machine)
Facts verified on this Remote-SSH host (Fir / gentoo stack) — confirm with the
checks above if the cluster changes:
- LaTeX binaries are **already on PATH** via the cvmfs gentoo stack — no
  `module load` needed: `latexmk`, `pdflatex`, `lualatex`, `bibtex`, `latexindent`.
- **`biber` is absent** → use natbib/bibtex.
- TeX Live is a **shared read-only** cvmfs install → no `tlmgr install`; vendor
  missing `.sty` files into the project folder.
- Settings live at `~/.vscode-server/data/Machine/settings.json` (already
  configured per the block above).
- Starter project: `~/papers/example-paper/` (`main.tex` + `refs.bib`).
  New paper: `cp -r ~/papers/example-paper ~/papers/<name>`.
- **node/npx** (for `npx skills …`, unrelated to LaTeX) is not on the default
  PATH; load it inside one shell call:
  `bash -lc 'module load nodejs/24.15.0 >/dev/null 2>&1; npx ...'`
  (`module load` does not persist across separate Bash tool calls).

## Related skills
- Manuscript prose → `scientific-writing`.
- Generating/validating BibTeX entries → `citation-management`.
- Publication figures → `scientific-visualization`.
