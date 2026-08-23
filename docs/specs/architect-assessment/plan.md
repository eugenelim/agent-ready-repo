# Plan: Progressive repository architecture assessment

- **Spec:** [`spec.md`](spec.md)
- **Status:** Done

> **Plan contract:** this is the implementation strategy. Unlike the spec, this
> document is allowed to change as implementation evidence changes. Material
> changes are recorded in the changelog below.

## Approach

Add `architect-assess` as the architect pack's current-state counterpart to
future-state design and artifact review. First establish a reusable architecture
knowledge plane as a pack-local OKF reference corpus compiled into the
`architecture-lenses-reference` router Skill. The workflow remains hand-authored:
it detects evidence and architecture shape, selects bounded corpus concepts,
owns the conversation and report, and never lets corpus knowledge stand in for
repository evidence. Then add one optional read-only profiler that strengthens
the Map and Focus stages without owning architectural judgment. Extend the
existing review surfaces with an assessment-report rubric, update activation and
product routing, retrofit the complete adopter journey, and finish by running
that published journey against materially different repositories. The highest-
risk implementation boundary is the profiler's filesystem and Git inspection;
it is kept standard-library-only, confined, non-executing, and optional.

## Constraints

- The applied method in
  [`docs/product/research/architecture-assessment-methodology.md`](../../product/research/architecture-assessment-methodology.md)
  grounds the stable stage spine, evidence ladder, view set, scenario method,
  triggered lenses, and action sequencing. Shipped pack content restates the
  portable method and carries no catalogue-internal governance citations.
- The decision taxonomy and corpus authoring requirements are grounded in
  [`docs/product/research/architecture-assessment-intents-survey.md`](../../product/research/architecture-assessment-intents-survey.md).
  The six-intent set is a moderate-confidence synthesis that must be tested with
  ambiguous and same-repository/different-intent prompts rather than presented
  as an external standard.
- RFC-0087's experimental `agentbundle-okf/v1` profile is used only as an
  authoring and deterministic projection format for inert `Reference` concepts.
  `packs/architect/okf/architecture-lenses/` is canonical; generated router,
  indexes, nested references, and `.okf-generated.json` are build output and are
  never edited directly.
- RFC-0087's promotion gate still governs release: implementation may author and
  test `architecture-lenses` as an additional reference-only pilot, but the
  architect pack cannot publish it until the pilot-results record includes the
  required model-routing evidence and explicit Approver sign-off and
  `docs/adr/0093-okf-reference-corpora-remain-governed-build-time-sources.md`
  records the release decision. An open gate fails release rather than being
  inferred from this feature's approval.
- `packs/architect/DESIGN.md` retains one read-only subagent and the existing
  config-driven per-effort output model. This change revises its former
  pure-Markdown and no-code-graph wording only as far as needed for one optional,
  bounded evidence profiler. It also narrows "no required composition" to
  independence among user-facing workflows while allowing a deterministic,
  same-pack knowledge router with visible degradation.
- `.apm/` is the projected runtime surface; deterministic tests live under
  `packs/architect/tests/`, while activation and agent-output evals live with the
  skill under `.apm/skills/architect-assess/evals/`.
- A new public workflow skill requires the next unclaimed minor architect-pack
  version in both `pack.toml` and `.claude-plugin/plugin.json`, pack-eval
  registration, a free-standing central changelog release entry, and self-host
  regeneration. The generated knowledge router has no user-prompt activation
  eval, mirroring core's reviewer-internal depth libraries.
- Product documentation sources live in `packs/architect/`, `guides/architect/`,
  and `web/src/content/packs/architect.md`. Generated docs-site content and the
  `/now/` projection are produced by tooling, never edited by hand.
- The profiler crosses this repo's filesystem boundary, and optional enterprise
  context crosses a network/untrusted-data boundary through an already exposed
  retrieval capability. The profiler implementation must resolve the tension
  between projected portability and the blessed confinement helper by isolating
  one confinement layer, using
  `agentbundle.catalogue_tooling.file_safety` where available, and proving the
  standard-library fallback has equivalent fail-closed behavior. The assessment
  workflow adds no knowledge connector, auth flow, or credential handling.
- Current Git refs only. Do not stage, commit, fetch, pull, merge, rebase, stash,
  switch branches, or update the index or refs. Preserve unrelated worktree
  changes. The base-freshness check is explicitly skipped in this workspace.
- No new runtime dependency, universal parser, persistent repository index,
  install-time profiler, new architect subagent, new output configuration key,
  executable assessment-report validator, OKF Playbook projection, executable
  computation, corpus-hosted remote retrieval, public OKF CLI, connector, auth
  mechanism, or adapter primitive.

## Construction tests

**Integration tests:**

- Compile the architect OKF bundle twice and in check mode; assert byte-identical
  managed output, source/output ownership, hierarchical index integrity,
  reference-only metadata, no tool authority, and no hand-edited generated
  surface.
- Frozen multi-consumer routing cases prove assessment, design, and review load
  the expected base and triggered concept paths, never fabricate a path, never
  flat-load the corpus, and never cite corpus knowledge as target-system evidence.
  Six assessment cases reuse one repository topology with baseline, assurance,
  optimization, growth, transformation, and disposition intents and must select
  different evidence requirements and decision tests while retaining the same
  observed architecture facts.
