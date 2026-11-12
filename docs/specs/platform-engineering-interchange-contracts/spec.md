# Spec: Platform engineering interchange contracts

- **Status:** Approved
- **Owner:** eugenelim
- **Plan:** [`plan.md`](plan.md)
- **Constrained by:** ADR-0071, ADR-0101
- **Brief:** none
- **Discovery:** none
- **Depends on:** none
- **Contract:** `packs/iac-terraform/.apm/skills/generate-iac/references/iac-plan-bundle.v1.schema.json`, `packs/release-engineering/.apm/skills/release-loop/references/release-handoff.v2.schema.json`
- **Shape:** data
- **Risk triggers:** security-boundary, structural-interface, persistent-representation, data-transformation

> **Spec contract:** this document defines what done means. Agent Rules, Testing
> Strategy and Acceptance Criteria are the completion contract. Outcome, What
> Changes, Durable Outputs, Follow-ons and Assumptions are working material.

## Outcome

Infrastructure authors and release consumers exchange reviewed saved plans and release candidates through two validated formats without requiring a work-loop G4 event. The Terraform and image-only caller examples validate, while missing or unverified required evidence produces an incomplete result and legacy import preserves its input bytes.

## What Changes

- `generate-iac` owns the JSON `iac-plan-bundle.v1` schema, validator, fixtures and native-ADR Terraform caller example in `packs/iac-terraform`.
- `release-loop` owns the YAML `release-handoff.yaml` schema `"2.0"`, strict subset reader, validator, v1 importer, fixtures and image-only CI caller example in `packs/release-engineering`.
- Both skills carry short pointers to their interchange tools; their guides, evals, pack versions, changelog fragments and CI suite registration cover the direct caller paths.

## Interchange contracts

### Common records and evidence

Every normative object rejects unknown fields. An optional `extensions` object
on each normative object holds metadata only; none of its values select policy,
checks, applicability, commands or approval. JSON Schema 2020-12 documents live
at the Contract paths above. Each pack owns its validator independently.

In the tables, fields are required unless marked `?`. Strings are non-empty
unless explicitly stated. IDs are unique within their record collection and
match `^[A-Za-z0-9][A-Za-z0-9._:-]{0,127}$`; any other ID is invalid
`unsafe-identifier`.
Times are RFC3339 UTC strings ending in `Z`. Digests use
`sha256:` followed by 64 lowercase hexadecimal digits over exact stored bytes.
Arrays preserve order. Integers exclude booleans.

| Record | Concrete fields and types | Meaning |
| --- | --- | --- |
| Subject | `id: string`, `sha256: string` | Identity and digest of the assessed artifact; both must match the referenced artifact. |
| Evidence | `id: string`, `kind: string`, `locator: string`, `sha256: string`, `media_type: string`, `producer: string`, `observed_at: string`, `subjects: Subject[]` (non-empty) | Local relative path or external `https://` / `oci://` locator, byte identity, origin and coverage. |
| Source | `repository: string`, `revision?: string`, `snapshot?: string` | Exactly one full 40/64-hex revision or evidence ID for an explicit dirty-input snapshot; no branch-only identity. |
| Check | `id: string`, `stage: string`, `status: string`, `subjects: Subject[]` (non-empty), `evidence: string[]`, `reason?: string`, `policy_basis?: string` | Status is exactly `pass`, `fail`, `not-run`, or `not-applicable`. Evidence entries resolve to Evidence IDs. |
| Target | `environment: string`, `account: string` | Explicit adopter target identity; no default target inferred from a locator. |

Required checks come from the caller's trusted policy and component/stage
requirements, outside the candidate. A candidate cannot reduce those requirements.
A `pass` has non-empty, verified evidence covering every assessed subject.
A `not-applicable` has a non-empty reason and a policy basis allowed for that
check by the trusted policy. Failed required checks are invalid; missing,
`not-run`, stale or ambiguous required evidence is incomplete. A digest proves
byte identity; provenance authenticity remains the adopter's trust decision.

