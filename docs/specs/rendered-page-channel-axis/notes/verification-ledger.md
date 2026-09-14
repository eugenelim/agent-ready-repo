# Verification ledger — rendered-page inspection channel axis

Execution observations for this delivery. The spec states outcomes and the plan
states mechanism; what actually happened when a task ran is recorded here.

## T1 — the reference states the channel axis

**Ran 2026-09-13.** Content complete and verified.

- Every table in the new `## Channels` section parses under `table_rows`'s
  cell-count rule, and `unique_keyed` rejects a duplicate key in each of the
  three blocks — band rows, rule rows, and the forbidden-token column.
- `capture_set_rules()` returns
  `{'every-captured-width-and-height-needs-the-pair': 'required'}`; the reference
  holds no remaining instance of the old key.
- `make build-self` exited 0 and left no projection diff.
- `python3 -m pytest packs/frontend-engineering/tests/skills/frontend-engineering/ -q`
  reported **4 failed, 234 passed in 1.24s**. All four failures are the pins the
  adversarial review named, and all four are T2's to re-decide:
  `test_an_extra_captured_height_needs_its_scrolled_counterpart`,
  `test_the_every_captured_height_rule_is_shipped`,
  `test_no_check_enforces_a_capture_rule_the_pack_does_not_state`, and
  `test_a_duplicate_capture_set_rule_row_is_rejected`. The last fails exactly as
  predicted — its `md.replace` is a no-op under the rename, so `assert mutated
  != md` prints two identical strings and names no cause.

### Deviation: T1's `Done when` is mis-scoped, carried forward to T2

**Owner decision 2026-09-13: carry forward, no amendment.**

T1's `Done when` requires that a search for `every-captured-height-needs-the-pair`
across `packs/frontend-engineering/` "returns no remaining site". T1's `Touches`
is the reference alone, and the plan assigns the remaining sites to T2, so the
condition cannot be met by T1. The line was written while repairing an
adversarial finding about mis-stating this same sweep, over-correcting from
"names a count" to "demands zero"; the plan sealed before the line was tested
against the task boundary.

What T1 discharged is the sweep itself. Its output, which is the enumeration and
not a recollection:

| File | Sites |
| --- | --- |
| `tests/skills/frontend-engineering/test_rendered_page_verdict.py` | `:196`, `:220`, `:221`, `:447`, `:448` |
| `tests/skills/frontend-engineering/frontend_engineering_rendered_page_rules.py` | `:247` |

Six sites across two files, both already in T2's `Touches`. The zero-site
condition is verified at the end of T2. No acceptance criterion changes.


## T8 — the step performed end to end across two channels

**Ran 2026-09-13 against a real surface.** AC-0017's four values, and a finding.

- **Route:** `/agent-ready-repo/docs/contributing/`, the built docs site served
  from `build/docs` at its configured base path.
- **Channel basis:** `declared-breakpoints`. One breakpoint declared, `1152`,
  because that is where the vendored Starlight component switches the right-hand
  rail from an in-flow block to a fixed full-height column. Bands `<1152` and
  `>=1152`; capture widths `1151` and `1152` by the shipped rule.
- **Result state:** `completed`. Eight captures, two channels x two heights x two
  scroll positions, each carrying all five required fields.
- **Verdict:** `fail`. One unresolved finding of `Blocker` severity.

### Observations

| Capture | width | height | scroll | rail fixed | article top | rail empty tail |
| --- | --- | --- | --- | --- | --- | --- |
| below-1152-short-at-rest | 1151 | 600 | 0 | no | 648 | 20 |
| below-1152-short-scrolled | 1151 | 600 | 400 | no | 248 | -380 |
| below-1152-tall-at-rest | 1151 | 900 | 0 | no | **948** | **319** |
| below-1152-tall-scrolled | 1151 | 900 | 400 | no | 548 | -81 |
| from-1152-short-at-rest | 1152 | 600 | 0 | yes | 101 | -48 |
| from-1152-short-scrolled | 1152 | 600 | 400 | yes | -299 | -48 |
| from-1152-tall-at-rest | 1152 | 900 | 0 | yes | **101** | 252 |
| from-1152-tall-scrolled | 1152 | 900 | 400 | yes | -299 | 252 |

