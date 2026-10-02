# Plan: visual-target rung precondition

- **Spec:** [`spec.md`](spec.md)
- **Status:** Drafting <!-- Drafting | Approved | Executing | Done -->
- **Repository anchors:** `packs/AGENTS.md` § Version bump rule,
  § Security and authoring rules (the eval-harness obligation) and
  § Self-hosting projection; the **root** `AGENTS.local.md` § Landing changes
  (`AGENTS.local.md:49-60`, "Never pass `FORCE=1` from automation") — **not**
  `packs/AGENTS.local.md`, which has no section of that name and whose line 29
  instructs the opposite; `tests/AGENTS.md` § A repository-level assertion
  cannot live in a package test tree, and § Roster steps are named and placed by
  hand;
  `docs/specs/frontend-visual-authority/spec.md:80` (the contract-tier
  `Always do` rule this contract supersedes);
  `packs/frontend-engineering/tests/skills/frontend-engineering/test_visual_authority_precedence.py:41`
  (`UPSTREAM_IDENTIFIERS`, the three literals `visual-observation.md` may not
  contain); `test_visual_authority_release.py:89` (the version pin);
  `test_visual_authority_entrypoint.py:30` (`BODY_BUDGET = 968`).

## Approach

Change the rung's condition in one authoritative place, then hold every other
carrier to a property rather than to a list.

The authoritative place is the precedence table in `visual-observation.md`,
whose `approved-visual-target` row currently states the condition as
`recorded-human-confirmation`. That becomes `visual_target: confirmed`. Every
other carrier restates the rule — deliberately, per `value-derivation.md` — so
changing it is a migration across its homes rather than an edit to one.

The migration is driven by the measured inventory. The enforcement is not: a
test that walks a file list can only ever be as complete as the list was on the
day it was written, and four review rounds on the predecessor contract each
found carriers the previous round had missed. The new test therefore computes
its own scope by sweeping the roots at run time.

### The governance reversal

`docs/specs/frontend-visual-authority/spec.md:80` carries a contract-tier
`Always do` rule: "State rung conditions as properties this pack defines. A
frontmatter value only an upstream template produces is an illustration, never
the condition itself." This contract does exactly what that rule forbids, and
ADR-0132 reverses it deliberately and records why. The reversal is not a licence
to ignore the rule quietly: T5 annotates the superseded spec's `Status` so a
reader of that spec meets the reversal where the rule lives.

### Version bump size

Patch, for both packs. `packs/AGENTS.md` classifies patch for changed content,
minor for new primitives, major for removals. This contract rewords shipped
instructions and adds one test; it publishes no new skill, subagent, command or
hook. Record both slice-start baselines before editing: `frontend-engineering`
is at `0.4.0` and `experience-design` at whatever `visual-target-field` leaves
it, which is `4.1.2` if that slice ships as planned. Read both at execution
time rather than trusting this sentence.

## Constraints

- `visual-target-field` ships first. This contract reads a field that slice
  writes; starting before it lands states a condition on a field no template
  produces.
- `visual-observation.md` may not contain `experience-design`,
  `creative-direction` or `design-system`. `visual_target` is not one of those
  literals, so the rung condition can name the field without tripping the pin.
- `test_visual_authority_slice_two.py` holds two sentences by
  whitespace-normalized match, one of them the rung-1 bullet in
  `frontend-engineering`'s `SKILL.md`, and pins an id plus the literal
  `resolved` in two eval cases. Reformatting those sentences is safe; rewording
  them is not.
- `test_visual_authority_release.py` pins `frontend-engineering`'s `pack.toml`
  version by equality. Its own message says a later delivery moves the pin with
  its own bump, so T6 moves it — it is not a value to change on its own.
- `frontend-engineering`'s `SKILL.md` body is 963 lines against
  `BODY_BUDGET = 968`. Five lines of headroom. Prefer editing sentences in
  place over adding them; if the change needs more, that is an Ask-first bar,
  not a budget to raise.
- No new dependency, module boundary, or top-level directory.

## Construction tests

Every criterion is an assertion over shipped bytes. AC-0006 is the exception
worth naming: it is a sweep, and **a sweep that finds nothing passes whether
the property holds or the sweep is broken**. T4 therefore carries a mutation
check — introduce a violating sentence in a scratch copy, assert the test reds,
remove it — so the test is proved able to fail before it is trusted.

## Stub validation record

Required by `tdd-stubs.md` § *Validate* and § *Record*, which fail closed at
plan approval without them.

**Re-run from scratch 2026-10-02 after round 1**, because round 1 proved the
previous record false: two blocks reddened on `NameError`, not on their
criteria, and `py_compile` cannot tell those apart. Every result below is from
that re-run, against the tree `visual-target-field` left.