Local evidence resolves under caller-supplied `--root`. Absolute paths, drive
paths, backslashes, `..`, symlink traversal, escapes and non-regular files are
refused. External evidence is never fetched and is reported `unverified`;
required checks depending on it are incomplete. URL userinfo is refused.
Query keys are percent-decoded, case-folded, and split at non-alphanumeric
characters; a token in `token`, `secret`, `password`, `passwd`, `signature`,
`sig`, `key`, `apikey`, `credential`, `authorization` refuses the locator.
Thus `access_token`, `api-key`, `X-Amz-Signature` and `key` are refused.

Manifest and supplement input limits are 1 MiB of encoded bytes, nesting depth
32 (root container is depth 1), 1,000 entries per list and 64 KiB of UTF-8 bytes
per decoded string, including mapping keys. Local evidence has a 512 MiB
per-file limit and is hashed as a stream. These limits also cover `extensions`.

### Plan bundle

The JSON root has `schema_version: "iac-plan-bundle.v1"`. JSON duplicate keys
and non-finite numbers are refused. The bundle records a reviewed saved
executable plan, rather than just a successful planning command.

| Field group | Concrete fields and types | Required meaning |
| --- | --- | --- |
| Source and governance | `source: Source`, `request: string`, `constraints: string[]` (non-empty), `evidence: Evidence[]` | Request and constraints are evidence IDs, including the native ADR in the caller example. |
| Toolchain | `toolchain: {engine: "terraform" or "opentofu", version: string, providers: Provider[], lock: string}`; `Provider = {source: string, version: string}` | Non-empty provider selections; `lock` is the dependency-lock evidence ID. |
| Target and state | `target: Target`, `state: {backend: string, workspace: string, lineage?: string, serial?: int, new_workspace?: string}` | Either lineage plus non-negative serial, or `new_workspace` evidence ID; never both forms. No raw state payload. |
| Plan identity | `plan: {saved_plan: string, inspection: string}` | Evidence IDs; the inspection's subjects include the saved plan ID and digest, proving the recorded binding. |
| Verification | `created_at: string`, `freshness: {policy_id: string, max_age_seconds: int}`, `checks: Check[]` | Positive max age. Plan check `stage` is one of `validation`, `policy`, `security`, `review`. Each of those four stages is required for every bundle whatever the trusted policy says: at least one `pass` check per stage covers the saved plan. A stage with no such check is incomplete `missing-evidence`; a stage with a `fail` check is invalid `check-failed`. The trusted policy can require more checks, never fewer. |
| Effects | `effects: {changes: Change[], stateful_impacts: Impact[], cost: string or null}`; `Change = {address: string, actions: string[]}`; `Impact = {address: string, impact: string, reversibility: string}` | Actions use `no-op`, `create`, `read`, `update`, `delete`; reversibility uses `reversible`, `costly-to-reverse`, `one-way-door`. Cost is an evidence ID or explicit null. |

`validate` accepts optional expected environment/account, backend/workspace,
current lineage/serial and engine name/version. Equality is exact, with state
serial compared as an integer. `--now` fixes the clock for freshness checking;
otherwise UTC wall time is used. Bundle creation and evidence observation times
cannot be in the future. The adopted policy ID must match trusted policy;
the effective maximum age is the smaller of the bundle and trusted-policy
values. Evidence and bundle age at or below that limit pass freshness.
A consumer expecting existing state cannot accept a new-workspace claim.

The validator never runs Terraform. The binding record is its inspection-from-plan
proof; consumer engine re-inspection and engine-specific compatibility checks
are stronger checks outside this validator. Invalidation requires a new reviewed
bundle; admitted manifest bytes are immutable.

### Release candidate

The YAML root has the string `schema_version: "2.0"`.

| Field group | Concrete fields and types | Required meaning |
| --- | --- | --- |
| Identity | `candidate_id: string`, `created_at: string`, `producer: string`, `sources: Source[]` (non-empty), `target: Target` | Source and target are explicit for every candidate. |
| Components | `components: Component[]` (non-empty); common fields `id: string`, `kind: string`; image fields `image_ref: string`, `artifact: string`; plan field `plan_bundle: string` | `oci-image` has readable tag plus immutable `@sha256:` digest; `artifact` is an evidence ID with that digest. `terraform-plan` has a bundle evidence ID. Kind-specific fields do not mix. |
| Provenance and checks | `evidence: Evidence[]`, `provenance: string[]`, `checks: Check[]` | Provenance evidence covers each component's ID and artifact/bundle digest. Checks bind to the same subjects. |
| Changes | `changes: {baseline: string, entries: Entry[]}`; `Entry = {id: string, summary: string}` | Explicit baseline; summary strings obey the common bound; an empty entries list states no changes. |
| Phases | `phases: Phase[]` (non-empty); `Phase = {id: string, depends_on: string[], components: string[], procedures: string[]}` | Unique ordered phase IDs; dependencies name earlier phases; non-empty component and approved procedure evidence IDs. Every component appears in a phase. Procedure text is evidence, never execution authority. |
| Repair owner | `repair_owner: {id: string, route?: string}` | Responsible role/team; optional route is an opaque contact locator, not a callable command. |

