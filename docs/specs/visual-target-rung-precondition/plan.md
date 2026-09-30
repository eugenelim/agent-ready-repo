# Plan: visual-target rung precondition

- **Spec:** [`spec.md`](spec.md)
- **Status:** Drafting <!-- Drafting | Approved | Executing | Done -->
- **Repository anchors:** `packs/AGENTS.md` § Version bump rule,
  § Security and authoring rules (the eval-harness obligation) and
  § Self-hosting projection; `packs/AGENTS.local.md` § Landing changes;
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
ADR-0131 reverses it deliberately and records why. The reversal is not a licence
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

- **Compile pass:** `python -m py_compile` over each of the four blocks, run
  from disposable scratch outside the repository test tree. Result: **all four
  compile.**
- **Intended red:** appended to a disposable copy of the owning test modules,
  collected and run under pytest, then removed. Result: **red**, including T7's
  inherited gating assertions and T2's rung-condition assertion, each on its
  own criterion. The sweep test in T4 is validated separately by its own
  mutation check, because a sweep that finds nothing passes for both the right
  and the wrong reason.
- **Isolation:** local, filesystem-confined to the repository and disposable
  scratch, no network. No isolation downgrade was needed.

## Durable-output map

| Durable output | Task | Evidence |
| --- | --- | --- |
| Interface compatibility (the rung condition) | T2 | Literal assertions over `visual-observation.md` |
| Behavioural invariant (the exclusive property) | T4 | The sweep test plus its mutation check |
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
`make build-self`. `packs/AGENTS.local.md` § Landing changes forbids passing
`FORCE=1` from automation, and committing first removes the reason to reach for
it.

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
  the inventory: 25 files, 59 loci, same file set. Record any difference found
  at execution time as a discovery in the verification ledger; a new carrier is
  expected behaviour for this contract, not a failure.

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
    text = read(VISUAL_OBSERVATION)
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

**Depends on:** T2

**Tests:**
- AC-0004 is covered through the T4 property rather than by per-file
  assertions, because a per-file assertion is the closed surface set this
  contract is forbidden to retry.
- Contract test: each of the ten non-Markdown carriers names the field where it
  asserts the rung's precondition, checked over parsed structure — the eval
  payloads' `assertions` entries and the test modules' rung constants — and one
  guard asserts the count of non-Markdown carriers the sweep reaches has not
  fallen. Verifies AC-0011.

**Approach:**
- The measured migration is **29 sentences across 15 Markdown files**, plus ten
  non-Markdown carriers. Both figures come from running the property against
  this tree on 2026-09-30, not from reading the inventory. Walk them and reword
  each statement of the rung's precondition to name the field. Both packs' eval harnesses are carriers and
  are updated here, which also discharges `packs/AGENTS.md`'s eval-harness
  obligation for both packs.
- Respect the two whitespace-normalized sentence pins and the two pinned eval
  ids in `test_visual_authority_slice_two.py`.

**Touches:** the carriers T1 measured, excluding those T2 owns

**Done when:** T4's property test is green over the full swept scope.

### T4: The exclusive property is enforced, and proved able to fail

**Depends on:** T3

**Tests:**
- Contract test: the sweep property holds. Verifies AC-0005, AC-0006.
- Contract test: the cue set is one named constant and the docstring records
  the property's limit. Verifies AC-0007.
- `no stub (goal-based check)`: the mutation check — the test reds against a
  scratch copy carrying one violating sentence, and greens again once removed.

**Stub** — new file `packs/frontend-engineering/tests/skills/frontend-engineering/test_visual_target_exclusive_property.py`:

