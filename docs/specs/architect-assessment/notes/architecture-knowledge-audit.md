# Architecture knowledge audit

This audit freezes the pre-migration architect reference surface and decides
which material belongs in the reusable `architecture-lenses` corpus. The unit
of classification is the pre-existing reference file, not every paragraph:
where a file mixes reusable knowledge with workflow behavior, the neutral
substance moves and the consumer-specific procedure remains local.

Generated files under `architecture-lenses-reference/references/okf/` are not
inputs to this audit. They are the projection produced after these decisions.

## Classification rules

- **Move to neutral corpus** — reusable questions, mechanisms, evidence,
  counter-evidence, failure modes, and confirmation scenarios that apply to
  assessment, design, and review.
- **Retain workflow-specific** — activation, elicitation, authoring, severity,
  verdict, convergence, permissions, degradation, or saving behavior owned by
  one workflow.
- **Unchanged diagram/output concern** — notation, rendering, provider symbol
  vocabulary, artifact layout, or diagram rubric content outside the shared
  architecture-question plane.

## Design and review references

| Reference | Classification | Destination or reason |
| --- | --- | --- |
| `architect-design/references/agentbundle-layout.md` | Retain workflow-specific | Design save-path resolution and adopter-owned configuration. |
| `architect-design/references/alternatives.md` | Retain workflow-specific | Design-authoring technique for producing credible alternatives. |
| `architect-design/references/cloud-primitives.md` | Move to neutral corpus | Provider responsibility and capability-gap reasoning moves to `concepts/operating-model-patterns/provider-and-platform-operating-models.md`; design routing remains in the Skill. |
| `architect-design/references/convergence-loop.md` | Retain workflow-specific | Review iteration, auto-fix boundary, termination, and stasis behavior. |
| `architect-design/references/cross-cutting-questions.md` | Move to neutral corpus | Cross-cutting questions move to `concepts/foundations/decisions-constraints-and-cross-cutting-concerns.md` and the applicable quality lenses. |
| `architect-design/references/design-doc-rubric.md` | Retain workflow-specific | Artifact-authoring completeness rubric. |
| `architect-design/references/knowledge-surfaces.md` | Mixed: move neutral core, retain workflow shell | The eight enterprise areas move to `concepts/enterprise-knowledge/`; detection, permission, attribution, and design degradation stay local. |
| `architect-design/references/leading-edge-domains.md` | Retain workflow-specific | Design-time research and confidence degradation when no domain lens fits. |
| `architect-design/references/lens-genai-agentic.md` | Move to neutral corpus | Replaced by the five `concepts/workload-lenses/genai-agentic/` concepts; design decides which ones to load. |
| `architect-design/references/lens-serverless.md` | Move to neutral corpus | Replaced by `concepts/workload-lenses/serverless.md`; binding provider figures remain live-source work. |
| `architect-design/references/local-dev.md` | Retain workflow-specific | The local-first graduation conversation and Stage-0 topology shaping remain design behavior; reusable delivery/runtime questions are also covered by the operating-model corpus. |
| `architect-design/references/nfr-checklist.md` | Retain workflow-specific | Compact authoring completion check; the deeper reusable evidence questions live in quality lenses. |
| `architect-design/references/quality-attribute-scenarios.md` | Move to neutral corpus | Replaced by `concepts/foundations/quality-attribute-scenarios.md`. |
| `architect-design/references/tradeoffs-and-sensitivity.md` | Move to neutral corpus | Replaced by `concepts/foundations/tradeoffs-sensitivity-and-evolution.md`. |
| `architect-design/references/well-architected-pillars.md` | Move to neutral corpus | The reusable quality spine moves to `concepts/quality-lenses/`; provider responsibility moves to the operating-model branch. |
| `architect-review/references/cloud-primitives.md` | Move to neutral corpus | Same provider operating-model destination as design. |
| `architect-review/references/cross-cutting-questions.md` | Move to neutral corpus | Same foundations and quality-lens destinations as design. |
| `architect-review/references/knowledge-surfaces.md` | Mixed: move neutral core, retain workflow shell | The taxonomy moves to the enterprise branch; verification triggers, severity treatment, and spot-check behavior stay local. |
| `architect-review/references/lens-genai-agentic.md` | Move to neutral corpus | Replaced by the five agentic workload concepts. |
| `architect-review/references/lens-serverless.md` | Move to neutral corpus | Replaced by the serverless workload concept. |
| `architect-review/references/local-dev.md` | Retain workflow-specific | Review-side fit and graduation checks stay local. |
| `architect-review/references/quality-attribute-scenarios.md` | Move to neutral corpus | Replaced by the shared quality-scenario concept. |
| `architect-review/references/rubric-c4-diagram.md` | Unchanged diagram/output concern | C4 artifact correctness rubric. |
| `architect-review/references/rubric-design-doc.md` | Retain workflow-specific | Design-doc review rubric and severity anchors. |
| `architect-review/references/rubric-er-diagram.md` | Unchanged diagram/output concern | ER artifact correctness rubric. |
| `architect-review/references/rubric-generic.md` | Retain workflow-specific | Fallback artifact-review rubric. |
| `architect-review/references/rubric-sequence-diagram.md` | Unchanged diagram/output concern | Sequence artifact correctness rubric. |
| `architect-review/references/rubric-state-diagram.md` | Unchanged diagram/output concern | State artifact correctness rubric. |
| `architect-review/references/rubric-well-architected.md` | Retain workflow-specific | Owns lens selection, finding tags, severity, and verdict; it now routes reusable knowledge through the generated corpus. |
| `architect-review/references/tradeoffs-and-sensitivity.md` | Move to neutral corpus | Replaced by the shared trade-off concept. |
| `architect-review/references/well-architected-pillars.md` | Move to neutral corpus | Replaced by shared quality and provider-operating-model concepts. |

## Diagram references

All pre-existing `architect-diagram/references/*.md` files are classified
**unchanged diagram/output concern**. This includes its layout contract,
provider symbol and agentic-platform vocabularies, cloud patterns, knowledge-
surface vocabulary used to label diagrams, Mermaid notation guides, notation
routing, visual encoding, and diagram rubric. These files answer how to depict
an architecture rather than how to judge its evidence or fitness. Moving them
would give the knowledge corpus rendering authority and blur the diagram
workflow boundary.

The audited files are:

`agentbundle-layout.md`, `agentic-ai-foundry.md`,
`agentic-bedrock-agentcore.md`, `agentic-vertex-agent-engine.md`,
`cloud-aws.md`, `cloud-azure.md`, `cloud-gcp.md`, `cloud-patterns.md`,
`cloud-primitives.md`, `diagram-rubric.md`, `knowledge-surfaces.md`,
`mermaid-architecture-beta.md`, `mermaid-c4.md`, `mermaid-er.md`,
`mermaid-flowchart.md`, `mermaid-gantt.md`, `mermaid-gitgraph.md`,
`mermaid-mindmap.md`, `mermaid-quadrant.md`, `mermaid-sequence.md`,
`mermaid-state.md`, `mermaid-timeline.md`, `notation-routing.md`, and
`visual-encoding.md`.

## Migration outcome

`architect-design` and `architect-review` now enter through the generated root
index and select only named concept paths. If the generated router is missing or
invalid, each workflow declares the knowledge layer unavailable and continues
with its local procedure at reduced coverage; neither silently falls back to
model-memory claims. The removed duplicate files are therefore compatibility
debt intentionally retired, not a new runtime dependency between user-facing
workflows.
