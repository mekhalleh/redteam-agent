---
name: engagement
description: How every redteam-agent engagement starts — always declare the engagement TYPE (whitebox/greybox/blackbox/redteam) and MODE (scoped/blackhat), record them in a git-ignored workspaces/<name>/ scope file, and the authorization rule that holds in every mode.
whenToUse: At the very start of any engagement, when creating a new workspace, or when unsure of the current engagement's type/mode/scope.
---

# Engagement start — type, mode, workspace

**Before any recon or offensive action, the type and mode MUST be declared** and
recorded in the engagement's workspace scope file. Never start an engagement
with the type or mode unstated. They can be declared two ways:

- **Full declaration** — the operator states type + mode (and ideally the scope
  fields) directly, in one message. Recorded as-is, no re-questioning.
- **Proposed-and-validated (single "yes")** — the operator describes the
  engagement in one breath ("greybox scoped pentest of client X, target Y,
  window Z"); the agent drafts the **complete `scope.md`** (type, mode, targets
  in/out, window, contacts, `authorization` ref, `exasi_channel`) and presents
  it; **a single affirmative answer ("yes" or equivalent) from the operator
  validates the whole engagement at once**, and the agent starts without
  re-asking field by field. A non-affirmative answer means the proposal is
  adjusted, not accepted.

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
  scope.md         # type, mode, track, targets in/out, authorization ref,
                   #   window, contacts, exasi_channel, dates
  recon/           # enumeration output
  loot/            # credentials, artifacts (local only)
  notes/           # working notes, the attack narrative
  flags/           # CTF/HTB flags (local only)
```

`scope.md` is created at step 1 (`engine/run.py init <name>`) with the declared
**type** and **mode**; the phase agents (recon/web/access/privesc/post-exploit/
challenge) read it to stay in scope. Nothing here is ever published to the repo,
a doc or the wiki.

## 3. EXA-SI client channel — ask every engagement (directive 11)

The **EXA-SI Discord server is a client / external server Pirates.RE does not
own** — the RSSI mandate does not apply to it. It carries a **client-dedicated
channel** that is the deliverable channel for an engagement: on it, and **only**
on it, the engagement's secrets and pentest-in-progress information are posted.

- **Ask at the start of every engagement** whether the EXA-SI channel is used,
  and record it in `scope.md` as `exasi_channel: <channel id>` (or `none`).
- This is a **scoped exception to directives 1 & 9** — valid **only** for that
  external client channel, **only** when the engagement authorizes it. Everything
  WE own (this repo, its wiki, `workspaces/`, any Pirates.RE Discord) still
  carries no secret.
- **Before posting to the channel, verify the channel exists.** If it does not,
  **abort the post and report it** — never publish the information anywhere else.

## Execution environment

All engagement tooling runs inside a per-engagement **Exegol** container (Exegol
MCP first, docker fallback); the bare host is never used or modified without the
operator's explicit permission (directive 10). See the `execution-environment`
skill.
