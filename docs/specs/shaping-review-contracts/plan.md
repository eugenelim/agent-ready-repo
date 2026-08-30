# Plan: Shaping review contracts

- **Spec:** [`spec.md`](spec.md)
- **Status:** Done
- **Repository anchors:** `ARCHITECTURE.md`,
  `docs/architecture/skill-and-pack-format.md`, and
  `docs/architecture/pack-layout.md`; analogous
  `docs/specs/architect-design-reviewer/` and
  `docs/specs/project-knowledge-review-integrations/`; current owners
  `packs/core/.apm/agents/adversarial-reviewer.md`,
  `packs/core/.apm/skills/new-spec/SKILL.md`, and
  `packages/agentbundle/agentbundle/catalogue_tooling/verify.py`. Deviation:
  Core MCP is another invocation route to caller skills, not a knowledge
  surface, so reviewer grounding uses installed skills, repository content,
  and a supplied evidence packet rather than a new projected retrieval tool.

> **Plan contract:** this is the implementation strategy. It may change while
> Drafting or Executing; the approved baseline is immutable after sealing.

## Approach

First make least-privilege agent boundary metadata a validated source contract
and prove its semantic adapter projections. Then add one read-only reviewer with
three explicit rubrics. Integrate it at each lifecycle owner after the canonical
intent/brief surfaces exist, and split spec-contract checks from later
adversarial plan/conformance checks without moving any delivery state.

The implementation reuses ordinary agent discovery and existing caller
dispatch. It adds no review script, state file, retrieval protocol, generic
loop, public review skill, or shared mode framework.

## Constraints

- RFC-0099, including all 2026-08-27 Errata, is normative.
- ADR-0042's distinct-work-type, unique-value, cadence, and
  collision-hardening test remains authoritative.
- `core-guidance-artifact-routing` creates `intake-intent` and
  `author-delivery-brief` before their integrations land.
- Workspace dependency resolution blocks plan approval until
  `core-guidance-artifact-routing` is Shipped; the executable task graph uses
  local task IDs only.
- Source metadata may map to native adapter restrictions; adapters need not
  preserve an opaque literal field when their effective permissions are tested.
- Plan tasks name exact implementation seams only when repository evidence
  establishes them; otherwise they pin the discovery predicate, constraint,
  required outcome, and verification mode named by AC7, which is the canonical
  home for that rule, without guessing a path or symbol.
- Shaping review remains outside work-loop state, finding adjudication,
  review-verdict records, and code review.
- No independent retrieval/network capability, dependency, or new public skill
  is added. The Codex read-only-sandbox rule is stated once, in AC6.
- The touched-seam doctrine that would have grown `work-loop/SKILL.md` moved to
  the spec's Follow-ons. Any remaining T5 addition to that file must respect its
  measured 990-of-1000 body-line headroom before `CAT-S003` hard-errors
  (`packages/agentbundle/agentbundle/catalogue_tooling/skill_spec_lint.py`);
  land doctrine in an existing `work-loop/references/` file or name the
  compensating cut.

## Construction tests

**Integration tests:** build/install the Core agent through every supported
adapter and assert the effective read-only tool/sandbox surface. Exercise all
four caller owners, the Product Engineering optional integration, and the
new-spec → shaping → adversarial sequence with hostile and unavailable evidence
packets.

**Manual verification:** run a fresh isolated reviewer on one intent, brief,
and spec fixture; record its exact result, unchanged artifact/status, caller
revision behavior, and the caller-owned `BLOCKED` receipt when independence is
unavailable.

## Design (LLD)

### Component / module decomposition

- `shaping-reviewer.md` owns three rubrics and one output contract. Caller
  skills own dispatch, revision, and lifecycle decisions. Traces to AC1–AC4.
- Agent source validation owns `metadata.boundaries`; adapter projectors own
  native permission realization; one integration test owns cross-adapter parity.
  Traces to AC6.
