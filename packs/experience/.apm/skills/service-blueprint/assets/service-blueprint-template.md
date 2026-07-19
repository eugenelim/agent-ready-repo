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

<!-- Traceability markers. Emit one bold-body Service field per distinct backstage
     service above — the literal form is the placeholder line below — as a stable
     kebab-case slug (the first token is the id). The structural-orphan lint reads
     each such Service line as a `service` chain node; a screen action ties down to
     one. Keep the slugs in sync with the service names in the table above. (Don't
     write the bold marker inside a comment — the lint scans every line, so a
     commented example would mint a phantom node.) -->

- **Service:** <service-slug>
- **Service:** <service-slug>

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
