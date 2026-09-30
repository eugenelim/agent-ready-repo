# Plan: design-system derives project-specific values

- **Spec:** [`spec.md`](spec.md)
- **Status:** Done
- **Repository anchors:** `AGENTS.md`, `packs/AGENTS.md`, `packs/AGENTS.local.md`, `guides/AGENTS.md`, `docs/AGENTS.md`, `guides/_shared/reference/catalogue-authoring-standards.md`; analogous implementation [`creative-direction-contract`](../creative-direction-contract/spec.md) with its construction test `packs/experience-design/tests/skills/creative-direction/test_contract.py`; owners `packs/experience-design/.apm/skills/design-system/`, `packs/frontend-engineering/.apm/skills/frontend-engineering/`, `packs/experience-design/pack.toml`. No new module boundary and no new dependency. Named uncertainty: how much of the derivation method belongs in the always-loaded skill versus a route-triggered reference.

> **Plan contract:** this is the implementation and verification strategy.
> `Touches`, `Tests`, and `Done when` are completion-gate inputs. After approval,
> execution observations belong in `notes/verification-ledger.md`.

## Approach

Record the governance decision first, because the skill change takes a side in a
contradiction two accepted records already carry. Then write one pack-local
construction test that fails against today's skill, and bring the skill,
references, template, and evals up to it. Reconcile the two
`frontend-engineering` statements that assert the artifact carries no numbers,
then the pack documentation, guide, versions, projection, and release entry.
Finish with the targeted pack, cross-pack, catalogue, lint, and
manual-invocation checks.

## Constraints

- RFC-0033 and ADR-0024 keep this work inside the Experience Design pack and
  keep the skill framework-agnostic and portable.
- The repository's experience-agnosticism lint fails on any colour literal,
  dimension or duration literal, ratio literal, named easing curve, framework
  name, styling-language token, or accessibility-platform role anywhere under
  `packs/experience-design/`. It collects `*.md` only and states that scope in
  its own docstring, so it holds the skill, references, and template — and
  never reads `evals/*.json`. The construction test carries the same value
  shapes over the eval corpus; the two together cover the surface, and neither
  alone does.
- `packs/AGENTS.md` forbids citing this catalogue's internal records from
  shipped pack content, so the ADR, this spec, and the lint are named here and
  never inside the pack.
- ADR-0116 keeps the only durable output under `<output_dir>/tokens/`.
- The shipped `creative-direction` contract owns the fifteen-axis vocabulary,
  the `[platform-default]` token, and the route names this skill mirrors; this
  slice reads them and changes none of them.
- `packs/AGENTS.md` requires matching version bumps in both source manifests
  and an eval-harness update for a non-cosmetic `.apm/` change.
- `packs/AGENTS.local.md` requires marketplace regeneration and a free-standing
  release entry with an explicit `Highlights` decision.
- `web/src/content/journeys/experience-design.md` mirrors the pack `JOURNEY.md`;
  both move together.
- No new RFC, executable, dependency, hook, browser surface, image-analysis
  requirement, or cross-pack dependency enters this slice.
- `creative-direction`, `design-review`, `information-architecture`,
  `interaction-design`, and reviewer-agent files are outside the write boundary.
- Skill-engineering knowledge provider: unavailable; repository contracts and
  the accepted request are the authoring baseline.

## Grounding

Four checks against the live tree, each re-runnable:

- `creative-direction` already assigns value derivation to this skill in four
  shipped places — `references/refusals.md`, `references/visualize.md`, and two
  lines of `assets/creative-direction-template.md`. The obligation exists
  upstream and is unmet downstream; this slice meets it rather than inventing
  authority.
- `tools/lint-experience-agnostic.py` is the mechanical floor under "no
  universal defaults" and scans every Markdown file under the pack. It stays
  unchanged and must stay clean.
- `packs/frontend-engineering/.apm/skills/frontend-engineering/references/fallback-tokens.md`
  ships a fixed spacing base, radius set, shadow recipe, and easing pair,
  reached whenever no taxonomy and no incumbent system resolve. It is the
  observed cost of a taxonomy that refuses values; this slice does not change
  its content or its reach condition.
- `packs/experience-design/JOURNEY.md` already asks whether contrast in the
  token set is verified and whether the set could be handed to a developer
  without ambiguity — obligations today's value-free artifact cannot meet.

Implementation stops for amendment if any named owner disappears or the
fifteen-axis vocabulary moves before execution.

## Construction tests

