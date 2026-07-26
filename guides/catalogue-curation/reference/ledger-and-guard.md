# Reference: the ledger and the engine guard

Two pieces of `catalogue-curation` machinery worth knowing in detail.

## The assimilation ledger

`assimilate-repo`'s progress lives in a user-scope scratch, in two parts (pinned
by the ledger ADR):

- **Per-run ledger** — `~/.agentbundle/catalogue-curation/<run-id>/ledger.toml`.
  Append-only; one entry per candidate (`path`, `name`, `content-hash`,
  `verdict`, `status`, `destination`); **purged on completion**. `<run-id>` is a
  deterministic hash of the source + a per-installation salt — *no per-run stamp*
  — so a resumed run and a sibling git worktree derive the **same** id and share
  one ledger. Keyed on stable identity, never commit SHAs.
- **Per-source marker** — `sources/<source-hash>/last-synced.toml`. The durable
  content baseline the next re-sync diffs against; dated append entries;
  **exempt from the completion purge**.

**Confidentiality:** ids are salted (a remote guesser without the local salt
can't read the source from the directory name); the ledger records no verbatim
source content or rejection prose — only hashes, enums, and dates. It is never
committed and never travels in an export.

## The engine / credbroker guard (D6)

The skills must never change this repo's `agentbundle` engine behaviour or the
`credential-brokers` pack. Two honest layers (`tools/lint-catalogue-curation-guard.py`,
run in `build-check` CI):

1. **Presence** — every skill carries a refusal clause naming the protected trees
   (scoped to *this* repo). A lint asserts the clause is present.
2. **Path-gate** — a changeset touching `packages/agentbundle/**` behavioural code
   or `packs/credential-brokers/**` fails **unless** it carries an
   `Engine-Change-RFC:` commit trailer. The declarative build recipes
   (`build/recipes/**`) are carved out — they're config every pack addition edits.

The guarantee is **barrier-plus-visibility**, not cryptographic impossibility: it
makes a protected-tree change require a deliberate, human-authored exemption and
show up loudly in review. Its residual — an assimilated *hook* runs before a diff
is gated — is covered by the ingest-time hook confirm, not the path-gate.

`export-catalogue` re-homing a *target copy's* engine anchors (default adapter,
self-host set, blanked source) is **not** a guard violation — the guard protects
*this* repo's engine, not a forked copy.