- **Compile pass:** `python -m py_compile` over each of the four blocks, run
  from disposable scratch outside the repository test tree. Result: **all four
  compile.**
- **Intended red, each on its own criterion** — this is the claim round 1
  falsified, so each is named with the assertion it reddened on:

  | Block | Placement | Red on |
  | --- | --- | --- |
  | T2 | appended to the pack's `test_visual_authority_precedence.py` | `AssertionError: AC-0001` |
  | T4 | new `tests/roster/test_visual_target_exclusive_property.py` | the property, **14 violations** |
  | T5 | new `tests/roster/test_visual_authority_supersession.py` | `AssertionError: AC-0008: Status does not name ADR-0132` |
  | T7 | appended to `creative-direction/test_contract.py` | `AssertionError: AC-0012` |

  T4's 14 agrees with the extent § *The mechanism* records. That agreement is
  the point of running it: a red count disagreeing with the measured migration
  is measuring something else.
- **T4's second test passes**, reaching 12 non-Markdown carriers against its
  floor of 12. It is the guard against a sweep that finds nothing, and it must
  pass while the property reds.
- **Boundary lint, with both new roster modules present in the tree:**
  `python3 tools/test-lint-pack-test-boundary.py` → **ok — 154 cases passed**,
  exit 0. This is the gate that refused the original placement; the relocation
  is verified against it rather than argued.
- **Isolation:** local, filesystem-confined to the repository and disposable
  scratch, no network. Each block was removed and the tree confirmed clean
  (`git status --porcelain` showing only the two spec files) after every run.
- **Cross-contract check.** T7's block was appended to the module the
  predecessor leaves `_unique_paragraph` in, and `ruff check --select F811` over
  the result is clean. That is the check that matters: T7 reuses the helper
  rather than redefining it, and a second definition would fire F811 under T6's
  `make lint-ruff` gate. Verified again on the re-run.

**What is still owed, and is not evidence yet.** T4's mutation check — a
*newly introduced* violation must red the property, and the property must green
again when it is removed. A standing red over an unmigrated tree does not prove
that. T4's Approach carries it and the verification ledger records both
observations at execution time.

## Durable-output map

| Durable output | Task | Evidence |
| --- | --- | --- |
| Interface compatibility (the rung condition) | T2 | Literal assertions over `visual-observation.md` |
| Behavioural invariant (the exclusive property) | T4 | The sweep test plus its mutation check |
| Producer instruction (converge, visualize, SKILL.md) | T7 | Contract-suite assertions for AC-0012 to AC-0014 |
| Governance record | T5 | Literal assertion over the superseded spec's `Status` |
| Release history | T6 | `test_pack_metadata.py`, the moved pin, and the changelog entries |

## Design (LLD)

### Design decisions

Owned by: T1, T4

The property is stated positively — every sentence that states the condition
must *contain* the field name — rather than negatively as a ban on retired
phrasings. A ban enumerates; a positive requirement does not need to. This is
the one mechanism the predecessor contract's reviewers proposed and nobody
tried, and it is the reason this slice is expected to converge where that one
did not.

Its limit is real and is recorded in the spec rather than left for a reviewer
to find: a carrier that states the condition using none of the confirmation
cues falls outside the property. The cue set is one module-level constant so
that widening it is a visible, deliberate edit.

### Data & schema

Owned by: T2

The rung's condition cell becomes the literal `visual_target: confirmed`. The
value vocabulary is owned by `visual-target-field`; this contract consumes it
and does not extend it.

### Behavior & rules

Owned by: T2, T3

`visual-observation.md` is the authoritative statement. `SKILL.md`,
`frontend-reviewer.md`, the two guide pages and the journey page restate it.
The eval harnesses of both packs assert against it.

### Dependencies & integration

Owned by: T6

Sequenced after `visual-target-field`. Both packs bump, because carriers in
each change. `marketplace.json` is generated: commit first, then run plain
`make build-self`. The **root** `AGENTS.local.md:49-60` forbids passing
`FORCE=1` from automation, and committing first removes the reason to reach for
it. `packs/AGENTS.local.md:29` says "Run `FORCE=1 make build-self`"; that is the
interactive maintainer path, and the root rule governs here.

## Tasks

### T1: Re-measure the carrier extent

**Depends on:** none

**Tests:**
- `no stub (goal-based check)`: the whitespace-normalized sweep runs and its
  result is recorded. Verifies no criterion on its own; it is the discovery
  input every later task depends on.

