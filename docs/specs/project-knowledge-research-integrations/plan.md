# Plan: Project knowledge research integrations

- **Spec:** [`spec.md`](spec.md)
- **RFC:** [`RFC-0077`](../../rfc/0077-distill-knowledge.md) (Accepted)
- **ADRs:** [`ADR-0081`](../../adr/0081-canonical-project-knowledge-uses-per-topic-json.md) and [`ADR-0082`](../../adr/0082-project-knowledge-modes-separate-authority.md) (Accepted)
- **Status:** Done
- **Mode:** full

> **Plan contract:** this is the implementation strategy. It may change while
> Drafting or Executing; substantial changes are recorded in the changelog.

## Approach

Keep one research specification but implement it in two behavior waves. The
first wave changes the single episodic producer and its counter-evidence
reviewer: quick and the six non-survey typed products stay no-integration;
standard, applied, and deep survey outputs gain exact terminal capture gates;
`devils-advocate` gains one optional bounded
`CQ-REVIEW` enquiry and remains non-writing. The second wave makes every
stateful project phase explicit: start, digest, check, and status are non-gates;
project synthesis is the sole terminal producer. Desk-research-owned state and
configuration behavior remains unchanged.

A final delivery task adds one optional desk-research-to-core handoff, pins the
supporting-workflow no-integration boundary, synchronizes documentation and
release authorities, builds every adapter into temporary roots, and records
disposable repository-relative and personal-root journeys. It also updates the
living knowledge architecture once the behavior ships; the Draft architecture
is not presented as current runtime behavior before approval.

The recommended smallest implementation slice is T1. It proves the hardest
shared boundary in one skill family: exact mode-sensitive terminal timing,
typed capture, receipt-scoped distillation, independent direct-source
verification, a non-writing counter-evidence enquiry, and safe degradation for
out-of-repository products. T2 reuses that contract for the project lifecycle
only after the episodic pilot is reviewable.

## Assumptions surfaced

- The public capture and enquiry contracts are sufficient for
  repository-contained research; neither a schema nor runtime change is needed.
- Personal and external roots are capture-ineligible until separately approved
  provenance semantics exist. The implementation does not copy or mirror those
  products into a repository.
- `CQ-REVIEW` fits counter-evidence candidate checks but no existing question ID
  fits source selection, claim formation, confidence, or synthesis authority.
- Episodic and project research share a pack, security boundary, provenance
  decision, release authority, and verification surface; two ordered tasks are
  safer and smaller than two workspace entries.
- Desk-research's optional `verdict_status` update and output-root precedence
  are separate product contracts. This slice classifies their paths for
  project knowledge but does not reconcile or change them.

## Declined alternatives

- **Recombine review and research:** declined because review is a non-writing
  bounded enquiry consumer while research owns durable products, raw corpora,
  terminal capture gates, and configurable output roots.
- **Split episodic and project research into separate workspace entries:**
  declined because it would duplicate the same pack handoff, provenance rule,
  security controls, version bump, docs, and release verification. Ordered
  implementation tasks provide the useful review boundary without roadmap
  overhead.
- **Pilot capture on quick or digest output:** declined because an inline answer
  and intermediate matrices/memos do not provide a stable, independently
  reviewable research-product gate.
- **Make personal roots capture-capable by substituting a repository path:**
  declined as dishonest provenance. A new external-provenance contract would be
  separate scope and requires explicit evidence and approval.
- **Let project knowledge recommend sources or corroborate claims:** declined
  because the current competency-question vocabulary does not grant that
  authority and retrieved memory cannot independently verify itself.
- **Capture from `devils-advocate` or supporting workflows:** declined to avoid
  copying counter-evidence judgments, double capture, nested receipt ownership,
  and intermediate-product promotion. The outer terminal producer owns any
  handoff.
- **Reconcile desk-research state or configuration drift:** declined because
  project-check state and output-root precedence are owned by desk-research,
  not by the project-knowledge handoff. The integration consumes only the
  already-resolved artifact and current terminal/non-terminal result.

## Constraints

- Follow RFC-0077 and ADR-0081/ADR-0082 without amending their frozen bodies.
- Preserve the shipped schemas, topic format, public mode separation, private
  writer, capture identity, partition, privacy, quarantine, freshness,
  provenance, enquiry, and receipt-selection behavior.
- Preserve existing research products, citation and confidence methods, source
  independence, output-root precedence, retrieval permissions, and human-owned
  phase and state behavior.