- Knowledge-surface fixtures cover none detected, an in-repo doc set, an exposed
  retrieval capability, empty results, one unconfirmed source, stale/sensitive
  context, conflicting standards and implemented evidence, malicious
  instruction-like content, and a denied query. They assert targeted area
  selection, attribution, lower confidence, no bulk retrieval, no secret access,
  and no persistence of organization content.
- Run the real profiler against the repository-shape fixture set named in the
  Testing Strategy, plus an unsupported-language fixture for degradation; assert
  deterministic evidence, honest degradation, and no writes to the target trees.
- Compare the profiler's fallback confinement behavior with
  `agentbundle.catalogue_tooling.file_safety` for allowed reads, symlink escapes,
  non-regular files, output paths, redacted diagnostics, and containment
  uncertainty.
- Exercise the skill's assessment output against its report rubric with planted
  scope overclaim, missing view/lens coverage, heat-as-severity misuse, weak
  evidence, and actions without finding traceability.
- Generate the architect journey and public documentation sources from canonical
  inputs, then verify routes, skill inventory, and reachable entry points.

**Manual verification:**

- Follow `guides/architect/how-to/assess-a-repository.md` verbatim from the
  generic prompt against two materially different repositories or realistic
  fixtures. Record the Frame and Focus correction points, current-state model,
  attention heat map, selected drill-downs, coverage limits, and action waves.
- Run a survey-only journey and confirm it stops after Focus with hypotheses and
  recommended drill-downs rather than presenting a completed remediation plan.
- Run a standard agentic/knowledge assessment and confirm the workload lens does
  not collapse into backend layering or model-client compliance findings.
- Against one stable fixture, compare baseline, assurance, optimization,
  growth-readiness, transformation, and disposition runs. Confirm that each
  preserves the same current-state map but requests different
  operational/business evidence, prioritizes different scenarios, and produces
  intent-appropriate actions and uncertainty.
- Run the three enterprise modes required by T6: no enterprise surface, in-repo
  enterprise documentation, and an explicitly authorized private retrieval
  fixture containing engineering patterns and a system landscape. Confirm that
  added context improves context coverage without changing target-evidence
  claims, and that no run fabricates local standards or ownership.

## Design (LLD)

### Design decisions

- **One progressive workflow, three stopping depths.** Frame → Map → Focus →
  Investigate → Act → Close is the stable conversation. Survey stops after
  Focus; standard completes the repository-grounded workflow; deep adds
  separately authorized operational evidence. This is easier to learn and
  compare than three unrelated procedures. Traces to: progressive-mode ACs.
- **Two correction points.** The user corrects the conceptual model before
  detailed analysis and redirects hotspot selection before expensive
  drill-down. A plain "continue" accepts the recommendation. Traces to:
  conversation and checkpoint ACs.
- **Three knowledge planes.** Repository/system evidence establishes what exists;
  enterprise surfaces establish local facts and constraints; pack knowledge
  supplies reusable lenses and questions. Reports and tests keep their
  provenance distinct. Traces to: evidence, corpus, and confidence ACs.
- **Enterprise knowledge composes when present and degrades when absent.** The
  workflow capability-discovers internal retrieval, declares what it found,
  asks before crossing the private-context boundary, and queries only selected
  areas from the shared eight-area taxonomy. Retrieved facts remain attributed,
  untrusted context rather than target evidence or corpus content. Traces to:
  enterprise-surface, permission, provenance, and confidence ACs.
- **OKF packages knowledge, not workflow.** Neutral concepts are canonical OKF
  `Reference` records compiled into a generated router. Each consuming workflow
  retains its own triggers, procedure, permissions, verdict semantics, and
  degradation behavior. Traces to: OKF and composition ACs.
- **A finite ontology, not a generic reference dump.** The initial corpus has
  foundation, operating-context, assessment-intent, quality,
  repository/system-shape, and workload branches. Every concept uses the same
  investigation-oriented record shape, while the agentic branch descends into
  the platform contracts that the motivating assessment missed. Traces to:
  corpus content and progressive-disclosure ACs.
- **Intent is orthogonal to architecture shape.** Frame selects one primary
  decision lens and may name secondary lenses. Baseline explains; assurance
  tests a risk or readiness threshold; optimization improves the current
  mission; evolution tests a future scenario; transformation compares ways to
  materially change a retained system; disposition decides whether to retain,
  invest, consolidate, acquire/integrate, replace, or retire it. Traces to:
  Frame, evidence, and action ACs.
- **Attention, not verdict, heat.** The heat map keeps raw dimensions visible and
  navigates investigation. Only traced mechanisms and threatened scenarios
  become findings. Traces to: heat-map and finding ACs.
- **One optional profiler.** `profile_repo.py` standardizes safe evidence census,
  basic concentration/history signals, and exact Python import extraction. It
  does not create the architecture model or validate report quality. Traces to:
  profiler and degradation ACs.
- **Assessment review stays artifact review.** The existing review skill and
  cold-context subagent receive an assessment-report rubric but never become
  alternative repository scanners. Traces to: reviewer AC.
- **Retrofit the entry journey.** "What does this architecture look like?" now
  starts a survey assessment; `reference.md` creation remains an explicit
  follow-up. Traces to: discovery and first-value ACs.

### Interfaces & contracts

The user-facing skill contract consists of natural-language activation,
progressive conversation receipts, optional file saving, and the report shape.
The architecture corpus conforms to the existing `agentbundle-okf/v1` profile
and extension schemas; it adds no new OKF field or projection behavior.
The profiler is an internal runtime helper with a small CLI and importable
functions; its JSON contains a schema version for tests and future-safe parsing
but is not promoted to `contracts/`. No network, service, API, or event contract
is added. Traces to: activation, output, profiler, and saving ACs.

