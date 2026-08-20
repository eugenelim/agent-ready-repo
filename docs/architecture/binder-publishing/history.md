# History (non-normative)

> Review and verification chronology. Normative files and
> [`decisions.md`](decisions.md) govern when this record differs.

## Shape decisions

| Decision | Change |
| --- | --- |
| D-A / D39 | Removed the trusted profile, policy files, grants, and six authority flags. Strict is the only profile. |
| D41 | Removed caller-named write destinations. Each verb derives its write location. |
| D-B / D40 | Replaced Quarto with Zensical as the v1 renderer. ADR-0073 holds the renderer decision. |
| D42 | Replaced cross-pack template discovery with producer-written recipes in the adopter `recipes_dir`. |
| D43 | Removed profile from the index and content key. |
| D44 | Moved chapter numbering to compiler-emitted `data-ordinal` attributes. |
| D46 | Replaced fence-attribute accessibility with theme-lifted Mermaid `accTitle:` and `accDescr:` directives. |
| D47 | Changed `--root` from required to recommended on measured agent surfaces; retained the installed-pack guard. |

## Review chronology

| Period | Result |
| --- | --- |
| Cold reviews 1–5 | Identified contradictory contracts, write-side confinement failures, emitted-string injection, and incomplete trust routing. |
| Cold reviews 6–8 | Required execution against the real renderer configuration and separated the neutral index from renderer plans. |
| Cold reviews 7–10 | Split the draft into this tree; D-A and D-B removed the repeated trust and renderer defect classes. |
| 2026-08-06 | Z1–Z4 corrected version probing, font suppression, Mermaid delivery, config behavior, and navigation validation. |
| 2026-08-07 | Z5 confirmed network-denied build behavior. Z6 replaced the accessible-name mechanism with D46. V6 changed the `--root` requirement to D47. |

## Rejected implementation shapes

| Shape | Recorded outcome |
| --- | --- |
| Renderer-specific contract | Replaced by the neutral index and adapter plan split. |
| Repository docs-site integration | Deferred behind index consumption or static mounting. |
| Custom static-site generator | Not selected for v1. |
| Cross-pack template scanning | Replaced by D42. |
