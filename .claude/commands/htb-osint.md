---
description: Run a passive OSINT pass for the current engagement — verify the gate, collect the five passes, write the sourced synthesis to workspaces/<name>/recon/
argument-hint: <name>
allowed-tools: Bash(engine/run.py:*), WebSearch, FetchURL, Read, Grep, Glob
---
Run a passive OSINT pass for the engagement `$ARGUMENTS`, following the
`osint-recon` skill and the `osint` persona (passive-first, clean-room, OPSEC).

1. **Verify the gate**: `workspaces/$ARGUMENTS/scope.md` must exist with a
   declared type + mode and the operator's authorization (directives 1 & 9). If
   the gate fails, stop and ask — no collection on assumption. Run
   `engine/run.py gate $ARGUMENTS` if available.
2. **Prepare the output area**: ensure `workspaces/$ARGUMENTS/recon/` exists
   (create it if the scaffold didn't); everything lands there, git-ignored.
3. **Run the five passes** of the `osint-recon` skill — assets, infrastructure,
   exposed surface, human/leaks, pivot & synthesis — strictly passive. Any
   source requiring an account or authentication, or any step that would send
   traffic to the target, **stops and asks the operator**.
4. **Write the synthesis report** to `workspaces/$ARGUMENTS/recon/` (English):
   every claim sourced and timestamped, each marked confirmed fact / inference
   / hypothesis, ending with the ranked candidate attack surface and the
   questions worth active recon.
5. **Report back** the summary to the orchestrator — sources included.

Reminder: the OSINT result *feeds* the offensive phases (recon, web, access, …)
— those stay governed as always, with the operator's confirmations before any
active or consequential action (directives 1 & 2). OSINT ranks and proposes;
it never authorizes.
