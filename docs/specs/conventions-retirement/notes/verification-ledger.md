# Verification ledger — conventions-retirement

Execution observations. The spec and plan are frozen; this file carries what
execution measured and recorded.

## T0 — guard module, anchor resolver, canary

Built `tests/roster/test_conventions_retirement.py`. Four guards green, one
deliberately red.

- `test_scan_predicate_matches_its_approved_form` — green. Pins the scan's
  digest. A class-by-class canary cannot see an exclusion class added after it
  was written.
- `test_guard_invokes_the_scan_rather_than_restating_it` — green. The pathspec
  needle is assembled at runtime; a guard searching its own source for a literal
  it must contain always finds itself. Found and fixed during T0.
- `test_scan_reports_in_domain_and_excludes_historical_records` — green.
  Positive and negative control on the predicate.
- `test_resolver_accepts_a_heading_that_exists` — green. Positive control, so a
  resolver red because it crashes is distinguishable from one red because the
  work is undone.
- `test_every_recorded_anchor_use_resolves` — **RED, as required.** Every
  failure line reads "row records no destination heading", because
  `anchor-map.txt` leaves the heading column empty until an owning task writes
  back the heading it chose against the real destination.

Recorded red: `1 failed, 4 passed` on
`tests/roster/test_conventions_retirement.py`, failing node
`test_every_recorded_anchor_use_resolves`, expected failure identity
"unresolved anchor uses:" followed by one line per recorded use.

## T1 — seed AGENTS.md line cap

Measured rather than estimated, per the task's own test.

| Promoted block, as rendered today | Lines |
| --- | ---: |
| § Commits rule | 17 |
| The four pull-request questions | 10 |
| The never-commit and privacy rule (repo rendering) | 6 |
| § Documentation table | 13 |
| The four development-workflow bullets | 7 |
| The three coding-convention rules | 10 |
| **Added across T2-T7** | **63** |
| Removed by T8: the optional-guidance comment, seed lines 124-143 | 20 |
| **Net delta** | **+43** |

Seed is 144 lines today, so the projected final length is **187**.

`MAX_SEED_LINES` is raised from 150 to 200. That is 13 lines above the measured
projection, to absorb re-rendering: the procedure requires each promoted block
land "in that destination's own voice" rather than being pasted, so the rendered
length is not the source length. The margin is stated rather than hidden because
§ Boundaries makes raising the cap beyond what the relocated rules need an
ask-first action.

One correction worth recording, since it changed the number. A first measurement
counted `CONVENTIONS` § Privacy whole at 16 lines, but the promotion is of the
rule, which the repo renders in 6. A second counted the removal by matching the
first `<!--` in the seed, which is the `readability:exclude` block at line 15,
giving a nonsensical 128-line removal. Both were caught by reading the output
rather than trusting it.

## T2 — session-priming rules in both AGENTS.md files

Seated the Conventional Commits format, the four pull-request questions and the
never-commit rule in root `AGENTS.md` and `packs/core/seeds/AGENTS.md`.

Two contracts constrained the rendering, both found before editing:

- `packs/core/tests/pack/test_razor_guidance.py:100` counts line-initial `1.`
  through `7.` across the **whole** seed and requires exactly seven, and
  `tests/roster/test_razor_guidance_repository.py:86` makes the same assertion
  for the seed and root. The four pull-request questions are therefore prose,
  not a numbered list. Both files still report exactly seven rungs.
- `packs/core/tests/pack/test_repository_context_seed.py:30` pins the seed's
  heading set to exactly five, and
  `tests/roster/test_repository_context_root_guidance.py:31` pins root's to
  exactly eight. T2 adds no heading to either file; the rules sit under existing
  headings. T4 and T7 are the tasks that amend those pinned sets.

Root `AGENTS.md` reached 170 of its 170-line cap on the first attempt. Tightened
the commit block to land at 169, leaving one line of margin rather than sitting
exactly on the ceiling.

Thirteen pinned contract tests pass: `test_razor_guidance.py`,
`test_repository_context_seed.py`, `test_work_intake_surface.py`,
`test_repository_context_root_guidance.py`, `test_razor_guidance_repository.py`.

### Two defects my own guards produced

