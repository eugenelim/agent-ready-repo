# Verification ledger: depends-on-headers

Execution observations recorded during the build. The spec and plan stay pinned; this file holds what the work learned.

## T1

- 2026-10-25: frozen `needs`-form expectations for 29 cases, commit `80c39a40f`; `test_depends_on_headers_equivalence.py` 3 passed.

## T2

- 2026-10-25: reader and resolution index, commit `155f213d8`; 64 reader tests red before, green after; workspace-status pack suite 344 passed, 1 skipped.
- 2026-10-25: a cooled intent cannot be indexed by slug, because its body is never opened and its lifecycle record carries only locators (`contracts/jsonschema/delivery-lifecycle-record.schema.json`). A typed reference to a cooled intent is therefore a missing target, which blocks, where a `needs` edge to it was satisfied by the lifecycle record. No live edge targets a cooled intent. The difference goes into the RFC-0106 errata entry (T7) as a recorded removal, for the Approver's signature.

## Amendment 1 — 2026-10-25

<a id="amendment-1"></a>

- **Trigger.** T2 added `invalid_dependency` to the engine's `_FINDING_NEXT_ACTIONS`, and T3 adds `unmigrated_needs`. `packs/core/tests/skills/navigate-intents/test_export_readiness.py::test_readiness_vocabulary_matches_workspace_status` requires `navigate-intents`' pinned copy, `_KNOWN_FINDINGS` in `intent_readiness.py`, to equal that table, so it fails at `155f213d8`. The spec's Never-do rule forbade any change to `navigate-intents`.
- **Owner decision.** eugenelim, 2026-10-25, in session: narrow the Never-do rule to admit one change in `navigate-intents`, adding the new finding codes to `_KNOWN_FINDINGS` as its parity test requires. The brief's non-goal about `navigate-intents` is read as narrowed the same way, for this copy only.
- **Also folded in.** The cooled-intent difference recorded under T2 becomes an Equivalence case (AC-0014) and a named removal in the RFC-0106 errata entry (T7).
- **Completed evidence.** T1 = commit `80c39a40f`; T2 = commit `155f213d8`.
- **Widened in review.** The amendment's adversarial review found the same cause for a cooled brief whose `Slug:` differs from its file stem: the index admits a cooled brief by stem alone, so a `brief:<Slug>` reference to it has no target once it cools. Both cases are one recorded removal, "the cooled target named by an unreadable slug". No brief in this repository has a `Slug:` that differs from its stem.
- **Deferred Nit (amendment review round 4).** A cooled brief with no `Slug:` field is named in neither AC-0003's cooled-brief case nor AC-0014's removal; it matches by stem and so behaves like AC-0003's case. Every live brief carries a `Slug:` line. Deferred with citation `.context/reviews/d123e014-033a-4fba-a583-8efe9ee0a4a4/9-pre-execute-adversarial-reviewer-raw.md`; T3 covers it with the cooled brief case.