- Edit canonical `.apm` sources first. Desk-research has no tracked self-host
  projection; use temporary build roots to verify all six declared adapters.
- Bump desk-research's patch version in both authorities and synchronize the
  root changelog and marketplace aggregate.
- Keep implementation and tests cross-platform and dependency-free. Add no new
  top-level directory, external service, database, package dependency, user
  spool, or external Git reference.
- Keep engineering/operational integration, adoption closeout, observation
  retention, derived-index scaling, external capture, and multi-project memory
  outside this implementation.

## Construction tests

- Existing project-knowledge suites remain the lower-level oracle for strict
  request parsing, public/private separation, mode isolation, privacy refusal,
  quarantine, source-relative freshness, enquiry abstention, prompt injection,
  repository confinement, and receipt-scoped distillation.
- Skill-local construction tests inspect ordering and required/forbidden seams
  in canonical sources. Tier-4 evals judge authority behavior with relevant,
  absent, hostile, stale, quarantined, irrelevant, and unverifiable knowledge.
- A pack-level boundary test covers every explicitly no-integration supporting
  skill, retrieval agent, and retriever script and validates the optional core
  handoff without turning metadata into dispatch.
- A disposable manual journey exercises repository-contained and personal-root
  outputs, every terminal and non-terminal path, receipt mismatch refusal,
  independent direct-source verification, unavailable provider, abstention,
  prompt injection, no fallback, and no phase advance.
- Temporary builds compare source behavior, integration metadata, tool and
  sandbox declarations, and pack runtime for `claude-code`, `kiro-ide`, `codex`,
  `copilot`, `cursor`, and `gemini`.

## Design (LLD)

### Interfaces & contracts

Eligible producers construct the unchanged
`knowledge-captured-observation.v1` request from explicit transient handoff
scratch. Its exact required fields are `contract_version`, `lesson`, `kind`,
`project_scope` (`paths`, `audience`), `competency_facets`, `destination_hint`
(`type`, `path`), `producer` (`workflow`, `workflow_version`), `semantic_gate`
(`name`, `artifact`), `provenance.sources`, `freshness_anchor` (`path`,
`digest`), `observed_at`, and `privacy_attestation`; optional `friction` and
`verification_route` appear only when their contract facts exist. The workflow
invokes the public `project-knowledge --capture` mode; it never imports or
locates the writer. A successful response supplies the only receipt IDs
eligible for an optional same-gate
`selection_mode: workflow-receipts` distillation request. Traces to AC2-AC7 and
AC13-AC18.

Nested deep and project-synthesis producers construct one unchanged public
enquiry query and pass its receipt envelope to every `devils-advocate` pass;
standalone `devils-advocate` constructs one for its target. The query uses
caller `skill`, a sanitized target label, fixed project scope,
consequential risk, and `CQ-REVIEW`, with one project-knowledge query and no
project-knowledge refinement. That budget does not reduce independent web or
other direct-source retrieval under the research method. The result is a
visibly delimited candidate-check envelope. No other research workflow gains
enquiry. Traces to AC8-AC12 and AC28.

No schema, Python runtime, private writer, topic body, or question-vocabulary
file changes. The pack manifest declares an optional handoff from selected
research skills to core's public provider. Traces to AC15-AC25.

### Component / module decomposition

- `desk-research` owns quick/standard/applied/deep classification, transient
  handoff scratch, repository eligibility, terminal capture, and same-gate
  receipt distillation. It delegates the deep challenge artifact but retains
  the outer deep gate.
- Deep and project-synthesis outer producers own the one-query budget and pass
  one sanitized envelope to nested `devils-advocate`; standalone review owns
  its one target-scoped query. `devils-advocate` owns independent counter-source
  verification, its counterpoints product, and the absolute no-capture rule.
- Project start, digest, check, and status own only their existing scaffold,
  intermediate, stop-signal, and orientation behavior. Project synthesis owns
  the terminal project handoff after both normative products and challenge
  passes complete.
- Supporting research skills, retrieval agents, and scripts remain unchanged
  no-integration components; pack construction coverage prevents a later nested
  capture or enquiry seam from appearing accidentally.
- Pack docs, public guides, integration metadata, and living architecture state
  the producer/reviewer/product-authority split after implementation ships.

Traces to AC1-AC27.

### State & control flow