### Failure, edge cases & resilience

- Very large or mixed monorepo: survey partitions the entity before deep
  inspection and reports uncovered areas rather than averaging them.
- Sparse or stale docs: implemented and exercised evidence reconstructs the map;
  intent remains unknown where no decision record exists.
- Unsupported language: generic topology, manifests, delivery, tests, history,
  and targeted reading remain available; semantic claims are downgraded.
- Missing Python or Git: the helper is skipped with an actionable receipt and the
  assessment proceeds manually without installing anything.
- Symlink, special-file, binary, generated, vendored, or out-of-root target:
  profiler fails closed or excludes it with a reason and never reads through an
  unsafe boundary.
- Active production defect: the report interrupts broad modernization to
  recommend containment and proof, while preserving broader assessment scope as
  a separately bounded continuation.
- No significant risk found: retain strengths/non-risks and residual unknowns;
  do not manufacture work.

### Dependencies & integration

- `architect-assess` owns current implemented-system investigation.
- `architecture-lenses-reference` supplies inert, reusable architecture concepts
  through generated hierarchical indexes; it never owns activation, assessment
  state, permissions, evidence claims, or verdicts.
- `architect-design` and `architect-review` consume genuinely neutral concepts
  from the same corpus while retaining their local authoring/review procedures.
- `architect-design` receives future-state choices or redesign work discovered
  by an assessment.
- `architect-diagram` may render a selected current-state view but does not own
  assessment conclusions.
- `architect-review` and `design-reviewer` critique saved assessment reports.
- The existing `[architecture] output_dir` resolves saved assessment efforts.
- `tools/build-site.py` projects canonical journey and changelog Highlights into
  generated site inputs, including the public `/now/` surface.

## Tasks

### T0: Reusable architecture knowledge compiles from OKF without taking workflow authority

**Depends on:** none

**Verification mode:** goal-based compiler, ownership, corpus-routing, and
multi-consumer parity checks; no red stub because the compiler is existing and
the new behavior is authored knowledge plus generated projection.

**Touches:** `packs/architect/okf/architecture-lenses/**`, `packs/architect/.apm/skills/architecture-lenses-reference/**`, `packs/architect/.okf-generated.json`, `packs/architect/pack.toml`, `packs/architect/.apm/skills/architect-design/references/**`, `packs/architect/.apm/skills/architect-review/references/**`, `packs/architect/DESIGN.md`, `packs/architect/tests/pack/**`, `docs/specs/architect-assessment/notes/architecture-knowledge-audit.md`, `docs/product/research/architecture-assessment-corpus/**`

**Tests:**

- `python3 packs/catalogue-curation/.apm/skills/compile-okf/scripts/compile_okf.py
  --root . --pack architect --check` is clean; two staged compiles produce
  byte-identical managed output and preserve all nested OKF bytes across the
  pack's declared adapters.
- Corpus-structure tests require only `Reference` concepts, valid provenance and
  lifecycle fields, freshness horizons for time-sensitive content, complete
  hierarchical indexes, no projected concepts, no volatile binding provider
  limits, no tools/network/credentials/executors/attesters/scripts/remotes, and
  generated ownership markers on every managed output.
- Concept-contract tests require every concept to contain its scope/routing
  signals, supported decisions and minimum evidence, architectural questions,
  mechanisms and trade-offs, evidence and counter-evidence, failure modes and
  false positives, confirmation scenarios, related concepts or escalation, and
  provenance/lifecycle information.
  Deterministic lint rejects missing or empty sections; a cold-context content
  review rejects generic checklist filler or universal claims unsupported by
  the cited sources.
- Source-packet tests enforce a one-to-one normalized concept-path mapping under
  the living maintenance surface
  `docs/product/research/architecture-assessment-corpus/`. Each
  typed packet records material claim identifiers and citations, independent
  source count, confidence and downgrade factors, counter-evidence/disagreement,
  licensing, known unknowns, lifecycle, and freshness. Every material concept
  claim resolves to its packet; high/moderate claims have at least three
  independent sources, while thinner evidence is visibly downgraded rather than
  accepted as an uncited rule.
- Frozen routing cases span base quality reasoning, enterprise grounding,
  all six assessment intents, libraries,
  layered/client-server systems, event-driven/distributed systems,
  data/ML/knowledge platforms, serverless, GenAI/agentic systems, and
  infrastructure/platform/monorepos. Expected concept paths are fixed before
  generated-router runs; fabricated paths, flat corpus loads, and corpus-as-
  repository-evidence responses fail. Same-topology/different-intent cases must
  preserve observed facts while changing the required decision data.
- The architecture-knowledge audit classifies every existing architect
  reference as `move to neutral corpus`, `retain workflow-specific`, or
  `unchanged diagram/output concern`, with a reason. Multi-consumer parity tests
  prove moved concepts retain their load-bearing meaning in design and review.
- No red test stub: compiler behavior is already contracted and tested; this
  task validates corpus content, projection drift, and agent routing outcomes.

**Approach:**

- Declare one `architecture-lenses` bundle in `[pack.metadata.okf]` and generate
  `architecture-lenses-reference` with the existing catalogue authoring tool.
  Edit canonical OKF concepts only; never patch generated router or indexes.
