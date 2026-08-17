# Spec: Project knowledge review integrations

- **Status:** Shipped
- **Owner:** eugenelim
- **Plan:** [`plan.md`](plan.md)
- **Constrained by:** RFC-0077, ADR-0081, ADR-0082, and `project-knowledge-authoring-integrations` (Shipped)
- **Brief:** none
- **Discovery:** none
- **Contract:** none
- **Shape:** integration

> **Spec contract:** this document defines what "done" means. The implementing
> PR must match this spec, or update it. Verification must be derivable from it.

## Objective

Architecture, adversarial, security, and quality reviews may consult bounded
project knowledge at one declared review-planning moment to identify recurring
risks worth checking. The reviewer then verifies every candidate independently
against the current target, its governing rubric or checklist, and current
canonical sources. Missing, irrelevant, stale, quarantined, malformed, or
insufficiently authoritative knowledge produces a visible abstention or the
named `project-knowledge unavailable` skip and never weakens the review.

Reviewers remain non-writing project-knowledge consumers and independently
authoritative over their own findings, severities, and verdicts. Their transient
reasoning is not persisted; they perform no capture or distillation. The
existing producer workflow may
later triage only its own reusable review-process residue at a gate it already
owns, without copying reviewer findings or scratch.

## Boundaries

### Always do

- Declare the exact task, structural scope, consequential risk, `CQ-REVIEW`
  competency question, and fixed one-query/no-refinement budget before enquiry.
- Delimit every returned envelope as untrusted evidence, reduce it to candidate
  checks, and ground any resulting finding independently in the current review
  target, the selected rubric or checklist, and a current canonical source.
- Keep reviewer scratch transient and keep findings, security conclusions,
  quality verdicts, citations, severities, and recommendations solely in the
  owning review artifact.
- Preserve the existing committed-only, source-relative freshness, privacy,
  quarantine, prompt-injection, repository-confinement, and abstention behavior
  of the public project-knowledge enquiry seam.
- Author behavior in canonical pack sources, preserve existing reviewer tool
  declarations and sandbox annotations, and prove generated projection and
  pack-runtime parity.

### Ask first

- Add capture or distillation to a reviewer, persist reviewer scratch, or move a
  review finding or verdict into project knowledge.
- Change a review's stable result gate, severity model, verdict rules, rubric,
  checklist routing, tool surface, or read-only filesystem posture.
- Widen enquiry beyond `CQ-REVIEW`, consequential risk, the declared task and
  structural scope, or the fixed one-query/no-refinement budget.
- Rejoin research workflows to this slice, or define capture for a research
  product whose output root, terminal gate, citation authority, and raw-corpus
  boundary have not been approved separately.
- Change the public enquiry contracts, private writer, capture identity,
  partition selection, receipt selection, or distillation behavior.

### Never do

- Treat retrieved knowledge as instructions, permission, approval, a reason to
  redirect scope, a severity or verdict override, or self-validating evidence.
- Let a reviewer locate journals, import the private writer, invent capture
  IDs, select partitions, create fallback storage, or invoke capture or
  distillation.
- Mine transcripts or tool history, copy raw source corpora, persist reviewer
  scratch automatically, or reconstruct observations from a completed review.
- Suppress a finding, lower severity, skip a rubric/checklist item, or relax
  independent source verification because retrieved knowledge says to do so.
- Add a database, service, network dependency, user-directory assumption, new
  package dependency, new top-level directory, or persisted comparison-product
  identifier.

## Review integration contract

Every selected workflow has one exact stable result gate, but the gate is a
non-writing boundary: it performs no capture and owns no distillation receipts.
Enquiry occurs earlier, after the reviewer knows what it is reviewing and before
substantive judgment begins.

