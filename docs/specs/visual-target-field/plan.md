# Plan: visual-target field

- **Spec:** [`spec.md`](spec.md)
- **Status:** Drafting <!-- Drafting | Approved | Executing | Done -->
- **Repository anchors:** `packs/AGENTS.md` § Version bump rule,
  § Security and authoring rules (the eval-harness obligation) and
  § Self-hosting projection; `packs/AGENTS.local.md` § Marketplace and release
  pipeline and § Landing changes; `docs/product/changelog.md` header;
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

The scope on each producing surface is worded as a condition on the producer's
own act of writing, never as a read of the field. `visualize` in particular
cannot read the field: it runs before `converge` on the only route that reaches
it, and `converge` is what creates the artifact and writes the disposition. Its
condition is therefore the human confirmation the operation already holds.

### Version bump size

Patch. `packs/AGENTS.md` § Version bump rule classifies patch for changed
content, minor for new primitives, major for removals. This slice adds a
frontmatter key and rewords instructions inside an existing skill; it publishes
no new skill, subagent, command or hook, so no new primitive exists. Target
version `4.1.2`.

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
(the guidebook lint) and AC-0009/AC-0010 (the release surface). The scoping
criteria assert an exact literal **inside a bounded unit** — one sentence, or
one list item — rather than anywhere in the file. A whole-file substring check
would pass on any other occurrence of the same word, which is the presence-check
mechanism the predecessor contract recorded as tried and rejected.

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
slice: the release baseline is the `4.1.1` this branch already carries, not the
`4.1.0` on `origin/main`; and the existing changelog entry belongs to that
slice, so this one authors its own rather than extending it.

## Tasks

### T1: The template carries the field, and the guide excerpt still matches

**Depends on:** none

**Tests:**
- Contract test: the frontmatter carries `visual_target` enumerating exactly the
  three values. Verifies AC-0001.
- Contract test: the `## Approved visual target` section carries a
  `**Confirmation record:**` line whose placeholder names a date and a location
  and offers no person-identifying prompt. Verifies AC-0002.
- Contract test: that section's comment carries the canonical-state literals.
  Verifies AC-0003.
- Contract test: that comment states the absent-field reading. Verifies AC-0011.
- Contract test: the guide carries both the frontmatter key and the
  `**Confirmation record:**` line. Verifies AC-0012.
- `no stub (goal-based check)`: `python3 tools/lint-guidebook-steps.py guides/experience-design`
  exits zero. Verifies AC-0008.

**Stub** — add to `packs/experience-design/tests/skills/creative-direction/test_contract.py`:

```python
def test_template_carries_the_visual_target_disposition() -> None:
    template = _read(TEMPLATE)
    frontmatter = template.split("---", 2)[1]
    assert re.search(
        r'^visual_target:\s*"<none \| unconfirmed \| confirmed>"\s*$',
        frontmatter,
        re.M,
    ), "AC-0001: frontmatter must carry visual_target over the closed set"

    section = template.split("## Approved visual target", 1)[1].split("\n## ", 1)[0]
    assert "**Confirmation record:**" in section, "AC-0002"
    record_line = next(
        line for line in section.splitlines() if line.startswith("**Confirmation record:**")
    )
    assert "date" in record_line and "where" in record_line, "AC-0002"
    assert not {"who", "name", "handle", "email"} & set(
        re.findall(r"[a-z]+", record_line.lower())
    ), "AC-0002: the placeholder must not invite person-identifying content"

    comment = section.split("-->", 1)[0]
    assert "visual_target" in comment, "AC-0003"
    for label in ("**Target:**", "**Binding:**", "**Confirmation record:**"):
        assert label in comment, "AC-0003"
    assert "bind nothing on their own" in comment, "AC-0003"
    assert "an absent" in comment.lower() and "unconfirmed" in comment, "AC-0011"


def test_guide_excerpt_carries_the_new_template_material() -> None:
    guide = _read(
        PACK_ROOT.parents[1]
        / "guides"
        / "experience-design"
        / "how-to"
        / "establish-design-intent.md"
    )
    assert "visual_target" in guide, "AC-0012"
    assert "**Confirmation record:**" in guide, "AC-0012"
```

**Approach:**
- Re-derive the guide excerpt in the same commit as the template edit. The lint
  compares the excerpt to its declared source verbatim, so a template edit alone
  reds it, and a guide edit alone reds it the other way.

**Touches:** packs/experience-design/.apm/skills/creative-direction/assets/creative-direction-template.md, guides/experience-design/how-to/establish-design-intent.md, packs/experience-design/tests/skills/creative-direction/test_contract.py

**Done when:** `python3 -m pytest packs/experience-design/tests/skills/creative-direction -q` and the guidebook lint are both green.

### T2: The producing surfaces are scoped to a confirmed target

**Depends on:** T1