- Author the canonical corpus under this initial tree; exact filenames are
  normalized during implementation, but the named coverage is mandatory:

  ```text
  architecture-lenses/
    concepts/
      foundations/
        evidence-confidence-and-coverage.md
        boundaries-and-current-state-views.md
        quality-attribute-scenarios.md
        tradeoffs-sensitivity-and-evolution.md
        decisions-constraints-and-cross-cutting-concerns.md
      enterprise-knowledge/
        source-detection-confidence-and-conflicts.md
        business-domain-and-meaning.md
        current-system-landscape.md
        interfaces-and-contracts.md
        operational-reality.md
        constraints-and-standards.md
        local-patterns-and-reference-architectures.md
        decisions-and-rationale.md
        in-flight-work-and-roadmap.md
      operating-model-patterns/
        governance-ownership-and-team-patterns.md
        provider-and-platform-operating-models.md
        delivery-runtime-and-development-patterns.md
      assessment-intents/
        baseline-and-understanding.md
        hardening-and-risk-reduction.md
        optimize-current-outcomes.md
        growth-and-scale-readiness.md
        transformation-and-modernization.md
        rationalization-disposition-and-due-diligence.md
      quality-lenses/
        reliability-resilience-and-recovery.md
        performance-scalability-and-capacity.md
        security-privacy-and-trust-boundaries.md
        operability-observability-and-supportability.md
        maintainability-modularity-and-evolvability.md
        data-integrity-lifecycle-and-governance.md
        cost-and-resource-efficiency.md
        testability-delivery-and-change-safety.md
      system-shapes/
        library-sdk-and-cli.md
        layered-and-modular-application.md
        client-server.md
        distributed-services.md
        event-driven-and-streaming.md
        monorepo-platform-and-infrastructure.md
      workload-lenses/
        transactional-request-response.md
        background-batch-and-scheduled-work.md
        data-analytics-and-ml.md
        knowledge-search-and-retrieval.md
        serverless.md
        genai-agentic/
          model-access-and-policy.md
          durable-run-state-and-recovery.md
          tool-authorization-and-credentials.md
          knowledge-provenance-and-isolation.md
          evaluation-and-observability.md
  ```

  Compiler-generated root and branch indexes expose this tree; authors never
  maintain those indexes by hand.
- Build the corpus in five gated passes: (1) freeze ontology, concept template,
  and trigger-to-path routing cases; (2) audit existing architect references and
  extract only neutral reusable material; (3) create evidence-backed source
  packets for each concept, including disagreement, false positives, provenance,
  licensing, and freshness; (4) author canonical OKF concepts and compile the
  router/indexes; (5) run multi-consumer routing, semantic-parity, and diverse-
  repo dogfood before migrating or deleting duplicated references.
- Use `desk-research` to build the whole corpus in waves rather than filling the
  tree from model memory: foundations and intent/quality concepts first, common
  system shapes and operating-model patterns second, workload branches third,
  and agentic/knowledge sub-concepts as a dedicated pressure-test wave. Each
  concept gets a typed source packet with material claims triangulated across at
  least three independent sources, confidence tags, counter-evidence, known
  unknowns, provenance/licensing, and a freshness decision. Prefer primary
  standards, original framework owners, official provider guidance, and
  established engineering references; use the applied practitioner overlay for
  patterns and failure cases, and record disagreement rather than flattening it
  into a universal rule.
- Make every consumer follow the generated router and selected sibling concept
  paths explicitly; do not rely on nested Skill auto-activation. Preserve a
  visible degraded path when the generated router is absent or invalid.
- Move only neutral, reusable substance from current design/review references:
  quality scenarios, trade-offs/sensitivity, cross-cutting questions,
  well-architected/provider operating-model concerns, the canonical eight
  enterprise knowledge areas, and applicable serverless/agentic lenses. Keep
  consumer-specific detection/approval/degradation framing, authoring procedure,
  review severity, artifact rubrics, diagram notation/provider vocabulary,
  convergence, layout, and save behavior local.
- Amend the pack design rule from "every Skill duplicates all depth" to "every
  user-facing workflow owns its procedure and degrades visibly; shared inert
  knowledge may be routed through a same-pack generated corpus."

**Done when:** The canonical corpus regenerates cleanly; every concept passes the
one-to-one source-packet and claim-trace gate; the router selects the expected
concept paths for all frozen cases without authority leakage; and the existing
design/review behavior remains semantically covered after neutral reference
migration.

### T1: The progressive assessment method produces a correctable current-state map, attention heat map, and action-ready report

**Depends on:** T0

**Verification mode:** goal-based fixture/eval checks; no TDD stub because the
method surface is agent behavior and report structure, not deterministic runtime
logic.

**Touches:** `packs/architect/.apm/skills/architect-assess/SKILL.md`, `packs/architect/.apm/skills/architect-assess/assets/**`, `packs/architect/.apm/skills/architect-assess/references/**`, `packs/architect/tests/skills/architect-assess/**`

**Tests:**

- Goal-based fixture checks assert the Frame, Map, Focus, Investigate, Act, and
  Close stages; cumulative mode exits; two correction points; current-state
  views; evidence ledger; attention-map legend; hotspot cards; triggered lens
  coverage; knowledge-surface detection and targeted enterprise-context
  attribution; finding schema; action-wave traceability; and completion receipt.
- Projection checks assert that skill frontmatter declares
  `filesystem_read_untrusted`, `filesystem_write`, and `network_fetch`
  boundaries and declares no credential boundary.
