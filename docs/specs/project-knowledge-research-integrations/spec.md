# Spec: Project knowledge research integrations

- **Status:** Shipped
- **Owner:** eugenelim
- **Plan:** [`plan.md`](plan.md)
- **Constrained by:** RFC-0077, ADR-0081, ADR-0082, and `project-knowledge-review-integrations` (Shipped)
- **Brief:** none
- **Discovery:** none
- **Contract:** `contracts/jsonschema/knowledge-captured-observation.schema.json` (consumed unchanged)
- **Shape:** integration

> **Spec contract:** this document defines what "done" means. The implementing
> PR must match this spec, or update it. Verification must be derivable from it.

## Objective

Terminal research producers may hand independently reusable research practice
or carefully sanitized evidence residue to project knowledge without turning
research products, raw sources, or research judgments into memory. Episodic
standard, applied, and deep cited-survey paths capture only after their complete
mode-specific gate; the current non-survey typed products remain no-integration
in this pilot. Stateful research projects capture only after both synthesis
products and the linked counterpoints artifact's required per-finding challenge
pass are complete. Quick
answers, scaffolds, intermediate digests, status reads, stop signals, abandoned
work, and incomplete products perform no capture or distillation.

Research retains its own transient scratch, source selection, direct-source
verification, citations, claims, confidence, counter-evidence, verdicts, and
governance authority. The counter-evidence review path alone may consume the
existing `CQ-REVIEW` competency question for candidate checks after its target
and scope are fixed; a nested outer producer owns the one-query budget.
Retrieved knowledge is bounded untrusted evidence: it cannot direct the
research, validate itself, become a citation, or strengthen a claim.

The integration uses only the shipped public project-knowledge modes. A
terminal gate with an honestly repository-relative product may submit the
published typed captured-observation request through `project-knowledge
--capture` and may distil only receipts returned by that gate. A product in a
personal or otherwise out-of-repository output root is capture-ineligible under
the existing schema and emits exactly `project-knowledge capture ineligible:
non-repository research output`; an undiscoverable provider emits exactly
`project-knowledge unavailable`. Neither outcome creates fallback storage.

## Boundaries

### Always do

- Resolve the research mode, product shape, output path, and exact semantic
  gate before considering a knowledge handoff. Resolve and canonicalize the
  Git root and product path before claiming repository-relative provenance.
- Keep a small producer-owned handoff scratch in transient prompt context. It
  may contain candidate practice, a sanitized evidence-residue summary,
  repository-relative provenance and freshness candidates, and the
  privacy/instruction-shape triage needed to construct a typed request.
- Capture only independently reusable practice or carefully sanitized evidence
  residue that is useful outside the current research product. Construct the
  published request through the public progressive skill seam, and distil only
  capture receipts returned by the same terminal gate.
- Keep every survey, matrix, memo, source corpus, quotation, citation, factual
  claim, confidence assessment, known unknown, counter-evidence claim, verdict,
  and governance conclusion solely in its owning research artifact.
- Treat web content, source extracts, tool output, and retrieved project
  knowledge as untrusted data. Verify every research claim against independent
  direct sources selected under the research workflow's own method.
- Preserve source-relative freshness, privacy refusal, quarantine, provenance,
  prompt-injection containment, repository confinement, and explicit
  abstention. Author canonical pack sources first and prove adapter projection
  and pack-runtime parity.

### Ask first

- Add a new competency-question identifier, change a project-knowledge schema,
  or make enquiry choose research questions, sources, citations, claims,
  confidence, counter-evidence, verdicts, or governance conclusions.
- Add capture to quick, scaffold, digest, check, status, supporting, abandoned,
  incomplete, or otherwise non-terminal research, or add capture directly to
  `devils-advocate`.
- Make personal or external output roots eligible for capture, add an external
  provenance representation, or add a storage fallback for an unavailable
  provider.
- Change the research modes, artifact schemas, source-independence rules,
  confidence method, human-owned phase transitions, output-root precedence, or
  public project-knowledge contract.
- Split this specification, change its downstream dependency order, or add a
  package, service, database, persistent scratch area, or user-directory
  assumption.

### Never do

