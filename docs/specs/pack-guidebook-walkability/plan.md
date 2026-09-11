# Plan: pack guidebook walkability

- **Status:** Approved <!-- Drafting | Approved | Executing | Done -->
- **Spec:** [`spec.md`](spec.md)

**Repository anchors:** `guides/AGENTS.md` (adopter-facing; frontmatter owned by
`contracts/guide.schema.json`; `author-product-docs` for authoring),
`packs/AGENTS.md` (why no pack source is touched), `web/AGENTS.md` (generated
inputs, the prime-journey anchor), root `AGENTS.md` § Coding conventions (cut
before adding; reuse before building). Analogous implementations:
`guides/atlassian/` for an `order:`-carried sequence — the mechanism, explicitly
not the quality bar — and `guides/product-engineering/how-to/create-a-lean-canvas.md`,
the strongest existing single guide, which already states both an artifact path
and the section that artifact must carry — rows 9 and 10 — and misses rows 1, 5
and 11. Per-surface resolution is in
[`notes/grounding-pass.md`](notes/grounding-pass.md). Named uncertainty: no pack
has ever carried a guidebook, so wave 1 exists to find out what the contract
costs on real content before four more packs are committed to it.

## Design

The contract is the deliverable; the five guidebooks are its proof. Order
matters — a contract fixed after the content it governs ratifies whatever the
content already says.

Three mechanisms already exist and are reused rather than rebuilt:

- **`order:` frontmatter** carries the sequence. `tools/build-site.py:872` lifts
  `order`-bearing guides into an explicit ordered navigation list ahead of the
  kind buckets. No `site.toml` change, so the navigation model
  `cohort-orientation-surfaces` owns is untouched.
- **`kind:`** stays the page contract it already is. A guidebook step may be a
  how-to or a tutorial; the sequence lives in `order`, the page contract in
  `kind`. This is the survey's headline — sequence organises navigation, type
  governs authoring — and the schema already says as much.
- **`JOURNEY.md` stages** are the *first rung* for rows 3, 4 and 6, not a
  universal source. Measured: 13 of 25 stages carry an utterance, 14 a gate, and
  four neither; `contract.youType` is one utterance per pack, not per stage. Each
  row's full ladder and its absence rule are fixed in the spec's Objective and
  checked by AC-0006. `lint-journey-contract.py` freezes each stage's label set
  and order, so the rung that does exist has a stable shape to read.

`journey:` frontmatter is **not** reused: `tools/build-site.py:908` strips it
before writing and nothing reads it. Building on an inert field would look like
reuse and behave like invention.

## Tasks

Each task closes every red test it opens. `Depends on:` is explicit.

## Wave 0 — the contract and its enforcement

### T1 — state the contract

**Depends on:** none.

**Grounding resolved.** The destination is the repository's existing scoped-
guidance mechanism, not a new document. Root `AGENTS.md` § Rule lookups obliges
an agent to read every scoped `AGENTS.md` on the path to the file it is
changing, and § Scoped instructions states that a scoped file carries deltas for
its subtree — so `guides/AGENTS.md` is read by construction by anyone authoring
a guidebook step, which no new document would be.

What is **not** available, and why: `packs/AGENTS.local.md:12` lists
`docs/CONVENTIONS.md` as a self-hosting projection of
`packs/core/seeds/docs/CONVENTIONS.md`, and the two are byte-identical — editing
it edits a projection, and editing its seed is a `packs/**` change this boundary
forbids. `AGENT_RULES.md` and root `AGENTS.md` are seeded for the same reason,
so the conditional-rule table is closed to this slice too. Of the AGENTS-family
files only those two plus `docs/AGENTS.md` and `packages/_example/AGENTS.md` are
seeded; `guides/AGENTS.md` is not. `docs/CONVENTIONS.md` § Documentation classes
at 763-786 is read as governing context, never edited. The survey at
`docs/product/research/workflow-guidebooks-survey.md` owns the evidence and the
confidence behind each obligation.