- Negative fixtures reject folder-only, compliance-only, unsupported-language,
  opaque-score, and platform-readiness-overclaim outputs.
- No red test stub: method content is agent behavior evaluated through fixtures
  and eval rubrics rather than runtime logic.

**Approach:**

- Keep `SKILL.md` as the concise controller and procedure; load its local stage
  method, heat-map guidance, report rubric, and output-path contract on demand.
  Route reusable current-state, decision-intent, quality, context, provider, and
  shape/workload knowledge through selected normalized concept paths in
  `architecture-lenses-reference`.
- Reuse the corpus's neutral eight-area enterprise taxonomy, but keep the
  assessment-specific detection, approval, targeted-query, attribution,
  conflict, and degradation procedure in `architect-assess`. Query capabilities
  by shape rather than a hardcoded tool name. Retrieved content is untrusted
  data and is never copied into saved artifacts beyond the minimum authorized
  attribution or paraphrase needed to support the report.
- Frame routes a declared intent to its concept. If the ask is ambiguous, infer
  no intent silently: present the plausible decision lenses and either obtain a
  primary choice with named secondary intents or carry an unresolved intent with
  visibly reduced action confidence. “Should we rewrite?” routes first to
  disposition; “how should we modernize this retained system?” routes to
  transformation. A rewrite recommendation must compare retain/harden,
  incremental modernization, targeted replacement, and full rewrite; code size,
  age, or coupling alone cannot eliminate an option.
- Use one report template in conversational order and one hotspot-card template.
- Translate the research methodology into portable practitioner guidance without
  copying internal citations into shipped pack content.

**Done when:** Focused skill tests can distinguish a bounded survey from a
complete standard assessment and can trace every report section to the method.

### T2: The optional profiler returns safe, deterministic evidence without pretending to understand every language

**Depends on:** T1

**Verification mode:** TDD for importable profiler functions, plus goal-based
CLI and fixture checks for emitted profiler artifacts.

**Touches:** `packs/architect/.apm/skills/architect-assess/scripts/profile_repo.py`, `packs/architect/tests/skills/architect-assess/test_profile_repo.py`, `packs/architect/tests/skills/architect-assess/fixtures/**`

**Tests:**

- `stub: true` — the following compilable red construction stub pins the
  profiler's public result shape and the positive inventory behavior from AC22
  and AC25. It stays red until T2 provides the script and contract; AC23–AC24
  and AC26–AC30 are completed as edge-case tests during EXECUTE.

  ```python
  # STUB: AC22/AC25 — profile_repo returns a deterministic evidence profile
  # Generated at PLAN; the exact counts and classifications remain construction
  # details, while these top-level fields are the durable contract surface.
  import importlib.util
  from pathlib import Path


  SCRIPT = Path(
      "packs/architect/.apm/skills/architect-assess/scripts/profile_repo.py"
  )


  def _load_profiler():
      spec = importlib.util.spec_from_file_location("profile_repo", SCRIPT)
      assert spec is not None and spec.loader is not None
      module = importlib.util.module_from_spec(spec)
      spec.loader.exec_module(module)
      return module


  def test_profile_repository_returns_traceable_inventory(tmp_path: Path) -> None:
      (tmp_path / "pyproject.toml").write_text("[project]\nname='fixture'\n")
      source = tmp_path / "src"
      source.mkdir()
      (source / "app.py").write_text("import json\n")

      result = _load_profiler().profile_repository(tmp_path)

      assert result["schema_version"]
      assert result["root"] == "."
      assert result["evidence"]["manifests"]
      assert result["evidence"]["source_areas"]
      assert result["signals"]
      assert result["limitations"] == []
  ```

- TDD unit tests cover root/output confinement, symlink escapes, special and
  binary files, exclusion classes, deterministic ordering, UTF-8 stdout/stderr,
  JSON schema version, Markdown rendering, missing Git, time/size bounds, and no
  writes to the assessed root by default.
- Security-boundary tests cover file-safety parity, containment uncertainty,
  strict JSON (`allow_nan=False` and valid Unicode), redacted errors, no absolute
  target paths in output, interrupted scans, decode failures, and bounded
  resource use.
- Output tests accept only the approved assessment effort folder or an
  explicitly surfaced and approved temporary/workspace output root, resolve the
  destination through the confinement layer, and reject every other location.
- Exact Python-AST import tests cover aliases, relative imports, parse failures,
  package boundaries, and confidence/provenance fields.
- Integration fixtures prove language-neutral discovery of manifests, source and
  tests, CI/CD, containers/deployment/IaC, schemas/migrations, operations files,
  concentration, and optional churn in non-Python repositories.

**Approach:**

- Implement one standard-library module with importable functions and a thin CLI.
  Put all filesystem access behind a named confinement layer. In this catalogue,
  prefer `agentbundle.catalogue_tooling.file_safety` when it is importable; keep
  a projected fallback with the same contract so installed skills do not require
  catalogue internals.
- Emit raw evidence and attention signals only; keep model and risk synthesis in
  the skill.
- Require an explicit root. Default to stdout; permit an explicit output file
  only after the caller has handled the skill's save/permission gate and the
  resolved destination is inside the approved assessment effort folder or an
  explicitly surfaced and approved temporary/workspace output root. Resolve the
  allowed root and destination through the same confinement layer and reject
  every other location.
- Detect already-available native analysis as a capability for the skill to
  consider, not a command the profiler automatically runs.

