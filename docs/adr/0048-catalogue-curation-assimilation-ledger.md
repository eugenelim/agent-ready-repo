# ADR-0048: Assimilation state lives in a user-scope ledger — per-run purged, per-source durable

- **Status:** Accepted
- **Date:** 2026-07-02
- **Decision-makers:** eugenelim
- **Supersedes:** none
- **Related:** RFC-0059 (the catalogue-curation pack — this ADR is its named ledger follow-on); ADR-0002 (per-pack install scope); the `adapt-to-project` / credbroker `~/.agentbundle/` user-scope precedent

## Decision summary

- **Decision:** `catalogue-curation`'s assimilation progress lives in a **two-part user-scope scratch** under `~/.agentbundle/catalogue-curation/` — a per-run append-only `<run-id>/ledger.toml` that is purged on completion, plus a per-source durable `sources/<source-hash>/last-synced.toml` that survives purges.
- **Because:** a repo survey is long-running and must resume across sessions, harnesses, and parallel worktrees; incremental re-sync needs a baseline that outlives any one run.
- **Applies to:** the `assimilate-repo` and `assimilate-primitive` skills' progress/resume/re-sync state only — not the assimilated content itself (that lands in `packs/`).
- **Tradeoff accepted:** state lives outside any git tree and outside the export scrub, so it carries an explicit confidentiality/retention contract rather than riding the repo's `.gitignore`.
- **Revisit if:** a second pack needs cross-harness resumable state (promote the pattern to a shared engine primitive), or the salted-but-local-salt confidentiality floor proves insufficient for a real threat model (move to a keyed/encrypted marker).

## Context

RFC-0059's `assimilate-repo` surveys a whole external repo/catalogue and assigns a verdict per candidate — a long agent run that routinely exceeds one session, may switch coding harness mid-way, and may be split across parallel git worktrees of the same repo. It must be **resumable and idempotent**: a re-run skips already-decided candidates. Separately, re-assimilating a source that changed since last time must be **incremental** — it needs the source's last content baseline to diff against, and that baseline must outlive the run that produced it.

Copybara (mined in RFC-0059, no dependency) solves resumability by writing the last-migrated revision as a `GitOrigin-RevId` label in the *destination* — stateless, but keyed on a commit identifier that is fragile under history rewrite. We want the resumability without that fragility.

Finally, the state is an **inbound confidentiality surface**: assimilating from a private or client repo records that repo's structure and the maintainer's rejection reasons somewhere no export scrub reaches.

## Decision

We will store assimilation state in a **user-scope scratch** rooted at `~/.agentbundle/catalogue-curation/`, in two distinct scopes:

1. **Per-run ledger** — `~/.agentbundle/catalogue-curation/<run-id>/ledger.toml`, where `<run-id>` is a **deterministic** hash of the source URL/path + a per-installation salt, **with no per-invocation stamp**. Determinism is load-bearing: a resumed run and a sibling git worktree must derive the *same* `<run-id>` to share one ledger — a per-invocation stamp would defeat both resume and worktree-sharing. (One assimilation of a source = one run-id; a later re-sync of the same source reuses it, then purges again on completion.) **Append-only**, per-candidate entries: `path`, `name`, `content-hash`, `verdict` (`assimilate` | `reject` | `needs-new-pack`), `status` (`pending` | `done`), `destination`. Concurrent worktrees append their own candidate entries without clobbering. **Purged** on run completion (with a documented stale-run sweep); never committed; never travels in an export.

2. **Per-source durable marker** — `~/.agentbundle/catalogue-curation/sources/<source-hash>/last-synced.toml`, holding *only* a content baseline (the set of candidate content-hashes last synced) plus dated sync entries. Written as **dated append entries, never overwritten**; **exempt from the per-run purge**; scoped per source, not per run. This is what the next re-sync diffs against.

State is keyed on **stable identity** — source-relative `path` + `name` + `content-hash` — never on commit SHAs, so a rebased or re-cloned source does not duplicate work.

`<run-id>` and `<source-hash>` are **salted** hashes (one per-installation salt, applied deterministically), so the directory name does not disclose the source to a *remote* reader who can guess the source URL but lacks the local salt. This is a real-but-bounded floor: an attacker with **local filesystem access holds the salt**, so a low-entropy source URL remains guess-confirmable to them — strong confidentiality against a local attacker is deferred (see Consequences / Revisit if). The `last-synced` marker records no verbatim source content and no rejection prose — only content-hashes and dates (enforced by schema, not by inspection — see Confirmation).

## Decision drivers

- **Cross-harness + cross-worktree.** Must be reachable and shared regardless of which editor/agent runs, and safe under concurrent worktree writes.
- **History-rewrite-proof.** Resume/idempotency must survive a rebase or re-clone of the source.
- **Incremental re-sync.** A durable per-source baseline is required, decoupled from any run's lifecycle.
- **Inbound confidentiality.** The residue of surveying a private source must be minimal and non-disclosing.
- **No new engine.** Files only — consistent with RFC-0059's no-engine constraint.

## Consequences

**Positive:**
- Resumable, idempotent, worktree-safe, harness-agnostic — reuses the established `~/.agentbundle/` user-scope home (`adapt-to-project`, credbroker), so no new top-level convention.
- Append-only + stable-identity keying makes concurrent and repeated runs safe by construction.
- The per-run/per-source split cleanly reconciles "purge the run" with "keep the baseline."

**Negative:**
- State lives outside git and outside the export scrub, so its confidentiality rests on the salt + minimal-fields contract, not on repo tooling — a weaker guarantee than an in-tree, scrubbed artifact would have.
- A user-global scratch can accumulate stale runs; the stale-run sweep is a maintenance surface the skills must own.
- A guess attack on a low-entropy source URL is defeated for a *remote* reader by the salt, but a *local* attacker holds the salt and can still confirm — strong confidentiality of *which sources were surveyed* is best-effort against local access, not guaranteed.

**Revisit if:** a second pack needs cross-harness resumable state (promote to a shared engine primitive rather than duplicate), or the salted-but-local-salt confidentiality floor proves insufficient for a real threat model (move to a keyed/encrypted marker).

## Confirmation

- **Mode:** lint/CI.
- **Signal:** a construction test enforces the schema mechanically — `ledger.toml` is append-only with the six named fields; `last-synced.toml` accepts **only** `content-hashes[]` + dated `synced[]` and its schema **rejects any free-text / rejection-reason field**, so marker purity is *enforced by schema*, not by reviewer opinion. A second test asserts the completion-purge removes `<run-id>/` but leaves `sources/<source-hash>/` intact.
- **Owner:** eugenelim.

## Alternatives considered

- **State in the destination tree (Copybara's model)** — rejected on *history-rewrite-proof*: keying on commit labels breaks under rebase/re-clone, and it puts inbound residue inside the repo.
- **No persisted state, re-derive each run** — rejected on *resumability*: a long survey that loses all progress on interruption is unusable, and re-sync would be non-incremental.
- **Repo-scope scratch (`.context/` or a gitignored repo dir)** — rejected on *cross-harness*: `.context/` is Conductor-specific and per-worktree, not shared across worktrees or harnesses.
- **A committed tracking doc in the repo** — rejected on *confidentiality* and noise: it would commit surveyed-source structure into git history and churn the tree every run.
- **Single combined ledger (no per-run/per-source split)** — rejected: cannot both purge run residue and retain the re-sync baseline.

## References

- RFC-0059 § The resumable ledger (D7) and § Re-assimilation; `docs/rfc/0059-notes/strip-substitute-brief.md`.
- Copybara `GitOrigin-RevId` resumability (external prior art, not a dependency).
