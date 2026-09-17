# Verification ledger — design-output-addressing

## Reviewer gate, 2026-09-16

`reviewers-clean` was fired on the owner's explicit instruction, **not** on a
clean sentinel. No adversarial round returned one. Recording the basis so a
later reader does not mistake the transition for sentinel-backed evidence.

**What the gate rests on.** Eight adversarial rounds, finding counts
21 → 15 → 14 → 8 → 2 → 4 → 3 → 1. Every round's findings were applied. The final
round returned one concern, no blockers, and verified the three substantive
repairs before it: T1's clause enumeration maps one-to-one onto the spec's eight
`The shared containment module states` criteria with no clause asserted that no
criterion carries; T9's three construction tests are differential; and T2's
account of both `type:` literals is true of the tree. That concern is patched,
and a companion sweep over every fact the last three commits changed found one
further instance the round had not reached, also patched.

**What it does not rest on.** No reviewer has seen the two commits that close
round eight. The structural properties were confirmed at round four and
re-confirmed since — every open criterion has an implementing task, and every
`Done when` is reachable from its declared dependency closure — but that
confirmation predates those commits.

**Known residual risk.** The recurring defect through rounds four to eight was a
companion statement left behind by an edit to the thing it described: a count, a
completion condition, or a restatement of a proof standard. It recurred five
times, including inside the fix intended to retire it. Both traversal
instruments were run before this gate; the class is diagnosed, not proven
absent. A reader finding another instance should treat it as expected residue of
that class rather than as a new defect class.

**Owner decision.** The owner approved the spec and plan and instructed
implementation to begin, having been shown the trend, the absent sentinel, and
the option to run a ninth round.

## Execution observation — T6, 2026-09-16

`guides/experience-design/how-to/design-each-screen.md:374` carries the rung
`authored; information-architecture SKILL.md declares the record but not its
path`. T2 gives that skill a declared path, at which point the rung's second
clause is false. No task owns rewriting it: T7's rung work is scoped to
`establish-design-intent.md`, and the guide-agreement test asserts that an
`artifact_location` resolves to a declared path, not that its rung is accurate.

This is the companion-staleness class that produced the majority of findings in
review rounds four through eight, now appearing in implementation: an edit to a
thing leaves a statement about that thing behind.

**Disposition.** Carried into T7 as a bundled fix under the carve-out's Tier 3 —
same area (a guide rung), same concern (a guide claim matching its skill),
visibly smaller than the task, and mechanical. It is not a design call. T7
depends on T2, so the declaration exists by then. Recorded here rather than
amending the approved plan for a one-line correction, and listed under
`Bundled fixes:` when T7 is committed.

## Execution observation — the T7/T8 boundary at `DESIGN.md`, 2026-09-16

T7's first test bans the literal `aesthetic/` from every file under
`packs/experience-design/`. `packs/experience-design/DESIGN.md:248` carries the
row `| aesthetic/ | creative-direction, design-system, design-principles |`, so
T7 cannot pass while that row stands. But T8's approach claims the same edit —
"replace the `aesthetic/` row with `direction/` and `tokens/`" — and T8 depends
on T7, so it runs later. As written, T7's own test fails on a line T8 owns.

**Disposition.** T7 replaces the `aesthetic/` row in `DESIGN.md`; it is the
retire-`aesthetic/` task and its test is the binding check. T8 keeps the other
five `DESIGN.md` corrections named in its approach: `screen-flows/` → the
shipped `screens/`, `design-principles` moved to `principles/`, the missing
`copy/` row, the `screens/` row that credits `interaction-design` with writing
its own file, and the `output_dir` comment listing `briefs/`. T8's completion
condition — every folder-naming surface names only declared folders — is
unchanged by moving one row earlier, and nothing T8 does depends on that row
still being present.

Recorded here rather than amending the approved plan: the task boundary moves,
no obligation is added or dropped, and the plan is frozen.

## Execution observation — T3's template, 2026-09-16

T3 was flagged before dispatch as the task that might not be able to ship a
template that is both clean under `tools/lint-experience-agnostic.py` and
useful to a reader, with instructions to surface the conflict rather than
resolve it. The conflict did not materialise. Every numeral in
`assets/token-taxonomy-template.md` is a step index or a list ordinal; no
palette, dimension, duration, ratio, or easing curve appears. The lint exits 0.
No owner decision was needed.

## Execution observation — T4's excerpt repair, 2026-09-16

T4's frontmatter addition put `surface:` beside an existing `## Surface` body
section that asks the reader for the same value. Two writable homes for one
fact with no tie-breaker is a drift the pack would ship, so the body section was
removed and its explanation carried onto the field.