**Done when:** The focused profiler suite is green across every fixture, a
second identical run is byte-for-byte equal, and target-tree snapshots remain
unchanged.

### T3: Assessment reports receive independent evidence and overclaim review without turning reviewers into scanners

**Depends on:** T0, T1

**Verification mode:** goal-based artifact-review fixtures against the assessment
rubric; no repository-scanning test because the reviewer contract forbids it.

**Touches:** `packs/architect/.apm/skills/architect-review/**`, `packs/architect/.apm/agents/design-reviewer.md`, `packs/architect/tests/pack/test_design_reviewer_rubric_parity.py`, `packs/architect/tests/skills/architect-review/**`

**Tests:**

- Fixture reviews detect planted scope inflation, missing evidence classes,
  model/view contradictions, heat-as-severity misuse, untriggered or skipped
  lenses, absent counter-evidence, and untraceable action waves.
- Existing design/diagram rubric and project-knowledge-boundary tests remain
  green; parity tests include the assessment rubric's load-bearing vocabulary.
- A no-artifact "review our architecture" request routes to
  `architect-assess`, while a supplied `assessment.md` remains reviewable.

**Approach:**

- Add assessment-report detection and a dedicated rubric to `architect-review`.
- Inline the equivalent condensed checks in the read-only reviewer while
  preserving its no-rewrite and artifact-required boundaries.
- Reuse neutral corpus concepts for architectural quality and triggered workload
  knowledge; keep report severity, evidence calibration, and verdict procedure
  in the review surfaces.

**Done when:** Both review surfaces return the same verdict class for the
assessment fixtures and neither performs repository discovery to fill report gaps.

### T4: Pack routing, metadata, evals, and projections expose four workflows plus one routed knowledge surface

**Depends on:** T0, T1, T2, T3

**Verification mode:** goal-based pack, eval-registration, activation, and
self-host projection checks.

**Touches:** `packs/architect/pack.toml`, `packs/architect/.claude-plugin/plugin.json`, `packs/architect/.apm/skills/architect-assess/evals/**`, `packs/architect/DESIGN.md`, `packs/architect/tests/pack/**`, `.agents/skills/architect-assess/**`, `.agents/skills/architecture-lenses-reference/**`, `.codex/skills/architect-assess/**`, `.codex/skills/architecture-lenses-reference/**`

**Tests:**

- Activation evals cover the routing and repository-shape cases named by the
  activation-and-quality AC, including negative near-miss prompts for the
  existing design, diagram, and review skills.
- Pack tests assert four user-facing workflow entries, one generated
  non-user-triggered knowledge router, eval registration only for the workflows,
  first-value routing, matching next-minor versions, and the one-subagent
  invariant.
- Catalogue self-host check is clean after regeneration; projected copies match
  `.apm/` and are not hand-edited.

**Approach:**

- Update description, keywords, first-value prompt/result, eval roster, and
  matching manifests.
- Complete the `DESIGN.md` integration begun in T0: add assessment to the product
  model; describe the three knowledge planes and OKF authoring boundary; and
  narrow the former graph-extraction/pure-Markdown non-goals to exclude
  enterprise EA or universal semantic tooling while permitting the bounded
  optional profiler.
- Run self-host only after canonical pack sources are complete.

**Done when:** Catalogue verification sees `architect-assess` as a valid public
primitive on every declared adapter and activation fixtures route without overlap.

### T5: The external documentation lets an adopter run and steer an assessment without knowing skill names

**Depends on:** T1, T3, T4

**Verification mode:** goal-based documentation source and navigation checks,
followed by manual docs-quality review through the published journey.

**Touches:** `packs/architect/README.md`, `packs/architect/JOURNEY.md`, `packs/architect/docs/index.md`, `web/src/content/packs/architect.md`, `guides/architect/README.md`, `guides/architect/how-to/assess-a-repository.md`, `guides/architect/reference/architecture-assessment.md`, `guides/architect/how-to/review-an-architecture-artifact.md`, `guides/architect/how-to/shape-an-architecture-concept.md`, `guides/architect/how-to/establish-reference-architecture.md`, `guides/architect/how-to/diagram-a-system.md`, `guides/architect/reference/reference-architecture.md`, `guides/architect/tutorials/architect-first-session.md`, `guides/architect/tutorials/create-your-reference-architecture.md`, `guides/architect/explanation/architect-diagram-skill-design.md`, `docs/specs/architect-assessment/notes/product-docs-audit.md`

**Tests:**

- Source checks confirm the product-prose AC's generic-prompt placement on the
  primary entry pages and that each states outcome, reads, optional writes,
  human decisions, and likely next request.
- Link and navigation checks prove every new page is reachable, all changed
  internal links resolve, and review/reference-architecture routes remain clear.
- Documentation checks describe the knowledge router as an internal support
  surface rather than a fifth user task, explain that lenses guide inspection
  but do not prove implementation, and keep OKF authoring details out of the
  primary how-to path.
- Documentation checks distinguish the internal OKF router from an adopter's
  enterprise knowledge surface; document capability detection, the eight areas,
  the private-query approval, targeted retrieval and attribution, conflict and
  sensitivity handling, and the no-surface degraded path without naming a
  specific knowledge product.
- The product-docs audit note lists every existing architect guide and pack
  discovery page, records `updated` or `unchanged`, and gives the reason for
  each unchanged page.
