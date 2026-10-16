---
name: execution-environment
description: Where redteam-agent runs engagement tooling — inside a per-engagement Exegol container (Exegol MCP first, docker fallback), never on the bare host without the operator's explicit permission. Mirrors htb-autopwn's Exegol rules (AGENTS.md directive 10).
whenToUse: Before running any target-side or engagement tooling (recon, enumeration, exploitation, cracking), when setting up an engagement container, when the Exegol MCP is unavailable, or whenever a step would touch the bare host.
---

# Execution environment — Exegol, not the bare host

All engagement tooling runs **inside Exegol**, exactly as in htb-autopwn. The
bare host is never used to run engagement tooling, nor modified, **without the
operator's explicit permission** (AGENTS.md directive 10). This holds in every
engagement type and mode; it is never relaxed by CTF/autonomous pacing.

## One container per engagement

- A fresh Exegol container per engagement, named after it (`exegol-<name>`),
  tied to that engagement's `workspaces/<name>/`. Never reuse a previous
  engagement's container.
- Inside the container you are root and you install whatever the engagement
  needs — `apt`, `pip` in a venv, a cloned tool — this is **pre-authorized
  environment setup** because the container is ephemeral and dies at cleanup. A
  missing tool is installed **in-container**, never worked around on the host and
  never silently run from the host.

## Access path (in order)

1. **Exegol MCP first.** Use the Exegol MCP tools (list/start containers,
   execute in a container) as the primary path. It is declared in the repo
   `.mcp.json` as `exegol-mcp` (loopback HTTP); its URL and Bearer token come
   from `${EXEGOL_MCP_URL}` / `${EXEGOL_MCP_TOKEN}` — set the token in the local
   `.env` (value in Vaultwarden), never in a tracked file.
2. **If the MCP is unavailable, restart it**; if it still fails, **ask the
   operator** — do not fall through silently.
3. **docker is the fallback.** Drive Exegol through the `docker` / `exegol` CLI
   (the `exegol` CLI is interactive, so talk to `docker` directly from a
   script). (Matches the jarvis `exegol-mcp-policy`.)

## The bare host is the one boundary

Anything that would run on the bare host — a tool, a crack on the host GPU, a
network action outside the container — needs the operator's **explicit
permission first**. Stop and ask; never run it on assumption, and never as a
quiet fallback for something that failed in the container. The only things that
touch the host are what the operator has authorized (e.g. `docker` itself).

## Output must be visible

Whatever runs — scan, exploit, wrapper — the operator must see what it does from
the task: never redirect all output into a file; use `cmd 2>&1 | tee <file>` so
the bytes land in the engagement's (git-ignored) workspace *and* in the task.
Flags/credentials may be masked on their way to the terminal, never hidden by
redirection.

> Knowledge for a phase comes from the synced `kb/` (the transferred htb-autopwn
> KB — references and metadata only), never a payload embedded here (directives
> 3 & 4). This skill governs *where* tooling runs; the phase agents govern *what*
> is attempted, always human-in-the-loop (directive 2).