```text
research invocation
  -> resolve mode, target, project scope, and output path
  -> run research-owned retrieval and direct-source verification
  -> write owning research product(s)
  -> run confidence, gap, moderation, and mode-required challenge passes
  -> exact terminal gate
       | quick/non-terminal/incomplete -> no knowledge operation
       | no admissible residue         -> no capture request
       | output outside Git root       -> exact capture-ineligible result
       | provider absent               -> exact unavailable result
       | eligible residue              -> public typed capture
                                             | no receipts -> no distillation
                                             | receipts    -> same-gate receipt distillation
  -> research product stays normative and unchanged by knowledge
```

For a nested `devils-advocate`, the outer producer resolves the common target
and honest project scope, forms a privacy-minimized label, issues at most one
`CQ-REVIEW` request before the first counter-position enumeration, and passes
the same delimited envelope to every per-finding pass and unchanged rerun.
Standalone review follows the same budget for its one target. A second nested
invocation cannot query; no envelope or no safe label means
`project-knowledge not requested`. Direct counter-sources remain independently
retrieved. Provider absence means `project-knowledge unavailable`; neither
outcome changes the review method. Traces to AC1-AC18 and AC28.

### Failure, edge cases & resilience

- Resolve and canonicalize both Git root and output artifact before forming any
  path fields. Missing Git, non-regular products, symlink escapes, ambiguous
  containment, personal roots, and external roots fail closed for capture with
  the exact ineligible result and without provider discovery.
- Provider discovery failure is fail-open for completing research and
  fail-closed for memory: emit the named unavailable result and write no
  fallback. A provider error or rejected request does not lead to a distillation
  attempt.
- An empty eligible enquiry supplies no candidate checks. Stale, quarantined,
  malformed, irrelevant, privacy-refused, or source-unverified evidence is
  excluded or abstaining. Research proceeds only when its own direct evidence
  is sufficient; otherwise it caveats, omits, or abstains.
- Untrusted retrieved text cannot cause a tool call, source redirect, scope
  change, citation, confidence upgrade, counter-evidence suppression, artifact
  write, or knowledge capture. Captured residue is producer-authored and
  privacy/instruction triaged before persistence.
- A partial product, empty/missing project prerequisite, interrupted challenge,
  or failed final verification never reaches a gate. Re-entry does not infer
  prior receipts from artifacts or journals.

Traces to AC2-AC22.

### Dependencies & integration

Desk-research declares one optional `handoff` integration to core with
consumers `skill:desk-research`, `skill:desk-research-project-synthesize`, and
`skill:devils-advocate`, and provider `skill:project-knowledge`. Metadata
describes both terminal capture and bounded review enquiry but does not execute
either and creates no hard install dependency. Installations without core use
the named skip paths. No dependency version or Python package changes. Traces
to AC23-AC25.

## Tasks

### T1: Episodic terminal surveys capture reusable practice and counter-review enquiry stays non-writing

**Depends on:** none

**Verification mode:** TDD construction tests + Tier-4 behavior evals.

**Touches:**
`packs/desk-research/.apm/skills/desk-research/SKILL.md`,
`packs/desk-research/.apm/skills/desk-research/evals/evals.json`,
`packs/desk-research/.apm/skills/devils-advocate/SKILL.md`,
`packs/desk-research/.apm/skills/devils-advocate/evals/evals.json`,
`packs/desk-research/tests/skills/desk-research/test_project_knowledge_boundary.py`,
and
`packs/desk-research/tests/skills/devils-advocate/test_project_knowledge_boundary.py`.

**Tests:**

- Construction tests pin quick's absolute no-integration rule and the complete
  standard, applied, and deep gate order, including no calls for created-only,
  abandoned, incomplete, missing-confidence, missing-gap, missing-moderator, or
  missing-counterreview products. They enumerate every current non-survey type
  and pin terminal as well as incomplete no-integration paths. Implements
  AC1-AC4 and AC28.
- Request tests pin typed fields, explicit transient scratch, allowed residue,
  normative exclusions, canonical repository confinement, every T1 gate's
  exact row in the spec's capture-field table, exact personal-root
  ineligibility, exact provider unavailability, public seam use, and same-gate
  receipt selection. Implements AC13-AC19.
- Counter-review tests pin enquiry after target/scope resolution and before
  enumeration; exact query fields/budget; sanitized-label rejection/redaction;
  one outer envelope across all nested per-finding passes and unchanged reruns;
  no honest scope; unavailable, empty, and abstaining results; no capture; and
  independent counter-source verification. Implements AC8-AC12 and AC15.
