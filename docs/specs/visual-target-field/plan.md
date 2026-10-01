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
surfaces — `converge`'s compositional-commitments write, `visualize`'s
binding-boundaries instruction and `SKILL.md`'s output-contract entry — are
**out of scope here**: gating them moves the `approved-visual-target` rung, so
they were retired on 2026-09-30 and belong to the successor. T2 touches one
instruction in `converge.md`, the disposition record, and nothing else.

Nothing is gated on the field in this slice. `converge` records the
disposition and every instruction keeps the condition it has today, so no rung
moves and nothing downstream resolves differently. The release entry's
`### Highlights` subsection is owed for the schema addition adopters must now
author against, not for a behaviour change.

The gating originally drafted here — three criteria over `converge`,
`visualize` and `SKILL.md` — moved to the successor on the owner's 2026-09-30
ruling, because gating `converge`'s compositional-commitments write drops an
approved-but-unconfirmed target off the `approved-visual-target` rung. The rung
resolves from the recorded composition, not from the field, so that change
belongs with the slice that owns rung semantics and migrates the carriers that
explain it. `visualize` in particular
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

Every criterion is an assertion over a shipped file's bytes, with three
exceptions: AC-0008 is the guidebook lint one-liner; AC-0009's start-of-work
baseline is a recorded observation, carried in § *Version baseline and target*;
and T4 carries one recorded manual check over the shipped changelog bullet,
which is a one-time repair condition rather than a criterion — the 2026-10-01
supplementary owner ruling kept it out of the acceptance criteria for that
reason.

AC-0004 and AC-0012 pin literals. AC-0004 asserts its literal **inside a
bounded unit** — a paragraph block, as the spec's Testing Strategy defines one
— read from the single file the criterion names, with the anchor's uniqueness
in that file asserted rather than assumed. The scoping criteria that shared
this machinery left with AC-0005 to AC-0007; the successor restates it for
them. An earlier draft bounded on `". "` in
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
- **Intended red (superseded by the 2026-09-30 re-validation below; kept
  because it records the original proof).** Each block appended to a disposable
  copy of
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
- **Coverage tally:** 10 live criteria after the 2026-09-30 retirement of
  AC-0005 to AC-0007 — 8 covered by stubs, 2
  `no stub (goal-based check)` (AC-0008 the guidebook lint; the manual
  start-of-work baseline half of AC-0009). 0 uncovered.
- **Re-validated after the 2026-09-30 narrowing.** Four blocks compile; four
  pack tests and one roster test red for their own reasons —
  AC-0001/AC-0002/AC-0003/AC-0011 on the template, AC-0012 on the guide
  excerpt, AC-0004 on `converge`'s disposition block, AC-0013 on the eval
  harness, and AC-0009 on `4.1.1 does not exceed the slice-start baseline
  4.1.1`. The three gating assertions left with their criteria and are
  re-validated in the successor's plan.
