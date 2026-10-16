---
description: Advance one human-in-the-loop phase checkpoint (refused if the gate fails)
argument-hint: <name>
allowed-tools: Bash(engine/run.py:*)
---
Advance the engagement `$ARGUMENTS` by exactly **one** phase checkpoint.

Run `engine/run.py advance $ARGUMENTS`. It re-checks the gate first (refuses if
it fails), then moves the phase pointer forward one step and records the
checkpoint in `workspaces/$ARGUMENTS/engine-state.json` + `engine.log`.

This is the human-in-the-loop boundary: the engine shows which phase agent would
act and the KB categories it draws on, but **executes nothing** (real offense is
Stage 5, operator-gated). Review the checkpoint with the operator, then run the
command again for the next phase. Use `/redteam-status $ARGUMENTS` to see where
the engagement stands.
