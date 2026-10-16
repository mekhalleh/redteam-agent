#!/usr/bin/env python3
"""engine/run.py — the orchestration-loop skeleton of redteam-agent (Stage 2).

It reads an engagement's git-ignored workspaces/<name>/scope.md, enforces the
engagement gate (type / mode / authorization — AGENTS.md directives 1 & 9),
lays out the ordered phase chain, and advances it ONE phase at a time behind a
human-in-the-loop checkpoint, logging every step.

NO OFFENSIVE ACTION is performed anywhere in this file — a phase is a planned
checkpoint, not an execution (real execution is Stage 5). The phases reference
the transferred knowledge by KB category; the knowledge itself is the synced
kb/kb-export.json (Stage 1b), never an exploit payload (directives 3 & 4).

All state and logs live inside the engagement's workspaces/<name>/ directory,
which is git-ignored (target data, loot and OPSEC stay local — directive 9).

Commands:
    engine/run.py init <name>       # scaffold workspaces/<name>/ + a scope.md template
    engine/run.py gate <name>       # parse scope.md, enforce the gate; exit 1 on failure
    engine/run.py plan <name>       # gate + print the phase chain + KB categories per phase
    engine/run.py advance <name>    # HITL checkpoint: advance one phase (refused if the gate fails)
    engine/run.py status <name>     # show the current phase state
"""
from __future__ import annotations

import datetime
import json
import os
import re
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
WORKSPACES = os.path.join(ROOT, "workspaces")
KB_EXPORT = os.path.join(ROOT, "kb", "kb-export.json")

TYPES = ("whitebox", "greybox", "blackbox", "redteam")
MODES = ("scoped", "blackhat")
TRACKS = ("machine", "challenge")

# The ordered phase chain per track. A phase names the knowledge it draws on by
# KB category (the categories emitted by htb-autopwn's kb-export.json); the
# mapping is indicative — the phase agents refine it. No category here is an
# instruction to execute anything.
PHASE_CHAINS = {
    "machine": [
        ("recon", ("services", "methodology")),
        ("web", ("web",)),
        ("access", ("vulns", "metasploit", "playbooks")),
        ("privesc", ("privesc",)),
        ("post-exploit", ("techniques", "intel")),
    ],
    "challenge": [
        ("challenge", ("techniques", "playbooks")),
    ],
}

SCOPE_FIELDS = ("type", "mode", "track", "authorization", "window", "contacts")

SCOPE_TEMPLATE = """\
# Engagement: {name}

This file is git-ignored (workspaces/ never leaves the machine). Fill every
field below, then run `engine/run.py gate {name}`. The gate refuses to start
while any field still holds a <placeholder>.

- type: <whitebox|greybox|blackbox|redteam>
- mode: <scoped|blackhat>
- track: <machine|challenge>
- authorization: <REQUIRED in every mode: a written-auth reference, platform ToS, or operator-owned lab>
- window: <engagement window, or n/a for own-lab/research>
- contacts: <point of contact, or operator>

## Targets in scope

- <target, host or CIDR — at least one>

## Targets out of scope

- <target, host or CIDR — or none>

## Notes

Authorization note: `blackhat` means no client scope document, NEVER no
authorization. Fill every field above; the gate refuses to start while any
field still holds an angle-bracket placeholder.

"""


def _now() -> str:
    # Local-only (workspaces/ is git-ignored), so a timestamp is fine here.
    return datetime.datetime.now().isoformat(timespec="seconds")


def _ws_dir(name: str) -> str:
    return os.path.join(WORKSPACES, name)


def _scope_path(name: str) -> str:
    return os.path.join(_ws_dir(name), "scope.md")


def _state_path(name: str) -> str:
    return os.path.join(_ws_dir(name), "engine-state.json")


def _log(name: str, msg: str) -> None:
    os.makedirs(_ws_dir(name), exist_ok=True)
    with open(os.path.join(_ws_dir(name), "engine.log"), "a", encoding="utf-8") as f:
        f.write("%s  %s\n" % (_now(), msg))


def _is_placeholder(value: str) -> bool:
    # A field is unfilled if it is empty or still carries a template marker.
    # Real values (hosts, CIDRs, "operator-owned lab", auth references) never
    # contain an angle bracket, so a stray '<' or '>' means "not filled in".
    return (not value) or ("<" in value) or (">" in value)


