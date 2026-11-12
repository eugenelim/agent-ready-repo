---
title: Plan bundle
summary: Fields, validation commands, limits, and result codes for reviewed saved-plan exchange.
pack: iac-terraform
kind: reference
---

# Plan bundle

Validate a reviewed saved plan and its local evidence with Python 3.11 or newer.
From the installed `generate-iac` skill directory, run:

```sh
python3 scripts/plan_bundle.py validate iac-plan-bundle.v1.json --root /protected/bundle --policy trusted-policy.json
```

`/protected/bundle` is your approved evidence directory; replace it with your path.
Input and policy names are relative to that root. Validation reads files and
prints JSON; it never runs Terraform, applies changes, fetches URLs or writes the
bundle. No work-loop approval event is needed to call it.

## Bundle fields

The [schema](../../../packs/iac-terraform/.apm/skills/generate-iac/references/iac-plan-bundle.v1.schema.json)
is owned by `generate-iac`. All fields below are required except those marked optional.

| Field | Type / fields | Meaning |
| --- | --- | --- |
| `schema_version` | `"iac-plan-bundle.v1"` | Exact version string. |
| `source` | Source | Repository and immutable revision or snapshot evidence. |
| `request`, `constraints` | Evidence ID; non-empty evidence ID list | Adopter request and governing constraints. |
| `evidence` | Evidence list | Saved plan, inspection, dependency lock and check proof. |
| `toolchain` | `engine`, `version`, `providers`, `lock` | Engine is `terraform` or `opentofu`; providers are non-empty `{source, version}` records; lock is evidence ID. |
| `target` | Target | Environment and account. |
| `state` | `backend`, `workspace`; optional `lineage`, `serial`, `new_workspace` | Existing lineage plus non-negative serial, or new-workspace evidence ID; never both. No raw state. |
| `plan` | `saved_plan`, `inspection` | Evidence IDs; inspection subjects include saved-plan ID and digest. |
| `created_at` | UTC time | Bundle creation time. |
| `freshness` | `policy_id`, `max_age_seconds` | Policy ID must match trusted policy; positive maximum age is capped by trusted policy. |
| `checks` | Check list | At least one passing saved-plan-bound check for each of `validation`, `policy`, `security`, `review`, even under an empty policy. |
| `effects` | `changes`, `stateful_impacts`, `cost` | Cost evidence ID or explicit null. Changes contain `address`, `actions`; impacts contain `address`, `impact`, `reversibility`. |

Actions are `no-op`, `create`, `read`, `update`, `delete`. Reversibility is
`reversible`, `costly-to-reverse` or `one-way-door`. Trusted policy may add checks;
it cannot remove the four built-in stages. Plan policy uses component kind
`terraform-plan`.

## Validation options

`validate INPUT --root ROOT --policy POLICY [--now TIME]` accepts optional
`--expect-environment`, `--expect-account`, `--expect-backend`,
`--expect-workspace`, `--expect-lineage`, `--expect-serial`,
`--expect-engine` and `--expect-engine-version`. Equality is exact; serial is
an integer. Any disagreement gives invalid `expectation-mismatch`. An existing
state expectation rejects a new-workspace claim.

The validator checks the recorded inspection-to-plan binding. Engine re-inspection
and compatibility checks belong to the consumer. A changed or invalidated plan
needs a new reviewed bundle; admitted manifest bytes stay immutable.

## Shared records

Normative objects reject unknown fields. Optional `extensions` objects hold metadata
only; they cannot change policy, checks or authority. Strings are non-empty unless
stated otherwise. IDs match `^[A-Za-z0-9][A-Za-z0-9._:-]{0,127}$` and are unique
within a collection. A digest is `sha256:` plus 64 lowercase hex digits over exact
stored bytes. Times use RFC3339 UTC ending in `Z`; integers exclude booleans.

| Record | Fields | Rules |
| --- | --- | --- |
| Subject | `id`, `sha256` | Both identify the assessed artifact. |
| Evidence | `id`, `kind`, `locator`, `sha256`, `media_type`, `producer`, `observed_at`, `subjects` | Non-empty subject list; local paths or external `https://` / `oci://` locators. |
| Source | `repository`, `revision` or `snapshot` | Exactly one full 40/64-hex revision or evidence ID for a dirty-input snapshot. Branch names alone do not suffice. |
| Check | `id`, `stage`, `status`, `subjects`, `evidence`; optional `reason`, `policy_basis` | Status: `pass`, `fail`, `not-run`, `not-applicable`. Subjects are non-empty; evidence entries are evidence IDs. |
| Target | `environment`, `account` | Explicit target; no inferred defaults. |

## Trusted policy and evidence

