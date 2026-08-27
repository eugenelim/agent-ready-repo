# Plan: Agent Skill Engineering Foundation

- **Spec:** [`spec.md`](spec.md)
- **Status:** Executing
- **Repository anchors:** [`RFC-0097`](../../rfc/0097-agent-skill-engineering.md);
  [`ADR-0093`](../../adr/0093-okf-reference-corpora-remain-governed-build-time-sources.md);
  [`ADR-0097`](../../adr/0097-knowledge-access-capability-detected-provider-mediated.md);
  [`agent-skill-engineering` architecture](../../architecture/agent-skill-engineering.md);
  [`packs/AGENTS.md`](../../../packs/AGENTS.md);
  [`packs/architect/pack.toml`](../../../packs/architect/pack.toml) and its
  `architecture-lenses` OKF bundle as the same-pack compilation precedent;
  [`okf_compiler.py`](../../../packs/catalogue-curation/.apm/skills/compile-okf/scripts/okf_compiler.py)
  and [`test_render.py`](../../../packs/catalogue-curation/tests/skills/compile-okf/test_render.py)

> **Plan contract:** this is the implementation strategy. Unlike the spec, this
> document is allowed to change as you learn while its Status is `Drafting` or
> `Executing`. Once it is `Done` and the spec is `Shipped`, the directory
> freezes as a unit.

## Approach

Harden the shared OKF compiler before any foundation corpus depends on it, then
build the portable pack in reviewable layers: authoring workflow,
review/optimize workflow, governed corpus and generated router, provider and
language-extension integration, and finally the cross-cutting M1 release
evidence. Each layer leaves the repository buildable and proves behavior with
fixtures before relying on it downstream.

The pack follows the existing `.apm/` portable-source and same-pack OKF build
pattern. A minimal `pack.toml` is delivery metadata outside the portable
content, not a new portable contract. The provider request/response contract is
implemented as skill instructions plus shared behavioral fixtures because no
deterministic component parses a serialized envelope in this slice. If
implementation introduces such a parser, the plan stops for a spec amendment
and contract-type decision rather than adding an incidental schema.

## Constraints

- [`RFC-0097`](../../rfc/0097-agent-skill-engineering.md) fixes the M1 product
  boundary, mode availability, foundation topics, evaluation gates, and later
  slices; implementation does not reopen them.
- [`ADR-0093`](../../adr/0093-okf-reference-corpora-remain-governed-build-time-sources.md)
  keeps raw OKF a declared same-pack build-time source.
- [`ADR-0097`](../../adr/0097-knowledge-access-capability-detected-provider-mediated.md)
  requires capability detection, explicit provider mediation for independent
  OKF knowledge, external trust eligibility, least authority, and clean
  absence.
- The portable content cannot cite repository-internal governance or depend on
  AgentBundle delivery mechanisms. The external wrapper follows the existing
  pack schema without changing it.
- The two named compiler findings retain their canonical ownership in
  `workspace.toml` until implementation evidence closes them. They block corpus
  generation, not spec approval.
- No new third-party dependency, top-level directory, adapter behavior,
  projection behavior, publication path, catalogue admission rule, or
  authentication mechanism is introduced.
- Repository tests stay strict when cleanup is restricted; tests use confined
  task-local temporary roots and assert retained-state behavior instead of
  weakening the contract.

## Construction tests

Most construction tests live under **Tasks** below. Cross-cutting evidence is:

- A staged-install test builds only the foundation pack's delivered tree,
  verifies no OKF authoring source or path is present, makes the source checkout
  unavailable, and runs every router and workflow fixture with filesystem reads
  confined to that tree and a declared temporary output root (AC1, AC6, AC8,
  AC9, AC18).
- Two clean OKF builds from the same committed inputs produce byte-identical
  generated routers, indexes, references, and manifests; the repository drift
  check then confirms generated output is current (AC8, AC20).
- `tools/run-pack-evals.py` covers both user-facing workflow activation sets;
  the generated router is tested through its integration fixtures and is not
  advertised as a user-facing workflow (AC6, AC9).
- A fixture-led independent quality review checks the four M1 workflow cases
  against predeclared checklists and records a reviewed fixture change whenever
  an expected result changes (AC6).