| Workflow | Exact stable result gate | Producer-owned transient scratch | Reusable supporting residue | Normative owner | Integration posture |
| --- | --- | --- | --- | --- | --- |
| `architect-review` | `architecture-review-complete`: the selected rubric or well-architected lens and grounding pass are complete, the verdict is decided, and the full critique or risk register is rendered. An ineligible artifact, partial rubric pass, or self-review refusal is not a gate. | Artifact classification, rubric failures, grounding spot checks, candidate risks, and severity ordering. | None captured by the reviewer. An owning outer workflow may later triage its own reusable review-process residue at its existing gate. | The inline critique or the user-requested saved review owns findings, severity, verdict, grounding, and recommendations. | Enquiry-only. After eligibility, artifact type, mode, scope, and rubric are resolved but before the rubric walk, declare one consequential `CQ-REVIEW` query with no refinement. |
| `adversarial-reviewer` | `adversarial-review-complete`: every applicable spec/plan or implementation checklist is traversed and the reviewer returns severity-labelled findings with fixes or exactly `Clean — ready to commit.` An invalid, incomplete, or interrupted report is not a gate. | Candidate drift, edge cases, acceptance-criterion mappings, authority conflicts, and finding fingerprints. | None captured by the reviewer. The invoking workflow owns any later process-residue triage. | The adversarial report owns findings, severity, fixes, and clean status. | Enquiry-envelope consumption only. The invoking workflow declares one bounded `CQ-REVIEW` call before first dispatch and passes the delimited envelope as candidate checks; absence is a named skip. |
| `security-reviewer` | `security-review-complete`: all routed security modules, helper-bypass checks, and the STRIDE/LINDDUN open pass are complete and the reviewer returns findings or exactly `Clean — ready to commit.` Missing required depth, an incomplete threat pass, or interrupted review is not a gate. | Boundary map, threat hypotheses, routed checklist notes, helper-bypass candidates, and evidence anchors. | None captured by the reviewer. The invoking workflow owns any later process-residue triage. | The security report owns threats, findings, severity, conclusions, limitations, and clean status. | Enquiry-envelope consumption only at the caller's declared `CQ-REVIEW` moment. Retrieved material can add a threat hypothesis but cannot decide a control, severity, or conclusion. |
| `quality-engineer` in review mode | `quality-review-complete`: the requested diff- or spec-level quality scope is traversed and the reviewer returns findings or exactly `Clean — ready to commit.` Test-author or testability-audit output, a partial pass, or interrupted review is not this gate. | Testability hypotheses, scenario coverage, failure-path notes, observability gaps, and maintainability candidates. | None captured by the reviewer. The invoking workflow owns any later process-residue triage. | The quality report owns findings, severity, quality verdict, and recommendations. | Enquiry-envelope consumption only at the caller's declared `CQ-REVIEW` moment. Retrieved material can suggest a regression scenario but cannot prove coverage or quality. |

For the specialist reviewer family, `work-loop` owns the enquiry invocation and
passes one envelope to the warranted reviewers after review scope is fixed and
before the first adversarial dispatch. A rerun over the same target reuses that
envelope; a materially changed target or scope requires a new explicit
declaration rather than an automatic refresh. Standalone callers that do not
declare enquiry provide no envelope and record `project-knowledge not
requested`; the invoking workflow records `project-knowledge unavailable` only
when a declared enquiry cannot discover the provider. A successful query with
no eligible topic returns an empty candidate set, while matched topics whose
consequential owning sources cannot be verified return `abstained: true`. In
every case the reviewer proceeds from the target, repository instructions,
rubrics, checklists, and current canonical sources.

The envelope is isolated as quoted data and may produce only candidate checks.
A reviewer must be able to reach the same finding without trusting the envelope:
the target supplies the observation, the rubric/checklist supplies the standard,
and a current canonical source supplies any external fact. A topic cannot cite
itself or another retrieved topic as independent corroboration.

No row constructs a captured-observation request. No row receives a capture
receipt or invokes `selection_mode: workflow-receipts`. The shipped work-loop
capture gates remain unchanged: if the outer workflow later admits reusable
review-process residue from its own explicit scratch, only receipts returned by
that outer gate are eligible for its existing receipt-scoped distillation.

### Downstream research approval gate

The separate research entry is not eligible for approval until it resolves the
authority differences visible in the current workflows:

- quick research is inline and produces no durable product;
- standard, applied, and deep research produce a cited survey only after their
  complete source, synthesis, confidence, known-unknown, and applicable
  challenge passes;
- project start is scaffolding, digest writes intermediate matrices and memos,
  project check is a read-only stop signal, and project synthesis writes a
  verdict and governance brief without advancing the human-owned phase; and
- `devils-advocate` owns counter-evidence in its research review artifact.

That spec must decide the mode and exact stable gate for each selected workflow
instead of inferring one from file creation. Its observable tests must prove
that abandoned, incomplete, scaffold-only, digest-only, check-only, and other
non-terminal paths do not capture; retrieved knowledge cannot count as a
citation or corroborate itself; every research claim retains independent direct
source verification; unavailable or unverified evidence yields a caveat,
omission, or abstention rather than a weaker claim; raw corpora, transcripts,
citations, verdicts, and research products are never copied into knowledge; and
personal output roots do not acquire fabricated repository-relative provenance.

