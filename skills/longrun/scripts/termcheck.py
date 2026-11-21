#!/usr/bin/env python3
"""termcheck: flag terms an agent introduces that the PI has not used and that the
glossary does not register.

A term is the PI's when the PI typed it (pi_vocab.txt, pi_phrases.txt) or confirmed it
as known. Instruction documents do not count: agents often draft them.

Rules, in order, for each word of prose (code spans, paths, URLs and numbers skipped):
  1. known: the word or its stem is in pi_vocab.txt, or in a GLOSSARY.md term;
  2. ordinary English: wordfreq Zipf >= ZIPF (default 3.5);
  3. otherwise flagged ("rare").
Coined labels (letters mixed with digits, or snake_case) in prose are flagged unless the
PI typed them, the glossary registers them, or they appear in the PI's instruction folder
(the PI's own labels, such as decision ids). Accessions, hashes and chromosome names pass.
Ordinary words used as a new name ("oracle floor") cannot be told apart from plain
phrases by counts alone (measured on a 7-day run). The check therefore only counts
phrases; `candidates` lists the repeated ones for the auditor to judge.

Commands (run with the longrun venv python):
  seed [--before ISO]        add the PI's typed words from all Claude Code transcripts
  known <term>...            mark terms as the PI's (no glossary row needed)
  check [--file F] [--count] print flagged terms for text on stdin or in F, as JSON
  docs <folder>              list candidate terms in the PI's instruction documents
  candidates [--since ISO]   repeated phrases the PI never typed, for the auditor
  lint                       check GLOSSARY.md rows against the entry rules
  hook-user                  UserPromptSubmit hook: add the typed prompt to pi_vocab
  hook-stop                  Stop hook: check the reply; block once, then log
  hook-file                  PostToolUse hook: check files meant for the PI
"""
import glob
import json
import os
import re
import subprocess
import sys
import time

ZIPF = float(os.environ.get("LONGRUN_ZIPF", "3.5"))
PHRASE_N = int(os.environ.get("LONGRUN_PHRASE_N", "5"))
HERE = os.path.dirname(os.path.abspath(__file__))

STOP = set("""a about above after again against all also am an and any are as at be because been
before being below between both but by can could did do does doing done down during each either
every few for from further had has have having he her here hers him his how however i if in into
is it its itself just let may me might more most much must my no nor not now of off on once only
or other our ours out over own per same she should since so some such than that the their them
then there these they this those through thus to too under until up upon us very via was we were
what when where whether which while who whom whose why will with within without would yes yet
you your one two three four five six seven eight nine ten first second third new old more less
each many several next last same other another""".split())

WORD = re.compile(r"[A-Za-z][A-Za-z']*[A-Za-z]|[A-Za-z]")
LABEL = re.compile(r"\b(?:[A-Za-z]+\d+[A-Za-z0-9]*|[A-Za-z0-9]+_[A-Za-z0-9_]+)\b")
PASS_LABEL = re.compile(r"^(?:ENC[A-Z]{2}\d{3}[A-Z]{3}|[0-9a-f]{7,40}|chr[0-9XYM]+|v\d+|\d+[a-z]{1,3})$", re.I)
IRREGULAR = {"strata": "stratum", "data": "datum", "criteria": "criterion",
             "matrices": "matrix", "indices": "index", "analyses": "analysis"}


# ---------- text handling ----------

def strip_code(text):
    text = re.sub(r"```.*?```", " ", text, flags=re.S)
    text = re.sub(r"`[^`\n]*`", " ", text)
    text = re.sub(r"https?://\S+", " ", text)
    text = re.sub(r"\S*[/\\]\S*", " ", text)          # paths
    text = re.sub(r"\S+\.(?:py|sh|md|json|yaml|yml|txt|tsv|csv|pt|h5|tex)\b", " ", text)
    return text


def typed_only(text):
    """Keep only what a human typed: drop pasted blocks and harness-injected messages."""
    text = re.sub(r"<pasted_content[^>]*>.*?</pasted_content[^>]*>", " ", text, flags=re.S)
    text = re.sub(r"\"[^\"\n]{1,60}\"|\u201c[^\u201d\n]{1,60}\u201d", " ", text)   # quoted = mentioned, not used
    text = text.strip()
    if not text or text.startswith("<") or len(text) > 3000:
        return ""
    for p in ("This session is being continued", "Base directory for this skill", "Caveat:",
              "[Request interrupted", "Another Claude session sent", "[SYSTEM NOTIFICATION"):
        if text.startswith(p):
            return ""
    return text


def words(text):
    return [w.lower().strip("'") for w in WORD.findall(text)]