- The standard skill lint, pack tests, catalogue deep lint/verify, documentation
  link tests, generated-projection drift checks, and proportionate repository
  build gate all pass without editing generated adapter projections directly
  (AC21, AC22).

Manual verification is limited to inspecting the independent-review evidence
and confirming that the external manifest contains delivery metadata only. No
candidate code execution is required for acceptance.

## Design (LLD)

### Design decisions

- Two user-facing skills own progressive author/update and review/optimize;
  one generated, inert router owns bounded knowledge selection. This preserves
  a small activation surface while keeping reference loading progressive (AC1,
  AC2, AC5, AC9).
- Raw authored knowledge and generated runtime knowledge remain visibly
  different trees. The compiler is the only bridge between them (AC7, AC8).
- The provider envelope remains semantic in `SKILL.md` and versioned fixtures.
  A JSON Schema would be a second source of truth without a parser in this
  slice (AC11, AC12).

### Data & schema

There is no runtime persistence or new repository-wide schema. Authored OKF
uses the existing `agentbundle-okf/v1` profile; generated files and manifest
membership use the existing compiler format. Versioned JSON evaluation
fixtures are test data, not a public serialized API. Stable topic identifiers,
provider fields, statuses, mode names, and the two language-extension family
names are the semantic vocabulary owned by the spec and exercised by those
fixtures (AC7-AC15).

### Interfaces & contracts

The user interface is the activation and progressive-mode behavior of
`author-or-update-agent-skill` and `review-or-optimize-agent-skill`. The
integration interface is the `agent-skill-engineering-reference/v1` semantic
request/response contract. Its normative fields and refusal behavior live in
spec AC11-AC13; provider and consumer skill instructions implement it, and one
shared fixture set proves both sides. There is no `contracts/jsonschema/`
artifact because no software component consumes one (AC2-AC6, AC10-AC14).

### Component / module decomposition

- `packs/agent-skill-engineering/.apm/skills/author-or-update-agent-skill/`
  owns `frame`, `create`, and `update` instructions plus workflow fixtures.
- `packs/agent-skill-engineering/.apm/skills/review-or-optimize-agent-skill/`
  owns read-only review, the explicit optimize transition, and workflow
  fixtures.
- `packs/agent-skill-engineering/okf/agent-skill-engineering/` owns the three
  raw foundation concepts and their authored index.
- `packs/agent-skill-engineering/.apm/skills/agent-skill-engineering-reference/`
  is generated and owns router-facing compiled references and provider
  behavior.
- `packs/agent-skill-engineering/tests/` owns contract, workflow, router,
  security, failure-mode, and staged-tree verification. Tests never project.
- `packs/agent-skill-engineering/pack.toml` is the minimal external build and
  catalogue wrapper; it does not own portable behavior.

These paths follow the repository's pack and OKF precedents. Exact reference
file decomposition inside a workflow remains an implementation choice as long
as progressive loading and the portable boundary hold (AC1, AC7, AC21).

### State & control flow

Authoring starts in `frame`; only an explicit user transition reaches `create`
or `update`. Review starts read-only; only an explicit user transition after
evidence reaches `optimize`. Either workflow may query the local router and may
then perform bounded capability detection. An eligible independent provider is
invoked explicitly with the v1 request; its validated guidance is treated as
untrusted input. Absence, refusal, or invalid response returns control to the
baseline workflow. Execution remains a separate user-approved transition
(AC2-AC5, AC10-AC17).

### Behavior & rules

Root-first routing narrows from index to at most three concepts; topic files
never participate in provider discovery. Language-extension requests identify
a future family but return honest absence in this slice; no language topic body
exists yet. `out-of-scope` returns no topic body. M2-only modes are omitted
from activation and answer with the stable unavailable contract when directly
requested (AC4, AC7, AC9-AC15).

### Failure, edge cases & resilience

All boundaries distinguish absence from an independently applicable safety
stop. Compiler and router errors are deterministic and confined. Provider
errors are bounded, redacted, and non-persistent; ambiguous provider selection
fails closed to baseline rather than guessing. Interrupted writes preserve or
identify recoverable state, and cleanup denial does not erase the primary test
result or lower its assertion set (AC13, AC16-AC20).

### Quality attributes (NFRs)

