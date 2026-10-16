#!/usr/bin/env python3
"""sync/pull.py — pull htb-autopwn's kb-export.json into kb/ (redteam-agent Stage 1b).

Fetches the KB export (the transferred intelligence — see docs/kb-contract.md),
validates it against the kb-export/1 schema AND the clean-room rule (references
and metadata only: reject anything payload- or secret-looking), then writes it
to kb/kb-export.json with a kb/SOURCE.json manifest.

Decoupled and read-only toward the source (AGENTS.md directive 4): this only
READS htb-autopwn's published export, never writes back into it.

Content-addressed and idempotent: the producer emits a deterministic file
(records sorted by id, no wall-clock), so an unchanged export is a no-op — the
stored bytes are identical and git stays clean.

Source resolution (first that is set):
    --from <path|url>                         explicit path or http(s) URL
    $HTB_KB_EXPORT_URL                        env (template.env)
    ../htb-autopwn/handbook/kb-export.json    sibling-clone fallback

Usage:
    sync/pull.py                 # pull + validate + write kb/kb-export.json (+ SOURCE.json)
    sync/pull.py --from <src>    # from an explicit path or http(s) URL
    sync/pull.py --check         # validate the source and that kb/ is in sync; write nothing
"""
from __future__ import annotations

import hashlib
import json
import os
import re
import sys
import urllib.request

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
KB = os.path.join(ROOT, "kb")
OUT = os.path.join(KB, "kb-export.json")
MANIFEST = os.path.join(KB, "SOURCE.json")

SCHEMA_PREFIX = "kb-export/"
MAX_BYTES = 32 * 1024 * 1024  # a KB export is metadata; anything larger is suspect

# Record shape expected from the producer (see docs/kb-contract.md §1).
REQUIRED_KEYS = {
    "id", "title", "category", "frameworks", "context_tags",
    "preconditions", "observable_signals", "remediation",
    "references", "maturity", "confidence", "relationships", "provenance",
}
FRAMEWORK_KEYS = {"attack", "wstg", "masvs", "ptes", "cwe", "capec"}
CONTEXT_KEYS = {"os", "service", "tech"}

# A record names its knowledge — it must never carry the knowledge's payload.
# These key names are a structural clean-room tripwire.
FORBIDDEN_KEYS = {"payload", "payloads", "shellcode", "exploit_body",
                  "poc_code", "poc_body", "raw", "body"}

# Secret / payload patterns scanned over every string leaf (defense in depth —
# the producer emits none of these, so a hit means the contract was violated).
SECRET_PATTERNS = [
    ("private-key", re.compile(r"-----BEGIN (?:[A-Z0-9 ]+ )?PRIVATE KEY-----")),
    ("aws-access-key", re.compile(r"\bAKIA[0-9A-Z]{16}\b")),
    ("github-pat", re.compile(r"\bghp_[A-Za-z0-9]{36}\b|\bgithub_pat_[A-Za-z0-9_]{22,}")),
    ("slack-token", re.compile(r"\bxox[baprs]-[A-Za-z0-9-]{10,}")),
    ("google-api-key", re.compile(r"\bAIza[0-9A-Za-z_\-]{35}\b")),
    ("discord-webhook", re.compile(r"https?://(?:canary\.|ptb\.)?discord(?:app)?\.com/api/webhooks/\d+/[\w-]+")),
    ("jwt", re.compile(r"\beyJ[A-Za-z0-9_-]{10,}\.[A-Za-z0-9_-]{10,}\.[A-Za-z0-9_-]{10,}")),
    ("openrouter-key", re.compile(r"\bsk-or-[A-Za-z0-9-]{20,}")),
]
# A long contiguous base64/hex run is the signature of embedded binary / shellcode.
BLOB_RE = re.compile(r"[A-Za-z0-9+/=]{200,}|(?:0x)?[0-9a-fA-F]{200,}")


class PullError(Exception):
    pass


def _fetch(src: str) -> bytes:
    if re.match(r"^https?://", src):
        req = urllib.request.Request(src, headers={"User-Agent": "redteam-agent/sync-pull"})
        with urllib.request.urlopen(req, timeout=30) as r:  # noqa: S310 (scheme checked above)
            data = r.read(MAX_BYTES + 1)
    else:
        if not os.path.isfile(src):
            raise PullError("source not found: %s" % src)
        with open(src, "rb") as f:
            data = f.read(MAX_BYTES + 1)
    if len(data) > MAX_BYTES:
        raise PullError("source larger than %d bytes — refusing (payload guard)" % MAX_BYTES)
    return data


def _resolve_source(explicit: str | None) -> str:
    if explicit:
        return explicit
    env = os.environ.get("HTB_KB_EXPORT_URL", "").strip()
    if env:
        return env
    sibling = os.path.normpath(os.path.join(ROOT, "..", "htb-autopwn", "handbook", "kb-export.json"))
    if os.path.isfile(sibling):
        return sibling
    raise PullError(
        "no source — pass --from <path|url>, set HTB_KB_EXPORT_URL, "
        "or place htb-autopwn beside this repo")


def _scan_secrets(value: str, where: str) -> list[str]:
    hits = []
    for name, rx in SECRET_PATTERNS:
        if rx.search(value):
            hits.append("%s: %s-looking string" % (where, name))
    if BLOB_RE.search(value):
        hits.append("%s: long base64/hex blob (possible payload)" % where)
    return hits


def _walk_strings(node, path: str):
    if isinstance(node, str):
        yield path, node
    elif isinstance(node, dict):
        for k, v in node.items():
            yield from _walk_strings(v, "%s.%s" % (path, k))
    elif isinstance(node, list):
        for i, v in enumerate(node):
            yield from _walk_strings(v, "%s[%d]" % (path, i))


