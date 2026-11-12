# Plan: Platform engineering interchange contracts

- **Spec:** [`spec.md`](spec.md)
- **Status:** Drafting
- **Repository anchors:** `packs/iac-terraform/.apm/skills/generate-iac/SKILL.md` saved-plan output; its `references/release-loop-integration.md`; `packs/release-engineering/.apm/skills/release-loop/SKILL.md` G4 v1 handoff; `guides/_shared/reference/catalogue-authoring-standards.md` pack loader recipe. New standalone parsers have no existing implementation seam in these skills; their internal callable layout is implementation-discovered.

> **Plan contract:** Tests, Touches and Done when are completion fields.
> Design, Approach, Grounding and Risks are working material. Execution evidence
> belongs in `notes/verification-ledger.md`, not in this plan. Both human approval
> gates remain pending; this draft dispatches no implementation.

## Approach

Full-mode delivery uses two independent pack-owned validators to establish the formats before caller examples
or import depend on them. The YAML reader is the deepest review unit; its grammar
and resource accounting receive TDD coverage before the v1 importer uses it.
Six task units separate parser work, caller proof and release wiring. Each unit
has independent evidence; split a DEEP unit further if reviewable behavior/test
volume approaches 2,000 lines and the proof does not fit one review.

## Constraints

- [ADR-0071](../../adr/0071-pack-runtime-export-boundary-and-test-placement.md) governs runtime exports, test placement and skill-local evals.
- [ADR-0101](../../adr/0101-pack-test-isolation-by-default-with-declared-compatibility-classes.md) governs isolated pytest processes. These suites use isolation, not a new compatibility class.
- Contract destinations are the pack-owned references named in the spec, rather than a third catalogue-level schema owner. No generic runtime schema evaluator is added.
- Only the six tasks below belong to the implementation envelope. Core, hooks, dependency requirements and standalone governance remain outside it.

## Construction tests

**Integration tests:** Each pack suite imports its real shipped script under a
pack-and-skill-qualified module name using `spec_from_file_location`, registers
that name in `sys.modules`, then calls `exec_module`. Never add `scripts/` to
`sys.path`. Each suite inspects only its own pack and temporary fixtures.
A small subprocess smoke layer checks argv, UTF-8, JSON stdout and exit codes;
most assertions call the implementation directly to avoid interpreter overhead.

**Manual verification:** Run each documented caller command against the built
projection with locally protected fixture evidence; record exact invocation,
exit code and JSON result in the verification ledger. No Terraform invocation,
network fetch, deployment or real infrastructure is involved. Synthetic plan
bytes prove validator behavior, not Terraform executability.

## Durable-output map

| Durable output | Tasks | Implementation evidence | Closeout evidence |
| --- | --- | --- | --- |
| Pack-owned schemas and validators | T1, T3, T5 | Pack suite results, parity assertions, importer byte snapshots | Contract files and current evidence resolve |
| Direct caller instructions and reference guides | T2, T4, T6 | Both CLI transcripts, guide/link checks | Guide destinations from spec are current |
| Release history | T6 | Matching manifest/plugin versions and generated fragments | Both pack release histories name the primitives |
| Execution evidence | T1–T6 | `notes/verification-ledger.md` with commands, results and review reports | Controller hands stable evidence to close-work |

## Design (LLD)

### Data & schema

Owned by: T1, T3, T5

Traces to AC-0001 through AC-0031 and AC-0034; implements both Contract header
schemas. Each pack keeps its evidence checker in its single standalone script.
A small duplicate is accepted because installed packs do not import one another.
Schema files express the public field tables, not repository workflow metadata.
Validator internals use typed stdlib records; the exact callable seam is
implementation-discovered by extracting the smallest importable parse/validate
boundary that tests can drive without a process or external binary.

The JSON reader uses `json.loads` with `object_pairs_hook` duplicate refusal and
`parse_constant` non-finite refusal. A lexical depth guard before decoding bounds
recursive work; strings and escapes must be accounted for so braces in strings
do not change depth. The YAML reader tokenizes indentation and quoted scalars,
counts containers before descending, and shares no parser with JSON. It rejects
unsupported constructs outside quoted text before constructing a candidate.
`[]` and `{}` are the only inline collections. Test quoted punctuation and
comment boundaries alongside rejected syntax so rejection is not overbroad.

