#!/usr/bin/env python3
"""termcheck: flag terms an agent introduces that the PI has not used and that the
glossary does not register.

A term is the PI's when the PI typed it in chat (pi_vocab.txt, pi_phrases.txt) or wrote it
in the instruction folder (protected= in .longrun/config, read live).

Rules, in order, for each word of prose (code spans, paths, URLs and numbers skipped):
  1. the PI's: the word or its stem is in pi_vocab.txt;
  2. admitted: the word is a GLOSSARY.md term with status admitted (a phrase term unlocks
     only as the whole phrase);
  3. ordinary English: wordfreq Zipf >= ZIPF (default 3.5);
  4. otherwise flagged ("rare"; "rejected" if the glossary rejected it).
Coined labels (letters mixed with digits, or snake_case) in prose are flagged unless they
are the PI's. Accessions, hashes, chromosome and histone-mark names pass.
Ordinary words used as a new name ("oracle floor") cannot be told apart from plain
phrases by counts alone (measured on a 7-day run). The check therefore only counts
phrases; `candidates` lists the repeated ones for the auditor to judge.

Admission has no LLM and no PI step. `propose` admits a term only when it is an
established term: listed in MeSH or Papers with Code methods (fetch-lists), a single
word wordfreq knows (Zipf >= WORD_ZIPF), or found in at least TITLE_MIN paper titles (Europe PMC phrase search; OpenAlex too for
single words). snake_case labels are always rejected. Frequency cannot tell a known word
used in a new sense ("rung") from its usual sense, so such a word is admitted with its
gloss; the gloss is what tells the PI the meaning. Everything else is a coinage and is rejected; the agent uses plain
words or the PI's word instead. Agents cannot write GLOSSARY.md or the vocab files
directly (guard.sh).

Commands (run with the longrun venv python):
  seed [--before ISO]        add the PI's typed words from all Claude Code transcripts
  fetch-lists                download MeSH and Papers with Code names to LISTS_DIR
  propose <term> <gloss>     admit or reject a term and record the GLOSSARY.md row
  check [--file F] [--count] print flagged terms for text on stdin or in F, as JSON
  candidates [--since ISO]   repeated phrases the PI never typed, for the auditor
  lint                       check GLOSSARY.md rows against the entry rules
  hook-user                  UserPromptSubmit hook: add the typed prompt to pi_vocab
  hook-stop                  Stop hook: check the reply; block until it is corrected
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
TITLE_MIN = int(os.environ.get("LONGRUN_TITLE_MIN", "10"))
# wordfreq knows real words down to Zipf ~1 (reran 1.5, autoencoder 1.1); every coined
# token in a 7-day replay scored 0.0 (slotwise, sysvi, tagalign, mergeable).
WORD_ZIPF = float(os.environ.get("LONGRUN_WORD_ZIPF", "1.0"))
LISTS_DIR = os.path.expanduser(os.environ.get("LONGRUN_LISTS", "~/.claude/longrun-data"))
HERE = os.path.dirname(os.path.abspath(__file__))
OPEN = ("admitted", "approved", "known")     # statuses that unlock a term (last two: old rows)

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
PASS_LABEL = re.compile(r"^(?:ENC[A-Z]{2}\d{3}[A-Z]{3}|[0-9a-f]{7,40}|chr[0-9XYM]+|v\d+|\d+[a-z]{1,3}"
                        r"|H2A[XZ]?|H2B|H3(?:\.3)?|H4|(?:H2A|H2B|H3|H4)[KRST]\d+(?:me[123]?|ac|ph|ub)?)$", re.I)
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
    for pre in ("un", "re", "over", "under", "non", "mis", "pre"):
        for x in list(out):
            if x.startswith(pre) and len(x) - len(pre) >= 4:
                out.add(x[len(pre):])
    return out


def phrase_re(t):
    """Regex for a phrase term, matching space or hyphen joins and a plural s."""
    parts = re.split(r"[\s-]+", t.strip())
    return r"\b" + r"[\s-]+".join(re.escape(p) for p in parts) + r"s?\b"


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
        rows = self._glossary()
        self.gloss_terms = {t for t, s in rows.items() if s in OPEN}
        self.rejected = {t for t, s in rows.items() if s == "rejected"}
        p = os.path.join(self.dir, "term_counts.json")
        self.counts = json.load(open(p)) if os.path.exists(p) else {}
        self.doc_labels = self._doc_vocab()

    def _doc_vocab(self):
        """Words, phrases and labels in the PI's instruction folder count as the PI's."""
        prot = ""
        cfg = os.path.join(self.dir, "config")
        if os.path.exists(cfg):
            for line in open(cfg):
                if line.startswith("protected="):
                    prot = line.split("=", 1)[1].strip()
        out = set()
        if prot:
            for f in glob.glob(os.path.join(self.root, prot, "**", "*.md"), recursive=True):
                text = open(f, errors="ignore").read()
                out |= set(m.group(0).lower() for m in LABEL.finditer(text))
                self.vocab |= set(words(text))
                self.pi_phrases |= phrases(text)
        return out

    def _lines(self, name):
        p = os.path.join(self.dir, name)
        return set(l.strip().lower() for l in open(p)) - {""} if os.path.exists(p) else set()

    def _glossary(self):
        p = os.path.join(self.dir, "GLOSSARY.md")
        terms = {}
        if not os.path.exists(p):
            return terms
        for line in open(p):
            cells = [c.strip() for c in line.strip().strip("|").split("|")]
            if len(cells) < 4 or not line.startswith("|") or set(cells[0]) <= set("-: "):
                continue
            if cells[0].lower() in ("term",):
                continue
            terms[cells[0].strip("`*").lower()] = cells[3].lower()
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
        return bool(s & self.vocab) or bool(s & self.gloss_terms)

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
    for t in run.gloss_terms:                 # an admitted phrase unlocks only as a whole
        if " " in t or "-" in t:
            prose = re.sub(phrase_re(t), " ", prose, flags=re.I)
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
    for t in list(flags):
        if stems(t) & run.rejected:
            flags[t] = "rejected"
    for t in run.rejected:
        if (" " in t or "-" in t) and re.search(phrase_re(t), prose, re.I):
            flags[t] = "rejected"
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
    py = "~/.claude/longrun-venv/bin/python ~/.claude/skills/longrun/scripts/termcheck.py"
    return (f"Glossary check on {where}: these terms are neither the PI's words nor admitted "
            f"in .longrun/GLOSSARY.md: {terms}. For a term you believe is an established field "
            f"term (not one you or another agent coined), run `{py} propose \"<term>\" "
            f"\"<gloss of 1-10 words without the term>\"` once. If it is admitted, "
            f"gloss it for the PI. For every other term, including rejected ones and labels, "
            f"say it in plain words or in the PI's own words, and do not use it again in text "
            f"for the PI. Fix a reply with one short correction line, not a rewrite; fix a "
            f"file by editing it.")


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
        if status not in OPEN + ("rejected",):
            out.append(f"line {n}: status '{status}' must be admitted or rejected")
        if status in ("known", "rejected"):
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


def norm(t):
    return re.sub(r"[\s-]+", " ", t.strip().lower().strip(" `*\"'"))


_lists = None


def field_lists():
    """name -> source, from the files fetch-lists wrote."""
    global _lists
    if _lists is None:
        _lists = {}
        for src, f in (("MeSH", "mesh.txt"), ("Papers with Code", "pwc_methods.txt")):
            p = os.path.join(LISTS_DIR, f)
            if os.path.exists(p):
                for line in open(p, errors="ignore"):
                    if line.strip():
                        _lists.setdefault(norm(line), src)
    return _lists


def in_lists(term):
    L = field_lists()
    t = norm(term)
    parts = t.split(" ")
    for last in stems(parts[-1]):
        cand = " ".join(parts[:-1] + [last])
        if cand in L:
            return L[cand]
    return None


def title_hits(term, source):
    """Papers whose title contains the term; cached. None on failure.
    europepmc matches the exact phrase. openalex covers arXiv but matches words, not phrases
    ("base view" gave 4,370), so it is asked only about single words."""
    import urllib.parse
    import urllib.request
    cpath = os.path.join(LISTS_DIR, "title_cache.json")
    cache = json.load(open(cpath)) if os.path.exists(cpath) else {}
    t = norm(term)
    key = f"{source}:{t}"
    if key in cache:
        return cache[key]
    if source == "europepmc":
        url = ("https://www.ebi.ac.uk/europepmc/webservices/rest/search?format=json&pageSize=1"
               "&query=" + urllib.parse.quote(f'TITLE:"{t}"'))
        count = lambda d: d.get("hitCount", 0)
    else:
        url = ("https://api.openalex.org/works?per-page=1&select=id&filter=title.search:"
               + urllib.parse.quote(f'"{t}"'))
        count = lambda d: d.get("meta", {}).get("count", 0)
    req = urllib.request.Request(url, headers={"User-Agent": "longrun-termcheck"})
    for attempt in range(3):
        try:
            n = int(count(json.load(urllib.request.urlopen(req, timeout=20))))
            break
        except Exception:
            if attempt == 2:
                return None
            time.sleep(2)
    cache[key] = n
    os.makedirs(LISTS_DIR, exist_ok=True)
    json.dump(cache, open(cpath, "w"))
    return n


def judge(term):
    """(status, origin) for a proposed term. No LLM, no PI step."""
    t = norm(term)
    if "_" in term:
        return "rejected", "label: keep it in code spans"
    src = in_lists(t)
    if src:
        return "admitted", f"field: {src}"
    if " " not in t and 99.0 > zipf(t) >= WORD_ZIPF:
        return "admitted", f"English word, Zipf {zipf(t):.1f}"
    srcs = ("europepmc",) if " " in t else ("europepmc", "openalex")
    hits = {src: title_hits(t, src) for src in srcs}
    if all(n is None for n in hits.values()):
        return None, "title lookup failed; use plain words for now and retry later"
    src, n = max(((k, v or 0) for k, v in hits.items()), key=lambda x: x[1])
    name = {"europepmc": "Europe PMC", "openalex": "OpenAlex"}
    if n >= TITLE_MIN:
        return "admitted", f"field: {name[src]}, {n} titles"
    return "rejected", f"coinage: {n} titles in " + " and ".join(name[k] for k in srcs)


def cmd_propose(run, args):
    if len(args) != 2:
        sys.exit('usage: termcheck.py propose "<term>" "<gloss of 1-10 words>"')
    term, gloss = args[0].strip(), args[1].strip()
    key = term.lower().strip("`*")
    rows = run._glossary()
    if key in rows:
        print(f"'{term}' is already in GLOSSARY.md with status {rows[key]}")
        return
    nw = len(gloss.split())
    if not 1 <= nw <= 10 or set(words(term)) & set(words(gloss)):
        sys.exit("the gloss needs 1 to 10 words and must not use the term")
    status, origin = judge(term)
    if status is None:
        print(origin)
        sys.exit(1)
    gpath = os.path.join(run.dir, "GLOSSARY.md")
    day = time.strftime("%Y-%m-%d", time.gmtime())
    with open(gpath, "a") as f:
        f.write(f"| {term} | {gloss} | {origin} | {status} | {day} |\n")
    log(run, f"glossary: {status} '{term}' ({origin})")
    if status == "admitted":
        print(f"admitted '{term}' ({origin}). Gloss it the first time the PI reads it.")
    else:
        print(f"rejected '{term}' ({origin}). Use plain words or the PI's words instead.")


def cmd_fetch_lists(run, args):
    """MeSH descriptor names and entry terms, and Papers with Code method names."""
    import gzip
    import io
    import urllib.request
    import xml.etree.ElementTree as ET
    os.makedirs(LISTS_DIR, exist_ok=True)
    year = time.gmtime().tm_year
    names = set()
    for y in (year, year - 1):
        url = f"https://nlmpubs.nlm.nih.gov/projects/mesh/MESH_FILES/xmlmesh/desc{y}.gz"
        try:
            raw = urllib.request.urlopen(url, timeout=120).read()
        except Exception:
            continue
        for _, el in ET.iterparse(io.BytesIO(gzip.decompress(raw)), events=("end",)):
            if el.tag in ("DescriptorName", "Term"):
                s = el.findtext("String")
                if s:
                    names.add(s)
            if el.tag == "DescriptorRecord":
                el.clear()
        break
    open(os.path.join(LISTS_DIR, "mesh.txt"), "w").write("\n".join(sorted(names)) + "\n")
    print(f"MeSH: {len(names)} names")
    pwc, off = set(), 0
    base = ("https://datasets-server.huggingface.co/rows?dataset=pwc-archive/methods"
            "&config=default&split=train&length=100&offset=")
    while True:
        for attempt in range(5):
            try:
                d = json.load(urllib.request.urlopen(base + str(off), timeout=60))
                break
            except Exception as e:
                if attempt == 4:
                    sys.exit(f"Papers with Code fetch failed at row {off}: {e}")
                time.sleep(5 * 2 ** attempt)
        for r in d.get("rows", []):
            x = r["row"]
            try:
                npap = int(x.get("num_papers") or 0)
            except ValueError:
                npap = 0
            for k in ("name", "full_name"):
                v = (x.get(k) or "").strip()
                if npap >= 2 and v.isascii() and 0 < len(v.split()) <= 6 \
                        and not re.search(r"[?\[\]@+]|\d{3}", v):
                    pwc.add(v)
        off += 100
        if off >= d.get("num_rows_total", 0):
            break
        time.sleep(1.0)
    open(os.path.join(LISTS_DIR, "pwc_methods.txt"), "w").write("\n".join(sorted(pwc)) + "\n")
    print(f"Papers with Code: {len(pwc)} names; lists in {LISTS_DIR}")


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
    # The PI has already seen a blocked reply, so the fix is a short follow-up. That
    # follow-up may repeat the terms it corrects; any other flagged term blocks again.
    guard = os.path.join(run.dir, ".termcheck_blocked")
    sid = d.get("session_id", "")
    prev = {}
    if os.path.exists(guard):
        try:
            prev = json.load(open(guard))
        except ValueError:
            prev = {}
    excused = set(prev.get("terms", [])) if prev.get("sid") == sid else set()
    flags = [f for f in check(run, text, None if excused else str(time.time()))
             if f["term"] not in excused]
    run.save_counts()
    if os.path.exists(guard):
        os.remove(guard)
    if not flags:
        return
    json.dump({"sid": sid, "terms": sorted(excused | {f["term"] for f in flags})}, open(guard, "w"))
    log(run, "glossary: blocked reply with " + ", ".join(f["term"] for f in flags))
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


COMMANDS = {"seed": cmd_seed, "check": cmd_check, "propose": cmd_propose,
            "fetch-lists": cmd_fetch_lists,
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
    if cmd == "fetch-lists":
        COMMANDS[cmd](None, sys.argv[2:])
        return
    root = find_root(os.getcwd())
    if not root:
        sys.exit("termcheck: no .longrun/ above the current folder")
    COMMANDS[cmd](Run(root), sys.argv[2:])


if __name__ == "__main__":
    main()