**Tests:**
- Contract test: `converge.md` carries both disposition literals. Verifies AC-0004.
- Contract test: `converge.md`'s compositional-commitments sentence carries the
  confirmed literal. Verifies AC-0005.
- Contract test: `visualize.md`'s binding-boundaries sentence carries the
  confirmation literal. Verifies AC-0006.
- Contract test: `SKILL.md`'s output-contract list item carries it. Verifies AC-0007.

**Stub** — add to the same file:

```python
def _sentence_containing(text: str, needle: str) -> str:
    flat = " ".join(text.split())
    assert needle in flat, f"anchor {needle!r} not found"
    start = flat.rfind(". ", 0, flat.index(needle))
    end = flat.find(". ", flat.index(needle))
    return flat[(start + 2) if start != -1 else 0 : end if end != -1 else len(flat)]


def test_producing_surfaces_are_scoped_to_a_confirmed_target() -> None:
    converge = _read(REFERENCE_ROOT / "converge.md")
    assert "visual_target: confirmed" in converge, "AC-0004"
    assert "visual_target: unconfirmed" in converge, "AC-0004"
    assert "visual_target: confirmed" in _sentence_containing(
        converge, "compositional commitments into the doc"
    ), "AC-0005"

    visualize = _read(REFERENCE_ROOT / "visualize.md")
    assert "the human has confirmed" in _sentence_containing(
        visualize, "record its identity and three boundaries"
    ), "AC-0006"

    item = next(
        block
        for block in _skill_text().split("\n- ")
        if block.startswith("**Approved visual target**")
    )
    assert "the human has confirmed" in " ".join(item.split()), "AC-0007"
```

**Touches:** packs/experience-design/.apm/skills/creative-direction/references/converge.md, packs/experience-design/.apm/skills/creative-direction/references/visualize.md, packs/experience-design/.apm/skills/creative-direction/SKILL.md, packs/experience-design/tests/skills/creative-direction/test_contract.py

**Done when:** the creative-direction contract suite is green.

### T3: The eval harness covers the field

**Depends on:** T2

**Tests:**
- Contract test: at least one eval case asserts a `visual_target` disposition.
  Verifies AC-0013.

**Stub** — add to the same file:

```python
def test_eval_harness_exercises_the_visual_target_disposition() -> None:
    evals, queries = _eval_payloads()
    blob = json.dumps(evals) + json.dumps(queries)
    assert "visual_target" in blob, "AC-0013"
```

**Approach:**
- `packs/AGENTS.md` § Security and authoring rules: "A non-cosmetic pack update
  also updates that pack's eval harness." This slice changes the published
  artifact schema, so the obligation is live rather than deferrable.

**Touches:** packs/experience-design/.apm/skills/creative-direction/evals/evals.json, packs/experience-design/.apm/skills/creative-direction/evals/eval_queries.json, packs/experience-design/tests/skills/creative-direction/test_contract.py

**Done when:** the creative-direction contract suite is green.

### T4: The release surface is consistent

**Depends on:** T1, T2, T3

**Tests:**
- `no stub (goal-based check)`. `tests/conformance/test_pack_metadata.py` passes,
  the three version sites agree and exceed the recorded slice-start baseline
  `4.1.1`, and the changelog carries this slice's own entry with its
  `### Highlights` subsection naming the field. Verifies AC-0009, AC-0010.

**Approach:**
- Bump to `4.1.2` per § Version bump size above.
- `marketplace.json` is generated. Commit first, then run plain `make
  build-self`. `packs/AGENTS.local.md` § Landing changes forbids passing
  `FORCE=1` from automation; the force flag only overrides the dirty-tree guard,
  so committing first removes the reason to reach for it.
- The change alters what a consumer can do — an adopter must now write a field
  that did not exist — so a `### Highlights` subsection is owed.

**Touches:** packs/experience-design/pack.toml, packs/experience-design/.claude-plugin/plugin.json, .claude-plugin/marketplace.json, docs/product/changelog.md

**Done when:** `make lint-ruff lint-mypy` and `tests/conformance/test_pack_metadata.py` are green.

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
  Recorded baseline observation, taken at the start of this work: the version on
  `$(git merge-base HEAD origin/main)` is `4.1.0`, and the version this branch
  already carries at HEAD is `4.1.1`, released by the sibling
  `creative-direction-inherit-scope` slice. AC-0009 therefore measures against
  `4.1.1`. Added AC-0011 (absent-field reading), AC-0012 (the excerpt carries
  the new material) and AC-0013 (eval harness), added T3 for the eval-harness
  obligation, replaced the prose stub descriptors with compilable red
  assertions, reworded AC-0005 to AC-0007 as exact literals inside bounded
  units, restated AC-0006 as a confirmation condition rather than a field read,
  and corrected the dependency section, which described the sibling slice as in
  flight after it had landed.
