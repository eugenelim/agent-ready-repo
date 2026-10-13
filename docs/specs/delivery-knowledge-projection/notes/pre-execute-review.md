# Pre-execute review record — 2026-10-13

The refreshed spec and plan reached a clean pre-execute review after seven
rounds of `adversarial-reviewer` and `security-reviewer`. Each report went
through an independent `finding-adjudicator` check before any revision.

## Final round

- `adversarial-reviewer`, round 7: its one finding was refuted on adjudication,
  so the result is an adjudicated clean.
- `security-reviewer`, round 7: two Nits and no Blocker or Concern. Both Nits
  are deferred, not applied.

## Deferred Nits

| Nit | Where | Why deferred |
| --- | --- | --- |
| The candidate mode should reuse project-knowledge's `_parse_strict_json` and `_assert_safe_unicode`, which also refuse lone surrogates, instead of its own character list. | `spec.md` AC-0014 | Build-time choice for T2; the likely failure is a refused render, not a forged line. |
| A pull scan has no total cap on spec directories or log bytes. | `spec.md` AC-0013 | Only someone who can commit large logs can trigger it, and AC-0007 keeps delivery decisions unaffected. |

## Owner decisions taken during review

Both are recorded in [`owner-decision-2026-10-11.md`](owner-decision-2026-10-11.md):

- ship beside the reusable capture gates, with removal moved to Slice 8;
- "candidates only" admission.

Two adjudication results were malformed: an unneeded indeterminate marker in
round 3, and multi-line findings in round 6. The owner chose to rerun the
check in that case. Each malformed file is kept beside its replacement in the
ignored review folder for audit.

## Not checked by the final security pass

- Parity between the work-loop `file_safety.py` copy and the blessed helper.
- Format patterns in the two new schemas, which do not exist yet.
- Dependency CVEs and static analysis, which belong to CI.
