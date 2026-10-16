---
name: osint-recon
description: The passive OSINT methodology of redteam-agent — five passes (assets, infrastructure, exposed surface, human/leaks, pivot & synthesis) over public sources only, with sourcing, timestamping and fact/inference/hypothesis discipline. Paired with the osint sub-agent persona; feeds workspaces/<engagement>/recon/.
whenToUse: Before any active reconnaissance of an authorized engagement, when footprinting a target from public sources, or when the operator asks for an attack-surface map without touching the target.
---

# OSINT recon — passive-first methodology

Every pass runs **strictly passive**: certificate-transparency logs, WHOIS/RDAP,
passive DNS, search engines and dorks, public leak corpora, public
social/metadatum sources. No scanning, no probing, no authenticated contact
with the target — anything beyond reading a public source escalates to the
competent phase agent with the operator's green light (AGENTS.md directives 1
& 2). The `osint` persona embodies these rules.

## The five passes

1. **Asset inventory** — domains and sub-domains from CT logs and passive DNS;
   expand to sister domains via shared certificates, name servers and netblocks.
2. **Infrastructure** — WHOIS/RDAP registrant/org/history, IP ranges and
   netblocks, hosting/ASN attribution, technologies visible *passively*
   (headers from cached/indexed pages, certificate subjects, favicon hashes
   from public engines — never a request we initiate against the target).
3. **Exposed surface** — search-engine dorks, publicly indexed
   buckets/misconfigurations and exposed files, certificate details, leaked
   configuration fragments in public indexes.
4. **Human surface** — public roles and contacts (team pages, public posts,
   document metadata from files already public), credentials or session
   material tied to the domain in public leak corpora — **verified by matching
   only, never by authenticating** against anything.
5. **Pivot & synthesis** — correlate the passes into a candidate attack-surface
   map: ranked candidate vectors, pivot points (a subsidiary domain, a shared
   netblock, a reused certificate), and the gaps worth an active-recon
   question. The synthesis report lands in `workspaces/<engagement>/recon/`.

## Rules

- **Every claim is sourced and timestamped** in the report: source (URL or
  corpus reference) + the time the source was observed. An unsourced claim is
  not written.
- **A source that requires an account or authentication stops the pass** —
  report it to the operator and wait; never create an account, never log in,
  never borrow a session (OPSEC).
- **The report distinguishes confirmed fact / inference / hypothesis**, per
  claim. Confidence follows the evidence, never the enthusiasm.
- **Clean-room (directive 3):** references and metadata only — hostnames,
  netblocks, technologies, source URLs, timestamps. No payload, no secret
  value, no personal data beyond what the engagement strictly needs; a leaked
  credential is referenced by source and matching fragment, not copied out.
- **Everything stays in the git-ignored `workspaces/<engagement>/recon/`** —
  never a commit, doc or wiki.

The synthesis feeds the offensive phases; those remain governed as always —
the OSINT report ranks and proposes, it never authorizes.
