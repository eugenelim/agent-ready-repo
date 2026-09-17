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

## Unowned defect — the `creative-direction.md` filename, 2026-09-16

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