**Tests:** the AC-0001 cases in `tools/test_lint_guidebook_steps.py` — section
present, normative statement present, obligations enumerated by identifier,
judgement kinds declared without overlapping an obligation identifier, and
prohibited vocabulary declared. Each fails independently, proved by mutation
rather than by red-first ordering: the contract was written before its test, so
the red was earned by removing each part in turn and restoring by editing. The
proofs are in [`notes/verification-ledger.md`](notes/verification-ledger.md).

**Approach:** add the guidebook step contract to `guides/AGENTS.md` as a scoped
section. It carries four things the lint and a reviewer both read: the normative
statement, the obligations by identifier, the closed set of judgement kinds
AC-0014 decides against, and the prohibited-claim vocabulary AC-0009, AC-0013
and AC-0020 scan for.

**It cites the survey for the evidence rather than restating it.** The per-row
standing belongs to one source, and duplicating an eleven-row evidence table
into scoped guidance is the drift this repository's one-source rule exists to
prevent. `guides/AGENTS.md` is 36 lines today and the precedent for a
substantive scoped file is 66 to 80 lines, so the contract fits without turning
the file into a document.

It also records what the contract may not be used to claim — no adoption,
completion or first-value assertion — because that prohibition is the one a
later author is most likely to breach innocently.

**Done when:** the AC-0001 case passes; `guides/AGENTS.md` names every
obligation the spec's table lists, checked by comparing the two rather than by
reading one; and `git diff -- packs/ docs/CONVENTIONS.md AGENT_RULES.md AGENTS.md`
is empty, which is the check that no seeded surface was touched.

### T2 — the lint

**Depends on:** T1.

**Grounding resolved:** `tools/` script conventions and the `--help`-as-docstring
contract named in the spec's Durable Outputs; `Makefile:584` for where
repository-level guide tests are wired.

**Tests:** `tools/test_lint_guidebook_steps.py`, new, red first. Cases for
AC-0002, AC-0003, AC-0014 and AC-0022. Each obligation gets a fixture step that satisfies every
other obligation and violates exactly that one, so a case proves the check it
names rather than the suite as a whole. The stub:

```python
from dataclasses import dataclass
from pathlib import Path

import pytest

OBLIGATIONS = (  # ids, not prose — the prose lives in guides/AGENTS.md
    "position", "prerequisite_cost", "utterance", "attributed_response",
    "variability", "decision", "judgement_check", "failure_path",
    "artifact_location", "artifact_outline", "next_step", "concept_resolved",
)

@dataclass(frozen=True)
class Finding:
    step: str
    obligation: str          # an id from OBLIGATIONS
    detail: str

@dataclass(frozen=True)
class SkillEntry:
    """The per-skill sub-entry AC-0015 requires.

    A step-level value cannot be attributed to one of ten named skills, so the
    three skill-specific obligations live here and nowhere else.
    """
    skill: str
    utterance: str | None
    artifact_location: str | None
    artifact_outline: tuple[str, ...]        # expected headings
    sources: dict[str, str]                  # obligation id -> ladder rung

@dataclass(frozen=True)
class Step:
    path: Path
    stage: str
    order: int
    entries: tuple[SkillEntry, ...]          # one per skill the step names
    values: dict[str, str]                   # step-level obligations only
    sources: dict[str, str]                  # obligation id -> ladder rung

def obligations_from_convention() -> tuple[str, ...]:
    """Parse the obligation ids out of guides/AGENTS.md. Never out of this file."""
    raise NotImplementedError

REGISTERED_CHECKS: dict[str, object] = {}   # filled by @register

# The load-bearing check. Row 10 is the only obligation whose oracle reads a
# second file, and it is what licenses row 7 to carry judgement only: once a
# machine owns structural completeness, asking the reader to re-verify headings
# would degrade the judgement items on the same list.
def check_artifact_outline(step: Step) -> list[Finding]:
    """The step's stated outline must match the skill's declared shape.

    Ladder: the named skill's template asset, else a real committed artifact of
    that type, else authored — and `step.sources` must say which. Reds on a
    heading present in one and not the other, in either direction, so drift is
    a failure rather than silent.
    """
    raise NotImplementedError

FIXTURE = {  # a step satisfying every obligation; values are illustrative
    o: f"<{o}>" for o in OBLIGATIONS
}

def complete_step_except(obligation: str) -> Step:
    """A step satisfying every obligation but `obligation`. Works from the
    literal FIXTURE above, so fixture construction never raises and cannot be
    the reason a case reds."""
    values = {k: v for k, v in FIXTURE.items() if k != obligation}
    return Step(path=Path("fixture.md"), stage="1", order=1,
                entries=(), values=values, sources={})

def check(step: Step) -> list[Finding]:
    """Dispatch to every registered check. Returns [] while the registry is
    empty, which is exactly the first red: no check has been registered yet."""
    out: list[Finding] = []
    for fn in REGISTERED_CHECKS.values():
        out.extend(fn(step))
    return out

def _ids() -> tuple[str, ...]:
    """Obligation ids for parametrisation, resolved at import time.

    Falls back to the literal OBLIGATIONS tuple until
    `obligations_from_convention` is implemented, so collection never depends
    on unimplemented behaviour. AC-0001 is what later guarantees the two lists
    agree.
    """
    try:
        return tuple(obligations_from_convention())
    except NotImplementedError:
        return OBLIGATIONS

@pytest.mark.parametrize("obligation", _ids())
def test_ac0003_each_registered_check_detects_its_own_omission(obligation):
    # The checker-coverage guard, parameterised over ids read out of the
    # contract rather than out of this module. Registry-key equality is not
    # enough: a no-op registered against a new obligation would pass it. So the
    # case builds a step satisfying everything except `obligation` and requires
    # the registered check to emit that identifier.
    step = complete_step_except(obligation)
    assert obligation in {f.obligation for f in check(step)}
```

**Reuse considered first, and declined with the reason.** Four guide tools
already exist and none can carry this:

- `tools/validate_guides.py` validates **frontmatter against
  `contracts/guide.schema.json`** and never walks body content. The obligations
  are body content plus cross-file comparison against `JOURNEY.md` and
  `SKILL.md`; adding that would replace its charter rather than extend it.
- `tools/audit-guide-affordances.py` is the closest — it walks bodies and
  detects five affordances with a per-hit ledger. But it **reports and does not
  gate**, it performs no cross-file source comparison, and the parent brief's
  own rabbit holes rule that promoting it to a gate is "its own decision and
  remains outside this brief". It stays the measurement instrument; T1a uses it
  as one.
- `tools/lint-guide-titles.py` and `tools/check-guide-index.py` each own a
  single narrow invariant unrelated to step structure.

So one new checker is the minimum correct addition, and it is the slice's only
new executable. It takes no new dependency.

**Approach:** `tools/lint-guidebook-steps.py`, reading its obligation
identifiers, judgement kinds and prohibited vocabulary out of
`guides/AGENTS.md`. It takes one or more guidebook
directories, reports one finding per unmet obligation naming the step and the
obligation, and exits non-zero on any finding. Its docstring is its `--help` and
names every obligation, every flag and every exit code.

AC-0003's oracle deliberately reads the obligation ids **out of the
convention**, so the contract stays the source and the lint the enforcement. A
guard that read its own registry would be a control that cannot fail.

**The lint checks structure and never judgement.** `judgement_check` asserts
that row 7 is *present and is not a restatement* — that it does not merely
echo the step's utterance, and does not duplicate a check the lint itself
performs. It cannot assess whether the judgement is a good one, and the
convention says so, because a lint claiming to verify judgement quality would
reach past its oracle.

