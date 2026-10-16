# engine/ — orchestration loop

The orchestration-loop **skeleton** (Stage 2). It drives an engagement through
the engagement gate and the ordered phase chain, one human-in-the-loop
checkpoint at a time. **No offensive action runs here** — a phase is a planned,
reviewed checkpoint, not an execution (real execution is Stage 5, operator-gated,
rig-backed). The phases reference the transferred knowledge by KB **category**;
the knowledge itself is the synced `kb/kb-export.json` (Stage 1b), never a
payload (AGENTS.md directives 3 & 4).

Everything an engagement produces — its `scope.md`, state, log, recon, loot —
lives under the git-ignored `workspaces/<name>/` (directive 9). Nothing here is
ever committed, documented or published.

## `run.py`

```
engine/run.py init <name>       # scaffold workspaces/<name>/ + a scope.md template
engine/run.py gate <name>       # parse scope.md, enforce the gate; exit 1 on failure
engine/run.py plan <name>       # gate + print the phase chain + KB categories per phase
engine/run.py advance <name>    # HITL checkpoint: advance one phase (refused if the gate fails)
engine/run.py status <name>     # show the current phase state
```

### The gate (directives 1 & 9)

`scope.md` must declare a valid **type** (`whitebox`/`greybox`/`blackbox`/`redteam`),
**mode** (`scoped`/`blackhat`) and **track** (`machine`/`challenge`), an
**authorization** that is filled in **every** mode (`blackhat` means *no client
scope document*, **never** *no authorization*), and at least one real in-scope
target. A `scoped` engagement additionally needs its RoE essentials (`window`,
`contacts`). Any field left as a `<placeholder>` fails the gate — the engine
**stops and asks** rather than start on assumption.

### The phase chain

- **machine**: `recon` → `web` → `access` → `privesc` → `post-exploit`
- **challenge**: `challenge`

`advance` moves exactly one phase forward per call and records the checkpoint in
`workspaces/<name>/engine-state.json`; `status` shows how far the engagement has
been checkpointed. `plan` reports, per phase, how many synced KB records sit in
the categories that phase draws on — so a run makes the Stage-1 knowledge
transfer visible before any phase is ever executed.

## Not here yet (later stages)

Real phase execution, rig-backed offense, OPSEC and audit are **Stage 5** and
stay operator-gated throughout. The regression harness is **Stage 3**
(`validation/`); the Privateer feed is **Stage 4** (`sync/push_privateer.py`).