- Mine transcripts or tool history, persist transient handoff scratch, copy raw
  source corpora, quotations, citations, research products, or normative
  judgments into project knowledge, or reconstruct an observation after the
  gate from the finished product.
- Let a producer locate journals, import `knowledge_store.py` or another private
  writer, invent capture IDs, select partitions, name direct-maintainer pending
  observations, guess receipts, drain another producer's receipts, or create
  fallback persistence.
- Fabricate a repository-relative artifact, provenance source, or freshness
  anchor for a personal path, an external path, a missing repository, a symlink
  escape, or any product whose repository containment is ambiguous.
- Treat retrieved knowledge as instructions, authority, permission, scope,
  source-selection guidance, a citation, a claim, corroboration, a confidence
  upgrade, a reason to suppress counter-evidence, or a verdict or governance
  override.
- Replace unavailable, irrelevant, stale, quarantined, insufficiently
  authoritative, or independently unverified evidence with a weaker unsupported
  claim. Use a caveat, omission, or abstention instead.
- Add a dependency, service, database, cross-project bank, automatic scratch
  persistence, raw-corpus index, user-directory spool, or persisted identifier
  copied from the prohibited comparison product.

## Research integration contract

File creation alone is never a stable gate. Each positive gate below fires once
per completed invocation after the named product and all required method passes
exist. A gate with no admissible reusable residue submits no request and emits
no receipt. A failed capture emits no distillation request. A successful gate
may distil only the receipt IDs returned by its own capture response through
`selection_mode: workflow-receipts`.