**Done when:** every case this task's `Tests` names passes, and
`python3 tools/lint-guidebook-steps.py --help` names every obligation the
convention enumerates, compared against it rather than restated, and every exit
code.

### T1a — measure deliverable-form coverage per skill

**Depends on:** none.

**Grounding resolved:** the survey's own caution that an unstated predicate
produces different answers over one corpus.

**Tests:** none of its own; it produces a measurement, not behaviour.

**Approach:** for each of the 74 skills, record whether it ships a template
asset, states its output's shape, and names an artifact path — with the
predicate for each stated in the ledger, because the same question has already
returned 33 and 38 under two different predicates. Write it to
`notes/deliverable-form-ledger.md`.

**Done when:** every skill has a row, each column's predicate is stated, and no
wave ordering anywhere in this plan rests on a figure the ledger does not
carry.

## Wave 1 — prove it on the worst pack

### T3 — the `experience-design` guidebook

**Depends on:** T2 and T1a.

**Grounding resolved:** `guides/AGENTS.md`; `contracts/guide.schema.json`;
`packs/experience-design/JOURNEY.md` (5 stages) and `DESIGN.md` § 1 "The full
sequence" and § 5 "The craft sequence", which own the intra-pack order;
`docs/product/intents/experience-design-delivery-packet.md`, whose guide-authoring
scope moves here per
[`notes/ownership-consolidation.md`](notes/ownership-consolidation.md).

**Tests:** cases for AC-0004, AC-0006, AC-0007, AC-0008, AC-0015 and AC-0022
scoped to this pack, red first; then the lint over this guidebook for AC-0005.

**Approach:** five steps under `guides/experience-design/`, `order: 1..5`, one
per journey stage, each naming the stage it implements. Rows 3, 4 and 6 are
projected from the stage, row 9's path from the named skill's `SKILL.md`; rows
1, 2, 5, 7, 8, 10 and 11 are authored.

This pack is where rows 9 and 10 do the most work. **None of its five journey
stages names a path**, while 15 of its 20 skills name one in their own
`SKILL.md`, so every step's artifact location is projected from the skill rather
than taken from the journey. For row 10 the pack is unusually well placed:
**8 of its 20 skills ship a template asset**, the highest of the five, so the
outline has a source of truth to be checked against rather than invented. The
11 skills with neither a template nor a stated shape are where the outline is
authored, and each one authored is a candidate finding for the cold read in T4.

Row 4 is the one that changes shape: the stage's single fenced block mixes the
typed invocation and the agent's reply, so the step splits them into an
attributed pair — the reader's turn and the agent's turn, separately labelled.

This pack is chosen first because it is the worst and the most load-bearing: 20
published skills, 2 guides carrying no prompt and no output, 10 skills named
nowhere in the journey, and 0 of 20 skills naming what to run next. AC-0008
forces all 20 to be reachable, and the craft sequence in `DESIGN.md` is where
the ten orphans belong — the genre-direct skills replace the
`information-architecture` step only, so they are named at that step rather than
given steps of their own.

**Done when:** every case this task's `Tests` names passes,
`python3 tools/lint-guidebook-steps.py guides/experience-design` exits 0, and
`python3 tools/validate_guides.py`, `python3 tools/lint-guide-titles.py` and
`python3 tools/check-guide-index.py` each exit 0.

### T4 — read wave 1 back before committing four more packs

**Depends on:** T3.

**Grounding resolved:** the AWS runbook practice the survey cites — validate by
having a second person execute the procedure before publishing.

**Tests:** the AC-0021 case. It has no mechanical oracle — a human reads the
recorded answers — and it is the criterion that stops a recorded defect being
deferred past this gate.