**Integration tests:** a new pack-local pytest reads the shipped skill,
references, template, and eval corpus together. The existing cross-pack roster
tests and the frontend visual-authority tests cover the handoff; deep catalogue
lint and catalogue verification cover packaging.

**Manual verification:** invoke the built `design-system` skill once on a
greenfield distinctive direction with no incumbent system. Record the route
taken, the authority record, the domains resolved, the domains left unresolved
with their missing authority, and the proving set, in
`notes/verification-ledger.md`.

## Durable-output map

| Durable output | Tasks | Implementation evidence | Closeout evidence |
| --- | --- | --- | --- |
| Governance decision | T1 | Accepted ADR and the intent's resolution note | AC-0001 context recorded; no accepted record left silently contradicted |
| Skill, references, and template | T2, T3 | Targeted construction test and diff | AC-0001–AC-0014, AC-0016, AC-0017 checked; catalogue verification passes |
| Skill eval corpus | T2, T4 | Valid JSON and one case per required scenario | AC-0018 checked |
| Pack documentation and guide | T6 | Guide-agreement test and diff | AC-0019 checked |
| Pack, plugin, and marketplace versions | T6 | Matching source versions in both changed packs and zero generated drift | AC-0019 checked; projection is current |
| Release history | T6 | One changelog entry per bumped pack, each with an explicit Highlights decision | Entry versions and behavior match the packs |
| Invocation evidence | T2, T7 | Recorded red run and one recorded real invocation | AC-0020 checked; ledger names route, authority, resolved and unresolved domains, and proving set |

## Design (LLD)

### Design decisions

<!-- Owned by: T3. -->

The always-loaded `SKILL.md` owns route selection, the authority precedence and
its floor, the two-clause invariant, the condition under which a value must be
resolved, the output contract, the downstream handoff, and the refused failure
modes. Per-domain derivation method, the axis-to-domain map's detail, and
incumbent-system mechanics move behind two route-triggered references, so a
run loads method only for the route it took. Traces to: AC-0001–AC-0012,
AC-0016, AC-0017. Owned by: T3.

### Interfaces & contracts

<!-- Owned by: T3. -->

The public interface is the installed `design-system` skill plus
`<output_dir>/tokens/<slug>.md`. The artifact path and the `type: token-taxonomy`
frontmatter identity are unchanged, because the frontend handoff read matches
that literal and a roster test pins the pair. The change is to what the body
carries, and the handoff read is deliberately section-agnostic, so it needs no
change at all — which is what lets the frontend pack stay out of this slice.
Traces to: AC-0009, AC-0010, AC-0014. Owned by: T3.

### Component / module decomposition

<!-- Owned by: T3, T4. -->

- `SKILL.md`: routes, selection rubric, authority precedence and floor, the
  invariant, when values must resolve, procedure, output, failure modes, and
  conditional reference routing.
- `references/value-derivation.md` (new): the axis-to-domain map, the
  per-domain resolution method, the proving set, the visual-target reading
  rule, and the accessibility-adaptation rule.
- `references/incumbent-systems.md` (new): discovering the source of visual
  truth, inherit and extend mechanics, the retained/extended/replaced record,
  and binding to whatever token architecture the project already uses.
- `references/token-taxonomy-derivation.md`: retained as the naming, layering,
  and ratio method, with the "reader supplies values" framing removed.
- `references/atomic-composition.md`: unchanged.
- `references/containment.md`, `references/agentbundle-layout.md`: unchanged.
- `assets/token-taxonomy-template.md`: the resolved artifact shape.
- `evals/`: one case per required scenario.

Traces to: AC-0001–AC-0019. Owned by: T3, T4.

### State & control flow

<!-- Owned by: T3. -->

A run resolves `output_dir` and the slug under the existing confinement
controls, reads the direction artifact and the repository's incumbent system,
and selects one route from incumbent coherence and the nature of the ask. It
then walks the six-rung authority precedence per axis, groups the resolved axes
into domains, resolves values for every domain an authority reaches, checks the
result against the proving set, holds the floor, and writes the artifact. A
domain no authority reaches is recorded unresolved with the missing authority
named. Traces to: AC-0001–AC-0012. Owned by: T3.

### Behavior & rules

<!-- Owned by: T3. -->

Authority is per-axis, not per-artifact: a rung overrides a lower one only on
the axis it decides, and hands down every axis it left open. That single rule
produces the brownfield behavior the outcome requires — a coherent incumbent
system keeps every axis the direction did not commit, including naming and
binding convention, so a new direction changes what it actually decided and
nothing else. It also settles the visual-target rung with no special case:
that rung decides composition and relationships, so it hands every value down,
which is what the upstream and downstream contracts already say.