Reads are bounded before parsing; scalar and list limits precede semantic shape
checks. Evidence hashing opens confined regular files with no-follow traversal,
streams chunks under the separate evidence budget and checks descriptor identity
before/after reading. The precise portable descriptor/fallback strategy is
implementation-discovered: inspect supported platforms, preserve refusal on
uncertain confinement, then test symlink and file-replacement seams. Do not
import catalogue-local helpers into exported scripts. Tests may use sparse
files or an injected stream boundary to reach the evidence-size limit without
allocating its full size in memory.

The importer reuses the release reader and validator through in-file functions.
It builds a new mapping, joins supplement evidence by component ID plus digest,
and validates the candidate before reporting complete. Incomplete output remains
an explicit candidate with missing facts, never a passing schema assertion.
Input/output identity checks include resolved aliases and same-file identity;
exclusive output creation prevents overwriting another candidate. It refuses
symlink outputs and confines output beneath `--root`. Refusals produce no
candidate; ordinary missing facts can produce an incomplete candidate.

### Interfaces & contracts

Owned by: T1, T2, T3, T4, T5, T6

Traces to AC-0013 through AC-0018, AC-0024 through AC-0033 and AC-0037 through
AC-0040; implements both published file formats through their skill scripts.
The implementation assigns the script basenames during T1/T3 and uses those same
names in caller examples, guides and evals. No ungrounded existing symbol is
assumed. Argument parsing exposes the spec's validation/import calls plus plan
expectation flags; tests drive the parser as well as callable validation.

A caller-selected policy file is parsed as bounded JSON and never inferred from
the candidate directory. Its per-kind/per-stage entries expand into required
checks over actual component subjects. Applicable plan validation/policy/security/
review minima cannot disappear through policy omission. An injected UTC clock
makes freshness deterministic. Issue collection has stable codes and field paths;
exceptions at the CLI boundary map to safe results without echoing raw text.
Output stream setup follows `packs/AGENTS.md` before the first print.

Examples live as runtime assets under each owning skill, with synthetic evidence
and caller policy alongside them. Tests instantiate examples into a temporary
root and hash fixture bytes, so repository layout and absolute checkout paths
are irrelevant. Native-ADR request/constraint evidence stays adopter-owned;
no catalogue ADR or spec citation enters `.apm/`. The image-only example models
CI-produced evidence without running CI or pretending a digest proves producer
identity. Plan components test bundle-byte verification using pack-local
synthetic bundles; release tests never import or inspect the other pack.

## Tasks

### T1: Plan-bundle contract and boundary tests pass

**Depends on:** none

**Verification mode:** TDD. Review shape: DEEP, confined to the plan bundle.

**Touches:** `packs/iac-terraform/.apm/skills/generate-iac/scripts/*`, `packs/iac-terraform/.apm/skills/generate-iac/references/iac-plan-bundle.v1.schema.json`, `packs/iac-terraform/tests/skills/generate-iac/**`

**Tests:**
- Start with a synthetic, complete local bundle and mutate typed fields, versions, keys, limits and bindings through the importable validator seam (AC-0001, AC-0041, AC-0046, AC-0003, AC-0004, AC-0005, AC-0006, AC-0007, AC-0008, AC-0009, AC-0010).
- Use a temp filesystem for path/symlink, streamed-budget and tamper cases; a no-network sentinel and captured output check external and credential locators (AC-0011, AC-0012, AC-0013, AC-0014, AC-0017, AC-0045, AC-0047).
- Drop each of the four built-in plan stages in turn under an empty trusted policy (AC-0048); time 1 MiB adversarial JSON inputs and a gzip-magic input (AC-0050).
- Inject a fixed clock and expectations; change each expected target/state/toolchain value separately and mutate inspection subject tuples independently from bytes (AC-0015, AC-0016, AC-0018).
- Parse the schema with stdlib JSON and compare required sets, enums, object closure and version to validator-owned structure tables, including deliberate parity mutations (AC-0034).

