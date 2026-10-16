---
description: Enforce the engagement gate and print the phase chain + KB categories
argument-hint: <name>
allowed-tools: Bash(engine/run.py:*)
---
Plan the engagement `$ARGUMENTS` — no offensive action, planning only.

Run `engine/run.py plan $ARGUMENTS`. It enforces the gate (type/mode/track +
authorization in every mode; scoped needs its RoE) and, if it passes, prints the
ordered phase chain (`recon → web → access → privesc → post-exploit`, or
`challenge`) with, per phase, how many synced-KB records sit in the categories
that phase draws on — so the Stage-1 knowledge transfer is visible before any
phase runs. If `kb/` is not synced it says so (run `/redteam-sync` first).

Relay the gate result and the chain to the operator. Do not advance any phase
here — that is `/redteam-advance`, one human-in-the-loop checkpoint at a time.