- Behavior evals inject source-selection, permission, scope, citation, claim,
  confidence, counter-evidence, and verdict instructions and attempt
  self-validation. The same claims and dispositions must require independent
  direct evidence with or without knowledge. Implements AC10-AC14 and AC19.
- Existing Tier-A activation queries run unchanged for `desk-research` and
  `devils-advocate`; their descriptions and trigger cues do not change. A cue
  change is plan drift and requires adding the corresponding
  `eval_queries.json` path before implementation continues. Implements AC29.
- stub: true

```python
def test_ephemeral_quick_and_incomplete_surveys_never_capture():
    raise NotImplementedError  # STUB: AC2-AC4


def test_non_survey_typed_products_are_explicit_no_integration_paths():
    raise NotImplementedError  # STUB: AC2, AC28


def test_terminal_survey_uses_typed_capture_and_only_same_gate_receipts():
    raise NotImplementedError  # STUB: AC13-AC18


def test_counterreview_enquiry_cannot_choose_sources_or_validate_itself():
    raise NotImplementedError  # STUB: AC8-AC12


def test_nested_counterreview_reuses_one_sanitized_envelope():
    raise NotImplementedError  # STUB: AC8, AC9
```

**Approach:**

1. Add failing construction tests for mode gates, public/private separation,
   non-survey no-integration paths, repository eligibility, exact skips,
   normative exclusions, and receipts.
2. Add the smallest explicit transient-handoff and terminal-gate sections to
   `desk-research`; do not change its research pipeline or products.
3. Add one outer-target-bounded enquiry branch and authority boundary to
   `devils-advocate`, including sanitized labels and nested-envelope reuse, then
   add hostile-evidence behavior evals for both skills.

**Done when:** the episodic family proves every survey and non-survey terminal
and non-terminal path, personal outputs stay honest, receipt scope is
gate-local, and one privacy-minimized review envelope cannot replace
independently sourced counter-evidence or its artifact authority.

### T2: Project lifecycle has one terminal synthesis handoff and explicit non-gates

**Depends on:** T1

**Verification mode:** TDD construction tests + Tier-4 behavior evals.

**Touches:**
`packs/desk-research/.apm/skills/desk-research-project-start/SKILL.md`,
`packs/desk-research/.apm/skills/desk-research-project-digest/SKILL.md`,
`packs/desk-research/.apm/skills/desk-research-project-check/SKILL.md`,
`packs/desk-research/.apm/skills/desk-research-project-status/SKILL.md`,
`packs/desk-research/.apm/skills/desk-research-project-synthesize/SKILL.md`,
`packs/desk-research/.apm/skills/desk-research-project-synthesize/evals/evals.json`,
`packs/desk-research/tests/skills/desk-research-project-start/test_project_knowledge_boundary.py`,
`packs/desk-research/tests/skills/desk-research-project-digest/test_project_knowledge_boundary.py`,
`packs/desk-research/tests/skills/desk-research-project-check/test_project_knowledge_boundary.py`,
`packs/desk-research/tests/skills/desk-research-project-status/test_project_knowledge_boundary.py`,
and
`packs/desk-research/tests/skills/desk-research-project-synthesize/test_project_knowledge_boundary.py`.

**Tests:**

- Start, digest, check, and status construction tests assert exact scaffold,
  intermediate, check-only, and status-only knowledge classifications and
  forbid capture, distillation, enquiry, receipt, private writer, journal,
  fallback, transcript, and raw-corpus seams. Implements AC1 and AC5-AC6.
- Project-check coverage proves its current optional `verdict_status` update is
  a desk-research-owned nonterminal action that cannot trigger a knowledge
  operation, while preserving no automatic phase transition and the human
  decision. Output-root resolution is exercised only to pass the already-
  resolved project path into capture-eligibility checks; precedence is not
  asserted or changed. Implements AC6, AC17-AC18, and AC21.
- Synthesis tests pin both synthesis products, the linked counterpoints
  artifact, prerequisite handling, confidence, triangulation, gaps, the
  required per-finding challenge pass, no phase advance, exact
  terminal capture ordering, the project-synthesis gate's exact row in the
  spec's capture-field table, public request construction, personal-root
  ineligibility, no fallback, and receipt-scoped distillation. Implements AC7
  and AC13-AC19.
