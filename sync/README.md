# sync/ — knowledge transfer

The read-only bridge between htb-autopwn's knowledge base and this engine
(AGENTS.md directive 4; the full contract is in [`docs/kb-contract.md`](../docs/kb-contract.md)).
Nothing here ever writes back into htb-autopwn.

## `pull.py` — pull the KB export into `kb/` (Stage 1b)

Fetches htb-autopwn's `handbook/kb-export.json` (the transferred intelligence),
validates it, and stores it under `kb/`. **References and metadata only —
anything payload- or secret-looking is rejected** (clean-room, directive 3).

```
sync/pull.py                 # pull + validate + write kb/kb-export.json (+ kb/SOURCE.json)
sync/pull.py --from <src>    # from an explicit local path or http(s) URL
sync/pull.py --check         # validate the source and that kb/ is in sync; write nothing (CI/precommit)
```

**Source resolution** (first that is set): `--from <path|url>` →
`$HTB_KB_EXPORT_URL` (see `template.env`) → the sibling clone
`../htb-autopwn/handbook/kb-export.json`.

**Validation** — the export is refused (exit 1, `kb/` left untouched) unless:

- the top level is `{schema: "kb-export/*", records: [...], count == len(records)}`;
- every record carries the contract's keys (`id`, bilingual `title`, `category`,
  `frameworks`, `context_tags`, `preconditions`/`observable_signals`/`remediation`,
  `references`, `relationships`, `provenance` with `source` + `content_sha256`)
  with the right shapes;
- **clean-room holds**: no record carries a forbidden key (`payload`,
  `shellcode`, `exploit_body`, …), and no string leaf matches a secret pattern
  (private key, AWS/GitHub/Slack/Google/OpenRouter token, Discord webhook, JWT)
  or a long base64/hex blob (possible embedded payload).

**Output** — two deterministic, tracked files (no wall-clock, so an unchanged
export is a git no-op):

- `kb/kb-export.json` — the validated export, byte-identical to the source.
- `kb/SOURCE.json` — the manifest: `source`, `schema`, `handbook_version`,
  `records`, and the `sha256` of the export.

**Idempotent & content-addressed**: re-pulling unchanged content rewrites the
same bytes (reported as a no-op); `--check` exits non-zero when `kb/` is stale.

## Later (roadmap)

`push_privateer.py` (Stage 4) maps `kb/` records to Privateer's `kb_*` schema
through Privateer's own ingestion path — never a direct DB write — preserving
provenance, human-reviewed. Blocked until Privateer's Stage-10 ingestion is ready.
