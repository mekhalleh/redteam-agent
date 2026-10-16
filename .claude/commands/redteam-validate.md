---
description: Knowledge-regression harness — re-check documented vectors against the synced kb/
argument-hint: [vector path]  (optional; or --json)
allowed-tools: Bash(validation/check.py:*)
---
Run the knowledge-regression harness (Stage 3). This checks the **transferred
knowledge**, not a live target — nothing is executed.

Run `validation/check.py $ARGUMENTS`:
- no argument → check every vector under `validation/vectors/`;
- `--vector <path>` → one vector;
- `--json` → machine-readable report.

Per referenced KB record it reports **PASS** (present, unchanged), **DRIFTED**
(present but `content_sha256` moved → re-validate the vector) or **MISSING**
(gone from the KB → regression, non-zero exit). An invalid or payload-carrying
vector also fails. Good to run after `/redteam-sync` so a knowledge update that
breaks a documented path is caught. Relay PASS/DRIFTED/MISSING to the operator;
a MISSING is a regression to investigate, not a result to record as-is.
