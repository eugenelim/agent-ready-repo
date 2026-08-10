# Security review round 1

**1. Hybrid/Major — recursive constraints bypass payload and secret-field guards** `contracts/jsonschema/normalized-intake.schema.json:170`

`suppliedConstraints` accepts unrestricted property names and recursively
reuses `constraintValue`, allowing schema-valid raw-payload or credential-like
keys at arbitrary depth. Replace it with a finite-depth constraint value and
deny sensitive/instruction-bearing key names; add nested and denied-key invalid
fixtures. **Disposition: apply.**

**2. Hybrid/Major — Windows drive-qualified paths pass the relative-path contract** `contracts/jsonschema/workspace-entry.schema.json:38`

Both path definitions reject POSIX absolute paths, backslashes, and `..`, but
accept `C:/...` and `C:...`. Reject drive-qualified forms in both schemas and
add invalid fixtures. **Disposition: apply.**

**3. Reason/Major — durable source locators can carry embedded credentials** `contracts/jsonschema/workspace-entry.schema.json:52`

The schemas reject a sibling credential field but accept URL userinfo and
credential-looking query parameters in durable `locator` / `ref` strings.
Reject those forms in both schemas and add invalid fixtures for both source
contracts. **Disposition: apply.**

SAST was green before review; the reviewer did not rerun scanners or gates.