**The priming guard needed a negative control, not a recorded red.** The plan's
step-4 rule produces the red by stripping rather than by timing, so the guard
ships with `test_the_priming_guard_detects_their_absence` — strip every token
and assert the same predicate reports all of them missing — plus
`test_the_priming_guard_ignores_commented_out_content`. Both are permanent
controls rather than a one-off run recorded in prose.

**The canary was pinned to a moving target.** Its in-domain witness was
`AGENTS.md`, and T2 legitimately removed both `CONVENTIONS` references from that
file, so it left the scan domain and the control failed. The deeper problem: by
T25 the default scan returns nothing by design, so *any* witness on the
retirement's own pattern reports a swallowed domain the moment the work
succeeds. Re-anchored on `MAX_SEED_LINES` in `tools/`, which no exclusion covers
and this change does not move, and split the negative control onto `## Decision`
inside `docs/adr/` with an assertion that the witness pattern matches something
at all — otherwise the exclusion check passes vacuously.

Root `AGENTS.md` is now out of the consumer domain: T2 removed its last two
`CONVENTIONS` references. That is the first baseline file this work has cleared.

## T3 — docs/README.md as the doc map

Created `packs/core/seeds/docs/README.md` and `docs/README.md`, declared the
seed, added the installed path, and re-pointed the section's consumers.

Discovery returned three `#document-lifecycle` consumers:
`guides/governance-extras/how-to/new-adr.md`,
`guides/governance-extras/how-to/new-rfc.md`, and
`packs/core/seeds/docs/product/README.md`. All three now address
`docs/README.md#the-three-lifecycle-classes`.

The `§ 5` discovery form also returned `.github/pull_request_template.md`,
`packs/core/.apm/skills/workspace-status/references/agentbundle-layout.md` and
`tools/test_build_site_routing.py` — every one cites § 5b specifically, so they
belong to T10, not here. Recorded rather than acted on.

**The anchor protocol works end to end.** Writing the chosen heading back into
`notes/anchor-map.txt` moved all five `#document-lifecycle` uses from unresolved
to resolved: the resolver went from 30 unresolved to 25. That is the first proof
T0's resolver and the write-back seam function as designed.

### The repo copy diverges from the seed, deliberately

The seed lists the four areas `core` installs plus one placeholder row. The
repository's own copy replaces that placeholder with `adr/`, `rfc/` and
`guides/`, which no `core` seed provides — `adr/` and `rfc/` arrive with
`governance-extras`. A seed that listed them would ship an adopter a map to
directories they never receive, which is the defect the round-5 scaffold audit
found in `packs/core/seeds/docs/architecture/README.md`.

### Re-pointing a contract rather than preserving its shape

`tests/roster/test_adapt_reference_architecture.py` pinned four things about
§ Document hierarchy's ASCII diagram: `reference.md (golden`, `overview.md (map`,
a descriptive/normative gloss, and fixed-width row alignment of the box.

The operative content is the distinction — `overview.md` is descriptive, the map;
`reference.md` is normative, the golden path. The box was presentation. So the
gloss moved to the docs map under its own heading, the test re-points at
`packs/core/seeds/docs/README.md`, and the row-alignment guard was removed with
the diagram it policed rather than left asserting over content that no longer
exists.

Stripped red recorded: removing the `**normative**` and `**descriptive**`
markers fails `test_docs_map_seats_reference_md`; restoring them passes.

### Two gates that fired for the wrong reason

**`catalogue lint` rejected the new seed even though the declaration was
correct.** `python3 -m agentbundle` resolved to
`/Users/eu.gene.lim/orca/agent-ready-repo/` — the main checkout — because the
editable install pointed there, so the CLI never loaded this worktree's
`_SEEDS_REQUIRED_PLACEHOLDERS`. Confirmed by `pip show`, diagnosed with a
one-shot `PYTHONPATH`, then fixed by repointing the editable install to this
worktree with owner approval. Repointing is shared state: other worktrees now
resolve here until it is pointed back.

**The install snapshot is a golden, not a hand-maintained list.** A hand-edited
insertion reordered `workspace.toml` and failed
`test_first_install_snapshot[core]`. Reverted and regenerated with
`UPDATE_GOLDEN=1`, which produced a one-line diff adding `docs/README.md` and
reordered nothing.

## T4 — § Documentation promoted into the seed

The seed now carries a `## Documentation` section after § Rule lookups, matching
the repo's own order, and its last `CONVENTIONS` reference is gone. **The seed
`AGENTS.md` is cleared from the consumer baseline** — the second file the work
has cleared, after root `AGENTS.md`.