Determinism is byte identity across clean compiles. Router quality meets the
RFC's 90% exact-selection and three-topic thresholds over at least twenty
predeclared fixtures. Security requires no authority gain, no secret access,
same-root confinement, hostile-input refusal, and staged runtime independence
from authored OKF. Portability requires all supported projections to consume
the same `.apm/` source without adapter-specific common-floor instructions
(AC1, AC6, AC8, AC9, AC16-AC19, AC22).

### Dependencies & integration

The existing OKF compiler is the only build-time knowledge dependency. Its two
named defects close before foundation generation. Optional runtime knowledge
providers are capabilities, not dependencies: consumers are complete without
them and integrations remain disabled until external eligibility and
confinement evidence pass. AgentBundle supplies external pack delivery only;
no adapter or catalogue code enters the portable components (AC10, AC13, AC14,
AC20, AC21).

## Tasks

### T1: Both canonical OKF compiler prerequisites are closed with regression evidence

**Depends on:** none

**Touches:** `packs/catalogue-curation/.apm/skills/compile-okf/scripts/okf_compiler.py`, `packs/catalogue-curation/tests/skills/compile-okf/test_render.py`, `packs/catalogue-curation/tests/skills/compile-okf/test_apply.py`, `workspace.toml`

**Mode:** TDD

**Tests:**

- PLAN-time red stubs on the existing render and apply test surfaces
  (`test_render.py`, `test_apply.py`):

  ```python
  # STUB: AC18, AC20 — hostile display metadata is encoded and repeated render divergence refuses
  def test_okf_index_encodes_hostile_display_metadata(tmp_path: Path) -> None:
      bundle = _copy_fixture(tmp_path)
      concept = bundle / "concepts" / "hostile.md"
      concept.write_text(
          concept.read_text(encoding="utf-8").replace(
              'title: "Hostile Prompt"',
              'title: "[escape](../../outside.md)"',
          ),
          encoding="utf-8",
      )

      result = render_okf_bundle(
          bundle,
          bundle_id="rich",
          router_skill="rich-router",
          projected_concepts={"concepts/runbook.md": RUNBOOK_DIGEST},
      )

      index = result.files["references/okf/concepts/index.md"].decode("utf-8")
      assert "[escape](../../outside.md)" not in index
      assert "\\[escape\\]\\(../../outside.md\\)" in index


  def test_compile_pack_reports_okf012_without_retaining_partial_output(
      tmp_path: Path, monkeypatch: pytest.MonkeyPatch
  ) -> None:
      from dataclasses import replace

      root = _make_catalogue(tmp_path)
      before = _snapshot(root)
      real_render = okf_compiler.render_okf_bundle
      calls = 0

      def divergent_render(*args: object, **kwargs: object) -> okf_compiler.RenderResult:
          nonlocal calls
          calls += 1
          result = real_render(*args, **kwargs)
          if calls == 2:
              return replace(result, files=result.files | {"diverged": b"x"})
          return result

      monkeypatch.setattr(okf_compiler, "render_okf_bundle", divergent_render)
      result = okf_compiler.compile_pack(root, "demo", check=False)

      assert result.exit_code == 2
      assert [item.code for item in result.diagnostics] == ["OKF012"]
      assert _snapshot(root) == before
  ```

  `stub: true` — both snippets call existing helpers with their current
  signatures, so the first red result is the missing display encoding or
  forced-determinism behavior rather than harness setup.

- Add red hostile-field fixtures proving generated Markdown indexes cannot
  interpolate link syntax, control-like layout, or unsafe destinations from
  OKF `title`, `status`, or `type`; assert stable escaped output for valid
  display values and deterministic refusal for values outside an allowed
  metadata vocabulary (AC18, AC20).
- Add a red regression around the repeated-render seam in `compile_pack` that
  forces the second output to differ and observes exit class 2 plus diagnostic
  `OKF012` without retained partial output (AC8, AC20).
- Run the focused render/compiler suite twice and confirm identical results.

**Approach:**

- Apply one target-format-aware display encoder to `title`, `status`, and
  `type` at `_render_indexes`, after existing allowed-value checks; do not
  change the OKF grammar or normalize unrelated metadata.
- Exercise the existing two-render nondeterminism guard rather than duplicating
  it in a new helper.
- After focused and full compiler evidence passes, close only the two exact
  canonical `[backlog].open` entries in `workspace.toml`, preserving their
  shipped-spec provenance in the implementation record.

