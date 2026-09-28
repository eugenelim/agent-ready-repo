# Spec: design-system derives project-specific values

- **Status:** Shipped
- **Owner:** eugenelim
- **Plan:** [`plan.md`](plan.md)
- **Constrained by:** ADR-0128; RFC-0033; ADR-0024; ADR-0052; [`creative-direction-contract`](../creative-direction-contract/spec.md)
- **Brief:** none
- **Discovery:** none
- **Contract:** none
- **Shape:** mixed

> **Spec contract:** this document defines what "done" means. The implementing
> change must match this spec or amend it through the repository workflow.
> `Agent Rules`, `Testing Strategy`, and `Acceptance Criteria` are the contract
> sections read by completion gates.

## Outcome

A `design-system` run turns an approved creative direction and the product's
incumbent constraints into a system a build can implement without deciding the
product's look for itself. The pack still ships no value of its own: the values
live in the artifact one invocation writes for one product, and an axis no
authority reaches is recorded unresolved rather than filled with a default.

## What Changes

- `design-system` gains four routes — `inherit`, `extend`, `originate`, and
  `refine` — selected from whether a coherent incumbent system exists and
  whether the work is a first derivation or a correction to a shipped one.
- The blanket "the reader produces the numbers" contract is replaced by a
  two-clause invariant: no universal defaults in the pack, project-specific
  values resolved in the artifact when authority supports them.
- A design-authority precedence orders stated project constraint, approved
  visual target, approved direction, incumbent system, and named platform
  convention above the skill's own derivation, with accessibility held as a
  non-rankable floor that constrains every resolved value and supplies none.
- Each of the fifteen direction axes is mapped to the system domain it
  constrains, and the two meanings the upstream contract gives
  `[platform-default]` — a decision the platform genuinely owns, and a
  decision nobody made — are told apart rather than merged.
- The artifact template resolves values instead of prompting the reader for
  them, and records authority, the relationships implementation must preserve,
  the proving set the system was checked against, and genuine unresolved
  decisions.
- Pack documentation, the Experience Design guide, evals, pack-local
  construction tests, pack metadata, the marketplace projection, and the
  release record agree with the published contract.

## Durable Outputs

| Semantic role | Applicability | Destination | Owner | Expected evidence | Closeout condition |
| --- | --- | --- | --- | --- | --- |
| Governance decision | An accepted RFC option is superseded | `docs/adr/0128-design-system-one-skill-resolves-project-values.md` | Repository decision-makers | Accepted ADR passing the shape lint | The stalled `xd-design-system-foundations` intent records the ADR as its resolution |
| Current product truth | The published skill contract changes | `packs/experience-design/.apm/skills/design-system/` | Experience Design maintainers | Skill, reference, template, and eval diff | Pack-local construction tests and catalogue verification pass |
| User promise | Adopters need to know what the artifact now contains | `guides/experience-design/` | Experience Design guide maintainers | Guide-agreement test and guide review | Guide describes a resolved artifact without naming a technology |
| Interface compatibility | Non-cosmetic pack content changes | `packs/experience-design/pack.toml`, `packs/experience-design/.claude-plugin/plugin.json`, `.claude-plugin/marketplace.json` | Pack maintainers and build projection | Matching patch versions in the pack's two manifests and regenerated marketplace data | Source manifests agree and the projection is current |
| Release history | Pack consumers gain a materially different artifact | `docs/product/changelog.md` | Product documentation maintainers | An Experience Design release entry with an explicit Highlights decision | The entry names the observable outcome and its version matches pack metadata |
| Reusable learning | Agent-level behavior needs durable examples | `packs/experience-design/.apm/skills/design-system/evals/` | Skill maintainers | One case per scenario named in AC-0018 | Eval JSON validates and construction tests pin the required cases |
| Invocation evidence | The artifact is something a person invokes | `docs/specs/design-system-values/notes/verification-ledger.md` | Delivery owner | One recorded real invocation and its written artifact | Recorded route, authority record, resolved domains, unresolved domains, and proving set |

## Agent Rules

### Always do

- Keep `design-system` a single registration. Express the four routes inside
  it; add no sibling skill for a design-system domain.
- Keep the write target `<output_dir>/tokens/<slug>.md` and the frontmatter
  identity `type: token-taxonomy`, which downstream reads by literal.
- Keep every confinement control and the existing `Writes:` / `Confinement:`
  declaration lines.
- Resolve a value only from the authority the precedence names, and record
  which rung supplied it.
- Treat accessibility as a floor that constrains every resolved value, never
  as a rung ranked against the direction and never as a source of one.
- Prefer the smallest coherent system that expresses the direction; state a
  relationship before the value that makes it executable.
- Inherit before extending, and extend before replacing. Name retained,
  extended, and replaced parts separately whenever a route changes an
  incumbent system.
- Point at the shared quality floor for accessibility criteria rather than
  restating them.

### Ask first

- Change the route set, the artifact path, the frontmatter type, or the
  fifteen-axis vocabulary this skill reads from `creative-direction`.