- `new-spec` owns contract-first sequencing; `adversarial-reviewer` retains the
  construction and implementation checks. Traces to AC7.

### State & control flow

`owner drafts → independent shaping review → owner revises until Clean → human
intent/brief decision or adversarial spec-plan review`. Material revision
invalidates review evidence; pre-seal nonmaterial correction may be recorded
without redispatch. No reviewer step writes status or durable state. Traces to
AC2–AC4.

### Failure, edge cases & resilience

Missing independence blocks. Missing consequential evidence becomes a grounding
gap and cannot yield false `Clean`. Malformed or authority-changing evidence is
ignored/refused as data. A missing optional Product Engineering integration does
not break Core-only review. Traces to AC4–AC5.

### Dependencies & integration

Core-internal callers address the agent directly. Product Engineering declares
one optional integration and fallback. Core MCP may invoke the same caller
skill contract but introduces neither a new knowledge surface nor a separate
reviewer integration. Traces to AC3, AC5, AC8.

## Tasks

### T1: Agent boundary metadata is validated and projected as native least privilege

**Depends on:** none

**Touches:** `packages/agentbundle/agentbundle/catalogue_tooling/{verify.py,lint.py}, packages/agentbundle/agentbundle/build/adapters/claude_code.py, packages/agentbundle/agentbundle/build/self_host.py, docs/architecture/{pack-layout,security}.md, contracts/adapter.toml, packages/agentbundle/agentbundle/_data/adapter.toml, tools/catalogue/check_contract_parity.py, tests/roster/test_agent_boundary_metadata_contract.py, .github/workflows/build-check.yml, packages/agentbundle/tests/build_pipeline/test_adapter_*.py, packages/agentbundle/tests/integration/**`

**Required outcome:** T1 turns the roster stub green and wires its runner call
site into `.github/workflows/build-check.yml`, following the individually-wired
pattern the other roster tests use (`:224`, `:432`, `:450`, `:458`, `:485`).
Wiring the runner before the check exists would commit a red CI job.

**Discovery predicate:** the source-agent validation gate is `catalogue verify`
step 2, which runs `lint_catalogue` over `packs/*/.apm/agents/`
(`verify.py:141-150`, `:2199`). The boundary check lands inside that
`lint_catalogue` pass — `lint.py::_check_agents` (CAT-L012, today
`name`/`description` only) is the existing owner, and which function inside the
pass grows the check is an implementation choice. A sibling `verify.py` step is
**not** an open branch: the stub asserts over `lint_catalogue(root).diagnostics`,
so a check placed outside that pass could never turn it green.

**Tests:**
- `stub: true` — `tests/roster/test_agent_boundary_metadata_contract.py`
  (`STUB: AC6`). Four assertions against the `lint_catalogue` pass that
  `catalogue verify` step 2 already runs over the pack tree: a valid read-only
  declaration is accepted, and an unknown boundary value, a non-list
  `boundaries`, and a declaration widened past the agent's tools each produce a
  diagnostic. The accept case passes today; the three rejection cases are red.
  The stub asserting `packs/core/.apm/agents/shaping-reviewer.md` belongs to T2,
  which creates that file.
- **Stub placement is deliberate.** The stub is repo-only, not under
  `packages/agentbundle/tests/`, because `MANIFEST.in` grafts that tree into the
  sdist and `tools/check-artifact-contents.py` re-runs it whole, raising
  `ArtifactViolation` on any non-zero exit with no deselection hook; a red module
  there would redden `gate-export-boundary`, `build-and-smoke`, and
  `make build-check` before EXECUTE starts. Until T1 lands, callers deselect it
  by exact node id as a future-behaviour exclusion.
- TDD: verifier accepts the bounded metadata schema and rejects unknown,
  malformed, missing-required, or widened boundary declarations (AC6).
