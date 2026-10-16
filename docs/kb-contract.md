# KB export contract — htb-autopwn → postable → Privateer

This is the contract that makes htb-autopwn's knowledge base **structured and
postable**, so `redteam-agent` and Privateer can sync it. **References and
metadata only — never raw exploit payloads** (clean-room, aligned with
Privateer's KB discipline).

## 1. Producer side (htb-autopwn)

htb-autopwn emits, alongside the existing `handbook/index.json` and per-item
`meta.json`, a versioned KB export: **`handbook/kb-export.json`** (guarded by the
same `content_sha256` mechanism as the handbook). One record per handbook item:

```json
{
  "id": "services/3306-mysql",
  "title": { "en": "...", "fr": "..." },
  "category": "services|privesc|vulns|web|techniques|playbooks|methodology|intel|metasploit",
  "frameworks": {
    "attack":  ["T1190"],
    "wstg":    ["WSTG-INPV-05"],
    "masvs":   [],
    "ptes":    ["exploitation"],
    "cwe":     ["CWE-89"],
    "capec":   ["CAPEC-66"]
  },
  "context_tags": { "os": ["linux"], "service": ["mysql"], "tech": ["php"] },
  "preconditions": "short prose",
  "observable_signals": "short prose",
  "remediation": "short prose",
  "references": ["https://attack.mitre.org/techniques/T1190/", "https://owasp.org/..."],
  "maturity": "stable|draft",
  "confidence": "high|medium|low",
  "provenance": {
    "source": "htb-autopwn",
    "handbook_version": "<VERSION.json version>",
    "content_sha256": "<item guard>",
    "updated": "YYYY-MM-DD"
  },
  "relationships": [
    { "type": "chains-to", "target": "privesc/sudo-gtfobins" },
    { "type": "methodology", "target": "methodology/recon-by-port" }
  ]
}
```

- Derived from `meta.json` + the note's structured front matter — **no payload
  body** is exported, only the catalogue metadata and public references.
- The export is produced by a small generator vendored from / shared with the
  handbook publish engine; it is **postable** the same way the handbook is
  (dry-run by default, `--send` writes), so a sync is a pull of a stable artifact.

## 2. Consumer side (redteam-agent)

- `sync pull` fetches `kb-export.json` for a given htb release/version into
  `kb/` (content-addressed by `content_sha256`; a no-op when unchanged — easy
  sync).
- It validates each record against this schema and the clean-room rule (reject
  anything that looks like a payload/secret).

## 3. Mapping to Privateer's Stage-10 KB (`kb_*`)

Privateer's KB (`PiratesRE/privateer`, wiki `Knowledge-Base`) is framework-
referenced with provenance. The record maps 1:1:

| This record | Privateer table |
|---|---|
| `id`, `title`, `category`, `maturity`, `confidence` | `kb_technique` |
| `frameworks.*`, `references` | `kb_reference` |
| `relationships[]` | `kb_relationship` |
| `provenance` | `kb_source` (provenance + version) |
| `context_tags.*` | `kb_tag` |

- `sync push --privateer` transforms the records and ingests them through
  **Privateer's own ingestion path** (never a direct DB write from here),
  preserving provenance and scope, and is **human-reviewed** before it lands.
- Bilingual (`en`/`fr`) descriptions carry over (Privateer's bilingual rule).

## 4. Guarantees

- Stable `id`s (the handbook path) so updates are idempotent.
- `content_sha256` provenance on every record → verifiable, versioned, auditable.
- References/metadata only; clean-room preserved end to end.
