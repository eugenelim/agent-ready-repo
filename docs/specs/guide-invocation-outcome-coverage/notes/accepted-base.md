# Accepted base: guide invocation and outcome coverage

Captured 2026-09-09 with:

```text
python3 tools/audit-guide-affordances.py --ledger <temporary-path>
```

This ledger freezes the targets accepted with the spec. Corpus additions do not
expand the slice. `A` means literal chat input and `D` means stated outcome.

Parent S3 boundary: “Every current in-scope target identified by the audit
gains its missing source-grounded invocation or outcome affordance; the
accepted-base ledger proves positive movement without freezing corpus totals.”

## Guide targets

| Guide | Missing affordance |
| --- | --- |
| `guides/catalogue-curation/explanation/catalogue-operator-journey.md` | A |
| `guides/core/reference/work-intake-routing-and-lifecycle.md` | A |
| `guides/credential-brokers/explanation/credentialed-skills.md` | A |
| `guides/credential-brokers/how-to/add-a-credentialed-skill.md` | A |
| `guides/figma/how-to/inspect-a-figma-file.md` | A |
| `guides/figma/reference/figma-skill.md` | A |
| `guides/frontend-engineering/reference/performance-targets.md` | A |
| `guides/iac-terraform/README.md` | A |
| `guides/monorepo-extras/README.md` | A |
| `guides/product-strategy/README.md` | D |
| `guides/product-strategy/explanation/why-strategy-is-its-own-seat.md` | A, D |
| `guides/product-strategy/reference/frameworks-and-artifacts.md` | A, D |

The first nine rows are the audit's remaining phrase-harvest targets after
excluding `guides/experience-design/**`. The last three are the unfinished
product-strategy U3 targets.

## Skill-description targets

Each published source below lacks a quoted example utterance. Sources that also
lack `Triggers on` receive it in their `description:` field; sources that
already carry `Triggers on` keep it while gaining the quoted example.

- `packs/atlassian/.apm/skills/confluence-crawler/SKILL.md`
- `packs/atlassian/.apm/skills/confluence-publisher/SKILL.md`
- `packs/atlassian/.apm/skills/jira/SKILL.md`
- `packs/atlassian/.apm/skills/jira-align/SKILL.md`
- `packs/atlassian/.apm/skills/jira-align-brief-intake/SKILL.md`
- `packs/atlassian/.apm/skills/jira-align-refresh/SKILL.md`
- `packs/atlassian/.apm/skills/jira-brief-intake/SKILL.md`
- `packs/atlassian/.apm/skills/jira-refresh/SKILL.md`
- `packs/catalogue-curation/.apm/skills/compile-okf/SKILL.md`
- `packs/contracts/.apm/skills/api-contract/SKILL.md`
- `packs/contracts/.apm/skills/event-contract/SKILL.md`
- `packs/converters/.apm/skills/file-to-markdown/SKILL.md`
- `packs/converters/.apm/skills/markdown-to-docx/SKILL.md`
- `packs/converters/.apm/skills/markdown-to-html/SKILL.md`
- `packs/converters/.apm/skills/markdown-to-pptx/SKILL.md`
- `packs/converters/.apm/skills/markdown-to-xlsx/SKILL.md`
- `packs/converters/.apm/skills/mermaid-renderer/SKILL.md`
- `packs/converters/.apm/skills/msg-to-markdown/SKILL.md`
- `packs/core/.apm/skills/adapt-to-project/SKILL.md`
- `packs/core/.apm/skills/author-delivery-brief/SKILL.md`
- `packs/core/.apm/skills/close-work/SKILL.md`
- `packs/core/.apm/skills/intake-intent/SKILL.md`
- `packs/core/.apm/skills/project-knowledge/SKILL.md`
- `packs/core/.apm/skills/work-intake/SKILL.md`
- `packs/core/.apm/skills/work-loop/SKILL.md`
- `packs/desk-research/.apm/skills/build-outline/SKILL.md`
- `packs/desk-research/.apm/skills/compare-hypotheses/SKILL.md`
- `packs/desk-research/.apm/skills/decision-archaeology/SKILL.md`
- `packs/desk-research/.apm/skills/desk-research/SKILL.md`
- `packs/desk-research/.apm/skills/desk-research-project-status/SKILL.md`
- `packs/desk-research/.apm/skills/identify-perspectives/SKILL.md`
- `packs/desk-research/.apm/skills/source-map/SKILL.md`
- `packs/figma/.apm/skills/figma/SKILL.md`
- `packs/github/.apm/skills/github-brief-intake/SKILL.md`
- `packs/github/.apm/skills/github-refresh/SKILL.md`
- `packs/governance-extras/.apm/skills/rfc-status/SKILL.md`
- `packs/linear/.apm/skills/linear/SKILL.md`
- `packs/linear/.apm/skills/linear-brief-intake/SKILL.md`
- `packs/product-documentation/.apm/skills/author-product-docs/SKILL.md`
- `packs/product-engineering/.apm/skills/diverge-solutions/SKILL.md`
- `packs/product-engineering/.apm/skills/place-bet/SKILL.md`
- `packs/user-guide-diataxis/.apm/skills/new-guide/SKILL.md`

## Accepted pack versions

These top-level manifest versions are the release baselines for AC8:

| Pack | Accepted version |
| --- | --- |
| `atlassian` | `0.9.3` |
| `catalogue-curation` | `0.4.6` |
| `contracts` | `0.3.6` |
| `converters` | `0.9.6` |
| `core` | `2.25.7` |
| `desk-research` | `1.1.7` |
| `figma` | `0.3.3` |
| `github` | `0.2.3` |
| `governance-extras` | `0.10.5` |
| `linear` | `0.3.3` |
| `product-documentation` | `0.1.1` |
| `product-engineering` | `0.13.9` |
| `user-guide-diataxis` | `0.3.1` |

## Deliberate exclusions

- `guides/experience-design/**` remains owned by
  `docs/product/intents/experience-design-delivery-packet.md`.
- `ase-okf-reference`, `architecture-lenses-reference`, `operational-safety`,
  `security-checklists`, and `security-checklists-reference` are internal or
  reference-only routing surfaces, not user invocation targets.
- `author-brief`, `capture-work`, and `receive-brief` are deprecated
  compatibility aliases; adding new invitation copy would work against their
  retirement direction.
- New cross-pack digital-product tutorials, intent indexes, and role-specific
  first-value, safety, recovery, or evaluation content remain with their
  related intents.
