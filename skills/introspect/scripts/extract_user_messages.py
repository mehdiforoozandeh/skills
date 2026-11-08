#!/usr/bin/env python3
"""Extract the user's own typed messages from Claude Code transcripts, plus usage counts.

Usage:
    python3 -I extract_user_messages.py --out DIR [--since YYYY-MM-DD]

Writes:
    DIR/messages/<project>.txt   one file per project; sessions in time order, each message stamped
    DIR/usage.json               typed slash commands and Skill-tool calls, counted

Skips tool results, system reminders, task notifications, agent hand-backs, compaction
summaries and subagent (sidechain) records, so what remains is what the user typed.
Worktrees fold into their parent project. Read-only on ~/.claude/projects.
"""
import argparse
import collections
import glob
import json
import os
import re

NOISE_TAGS = ("system-reminder", "task-notification", "local-command", "agent-message",
              "side-sessions", "ci-monitor", "command-message")
SKILL_CALL = re.compile(r'"name":"Skill","input":\{"skill":"([^"]+)"')


def project_key(proj_dir):
    key = re.sub(r"--claude-worktrees-.*", "", proj_dir)
    key = re.sub(r"crux-auto-q\d+-.*", "crux-auto", key)
    return "tmp" if "private-tmp" in key else key.strip("-")


def message_text(record):
    c = record.get("message", {}).get("content")
    if isinstance(c, list):
        c = "\n".join(x.get("text", "") for x in c if isinstance(x, dict) and x.get("type") == "text")
    if not isinstance(c, str):
        return None
    c = c.strip()
    if not c:
        return None
    if c.startswith("<"):
        m = re.search(r"<command-name>(.*?)</command-name>.*?<command-args>(.*?)</command-args>", c, re.S)
        if m:
            return "[SLASH] " + m.group(1) + " " + m.group(2)[:300]
        if any(t in c[:200] for t in NOISE_TAGS):
            return None
    if c.startswith(("This session is being continued", "Caveat:")):
        return None
    c = re.sub(r"<system-reminder>.*?</system-reminder>", "", c, flags=re.S).strip()
    return c[:4000] or None


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", required=True)
    ap.add_argument("--since", default="", help="only messages on or after this date (YYYY-MM-DD)")
    args = ap.parse_args()
    os.makedirs(os.path.join(args.out, "messages"), exist_ok=True)

    groups = collections.defaultdict(list)
    slash, skills = collections.Counter(), collections.Counter()
    for f in glob.glob(os.path.expanduser("~/.claude/projects/*/*.jsonl")):
        msgs = []
        with open(f, errors="ignore") as fh:
            for line in fh:
                try:
                    d = json.loads(line)
                except ValueError:
                    continue
                ts = d.get("timestamp", "")
                if args.since and ts[:10] < args.since:
                    continue
                for s in SKILL_CALL.findall(line):
                    skills[s] += 1
                if d.get("type") != "user" or d.get("isMeta") or d.get("isSidechain"):
                    continue
                text = message_text(d)
                if text:
                    msgs.append((ts, text))
                    if text.startswith("[SLASH] "):
                        slash[text.split()[1]] += 1
        if msgs:
            key = project_key(os.path.basename(os.path.dirname(f)))
            groups[key].append((msgs[0][0], os.path.basename(f), msgs))

    for key, sessions in groups.items():
        sessions.sort()
        with open(os.path.join(args.out, "messages", key + ".txt"), "w") as o:
            for ts, fn, msgs in sessions:
                o.write(f"\n\n######## SESSION {fn} start {ts}\n")
                for t, c in msgs:
                    o.write(f"\n--- [{t[:16]}]\n{c}\n")

    with open(os.path.join(args.out, "usage.json"), "w") as o:
        json.dump({"since": args.since or None,
                   "slash_commands_typed": slash.most_common(),
                   "skill_tool_calls": skills.most_common(),
                   "note": "Skill-tool counts include forked copies of sessions; their order is reliable, their size is inflated."},
                  o, indent=2)
    n = sum(len(m) for s in groups.values() for _, _, m in s)
    print(f"{n} messages from {len(groups)} projects -> {args.out}")


if __name__ == "__main__":
    main()
