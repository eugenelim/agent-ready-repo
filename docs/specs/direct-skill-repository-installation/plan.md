# Plan: Direct skill repository installation

- **Spec:** [`spec.md`](spec.md)
- **Status:** Drafting
- **Repository anchors:** `catalogue.py:resolve_catalogue`, `https_catalogue.py:fetch_catalogue_archive`, `commands/install.py:_render_for_repo_scope` and `_check_source_conflict`, and `config.py:State`.

## Approach

Run T0a–T0c before their dependent layers. Then harden acquisition, establish manifest/classification/normalization, compose admission and state, expose CLI/lifecycle/docs, and join evidence. T11 is the final evidence thread; T12 records security evidence; T13 prepares release artifacts.

## Design (LLD)

- `direct_source_acquisition.py`: credential-free GitHub archive acquisition and Family-1 policy for direct and catalogue routes.
- `bounded_metadata.py`: lifts unchanged bounded frontmatter/TOML primitives and limits from `catalogue_tooling/okf_discovery.py`.
- `direct_source.py`: direct classification, Family-2 inventory, admission, diagnostics, and normalization entry point.
- `direct_source_state.py`: direct provenance and digest inputs for the existing pack/adapter state writer.
- `commands/upgrade.py`: direct-upgrade re-consent.

## Constraints

- Preserve catalogue precedence, pack/adapter ownership, projection, and source-conflict behavior.
- T2 updates `contracts/pack.schema.json` and the bundled `_data/` copy in byte parity; this is release-impacting. Do not add a runtime dependency, state hierarchy, picker, preview, transport, or unlisted guide.
- Protected AgentBundle implementation changes carry `Engine-Change-RFC: RFC-0098`.

## Construction tests

TDD covers parity, bounds, admission, state/digest, diagnostics, selection, re-consent, and no-write behavior. Manual QA records the built CLI. Goal checks cover spikes and documentation. The autouse offline `conftest` fixture fails every socket attempt. Before T2, sweep anchor tests for content hashes, snapshots, exact tables, and line counts.

## Tasks

### T0a: Spike — normalization parity

**AC:** AC15  
**Depends on:** none  
**Verification:** Goal-based; no stub.

Hand-author canonical, direct, and expected-normalized fixtures; compare repo/user projections, local footprint, and per-file plans. **Done when:** all direct shapes match; a divergence stops T4 and reopens the design.

### T0b: Spike — manifest schema expressiveness

**AC:** AC6  
**Depends on:** none  
**Verification:** Goal-based; no stub.

Test a throwaway schema against catalogue and direct fixtures. **Done when:** both profiles validate as required; unsupported expression reopens the design rather than widening the validator.

### T0c: Spike — installed-file map versus digest

**AC:** AC9, AC13, AC17  
**Depends on:** none  
**Verification:** Goal-based; no stub.

Use discriminating projection, adapter, scope, mode, and display fixtures. **Done when:** record whether the map satisfies the digest contract; if it does, amend the affected contract before T6, otherwise retain the digest.

### T1: Harden GitHub acquisition

**AC:** AC2, AC16, AC18  
**Depends on:** none  
**Verification:** TDD.

**Tests:** boundary/refusal fixtures for both archive routes: limits, URL/ref/SHA/redirect binding, named hex-shaped-tag diagnostic, spool/deadlines spanning acquisition/extraction, library-resolved member checks, cleanup, extraction, and descriptor authorization. Include a gzip stream whose declared member sizes total under 1 MiB but whose decompressed stream crosses 1 GiB; assert the per-minor runtime guard (including synthetic 3.12.10 and zipapp-route refusal), both-route FIFO/case-fold refusal, and direct-only absolute/escaping-symlink refusal while catalogue retains and installs symlinks. **Stub:** `packages/agentbundle/tests/unit/test_direct_source_acquisition.py::test_git_https_acquisition_contract`.

**Done when:** acquisition binds bytes to the requested source, applies Family 1, preserves permitted catalogue symlinks, and leaves no temporary tree on refusal.

### T2: Establish direct-manifest behavior

**AC:** AC6  
**Depends on:** T0b  
**Verification:** TDD.

**Tests:** direct schema acceptance/refusals, legacy catalogue behavior, `contracts/pack.schema.json`/bundled `_data/` byte parity, and reserved-sentinel refusal. **Stub:** `packages/agentbundle/tests/unit/test_pack_config_api.py::test_direct_manifest_rejects_manifestless_sentinel`.

**Done when:** direct and catalogue manifest profiles remain distinct without changing existing schema-major-1 field meanings.

### T3: Classify roots and inventory

**AC:** AC1, AC10, AC16  
**Depends on:** none  
**Verification:** TDD.

**Tests:** shape matrix, candidate order, root-single ignored-context asymmetry, Family-2 per-file/depth/count/total order with limit+1 specific-code overlaps, special entries, and no-write snapshots that detect creation, content/mode change, deletion, and empty directories. **Stub:** `packages/agentbundle/tests/unit/test_direct_admission.py::test_classification_contract`.

**Done when:** classification is deterministic and every mandatory refusal leaves the snapshot equal.

### T4: Normalize direct sources

**AC:** AC15, AC16  
**Depends on:** T0a, T3  
**Verification:** TDD.

**Tests:** expected normalized tree and projection parity, cleanup on refusal/exception, source-copy API prohibition, and replacement-race control. **Stub:** `packages/agentbundle/tests/unit/test_direct_admission.py::test_normalization_projection_parity`.

**Done when:** one bounded temporary canonical representation has demonstrated parity.

### T4a: Lift bounded metadata primitives

