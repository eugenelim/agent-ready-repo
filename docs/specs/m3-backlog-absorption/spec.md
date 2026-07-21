# Spec: m3-backlog-absorption

- **Status:** Shipped <!-- Draft | Approved | Implementing | Shipped | Archived -->
- **Owner:** eugenelim
- **Plan:** [`plan.md`](plan.md)
- **Constrained by:** RFC-0064 (amendment 2026-07-20 — "Repo-level backlog & deferral register")
- **Brief:** none
- **Contract:** none
- **Shape:** mixed

> **Spec contract:** this document defines what "done" means. The implementing
> PR must match this spec, or update it. Verification must be derivable from it.

## Objective

The repo has accumulated open work in `docs/backlog.md` — a 1625-line markdown
file with ~116 headings that is hard to surface at session start, hard to audit
for staleness, and structurally disconnected from the TOML-native `workspace.toml`
coordination layer that everything else uses. The `(deferred: <slug>)` convention
in specs resolves anchors against backlog.md headings, but there is no machine-
readable schema, no stale-check, and no justification gate.

This spec migrates all open backlog items from `docs/backlog.md` into a new
`workspace.toml [backlog].open` top-level section — audited for staleness and
rewritten to be cold-start-sufficient (problem, fix, affected file/skill, key
decisions) — reduces `docs/backlog.md` to a ~15-line anchor-tombstone stub
retaining only the four headings that Frozen RFCs link to, rewrites the
`lint-spec-status.py` invariant (iv) to resolve `(deferred:)` slugs against
`workspace.toml [backlog].open`, and updates the deferral convention in
`packs/core/seeds/docs/CONVENTIONS.md`, the `new-spec` template, and the
`work-loop` SKILL.md. On completion, `workspace-status` surfaces open backlog
items at session start alongside initiative queues, giving every session a
single view of open work.

## Boundaries

### Always do

- Edit canonical pack sources only (`packs/core/.apm/…`); edit seeds at
  `packs/core/seeds/…`; run `make build-self` after to project `CONVENTIONS.md`
  and sync all three lint copies. Never edit projected paths (`.claude/`, `.agents/`)
  directly.
- Audit every item migrated from `docs/backlog.md`: grep the referenced spec,
  check whether the work is still open. **Never drop a slug that is still referenced
  by a live single-line `(deferred: <slug>)` marker in any `docs/specs/*/spec.md`**
  (the set `lint-spec-status.py` enforces; plan.md markers are not lint-checked and
  may be dropped by the stale-audit). For items with no live spec.md marker and
  whose referenced spec is Shipped/Archived, drop as stale. When unsure, retain
  with a `# ?stale — verify` flag for human review.
- Rewrite each migrated item's TOML comment to be cold-start-sufficient:
  what the problem is, what the fix is, which file/skill it affects, and what
  would unblock it. The original markdown prose is a starting point; the final
  comment must read well standalone in workspace.toml.
- Preserve all four tombstone anchors in `docs/backlog.md`:
  - `## \`iac-terraform\`` → slug `iac-terraform` (RFC-0065)
  - `### credbroker-phase-2` → slug `credbroker-phase-2` (RFC-0023)
  - `## \`extraction-tier0-and-output-contract\`` → slug `extraction-tier0-and-output-contract` (RFC-0058)
  - `## adapt-to-project — Shipped: AC4b transcripts deferred` → slug
    `adapt-to-project--shipped-ac4b-transcripts-deferred` (RFC-0007 — this heading
    does not currently exist in backlog.md; create it in the tombstone).
- Land all changes atomically in a single PR (migration + tombstone + lint rewrite
  + doc updates) to avoid breaking the `(deferred:)` HARD gate between steps.
  The lint rewrite must use a **dual-source union**: accepts slugs from BOTH
  `workspace.toml [backlog].open` AND `docs/backlog.md` headings, so existing
  markers continue resolving while the tombstone retains only 4 headings.
- Deferred-AC items in `[backlog].open` carry `source = "spec/<name> ACn"` in their
  inline-object entry.
- Enumerate all inbound `docs/backlog.md#<anchor>` links in editable files (spec.md,
  plan.md, guide files, non-frozen RFCs) and repoint them to `workspace.toml` or
  the corresponding `[backlog].open` entry. Frozen RFC files (0007, 0023, 0058,
  0065) cannot be edited — their anchors must remain in the tombstone.
- Run `make build-self` before final gate check so `docs/CONVENTIONS.md` is
  regenerated from the seed and all three lint copies are byte-identical.

### Ask first

- Any change to `docs/CHARTER.md` or to the RFC-0064 amendment text.
- Removing a backlog item that has a live `(deferred:)` marker pointing to it —
  this would hard-fail the lint gate.
- Restructuring `workspace.toml` in ways not described by this spec.

### Never do

