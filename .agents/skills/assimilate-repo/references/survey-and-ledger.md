# Survey + the resumable ledger

The ledger is what makes a whole-repo survey survive interruption, a harness
switch, and parallel git worktrees. Its schema and lifecycle are pinned by
ADR-0048 (the assimilation-ledger decision).

## Fetch
Same SSRF allowlist as single-primitive ingest — see the `assimilate-primitive`
skill's `ingest-safety` reference. Prefer `git clone` / `gh` for a repo source.

## Ledger layout
- **Per-run ledger:** `~/.agentbundle/catalogue-curation/<run-id>/ledger.toml`.
  Append-only, one entry per candidate: `path`, `name`, `content-hash`,
  `verdict` (enum: `assimilate` | `reject` | `needs-new-pack`), `status`
  (`pending` | `done`), `destination`. **No free-text reason field** that could
  drift into holding surveyed source content — keep reasons terse and bounded.
  Purged on completion; never committed; never travels in an export.
- **`<run-id>` is deterministic** — a hash of the source URL/path + a
  per-installation salt, **no per-invocation stamp**. That determinism is what
  lets a resumed run and a sibling worktree derive the *same* run-id and share
  one ledger. Keyed on stable identity (path + name + content-hash), never on
  commit SHAs (fragile under rebase).

## Resume + concurrency
- A re-run reads the ledger and skips `done` candidates.
- Parallel worktrees append their own candidate entries; append-only + stable
  keys mean no clobber.

## Confidentiality
- `<run-id>` and `<source-hash>` are salted hashes, so the directory name does
  not disclose the source in plaintext (an unsalted low-entropy URL would be
  guess-confirmable; salt raises the floor — strong confidentiality against a
  local attacker who holds the salt is out of scope, deferred to the ADR).
- No verbatim source content or rejection prose is recorded.

## Output
Emit the inventory + verdicts as an RFC (reviewable proposal). Offer — never
auto-invoke — `propose-catalogue-pack` when `needs-new-pack` verdicts appear.
For each `assimilate` verdict, apply `assimilate-primitive`'s per-unit safety +
craft. Re-sync mechanics: see [re-sync](re-sync.md).