- **Re-validated after the round-3 repair.** All four blocks compile; all five
  tests red for their own reason. AC-0012's fence selector was checked against
  the real guide: it finds exactly one ` ```markdown ` fence carrying
  `type: creative-direction`, that fence is the template excerpt ending at
  `**May adapt responsively:**`, and it lacks the field today — so the test now
  reds because the material is absent rather than because it was reading the
  design-principles block. `python tools/lint-conformance-portability.py
  --root .` exits zero with the release test in `tests/roster/`.
- **Re-opened by the 2026-10-01 amendment. This bullet is the current record;
  every bullet above it describes an earlier state.** The amendment adds T5 and
  changes which module asserts AC-0012, so the dispositions and the tally are
  restated here over the post-amendment assertion set.
  - **Dispositions, 11 obligations over 10 live criteria.** `stub: true` for
    AC-0001/AC-0002/AC-0003 and AC-0011 (T1, with AC-0011's assertion replaced
    by T5), AC-0004 (T2), AC-0013 (T3), AC-0009 and AC-0010 (T4), and AC-0012
    (T5's new roster module). `no stub (goal-based check)` for AC-0008, the
    guidebook lint one-liner, and for AC-0009's start-of-work baseline
    observation recorded in § *Version baseline and target*. 0 uncovered. This
    supersedes the "8 covered by stubs, 2 goal-based" tally above, which counted
    AC-0012 under its old home and predates T5.
  - **Compile pass, by block, because they were validated differently.**
    Measured 2026-10-01 against the blocks as they now stand, after T4's block
    lost its unused `import re`: all six stored blocks pass. T4's roster module
    and T5's roster module each compile standalone under `python -m py_compile`
    from disposable scratch outside the repository test tree, exit 0; T1's,
    T2's and T3's blocks compile the same way. This record covers every stored
    block, superseding the round-3 four-block record above, which predates T4's
    edit. The AC-0011 block is a
    function-body fragment replacing one assertion, so it does not compile
    standalone — `py_compile` on it exits non-zero with
    `IndentationError: unexpected indent`. Its syntax was validated by splicing
    it into a disposable copy of its host module
    (`packs/experience-design/tests/skills/creative-direction/test_contract.py`),
    which then compiled clean. Recorded this way because an earlier revision
    claimed a bare `py_compile` pass for both blocks, which was not what was
    run.
  - **Intended red: unobtainable for both T5 blocks, by construction.** T1 has
    already landed the template phrase and the guide excerpt material, so each
    assertion is green on first run.
    **Owner-granted waiver, not a self-declared deviation.** `tdd-stubs.md`
    § *Validate* fails closed at plan approval without a recorded intended red,
    and admits no third disposition beside `stub: true` and
    `no stub (implementation-discovered)`. Neither fits: the assertions are
    authored and compilable, so they are not implementation-discovered, and the
    red cannot be obtained because the property they assert is already present
    in the tree T1 committed at `f69606cfb`.

    An earlier revision asserted a departure "under the 2026-10-01 amendment
    authority" — a grant that authority did not contain. Review sustained that
    as a blocker and adjudication returned `ADJUDICATION-INDETERMINATE` on the
    question behind it, because neither `tdd-stubs.md` nor `mutation-proof.md`
    decides whether a PLAN-time mutation red satisfies the non-vacuity
    requirement. The owner ruled on that question rather than the plan
    reinterpreting it: see § *Supplementary owner ruling — 2026-10-01, a scoped
    intended-red waiver for T5* in
    [`notes/amendment-2026-10-01.md`](notes/amendment-2026-10-01.md), which
    waives the intended-red requirement for these two blocks only and records
    the measured substitute evidence.

    Both prescribed mutations were applied in throwaway worktrees and observed
    red; the AC-0011 mutation additionally shows the superseded co-occurrence
    assertion staying green where the replacement fails. The waiver is from the
    red requirement and nothing else in § *Validate*: the compile pass above is
    recorded as that section requires. The owner later extended the waiver to
    § *Lifecycle*'s EXECUTE-time red for the same two blocks, on the same
    reason: see § *Supplementary owner ruling — 2026-10-01, the waiver extends
    to the Lifecycle red* in the same note. It therefore covers both phases and
    nothing further. The EXECUTE-time ledger entry T5's `Done when` gates on is
    still owed; the ruling permits the substitution, it does not perform it.
  - **Isolation:** local, filesystem-confined to the repository and disposable
    scratch, no network use. No isolation downgrade was needed.

## Durable-output map

| Durable output | Task | Evidence |
| --- | --- | --- |
| Interface compatibility (the template) | T1 | Contract-suite assertions |
| Current product truth (the guide excerpt) | T1 for the excerpt edit; T5 for AC-0012's assertion | `lint-guidebook-steps.py` exit zero (T1) plus AC-0012, asserted from T5's `tests/roster/` module after the 2026-10-01 amendment moved it out of the pack contract suite |
| Behavioural coverage (the eval harness) | T3 | Contract-suite assertion over the harness JSON |
| Release history | T4 | `tests/roster/test_visual_target_release_surface.py`, which reads all three version sites and the changelog; plus the recorded slice-start baseline. `tests/conformance/test_pack_metadata.py` is not evidence for AC-0009 or AC-0010: it compares `pack.toml` to `plugin.json` only, never a marketplace version and never the changelog |

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
where it was recorded, per ADR-0132. It deliberately does not offer a "who",
because the spec's `Never do` rail forbids a person's name, handle or contact
detail there and a placeholder that asks for one invites the breach.

### Data & schema

Owned by: T1

The closed set is `none | unconfirmed | confirmed`, written as a quoted
placeholder exactly as `status` is.

### Behavior & rules

Owned by: T1, T2

`converge` is the only surface this slice touches beyond the template, and it
touches one instruction: the disposition record. `visualize.md` and `SKILL.md`
are untouched. The three producing surfaces are gated together in the
successor, which is the right granularity — gating one without the others
would have a producer forming a binding claim the writer then records.

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


def _template_fence(text: str) -> str:
    """The one markdown fence reproducing the creative-direction template.

    Selected by a property, not by ordinal: this guide carries three such
    fences and the first is a design-principles block.
    """
    bodies = [part.split(TICKS, 1)[0] for part in text.split(FENCE)[1:]]
    matching = [b for b in bodies if "type: creative-direction" in b]
    assert len(matching) == 1, "AC-0012: exactly one creative-direction fence"
    return matching[0]


# STUB: AC-0001, AC-0002, AC-0003, AC-0011  (spec: visual-target-field)
def test_template_carries_the_visual_target_disposition() -> None:
    """visual-target-field AC-0001, AC-0002, AC-0003, AC-0011.

    This module also carries creative-direction-modes criteria under
    overlapping numbers, so every AC reference here names its spec.
    """
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
    assert " ".join(record_lines[0].split()) == (
        "**Confirmation record:** <YYYY-MM-DD> — "
        "<where the confirmation was recorded>"
    ), "AC-0002: the placeholder is pinned exactly, leaving no slot for a person"

    comment = section.split("-->", 1)[0]
    assert "visual_target" in comment, "AC-0003"
    for label in ("**Target:**", "**Binding:**", "**Confirmation record:**"):
        assert label in comment, "AC-0003"
    assert "bind nothing on their own" in comment, "AC-0003"
    assert "unconfirmed" in comment and "absent" in comment.lower(), "AC-0011"


# STUB: AC-0012  (spec: visual-target-field)
def test_guide_excerpt_carries_the_new_template_material() -> None:
    """visual-target-field AC-0012."""
    guide = _read(
        PACK_ROOT.parents[1]
        / "guides"
        / "experience-design"
        / "how-to"
        / "establish-design-intent.md"
    )
    excerpt = _template_fence(guide)
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

### T2: `converge` records the disposition

**Depends on:** T1

**Tests:**
- `test_converge_records_the_disposition` — AC-0004 — `stub: true`

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


# STUB: AC-0004  (spec: visual-target-field)
def test_converge_records_the_disposition() -> None:
    """visual-target-field AC-0004."""
    disposition = _unique_paragraph(
        REFERENCE_ROOT / "converge.md", "Record the approved visual target disposition"
    )
    for value in ("none", "unconfirmed", "confirmed"):
        assert f"visual_target: {value}" in disposition, f"AC-0004: {value}"
```

**Approach:**
- Reword only the disposition instruction, which today records the no-target
  case as the bare word `none`, so it names all three field values. Leave every
  other instruction in `converge.md`, `visualize.md` and `SKILL.md` exactly as
  it stands — gating them is the successor's contract, and doing it here is
  what the owner's ruling removed.
