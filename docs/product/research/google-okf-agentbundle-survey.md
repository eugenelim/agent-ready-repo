# Google OKF as AgentBundle knowledge infrastructure — applied survey

> Discipline: applied (practitioner-pattern survey)

**Question.** Can AgentBundle reuse Google's Open Knowledge Format (OKF) as a
catalogue substrate for enterprise and SDLC knowledge, natively deliver OKF
bundles, and project selected OKF concepts into progressively disclosed Agent
Skills? If so, what should be built first, and which available knowledge domain is
the strongest pack opportunity?

**Verdict.** Build both, in sequence. First, establish an experimental convention
that ships an unchanged OKF bundle inside a thin Agent Skill. Second, add a
deterministic authoring-time OKF-to-Skills projection governed by a namespaced
`x-agentbundle` extension. Pilot it with a new **cost-engineering** pack, scoped to
engineering-owned cloud and AI cost practices. Do not add an AgentBundle primitive
or make OKF parsing part of normal distribution builds until two real callers prove
that a standalone primitive is necessary.

---

## Findings

**F1. OKF and Agent Skills are complementary formats, not substitutes.** `[high]`
OKF v0.2 represents durable, linked knowledge as Markdown concepts with provenance,
trust, freshness, lifecycle, and optional computation metadata. Agent Skills package
procedures: a required `SKILL.md` plus optional scripts, references, and assets. OKF
answers *what the agent should know*; a Skill answers *what the agent should do and
when*. Both use directory structure and staged loading, which makes nesting an OKF
bundle under a Skill's `references/` directory a natural composition rather than a
format hack. [OKF specification](https://github.com/GoogleCloudPlatform/knowledge-catalog/blob/main/okf/SPEC.md),
[Agent Skills specification](https://github.com/agentskills/agentskills/blob/main/docs/specification.mdx)

**F2. Raw OKF delivery requires no AgentBundle engine change.** `[high]` The current
adapter contract projects an entire `.apm/skills/<skill>/` directory, and adapter
implementations recursively copy its contents. A pack can therefore place a complete
bundle at `.apm/skills/<router>/references/okf/`; every supported adapter will receive
the raw OKF tree with the skill. This is local contract evidence, not an ecosystem
claim. [Adapter contract](../../../contracts/adapter.toml),
[pack layout](../../architecture/pack-layout.md)

**F3. OKF is intentionally extension-friendly enough for an AgentBundle projection
profile.** `[high]` Only `type` is always required. Producers may add arbitrary
frontmatter keys; consumers must tolerate unknown fields and should preserve them
when round-tripping. There is no central type or schema registry. That permits a
namespaced `x-agentbundle` object without forking OKF. The lack of a registry also
means the extension needs its own version and schema URI; merely inventing a new
`type` would not define interoperable transformation semantics.
[OKF specification §4.1](https://github.com/GoogleCloudPlatform/knowledge-catalog/blob/main/okf/SPEC.md#41-frontmatter)

**F4. “Convert OKF to skills” must be a projection with an opt-in boundary, not a
blanket conversion.** `[high]` Most OKF concepts are facts, schemas, metrics, or
references and do not contain an executable procedure or a reliable activation
description. Agent Skills require both instructions and a description that tells an
agent when to use them. Generating a skill from every concept would manufacture
procedural meaning that the source never asserted. The safe contract is: retain the
whole OKF bundle as canonical knowledge; emit a Skill only for a concept explicitly
annotated with `x-agentbundle.skill`; make generated files replaceable build outputs.
[synthesis from the two format specifications]

**F5. OKF v0.2's own progressive disclosure can be preserved inside the Skill's
progressive disclosure.** `[high]` An OKF `index.md` lets an agent inspect a
directory before loading individual concepts. An Agent Skill exposes name and
description first, `SKILL.md` when selected, and references on demand. A thin router
can therefore load the OKF root index, descend through sub-indexes, and open only the
concepts required for the task. “Quick” versus “full” research or operating modes
remain a separate pack-level behavior; neither specification supplies them
automatically. [OKF specification §8](https://github.com/GoogleCloudPlatform/knowledge-catalog/blob/main/okf/SPEC.md#8-index-files),
[Agent Skills progressive disclosure](https://agentskills.io/what-are-skills)

**F6. The reusable compiler/catalogue layer is a plausible market gap, but the OKF
ecosystem is too young to call it proven demand.** `[moderate]` The ecosystem contains
validators, viewers, search/MCP servers, raw-content-to-OKF compilers, and skills that
teach agents to author or maintain OKF. The official discussions now include “OKF
Agent Skills” and publishing-engine ideas. The search did not find a mature tool that
deterministically projects selected OKF concepts into portable Agent Skills while
preserving arbitrary extensions and provenance. Downgraded from high: this is a
negative search result in a fast-moving ecosystem, not an exhaustive registry audit.
[official OKF discussions](https://github.com/GoogleCloudPlatform/knowledge-catalog/discussions),
[GitHub OKF topic](https://github.com/topics/open-knowledge-format),
[community tool index](https://okf.md/tools/)

**F7. There is useful extension prior art, but no extension convention is yet
standard.** `[moderate]` Community implementations use bundle-local JSON Schemas,
namespaced foreign metadata such as `x-llmwiki`, and root capability registries. The
patterns converge on preserving unknown fields and declaring an extension contract;
they do not converge on one field name or registry mechanism. Downgraded for recency
and small implementation count.
[okf-schema custom schemas](https://okf-schema.readthedocs.io/en/latest/how-to/write-custom-schema.html),
[llm-wiki-compiler](https://github.com/atomicstrata/llm-wiki-compiler)

**F8. No available OKF corpus is yet a strong “rebundle as-is” enterprise/SDLC
pack.** `[moderate]` The official reference bundles demonstrate analytics and data
catalogue use cases; the wider public ecosystem is dominated by tooling, templates,
and narrow project knowledge. No broad, maintained, clearly licensed enterprise or
SDLC corpus emerged that is both pack-shaped and additive to this catalogue.
Downgraded because public search cannot establish that no suitable private or
poorly-indexed corpus exists. The practical route is to compile our own OKF bundle
from authoritative, reusable sources rather than inherit an immature community
bundle. [official OKF repository](https://github.com/GoogleCloudPlatform/knowledge-catalog/tree/main/okf),
[community tool index](https://okf.md/tools/)

**F9. Cost engineering is the strongest first knowledge pack.** `[moderate]` It
fits the catalogue when bounded to engineering decisions and recurring operating
habits: allocating workload cost, estimating changes, detecting anomalies, comparing
architecture and workload-placement options, optimizing utilization, and applying AI
cost guardrails. The FinOps Framework explicitly assigns much usage optimization and
estimating work to engineering and now covers AI model, token, inference, GPU, and
agentic cost concerns. Downgraded from high: the source is the field's own foundation
and is partly normative rather than independent outcome evidence.
[FinOps usage optimization](https://www.finops.org/framework/capabilities/usage-optimization/),
[planning and estimating](https://www.finops.org/framework/capabilities/planning-estimating/),
[FinOps for AI](https://www.finops.org/framework/technology-categories/ai/)

**F10. Demand for cost engineering is large and current, but “extremely in demand”
is only moderately supported.** `[moderate]` The 2025 State of FinOps reports that a
majority of participating practices manage AI costs and that 97% of respondents were
investing across multiple AI infrastructure areas. A separate 2025 cloud-industry
survey reports cost efficiency/savings as the leading cloud-goal metric for the sixth
year running. These are large practitioner signals from different organizations, but
both are self-reported surveys published by organizations that sell, organize, or
advocate in the field; sampling and wording limit causal or population-wide claims.
[State of FinOps 2025](https://data.finops.org/2025-report/),
[2025 State of the Cloud release](https://www.flexera.com/about-us/press-center/new-flexera-report-finds-84-percent-of-organizations-struggle-to-manage-cloud-spend)

**F11. The source/licensing position for a cost-engineering pack is unusually
workable.** `[high]` The FinOps Foundation expressly permits sharing and adaptation of
its Framework under CC BY 4.0 with attribution and change indication. FOCUS supplies
an open, versioned, vendor-neutral vocabulary for cost and usage data. That supports a
curated and attributed pack rather than a link-only wrapper. It does not permit us to
copy unrelated training, certification, or third-party materials without checking
their individual terms.
[FinOps attribution guidance](https://www.finops.org/introduction/how-to-use/),
[FOCUS specification repository](https://github.com/FinOps-Open-Cost-and-Usage-Spec/FOCUS_Spec),
[FOCUS licence](https://github.com/FinOps-Open-Cost-and-Usage-Spec/FOCUS_Spec/blob/main/LICENSE)

**F12. Attested Computation is valuable for the pilot, but it is not an execution
permission.** `[high]` OKF v0.2 can point to an executor and deterministic attester,
which maps well to cost-allocation checks, anomaly calculations, and unit-economics
formulas. The specification explicitly does not define packaging or invocation for
the referenced code. A compiler must therefore keep computation material as
knowledge unless an independently reviewed Skill explicitly binds it to permitted
tools. It must never infer `allowed-tools` or execute code from an OKF bundle.
[OKF specification non-goals and Attested Computation](https://github.com/GoogleCloudPlatform/knowledge-catalog/blob/main/okf/SPEC.md)

---

## Opportunity comparison

| Candidate | Demand evidence | Open reusable corpus | Catalogue fit | Verdict |
| --- | --- | --- | --- | --- |
| OKF delivery + projection infrastructure | Early ecosystem activity; no mature compiler found | Official specification and reference implementation | Cross-pack substrate | **Build experimentally now** `[moderate]` |
| Cost engineering for cloud and AI | Repeated enterprise survey signals; expanding AI scope | FinOps Framework and FOCUS, both attribution-friendly | Additive if engineering-scoped | **First knowledge pack** `[moderate]` |
| Platform engineering | DORA reports 90% internal-platform adoption and 76% dedicated teams | DORA material is openly licensed | Useful, but overlaps architecture, IaC, product engineering, and release engineering | Second-wave candidate `[moderate]` |
| Secure software supply chain | Strong standards and regulatory pull | NIST SSDF and related public standards | Already substantially covered by `security-checklists` | Enrich existing skill, not a pack `[high]` |
| SRE / reliability | Established recurring need | Some open material, but prominent books have restrictive reuse terms | Overlaps `release-engineering` and `operational-safety` | Do not lead with it `[moderate]` |

The platform-engineering adoption figures come from DORA's 2025 practitioner
research and are not independently replicated here.
[DORA platform engineering](https://dora.dev/capabilities/platform-engineering/)

---

## Recommended architecture

```text
Authoritative licensed sources + enterprise-local knowledge
                         │
                         ▼
              canonical OKF v0.2 bundle
              (all extensions preserved)
                         │
            ┌────────────┴────────────┐
            ▼                         ▼
  raw references/okf/        x-agentbundle-selected concepts
  shipped unchanged                   │
                                      ▼
                         deterministic Skill projection
                         SKILL.md + references + trace metadata
            └────────────┬────────────┘
                         ▼
             existing AgentBundle adapter projection
             Codex / Claude / Gemini / Cursor / Copilot / Kiro
```

This makes the OKF bundle the source of truth and generated Skills disposable.
There is intentionally no reverse conversion from generated Skill to OKF. Unknown
OKF fields survive because the raw canonical tree survives, not because generated
Markdown can losslessly reconstruct them.

### Minimal extension profile

The exact vocabulary belongs in a versioned contract, but the smallest useful shape
is:

```yaml
---
type: Playbook
title: Triage an AI cost anomaly
description: Determine whether an AI workload cost change is expected or actionable.
x-agentbundle:
  schema: https://agentbundle.dev/schemas/okf-skill-projection/v1
  skill:
    name: triage-ai-cost-anomaly
    description: Triage unexpected AI workload spend. Use for cost spikes or alerts.
    entrypoint: playbooks/triage-ai-cost-anomaly.md
    include:
      - concepts/ai-cost-drivers.md
      - concepts/unit-economics.md
    modes: [quick, full]
---
```

Compiler rules should be conservative:

1. Preserve and ship the input bundle byte-for-byte; never rewrite unknown fields.
2. Project only concepts with a supported, versioned `x-agentbundle.skill` object.
3. Validate the OKF version and extension schema independently.
4. Resolve includes within the bundle root; reject path traversal, name collisions,
   missing entrypoints, unsupported extension versions, and stale or deprecated
   entrypoints unless explicitly overridden by policy.
5. Produce stable ordering, a source digest, and trace metadata in generated Skills.
6. Copy provenance and licence notices into the generated output; do not collapse
   per-concept trust into one pack-wide assertion.
7. Treat executors, attesters, scripts, URLs, and tool permissions as inert data
   unless a separately reviewed mapping explicitly activates them.

### Where it belongs in AgentBundle

**Now:** a catalogue authoring convention and a thin routing skill in each adopting
pack. Store raw OKF under `.apm/skills/<skill>/references/okf/`. Generate committed
skill directories so normal adapter builds remain deterministic projection-only
operations.

**After two callers:** consider an optional `agentbundle catalogue compile-okf`
authoring command and a drift check. YAML parsing should be an optional authoring
dependency, not silently added to the stdlib-only runtime path. A public CLI command,
new primitive, or adapter-contract change should proceed through the repository's RFC
and engine-change process.

**Not yet:** `.apm/knowledge/`, automatic execution of OKF computations, a central
global extension registry, or reverse transformation. Each adds a public boundary
before a second caller demonstrates that the simpler Skill-contained form is
insufficient.

---

## Pilot pack: cost engineering

The pilot should teach a recurring engineering operating loop, not become a finance
or procurement handbook:

1. **Frame cost as a quality attribute** — define cost objectives and unit metrics
   alongside performance, reliability, security, and sustainability.
2. **Estimate a change** — compare architecture, service, model, and workload
   placement options with explicit assumptions and sensitivity ranges.
3. **Allocate and inspect** — use FOCUS vocabulary where available; distinguish
   shared, idle, committed, and directly attributable cost.
4. **Triage anomalies** — establish expected change, isolate the driver, quantify
   value versus effort, and avoid optimization that harms service objectives.
5. **Optimize cloud and AI workloads** — rightsizing, scheduling, caching, batching,
   model routing, token controls, GPU utilization, and architectural trade-offs.
6. **Verify outcomes** — use attested formulas or scripts where safe, preserve
   receipts outside the knowledge bundle, and record when knowledge becomes stale.

Boundaries should exclude accounting policy, tax, procurement negotiation,
chargeback politics, and vendor-specific pricing advice. Those are enterprise-local
or time-sensitive domains and would weaken the pack's universal SDLC fit.

The two initial callers for the projection should be this new pack and one existing
knowledge-heavy skill such as `security-checklists` or `operational-safety`. That
tests whether the extension is genuinely generic before changing the engine.

---

## Suggested decision sequence

1. **Convention spike:** hand-author a tiny OKF bundle and thin router Skill; verify
   current adapters ship it unchanged.
2. **Contract spike:** write the `x-agentbundle` JSON Schema and golden input/output
   fixtures. Include unknown extension fields and Attested Computation negative
   cases.
3. **Two-caller pilot:** project cost-engineering plus one existing knowledge-heavy
   skill. Measure source duplication, generated diff stability, retrieval behavior,
   and authoring burden.
4. **Decision gate:** only then decide whether the compiler remains a pack-local
   authoring tool, becomes an optional AgentBundle CLI command, or justifies a new
   primitive.
5. **Catalogue proposal:** if the cost-engineering pilot passes the charter's
   additive/frequency bar, route the new pack through the catalogue pack proposal
   workflow rather than scaffolding it from this research alone.

---

## Known unknowns

- **Known-unknown:** whether agents retrieve nested OKF indexes more accurately or
  cheaply than equivalent ordinary Skill references. Close with a controlled task
  set comparing answer quality, loaded tokens, and source attribution.
- **Known-unknown:** whether `x-agentbundle` should annotate existing domain types or
  introduce an `Agent Skill` type. Close during the schema spike; annotation is the
  conservative default because `type` describes the knowledge concept, not a build
  target.
- **Known-unknown:** whether any adapter drops nested files or alters bytes in a real
  multi-adapter build. Local code inspection says it should not; the convention spike
  must verify actual artifacts.
- **Known-unknown:** whether a reusable public OKF enterprise/SDLC corpus appears as
  the ecosystem matures. Re-run the catalogue scan before productizing the compiler.
- **Known-unknown:** whether cost-engineering users want one broad router skill or
  several task-specific generated skills. Close with pilot task routing, not design
  preference.
- **Unknowable from desk research:** actual willingness to install or pay for either
  the infrastructure or the pack. Survey demand is not product demand; adopter
  interviews or a published pilot are required.

---

## Sources and search boundary

Primary sources: [OKF v0.2 specification](https://github.com/GoogleCloudPlatform/knowledge-catalog/blob/main/okf/SPEC.md) ·
[Google OKF announcement](https://cloud.google.com/blog/products/data-analytics/how-the-open-knowledge-format-can-improve-data-sharing) ·
[OKF v0.2 announcement](https://cloud.google.com/blog/products/data-analytics/okf-v0-2-adds-trust-signals/) ·
[Agent Skills specification](https://github.com/agentskills/agentskills/blob/main/docs/specification.mdx) ·
[FinOps Framework](https://www.finops.org/framework/) ·
[FinOps reuse terms](https://www.finops.org/introduction/how-to-use/) ·
[FOCUS specification](https://github.com/FinOps-Open-Cost-and-Usage-Spec/FOCUS_Spec) ·
[DORA platform-engineering capability](https://dora.dev/capabilities/platform-engineering/).

Market/practitioner sources: [State of FinOps 2025](https://data.finops.org/2025-report/) ·
[Flexera 2025 State of the Cloud release](https://www.flexera.com/about-us/press-center/new-flexera-report-finds-84-percent-of-organizations-struggle-to-manage-cloud-spend).
These are treated as directional self-report evidence, not independent causal proof.

Ecosystem search covered the official repository, discussions, GitHub topic,
community tool catalogue, and searches for OKF compilers, schemas, extensions,
skills, enterprise knowledge, platform engineering, SRE, software supply chain, and
FinOps materials as of 2026-08-14. Public indexing is incomplete and the ecosystem is
changing quickly; all negative ecosystem findings are therefore capped at
`[moderate]` confidence.