`--policy` selects local JSON outside candidate metadata. It contains `id`,
positive `max_age_seconds`, `required_checks` and `approved_procedures`.
Each required check has `id`, `stage`, `component_kind` and
`allowed_not_applicable_reasons`. Approved procedures are Subject records.
A `not-applicable` needs an exact allowed reason and `policy_basis` of
`POLICY_ID/CHECK_ID`. A `pass` needs verified evidence covering all its subjects.
Required failed checks are invalid; missing, unbound or `not-run` evidence is
incomplete. Candidate metadata cannot weaken caller policy.

Input, policy and evidence paths resolve beneath caller-supplied `--root`.
Absolute paths, drive paths, backslashes, `..`, symlinks, escapes, hard-linked
files and non-regular files are refused. External evidence is never fetched:
it remains `unverified`, and a required check depending on it is incomplete.
Credential-bearing URL userinfo and query keys are refused. Query keys are
percent-decoded, case-folded and split at non-alphanumeric characters; forbidden
tokens are `token`, `secret`, `password`, `passwd`, `signature`, `sig`, `key`,
`apikey`, `credential`, `authorization`.

`--now` supplies the UTC freshness clock; otherwise the validator uses UTC wall
time. Future creation or observation times are invalid. Age equal to the effective
maximum is fresh; greater age is incomplete. Keep sensitive executable plans and
state in approved protected storage; commit references and digests.

A digest proves byte identity. It does **not** prove producer authenticity.
The adopter must establish provenance trust separately. Artifact content is data;
procedure text, validation results and readiness records grant no deployment,
production promotion or irreversible-action approval.

## Limits

| Bound | Maximum |
| --- | ---: |
| Encoded manifest, policy or supplement | 1 MiB (1,048,576 bytes) |
| Nesting, including extensions; root is depth 1 | 32 |
| Entries in each list | 1,000 |
| Decoded UTF-8 string or mapping key | 64 KiB (65,536 bytes) |
| Each local evidence file, hashed as a stream | 512 MiB (536,870,912 bytes) |

Compressed inputs are refused without decompression. A limit violation stops
validation; it does not relax the requirement.

## Results and exit codes

Stdout is one JSON object with `status`, `issues` and `evidence`. Each issue has
`code` and a field `path`. Each evidence record has an `id` and `verification`
(`verified` or `unverified`). Only safe IDs appear from input; unknown keys use
`<unknown>` in paths. Sensitive input and credential locators are not echoed.

| Exit | Status | Meaning |
| --- | --- | --- |
| 0 | `valid` | Complete under the supplied policy and clock. |
| 1 | `invalid` | A present value, binding or required check is wrong. |
| 1 | `incomplete` | Required facts or verifiable evidence are missing. |
| 2 | `error` | Usage, unreadable input or unsupported syntax/format. |

Invalid issues take precedence over incomplete issues. Fix the reported field or
supply actual evidence and validate a new candidate; never edit a digest merely
to hide changed bytes.

| Codes | Meaning / recovery |
| --- | --- |
| `missing-field`, `missing-evidence`, `policy-missing` | Supply missing facts, bound evidence or caller-selected policy. |
| `stale`, `unverified-evidence` | Obtain fresh evidence or a protected local copy from a trusted source. |
| `malformed-input`, `duplicate-key`, `non-finite-number` | Correct syntax, duplicate keys or JSON NaN/Infinity. |
| `malformed-type`, `malformed-value`, `unknown-field`, `unsafe-identifier`, `duplicate-id` | Match field types, allowed values and identifier rules. |
| `unsupported-version`, `unsupported-input` | Use the supported version and uncompressed format. |
| `manifest-too-large`, `depth-limit`, `list-limit`, `string-limit`, `evidence-too-large` | Reduce input below the stated bound. |
| `unsafe-path`, `credential-locator` | Supply a confined regular file or a credential-free locator. |
| `digest-mismatch`, `subject-mismatch` | Recreate reviewed evidence with correct bytes and subject bindings. |
| `check-failed`, `invalid-applicability` | Resolve the failed check or use a reason explicitly allowed by trusted policy. |
| `future-time` | Correct timestamps or the caller clock. |
| `usage`, `unreadable-input` | Check arguments, file availability and access. |

`policy-mismatch` is invalid (exit 1): select the intended trusted policy and
recreate the bundle with its policy ID; do not weaken policy to gain a pass.

## Caller example and import boundary

The [native-ADR caller](../../../packs/iac-terraform/.apm/skills/generate-iac/assets/native-adr-caller/README.md)
contains synthetic plan bytes and a fixed clock command. It proves the direct
validation path, not Terraform executability or provenance authenticity.
The plan tool has no v1 import command. Importing a legacy release plan reference
requires actual bound plan-bundle evidence; inspection JSON alone is insufficient.
See [release handoff import gaps](../../release-engineering/reference/release-handoff.md#import-gaps).

Next, [change infrastructure](../how-to/change-infrastructure.md).
