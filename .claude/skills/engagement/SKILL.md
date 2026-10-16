---
name: engagement
description: How every redteam-agent engagement starts — always declare the engagement TYPE (whitebox/greybox/blackbox/redteam) and MODE (scoped/blackhat), record them in a git-ignored workspaces/<name>/ scope file, and the authorization rule that holds in every mode.
whenToUse: At the very start of any engagement, when creating a new workspace, or when unsure of the current engagement's type/mode/scope.
---

# Engagement start — type, mode, workspace

**Before any recon or offensive action, ALWAYS ask the operator two things** and
record them in the engagement's workspace scope file. Never start an engagement
with the type or mode unstated.

## 1. Type (how the engagement is run / what the tester knows)

- **whitebox** — full knowledge: source, credentials, architecture provided.
- **greybox** — partial knowledge: some creds/accounts or docs.
- **blackbox** — no prior knowledge: external perspective only.
- **redteam** — objective-driven, stealth, full attack chain (not just finding
  vulns), with detection/response in play.

## 2. Mode (scope posture)

- **scoped** — a defined engagement with an **explicit scope and written
  authorization** (targets in / out of scope, rules of engagement, window,
  contacts). The default for any client or third-party target.
- **blackhat** — **no formal scope document** (research, own lab, CTF/HTB). It
  means *no client scope doc*, **never** *no authorization*.

## Authorization — holds in EVERY mode (non-negotiable)

Whatever the type or mode, the agent operates **only on targets the operator
owns or is explicitly authorized to test**: the operator's own lab/infra, or
HTB/CTF targets under their platform ToS. It **never** touches a third-party
system without authorization. If a target's authorization is unclear, the agent
**stops and asks** — it does not proceed on assumption. (redteam-agent AGENTS.md
directive 1.)

## Workspace (git-ignored)

Each engagement is a directory under **`workspaces/<name>/`** — **git-ignored**,
never committed (target data, loot and OPSEC stay local). Suggested layout:

```
workspaces/<name>/
  scope.md         # type, mode, targets in/out, authorization ref, window, contacts, dates
  recon/           # enumeration output
  loot/            # credentials, artifacts (local only)
  notes/           # working notes, the attack narrative
  flags/           # CTF/HTB flags (local only)
```

`scope.md` is created at step 1 with the declared **type** and **mode**; the
phase agents (recon/web/access/privesc/post-exploit/challenge) read it to stay
in scope. Nothing here is ever published to the repo, a doc or the wiki.