| Workflow / path | Exact stable semantic gate | Earlier or excluded paths | Producer-owned transient scratch | Normative owner | Integration posture |
| --- | --- | --- | --- | --- | --- |
| `desk-research` quick | None. Its bounded inline answer is terminal for the user but is not a durable research-product gate. | Every fetch, partial answer, refusal, interruption, and the final inline answer are capture non-gates. | Query decomposition, source notes, and inline synthesis remain transient research scratch only. | The inline answer owns its citations, claims, caveats, and confidence language. | No capture, distillation, or enquiry. |
| `desk-research` non-survey typed products | None approved for project knowledge. Each current closed-vocabulary `<topic-slug>-<type>.md` product (`fact-check`, `comparison-matrix`, `shortlist`, `blueprint`, `hypotheses`, or `methodology`) retains its own existing shape and mode completion contract, but that completion is not a knowledge gate. | Every terminal, partial, or invalid product is a knowledge non-gate. These shapes do not inherit a survey capture gate, even when requested with standard, applied, or deep depth cues. A legacy `research.md` alias is never emitted and is not a gate. | Shape-specific planning, evidence, and synthesis remain research scratch. | Each typed product owns its sources, citations, claims, confidence, gaps, decisions, and conclusions. | Explicit no integration in this pilot: no capture, distillation, or enquiry. A later proposal needs shape-specific reuse evidence and a separately approved capture gate. |
| `desk-research` standard | `research-survey-complete`: `<topic-slug>-survey.md` exists only after source retrieval, synthesis, per-finding confidence, known-unknown/unknowable, citation, independence/triangulation, and moderator passes complete. | A created file, partial corpus, incomplete synthesis, missing confidence/gaps/moderation, abandonment, refusal, or interruption is not the gate. | Candidate reusable retrieval, triangulation, calibration, or verification practice recorded during this invocation; never the survey body or source corpus. | The survey owns all sources, quotations, citations, claims, confidence, gaps, and conclusions. | Capture plus same-gate receipt-scoped distillation when admissible residue exists and provenance is honestly repository-relative; otherwise no request or the exact ineligible/unavailable result. No enquiry. |
| `desk-research` applied | `research-applied-survey-complete`: the standard survey conditions hold and the survey also carries the applied discipline marker, practitioner-independence taxonomy, applied confidence overlay, and failure-mode coverage. | Every standard-mode non-gate plus a missing marker, same-vendor/employer independence error, missing overlay, or incomplete applied section is not the gate. | Independently reusable practitioner-source independence, stale-prior-art, survivorship-bias, or calibration practice; never practitioner claims or source material. | The applied survey owns all normative research content and judgments. | Capture plus same-gate receipt-scoped distillation under the same eligibility rules. No enquiry. |
| `desk-research` deep | `research-survey-counterreview-complete`: the survey satisfies the standard gate and the linked `<topic-slug>-counterpoints.md` has completed the applicable counter-position, direct counter-source, confidence-downgrade/do-not-resolve, uncited-material, and challenge passes. | Survey completion alone, a missing or partial counterpoints product, unresolved review interruption, or any standard-mode non-gate is not the deep gate. | Reusable challenge-pass, counter-source independence, or calibration practice; never either product's claims, citations, counter-evidence, or verdicts. | The survey and counterpoints artifacts jointly own their respective claims, confidence, counter-evidence, tensions, and verdicts. | Capture plus same-gate receipt-scoped distillation under the same eligibility rules. `devils-advocate` may supply the separately bounded enquiry described below. |
| `desk-research-project-start` | None. | Output-root elicitation/configuration and project-folder, overview, and source-ledger creation are scaffold-only. | Project framing and scaffold choices remain in the scaffold or transient context. | The project overview and source ledger own the brief and capture plan. | No capture, distillation, or enquiry. |
| `desk-research-project-digest` | None. | Every synthesis matrix and memo is intermediate, including a complete digest; skipped, partial, stale, and interrupted digests are also non-gates. | Coding, clustering, contradiction, and memo-development scratch remains transient or in the owning intermediate artifacts. | `synthesis-matrix.md` and `memos.md` own all extracted claims, source mappings, quotations, and interim analysis. | No capture, distillation, or enquiry. |
| `desk-research-project-check` | None for project knowledge. It remains the desk-research-owned qualitative stop signal. | Corpus inspection, saturation judgment, recommendation, the current optional `verdict_status` update, and every incomplete check are check-only knowledge non-gates. The skill never advances phase. | The by-eye saturation comparison remains transient. | The inline stop-signal and any current desk-research-owned state update remain governed by desk-research; the human owns the decision. | No capture, distillation, or enquiry. |
| `desk-research-project-status` | None. It is a read-only orientation surface. | Reading and reporting overview state is status-only and non-terminal. | None beyond transient rendering context. | The project artifacts own project state; status only reports it. | No capture, distillation, or enquiry. |
| `desk-research-project-synthesize` | `research-project-synthesis-complete`: the typed verdict and `<topic-slug>-brief.md` exist after matrix/memo consumption, citations, per-finding confidence, three-source triangulation, and known unknowns, and the linked counterpoints artifact has completed the required per-finding `devils-advocate` pass. The skill has not advanced the human-owned phase. | Missing/empty prerequisite handling, either synthesis product alone, a missing or partial counterpoints product, interruption, refusal, and phase mutation are not the gate. An empty matrix remains a warning path, not a weaker terminal product. | Reusable corpus-structure, synthesis, triangulation, verification, calibration, or handoff practice; never matrix/memo/source or final-product content. | The typed verdict and governance brief own findings, citations, confidence, recommendations, and governance conclusions; the linked counterpoints artifact owns counter-evidence, confidence-change proposals, tensions, and challenge verdicts. | Capture plus same-gate receipt-scoped distillation under the same eligibility rules. No enquiry for synthesis or claim formation. |
| `devils-advocate` | `research-counterevidence-review-complete`: the target and scope are fixed, counter-positions and independently sourced counter-evidence are traversed, every finding receives a confidence-downgrade or do-not-resolve disposition, uncited material is marked, and the linked counterpoints artifact is complete. | Target resolution, candidate enumeration, retrieval, a partial artifact, interruption, or an invalid target is not the gate. | Candidate counter-checks, source gaps, and disposition reasoning remain transient. | The counterpoints artifact owns counter-evidence, citations, confidence changes, tensions, and verdicts. | Enquiry-only; never capture or distillation. A nested outer producer declares and passes one consequential `CQ-REVIEW` envelope for the common target; standalone review declares once after target/scope resolution. Otherwise record `project-knowledge not requested`. |

