# Plan: Direct skill repository installation

- **Spec:** [`spec.md`](spec.md)
- **Status:** Drafting
- **Repository anchors:** `packages/agentbundle/agentbundle/catalogue.py:resolve_catalogue`, `packages/agentbundle/agentbundle/https_catalogue.py:fetch_catalogue_archive`, `packages/agentbundle/agentbundle/commands/install.py:_render_for_repo_scope` and `_check_source_conflict`, and `packages/agentbundle/agentbundle/config.py:State`.

## Approach

Run T0a–T0c before their dependent layers. Then harden acquisition, establish manifest/classification/normalization, compose admission and state, expose CLI/lifecycle/docs, and join evidence. T11 is the final evidence thread; T12 records security evidence; T13 prepares release artifacts.

## Design (LLD)

- `direct_source_acquisition.py`: credential-free GitHub archive acquisition, Family-1 policy, and injectable deadline/progress seams for direct and catalogue routes.
- `bounded_metadata.py`: lifts unchanged bounded frontmatter/TOML primitives and limits from `catalogue_tooling/okf_discovery.py`.
- `direct_source.py`: direct classification, Family-2 inventory, admission, diagnostics, and normalization entry point.
- `direct_source_state.py`: direct provenance and digest inputs for the existing pack/adapter state writer.
- `commands/upgrade.py`: direct-upgrade re-consent.
- `tools/lint-direct-code-table.py` and `tools/test_lint_direct_code_table.py`: published direct-code-table equality lint and its mutation control.

## Constraints

- Preserve catalogue precedence, pack/adapter ownership, projection, and source-conflict behavior.
- T2 updates `contracts/pack.schema.json` and the bundled `_data/` copy in byte parity; this is release-impacting. Do not add a runtime dependency, state hierarchy, picker, preview, transport, or unlisted guide.
- Protected AgentBundle implementation changes carry `Engine-Change-RFC: RFC-0098`.

## Construction tests

TDD covers parity, bounds, admission, state/digest, diagnostics, selection, re-consent, and no-write behavior. Manual QA records the built CLI at `docs/specs/direct-skill-repository-installation/manual-qa.md` and stops when every fixed command has an exit code, receipt/output record, and its mapped AC. Goal checks cover spikes and documentation. T1 adds opt-in direct-source offline fixtures beside the direct-source test modules, never to the root `packages/agentbundle/tests/conftest.py`; they refuse non-loopback sockets while allowing loopback TLS-server controls. Before T2, sweep anchor tests for content hashes, snapshots, exact tables, and line counts.

## Tasks

### T0a: Spike — normalization parity

**AC:** AC24  
**Depends on:** none  
**Verification:** Goal-based; no stub.

Hand-author canonical, direct, and expected-normalized fixtures; compare repo/user projections, local footprint, and per-file plans. **Done when:** all direct shapes match; a divergence stops T4 and reopens the design.

### T0b: Spike — manifest schema expressiveness

**AC:** AC10  
**Depends on:** none  
**Verification:** Goal-based; no stub.

Test a throwaway schema against catalogue and direct fixtures. **Done when:** both profiles validate as required; unsupported expression reopens the design rather than widening the validator.

### T0c: Spike — installed-file map versus digest

**AC:** AC13, AC22, AC26  
**Depends on:** none  
**Verification:** Goal-based; no stub.

Use discriminating projection, adapter, scope, mode, and display fixtures. **Done when:** record whether the map satisfies the digest contract; if it does, reopen the governing digest change through *Ask first* (RFC erratum plus spec amendment) before T6, otherwise retain the digest.

### T0d: Spike — corpus admission

**AC:** AC35–AC36  
**Depends on:** none  
**Verification:** Goal-based; no stub.

