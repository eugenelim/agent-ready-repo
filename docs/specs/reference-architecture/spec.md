# Spec: reference-architecture

- **Status:** Draft <!-- Draft | Approved | Implementing | Shipped | Archived -->
- **Owner:** eugenelim
- **Plan:** [`plan.md`](plan.md)
- **Constrained by:** RFC-0020 (the accepted proposal — Decisions 1–6); ADR-0010 (records those decisions); ADR-0009 (the consumer relationship: the LLD reads `reference.md` when present); RFC-0019 (ships that consumer; **not touched here**)
- **Brief:** none
- **Contract:** none — this feature exposes no machine-readable interface surface. The "stack-pack contract" named below is a *documented convention* (how a pack pre-bakes + delivers a filled `reference.md`), **not** a `contracts/<type>/` interface, so new-spec step 4b is intentionally skipped.
- **Shape:** mixed — a template asset (doc), a skill-behavior extension (`adapt-to-project` harvest), a documented delivery convention, a convention-diagram edit, and user guides. The plan's `## Design (LLD)` is pruned to the three sub-sections this spans.

> **Spec contract:** this document defines what "done" means. The implementing
> PR must match this spec, or update it. Verification must be derivable from it.

## Objective

RFC-0020 establishes a **normative** reference-architecture document —
`docs/architecture/reference.md` — the repo's golden path (stack, internal
framework building blocks, component stereotypes, cross-cutting standards) that
a low-level design *conforms to* as **steering**, distinct from the
**descriptive** `overview.md` code map. The consumer side already ships:
RFC-0019's `new-spec`/`plan.md` templates read `reference.md` when present
(Shape/Stack derivation). This feature ships the **producer** side and seats the
artifact in the conventions.

Concretely, an adopter — or a stack-pack author — needs three things. (1) A way
to **instantiate** the empty foundation: an arc42-shaped template, kept as a
skill asset and instantiated on demand (the `spec.md`/`plan.md` pattern), **never
pre-placed as a core seed** — so no shipped file collides with a stack pack's.
(2) A **brownfield path**: running `adapt-to-project` detects the stack,
reusable components, and recurring patterns from existing code and **proposes a
draft** `reference.md` the adopter confirms or edits — never authoritative until
confirmed. (3) A **documented stack-pack contract**: how an opt-in stack pack
pre-bakes a filled `reference.md` and delivers it as an ordinary seed without a
core-seed collision. The work also amends the CONVENTIONS document-hierarchy
diagram to seat `reference.md` beside `overview.md`, and ships user guides on
establishing and using it.

Success: an adopter with an existing codebase runs `adapt-to-project` and gets a
confirmable draft `reference.md`; any adopter can instantiate the empty template;
a stack-pack author has a documented, collision-free delivery path; and the
LLD (RFC-0019) has a normative anchor to conform to. **Greenfield authoring**
(`init-project` writing the first `reference.md`) is RFC-0021's foundation step
and is **out of scope** here — this spec ships a template that path will later
consume.

## Boundaries

The three-tier guard that keeps an implementing agent inside the lines.
*Always do* applies without asking; *Ask first* requires human sign-off
before proceeding; *Never do* is a hard rule, even under time pressure.

### Always do

- **Edit pack source, then `make build-self`.** Author under
  `packs/core/.apm/...` and `packs/core/seeds/...`; project with `make
  build-self`; then check `git status` for *unexpected* reverts to projected
  paths (a prior projection-only edit can be silently undone).
- **Keep core stack-neutral.** The template and the harvest output name **no**
  specific framework — stack specifics live only in the adopter's filled
  instance or an opt-in stack pack (CHARTER Principle 1).
- **Preserve the harvest confirm gate.** Harvest *proposes a draft* only; it
  never writes an authoritative `reference.md` without adopter confirmation, and
  every write stays inside `adapt-to-project`'s repo-scope path-jail.

### Ask first

- **Changing the four arc42 sections** (§2 Constraints · §4 Solution strategy ·
  §5 Building-block view/component catalogue · §8 Crosscutting concepts) or
  their vocabulary — RFC-0020 Decision 2 fixed these.
