# Pre-execute review record — 2026-10-13

This record covers two review runs of this spec and plan. The `spec-plan` run
below approved the pair for planning only. The code-mode amendment review at
the end of this record governs the current pair.

## Spec-plan run

The refreshed spec and plan reached a clean pre-execute review in the
`spec-plan` run after seven rounds of `adversarial-reviewer` and
`security-reviewer`. Each report went through an independent
`finding-adjudicator` check before any revision.

### Final round of the spec-plan run

- `adversarial-reviewer`, round 7: its one finding was refuted on adjudication,
  so the result is an adjudicated clean.
- `security-reviewer`, round 7: two Nits and no Blocker or Concern. Both Nits
  are deferred, not applied.

### Deferred Nits

| Nit | Where | Why deferred |
| --- | --- | --- |
| The candidate mode should reuse project-knowledge's `_parse_strict_json` and `_assert_safe_unicode`, which also refuse lone surrogates, instead of its own character list. | `spec.md` AC-0014 | Build-time choice for T2; the likely failure is a refused render, not a forged line. |
| A pull scan has no total cap on spec directories or log bytes. | `spec.md` AC-0013 | Only someone who can commit large logs can trigger it, and AC-0007 keeps delivery decisions unaffected. |

### Owner decisions taken during review

Both are recorded in [`owner-decision-2026-10-11.md`](owner-decision-2026-10-11.md):

- ship beside the reusable capture gates, with removal moved to Slice 8;
- "candidates only" admission.

Two adjudication results were malformed: an unneeded indeterminate marker in
round 3, and multi-line findings in round 6. The owner chose to rerun the
check in that case. Each malformed file is kept beside its replacement in the
ignored review folder for audit.

### Not checked by the final security pass

- Parity between the work-loop `file_safety.py` copy and the blessed helper.
- Format patterns in the two new schemas, which do not exist yet.
- Dependency CVEs and static analysis, which belong to CI.

## Code-mode amendment review — 2026-10-13

Engine run `96306346-da7f-4cb2-b812-085f54974fa4` re-reviewed the pair after
the terminal-intent amendment. Owner decisions taken during it are in
[`owner-decision-2026-10-13.md`](owner-decision-2026-10-13.md). Revisions by
round, each made only from adjudicated sustained findings:

- Amendment: terminal intent amended from `spec-plan` to `code` on owner
  request to build T1-T4. Owner decision in the same amendment: the Release
  history durable output and T4 name a changelog fragment under
  `docs/product/changelog.d/`, because main now authors the product changelog
  as fragments. No other protected field changed. The spec-plan run approvals stay as
  history; this amendment needs fresh spec and plan review and fresh human
  approval of both.
- Round 1: T2 confines per-record
  exclusion to the enquiry and distillation read paths and keeps
  whole-operation refusal on every write, disposition, and identity path, with
  a write-path fixture. T2 adds a deeply nested page fixture and a
  schema-versus-validator differential corpus.
- Round 2: Constraints name the
  read-only entry points that get per-record exclusion and every observation
  and topic writer or integrity check that keeps whole-operation refusal; the
  T2 write-path fixtures add an invalid topic under promotion and map rebuild.
- Round 3: Owner decision: AC-0005
  limits per-record exclusion to the read-only paths and requires every
  writer, admission, integrity, and migration path to keep whole-operation
  refusal; the spec's Accepted Risk gains the store-wide write stop. The plan
  names the actual enquire-mode helpers, the full refusal set, the
  pending-page-only capture closure, the existing enquiry tests to revise, a
  new-journal-read Stop condition, and write-path fixtures for writer
  admission and migration.
- Round 4: The LLD defines an orphaned
  record for AC-0005 and keeps topics self-contained, so enquiry stays
  journal-free; the T2 topic fixture checks that rule instead of excluding a
  topic over a capture. T2 Done when names the write-path and
  differential-corpus fixtures, and the spec's What Changes bullet matches
  AC-0005.
- Round 5: The pending page fails
  closed on a partition holding an invalid line whose target capture cannot be
  identified, with fixtures. The LLD names the quarantine output channel: a
  separate `knowledge-quarantine.v1` element and top-level `quarantine` list on
  enquiry, and the drain receipt's `diagnostics` on the pending page, with
  `knowledge-evidence.v1` unchanged.
- Round 6: the pending page's `workflow-receipts` mode keeps its
  `replay_required` whole refusal when a selected capture is excluded or
  hidden; the plan defines locator validity with AC-0014's character limits
  and adds hostile-locator fixtures for the `knowledge-quarantine.v1` element;
  revision history moved from the plan Changelog to this record.

One round-2 security adjudication was malformed (multi-line finding body); the
owner chose a rerun, and the malformed file is kept beside its replacement in
the ignored review folder.
- Round 7: `select_pending` keeps whole refusal, with exclusion applied in
  `pending_page`; this record's opening now scopes the earlier clean result to
  the `spec-plan` run.
