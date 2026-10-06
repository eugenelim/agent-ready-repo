# Spec-stage review, 2026-10-05 — five sustained Blockers, no code written

This records why execution of `capture-work-alias-removal` stopped before its
first implementation write. The spec and plan are owner-approved; this note
does not amend them. It states what an adversarial pass and a secure-design
pass found, what an independent adjudicator sustained against repository
evidence, and what the owner has to decide.

Run id `51cd5c8b-b1a7-4ac2-921d-44a6173cb724`. Raw reports and the paired
adjudication are under `.context/reviews/<run-id>/`, which is gitignored; the
substance is reproduced here because that directory does not survive.

Scope under review was T1, T2 and T3 only. T4 to T6 — the Core 3.0.0 release,
the fresh RFC-0083 authorization, and the coordinated AgentBundle release —
were explicitly out of the authorized unit. Every finding below bites inside
T1 to T3.

Fifteen findings were raised across the two passes. Seven were refuted on
evidence and are not reproduced; five Blockers, two Concerns and one advisory
were sustained.

## The two that change what the contract means

### AC-0003 can be satisfied while the property it exists to deliver stays false

AC-0003 binds "ordinary canonical reconciliation", and both the Testing
Strategy and the carried T1 stub name exactly one callable,
`run_canonical_reconciliation`. The adjudicator traced a second ordinary
reader and confirmed it:

`extract_initiatives` (`workspace_status_engine.py:3862`) builds `ini.shaping`
through `_parse_supported_shaping_entries`, which calls the accepted-legacy
decoder and keeps precisely those entries whose code is `legacy_entry`
(`:1211-1218`); it builds `ini.work` through `_parse_work_entry` (`:1184`),
which accepts a bare string as a real `WorkEntry` path with `needs=[]`. Both
reach `classify_entries` (`:4286`) and `classify_shaping_entries` (`:4321`)
from `analyze` and `analyze_bounded`, where an entry with no `needs` is
emitted `is_ready=True`.

So a build can empty `run_canonical_reconciliation(...).legacy_memberships`,
pass AC-0003 verbatim, and still accept a bare-slug shaping entry and a bare
`spec/<slug>` work entry as ordinary lifecycle memberships and present them as
dispatchable. That is the outcome the criterion claims to forbid.

The fix the adjudicator names: restate AC-0003 as a property of the ordinary
read boundary and enumerate the entry points it binds — at minimum
`run_canonical_reconciliation`, `analyze` and `analyze_bounded` — requiring no
accepted membership and no ready or dispatchable classification for every
RFC-0083 section 10 item 2 shape.

### Merging T1 to T3 is itself the authorization-gated act

AC-0013 triggers "Before Core 3.0.0 is published". AC-0014 records that Core
is repo-only and needs no registry receipt, so no published artifact exists
apart from the `main` commit. A 2.x merge of T1 and T2 therefore removes the
ordinary accepted-legacy reader and the `capture-work` skill from the only
artifact Core has, and never trips AC-0013.

The RFC-0083 2026-10-02 Errata requires fresh Approver authorization *before
the compatibility behaviour changes*
(`docs/rfc/0083-work-intake-and-artifact-routing.md:1360-1361`). The spec's
`Ask first` rule does cover merging, but that is an instruction to the agent,
not a criterion a completion gate reads — and AC-0013 passes vacuously at a
2.x merge.

The fix: bind AC-0013's trigger to the first commit on `main` that changes
compatibility behaviour, rather than to the version bump.

## The three that stop the tasks landing inside their own scope

**Deleting the `capture-work` test directory reds the always-on gate.**
`Makefile:616` runs `pytest packs/core/tests/skills/capture-work/ -q` inside
the `run-test-suite` define; `tools/lint-ci-parity.py:1169` holds that exact
path as a `PR_GATED_IF` `SUITE_DISPOSITION` key and `:2483` lists it in the
digest-pinned `_SUITE_SOURCE_EXCEPTIONS` roster; `build_gate_chain.py:587`
chains `lint-ci-parity` into build-check. T2's pinned `Touches` names neither
`Makefile` nor `lint-ci-parity.py`, so T2 as written either leaves the gate red
or forces an edit outside pinned scope.

**Prune closure is an unrecognised third consumer of the legacy reader.**
`resolve_selected_memberships` (`:2992-3039`) emits `form: "legacy"`
occurrences that `_prune_closure` and `prune_preview` consume, and
`tests/roster/test_two_sided_prune_closure_invariant.py:1423` pins the
resulting `closure_failed` refusal. Prune is neither ordinary reconciliation
nor an explicit migration seam, so the plan's named deviation recognises two of
three consumers and AC-0004/AC-0005 scope preservation to migration, apply,
recovery and rollback — none of which is prune. Nothing says whether a legacy
alias still blocks prune closure after the change.

**Four live suites pin the behaviour T1 changes, none admitted.**
`tools/test_workspace_status_cli.py:655`, `:1608`, `:3858` and `:3923` assert
`legacy_entry` codes and `canonical.legacy_memberships[0]`. T1's `Touches`
names only the engine and two files under
`packs/core/tests/skills/workspace-status/`.

## The two Concerns

Cooled-brief child-scope attribution (`_brief_child_spec_states`, `:3206-3214`)
unions legacy brief-membership paths into its input. AC-0003 erases that input
and no criterion says whether the attribution keeps or loses it.

No criterion keeps the explicit recovery route reachable. AC-0007 is satisfied
by any current guidance containing no `capture-work` instruction, and for a
WIDE prose pass the cheapest route to that state is deletion. The protecting
intent lives only in working material — `plan.md:234` and `spec.md:39` — which
the documents' own contract notes declare non-contract. The Errata relies on
current migration guidance as part of the notice basis.

Advisory: the disposition of `guides/core/how-to/capture-work.md`, whose body
states the alias "remains available for compatibility", is undecided — deleted,
rewritten, or redirected, and whether its URL must stay resolvable.

## What was checked and could not be confirmed

The adversarial reviewer reported running the T1 stub's fixture against the
current engine and finding `codes.count("unsupported_legacy") == 5` correct.
The adjudicator could not corroborate that — executing project code is outside
its envelope. What it confirmed statically is that
`run_canonical_reconciliation` accepts the stub's single-argument call and that
`plan.md:189` records the author's own 2026-10-02 red validation against the
`legacy_memberships == []` assertion, on which the stub's redness rests. The
`== 5` figure remains unverified and is build-time detail.

## Disposition

No implementation was written. The spec needs amendment on at least AC-0003 and
AC-0013, and the three scope findings need either widened `Touches` or a
recorded reason each surface survives — all of which require the owner, because
both documents are approved and hash-sealed by their own contract.

Independently of the amendment, the merge needs the RFC-0083 Approver bound to
the exact candidate. That was true before this review and the review sharpened
why: the gated act is the merge, not the version bump.