**Approach:**
- Sweep `packs/`, `guides/`, `web/src/content/`, `tests/` and `docs/design/`
  for `visual[ _-]target` with whitespace normalized before matching.
- The extent at authoring was re-measured on 2026-09-30 and agreed exactly with
  the inventory: 25 files, 59 loci, same file set. **Re-measured 2026-10-02
  against the tree `visual-target-field` left: 27 files, 105 loci, 15 Markdown
  and 12 non-Markdown carriers.** The two new non-Markdown carriers are that
  slice's own roster tests, `tests/roster/test_visual_target_guide_excerpt.py`
  and `tests/roster/test_visual_target_release_surface.py`. The loci jump is
  that slice's additions to the template, the guide excerpt, `converge.md` and
  both packs' eval payloads. This is the expected discovery, and it moved
  AC-0011's stated count from ten to twelve. Record any further difference found
  at execution time as a discovery in the verification ledger.

**Touches:** docs/specs/visual-target-rung-precondition/ (the ledger only)

**Done when:** the sweep result is recorded and compared against the inventory.

### T2: The rung condition names the field

**Depends on:** T1

**Tests:**
- Contract test: the `approved-visual-target` row's condition cell carries
  `visual_target: confirmed`. Verifies AC-0001.
- Contract test: the file carries none of the three upstream identifiers.
  Verifies AC-0002.
- Contract test: `SKILL.md`'s rung-requirement sentence carries the literal.
  Verifies AC-0003.

**Stub** — add to `packs/frontend-engineering/tests/skills/frontend-engineering/test_visual_authority_precedence.py`:

```python
def test_the_top_rung_requires_a_confirmed_visual_target() -> None:
    # OBSERVATION, not VISUAL_OBSERVATION: this module imports the former from
    # frontend_engineering_visual_authority_rules. The latter is defined only in
    # the sibling test_visual_authority_slice_two.py and would raise NameError
    # here — a red indistinguishable from a criterion failure.
    text = read(OBSERVATION)
    row = next(
        line
        for line in text.splitlines()
        if line.strip().startswith("| approved-visual-target")
    )
    assert "visual_target: confirmed" in row, "AC-0001"
    for identifier in UPSTREAM_IDENTIFIERS:
        assert identifier not in text, f"AC-0002: {identifier}"
```

**Approach:**
- Edit the condition cell in place. The row is one table line, so this costs no
  body-budget lines in `visual-observation.md` and none in `SKILL.md` if the
  `SKILL.md` sentence is reworded rather than extended.

**Touches:** packs/frontend-engineering/.apm/skills/frontend-engineering/references/visual-observation.md, packs/frontend-engineering/.apm/skills/frontend-engineering/SKILL.md, packs/frontend-engineering/tests/skills/frontend-engineering/test_visual_authority_precedence.py

**Done when:** `python -m pytest packs/frontend-engineering/tests/skills/frontend-engineering/ -q` and `python3 -m agentbundle catalogue lint --root . --deep` are green. The `--deep` flag is load-bearing: a shallow run reports no body-length finding however long the file is.

### T3: Migrate the restating carriers

**Depends on:** T2, T4

T4 now runs **before** T3, not after. The first draft had T4 `Depends on: T3`
while T3's `Done when` was "T4's property test is green", so the artifact that
closed T3 did not exist when T3 closed. The property is the migration's
instrument; it lands first, reds over the unmigrated tree, and goes green as T3
walks the loci it names.

**Tests:**
- AC-0004 is covered through the T4 property rather than by per-file
  assertions, because a per-file assertion is the closed surface set this
  contract is forbidden to retry.
- `no stub (goal-based check)` for AC-0005: its two loci lie outside every
  mechanism in this contract, so each is a recorded manual observation in
  `notes/verification-ledger.md`, not an assertion. Naming two loci a
  measurement found is not the forbidden closed surface set — the property
  still computes its own scope, and these are its measured complement.
- Contract test: each of the twelve non-Markdown carriers names the field where
  it asserts the rung's precondition, checked over parsed structure — the eval
  payloads' `assertions` entries and the test modules' rung constants.
  Verifies AC-0011's per-pack half; T4 carries its guard half.

**Approach:**
- The measured migration is **14 sentences across 12 Markdown files**, plus
  twelve non-Markdown carriers. Both figures come from running the amended
  property against this tree on 2026-10-02, not from reading the inventory.
  T3 owns eleven of the fourteen: T2 owns the two authoritative statements in
  `visual-observation.md` and `frontend-engineering`'s `SKILL.md`, and T7 owns
  the one in `visualize.md`. Walk them and reword each statement of the rung's
  precondition to name the field. Both packs' eval harnesses are carriers and
  are updated here, which also discharges `packs/AGENTS.md`'s eval-harness
  obligation for both packs.