def stems(w):
    w = w.lower()
    if w.endswith("'s"):
        w = w[:-2]
    out = {w}
    for suf, rep in (("ies", "y"), ("es", ""), ("s", ""), ("ed", ""), ("ed", "e"),
                     ("ing", ""), ("ing", "e"), ("ly", "")):
        if w.endswith(suf) and len(w) > len(suf) + 2:
            out.add(w[: -len(suf)] + rep)
    if w in IRREGULAR:
        out.add(IRREGULAR[w])
    return out


def clauses(text):
    """Split prose into runs without punctuation, so phrases never cross a comma."""
    return re.split(r"[.,;:!?()\[\]{}\"|*#>\n—–]+", text)


def phrases(text):
    """Two-word phrases and hyphenated compounds in prose, lowercased."""
    out = set()
    for cl in clauses(strip_code(text)):
        toks = re.findall(r"[A-Za-z][A-Za-z'-]*[A-Za-z]", cl)
        for t in toks:
            if "-" in t:
                out.add(t.lower())
        toks = [t.lower() for t in toks if "-" not in t]
        for a, b in zip(toks, toks[1:]):
            if a in STOP or b in STOP or len(a) < 3 or len(b) < 3:
                continue
            out.add(a + " " + b)
    return out


# ---------- run files ----------

def find_root(start):
    d = os.path.realpath(start or ".")
    while d and d != "/":
        if os.path.isdir(os.path.join(d, ".longrun")):
            return d
        d = os.path.dirname(d)
    return None


class Run:
    def __init__(self, root):
        self.root = root
        self.dir = os.path.join(root, ".longrun")
        self.vocab = self._lines("pi_vocab.txt")
        self.pi_phrases = self._lines("pi_phrases.txt")
        self.gloss_terms = self._glossary()
        self.gloss_words = set()
        for t in self.gloss_terms:
            self.gloss_words |= set(words(t))
        p = os.path.join(self.dir, "term_counts.json")
        self.counts = json.load(open(p)) if os.path.exists(p) else {}
        self.doc_labels = self._doc_labels()

    def _doc_labels(self):
        prot = ""
        cfg = os.path.join(self.dir, "config")
        if os.path.exists(cfg):
            for line in open(cfg):
                if line.startswith("protected="):
                    prot = line.split("=", 1)[1].strip()
        out = set()
        if prot:
            for f in glob.glob(os.path.join(self.root, prot, "**", "*.md"), recursive=True):
                out |= set(m.group(0).lower() for m in LABEL.finditer(open(f, errors="ignore").read()))
        return out

    def _lines(self, name):
        p = os.path.join(self.dir, name)
        return set(l.strip().lower() for l in open(p)) - {""} if os.path.exists(p) else set()

    def _glossary(self):
        p = os.path.join(self.dir, "GLOSSARY.md")
        terms = set()
        if not os.path.exists(p):
            return terms
        for line in open(p):
            cells = [c.strip() for c in line.strip().strip("|").split("|")]
            if len(cells) < 2 or not line.startswith("|") or set(cells[0]) <= set("-: "):
                continue
            if cells[0].lower() in ("term",):
                continue
            terms.add(cells[0].strip("`*").lower())
        return terms

    def add_words(self, text):
        new_w = set(words(text)) - self.vocab
        new_p = phrases(text) - self.pi_phrases
        if new_w:
            with open(os.path.join(self.dir, "pi_vocab.txt"), "a") as f:
                f.write("".join(w + "\n" for w in sorted(new_w)))
            self.vocab |= new_w
        if new_p:
            with open(os.path.join(self.dir, "pi_phrases.txt"), "a") as f:
                f.write("".join(p + "\n" for p in sorted(new_p)))
            self.pi_phrases |= new_p
        return len(new_w), len(new_p)

    def save_counts(self):
        json.dump(self.counts, open(os.path.join(self.dir, "term_counts.json"), "w"))

    def known_word(self, w):
        s = stems(w)
        return bool(s & self.vocab) or bool(s & self.gloss_words)

    def known_phrase(self, p):
        if p in self.pi_phrases or p in self.gloss_terms:
            return True
        alt = p.replace("-", " ") if "-" in p else p.replace(" ", "-")
        return alt in self.pi_phrases or alt in self.gloss_terms


# ---------- the check ----------

_zipf = None


def zipf(w):
    global _zipf
    if _zipf is None:
        try:
            from wordfreq import zipf_frequency
            _zipf = zipf_frequency
        except ImportError:
            _zipf = lambda w, lang: 99.0   # without wordfreq, only labels are checked
    return _zipf(w, "en")


