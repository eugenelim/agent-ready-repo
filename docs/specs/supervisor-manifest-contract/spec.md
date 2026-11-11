# Spec: Supervisor manifest contract

- **Status:** Draft
- **Owner:** eugenelim
- **Plan:** [`plan.md`](plan.md)
- **Constrained by:** ADR-0162, ADR-0163, RFC-0115
- **Brief:** brief:everyday-supervisors-delivery
- **Discovery:** none
- **Depends on:** none
- **Contract:** packs/core/.apm/skills/new-spec/assets/supervisor-manifest.v1.schema.json, packs/core/.apm/skills/new-spec/assets/supervisor-request-envelope.v1.schema.json
- **Shape:** data
- **Risk triggers:** security-boundary, structural-interface

> **Spec contract:** this document defines what "done" means. The implementing
> PR must match this spec, or update it. Verification must be derivable from it.
>
> **Not every section is contract.** `Agent Rules`, `Testing Strategy` and
> `Acceptance Criteria` are what a completion gate reads, and an amendment
> changes them. `Outcome`, `What Changes`, `Durable Outputs`, `Follow-ons` and
> `Assumptions` are working material: they orient a reader and an author corrects them in place
> as the work teaches, without an amendment and without a review round. A review
> finding against working material is advisory — it cannot block, because nothing
> gates the text it cites.

## Outcome

A supervisor author and a controller read one published description of a supervisor: the commands it answers, the request kinds it emits and how each is worked, the files it pins, and the commands it may ask a controller to run in another supervisor. A manifest that conforms to the schema validates, and one that names an unknown version, an unlisted command, a worker mode a reserved kind may not use or a path outside the portable relative form fails validation.

## What Changes

- `supervisor-manifest.v1`, a JSON Schema for the TOML manifest a supervisor ships — `packs/core/.apm/skills/new-spec/assets/`, with a copy at `contracts/ferryman/supervisor-manifest.v1.schema.json` that adds an `x-spec` back-pointer
- `supervisor-request-envelope.v1`, the five keys every supervisor request carries, which each supervisor extends with its own `kind` and `stage` values — the same two locations
- A core-pack test that validates example manifests and envelopes against the pack originals and checks they cite no internal record, and a roster test that checks the copies — `packs/core/tests/skills/new-spec/` and `tests/roster/`
- Registration of both contracts and the pages that name them — a `contracts/README.md` row that marks the `contracts/ferryman/` files as copies of the pack originals, and pages 01, 02 and 05 of `docs/architecture/unattended-delivery-runner/`
- A core pack release for the new assets — `packs/core/pack.toml`, `packs/core/.claude-plugin/plugin.json`, a changelog fragment and the self-host projections

## Durable Outputs

| Semantic role | Applicability | Destination | Owner | Expected evidence | Closeout condition |
| --- | --- | --- | --- | --- | --- |
| Interface compatibility | The two schemas are a published interface every supervisor and controller reads | the core pack assets, `contracts/ferryman/`, the README row | repository owner | the pack test and the roster test run named in the plan | both copies present, equal apart from `x-spec`, and the runs green |
| Current architecture | Page 05 line 271 says the core pack owns the schema and a copy sits in `contracts/ferryman/`; page 01 counts twelve contracts and lists no envelope file; page 02 places the manifest beside the script | pages 01, 02 and 05 of the unattended-delivery architecture | repository owner | each page names `supervisor-request-envelope.v1`, the shipped paths and the manifest location | no page names a different path, count or location |
| Release history | A pack file changes | `packs/core/pack.toml`, `packs/core/.claude-plugin/plugin.json` and `docs/product/changelog.d/` | repository owner | the changelog validates and the core release check passes | the core version is one patch above `main` at merge |
| Decision rationale | ADR-0162 records the contract and ADR-0163 the spec supervisor's placement | `docs/adr/` | repository owner | both ADRs Accepted | none further |
| Maintainer procedure | A supervisor author needs a worked manifest; the first ones ship with `spec-supervisor` and `discovery-supervisor` | the E1 and E2 specs | repository owner | each supervisor's own manifest test | none here |
| User promise, operations, reusable learning | not applicable: no user-facing behavior or deployment change | none | none | none | none |

## Agent Rules

### Always do

- Validate every example manifest and envelope in tests against the schema it claims to satisfy.
- Keep the published manifest schema closed: a new manifest field is a new `manifest_version`. The envelope stays open to extra keys and frozen at `schema_version` 1.
- Cite ADR-0162 D1, D2, D3 and D7 in this spec, the plan and the `contracts/ferryman/` copy's `x-spec`, and nowhere in the pack originals.
- Edit the pack original and refresh the `contracts/ferryman/` copy from it, so the two stay equal apart from `x-spec`.

### Ask first

- Proposing a new schema version for either contract.
- Moving the canonical schema files out of the core pack.

