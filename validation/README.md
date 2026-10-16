# validation/ — knowledge-regression harness

The regression layer (Stage 3). A **vector** records which KB techniques a
validated attack path relied on, and the knowledge version it was validated
against. `check.py` re-checks every vector against the currently synced
`kb/kb-export.json` and reports whether the knowledge still holds.

This checks the **transferred knowledge** (Stage 1b), not a live target —
**nothing is executed against anything here**. Live replay of a vector on an
authorized target is Stage 5 (operator-gated, rig-backed). A vector carries
**references and metadata only**, never a payload (AGENTS.md directives 3 & 4).

## `check.py`

```
validation/check.py                 # check every vector under validation/vectors/
validation/check.py --vector <p>    # check one vector file
validation/check.py --json          # machine-readable report
```

Per referenced KB record:

- **PASS** — present and unchanged (same `content_sha256`).
- **DRIFTED** — still present but `content_sha256` moved → re-validate the vector
  against the new knowledge.
- **MISSING** — gone from the KB → regression (non-zero exit).

Exit is `0` when every vector is PASS/DRIFTED, `1` on any MISSING or an invalid
vector. Good for CI once the repo gains a workflow, and to run after each
`sync/pull.py` so a knowledge update that breaks a documented path is caught.

## Vector schema (`vectors/*.json`)

```json
{
  "id": "short-stable-id",
  "description": "what path this vector documents (prose, no payload)",
  "knowledge_version": "<handbook_version when validated>",
  "maturity": "stable|draft",
  "kb_records": [
    { "id": "<kb record id>", "content_sha256": "<sha at validation time>" }
  ]
}
```

`kb_records[].id` is a KB record id (the handbook path, e.g.
`privesc/gtfobins-linux`); `content_sha256` is that record's provenance digest
at the time the vector was validated, which is what DRIFTED compares against.
Forbidden keys (`payload`, `shellcode`, `exploit_body`, …) fail the vector:
a vector references knowledge, it never carries it.

`vectors/sample-linux-privesc.json` is a sample so the harness has something to
run; real vectors are added as engagements validate them. Engagement-specific
material (targets, loot, flags) never appears here — it stays in the git-ignored
`workspaces/`.