The release validator checks local plan-bundle byte digests through its own
evidence checker. It reports that deep plan validation belongs to the
plan-bundle validator; it never imports the Terraform pack. A plan-validation
check required by trusted policy needs its own bound evidence. Infrastructure-only
and image-only candidates are valid without fabricated components of the other
kind. Unsupported component kinds produce a named gap and an incomplete result.

### YAML subset and command results

The release reader accepts block mappings and sequences, plain/single/double-quoted
scalars, comments and empty `[]` / `{}` only. Unquoted `true`, `false`, `null`
and canonical decimal integers (`0` or `-?[1-9][0-9]*`) resolve to their scalar
types; all other plain scalars stay strings. Quoted scalars stay strings.
Single quotes escape by doubling; double quotes use JSON string escapes.
A comment starts with `#` outside quotes at line start or after whitespace.
Mapping separators are unquoted colons followed by whitespace or end of line.

Each reader does work linear in input size: a fixed number of forward passes,
and no step rescans earlier input per line, key or scalar. Gzip, zip and other compressed input is
refused as `unsupported-input` and never decompressed.

Tags, anchors, aliases, non-empty flow collections, multi-document markers,
merge keys, indentation tabs and block scalars are unsupported. Duplicate keys
are invalid even when one spelling is quoted. Unsupported v1 syntax returns
`unsupported-input`, never a crash or partial pass.

Each skill ships one Python >=3.11 stdlib script under its `scripts/` directory:
Terraform has `validate`; release has `validate` and `import-v1`.
`validate INPUT --root ROOT --policy POLICY [--now TIME]` is the common call.
Policy is caller-selected local JSON containing `id`, `max_age_seconds`,
`required_checks` (entries with `id`, `stage`, `component_kind`,
`allowed_not_applicable_reasons`) and approved procedure evidence identities
(`approved_procedures`). It is not taken from candidate metadata.
Plan checks use `component_kind: "terraform-plan"`. `approved_procedures` is
a Subject array; each phase procedure must match an approved identity and digest.
A check's `policy_basis` is `POLICY_ID/CHECK_ID`; applicability requires that
policy identity and an exact reason in that check's allowed reason list.
Release creation and evidence times use the same trusted freshness clock and
maximum age as plan verification.

When a result has both invalid and incomplete issues, its status is `invalid`.
Stdout contains one JSON result with `status` (`valid`, `incomplete`, `invalid`,
`error`), `issues` (objects with `code` and field `path`), and `evidence`
(objects with `id` and `verification`: `verified` or `unverified`).
The only input-derived text a result carries is an ID that passed the identifier
rule. Issue `path` values use schema field names, list indices and those IDs;
an unknown or unsafe key appears as `<unknown>`. Exit 0 means
valid/complete; 1 means invalid or incomplete; 2 means usage, unreadable input
or unsupported input. No input content or credential locator is echoed to
stdout, stderr, logs or skill output surfaced to the agent. Both streams are
configured for UTF-8 before output. Missing trusted policy yields incomplete `policy-missing`; unreadable policy
yields exit 2 `unreadable-input`. A readable but malformed policy is invalid.
Malformed syntax yields `malformed-input`; JSON NaN/Infinity yields
`non-finite-number`. Other invalid issues use exit 1; incomplete issues use
exit 1. Future timestamps yield invalid `future-time`. Missing required fields
yield incomplete `missing-field`; incorrect present values remain invalid. No result authorizes deployment or production promotion.

### Read-only v1 import

