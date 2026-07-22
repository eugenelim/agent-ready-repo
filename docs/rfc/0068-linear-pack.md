# RFC-0068: `linear` pack — Issue intake + delta-sync skills for the brief pipeline

- **Status:** Accepted
- **Author:** eugenelim
- **Approver:** eugenelim
- **Date opened:** 2026-07-21
- **Date closed:** 2026-07-21
- **Related:** RFC-0064 M5 (tracker integration mandate + lifecycle resolution); RFC-0019 (own-the-slice boundary, `Epic:` pointer); `docs/specs/m5-linear-brief-intake-and-sync/spec.md` (implementation spec, gated on this RFC); `jira-brief-intake` (pattern precedent — same choreography shape)

## Reviewer brief

- **Decision:** Add a new opt-in **`linear` pack** with three skills —
  `linear` (credentialed GraphQL primitive), `linear-brief-intake` (first-time
  Issue → brief), and `linear-brief-sync` (delta catch-up with PE-approval
  gate and Executing lock) — closing the M5 tracker-intake gap for teams
  that plan in Linear.
- **Outcome:** accepted.
- **Change accepted:** new `packs/linear/` directory; no changes to `core`,
  `atlassian`, or any existing pack. All five decisions resolved below.

## The ask

- **Recommendation (BLUF):** Approve the `linear` pack as an opt-in,
  user-scope-default pack composed of one credentialed primitive (`linear`)
  and two choreography skills (`linear-brief-intake`, `linear-brief-sync`)
  that close the M5 tracker-intake gap for Linear-planning teams.

- **Why now (SCQA):**
  - *Situation.* RFC-0064 M5 (resolved 2026-07-18) chose a PE-triggered,
    zero-infrastructure sync lifecycle for Linear: first-time intake creates
    a brief from a Linear Issue; after a spec review round the Issue may
    change; delta catch-up (`linear-brief-sync`) re-fetches, diffs, and
    presents changes for PE approval before writing.
  - *Complication.* The implementation spec (`m5-linear-brief-intake-and-sync`)
    is written and resolves field mapping, protected-field convention, and
    Project-scope handling from API research — but two design choices required
    approval-level decisions: the PE interaction model for delta presentation
    (D3), and whether `push-acs-to-linear` ships in v1 (D4).
  - *Resolution.* Both decided below.

- **Decisions:**

  | ID | Question | Decision |
  |---|---|---|
  | D1 | New `linear` pack, excluded from every default profile? | ✅ Yes — opt-in, user-scope-default. Same posture as `atlassian`/`figma`. |
  | D2 | Three-skill shape: `linear` primitive + `linear-brief-intake` + `linear-brief-sync`? | ✅ Yes. Mirrors `jira-brief-intake` precedent; primitive isolates the API surface. |
  | D3 | Delta diff presentation format for `linear-brief-sync`? | ✅ Section-level before/after with per-field `y / n / edit` prompt (see Proposal). |
  | D4 | Does `push-acs-to-linear` ship in v1 of this pack? | ✅ No — follow-on. Added to `[backlog]` in `workspace.toml`. |
  | D5 | Auth mechanism for the `linear` primitive? | ✅ Credential-brokers `creds` path (`auth: creds`, `namespace: linear`, `keys: ["API_KEY"]`); personal API key header `Authorization: <KEY>` (no Bearer prefix). Same wiring as other credentialed primitives. |

## Problem & goals

Teams that plan in Linear keep the *what/why* in a Linear Issue (or a set
of Issues within a Project). The `receive-brief` / `author-brief` skills are
the spec-driven delivery front door, but they have no knowledge of Linear.
The M5 gap: no path from a Linear Issue to a queued, workspace-visible brief
without manual re-typing.

The lifecycle RFC-0064 M5 resolved (2026-07-18):

1. **First intake** — `linear-brief-intake` creates a brief from a Linear Issue.
2. **Spec authored** — spec's ACs are pasted back into the Linear Issue for a review round (manual; `push-acs-to-linear` is the deferred follow-on).
3. **Review round** — PM/stakeholder edits the Linear Issue.
4. **Delta catch-up** — `linear-brief-sync` re-fetches, diffs, presents delta for PE approval, writes approved changes. PE-authored fields protected.
5. **Lock** — brief `Status: Executing` → `linear-brief-sync` refuses further updates.

### Goals

- First-time intake from a Linear Issue or Project → brief, registered in `[brief_queue].draft`.
- Delta sync with PE-approval gate; PE-authored fields never overwritten.
- Lock when brief is Executing (spec under construction).
- Zero infrastructure — all PE-triggered, no webhook, no event subscription.

### Non-goals

- **Live sync** (webhook-driven or polling). Zero infrastructure was an explicit M5 resolution.
- **Write direction in v1.** `push-acs-to-linear` deferred to follow-on (D4).
- **Cross-repo coordination.** Carry the Linear Project URL as `Epic:` pointer only (RFC-0019 boundary).
- **Modifying `core` or `atlassian`.** `linear` is a standalone pack.

## Proposal

### D1 + D2 — Pack shape

A new `packs/linear/` directory. Pack `default-scope = "user"` (same as
`atlassian`). Three skills:

| Skill | Role | Analogue |
|---|---|---|
| `linear` | Credentialed GraphQL primitive — all API calls live here | `jira` in atlassian |
| `linear-brief-intake` | Intake choreography: Issue/Project → brief → `receive-brief` | `jira-brief-intake` |
| `linear-brief-sync` | Delta-sync choreography: re-fetch → diff → PE approval → write | new (no Jira analogue yet) |

The `linear` primitive exposes named read subcommands (`get-issue`,
`get-project`) and the two write mutations (`update-issue`, `create-comment`)
the deferred `push-acs-to-linear` will use — primitive is the boundary;
choreography skills never call the Linear API directly.

**Linear API facts (researched 2026-07-21, confirmed from Linear developers docs):**

| Fact | Detail |
|---|---|
| Endpoint | `https://api.linear.app/graphql` |
| Auth header | Personal API key: `Authorization: <KEY>` (no Bearer prefix). OAuth: `Authorization: Bearer <TOKEN>` |
| Issue fields relevant to brief | `title`, `description` (markdown), `identifier` (human slug e.g. ENG-123), `children` (IssueConnection), `project` (nullable Project) |
| Project → Issue | `project.issues` (IssueConnection); or `issues(filter: {project: {id: {eq: "..."}}})` |
| Sub-issues | `issue.children` — direct field; no separate sub-issue type |
| Write: update description | `issueUpdate(id, input: {description: markdown})` |
| Write: add comment | `commentCreate({issueId, body: markdown})` |
| Rate limits | 5 000 req/hr, 3 M complexity/hr (personal key) |

### D5 — Auth via credential-brokers

The `linear` primitive uses the credential-brokers `creds` path — the same
wiring as other credentialed primitives in the catalogue:

```yaml
metadata:
  credentialed: true
  primitive-class: credentialed-cli
  auth: creds
  namespace: linear
  keys: ["API_KEY"]
```

The adopter stores their Personal API key via `credential-setup` under
`namespace: linear`, key `API_KEY`. The primitive reads it at runtime through
the credential-brokers tiered resolution (env var → keyring → dotfile). No
SSO path — Linear personal keys are static bearer tokens, not session cookies.

### D3 — Delta diff presentation format

The sync skill diffs only Linear-sourced fields (Outcome and User stories)
against the re-fetched Issue. Three options considered:

**Option A — Unified diff** (`--- was / +++ now`). Technically precise but
PE-hostile: prose diffs are noisy for minor wording; PE must mentally reconstruct
the new state. Dropped.

**Option B — Section-level before/after** (accepted). For each changed field:

```
## Outcome — proposed change
CURRENT:
---
<verbatim current brief section>
---

PROPOSED (from Linear re-fetch YYYY-MM-DD):
---
<verbatim proposed replacement>
---
Accept this change? (y / n / edit)
```

For User stories (a list), show diff items explicitly:
- `+ US-3. (ENG-456) <new story>` — new sub-issue in Linear
- `~ US-1.` — title changed (shows old and new text)
- `- US-2.` — sub-issue removed (PE decides whether to keep or drop)

Per-field approval prevents wholesale overwrites. PE can accept Outcome but
reject a story removal. No diff tooling needed.

**Option C — Summary only.** Too abstract for a meaningful approval decision. Dropped.

### D4 — AC export deferred

`push-acs-to-linear` is not in this pack's v1. The copy-paste workflow is
sufficient for the review round. Deferring keeps v1 read-only toward Linear
(lower security surface) and avoids premature UX commitments on comment-vs-
description-update. The `linear` primitive already ships `create-comment` and
`update-issue`, so adding the skill later is low-friction. Added to
`[backlog]` in `workspace.toml` with `commentCreate` noted as the safer write
direction when the need surfaces.

## Affected surface

- **New:** `packs/linear/` — `pack.toml`, `plugin.json`, `README.md`, three
  skill directories (`linear/`, `linear-brief-intake/`, `linear-brief-sync/`)
- **Updated:** `docs/architecture/overview.md` (per-pack skill table row);
  `docs/guides/README.md` (pack-index row); `docs/product/changelog.md`
  ([Unreleased] entry); `.claude-plugin/marketplace.json` (regenerated by
  `make build`)
- **Unchanged:** `core`, `atlassian`, `agentbundle-layout.toml` (user-scope
  pack — no repo-scope projection needed)
- **Backlog:** `push-acs-to-linear` added to `[backlog].open` in
  `workspace.toml` as a follow-on item.

## Alternatives considered

**Single skill (intake only, no sync):** mirrors `jira-brief-intake` exactly.
Rejected — the M5 lifecycle resolution explicitly includes delta catch-up as a
first-class deliverable. Deferring sync would reopen a resolved decision.

**Sync skill in the `atlassian` pack:** Linear and Atlassian are unrelated
vendors. A shared pack would confuse the install surface and violate the
"substantive not duplicative" principle. Rejected.

**Inline diff (unified format):** evaluated as D3 Option A. PE-hostile for
prose; dropped in favour of section-level before/after.

**Ship `push-acs-to-linear` in v1:** evaluated as D4 Option B. Deferred —
write direction is the one-way part; copy-paste is sufficient for v1.