- `_unique_paragraph` reads the file the criterion names. It does not use
  `_skill_text()`, which concatenates eight files, so a match cannot come from
  a neighbour.

**Touches:** packs/experience-design/.apm/skills/creative-direction/references/converge.md, packs/experience-design/tests/skills/creative-direction/test_contract.py

**Done when:** the creative-direction contract suite is green.

### T3: The eval harness covers the field

**Depends on:** T2

**Tests:**
- `test_eval_harness_asserts_a_visual_target_disposition` — AC-0013 —
  `stub: true`

**Stub** — add to the same file:

```python
# STUB: AC-0013  (spec: visual-target-field)
def test_eval_harness_asserts_a_visual_target_disposition() -> None:
    """visual-target-field AC-0013."""
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

**Stub** — new file `tests/roster/test_visual_target_release_surface.py`:

```python
"""AC-0009 and AC-0010 for the experience-design visual-target release.

Lives in tests/roster/ and not tests/conformance/: a conformance test may name
no shipped pack and may not reach docs/, and this one must do both.
tools/lint-conformance-portability.py enforces that on every pull request.
tests/AGENTS.md names tests/roster/ as the repository-level home.

Run mode: build-check.yml triggers on pull_request and its carve-out step runs
`python -m pytest tests/ -q`, so the PR gate runs this. No corpus dispatch is
needed.
"""

from __future__ import annotations

import json
import tomllib
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]  # tests/roster/ -> repo root
PACK = REPO_ROOT / "packs" / "experience-design"
# Both literals are derived from plan.md § Version baseline and target, which is
# their single home. BASELINE is what AC-0009 measures the bump against.
BASELINE = "4.1.1"
# RELEASE pins the one entry this slice authored. The changelog half must NOT
# read the live pack version: changelog entries describe one release each, so a
# later unrelated experience-design bump would red this permanently installed
# test for an author who never touched this field. The three-site version
# agreement below keeps reading the live version, because that claim must stay
# live. Same split as tests/roster/test_wave4_durable_outputs_and_release.py.
RELEASE = "4.1.2"


def _tuple(version: str) -> tuple[int, ...]:
    return tuple(int(part) for part in version.split("."))


# STUB: AC-0009, AC-0010  (spec: visual-target-field)
def test_release_surface_is_consistent() -> None:
    """visual-target-field AC-0009 and AC-0010."""
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
    heading = f"## [experience-design][{RELEASE}]"
    starts = [
        line for line in changelog.splitlines() if line.startswith(heading)
    ]
    assert len(starts) == 1, (
        f"AC-0010: expected exactly one free-standing '## ' entry for {RELEASE}. "
        "A substring test would also accept a '### ' entry nested under "
        "[Unreleased], which never publishes."
    )
    body = changelog.split("\n" + heading, 1)[1].split("\n## ", 1)[0]
    assert "### Highlights" in body, "AC-0010: entry carries no Highlights"
    highlights = body.split("### Highlights", 1)[1].split("\n### ", 1)[0]
    bullets = [
        line for line in highlights.splitlines() if line.strip().startswith("- ")
    ]
    assert any("visual_target" in bullet for bullet in bullets), (
        "AC-0010: no Highlights bullet names visual_target. The /now/ projection "
        "extracts only bullets, so a paragraph is dropped silently."
    )
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
- **The Highlights bullet is adopter copy, and `changelog.md`'s own header
  governs it: "Rewrite for users, not contributors" and "Outcome, not
  activity."** Lead with what an adopter can now do, not with the artifact
  mechanism, and do not close in contributor register. Two accuracy rails bind
  it: the bullet must not state or imply that recording the disposition is
  conditional on anything — `converge` records it unconditionally, and the
  no-target case is exactly the one a conditional reading would drop — and it
  must keep saying plainly that nothing reads the field and nothing is gated on
  it. It must still name `visual_target` in a `-` bullet under
  `### Highlights`, because the `/now/` projection extracts only bullets.
- Placing a file in `tests/roster/` obliges three further edits, per
  `tests/AGENTS.md` § *Roster steps are named and placed by hand*: a step in
  `.github/workflows/build-check.yml` naming the file, placed **above** the bulk
  `pytest tests/ -q` step so the failure is attributed to the named target
  rather than the broad one; a matching `STEP_DISPOSITION` entry of
  `LOCAL("test-after-build-check")` in `tools/lint-ci-parity.py`; and a
  `.workspace-prune-protected.toml` entry only if the test names a
  `docs/specs/<slug>` path literal — this one does not, so that third edit is
  not owed.
  **`lint-ci-parity.py` feeds two axes and refuses a step missing from either,**
  so the step name goes in both `_LOCAL_STEP_DISPOSITION` and the
  `_GATE_MAIN_CHECKS` tuple. `tests/AGENTS.md` documents only the first; a step
  named in one axis alone is still a violation, which `_step_disposition` is
  written to preserve.
- Run `ruff check .` afterwards: the repository lint targets do not cover
  orphaned imports left by a moved test.

#### Repair state for this task after the 2026-10-01 amendment

Two artifacts T4 already committed are **currently non-conforming** and T4 is
not met until both are repaired. Neither is caught by the checks T4's original
`Done when` names, which is why they are called out here rather than left to a
re-run:

1. `tests/roster/test_visual_target_release_surface.py` builds its changelog
   heading from the live `version` instead of the `RELEASE` literal this plan
   now pins. The committed file predates the amended stub above.
2. The `## [experience-design][4.1.2]` Highlights bullet in
   `docs/product/changelog.md` states that `converge` records the disposition
   "when writing compositional commitments". `converge` records it
   unconditionally, so the published sentence describes a condition the shipped
   instruction does not have and reads as the gating this slice forbids. It is
   also schema-led where `changelog.md`'s header requires outcome-led user
   register.

