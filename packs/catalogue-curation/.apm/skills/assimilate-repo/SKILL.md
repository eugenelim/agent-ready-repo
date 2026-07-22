---
name: assimilate-repo
description: Use to survey a whole external repo or catalogue (local path or URL) for ingestion candidates and produce a reviewable RFC of per-candidate verdicts (assimilate, reject, or needs-new-pack), resumable across sessions and git worktrees via a ledger. Triggers on "survey this repo for skills we can adopt", "inventory this catalogue", "what can we assimilate from <repo>", "re-sync from <upstream>". Do NOT use for a single known unit (use assimilate-primitive) or to scaffold a proposed pack (use propose-catalogue-pack).
metadata:
  boundaries: [network_fetch, filesystem_write]
---

# Skill: assimilate-repo

Survey a **whole** external repo or catalogue and turn it into a **reviewable
RFC** of per-candidate verdicts — resumable, idempotent, and safe under parallel
git worktrees. It reuses `assimilate-primitive`'s per-unit safety + craft for
each `assimilate` verdict; its own job is the **survey, the ledger, and the RFC**.

## Procedure

1. **Establish the charter anchor.** Read `docs/CHARTER.md` from the running
   catalogue if present; extract the mission and scope (the `## Domain` section
   if present, else `## Mission` + `## Scope`). Show the operator a one-line
   summary: "Anchoring verdicts against: [catalogue-name] — [domain summary].
   Override?" Accept: a path to a different CHARTER.md (the *target* catalogue's
   charter), or an inline mission statement (one phrase or sentence — the skill
   expands it into a working scope anchor). If `docs/CHARTER.md` is absent,
   **elicit before proceeding**: "What is this catalogue for? One phrase, sentence,
   or path to a CHARTER.md." The charter anchor governs all verdicts: a candidate
   is in scope if its function fits the mission; otherwise `reject`. Run from
   inside the target catalogue for correct anchoring — see workflow note below.
2. **Fetch the source, SSRF-guarded** — same allowlist as `assimilate-primitive`
   (`https`/`git`/`ssh` only; reject `file:`/`ftp:` and private/metadata ranges).
   See [`references/survey-and-ledger.md`](references/survey-and-ledger.md).
3. **Open (or resume) the ledger.** State lives at
   `~/.agentbundle/catalogue-curation/<run-id>/ledger.toml`, where `<run-id>` is a
   **deterministic** hash of the source + a per-installation salt (no per-run
   stamp) — so a resumed run and a sibling worktree derive the *same* run-id and
   share one append-only ledger. A re-run skips candidates already marked `done`.
4. **Inventory candidates and assign a verdict each**, iteratively (one
   reviewable verdict at a time, appended to the ledger): `assimilate` (names the
   destination pack), `reject` (terse reason — no verbatim source content), or
   `needs-new-pack`. Keep the ledger's reason field bounded; it is scratch, never
   committed, purged on completion.
5. **Emit an RFC** capturing the inventory + verdicts — a reviewable proposal,
   not a silent commit. When any `needs-new-pack` verdict appears, **offer** the
   hand-off to `propose-catalogue-pack` — describe what needs a pack and let the
   operator choose. **Never auto-invoke it.**
6. **Incremental re-sync.** Re-pointing at a source assimilated before is a
   diff, not a fresh run: the durable per-source marker
   (`sources/<source-hash>/last-synced.toml`, dated append, exempt from the
   completion purge) classifies each candidate `unchanged` (skip) / `changed` /
   `new`. The **git commit log is the time-of-sync record** — no parallel log.
   Record the re-sync on the prior source-RFC via RFC-0055's forms: an
   **Amendment** if it's Open; an **Erratum** if Frozen + a genuine correction; a
   **new RFC** (recorded as an Erratum entry naming it on the prior) if Frozen +
   new candidates or reversed verdicts. Detail:
   [`references/re-sync.md`](references/re-sync.md).

## Never do

- Write under this repo's `packages/agentbundle/**` or `packs/credential-brokers/**`
  (RFC-0059 D6) — those change only through a separate human-authored RFC.
- Auto-invoke `propose-catalogue-pack` — always offer with prepared context.
- Commit the ledger, let it travel in an export, or record verbatim source
  content / rejection prose in it.
- Bypass `assimilate-primitive`'s per-unit safety (raw-body review, code confirm,
  repo lints/scanners, AST01-AST10 agentic-skills security review, `safety.write_jailed`)
  for an `assimilate` verdict.

## Canonical workflow

Run `assimilate-repo` **from inside the target catalogue**, not from the source.
`export-catalogue` writes a `docs/CHARTER.md` stub and projects core +
governance-extras + catalogue-curation as local tools into the fork before you
start surveying — so the fork is survey-ready from day one. Running from the
source catalogue anchors verdicts against the wrong charter.

_Depends on `core` + `governance-extras`. Repo-scope; not in any default profile._