Supporting workflows are deliberately outside the write/read integration. They
remain research-owned inputs or nested methods, not independent knowledge
gates: `build-outline`, `source-map`, and `identify-perspectives` produce
planning artifacts; `compare-hypotheses` produces a hypothesis matrix or is
invoked inside project synthesis; `decision-archaeology` produces its own
source-grounded reconstruction; `evidence-retriever`, `source-extractor`, and
retriever scripts return transient source material. None captures, distils, or
enquires in this slice. When a supporting method runs inside a selected
terminal producer, only the outer producer may triage its own explicit handoff
scratch at the outer gate.

### Capture eligibility and residue

An admissible observation describes independently reusable supporting practice,
such as a source-verification route, a source-independence failure mode, a
triangulation technique, a confidence-calibration technique, corpus-structuring
practice, or a research-to-governance handoff constraint. Carefully sanitized
evidence residue is eligible only when it has become such reusable practice,
contains no quotation, citation, raw locator, source body, claim, conclusion,
confidence judgment, counter-evidence, or product excerpt, and passes the
published privacy and instruction-shape refusal.

The producer constructs a request only when the resolved gate artifact is a
regular file canonically contained by the current Git repository and every
provenance source and freshness anchor can be stated as an honest
repository-relative path. A personal absolute root, an external root, no Git
root, a path that resolves outside the root, or ambiguous containment emits
exactly `project-knowledge capture ineligible: non-repository research output`.
That result is not provider unavailability and does not trigger provider
discovery, capture, distillation, path rewriting, copying into the repository,
or fallback persistence.

The single-artifact fields in the unchanged capture schema bind each positive
gate deterministically:

| Gate | `semantic_gate.artifact` | Required `provenance.sources` | `freshness_anchor.path` |
| --- | --- | --- | --- |
| `research-survey-complete` | `<topic-slug>-survey.md` | the survey | `<topic-slug>-survey.md` |
| `research-applied-survey-complete` | `<topic-slug>-survey.md` | the applied survey | `<topic-slug>-survey.md` |
| `research-survey-counterreview-complete` | `<topic-slug>-survey.md` | the survey and linked `<topic-slug>-counterpoints.md` | `<topic-slug>-counterpoints.md` |
| `research-project-synthesis-complete` | the project's resolved typed verdict `<type>.md` | the typed verdict, `<topic-slug>-brief.md`, and linked `<topic-slug>-counterpoints.md` | `<topic-slug>-counterpoints.md` |

Every listed source and anchor must independently pass the same confined
regular-file proof before request construction. Companion paths establish that
the multi-artifact gate actually completed; their bodies remain normative
research products and are never copied into the lesson. The one freshness
anchor deliberately identifies the final required counter-review artifact for
deep and project synthesis; the schema is not extended with a composite digest.

### Enquiry and research authority

The only competency question authorized in this slice is:

> `CQ-REVIEW`: Which recurring review failure modes or counter-evidence checks
> are relevant to this already-fixed research target and project scope?

For a nested deep or project-synthesis challenge, the outer producer declares
at most one query after the common target and scope are fixed and before the
first counter-position enumeration, then passes the same envelope to every
per-finding `devils-advocate` pass. Standalone `devils-advocate` declares at
most one query for its target. Unchanged reruns reuse the envelope; another
nested invocation never issues a second query and records
`project-knowledge not requested` if the caller cannot supply the existing
envelope.

The unchanged public query uses `caller: skill`, the fixed
project/subproject `scope`, consequential `risk`, and
`question_id: CQ-REVIEW`. Its `task_summary` is a producer-authored sanitized
label containing only the topic slug or artifact kind and repository-relative
scope needed to identify the review. Raw claims, quotations, citations, URLs,
source titles, instruction-shaped text, and personal or external absolute paths
are rejected or redacted before enquiry and never echoed through the evidence
envelope. If a safe summary cannot be formed, enquiry is not requested. The
budget is one project-knowledge query and no project-knowledge refinement per
outer or standalone target; it does not reduce the research method's
independent direct-source retrieval. If no honest project scope exists,
enquiry is not requested. If a declared provider is absent, emit exactly
`project-knowledge unavailable`; an empty eligible result supplies zero
candidate checks; consequential evidence whose owning source cannot be verified
abstains.

