# Native ADR caller example

`decision.md` is an adopter-owned decision in plain MADR-like Markdown. The
bundle uses its evidence ID for both `request` and `constraints`; it needs no
catalogue record format or workflow approval event.

All evidence is synthetic. `saved-plan.synthetic` contains demonstration bytes,
not an executable Terraform plan. `inspection.json` models `terraform show -json`
output; it was not produced by running Terraform. The lock and four check reports
are synthetic too. Provider versions and the source revision are illustrative.
The example makes no claim about Terraform compatibility or producer authenticity.
No cloud account, state payload or credentials are included.

Run from the repository root with Python 3.11 or newer:

```sh
python3 packs/iac-terraform/.apm/skills/generate-iac/scripts/plan_bundle.py validate iac-plan-bundle.v1.json --root packs/iac-terraform/.apm/skills/generate-iac/assets/native-adr-caller --policy trusted-policy.json --now 2026-01-01T12:30:00Z
```

Expected exit code: `0`. Expected stdout (one JSON object):

```json
{"status":"valid","issues":[],"evidence":[{"id":"native-decision","verification":"verified"},{"id":"saved-plan","verification":"verified"},{"id":"plan-inspection","verification":"verified"},{"id":"dependency-lock","verification":"verified"},{"id":"validation-proof","verification":"verified"},{"id":"policy-proof","verification":"verified"},{"id":"security-proof","verification":"verified"},{"id":"review-proof","verification":"verified"}]}
```

The caller selects `trusted-policy.json` explicitly, outside the bundle. Its four
required checks bind to the saved-plan digest, as does the inspection evidence.
The fixed clock keeps the example within its one-hour freshness window. Evidence
locators and input paths resolve beneath `--root`; move this whole directory to
use it elsewhere and point to the installed skill's script.

Change one byte of a temporary copy of `saved-plan.synthetic` without updating
the bundle: validation exits `1` with `status: "invalid"` and `digest-mismatch`.
A valid result checks the recorded bytes and bindings; it grants no deployment
or production-promotion approval.