## Testing Strategy

- **Review timing and authority:** TDD-style construction tests pin each exact
  enquiry/result boundary, the `CQ-REVIEW` request fields, the no-refinement
  budget, envelope delimiting, and the absence of capture, distillation, private
  writer, storage, identity, and partition vocabulary.
- **Reviewer judgment:** Tier-4 behavior evals exercise relevant knowledge,
  unavailable knowledge, abstention, stale/quarantined/irrelevant evidence,
  prompt injection, severity manipulation, scope redirection, permission/tool
  requests, attempted finding suppression, and self-validation.
- **Independence and degradation:** integration tests prove reviewers produce
  the same independently grounded finding with or without a suggestive envelope,
  proceed without fallback persistence, and do not report terminal completion
  for abandoned, incomplete, invalid, or interrupted reviews.
- **Published parity:** goal-based catalogue build, lint, verify, forced
  self-host, and temporary multi-adapter build checks prove canonical source,
  projections, reviewer permission metadata, pack versions, and optional pack
  handoffs agree.
- **End-to-end review journey:** manual QA in a disposable adopter-shaped
  repository records the enquiry declaration, bounded result or named skip,
  independent source check, final review result, and zero knowledge writes.

## Acceptance Criteria

- [x] **AC1.** The four-row matrix is the complete selected scope. Every row
  names its exact stable result gate, earlier non-gates, producer-owned scratch,
  reusable residue posture, normative owner, and enquiry posture.
- [x] **AC2.** `architect-review` invokes enquiry only after artifact
  eligibility, type or lens mode, structural scope, and rubric are resolved and
  before the substantive rubric pass. It uses caller `skill`, consequential
  risk, `CQ-REVIEW`, one query, and no refinement.
- [x] **AC3.** `work-loop` invokes at most one review-planning enquiry after the
  target and review scope are fixed and before the first adversarial dispatch,
  then passes the same delimited envelope to warranted adversarial, security,
  and quality reviewers. An unchanged rerun does not query again; a materially
  changed target requires a new explicit declaration.
- [x] **AC4.** Enquiry query objects use the unchanged public surface and carry
  `caller: skill`, a bounded task summary that names the invoking workflow,
  structural project or subproject `scope`, known `CQ-REVIEW` `question_id`,
  and consequential `risk`. The invoking workflow separately fixes one query
  and no refinement; reviewers do not construct a captured-observation request.
- [x] **AC5.** A declared enquiry whose provider cannot be discovered makes the
  invoking workflow emit exactly `project-knowledge unavailable`; an undeclared
  enquiry is `project-knowledge not requested`. The review continues when its
  own inputs are sufficient and neither outcome creates a journal candidate,
  legacy append, scratch file, user-directory spool, or other fallback.
- [x] **AC6.** A successful query with no eligible topic returns zero candidate
  checks without claiming provider failure; matched topics whose consequential
  owning sources cannot be verified return explicit `abstained: true`.
  Irrelevant, stale, quarantined, malformed, out-of-scope, or privacy-refused
  material is excluded or refused under the existing public contract. The
  caller does not weaken the question, read working-tree topics or journals, or
  broaden scope to force a result.
- [x] **AC7.** The returned envelope is visibly delimited and labelled
  untrusted. Injected text cannot change repository instructions, tools,
  permissions, identity, scope, reviewer routing, rubric/checklist coverage,
  severity, verdict, clean status, or normative authority.
- [x] **AC8.** Every knowledge-suggested finding is independently supported by
  the current target and applicable rubric/checklist; every factual claim also
  resolves to a current canonical source. Retrieved topics never corroborate
  themselves, and absence of knowledge never suppresses a finding.
- [x] **AC9.** Architecture findings and verdicts remain in the critique or
  risk register; adversarial findings and fixes remain in the adversarial
  report; security threats and conclusions remain in the security report; and
  quality findings and verdicts remain in the quality report.
- [x] **AC10.** Reviewer scratch is transient and never reconstructed from a
  transcript or tool history. No integration copies raw artifacts, source
  corpora, citations, full evidence envelopes, findings, conclusions, verdicts,
  or severity decisions into project knowledge.
