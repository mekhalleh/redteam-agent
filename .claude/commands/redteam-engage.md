---
description: Start an engagement — declare type + mode, scaffold the workspace, fill scope.md
argument-hint: <name>
allowed-tools: Bash(engine/run.py:*)
---
Start the engagement `$ARGUMENTS`. Follow the `engagement` skill and AGENTS.md
directives 1 & 9 — do NOT skip the two questions.

1. **Ask the operator two things and wait** (never assume):
   - **type**: whitebox / greybox / blackbox / redteam.
   - **mode**: scoped (explicit scope) or blackhat (no scope doc — research /
     own lab / CTF-HTB). Authorization = the operator's declaration of
     ownership/authorization, quoted verbatim in `scope.md` (operator-declared
     ownership is title).
2. Scaffold the git-ignored workspace: `engine/run.py init $ARGUMENTS`
   (creates `workspaces/$ARGUMENTS/` + a `scope.md` template + recon/loot/notes/flags).
3. **Ask whether the EXA-SI client Discord channel is used** (directive 11) and
   record it as `exasi_channel:` in `scope.md` (a channel id, or `none`). That
   external client channel is the ONE place engagement secrets / pentest-in-
   progress info may be posted; verify it exists before posting, else abort and
   report. What WE own stays secret-free.
4. Fill `workspaces/$ARGUMENTS/scope.md` with the declared type/mode/track, the
   **authorization** (required in every mode), the in/out-of-scope targets, the
   `exasi_channel`, and — for a scoped engagement — the RoE (window, contacts).
   Leave no `<placeholder>`.
5. Verify the gate: `engine/run.py gate $ARGUMENTS`. If it fails, fix the named
   field; the engine stops and asks rather than start on assumption.

Authorization unclear for any target → stop and ask. Engagement data lives only
under the git-ignored `workspaces/` — never a commit, doc or the wiki. All
tooling runs inside Exegol, never the bare host without operator permission
(directive 10 / the `execution-environment` skill).