- **Five of the fourteen are segmentation artefacts**, per the spec's limit 3 —
  `design-system/SKILL.md`'s two tables, the `**Route:**` comment block in
  `token-taxonomy-template.md` and `establish-design-intent.md`, and a second
  `establish-design-intent.md` run-on starting `confirm the shape against what
  you get back.*`, whose `.*` defeats the sentence splitter. Migrate all five;
  do not add table or comment awareness to the property to exempt them. The
  run-on is the worst of them: its only available migration names the field
  inside a copy-paste user prompt that states no condition. Record that in the
  verification ledger as a known cost rather than letting a later round
  rediscover it as a defect.
- **Two AC-0005 loci are migrated by hand**, because no mechanism here reaches
  them. In `guides/frontend-engineering/how-to/read-the-design-handoff.md`,
  `**You are here if** the artifact says somewhere that the composition was
  approved or signed off, rather than merely proposed or picked.` carries no
  target reference at all. In
  `packs/experience-design/.apm/skills/design-system/SKILL.md`,
  `the visual target when one exists` has only the cue `exists`, outside the
  confirmation-cue set. Both are the superseded reading stated plainly. Record
  each as a named observation in the verification ledger.
- Respect the two whitespace-normalized sentence pins and the two pinned eval
  ids in `test_visual_authority_slice_two.py`.

**Touches:** the carriers T1 measured, excluding those T2 owns and excluding
`converge.md`, `visualize.md` and `creative-direction`'s `SKILL.md`, which T7
owns outright. Those three carry both a migration and a gate, and splitting
them across two tasks is how the AC-0006 interaction goes unnoticed; T7 does
both edits in one place.

**Done when:** `python3 -m pytest tests/roster/test_visual_target_exclusive_property.py -q` is green, and the verification ledger records the two AC-0005 observations and the run-on locus cost.

### T4: The exclusive property is enforced, and proved able to fail

**Depends on:** T1

**Where it lives, and why it moved.** `tests/roster/`, not the pack suite the
first draft named. The sweep reads `packs/`, `guides/`, `web/src/content/`,
`tests/` and `docs/design/`, and `tests/AGENTS.md` § *A repository-level
assertion cannot live in a package test tree* forbids a pack test reading above
its own pack — `tools/lint-pack-test-boundary.py` check 8 enforces it on both
`parents[5]` and `REPO_ROOT / root`. That file names `tests/roster/` as the home
for a repository-level assertion and fixes its anchor at `parents[2]`. Landing
there carries the registration obligations T8 discharges.

**Tests:**
- Contract test: the sweep property holds. Verifies AC-0006.
- Contract test: the cue set and the stripped name forms are named constants and
  the docstring records both exclusions. Verifies AC-0007.
- Contract test: the count of **non-Markdown** carriers the sweep reaches has
  not fallen. Verifies AC-0011's guard half. It counts that subset, not the
  aggregate: an aggregate floor stays green while every non-Markdown carrier
  disappears and Markdown ones replace them.
- `no stub (goal-based check)`: the mutation check — the test reds against a
  scratch copy carrying one violating sentence, and greens again once removed.

AC-0005 is **not** verified here. Its two loci lie outside the property by
measurement, and the spec routes them to the verification ledger as recorded
manual observations under T3.

**Stub** — new file `tests/roster/test_visual_target_exclusive_property.py`:

```python
"""The rung's precondition names the field wherever it is stated.

Positive exclusive property: within the swept Markdown scope, every sentence
that refers to a visual target and states a confirmation or approval condition
also contains the literal `visual_target`.

The two tests read different text, deliberately. A name is not a cue — both
`approved-visual-target` and the spaced `approved visual target` carry the word
`approved` as part of what the thing is called — so NAME_FORMS is stripped
before the cue test. A name is still a reference, so the target test reads the
unstripped sentence. Stripping it from both would exempt every carrier that
names the rung and then states its condition, which is most of the migration.

Two limits, stated so they are not rediscovered. A carrier that states the
condition using none of CONFIRMATION_CUES is outside this property, and so is
one whose only cue came from a stripped name. Widening either constant is a
deliberate edit, gated Ask-first by the owning spec.

This module lives in tests/roster/ because the sweep reads above any one pack;
tools/lint-pack-test-boundary.py refuses that from a pack suite.
"""

from __future__ import annotations

import re
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
SWEEP_ROOTS = ("packs", "guides", "web/src/content", "tests", "docs/design")
TARGET = re.compile(r"visual[ _-]target", re.I)
NAME_FORMS = re.compile(r"approved[ -]visual[ -]target", re.I)
CONFIRMATION_CUES = ("confirm", "approved")
SKIP_DIRS = {"__pycache__", "node_modules", ".git"}
NON_MARKDOWN_CARRIER_FLOOR = 12


def _sentences(text: str) -> list[str]:
    return re.split(r"(?<=[.!?])\s+", " ".join(text.split()))


def _swept_files() -> list[Path]:
    found = []
    for root in SWEEP_ROOTS:
        for path in (REPO_ROOT / root).rglob("*"):
            if not path.is_file() or SKIP_DIRS & set(path.parts):
                continue
            found.append(path)
    return found


def _carries_target(path: Path) -> bool:
    try:
        text = path.read_text(encoding="utf-8")
    except (OSError, UnicodeDecodeError):
        return False
    return TARGET.search(" ".join(text.split())) is not None


def test_every_confirmation_sentence_names_the_field() -> None:
    violations = []
    for path in _swept_files():
        # Limit 2: segmentation is meaningless outside prose. In JSON and
        # Python a whole file is one "sentence" — including this module's own
        # docstring, which explains the mechanism and would violate it.
        # AC-0011 covers the non-Markdown carriers over parsed structure.
        if path.suffix != ".md":
            continue
        try:
            text = path.read_text(encoding="utf-8")
        except (OSError, UnicodeDecodeError):
            continue
        if not TARGET.search(" ".join(text.split())):
            continue
        for sentence in _sentences(text):
            # Reference test: the sentence as written.
            if not TARGET.search(sentence):
                continue
            # Cue test: name forms removed, so a name supplies no cue.
            cue_source = NAME_FORMS.sub("", sentence).lower()
            if not any(cue in cue_source for cue in CONFIRMATION_CUES):
                continue
            if "visual_target" not in sentence:
                violations.append(
                    f"{path.relative_to(REPO_ROOT)}: {sentence[:160]}"
                )
    assert not violations, "AC-0006: " + "\n".join(violations)


def test_the_non_markdown_carrier_count_has_not_fallen() -> None:
    """A sweep that finds nothing passes for the wrong reason.

    Counts the non-Markdown subset specifically. An aggregate floor over
    .md/.json/.py stays green while every non-Markdown carrier disappears and
    Markdown ones replace it, which is the shrinkage AC-0011 exists to catch.
    """
    reached = sum(
        1
        for path in _swept_files()
        if path.suffix in {".json", ".py"} and _carries_target(path)
    )
    assert reached >= NON_MARKDOWN_CARRIER_FLOOR, (
        f"AC-0011: sweep reached only {reached} non-Markdown carriers, "
        f"floor is {NON_MARKDOWN_CARRIER_FLOOR} (measured 2026-10-02)"
    )
```

**Approach:**
- Run the mutation check before trusting the test: add one violating sentence
  to a scratch copy of a carrier, confirm red, remove it, confirm green. Record
  both observations in the verification ledger. A standing red does not prove
  the property reds on a *newly introduced* violation; the mutation check does.
- The second test is the guard against the sweep silently reaching nothing.

**Touches:** tests/roster/test_visual_target_exclusive_property.py

**Done when:** both tests are green over the migrated tree and the mutation
check is recorded in the verification ledger.

### T5: The superseded rule is annotated where it lives

**Depends on:** T2

**Where it lives.** `tests/roster/`, for the same boundary reason as T4: the
assertion reads `docs/specs/frontend-visual-authority/spec.md`, and no pack test
may reach above its own pack. The first draft appended it to the pack's
precedence module and dereferenced `REPO_ROOT`, which that module does not
define — the block raised `NameError` rather than failing on AC-0008, and the
recorded intended-red evidence for AC-0008 was false.

Unlike T4's module, this one **names a `docs/specs/<slug>` literal**, so it owes
a `.workspace-prune-protected.toml` entry. T8 carries it. The entry is not
present today: `docs/specs/frontend-visual-authority` is absent from that file,
verified 2026-10-02.

**Tests:**
- Contract test: the superseded spec's `Status` names ADR-0132 and the
  superseded `Always do` rule. Verifies AC-0008.

**Stub** — new file `tests/roster/test_visual_authority_supersession.py`:

```python
"""ADR-0132 supersedes a contract-tier rule in a Shipped spec.

Lives in tests/roster/ because it reads docs/specs/, which
tools/lint-pack-test-boundary.py forbids a pack test from reaching.
"""

from __future__ import annotations

from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
SUPERSEDED_SPEC = REPO_ROOT / "docs/specs/frontend-visual-authority/spec.md"


def test_the_superseded_rung_condition_rule_is_annotated() -> None:
    status = next(
        line
        for line in SUPERSEDED_SPEC.read_text(encoding="utf-8").splitlines()
        if line.startswith("- **Status:**")
    )
    flat = " ".join(status.split()).lower()
    assert "adr-0132" in flat, "AC-0008: Status does not name ADR-0132"
    assert "rung condition" in flat, "AC-0008: Status does not name the rule"
```