- Add a dependency on another pack, runtime, browser, image-analysis tool,
  script, hook, extension, downloaded binary, or package.
- Change a file outside this enumerated write boundary: the `design-system`
  skill and its pack-local tests; the Experience Design guide pages; the
  Experience Design pack's metadata and the generated marketplace metadata;
  the Experience Design pack
  documentation (`DESIGN.md`, `README.md`, `JOURNEY.md`, `docs/index.md`) and
  its site mirror under `web/src/content/`; this delivery contract and its
  notes; ADR-0128 and the intent record it resolves; and the release record.

### Never do

- Ship a palette, typeface, type scale, spacing rhythm, radius, border,
  shadow, breakpoint, duration, or easing value in the skill, any reference,
  the template, or the evals.
- Fill an axis no authority reached with a chosen value, or present a derived
  value as if it had been measured from an image.
- Let the approved-visual-target rung supply any value; it binds composition
  and relationships only, exactly as the upstream and downstream contracts
  already state.
- Add image extraction, computer vision, screenshot comparison, or any
  rendering capability.
- Re-run divergence, generate candidate directions, or invent a creative
  premise the approved direction does not carry.
- Create a second system beside a coherent incumbent one, or rename incumbent
  tokens to match a tidier model.
- Weaken an accessibility requirement to match a visual target.
- Name a UI framework, styling language, token pipeline, or design tool as
  the system's required binding.
- Change `creative-direction`, `design-review`, `information-architecture`,
  `interaction-design`, or any reviewer agent in this delivery.
- Change `frontend-engineering` at all. Its value-resolution bullet and its
  `direction-and-taxonomy` rung do assert the superseded contract, but
  `frontend-visual-authority` is still `Implementing` and its AC-0025a
  reserves that pack's next version, so the edit is handed to that slice
  rather than contending for the version. Recorded under Follow-ons.

## Testing Strategy

- **Published contract (AC-0001 through AC-0012, AC-0016, AC-0017):** TDD
  through a new pack-local construction test that reads the real skill,
  references, template, and eval files and fails when a route, the
  precedence, the floor rule, the axis-to-domain map, the
  `[platform-default]` split, the authority record, the proving set, or the
  unresolved-decision rule disappears.
- **No universal defaults (AC-0013):** two checks, because neither covers the
  whole surface. The repository's experience-agnosticism lint scans Markdown
  only, so it holds the skill, references, and template and must stay clean.
  The eval corpus is JSON and the lint never reads it, so the same value
  shapes are asserted absent from the eval files by the construction test.
- **Downstream compatibility (AC-0014):** goal-based checks through the
  cross-pack corpus tests and the frontend pack's own suite, which must stay
  green with the frontend pack unmodified — the artifact keeps its address and
  `type: token-taxonomy` identity, and the frontend read contract is
  section-agnostic, so nothing there breaks.
- **Agent behavior (AC-0018):** goal-based checks over the skill-local eval
  corpus, one case per scenario AC-0018 enumerates. AC-0018 is the single
  canonical list; nothing else restates it.
- **Packaging (AC-0019):** goal-based checks through targeted pytest, deep
  catalogue lint, catalogue verification, generated-projection comparison,
  and `make lint-ruff lint-mypy`.
- **Invoked artifact (AC-0020):** visual / manual QA through one real
  `design-system` prompt on a greenfield distinctive direction, owned by T7.

## Acceptance Criteria

- [x] **AC-0001.** `design-system` publishes four routes — `inherit`,
  `extend`, `originate`, `refine` — each with the trigger that selects it and
  the responsibilities it carries, in one skill with no sibling registration.
- [x] **AC-0002.** `SKILL.md` carries a selection rubric that maps a request
  to exactly one route, positioned ahead of the conditional reference routing
  section so route selection is readable before any reference is loaded.
- [x] **AC-0003.** The skill states the replacement invariant in two clauses:
  the pack ships no universal design value, and a run resolves
  project-specific values for every axis a stated project constraint, the
  approved direction, the incumbent system, or a named platform convention
  gives it authority to fix.
- [x] **AC-0004.** A design-authority precedence orders `stated-constraint`,
  `approved-visual-target`, `approved-direction`, `incumbent-system`,
  `platform-convention`, and `derivation`; states that a rung overrides a
  lower one only on the axis it decides and hands down every axis it left
  open; and states that `approved-visual-target` binds composition and
  relationships only and supplies no value, so values always come from a
  lower rung.
- [x] **AC-0005.** The accessibility floor is published as non-rankable: it
  constrains every resolved value, supplies none, and is never ranked against
  a goal. A resolved value that cannot clear it is adapted and the adaptation
  recorded, never traded away.
- [x] **AC-0006.** Each of the fifteen `creative-direction` axes is mapped to
  exactly one system domain, and every domain the skill resolves carries at
  least one axis.