Scoped to what core installs rather than copied. The repo's table names
`docs/adr/`, `docs/rfc/`, `guides/` and `ARCHITECTURE.md`; none is a core
install path, so the seeded version routes to `docs/README.md`,
`docs/CHARTER.md`, and the four seeded area READMEs. `test_seed_documentation_names_only_installed_paths`
checks every link target against `core.paths.txt`, so a later edit cannot
re-introduce one.

Both universal rows carried over unchanged — a repeating agent workflow lives in
its own `SKILL.md`, a mechanically knowable fact in code, schema, manifest, test
or linter. They are named operative content because once `docs/README.md` is
installed, a single-row table satisfies every other predicate. Stripped red
recorded: removing the two rows fails
`test_seed_documentation_keeps_the_universal_rows`; restoring them passes.

### Two pinned contracts amended in the same step

`packs/core/tests/pack/test_repository_context_seed.py` pinned the seed's
heading set to exactly five and separately required `Documentation` to remain
backticked inside the optional-guidance comment. Both changed: the heading set
gains `Documentation`, and the comment no longer offers it, because the trigger
the comment itself named has fired — the seed installs four `docs/` areas plus
the map. `Security considerations`, `Scoped instructions` and
`Repository structure` stay offered until their own tasks promote them.

`packs/core/tests/pack/test_work_intake_surface.py` pinned the seed's relative
links to exactly `AGENT_RULES.md` and `docs/CONVENTIONS.md`. The set now names
the map and the five area READMEs, each asserted to be a real seeded file — the
test's own reason for pinning literals rather than computing a join, which the
amendment preserves.

Neither test contains a `CONVENTIONS` token, so this plan's discovery cannot
surface them. They were found by reading the contracts before editing, which is
what round 6 established as the rule.

## T5, T6, T7 — the remaining promotions into the seed

T5 seated the four development-workflow rules; T6 the three coding-convention
rules; T7 promoted the never-commit rule and the report-stale rule into
`## Security considerations` and `## Scoped instructions`, which are now real
sections rather than offered options. T7 also moved the never-commit rule out of
§ Coding conventions, where T2 had placed it as prose, so it is stated once.

The blessed-helpers list stayed out, and a guard asserts the seed never names
`credbroker`, `file_safety` or `UnsafeContentError` — promoting them would hand
an adopter a list of tools they do not have, the same defect as a table of links
they cannot follow.

### T7 exceeded the line cap, and the cause was my task split

After T7's two sections landed the seed was 204 lines against the 200-line cap
T1 set. T8 is the task that trims the optional-guidance comment, so the file was
oversized in the window between them: an invalid intermediate state, which is
exactly what round 6 sustained as "walk the intermediate states" and what the
step-4 check requires each task to avoid.

The fix was not a second cap raise. Round 8 refuted a finding that wanted the
cap pinned in a test, on the ground that § Boundaries already makes raising it
an ask-first action and T8 already runs the linter after the last seed edit —
raising it twice to accommodate my own ordering would have spent that boundary
on a defect rather than a need.

Instead the task that makes an entry false removes it. T7 promotes
`Security considerations` and `Scoped instructions`, so T7 removes those two
offers from the comment; the seed lands at 198. T8 keeps the `Documentation`
entry that T4 made false, plus whatever the comment retains.

That is the correct shape generally: a separate "trim the comment" task was an
artifact of splitting one concern per task, and it created a window where the
file advertised sections it already had. Recorded rather than amended, because
the plan is frozen and each task's own step-4 obligation to leave the tree
working already covers it.

`packs/core/tests/pack/test_repository_context_seed.py` is amended in the same
step: the heading set gains both sections, and only `Repository structure`
remains an asserted offer.

## T8 — the optional-guidance comment, and the cap condition

Removed the `Documentation` offer that T4 made false. `Security considerations`
and `Scoped instructions` were already removed by T7, in the task that made each
real. `Repository structure` survives, because the seed still does not carry it.

Guarded in both directions. Round 6 sustained a cheat that the comment could be
trimmed by deleting it outright, so `test_comment_still_offers_what_the_seed_lacks`
asserts the surviving offer keeps its trigger-and-benefit shape. Negative control
recorded: deleting the comment fails both assertions; restoring it passes both.