Clone at least fifteen real public skill repositories, classify each, and measure both bound families against the shape's own content. **Done when:** the verdict table is committed and every refusal is attributable to a named shape exclusion or budget. A first run over eighteen repositories (2026-08-28) admitted seven and recorded: the widest real layouts are root-level skill directories (`<name>/SKILL.md`, e.g. 864 and 846 skills in the two most-starred repositories) and category nesting (`skills/<category>/<name>/SKILL.md`), both outside the two accepted shapes; the tightest budget headroom is depth, at a measured 7 against a limit of 10 for `anthropics/skills` (`skills/xlsx/scripts/office/schemas/ecma/fouth-edition/`), which is reported under AC36 rather than raising the bound; every other budget cleared with 56% or more headroom (worst: 572/5,000 entries, 438/1,000 files, 275 KiB/1 MiB largest file, 10.2/25 MiB total). A second run under E14's two collection roots and optional category level (2026-08-28) admitted nine of eighteen: `.claude/skills/` gained two repositories (35 and 6 skills). A third run over an expanded corpus (2026-08-28) covered 35 repositories holding a collection root; **5 use a category level** and 4 of those admit: `google/skills` (127 skills), `obra/superpowers-skills` (31), `davidondrej/skills` (53), and `mrgoonie/claudekit-skills` (35, which mixes 31 root envelopes with 1 category directory and so exercises the mixed case directly). The one category-grouped refusal, `chujianyun`, refuses on budgets rather than shape (1,255 files and a 3.2 MiB bundled `assets/main.js`) because 1,102 of its files are vendored documentation mirrors; that refusal is correct. Depth is now the binding budget: the corpus maximum is 9 of 10 measured from the collection root (10% headroom) but 7 of 10 measured from the skill envelope (30%), because category grouping costs one level. Family-2 admission cost was measured at every budget simultaneously at its limit (5,000 entries, 1,000 files, 25 MiB): **1.70 s wall-clock and 28 MiB resident**, of which enumeration is 1.32 s at roughly 0.26 ms per entry and reading plus hashing all 25 MiB is 0.38 s — so the budgets sit far inside AC36's 5 s / 256 MiB ceiling and are not a resource control. E15 settled the depth question: depth is measured from each skill envelope and bounded at 12, giving 42% headroom against the measured maximum of 7. No corpus verdict changed; depth was not the binding constraint for any admitted repository.

### T1: Harden GitHub acquisition

**AC:** AC3–AC6, AC25, AC27  
**Depends on:** none  
**Verification:** TDD.

**Tests:** add opt-in direct-source socket-refusal fixtures beside direct-source test modules, refusing non-loopback sockets while permitting loopback TLS-server controls; never add an autouse root-conftest fixture. Add boundary/refusal fixtures for both archive routes: limits, requested-GitHub/codeload redirect equivalence including the percent-encoded requested ref, hop/user-info/HTTPS refusal, URL/ref/SHA binding, named hex-shaped-tag diagnostic, `CatalogueError(message, code, remediation)` diagnostic/recovery for catalogue Family-1 refusal, spool/deadlines with acquisition socket-timeout and extraction-only inactivity-timeout fixtures, library-resolved member checks, cleanup, extraction, and descriptor authorization. Include a gzip stream whose declared member sizes total under 1 MiB but whose decompressed stream crosses 1 GiB; assert its runtime budget in the test, lower constructor/parameter deadline and decompressed-counter defaults through the injectable clock/progress seam, and assert the call-time per-minor runtime guard (below the lowest listed minor refuses, listed floors apply, higher minors pass; including synthetic 3.12.10 and zipapp-route refusal), both-route FIFO/case-fold refusal, and direct-only absolute/escaping-symlink refusal while catalogue retains and installs symlinks. Windows FIFO/symlink fixtures assert documented `unknown`/no-write outcomes rather than skipping; add the Windows catalogue-symlink regression arm. Add a value check that parses E11 bounds and compares them with the module constants. `CatalogueError` gains optional `code` and `remediation` parameters across 61 existing raise sites: assert `str(CatalogueError("m", code=..., remediation=...)) == "m"` so no `pytest.raises(..., match=...)` assertion changes, and name `test_https_catalogue.py`, `test_upgrade_bulk_all.py`, and `test_catalogue_trust_fallback.py` as the regression set, since the pre-T2 anchor sweep covers hashes and tables but not exception-message assertions. **Stub:** `packages/agentbundle/tests/unit/test_direct_source_acquisition.py::test_git_https_acquisition_contract`.

**Done when:** acquisition binds bytes to the requested source, applies Family 1, preserves permitted catalogue symlinks, and leaves no temporary tree on refusal.

### T2: Establish direct-manifest behavior

**AC:** AC10  
**Depends on:** T0b  
**Verification:** TDD.

**Tests:** direct schema acceptance/refusals (including unsupported major in baseline code), legacy catalogue behavior, and reserved-sentinel refusal. `tools/test_contract_parity.py` owns the `contracts/pack.schema.json`/bundled `_data/` byte-parity assertion. **Stub:** `packages/agentbundle/tests/unit/test_pack_config_api.py::test_direct_manifest_rejects_manifestless_sentinel`.