- Behavior evals prove project knowledge cannot affect sources, citations,
  claims, confidence, counter-evidence, verdicts, governance conclusions, or
  phase and cannot compensate for an empty or insufficient corpus. Implements
  AC10-AC14 and AC19.
- Existing Tier-A activation queries run unchanged for project-start and
  project-status. Digest/check/synthesize retain their documented interior-step
  Tier-A exclusion; synthesis's Tier-4 eval changes only behavior judgment. Any
  trigger-description change returns to plan review. Implements AC29.
- stub: true

```python
def test_project_scaffold_digest_check_and_status_are_never_capture_gates():
    raise NotImplementedError  # STUB: AC5, AC6


def test_project_check_optional_state_write_is_not_a_knowledge_gate():
    raise NotImplementedError  # STUB: AC6, AC21


def test_project_synthesis_requires_both_products_before_typed_capture():
    raise NotImplementedError  # STUB: AC7, AC13-AC18
```

**Approach:**

1. Add explicit no-integration boundary sections to the four non-gates without
   changing their desk-research-owned state or configuration behavior.
2. Add the terminal handoff to synthesis by reusing T1's eligibility, scratch,
   typed request, failure, and receipt language without adding shared runtime
   code.
3. Add focused construction tests and hostile-evidence synthesis evals while
   preserving every product schema and human phase transition.

**Done when:** the lifecycle has one observable terminal producer, all other
phases are proven non-gates, and its two normative products retain exclusive
research and governance authority.

### T3: Pack boundary, publication parity, and end-to-end research evidence are complete

**Depends on:** T1, T2

**Verification mode:** Goal-based checks + manual QA + specialist review.

**Touches:**
`packs/desk-research/tests/pack/test_project_knowledge_boundaries.py`,
`packs/desk-research/pack.toml`,
`packs/desk-research/.claude-plugin/plugin.json`,
`packs/desk-research/README.md`,
`packs/desk-research/JOURNEY.md`,
`packs/desk-research/DESIGN.md`,
`guides/desk-research/reference/desk-research-pack.md`,
`guides/desk-research/explanation/episodic-vs-project-research.md`,
`guides/desk-research/how-to/research-pipelines.md`,
`docs/specs/project-knowledge-research-integrations/spec.md`,
`docs/specs/project-knowledge-research-integrations/plan.md`,
`docs/specs/project-knowledge-research-integrations/notes/manual-qa.md`,
`docs/specs/README.md`,
`docs/architecture/knowledge-capture.md`,
`docs/knowledge/README.md`,
`docs/product/changelog.md`,
`.claude-plugin/marketplace.json`, and
`workspace.toml`.

No tracked desk-research projection exists. Temporary outputs verify every
declared adapter without adding `.agents`, `.claude`, `.codex`, `.github`,
`.kiro`, `.cursor`, or `.gemini` projection files to the repository. Any
additional generated or version-authority file is scope evidence to review, not
permission for an open-ended edit.

**Tests:**

- The pack boundary test enumerates all six non-survey typed products,
  `build-outline`, `source-map`,
  `identify-perspectives`, `compare-hypotheses`, `decision-archaeology`, both
  retrieval agents, and both retriever scripts and forbids direct knowledge
  operations. It pins the optional core handoff's exact consumers, provider,
  timing, purpose, and fallback. Implements AC20, AC23, and AC28.
- Documentation checks describe only the project-knowledge handoff and preserve
  desk-research's existing state/configuration claims byte-for-byte unless an
  integration sentence must distinguish them from knowledge writes. Implements
  AC21.
- Run every new test file in an independent pytest process, then the current
  desk-research, project-knowledge contract/mode/privacy/enquiry/capture/
  distillation, pack-schema, and integration-metadata suites. Implements
  AC1-AC25 and AC28.
- Build desk-research to temporary roots for all six adapters and compare
  canonical behavior, metadata, and existing tool/sandbox boundaries. Run
  behavior eval validation, catalogue lint/verify, Ruff, targeted mypy if
  Python changes, `SKIP_SAST=1 make build-check`, and the repository security
  scan. Implements AC22-AC25.
- Prove every modified registered prompt-triggered skill retains byte-unchanged
  Tier-A activation queries and passes the activation-query schema, coverage,
  runner-self-test, and skill-description anchor checks. Retain the documented
  interior-step exclusions. The model-backed activation harness remains
  report-only evidence: run it when the installed host can complete it, or
  record a named environment limitation without claiming a live score.
  Implements AC29.