### The T1 margin was needed, and by roughly the amount estimated

T1 measured a 187-line projection and set the cap to 200, with the 13-line
margin justified as absorbing re-rendering — the procedure requires each block
land in its destination's own voice rather than being pasted, so source length
is not rendered length.

The seed finished at 196. So re-rendering cost 9 lines against a 13-line margin.
The margin was the right call and was not excessive; had the cap been set to the
projection, T7 would have breached it by 9 rather than by 4, and the ask-first
boundary would have been spent on a measurement error rather than on ordering.

This is the headroom condition round 6 moved here from T1, where it could not
fail because the content did not yet exist. It is now a test that runs the
linter with every promotion present.

## T24 — the consumer sweep

116 → 12. Every file the scan still returns is deletion-bound and owned by T25.

**The agent briefs were the point.** `implementer`, `security-reviewer`,
`discovery-lead` and `release-lead` now load `AGENTS.md` alone. The first two
read the retired document in full on every dispatch, which is the cost this
whole change exists to remove.

### One documented exemption

`packs/core/tests/skills/new-spec/test_acceptance_criteria_discipline.py` lists
`CONVENTIONS.md` among the internal locators shipped guidance must never cite.
That is a *forbidden* literal, not a reference — and keeping it is stronger than
removing it, because it now guards against the retired path being reintroduced
into shipped guidance.

The AC2 predicate cannot distinguish citing the file from forbidding its
citation, so the file is exempted in `ac2-scan.sh` with that reason inline. The
canary then failed, because it pins the script's form by digest — which is the
canary working exactly as designed. Digest updated in the same commit.

### Re-pointings that needed a judgement, not a substitution

- `test_shaping_review_documentation_contract.py` asserted byte-parity between
  the retired document and its seed. Parity is the wrong relation for what
  replaced it: `docs/README.md` deliberately diverges, seed from repository. The
  assertion became presence, with the reason recorded.
- The same file's closed document set is now seven, not eight. The review-lens
  distinction that put the retired document in it moved into `core-pack.md`,
  already a member, so the entry drops rather than being replaced. Substituting
  the docs map would have failed: a doc map is not a review-lens document.
- `test_verification_ledger_contract.py` pinned three regions with their
  clauses. Two anchors survived T15's move into the spec-and-plan contract; the
  third — "A spec directory freezes as a unit" — sat under § Document lifecycle,
  which T3 summarised rather than relocated verbatim. Its clauses are
  spec-lifecycle mechanics, so the subsection moved into the spec-and-plan
  contract where it belongs, and the test points there.
- `test_tdd_stub_lifecycle_contract.py` gained AC9's existence assertion: every
  member of its `live_sources` is proved present before being read, so a
  vanished source cannot make its negative assertion pass vacuously.

### A recurring process defect

Two substitution passes silently matched nothing, because I built the needles
from grep output truncated at 135 characters. A third failed because a Bash
heredoc mangled a Python lambda. In all three cases the command reported success
and the counts caught it. Writing the script to a file and checking the
before/after count is the reliable shape; a replacement that does not match is
indistinguishable from one that had nothing to do.

## T25 — the deletion

`docs/CONVENTIONS.md` and its seed are gone. **AC2 closed**: the recorded scan
returns nothing, so no live source in the repository names the retired path.

`PROJECTED_README_OVERRIDES` is empty. The retired path was its last entry after
the 2026-05-25 amendment shrank it from twenty, so classification now comes from
`EXCLUDED_PATTERNS` alone with no exception. The tuple stays rather than being
deleted — a future Projected path that an excluded pattern would catch belongs
there — and the test that pinned its single entry now pins emptiness.

The scaffold link check was reworked, not deleted. Round 5 found that deleting
it with the file it read would remove the only relative-link check over the
adopter scaffold. It now scans the Markdown this change touches, narrowed on the
same ground as AC14.

## T26 — the release

Both manifests at `2.27.0`. A new free-standing `core` changelog entry above
`2.26.1`, with a `Highlights` block.

The `Highlights` disposition was answered rather than assumed, as
`packs/AGENTS.local.md` step 4 requires: a pack consumer's capability does
change, because adopters stop receiving one file and start receiving another,
and the seeded `AGENTS.md` they install now states the rules instead of pointing
at a file that no longer ships. The `/now/` projection is a pure parser over
these bytes, so an unwritten block would have been a release the public page
never mentions.

