# AGENTS.md — redteam-agent

This file applies to any AI assistant/agent (Claude Code, Kimi or another)
working in this repository. Validated by RAMELLA Sébastien (mekhalleh), owner and
Directeur Général of Pirates.RE.

`redteam-agent` is the **autonomous red-team agent** of Pirates.RE — the
**successor to the `htb-autopwn` autopwn release/engine**. The *engine* lives
here; the *intelligence* (the knowledge base) **remains in htb-autopwn** and is
transferred to this agent read-only through the export contract
(`docs/kb-contract.md`). It also shares that knowledge with the Privateer
Stage-10 KB. It is orchestrated, like the other repositories, by the **jarvis**
control plane (`~/Projects/jarvis`); jarvis rules add to this file and never
relax it — the stricter rule wins.

## Protocol for updating this file

- The agent never grants itself a new directive here.
- Before adding, changing or removing a directive, the agent asks the operator
  and waits for an explicit confirmation.
- A directive proposed and refused is not rewritten under another form without a
  new confirmation.

## Active directives

1. **Authorized engagements only.** Any exercise of a target runs strictly inside
   a written authorization (an HTB subscription against HTB targets, or the
   operator's own lab). No scanning/exploitation outside that scope. OPSEC
   applies; a flag, target secret or engagement detail never leaves the
   engagement artifacts and never enters a doc/wiki/commit.

2. **Human-in-the-loop, never autonomous offense.** The agent suggests, prepares
   and validates; it never fires an offensive action or pushes to Privateer on
   its own. The orchestrator re-verifies every claim; the operator approves every
   consequential action (jarvis directive 2).

3. **References & metadata, never raw payloads (clean-room).** The knowledge base
   this repo carries or emits holds framework references (MITRE ATT&CK, OWASP
   WSTG/MASVS, PTES, CWE/CAPEC), context tags and provenance — **never** exploit
   payloads or secrets. Aligned with Privateer's clean-room discipline.

4. **Decoupled and read-only toward the sources.** It consumes htb-autopwn's KB
   only through the export contract (`docs/kb-contract.md`) and **never writes**
   into htb-autopwn. It feeds Privateer only through Privateer's own ingestion
   path — never a direct database write — preserving provenance, scope and audit.
   The phase agents in `.claude/agents/` (recon, web, access, privesc,
   post-exploit, challenge) reference the knowledge by its `kb-*` **category**;
   in this repo that knowledge is the **transferred KB synced into `kb/`** (the
   intelligence that stays in htb-autopwn), not htb's own `kb-*` skills.

5. **Confirmation before every commit, push, merge and production action.** On a
   `feature/`/`fix/`/`chore/` branch off `develop`, in a worktree; never directly
   on `develop`/`main`; never `--no-verify` (jarvis directives 2–3).

6. **Never a secret in cleartext in a shared/published document.** Operational
   secrets live only in the local git-ignored `.env` (`template.env` is the
   tracked, value-free placeholder), the orchestrator Vaultwarden base, or the
   platform secret store (jarvis directive 9).

7. **Shared governance baseline (jarvis directive 7).** Satisfies the baseline:
   tracked `core.hooksPath` pre-commit judging the staged index, gitleaks
   extending the default ruleset + the Discord-webhook rule with a documented
   `.gitleaksignore`, `develop` integration branch, `AGENTS.md` + skills shared
   with Kimi via relative `.kimi-code/` symlinks, the four-axis precommit. *(To be
   wired during baseline onboarding — this repo is newly created.)*

8. **All repository files in English; product docs in the bilingual GitHub wiki
   (FR+EN).** Conversation follows the operator's language.

9. **Every engagement declares its type and mode, and stays authorized.** Before
   any recon or offensive action the agent ALWAYS has, and records in the
   engagement's `workspaces/<name>/scope.md`, the **type** (`whitebox` /
   `greybox` / `blackbox` / `redteam`) and the **mode** (`scoped` = a defined
   engagement with explicit scope + written authorization; `blackhat` = no formal
   scope document — research / own lab / CTF-HTB). The declaration may be made
   **by the operator in full**, or **proposed by the agent as a complete `scope.md`
   and validated by a single affirmative answer ("yes") from the operator** — no
   field-by-field re-questioning once the operator has validated the proposal.
   The "yes" validates only what is written: in **scoped** mode the proposal
   must name the written authorization, every in-scope target, the window and
   the contacts; in **blackhat** mode it must state the ownership basis (own
   lab/infra or HTB/CTF platform ToS) and every proposed target is checked
   against it — a "yes" never extends either basis, and out-of-basis targets
   are refused, "yes" or not.
   `blackhat` means *no scope doc*, **never** *no authorization*: in every mode
   the agent operates only on targets the operator owns or is explicitly
   authorized to test, and stops to ask when authorization is unclear
   (reinforces directive 1). See the `engagement` skill. Engagements live in the
   **git-ignored `workspaces/`** — target data, loot and flags stay local, never
   in a commit/doc/wiki.

