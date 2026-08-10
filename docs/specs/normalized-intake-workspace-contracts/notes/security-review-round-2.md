# Security review round 2

**1. Hybrid/Major — sensitive-name rejection misses common aliases** `contracts/jsonschema/normalized-intake.schema.json:171`

The first hardening pass rejects its fixtures but still permits concatenated
`apikey` / `apitoken` constraint names and plural `credentials`, `tokens`,
`secrets`, or `passwords` query keys. Centralize the sensitive-name matcher,
cover those aliases in both schema families, and add regression fixtures.
**Disposition: apply.**
