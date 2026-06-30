---
type: service-blueprint
journey: "<journey name>"
slug: "<kebab-case-slug>"
date: "<YYYY-MM-DD>"
---

# Service Blueprint: <Journey Name>

## Summary

**Journey:** <one-sentence description of the customer journey this blueprint covers>
**Scope:** <start stage> → <end stage>
**Surfaces / channels:** <web | mobile | in-person | …>

---

## Blueprint

<!-- Column headings = journey steps (one per stage/touchpoint).
     Fill each row for every column. Leave no frontstage cell without
     checking the backstage row — a blank backstage against a frontstage
     action is a named gap (see "Column gaps" below). -->

| Row | Step 1: <name> | Step 2: <name> | Step 3: <name> | … |
| --- | --- | --- | --- | --- |
| **Frontstage** (customer actions + touchpoints) | | | | |
| ············· LINE OF VISIBILITY ············· | | | | |
| **Backstage** (employee + system actions, hidden from customer) | | | | |
| **Support** (internal systems + vendors enabling backstage) | | | | |

---

## Column gaps

<!-- List every frontstage action that has no backstage entry.
     Each gap is design debt — name it so the spec LLD can plan for it. -->

- Step N: <description of gap>

---

## Named backstage services

<!-- Every distinct backstage service, named by-reference for hand-off.
     When `architect`/`contracts` are present: use stable, short noun-phrase
     service names. When absent: add a one-line role description. -->

| Service name | Role | Hand-off target |
| --- | --- | --- |
| <Service Name> | <one-line role> | `architect` / `contracts` / spec LLD |

---

## Hand-off

<!-- The by-reference seam. List named backstage services and their
     downstream consumer. Do NOT draft the downstream artifact here. -->

The following backstage services are named candidates for downstream work:

- **<Service Name>** → `architect` (C4 component decomposition)
- **<Service Name>** → `contracts` (interface contract)
- **<Service Name>** → spec LLD (integration requirement)

---

## Open questions

<!-- Gaps, assumptions, or ambiguities to resolve before the blueprint
     is consumed downstream. -->

- [ ] <question>