**Finding — `clipped-at-rest-top`, severity `Blocker`.** At 1151x900 at rest the
whole content column is blank: the article's first line sits 948px down a 900px
viewport, so a reader who never scrolls sees the navigation sidebar beside an
empty white column and no article at all. The rail holds 799px of height with
319px of empty space below its last in-flow child. One pixel wider, at 1152x900
at rest, the same page renders correctly with its first line 101px down.

The two captures differ only in viewport width, and `matchMedia('(min-width:
72rem)')` reports `false` at 1151 and `true` at 1152 — read from the page rather
than compared against a copy of the number, so a dependency moving its breakpoint
cannot leave a width silently unchecked.

This is the defect class the delivery exists for, found by the axis it adds. A
capture set taken only at 1280, 1440 and 1920 sits entirely in the `>=1152` band
and reports this page as sound. The finding is in `docs-site`, outside this
delivery's scope, and a fix for it already exists on another branch; it is
recorded here as the run's observation, not taken into this change.

### A false pass caught before it was recorded

The first run of this capture served `build/docs` as the server root. The site is
built for the base path `/agent-ready-repo/docs`, so every stylesheet 404'd and
every page rendered unstyled. The geometry probes still returned numbers —
`railEmptyTail: 0` everywhere, `articleTop` identical across both channels — and
the run would have been recorded as `completed` / `pass` on a page with no CSS
applied at all. Reading one capture rather than the numbers is what exposed it.
The rule the pack already states covers this: a value naming only filenames does
not satisfy the observations field, and neither does a table of measurements
nobody looked behind.


## Post-gates review round 1 — 24 findings, all sustained

Two reviewers ran against the shipped diff. `adversarial-reviewer` returned 9,
all sustained by `finding-adjudicator` with none refuted; `quality-engineer`
returned 15. They converged on the same class of defect from opposite sides, and
the class is the one this delivery exists to remove: **a control that cannot fail
on what it names.**

### What was green and should not have been

Each of these was a passing suite before the round. Every one is now red under the
same mutation:

| Mutation | Before | After |
| --- | --- | --- |
| Delete `\| every-required-channel-needs-the-matrix \| required \|` | 269 passed | 37 failed |
| Rename the worked snippet's channel to `mobile` | 269 passed | 3 failed |
| Replace `forbidden_channel_name_tokens`' body with a hard-coded list | 269 passed | 1 failed |
| Rewrite the snippet's widths to 768 and 900, outside their own bands | 269 passed | 1 failed |
| Empty the manifest `viewports` row to `none` | 269 passed | 2 failed |

The first is the worst. `evaluate_capture_set` read the row that gates the entire
channel axis with a bare `.get(...) == "required"`, so **deleting the row turned a
single-channel capture set from `incomplete` to `complete`** — the axis silently
disabled. One line below, the sibling pair rule went through `_required_rule`,
which raises. The spec's own `Always do` says "Raise on an absent rule row rather
than skipping the rule it governs" and the plan's § Design decisions says "The
absent-row guard is the raise, not the skip". Five rules honoured that; the one
that mattered most did not. Both now route through one seam, `_rule_in_force`, and
a per-row test walks every rule row the completeness walk reads rather than the
one that happened to fail.

AC-0008's own test missed it because its fixture deleted the whole `## Channels`
section — which raises via the section reader — instead of the row the criterion
names. A control shaped to the mutation its author imagined rather than the one
the criterion describes.

### Criteria reopened

AC-0008, AC-0011, AC-0012 and AC-0013 went back to `[ ]` and the spec to
`Implementing`. AC-0011 named a construction test that never existed; AC-0013's
must-red half was `lens.replace(X, "")` followed by `assert X not in …`, true by
construction for every input. Four further criteria cited test names that did not
resolve to shipped tests. Those were ticks written from a reading rather than from
a run.

### Deviation: the content pin reaches four of the five strings the plan named

**Recorded rather than repaired.** `plan.md` § Design decisions names five shipped
strings stating the superseded height-only floor and says all five are rewritten
and pinned. Four are: two `evals.json` strings in `HARNESS_SUPERSEDED_FLOOR`, two
guide strings in `SUPERSEDED_FLOOR`. The fifth, the how-to's height-keyed capture
table, is neither rewritten nor pinned — because it was not superseded. The prose
above it now frames it as the matrix taken *in every channel*, so the table still
states the contract correctly and rewriting it would say the same thing twice.
The plan was sealed before that was known. Both pin sites now state the full
reach and name each other, so a maintainer at either one sees the whole pin.