- Goal-based: all supported adapter projections expose only native read/search
  or a coarse read-only sandbox; Codex's command tool can perform bounded reads
  but not project execution, write, network, credential, MCP, skill, or
  recursive-dispatch actions. kiro-ide and kiro-cli are included, and each
  asserts the injected `skill://` resource glob is suppressed.
- TDD/integration: discover every Claude Code direct-file agent consumer from
  the adapter contract and the self-host recipe; the smallest shared projection
  seam strips source-only `metadata` so no unrecognised key reaches
  `.claude/agents/`, and built/install/self-host outputs preserve the effective
  read-only tool contract. Source-side validation, not the projected artifact,
  is where `metadata.boundaries` is checked.
- Goal-based: the owning security convention defines boundary metadata for
  skills, agents, and compatibility aliases; contract-parity verification
  proves the source and packaged adapter twins remain identical.

**Approach:**
- Admit only the metadata structure needed by agent boundaries; do not add a
  generic opaque metadata passthrough.
- Assert effective native restrictions per adapter rather than force identical
  syntax into incompatible targets.
- The adapter contract is unchanged: boundary metadata is source-only and needs
  no new projector capability, so neither `contracts/adapter.toml` nor its
  packaged twin gains a numbered version entry or a `[contract] version` bump.
- Validate `metadata.boundaries` where the declaration lives — on the source
  agent under `packs/*/.apm/agents/` — rather than on the projected
  `.claude/agents/` artifact, which the seam above strips.

**Done when:** catalogue verification accepts and validates a source agent's
`metadata.boundaries`, rejects a widened or malformed declaration, no projected
adapter artifact carries the source-only key, and every supported adapter's
projection of an existing read-only core agent asserts its equivalent native
restriction — all provable before `shaping-reviewer.md` exists.

### T2: `shaping-reviewer` implements three cold, stateless rubrics

**Depends on:** T1

**Touches:** `packs/core/.apm/agents/shaping-reviewer.md, packs/core/tests/pack/test_shaping_review_contract.py`

**Tests:**
- `stub: true` — `packs/core/tests/pack/test_shaping_review_contract.py`
  (`STUB: AC6`). This task creates the agent the stub asserts, so the stub is
  declared here. Plus three recorded fresh-context fixture reports.
- Goal-based construction tests pin exact modes, fields, materiality, result
  vocabulary, caller-owned evidence, prohibited authority, lack of loop
  machinery, exact agent name/description cue including `not code review`, and
  roster collision hardening (AC1–AC6).
- Visual/manual QA: fresh reviewer runs on seeded intent/brief/spec and hostile
  evidence fixtures produce the expected findings or grounding gaps.

**Approach:**
- Author one agent with compact per-mode sections and one shared output/trust
  boundary.
- Use exact read-only tools and source boundary metadata proven by T1.

**Done when:** all three fixtures return complete review evidence and the
repository/status remain byte-identical.

### T3: Core intent and brief lifecycle owners receive shaping findings

**Depends on:** T2

**Touches:** `packs/core/.apm/skills/intake-intent/**, packs/core/.apm/skills/author-delivery-brief/**, packs/core/tests/skills/{intake-intent,author-delivery-brief}/**, guides/core/**`

**Tests:**
- `no stub (goal-based)` — caller behavior/eval fixtures under
  `packs/core/tests/skills/{intake-intent,author-delivery-brief}/`.
- Goal-based: clean/findings, material revision, nonmaterial correction, alias
  non-dispatch, human status confirmation, and unavailable independence cover
  AC2–AC5.
- Goal-based: changed skills declare the exact dispatch/read/write boundaries
  and no Bash/network capability.

**Approach:**
- Add direct lifecycle-owned dispatch and finding-revision steps to the two
  canonical skills.
- Keep compatibility aliases unaware of reviewer mechanics.
- Ship the intent/brief shaping-review guide delta with these callers.

**Done when:** neither intent nor brief can advance without independent clean
evidence and the existing human decision.