### Never do

- Edit `work-supervisor.py` or any file in its pin set (ADR-0144).
- Add a new top-level dependency or a runtime import: the schemas are data and the tests use the validator the repository already uses.
- Ship a manifest for `work-supervisor`: its descriptor is held by the controller (page 02 of the architecture).
- Put a command line, interpreter or argv element in the manifest: a controller builds argv only from its own descriptors (RFC-0115 D3). `pinned_files` entries are data, never argv.
- Add a command beyond the six without an ADR-0162 amendment first.
- Put an internal citation in a schema under `packs/`: shipped pack content carries none (`packs/AGENTS.md`).

## Testing Strategy

- **Manifest rules (AC-0001, AC-0002, AC-0003, AC-0004, AC-0005, AC-0006, AC-0007, AC-0008, AC-0009, AC-0010, AC-0011, AC-0012, AC-0013, AC-0014, AC-0015, AC-0016, AC-0017, AC-0018, AC-0019, AC-0020):** TDD, because each rule is a compressible invariant a schema validator decides. The pack test runs one valid manifest and one invalid variant per rule.
- **Envelope rules (AC-0021, AC-0022, AC-0023, AC-0024, AC-0025):** TDD, for the same reason, over one valid envelope and one variant per rule.
- **Copies and citations (AC-0026, AC-0027, AC-0028):** goal-based, a roster test that compares the copies and a pack test that scans the pack originals for internal references.

## Acceptance Criteria

- [ ] **AC-0001.** A representative manifest, with every field present and in range, validates against `supervisor-manifest.v1`.
- [ ] **AC-0002.** A manifest carrying only the required keys validates.
- [ ] **AC-0003.** A manifest whose `delegates_to` lists `park`, and one that lists `start`, each validate when a `delegate-verb` request kind is listed.
- [ ] **AC-0004.** A request kind that lists several modes validates.
- [ ] **AC-0005.** A manifest whose `manifest_version` is not the integer 1, including 0, 2 and 1.5, fails validation.
- [ ] **AC-0006.** A manifest missing any one of `manifest_version`, `id`, `subject_kind`, `commands`, `request_kinds` and `pinned_files` fails validation.
- [ ] **AC-0007.** A manifest whose `commands` are not exactly `start`, `next`, `report`, `status`, `park` and `gates`, each listed once in any order, fails validation, whether a command is missing, repeated or extra.
- [ ] **AC-0008.** A request kind whose `modes` is empty, repeats a mode, or names a mode outside `headless`, `attach`, `session`, `supervisor-run`, `ferryman-run` and `human`, fails validation.
- [ ] **AC-0009.** A manifest fails validation unless `consent` and `human-decision`, where listed, have `human` as their only mode, `delegate-verb`, where listed, has `ferryman-run` as its only mode, and no other request kind lists `human` or `ferryman-run`.
- [ ] **AC-0010.** A `delegates_to` entry whose `command` is not `park` or `start`, or that has no `supervisor`, fails validation.
- [ ] **AC-0011.** A manifest fails validation when it lists `delegates_to` without a `delegate-verb` request kind, or a `delegate-verb` request kind without `delegates_to`.
- [ ] **AC-0012.** A manifest whose `delegates_to` is an empty list fails validation.
- [ ] **AC-0013.** A manifest whose `delegates_to` repeats an entry fails validation.
- [ ] **AC-0014.** A manifest fails validation when it holds a key outside these sets: at the top level `manifest_version`, `id`, `subject_kind`, `commands`, `request_kinds`, `pinned_files`, `delegates_to` and `max_width`; in a request kind `modes`; in a delegation `supervisor` and `command`.
- [ ] **AC-0015.** A manifest whose `max_width` is below 1 or is not an integer fails validation.
- [ ] **AC-0016.** A manifest whose `pinned_files` holds an entry outside the portable relative form fails validation. The form is non-empty `/`-separated segments of ASCII letters, digits, `_`, `.` and `-`, no segment starting with `.`, and no trailing newline.
- [ ] **AC-0017.** A manifest whose `pinned_files` is empty or repeats an entry fails validation.
- [ ] **AC-0018.** A manifest fails validation when `id`, `subject_kind`, a request-kind name or a delegation `supervisor` is not a lowercase identifier, which is ASCII `a` to `z`, digits and hyphens, starts with a letter, and has no trailing newline.
- [ ] **AC-0019.** A manifest whose `id` is `work-supervisor`, with or without a trailing newline, fails validation.
- [ ] **AC-0020.** A manifest whose `request_kinds` table is empty fails validation.
- [ ] **AC-0021.** An envelope with `schema_version` 1, a non-empty `request_id` of at most 512 characters, a non-empty `run_id` of at most 128 characters, a non-empty `kind` and a non-empty `stage` validates against `supervisor-request-envelope.v1`, with any extra keys.
- [ ] **AC-0022.** An envelope missing any one of those five keys fails validation.
- [ ] **AC-0023.** An envelope whose `schema_version` is not the integer 1, including 2 and 1.5, fails validation.
- [ ] **AC-0024.** An envelope whose `request_id` or `run_id` is not a string, is empty, or exceeds its bound fails validation.
- [ ] **AC-0025.** An envelope whose `kind` or `stage` is the empty string fails validation.
- [ ] **AC-0026.** Each of the two supervisor schemas in `packs/core/.apm/skills/new-spec/assets/` equals its copy in `contracts/ferryman/` apart from the `x-spec` entry, which only the `contracts/ferryman/` copy carries.
- [ ] **AC-0027.** Every supervisor schema in `packs/core/.apm/skills/new-spec/assets/` has a copy in `contracts/ferryman/`, and no `contracts/ferryman/` file named `supervisor-*` lacks its pack original.
- [ ] **AC-0028.** The two pack schemas contain no ADR, RFC, spec or `docs/` reference.