**Approach:** a cold read of the built `experience-design` guidebook by a fresh
session given **only** the rendered pages, barred from opening `docs/` or any
file named `spec` or `plan`. It answers **eight** questions per step, not five:
what do I type, what comes back, where do I decide, what do I hold, what do I
run next — plus **does any sentence here tell me I will adopt faster or reach
value sooner, however phrased**, **does any check here ask me to confirm
something a tool could confirm**, and **did any step assume a term or concept it
never explained or linked**. The last three are the semantic residue no
mechanical criterion reaches, and a read that omits them leaves them observed by
nothing. Any step it cannot answer for is a contract or authoring defect,
recorded in `notes/verification-ledger.md`.

**Waves 2 and 3 each close with the same eight-question read** over the packs
they ship. AC-0021 is false until every shipped pack has one, so a single
first-pack read does not discharge it.

If the read shows an obligation that is satisfiable mechanically but useless to
a reader, **stop and surface** rather than carrying the contract into four more
packs. That is the whole reason this task exists between waves.

**Done when:** the cold read is recorded with all eight answers per step,
**every execution defect it found is resolved and the affected step re-read**,
and
`git status --short` is clean. A recorded disposition is not sufficient: AC-0021
is false while any execution defect stands, and T5 must not open while it is
false. If a defect cannot be resolved without changing the contract, stop and
surface rather than deferring it into the next wave.

## Wave 2 — the packs whose journeys already reach every skill

### T5 — `desk-research` and `product-strategy` guidebooks

**Depends on:** T4.

**Grounding resolved:** as T3, plus each pack's `JOURNEY.md` — 3 and 4 stages —
and `DESIGN.md` boundaries.

**Tests:** the AC-0004 to AC-0008, AC-0015 and AC-0022 cases extended to both
packs, red first.

**Approach:** 3 steps for `desk-research`, 4 for `product-strategy`. Both
journeys already name every published skill, so AC-0008 is satisfied on arrival.

**These two are not obviously the cheap wave, and the cost is not yet
measured.** Their journeys already name every published skill, but deliverable
form is a different axis, and the count of skills declaring a shape moves
between predicates — the figure this plan once quoted for `product-strategy` was
a predicate artifact and is withdrawn. **No wave is ordered on deliverable-form
cost until the wave-0 measurement ledger exists** (T1a); these two are sequenced
after wave 1 only because wave 1 proves the contract, which is a dependency and
not a cost claim.

**Done when:** every case this task's `Tests` names passes, the lint exits 0
over both guidebooks, and each pack has its eight-question cold read recorded
with no unresolved execution defect.

## Wave 3 — the packs with the largest orphan sets

### T6 — `product-engineering` and `core` guidebooks

**Depends on:** T5.

**Grounding resolved:** as T3, plus `packs/product-engineering/JOURNEY.md`
(6 stages) and `packs/core/JOURNEY.md` (7 stages), and
`docs/specs/discovery-loop/spec.md`, Shipped, which fixes where
`product-engineering` ends.

**Tests:** the AC-0004 to AC-0008, AC-0015 and AC-0022 cases extended to both
packs, red first.

**Approach:** 6 steps and 7 steps. These carry the largest orphan sets — 9 of 15
and 10 of 18 skills unnamed in their journeys — so AC-0008 does the most work
here. `core` is last because its journey is the longest and it is the pack a
reader reaches after the other four, so its row 10 terminates the walk rather
than continuing it.

**Done when:** every case this task's `Tests` names passes, the lint exits 0
over all five guidebooks, and each pack has its eight-question cold read
recorded with no unresolved execution defect.

## Wave 4 — the walk's surfaces, the consolidation, and the gates

### T7 — correct the walk's surfaces

**Depends on:** none of T3 to T6; it shares no file with them.

**Grounding resolved:** `web/AGENTS.md:7,13` — the latter requires anchoring a
marketing-surface content change on
`docs/design/journeys/team-orientation-future-state.md` and re-gating through
`approve-journey` if a stage's actions or residual pains change. An independent
design pass against that prime journey established that correcting what a card
claims about a pack contract preserves both, so no re-gate is required; the task
re-reads it and stops if that no longer holds.
`docs/design/content/journeys-index.md:72-82` owns the reader-facing grouping.

