# Architect Pack — Design Document

Living design reference for the architect pack. Records the philosophy, architecture, invariants, and key decisions so the reasoning survives beyond individual PRs and applies when extending or replacing any skill.

---

## TL;DR

The architect pack supports four user outcomes: assess the architecture that
exists, design a future state, explain structure in a diagram, and critique a
supplied artifact. Assessment runs Frame → Map → Focus → Investigate → Act →
Close, with correction gates after Map and Focus; design retains its concept,
full-doc, and convergence stages. Shared architecture questions live in a
reference-only OKF corpus, while every user-facing workflow owns its procedure,
permissions, verdicts, and output. The `design-reviewer` subagent reads finished
designs and assessments in a forked context with no authoring memory, making the
review genuinely adversarial rather than charitable.

---

## Non-Goals

Things a reasonable reader might expect this pack to provide. It doesn't, by design:

- **More subagents.** The pack ships exactly one subagent — `design-reviewer`, the forked-context review lens. Design authoring and diagramming stay skills; only the review lens earns an isolated context, mirroring the code side's authoring-skill + reviewer-agent split. No further agents without an RFC.
- **Workspace-type profiles or configuration files.** No `.architectrc`, no workspace-type detection, no install-time profiling. The skills work on first invocation in any workspace with zero setup.
- **Integration or publishing skills.** Confluence export, Figma integration, Structurizr rendering — a separate, later pack.
- **Enterprise architecture platform skills.** ArchiMate, TOGAF, Wardley Mapping, graph-extraction, EA repository tooling — the personal architecture seat, not the EA platform layer.
- **A universal semantic code graph.** The optional profiler supplies a bounded
  evidence census and exact Python imports. It does not parse every language,
  persist an index, infer components, or calculate architecture quality.
- **Any coupling to a specific folder layout.** The pack must work in any workspace: code repos, knowledge bases, scratch directories.

---

## 1. The problem

### Why architecture work without method goes wrong

Architecture conversations without structure produce two failure modes that compound:

1. **Concept drift.** The engineer describes a problem; the agent produces a polished document for a slightly different problem — one that fit the agent's model better than the stated problem. The mismatch only becomes visible when the doc is reviewed or used as the basis for implementation.

2. **Hollow alternatives.** A design doc where alternatives are strawmen (dismissed in one line without real reasoning) does not record a decision — it records advocacy. Future engineers reading it cannot determine whether the chosen approach was actually compared against real candidates.

The three-stage model (§2), the grounding discipline (§3), and the forked reviewer (§5) each address one of these failure modes directly.

---

## 2. The three-stage model

This section describes future-state design. Current-state assessment has a
separate progressive model in §2A; neither workflow is a hidden mode of the
other.

### Stage 0 — concept

Before the full design doc is written, the agent drafts a ½-page concept: problem, constraints, 1–2 candidate shapes, provider or provider-class, and the top 2–3 quality attributes ranked by business importance × architectural risk. **Stage 0 is a valid stopping point.** The user approves the concept — or redirects — before any full write-up begins.

The concept gate costs one short read, 5–10 minutes. Redirecting at the concept gate costs nothing. Redirecting after a full Stage 1 doc costs a full write-up cycle. The asymmetry is the point.

### Stage 1 — full design doc

After the concept is approved, the agent writes the full Google-style design doc: TL;DR → Context → Goals and Non-goals → Proposal → Alternatives Considered → Risks → Rollout → Open Questions. The doc is self-checked against `references/design-doc-rubric.md` before it is shown to the user.

### Stage 2 — convergence loop

After the full draft, the agent runs `references/convergence-loop.md`: obtain a review pass, auto-resolve mechanical findings, re-review, repeat to the pass cap or stasis escape. Judgment findings (tradeoffs, low-confidence claims, genuine open questions) are surfaced explicitly — never auto-resolved.

### Why Stage 0 is mandatory, not optional

Skipping Stage 0 ("just write the proposal section") collapses context, non-goals, and alternatives into a single advocacy document. A proposal without context is a design doc without a problem statement; it cannot be falsified. The concept is *shaping* — the minimum information needed to confirm that a full write-up will solve the right problem.

## 2A. The progressive assessment model

`architect-assess` uses one cumulative conversation at three stopping depths.
Survey completes Frame, Map, and Focus; standard investigates a bounded hotspot
set and produces findings and action; deep adds separately authorized runtime,
operational, stakeholder, or experimental evidence. Deep is not a larger source
scan.