- **Re-homing the template asset** if `adapt-to-project/assets/` proves wrong at
  build time (surface it as a `## Design (LLD)` decision, don't silently move it).
- **Shipping the user guides to adopters** (seeding them into
  `user-guide-diataxis`) rather than authoring them in this catalogue repo's
  `docs/guides/` as RFC-0020 directs.

### Never do

- **Pre-place `reference.md` as a core seed**
  (`packs/core/seeds/docs/architecture/reference.md`) — RFC-0020 Decision 3
  forbids it; a core seed *guarantees* a collision with every stack pack that
  ships its own. *(structural)*
- **Create a new harvester skill** — extend `adapt-to-project` Class-3 discovery
  instead (RFC-0020 Decision 5). *(structural — no new skill)*
- **Touch `new-spec`'s `spec.md`/`plan.md` templates** — the consumer side is
  RFC-0019's; reading `reference.md` is already shipped there. *(structural)*
- **Author an actual stack pack** (React, Spring, …) — each is a downstream
  follow-on clearing the charter bars on its own; this spec ships only the
  *contract*. *(structural — no new pack)*
- **Introduce a pack-override field in the bundler** — RFC-0020 §Delivery says
  none is needed; the sole-producer case has nothing to collide against and the
  two-producer case routes through the existing `.upstream` + merge path.
  *(structural)*

## Testing Strategy

Skill/template/doc work has no runtime harness; behavior is prose verified by
presence checks, grep invariants, lints, and one executable bundler-contract
test. Modes, per user-visible outcome from the Objective:

- **Template exists, arc42-shaped, stack-neutral** — *goal-based*: grep asserts
  the four arc42 section headings are present and a representative
  framework-token set is **absent** (the stack-neutral invariant); a
  build-self projection check asserts the `.claude/...` copy is byte-identical
  to source. Cheap, mechanical, exactly fits a doc artifact.
- **`reference.md` is not a core seed** — *goal-based*: assert
  `packs/core/seeds/docs/architecture/reference.md` is absent and `make
  build-self` succeeds without it (the no-pre-placed-seed invariant).
- **Stack-pack two-producer collision guard** — *goal-based, exercised by an
  integration test*: a pytest stages two packs each seeding
  `docs/architecture/reference.md` with differing content and asserts
  `_project_seeds` raises the collision `ValueError` — the executable proof of
  the documented contract. (Integration-level: it drives the bundler's
  multi-pack projection, not a single function in isolation.)
- **Harvest path documented + lint-clean** — *goal-based*: a self-test asserts
  `adapt-to-project` SKILL.md documents the reference-architecture harvest
  (detect → instantiate → propose draft → repo-scope path-jail → per-finding
  accept/edit/decline); both lint surfaces (`lint-packs` and
  `lint-agent-artifacts`) pass. Prose can't be unit-tested; presence + lint is
  the right altitude.
- **CONVENTIONS diagram amended** — *goal-based*: grep the seed shows
  `reference.md` under `architecture/` distinct from `overview.md`; build-self
  projects it; the doc-drift gate is green.
- **User guides ship** — *goal-based*: four files exist under the right
  `docs/guides/<quadrant>/` paths, and a **task-local self-test** greps each
  guide's `](relative/path)` link targets and asserts every intra-repo target
  resolves on disk; `tools/lint-agents-md.py`'s Diátaxis-directory check stays
  satisfied. (There is no *repo-wide* markdown-link or guide-frontmatter gate, so
  T5 carries its own link-resolution self-test — a goal-based grep, not a new
  shared linter. `new-guide` supplies the audience-contract front matter.)

## Acceptance Criteria

- [ ] The arc42 `reference.md` template exists at
  `packs/core/.apm/skills/adapt-to-project/assets/reference.md` with all four
  sections — **Constraints** (arc42 §2), **Solution strategy** (§4),
  **Building-block view / component catalogue** (§5), **Crosscutting concepts /
  standards** (§8) — and carries guidance that it is filled only when there are
  real architecture decisions (a thin repo simply never instantiates it).
- [ ] The template names no specific tech stack or framework — a
  grep-absence check over a representative token set passes.
- [ ] No `packs/core/seeds/docs/architecture/reference.md` exists; `make
  build-self` succeeds and projects the template to
  `.claude/skills/adapt-to-project/assets/reference.md` byte-identical to source.
- [ ] `adapt-to-project` SKILL.md documents a Class-3 reference-architecture
  **harvest** path that: detects the stack + reusable components + recurring
  patterns, instantiates the template, **proposes a draft** `reference.md` at
  `docs/architecture/reference.md`, writes only within the repo-scope path-jail,
  and is per-finding accept/edit/decline — never authoritative before
  confirmation.
- [ ] The stack-pack delivery contract is documented (this spec + the reference
  guide): a stack pack ships a filled `reference.md` as
  `packs/<stack>/seeds/docs/architecture/reference.md`; sole-producer ⇒ no
  collision; the two-producer / atop-an-adopter's-own case routes through the
  `.upstream` companion + `adapt-to-project` merge; a stack pack never ships
  `overview.md`; **no bundler override field is added**. A presence check
  confirms the reference guide (AC8) states each of these four clauses — so the
  *documented* half of the contract fails on absence, not only the mechanism.
- [ ] A regression test **characterizes** the existing bundler behavior the
  contract leans on (`self_host.py` `_project_seeds`, ~L459): two packs seeding
  `docs/architecture/reference.md` with differing content raise the collision
  `ValueError`. This pins the two-producer guard; it does **not** by itself prove
  the contract is documented (that is the AC5 presence check).
- [ ] `docs/CONVENTIONS.md` (via its seed
  `packs/core/seeds/docs/CONVENTIONS.md`) document-hierarchy diagram seats
  `reference.md` under `architecture/` as the **normative** sibling of the
  **descriptive** `overview.md`; build-self projects the edit and the doc-drift
  gate is green.
- [ ] User guides ship under `docs/guides/`: a **tutorial** ("Create and use
  your `reference.md`"), a **how-to** ("Establish your repo's reference
  architecture"), an **explanation** ("Foundation vs. map"), and a **reference**
  ("`reference.md` arc42 sections + the stack-pack contract"); a task-local
  self-test asserts the four files exist at the right paths and that every
  intra-repo relative link in them resolves.
- [ ] All gates green: `lint-packs`, `lint-agent-artifacts`, `validate`,
  `build`, `build-self`, the relevant `pre-pr` subset, and `pytest`.

## Assumptions

- Technical: `reference.md` is NOT a core seed — RFC-0020 Decision 3 mandates
  template-on-demand, not a seed (source: `docs/rfc/0020-...md` §Proposal;
  `ls packs/core/seeds/docs/architecture/` confirms absent).
- Technical: the only projectable asset path is
  `.apm/skills/<skill>/assets/` → `.claude/skills/`, so a non-placed template
  must live under a skill, not `seeds/` (source:
  `packages/agentbundle/agentbundle/build/recipes/self-host.toml`
  `copy-from-pack-apm`).
- Technical: `adapt-to-project` is a core skill with no `assets/` dir today —
  the harvest extension creates one (source: `ls
  packs/core/.apm/skills/adapt-to-project/`).
- Technical: stack-pack delivery is an ordinary seed; collision → `_project_seeds`
  `ValueError` at self-host / install-time `.upstream` companion; no override
  field (source: `self_host.py:457-463`; RFC-0020 §Delivery).
- Technical: the consumer is already shipped — `new-spec`'s `spec.md`/`plan.md`
  read `reference.md` (Shape/Stack, step 4c) per RFC-0019; this spec ships only
  the producer (source: `.claude/skills/new-spec/assets/spec.md` `Shape:` header).
- Process: `docs/CONVENTIONS.md` is seed-projected from
  `packs/core/seeds/docs/CONVENTIONS.md` (sole `PROJECTED_README_OVERRIDES`
  entry) — the diagram edit goes to the seed, then build-self (source:
  `self_host.py:398-399`).
- Process: the CONVENTIONS hierarchy edit is pre-authorized — RFC-0020 (Accepted)
  lists it as a follow-on artifact, so it lands in this PR without a separate
  `update-conventions` RFC (source: `docs/rfc/0020-...md` §Follow-on artifacts).
- Process: edit pack source then `make build-self`; never edit projected
  `.claude/` or `docs/` paths directly (source: repo self-hosting convention).
- Product: all three build deliverables (template + harvest + stack-pack
  contract), the user guides, and the CONVENTIONS edit are in scope; greenfield
  authoring (RFC-0021) is out (source: user confirmation 2026-06-01).
- Process: the user guides are **this catalogue repo's own** `docs/guides/`
  documentation (repo-owned, matched by `EXCLUDED_PATTERNS` so never projected to
  adopters), authored via the `user-guide-diataxis` pack's `new-guide` skill —
  distinct from what `core` ships (the template + harvest + contract). A
  core-only adopter gets the producer machinery, not these guides (source:
  `self_host.py` `EXCLUDED_PATTERNS` `docs/guides/**`; RFC-0020 §Follow-on "in
  *this* catalogue repo, `docs/guides/`").