```python
"""The rung's precondition names the field wherever it is stated.

Positive exclusive property: within the swept scope, every sentence that
refers to a visual target and states a confirmation or approval condition
also contains the literal `visual_target`.

Limit, stated so it is not rediscovered: a carrier that states the condition
using none of CONFIRMATION_CUES is outside this property. Widening the set is
a deliberate edit, gated Ask-first by the owning spec.
"""

from __future__ import annotations

import re
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[5]
SWEEP_ROOTS = ("packs", "guides", "web/src/content", "tests", "docs/design")
TARGET = re.compile(r"visual[ _-]target", re.I)
CONFIRMATION_CUES = ("confirm", "approved")
SKIP_DIRS = {"__pycache__", "node_modules", ".git"}


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


def test_every_confirmation_sentence_names_the_field() -> None:
    violations = []
    for path in _swept_files():
        try:
            text = path.read_text(encoding="utf-8")
        except (OSError, UnicodeDecodeError):
            continue
        if not TARGET.search(" ".join(text.split())):
            continue
        for sentence in _sentences(text):
            if not TARGET.search(sentence):
                continue
            if not any(cue in sentence.lower() for cue in CONFIRMATION_CUES):
                continue
            if "visual_target" not in sentence:
                violations.append(
                    f"{path.relative_to(REPO_ROOT)}: {sentence[:160]}"
                )
    assert not violations, "AC-0006: " + "\n".join(violations)


def test_the_sweep_actually_reaches_the_known_carriers() -> None:
    """A sweep that finds nothing passes for the wrong reason."""
    reached = sum(
        1
        for path in _swept_files()
        if path.suffix in {".md", ".json", ".py"}
        and TARGET.search(" ".join(path.read_text(encoding="utf-8", errors="ignore").split()))
    )
    assert reached >= 25, f"AC-0006: sweep reached only {reached} carriers"
```

**Approach:**
- Run the mutation check before trusting the test: add one violating sentence
  to a scratch copy of a carrier, confirm red, remove it, confirm green. Record
  both observations in the verification ledger.
- The second test is the guard against the sweep silently reaching nothing; it
  is why the property is trustworthy rather than merely present.

**Touches:** packs/frontend-engineering/tests/skills/frontend-engineering/test_visual_target_exclusive_property.py

**Done when:** both tests are green and the mutation check is recorded.

### T5: The superseded rule is annotated where it lives

**Depends on:** T2

**Tests:**
- Contract test: the superseded spec's `Status` names ADR-0131 and the
  superseded `Always do` rule. Verifies AC-0008.

**Stub** — add to the same precedence test file:

```python
def test_the_superseded_rung_condition_rule_is_annotated() -> None:
    status = next(
        line
        for line in (REPO_ROOT / "docs/specs/frontend-visual-authority/spec.md")
        .read_text(encoding="utf-8")
        .splitlines()
        if line.startswith("- **Status:**")
    )
    flat = " ".join(status.split()).lower()
    assert "adr-0131" in flat, "AC-0008"
    assert "rung condition" in flat, "AC-0008"
```

**Approach:**
- The existing `Status` reads `Shipped (superseded in part by ADR-0130 —
  960-line body budget; everything else stands)`. "Everything else stands" is
  no longer true once this contract lands, so the annotation both adds ADR-0131
  and removes that clause.

**Touches:** docs/specs/frontend-visual-authority/spec.md, packs/frontend-engineering/tests/skills/frontend-engineering/test_visual_authority_precedence.py

**Done when:** the precedence suite is green.

### T7: The producing surfaces are gated on a confirmed target

**Depends on:** T2

**Tests:**
- `test_producing_surfaces_are_gated_on_confirmation` — AC-0012, AC-0013,
  AC-0014 — `stub: true`

**Stub** — add to `packs/experience-design/tests/skills/creative-direction/test_contract.py`:

```python
def _unique_paragraph(path: Path, anchor: str) -> str:
    """The one blank-line-delimited block carrying `anchor`, in this file only."""
    blocks = [b for b in re.split(r"\n\s*\n", _read(path)) if anchor in b]
    assert len(blocks) == 1, f"{anchor!r} must occur in exactly one block of {path.name}"
    return " ".join(blocks[0].split())


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

    items = [
        block
        for block in _read(SKILL).split("\n- ")[1:]
        if block.startswith("**Approved visual target**")
    ]
    assert len(items) == 1, "AC-0014: exactly one such list item in SKILL.md"
    assert "the human has confirmed" in " ".join(items[0].split()), "AC-0014"
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
  field read: it runs before `converge` writes the field.

**Touches:** packs/experience-design/.apm/skills/creative-direction/references/converge.md, packs/experience-design/.apm/skills/creative-direction/references/visualize.md, packs/experience-design/.apm/skills/creative-direction/SKILL.md, packs/experience-design/tests/skills/creative-direction/test_contract.py

**Done when:** `python3 -m pytest packs/experience-design/tests/skills/creative-direction -q` is green.

### T6: The release surface is consistent

**Depends on:** T2, T3, T4, T5, T7

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
- **Deployment sequencing:** T1, T2, then T3, T5 and T7 in any order, then T4,
  then T6.

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