That removal falls inside a fenced excerpt `establish-design-intent.md`
publishes, and `tools/lint-guidebook-steps.py` requires an excerpt to be a
contiguous verbatim run of its declared source. The excerpt was re-taken from
the template's first line. Doing so also repaired the caption below it, which
claims to show "the opening of the template" and became false the moment
frontmatter went in above the H1.

**Disposition.** Both edits are bundled into T4 rather than deferred. The
caption falsehood is not a pre-existing defect T7 inherits — T4 created it — and
the excerpt is the verbatim mirror of the file T4 edits, so leaving it would
have landed a red lint. No plan task's Tests block covers re-excerpting this
preview: T6 re-excerpted `design-each-screen.md` only, and T7's guide work is
the three `**Where it lands:**` lines and their rungs.

## Unowned defect — the `creative-direction.md` filename, 2026-09-16 — **REPAIRED, see below**

Two shipped surfaces name this skill's artifact `creative-direction.md`:

- `packs/experience-design/.apm/skills/creative-direction/SKILL.md:3`, in the
  `description:` — "Produces ranked aesthetic goals and a `creative-direction.md`
  record".
- `guides/experience-design/reference/experience-design.md:155` — "recorded in
  `creative-direction.md`".

Neither matches the declared target `<output_dir>/direction/<slug>.md`, and
neither matched the previous `<output_dir>/aesthetic/<slug>.md` either — this is
a pre-existing wrong filename, not drift this change introduced. No task's Tests
block covers either line: T4's is the template's frontmatter, and T7's literal
work is scoped to `aesthetic/`, which neither line contains.

**Disposition.** Left alone and recorded. It is a third defect in the same
class the spec addresses — a claim about where a skill writes that disagrees
with where it writes — but repairing it needs a criterion, and inventing one
mid-implementation against a frozen contract is the failure this ledger exists
to avoid. It belongs to the `design-handoff-read` follow-on or a successor, and
should be carried there rather than closed here.

## Execution observation — the containment module has five copies, not four, 2026-09-16

T5 gave `design-review` its own `references/containment.md`. A skill installs
standalone and cannot reach a sibling's `references/`, so the byte-identical
copy is the pack's own mechanism for a shared control — the one T1 chose. The
module therefore has **five** copies: `creative-direction`,
`design-principles`, `design-system`, `information-architecture`, and now
`design-review`. All five carry one md5.

The approved plan says four in three live places — `plan.md:65`, `:103` and
`:153` — and `plan.md:375` specifies T9's declaration test as red "when one
module copy is altered so equality fails". **T9's test must quantify over all
five copies.** A test written from the plan's count would leave the fifth
unpinned, which is the copy most likely to drift: it is the only one held by a
skill that does not write.

No obligation changes. The criterion is equality across the module's copies;
only the population grew, and it grew because T5 added a reader that needs the
controls. Recorded here rather than amending the frozen plan, and carried into
T9's brief.

The module's opening paragraph was generalized in the same commit, identically
across all five copies. It said the module governed "the four writes in this
skill set", which became false the moment a read-only skill held a copy, and
half its controls — intermediate-directory creation, replacing an artifact
already at the target — have no read counterpart. T5 created that falsehood by
adding the fifth copy, so T5 repaired it. Equality is unaffected.

## Execution observation — T7's two undispositioned bundled fixes, 2026-09-16

Two repairs landed in T7 that no prior ledger entry had dispositioned.

**`JOURNEY.md:218`.** The transcript read `screen  docs/design/screens/welcome.md`.
Both `user-flow/SKILL.md:128` and `design-each-screen.md:423` declare the
per-screen brief as `<output_dir>/screens/<slug>/<screen>.md`, so the line
omitted the `<slug>` segment and named a path no skill writes. It sits inside
the fenced block T7's own criterion governs, in a file T7 owns, and the fix is
one path segment. A transcript is what a reader copies, so this is not cosmetic.

**The `design-system` preview at `establish-design-intent.md:197-208`.** It was
rung `authored` and captioned "This skill ships no output template", and showed
five headings — `# Token taxonomy`, `## Semantic roles`, `## Scale rationale`,
`## Accessibility constraints`, `## Composition rules` — that the shipped
template does not have. T3 created both falsehoods by shipping
`assets/token-taxonomy-template.md`. `tools/lint-guidebook-steps.py` cannot
catch it: an `authored` rung disables the excerpt comparison, so the guide can
claim anything.

The preview is re-taken verbatim from the template's opening and rung to its
path. That is mechanical rather than a judgment call **because T4 already made
the identical repair** for `creative-direction` earlier in this same change —
the excerpt boundary, the rung form, and the caption wording are all copied from
it rather than chosen here.

The other twenty-four instances of that caption in `guides/` belong to skills
that genuinely ship no template, including `establish-design-intent.md:88` for
`design-principles`, which has no `assets/` directory. All were left alone.