**Done when:** The isolated `python3 -m pytest packs/iac-terraform/tests/skills/generate-iac/ -q` run passes, including a CLI smoke and JSON non-finite refusal. Boundary cases prove their first firing limit with inputs below earlier limits.

### T2: Native-ADR Terraform caller validates through the shipped CLI

**Depends on:** T1

**Verification mode:** Goal-based integration plus visual/manual CLI QA. Review shape: bounded example.

**Touches:** `packs/iac-terraform/.apm/skills/generate-iac/assets/**`, `packs/iac-terraform/tests/skills/generate-iac/**`

**Tests:**
- Copy the caller example into a fresh temp root and invoke the real entry point using example policy and fixed time; parse stdout, compare exit status and record a manual run from the pack-source entry point (AC-0032).
- Assert the example's request/constraint evidence resolves to its adopter ADR and that changing saved-plan bytes breaks the same journey.

**Done when:** The direct caller smoke passes without Terraform or a G4 event; the isolated plan suite remains green and the ledger contains the pack-source manual invocation result. T6 repeats it against the rebuilt projection.

### T3: Release YAML subset and candidate validation tests pass

**Depends on:** none

**Verification mode:** TDD. Review shape: DEEP; split parser and semantic validation if independent review exceeds the unit's proof budget.

**Touches:** `packs/release-engineering/.apm/skills/release-loop/scripts/*`, `packs/release-engineering/.apm/skills/release-loop/references/release-handoff.v2.schema.json`, `packs/release-engineering/tests/skills/release-loop/**`

**Tests:**
- Build table-driven reader cases for quoted/plain scalars, escapes, comments, empty collections and every forbidden syntax form; drive resource boundaries before semantic validation (AC-0003, AC-0004, AC-0005, AC-0006, AC-0007, AC-0008, AC-0009, AC-0010, AC-0019).
- Reuse only release-local temp-fixture builders to test Evidence reads and checks, including byte mutation and fake external locators; no cross-pack imports (AC-0011, AC-0012, AC-0013, AC-0014, AC-0015, AC-0016, AC-0017).
- Run image-only, plan-only, unknown-kind and empty-component fixtures through the validator; alter applicability and trusted-policy requirements rather than mocking readiness (AC-0002, AC-0020, AC-0021, AC-0022, AC-0023, AC-0024, AC-0041, AC-0042, AC-0043, AC-0044, AC-0045, AC-0047).
- Time 1 MiB adversarial YAML inputs (long lines, dense escapes, many keys, many comments) and a gzip-magic input (AC-0050).
- Compare release schema structure with validator tables and assert stdout/exit mappings through a CLI smoke (AC-0034).

**Done when:** The isolated `python3 -m pytest packs/release-engineering/tests/skills/release-loop/ -q` run passes. Parser fixtures prove accepted quoted syntax survives the forbidden-token checks.

### T4: Image-only CI caller validates through the shipped CLI

**Depends on:** T3

**Verification mode:** Goal-based integration plus visual/manual CLI QA. Review shape: bounded example.

**Touches:** `packs/release-engineering/.apm/skills/release-loop/assets/**`, `packs/release-engineering/tests/skills/release-loop/**`

**Tests:**
- Instantiate the CI example in a temp root and invoke the real release script with its policy, local attestation/check bytes and fixed time; parse JSON stdout and exit code (AC-0033).
- Remove its image tag and then digest to prove this positive journey is not satisfied by an invented infrastructure component.

**Done when:** The direct image-only CLI smoke and isolated release suite pass; the ledger includes the pack-source manual result. T6 repeats it against the rebuilt projection.

### T5: V1 import preserves input and reports evidence gaps

**Depends on:** T3

**Verification mode:** TDD. Review shape: DEEP, bounded to legacy translation.

**Touches:** `packs/release-engineering/.apm/skills/release-loop/scripts/*`, `packs/release-engineering/tests/skills/release-loop/**`