AC12 is pinned against `2.26.1`, the version both manifests held before this
change. "Greater than the previous release" — the phrasing an earlier draft
used — was already satisfied by `2.26.1 > 2.26.0` with no edit at all.

### What build-check surfaced, in four passes

Each failure was real, and none was caught by the per-task gates:

1. **CAT-V-014, stale `dist/`.** `build-check` verifies the generated plugin
   tree but does not build it; `make build` does. The `.apm/` edits invalidated
   it.
2. **CAT-V-015, stale self-host projection**, from T24's brief edits and T25's
   deletion. `make build-self` refuses a dirty tree, so this has to be committed
   first, then regenerated, then committed again.
3. **Prose the bulk substitution broke.** T24's blanket regex over
   `governance-extras` produced "an updated the artifact that owns the rule" in
   `JOURNEY.md` and "no `the owning artifact`" in `DESIGN.md`. The web
   projection surfaced the first when `build-self` regenerated it.
4. **Two chain-only flakes**, both passing standalone on this tree and on a
   clean one: `test_next_ordinal_ignores_git_redirect_environment` and
   `test_v_forward_without_backward_warns`. A further run died with a sandbox
   `PermissionError` when a git subprocess timed out and cleanup could not kill
   the child. Three sessions are contending for git and one editable install.

### Two environment facts worth recording

**A piped gate reports the filter's exit code.** The task notification for the
first `build-check` said exit 0 when the gate had exited 2; the truth came from
an explicit `echo "exit=$?"`. Third occurrence this session, and the reason no
gate here is piped any more.

**The shared editable install was repointed away mid-run.** A session in
`loop-dependency-missing-fix` pointed `agentbundle` at its worktree, so
`catalogue verify` ran that tree's code against this one and reported a seed
declaration that is present here at `catalogue_tooling/lint.py:520`. Every gate
here now runs with `PYTHONPATH` set. That is contention management, not a fix:
the split is CLI-versus-repo-local, so `make lint-ruff`, `make lint-mypy` and
`lint-spec-status.py` were never affected.

### Bulk substitution is not a mechanical edit

Three passes matched nothing, because the needles came from grep output
truncated at 135 characters; the counts caught those. Two matched and should not
have, producing ungrammatical prose; the projection caught one and a targeted
search the other. The reliable shape is a script in a file, a before/after
count, and a read of what changed — not a regex over prose.

## Round 9 — post-implementation review

Ten findings, all sustained, none refuted. Three blockers, six concerns, one
nit. Every repair is proved by stripping: with the named content removed the
assertion reds, and it passes again once restored.

### Four controls could not fail, and one hid a live defect

**An exclusion predicate hid a live index.** `docs/product/**` was excluded
wholesale, where the parallel `docs/specs/*/**` exclusion is deliberately
scoped one level down so a directory index stays in domain. `docs/product/
README.md` therefore sat outside AC2, AC2b and AC6 while still linking to the
deleted document in two places. The lesson generalises past this spec: the
exclusion was written from the directory's *usual* content, and a record
directory's index is the exception that lives at its root.

**A pathspec cannot split a file.** `docs/product/changelog.md` mixes a living
maintenance header with dated entries that name the retired document. Excluding
the file protected the entries and hid the header, which held a dangling
pointer. Found by reading the release surface, not by any scan. A file-granular
exclusion over a file with two lifecycles needs a companion guard over the live
region, and that guard must name what it does not reach.

**AC6 never opened the consumer.** The resolver checked that the mapped
destination existed and exposed the written-back heading, which proves the
content landed and not that anything was re-pointed at it. A diagnostic
re-pointed at `docs/work-loop/references/model-selection.md` — a path in no
tree, neither this repository nor an installed adopter one — kept AC6 green.
Three uses cannot carry an in-tree link and now record why rather than passing
silently: the content landed in the citing file; the consumer is not Markdown
and its pointer is pinned as the exact spelling its reader resolves; or the
guidance is not adopter-facing and the note is deleted.

**A needle that can never match widens every window.** `section_of` collapsed
whitespace and then searched the result for a newline-anchored `## `, so the
boundary was never found and every section body ran to end of file. Nothing was
falsely green, because each asserted rule does sit in its own section today —
but the placement half of AC17 and AC20 through AC23 was unenforceable, and
those criteria are stated as "rule X sits under § Y". Proved by relocating a
section body to the end of the file with every token intact: red after the fix,
green before it.