- Edit `.claude/` or `.agents/` skill files or `docs/CONVENTIONS.md` directly —
  edit `packs/core/.apm/` (skills) or `packs/core/seeds/` (CONVENTIONS.md) and
  run `make build-self`.
- Remove any of the four tombstone headings from `docs/backlog.md`.
- Add a `(deferred:)` marker in any spec without a corresponding `[backlog].open`
  entry — the lint will hard-fail on this after the rewrite.
- Introduce a new Python dependency (use stdlib `tomllib` / fallback regex only).
- Edit Frozen RFC documents (RFC-0007, RFC-0023, RFC-0058, RFC-0065).

## Testing Strategy

- **Lint invariant (iv) rewrite — TDD.** Write a new test file
  `packages/agentbundle/tests/unit/test_lint_spec_status_deferred.py` that
  exercises the new dual-source resolution: (a) slug only in `workspace.toml`
  `[backlog].open`, not in backlog.md → `check()` returns no HARD violation for
  that spec file; (b) slug in `docs/backlog.md` heading but not workspace.toml →
  passes (tombstone backward-compat); (c) slug in neither → hard violation;
  (d) `workspace.toml` absent → falls back to backlog.md only;
  (e) `workspace.toml` present but malformed TOML → `backlog_open_slugs` catches
  the parse error and falls back to regex, still resolving the slugs.
  Write the stubs **red** (T4a) before the lint change (T4b). Red means every test
  fails for the right reason: test (a) fails because `check()` doesn't yet read
  workspace.toml; tests (b), (c), (d) fail because the helper functions don't
  exist yet.
- **Migration completeness — goal-based.** After migration: `python3
  .claude/skills/work-loop/scripts/lint-spec-status.py --root . 2>&1; echo $?`
  exits 0. Additionally, all 11 required slugs (spec AC2) exist as `slug` fields
  in `[backlog].open`.
- **Tombstone structure — goal-based.** The tombstone file contains exactly the 4
  required heading anchors verified via Python slugify (plan T3 done-check).
- **Byte-identical lint copies — goal-based.** After `make build-self`:
  `diff packs/core/.apm/.../lint-spec-status.py .claude/.../lint-spec-status.py`
  and the `.agents/` diff both exit 0.
- **CONVENTIONS.md seed projection — goal-based.** After `make build-self`:
  `diff packs/core/seeds/docs/CONVENTIONS.md docs/CONVENTIONS.md` exits 0.
- **Full gates — goal-based.** `make build-check` passes green; full pytest (both
  test roots: `packages/agentbundle/tests/` and
  `packages/agentbundle/agentbundle/build/tests/`) passes.
- **workspace-status rendering — manual QA.** After migration, run `workspace-status`
  in session and verify a Backlog section surfaces the open items from
  `[backlog].open`.

## Acceptance Criteria

- [x] `workspace.toml` contains a top-level `[backlog]` section with `open = [...]`
  populated with all non-stale open items from `docs/backlog.md`. Each entry is
  an inline object `{slug = "...", ...}` with a preceding TOML comment that is
  cold-start-sufficient (problem, fix, file/skill, unblock condition). Deferred-AC
  entries carry `source = "spec/<name> ACn"`. No item with a live `(deferred:)`
  marker in any `docs/specs/*/spec.md` is dropped.
- [x] All 11 slugs currently used in single-line `(deferred: <slug>)` markers in
  `docs/specs/*/spec.md` exist as `slug` fields in `workspace.toml [backlog].open`:
  `apm-install-route-parity`, `apm-leak-lint-rfc`,
  `architect-review-diagram-knowledge-surfaces`, `artifactory-first-publish-gesture`,
  `atlassian-sso-cookie-live-dc-read-transcript`, `cdn-sri-mermaid`,
  `convenient-install-defaults-followons`, `credbroker-frozen-pack-ref-sweep`,
  `extraction-msg-realworld-sample`, `ml-saas-serverless-workload-class-lenses`,
  `upgrade-orphan-removal-on-projection-shape-change`.
  (`credbroker-phase-2` and `pack-evals-converters-gate-consolidation` are also
  migrated for completeness but are not lint-enforced via spec.md markers — they
  may or may not appear in `.open` depending on staleness audit results.)
- [x] `docs/backlog.md` is reduced to an anchor-tombstone stub retaining exactly
  four heading anchors (iac-terraform, credbroker-phase-2,
  extraction-tier0-and-output-contract, adapt-to-project--shipped-ac4b-transcripts-deferred)
  plus a file-level header and one-line pointers per retained section. All other
  content is removed.
