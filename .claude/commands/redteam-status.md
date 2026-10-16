---
description: Show how far an engagement has been checkpointed
argument-hint: <name>
allowed-tools: Bash(engine/run.py:*)
---
Show the state of the engagement `$ARGUMENTS`.

Run `engine/run.py status $ARGUMENTS`: it prints the gate result, the track, and
the ordered phase chain with each phase marked done `[x]` or pending `[ ]` and
the next one flagged. Read-only — nothing is changed, nothing is executed.
