# Plan: visual-target field

- **Spec:** [`spec.md`](spec.md)
- **Status:** Drafting <!-- Drafting | Approved | Executing | Done -->
- **Repository anchors:** `packs/AGENTS.md` § Version bump rule,
  § Security and authoring rules (the eval-harness obligation) and
  § Self-hosting projection; `packs/AGENTS.local.md` § Marketplace and release
  pipeline; the **root** `AGENTS.local.md` § Landing changes — that section is
  in the root file, not the packs-scoped one, and the two rules it carries
  (never pass `FORCE=1` from automation; regenerate before staging) are what
  the release step below follows; `docs/product/changelog.md` header;
  `tools/lint-guidebook-steps.py:672-690` (`_appears_verbatim_in`, the
  contiguous-verbatim-run check that couples the template to
  `establish-design-intent.md`);
  `packs/frontend-engineering/.apm/skills/frontend-engineering/references/design-handoff.md:37,46`
  (the read takes the frontmatter as found and requires only `type:`, which is
  what makes an added key compatible with artifacts that predate it).

## Approach

Additive within one pack. The field is written but not read, so nothing
downstream changes and the slice cannot move a rung by accident. The producing
surfaces are scoped in the same change as the field, because a field that
exists while `converge` still records a binding claim for an unconfirmed target
would put the artifact in a state the successor slice then has to interpret.

One producer behaviour changes: `converge` currently writes compositional
commitments whenever a target exists, and afterwards writes them only for a
confirmed one. That is the change the release entry's `### Highlights`
subsection is owed for. Nothing downstream changes, because no consumer reads
the field.

The scope on each producing surface is worded as a condition on the producer's
own act of writing, never as a read of the field by a second party. The one
field-literal form — AC-0005 — is `converge` conditioning its own write on the
disposition it itself records, which the spec's `Never do` ruling places inside
the carve-out. `visualize` in particular
cannot read the field: it runs before `converge` on the only route that reaches
it, and `converge` is what creates the artifact and writes the disposition. Its
condition is therefore the human confirmation the operation already holds.

### Version baseline and target

**This is the canonical statement of both values. Every other mention in the
spec or this plan refers here rather than restating them.**

- **Slice-start baseline: `4.1.1`.** Observed, not assumed: `git show $(git
  merge-base HEAD origin/main):packs/experience-design/pack.toml` carries
  `4.1.0` and `git show HEAD:packs/experience-design/pack.toml` carries
  `4.1.1`. The branch already carried `4.1.1` because the sibling
  `creative-direction-inherit-scope` slice released it. AC-0009 measures against
  `4.1.1`; measuring against `origin/main` would pass on the sibling's bump.
- **Target: `4.1.2`, a patch bump.** `packs/AGENTS.md` § Version bump rule
  classifies patch for changed content, minor for new primitives, major for
  removals. This slice adds a frontmatter key and rewords instructions inside an
  existing skill; it publishes no new skill, subagent, command or hook, so no
  new primitive exists.

## Constraints

- No consumer reads the field in this slice. An instruction telling a producer
  when to write it is not a consumer read.
- The template's opening lines are reproduced verbatim at
  `guides/experience-design/how-to/establish-design-intent.md` and checked by
  `tools/lint-guidebook-steps.py`. Every template edit re-derives that excerpt
  in the same commit. The lint tests for a contiguous verbatim run, not a pinned
  line range, so it cannot by itself prove the excerpt gained the new lines —
  AC-0012 covers that separately.
- No new dependency, module boundary, or top-level directory; no sidecar file.
- `design-handoff.md` keeps saying only `type:` is required and the read takes
  the frontmatter as found, so artifacts predating the field stay valid.

## Construction tests

Every criterion is an assertion over a shipped file's bytes, except AC-0008
(the guidebook lint).

The scoping criteria assert an exact literal **inside a bounded unit** — a
paragraph block or a list item, as the spec's Testing Strategy defines them —
read from the single file the criterion names, with the anchor's uniqueness in
that file asserted rather than assumed. An earlier draft bounded on `". "` in
whitespace-normalized text; that admits any adjacent period-free heading or
bullet into the unit, so a scoped heading above an unscoped instruction would
pass. A whole-file substring check is worse still: it is the presence-check
mechanism the predecessor contract recorded as tried and rejected.

### Stub validation record

