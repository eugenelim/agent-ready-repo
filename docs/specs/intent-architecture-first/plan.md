# Plan: Architecture before the cut on the intent short route

- **Spec:** [`spec.md`](spec.md)
- **Status:** Approved
- **Repository anchors:** `packs/AGENTS.md` (version bump, self-host, eval
  harness); `docs/specs/architect-shaping-reach/plan.md` § Behavior & rules (the
  roster-check offer and silent clause this extends);
  `packs/product-engineering/tests/pack/test_architect_optional_offers.py` and
  `test_intent_skill_structure.py` (the prose-contract test shape and the pins
  this change must keep green). Non-structural: prose, eval, guide, and test
  edits only.

> **Plan contract:** this is the implementation strategy. It may change
> substantively only while its Status is `Drafting`, before approval records its
> baseline. After approval, `spec.md` and `plan.md` are pinned in substance;
> only lifecycle bookkeeping is permitted, and execution observations belong in
> `docs/specs/<feature>/notes/verification-ledger.md` (or the adopter's
> equivalent). A genuine artifact error follows the controlled-amendment path.
>
> **Not every field is contract.** `Touches`, `Tests` and `Done when` are what a
> completion gate reads, and they are pinned. `Design`, `Approach`, `Grounding`
> and `Risks` are working material that an implementer corrects in place only
> before approval: approval hashes the whole plan.

## Approach

Test first: extend the two pack tests, see them red, then edit the skill prose
until green. Skill prose, evals, and pack tests in T1; adopter docs and release
in T2. The riskiest part is keeping the existing pins true while adding a third
survive option and a new decompose section, so T1 lists every pin it moves.

## Constraints

- `test_intent_skill_structure.py` pins the four `##` headings of
  `SKILL.md`, the `Stage:` lines, the "step N of 3" labels, the survive-offer
  sentences, and the known-token set of every `## Next` section. The canonical
  rules therefore live in a `###` subsection, and the survive sentence is
  extended rather than replaced.
- `test_architect_optional_offers.py` treats every paragraph naming an architect
  skill plus "roster" as an offer that must carry the silent clause.
- `docs/specs/intent-short-route/spec.md` (Shipped) describes the survive offer
  as recommending the route's own next stage. This spec extends that case when
  `architect-design` is installed; the shipped record is not edited.
- `docs/product/changelog.md` header: release entries are fragments made with
  `python3 tools/changelog.py new` under `docs/product/changelog.d/`.
- `packs/AGENTS.md`: patch bump for changed content; non-cosmetic changes update
  the pack's evals; shipped pack content cites no internal records.
- `guides/AGENTS.md` § Job pages: one prompt per section, a lead-in ending in a
  colon, packs named.

## Construction tests

**Integration tests:** none beyond per-task tests.
**Manual verification:** none; prose has no runtime. AC-0019 proves projection parity.

## Durable-output map

| Durable output | Tasks | Implementation evidence | Closeout evidence |
| --- | --- | --- | --- |
| User promise — guide and README | T2 | AC-0016, AC-0017 checks | Both describe the step |
| Release history — changelog fragment | T2 | AC-0015 validate | Fragment present |

## Design (LLD)

### Behavior & rules

Owned by: T1.

**SKILL.md `### Architecture before the cut`** — after `### Supervised route`:

> On the short route, the architecture is designed after `de-risk` and before
> `decompose`. Check your available-skills roster for `architect-design`. When
> it is there, offer it before the cut unless a design already covers the
> intent or the user declined it for this intent. The offer is a default the
> user may decline; never start it yourself. If it is not in the roster,
> continue with this skill's own behaviour and say nothing about it: no
> mention, no note, and no error.
>
> Pick the scope from the intent's level:
>
> | Level | Scope |
> | --- | --- |
> | `product-vision` or `product-strategy` | `application/system` |
> | `capability` | `subsystem` when the system it belongs to already runs; otherwise `application/system` |
> | `feature` | `architecture change` |
>
> A design covers an intent when it is a resolved `architecture-design`
> artifact made for that intent or for one of its ancestors, and it names the
> system or subsystem the intent changes. When the user declines
> `architect-design` for an intent, do not offer it again for that intent in
> this conversation. Choosing another offered option counts as declining it;
> declining the frame mode's system-shape offer does not.

**SKILL.md § Short route** — a sub-bullet under step 2: "Then, before
`decompose`: `architect-design` (separate skill) is offered to design the
architecture when it is in your available-skills roster, as § Architecture
before the cut says. The user may decline it. If it is not in the roster,
continue with this skill's own behaviour and say nothing about it: no mention,
no note, and no error."

**de-risk.md § Next, survive bullet** — the lead becomes "Offer the next stage
for each route, each labelled with its route:", then "Recommend the one for the
route the conversation shows, unless the next paragraph applies." then the
kept sentence "When the conversation shows no route, recommend neither and ask
which route applies.", which the next paragraph never overrides because it acts
only on the short route, then a continuation paragraph: "On the short route, check your available-skills roster for
`architect-design` and offer it as a third option, labelled short route, when
§ Architecture before the cut in the skill calls for it, at the scope that
section picks. When you offer it, recommend `architect-design` instead of
`intent decompose`." followed by the silent clause.

