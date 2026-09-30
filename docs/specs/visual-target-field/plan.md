# Plan: visual-target field

- **Spec:** [`spec.md`](spec.md)
- **Status:** Drafting <!-- Drafting | Approved | Executing | Done -->
- **Repository anchors:** `packs/AGENTS.md` § Version bump rule and
  § Self-hosting projection; `packs/AGENTS.local.md` § Marketplace and release
  pipeline; `docs/product/changelog.md` header;
  `tools/lint-guidebook-steps.py:537` (the verbatim-excerpt check that couples
  the template to `establish-design-intent.md:136-221`);
  `packs/frontend-engineering/.apm/skills/frontend-engineering/references/design-handoff.md:37,46`
  (the read takes the frontmatter as found and requires only `type:`, which is
  what makes an added key compatible with artifacts that predate it).

## Approach

Additive within one pack. The field is written but not read, so nothing
downstream changes and the slice cannot move a rung by accident. The producing
surfaces are gated in the same change as the field, because a field that exists
while `converge` still records a binding claim for an unconfirmed target would
put the artifact in a state the successor slice then has to interpret.

## Constraints

- No consumer reads the field in this slice.
- The template's first 84 lines are reproduced verbatim at
  `guides/experience-design/how-to/establish-design-intent.md:136-221` and
  checked by `tools/lint-guidebook-steps.py`. Every template edit re-derives
  that excerpt in the same commit.
- No new dependency, module boundary, or top-level directory; no sidecar file.
- `design-handoff.md` keeps saying only `type:` is required and the read takes
  the frontmatter as found, so artifacts predating the field stay valid.

## Construction tests

Every criterion is an assertion over a shipped file's bytes, except AC-0008
(the guidebook lint) and AC-0009/AC-0010 (the release surface). The gating
criteria assert a literal inside the instruction rather than the instruction's
presence, so removing the gate reds rather than passing on the sentence still
existing.

## Durable-output map

| Durable output | Task | Evidence |
| --- | --- | --- |
| Interface compatibility (the template) | T1 | Contract-suite assertions |
| Current product truth (the guide excerpt) | T1 | `lint-guidebook-steps.py` exit zero |
| Release history | T3 | `tests/conformance/test_pack_metadata.py` and the changelog entry |

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
adopter writing an artifact today records the disposition deliberately.

### Data & schema

Owned by: T1

The closed set is `none | unconfirmed | confirmed`, written as a quoted
placeholder exactly as `status` is.

### Behavior & rules

Owned by: T1, T2

Three producing surfaces state when a target's binding reaches the artifact:
`converge.md`, `visualize.md`, and `creative-direction`'s own output contract in
`SKILL.md`. All three are gated on the confirmed reading. `converge` is the only
writer; the other two are instruction surfaces that a producer follows, and
leaving either ungated would have a producer writing a binding claim the writer
then records.

### Dependencies & integration

Owned by: T3

Independent of `creative-direction-inherit-scope`, which touches a different
sentence of the same `SKILL.md`. If both are in flight, whichever lands second
rebases; there is no ordering requirement.

## Tasks

### T1: The template carries the field, and the guide excerpt still matches

**Depends on:** none

**Tests:**
- Contract test: the frontmatter carries `visual_target` enumerating exactly the
  three values. Verifies AC-0001.
- Contract test: the `## Approved visual target` section carries a
  `**Confirmation record:**` line. Verifies AC-0002.
- Contract test: that section's comment carries the canonical-state literals.
  Verifies AC-0003.
- `no stub (goal-based check)`: `python3 tools/lint-guidebook-steps.py guides/experience-design`
  exits zero. Verifies AC-0008.
- `stub: true` — one compilable red assertion over the template's frontmatter.

**Approach:**
- Re-derive the guide excerpt in the same commit as the template edit. The lint
  compares the excerpt to its declared source verbatim, so a template edit alone
  reds it, and a guide edit alone reds it the other way.

**Touches:** packs/experience-design/.apm/skills/creative-direction/assets/creative-direction-template.md, guides/experience-design/how-to/establish-design-intent.md, packs/experience-design/tests/skills/creative-direction/test_contract.py

**Done when:** `python3 -m pytest packs/experience-design/tests/skills/creative-direction -q` and the guidebook lint are both green.

### T2: The producing surfaces gate on the confirmed reading

**Depends on:** T1

**Tests:**
- Contract test: `converge.md` carries both disposition literals. Verifies AC-0004.
- Contract test: `converge.md`'s compositional-commitments instruction is gated.
  Verifies AC-0005.
- Contract test: `visualize.md`'s binding-boundaries instruction is gated.
  Verifies AC-0006.
- Contract test: `SKILL.md`'s output-contract entry is gated. Verifies AC-0007.

**Touches:** packs/experience-design/.apm/skills/creative-direction/references/converge.md, packs/experience-design/.apm/skills/creative-direction/references/visualize.md, packs/experience-design/.apm/skills/creative-direction/SKILL.md, packs/experience-design/tests/skills/creative-direction/test_contract.py

**Done when:** the creative-direction contract suite is green.

### T3: The release surface is consistent

**Depends on:** T1, T2

**Tests:**
- `no stub (goal-based check)`. `tests/conformance/test_pack_metadata.py` passes,
  the three version sites agree and exceed `origin/main`, and the changelog
  carries the entry with its `### Highlights` subsection. Verifies AC-0009,
  AC-0010.

**Approach:**
- `marketplace.json` is generated: run `FORCE=1 make build-self` after the bump.
- The change alters what a consumer can do — an adopter must now write a field
  that did not exist — so a `### Highlights` subsection is owed.

**Touches:** packs/experience-design/pack.toml, packs/experience-design/.claude-plugin/plugin.json, .claude-plugin/marketplace.json, docs/product/changelog.md

**Done when:** `make lint-ruff lint-mypy` and `tests/conformance/test_pack_metadata.py` are green.

## Rollout

- **Delivery:** one PR. Reversible by reverting it; no migration, because no
  consumer reads the field yet.
- **Infrastructure:** none.
- **External-system integration:** none.
- **Deployment sequencing:** T1 before T2, T3 last.

## Risks

- An adopter who writes the field expecting it to bind composition will find it
  does not until the successor slice ships. The template comment states the
  field's meaning; it cannot state a downstream behaviour that does not exist
  yet. This is the cost of splitting, and it is smaller than shipping the
  consumer change against an unmeasured carrier set.

## Changelog

- 2026-09-29: Drafted. Cut from `visual-target-confirmation`; carries the
  additive half, which is confined to one pack.