## Gate note: the catalogue gates were read through the wrong install

**Not a defect in this delivery, and not repaired here.**

After the review fixes, `python3 -m agentbundle catalogue lint --root . --deep`
reported one error — `CAT-L029 packs/core/seeds/AGENT_RULES.md:
agent-rules-preamble-invalid` — and `catalogue verify` failed with the matching
`CAT-V-002`. The same two gates had run clean twice earlier in this delivery.

The file is not in this delivery's diff, and the commit that last touched it is an
ancestor of the approved baseline. What changed is the linter, not the tree:

```
agentbundle resolves to  /Users/eu.gene.lim/orca/agent-ready-repo/...   (primary checkout)
this worktree is         /Users/eu.gene.lim/orca/workspaces/.../ui-viewports

lint  through the primary checkout   1 ERROR
lint  through this worktree's code    0 errors
verify through this worktree's code   ok
```

The editable install points at the primary checkout, so a bare `python3 -m
agentbundle` runs whatever revision that checkout is on. It has since advanced to
`a6bb22320 feat(core): inline the cognitive-load clauses into both AGENTS.md
files (#1296)`, which tightens the agent-rules preamble rule. `origin/main` is
now four commits ahead of this branch.

`PYTHONPATH` was used to **diagnose** this and not to fix it. The seed is not
edited here: satisfying #1296's rule belongs to that change's follow-through, and
editing a `packs/core/` seed from this delivery would route around the cause
rather than address it. **This branch needs a rebase onto `origin/main` before
merge, and the seed update is rebase work.**


## Post-gates rounds 2 and 3

Round 2: 13 findings across the two reviewers, **one refuted**. Round 3: 7, none
a blocker. Both rounds are the same story as round 1 told smaller — each repair
was narrower than the claim it carried, and the reviewers kept finding the gap
between them.

### The refutation, which is the round's most useful result

`adversarial-reviewer` raised as a Blocker that "the commit asserts both that the
pack has shipped and that its contract has not" — four criteria reopened to
`- [ ]` while `pack.toml`, both plugin manifests and the topmost changelog
heading carry `0.2.4`. It was accepted here and was wrong.
`docs/CONVENTIONS.md:489` governs: "No new shipped acceptance debt" applies to a
spec *newly transitioning* to `Shipped`, and directs that a spec with remaining
accepted work "stays `Implementing` across sessions" — the exact observed state.
A deferral marker is required only for work *removed* from the AC set, and none
was. The version bump is obliged by `packs/AGENTS.md` § *Version bump rule* for
pack content already changed, unconditionally on criteria state. No work was done
on it.

### Controls that degraded silently

Three rounds produced one recurring shape, and it is the shape this whole
delivery exists to remove:

| Mutation | before | after |
| --- | --- | --- |
| Copyedit `\`narrow\` at ≤480` → `\`narrow\`, covering ≤480` | 285 passed | 1 failed |
| …then rename those channels to `mobile` / `desktop` | 285 passed | 3 failed |
| Ship a rule row nothing requires | 285 passed | 2 failed |
| Rewrite `SKILL.md`'s declaring prose to device names | 275 passed | 2 failed |
| Delete any of the six shipped rule rows | 3 of 5 green | 44–49 failed each |

The first pair is the sharpest. An ordinary copyedit that changed no channel name
killed the `prose-declaration` shape outright, and a device rename then shipped
green *behind the dead shape*. A guard that stops matching in silence is worse
than no guard, because the suite keeps reporting coverage it no longer has. Two
of the three shapes were anchored only incidentally, by controls written for
other reasons; "happens to be anchored" is not a control, so each shape is
pinned to the shipped site it was written for. That pin was first a separate
`SHAPE_LIVE_SITES` map and is now the `live_site` field of `ChannelNameShape`,
after a later round collapsed four parallel registries into one record.

### A claim settled instead of hardened