**Approach:**
- The existing `Status` reads `Shipped (superseded in part by ADR-0130 —
  960-line body budget; everything else stands)`. "Everything else stands" is
  no longer true once this contract lands, so the annotation both adds ADR-0132
  and removes that clause.
- Prove the intended red from this placement, not from the pack suite: a
  `NameError` and a criterion failure are both reds, and only one of them is
  evidence.

**Touches:** docs/specs/frontend-visual-authority/spec.md, tests/roster/test_visual_authority_supersession.py

**Done when:** `python3 -m pytest tests/roster/test_visual_authority_supersession.py -q` is green and `python3 tools/test-lint-pack-test-boundary.py` is clean.

### T8: Register both roster modules in CI

**Depends on:** T4, T5

**Tests:**
- `no stub (goal-based check)`. `python3 tools/lint-ci-parity.py --root .`
  exits 0, and the construction test that re-derives
  `.workspace-prune-protected.toml` from the roster tests' literal spec paths
  is green. Verifies AC-0015.

**Approach:**
- For each of the two new modules, add a step to
  `.github/workflows/build-check.yml` naming the file, **above** the bulk
  `pytest tests/ -q` carve-out step, carrying the
  `if: "!cancelled() && steps.python.conclusion == 'success'"` guard every
  roster step carries. Placement decides attribution, not execution.
- Add each step name to **both** axes of `tools/lint-ci-parity.py` with
  `LOCAL("test-after-build-check")`: `_LOCAL_STEP_DISPOSITION` (line 341) and
  the `_GATE_MAIN_CHECKS` tuple (line 895). `tests/AGENTS.md` documents only
  the first; a step named in one axis alone is still a violation. The
  predecessor slice registered its two roster tests on both — lines 665, 667
  and 965, 966 — and that is the shape to copy.
- Add `docs/specs/frontend-visual-authority` to
  `.workspace-prune-protected.toml` for T5's module only. T4's module names no
  spec path and owes no entry.
- Run `ruff check .` afterwards. Moving a test out of a pack suite orphans the
  imports only it used, and the repository lint targets do not cover that.

**Touches:** .github/workflows/build-check.yml, tools/lint-ci-parity.py, .workspace-prune-protected.toml

**Done when:** `python3 tools/lint-ci-parity.py --root .` exits 0 and `ruff check .` is clean.

### T7: The producing surfaces are gated on a confirmed target

**Depends on:** T2

**Tests:**
- `test_producing_surfaces_are_gated_on_confirmation` — AC-0012, AC-0013,
  AC-0014 — `stub: true`

**Stub** — add to `packs/experience-design/tests/skills/creative-direction/test_contract.py`:

```python
# `_unique_paragraph` is NOT defined here. `visual-target-field` is a hard
# predecessor and adds it to this same module, so a second definition would
# fire ruff F811 under T6's `make lint-ruff` gate. Reuse what it leaves.


# STUB: AC-0012, AC-0013, AC-0014  (spec: visual-target-rung-precondition)
def test_producing_surfaces_are_gated_on_confirmation() -> None:
    """visual-target-rung-precondition AC-0012 through AC-0014.

    This module also carries other specs' criteria under overlapping numbers,
    so every AC reference here names its spec.
    """
    commitments = _unique_paragraph(
        REFERENCE_ROOT / "converge.md",
        "write the selected direction's compositional commitments",
    )
    assert "visual_target: confirmed" in commitments, "AC-0012"

    boundaries = _unique_paragraph(
        REFERENCE_ROOT / "visualize.md", "record its identity and three boundaries"
    )
    assert "the human has confirmed" in boundaries, "AC-0013"
    assert "visual_target: confirmed" in boundaries, "AC-0013 (own requirement)"

    items = [
        block
        for block in _read(SKILL).split("\n- ")[1:]
        if block.startswith("**Approved visual target**")
    ]
    assert len(items) == 1, "AC-0014: exactly one such list item in SKILL.md"
    item = " ".join(items[0].split())
    assert "the human has confirmed" in item, "AC-0014"
    assert "visual_target: confirmed" in item, "AC-0014 (own requirement)"
```