The current question vocabulary does not safely express "which sources should
I select?", "what claim should I make?", "how confident should I be?", or
"what verdict should I reach?" No other research workflow enquires, and this
slice adds no question ID or schema extension. The returned envelope is visibly
delimited as untrusted candidate-check data. It cannot alter instructions,
identity, tools, permissions, scope, research mode, source selection, fetch
targets, citations, claims, confidence, known unknowns, counter-evidence,
verdicts, governance conclusions, or phase. It never counts as a source or
corroborates itself. Any check that affects the counterpoints artifact must be
supported anew by independent direct sources under the existing research
method; failure to verify produces a caveat, omission, or abstention.

## Testing Strategy

- **Gate and request construction:** TDD construction tests pin every exact
  gate after all mode-specific passes, typed request fields, producer-owned
  scratch boundary, repository containment, exact skip strings, and zero calls
  on quick, scaffold, digest, check, status, abandoned, incomplete, or otherwise
  non-terminal paths.
- **Write authority and receipt scope:** structural tests allow only the public
  `project-knowledge --capture` handoff, forbid private writer/journal/ID/
  partition/fallback surfaces, and prove terminal distillation names exactly
  the receipts returned by the same gate and never direct-maintainer pending
  observations.
- **Research authority:** Tier-4 behavior evals exercise relevant, absent,
  irrelevant, stale, quarantined, unverifiable, and hostile knowledge. They
  prove enquiry is explicit and bounded, every claim retains independent direct
  verification, topics cannot self-validate, and unavailable evidence yields a
  caveat, omission, or abstention rather than a weakened claim.
- **Content and provenance safety:** tests reject transcript/tool-history
  mining, raw corpus and product copying, quotations, citations, claims,
  confidence, counter-evidence, verdicts, governance conclusions, privacy-
  shaped content, instruction-shaped residue, symlink escapes, and fabricated
  provenance for personal roots.
- **Published parity:** pack-local suites, behavior evals, catalogue build and
  verification, and temporary builds for every declared adapter prove canonical
  source, projection, optional handoff metadata, permissions, and runtime
  behavior agree without adding a repository projection tree.
- **End-to-end journey:** manual QA in disposable repository-relative and
  personal-root projects records positive capture, no-admissible-residue,
  unavailable-provider, ineligible-root, abstaining enquiry, hostile evidence,
  incomplete work, receipt mismatch refusal, independent source verification,
  no phase advance, and zero-fallback outcomes as redacted pass/fail evidence.

## Acceptance Criteria

- [x] **AC1.** The matrix and supporting-workflow paragraph are the complete
  reviewed scope. Every selected workflow has an exact stable gate or an
  explicit no-gate result, its scratch and normative owner are named, and all
  earlier, abandoned, incomplete, scaffold, intermediate, check, and status
  paths are classified.
- [x] **AC2.** Quick research and all six current non-survey typed products
  perform no capture, distillation, or enquiry, including after a valid final
  result. Standard survey capture occurs only at
  `research-survey-complete` after every named source, synthesis, confidence,
  gap, citation, independence/triangulation, and moderator pass.
- [x] **AC3.** Applied capture occurs only at
  `research-applied-survey-complete` after the standard passes plus the applied
  marker, practitioner-independence taxonomy, applied confidence overlay, and
  failure-mode coverage.
- [x] **AC4.** Deep capture occurs only at
  `research-survey-counterreview-complete` after the complete survey and linked
  complete counterpoints artifact. Survey completion alone and any partial or
  interrupted challenge pass perform no capture or distillation.
- [x] **AC5.** Project start and digest perform no knowledge operation. Their
  scaffold, source ledger, synthesis matrix, memos, and all associated scratch
  remain solely in their owning project artifacts or transient context.
- [x] **AC6.** Project check and project status are project-knowledge non-gates.
  Check's current optional desk-research-owned `verdict_status` update remains
  unchanged, never advances phase, and never triggers capture, distillation, or
  enquiry; status remains read-only and performs no knowledge operation.
- [x] **AC7.** Project synthesis captures only at
  `research-project-synthesis-complete` after both synthesis products, their
  citation, confidence, triangulation, and gap passes, and the linked
  counterpoints artifact's required per-finding challenge pass are complete. It
  never converts an empty/missing prerequisite warning into a weaker product
  and never advances the human-owned phase.