**Standing observation.** Three of the four wave-3 tasks found a falsehood that
an earlier task in this same change had created — T4's caption, T5's module
opening, T7's preview. Each was repaired by the task that created it rather than
deferred. This is the companion-staleness class the spec's review rounds
diagnosed, now reproducing inside implementation at roughly one instance per
task. A reviewer should expect more of it and treat each as residue of the known
class, not as a new defect class.

## Owner waiver — one `Makefile` line, 2026-09-17 — **REVERSED, see below**

**§ Boundaries § Never do** confines this change to a path list that does not
name `Makefile`. T9 adds one line to it, inside `run-test-suite`:

```
$(PYTHON) -m pytest packs/experience-design/tests/pack/ -q
```

**Measured, both directions.** Without the line,
`tools/lint-pack-test-boundary.py` exits 1: "packs/experience-design/tests/pack
holds a suite that no runner names. Wire it, or add it to `_NO_RUNNER` with the
reason — a suite nobody runs must be declared, not discovered." With it, 0.

The two alternatives are worse. `_NO_RUNNER` lives inside the lint, so taking
that route is editing a lint to pass a gate — which this spec also forbids —
and it would declare the suite permanently ungated. Leaving it unwired ships a
suite that stays green by never executing.

**Owner decision.** The owner was shown the boundary text, the measured exit
codes, and two alternatives — moving both tests to `tests/roster/`, which is
inside the allowed list but stops them shipping with the pack, and amending the
spec's path list, which re-opens approval and forces a cohort reset. The owner
chose to keep the line under this waiver.

Recorded here rather than in `spec.md`: the spec is hash-pinned by the cohort
and takes Status-line pointers only. No obligation changes; one path is added
to what the change may touch.

## Execution observation — the 0116 ordinal collision, 2026-09-17

T9's gate run surfaced a red this change had created: `docs/adr/` held both
`0116-creative-direction-...md` and `0116-direction-folder-name-dataset.md`,
and `tests/roster/test_decision_record_ordinal_uniqueness.py` fails on any
ordinal held by two regular files. T12 introduced it by giving the dataset the
ADR's own ordinal.

It mattered beyond tidiness because T10 wires the roster suite into CI, so the
red would have been wired in rather than found.

Repaired at `0f6debfde` by moving the dataset to `docs/adr/0116-notes/`, the
`<ordinal>-notes/` directory convention already used by more than ten records
in `docs/rfc/` and the mechanism the guard is built around — it skips entries
that are not regular files.

**Two findings worth carrying.** First, the guard's diagnostic prints the word
"companion" next to shared ordinals, which reads as though a companion
exemption exists for files; it does not, and that wording invited the original
mistake. Second, the roster suite was red before this change touched it in one
other place — `tools/test_local_ci_shared_test_deduplication.py` fails three
tests on a clean tree, verified by reverting the Makefile line and re-running.
That one is not this change's to fix, but T10 should not be read as wiring a
green suite.

## The `Makefile` waiver is reversed — both tests moved to `tests/roster/`, 2026-09-17

The waiver recorded above no longer applies. Two facts invalidated it, one of
them a wrong premise I gave the owner when they decided.

**The wrong premise.** I told the owner that pack placement meant the tests
"ship with the pack and run for adopters". They do not. `packs/AGENTS.md:6`
states "tests and pack documentation are not projected", and the runtime export
boundary is `.apm/` only. Pack placement bought no adopter coverage, which was
the sole argument for crossing the boundary.

**The cost rose after the rebase.** `origin/main` commit `029092b94` re-pinned
the shared-test dedup guard's baselines. Verified on a clean `origin/main`
worktree: `test_effective_make_recipes_apply_exact_composition_and_fail_on_mutation`
**passes** there and **failed** on this branch. Attribution was measured, not
assumed — reverting the `Makefile` line alone did not clear it, because the
existence of `packs/experience-design/tests/pack/` drifts the approved plan by
133 items on its own. Keeping pack placement would therefore have required
re-pinning `APPROVED_STANDALONE_PLAN_DIGEST`, `APPROVED_COMPOSED_PLAN_DIGEST`, a
group-count constant, and the audit comment that file demands — all in
`tools/test_local_ci_shared_test_deduplication.py`, a second file outside the
spec's path list.

**Owner decision.** Shown the corrected premise and the measured cost, the owner
chose to move both tests to `tests/roster/`, which the spec's § Never do list
already admits. `Makefile` is now byte-identical to `origin/main`,
`packs/experience-design/tests/` is gone, the dedup guard is green, and **the
change crosses no boundary at all.** The waiver above is superseded, not
exercised.

**What the move cost.** Nothing in coverage: the two tests keep every assertion,
and two of the four mutations were re-run end to end after the move and still go
red with the same messages. The only edit to either file was re-anchoring
`ROOT`/`PACK_ROOT` on the sibling roster convention.

