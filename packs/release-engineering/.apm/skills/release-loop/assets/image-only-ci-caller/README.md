# Image-only CI caller example

This directory is a complete, local schema `"2.0"` candidate for one application
image. All evidence is synthetic, including the OCI manifest, attestation, test
and security reports, source revision, and approved procedure. The manifest is
demonstration bytes, not a runnable image. No image is built or pushed by validation.

Run from the repository root with Python 3.11 or newer:

```sh
python3 packs/release-engineering/.apm/skills/release-loop/scripts/release_handoff.py validate release-handoff.yaml --root packs/release-engineering/.apm/skills/release-loop/assets/image-only-ci-caller --policy trusted-policy.json --now 2026-01-01T12:30:00Z
```

Expected exit code: `0`. Expected stdout (one JSON object):

```json
{"status":"valid","issues":[],"evidence":[{"id":"image-artifact","verification":"verified"},{"id":"provenance","verification":"verified"},{"id":"test-report","verification":"verified"},{"id":"security-report","verification":"verified"},{"id":"approved-procedure","verification":"verified"}]}
```

The caller chooses `trusted-policy.json` outside the candidate. Both required
checks and the provenance record bind to the image component and manifest digest.
The procedure's ID and byte digest must match the trusted policy. The fixed clock
keeps all evidence within the one-hour freshness window. Move this whole directory
to a fresh root to use the installed release skill's script.

`ci-workflow.example.yml` is an illustrative application-CI excerpt, not a
ready-to-run workflow. It shows image build/push and candidate writing. An adopter
must supply checkout, Docker tooling, registry authentication through its approved
mechanism, real attestation/check collection for the built digest, and separately
approved policy/procedure bytes. Do not use the synthetic reports as real proof.
No credentials or deployment commands are included.

Removing `:v1.0.0` or the `@sha256:...` suffix from a temporary candidate copy
causes exit `1`, `status: "invalid"`, and `invalid-image-reference`.
Byte verification does not prove producer authenticity; that trust decision
belongs to the adopter. A valid result grants no deployment or production approval.