**Touches:** packs/experience-design/pack.toml, packs/experience-design/.claude-plugin/plugin.json, .claude-plugin/marketplace.json, docs/product/changelog.md, tests/roster/test_visual_target_release_surface.py, .github/workflows/build-check.yml, tools/lint-ci-parity.py

**Done when:** all five hold. The first two were added by the 2026-10-01
amendment because the other three are green against the unrepaired tree, so
without them an implementer could report T4 met with both non-conforming
artifacts standing.

1. **Byte identity against the approved stub.** The materialized
   `tests/roster/test_visual_target_release_surface.py` matches the stub block
   in this task section, per `tdd-stubs.md` § *Lifecycle*. This is what fails
   while the committed file still derives its changelog heading from the live
   `version` rather than from `RELEASE`.
2. **Both defects named in the repair-state list above are repaired.** The
   `## [experience-design][4.1.2]` entry's Highlights bullet (a) does not
   contain the string `when writing compositional commitments` and states no
   other condition on recording the disposition, and (b) leads with what an
   adopter can now do rather than with the artifact mechanism, and does not
   close in contributor register — the two things `changelog.md`'s header
   requires of a highlight. It still names `visual_target` in a `-` bullet and
   still says plainly that nothing reads the field and nothing is gated on it.
   Verified by reading the bullet against that header and recording the
   observation in the verification ledger; no lint reads prose register, so
   this is a recorded manual check rather than a gate.
   This is a one-time repair condition on an already-shipped artifact, not a
   standing criterion: the 2026-10-01 supplementary owner ruling removed the
   equivalent clauses from AC-0010 precisely so the contract does not carry an
   obligation a completion gate cannot decide. Both halves stay here because
   both were sustained findings, and a repair condition that omits one would
   let T4 pass with that defect standing.
3. `make lint-ruff lint-mypy` and `ruff check .` are green.
4. `python3 -m pytest tests/conformance/test_pack_metadata.py tests/roster/test_visual_target_release_surface.py -q` is green.
5. `python3 tools/lint-conformance-portability.py --root .` and `python3 tools/lint-ci-parity.py` both exit zero, which is what proves the file sits in a tree whose rules admit it.

### T5: AC-0012 is asserted from a tree that may read the guide, and AC-0011 is decided

**Depends on:** T4

Added by the 2026-10-01 amendment. T1's plan section is pinned, so these two
corrections to its assertions arrive as a new task rather than as edits to it.
The edge is on T4, not T1: both tasks write
`.github/workflows/build-check.yml` and `tools/lint-ci-parity.py`, and
declaring T1 would let the scheduler place T4 and T5 in one wave, since T1 is
already completed. T1's content dependency is satisfied by its completion.

**Tests:**
- `test_visual_target_guide_excerpt` — AC-0012 — `stub: true`. The assertion
  moves out of the pack contract suite into a new `tests/roster/` module. It is
  not a pure relocation: the new module authors its own root anchor and
  file-read mechanism, because `_read` and `PACK_ROOT` live in the pack suite
  and do not exist under `tests/roster/`.
- `test_template_carries_the_visual_target_disposition` — AC-0011 —
  `stub: true` for the replaced assertion only. The surrounding test keeps its
  AC-0001, AC-0002 and AC-0003 assertions unchanged; only the final AC-0011
  line is replaced, by the block below.

**Stub** — new file `tests/roster/test_visual_target_guide_excerpt.py`:

```python
"""AC-0012 for the experience-design visual-target field.

Lives in tests/roster/ and not in the pack contract suite: AC-0012 is a claim
about guides/experience-design/how-to/establish-design-intent.md, and
tools/lint-pack-test-boundary.py forbids a pack test from reading above its own
pack. The spec's Testing Strategy records why the original home could not
satisfy both. tests/AGENTS.md names tests/roster/ as the repository-level home.

Run mode: build-check.yml triggers on pull_request and its carve-out step runs
`python -m pytest tests/ -q`, so the PR gate runs this.
"""

from __future__ import annotations

from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]  # tests/roster/ -> repo root
GUIDE = (
    REPO_ROOT
    / "guides"
    / "experience-design"
    / "how-to"
    / "establish-design-intent.md"
)
TICKS = "`" * 3  # written this way so the literal survives a fenced code block
FENCE = TICKS + "markdown"


def _template_fence(text: str) -> str:
    """The one markdown fence reproducing the creative-direction template.

    Selected by a property, not by ordinal: this guide carries three such
    fences and the first is a design-principles block.
    """
    bodies = [part.split(TICKS, 1)[0] for part in text.split(FENCE)[1:]]
    matching = [b for b in bodies if "type: creative-direction" in b]
    assert len(matching) == 1, "AC-0012: exactly one creative-direction fence"
    return matching[0]


KEY_LINE = 'visual_target: "<none | unconfirmed | confirmed>"'
RECORD_LINE = (
    "**Confirmation record:** <YYYY-MM-DD> — "
    "<where the confirmation was recorded>"
)


# STUB: AC-0012  (spec: visual-target-field)
def test_visual_target_guide_excerpt() -> None:
    """visual-target-field AC-0012."""
    excerpt = _template_fence(GUIDE.read_text(encoding="utf-8"))
    lines = [line.rstrip() for line in excerpt.split("\n")]
    for pinned in (KEY_LINE, RECORD_LINE):
        assert lines.count(pinned) == 1, (
            f"AC-0012: {pinned!r} must appear exactly once in the template "
            "fence. Containment over the bare words does not decide this: the "
            "fence carries `visual_target` four times and "
            "`**Confirmation record:**` twice, because the section comment "
            "discusses both, so a word check passes on an excerpt that "
            "reproduces the comment and omits the key and the record line."
        )