### T4: `frame-intent` uses the optional Core reviewer without losing user-scope operation

**Depends on:** T2

**Touches:** `packs/product-engineering/.apm/skills/frame-intent/**, packs/product-engineering/pack.toml, packs/product-engineering/tests/pack/**, guides/product-engineering/**`

**Constraint:** the fixtures land under the already-registered
`packs/product-engineering/tests/pack/`, the pack's only runner call site
(`Makefile:454`, `.github/workflows/build-check.yml:372`). A new
`tests/skills/` directory would be an unrunnered suite dir and fail
`tools/lint-pack-test-boundary.py`'s `every-suite-dir-has-a-runner` check, since
`_NO_RUNNER` holds no `product-engineering` entry. Reusing the registered
directory keeps `Makefile` and the workflow out of this slice.

**Tests:**
- `no stub (goal-based/manual QA)` — frame-intent integration fixtures and one
  recorded Core-absent run.
- Goal-based: integration metadata names Core's reviewer, trigger, and
  fresh-context/independent-human fallback (AC4, AC8).
- Goal-based/eval: with Core present, fixtures exercise independent intent-mode
  invocation, `Clean`, `Findings`, unresolved-finding blocking, and
  caller-retained lifecycle authority (AC3–AC4).
- Goal-based: the same fixture set asserts `frame-intent` allowed tools,
  `metadata.boundaries`, and native projection posture (AC6).
- Visual/manual QA: user-scope Product Engineering without Core reports the
  unavailable optional augmentation honestly and never marks itself clean.

**Approach:**
- Add one optional integration; keep product-intent authorship in place and
  repository admission outside `frame-intent`.
- Ship the optional-integration and fallback guide delta with the caller.

**Done when:** product intents receive the same gate when Core is present and
remain authorable without pretending review occurred when it is absent.

### T5: `new-spec` runs shaping review before the preserved adversarial spec-plan gate

**Depends on:** T2

**Touches:** `packs/core/.apm/skills/new-spec/{SKILL.md,assets/plan.md}, packs/core/.apm/agents/adversarial-reviewer.md, packs/core/.apm/skills/work-loop/references/{pre-execute-review,tdd-stubs}.md, packs/core/tests/skills/new-spec/test_shaping_review.py, packs/core/tests/pack/{test_review_depth_and_verdict_contract.py,test_shaping_review_contract.py}, guides/_shared/explanation/the-three-loops.md`

**Tests:**
- `no stub (goal-based)` — exact content/construction fixtures in the two named
  test files.
- Goal-based: exact gate order, caller-owned `BLOCKED` refusal, atomic ACs,
  universal-scope proof, grounded/discovery-shaped plan detail, build-finding
  routing, and all ownership-split fixtures cover AC3, AC4, AC7.
- Goal-based: planning-sufficiency fixtures distinguish a blocking contract gap
  from nonblocking helper, symbol, fixture-internal, and edge-matrix questions;
  reviewers cannot turn build-time guidance into a pre-EXECUTE blocker.
- Goal-based: representative red stubs and `no stub
  (implementation-discovered)` tasks cover both grounded and discovery-shaped
  seams without claiming the PLAN artifact is the finished test suite.
- Goal-based: adversarial review retains every plan/conformance check and gains
  no duplicate product-meaning verdict.
- Goal-based: a dual-target ownership row passes when each reviewer applies it
  to its own target, and a row with no owning reviewer fails.
- Goal-based: every changed skill/agent surface pins its tools,
  `metadata.boundaries`, and native projection posture (AC6).
- Goal-based: `new-spec`'s existing `adversarial-reviewer` absence note and the
  Profile-A opt-out are unchanged; only an unresolved shaping finding blocks
  indexing.
- Goal-based: a material edit to a spec that already holds a shaping `Clean`
  invalidates that result and forces redispatch before adversarial review; a
  correction the lifecycle owner records as nonmaterial retains it (AC2).