**Tests:** AC-0009, AC-0010, AC-0018 and AC-0020 over `guides/README.md`'s P2
and P2b spans; AC-0011, AC-0016 and AC-0017 over built output in
`web/src/test/FourDisciplineSequence.test.ts`; AC-0019 over
`web/src/test/rendered-output.test.ts`.

**One existing assertion must be replaced, not extended.** The case at
`FourDisciplineSequence.test.ts:114-131` requires each of the first three cards
to state a handoff — the claim this slice retires. Leaving it green while
correcting the group body would hold the surface false, so AC-0011 covers the
body and all four cards together and that assertion is rewritten with a mutation
per card. All red first except AC-0016, AC-0017
and AC-0019, which pass today and are each re-derived by the mutation recorded
against them before they count as evidence.

**Approach:** remove the whole-pack handoff claim from P2b and from the journeys
index's sequence-group body; re-end P2b's fourth step at an approved decision
brief routed onward to the build loop. Three spans in
`web/src/pages/journeys/index.astro`: the group body, the card copy, and the
source comment at lines 13-16, which walks the retired chain and would lead a
maintainer to restore it. Do not touch `web/src/content/journeys/*.md`.

**Done when:** every case this task's `Tests` names passes after
`make site-build`, and `git diff -- web/src/content/journeys/` is empty.

### T8 — record the consolidation on both sides

**Depends on:** T1, whose contract the records cite.

**Grounding resolved:** root `AGENTS.md`, which forbids silently resolving a
conflict between documented guidance and code and requires updating the owning
source; `docs/product/AGENTS.md` on backlog and governance records.

**Tests:** the AC-0012 case, red first — a three-set comparison: the eligible
target universe derived from the three siblings' accepted-base ledgers, this
ledger's rows, and the reciprocal records. Two-set equality is insufficient and
the case proves it, because a target missing from both sides satisfies it.

**Approach:** first enumerate the concrete carve-out. Read the accepted-base
ledgers of `guide-invocation-outcome-coverage`, `tutorial-worked-examples` and
`how-to-sample-output-coverage`, list every target path each one owns inside the
five packs, and record in the ledger which of those this slice takes and which
each sibling retains. A pack-level statement is not sufficient and AC-0012
compares paths: S3 alone holds 16 `packs/**/.apm/skills/**` targets inside the
five packs that this slice cannot edit, and an aggregate carve-out would strand
any guide target it failed to name.

Then, for each artifact in
[`notes/ownership-consolidation.md`](notes/ownership-consolidation.md), add its
record to its own body: the five-pack carve-out in the three sibling specs; the
partial-delivery note in `skill-sequence-wayfinding`; the moved guide-authoring
scope in `experience-design-delivery-packet`; the recorded boundary in the four
adjacent artifacts. Set the brief's Spec-map cell for this spec to `<auto>` and
narrow its S7 row to this scope. Mark the superseded instruction in
`docs/product/findings/s7-walkability-handoff.md` rather than rewriting it.

None of the sibling accepted-base ledgers gains or loses an entry; the carve-out
is a scope statement, not a re-measurement.

**Done when:** the AC-0012 case passes, and searching for each retired phrasing
returns only the records that document it as retired.

### T9 — gates and ledger

**Depends on:** T2, T3, T5, T6, T7, T8.

**Grounding resolved:** root `AGENTS.md` § Build and test commands.

**Tests:** the AC-0013 case — a scan for adoption, completion, task-success and
first-value claims across every surface this slice writes, which is the one
prohibition no single authoring task owns because it applies to all of them —
plus the full local gate set, each run separately and unfiltered —