**decompose.md `## Design before you cut`**:

> When `discovery-loop` or its `discovery-lead` agent called this mode, skip
> this section: the loop runs the architecture work itself.
>
> Otherwise, before cutting, check your available-skills roster for
> `architect-design`. When § Architecture before the cut in the skill calls for
> it, pause before cutting: say the architecture comes first on the short
> route, offer `architect-design` at the scope that section picks, and wait. If
> it is not in the roster, continue with this skill's own behaviour and say
> nothing about it: no mention, no note, and no error.
>
> When the user declines, cut as usual. When a design covers the intent, use it
> in step 1 and step 3. When the design changes the intent's capabilities, do
> not cut yet: for a `capability` or higher intent, recommend the longer route
> at `map-capabilities`; for a `feature`, recommend `intent frame` for its
> parent capability. Also offer to cut.

The feature branch exists because `map-capabilities` refuses a single feature
and sends it to `intent frame`.

**Guide section** — `## Design the architecture` between the de-risk and
break-down sections: one prompt, a sentence saying the `architect` pack is
optional with `agentbundle install --pack architect`, and that saying skip goes
straight to the break-down. `uses:` stays `[product-engineering]`, because the
page's job does not need the optional pack.

**decompose.md step 1** — the boundary-check paragraph keeps its first two
sentences and drops the structural-decomposition offer.

## Tasks

### T1: Skill prose, evals, and pack tests

- **Implements:** AC-0001 – AC-0013, AC-0020, AC-0021
- **Depends on:** none
- **Mode:** goal-based (prose contract tests), mutation for the silent clause
- **Review shape:** DEEP, small
- **Touches:** `packs/product-engineering/.apm/skills/intent/SKILL.md`,
  `.../intent/references/de-risk.md`, `.../intent/references/decompose.md`,
  `.../intent/evals/evals.json`,
  `packs/product-engineering/tests/pack/test_architect_optional_offers.py`,
  `packs/product-engineering/tests/pack/test_intent_skill_structure.py`
- **Tests:**
  - `test_architect_optional_offers.py`: a new test reads the `SKILL.md`
    subsection for AC-0001, AC-0002, and AC-0003; a new test reads the short
    route's sub-bullet order for AC-0004; a new test reads the survive bullet
    for AC-0005; a new test reads `## Design before you cut` and its position
    for AC-0007 and AC-0008; a new test slices `decompose.md` from
    "1. **Decompose one level.**" to "2. **Record" and asserts neither
    architect skill appears in it (AC-0009);
    `test_decompose_and_map_capabilities_offers` drops the old scope phrase and
    asserts the new section's phrases (AC-0010); `OFFER_FILES` gains
    `SKILL.md` and a mutation on it is reported (AC-0011); the eval test gains
    AC-0012's ids, modes, and assertions and AC-0013's prompt sentence; the
    existing heading and step-label pins cover AC-0020 and AC-0021.
  - `test_intent_skill_structure.py`: the known-token set gains
    `architect-design` only, and the per-bullet offer regex gains
    `architect-design` (AC-0006).
- **Done when:** `python3 -m pytest packs/product-engineering/tests -q` passes
  and the new tests were red before the prose edits.

### T2: Adopter docs, release, and projections

- **Implements:** AC-0014 – AC-0019, AC-0022
- **Depends on:** T1
- **Mode:** goal-based
- **Review shape:** WIDE
- **Touches:** `guides/product-engineering/how-to/frame-the-intent.md`,
  `packs/product-engineering/README.md`, `packs/product-engineering/pack.toml`,
  `packs/product-engineering/.claude-plugin/plugin.json`, a new
  `docs/product/changelog.d/*.md` fragment, regenerated projections
- **Tests:**
  - AC-0014: a `tomllib`/`json` one-liner prints both versions as `2.0.1`.
  - AC-0015: `python3 tools/changelog.py validate`.
  - AC-0016: `test_readme_states_the_optional_behaviour` gains the README phrase.
  - AC-0017: a `grep` for the section order and phrases.
  - AC-0018: `agentbundle catalogue verify --root .`.
  - AC-0019: `make build-self`, then `git status --porcelain` is empty.
  - AC-0022: `python3 tools/validate_guides.py`.
- **Done when:** every T2 check passes on the committed tree.

## Rollout

Ships with the next `product-engineering` release. Adopters get the step on
reinstall; nothing persisted changes.

## Risks

- A team with small features may find the pause noisy. The decline rule and the
  covers rule bound it to one question per intent, and none for a child inside
  a designed system.

## Changelog

- 2026-10-20: spec approved by eugenelim
- 2026-10-20: plan approved by eugenelim