`import-v1 INPUT --output OUTPUT --root ROOT --policy POLICY [--supplement JSON]`
accepts only v1 `schema_version: "1.0"`. It writes a new v2 candidate, never the
input. An output equal to or resolving to the input is refused before writing;
existing output files are not overwritten. The candidate is written to a
temporary file in the output's confined directory and published with a
no-overwrite link or rename; a write or publish failure removes the temporary
file, leaves no candidate at the output path, and reports `error`. The supplement uses v2 field names
for missing target, source, plan binding, provenance, applicability, phase and
repair-owner facts; conflicting known facts are refused. It cannot override a
failed check or a component digest. Input, supplement and policy use the same
bounded/confined reads as validation.

V1 names and `image_ref` values map to image components; changelog baseline and
entries map to changes; build time and producer map to identity. A v1 plan
reference needs a supplement containing a bound plan bundle, rather than
relabeling inspection JSON as an executable plan. Unbound v1 `pass` results
become `not-run` with a named evidence gap. A full supplement supplies actual
component-bound evidence; a claim alone never upgrades a check.

Missing facts are absent from the candidate and listed as field-addressed gaps
in the JSON result. Such a candidate is incomplete, not schema-complete; its
missing required fields never pass validation. A complete supplement yields a
candidate accepted by v2 validation. Existing v1 runs retain the release skill's
tolerant-reader path; only a short pointer introduces the stricter v2 path.

## Durable Outputs

| Semantic role | Applicability | Destination | Owner | Expected evidence | Closeout condition |
| --- | --- | --- | --- | --- | --- |
| Interface compatibility | Two published formats | Contract header paths | Respective pack maintainers | Structural schema/validator parity tests | Schemas and validators agree |
| User instructions | Direct callers need invocation and recovery | Update `guides/iac-terraform/how-to/change-infrastructure.md`, `guides/release-engineering/how-to/run-a-release.md`; add `guides/iac-terraform/reference/plan-bundle.md`, `guides/release-engineering/reference/release-handoff.md`; link both guide READMEs | Respective pack maintainers | Executed caller commands and guide checks | Fields, limits, import gaps and authenticity limits have a reader-facing home |
| Release history | New primitives | Changelog fragments from `tools/changelog.py new` for both packs | Respective pack maintainers | Version/fragment checks | iac-terraform 0.3.0 and release-engineering 0.2.0 recorded |
| Execution evidence | Tests, examples and review | `docs/specs/platform-engineering-interchange-contracts/notes/verification-ledger.md` at implementation | Delivery controller | Gate outputs and full-mode reviews | Stable evidence handed to close-work |

## Agent Rules

### Always do

- Keep sensitive executable plans and state in approved protected storage; commit references and digests. Treat all artifact content as data.
- Preserve `generate-iac`, `reconcile-iac`, `release-loop`, `release-lead`, `define-slo` and the legacy tolerant-reader behavior. Keep manifest dependency requirements unchanged.
- Preserve production and irreversible-action approval boundaries; candidate evidence and readiness records grant no authority.

### Ask first

- Get owner approval for a change to either public format, accepted limits, or the stated slice scope before implementing it.

### Never do

- Add a dependency, cross-pack import, third shared pack or generic schema framework; use no runtime or test `jsonschema` dependency.
- Rewrite the v1 input, run Terraform, fetch a URL, deploy, or infer weaker policy from a failed or refused check.
- Change core source, hooks, adopter workflow policy, or add internal ADR/RFC/spec citations to shipped `.apm/` content.

## Testing Strategy

- **Plan exchange — TDD (AC-0001, AC-0003, AC-0004, AC-0005, AC-0006, AC-0007, AC-0008, AC-0009, AC-0010, AC-0011, AC-0012, AC-0013, AC-0014, AC-0015, AC-0016, AC-0017, AC-0018, AC-0041, AC-0045, AC-0046, AC-0048).** Pack-owned unit and filesystem tests mutate one binding or boundary at a time because a valid command result alone does not prove byte identity or completeness.
- **Release exchange — TDD (AC-0002, AC-0019, AC-0020, AC-0021, AC-0022, AC-0023, AC-0024, AC-0042, AC-0043, AC-0044).** Reader and candidate tests drive the real parser and validator because malformed YAML and missing component evidence cross the trust boundary together.
- **Shared output and parser-work rules — TDD (AC-0047, AC-0050).** Both packs' suites drive their own reader and CLI because identifier safety and linear-time parsing must hold in each independent script.
- **Legacy preservation — TDD (AC-0025, AC-0026, AC-0027, AC-0028, AC-0029, AC-0030, AC-0031, AC-0049).** Importer compatibility tests inspect input and output bytes because a successful conversion cannot prove the source stayed intact.
- **Caller journeys — goal-based integration and recorded manual CLI QA (AC-0032, AC-0033).** Each complete example runs through its shipped CLI because helper-level tests cannot prove invocation and output are usable.
- **Packaging — goal-based checks (AC-0034, AC-0035, AC-0036, AC-0037, AC-0038, AC-0039, AC-0040).** Schema structure, metadata, eval coverage, docs and projection gates are directly inspectable without inventing runtime behavior.