Required by `tdd-stubs.md` § *Validate* and § *Record*, which fail closed at
plan approval without it.

- **Compile pass:** `python -m py_compile` over each block, run from disposable
  scratch outside the repository test tree. Result: **all four blocks compile**,
  after one bounded correction pass — the contract allows exactly one. The
  first pass failed on T1's block: a literal triple-backtick fence marker
  cannot survive inside a fenced code block. It is now built as `"`" * 3`,
  which compiles and keeps the plan's own fencing intact.
- **Intended red:** each block appended to a disposable copy of
  `packs/experience-design/tests/skills/creative-direction/test_contract.py`,
  collected and run under pytest, then the copy removed; T4's block ran the
  same way under `tests/conformance/`. Result: **all five stub tests fail
  against the current tree**, each on its own AC assertion — `visual_target` is
  absent from the template, the guide excerpt, `converge.md`, `visualize.md`,
  `SKILL.md` and the eval harness, and the release test reds with
  `4.1.1 does not exceed the slice-start baseline 4.1.1`, which is round 1's
  borrowed-version blocker now mechanically enforced rather than argued. No
  test passed vacuously.
- **Isolation:** the run was local, filesystem-confined to the repository and
  disposable scratch, with no network use. No isolation downgrade was needed.
- **Coverage tally:** 13 criteria — 11 covered by stubs, 2
  `no stub (goal-based check)` (AC-0008 the guidebook lint; the manual
  start-of-work baseline half of AC-0009). 0 uncovered.

## Durable-output map

| Durable output | Task | Evidence |
| --- | --- | --- |
| Interface compatibility (the template) | T1 | Contract-suite assertions |
| Current product truth (the guide excerpt) | T1 | `lint-guidebook-steps.py` exit zero plus AC-0012 |
| Behavioural coverage (the eval harness) | T3 | Contract-suite assertion over the harness JSON |
| Release history | T4 | `tests/conformance/test_pack_metadata.py`, the recorded baseline check, and the changelog entry |

## Design (LLD)

### Design decisions

Owned by: T1

`visual_target` is frontmatter because that is where the artifact already
carries machine-read lifecycle state. The body's `**Target:**`, `**Binding:**`
and `**Confirmation record:**` lines are provenance for a human reader; the
section comment says so and names the frontmatter key as canonical, which is
what stops the body's existing `"none"` wording becoming a second home for the
state.

An absent field reads `unconfirmed`. Nothing in this slice consumes that
reading — the successor does — but the template's comment states it so an
adopter writing an artifact today records the disposition deliberately, and
AC-0011 holds the comment to it.

The `**Confirmation record:**` placeholder offers the confirmation's date and
where it was recorded, per ADR-0131. It deliberately does not offer a "who",
because the spec's `Never do` rail forbids a person's name, handle or contact
detail there and a placeholder that asks for one invites the breach.

### Data & schema

Owned by: T1

The closed set is `none | unconfirmed | confirmed`, written as a quoted
placeholder exactly as `status` is.

### Behavior & rules

Owned by: T1, T2

Three producing surfaces state when a target's binding reaches the artifact:
`converge.md`, `visualize.md`, and `creative-direction`'s own output contract in
`SKILL.md`. `converge` is the only writer; the other two are instruction
surfaces a producer follows, and leaving either unscoped would have a producer
forming a binding claim the writer then records.

### Dependencies & integration

Owned by: T4

`creative-direction-inherit-scope` is **not in flight — it has already landed on
this branch**, as commits `2ba21c97b` and `eaaa5039a`. Its spec directory no
longer exists, and its release consumed version `4.1.1` together with the
`## [experience-design][4.1.1]` changelog entry. Two consequences bind this
slice: the release baseline is the one recorded in § Version baseline and
target, not the version on `origin/main`; and the existing changelog entry
belongs to that slice, so this one authors its own rather than extending it.

## Tasks

### T1: The template carries the field, and the guide excerpt still matches

**Depends on:** none

**Tests:**
- `test_template_carries_the_visual_target_disposition` — AC-0001, AC-0002,
  AC-0003, AC-0011 — `stub: true`
- `test_guide_excerpt_carries_the_new_template_material` — AC-0012 —
  `stub: true`
- `no stub (goal-based check)` — AC-0008 —
  `python3 tools/lint-guidebook-steps.py guides/experience-design` exits zero.

**Stub** — add to `packs/experience-design/tests/skills/creative-direction/test_contract.py`:

```python
TICKS = "`" * 3  # written this way so the literal survives a fenced code block
FENCE = TICKS + "markdown"


def _fenced_excerpt(text: str) -> str:
    """The guide's reproduced-template block, not the file around it."""
    after = text.split(FENCE, 1)[1]
    return after.split(TICKS, 1)[0]


# STUB: AC-0001, AC-0002, AC-0003, AC-0011
def test_template_carries_the_visual_target_disposition() -> None:
    template = _read(TEMPLATE)
    frontmatter = template.split("---", 2)[1]
    assert re.search(
        r'^visual_target:\s*"<none \| unconfirmed \| confirmed>"\s*$',
        frontmatter,
        re.M,
    ), "AC-0001: frontmatter must carry visual_target over the closed set"

    section = template.split("## Approved visual target", 1)[1].split("\n## ", 1)[0]
    record_lines = [
        line
        for line in section.splitlines()
        if line.startswith("**Confirmation record:**")
    ]
    assert len(record_lines) == 1, "AC-0002: exactly one confirmation-record line"
    assert re.fullmatch(
        r"\*\*Confirmation record:\*\* <[^<>]*date[^<>]*> — "
        r"<[^<>]*(where|record|location)[^<>]*>",
        " ".join(record_lines[0].split()),
    ), "AC-0002: two slots, a date and a location, and no third"

    comment = section.split("-->", 1)[0]
    assert "visual_target" in comment, "AC-0003"
    for label in ("**Target:**", "**Binding:**", "**Confirmation record:**"):
        assert label in comment, "AC-0003"
    assert "bind nothing on their own" in comment, "AC-0003"
    assert "unconfirmed" in comment and "absent" in comment.lower(), "AC-0011"


# STUB: AC-0012
def test_guide_excerpt_carries_the_new_template_material() -> None:
    guide = _read(
        PACK_ROOT.parents[1]
        / "guides"
        / "experience-design"
        / "how-to"
        / "establish-design-intent.md"
    )
    excerpt = _fenced_excerpt(guide)
    assert "visual_target" in excerpt, "AC-0012: inside the fence, not the file"
    assert "**Confirmation record:**" in excerpt, "AC-0012"
```

**Approach:**
- Re-derive the guide excerpt in the same commit as the template edit. The lint
  compares the excerpt to its declared source verbatim, so a template edit alone
  reds it, and a guide edit alone reds it the other way. AC-0012 is separate
  because the lint proves only that *some* contiguous run matches.

**Touches:** packs/experience-design/.apm/skills/creative-direction/assets/creative-direction-template.md, guides/experience-design/how-to/establish-design-intent.md, packs/experience-design/tests/skills/creative-direction/test_contract.py

**Done when:** `python3 -m pytest packs/experience-design/tests/skills/creative-direction -q` and the guidebook lint are both green.

### T2: The producing surfaces are scoped to a confirmed target

**Depends on:** T1

**Tests:**
- `test_producing_surfaces_are_scoped_to_a_confirmed_target` — AC-0004,
  AC-0005, AC-0006, AC-0007 — `stub: true`

**Stub** — add to the same file:

```python
def _unique_paragraph(path: Path, anchor: str) -> str:
    """The one blank-line-delimited block carrying `anchor`, in this file only.

    Bounding on markdown's own delimiter rather than on ". " keeps an adjacent
    period-free heading, bullet or table cell out of the unit.
    """
    blocks = [b for b in re.split(r"\n\s*\n", _read(path)) if anchor in b]
    assert len(blocks) == 1, f"{anchor!r} must occur in exactly one block of {path.name}"
    return " ".join(blocks[0].split())


# STUB: AC-0004, AC-0005, AC-0006, AC-0007
def test_producing_surfaces_are_scoped_to_a_confirmed_target() -> None:
    disposition = _unique_paragraph(
        REFERENCE_ROOT / "converge.md", "Record the approved visual target disposition"
    )
    assert "visual_target: confirmed" in disposition, "AC-0004"
    assert "visual_target: unconfirmed" in disposition, "AC-0004"

    commitments = _unique_paragraph(
        REFERENCE_ROOT / "converge.md", "compositional commitments into the doc"
    )
    assert "visual_target: confirmed" in commitments, "AC-0005"

    boundaries = _unique_paragraph(
        REFERENCE_ROOT / "visualize.md", "record its identity and three boundaries"
    )
    assert "the human has confirmed" in boundaries, "AC-0006"

    skill = _read(SKILL)
    items = [
        block
        for block in skill.split("\n- ")[1:]
        if block.startswith("**Approved visual target**")
    ]
    assert len(items) == 1, "AC-0007: exactly one such list item in SKILL.md"
    assert "the human has confirmed" in " ".join(items[0].split()), "AC-0007"