- Journey schema/index generation validates the new assessment gates, four
  user-facing workflows plus the internal knowledge router, effects, and
  first-value outcome.

**Approach:**

- Apply the `author-product-docs` retrofit contract:
  - mode: retrofit;
  - audience: external product user;
  - situation: a maintainer needs to understand an existing repository and act;
  - primary job: obtain an evidence-backed current-state assessment;
  - natural start: the generic activation prompt named by the spec;
  - expected result: corrected current-state model, attention heat map, bounded
    drill-downs, coverage/confidence, and sequenced action;
  - human decisions: correct the map, redirect hotspots, authorize deeper checks,
    and accept or revise action;
  - read/write boundary: repository inspection is read-only; executable checks
    and saving require the stated gates; private enterprise retrieval is a
    separate ask-first boundary;
  - likely next: validate a hotspot, design a target change, or review the report.
- Add one complete how-to and one compact reference. Keep architecture-shape
  and enterprise-knowledge variations inside the how-to rather than creating
  thin per-shape or per-tool pages.
- Audit the existing concept, diagram, review, reference-architecture, and
  first-session guides for changed routing or "how to use" instructions before
  deciding whether to edit them.
- Revise existing discovery and journey pages only where the new entry point
  changes the reader's route.

**Done when:** A cold reader can start the generic assessment, understand both
checkpoints, and choose the next action using only the published guide set.

### T6: The documented journey survives cross-shape dogfood and the complete catalogue gates

**Depends on:** T2, T5

**Verification mode:** manual QA with recorded session scope, plus goal-based
pack, docs, site, and source-claim checks.

**Touches:** `packs/architect/tests/skills/architect-assess/fixtures/**`, `docs/specs/architect-assessment/notes/**`, `docs/rfc/0087-notes/pilot-results.md`, `docs/adr/0093-okf-reference-corpora-remain-governed-build-time-sources.md`

**Tests:**

- Manual-QA transcripts or evidence notes record the guide-driven generic-prompt
  run against two materially different repositories/fixtures and the
  agentic/knowledge standard-mode pressure test, including the session stop
  point and what was documented but not exercised.
- The guide-driven evidence set exercises all three enterprise modes: no surface
  detected; in-repo enterprise documentation; and an exposed private retrieval
  fixture whose query follows a recorded user authorization. Modes may reuse a
  repository fixture, but each record names selected knowledge areas and corpus
  concept paths and proves target evidence, enterprise context, and pack
  knowledge remain separately attributed.
- Focused pack tests, Ruff, catalogue lint/verify, self-host check, site
  generation, web build/tests, docs-site build, and rendered link checks pass.
- RFC-0087's release gate is explicit and fail-closed: the pilot-results record
  contains the required model-routing evidence and RFC Approver sign-off, and
  ADR-0093 records the reviewed release decision for reference-only OKF corpora.
  Until both records exist, release checks reject publication of the architect
  bundle/router; feature approval alone does not satisfy the gate.
- A final source audit confirms the docs match the implemented skill and profiler
  behavior and names any evidence that deep mode still requires from a human or
  live environment.

**Approach:**

- Follow the published guide literally; do not supplement it from this spec or
  implementation knowledge during the run.
- Treat any missing prompt, ambiguous checkpoint, overclaim, or weak next action
  as a product defect and repair the canonical skill or guide before rerunning.
- Record observed output and remaining limits in spec notes without promoting
  fixture-specific conclusions into shipped guidance.
- Present the completed pilot evidence to the RFC Approver, record the explicit
  sign-off in the pilot-results note, and add ADR-0093 as the durable release
  decision. If approval is withheld, keep the assessment workflow on ordinary
  hand-authored references and do not publish the OKF bundle/router.

**Done when:** All required cross-shape and enterprise-mode dogfood journeys
satisfy the report rubric, the full relevant gate set is green, RFC-0087's
promotion records are complete, and a second docs/site generation run is clean.

### T7: The architect release publishes an outcome-led changelog highlight on the NOW page

**Depends on:** T4, T5, T6

**Verification mode:** goal-based changelog parser, generated projection, and
rendered `/now/` route checks.

**Touches:** `docs/product/changelog.md`, `web/src/lib/now-highlights.generated.json`, generated journey inputs changed by `tools/build-site.py`

**Tests:**

- The changelog parser sees one free-standing architect release at the matching
  pack version with an immediate-child `### Highlights` block.
- `tools/build-site.py --journeys-only` regenerates the committed projection;
  a second run produces no diff.
- Web rendered-output tests prove `/now/` displays the architect outcome and its
  link resolves to that exact release heading in the rendered changelog.

**Approach:**

- Write the release entry for users, not maintainers: they can now move from a
  repository-wide question to a corrected current-state model, attention map,
  focused evidence, and action plan.
- Generate NOW and journey inputs from canonical sources. Do not edit generated
  JSON directly.

**Done when:** The built `/now/` page contains the architect highlight with a
working release-specific changelog link.

## Rollout

- **Delivery:** one minor architect-pack release after RFC-0087's promotion gate
  is recorded. The new skill is additive; the
  existing design, diagram, and review entry points remain available. The OKF
  corpus is an experimental authoring source whose generated router is an
  ordinary read-only Skill at runtime.
- **Compatibility:** the generic current-state prompt changes route from a loose
  architecture description/reference snapshot to a bounded survey assessment.
  Explicit `reference.md` creation remains supported through its existing guide.