def parse_scope(name: str) -> dict:
    """Parse scope.md into {fields..., in_scope:[], out_scope:[]}. Lenient markdown."""
    path = _scope_path(name)
    if not os.path.isfile(path):
        raise FileNotFoundError(path)
    fields: dict = {k: "" for k in SCOPE_FIELDS}
    in_scope: list[str] = []
    out_scope: list[str] = []
    section = None
    for raw in open(path, encoding="utf-8"):
        line = raw.rstrip("\n")
        low = line.strip().lower()
        if low.startswith("## "):
            if "out of scope" in low:
                section = "out"
            elif "in scope" in low:
                section = "in"
            else:
                section = None
            continue
        # "- key: value" or "key: value"
        m = re.match(r"^\s*(?:[-*]\s*)?(?:\*\*)?([a-zA-Z_]+)(?:\*\*)?\s*:\s*(.*)$", line)
        if m and m.group(1).lower() in SCOPE_FIELDS:
            fields[m.group(1).lower()] = m.group(2).strip()
            continue
        # bullet items inside a scope section
        b = re.match(r"^\s*[-*]\s+(.*\S)\s*$", line)
        if b and section in ("in", "out"):
            item = b.group(1).strip()
            (in_scope if section == "in" else out_scope).append(item)
    return {**fields, "in_scope": in_scope, "out_scope": out_scope}


def gate(scope: dict) -> list[str]:
    """Return a list of gate failures. Empty list == the engagement may start."""
    errs: list[str] = []
    t = scope.get("type", "")
    if t not in TYPES:
        errs.append("type must be one of %s (got %r)" % ("/".join(TYPES), t))
    mode = scope.get("mode", "")
    if mode not in MODES:
        errs.append("mode must be one of %s (got %r)" % ("/".join(MODES), mode))
    track = scope.get("track", "")
    if track not in TRACKS:
        errs.append("track must be one of %s (got %r)" % ("/".join(TRACKS), track))

    # Authorization is mandatory in EVERY mode (directive 1/9).
    auth = scope.get("authorization", "")
    if _is_placeholder(auth):
        errs.append("authorization is missing or still a <placeholder> — "
                    "mandatory in every mode (blackhat is no scope doc, never no "
                    "authorization); stop and ask the operator")

    # At least one real in-scope target.
    real_in = [x for x in scope.get("in_scope", []) if not _is_placeholder(x)]
    if not real_in:
        errs.append("no in-scope target — list at least one host/CIDR the "
                    "operator owns or is authorized to test")

    # Scoped engagements need the RoE essentials filled (not 'n/a').
    if mode == "scoped":
        for f in ("window", "contacts"):
            v = scope.get(f, "")
            if _is_placeholder(v) or v.lower() == "n/a":
                errs.append("scoped mode requires %s (RoE) — not a placeholder/'n/a'" % f)
    return errs


def _load_kb_categories() -> tuple[dict | None, str | None]:
    """Return (counts-per-category, None) or (None, reason) if kb/ is not synced."""
    if not os.path.isfile(KB_EXPORT):
        return None, "kb/kb-export.json not found — run sync/pull.py (Stage 1b) first"
    try:
        doc = json.load(open(KB_EXPORT, encoding="utf-8"))
    except (json.JSONDecodeError, OSError) as e:
        return None, "kb/kb-export.json unreadable (%s)" % e
    counts: dict = {}
    for rec in doc.get("records", []):
        c = rec.get("category", "")
        counts[c] = counts.get(c, 0) + 1
    return counts, None


def _load_state(name: str) -> dict:
    try:
        return json.load(open(_state_path(name), encoding="utf-8"))
    except (FileNotFoundError, json.JSONDecodeError):
        return {}


def _save_state(name: str, state: dict) -> None:
    os.makedirs(_ws_dir(name), exist_ok=True)
    with open(_state_path(name), "w", encoding="utf-8") as f:
        json.dump(state, f, indent=2, sort_keys=True)
        f.write("\n")


# ----------------------------------------------------------------- commands