```

**Approach:**
- `_unique_paragraph` reads the file the criterion names. It does not use
  `_skill_text()`, which concatenates eight files, so a match cannot come from
  a neighbour.

**Touches:** packs/experience-design/.apm/skills/creative-direction/references/converge.md, packs/experience-design/.apm/skills/creative-direction/references/visualize.md, packs/experience-design/.apm/skills/creative-direction/SKILL.md, packs/experience-design/tests/skills/creative-direction/test_contract.py

**Done when:** the creative-direction contract suite is green.

### T3: The eval harness covers the field

**Depends on:** T2

**Tests:**
- `test_eval_harness_asserts_a_visual_target_disposition` — AC-0013 —
  `stub: true`

**Stub** — add to the same file:

```python
# STUB: AC-0013
def test_eval_harness_asserts_a_visual_target_disposition() -> None:
    evals, _ = _eval_payloads()
    values = ("visual_target: none", "visual_target: unconfirmed", "visual_target: confirmed")
    carrying = [
        case["id"]
        for case in evals["evals"]
        if any(
            value in assertion
            for assertion in case.get("assertions", [])
            for value in values
        )
    ]
    assert carrying, (
        "AC-0013: no eval case asserts a visual_target disposition. A mention in "
        "a prompt, an expected_output or a trigger query does not satisfy this."
    )
```

**Approach:**
- `packs/AGENTS.md` § Security and authoring rules: "A non-cosmetic pack update
  also updates that pack's eval harness." This slice changes the published
  artifact schema, so the obligation is live rather than deferrable.
- The assertion reads each case's own `assertions` list, which the harness
  already exposes, rather than a concatenated corpus.

**Touches:** packs/experience-design/.apm/skills/creative-direction/evals/evals.json, packs/experience-design/tests/skills/creative-direction/test_contract.py

**Done when:** the creative-direction contract suite is green.

### T4: The release surface is consistent

**Depends on:** T1, T2, T3

**Tests:**
- `test_release_surface_is_consistent` — AC-0009, AC-0010 — `stub: true`
- `no stub (goal-based check)` — the start-of-work half of AC-0009, recorded in
  § Version baseline and target above.

**Stub** — new file `tests/conformance/test_visual_target_release_surface.py`:

```python
"""AC-0009 and AC-0010 for the experience-design visual-target release.

Lives in tests/conformance/ because a pack suite may not read the changelog or
the root marketplace manifest. Run mode: `make test` and the dispatch-only
test-corpus workflow — NOT `make build-check`, which is what a PR runs. A green
PR says nothing about these two criteria.
"""

from __future__ import annotations

import json
import re
import tomllib
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
PACK = REPO_ROOT / "packs" / "experience-design"
BASELINE = "4.1.1"


def _tuple(version: str) -> tuple[int, ...]:
    return tuple(int(part) for part in version.split("."))


# STUB: AC-0009, AC-0010
def test_release_surface_is_consistent() -> None:
    pack = tomllib.loads((PACK / "pack.toml").read_text(encoding="utf-8"))
    version = pack["pack"]["version"]
    plugin = json.loads(
        (PACK / ".claude-plugin" / "plugin.json").read_text(encoding="utf-8")
    )
    marketplace = json.loads(
        (REPO_ROOT / ".claude-plugin" / "marketplace.json").read_text(encoding="utf-8")
    )
    entry = next(
        item
        for item in marketplace["plugins"]
        if item.get("name") == "experience-design"
    )

    assert plugin["version"] == version, "AC-0009: plugin.json disagrees"
    assert entry.get("version") == version, "AC-0009: marketplace entry disagrees"
    assert _tuple(version) > _tuple(BASELINE), (
        f"AC-0009: {version} does not exceed the slice-start baseline {BASELINE}"
    )

    changelog = (REPO_ROOT / "docs" / "product" / "changelog.md").read_text(
        encoding="utf-8"
    )
    heading = f"## [experience-design][{version}]"
    assert heading in changelog, f"AC-0010: no free-standing entry for {version}"
    body = changelog.split(heading, 1)[1].split("\n## ", 1)[0]
    assert "### Highlights" in body, "AC-0010: entry carries no Highlights"
    highlights = body.split("### Highlights", 1)[1].split("\n### ", 1)[0]
    assert "visual_target" in highlights, "AC-0010: Highlights do not name the field"