## Acceptance Criteria

- [ ] **AC-0001.** A complete local plan bundle conforming to the field tables returns `valid`.
- [ ] **AC-0002.** Complete image-only and infrastructure-only release candidates conforming to the field tables return `valid`.
- [ ] **AC-0003.** Each validator returns `invalid` with `malformed-type` for a wrong normative field type, including a boolean in an integer field.
- [ ] **AC-0004.** Each input reader refuses duplicate mapping keys with `duplicate-key`.
- [ ] **AC-0005.** Each validator refuses an unknown schema version with `unsupported-version` and exit 2.
- [ ] **AC-0006.** Each validator returns `unknown-field` for an unrecognized normative field; the same key inside bounded `extensions` is accepted as inert metadata.
- [ ] **AC-0007.** A manifest or supplement whose encoded size first reaches 1,048,577 bytes returns `manifest-too-large`; a bounded read of at most 1,048,577 bytes enforces the limit before parsing.
- [ ] **AC-0008.** A nested input below the byte limit whose root-relative container depth first reaches 33 returns `depth-limit`; depth accounting during parsing precedes normative field validation.
- [ ] **AC-0009.** A list below byte/depth limits whose item count first reaches 1,001 returns `list-limit`; per-list counting precedes normative field validation.
- [ ] **AC-0010.** A decoded string below manifest/depth/list limits whose UTF-8 size first reaches 65,537 bytes returns `string-limit`; scalar-size checking precedes normative field validation.
- [ ] **AC-0011.** Local evidence whose streamed byte count first reaches 536,870,913 returns `evidence-too-large`; streaming stops at that byte before digest comparison, so the manifest-size limit does not mask this separate-file limit.
- [ ] **AC-0012.** Each validator refuses local evidence traversal, absolute/drive paths, backslashes, symlink paths, escapes and non-regular files with `unsafe-path`.
- [ ] **AC-0013.** Each validator refuses credential-bearing locators under the common rule with `credential-locator`.
- [ ] **AC-0014.** Required external evidence is `unverified` with `unverified-evidence` and an incomplete result; a network-call sentinel observes zero fetches.
- [ ] **AC-0015.** Given `--now` and trusted freshness policy, evidence or bundle age above the effective maximum returns incomplete with `stale`; age exactly at the maximum remains fresh.
- [ ] **AC-0016.** A check or inspection binding to the wrong subject ID or digest returns `subject-mismatch`.
- [ ] **AC-0017.** Tampered saved-plan, inspection-output or referenced local plan-bundle bytes return `digest-mismatch`.
- [ ] **AC-0018.** A plan bundle that disagrees with a supplied target, backend/workspace, state lineage/serial or engine expectation returns `expectation-mismatch`.
- [ ] **AC-0019.** The YAML reader refuses each excluded syntax class with `unsupported-input` and exit 2, including tags, anchors and aliases.
- [ ] **AC-0020.** A required `not-applicable` check without a reason allowed by its trusted policy basis returns `invalid-applicability`.
- [ ] **AC-0021.** A release candidate with empty `components` returns `empty-components`.
- [ ] **AC-0022.** An unsupported component kind returns incomplete with `unsupported-component-kind`.
- [ ] **AC-0023.** An image without a tag or without an immutable digest returns `invalid-image-reference`.
- [ ] **AC-0024.** Candidate or extension metadata that claims weaker check requirements cannot suppress a check required by trusted policy.
- [ ] **AC-0025.** A valid synthetic v1 handoff imported without its missing facts returns incomplete with named field gaps; each unbound v1 `pass` is `not-run` with `missing-evidence`.
- [ ] **AC-0026.** A valid v1 handoff plus a complete, consistent supplement produces a v2 candidate whose validation returns `valid`.
- [ ] **AC-0027.** Every import outcome preserves the input's exact bytes.
- [ ] **AC-0028.** An import output equal to or resolving to the input returns `output-is-input` before any write.
- [ ] **AC-0029.** Import refuses any v1 version other than `"1.0"` with `unsupported-version` and exit 2.
- [ ] **AC-0030.** A v1 handoff using unsupported YAML syntax returns `unsupported-input` and exit 2 without producing a candidate.
- [ ] **AC-0031.** Legacy compatibility fixtures retain the documented tolerant-reader outcomes for unknown fields and warning-only unknown versions on the existing skill path.
- [ ] **AC-0032.** The native-ADR Terraform caller example validates through the shipped plan-bundle CLI with exit 0 and JSON `status: "valid"`.
- [ ] **AC-0033.** The application-CI image-only caller example validates through the shipped release CLI with exit 0 and JSON `status: "valid"`.
- [ ] **AC-0034.** Each schema's required fields, enums, normative-object `additionalProperties: false` and version const match its validator's accepted structure in structural parity tests without evaluating JSON Schema.
- [ ] **AC-0035.** Both `pack.toml` and `.claude-plugin/plugin.json` report 0.3.0 for iac-terraform and 0.2.0 for release-engineering.
- [ ] **AC-0036.** Each pack has a valid changelog fragment created through `tools/changelog.py new` for its interchange primitives.
- [ ] **AC-0037.** Each affected skill's eval harness covers its direct caller and refusal/incomplete outcomes in addition to its existing output-quality cases.
- [ ] **AC-0038.** The guide validation/link checks pass for all pages named in Durable Outputs.
- [ ] **AC-0039.** CI parity and pack-test-boundary lints pass with both new suites explicitly registered in build-check and the local test roster.
- [ ] **AC-0040.** `make precheck` passes after `make build-self` rebuilds projections from the pack sources.

