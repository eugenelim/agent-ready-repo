# Architecture assessment intents: decision taxonomy and corpus implications

## Research question

What mutually exclusive primary decision intents, taken together, cover the
common reasons for assessing an existing application's or repository's
architecture; what evidence does each intent require; and what reusable
knowledge can a portable assessor carry without pretending to know the adopting
organization's local context?

## Sources and method

This is a standard desk-research synthesis of primary standards bodies,
framework owners, and original engineering-method sources. The taxonomy is a
synthesis: no cited source publishes this exact six-intent set. Material
findings are triangulated across at least three independent source families.

## Findings

### 1. Start with the decision and concerns, not a universal checklist [high]

Architecture descriptions exist to address stakeholder concerns through
selected viewpoints; architecture evaluation methods derive prioritized quality
scenarios from mission and business drivers; workload frameworks likewise ask
teams to prioritize requirements and trade-offs against a workload's purpose.
The stable assessment method can therefore be shared, but evidence selection and
the meaning of “good enough” must follow the decision being supported.
([ISO/IEC/IEEE 42010:2022](https://www.iso.org/standard/74393.html),
[SEI ATAM collection](https://www.sei.cmu.edu/library/architecture-tradeoff-analysis-method-collection/),
[Azure Well-Architected workload model](https://learn.microsoft.com/en-us/azure/well-architected/workloads))

### 2. Quality attributes are lenses, not assessment intents [high]

Reliability, security, performance, cost, operability, and sustainability recur
as cross-cutting quality areas in independent cloud architecture frameworks.
They do not state why a particular assessment is being commissioned. Security,
for example, may dominate a hardening assessment, constrain a migration, or be
one trade-off in a growth assessment. The corpus should therefore route quality
lenses orthogonally to decision intent.
([AWS Well-Architected review guidance](https://docs.aws.amazon.com/wellarchitected/latest/framework/ops_evolve_ops_process_cont_imp.html),
[Azure Well-Architected Framework](https://learn.microsoft.com/en-us/azure/well-architected/what-is-well-architected-framework),
[Google Cloud Well-Architected Framework](https://docs.cloud.google.com/architecture/framework))

### 3. Six primary decision intents form a practical MECE routing set [moderate]

The following set is mutually exclusive when classification uses the report's
primary decision verb. A report may name secondary intents, but it must choose
one primary intent or declare that the decision is still unresolved.

| Primary intent | Decision supported | Distinguishing evidence | Characteristic report outcome |
| --- | --- | --- | --- |
| Baseline / understand | What is this system, how does it work, and what remains unknown? | Declared versus implemented views, dependency/data/runtime boundaries, delivery and operational evidence coverage | Correctable current-state model, evidence gaps, and bounded hypotheses |
| Assure / harden | Is risk controlled enough for a stated obligation, threat, release, or service level? | Target outcomes and tolerance, threats/incidents, control implementation and exercise, failure/recovery evidence, compliance obligations | Accept/contain/remediate decision with proof requirements and residual risk |
| Optimize current outcomes | How can the retained system perform its present mission more efficiently or effectively? | Current workload and service baselines, latency/throughput, cost, toil, delivery flow, bottleneck traces, before/after target | Ranked, measurable improvements that preserve the present mission and major boundaries |
| Evolve / prepare for growth | What must change to support a defined future demand, capability, market, or team scale? | Future scenarios and horizon, demand/capacity model, sensitivity points, provider limits, change coupling, team/operating constraints | Runway, trigger thresholds, staged investments, and experiments |
| Transform / modernize | How should a system that remains needed move to a materially different architecture, platform, or delivery model? | Drivers and target constraints, seams/contracts, data migration, compatibility, characterization coverage, skills, cutover and rollback | Comparative transition options and an incremental modernization roadmap |
| Rationalize / disposition / due diligence | Should the organization retain, invest in, consolidate, acquire/integrate, replace, or retire this system? | Business criticality/value, strategic fit, usage, total cost, redundancy, technical health, legal/retention duties, exit dependencies, option cost/risk | Evidence-backed disposition and investment decision; a follow-on transformation assessment if retained |

This synthesis is supported by: architecture evaluation tied to business drivers
and quality scenarios; current-versus-target risk profiles; recurring workload
improvement reviews; distinct current-demand and future-demand guidance; and
portfolio/migration frameworks that explicitly retain, retire, replace,
replatform, or rearchitect workloads.
([SEI ATAM collection](https://www.sei.cmu.edu/library/architecture-tradeoff-analysis-method-collection/),
[NIST CSF 2.0 organizational profiles](https://csrc.nist.gov/pubs/sp/1301/final),
[Azure performance-efficiency guidance](https://learn.microsoft.com/en-us/azure/well-architected/performance-efficiency/),
[Azure mission-critical capacity guidance](https://learn.microsoft.com/en-us/azure/well-architected/mission-critical/mission-critical-design-principles),
[AWS application portfolio management](https://docs.aws.amazon.com/whitepapers/latest/aws-caf-governance-perspective/application-portfolio-management.html),
[Microsoft migration-strategy options](https://learn.microsoft.com/en-au/azure/cloud-adoption-framework/digital-estate/5-rs-of-rationalization))

Confidence is moderate rather than high because MECE completeness is an
analytical construction. It must be pressure-tested against real prompts and
may need label changes even if the decision boundaries remain stable.

### 4. Modernization and rewrite require two decision gates [high]

Modernization sources distinguish multiple strategies and warn that the more
structural options introduce additional complexity and risk. Portfolio guidance
also includes retain, replace/repurchase, and retire, so a technical assessment
cannot assume that transformation is the right investment. First decide the
system's disposition; if it remains needed, compare transformation paths. A full
rewrite is one option, not a default conclusion from age, size, coupling, or
technology fashion.
([Microsoft migration-strategy options](https://learn.microsoft.com/en-au/azure/cloud-adoption-framework/digital-estate/5-rs-of-rationalization),
[AWS migration strategies](https://docs.aws.amazon.com/prescriptive-guidance/latest/large-migration-guide/migration-strategies.html),
[SEI Architecture Options Workshop](https://www.sei.cmu.edu/library/creating-software-modernization-roadmaps-the-architecture-options-workshop/))

### 5. Local operating context is input to the assessment, not portable corpus truth [high]

Organizational profiles are explicitly tailored to mission objectives,
stakeholder expectations, threats, and requirements; cloud guidance tells teams
to use internal standards where present and recognizes that workload ownership,
budgets, support, and operating models vary. A catalogue bundle cannot know
those facts. It can carry context categories, common patterns, elicitation
questions, and confidence rules, then keep retrieved local facts in a separate
enterprise-context evidence plane.
([NIST CSF 2.0 profiles](https://www.nist.gov/cyberframework/profiles),
[AWS continuous-improvement guidance](https://docs.aws.amazon.com/wellarchitected/latest/framework/ops_evolve_ops_process_cont_imp.html),
[Azure operating-model readiness](https://learn.microsoft.com/en-us/azure/cloud-adoption-framework/strategy/prepare-organizational-alignment),
[DORA loosely coupled teams](https://dora.dev/capabilities/loosely-coupled-teams/))

## Routing rules

- **Baseline versus another intent:** use Baseline only when the immediate
  decision is shared understanding or evidence acquisition. Once an acceptance,
  improvement, future-readiness, transformation, or investment decision is
  named, that becomes primary and Baseline becomes its Map stage.
- **Assure versus Optimize:** a threshold, obligation, threat, release, or risk
  acceptance decision is Assure. A measurable improvement to the present
  mission without an acceptance threshold is Optimize.
- **Optimize versus Evolve:** current workload and current capability targets
  are Optimize. A named future horizon, demand shape, capability, market, or
  organizational scale is Evolve.
- **Evolve versus Transform:** Evolve asks what the future scenario requires;
  Transform begins when materially changing architecture or platform is itself
  an option to compare and sequence.
- **Transform versus Disposition:** “how do we modernize this retained system?”
  is Transform. “should we retain, replace, retire, or rewrite it?” is
  Rationalize/Disposition. The latter may hand off to the former.
- **Incident response and new-system design:** active incident containment is an
  incident/defect workflow with a later Assure assessment; a net-new target
  architecture is future-state design, not repository assessment.

## Corpus implications

The OKF bundle should contain one concept per primary intent. Each records:

- supported decision and explicit non-decisions;
- minimum evidence and the confidence floor for action;
- repository evidence available without execution;
- operational, enterprise, or business data that require separate access;
- decision-specific scenarios and attention signals;
- false positives and common category errors;
- valid report outcomes and mandatory alternatives;
- hand-offs to other intent or specialist workflows.

The separate operating-context branch should be named around **context
acquisition and common operating-model patterns**, not “enterprise standards.”
It may enumerate local facts to discover—ownership, on-call and support model,
approved platforms, identity and data policies, service levels, regulatory
obligations, sourcing constraints, delivery controls, budgets, skills, and
in-flight change—and common organizational patterns that help form hypotheses.
It must never assert which pattern or standard an adopter uses.

## Known unknowns

- **Known-unknown:** whether six labels are understandable and reliably selected
  from ordinary user prompts. Would be closed by: frozen routing evals plus
  dogfood across ambiguous, mixed-intent, and same-repository/different-intent
  cases.
- **Known-unknown:** whether portfolio/disposition belongs in the architect
  pack's initial product boundary. Would be closed by: guide-level journey tests
  showing the assessor can request business evidence without pretending a code
  repository contains it.
- **Known-unknown:** which corpus concepts require explicit freshness horizons.
  Would be closed by: the per-concept source audit distinguishing durable method
  from changing platform or regulatory guidance.
- **Unknowable from public research:** an adopter's actual standards, ownership,
  risk tolerance, target demand, budget, skills, and portfolio strategy. Why not:
  these are local facts that must be elicited or retrieved through an authorized
  enterprise knowledge surface.

## Conclusion

Use six primary intent concepts—Baseline, Assure, Optimize, Evolve, Transform,
and Rationalize/Disposition—plus orthogonal quality, system-shape, workload, and
operating-context-pattern lenses. Require one primary decision per assessment,
allow named secondary intents, and preserve ambiguity when evidence or user
intent does not support a choice. Build every corpus concept from a traceable
desk-research packet and validate it through routing and report dogfood rather
than treating the initial taxonomy as self-proving.
