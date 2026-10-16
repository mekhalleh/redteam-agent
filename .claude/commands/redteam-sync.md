---
description: Pull + validate htb-autopwn's KB export into kb/ (clean-room, read-only)
argument-hint: [source path|url]  (optional; or --check)
allowed-tools: Bash(sync/pull.py:*)
---
Sync the transferred knowledge (Stage 1b). Read-only toward htb-autopwn — this
never writes back into the source (AGENTS.md directive 4).

Run `sync/pull.py $ARGUMENTS`:
- no argument → resolve the source from `$HTB_KB_EXPORT_URL` or the sibling
  `../htb-autopwn/handbook/kb-export.json`;
- `--from <path|url>` → an explicit source;
- `--check` → verify the source is valid and `kb/` is in sync, write nothing.

It validates the export against the `kb-export/1` schema and the **clean-room
rule** — it refuses any forbidden key, secret pattern or long base64/hex blob —
then writes `kb/kb-export.json` + `kb/SOURCE.json` deterministically (an
unchanged export is a no-op). Relay the record count, handbook version and any
refusal to the operator. After a successful sync, `/redteam-validate` re-checks
that documented vectors still hold against the new knowledge.
