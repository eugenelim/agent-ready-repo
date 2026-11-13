---
title: Release handoff
summary: Candidate fields, v1 import gaps, limits, and validation result codes for release exchange.
pack: release-engineering
kind: reference
---

# Release handoff

Validate an image-only, plan-only or mixed release candidate with Python 3.11 or
newer. From the installed `release-loop` skill directory, run:

```sh
python3 scripts/release_handoff.py validate release-handoff.yaml --root /protected/release --policy trusted-policy.json
```

Replace `/protected/release` with your approved evidence directory. Input and
policy names resolve beneath it. Validation reads files and prints JSON without
deploying or fetching evidence. Direct callers need no G4 event. Existing v1
runs keep the skill's tolerant-reader path: unknown fields are ignored and an
unknown version warns. The strict v2 validator and importer use separate rules.

## Candidate fields

The [schema](../../../packs/release-engineering/.apm/skills/release-loop/references/release-handoff.v2.schema.json)
is owned by `release-loop`. All fields below are required except those marked optional.

| Field | Type / fields | Meaning |
| --- | --- | --- |
| `schema_version` | String `"2.0"` | Exact version; quote it in YAML. |
| `candidate_id`, `created_at`, `producer` | ID, UTC time, string | Explicit candidate identity and producer. |
| `sources`, `target` | Non-empty Source list; Target | Immutable inputs and explicit environment/account. |
| `components` | Non-empty component list | Each has unique `id` and `kind`; see kinds below. |
| `evidence`, `provenance`, `checks` | Evidence list, evidence ID list, Check list | Provenance and checks bind to every component ID and artifact/bundle digest. |
| `changes` | `baseline`, `entries` | Explicit baseline; entries contain `id`, `summary`; empty entries means no changes. |
| `phases` | Non-empty list of `id`, `depends_on`, `components`, `procedures` | Unique ordered phases; dependencies name earlier phases; non-empty component and approved procedure ID lists; every component appears. |
| `repair_owner` | `id`; optional `route` | Responsible team/role; route is opaque contact data, never a command. |

An `oci-image` component has `image_ref` (readable tag plus immutable
`@sha256:` digest) and `artifact` (evidence ID with that digest).
A `terraform-plan` component has `plan_bundle` (evidence ID).
Kind-specific fields cannot mix. Unsupported kinds are incomplete
`unsupported-component-kind`; an empty list is invalid `empty-components`.
Missing image tags or digests give invalid `invalid-image-reference`.

Local plan-bundle bytes are hashed here. Deep validation belongs to the
[plan-bundle validator](../../iac-terraform/reference/plan-bundle.md), which this
tool never imports. Policy-required plan-validation checks need their own bound
evidence. Neither image-only nor plan-only candidates need an invented component.

## Commands and YAML syntax

`validate INPUT --root ROOT --policy POLICY [--now TIME]` reads without writing.
`import-v1 INPUT --output OUTPUT --root ROOT --policy POLICY [--supplement JSON]
[--now TIME]` writes a new candidate. All names resolve beneath `--root`.
`--now` defaults to UTC wall time. Release and evidence freshness use trusted
policy's maximum age.

The YAML reader accepts block mappings and sequences, plain/single/double-quoted
scalars, comments, and empty `[]` / `{}`. Unquoted `true`, `false`, `null` and
canonical decimal integers (`0` or `-?[1-9][0-9]*`) become typed values; other
plain scalars and all quoted scalars stay strings. Single quotes escape by
doubling; double quotes use JSON escapes. Comments start with `#` outside quotes
at line start or after whitespace. A mapping separator is an unquoted colon
followed by whitespace or end of line.

Tags, anchors, aliases, non-empty flow collections, multi-document markers, merge
keys, indentation tabs and block scalars are unsupported. Duplicate keys are
invalid, including quoted duplicates.

## Import gaps

Import accepts only string version `"1.0"`. It preserves the exact source bytes.
V1 names and image references map to image components; baseline and changelog
entries map to changes; build time and producer map to identity.

A JSON supplement uses v2 fields to supply actual missing target, source, plan
binding, provenance, applicability, phases and repair-owner facts. A plan reference
needs a bound saved-plan bundle, not relabeled inspection JSON. An unbound v1
`pass` becomes `not-run` plus `missing-evidence`. A claim cannot upgrade it.
Conflicting facts, component digests and failed checks cannot be overridden.

Missing facts stay absent and appear as field-addressed gaps. Such output is an
incomplete candidate, not schema-complete. A complete consistent supplement must
pass v2 validation. The synthetic fixtures do not establish compatibility with
adopter-specific YAML or extensions.

Output must be a distinct non-existing path under the root. Import writes a
temporary file in that directory and publishes without overwriting. Failure
removes the temporary file and preserves any pre-existing destination.

| Import code | Result / recovery |
| --- | --- |
| `output-is-input` | Invalid, exit 1; choose a distinct output, including resolved aliases. |
| `output-exists` | Invalid, exit 1; choose a fresh output; never overwrite. |
| `supplement-conflict` | Invalid, exit 1; resolve conflicting evidence with its owner. |
| `output-failed` | Error, exit 2; check protected output storage and retry with a fresh path. |
| `unsupported-version` | Error, exit 2 for import; only v1 `"1.0"` is accepted. |
| `unsupported-input` | Error, exit 2; use the supported subset; no candidate is published. |

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

Integer literals of at most 4,300 digits stay integers; longer literals retain their
exact decimal text marked as over-long integers, accepted as inert `extensions`
metadata and refused as `malformed-type` in normative integer fields.

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

`invalid-phase-order` is invalid (exit 1): place each dependency before the
phase that needs it. `unapproved-procedure` is invalid (exit 1): obtain procedure
evidence whose ID and digest are approved by the trusted policy.

## Caller example

The [image-only CI caller](../../../packs/release-engineering/.apm/skills/release-loop/assets/image-only-ci-caller/README.md)
provides synthetic local evidence, explicit caller policy and a fixed clock.
It builds or pushes no image and proves no producer identity.

Next, [release a change](../how-to/run-a-release.md).