- [x] **AC-0007.** The skill distinguishes the two meanings the upstream
  contract gives `[platform-default]`. Where the named target surface owns
  the decision, the value resolves from that platform's convention and the
  artifact records the `platform-convention` rung. Where no platform
  convention and no lower rung reaches it, the domain is recorded unresolved
  with the missing authority named and is not filled with a chosen value. A
  structural axis left at `[platform-default]` is reported back as a gap in
  the direction, because the upstream contract requires those seven decided.
- [x] **AC-0008.** An approved visual target informs relative scale, density,
  color relationships, hierarchy, containment, depth, spacing character, and
  recurrent graphic language as *relationships*. It yields no value directly,
  and the skill refuses to report any value as measured from it.
- [x] **AC-0009.** The artifact records its authority: the route taken, the
  direction source, the incumbent source, the visual target when one exists,
  and the rung that supplied each resolved domain.
- [x] **AC-0010.** The artifact separates the relationships implementation
  must preserve from the resolved values that make them executable, and
  records explicitly prohibited treatments where the direction makes one
  material.
- [x] **AC-0011.** Creating or materially extending a system requires checking
  it against a proving set — the smallest set of real product needs that
  exercises every resolved domain at least once — and the artifact records
  that set.
- [x] **AC-0012.** A route that changes an incumbent system records retained,
  extended, and replaced parts separately, and the skill refuses to create a
  parallel system or rename incumbent tokens for tidiness.
- [x] **AC-0013.** No color, typeface, dimension, duration, ratio, breakpoint,
  or easing value appears in the skill, its references, its template, or its
  evals. The pack's agnosticism lint is clean over the Markdown; the
  construction test covers the JSON eval files the lint does not read.
- [x] **AC-0014.** The skill binds to whatever token architecture the project
  already uses — a layered token system, a custom-property file, a theme
  object, a platform token source, a small constants module, or a design-only
  artifact whose binding comes later — and names no technology as required.
- [x] **AC-0016.** The skill publishes the failure modes it refuses: empty
  taxonomy, universal defaults, token proliferation without a product need,
  direction drift into a generic default, a parallel system beside a coherent
  incumbent one, a value presented as measured from an image, fidelity
  purchased at the cost of accessibility, and an artifact coupled to a
  technology the project does not require.
- [x] **AC-0017.** `design-system/SKILL.md` remains the control plane: route
  selection, authority, the invariant, the output contract, the handoff, and
  the failure modes load always; per-domain derivation method loads only when
  a route needs it.
- [x] **AC-0018.** Skill evaluations cover exactly these seven scenarios, one
  case each, and this list is the only canonical statement of them: a mature
  incumbent system; a greenfield distinctive direction; an approved visual
  target; a rejected category default; a brownfield conflict; insufficient
  authority; an accessibility conflict.
- [x] **AC-0019.** The Experience Design guide and pack documentation, the
  matching Experience Design pack and plugin versions, the pack's eval
  harness, the generated marketplace projection, and the release entry agree
  with the published contract. The `frontend-engineering` pack is unmodified
  and its suite stays green.
- [x] **AC-0020.** One real `design-system` invocation on a greenfield
  distinctive direction is recorded in the verification ledger, with the route
  taken, the authority record, the domains resolved, the domains left
  unresolved with their missing authority, and the proving set.

## Follow-ons

- **The two `frontend-engineering` statements that assert the superseded
  contract.** Its value-resolution step still says the taxonomy "carries roles,
  scales and relationships rather than numbers", and its
  `direction-and-taxonomy` rung does not record that the artifact binds values
  it resolved. Both edits were written, verified against that pack's suite, and
  reverted: `docs/specs/frontend-visual-authority/spec.md` is `Implementing`
  and its AC-0025a reserves the pack's next version for its slice 2, which a
  version-pin test enforces, so any edit here would contend for a version
  another slice owns. Owner: `frontend-visual-authority` slice 2, which is
  already rewriting that pack's journey, guide tree and release. The exact
  replacement text, the 960-line entrypoint budget it must fit, and the
  statements that must *not* change were handed to that work. Until it lands,
  a build reading a resolved artifact still gets the correct values — the read
  contract is section-agnostic — but is not yet told to prefer them.

- **Four dangling `design-system-foundations` references.**
  `references/digital-experience-contract.md` line 167 names a skill that does
  not exist, in four byte-pinned copies across the `experience-design`,
  `frontend-engineering`, `product-strategy`, and `product-engineering` packs.
  ADR-0128 changes their meaning from "not built yet" to "will not be built",
  so the wording is now wrong rather than merely early. Repairing them crosses
  four packs under a byte-parity check and would require four version bumps
  for a comment edit, which is out of proportion to this slice. Owner:
  Experience Design pack maintainers, alongside the next change that already
  touches that parity set. Stable reference:
  `docs/adr/0128-design-system-one-skill-resolves-project-values.md`, whose
  Consequences section records these four copies as a negative this decision
  accepts and does not repair — so the obligation survives in a governance
  record rather than only in this spec.

## Assumptions

- How much derivation method belongs in the always-loaded skill versus a
  route-triggered reference is settled by the plan's design decision, not by
  a measured threshold; no repository mechanism enforces a skill-body budget.
