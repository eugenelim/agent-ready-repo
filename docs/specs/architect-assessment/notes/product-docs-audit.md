# Architect product-documentation audit

Mode: retrofit and verify

Audience: external catalogue users, except `packs/architect/DESIGN.md`, which is
the maintainer design record

Natural start: “Assess architecture and provide an action plan.”

Expected result: a corrected current-state model, evidence coverage, attention
heat, bounded hotspot investigation, findings, and traced action waves

Human decisions: correct the map, choose the drill-downs, accept evidence and
action priority, approve any additional evidence boundary or write

Read/write boundary: ordinary repository inspection is read-only; private
retrieval, execution, runtime/operational access, experiments, and writes ask
first

## Complete surface decision

| Surface | Decision | Reason |
| --- | --- | --- |
| `packs/architect/README.md` | Rewritten | The landing page was design-first and listed three skills. It now starts from the generic assessment outcome, previews the progressive conversation, distinguishes the four routes, and states read/write boundaries. |
| `packs/architect/JOURNEY.md` | Rewritten | First value is now a read-only survey with Map and Focus correction gates; standard investigation, optional saving, and review remain reachable. |
| `packs/architect/docs/index.md` | Rewritten | Inventory and positioning now include four workflows, the internal generated router, the optional profiler, and permission boundaries. |
| `web/src/content/packs/architect.md` | Updated | Public pack discovery now includes `architect-assess`, the generic prompt, observable output, and permission posture. |
| `guides/architect/README.md` | Rewritten | The guide index now routes by user job and makes assessment the current-state entry path. |
| `guides/architect/tutorials/architect-first-session.md` | Rewritten | The former automatic `reference.md` write conflicted with the new first-value contract. The tutorial now guarantees a chat-only survey and keeps reference creation separate. |
| `guides/architect/tutorials/create-your-reference-architecture.md` | Updated | Clarifies normative foundation versus descriptive assessment and links the likely assessment follow-up. |
| `guides/architect/how-to/assess-a-repository.md` | Created | Common task recipe with stages, correction points, enterprise modes, automation degradation, repository-shape variations, saving, review, and next action. |
| `guides/architect/how-to/shape-an-architecture-concept.md` | Updated | Routes unknown current state to assessment and preserves design as the future-state workflow. |
| `guides/architect/how-to/diagram-a-system.md` | Updated | Distinguishes a picture as the outcome from an evidence-and-action assessment. |
| `guides/architect/how-to/establish-reference-architecture.md` | Updated | Explains how assessment compares normative intent with implementation without treating `reference.md` as proof. |
| `guides/architect/how-to/review-an-architecture-artifact.md` | Updated | Adds assessment-report review, its dedicated methodology dimensions, and the no-rescan boundary; routes artifact-less current-state asks to assessment. |
| `guides/architect/reference/architecture-assessment.md` | Created | Dry lookup for intents, modes, stages, evidence, enterprise eligibility, permissions, outputs, findings/actions, lens coverage, and finite profiler limits. |
| `guides/architect/reference/reference-architecture.md` | Updated | Corrects the layout table name to `[architecture]`, removes the obsolete silent path scan, includes assessment artifacts, and retains the normative-foundation contract. |
| `guides/architect/explanation/architect-diagram-skill-design.md` | Intentional no change | Its notation, layout, visual-encoding, and portability explanation remains accurate. Current-state assessment routing belongs in the diagram how-to and guide index, not this why-oriented page. |
| `packs/architect/DESIGN.md` | Updated | Maintainer design now records the progressive assessment method, three knowledge planes, OKF corpus boundary, optional profiler, report review, and enterprise permission model. |

## Documentation contract

The how-to is the common task path; the reference owns exhaustive behavior; the
first-session tutorial stays on rails and ends with a verifiable survey. The
pack README, web page, guide index, tutorial, and how-to place the generic prompt
within their first 120 words. Each entry surface names the observable outcome,
read/write line, human decision, and likely next request without requiring skill
names up front.