- [ ] **AC-0041.** Each validator reports incomplete `missing-field` for an absent required field from its normative field tables.
- [ ] **AC-0042.** A failed required check returns invalid `check-failed`.
- [ ] **AC-0043.** A missing, unbound or `not-run` required check returns incomplete `missing-evidence`.
- [ ] **AC-0044.** Validation without trusted policy returns incomplete `policy-missing`.
- [ ] **AC-0045.** No rejected input content or credential-bearing locator appears on stdout, stderr, logs or surfaced skill output.
- [ ] **AC-0046.** JSON NaN/Infinity input returns invalid `non-finite-number`.
- [ ] **AC-0047.** An ID outside the identifier rule returns invalid `unsafe-identifier`, and neither that ID nor an unknown field name containing sensitive text appears in any output stream.
- [ ] **AC-0048.** A plan bundle lacking a `pass` check bound to the saved plan for any one of the stages `validation`, `policy`, `security` or `review` and no `fail` check for that stage returns incomplete `missing-evidence`, even under a trusted policy that requires no checks; a `fail` check for a mandatory stage returns invalid `check-failed`, because invalid outcomes take precedence over incomplete ones.
- [ ] **AC-0049.** An import whose write or publish step fails, or whose output path appears between the existence check and publication, leaves the pre-existing destination unchanged, leaves no partial candidate, and reports `error`.
- [ ] **AC-0050.** For each reader, a 1 MiB adversarial input built from long lines, dense escapes, many keys or many comments finishes in under 2 seconds in the pack test suite, and compressed input returns `unsupported-input`.

## Follow-ons

Sections 2–5 are outside this contract: evidence collection, focused reviewers,
workflow integration and final pack consolidation/dependency removal. This slice
adds no standalone-governance rewrite, new execution engine, production promotion,
post-production operations, incident response or autonomous remediation.

## Assumptions

- Technical: no recorded corpus of real v1 handoffs is available. Import and compatibility fixtures are synthetic; their passing results do not establish coverage of adopter-specific YAML or extensions.

## Terminal Intent

`code` — both interchange schemas, validators, fixtures, caller examples and the v1 importer are in place, documented, versioned and projected.

## Accepted Risk

none