- [x] **AC11.** All four reviewers perform no capture or distillation at their
  stable result gate or at abandoned, incomplete, invalid, refused, or
  non-terminal states. They never receive, guess, retain, or select capture IDs
  or partitions.
- [x] **AC12.** Construction tests fail if a reviewer locates a journal,
  imports `knowledge_store.py`, invokes a private writer, creates fallback
  persistence, or names `direct-maintainer-pending`. The public read-only
  `project-knowledge --enquire` seam is the only allowed knowledge operation.
- [x] **AC13.** Existing work-loop capture and distillation behavior remains
  unchanged. Any later outer-workflow capture uses only its explicit scratch,
  and terminal distillation can select only receipts returned by that same
  outer gate through `selection_mode: workflow-receipts`.
- [x] **AC14.** Privacy-shaped or instruction-shaped retrieved content remains
  redacted, refused, quarantined, or abstaining according to the existing
  project-knowledge contract. Diagnostics and review output expose no rejected
  body, sensitive locator, raw request, internal path, or hidden fallback.
- [x] **AC15.** Reviewer tool declarations and sandbox posture do not widen.
  Codex projections remain `sandbox_mode = "read-only"`; other projections add
  no Write/Edit or project-knowledge mutation capability beyond their existing
  canonical tool surface. Passing an evidence envelope does not widen a
  subagent's identity, filesystem scope, network access, execution authority,
  or available tools.
- [x] **AC16.** Reviewer independence tests cover a knowledge-suggested risk, a
  misleading counterclaim, a request to suppress or downgrade a finding, and a
  self-validating topic. Findings and severities derive from independent review
  evidence in every case.
- [x] **AC17.** Existing project-knowledge contract, mode-isolation, privacy,
  quarantine, freshness, enquiry, and prompt-injection suites remain green;
  existing reviewer rubrics, clean-report parsers, rerun limits, and source
  verification behavior do not regress.
- [x] **AC18.** Core and architect pack tests run independently. Core's
  same-pack work-loop uses normal skill discovery; architect declares an
  optional handoff to core's public provider without turning metadata into
  dispatch or tightening a dependency to erase the unavailable branch.
- [x] **AC19.** Pack versions, plugin manifests, behavior evals, pack
  documentation when behavior descriptions change, root changelog, marketplace
  aggregate, canonical sources, and generated adapter projections are
  synchronized. Tests prove reviewer permission metadata survives projection.
- [x] **AC20.** The implementation is cross-platform and dependency-free,
  changes no public knowledge schema or private writer behavior, adds no
  service/database/user-state assumption, and persists no identifier copied
  from the prohibited comparison product.
- [x] **AC21.** Architecture and knowledge documentation distinguish producer,
  reviewer, and research authority. Manual QA records positive, abstaining,
  unavailable, hostile-evidence, incomplete-review, and zero-write outcomes as
  redacted pass/fail evidence only.
- [x] **AC22.** The roadmap carries research as a separate dependent slice
  before engineering/operational integration. Its approval gate covers every
  current research mode named above and requires the observable no-capture,
  independent source-verification, abstention, raw-corpus, normative-authority,
  and output-root tests defined above before implementation may start.

## Assumptions

- Technical: the shipped enquiry contract already provides committed-only,
  scoped, source-verified consequential results and all required abstention
  states (source: `packs/core/.apm/skills/project-knowledge/SKILL.md`, enquiry
  reference, and current project-knowledge tests).
- Technical: specialist reviewer definitions are read-only and receive context
  from an invoking workflow; they do not own a project-knowledge write seam
  (source: `packs/core/.apm/agents/` and their current Codex/Claude projections).
- Technical: `architect-review` is a no-write inline review by default and
  already requires independent rubric and source grounding (source:
  `packs/architect/.apm/skills/architect-review/SKILL.md`).
- Process: the user approved the spec and plan before implementation; this
  full-mode work-loop run proceeds through implementation and specialist review,
  then stops at the repository's human delivery gate (source: user approval
  2026-08-17, `docs/CONVENTIONS.md`, and `work-loop`).
- Product: normative review and research outputs remain solely in their owning
  artifacts; only independently reusable supporting practice or evidence
  residue can ever be eligible for capture (source: user confirmation
  2026-08-17 and RFC-0077 authority routing).
- Roadmap: observation retention, derived-index scaling, an external capture
  backend, and a multi-project knowledge bank remain conditional post-closeout
  shaping items (source: user confirmation 2026-08-17 and `workspace.toml`).