## Follow-ons

- repository owner: the `spec-supervisor` and `discovery-supervisor` specs of brief `everyday-supervisors-delivery` — each ships a manifest at its skill root that conforms to these schemas, so its `pinned_files` resolve from the manifest's directory without a parent segment, and a test that its listed request kinds equal the kinds it emits.
- repository owner: the controller's load-time controls, in phase P0 of brief `ferryman-local-delivery` — refusing a manifest at load (ADR-0162 D2), the release-time hash comparison of the supervisor and manifest files (RFC-0115 D3, `docs/adr/0171-installed-supervisors-checked-against-release-record-before-running.md`), always pinning the manifest and the script whatever `pinned_files` lists, resolve-time confinement of `pinned_files` with a link-refusing helper, binding a manifest's `id` to the directory it loaded from, refusing a delegation that names the manifest's own `id`, enforcing `delegates_to` per request with the target supervisor's own admission check deciding a `start`, dispatching a gate kind as human-only from the kind name and never from manifest text, refusing a TOML float such as `1.0` where the schema asks for an integer, choosing which of a kind's listed modes a request uses (the envelope carries no mode key), and bounding `max_width` by the controller's configured width.
- repository owner: the controller's stdlib schema checker must refuse a schema keyword it does not support, and a differential test runs the invalid-variant fixtures of this spec's pack test through it and the full validator (page 01 section 8) — phase P0 of brief `ferryman-local-delivery`.
- repository owner: the `approval-fields.v1` lists — page 10b and page 13 place them in phase E0 and the brief scopes E0 to the manifest and envelope, so the lists ship with the record 11a work (`docs/adr/0172-approval-invariant-levels-and-attribution-record.md`) unless the brief is widened.

## Assumptions

- Defaulted: Technical: the canonical schemas ship in the core pack's `new-spec` assets, as page 05 line 271 and ADR-0162 D7 say, with copies in `contracts/ferryman/` that add `x-spec` — default: that placement; if wrong: the copies move and the drift test changes (settled by: repository owner, who chose it).
- Defaulted: Technical: JSON Schema draft 2020-12, as the sibling delivery schemas use — default: 2020-12; if wrong: the `$schema` line and validator class change (settled by: repository owner).
- Defaulted: Technical: `commands` lists the six controller-driven contract commands only; human-run verbs such as `answer` (page 05) are outside the manifest — default: six only; if wrong: a new `manifest_version` adds them (settled by: repository owner).
- Defaulted: Technical: a manifest sits at its skill root, not beside the script in `scripts/` as page 02 line 225 says, so its `pinned_files` reach a policy file at the root without a parent segment; the same change corrects page 02 — default: skill root; if wrong: a spec changes the location and the page edit reverts (settled by: repository owner).
- Defaulted: Technical: `consent` and `human-decision` are the human-only kinds named in the sources (page 05 lines 105, 173 and 211; page 03 line 78), and `session` is an agent-worked mode — default: those two; if wrong: the human-only set grows in a new `manifest_version` (settled by: repository owner).
- Defaulted: Technical: no `contracts/catalogue-spec.toml` entry, because the contract parity check covers only top-level `contracts/*.json` and `*.toml` and `contracts/delivery/` has none — default: no entry; if wrong: `make precheck` says so (settled by: repository owner).
- Defaulted: Process: the new assets are inert data with no skill behavior change, so `new-spec/evals/` is unchanged — default: no eval update; if wrong: the eval harness gains a case (settled by: repository owner).
- Defaulted: Process: the pack test and the roster test are not in a pull-request check, so closeout evidence is a targeted run of both, `make precheck PRECHECK_ARGS="--with-tests --base origin/main"`, and one `test-corpus.yml` dispatch — default: that evidence; if wrong: the suites are registered in a PR workflow (settled by: repository owner).