`[platform-default]` carries two upstream meanings and the split matters. In
`explore` it marks an axis the platform genuinely owns; in `converge` it is
also the token for undecided, and only the seven structural axes are forbidden
to keep it. So the skill reads the direction's named target surface first:
where that platform owns the decision, the value resolves from the platform's
convention at the `platform-convention` rung. Only when no platform convention
and no lower rung reaches the axis is the domain recorded unresolved. Without
that split, a normally converged iOS direction would report typography, color,
and motion unresolved, which is the opposite of the outcome.

Accessibility sits outside the ranking entirely: it constrains every resolved
value and supplies none. A resolved value that cannot clear the floor is
adapted and the adaptation recorded, never traded against a goal. Traces to:
AC-0004, AC-0005, AC-0007, AC-0008, AC-0012. Owned by: T3.

### Failure, edge cases & resilience

<!-- Owned by: T3, T4. -->

Absent direction, absent incumbent system, and absent visual target are normal
input states. Absent direction plus absent incumbent system is the one state
that cannot produce a complete system: the skill records what it cannot resolve
and names the missing authority rather than fabricating a brand. An axis left
at `[platform-default]` resolves from the named platform's convention where
that platform owns the decision, and is otherwise undecided — never permission
to choose. A visual target informs relationships and never yields a value,
measured or otherwise. Traces to: AC-0007, AC-0008, AC-0016, AC-0018. Owned
by: T3, T4.

### Quality attributes

<!-- Owned by: T2, T3, T6. -->

The change stays pure Markdown and JSON and adds no runtime dependency.
Progressive disclosure is measured as always-loaded bytes, with the mandatory
shared rendering block counted separately, because moving a mandatory
instruction into a reference every run then loads is not an improvement.
Construction tests cover exact contract anchors; eval rubrics cover the
judgment-heavy behavior those tests cannot execute. Traces to: AC-0013,
AC-0017–AC-0019. Owned by: T2, T3, T6.

### Dependencies & integration

<!-- Owned by: T3. -->

The direction artifact, the incumbent system, the visual target, and the screen
briefs are optional evidence sources, not installed-pack dependencies. No
image, browser, or vision capability is required or invoked. The frontend pack
consumes the artifact through its existing read contract, unmodified. Traces
to: AC-0014. Owned by: T3.

## Tasks

### T1: Record the governance decision that lets one skill own value resolution

**Depends on:** none

**Touches:** `docs/adr/0128-design-system-one-skill-resolves-project-values.md`,
`docs/product/intents/xd-design-system-foundations.md`.

**Tests:** no stub (goal-based). `Done when:` `tests/roster/test_lint_adr_shape_corpus.py`
passes with the new record present; the ADR is Accepted, answers RFC-0071 D3a
and cites ADR-0052 in `Related` — the supersession fields take ADR ordinals
only, so an RFC decision cannot be cited there — and the intent's contradiction
note points at it.

**Approach:** RFC-0071 D3a chose a separate `design-system-foundations` skill;
ADR-0052 renamed that name away. The intent records that neither can be
delivered until one gives way. This ADR takes the third option the accepted
request names: one `design-system` skill whose routes carry the foundation
work, so ADR-0052's name survives and D3a's capability lands without a second
registration.

### T2: Construction test fails when the new contract is absent

**Depends on:** none

**Touches:** `packs/experience-design/tests/skills/design-system/test_design_system_contract.py`.

**Tests:** TDD. The stub asserts the four route names, the six precedence rungs
in order, the floor rule, all fifteen axis names in the axis-to-domain map, the
`[platform-default]` split, the authority record fields, the proving-set rule,
the unresolved-decision rule, the two-clause invariant, the failure-mode
inventory, the absence of every value shape in both the Markdown corpus and the
eval JSON, and the seven eval scenarios AC-0018 enumerates.

`Done when:` the suite fails against today's skill for those reasons and no
other, and the red run is recorded in `notes/verification-ledger.md` with its
failure count.

**Approach:** mirror the creative-direction contract test — static reads,
literal and regex pins, id-keyed eval assertions, no subprocess and no fixture.

### T3: `design-system` resolves project-specific values under a stated authority

**Depends on:** T2

**Touches:** `packs/experience-design/.apm/skills/design-system/SKILL.md`,
`packs/experience-design/.apm/skills/design-system/references/value-derivation.md` (new),
`packs/experience-design/.apm/skills/design-system/references/incumbent-systems.md` (new),
`packs/experience-design/.apm/skills/design-system/references/token-taxonomy-derivation.md`,
`packs/experience-design/.apm/skills/design-system/assets/token-taxonomy-template.md`.