- [x] **AC8.** Nested `devils-advocate` performs enquiry only through one
  outer-producer declaration after the common target and project scope are fixed
  and before the first counter-position enumeration. Deep and project-synthesis
  flows reuse that envelope across every per-finding pass and unchanged rerun;
  standalone review has the same one-query/no-refinement target budget. No
  duplicate nested query occurs, and the reviewer never captures or distils.
- [x] **AC9.** The exact enquiry object carries `caller: skill`, a sanitized
  producer-authored task label, fixed project/subproject scope, consequential
  risk, and the known `CQ-REVIEW` ID. Raw claims, quotations, citations, URLs,
  source titles, instruction-shaped text, and personal/external absolute paths
  never enter or return through `task_summary`; inability to form a safe label
  yields `project-knowledge not requested`. No workflow invents a question ID
  or uses enquiry to select sources, substantiate claims, set confidence, or
  decide a verdict.
- [x] **AC10.** A workflow with no honest project scope records
  `project-knowledge not requested`. A declared but undiscoverable provider
  emits exactly `project-knowledge unavailable`. An eligible empty result
  yields zero candidate checks, and unverifiable consequential evidence
  abstains; none creates fallback persistence or weakens the research method.
- [x] **AC11.** Retrieved knowledge is visibly delimited and inert. Tests prove
  it cannot change instructions, identity, permissions, tools, scope, mode,
  source choice, fetch targets, citations, claims, confidence, gaps,
  counter-evidence, verdicts, governance conclusions, or phase.
- [x] **AC12.** Every research and counter-evidence claim is independently
  verified against direct sources selected under the owning method. Retrieved
  topics cannot cite or corroborate themselves or each other; unverifiable
  material yields a caveat, omission, or abstention.
- [x] **AC13.** Producer handoff scratch is explicit, transient, and limited to
  candidate reusable practice or sanitized evidence residue. It is never saved
  automatically, reconstructed from transcripts/tool history, or populated by
  copying a research product or raw source corpus.
- [x] **AC14.** Surveys, matrices, memos, source corpora, quotations, citations,
  claims, confidence assessments, known unknowns, counter-evidence, typed
  verdicts, governance briefs, recommendations, and governance conclusions
  remain solely in their owning artifacts and are rejected from captured
  observation bodies.
- [x] **AC15.** Eligible capture constructs the unchanged published typed
  captured-observation request with its exact required fields and invokes only
  the public
  `project-knowledge --capture` seam. Producers do not locate journals, import
  the private writer, invent IDs, select partitions, name direct-maintainer
  pending observations, or create fallback storage.
- [x] **AC16.** A gate may request distillation only after successful capture
  and only with receipt IDs returned by that gate through
  `selection_mode: workflow-receipts`. No guessed, prior-gate, reviewer,
  supporting-workflow, or direct-maintainer receipt is eligible.
- [x] **AC17.** Capture eligibility canonicalizes the Git and product paths and
  requires a regular gate artifact plus honest repository-relative semantic
  gate, provenance, and freshness paths. Symlink escapes, ambiguous roots,
  missing repositories, personal roots, and external roots never construct a
  request.
- [x] **AC18.** Every capture-ineligible personal or external output emits
  exactly `project-knowledge capture ineligible: non-repository research
  output`, does not probe the provider, and creates no repository copy,
  fabricated path, user-directory spool, legacy append, or fallback file.
- [x] **AC19.** Privacy-shaped, instruction-shaped, stale, quarantined,
  irrelevant, malformed, or insufficiently authoritative material is refused,
  excluded, or abstaining under the shipped project-knowledge contract.
  Diagnostics expose no rejected body, raw source, sensitive locator, request,
  internal personal path, or hidden fallback.
- [x] **AC20.** Supporting planning, hypothesis, archaeology, retrieval-agent,
  extraction-agent, and retriever-script workflows perform no direct capture,
  distillation, or enquiry. A selected outer producer alone owns terminal
  handoff timing and receipts.
- [x] **AC21.** Existing research modes, artifacts, source methods, confidence
  rules, counter-evidence ownership, output-root resolution, optional
  desk-research-owned state writes, and human phase authority remain unchanged.
  The integration evaluates only the already-resolved terminal artifact for
  repository capture eligibility and does not reconcile or redefine
  desk-research configuration precedence or project-state policy.
