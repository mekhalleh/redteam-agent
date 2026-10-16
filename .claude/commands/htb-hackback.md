---
description: Start or resume a HACKBACK engagement — active counter-operations against an identified adversary (directive 9)
argument-hint: <name>
allowed-tools: Bash(engine/run.py:*), mcp__jarvis-bus__ask, mcp__jarvis-bus__check
---
Start or resume the HACKBACK engagement `$ARGUMENTS` (directive 9, mode
`hackback`).

1. **Verify the workspace**: `workspaces/$ARGUMENTS/scope.md` MUST exist with
   `mode: hackback`. If the mode is not `hackback`, stop and tell the operator
   to declare the engagement as hackback first (the `redteam-engage` command).
2. **Verify the adversary target is operator-declared**: only
   operator-declared adversary infrastructure is in scope; anything discovered
   later is stop-and-ask.
3. **Check the blueteam tasking via jarvis-bus**: ask `blueteam-agent` for the
   current HACKBACK tasking and confirm the engagement is coordinated under the
   HACKBACK protocol (`docs/hackback-protocol.md` in
   github.com/mekhalleh/blueteam-agent, the shared contract between the two
   agents).
4. **Remind the operator of the standing rules before any action**:
   - **Each action is confirmed by the operator individually** — nothing is
     fired autonomously (directives 1 & 2).
   - **Full traceability** — every step is recorded in the workspace
     (`workspaces/$ARGUMENTS/`), git-ignored, never in a commit/doc/wiki.
5. Then proceed step by step under the HACKBACK protocol, one
   operator-confirmed action at a time.