`WALK_RULE_ROWS` carried a comment saying a newly shipped row "inherits the
delete-and-red discipline instead of needing to be remembered into a hand-written
list" — while being that list. Three rounds argued the claim. The fix was not a
better list: it is `REQUIRED_RULE_ROWS`, named for what it holds, plus an
equality control comparing it against the keys the shipped tables actually state.
The asymmetry the quality reviewer named — over-listing already caught,
under-listing not — is now symmetric.

### A process error of the orchestrator's

The first adjudication of round 2 returned two findings **indeterminate** because
this session edited the cited file while the adjudicator was reading it: it saw
`CHANNEL_NAME_SITES` as a three-entry tuple, re-read the same path minutes later
and found it gone. The remedy was to commit, quiesce, and re-adjudicate against a
fixed basis, where both came back refuted — the repairs had discharged them. A
review target must hold still for the length of its review.

### Criteria verified rather than recalled

All 18 construction tests the criteria name were collected by name and run: every
one resolves. Four criteria had previously been ticked against test names that
did not exist, which is what reopening AC-0008, AC-0011, AC-0012 and AC-0013 was
for.


## The gate was narrower than the change, and caught it by accident

**A defect shipped by T9 survived four review rounds and every gate run in this
delivery.** `tests/roster/test_verification_ledger_contract.py::test_the_core_release_heading_sits_directly_beneath_unreleased`
requires the `core` heading to sit **directly** beneath `[Unreleased]` —
adjacency, not "a core heading somewhere above". T9 put the
`frontend-engineering 0.2.4` entry at the top and displaced it.

The gate used throughout was `packs/frontend-engineering/tests/` plus the one
roster file this delivery wrote. That is a defensible gate for a pack change and
an indefensible one for a change that edits `docs/product/changelog.md`,
`pack.toml`, `.claude-plugin/plugin.json` and `.claude-plugin/marketplace.json` —
four files outside the pack, none of them read by any test in the chosen gate.

It surfaced because a path was mistyped and one run widened to the whole roster
suite. A narrower command — the one that looked correct — would have shipped it.
**The lesson is not "run more tests". It is that a gate has to be chosen from the
files the change touches, not from the subsystem the change is about.** Four of
this delivery's nine tasks wrote outside `packs/frontend-engineering/`, and the
gate never moved to follow them.

Two compounding errors, both the same shape as ones already recorded above:

- The commit that carried the failing state (`61e65598d`) asserts "295 passed,
  ruff clean" in its message. The shell chain gated `git commit` on `git add`
  succeeding, not on pytest passing — the same construction as the earlier run
  that reported `ruff exit=0` when the 0 belonged to `tail`. A git note carries
  the correction; the commit is not rewritten because the branch builds on it.
- The failing run was read as "the commit landed" rather than "the gate failed".
  The exit code consulted was the chain's, not the suite's.

Fixed in `1ce654b74`. Full roster sweep after the fix: **1500 passed, 6 skipped**.
AC-0015 still holds — it requires the entry to be topmost *for this pack*, and no
other `frontend-engineering` heading precedes it.


## What runs on a PR, and what this delivery therefore owes

**Corrected 2026-09-14 after an adversarial finding. The first version of this
section was wrong, and a register entry had already been built on it.**

It claimed "no test written by this delivery runs on a pull request" and marked
`test-roster.yml` unreachable by PR. That was derived by grepping
`tools/repo/build_gate_chain.py` for its `_pytest_step` calls and concluding
about the whole PR gate — without reading `build-check.yml`, which carries 57
`python -m pytest` invocations of its own. A filtered grep over one file was
allowed to stand for an exhaustive answer about a different file.

Measured rather than inferred:

| Surface | PR trigger | Reaches this delivery's tests |
| --- | --- | --- |
| `build-check.yml` | yes | **partly** — `:410` runs `python -m pytest tests/ -q` from the root, collecting 1506 `tests/roster/` node IDs |
| `build-check.yml` | yes | **no** for the pack suite — `packs/frontend-engineering` appears 0 times in the workflow |
| `docs.yml` | yes | no |
| `test-corpus.yml` (`make test`) | dispatch only | yes — `Makefile:574` runs the pack suite |
| `test-roster.yml` | dispatch only | yes, and redundantly: the roster is already reached by `build-check.yml` |

What that changes:

- **AC-0019 is PR-gated.** Its three tests in
  `tests/roster/test_rendered_page_channel_axis_supersession.py` are collected by
  `build-check.yml`. Placing it in the roster on the test-boundary argument cost
  nothing in reach.
- **The changelog invariant is PR-gated.** `test_the_core_release_heading_sits_directly_beneath_unreleased`
  is collected too. The round-5 defect therefore survived a narrow **local**
  command, not an absent CI gate — which is what this ledger's own "caught it by
  accident" section actually describes, and the correction does not soften it.
- **AC-0014 is PR-gated by one case, and weakly.** The predicate that case
  asserts is narrower than the criterion's wording; § *AC-0014's verification is
  weaker than the criterion it verifies* below carries the measurement.
- **The residue is real and narrower than claimed.** `packs/frontend-engineering/tests/`
  is named nowhere in `build-check.yml`, so the **292** tests that path collects —
  every channel-axis guard and every mutation control five review rounds argued
  over — are PR-ungated. The `test-corpus.yml` dispatch remains obligatory
  evidence for this delivery. The roster dispatch is not obligatory, only
  confirmatory.

  The figure is 292 and not 295, and the difference is the point of this whole
  section. 295 was 292 plus the three tests in
  `tests/roster/test_rendered_page_channel_axis_supersession.py` — the three the
  bullet above has just established **are** PR-gated. Carrying the larger number
  here would re-import them into the ungated set, in the section written to
  replace an unmeasured figure with a measured one. Both counts are what the
  collector reports for the path named beside them.

**Deviation, recorded rather than repaired.** T9's `Done when` names
`make build-self` and `ruff check`, neither of which reads a `docs/` file, while
T9's own `Touches` lists `docs/product/changelog.md`. The plan was sealed before
that mismatch was visible. The obligation is carried here and discharged in the
closeout: `gh workflow run test-corpus.yml` is dispatched against this branch
after push, and its result belongs to this delivery's evidence.


## AC-0014's verification is weaker than the criterion it verifies

**Recorded, not repaired.** AC-0014 states that both manifests carry `0.2.4`. Its
PR-reachable artifact asserts something weaker:

```
tests/conformance/test_pack_metadata.py::test_pack_and_plugin_versions_match[frontend-engineering]
    assert plugin.get("version") == _pack_data(pack_dir)["version"]
```

That is **agreement** between the two manifests, not the value the criterion
names. The criterion stays green on two manifests both reading `0.2.3`, and the
literal `0.2.4` is pinned by nothing — it appears nowhere in `tests/`, `tools/`,
`.github/` or the `Makefile`. The sibling parametrization,
`test_pack_declares_enriched_metadata[frontend-engineering]`, is collected on the
same PR but reads no version field at all: it asserts readme, license,
`links.repository`, categories, keywords and maintainers.

The spec's own Testing Strategy describes AC-0014's check as "compare the two
manifests' version fields", which *is* the agreement predicate — so the
criterion's text and its verification differ in strength by exactly this much,
and the Testing Strategy is the honest half. The gap is in the criterion's
wording, which names a literal **no PR-reachable check** reads. The literal was
read at delivery by direct inspection of both manifests, stated three paragraphs
down — so the gap is in what CI would catch on a future edit, not in what was
verified here.

Not repaired here for two reasons. The first is an **assumption, not a cited
rule**: pinning `0.2.4` anywhere would create a surface that must be edited on
every subsequent release of this pack, which seems a poor trade for the coverage
it buys. `packs/AGENTS.md` § *Version bump rule* warns only against borrowing an
unreleased version from another change, and no convention in
`docs/CONVENTIONS.md`, `packs/AGENTS.md`, `docs/adr/` or `guides/` warns about a
per-release pinning surface — an earlier draft of this section attributed the
judgement to a convention that does not carry it. The second reason does not rest
on a citation: a criterion whose only defect is that it names a value its
PR-reachable check does not read is a wording matter on a `Shipped` spec, not a
behaviour defect, and both manifests do carry `0.2.4`, verified by direct read at
delivery.

Recorded because a future reader of AC-0014 has no other way to discover it. This
was single-copy in the spec's `Follow-ons` bullet — grepped across all three
artifacts and present in exactly one — and that bullet was then shortened to a
routing pointer on both reviewers' advice, so without this section the
observation would have been deleted rather than relocated.