def check(run, text, reply_id=None):
    """Return flagged terms as dicts {term, kind}. With reply_id, update phrase counts."""
    flags = {}
    prose = strip_code(text)
    for m in LABEL.finditer(prose):
        tok = m.group(0)
        if tok.isdigit() or PASS_LABEL.match(tok):
            continue
        low = tok.lower()
        if low in run.doc_labels or low in run.gloss_terms or run.known_word(tok):
            continue
        flags[low] = "label"
    for w in set(words(re.sub(LABEL, " ", prose))):
        if len(w) < 3 or run.known_word(w):
            continue
        if any(zipf(s) >= ZIPF for s in stems(w)):
            continue
        flags.setdefault(w, "rare")
    if reply_id:
        day = time.strftime("%Y-%m-%d", time.gmtime())
        for p in phrases(text):
            if run.known_phrase(p):
                continue
            rec = run.counts.setdefault(p, {"n": 0, "first": day, "last": day})
            rec["n"] += 1
            rec["last"] = day
    return [{"term": t, "kind": k} for t, k in sorted(flags.items())]


def message(flags, where):
    terms = ", ".join(f"{f['term']} ({f['kind']})" for f in flags)
    return (f"Glossary check on {where}: these terms are neither the PI's words nor registered "
            f"in .longrun/GLOSSARY.md: {terms}. For each, either add a GLOSSARY.md row "
            f"(term, gloss of 10 words or fewer that does not use the term, origin, status "
            f"proposed, first use) or replace it with a conventional term the PI uses.")


def log(run, text):
    subprocess.run([os.path.join(HERE, "log.sh"), "--root", run.root, text], check=False)


# ---------- commands ----------

def user_texts(path, before=None):
    for raw in open(path, errors="ignore"):
        try:
            e = json.loads(raw)
        except ValueError:
            continue
        if e.get("type") != "user" or e.get("isSidechain") or e.get("isMeta") \
                or e.get("isCompactSummary"):
            continue
        if before and e.get("timestamp", "") >= before:
            continue
        c = e.get("message", {}).get("content")
        texts = [c] if isinstance(c, str) else [b.get("text", "") for b in c
                 if isinstance(b, dict) and b.get("type") == "text"] if isinstance(c, list) else []
        for t in texts:
            t = typed_only(t)
            if t:
                yield t


def cmd_seed(run, args):
    before = args[args.index("--before") + 1] if "--before" in args else None
    nw = np_ = 0
    for p in glob.glob(os.path.expanduser("~/.claude/projects/*/*.jsonl")):
        for t in user_texts(p, before):
            a, b = run.add_words(t)
            nw += a
            np_ += b
    for f in glob.glob(os.path.join(HERE, "..", "templates", "*.md")):
        a, b = run.add_words(open(f).read())     # the harness's own words
        nw += a
        np_ += b
    print(f"seeded {nw} words and {np_} phrases into {run.dir}")


def cmd_check(run, args):
    text = open(args[args.index("--file") + 1]).read() if "--file" in args else sys.stdin.read()
    rid = str(time.time()) if "--count" in args else None
    print(json.dumps(check(run, text, rid), indent=1))
    if rid:
        run.save_counts()


def cmd_docs(run, args):
    folder = args[0]
    counts = {}
    text_all = ""
    ref = re.compile(r"(et al\.|arXiv|doi\.org|doi:|\b(19|20)\d\d[a-z]?\)|Proceedings|Journal|Conference)", re.I)
    for f in sorted(glob.glob(os.path.join(folder, "**", "*.md"), recursive=True)):
        text = "\n".join(l for l in open(f, errors="ignore").read().splitlines() if not ref.search(l))
        text_all += text + "\n"
        for p in phrases(text):
            counts[p] = counts.get(p, 0) + text.lower().count(p)
    rare = [f for f in check(run, text_all) if f["kind"] != "repeated phrase"]
    reps = sorted((p for p, n in counts.items() if n >= 3 and not run.known_phrase(p)),
                  key=lambda p: -counts[p])
    print(json.dumps({"words_and_labels": rare,
                      "repeated_phrases": [{"term": p, "count": counts[p]} for p in reps[:80]]},
                     indent=1))


def cmd_candidates(run, args):
    since = args[args.index("--since") + 1][:10] if "--since" in args else ""
    rows = [(p, r) for p, r in run.counts.items()
            if isinstance(r, dict) and r["n"] >= PHRASE_N and r["last"] >= since
            and not run.known_phrase(p)]
    rows.sort(key=lambda x: -x[1]["n"])
    print(json.dumps([{"phrase": p, **r} for p, r in rows[:150]], indent=1))