def cmd_init(name: str) -> int:
    path = _scope_path(name)
    if os.path.exists(path):
        print("engine: %s already exists — refusing to overwrite" % os.path.relpath(path, ROOT),
              file=sys.stderr)
        return 1
    for sub in ("recon", "loot", "notes", "flags"):
        os.makedirs(os.path.join(_ws_dir(name), sub), exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        f.write(SCOPE_TEMPLATE.format(name=name))
    _log(name, "init: scaffolded workspace + scope.md template")
    print("engine: scaffolded %s" % os.path.relpath(_ws_dir(name), ROOT))
    print("  edit %s, then: engine/run.py gate %s" % (os.path.relpath(path, ROOT), name))
    return 0


def _gate_or_report(name: str) -> tuple[dict | None, list[str]]:
    try:
        scope = parse_scope(name)
    except FileNotFoundError:
        print("engine: no scope.md for %r — run: engine/run.py init %s" % (name, name),
              file=sys.stderr)
        return None, ["missing scope.md"]
    return scope, gate(scope)


def cmd_gate(name: str) -> int:
    scope, errs = _gate_or_report(name)
    if scope is None:
        return 2
    if errs:
        print("engine: GATE FAILED for %r (%d issue(s)) — engagement does NOT start:" % (name, len(errs)))
        for e in errs:
            print("  - %s" % e)
        _log(name, "gate: FAILED (%d) — %s" % (len(errs), "; ".join(errs)))
        return 1
    print("engine: gate PASSED — %s/%s, track=%s, %d in-scope target(s)"
          % (scope["type"], scope["mode"], scope["track"], len([x for x in scope["in_scope"] if not _is_placeholder(x)])))
    _log(name, "gate: PASSED (%s/%s/%s)" % (scope["type"], scope["mode"], scope["track"]))
    return 0


def cmd_plan(name: str) -> int:
    scope, errs = _gate_or_report(name)
    if scope is None:
        return 2
    if errs:
        return cmd_gate(name)  # prints the failure
    chain = PHASE_CHAINS[scope["track"]]
    counts, kb_reason = _load_kb_categories()
    print("engine: plan for %r — %s/%s, track=%s" % (name, scope["type"], scope["mode"], scope["track"]))
    if kb_reason:
        print("  KB: %s (plan still shown; no phase will run without the KB and your go-ahead)" % kb_reason)
    else:
        print("  KB: kb/kb-export.json synced (%d records across %d categories)"
              % (sum(counts.values()), len(counts)))
    print("  phase chain (human-in-the-loop; NO offensive action in this skeleton):")
    for i, (phase, cats) in enumerate(chain):
        if counts is None:
            avail = "kb not synced"
        else:
            avail = ", ".join("%s=%d" % (c, counts.get(c, 0)) for c in cats)
        print("    %d. %-12s draws on KB [%s]" % (i + 1, phase, avail))
    _log(name, "plan: shown (%d phases, track=%s)" % (len(chain), scope["track"]))
    return 0


def cmd_advance(name: str) -> int:
    scope, errs = _gate_or_report(name)
    if scope is None:
        return 2
    if errs:
        print("engine: cannot advance — gate failed. Run: engine/run.py gate %s" % name, file=sys.stderr)
        _log(name, "advance: REFUSED (gate failed)")
        return 1
    chain = PHASE_CHAINS[scope["track"]]
    state = _load_state(name)
    idx = int(state.get("phase_index", 0))
    if idx >= len(chain):
        print("engine: all %d phase(s) already checkpointed for %r — engagement complete (skeleton)" % (len(chain), name))
        return 0
    phase, cats = chain[idx]
    print("engine: CHECKPOINT %d/%d — phase %r (track=%s)" % (idx + 1, len(chain), phase, scope["track"]))
    print("  the %r agent would draw on KB categories: %s" % (phase, ", ".join(cats)))
    print("  SKELETON: no offensive action is executed (that is Stage 5).")
    print("  review this checkpoint, then run `engine/run.py advance %s` again to move on." % name)
    state["track"] = scope["track"]
    state["phase_index"] = idx + 1
    state.setdefault("history", []).append({"phase": phase, "checkpointed_at": _now()})
    _save_state(name, state)
    _log(name, "advance: checkpoint %d/%d phase=%s" % (idx + 1, len(chain), phase))
    if idx + 1 >= len(chain):
        print("  (this was the last phase — engagement complete in the skeleton sense)")
    return 0


def cmd_status(name: str) -> int:
    scope, errs = _gate_or_report(name)
    if scope is None:
        return 2
    track = scope["track"] if scope["track"] in TRACKS else "machine"
    chain = PHASE_CHAINS.get(track, [])
    state = _load_state(name)
    idx = int(state.get("phase_index", 0))
    print("engine: status for %r — gate %s, track=%s" % (name, "FAILED" if errs else "PASSED", track))
    for i, (phase, _cats) in enumerate(chain):
        mark = "x" if i < idx else " "
        cur = "  <- next" if i == idx and not errs else ""
        print("    [%s] %d. %s%s" % (mark, i + 1, phase, cur))
    if idx >= len(chain) and chain:
        print("    all phases checkpointed.")
    return 0


COMMANDS = {
    "init": cmd_init,
    "gate": cmd_gate,
    "plan": cmd_plan,
    "advance": cmd_advance,
    "status": cmd_status,
}


def main(argv: list[str]) -> int:
    if len(argv) < 2 or argv[0] not in COMMANDS:
        print("usage: engine/run.py {%s} <name>" % "|".join(COMMANDS), file=sys.stderr)
        return 2
    name = argv[1]
    if not re.match(r"^[A-Za-z0-9][A-Za-z0-9._-]*$", name):
        print("engine: invalid workspace name %r" % name, file=sys.stderr)
        return 2
    return COMMANDS[argv[0]](name)


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
