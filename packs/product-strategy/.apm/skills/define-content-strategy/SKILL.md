---
name: define-content-strategy
description: Use when a strategist needs to set the organizational content direction before content design begins — the governance and structural layer above per-surface content execution. Triggers on "define the content strategy", "I need to set the content strategy before content design", "content governance framework", "Halvorson content strategy", "Purpose Process Structure Governance". Produces a committed content-strategy.md. Do NOT use to write per-surface content or microcopy — that belongs to the content-design skill in the experience-design pack.
---

# Skill: define-content-strategy

Produces a **content strategy** — a governance and structural document grounded in the Halvorson content strategy quad (Brain Traffic, 2018 revision): Purpose + Process + Structure + Governance. This is the organizational/governance layer above per-surface content design — it defines why content exists, how it is made and maintained, how it is structured, and how it stays consistent. The artifact feeds the experience-design pack's `content-design` skill and the design-thread `map-screen-flow` step. See `references/agentbundle-layout.md` for artifact path.

## When to invoke

1. **Business goals and audience are known** — content strategy is derived from the organization's goals and its understanding of its audience; it cannot precede them.
2. **Content design has not yet begun** — content strategy is set before per-surface content work, not after.
3. **No current content strategy exists** — amend rather than duplicate.

## Procedure

1. **Establish Purpose.** Ask: "Why does this organization's content exist? What should it achieve for the business and for the audience?" Name the primary content goal (e.g., help users complete tasks, build trust with regulators, educate prospects). Align to the business strategy and any UX strategy artifact in `docs/product/shaping/`.
2. **Define Process.** Map how content is created, reviewed, approved, published, and maintained. Name the roles involved (author, editor, subject-matter expert, approver, publisher). Define the lifecycle: creation → review → publish → maintenance trigger → archive/deprecate. Identify the current process gaps — these are the highest-leverage governance improvements.
3. **Define Structure.** Name the content models: what types of content exist (articles, FAQs, in-app guidance, release notes, API docs), and what metadata each carries (audience, topic, lifecycle stage, owner, last-reviewed date). Define the taxonomy — the controlled vocabulary that makes content findable and reusable. Flag any structural inconsistency that produces the same information in multiple incompatible forms.
4. **Define Governance.** Set the standards for consistency (style guide reference, voice and tone reference — link to `voice-and-microcopy` output if available), accuracy (review cadence, subject-matter expert sign-off requirements), and relevance (deprecation triggers, audit schedule). Name the content owner role responsible for governance.
5. **Document the hand-off to content-design.** Note: "This content strategy is consumed by the `content-design` skill (experience-design pack) and the design-thread `map-screen-flow` step. The Purpose and Governance sections are the primary inputs for per-surface content briefs."
6. **Resolve the artifact path** following `references/agentbundle-layout.md`. Surface the path, then commit `content-strategy.md` with frontmatter `type: content-strategy`.

## Anti-patterns

- **Per-surface content design in this skill.** Content strategy is the organizational/governance layer; writing the actual words for a screen, a tooltip, or an error message belongs in the experience-design pack's `content-design` skill. These are sequential, not synonymous.
- **Governance without an owner.** A governance section without a named role responsible for enforcement is documentation theater — it produces a document no one acts on.
- **Structure without metadata.** Naming content types is not sufficient; each type must carry a metadata schema or it cannot be found, reused, or governed systematically.
