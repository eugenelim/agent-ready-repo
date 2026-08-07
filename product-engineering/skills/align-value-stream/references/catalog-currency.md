# Catalog currency — the discipline that keeps the meta-repo worth reading

The meta-repo's value is entirely in being **current**. A catalog, a contract
reference, an architecture view, or a rollup that nobody reconciles is **worse
than none**: an agent (or a person) follows a stale map confidently and ships
against a contract that moved or a component that was renamed. Drift is the
dominant failure mode of a coordinating repo, so currency is a **first-class,
enforced discipline**, not a nice-to-have.

## Treat every cross-cutting artifact as a living document

The same doc-drift discipline the delivery loop applies to specs applies here, to
each artifact the meta-repo holds:

- **The federated catalog** — when a component repo is added, renamed, retired,
  or changes the APIs it provides/consumes, update the `Location` references. The
  entity definitions themselves stay in the component repos (federation), so the
  meta-repo only ever reconciles *which* repos it points at, not their contents.
- **The shared-contract references** — when the authority bumps a version, the
  references and courier snapshots in the affected slices are stale until
  reconciled. The compatibility direction tells you which side must move first.
- **The architecture `reference.md`** — when a bounded context or a major
  building block changes, update the system view here; component repos link to it.
- **The cross-component rollup** — reconcile each row's snapshot against the
  component repo's auto-derived coverage whenever a slice's status changes.
  Because the row points at the *auto-derived* source, only the cached snapshot
  can drift.

## Make currency a habit, not a hope

Reconcile the meta-repo on a cadence the value stream can sustain (a review when
a slice ships, a standing checkpoint) and whenever a coordinated change lands.
The point is not ceremony — it's that the snapshot has a known freshness. A row,
reference, or catalog entry you can't vouch for should say so (an
`unknown / not-yet-catalogued` rollup row, a flagged-stale reference) rather than
present a confident lie.

## The boundary with `monorepo-extras`

Currency is about keeping the cross-cutting artifacts true; it is **not** a
restatement of how to structure monorepo-vs-polyrepo work. That structuring
decision lives in `monorepo-extras` (`new-package`). The two meet only at "where
the shared contract lives" — reference that seam, don't duplicate it here.
