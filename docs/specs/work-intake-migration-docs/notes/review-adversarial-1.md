# Adversarial implementation review — round 1

## Blockers

**1. Repair-plan migration reads bypass the safe-read contract.** `packs/core/.apm/skills/workspace-status/scripts/workspace_status.py:2211`
and
   `packs/core/.apm/skills/workspace-status/scripts/workspace_status_engine.py:4360`
   read the human selection and workspace through ordinary `Path` reads after
   confinement.
   **Fix:** Route both through guarded pre-open/fstat/post-stat reads and return
   `unsafe_path` on identity mismatch.
**2. Repository identity is not bound to ledger operations.** `contracts/jsonschema/work-intake-migration-manifest.schema.json:9`
omits
   that semantic invariant, while the operation digest in
   `workspace_status_engine.py:4319` excludes repository identity.
   **Fix:** Bind the identity cryptographically or reject any operation not
   bound to it, then update fixtures and tests.
**3. Stale workspace bytes can pass recovery by membership shape.** `packs/core/.apm/skills/workspace-status/scripts/workspace_status.py:1573`
falls back from
   fingerprints to legacy/target membership shape.
   **Fix:** Require exact recorded fingerprints for effects, pre-record expected
   post-effect fingerprints for recovery, and keep membership inspection
   diagnostic-only.
**4. Mixed migration argument sets escape the JSON result contract.** `packs/core/.apm/skills/workspace-status/scripts/workspace_status.py:1980`
lets
argparse reject flags
   that belong to another migration verb, producing usage text instead of the
   AC27 JSON refusal envelope.
   **Fix:** Admit migration-surface flags at those parsers and reject partial or
   mixed sets with closed result codes.
**5. Shipping metadata remains in implementation state.** `docs/specs/work-intake-migration-docs/spec.md:3`
After runtime
   blockers and all reviews are clean, the spec and plan still require their
   terminal lifecycle edits.
   **Fix:** Set the spec to `Shipped`, the plan to `Done`, mark met acceptance
   criteria, and leave AC14 explicitly deferred to
   `capture-work-alias-removal`.