**Approach:**
- Split `converge.md`'s five-sentence capture paragraph so the
  compositional-commitments instruction is its own blank-line-delimited block
  before gating it. Without the split, AC-0012's unit spans the target path,
  the template copy, the `visualize` handoff and the fill list, and the literal
  could satisfy the criterion from an unrelated sentence.
- Gate all three surfaces in one change. `converge` is the writer; the other
  two are instruction surfaces a producer follows, and leaving either ungated
  would have a producer forming a binding claim the writer then records.
- `visualize`'s condition is the human confirmation it already holds, not a
  field read: it runs before `converge` writes the field. Its sentence still
  names `visual_target: confirmed`, because AC-0013 requires that literal in
  its own right and naming the disposition is not consulting it. Write the gate
  so both readings are obvious — "a target the human has confirmed, which
  `converge` records as `visual_target: confirmed`" — rather than leaving an
  implementer to work out why both literals are there.
- **The gated sentences are outside AC-0006 after the 2026-10-02 amendment.**
  `converge.md`'s `When an approved visual target exists, write ...` strips to
  `When an exists, write ...`, which carries no cue. That reconciliation is no
  longer load-bearing; the three criteria stand on their own. `visualize.md`
  carries a *separate* in-scope sentence — `**Approved visual target** — a
  composition the human has confirmed ...` — which T7 migrates along with the
  gate, because T7 owns that file outright.

**Touches:** packs/experience-design/.apm/skills/creative-direction/references/converge.md, packs/experience-design/.apm/skills/creative-direction/references/visualize.md, packs/experience-design/.apm/skills/creative-direction/SKILL.md, packs/experience-design/tests/skills/creative-direction/test_contract.py

**Done when:** `python3 -m pytest packs/experience-design/tests/skills/creative-direction -q` is green.

### T6: The release surface is consistent

**Depends on:** T2, T3, T4, T5, T7, T8

**Tests:**
- `no stub (goal-based check)`. `tests/conformance/test_pack_metadata.py`
  passes, both packs' three version sites agree and exceed their recorded
  slice-start baselines, the release pin equals the new `frontend-engineering`
  version, and the changelog carries one entry per pack with a
  `### Highlights` subsection naming the rung precondition. Verifies AC-0009,
  AC-0010.

**Approach:**
- Read and record both slice-start baselines before bumping.
- Move `test_visual_authority_release.py`'s pin in the same change as the bump,
  and update its docstring to name this delivery.
- Commit, then run plain `make build-self` to regenerate `marketplace.json`.

**Touches:** packs/frontend-engineering/pack.toml, packs/frontend-engineering/.claude-plugin/plugin.json, packs/experience-design/pack.toml, packs/experience-design/.claude-plugin/plugin.json, .claude-plugin/marketplace.json, docs/product/changelog.md, packs/frontend-engineering/tests/skills/frontend-engineering/test_visual_authority_release.py

**Done when:** `make lint-ruff lint-mypy` and `tests/conformance/test_pack_metadata.py` are green.

## Rollout

- **Delivery:** one PR, after `visual-target-field` lands. Reversible by
  reverting it.
- **Infrastructure:** none.
- **External-system integration:** none.
- **Deployment sequencing:** T1, T2, then T4 (the property lands red), then T3
  (the migration turns it green), with T5 and T7 in any order alongside, then T8
  to register the two roster modules, then T6.

## Risks

- **The property's cue set is narrower than English.** A carrier phrased
  without `confirm` or `approved` escapes it. This is stated in the spec and
  carried in one constant so widening it is deliberate. It is a smaller risk
  than the three mechanisms this contract replaces, each of which assumed the
  author already knew the full extent.
- **Body budget.** `SKILL.md` has five lines of headroom. If T2's rewording
  needs more, stop and ask rather than raising `BODY_BUDGET`, which a Shipped
  spec owns.
- **The sweep test is repository-wide and will be read by every later change.**
  A future contract that legitimately discusses visual targets in prose will
  trip it. That is the intended cost; the escape is to name the field, not to
  weaken the property.

## Changelog

