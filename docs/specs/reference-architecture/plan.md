# Plan: reference-architecture

- **Spec:** [`spec.md`](spec.md)
- **Status:** Done <!-- Drafting | Executing | Done -->

> **Plan contract:** this is the implementation strategy. Unlike the spec, this
> document is allowed to change as you learn. When it changes substantially
> (a different approach, not just a re-ordering), note why in the changelog
> at the bottom.

## Approach

Source-first, projection-second. Every change is authored under `packs/core/`
(skill assets, the `adapt-to-project` SKILL.md, the CONVENTIONS seed) or this
repo's own `docs/guides/`, then realized by `make build-self`; nothing edits a
projected `.claude/` or projected `docs/` path directly.

The work splits into four near-independent build pieces plus guides. The
**template asset** (T1) is foundational — both the harvest path and the guides
describe instantiating it — so it goes first. The **stack-pack contract** (T2)
is independent: it adds an executable regression test that pins the bundler's
existing collision behavior (the contract's guarantee) and documents the
delivery shape. The **harvest extension** (T3) depends only on T1's template
path. The **CONVENTIONS diagram** (T4) is independent. The **user guides** (T5)
come last because they describe the finished mechanism accurately. T1, T2, and
T4 touch disjoint files and can run in one wave; T3 follows T1; T5 follows all.

The riskiest part is the `adapt-to-project` SKILL.md extension (T3): it must
stay inside Class-3's existing propose-and-confirm + repo-scope path-jail shape
(mirroring the "Contract relocation" precedent) without inventing a new
mechanism, and clear both lint surfaces. Second risk is build-self silently
reverting a projection — mitigated by always editing source and checking `git
status` after every build.

## Constraints

- **RFC-0020** (Accepted) — Decisions 1–6: a normative `reference.md` distinct
  from `overview.md` (D1); arc42 four sections (D2); template-on-demand, **not**
  a core seed (D3); population by repo context (D4); harvest via `adapt-to-project`
  Class-3 (D5); stack specifics in opt-in packs (D6). Plus its §Delivery (no
  override field) and §Follow-on artifacts (this spec's deliverable list).
- **ADR-0010** — records RFC-0020's six decisions (normative `reference.md`,
  template-on-demand not a seed, population by repo context, Class-3 harvest);
  this plan implements them.
- **ADR-0009** — records that the LLD reads `reference.md` when present; this
  spec ships the producer of what that consumer reads.
- **RFC-0019** — ships the consumer (`new-spec`/`plan.md` Shape/Stack
  derivation). **Not modified here.**
- **CHARTER Principle 1** (universality) — core stays stack-neutral; stack
  specifics live only in opt-in packs or the adopter's filled instance.
- **Repo self-hosting convention** — edit pack source, then `make build-self`;
  `docs/CONVENTIONS.md` projects from `packs/core/seeds/docs/CONVENTIONS.md`.

## Construction tests

Most tests live per-task below. Cross-cutting:

**Integration tests:** the two-producer collision test (T2) drives the bundler's
multi-pack `_project_seeds` projection end-to-end, not a single function — it is
the executable proof of the stack-pack contract and the no-pre-placed-seed
invariant together.
**Manual verification:** none beyond per-task gates — there is no runtime
surface; behavior is template/prose/convention verified by presence checks,
grep invariants, and lints.

## Design (LLD)

Shape is **mixed**; pruned to the three sub-sections this work spans. No
acceptance criterion lives here — each sub-section traces to the AC(s) it serves.

### Design decisions

- **Template homed at `packs/core/.apm/skills/adapt-to-project/assets/reference.md`.**
  The only projectable asset path is `.apm/skills/<skill>/assets/`; a non-placed
  template can't be a seed, so it lives under a skill, and `adapt-to-project` is
  the sole *in-scope* producing skill. *Rejected:* a core seed (D3 — guaranteed
  collision); a new dedicated skill (D5 — extend, don't add); `new-spec/assets/`
  (new-spec *consumes* `reference.md`, hosting the producer-template under the
  consumer is backwards). RFC-0021's `init-project` and stack-pack authors
  reference the same template path (forward consumers). *Traces to:* AC1, AC3.
- **arc42 four sections only** (§2 Constraints, §4 Solution strategy, §5
  Building-block view/component catalogue, §8 Crosscutting concepts) — *rejected*
  C4 (visualization, not a normative-standards vocabulary) and invented headings
  (D2). *Traces to:* AC1.
- **Stack pack ships a filled `reference.md` as an ordinary seed**; rely on the
  existing `_project_seeds` collision `ValueError` (self-host) / `.upstream`
  companion (install) — **no override field** (D3/D6 §Delivery). The sole-producer
  case has nothing to collide against; the two-producer case routes through
  `.upstream` + `adapt-to-project` merge. *Traces to:* AC5, AC6.
- **Harvest is a Class-3 extension**, propose-and-confirm, repo-scope path-jail,
  mirroring the "Contract relocation" precedent — no new skill (D5). *Traces to:*
  AC4.

### Component / module decomposition

- **New:** `packs/core/.apm/skills/adapt-to-project/assets/reference.md` (the
  arc42 template — creates the skill's first `assets/` dir).
- **New:** a regression test under the `agentbundle` integration test root
  (two-producer collision guard).
- **New:** four files under `docs/guides/<quadrant>/` (this repo's own guides).
- **Modified:** `packs/core/.apm/skills/adapt-to-project/SKILL.md` (a
  reference-architecture harvest subsection under Class-3).
- **Modified:** `packs/core/seeds/docs/CONVENTIONS.md` (the document-hierarchy
  diagram + the matching projection `docs/CONVENTIONS.md` via build-self).

### Dependencies & integration

- **Consumes:** RFC-0019's `new-spec`/`plan.md` templates already read
  `reference.md` — unchanged here.
- **Integrates with:** `self_host.py` `_project_seeds` (collision), `commands/_common.py`
  (`.upstream`), and `make build-self` (skill-asset + CONVENTIONS projection).
- **Future consumer (out of scope):** RFC-0021 `init-project` reads the same
  template for greenfield authoring.

> **Rollout & deployment** — see [`## Rollout`](#rollout). No runtime, no infra,
> no data migration.

## Tasks

### T1: arc42 `reference.md` template asset exists, stack-neutral, and projects

**Depends on:** none

**Touches:** `packs/core/.apm/skills/adapt-to-project/assets/reference.md`, `.claude/skills/adapt-to-project/assets/reference.md`

**Tests:** *(goal-based — AC1, AC2, AC3, adopter-clean AC)*
- grep asserts all four arc42 section headings present (Constraints / Solution
  strategy / Building-block view / Crosscutting concepts).
- grep-absence over a representative framework-token set → stack-neutral
  invariant holds. Use **collision-resistant** tokens (`react`, `spring`,
  `django`, `fastapi`, `express.js`, `postgresql`) with word-boundary anchoring,
  not bare English-colliding stems like `express` (would fire on "expressed").
- grep-absence over the template body for `RFC-NNNN` / `ADR-NNNN` tokens and
  `docs/(specs|rfc|adr)/` path strings → the adopter-clean invariant (the asset
  ships to every core adopter; no existing lint scans `.apm/`).
- the template carries the "fill only when there are real architecture decisions"
  guidance line.
- `make build-self` succeeds and `.claude/skills/adapt-to-project/assets/reference.md`
  is byte-identical to source; `git status` shows no unexpected projection revert.
- assert `packs/core/seeds/docs/architecture/reference.md` does NOT exist (the
  build-self-succeeds-without-it half of AC3; the **canonical** contract-binding
  copy of this absence assertion lives in T2, where it pairs with the collision
  guard — the duplication here is deliberate, covering AC3's projection check).

**Approach:**
- Author `packs/core/.apm/skills/adapt-to-project/assets/reference.md`: a brief
  preamble (what this is, that it's normative steering an LLD conforms to, filled
  only on real decisions), then the four arc42 sections with stack-neutral
  placeholder guidance under each. No framework names; no RFC number in the file
  body if it would trip `lint-seeds` (it's a skill asset, not a seed, but keep it
  generic regardless).
- `make build-self`; verify projection + clean `git status`.

**Done when:** template present in source and projection, all grep checks green,
build-self clean.

### T2: stack-pack delivery contract pinned by a two-producer collision test

**Depends on:** none

**Touches:** `packages/agentbundle/agentbundle/build/tests/` (or the integration test root)

**Tests:** *(goal-based, integration — the characterization AC)*
- a pytest stages two temp packs each with `seeds/docs/architecture/reference.md`
  of differing content and asserts `_project_seeds` raises the collision
  `ValueError` with the expected message shape.
- assert no `packs/core/seeds/docs/architecture/reference.md` exists (the
  no-pre-placed-seed precondition that makes the sole-producer case collision-free).

**Approach:**
- This is a **characterization** test of behavior that *already ships*
  (`self_host.py` `_project_seeds`, L457-463 — this PR changes nothing about the
  bundler). The *generic* collision mechanism is already proven by the existing
  `test_collision_with_different_content_raises` (`test_self_host_check.py:938`,
  staged on `AGENTS.md`), and the collision branch is path-agnostic — so a
  reference.md-named test asserts the same production path. It earns its place as
  **living documentation of the stack-pack contract**: a contract-labelled,
  path-named guard so that any *future* special-casing of
  `docs/architecture/reference.md` (e.g. the pack-override the contract forbids)
  trips a test that names the contract, not a generic one — and it co-asserts the
  no-pre-placed-seed precondition, binding the sole-producer-is-collision-free
  guarantee in the same test. It pins the guarantee the contract leans on; it
  does **not** cover the *documented* convention — that prose is verified by the
  presence check in the T5 reference guide. The two ACs are not satisfied by this
  one test.
- Add the test next to the existing `_project_seeds`/self-host tests (grep both
  `agentbundle` test roots for the current home — it is
  `test_self_host_check.py` `SeedProjectionTests`).
- Capture the actual `ValueError` message bytes from a real invocation rather
  than reconstructing it.

**Done when:** the collision test is green and the absence assertion holds.

### T3: `adapt-to-project` documents the Class-3 reference-architecture harvest

**Depends on:** T1

**Touches:** `packs/core/.apm/skills/adapt-to-project/SKILL.md`, `.claude/skills/adapt-to-project/SKILL.md`

**Tests:** *(goal-based — AC4, adopter-clean AC)*
- a self-test (presence check) asserts SKILL.md documents the harvest: detect
  stack + reusable components + recurring patterns → instantiate the T1 template
  → propose a draft at `docs/architecture/reference.md` → repo-scope path-jail →
  per-finding accept/edit/decline, never authoritative pre-confirmation.
- grep-absence over the new harvest subsection for `RFC-NNNN` / `ADR-NNNN` and
  `docs/(specs|rfc|adr)/` paths → adopter-clean (SKILL.md ships to adopters).
- `lint-packs` AND `lint-agent-artifacts` both pass (two lint surfaces); any
  frontmatter-length / `: `-in-description lints stay green.

**Approach:**
- Add a "Reference-architecture harvest" subsection under Class-3 in SKILL.md,
  mirroring the "Contract relocation" propose-and-confirm shape (repo-scope,
  no cross-scope move — `reference.md` is a repo artifact).
- Point it at the T1 template asset path; state it instantiates then proposes,
  never overwrites an existing authoritative `reference.md` without the confirm
  gate.
- `make build-self`; run both lint surfaces by hand.

**Done when:** the SKILL.md subsection is present and projected, the self-test is
green, and both lint surfaces pass.

### T4: CONVENTIONS document-hierarchy diagram seats `reference.md`

**Depends on:** none

**Touches:** `packs/core/seeds/docs/CONVENTIONS.md`, `docs/CONVENTIONS.md`

**Tests:** *(goal-based — AC7, adopter-clean AC)*
- grep the seed shows `reference.md` under the `architecture/` node, glossed as
  the **normative** sibling of the **descriptive** `overview.md`.
- `make build-self` projects the edit to `docs/CONVENTIONS.md`; the
  **projection-parity check** (`make build-check` / `agentbundle.build check`)
  is green; no `RFC-NNNN` / `ADR-NNNN` token in **the diagram lines this task
  adds** (scope the grep to the edit hunk — CONVENTIONS.md legitimately names
  `docs/specs|rfc|adr` and cites RFC/ADR numbers elsewhere, so a whole-file scan
  would falsely fail; lint-seeds catches RFC, the adopter-clean grep additionally
  covers ADR + paths in the new lines).

**Approach:**
- The diagram's `architecture/` node today carries no file list (unlike the
  `product/` box). Edit it in `packs/core/seeds/docs/CONVENTIONS.md` to enumerate
  both `overview.md` (descriptive map) and `reference.md` (normative golden path)
  as the node's children — adding the first child listing under that node — with
  a one-line gloss on the descriptive/normative split.
- `make build-self`; confirm projection + drift gate.

**Done when:** the diagram shows both docs distinctly in source and projection,
and the projection-parity check is green.

### T5: user guides for `reference.md`

**Depends on:** T1, T2, T3, T4

**Touches:** `docs/guides/tutorials/`, `docs/guides/how-to/`, `docs/guides/explanation/`, `docs/guides/reference/`

**Tests:** *(goal-based — the user-guides AC; the documentation half of the
stack-pack-contract AC; adopter-clean AC)*
- four files exist at the correct `docs/guides/<quadrant>/<slug>.md` paths.
- a **task-local self-test** greps each guide's `](relative/path)` targets and
  asserts every intra-repo target resolves on disk. (No repo-wide markdown-link
  or guide-frontmatter gate exists, so this task ships its own goal-based
  link-resolution grep — not a new shared linter. `tools/lint-agents-md.py`'s
  Diátaxis check only asserts the quadrant dirs exist, so it is a no-op coverage
  source here. `new-guide` supplies the audience-contract front matter.)
- grep-absence over the four guides for `RFC-NNNN` / `ADR-NNNN` and
  `docs/(specs|rfc|adr)/` paths → adopter-clean.
- a presence check confirms the **reference** guide states all four stack-pack
  contract clauses (sole-producer / two-producer `.upstream`-merge / never
  `overview.md` / no override field) — the documentation coverage for the
  stack-pack-contract AC.

**Approach:**
- These guides are this repo's own `docs/guides/` content (repo-owned, not
  projected to adopters), authored via the `user-guide-diataxis` pack's
  `new-guide` skill — not part of what `core` ships.
- Invoke `new-guide` per quadrant (it settles each guide's audience contract):
  - *Tutorial* — "Create and use your `reference.md`" (establish it via harvest
    / stack-pack pre-bake, then use it — how a design conforms, references
    components/stereotypes by name, and how the LLD reads it as steering).
  - *How-to* — "Establish your repo's reference architecture" (brownfield
    harvest / stack-pack pre-bake). A greenfield path (an `init-project` skill
    that writes the first `reference.md` at project bootstrap) is **not yet
    available** — name it honestly in plain prose as planned-not-shipped, with
    **no** proposal/RFC number and no implication it ships today (adopter-clean
    AC; the consumer this guide describes must not leak internal references).
  - *Explanation* — "Foundation vs. map" (why `reference.md` is normative
    steering and `overview.md` is descriptive; why template-instantiated, not
    seeded).
  - *Reference* — the `reference.md` arc42 sections + the stack-pack contract.
- Author against the finished T1–T4 behavior so the guides are accurate.

**Done when:** the four guides exist at the correct paths, the relative-link
check passes, and the reference guide states all four stack-pack contract clauses.

## Rollout

- **Delivery:** ships with the `core` pack; for this repo, realized by `make
  build-self`; adopters get the template + harvest on their next install/update.
  Fully reversible — revert the PR; nothing irreversible (no data migration, no
  published event).
- **Infrastructure:** none.
- **External-system integration:** none.
- **Deployment sequencing:** T1 (template) before T3 (harvest references it) and
  before T5 (guides describe it); T2 and T4 are independent; T5 last so guides
  describe the finished mechanism. No schema/migration ordering.

## Risks

- **build-self reverts a projection-only edit.** A prior PR that edited only a
  projected path can be silently undone on `make build-self`. *Mitigation:* edit
  source only; check `git status` after every build for unexpected reverts and
  close any drift in-PR.
- **Two lint surfaces, one local gate.** `make build-check` runs `lint-packs`
  (source); CI also runs `lint-agent-artifacts` (projection). *Mitigation:* run
  both by hand on the SKILL.md and template changes (T1, T3).
- **`lint-seeds` forbids RFC numbers in seeds.** The CONVENTIONS seed edit (T4)
  and any seed-shaped content must not embed `RFC-0020`. *Mitigation:* keep the
  diagram gloss generic; cite RFC-0020 only in this spec/plan and the ADR.
- **Skill frontmatter parser limits.** SKILL.md additions (T3) must keep
  frontmatter within the documented cap and avoid unquoted `: ` in the
  description. *Mitigation:* the harvest content is body prose, not frontmatter;
  verify the description line is untouched.
- **ADR recorded.** RFC-0020 §Follow-on's ADR is recorded as **ADR-0010**
  (Status: Accepted), landing in this same PR — the governance trail is closed.

## Changelog

- 2026-06-01: initial plan.
- 2026-06-01: pre-EXECUTE review amendments. (1) Encoded the user's
  adopter-clean constraint as a new acceptance criterion plus a per-task
  grep-absence test (T1/T3/T4/T5) — no `RFC-NNNN`/`ADR-NNNN` token or
  `docs/(specs|rfc|adr)/` path in any adopter-facing created/edited file;
  `lint-seeds` covers only RFC numbers under `seeds/`, so the `.apm/` template,
  the SKILL.md harvest, and the guides need the explicit grep. (2) Reworded the
  T5 how-to to name the greenfield/`init-project` path as planned-not-shipped in
  plain prose, dropping the `RFC-0021` citation (the citation was itself the
  leak; `init-project` does not exist yet). (3) Reframed T2 as living
  documentation of the stack-pack contract — the generic collision mechanism is
  already covered by `test_collision_with_different_content_raises`, so the
  reference.md-named test is a contract-labelled regression guard paired with the
  no-pre-placed-seed precondition, not a duplicate. (4) Noted the CONVENTIONS
  `architecture/` node has no child listing today (T4 adds both `overview.md`
  and `reference.md`), pinned the `_project_seeds` collision citation to
  L457-463, and downgraded the `lint-agents-md` Diátaxis citation to a non-coverage
  guard.