**Approach:**
- Insert shaping review after draft contract creation and before complete-pair
  adversarial review.
- Remove only the contract-shape slice from adversarial ownership and keep its
  later work-loop cadence unchanged.
- Replace mandatory guessed specificity with grounded exact seams or an
  explicit discovery predicate; add no AC word-count gate.
- Amend the TDD-stub doctrine and pre-EXECUTE reviewer rubric at their current
  owners so Clean measures planning-level viability rather than implementation
  completeness.
- Ship the spec-review and three-loops guide delta with this task.

**Done when:** a spec cannot reach approval through shaping alone and both
reviewers find exactly their seeded defects.

### T6: Guides, evals, releases, and projections close the shaping-review slice

**Depends on:** T3, T4, T5

**Touches:** `packs/{core,product-engineering}/{README.md,JOURNEY.md,pack.toml,.claude-plugin/plugin.json}, packs/core/DESIGN.md, packs/core/docs/index.md, packs/core/seeds/docs/CONVENTIONS.md, docs/CONVENTIONS.md, packages/agentbundle/{CHANGELOG.md,pyproject.toml,agentbundle/version.py}, guides/core/**, guides/product-engineering/**, guides/_shared/explanation/the-three-loops.md, docs/product/changelog.md`

**Tests:**
- `no stub (goal-based/manual QA)` — aggregate guide, eval, catalogue, adapter,
  build, and installed-profile evidence.
- Goal-based: each of the eight documents AC8 enumerates distinguishes shaping
  review from the three code-review lenses, and scaffold sync regenerates root
  `docs/CONVENTIONS.md` from the Core seed with a clean source/target check. The
  assertion runs over that enumeration; no search predicate stands behind AC8.
- Goal-based: caller evals, pack tests, guide/site checks, catalogue
  lint/verify, pack and AgentBundle version parity, all-adapter integration,
  release/changelog evidence, and build/self-host checks cover AC8.
- Visual/manual QA: built Core-only and Product Engineering configurations
  demonstrate isolated-agent and fallback paths.

**Approach:**
- Update existing guides and pack summaries; add no review guide family.
- Keep only cross-cutting navigation, link, release, and projection work here;
  capability-specific guidance ships in T3–T5.
- Bump only changed packs/packages and regenerate owned projections.

**Done when:** AC1–AC8 are green across every supported adapter and guide path.

## Rollout

Land boundary-schema support before the new agent source, then land caller
integrations after their canonical skills exist. Core callers may ship together;
Product Engineering remains an optional integration. Rollback removes caller
dispatch first, then the agent, while leaving the backward-compatible metadata
validator harmless. No persistent shaping state or data migration exists.

## Risks

- A generic metadata passthrough would create an undocumented adapter API;
  validate the smallest boundary schema and test effective permissions.
- Reviewer/caller prose can duplicate the same rubric; keep artifact questions
  in the agent and lifecycle/status behavior in callers.
- Moving too many adversarial checks weakens delivery review; the seeded
  ownership matrix is a release gate.
- Treating Core MCP as a knowledge provider would invent a second surface;
  caller-supplied evidence and the accepted Errata prohibit it.

## Changelog

- 2026-08-27: initial plan from accepted RFC-0099 and its MCP Errata; kept
  knowledge on installed skills and repository content, and declined a public
  review skill, durable review state, and a fourth mode.