**Carried into T10.** All three experience-design roster tests now reach CI only
through the dispatch-only `test-corpus.yml`. `tests/AGENTS.md` § "Roster is not
auto-discovered" requires a named step in `build-check.yml` plus a
`STEP_DISPOSITION` entry. The pre-existing `test_experience_design_guide_agreement.py`
never had one either, so T10 now closes the gap for three files rather than one.

**One companion the move broke and this commit fixes.** ADR 0116 cited "the
declaration test in `packs/experience-design/tests/`", a directory the move
deletes. It now names the file's real path.

## The `creative-direction.md` filename is repaired, not deferred, 2026-09-17

The entry above deferred this to a follow-on on the reasoning that no task's
Tests block covered either line. Review round 1 sustained it as **F9**, and the
adjudicator refuted the premise that made it out of scope: this branch changed
that target, and the changelog claims the guides now give either the path the
skill writes or a statement that it writes none, so the two lines are stale
companions of this change rather than pre-existing prose.

Repaired in all three places — `creative-direction/SKILL.md:3`, the same file's
body sentence, and `guides/experience-design/reference/experience-design.md`'s
`creative-direction` **Returns:** line, which now matches the `design-principles`
sibling shape. `creative-direction.md` as an artifact name now has zero
occurrences under `packs/experience-design/` and `guides/experience-design/`.

**What this corrects about the earlier entry.** Deferring was the wrong call,
and the reason is worth keeping: "no test covers it" is not the same as "not
this change's defect". The ownership question is whether the change made the
sentence false, and it had.

## Owner waiver — T11's four plan-only case families, 2026-09-17

**Owner:** eugenelim. **Recorded:** 2026-09-17, after review round 1 sustained
finding F7.

`plan.md:442` sets T11's completion condition as "every control has both halves
recorded in the ledger, or a waiver recorded in the spec with its owner", and
`plan.md:439` / `spec.md:155` make an unstageable case a blocking condition
needing a named owner waiver rather than an unverified pass.

**Waived — four case families the plan's Tests block names and the spec's
acceptance criterion never contracted:**

1. an existing target carrying a foreign `type:`
2. a foreign-product target under user-profile configuration
3. blank-template-over-artifact, for the two skills that ship a template
4. matching-`type:` replacement, for all four writes

**Basis.** The owner was shown the measured cost — roughly 28 further agent
runs — against the alternative of measuring only family 4, which is the
data-loss path (`information-architecture` and `design-principles` declare no
amend branch, so a second run on a slug replaces a hand-amended artifact). The
owner chose the waiver for all four.

**What this waiver does not cover.** The spec's own acceptance criterion at
`spec.md:287-291` — a refusal observed, for each of the four writes, against an
inadmissible `output_dir`, a symlinked target and a non-conforming slug, plus
the `design-review` load — is unaffected and is separately evidenced in
`notes/t11-refusal-runs.md`.

**Correction to the record.** This waiver was granted when the owner chose the
25-run population, before implementation began. It was not written down then.
Review round 1 found the omission as F7, correctly: a decision an owner made and
an implementer failed to persist is indistinguishable, in the artifact, from a
control that shipped unmeasured.

## Owner decision — F1 and F3 documented as limits, design deferred, 2026-09-17

**Owner:** eugenelim. Review round 1 sustained two control-design gaps that the
adjudicator ruled advisory, because nothing in the spec or its authority decides
the remedy.

**F1 — the reserved-tree set is not closed.** The module says reserved trees
"include" paths at or beneath `.apm/` for the repo-root branch and gives
`~/.claude/skills` as an example for the user-profile branch. Neither closes the
set nor states a discovery rule, so a realpath inside the repository but outside
`.apm/` — `.git/`, for instance — satisfies every named check. The
user-profile branch's positive test is also circular: it approves `output_dir`
against the root the user-profile config names for design output, which is
`output_dir` itself.

**F3 — product belonging has no discriminator.** The control requires
confirming an existing artifact belongs to the current product and states that a
matching slug cannot distinguish products sharing a user-profile `output_dir`,
but supplies no replacement test. The frontmatter contract carries `type`,
`slug` and `date` only, so a shared user-profile directory plus a common slug
such as `mobile-app` yields a foreign artifact that passes every executable
check.

**Decision.** Both are stated as known limits in the containment module, the way
that module already states the confinement limit, and the design is deferred to
a follow-on. Closing F1 means choosing which trees are reserved; closing F3
means adding a frontmatter field, which needs a migration story for artifacts
already written under 2.0.4 and earlier. Neither choice is fixed by the target
or its authority, and inventing one under review pressure is how a control
acquires a rule nobody can maintain.

**Explicitly not claimed.** With these limits documented rather than closed,
the module must not be read as deciding approval for every input. It decides the
cases it names.