**Done when:** both regression tests fail before their fixes, pass afterward,
the compiler suite is green, and both named canonical entries are removed from
`[backlog].open` or replaced there by an explicit owner-accepted disposition
that names why closure is not valid.

### T2: The portable authoring workflow passes frame, create, and update contracts

**Depends on:** T1

**Touches:** `packs/agent-skill-engineering/pack.toml`, `packs/agent-skill-engineering/.apm/skills/author-or-update-agent-skill/**`, `packs/agent-skill-engineering/tests/**`

**Mode:** TDD plus goal-based workflow evaluation

**Tests:**

- PLAN-time red stub (`packs/agent-skill-engineering/tests/skills/author_or_update/test_contract.py`):

  ```python
  # STUB: AC1-AC4, AC6, AC17-AC19 — the author workflow exposes only the confirmed progressive contract
  from pathlib import Path

  AUTHOR_ROOT = Path("packs/agent-skill-engineering/.apm/skills/author-or-update-agent-skill")


  def test_authoring_skill_exposes_the_three_progressive_modes() -> None:
      skill = (AUTHOR_ROOT / "SKILL.md").read_text(encoding="utf-8")
      assert "frame" in skill
      assert "create" in skill
      assert "update" in skill
      assert "frame is the default" in skill.lower()
      assert "explicit" in skill.lower() and "transition" in skill.lower()
      assert "knowledge-provider" not in skill.split("description:", 1)[1].split("---", 1)[0]
      assert "runtime-package" not in skill.split("description:", 1)[1].split("---", 1)[0]


  def test_authoring_skill_declares_minimum_boundaries_and_confinement() -> None:
      skill = (AUTHOR_ROOT / "SKILL.md").read_text(encoding="utf-8")
      assert "filesystem_read_untrusted" in skill
      assert "filesystem_write" in skill
      assert "canonicalize" in skill.lower()
      assert "before" in skill.lower() and "read" in skill.lower()
      assert "agentbundle" not in skill.lower()
  ```

  `stub: true` — EXECUTE replaces incidental string checks with the pack's
  construction helper while retaining the asserted activation, transition,
  authority, and confinement surfaces.
- `no stub (goal-based workflow evaluation)` — the real pack eval runner must
  exercise the four versioned user tasks after the deterministic construction
  contract is green.

- Add activation positives for explicit skill framing/creation/update and
  negatives for generic writing, coding, architecture, and repository work
  (AC2, AC6).
- Add construction fixtures for a new skill and an existing-skill update that
  assert progressive transitions, portable artifacts, target confinement,
  retained behavior, and explicit unavailable M2 modes (AC1-AC4).
- Add failure fixtures for missing/ambiguous target, refused write authority,
  interrupted write, verification failure, and cleanup denial (AC17, AC19).
- Add metadata and projection fixtures proving the workflow declares and
  preserves exactly `filesystem_read_untrusted` and `filesystem_write`, and
  confinement fixtures proving unsafe candidates are refused before content is
  read (AC17, AC18).

**Approach:**

- Create the minimal external pack wrapper using the existing manifest schema
  and register only the user-facing workflow for pack activation evaluation.
- Author one portable skill with progressively loaded references for the three
  modes; keep `frame` read-only and gate both write modes explicitly.
- Use one pack-owned, runtime-neutral canonicalize-then-confine routine before
  every candidate read and authorized write; do not import AgentBundle into the
  portable workflow.
- Prefer declarative checklists and small deterministic helpers only where a
  repeated mechanical operation warrants code.

**Done when:** the new-skill and update fixtures pass, negative activation stays
dark, unsupported modes degrade explicitly, and portable content contains no
AgentBundle-specific behavior.

### T3: The review/optimize workflow reports every seeded foundation defect

**Depends on:** T2

**Touches:** `packs/agent-skill-engineering/.apm/skills/review-or-optimize-agent-skill/**`, `packs/agent-skill-engineering/tests/**`, `packs/agent-skill-engineering/pack.toml`

**Mode:** goal-based workflow evaluation with TDD construction checks

**Tests:**