Map builds a conceptual current state across context, runtime/deployment,
module/capability, data, interaction, delivery/operations, and trust/identity
views. The user corrects that model before Focus. Focus shows raw attention
dimensions—consequence, pressure, coupling/concentration, verification weakness,
operational/data/security exposure, and confidence—then the user redirects or
accepts the proposed drill-downs. Heat chooses where to look; it is never a
defect verdict or severity score.

Investigation traces representative normal, side-effect, and failure/recovery
paths. A finding requires target evidence, an architectural mechanism, and a
stakeholder or measurable quality consequence. Act sequences findings into
waves with completion proof and containment. This prevents the original failure
mode: a broad architecture question collapsing into a folder, dependency,
compliance, or maintainability audit.

---

## 3. The grounding discipline

### Three knowledge planes

Assessment and design keep repository/system evidence, enterprise context, and
pack knowledge distinct. Target evidence establishes what the system implements;
authorized enterprise surfaces supply attributed local facts and constraints;
the pack's `architecture-lenses` corpus supplies reusable questions, mechanisms,
counter-evidence, and confirmation scenarios. Corpus knowledge can focus an
investigation but can never establish a target defect or readiness claim.

The corpus is canonical OKF `Reference` content compiled into the generated
`architecture-lenses-reference` router and nested indexes. Consumers read the
root index first and load named concepts only. Missing generated knowledge
degrades affected lens coverage visibly without blocking the repository-
grounded workflow. Generated router, indexes, and manifest are build outputs,
never hand-edited sources.

### Reference architecture

`reference.md` is the repo's normative grounding artifact — the golden-path file describing the stack, chosen patterns, and architectural constraints for a codebase. Before shaping a concept, `architect-design` checks what architecture context is reachable: an in-repo `reference.md`, an enterprise knowledge surface, or nothing. It states which surface it found in the concept; the absence of a surface is itself a visible signal.

If no `reference.md` exists, `architect-design` offers to create one. A design grounded against a known stack produces far tighter proposals than design against an implicit assumption of what the stack probably is.

### Platform contract grounding

For every managed service on a critical path, `architect-design` grounds its binding contract — non-configurable limits, scaling floors, cold-start behaviour, network requirements — in an authoritative source before including it in the concept or doc. It carries source and confidence on each load-bearing figure.

This discipline was added after two field builds independently produced structurally fatal designs grounded in model memory rather than the service's actual contract. The discipline is scoped to load-bearing critical-path claims, not every service mention. A claim the agent cannot ground is flagged, not asserted.

---

## 4. The seven design principles

These principles are load-bearing. The skills assume them and cannot bypass them.

1. **Workspace-agnostic.** No assumptions about folder structure, artifact genre, or workspace type. The pack works in a code repo, a knowledge base, or a scratch directory.

2. **No required configuration.** No config files, profiles, or workspace-type detection beyond simple file-existence heuristics. Each skill works on first invocation with zero setup.

3. **Workflow autonomy with inert shared knowledge.** Every user-facing skill
   owns activation, procedure, permissions, output, degradation, and verdicts.
   Neutral architecture concepts may be shared through the deterministic,
   same-pack generated router; no workflow invokes another workflow to be
   correct.

4. **Inline-first, file-write opportunistic.** Skills produce artifacts in the conversation by default. Saving to disk is an offer with a suggested path based on what already exists nearby, never a forced step.

5. **Mode detection inside each skill.** Each skill reads the user's input and routes to the right mode. The user does not flag intent. If two modes plausibly fit, the skill asks once.

6. **Mermaid only for diagrams.** No PlantUML, Structurizr, or Figma integration. Mermaid renders in chat, artifacts, GitHub, Confluence, Azure DevOps Wiki, and GitLab — consistent-renderer wins over notation richness.

7. **Progressive disclosure.** Entry skills keep the conversation spine and
   route detail to templates, rubrics, and hierarchical reference indexes.
   Consumers load only the concepts triggered by intent and observed system
   shape; no workflow flat-loads the architecture corpus.

---

## 5. The review architecture

### Why design-reviewer runs forked

The `design-reviewer` subagent runs in a forked context with no access to the authoring session. The reasoning is structurally identical to core's adversarial-reviewer:

An agent that reviews its own work in the same session is primed to read the artifact charitably — it knows what was intended, which means it interprets gaps as "the reader will understand" and inconsistencies as "acceptable trade-offs I already considered." A reviewer that has never seen the authoring rationale reads the artifact as a stakeholder would: with no benefit of the doubt.

