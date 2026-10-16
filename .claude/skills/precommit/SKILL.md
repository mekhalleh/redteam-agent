---
name: precommit
description: The four-axis precommit runbook for redteam-agent (conformant / consolidated / stable / versioned) plus the hard secret gate — what the tracked git hook checks on the staged index, how to activate it, and what to do when it blocks.
type: prompt
whenToUse: Before any commit in redteam-agent, when wiring up a fresh clone/worktree (activating the hook), when the pre-commit hook blocks and you need to understand why, or when adding a check to the hook.
---

# Precommit runbook — redteam-agent

The tracked hook `.githooks/pre-commit` judges the **staged index only**
(`git diff --cached`), never the whole working tree. Bypassing it with
`--no-verify` is not allowed (AGENTS.md directive 5) — fix the cause instead.

## Activation (once per clone / worktree)

`core.hooksPath` is local git config and is not committable, so in each clone and
worktree:

```
git config core.hooksPath .githooks
git config --get core.hooksPath      # -> .githooks
ls -l .githooks/pre-commit           # -> executable
```

## The hard secret gate (runs first, BLOCKS)

- **Forbidden files**: refuses a staged `.env` / `.env.*` (except the tracked,
  value-free `template.env`), `SECRETS.md`, `*.local.md`,
  `.claude/settings.local.json`, and key material (`*.pem`, `*.key`, `id_rsa*`,
  `id_ed25519*`). These are git-ignored by design; staging one is a bug.
- **gitleaks** on the staged diff via `.gitleaks.toml` (extends the default
  ruleset + the Discord-webhook rule), honouring `.gitleaksignore`; from `PATH`
  or a vendored binary. Never downloaded (jarvis directive 13).
- **Offline pattern gate**: always runs, always blocks — a backstop (GitHub/CF
  tokens, private keys, OpenRouter keys, Discord webhooks) that works without
  gitleaks.

## The four axes

### 1. Conformant — syntax of what is staged
`bash -n` on `*.sh`/`.githooks/*`; `python3 -m py_compile` on `*.py`;
`node --check` on `*.mjs`/`*.js`; `ruby -c` on `*.rb`; JSON and TOML load; and
the agent/skill frontmatter (`name` = file name, `description`,
`tools`/`disallowedTools` as a comma list).

### 2. Consolidated — shared content & coherence
`.kimi-code/` holds ONLY the `skills` and `agents` relative symlinks
(→ `../.claude/skills`, `../.claude/agents`); anything else, a dangling or
absolute symlink, is refused (BLOCKS, baseline B7).

### 3. Stable — run the repo's tests when any exist
Runs `tests/run.sh`, else `pytest`, else `make test`, if present. The engine /
sync / validation code will add tests as it is built; until then this axis is a
no-op (the conformant axis is the only automated check).

### 4. Versioned — version bump when code changed
SemVer `MAJOR.MINOR.PATCH` once a `VERSION`/`pyproject.toml` version exists; warn
if staged code changed without a bump. No versioning scheme yet — add one with
the operator when the engine lands.

## When the hook blocks

Read the `pre-commit:` lines on stderr. Resolve the cause (never `--no-verify`),
re-stage, commit again.