- [x] `packs/core/.apm/skills/work-loop/scripts/lint-spec-status.py` invariant (iv)
  rewritten to resolve `(deferred: <slug>)` markers against the **union** of
  (a) `workspace.toml [backlog].open` slug fields (parsed via `tomllib.loads()` /
  `tomli.loads()` with a regex fallback for all other cases including malformed
  TOML — the `backlog_open_slugs()` function catches `TOMLDecodeError` and falls
  through to regex) and (b) `docs/backlog.md` heading anchors (tombstone backward-
  compat). The error message updated to reference `workspace.toml [backlog].open`.
- [x] After `make build-self`, all three lint copies are byte-identical:
  `packs/core/.apm/.../lint-spec-status.py`, `.claude/.../lint-spec-status.py`,
  `.agents/.../lint-spec-status.py`.
- [x] All existing `(deferred:)` markers in live specs continue to pass invariant
  (iv) (`lint-spec-status.py --root .` exits 0 with no new HARD violations).
- [x] New TDD test file
  `packages/agentbundle/tests/unit/test_lint_spec_status_deferred.py` exists with
  ≥6 test cases: workspace.toml-only slug passes `check()` end-to-end; tombstone
  heading backward-compat; slug-in-neither hard violation; absent workspace.toml
  fallback; malformed TOML drives through `backlog_open_slugs` (not just the regex
  helper directly) and still resolves slugs; regex fallback helper directly.
- [x] `packs/core/seeds/docs/CONVENTIONS.md` §4 deferral token definition updated:
  `<anchor>` now resolves to a `[backlog].open` entry slug in `workspace.toml`
  (not a `docs/backlog.md` heading). After `make build-self`, `docs/CONVENTIONS.md`
  is byte-identical to the seed.
- [x] `packs/core/.apm/skills/new-spec/assets/spec.md` deferral example updated
  to reference `workspace.toml [backlog]` (not `docs/backlog.md`).
- [x] `packs/core/.apm/skills/work-loop/SKILL.md` DECIDE phase updated:
  references to `docs/backlog.md` replaced with `workspace.toml [backlog].open`;
  an explicit "is this deferral justified?" prompt added at the point an agent
  would defer an AC.
- [x] `packs/core/.apm/skills/workspace-status/SKILL.md` procedure updated to
  render a **Backlog** section when `[backlog].open` has entries: item count and
  slug list with each entry's first TOML-comment line.
- [x] All inbound `docs/backlog.md#<anchor>` links in editable files repointed.
  Specifically: `docs/specs/credbroker/spec.md` (`#credbroker`, `#credbroker-phase-2`),
  `docs/specs/traceability-lint/spec.md` (`#sidecar-drift-hard-fail`),
  `docs/specs/discovery-producer-type-markers/spec.md` (×2) (`#discovery-loop-type-marker-producers`),
  `docs/specs/credbroker-user-scope/plan.md` (`#active-with-credbroker-pip`),
  `docs/specs/pack-activation-evals/plan.md` (`#behavior-check-for-backend-skills`),
  `docs/guides/_shared/how-to/preview-install-or-upgrade.md` (`#install-dry-run-preview-governance-seeds`).
  `CONTRIBUTING.md` updated where applicable. `docs/specs/README.md` reference
  to `#credbroker-phase-2` may remain (tombstone retains the heading).
- [x] `CONTRIBUTING.md` and `packs/core/.apm/skills/export-catalogue/SKILL.md`
  references to `docs/backlog.md` removed or updated.
- [x] Full pytest (both test roots) passes green; `make build-check` passes green.

## Assumptions

- Technical: `tomllib` (Python 3.11+ stdlib) / `tomli` (backport) / regex fallback
  avoids adding a new dependency. The `backlog_open_slugs()` function catches
  `TOMLDecodeError` so malformed workspace.toml falls back to regex, not empty set.
- Technical: `docs/backlog.md` is a Manual seed path (not overwritten by
  `make build-self`; the seed at `packs/core/seeds/docs/backlog.md` is only
  delivered on fresh `agentbundle install`, not `make build-self`). T3 edits
  `docs/backlog.md` directly. The seed is not updated in this PR — the
  `docs/backlog.md` format is being deprecated in favour of `workspace.toml`.
- Technical: `docs/CONVENTIONS.md` is a Projected seed path (`PROJECTED_README_OVERRIDES`
  in `self_host.py:453`); `make build-self` overwrites it from
  `packs/core/seeds/docs/CONVENTIONS.md`. T5 edits the seed source only.
- Process: This spec ships in a single PR. The dual-source lint makes the migration
  order-independent within the PR.
- Process: `credbroker-phase-2` is already resolved (2026-06-10) and its tombstone
  heading is retained to preserve inbound RFC-0023 links; it does not need to be
  in `[backlog].open` if the staleness audit confirms it's fully resolved.
- Process: Multi-line `(deferred:)` markers (anchors spanning two lines) are not
  checked by `lint-spec-status.py` (the regex matches single-line only); their
  slugs are migrated for completeness but are not lint-enforced.
