# Survey a repo for what to adopt

**Use this when:** You want to evaluate an entire external repo or catalogue for skills to adopt, not just a single known unit.
**Prerequisites:** The `catalogue-curation` pack installed; an HTTPS or git URL for the source repo.
**Result:** A reviewable RFC capturing inventory verdicts (assimilate / reject / needs-new-pack) for every candidate, resumable if the session is interrupted.

When you want to evaluate a *whole* external repo or catalogue — not one known
unit — reach for `assimilate-repo`. It inventories every candidate, gives each a
verdict, and emits a reviewable RFC, resumably.

## Run it

> Survey `https://github.com/some-org/their-catalogue` for skills we can adopt.

`assimilate-repo` fetches the source (same scheme allowlist as single-unit
ingest), then works candidate by candidate, appending each to a ledger under
`~/.agentbundle/catalogue-curation/<run-id>/`. Each candidate gets a verdict:
**assimilate** (names a destination pack), **reject** (with a terse reason), or
**needs-new-pack**.

## It survives interruption

The run-id is deterministic for a given source, so if the session ends, the
harness changes, or you run it from a second git worktree, a re-run picks up
where it left off — already-decided candidates are skipped. You don't restart.

## The output is an RFC, not a silent commit

When it finishes it writes an RFC capturing the inventory + verdicts, for you to
review. If some candidates are tagged `needs-new-pack`, the skill *offers* to
hand off to the `propose-catalogue-pack` skill — it describes what needs a pack
and lets you decide. It never spawns that itself.

## Re-syncing later

Point it at the same source again after upstream changes and it runs
incrementally: unchanged candidates are skipped, changed and new ones
re-surface. The git commit log is your record of what synced when; the prior
RFC records the delta (an amendment while it's open, an erratum once frozen, or
a fresh RFC if the delta is genuinely new decisions).

For the ledger's shape and confidentiality contract, see
[The ledger and the engine guard](../reference/ledger-and-guard.md).