- 2026-10-02 (round 1): Revised from eleven sustained findings. The round found
  one thing the contract could not survive and several it could not verify.
  **The enforcing test could not live where the contract put it.** A pack test
  may not read above its own pack, `tools/lint-pack-test-boundary.py` check 8
  enforces it, and T4's sweep reads five repository roots. T4 and AC-0008's
  assertion both move to `tests/roster/` anchored at `parents[2]`, which
  `tests/AGENTS.md` names as the home for a repository-level assertion. That
  placement carries three registration obligations, so **T8 and AC-0015 are
  new** — a named build-check step above the bulk step, a `STEP_DISPOSITION`
  entry on *both* axes of `lint-ci-parity.py`, and a
  `.workspace-prune-protected.toml` entry for T5's module only, which is the
  one naming a `docs/specs/<slug>` literal.
  **Two stubs reddened on `NameError`, not on their criteria.** T2 called
  `read(VISUAL_OBSERVATION)` where its module exports `OBSERVATION`; T5
  dereferenced a `REPO_ROOT` the pack defines nowhere. `py_compile` cannot see
  either, so the previous Stub validation record asserted evidence it did not
  have. The record is re-run from scratch and now names the assertion each
  block reds on.
  **T3 could not close.** Its `Done when` was T4's test going green while T4
  depended on T3. T4 now runs first: the property lands red and T3's migration
  turns it green.
  **AC-0005 had nothing that could decide it**, and the owner narrowed it
  rather than widening the cue set. Adding `exists` and `present` was measured —
  14 sentences to 19, three of the five additions stating no condition — and
  declined. AC-0005 now asserts over the sentences AC-0006 reaches and names
  its two outside loci for hand migration.
  **Two counts were wrong.** The segmentation-artefact class is five, not four;
  `establish-design-intent.md` carries two, the second a run-on whose `.*`
  defeats the splitter. And limit 3 still carried a pre-amendment "seven"
  beside the amended "fourteen".
  **One citation pointed at a file that says the opposite.** The no-`FORCE=1`
  rule is in the root `AGENTS.local.md:49-60`; `packs/AGENTS.local.md` has no
  § Landing changes and its line 29 instructs `FORCE=1 make build-self`.
  Finding #12 was refuted and nothing was changed for it: `NAME_FORMS` matches
  the two forms AC-0006 names, and `approved_visual_target` occurs nowhere in
  the repository.
- 2026-10-02: Revised after T1's re-measurement against the tree
  `visual-target-field` left, before any reviewer started. Three changes, each
  from a measurement rather than a reading.
  (1) **The property's cue test now strips the artefact's name.** `approved
  visual target` carries `approved` as part of what the thing is called, so
  every mention supplied its own cue: 24 sentences fired, and 17 of them stated
  no condition. The cue test now runs on the sentence with both name forms
  removed. The reference test still runs on the unstripped sentence, because
  stripping it from both dropped the two carriers AC-0004 names — including
  `read-the-design-handoff.md`, the most explicit surviving statement of the
  reading ADR-0132 retires. Measured: 24 → 7 → **14** across the three
  variants. The owner chose the narrowing on 2026-10-02 and the asymmetry
  follows from the measurement that narrowing alone lost AC-0004.
  (2) **AC-0011's count moved from ten to twelve**, four eval payloads and
  eight test modules. The two new ones are `visual-target-field`'s own roster
  tests. Extent is now 27 files and 105 loci, from 25 and 59.
  (3) **T5's stub asserted `adr-0131`** where AC-0008 and T5's own Approach say
  ADR-0132. Stubs materialize byte-identically, so this would have shipped a
  test green against the wrong record.
  Limit 3 is new and records a fourth measured class: a Markdown table or HTML
  comment block carries no terminal period, so normalization joins unrelated
  rows into one sentence. Four of the fourteen are that class. They are
  migrated, not exempted — a structural parser is machinery four loci do not
  justify.
- 2026-09-30: Revised after the predecessor's review round 4. Reconciled
  AC-0006 with the inherited gating criteria: a gated sentence in `converge.md`,
  `visualize.md` and `SKILL.md` carries the `visual_target` literal, because the
  sweep property requires the literal and not a field read, and naming a
  disposition is not consulting it. Without that statement an implementer
  following AC-0013's "not a field read" wording would have written a sentence
  that reds T4. Added the producing surfaces to both output tables, gave T7
  sole ownership of its three carriers so T3 and T7 no longer overlap, and
  stopped T7 redefining a helper the predecessor adds to the same module.
- 2026-09-30: Inherited AC-0012, AC-0013 and AC-0014 from `visual-target-field`,
  which retired them as AC-0005 to AC-0007 on the owner's ruling. Gating
  `converge`'s compositional-commitments write moves the
  `approved-visual-target` rung, so it belongs in the slice that changes the
  rung rather than in one whose stated outcome was that nothing downstream
  changes. Added T7 to carry them.
- 2026-09-30: Drafted. Third slice cut from `visual-target-confirmation`,
  carrying the consumer change and the carrier migration. Authored against a
  re-measured carrier sweep, which agreed exactly with the recorded inventory
  at 25 files and 59 loci. Uses the positive exclusive property a predecessor
  reviewer proposed and nobody tried; the three mechanisms that failed are
  named in the spec and not retried.