- PLAN-time red stub (`packs/agent-skill-engineering/tests/skills/review_or_optimize/test_contract.py`):

  ```python
  # STUB: AC5, AC6, AC17 — review stays read-only until measured optimization is explicitly authorized
  from pathlib import Path

  REVIEW_ROOT = Path("packs/agent-skill-engineering/.apm/skills/review-or-optimize-agent-skill")


  def test_review_precedes_measured_optimization() -> None:
      skill = (REVIEW_ROOT / "SKILL.md").read_text(encoding="utf-8").lower()
      assert "read-only" in skill
      assert "observed failure" in skill or "measured baseline" in skill
      assert "explicit" in skill and "transition" in skill
      assert "before" in skill and "after" in skill


  def test_review_skill_covers_the_foundation_defect_classes() -> None:
      skill = (REVIEW_ROOT / "SKILL.md").read_text(encoding="utf-8").lower()
      for required in (
          "trigger", "progressive disclosure", "portability", "determinism",
          "authority", "security", "duplicated context", "conflicting writes",
          "unbounded concurrency",
      ):
          assert required in skill
  ```

  `stub: true` — EXECUTE completes the seeded-fixture assertions without
  coupling them to prose wording.
- `no stub (goal-based workflow evaluation)` — independent scoring of the four
  combined M1 cases runs only after their deterministic fixtures exist.

- Add activation positives for skill review and measured optimization and
  negatives for generic code review, prose editing, and unmeasured cleanup
  requests (AC5, AC6).
- Add activation-failure and deterministic-script-failure fixtures with
  predeclared applicable checklist items and seeded portability, authority,
  script-contract, context-duplication, conflicting-write, and concurrency
  defects (AC5, AC6).
- Add metadata and projection fixtures proving the workflow's untrusted-read
  and write boundaries survive every supported projection (AC17).
- Have an independent reviewer score the four combined M1 workflow cases
  against the fixed fixture checklists (AC6).

**Approach:**

- Keep review read-only and route optimize through an explicit evidence and
  authorization gate.
- Use the same pack-owned, runtime-neutral confinement routine before every
  candidate-skill read and authorized optimization write; refuse uncertainty
  before reading content.
- Share foundation vocabulary and evaluation identifiers with T2 without
  coupling the workflows to each other's prose.
- Register this second and final user-facing skill in the external pack eval
  declaration.

**Done when:** all applicable seeded defects are reported, optimization proves
semantic preservation against its baseline, and neither user-facing skill
activates for any negative fixture.

### T4: The governed foundation corpus compiles into a precise deterministic router

**Depends on:** T1

**Touches:** `packs/agent-skill-engineering/okf/**`, `packs/agent-skill-engineering/.apm/skills/agent-skill-engineering-reference/**`, `packs/agent-skill-engineering/tests/**`, `packs/agent-skill-engineering/pack.toml`

**Mode:** TDD

**Tests:**

- PLAN-time red stub (`packs/agent-skill-engineering/tests/pack/test_foundation_corpus.py`):

  ```python
  # STUB: AC7-AC9, AC17, AC18 — the declared corpus generates one inert precise bounded router
  import json
  from pathlib import Path

  PACK_ROOT = Path("packs/agent-skill-engineering")
  EXPECTED_TOPICS = {
      "framing-and-trigger-quality",
      "instruction-density-and-progressive-disclosure",
      "resources-scripts-and-exit-contracts",
  }


  def test_foundation_router_cases_are_predeclared_and_bounded() -> None:
      cases = json.loads((PACK_ROOT / "tests/fixtures/router-cases.json").read_text(encoding="utf-8"))
      assert len(cases) >= 20
      assert all(set(case["expected_topics"]) <= EXPECTED_TOPICS for case in cases)
      assert all(len(case["expected_topics"]) <= 3 for case in cases)


  def test_generated_router_is_inert_and_source_independent() -> None:
      router = (
          PACK_ROOT / ".apm/skills/agent-skill-engineering-reference/SKILL.md"
      ).read_text(encoding="utf-8")
      assert "filesystem_read_untrusted" in router
      assert "filesystem_write" not in router
      assert "Read `references/okf/index.md` first" in router
      assert "do not load the full bundle" in router.lower()
  ```

  `stub: true` — EXECUTE adds exact-score, double-compile, staged-tree, and
  hostile-structure assertions around this stable fixture surface.

- Declare at least twenty exact-set router fixtures, including near misses and
  integration-only requests, before generating the implementation (AC7-AC9).