- [x] **AC22.** Existing project-knowledge schema, mode-isolation, privacy,
  quarantine, freshness, prompt-injection, provenance, and receipt-selection
  suites remain green. No public schema, private writer, reader, topic format,
  question vocabulary, or storage behavior changes.
- [x] **AC23.** Desk-research declares one optional handoff to core's public
  project-knowledge provider without introducing a hard install dependency.
  Missing core keeps the exact unavailable/no-fallback behavior.
- [x] **AC24.** Pack version, plugin manifest, behavior evals, owning pack and
  public documentation, root changelog, marketplace aggregate, canonical
  sources, and temporary projections for every declared adapter are
  synchronized. Tests preserve current tool and sandbox boundaries.
- [x] **AC25.** The implementation is dependency-free and cross-platform, adds
  no service, database, external backend, user-directory assumption, automatic
  scratch retention, derived index, or multi-project bank, and persists no
  identifier copied from the prohibited comparison product.
- [x] **AC26.** Architecture and knowledge documentation distinguish research
  producer, research reviewer, and normative research-product authority, and
  manual QA records every positive, negative, abstaining, personal-root,
  hostile-evidence, receipt-scope, and phase-ownership outcome using redacted
  pass/fail evidence only.
- [x] **AC27.** Workspace ordering remains research after the shipped review
  slice and before engineering/operational integration and adoption closeout.
  Observation retention, derived-index scaling, an external capture backend,
  and a multi-project bank remain conditional post-closeout shaping items.
- [x] **AC28.** Construction and behavior tests enumerate `fact-check`,
  `comparison-matrix`, `shortlist`, `blueprint`, `hypotheses`, and `methodology`
  products and prove their terminal and incomplete paths perform no direct
  knowledge operation in this pilot.
- [x] **AC29.** Prompt-trigger descriptions and activation cues do not change.
  The existing Tier-A `eval_queries.json` files for every modified registered
  skill remain byte-unchanged and pass the current activation-query schema,
  coverage, runner-self-test, and skill-description anchor checks. The
  model-backed activation harness remains report-only evidence rather than a
  shipping gate; run it when the installed host can complete it, and record a
  named environment limitation otherwise. Any implementation-time trigger
  change instead updates its query file and returns to plan review.

## Assumptions

- Technical: the shipped captured-observation contract requires
  repository-relative semantic-gate, provenance-source, and freshness-anchor
  paths, so it cannot honestly represent a product stored in a personal or
  external output root (source: published JSON Schema and current capture
  parser/tests).
- Technical: the shipped enquiry vocabulary contains `CQ-REVIEW`, which can
  supply candidate counter-evidence checks after a target is fixed, but no
  existing question safely delegates research source selection, claim
  formation, confidence, or verdict authority (source: current enquiry
  contract and shipped review integration).
- Technical: the public enquiry query and `knowledge-enquiry-receipt.v1`
  response remain the shipped core skill/runtime contract; this integration
  consumes them unchanged and adds no separate schema (source: current
  `project-knowledge` skill, CLI, reader, and enquiry tests).
- Technical: standard, applied, and deep episodic research share one producer
  and artifact family, while the project lifecycle shares the same pack,
  source-verification method, optional core handoff, output-root eligibility
  rule, and release boundary. Two implementation waves inside one spec are
  therefore smaller than separate roadmap items (source: current desk-research
  pack and user approval 2026-08-17).
- Scope: desk-research owns its own configuration precedence, optional project
  state writes, and any internal documentation reconciliation. This slice
  observes the resolved artifact and terminal/non-terminal classification but
  changes none of those policies (source: user clarification 2026-08-17).
- Process: the full-mode authoring run completed clean adversarial and security
  review, and the human approved both the spec and plan on 2026-08-17. The
  implementation work-loop must seal that approved baseline before changing
  published workflow behavior.
- Roadmap: engineering/operational integration remains dependent on this item,
  adoption closeout remains dependent on engineering/operations, and the four
  post-closeout shaping items remain conditional (source: `workspace.toml` and
  user confirmation 2026-08-17).