```

**Stub** — replaces the final AC-0011 assertion inside
`test_template_carries_the_visual_target_disposition` in
`packs/experience-design/tests/skills/creative-direction/test_contract.py`:

```python
    normalized_comment = " ".join(comment.split())
    assert (
        "An absent `visual_target` reads as `unconfirmed`" in normalized_comment
    ), (
        "AC-0011: the comment must state the absent-field reading as one "
        "contiguous phrase. Testing for `unconfirmed` beside the word `absent` "
        "reduces the criterion to whether `absent` appears at all, so a comment "
        "stating that an absent target means `none` would pass while "
        "contradicting the fail-closed default."
    )
```

**Approach:**
- Move the AC-0012 assertion out of
  `packs/experience-design/tests/skills/creative-direction/test_contract.py`
  and into the new roster module above, deleting `_template_fence`, `TICKS` and
  `FENCE` from the pack suite along with it. A pack test may not read above its
  own pack, and AC-0012 is a claim about a file in `guides/`; the spec's Testing
  Strategy records why the original home could never have satisfied both.
- Placing a file in `tests/roster/` obliges the two edits `tests/AGENTS.md`
  names: a step in `.github/workflows/build-check.yml` naming the file, placed
  **above** the bulk `pytest tests/ -q` step, and a matching `STEP_DISPOSITION`
  entry of `LOCAL("test-after-build-check")` in `tools/lint-ci-parity.py`.
  That lint feeds two axes and refuses a step missing from either, so the step
  name also joins the `_GATE_MAIN_CHECKS` tuple. The third obligation, a
  `.workspace-prune-protected.toml` entry, is owed only when the test names a
  `docs/specs/<slug>` literal; this one does not.
- Replace AC-0011's assertion in the contract suite with the block above.
  AC-0001, AC-0002, AC-0003 and AC-0011 stay in the contract suite, which reads
  only the template.
- Run `ruff check .` afterwards: moving a test orphans the imports only it used,
  and the repository lint targets do not cover that.

**Verification: mutation proof, not red-then-green.** Both assertions are green
on first run against the current tree — the template comment already carries the
pinned phrase, and the guide's `type: creative-direction` fence already carries
both markers, because T1 put them there. An assertion accepted on a first
green carries no evidence it can fail at all, so non-vacuity is shown by
[`mutation-proof.md`](../../../.claude/skills/work-loop/references/mutation-proof.md),
the repository's declared instrument for a test whose property is already
present.

**What is granted, and what is not.** The owner's waiver covers
`tdd-stubs.md` § *Validate*'s intended-red requirement at **plan approval**, for
these two blocks, and nothing further. § *Lifecycle* separately requires EXECUTE
to materialize the approved block, verify byte identity, **and prove the intended
red**, and `work-loop/SKILL.md` repeats that for the full-mode engine after
`CODE-IMPLEMENTATION`. That EXECUTE-time red is unobtainable for the same reason
the plan-approval one is, and **whether the mutation proof may stand in for it is
not decided by the current grant.** An earlier revision of this section claimed
the substitution without phase qualification, which claimed more than the waiver
gives; that overreach is removed here rather than argued.

**Resolved, 2026-10-01.** The owner extended the waiver to cover
§ *Lifecycle*'s EXECUTE-time intended red for these same two blocks, on the same
reason: the red is unobtainable at either phase because T1 already committed the
material both assertions check, and reaching `CODE-IMPLEMENTATION` does not
change that. See § *Supplementary owner ruling — 2026-10-01, the waiver extends
to the Lifecycle red* in
[`notes/amendment-2026-10-01.md`](notes/amendment-2026-10-01.md).

The substitution is now granted at both phases, and nothing further is waived.
The ledger entries stay owed: the ruling permits the substitution rather than
performing it, so T5 is not met until both mutation proofs are recorded in the
verification ledger with the full field set `mutation-proof.md` § *Proof record*
requires. Record for each of the two assertions, in the verification
ledger, the complete field set `mutation-proof.md` § *Proof record* requires —
cited rather than restated here so the list cannot drift short of it, and noting
that `Catching test` is load-bearing for AC-0011, whose assertion is one line
inside a four-criterion test function. Two mutations are owed:

- **AC-0012** — in the guide's fenced excerpt only, delete the single
  `visual_target: "<none | unconfirmed | confirmed>"` line. Expected red:
  `test_visual_target_guide_excerpt`, on the `KEY_LINE` count assertion.
  This falsifies the pinned sub-property rather than deleting the construct:
  the fence still carries `visual_target` three times and the record line
  intact, so the mutation proves the assertion decides the key's presence and
  not merely that the word appears somewhere. A whole-fence deletion would
  prove nothing about that sub-property. **Confined to the guide.** Restore by
  re-deriving the excerpt from the template, then confirm
  `tools/lint-guidebook-steps.py guides/experience-design` is green again.
- **AC-0011** — in the template only, reword the section comment's
  absent-field sentence so it still contains both `absent` and `unconfirmed`
  but no longer as the pinned contiguous run. Expected red:
  `test_template_carries_the_visual_target_disposition`, on the replaced
  AC-0011 assertion. Record that the superseded co-occurrence form would have
  stayed green under this same mutation; that contrast is the whole reason for
  the replacement, so both outcomes belong in the ledger.
  **Confined to the template. Do not re-derive the guide excerpt while the
  mutation stands** — the comment is reproduced verbatim in the guide and
  coupled by the guidebook lint, so re-deriving under mutation would write the
  mutation into a second shipped byte-pinned file. The lint is expected to red
  during the mutation, which is the coupling working. Restore by editing the
  template back, which returns the lint to green and leaves restoration a
  one-file operation; `mutation-proof.md` permits no `git checkout`, `reset` or
  `stash` here.

**Touches:** packs/experience-design/tests/skills/creative-direction/test_contract.py, tests/roster/test_visual_target_guide_excerpt.py, .github/workflows/build-check.yml, tools/lint-ci-parity.py, docs/specs/visual-target-field/notes/verification-ledger.md

**Done when:** `python3 tools/test-lint-pack-test-boundary.py` exits zero — the gate that caught this, and the one that proves the boundary violation is gone; the materialized roster module matches the stub block above byte for byte; `python3 -m pytest packs/experience-design/tests/skills/creative-direction tests/roster/test_visual_target_guide_excerpt.py -q` is green; `make lint-ruff lint-mypy` and `ruff check .` are green; `python3 tools/lint-ci-parity.py` and `python3 tools/lint-conformance-portability.py --root .` both exit zero; and the verification ledger records both mutation proofs above with observed reds and restoration.

## Rollout

- **Delivery:** one PR. Reversible by reverting it. No migration, and this
  time the reason holds: nothing is gated on the field, so no rung resolves
  differently for any artifact, new or existing.
- **Infrastructure:** none.
- **External-system integration:** none.
- **Deployment sequencing:** T1, then T2, then T3, then T4, then T5. T1 to T3
  landed before the 2026-10-01 amendment and are preserved as met; T5 corrects
  two of T1's assertions without editing its pinned section. This slice must
  land before `visual-target-rung-precondition`, which reads the field it
  writes.

## Risks

- **An intermediate state exists between this slice and its successor.**
  `converge` records a disposition while still writing a binding claim for an
  unconfirmed target, so an artifact can carry `visual_target: unconfirmed`
  beside compositional commitments. Round 1 raised this as the reason to gate
  here; the owner's ruling accepted it instead, because the alternative moved a
  rung inside a slice that claimed to move nothing. The successor is authored
  and registered, and it closes the state.
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
- 2026-09-30: Revised after pre-EXECUTE review round 3 (10 sustained findings,
  1 refuted). Two were corrections of round-2 work. The release test moved from
  `tests/conformance/` to `tests/roster/`: a conformance test may name no
  shipped pack and may not reach `docs/`, and this one must do both, so the
  stated reason for the old location was inverted and the file would have red
  the PR gate on first push. T4 now carries the two roster obligations it owes
  and records why the third does not apply. Corrected the run-mode claim, which
  reasoned from the Make target to the workflow: `build-check.yml` triggers on
  `pull_request` and runs `pytest tests/ -q` directly, so the PR gate does
  cover AC-0009 and AC-0010 and no corpus dispatch is needed. Replaced
  AC-0012's fence-ordinal selection, which read the guide's design-principles
  block and could never have gone green, with selection by the
  `type: creative-direction` property. Replaced AC-0002's regex, which passed
  `<who recorded it>` on `record`, with exact equality on the placeholder text,
  and stopped the criterion claiming to enforce the runtime half of the rail.
  Tightened AC-0005's anchor and split the paragraph in T2 so the unit is the
  gated write. Anchored AC-0010 at line start and required a Highlights bullet,
  since the projection drops paragraphs. Added `visual_target: none` to
  AC-0004. Qualified every AC reference in the shared test module. Recorded the
  rung consequence in `Outcome`, `Rollout` and `Risks`, and raised the owner
  decision it implies. The refuted finding, on excerpt ordering, was not acted
  on: AC-0012 already reds in that case.
- 2026-09-30: Narrowed on the owner's ruling, the largest revision this
  contract has had. AC-0005, AC-0006 and AC-0007 were retired through the
  spec's `Retired identifiers` section and inherited by
  `visual-target-rung-precondition`, which renumbers them under its own
  sequence — deliberately not cited here, because this spec's own AC-0012 and
  AC-0013 mean different things and a bare number would resolve to the wrong
  contract. Gating `converge`'s
  compositional-commitments write moves the `approved-visual-target` rung —
  that rung resolves from the recorded composition, not from the field — so it
  belongs in the slice that migrates the carriers explaining it. T2 was
  rescoped from four gating assertions to one disposition assertion, `Approach`
  and `Outcome` were restated as additive, and `Risks` now carries the
  intermediate state the narrowing accepts. Round 4 found that the first
  attempt at this edit left `Outcome` and `Approach` asserting the retired
  behaviour, including a start gate on a question the ruling had already
  answered; both were rewritten and read back.
- 2026-10-01: **Controlled contract amendment** under owner authority, recorded
  at [`notes/amendment-2026-10-01.md`](notes/amendment-2026-10-01.md);
  amendment id `6a558bc592327e241ae36110641e6e6cb17cae181c259deadc90e18672da7896`.
  T1 to T4 had been implemented and gated when post-gates review round 1
  sustained 6 of 20 raw findings across two reviewers. Two were blockers in the
  accepted contract rather than in the work: the spec's Testing Strategy
  required AC-0012 as a contract-suite assertion, which cannot be satisfied
  because deciding AC-0012 means reading a guide outside the pack and
  `tools/lint-pack-test-boundary.py` forbids that — measured red, and the docs
  workflow runs it on every pull request touching these paths; and T4's stub
  bound the `visual_target` changelog claim to whatever version `pack.toml`
  carries, so the next unrelated bump would red a permanently installed test.
  Four pre-EXECUTE rounds had missed both, and the first is the same class of
  boundary error round 3 caught for T4's own placement. The Testing Strategy now
  places AC-0012's assertion in `tests/roster/` and records why the original home
  was unsatisfiable; AC-0011 now pins its phrase as one contiguous run, because
  the co-occurrence form could not fail; T4's stub pins only the changelog half
  to the literal release and keeps the three-site agreement reading the live
  version; and T4's approach now carries the register and accuracy rails
  `changelog.md`'s header imposes on a Highlights bullet. T1 to T3 are preserved
  as completed with their commits bound as evidence, so the two corrections to
  T1's assertions arrive as new task T5 rather than as edits to its pinned
  section. No acceptance criterion was removed, weakened, or renumbered, and the
  outcome is not narrowed. One advisory finding, on the guide caption's
  unconditional placeholder sentence, was deferred rather than acted on.
- 2026-10-01: Revised after the post-amendment pre-EXECUTE review (9 sustained
  of 11 raw, 2 refuted). Every sustained finding was a defect in the amendment
  itself rather than in the work it governs, which is the third time in this
  delivery that repair work was the defect source. Four were blockers. T4's
  `Done when` was green against the unrepaired tree, so a re-dispatched
  implementer could have reported it met with both non-conforming artifacts
  standing; it now leads with a byte-identity check against the approved stub
  and a recorded check that the Highlights bullet carries no conditional
  framing, and T4 names those two artifacts as currently non-conforming. T5
  claimed proof by red-then-green, which is unobtainable because T1 already
  landed the material both assertions look for; it now carries a mutation proof
  with two named mutations, their expected reds, and restoration, per
  `mutation-proof.md`. T5 had no admitted stub disposition and no code for the
  new roster module; both blocks are now present, compiled, and recorded. T5's
  relocation claim was untrue — `_read` and `PACK_ROOT` do not exist under
  `tests/roster/` — so the module authors its own root anchor and read
  mechanism and the "nothing newly authored" claim is gone. Three concerns:
  AC-0009 named a conformance test that cannot own it, AC-0010 measured the
  live version where its verification pins the released one, and two Testing
  Strategy bullets declared goal-based mode for criteria the plan stubs — the
  mode declaration is normative, since only a TDD-mode criterion is stubbed.
  Two nits: T5's dependency edge moved to T4 so the scheduler cannot place two
  tasks that write the same workflow and parity files in one wave, and T4 now
  names both `lint-ci-parity.py` axes. The stub validation record was re-opened
  with a current-state bullet and a disposition tally over 11 obligations; the
  stale "this bullet is the current record" claim two bullets up was removed.
  The two refusals were not acted on: the test's version literals are already
  recorded as derived from the single home, and pinning the criterion rather
  than deriving the version in the test is what the amendment authority
  requires; and AC-0011's prose wording cannot mislead, because the criterion
  pins the exact phrase in its own fenced block.
- 2026-10-01: Revised after the third pre-EXECUTE pass (10 sustained, 0
  refuted). Every finding was a defect in the previous repair, and the shape of
  the previous repair is the finding behind the finding: it answered sustained
  findings by adding obligations, and the additions then needed verification of
  their own. Two blockers were measured, not argued. T4's approved stub carried
  `import re` unused, so `Done when`'s byte-identity condition and its
  `ruff check .` condition could not both hold — the same unused import the T4
  implementer had already removed from the real file and reported, pinned back
  in by a stub nobody re-read. AC-0012's prescribed mutation left its assertion
  green, because the fence carries `visual_target` four times and
  `**Confirmation record:**` twice; the answer was to tighten the criterion to
  its two pinned lines, each occurring exactly once, which both strengthens
  AC-0012 and makes it falsifiable by one line. The third blocker was resolved
  by narrowing rather than specifying: under a supplementary owner ruling
  recorded in [`notes/amendment-2026-10-01.md`](notes/amendment-2026-10-01.md),
  the register and conditional-framing clauses the previous repair added to
  AC-0010 are removed, and the shipped bullet's two defects stay as a one-time
  repair condition in T4's `Done when`, which adjudication distinguished from a
  standing criterion. T5's `stub: true` with an unobtainable red is now a
  recorded deviation from `tdd-stubs.md` § *Validate* under that authority
  rather than an assertion that the obligation was discharged. The AC-0011
  mutation is confined to the template and explicitly forbids re-deriving the
  guide while the mutation stands, so restoration touches one file. The
  mutation field list now cites `mutation-proof.md` § *Proof record* instead of
  restating it short of `Catching test`. Three structural corrections: the
  orphaned `ruff check .` bullet returned to T4's Approach, the durable-output
  map now attributes AC-0012's assertion to T5, and the construction-tests
  preamble states its three real exceptions.
- 2026-10-01: Revised after the fourth pre-EXECUTE pass. Its adjudication
  returned `ADJUDICATION-INDETERMINATE` and classified `invalid`
  (`indeterminate-present`), which is a fail-closed stop, so no revision was
  made from that round until the owner decided the question behind it. The
  blocker was that this plan asserted a `tdd-stubs.md` § *Validate* departure
  "under the 2026-10-01 amendment authority" — a grant that authority did not
  contain. The question behind it, which neither `tdd-stubs.md` nor
  `mutation-proof.md` decides, was whether a mutation red obtained at PLAN time
  satisfies the non-vacuity requirement. The owner ruled on 2026-10-01 to record
  an explicit scoped waiver rather than reinterpret "intended red" to admit
  evidence already in hand, which would have set a precedent for every future
  stub whose asserted property is already present. That waiver, its reason, and
  its scope limit are recorded in
  [`notes/amendment-2026-10-01.md`](notes/amendment-2026-10-01.md); this plan now
  cites it instead of claiming a grant. Both prescribed mutations were measured
  in throwaway worktrees and observed red, and the AC-0011 mutation additionally
  shows the superseded co-occurrence assertion staying green where the
  replacement fails — the evidence that the replacement was worth making. The
  compile record is now stated per block: the roster module compiles standalone,
  while the AC-0011 fragment does not and was validated by splicing into a
  disposable copy of its host module. An earlier revision claimed a bare
  `py_compile` pass for both, which was not what was run. The amendment note's
  § *What this amendment does not change* now marks its two superseded claims,
  one of which — "AC-0012 keeps its wording" — had become false. One finding was
  refuted: holding the Highlights rails in both Approach and `Done when` is a
  structure preference, not a defect, since the two are differently decidable.
- 2026-10-01: Revised after the fifth pre-EXECUTE pass — the first with no
  blockers (1 concern, 1 nit, both sustained, none refuted). That pass also
  reproduced independently every claim the intended-red waiver rests on: both
  mutation reds, the superseded-assertion contrast, the per-block compile
  results, and the guidebook lint returning to zero after restoration by
  editing. The concern was an overreach of this plan's own making: § *Verification*
  claimed the mutation proof substitutes for the intended red without phase
  qualification, while the waiver grants that only at plan approval and
  `tdd-stubs.md` § *Lifecycle* imposes an EXECUTE-time red separately. The plan
  also contradicted itself, repeating the plan-approval-only limit in one place
  and exceeding it in another. Adjudication ruled that removing an overreach
  needs no grant, so the claim is narrowed here rather than argued, and the
  residue is recorded at the T5 seam as a named open decision owed before T5 is
  marked met: whether § *Lifecycle*'s EXECUTE-time red is waived on the same
  reason. Adjudication also established that the in-tree mutation proofs supply
  that non-vacuity evidence in substance, so what remains is an authority
  statement, not more evidence work. The nit is closed by extending the compile
  record to every stored block, measured as they now stand after T4's block lost
  its unused `import re`; the round-3 four-block record it supersedes predated
  that edit.
- 2026-10-01: The open § *Lifecycle* decision recorded above is resolved. The
  owner extended the intended-red waiver to cover § *Lifecycle*'s EXECUTE-time
  red for the same two T5 blocks, on the same reason — the red is unobtainable
  at either phase because T1 already committed the material both assertions
  check, and reaching `CODE-IMPLEMENTATION` does not change that. The extension
  and its scope limit are recorded in
  [`notes/amendment-2026-10-01.md`](notes/amendment-2026-10-01.md). The
  substitution is now granted at both phases and nothing further is waived; the
  two verification-ledger entries stay owed, because the ruling permits the
  substitution rather than performing it.
- 2026-10-01: The § *Stub validation record* bullet that declares itself the
  current record still closed "the waiver concerns plan approval only", which
  the extension recorded above had already superseded, so the plan asserted two
  scopes in two places with no cross-reference between them. A reader stopping
  at the current record would have concluded an unobtainable EXECUTE-time red
  was still required for T5's two blocks. The stale clause is removed rather
  than reconciled by adding a second statement: the record now states the one
  extended scope and cites the ruling that grants it. The two
  verification-ledger entries stay owed, worded as before.
- 2026-10-01: **Scope gate passed. `eugenelim` approved the spec.** The seventh
  pre-EXECUTE pass returned no blockers and no concerns, and its one nit was
  refuted on adjudication as a presentation preference no record or authority
  decides, giving a clean adjudicated verdict (`## Main-loop result` reads
  `Clean — ready to commit.`, refuted 1, indeterminate 0). Residual risk
  recorded with the approval: the sustained-finding count fell 6, 9, 10, 3, 2,
  1, 0 across the rounds run under the amendment, and the trend only turned
  when repairs stopped adding obligations to the contract and started dropping
  or narrowing claims instead. Rounds 2 through 6 each sustained findings that
  were defects in the previous round's repair rather than in the work governed,
  so the clean verdict rests on a contract that stopped moving, not on a
  contract that was never wrong. Nothing in the spec changed between the
  approval given earlier today and this entry; the repair since then was
  confined to `plan.md`.