- Add double-clean-compile byte comparison, generated-drift, three-topic cap,
  exact/pre-approved-set scoring, and staged-tree source-independence checks
  (AC8, AC9).
- Add hostile metadata, path, link, traversal, symlink, and outside-write
  fixtures. Display-only titles assert stable escaped output; unsafe structural
  metadata asserts deterministic refusal, no pre-refusal content read, and no
  source mutation (AC18).
- Add metadata and projection fixtures proving the inert generated router
  carries `filesystem_read_untrusted` without acquiring write authority
  (AC17).

**Approach:**

- Author only the three foundation OKF topics and declare the bundle in the
  existing external pack metadata.
- Compile the router and references with the hardened shared compiler; never
  hand-edit generated output.
- Keep router activation integration-only and read at most three selected
  concepts after root-first index narrowing.

**Done when:** both RFC M1 router thresholds meet or exceed 90%, every result is
bounded to the allowed topic count contract, two builds are byte-identical,
and the staged tree passes without authored OKF.

### T5: Provider mediation and language-extension seams preserve the common floor

**Depends on:** T2, T3, T4

**Touches:** `packs/agent-skill-engineering/.apm/skills/**`, `packs/agent-skill-engineering/okf/**`, `packs/agent-skill-engineering/tests/**`

**Mode:** TDD integration and security evaluation

**Tests:**

- PLAN-time red stub (`packs/agent-skill-engineering/tests/integration/test_provider_contract.py`):

  ```python
  # STUB: AC10-AC16, AC18 — provider mediation validates eligibility, manifest ownership, and clean absence
  import json
  from pathlib import Path

  FIXTURES = Path("packs/agent-skill-engineering/tests/fixtures/provider-contract.json")


  def test_provider_contract_is_versioned_bounded_and_transport_independent() -> None:
      contract = json.loads(FIXTURES.read_text(encoding="utf-8"))
      assert contract["contract_version"] == "agent-skill-engineering-reference/v1"
      assert set(contract["task_kinds"]) == {
          "skill-authoring", "skill-review", "skill-eval-ci", "agent-extension-design"
      }
      assert contract["max_topics"] == {"minimum": 1, "maximum": 3, "default": 3}
      assert set(contract["response_statuses"]) == {
          "ok", "out-of-scope", "unavailable", "stale-profile"
      }


  def test_unmanifested_independent_provider_reference_refuses_before_read() -> None:
      case = json.loads(
          Path(
              "packs/agent-skill-engineering/tests/fixtures/providers/"
              "eligible-unmanifested-reference.json"
          ).read_text(encoding="utf-8")
      )
      result = evaluate_provider_case(case)
      assert result.status == "unavailable"
      assert result.topic_bodies == []
      assert result.content_reads == []
      assert result.baseline_continues is True
      assert result.diagnostic == "provider integrity unavailable"
  ```

  `stub: true` — the second test is the explicit independent-provider
  missing/mismatched manifest-membership fixture required by ADR-0097; EXECUTE
  supplies the shared fixture evaluator and adds the remaining hostile cases.

- Use one shared fixture table to drive provider and consumer checks for every
  v1 request field, response status, zero-to-three result, refusal, provenance,
  and warning rule (AC10-AC14).
- Cover absent, multiple, ineligible, malformed, stale, overbroad, generic,
  authority-changing, prompt-injected, and credential-shaped provider cases;
  assert redaction, non-persistence, baseline continuation, and no topic reads
  after refusal (AC10-AC18).
- Cover an otherwise eligible independently delivered provider whose selected
  compiled reference is absent from or mismatched against its generated
  ownership manifest; assert refusal before content read, one bounded redacted
  diagnostic, and baseline continuation (AC13, AC14, AC18).
- Cover the four ADR-0097 knowledge-surface classes—organization standards,
  framework libraries, architecture references, and the agent-skills
  reference—with eligible, absent, ambiguous, and conflicting fixtures. Prove
  direct governed repository authorities remain direct and independent OKF
  knowledge remains provider-mediated (AC10-AC14).
- Add contract fixtures proving Python/pytest and TypeScript/Node are distinct
  extension-family values, neither has a topic body in this slice, and both
  return honest unavailability plus applicable foundation fallback (AC15).

**Approach:**