**Tests:** T2's suite. `Done when:` it passes and
`python3 tools/lint-experience-agnostic.py` exits 0.

**Approach:** rewrite the skill as a control plane; move method behind the two
new references; make the template resolve values, record authority per domain,
separate relationships from values, carry the proving set, and keep only
genuine unresolved decisions.

### T4: Evals distinguish the new contract from the old one

**Depends on:** T2, T3

**Touches:**
`packs/experience-design/.apm/skills/design-system/evals/evals.json`,
`packs/experience-design/.apm/skills/design-system/evals/eval_queries.json`.

**Tests:** T2's suite pins the required cases by id. `Done when:` the JSON
validates, one case covers each of the seven scenarios AC-0018 enumerates, and
the suite's eval-corpus value-shape assertions pass.

### T6: The published pack, guide, versions, projection, and release agree

**Depends on:** T3, T4

**Touches:** `packs/experience-design/DESIGN.md`,
`packs/experience-design/README.md`, `packs/experience-design/JOURNEY.md`,
`packs/experience-design/docs/index.md`,
`packs/experience-design/pack.toml`,
`packs/experience-design/.claude-plugin/plugin.json`,
`guides/experience-design/how-to/establish-design-intent.md`,
`guides/experience-design/reference/experience-design.md`,
`web/src/content/journeys/experience-design.md`,
`web/src/content/packs/experience-design.md`,
`.claude-plugin/marketplace.json`,
`docs/product/changelog.md`.

**Tests:** no stub (goal-based). `Done when:` `python3 tools/validate_guides.py`,
`python3 -m pytest tests/roster`, `agentbundle catalogue lint --root . --deep`,
`agentbundle catalogue verify --root .`, and `FORCE=1 make build-self` with no
resulting drift all pass; the Experience Design pack carries matching patch
versions in its two manifests; and it has a free-standing release entry with an
explicit `Highlights` decision.

**Approach:** `DESIGN.md`'s "No values, ever" safety invariant is the
pack-level statement of the old contract and is the one that must be split into
its two halves rather than deleted. The `frontend-engineering` pack is not
touched: its next version is reserved by an in-flight slice, so its two
superseded statements are handed to that slice and recorded under the spec's
Follow-ons.

### T7: One real invocation is recorded

**Depends on:** T3, T4

**Touches:** `docs/specs/design-system-values/notes/verification-ledger.md`.

**Tests:** visual / manual QA. `Done when:` the ledger records one real
`design-system` invocation on a greenfield distinctive direction, naming the
route taken, the authority record, the domains resolved with the rung that
supplied each, the domains left unresolved with their missing authority, and
the proving set — and no domain the direction's axes reached is left as a
reader-decides placeholder. Satisfies AC-0020.

## Rollout

Single change, no migration. Adopters with an existing value-free taxonomy keep
a valid artifact: the frontend read is section-agnostic, and its value
resolution still handles a taxonomy that resolved nothing.

## Risks

- **A resolved value leaks into pack source.** The agnosticism lint catches
  every shape of it across the pack's Markdown, and the construction test
  carries the same shapes over the eval JSON the lint cannot read. Together
  they are the gate; neither alone covers the surface.
- **The skill grows into a design essay.** The construction test pins the
  always-loaded body's contract anchors, and the footprint is measured before
  and after rather than asserted. No repository mechanism enforces a budget,
  so the measurement is reported, not gated.
- **The precedence drifts from the frontend one.** AC-0004 adopts verbatim
  the rule the frontend and upstream packs already state about the
  visual-target rung, so the two agree by construction rather than by
  synchronisation. The frontend pack is unmodified here, and its suite is run
  to prove the artifact change did not reach it.

## Changelog

- 2026-09-27 — Drafted.
- 2026-09-27 — Revised against pre-EXECUTE adversarial review: task
  dependencies added; the `[platform-default]` split and the visual-target
  rung's no-value rule adopted from the shipped upstream and downstream
  contracts; the lint's Markdown-only scope corrected and eval-JSON coverage
  moved to the construction test; T7 added for the recorded invocation.
- 2026-09-28 — T5 removed and handed to `frontend-visual-authority` slice 2.
  Both frontend edits were written and verified, then reverted: that spec is
  `Implementing` and its AC-0025a reserves the pack's next version, enforced by
  a version-pin test. Handing the edit over rather than contending for the
  version was the owner's decision.