- 2026-10-01: **Build-strategy gate passed. `eugenelim` approved the plan.**
  The same clean adjudicated verdict covers the plan, which is the artifact the
  seventh pass spent most of its reading on. Approved with three conditions
  already recorded above and carried into execution rather than waived: T4 is
  committed but not met, and its `Done when` cannot pass until the roster test
  matches the approved stub byte for byte and the `4.1.2` changelog bullet is
  rewritten in outcome-led user register; T5's intended red is unobtainable at
  both phases and stands on the owner's scoped waiver plus two mutation proofs
  that are still owed as verification-ledger entries; and the boundary lint
  `tools/test-lint-pack-test-boundary.py` reds on this branch today, because T1
  introduced the pack test that reaches above its own pack, so the branch
  cannot go green until T5's relocation lands. T1, T2 and T3's sections are
  pinned and were verified byte-identical immediately before this approval.
- 2026-10-01: **Second contract amendment, post-gates.** The post-gates review
  sustained two findings that both sit inside the pinned canonical spec hash,
  measured rather than assumed, so the controlled `contract-amendment` path
  applied. AC-0011's rationale had asserted the superseded assertion "cannot
  fail" because the comment carries `unconfirmed` "in AC-0001's closed-set
  enumeration" — false, because AC-0001 pins the frontmatter placeholder while
  the assertion reads only the section comment, whose own enumeration no
  criterion pins. The entailment is deleted rather than restated, in all three
  carriers it occupied: this spec, T5's stub block, and the shipped assertion
  message, with the last two kept byte-identical. AC-0004's "exactly once in the
  file" clause is narrowed to the one-paragraph-block property its assertion
  actually decides, rather than strengthening the assertion, which was shipped
  under pinned T2 and would have needed a new dependency-ordered task. The
  authority, reason, the deadlock that interrupted the transition and the
  authorized one-field state repair that recovered it are recorded in
  [`notes/amendment-2026-10-01-post-gates.md`](notes/amendment-2026-10-01-post-gates.md).
  T1 through T4 are pinned and evidence-bound; only T5 is re-emitted. The
  experience review's twelve findings were all refuted and none is acted on.
