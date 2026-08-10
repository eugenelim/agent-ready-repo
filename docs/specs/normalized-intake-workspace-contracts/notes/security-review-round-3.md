# Security review round 3

**1. Hybrid/Major — scheme-relative URL userinfo passes locator validation** `contracts/jsonschema/normalized-intake.schema.json:212`

The userinfo denial requires an explicit URI scheme, so a network-path
reference such as `//user:secret@example-service.invalid/item` remains valid.
Make durable locators exclude all userinfo, query, and fragment delimiters and
add invalid fixtures in both schema families. **Disposition: apply.**