**An ordering is not a pin.** AC12 asserted a version greater than 2.26.1,
which 2.26.2 and 3.0.0 both satisfy, against a criterion that names 2.27.0
exactly and says so because a patch bump satisfies any looser comparison.

### Two controls this change itself left red, and no wave caught them

Both were introduced by re-pointing a constant, and neither had passed since
the wave that wrote it.

`test_sequential_implementer_dispatch_contract` pinned its adopter-facing
surface at the seeded conventions document. Re-pointing that constant at the
seeded `AGENTS.md` aimed it at a file that never carried the clause: the
positive assertion failed outright, and the two sibling negatives over the same
constant went vacuous at the same moment. Supervisor mode is a skill concern
and an adopter scaffold states no dispatch rule, so the rule has one live home
and all three assertions read it there.

`test_spec_index_retirement` paired each governance how-to with both record
indexes, obliging the ADR guide to state the RFC rule. An ADR author does not
regenerate the RFC index.

The shared cause is scope, not care: per-wave verification ran the suites the
wave *touched*, and both defects were in suites the wave's edits *reached*. A
re-pointed constant moves a test's subject without appearing in that test's
own diff. The full roster run is what surfaced both — 1547 passed after the
repairs, and the two failures were the only ones in it.

### The gate chain, and two real failures it found

`build-check` cleared two genuine failures across successive runs, then hit one
environmental wall.

**`catalogue-verify` failed on a poisoned `dist/`.** CAT-V-014 reported a
missing generated output at
`dist/apm/governance-extras/.apm/skills/new-adr/scripts/__pycache__/index-records.cpython-313.pyc`.
The per-skill pack sweep had imported that generator through `importlib`, which
wrote a `.pyc` beside it, and the build copied the `__pycache__` into `dist/`.
Running pytest before the gate is what creates this; the fix is to delete
`dist/`, `build/` and every `__pycache__` so the chain builds them itself, not
to touch the verifier.

**`test-workspace-status` failed on a content pin.** The work-loop
finish-checklist window is hashed, and an earlier wave added one bullet inside
it: a shipped feature's user-facing documentation is updated, routed to the
guides by Diataxis quadrant. That is the phase-slice doctrine the retired
document carried. The pin's protocol is to review the change and decide whether
the engine needs an edit before re-pinning — it does not: the bullet writes no
`spec.md` field, mutates no `workspace.toml` array, and adds no invariant the
engine evaluates. The engine states the same boundary in its own comment, that
its finish checklist only sets `spec.md Status: Shipped`.

**The SAST leg is blocked by machine load, and said so itself.** Two semgrep
*timeout* diagnostics — not findings — on
`packs/core/.apm/skills/work-loop/scripts/loop-cohort.py`, at a one-minute load
average of 112 on 10 CPUs. `--strict` turns a diagnostic into a non-zero exit.
The gate prints the discriminating procedure, and both halves clear it: the
named file is not in this change's diff at all, and the same invocation against
that file alone exits 0 with no diagnostics. Three peer sessions are competing
for this machine; load was still 95 when the single-file run was taken. The
correct disposition is a clean-runner re-run, not a new `SEMGREP_EXCLUDE` entry
— ADR-0102 would require a stated residual and a retirement trigger for an
exclusion, and there is no defect here to state.

The clean-runner re-run the gate asked for came from the same machine at a
lower load, and it is the report the gate's wording requires rather than a bare
"a later run passed": at a starting one-minute load average of 51 on 10 CPUs,
over the identical file set (`tools packs packages tests`) and the identical
invocation, semgrep produced **zero** timeout diagnostics where the load-112
run produced two. `make build-check` then exited 0 with every leg invoked, SAST
and SCA included — one semgrep run, all four `pip-audit` legs and the npm SCA
leg. The timeout count tracks load, not content, which is the discriminator the
gate names.

### What the gate chain caught that no targeted run did

Both real failures came from state the targeted suites cannot see: a `dist/`
tree poisoned by an earlier pytest, and a content hash over a skill window an
earlier wave had edited. Neither is reachable by running the suite that owns
the changed file, because neither failure lives in a suite — one lives in build
output and one in a pin held by a different tool. The chain is the only place
they surface.
