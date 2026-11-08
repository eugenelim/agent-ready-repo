# The re-sync reference still asks for Approver sign-off

- **Status:** Open
- **Kind:** defect

## Summary

`packs/catalogue-curation/.apm/skills/assimilate-repo/references/re-sync.md` still tells the reader to request Approver sign-off, though the lighter RFC template has no `Approver` field. Owner: `eugenelim`.

## Observed

- `re-sync.md` lines 31 to 37 require Approver sign-off before an Erratum, and cite `new-rfc/SKILL.md` for Approver-signed Errata.
- The `assimilate-repo` evals in `evals/evals.json` assert that wording, and the fixtures `evals/files/resync/prior-rfc-open.md` and `prior-rfc-frozen.md` carry `Approver:` header lines.
- The new RFC template and `new-rfc` skill drop the field and add a supersession step in its place.
- The reference says nothing about how the new seed files reach an adopter, so it also gives no hint that upgrades do not carry seeds (see `fix-seed-upgrades.md`).

## Intended

- `re-sync.md`, its evals and its fixtures describe Errata and supersession in the current `new-rfc` terms, with no `Approver` field.
- The pack source under `.apm/` is edited and projections are regenerated with self-host.
