# Additive Linear acceptance-criteria comment write-back

- **Status:** Draft
- **Level:** feature

## Outcome

When confirmed adopter demand exists, Linear acceptance criteria can be written back as additive comments without rewriting an Issue description.

## Opportunity

Linear v1 has shipped, but automatic acceptance-criteria comment write-back remains intentionally absent pending real adopter demand.

## What this absorbs

### push-acs-to-linear

When needed, add a confirmed additive `commentCreate` flow that never rewrites the Linear Issue description. `packs/linear/.apm/skills/linear/scripts/linear.py:836` has `if action == "comment":`; the configured write-back maps `comment` to the `commentCreate` mutation and sends only `issueId` plus comment body. The previous premise changed: no implementation gap is currently authorized without real adopter demand.

## Assumptions

- This changed premise is settled by a dated adopter request confirming demand for automatic acceptance-criteria comment write-back.

## Source

- Mode: repo-origin
- Locator: workspace.toml
- Revision: 581dd8b7aefba04f566e4ea9a3213da8c6afb55d