def lint(run):
    """Problems in GLOSSARY.md rows: empty or long gloss, gloss using its own term,
    bad status, duplicate terms."""
    p = os.path.join(run.dir, "GLOSSARY.md")
    seen, out = set(), []
    for n, line in enumerate(open(p) if os.path.exists(p) else [], 1):
        cells = [c.strip() for c in line.strip().strip("|").split("|")]
        if not line.startswith("|") or len(cells) < 4 or set(cells[0]) <= set("-: ") \
                or cells[0].lower() == "term":
            continue
        term, gloss, status = cells[0].strip("`*").lower(), cells[1], cells[3].lower()
        if term in seen:
            out.append(f"line {n}: '{term}' is registered twice")
        seen.add(term)
        if status not in ("proposed", "approved", "known"):
            out.append(f"line {n}: status '{status}' must be proposed, approved or known")
        if status == "known":
            continue
        nw = len(gloss.split())
        if nw == 0 or nw > 10:
            out.append(f"line {n}: gloss of '{term}' has {nw} words; it needs 1 to 10")
        if set(words(term)) & set(words(gloss)):
            out.append(f"line {n}: gloss of '{term}' uses the term itself")
    return out


def cmd_lint(run, args):
    probs = lint(run)
    print("\n".join(probs) if probs else "GLOSSARY.md: no problems")
    sys.exit(1 if probs else 0)


def cmd_known(run, args):
    for t in args:
        t = t.lower().strip()
        if " " in t or "-" in t:
            open(os.path.join(run.dir, "pi_phrases.txt"), "a").write(t + "\n")
        else:
            open(os.path.join(run.dir, "pi_vocab.txt"), "a").write(t + "\n")
    print(f"marked {len(args)} terms as known")


def hook_input():
    try:
        return json.loads(sys.stdin.read() or "{}")
    except ValueError:
        return {}


def cmd_hook_user(_, __):
    d = hook_input()
    run = Run(find_root(d.get("cwd")) or "") if find_root(d.get("cwd")) else None
    if run:
        t = typed_only(d.get("prompt", ""))
        if t:
            run.add_words(t)


def cmd_hook_stop(_, __):
    d = hook_input()
    root = find_root(d.get("cwd"))
    if not root:
        return
    run = Run(root)
    text = d.get("last_assistant_message") or ""
    if not text.strip():
        return
    guard = os.path.join(run.dir, ".termcheck_blocked")
    sid = d.get("session_id", "")
    blocked_before = os.path.exists(guard) and open(guard).read().strip() == sid
    flags = check(run, text, None if blocked_before else str(time.time()))
    run.save_counts()
    if not flags:
        if blocked_before:
            os.remove(guard)
        return
    if blocked_before or d.get("stop_hook_active"):
        if os.path.exists(guard):
            os.remove(guard)
        log(run, "glossary: reply sent with unregistered terms: " +
            ", ".join(f["term"] for f in flags))
        return
    open(guard, "w").write(sid)
    print(json.dumps({"decision": "block", "reason": message(flags, "your last reply")}))


def cmd_hook_file(_, __):
    d = hook_input()
    f = (d.get("tool_input") or {}).get("file_path") or ""
    if not f or not os.path.exists(f):
        return
    root = find_root(os.path.dirname(f))
    if not root:
        return
    run = Run(root)
    rel = os.path.relpath(os.path.realpath(f), os.path.realpath(root))
    pats = ["STATE.md", ".longrun/STATE.md"]
    cfg = os.path.join(run.dir, "config")
    if os.path.exists(cfg):
        for line in open(cfg):
            if line.startswith("pi_files="):
                pats += [p.strip() for p in line.split("=", 1)[1].split(",") if p.strip()]
    import fnmatch
    if rel == os.path.join(".longrun", "GLOSSARY.md"):
        probs = lint(run)
        if probs:
            print(json.dumps({"decision": "block", "reason": "GLOSSARY.md breaks the entry rules: "
                              + "; ".join(probs)}))
        return
    if not any(fnmatch.fnmatch(rel, p) for p in pats):
        return
    flags = check(run, open(f, errors="ignore").read())
    if flags:
        print(json.dumps({"decision": "block", "reason": message(flags, rel)}))


COMMANDS = {"seed": cmd_seed, "check": cmd_check, "docs": cmd_docs, "known": cmd_known,
            "candidates": cmd_candidates, "lint": cmd_lint,
            "hook-user": cmd_hook_user, "hook-stop": cmd_hook_stop, "hook-file": cmd_hook_file}


def main():
    if len(sys.argv) < 2 or sys.argv[1] not in COMMANDS:
        print(__doc__)
        sys.exit(2)
    cmd = sys.argv[1]
    if cmd.startswith("hook-"):
        try:
            COMMANDS[cmd](None, sys.argv[2:])
        except Exception as e:            # a hook must never break the session
            sys.stderr.write(f"termcheck {cmd}: {e}\n")
        return
    root = find_root(os.getcwd())
    if not root:
        sys.exit("termcheck: no .longrun/ above the current folder")
    COMMANDS[cmd](Run(root), sys.argv[2:])


if __name__ == "__main__":
    main()