**Done when:** direct and catalogue manifest profiles remain distinct without changing existing schema-major-1 field meanings.

### T3: Classify roots and inventory

**AC:** AC1–AC2, AC14–AC17, AC25, AC32–AC33, AC34  
**Depends on:** none  
**Verification:** TDD.

**Tests:** shape matrix, measured paths rooted only at `skills/` plus direct-pack root `pack.toml`, or root `SKILL.md` plus payload directories (never repository context), and the Family-2 measure order (enumeration budgets, then read per-file → total). **T3 owns the diagnostic-attribution mechanism.** A spike against the real helper established: `list_confined_regular_files` refuses a file-typed `directory` argument (`directory boundary is unsafe: SKILL.md`), so named files must be read, never enumerated; `root=<source>, directory=<payload dir>` works, so AC34's binding is achievable; and a budget breach and an entry-integrity refusal are both bare `UnsafeContentError`, distinguished in the message alone (`source tree exceeds entry-count limit` versus `source entry is not a regular file: <path>`), which AC33 forbids parsing. Only `max_entries` must therefore be a helper parameter — file count, selected-skill count, and depth are derivable from the returned paths, so each carries its own diagnostic without a second traversal. Settle bound-versus-integrity attribution without message parsing and record the chosen mechanism here; note that a depth-only chain of empty directories is bounded by the entry budget rather than the depth budget. Set entry limit to 5,000, depth limit to 12 measured from each skill envelope, file limit to 1,000, and selected-skill limit to 500: a 5,001-entry directory reaches the entry code; a 13-level envelope reaches the depth code, and a 12-level envelope under a category directory is admitted, proving depth is measured from the envelope and not the collection root; a 1,001-file directory reaches the file code; and a 501-skill fixture (1,002 entries, 501 files, depth 2) reaches only the selected-skill code. Add a multi-directory accumulation fixture that no per-directory implementation can pass: a root single with 600 files under `scripts/` and 401 under `references/`, each individually under 1,000, which must reach the file code. Add a total-bytes fixture of two files summing past 25 MiB with each under 1 MiB, proving accumulation rather than a per-file trip, and a per-file fixture of one 1 MiB+1 file; both must reach their own budget code. Add an entry-integrity fixture — a symlink inside `skills/<one>/scripts/` — asserting the integrity code and its offending path, never a budget code. Add one link-like fixture for every measured path (each enumerated directory and each named file), plus a link-like non-measured marker fixture (a symlinked root `pack.toml` beside a valid `skills/`) and a wrong-type fixture per marker kind, each asserting the measured-path-integrity code; add E13 fixtures for a link-like/special root sibling beside valid `skills/` and for a root sibling tree exceeding 5,000 entries, each proving ignored content is absent from counts, normalized tree, digest preimage, AC19 capability block, file plan, and projection. Cover special entries with Windows `unknown`/no-write arms, and no-write snapshots that detect creation, content/mode change, deletion, and empty directories. **Stub:** `packages/agentbundle/tests/unit/test_direct_admission.py::test_classification_contract`.

**Done when:** classification is deterministic and every mandatory refusal leaves the snapshot equal.

### T4: Normalize direct sources

**AC:** AC24, AC25  
**Depends on:** T0a, T3  
**Verification:** TDD.

**Tests:** expected normalized tree and projection parity, cleanup on refusal/exception, source-copy API prohibition, and a replacement-race control that mutates the source between admission and copy and proves installed bytes equal digested bytes. **Stub:** `packages/agentbundle/tests/unit/test_direct_admission.py::test_normalization_projection_parity`.

**Done when:** one bounded temporary canonical representation has demonstrated parity.

### T4a: Lift bounded metadata primitives

**AC:** AC14–AC17, AC18–AC20  
**Depends on:** none  
**Verification:** TDD.

**Tests:** characterize unchanged `okf_discovery.py` parser primitives and limits, show the 2 MiB skill ceiling is non-binding on the direct route, plus fail-closed TOML exceptional cases and named display/description excess. **Stub:** `packages/agentbundle/tests/unit/test_direct_admission.py::test_bounded_metadata_characterization`.

**Done when:** direct admission and discovery share bounded primitives.

### T5: Compose admission and diagnostics

