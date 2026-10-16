---
description: Per-repo entry point — menu of every redteam-* command
argument-hint: (none)
---
redteam-agent command menu. All slash commands in this repo are prefixed
`redteam-` (a multi-clone jarvis session carries several repos at once — the
prefix keeps `/redteam-status` from colliding with another repo's `/status`).
This repo is self-governing: it runs the same **with or without the jarvis
orchestrator** — open it directly (`claude` / `kimi` in the repo) and the hook,
skills, agents and these commands all load from the repo itself. The standing
rules live in `AGENTS.md`; the staged build in the wiki `Roadmap`.

**Start here**
- `/redteam-help` — this menu.

**Engagement (always declare type + mode first)**
- `/redteam-engage <name>` — start an engagement: ask **type** (whitebox/greybox/
  blackbox/redteam) + **mode** (scoped/blackhat), scaffold the git-ignored
  `workspaces/<name>/`, and fill `scope.md`. See the `engagement` skill.
- `/redteam-plan <name>` — enforce the gate and print the phase chain with the KB
  categories each phase draws on (no offense).
- `/redteam-advance <name>` — one human-in-the-loop phase checkpoint (refused if
  the gate fails).
- `/redteam-status <name>` — how far the engagement has been checkpointed.

**Knowledge transfer (read-only toward htb-autopwn)**
- `/redteam-sync [source]` — pull + validate htb-autopwn's `kb-export.json` into
  `kb/` (clean-room: rejects any payload/secret). `--check` to test staleness.
- `/redteam-validate [vector]` — knowledge-regression harness: re-check documented
  vectors against the synced `kb/` (PASS / DRIFTED / MISSING).

**Guardrails (every command)**
Authorized targets only in every mode (`blackhat` = no scope doc, never no
authorization); references & metadata only, never payloads; engagement data
stays in the git-ignored `workspaces/`; nothing offensive runs until Stage 5
(operator-gated). Confirm before every commit / push / merge.