```
make site-build
npm run test --prefix web
python3 -m pytest tools/test_lint_guidebook_steps.py -q
python3 -m pytest tools/test_build_site_routing.py -q
python3 -m pytest tests/roster/ -q
python3 tools/lint-guidebook-steps.py guides/desk-research guides/product-strategy guides/experience-design guides/product-engineering guides/core
python3 tools/validate_guides.py
python3 tools/lint-guide-titles.py
python3 tools/check-guide-index.py
python3 tools/audit-guide-affordances.py --ledger notes/affordance-ledger.json
make site-link-check
python3 .agents/skills/author-delivery-brief/scripts/lint-brief-coverage.py
python3 .claude/skills/work-loop/scripts/lint-spec-status.py --root .
```

`lint-brief-coverage.py` is mode `-rw-r--r--` with no execute bit, so it runs
under `python3`; invoking it directly returns permission denied.

**Approach:** confirm the `workspace.toml` membership still matches this spec's
status and that `source.parent` resolves to the brief. Re-run the affordance
audit and record the before-and-after per pack in the ledger — the numbers in
the spec's Objective are its baseline, and a slice that claims to move them owes
the second measurement. Never chain a gate with a commit or a push.

**Done when:** every command this task's `Tests` names has run separately and
exited 0, roster included, and the verification ledger records each result with
its count and runtime, plus the per-pack affordance before-and-after.

## Changelog

- 2026-09-11 — Owner direction: the slice is the guidebook, not the
  cross-pack walk. Orientation exists; a usable guidebook does not.
- 2026-09-11 — Owner direction: derive a consistent guidebook protocol from
  desk research on multi-skill workflow guidebooks, applying the journeys' own
  chat-interaction pattern, and weave it into the spec. Survey at
  `docs/product/research/workflow-guidebooks-survey.md`; the step contract is its
  output.
- 2026-09-11 — Owner decision: all five SOP packs, with the contract proved on
  `experience-design` first.
- 2026-09-11 — Owner decision: this slice supersedes S3, S4 and S5 inside the
  five packs; they keep the rest of the corpus.
- 2026-09-11 — Owner direction: consolidate the superseded intents and slugs.
  Ledger at [`notes/ownership-consolidation.md`](notes/ownership-consolidation.md);
  the earlier `four-discipline-walk-execution` slug is retired.
- 2026-09-11 — **Amendment during T1.** AC-0001's Testing Strategy compared the
  contract's identifiers against the spec's obligation table; that table is
  numbered and carries no identifiers, so the oracle was not implementable. It
  is now structural, with each part failing independently. The baseline was
  re-pinned, which is a re-approval in substance.
- 2026-09-11 — Owner direction: where a guide page needs a key concept
  explained, the step carries that too. Added as obligation 12 — **named and
  linked**, not inlined, because inlining explanation into a how-to is the
  content-drift anti-pattern the survey records at `[high]`; a bounded
  explanation is admitted only where nothing exists to link to, which is a
  labelled house choice. New AC-0022 claims resolution; the cold read gains an
  eighth question for whether a step silently assumed a concept.
- 2026-09-11 — The contract lives in `guides/AGENTS.md`, the existing
  scoped-guidance mechanism for the tree it governs. An earlier draft proposed a
  new document; the repository already has this mechanism, the rule-lookup walk
  makes it read by construction, and `docs/CONVENTIONS.md`, `AGENT_RULES.md` and
  root `AGENTS.md` are all pack-seed projections this slice cannot edit.
- 2026-09-11 — Owner direction: these skills generate artifacts, so the contract
  must carry what to expect from the artifact and where it is located. Row 9
  gained the path and row 10 was added for the shape, giving eleven obligations.
  Measured: 6 of 25 journey stages name a path, against 63 of 74 skills that
  name one in their own `SKILL.md`, so location is projected from the skill.
- 2026-09-11 — Owner decision: the inherited three-whole-pack-handoff premise is
  false against the packs' Shipped contracts. The surfaces are corrected and no
  pack source is touched. Evidence in
  [`notes/walk-premise-correction.md`](notes/walk-premise-correction.md).