- 2026-08-28: revised from twelve adjudicated pre-EXECUTE findings before any
  code. Moved the `stub: true` declaration from T1 to T2, which creates the
  agent the stub asserts, and rescoped T1's `Done when` to the surface T1
  actually delivers. Corrected the PLAN-time stub: it forbade the literal
  `skills:`, but kiro-ide and kiro-cli inject a `skill://**/SKILL.md` resource
  glob into every projected agent unless the source declares `skills: []`, so
  the stub as written would have shipped the reviewer with reach to every
  installed skill on two adapters — measured by projecting a synthetic agent
  both ways. Both kiro adapters now carry a suppression assertion. Recorded the
  adapter contract as unchanged. Restored the four-element discovery-predicate
  rule and pointed the Codex sandbox statement at its single canonical home in
  AC6. Added the `work-loop/SKILL.md` 990-of-1000 line-budget constraint.
  Briefly deviated from the original T1 test bullet by proposing that `metadata`
  be admitted as an agent frontmatter key instead of stripped, on the analogy
  with `skills`. **Reverted the same day.** Adjudicated review sustained that
  the analogy was unsourced, and the canonical Claude Code subagent
  documentation settles it: the recognised field set is `name`, `description`,
  `tools`, `disallowedTools`, `model`, `permissionMode`, `maxTurns`, `skills`,
  `mcpServers`, `hooks`, `memory`, `background`, `effort`, `isolation`, `color`
  (https://code.claude.com/docs/en/sub-agents.md; plugin agents take a documented
  subset). `skills` is genuinely a Claude Code field — which is why the stub
  correction above is portable — and `metadata` is not on the list, while the
  documentation is silent on how unknown subagent keys are handled. Shipping an
  unrecognised key into every adopter's `.claude/agents/` on unspecified
  behaviour is not worth avoiding one projection edit, so T1 keeps the approved
  strip-at-the-seam approach and validates the declaration at its source.
- 2026-08-28 (round 4): three further adjudicated findings, three refuted. Moved
  T1's red stub out of `packages/agentbundle/tests/` to `tests/roster/`:
  `MANIFEST.in` grafts that tree into the sdist and
  `tools/check-artifact-contents.py` re-runs it whole with no deselection hook,
  so a red module there would have reddened `gate-export-boundary`,
  `build-and-smoke`, and `make build-check` before EXECUTE began. T1 now owns
  wiring the roster runner call site once the check is green. Replaced T6's AC8
  search bullet with an assertion over AC8's eight enumerated paths — round 3
  deleted that predicate from the spec but left it in the plan. Removed the false
  `verify.py`-step alternative from T1's discovery predicate: the stub asserts
  over `lint_catalogue`, so that branch could never turn it green.
- 2026-08-28 (round 3): five further adjudicated findings, six refuted. Closed
  AC8's document set on its explicit enumeration and deleted the search
  predicate that did not reproduce it; corrected the false claim that
  `the-three-loops.md` names no lens (line 74 names all three). Added ADR-0099
  to `Constrained by:`. Dropped the `[pack.evals]` absence clause, which no
  agent could ever falsify. Gave T1 the compilable red stub AC7 requires —
  adjudication established the seam *is* grounded, so a discovery predicate was
  the wrong disposition. Split the last three grafted items.
- 2026-08-28 (round 2): ten further adjudicated findings. Re-ran the AC8 lens
  search — the closed set is seven Core documents, not four, and
  `the-three-loops.md` is not among them because it names no lens; added
  `packs/core/DESIGN.md`, `packs/core/docs/index.md`, and the
  `seeds/docs/CONVENTIONS.md` → `docs/CONVENTIONS.md` scaffold-sync pair to T6.
  Moved T4's fixtures into the already-registered
  `packs/product-engineering/tests/pack/` so no unrunnered suite dir is created.
  Added the missing spec-path materiality fixture to T5. Added core-only
  viability to AC1's intent rubric, which RFC-0099 § 5 enumerates. Aligned the
  Testing Strategy's TDD and Goal-based lines with the per-task modes and added
  the stub tally the TDD-stub convention requires. Dropped the Core MCP
  acceptance item, which no task could prove; the fact remains in the Objective
  and Assumptions. Replaced AC8's referent-free "public activation roster" with
  the two concrete artifacts. Split the remaining grafted items in AC3, AC6, and
  AC7.