**AC:** AC9, AC11, AC14–AC21, AC25, AC27, AC34  
**Depends on:** T1, T2, T4, T4a  
**Verification:** TDD.

**Tests:** failure registry, validate/preflight parity, character/parser/PyYAML controls, one-observation `read_confined_regular_file(..., max_bytes=1 MiB, include_mode=True)` control and `UnsafeContentError`/tar-error translation, a 1 MiB+1 file refusal, measured-path-integrity diagnostic, no-bypass/NFC-case-fold collision cases, direct entry-point boundary, and registry typing. Statically assert direct modules have no `Import`/`ImportFrom` of `subprocess` or `runpy`, no `ImportFrom os` execution member, and no `lstat`/`stat`/`fstat`/`resolve` except the named candidate-probe carve-out; prohibit the explicit `os` execution-name frozenset plus the `os.spawnv` prefix fixture; and prohibit `ast.Name` uses of `exec`, `eval`, `compile`, `__import__`, and imported `os` execution names. Add one mutation fixture for each family (explicit `os` member, `subprocess` import, `os.spawnv` prefix, and builtin name) that fails if its control is removed. Include one fixture per U+115F/U+1160/U+2065/U+3164/U+FFA0/U+FFF0–U+FFF8, pin the generated Unicode-data version, and assert an invisible-letter name refuses at identity rather than display stripping. **Stub:** `packages/agentbundle/tests/unit/test_direct_admission.py::test_direct_admission_diagnostic_registry`.

**Discovery predicate:** derive the diagnostic-code set here; once published it must satisfy AC27/AC31.  
**Done when:** mandatory failure is fail-closed and both routes use shared admission.

### T6: Add direct state and digest

**AC:** AC12, AC13, AC22, AC26, AC28  
**Depends on:** T0c, T4  
**Verification:** TDD.

**Tests:** 0.4/0.5 read/write matrix, a committed golden `state.toml` asserting row key order, old-reader refusal, identity/confinement, content-only preimage vectors, update cases, sentinel absence, and recovery for invalid digest prefix. **Stub:** `packages/agentbundle/tests/unit/test_direct_source_state.py::test_digest_version_prefix_refuses`.

**Done when:** direct state is replayable, pinned, and free of mode-driven updates.

### T7: Extend validate and grammar

**AC:** AC7, AC21  
**Depends on:** T5  
**Verification:** TDD plus T11 manual QA.

**Tests:** parser/help, direct JSON envelope/shape, and catalogue JSON goldens. **Stub:** `packages/agentbundle/tests/unit/test_direct_validate.py::test_direct_validate_json_contract`.

**Done when:** direct validation works without changing canonical routes or adding deep validation.

### T8: Implement install selection, summary, and receipt

**AC:** AC7, AC8, AC18–AC20, AC25–AC27  
**Depends on:** T1, T5, T6  
**Verification:** TDD plus Manual QA.

**Tests:** TDD stub covers AC8 exit-1 selection arms and source-preserving recovery-command text; fixtures cover selection, dry run, line-anchored delimited untrusted publisher data (including instruction-shaped one-line values, delimiter-line equality refusal, and a normalized 4,097-UTF-8-byte value refusal), summary, unknown executable mode on Windows, confirmation, receipt, sentinel control, non-executable projection, and no-write snapshots. Record the built CLI Manual-QA evidence in T11. **Stub:** `packages/agentbundle/tests/integration/test_direct_install.py::test_collection_selection_refusals`.  
**Done when:** local/remote runs record deterministic selection, admissibility summary, SHA receipt, and refusal integrity.

### T9: Complete lifecycle behavior

**AC:** AC7, AC9, AC12, AC21, AC22, AC26, AC28, AC30  
**Depends on:** T8  
**Verification:** TDD plus T11 manual QA.

**Tests:** cover grammar refusals, `--check` default-off direct status with no outbound request, stored-source grammar failure rendering `unknown` without a request, an AC4 differential fixture proving the validated string and the requested string are byte-identical on both the status and the upgrade routes, a direct row whose stored source is absent or fails the grammar refusing rather than taking the legacy default-chain inference, list/show fields, digest/footprint-DRIFT, conflicts, interruption, all scopes, `upgrade --all` refusing capability acceptance, and SHA-pinned remote plus required refusal-printed local digest-pin re-consent including capability drift. AC30 has a parameterized stub for manifestless and direct-pack route-valid acceptance, allowed-tools set inequality including declared → `undeclared (unrestricted)`, `SKILL.md` digest inequality, added/removed skill identities, payload digest/set under each of `scripts/`, `references/`, `assets/`, and `evals/`, boundary-set inequality in either direction, credentialed normalized-value inequality, and each adapter’s lossless round-trip of compared fields. **Stub:** `packages/agentbundle/tests/unit/test_direct_source_state.py::test_interrupted_install_leaves_unowned_projection`; **Stub:** `packages/agentbundle/tests/unit/test_direct_upgrade.py::test_capability_reconsent_directions`.

