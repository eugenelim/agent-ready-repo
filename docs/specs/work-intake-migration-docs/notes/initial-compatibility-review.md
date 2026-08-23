# Initial compatibility review

- **Date:** 2026-08-21
- **Reviewer:** Codex primary work-loop implementation session, with the
  production build executed by the repository user in the same worktree
- **Scope:** Initial write-new migration delivery only: target-writer audit,
  dual-reader retention, ledger-backed rollback, alias retention, release-clock
  evidence, RFC Approver authority, root backlog anchor, projections, and site
  generation. This review does not authorize or plan alias/reader removal.
- **Run/session boundary:** Evidence was collected from the current worktree and
  current Git refs in one local session. No Git ref/index write, tracker network
  call, credential lookup, browser session, or remote mutation occurred. After
  the repository user restored the locked Node dependencies, site source
  generation, both production renderers, and the rendered-link audit completed.

## Fixture and build inputs

- RFC-0083 metadata and compatibility rules, the approved AC14 deferred marker,
  and root `workspace.toml` backlog entry `capture-work-alias-removal`.
- The acceptance-pinned legacy inventory and exact valid/invalid migration
  fixtures under the core workspace-status tests.
- Migration selection, confirmation, ledger, and result JSON Schemas.
- Core 2.6.0 at `2f8ff96b7^` as the release immediately before the first
  write-new work-intake implementation; current core 2.10.5 sources and
  projections as the initial migration delivery under review.
- Current `work-intake`, `capture-work`, workspace seed, four profile adapters,
  workspace-status engine/CLI, integrated routing matrix, and profile matrices.
- `FORCE=1 make build-self`, guide/journey validators,
  `tools/build-site.py`, the focused intake surface tests, and the exact
  ledger-first apply/rollback test.

## Observed compatibility results

### Readers, writers, and alias

- The core 2.6.0 predecessor contains both `parse_workspace_entry` and the
  accepted legacy parser/finding path. It is therefore the designated
  dual-reader fallback: it reads target entries and the exact legacy
  representation restored by current rollback tooling.
- Current `workspace-status` still contains the accepted legacy reader and
  returns retained legacy membership as non-dispatchable context.
- `capture-work` remains installed. Its only behavior is to emit the documented
  deprecation notice and forward the normalized request to `work-intake`; it
  owns no classifier, queue shape, or storage path.
- Current profile intake adapters are read-only at the tracker and workspace
  boundaries. `work-intake` materializes the canonical artifact before calling
  the target-entry registration writer. The shipped workspace seed documents
  only the five-field target entry and contains no legacy entry.
- The focused work-intake surface and rollback run passed 9/9 tests. It covers
  target-route/alias equivalence and proves that ledger-first apply followed by
  rollback restores the exact original workspace bytes while leaving the
  canonical artifact byte-identical.

### Ledger and rollback

- Apply consumes confirmation before its effect, records an `applied` operation
  and artifact receipt, and leaves the artifact unchanged.
- Rollback requires a fresh confirmation, adds a separate receipt, transitions
  the operation to `rolled_back`, and restores the pre-apply workspace bytes.
- The durable ledger remains present after rollback. Canonical artifacts and
  migration evidence are not deletion targets.

### Removal predicates

| Predicate | Evidence on 2026-08-21 | State |
| --- | --- | --- |
| Two consecutive minor releases counted from first write-new | First write-new is the core 2.7 line released 2026-08-17; later 2.8 and subsequent minor lines are recorded. | evidenced, not sufficient alone |
| At least 90 elapsed days | Earliest date from the first write-new release is 2026-11-15. | **not met** |
| One-minor advance notice | No removal release is announced. | **not met** |
| Legacy fixture gate | Acceptance-pinned valid/invalid fixture and schema tests pass. | met for initial evidence |
| Current writer/seed gate | Current writers/seed emit or delegate only the target contract. | met for initial evidence |
| Current-guide removal audit | Current guides intentionally retain compatibility alias and migration guidance during the window. | **not met for removal** |
| Rollback readiness | Exact apply/rollback test passed; dual-reader predecessor was inspected. | met for initial evidence |
| Separately approved removal plan | Root entry is deliberately non-dispatchable and no removal spec exists. | **not met** |
| Check-before-effect RFC Approver authorization | No fresh removal authorization exists. | **not met** |

The conjunctive removal gate is therefore closed. The current decision is
`deferred`: retain both `capture-work` and the legacy reader.

## Compatibility-policy authority

- **Identity:** `eugenelim`
- **Role:** RFC-0083 `Approver`
- **Timestamp recorded by the metadata:** 2026-08-08 (the RFC's accepted/closed
  date; the frozen metadata supplies no finer time)
- **Metadata source:** `docs/rfc/0083-work-intake-and-artifact-routing.md`, header
  fields `Approver`, `Status`, and `Date closed`
- **Current decision:** `deferred`; this accepted RFC metadata defines who may
  later authorize the removal check but is not itself fresh removal approval.

This authority is distinct from repository `[authorization.migration]` roles.
Migration apply/rollback approval cannot satisfy the compatibility removal gate,
and RFC approval cannot satisfy a migration effect confirmation.

## Root backlog anchor

`workspace.toml [backlog].open` contains exactly one
`capture-work-alias-removal` entry. Its source points to this spec's AC14, it has
no future spec path or dispatchable work membership, and its comments preserve
all conjunctive clock, notice, audit, rollback, and later-approval conditions.
The entry remains a non-dispatchable reminder; it is not an implementation task.

## Projection and site evidence

- `FORCE=1 make build-self` completed. Authored core sources were projected to
  Claude and Codex, packaged workspace-status engine parity is byte-identical,
  `docs/CONVENTIONS.md` is byte-identical to its core seed, and marketplace
  versions are Atlassian 0.9.1, GitHub 0.2.1, and Linear 0.3.1.
- Guide, guide-index, title, journey-contract, and pack-journey validators all
  passed.
- `tools/build-site.py` completed and generated the canonical guides, all 14
  pack journeys, and four released highlights. The marketing build emitted 49
  pages, the documentation build emitted 226 pages, and
  `tools/check-rendered-site-links.py` checked 65,571 links across 275 pages
  without a finding. The deprecation and chunk-size messages were build
  warnings rather than failures.

No evidence above weakens AC14. Until every row is met and the named Approver
supplies fresh check-before-effect authorization to a separately approved
removal change, the compatibility bridge remains installed.