10. **Execution environment — Exegol, never the bare host without operator
    permission.** All engagement tooling (recon, enumeration, exploitation,
    cracking, any target-side command) runs inside a **per-engagement Exegol
    container**, exactly as in htb-autopwn — the **bare host is never used to run
    engagement tooling, nor modified, without the operator's explicit
    permission**. Access path, in order: the **Exegol MCP** first; if it is
    unavailable, restart it, and if it still fails, **ask the operator**;
    **docker** (the `docker`/`exegol` CLI) is the fallback. Installing a tool
    *inside* the container is pre-authorized environment setup (the container is
    ephemeral, one per engagement) — a missing tool is installed in-container,
    never worked around on, or silently run from, the host. The one boundary is
    the bare host, which stays clean. See the `execution-environment` skill.

11. **EXA-SI client Discord channel — external, outside the org and the RSSI
    mandate.** The EXA-SI Discord server is a **client / external server that
    Pirates.RE does not own**, so the RSSI Discord-compliance mandate (jarvis
    directive 14) does **not** apply to it. On that server there is a
    **client-dedicated channel** into which the engagement's secrets and all
    pentest-in-progress information are posted — it is the client deliverable
    channel, a deliberate **scoped exception to directives 1 & 9** ("never in a
    channel"), valid **only** for that external client channel and **only** when
    the engagement authorizes it. The agent **asks at the start of every
    engagement** whether the EXA-SI channel is used, and records the answer (and
    the channel) in `workspaces/<name>/scope.md`. **Before posting to the channel
    it verifies the channel exists; if it does not, it aborts the post and
    reports it**, never publishing the information anywhere else. This exception
    does NOT widen what WE own: this repository, its wiki, `workspaces/` and any
    Pirates.RE-owned Discord still carry no secret (directive 9 unchanged there).

## Decision history

| Date | Directive | Decision |
|---|---|---|
| 2026-10-16 | Repository created as the **autonomous red-team engine, successor to the htb-autopwn autopwn release**: the engine moves here, the intelligence (KB) stays in htb-autopwn and is transferred via the export contract; also shares with the Privateer Stage-10 KB. Authorized-only, human-in-the-loop, clean-room, decoupled/read-only toward the sources; orchestrated by jarvis; baseline onboarding to follow | Added (directives 1–8, scaffold) |
| 2026-10-16 | Directive 9 — engagement type (whitebox/greybox/blackbox/redteam) + mode (scoped/blackhat), always asked and recorded in a git-ignored `workspaces/<name>/scope.md`; blackhat = no scope doc, never no authorization (authorized targets only in every mode); `engagement` skill + `workspaces/` added | Added (directive 9) |
| 2026-10-16 | Directive 10 — execution environment: all engagement tooling runs inside a per-engagement Exegol container (Exegol MCP first → restart/ask operator → docker fallback), the bare host is never used/modified without operator permission, in-container install is pre-authorized; mirrors htb-autopwn. `execution-environment` skill added | Added (directive 10) |
| 2026-10-16 | Directive 11 — EXA-SI client Discord channel: external/client-owned server, outside the org and the RSSI mandate (jarvis dir 14 N/A); its client-dedicated channel is where engagement secrets + pentest-in-progress info go (scoped exception to dir 1 & 9, only that channel, only when the engagement authorizes); ask per engagement + record in `scope.md`; verify the channel exists before posting, else abort + report; what WE own stays secret-free | Added (directive 11) |
| 2026-10-16 | Directive 9 + `engagement` skill amended — relaxed: the type/mode may be declared in full by the operator OR proposed by the agent as a complete `scope.md` validated by a single operator "yes" (no field-by-field re-questioning); explicit scoped-vs-blackhat differentiation added (scoped: the "yes" validates a contract-backed scope — authorization, every in-scope target, window, contacts named; blackhat: the "yes" validates a stated ownership basis — own lab / HTB-CTF platform ToS — and never extends it); explicit authorization still mandatory in every mode | Amended (directive 9) |