- Add bounded deterministic inspection of exposed capability metadata to both
  workflows; keep direct governed repository authorities direct. Only after an
  eligible provider is selected and explicitly invoked may that provider use
  root-first traversal of its own compiled reference tree.
- Resolve local capability metadata through the portable confinement contract,
  treat it as untrusted data, and reserve the blessed AgentBundle helpers for
  repository/compiler read-side construction checks.
- Encode the transport-independent contract in provider/consumer instructions
  and shared fixtures, with deterministic provider selection based only on
  externally eligible metadata.
- Preserve the two language families as unpopulated extension seams; their
  topic content and language-specific retrieval fixtures belong to the later
  corpus slice. Do not introduce runtime profiles or generic handbooks.

**Done when:** both sides pass the same semantic contract fixtures, provider
absence leaves every baseline workflow green, hostile responses cannot widen
authority, all four knowledge-surface classes have deterministic evidence, and
both language seams degrade without inventing language guidance.

### T6: The complete foundation passes its release-blocking evidence gates

**Depends on:** T2-T5

**Touches:** `packs/agent-skill-engineering/**`, `docs/specs/agent-skill-engineering-foundation/**`, `docs/product/briefs/agent-skill-engineering.md`, `workspace.toml`

**Mode:** goal-based integration, deterministic construction, independent review

**Tests:**

- `no stub (goal-based integration, deterministic construction, and independent review)` —
  T6 runs the already-materialized T1-T5 contracts together through the real
  pack, catalogue, projection, staged-tree, and reviewer surfaces; it adds no
  second test implementation of those contracts.

- Run the full staged-install, pack activation, workflow behavior, router
  precision, determinism, security, and failure-mode matrices (AC6, AC8, AC9,
  AC16-AC19, AC22).
- Run skill lint, pack tests, OKF generated-drift checks, catalogue deep lint
  and verify, documentation/link checks, self-host projection verification, and
  the proportionate repository build gate (AC1, AC21, AC22).
- Verify the portable tree contains no internal-governance citations or
  delivery logic and inspect the manifest boundary manually (AC1, AC21).
- Verify every skill's declared security boundaries survive each supported
  projection and no confined-file fixture reads content before refusal (AC17,
  AC18).

**Approach:**

- Fix only foundation defects exposed by the predeclared gates; expectation
  changes require explicit fixture review.
- Record independent workflow-quality, adversarial, security, and pack-boundary
  review evidence, adjudicating findings under the repository workflow.
- Update spec/plan lifecycle and programme evidence only after all blocking
  gates pass; do not implement later slices as release cleanup.

**Done when:** all M1 blocking gates are green, required independent reviews are
clean, generated projections are current, and the foundation is ready for a
separate release decision without any later-slice implementation.

## Rollout

Delivery is one dependency-ordered foundation sequence. The compiler hardening
lands first; portable workflows and corpus layers then land behind no activation
alias beyond their explicit descriptions; provider integration remains optional
and fail-closed; the final task proves the built pack. Rollback removes or
reverts the new pack as a unit and leaves the compiler hardening in place. No
infrastructure, service account, secret, network permission, migration, adapter
cutover, publication, or automatic installation is part of this plan.

## Risks

- The workflows could become generic meta-guidance. Exact activation negatives,
  three foundation topics, and unavailable later modes bound that drift.
- The provider seam could become de facto corpus coupling. External eligibility,
  explicit invocation, no topic-file discovery, and provider absence fixtures
  keep the coupling at the capability contract.
- A semantic envelope can drift between provider and consumers. One versioned
  shared fixture table is the conformance source; prose may evolve while those
  observable fields and outcomes remain stable.
- Language extensions could fork the common floor. Foundation-owned extension
  family names and absence fixtures reserve the seam while deferring actual
  topic content and cross-language behavior to Slice 2.
- Generated output can hide unsafe metadata or host-dependent ordering. T1,
  hostile fixtures, byte comparison, and staged-tree confinement block release.
- New pack work could accidentally absorb AgentBundle delivery design. The
  manifest is treated as an external wrapper and adapter/catalogue changes are
  prohibited by both spec and plan.

## Changelog

- 2026-08-26: initial scaffold
- 2026-08-26: filled the mixed-shape foundation plan after product, slice,
  semantic-contract, and shape confirmation; placed both named OKF defects in
  the blocking dependency graph under their existing canonical ownership.