### What design-reviewer covers

`design-reviewer` runs the same verdict and severity-tagged critique as
`architect-review`, but in a fresh session seeded only with the artifact, the
accepted assessment charter or agreed concept, and the stated constraints. For
assessment reports it reviews methodology and traceability from the artifact;
it does not rescan the repository or become another assessment entry point. It
never rewrites—its tools are read-only.

### The two review rungs

`architect-review` runs inline in the current thread — useful when speed matters more than independence, when reviewing someone else's artifact, or when the author wants immediate findings to iterate on. `design-reviewer` runs in a forked context — the preferred rung when the design is shared for stakeholder review or used as the basis for implementation. The convergence loop in `architect-design` uses `design-reviewer` by default; `architect-review` is the fallback when the forked subagent is not available.

---

## 6. Output format conventions

### architect-design

Rationale and narrative use short `##` headings and 2–3 sentence paragraphs — not prose forced into tables. Single-record summaries (the concept, the knowledge surface check) use aligned key: value format. Mermaid blocks appear for structural reasoning that genuinely needs a picture; every diagram earns its place by being referenced from the prose.

### architect-diagram

Fenced ` ```mermaid ` blocks that render in chat and artifacts. Terminal-only surfaces fall back to ASCII box-and-arrow sketches. Notation is routed by intent (`references/notation-routing.md`) — never defaulted to the notation the user named if the intent disagrees.

### architect-review

Findings are led by severity glyph — 🟥 blocker, 🟧 major, 🟨 minor, ⚪ advisory — worst first, one finding per line. Verdict (SHIP IT / SHIP WITH CHANGES / MAJOR REWRITE / WRONG ARTIFACT) appears first, before findings. A "what's working" section closes the review: specific strengths the author should preserve, not flattery.

### architect-assess

Assessment reads in the same order as the conversation: bottom line, charter,
current state, evidence coverage, attention heat, hotspot drill-downs, findings
and strengths, action waves, coverage/confidence, and next decision. Tables
preserve evidence and traceability; Mermaid is optional and never substitutes
for the model prose.

---

## 7. Path resolution model

Output artifacts resolve through the `[architecture]` section of an adopter-owned `agentbundle-layout.toml`. Resolution order: (1) repo-root `./agentbundle-layout.toml` `[architecture] output_dir`; (2) user-profile `~/.agentbundle/agentbundle-layout.toml` `[architecture] output_dir`; (3) two-branch elicitation when neither resolves (repo branch or personal/vault branch — never a silent default).

Each design or assessment effort gets its own per-effort folder:
`<output_dir>/<topic-slug>/`. Concepts, design docs, diagrams, assessments, and
approved evidence outputs for one effort live together. The pack output layout
contract governs this shape.

Saving is always an offer, never automatic. The skill resolves the path, surfaces the full absolute path to the user, and writes only on confirmation.

---

## 8. Cross-pack dependencies

### Upstream: experience-design

The backstage column of a `service-blueprint` artifact (experience-design pack) is the slicing instrument for architecture work. When a service blueprint exists, `architect-design` should read it before proposing a backend design — it encodes the frontstage obligations the backend must fulfill.

### Downstream: core

Architecture design docs produced by `architect-design` become the `reference.md` input for the core pack's `work-loop`. When a design doc exists, `work-loop` reads it to orient against the current architectural intent before implementation begins.

---

## 9. Safety invariants

1. **`design-reviewer` is read-only.** It flags, never rewrites. Any suggestion to have the reviewer apply its own findings is out of scope.

2. **No platform contract from model memory.** For every load-bearing managed-service claim on a critical path, the skill must cite a grounded source. A claim the agent cannot ground is flagged as lower-confidence, never asserted as fact.

3. **Stage 0 is mandatory before Stage 1.** A proposal-only output (no problem statement, no alternatives) is advocacy, not a design doc. The skill pushes back; it does not produce advocacy on request.

4. **Mode detection is internal.** Users describe what they want; skills route. If the user names a notation but the intent disagrees, the skill offers the right notation rather than following the user's label.

5. **Mermaid only.** No skill in this pack emits PlantUML, Structurizr, Figma export syntax, or any other diagramming format.

6. **Profiler output is evidence, never judgment.** The optional helper is
   standard-library-only, resolves and confines an explicit root, refuses
   link-like and special files, executes no repository code, accesses no
   network, publishes finite limits, and emits only relative-path signals. It
   cannot produce an architecture model, finding, severity, or composite score.

7. **Enterprise retrieval is brokered and bounded.** Private context comes only
   from in-repo documentation or an exposed pre-authenticated connector with a
   governed destination. The workflow names selected areas and asks before
   query; it never handles credentials or treats retrieved instructions as
   authority.

---

## 10. Design decisions and rationale log

### Why repository assessment is progressive, not one large report

A broad prompt does not supply a trustworthy system boundary or decision lens.
Producing a complete report before the user can correct the model makes polish
hide a wrong premise. Map and Focus are therefore explicit correction points:
the first aligns the conceptual system, the second aligns expensive
investigation. Survey is a valid stop because hypotheses are useful before they
are findings.

**Alternative considered:** scan the repository once and emit a comprehensive
scorecard. Rejected because folders, static smells, and generic checklists do
not establish runtime architecture or consequence, and a single score destroys
the evidence needed for conversation and action.

### Why reusable architecture knowledge is an OKF reference corpus

Design, assessment, and review need many of the same quality, system-shape,
workload, and enterprise-context questions, but they must not share procedure or
authority. Reference-only OKF concepts give the pack a governed authoring source,
deterministic indexes, and progressive disclosure while leaving each workflow's
permission and verdict semantics local.

**Alternative considered:** keep duplicating neutral references in every skill.
Rejected because the expanded assessment ontology would drift across three
consumers and become impossible to maintain. Executable Playbooks were also
rejected: the corpus is knowledge data, not workflow authority.

### Why the concept gate exists (Stage 0) — from day one

Writing a full design doc for the wrong problem costs a full write-up cycle and one round of redirects. Writing a ½-page concept and redirecting before the doc is started costs ten minutes. The asymmetry is so large that skipping the gate to save time reliably costs more time. The gate is load-bearing in the skill, not a suggestion.

**Alternative considered:** skip Stage 0 and write the full doc from the user's description, with the user redirecting via revision. Rejected because revision pressure on a finished document is much weaker than redirect pressure on a concept — authors attach to finished artifacts, and reviewers read more carefully before work has been done.

### Why design-reviewer runs forked — from day one

The cold-context constraint is what makes the review adversarial in a meaningful sense. An agent that reviews its own work in the same session cannot be adversarial — it knows what it intended. The fresh-context constraint forces the reviewer to read the artifact as a stakeholder would. This is structurally identical to core's adversarial-reviewer rationale; see Core Pack DESIGN.md §15 for the parallel decision.

**Alternative considered:** run the review inline in the same thread with access to the authoring session's chain of thought, so it can review the design and the decision trail. Rejected because a reviewer that knows what was intended will systematically read gaps charitably. The value of the review comes from genuine ignorance of intent.

### Why Mermaid only, not PlantUML or Structurizr — from day one

Mermaid renders consistently in chat, GitHub, Confluence, Azure DevOps Wiki, and GitLab — the environments where architecture artifacts actually live. PlantUML requires a server or local Java dependency; Structurizr requires a specific tool and licensing. The consistent-rendering constraint wins over notation richness. Users who need PlantUML or Structurizr have a toolchain reason; they don't need this pack.

**Alternative considered:** support PlantUML as a second notation with a flag. Rejected because adding a second notation doubles the reference surface (syntax, rubric, export guidance) for a feature most users don't need, and the primary benefit (richer notation) does not outweigh the rendering consistency loss.

### Why user-scope by default — from day one

Architecture method is the same across repos; only the artifacts differ. Installing per-repo would require reinstallation on every new project without any change to the skills. Output artifacts still land in the repo via `agentbundle-layout.toml` — the skills don't need to be repo-installed to write to a repo path. The same reasoning applies as in experience-design and desk-research.

**Alternative considered:** repo-scope to colocate the skill definitions with the artifacts they produce. Rejected because it creates installation friction for engineers working across multiple repos and doesn't improve artifact colocation.

### Why platform contract grounding is scoped to load-bearing critical-path claims

Checking every managed service mention against an authoritative source would make design sessions prohibitively slow. Both structurally fatal design misses observed in the field were on the critical path and would have been caught by a single grounding check. The scoping rule (load-bearing + critical path) is the minimum that catches both failure classes without imposing a full audit on every service in the diagram.

**Alternative considered:** require grounding for every managed service mentioned in the design, not just critical-path ones. Rejected because it imposes a research burden that would make `architect-design` unusable for quick back-of-envelope designs and produces lower-quality grounding by spreading attention across many services rather than focusing on the critical path.