- In disposable projects, exercise standard/applied/deep, every project phase,
  standalone and nested counter-review, one-envelope reuse across per-finding
  passes, privacy-minimized task labels, repository/personal output roots,
  absent/no-residue/unavailable/abstaining/hostile knowledge, receipt mismatch,
  independent source verification, and zero fallback/phase mutation. Record
  redacted pass/fail evidence only. Implements AC1-AC26 and AC28.
- Update the architecture only after implementation is present, then assert
  workspace dependencies remain review -> research -> engineering/operations
  -> adoption and the conditional shaping items remain outside the build
  sequence. Implements AC26-AC27.
- Run adversarial, security, and quality implementation review until clean.
  Scan changed bytes for the prohibited comparison identifier and record only
  pass/fail. Implements AC11-AC27.
- no stub (goal/manual mode).

**Approach:**

1. Add the pack-level no-integration inventory and optional handoff, then bump
   desk-research from 1.1.4 to the next patch in both version authorities.
2. Synchronize owning pack docs, public reference/explanation/how-to guidance,
   living knowledge architecture, changelog, marketplace, spec index, and
   workspace lifecycle state.
3. Run targeted tests, all-adapter temporary builds, repository gates, and the
   disposable manual matrix. Store only redacted verification evidence.
4. Harden through specialist review and stop at the ordinary human delivery
   gate.

**Done when:** every selected and supporting workflow has an observable
integration boundary, all published forms agree, the full security and
provenance matrix is evidenced, and the implementation is ready for ordinary
human delivery approval.

## Rollout

1. Land T1 as the smallest pilot. It is independently reviewable and reversible
   within the episodic producer/counter-review family.
2. Land T2 after T1's gate, eligibility, and receipt language is accepted. No
   project phase invokes the handoff until terminal synthesis.
3. Complete T3 only with both waves present, publish one coordinated patch, and
   update workspace status to Shipped after normal implementation review and
   human delivery approval.
4. Rollback removes the optional handoff and integration prose/evals/tests and
   restores the prior patch metadata and documentation. Existing desk-research
   behavior, research products, and project-knowledge records are not rewritten
   or deleted.

## Risks

- **Stored prompt injection or corpus leakage:** source content may look like a
  reusable observation. Explicit producer-authored scratch, privacy and
  instruction triage, strict normative exclusions, and hostile-residue tests
  keep raw or instructional material out of durable knowledge.
- **Research authority contamination:** retrieved memory may anchor source
  choice, confidence, or verdicts. The enquiry is limited to counter-review
  candidate checks and every adopted check needs new independent direct-source
  support.
- **False terminal gates:** early file creation can look complete. Mode-specific
  ordering tests require all source, synthesis, confidence, gap, moderation,
  triangulation, and challenge passes before a handoff.
- **Fabricated personal-root provenance:** the public schema has no external
  artifact representation. Canonical containment and the exact ineligible
  branch fail closed without copying, rewriting, or probing the provider.
- **Nested or duplicate capture:** deep research and project synthesis invoke
  supporting review/synthesis methods. Only the outer terminal producer can
  capture and its receipts are invocation-local.
- **Phase or product mutation:** integration could accidentally turn a stop
  signal into state or memory into normative content. Read-only phase tests and
  product-authority evals pin the human and artifact ownership boundaries.
- **Cross-platform projection drift:** desk-research is user-scoped and has no
  tracked projection oracle. Six explicit temporary builds plus metadata and
  permission comparisons cover the distribution boundary.
- **Overlarge slice:** episodic and project workflows differ. T1 and T2 remain
  separately reviewable and ordered; if T1 reveals a contract change is
  necessary, implementation stops before T2 and returns to spec approval.

## Changelog

- 2026-08-18: Implementation review aligned AC29 verification with the
  repository's report-only activation-harness posture. Immutable Tier-A inputs
  and static contract checks remain the shipping gate; a managed host that
  cannot complete the model-backed runner records a named limitation. Product
  scope, task order, and workflow behavior are unchanged.
- 2026-08-17: Initial full-mode plan keeps research as one specification with
  two ordered implementation waves. The shared pack, optional core handoff,
  provenance rule, source-verification authority, release boundary, and parity
  suite outweigh the gate differences; exact per-workflow non-gates prevent the
  grouping from hiding lifecycle semantics. No workspace dependency amendment
  is proposed.