```

**Approach:**
- Bump to the target in § Version baseline and target.
- `marketplace.json` is generated. Commit first, then run plain
  `make build-self`. **Recorded deviation:** `packs/AGENTS.local.md`
  § Marketplace and release pipeline step 2 prescribes `FORCE=1 make
  build-self`; this plan departs from that step, because the root
  `AGENTS.local.md` § Landing changes says never to pass `FORCE=1` from
  automation, and the force flag only overrides the dirty-tree guard — which
  committing first removes the need for. The deviation is from step 2 and
  nothing else in that pipeline.
- The change alters what a producer does, so a `### Highlights` subsection is
  owed.
- Dispatch `test-corpus.yml` before approving the release; the PR gate does not
  run this test.

**Touches:** packs/experience-design/pack.toml, packs/experience-design/.claude-plugin/plugin.json, .claude-plugin/marketplace.json, docs/product/changelog.md, tests/conformance/test_visual_target_release_surface.py

**Done when:** `make lint-ruff lint-mypy` is green, and `python3 -m pytest tests/conformance/test_pack_metadata.py tests/conformance/test_visual_target_release_surface.py -q` is green.

## Rollout

- **Delivery:** one PR. Reversible by reverting it; no migration, because no
  consumer reads the field yet.
- **Infrastructure:** none.
- **External-system integration:** none.
- **Deployment sequencing:** T1, then T2, then T3, then T4.

## Risks

- An adopter who writes the field expecting it to bind composition will find it
  does not until the successor slice ships. The template comment states the
  field's meaning; it cannot state a downstream behaviour that does not exist
  yet. This is the cost of splitting, and it is smaller than shipping the
  consumer change against an unmeasured carrier set.

## Changelog

- 2026-09-29: Drafted. Cut from `visual-target-confirmation`; carries the
  additive half, which is confined to one pack.
- 2026-09-30: Revised after pre-EXECUTE review round 1 (11 sustained findings).
  Recorded the slice-start baseline observation in § Version baseline and
  target. Added AC-0011, AC-0012 and AC-0013, added T3 for the eval-harness
  obligation, replaced the prose stub descriptors with assertions, reworded
  AC-0005 to AC-0007 to name literals inside bounded units, restated AC-0006 as
  a confirmation condition rather than a field read, and corrected the
  dependency section, which described the sibling slice as in flight after it
  had landed.
- 2026-09-30: Revised after pre-EXECUTE review round 2 (15 sustained findings,
  1 refuted). The round-1 repair introduced two of them. Replaced the
  `". "`-bounded sentence helper, which admitted any adjacent period-free
  heading or bullet into the unit, with a paragraph-block helper that reads the
  single file each criterion names and asserts the anchor's uniqueness there.
  Re-pinned AC-0004, which had become a whole-file containment check that
  AC-0005's own edit would have made unfailable, and AC-0013, which was
  substring containment over a concatenated corpus rather than a case
  assertion. Gave AC-0010 and AC-0009's marketplace site a real verification
  artifact and recorded that it runs under `make test`, not the PR gate.
  Brought every stub to the marker convention and recorded the compile and
  intended-red results, which `tdd-stubs.md` fails closed without. Replaced
  AC-0002's four-token denylist with a two-slot shape, because the denylist
  passed `<approver>` and `<signed off by>`. Ruled on the `Never do` carve-out
  so AC-0005's field-literal form is settled rather than left to an
  implementer. Scoped AC-0012 to the fenced excerpt. Corrected Outcome, which
  claimed no behaviour changes while two sections relied on the opposite.
  Corrected the § Landing changes citation — that section is in the root
  `AGENTS.local.md`, not the packs-scoped file — and recorded the deviation
  from release-pipeline step 2 explicitly. Registered the follow-on in
  `workspace.toml`. Made § Version baseline and target the single home for both
  version values. The one refuted finding, on AC-0003's `bind nothing on their
  own` referent, was not acted on.