def _validate_record(rec, idx: int) -> list[str]:
    errs = []
    where = "records[%d]" % idx
    if not isinstance(rec, dict):
        return ["%s is not an object" % where]
    rid = rec.get("id")
    if isinstance(rid, str) and rid:
        where = "record %r" % rid
    else:
        errs.append("%s has no string id" % where)

    missing = REQUIRED_KEYS - set(rec)
    if missing:
        errs.append("%s missing keys: %s" % (where, ", ".join(sorted(missing))))

    forbidden = FORBIDDEN_KEYS & set(rec)
    if forbidden:
        errs.append("%s carries forbidden key(s) %s — clean-room: metadata only, no payload"
                    % (where, ", ".join(sorted(forbidden))))

    title = rec.get("title")
    if not isinstance(title, dict) or not {"en", "fr"} <= set(title):
        errs.append("%s title must be an object with en + fr" % where)

    fw = rec.get("frameworks")
    if not isinstance(fw, dict):
        errs.append("%s frameworks must be an object" % where)
    else:
        for k in FRAMEWORK_KEYS:
            if k in fw and not isinstance(fw[k], list):
                errs.append("%s frameworks.%s must be a list" % (where, k))

    ctx = rec.get("context_tags")
    if not isinstance(ctx, dict):
        errs.append("%s context_tags must be an object" % where)
    else:
        for k in CONTEXT_KEYS:
            if k in ctx and not isinstance(ctx[k], list):
                errs.append("%s context_tags.%s must be a list" % (where, k))

    for k in ("references", "relationships"):
        if k in rec and not isinstance(rec[k], list):
            errs.append("%s %s must be a list" % (where, k))

    prov = rec.get("provenance")
    if not isinstance(prov, dict) or not {"source", "content_sha256"} <= set(prov):
        errs.append("%s provenance must carry source + content_sha256" % where)

    # Clean-room scan over every string leaf of the record.
    for p, v in _walk_strings(rec, where):
        errs.extend(_scan_secrets(v, p))
    return errs


def validate(doc) -> tuple[list[str], int]:
    """Return (errors, record_count). An empty error list means the export is clean."""
    errs = []
    if not isinstance(doc, dict):
        return ["top level is not an object"], 0
    schema = doc.get("schema", "")
    if not (isinstance(schema, str) and schema.startswith(SCHEMA_PREFIX)):
        errs.append("unexpected schema %r (want %s*)" % (schema, SCHEMA_PREFIX))
    records = doc.get("records")
    if not isinstance(records, list):
        return errs + ["records missing or not a list"], 0
    count = doc.get("count")
    if isinstance(count, int) and count != len(records):
        errs.append("count=%s but %d records present" % (count, len(records)))
    for i, rec in enumerate(records):
        errs.extend(_validate_record(rec, i))
    return errs, len(records)


def _read(path: str) -> bytes | None:
    try:
        with open(path, "rb") as f:
            return f.read()
    except FileNotFoundError:
        return None


def _manifest_bytes(doc, sha: str) -> bytes:
    # Deterministic: derived only from the export, no wall-clock field.
    m = {
        "source": doc.get("source", ""),
        "schema": doc.get("schema", ""),
        "handbook_version": doc.get("handbook_version"),
        "records": len(doc.get("records", [])),
        "sha256": sha,
    }
    return (json.dumps(m, ensure_ascii=False, indent=2, sort_keys=True) + "\n").encode("utf-8")


def main(argv: list[str]) -> int:
    check = "--check" in argv
    src = None
    if "--from" in argv:
        i = argv.index("--from")
        if i + 1 >= len(argv):
            print("pull: --from needs a value", file=sys.stderr)
            return 2
        src = argv[i + 1]

    try:
        src = _resolve_source(src)
        raw = _fetch(src)
    except PullError as e:
        print("pull: %s" % e, file=sys.stderr)
        return 2

    try:
        doc = json.loads(raw)
    except json.JSONDecodeError as e:
        print("pull: source is not valid JSON (%s)" % e, file=sys.stderr)
        return 2

    errs, count = validate(doc)
    if errs:
        print("pull: REFUSING — the export failed validation (%d issue(s)):" % len(errs),
              file=sys.stderr)
        for e in errs[:20]:
            print("  %s" % e, file=sys.stderr)
        if len(errs) > 20:
            print("  ... %d more" % (len(errs) - 20), file=sys.stderr)
        return 1

    sha = hashlib.sha256(raw).hexdigest()
    manifest = _manifest_bytes(doc, sha)

    if check:
        cur_export = _read(OUT)
        cur_manifest = _read(MANIFEST)
        if cur_export == raw and cur_manifest == manifest:
            print("pull: up to date (%d records, handbook %s)"
                  % (count, doc.get("handbook_version")))
            return 0
        print("pull: kb/ is stale — run sync/pull.py (source has %d records, sha %s)"
              % (count, sha[:12]), file=sys.stderr)
        return 1

    os.makedirs(KB, exist_ok=True)
    before = _read(OUT), _read(MANIFEST)
    with open(OUT, "wb") as f:
        f.write(raw)
    with open(MANIFEST, "wb") as f:
        f.write(manifest)
    if before == (raw, manifest):
        print("pull: no-op — kb/ already matches (%d records, handbook %s)"
              % (count, doc.get("handbook_version")))
    else:
        print("pull: wrote kb/kb-export.json + kb/SOURCE.json (%d records, handbook %s, sha %s)"
              % (count, doc.get("handbook_version"), sha[:12]))
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