**Done when:** direct skills are listable, showable, upgradable, removable, and recoverable without sentinel leakage.

### T10: Publish documentation and help

**AC:** AC7, AC23, AC31  
**Depends on:** T7, T8, T9  
**Verification:** Goal-based; no stub.

**Tests:** fixture exercise per published command, help, guide/link build, local-only prompt, direct-code-table equality, and a mutation sibling `tools/test_lint_direct_code_table.py`. **Done when:** the new stdlib-only `tools/lint-direct-code-table.py` imports `DIRECT_CODES`, parses the published direct diagnostic-code table, and verifies set equality; `run-test-suite` invokes it beside `tools/lint-conformance-portability.py`, while its pytest companion is added to `FINAL_TOOL_BATCH` and the matching Makefile final-batch line in lockstep. Because CI runs `make build-check` rather than `make test`, register both in `.github/workflows/build-check.yml` as well—the lint beside the `lint-conformance-portability` step and the companion in the pytest batch—matching that precedent's two-place registration; a Makefile-only registration never gates a PR. Published guidance contains no internal-governance identifiers.

### T10a: Register inherited collection floor

**AC:** — (build hygiene)  
**Depends on:** T5  
**Verification:** Goal-based; no stub.

Append `"packages/agentbundle/tests/": 3200` after the two desk-research entries in `COLLECTION_FLOORS`; 3,200 is the measured 4,119 collection minus 919 tests of stated headroom. On the existing bare `$(PYTHON) -m pytest packages/agentbundle/tests/ -q` `run-test-suite` line, add `-p tools.pytest_collection_floor`, `--minimum-collected=3200`, and `--collection-floor-suite=packages/agentbundle/tests/`; do not add a second suite invocation or `--ignore`. **Done when:** `tools/test_local_ci_shared_test_deduplication.py::test_real_make_floors_are_one_pass_and_keep_inherited_streams` proves the floor has one pass and inherited streams.

### T11: Run the joined steel thread

**AC:** AC1–AC36  
**Depends on:** T1, T9, T10, T10a  
**Verification:** Manual QA; no stub.

**Tests:** fixed local/direct-pack/collection/pinned-remote command list; output sweep for sentinel absence; join all construction evidence and the T8 built-CLI Manual-QA record at `docs/specs/direct-skill-repository-installation/manual-qa.md`. Add `packages/agentbundle/tests/unit/test_direct_source_acquisition.py`, `packages/agentbundle/tests/unit/test_direct_admission.py`, and `packages/agentbundle/tests/integration/test_direct_install.py` to the curated Windows agentbundle test list as `tests/unit/...` and `tests/integration/...`, matching its package `cwd`, so their Windows arms execute. The Windows step judges each module by executed-test count, not by return code alone: an all-skipped pytest run exits 0, so assert a non-zero executed count for each of the three modules, matching the dependency-probe precedent already in that module. Assert those three module paths are in the collected node set; the collection floor remains build hygiene only. Each direct test suite is collected once through its inherited `run-test-suite` invocation and the matching `COLLECTION_FLOORS` registry entry. **Done when:** recorded evidence maps every AC to an artifact; defects return to their owning task.

### T12: Record boundary security evidence

**AC:** AC29  
**Depends on:** T1, T5, T8, T11  
**Verification:** Goal-based; no stub.

Apply the five required checklist modules and record dispositions at `docs/specs/direct-skill-repository-installation/security-evidence.md` under headings Path/file, Outbound acquisition, Supply chain, Exceptional condition, and Agentic skills. **Done when:** no unresolved blocker remains.

### T13: Prepare release artifacts

**AC:** AC3–AC6, AC10  
**Depends on:** T11, T12  
**Verification:** Goal-based; no stub.

Update version, changelog, and release notes for the `contracts/` release impact and the new catalogue acquisition-limit refusal/recovery. **Done when:** the version convention check passes.