**Tests:**
- No recorded real v1 corpus is available. Freeze synthetic v1 fixtures from the documented G4 fields, run them through the reader, and record accept/reject counts; this is synthetic coverage, not adopter-corpus evidence.
- Import a missing-facts fixture and a fully supplemented twin through the CLI into fresh output files, then run the output through v2 validation (AC-0025, AC-0026).
- Snapshot input bytes before success, incomplete conversion and refusal; test equal paths, same-file aliases, existing output and symlink output without altering the source (AC-0027, AC-0028).
- Change version and unsupported YAML features independently; assert result codes and absence of output on refusal (AC-0029, AC-0030).
- Inject a failing write and a failing publish, and create the destination between the existence check and publication through a seam; assert the destination bytes, the absence of temporary files and the `error` result (AC-0049).
- Pin the unchanged legacy tolerant-reader passage and exercise synthetic unknown-field/version cases against its documented outcomes; there is no legacy parser executable to claim as runtime proof (AC-0031).

**Done when:** The isolated release suite passes with complete/incomplete/refusal outputs observed and source-byte equality checked for each import case. Synthetic corpus counts are recorded in the ledger.

### T6: Guides, evals, releases and CI registration pass repository gates

**Depends on:** T1, T2, T3, T4, T5

**Verification mode:** Goal-based checks. Review shape: MIXED; schema/parser code stays in earlier units, this unit carries integration wiring.

**Touches:** `packs/iac-terraform/**`, `packs/release-engineering/**`, `guides/iac-terraform/**`, `guides/release-engineering/**`, `.github/workflows/build-check.yml`, `Makefile`, `tools/lint-ci-parity.py`, `tools/test_local_ci_shared_test_deduplication.py`, generated self-host projections

**Tests:**
- Content-pin each short skill pointer; retain the existing legacy passage and existing eval cases, add direct-caller and refusal/gap eval prompts (AC-0031, AC-0037).
- Compare parsed TOML/plugin JSON versions; run `python3 tools/changelog.py new --help`, then its supported command for each pack's fragment (AC-0035, AC-0036).
- Validate and link-check the guide pages named by the spec, including reference-page and README entry links (AC-0038).
- Register both explicit pack suite paths in `.github/workflows/build-check.yml` and the Makefile test roster in separate pytest processes. Update `tools/lint-ci-parity.py` step dispositions and `SUITE_DISPOSITION` entries as required. Run `tools/lint-pack-test-boundary.py` to prove the literal runners are recognized, without adding `_NO_RUNNER` exemptions (AC-0039).
- Inspect `tools/test_local_ci_shared_test_deduplication.py` ownership/exclusion data and Makefile baseline derivation. Re-derive only affected baseline pins with a before/after semantic roster comparison; keep new suites out of composed exclusions unless an existing owner actually runs them. Run that guard, CI parity lint and pack-boundary lint (AC-0039).
- Run `make build-self`, exercise both built CLI examples, then `make lint-ruff lint-mypy` and `make precheck`; record exits and projection freshness (AC-0040).

**Done when:** Both isolated pack suites, guide checks, metadata checks and named repository gates pass. Full-mode adversarial, security and quality reviews have no unresolved findings; no approval or execution authority is inferred from this plan.

## Rollout

The two minor pack releases publish additive formats and direct validation paths.
The v1 tolerant reader remains available. No deployment or in-place data migration
occurs. Rollback selects the prior pack release and retains original v1 inputs;
published v2 candidates remain immutable rather than being rewritten as v1.

## Risks

- A strict YAML subset rejects some real adopter files; explicit unsupported results and the unchanged legacy route contain that compatibility risk. Synthetic fixtures cannot measure its prevalence.
- Filesystem races and parser depth checks are the highest implementation risks; review needs the actual descriptor/lexical guard code and adversarial fixtures, not only schema parity.
- Authentic-looking evidence can have a correct digest. Guides and examples must preserve the distinction between byte verification and adopter provenance trust.

## Changelog

No approvals recorded.