**AC:** AC10, AC11  
**Depends on:** none  
**Verification:** TDD.

**Tests:** characterize unchanged `okf_discovery.py` parser primitives and 64 KiB/20/1 MiB/2 MiB limits, plus fail-closed TOML exceptional cases and named display/description excess. **Stub:** `packages/agentbundle/tests/unit/test_direct_admission.py::test_bounded_metadata_characterization`.

**Done when:** direct admission and discovery share bounded primitives.

### T5: Compose admission and diagnostics

**AC:** AC5, AC7, AC10–AC12, AC16, AC18, AC22  
**Depends on:** T1, T2, T4, T4a  
**Verification:** TDD.

**Tests:** failure registry, validate/preflight parity, character/parser/PyYAML controls, one-observation `read_confined_regular_file(..., include_mode=True)` control and `UnsafeContentError` translation, no-bypass/collision cases, direct entry-point boundary, and code registry typing/reachability. Include one fixture per U+115F/U+1160/U+2065/U+FFA0/U+FFF0–U+FFF8. **Stub:** `packages/agentbundle/tests/unit/test_direct_admission.py::test_direct_admission_diagnostic_registry`.

**Discovery predicate:** derive the diagnostic-code set here; once published it must satisfy AC18/AC22.  
**Done when:** mandatory failure is fail-closed and both routes use shared admission.

### T6: Add direct state and digest

**AC:** AC8, AC9, AC13, AC17, AC19  
**Depends on:** T0c, T4  
**Verification:** TDD.

**Tests:** 0.4/0.5 read/write matrix, a committed golden `state.toml` asserting row key order, old-reader refusal, identity/confinement, content-only preimage vectors, update cases, sentinel absence, and recovery for invalid digest prefix. **Stub:** `packages/agentbundle/tests/unit/test_direct_source_state.py::test_digest_version_prefix_refuses`.

**Done when:** direct state is replayable, pinned, and free of mode-driven updates.

### T7: Extend validate and grammar

**AC:** AC3, AC12  
**Depends on:** T5  
**Verification:** TDD plus T11 manual QA.

**Tests:** parser/help, direct JSON envelope/shape, and catalogue JSON goldens. **Stub:** `packages/agentbundle/tests/unit/test_direct_validate.py::test_direct_validate_json_contract`.

**Done when:** direct validation works without changing canonical routes or adding deep validation.

### T8: Implement install selection, summary, and receipt

**AC:** AC3, AC4, AC11, AC16–AC18  
**Depends on:** T1, T5, T6  
**Verification:** TDD plus Manual QA.

**Tests:** TDD stub covers AC4 exit-1 selection arms and source-preserving recovery-command text; fixtures cover selection, dry run, delimited untrusted publisher data (including instruction-shaped description), summary, unknown executable mode, confirmation, receipt, sentinel control, non-executable projection, and no-write snapshots. **Stub:** `packages/agentbundle/tests/integration/test_direct_install.py::test_collection_selection_refusals`.  
**Done when:** local/remote runs record deterministic selection, admissibility summary, SHA receipt, and refusal integrity.

### T9: Complete lifecycle behavior

**AC:** AC3, AC5, AC8, AC12, AC13, AC17, AC19, AC21  
**Depends on:** T8  
**Verification:** TDD plus T11 manual QA.

**Tests:** cover grammar refusals, list/show fields, `--no-check` unknown and per-row/total Family-1 bounds, digest/DRIFT, conflicts, interruption, all scopes, and SHA-pinned re-consent including drift. AC21 has a four-direction parameterized stub (new tool, script digest/set, boundaries, credentialed). **Stub:** `packages/agentbundle/tests/unit/test_direct_source_state.py::test_interrupted_install_leaves_unowned_projection`; **Stub:** `packages/agentbundle/tests/unit/test_direct_upgrade.py::test_capability_reconsent_directions`.

**Done when:** direct skills are listable, showable, upgradable, removable, and recoverable without sentinel leakage.

### T10: Publish documentation and help

**AC:** AC3, AC14, AC22  
**Depends on:** T7, T8, T9  
**Verification:** Goal-based; no stub.

**Tests:** fixture exercise per published command, help, guide/link build, local-only prompt, and code-table equality. **Done when:** published guidance contains no internal-governance identifiers.

### T11: Run the joined steel thread

**AC:** AC1–AC22  
**Depends on:** T1, T9, T10  
**Verification:** Manual QA; no stub.

**Tests:** fixed local/direct-pack/collection/pinned-remote command list; output sweep for sentinel absence; join all construction evidence. Each direct test suite runs once through `run-test-suite` with `-p tools.pytest_collection_floor --minimum-collected=<floor> --collection-floor-suite=<suite-path>`, has the matching `COLLECTION_FLOORS` registry entry, and adds the required `--ignore` at `Makefile:408` to prevent a second execution. **Done when:** recorded evidence maps every AC to an artifact; defects return to their owning task.

### T12: Record boundary security evidence

**AC:** AC20  
**Depends on:** T1, T5, T8, T11  
**Verification:** Goal-based; no stub.

Apply the five required checklist modules and record dispositions at `docs/specs/direct-skill-repository-installation/security-evidence.md` under headings Path/file, Outbound acquisition, Supply chain, Exceptional condition, and Agentic skills. **Done when:** no unresolved blocker remains.

### T13: Prepare release artifacts

**AC:** no AC; convention-driven  
**Depends on:** T11, T12  
**Verification:** Goal-based; no stub.

Update version, changelog, and release notes for the `contracts/` release impact and the new catalogue acquisition-limit refusal/recovery. **Done when:** the version convention check passes.
