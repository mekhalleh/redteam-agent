# redteam-agent

The **autonomous red-team agent** of Pirates.RE — the **successor to the
`htb-autopwn` autopwn release/engine**. The *engine* moves here; the
*intelligence* stays in [`htb-autopwn`](https://github.com/mekhalleh/htb-autopwn)
(its knowledge base) and is transferred to this agent through a stable contract.

## What it is

- It **is the engine**: an autonomous red-team agent that runs **authorized**
  engagements (recon → access → privesc → post-exploit / challenge solving), with
  a human in the loop. It replaces what htb-autopwn used to ship as its release.
- Its **intelligence comes from htb-autopwn's knowledge base** — which *remains*
  in htb-autopwn — transferred read-only through a stable **export contract**
  (`docs/kb-contract.md`) and synced easily; the agent never authors that KB and
  never writes back into htb-autopwn.
- It **feeds / shares with the Privateer Stage-10 knowledge base**
  ([`PiratesRE/privateer`](https://github.com/PiratesRE/privateer)) — the AI KB
  under construction — through Privateer's own ingestion path (`kb_*` schema).
- Validating that a knowledge version still reproduces its documented vectors on
  an authorized target is one **facet** of the engine (regression), not its only
  job.

## Division of responsibility

| Project | Role going forward |
|---|---|
| **htb-autopwn** | **Intelligence / knowledge base** (handbook, `kb-*`), kept and exposed as a postable KB export. No longer ships the autopwn engine. |
| **redteam-agent** | **The engine** — the autonomous red-team agent, consuming htb's KB. |
| **Privateer** | The platform's AI KB (Stage 10); receives the transferred knowledge. |

## Hard rules

- **Authorized engagements only.** Any target exercise runs strictly inside an
  authorization: a written authorization when one exists, or the operator's
  declaration of ownership/authorization (operator-declared ownership is
  title — directive 9). OPSEC applies; no flag/engagement detail leaks into docs/wiki.
- **References + metadata, never raw payloads** (clean-room, aligned with
  Privateer): the KB carries framework references, context and provenance — not
  exploit code.
- **Human-in-the-loop.** Suggestions and validations only; no autonomous
  offensive action and no autonomous push to Privateer without review.

## Layout (proposed)

```
AGENTS.md            # governance (any AI agent working here)
docs/kb-contract.md  # the htb -> postable KB export contract + the Privateer mapping
engine/              # the autonomous red-team engine (orchestration loop, execution)
kb/                  # local mirror of htb's transferred KB (synced, not authored here)
sync/                # pull htb KB export -> normalize -> optional push to Privateer
validation/          # regression facet: a knowledge version reproduces its vectors
.claude/             # red-team phase agents + skills, shared with Kimi via .kimi-code
```

> Status: **scaffold / design under review.** Baseline onboarding (develop
> branch, tracked hooks, gitleaks, bilingual wiki, `.env`/`template.env`) follows
> once the design is validated — same governance baseline as the other Pirates.RE
> repositories (jarvis `AGENTS.md` directive 7).