- **Rollback:** remove the new workflow primitive, restore migrated neutral
  references as ordinary hand-authored workflow references, remove the declared
  OKF bundle through its ownership-safe compiler path, and restore the prior
  first-value routing in a subsequent pack release. Saved Markdown assessments
  and profiler evidence remain ordinary user-owned files and require no migration.
- **Infrastructure:** none. The profiler runs locally and uses only Python's
  standard library plus optional read-only Git already present.
- **Deployment sequencing:** canonical OKF corpus and generated-router checks →
  workflow skill and tests → review rubric → pack metadata/self-host projection
  → product docs → dogfood and full gates → changelog/NOW generation.

## Risks

- The workflow may become too large for progressive disclosure. Keep the skill
  body concise and route only triggered local procedure references and OKF
  concept paths.
- Experimental OKF authoring could add maintenance burden or weak semantic
  routing. Keep it reference-only, commit deterministic output, freeze routing
  cases before evaluation, retain the hand-authored workflow trigger table, and
  make rollback to ordinary references possible without changing the public
  assessment contract.
- The heat map may create false quantitative authority. Expose raw dimensions,
  confidence, provenance, and the "attention, not severity" rule everywhere it
  appears.
- A profiler can become an attractive but misleading source of truth. Keep it
  optional, language-neutral at baseline, exact only where implemented, and
  subordinate to path tracing and scenario evidence.
- Changing the generic first-value route may surprise users who expected a
  `reference.md` write. Make survey read-only by default and retain an explicit,
  well-linked reference-architecture journey.
- Deep mode may imply capabilities unavailable in enterprise or adapter
  environments. Require capability discovery and approval, degrade visibly, and
  never install or invent a runtime.
- Product docs can describe the intended method before code matches it. Draft
  from the approved contract, then run a final verify-mode claim audit against
  the implemented skill before release.
- NOW projection can silently miss a malformed release heading. Use the
  free-standing release shape, generate from the changelog, and run the existing
  projection and rendered-anchor tests.

## Changelog

- 2026-08-21: Pre-execution review follow-up. Made RFC-0087 promotion and its
  follow-on ADR a fail-closed release prerequisite, moved maintainable corpus
  source packets out of the eventually frozen spec directory, aligned dogfood
  on all three enterprise modes, and restricted private context to governed
  connector-scoped knowledge surfaces rather than arbitrary URL/web fetchers.
- 2026-08-21: Review closure follow-up. Made one typed, claim-traceable
  desk-research source packet per corpus concept a T0 acceptance gate and made
  guide-driven dogfood exercise no-surface, in-repo-context, and explicitly
  authorized private-retrieval modes.
- 2026-08-21: Enterprise-knowledge-surface follow-up. Added optional targeted
  retrieval of organization engineering patterns, standards, landscape,
  ownership, operational reality, decisions, and in-flight work; moved the
  neutral eight-area taxonomy into the OKF corpus while keeping local facts,
  permissions, attribution, conflicts, and degradation in the workflow.
- 2026-08-21: Intent-taxonomy research follow-up. Replaced the three illustrative
  intents with a researched six-intent decision taxonomy; separated
  transformation from disposition, corrected operating context to portable
  acquisition questions and generic patterns, and required desk-research source
  packets for every corpus concept.
- 2026-08-21: Decision-intent follow-up. Added hardening, growth-readiness, and
  modernization/rewrite as an axis independent of repository shape; required
  intent-specific data, confidence floors, same-topology routing tests, and a
  comparative alternatives case before any rewrite recommendation.
- 2026-08-21: Corpus blueprint follow-up. Defined the architect pack's own
  minimum OKF ontology, repeatable concept body contract, agentic/knowledge
  sub-concepts, research-source packets, and five-pass authoring pipeline so T0
  produces a routed practitioner corpus rather than a shallow checklist dump.
- 2026-08-21: Human-gate architecture correction. Added a pack-local OKF
  architecture knowledge corpus and generated router as the progressive-depth
  plane shared by assessment, design, and review; kept workflow procedure and
  repository evidence outside the corpus; added deterministic routing,
  provenance, experimental-adoption, documentation, and rollback requirements.
- 2026-08-21: Adversarial review follow-up. Made missing evidence an explicit
  confidence limitation, moved file-safety construction choices out of the
  durable spec contract, and materialized T2's compilable red profiler stub.
- 2026-08-21: Security review follow-up. Restricted profiler output to resolved,
  explicitly approved assessment or temporary/workspace roots and required the
  projected skill to declare its untrusted-read and write boundaries without
  claiming unused network or credential access.
- 2026-08-21: Spec-plan review pass. Made Objective success observable,
  clarified standard-mode executable checks as separately authorized, reordered
  dogfood before changelog/NOW publication, added explicit verification modes to
  every task, and removed duplicate canonical prompt/fixture values from the
  plan.
- 2026-08-21: Spec-review hardening. Added the profiler confinement-layer
  contract, parity expectations against the repo's blessed file-safety helper,
  strict JSON/redacted-diagnostic tests, and a complete architect guide-surface
  audit requirement so product-documentation updates include every affected
  "how to use" route and intentional no-change decisions.
- 2026-08-21: Initial plan. Chose one cumulative six-stage conversation,
  standard as the general-request default, an attention heat map as navigation,
  one optional profiler, and guide-driven dogfood. Product-documentation
  pressure testing added exact discovery, how-to, reference, journey,
  changelog, and NOW-page obligations; it rejected separate per-architecture
  example pages and an executable report-heading validator.
