#!/usr/bin/env python3
"""validation/check.py — knowledge-regression harness of redteam-agent (Stage 3).

A documented *vector* records which KB techniques a validated attack path relied
on, and the knowledge version it was validated against. This harness re-checks
each vector against the currently synced kb/kb-export.json and reports whether
the knowledge it depends on still holds:

    PASS      — every referenced KB record is present and unchanged (same content_sha256)
    DRIFTED   — a referenced record still exists but its content_sha256 moved → re-validate
    MISSING   — a referenced record is gone from the KB → regression

This is a regression check over the TRANSFERRED KNOWLEDGE (Stage 1b), not a live
attack: nothing is executed against any target here. Live replay of a vector on
an authorized target is Stage 5 (operator-gated, rig-backed). References and
metadata only — a vector never carries a payload (AGENTS.md directives 3 & 4).

Vectors are small JSON files (references only) under validation/vectors/, or a
path passed with --vector. Schema (see validation/vectors/README or a sample):

    {
      "id": "sample-linux-sudo-gtfobins",
      "description": "short prose — what path this vector documents",
      "knowledge_version": "<handbook_version when validated>",
      "maturity": "stable|draft",
      "kb_records": [ { "id": "privesc/gtfobins-linux",
                        "content_sha256": "<sha at validation time>" } ]
    }

Usage:
    validation/check.py                 # check every vector under validation/vectors/
    validation/check.py --vector <p>    # check one vector file
    validation/check.py --json          # machine-readable report on stdout
Exit: 0 if all PASS/DRIFTED, 1 if any MISSING (regression) or a vector is invalid.
"""
from __future__ import annotations

import glob
import json
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
KB_EXPORT = os.path.join(ROOT, "kb", "kb-export.json")
VECTORS_DIR = os.path.join(ROOT, "validation", "vectors")

REQUIRED = {"id", "description", "knowledge_version", "kb_records"}


def _load_kb() -> dict:
    """Return {record_id: content_sha256}. Raises if the KB is not synced."""
    if not os.path.isfile(KB_EXPORT):
        raise FileNotFoundError(
            "kb/kb-export.json not found — run sync/pull.py (Stage 1b) first")
    doc = json.load(open(KB_EXPORT, encoding="utf-8"))
    index = {}
    for rec in doc.get("records", []):
        rid = rec.get("id")
        sha = (rec.get("provenance") or {}).get("content_sha256")
        if rid:
            index[rid] = sha
    return index


def _validate_vector(vec: dict, where: str) -> list[str]:
    errs = []
    if not isinstance(vec, dict):
        return ["%s: not a JSON object" % where]
    missing = REQUIRED - set(vec)
    if missing:
        errs.append("%s: missing keys %s" % (where, ", ".join(sorted(missing))))
    recs = vec.get("kb_records")
    if not isinstance(recs, list) or not recs:
        errs.append("%s: kb_records must be a non-empty list" % where)
    else:
        for i, r in enumerate(recs):
            if not isinstance(r, dict) or "id" not in r:
                errs.append("%s: kb_records[%d] needs an id" % (where, i))
    # Clean-room tripwire: a vector references knowledge, it never carries it.
    forbidden = {"payload", "shellcode", "exploit_body", "poc_code", "command"} & set(vec)
    if forbidden:
        errs.append("%s: forbidden key(s) %s — a vector is references only, no payload"
                    % (where, ", ".join(sorted(forbidden))))
    return errs


def check_vector(vec: dict, kb: dict) -> dict:
    """Return {status, records:[{id, result, ...}]} for one (already-valid) vector."""
    results = []
    worst = "PASS"
    for r in vec["kb_records"]:
        rid = r["id"]
        want = r.get("content_sha256")
        if rid not in kb:
            res = "MISSING"
            worst = "MISSING"
        elif want and kb[rid] != want:
            res = "DRIFTED"
            if worst != "MISSING":
                worst = "DRIFTED"
        else:
            res = "PASS"
        results.append({"id": rid, "result": res,
                        "recorded_sha": (want or "")[:12], "current_sha": (kb.get(rid) or "")[:12]})
    return {"status": worst, "records": results}


def main(argv: list[str]) -> int:
    as_json = "--json" in argv
    one = None
    if "--vector" in argv:
        i = argv.index("--vector")
        if i + 1 >= len(argv):
            print("check: --vector needs a path", file=sys.stderr)
            return 2
        one = argv[i + 1]

    try:
        kb = _load_kb()
    except (FileNotFoundError, json.JSONDecodeError, OSError) as e:
        print("check: %s" % e, file=sys.stderr)
        return 2

    paths = [one] if one else sorted(glob.glob(os.path.join(VECTORS_DIR, "*.json")))
    if not paths:
        print("check: no vectors to check (validation/vectors/ is empty)")
        return 0

    report = []
    invalid = False
    regressed = False
    for p in paths:
        where = os.path.relpath(p, ROOT)
        try:
            vec = json.load(open(p, encoding="utf-8"))
        except (json.JSONDecodeError, OSError) as e:
            report.append({"vector": where, "status": "INVALID", "error": str(e)})
            invalid = True
            continue
        errs = _validate_vector(vec, where)
        if errs:
            report.append({"vector": where, "status": "INVALID", "error": "; ".join(errs)})
            invalid = True
            continue
        out = check_vector(vec, kb)
        report.append({"vector": where, "id": vec["id"], "status": out["status"],
                       "knowledge_version": vec.get("knowledge_version", "")[:12],
                       "records": out["records"]})
        if out["status"] == "MISSING":
            regressed = True

    if as_json:
        print(json.dumps(report, indent=2, ensure_ascii=False))
    else:
        for item in report:
            print("[%s] %s" % (item["status"], item["vector"]))
            if "error" in item:
                print("    %s" % item["error"])
            for r in item.get("records", []):
                extra = ""
                if r["result"] == "DRIFTED":
                    extra = "  (recorded %s → current %s)" % (r["recorded_sha"], r["current_sha"])
                elif r["result"] == "MISSING":
                    extra = "  (no longer in the KB)"
                print("    - %-8s %s%s" % (r["result"], r["id"], extra))
        n = len(report)
        bad = sum(1 for i in report if i["status"] in ("MISSING", "INVALID"))
        drift = sum(1 for i in report if i["status"] == "DRIFTED")
        print("check: %d vector(s) — %d regression/invalid, %d drifted" % (n, bad, drift))

    return 1 if (invalid or regressed) else 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
