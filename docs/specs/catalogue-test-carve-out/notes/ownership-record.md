# Catalogue test carve-out ownership record

This is the migration ledger required by AC13. Ownership follows what each test
asserts, not what it imports, reads, or invokes.

## Progress

- [x] T1a — `tests/build_pipeline/` dispositions complete.
- [x] T1b — `tests/unit/` dispositions complete.
- [x] T1c — `tests/integration/` dispositions complete.
- [x] T1d — loose root, supplemental inventory, completeness proof, and human
  disposition of all contested rows complete.

## Discovery methods

For each nested root, the two RFC-0082 signals are re-derived from current
source rather than inherited from the RFC:

1. **Quoted-directory signal:** an indexed `Path(__file__)` repository anchor
   combined with a quoted root-directory composition for `packs`, `contracts`,
   `profiles`, or `guides`.
2. **Path-form signal:** an indexed `Path(__file__)` repository anchor combined
   with any catalogue-shaped path form, including `marketplace.json`.
3. **Supplemental inventory:** marker-walking anchors and paths composed from
   separate literals that either indexed-parent signal can miss.

The signals select candidates only. They never assign ownership.

## T1a — `tests/build_pipeline/`

Current root: `packages/agentbundle/tests/build_pipeline/`.

- Modules inspected: **44/44**.
- Quoted-directory signal: **29/44**.
- Path-form signal: **36/44**.
- Supplemental candidate: `test_shared_libs_projection.py`, which walks parents
  until it finds a catalogue marker instead of using an indexed parent.
- Composed-path case: `test_shared_prefix_contract.py` uses the literal
  `contracts/adapter.toml`; the quoted-directory signal misses it.
- Six no-`__file__` modules use synthetic paths only and are not live-catalogue
  candidates: `test_direct_directory_cleanup.py`,
  `test_load_pack_hook_wiring_safely.py`, `test_projections_merge_json.py`,
  `test_scope_rails.py`, `test_self_host_fixture_guard.py`, and
  `test_self_host_recipe_config.py`.

Shipping legend: **sdist** = engine sdist only; **catalogue** = catalogue
archives and init scaffolds; **pack** = catalogue archives and self-hosted init
with its pack; **never** = repository-only.

| Module | Test class or module-level group | Owner | Assertion basis | Destination | Ships |
| --- | --- | --- | --- | --- | --- |
| `test_adapter_claude_code.py` | all classes | engine | Adapter projection and orphan behaviour; packs are inputs. | stay | sdist |
| `test_adapter_codex.py` | all classes | engine | Codex projection and migration behaviour; the shipped-skill sweep asserts projector output. | stay; fixture-back | sdist |
| `test_adapter_copilot.py` | all classes | engine | Adapter behaviour. | stay | sdist |
| `test_adapter_cursor.py` | all classes | engine | Contract and adapter behaviour; core is projection input. | stay | sdist |
| `test_adapter_gemini.py` | `GeminiCommandTomlTests`; `GeminiContractTests`; `GeminiProjectionTests`; `GeminiSettingsMergeTests`; `GeminiInstallDispatchTests`; `GeminiSelfHostTests` | engine | Adapter, install, and self-host behaviour. | stay | sdist |
| `test_adapter_gemini.py` | `GeminiShippedAgentToolCoverageTests`; `GeminiAllPacksAdmissibleTests` | catalogue rule-shaped | Sweeps whatever packs exist and asserts portable catalogue rules. | `tests/conformance/` | catalogue |
| `test_adapter_kiro.py` | all classes | engine | Adapter behaviour. | stay | sdist |
| `test_adapter_kiro_alias.py` | `KiroAliasTests` | engine | Alias and shipped-adapter API. | stay | sdist |
| `test_adapter_kiro_cli.py` | `KiroCliAdapterTests` | engine | Adapter behaviour. | stay | sdist |
| `test_adapter_kiro_ide.py` | `KiroIdeAdapterTests` | engine | Adapter behaviour. | stay | sdist |
| `test_adapter_root_bins_projection.py` | all classes | engine | Projection primitive; a real credential pack is smoke-test input. | stay; fixture-back | sdist |
| `test_architect_design_reviewer_projection.py` | `ArchitectDesignReviewerProjectionTests` | pack: architect | Pins one pack's agent and declared adapter roster. | `packs/architect/tests/` | pack |
| `test_architect_design_reviewer_rubric_parity.py` | `ArchitectRubricParityTests` | pack: architect | Asserts only architect pack content. | `packs/architect/tests/` | pack |
| `test_build_ships_seeds.py` | `BuildShipsSeedsTests` | engine | Pipeline against a synthetic pack. | stay | sdist |
| `test_contract.py` | all except the named method below | engine | Engine contract and schema behaviour. | stay | sdist |
| `test_contract.py` | `TestCodexSkillDirectDirectory.test_seed_agents_md_has_no_legacy_delimiters` | pack: core | Direct assertion on one pack seed, without engine invocation. | `packs/core/tests/` | pack |
| `test_contract_scope.py` | all classes | engine | Validator and adapter-contract semantics. | stay | sdist |
| `test_contract_v07.py` | `TestContractV07` | engine | Adapter-contract floors and invariants, not a pack roster. | stay | sdist |
| `test_contract_v08.py` | `TestContractV08` | engine | Adapter-contract floors and invariants, not a pack roster. | stay | sdist |
| `test_direct_directory_cleanup.py` | all module-level tests | engine | Pure projection cleanup over temporary trees. | stay | sdist |
| `test_end_to_end_build.py` | all classes | engine | Pipeline against package fixtures. | stay | sdist |
| `test_lint_agents_md_diataxis_block.py` | `DiataxisBlockTests` | tools | Exercises `tools/lint-agents-md.py`. | `tools/` | never |
| `test_lint_agents_md_legacy_block.py` | `LegacyBlockWarningTests` | tools | Exercises `tools/lint-agents-md.py`. | `tools/` | never |
| `test_lint_agents_md_risk_block.py` | `RiskBlockEqualityTests` | tools | Exercises `tools/lint-agents-md.py`. | `tools/` | never |
| `test_lint_packs.py` | all classes | engine | Invokes the engine linter over synthetic packs. | stay | sdist |
| `test_load_pack_hook_wiring_safely.py` | `TestLoadPackHookWiringSafely` | engine | Engine parser and security behaviour. | stay | sdist |
| `test_pack_schema.py` | all classes | engine | Engine schema behaviour. | stay | sdist |
| `test_pack_schema_allowed_adapters.py` | all classes | engine | Engine schema and cross-field validation. | stay | sdist |
| `test_pack_schema_install.py` | all classes | engine | Engine schema behaviour. | stay | sdist |
| `test_pipeline.py` | all classes | engine | Pipeline and recipe behaviour over synthetic packs. | stay | sdist |
| `test_plugin_manifest_schema.py` | all except `SourcePluginJsonAuditTests` | engine | Engine schema behaviour. | stay | sdist |
| `test_plugin_manifest_schema.py` | `SourcePluginJsonAuditTests` | catalogue rule-shaped | Sweeps every source manifest and asserts portable shape rules. | `tests/conformance/` | catalogue |
| `test_projectable_subset.py` | all classes | engine | Engine projection over fixtures. | stay | sdist |
| `test_projections_merge_json.py` | all classes | engine | Engine merge-json primitive. | stay | sdist |
| `test_scope_rails.py` | all classes | engine | Engine validation rails over synthetic packs. | stay | sdist |
| `test_security.py` | all classes | engine | Engine path and manifest validation. | stay | sdist |
| `test_self_host_check.py` | all except the named method below | engine | Self-host engine behaviour over synthetic trees. | stay | sdist |
| `test_self_host_check.py` | `SeedProjectionTests.test_no_pre_placed_reference_md_core_seed` | pack: core | Pins the absence of one core seed. | `packs/core/tests/` | pack |
| `test_self_host_fixture_guard.py` | all classes | engine | Engine destructive-write guard. | stay | sdist |
| `test_self_host_recipe_config.py` | all classes | engine | Engine recipe parsing and constants. | stay | sdist |
| `test_shared_libs_projection.py` | fixture classes; `ProjectionRetirementGuardTests` | engine | Engine collection and API behaviour. | stay | sdist |
| `test_shared_libs_projection.py` | `RealTreeInvariantTests.test_no_shim_copies_outside_source_pack`; `RealTreeInvariantTests.test_no_consumer_scripts_import_source_pack` | catalogue rule-shaped | Rule-shaped sweep over every pack consumer. | `tests/conformance/` | catalogue |
| `test_shared_libs_projection.py` | `RealTreeInvariantTests.test_shim_source_retained_in_source_pack` | pack: credential-brokers | Names and asserts one pack's retained content. | `packs/credential-brokers/tests/` | pack |
| `test_shared_libs_projection.py` | `RealTreeInvariantTests.test_collect_sources_finds_source_pack` | engine | Invokes the engine collector; live tree is input. | stay; fixture-back | sdist |
| `test_shared_prefix_contract.py` | all classes | engine | Engine shared-prefix contract and mirror. | stay | sdist |
| `test_shipped_packs_v07_declarations.py` | all classes | catalogue roster-shaped | Pins hardcoded pack groups and declarations. | `tests/roster/` | never |
| `test_shipped_packs_v08_declarations.py` | `TestShippedPacksDeclareV08` | catalogue roster-shaped | Pins `V08_PACKS` and equality to this repository's roster. | `tests/roster/` | never |
| `test_user_libs_projection.py` | `UserLibsProjectionTests` | engine | Projection primitive over a synthetic tree. | stay | sdist |
| `test_user_libs_projection.py` | `UserLibsRealRepoTests.test_real_repo_targets_match_package_source` | pack: credential-brokers | Pins one pack copy against package source. | `packs/credential-brokers/tests/` | pack |
| `test_user_libs_projection.py` | `UserLibsRealRepoTests.test_vendored_floor_base_import_is_third_party_free` | engine | Vendored-floor runtime behaviour. | stay | sdist |
| `test_validate.py` | all classes | engine | Engine validator and CLI behaviour. | stay | sdist |
| `test_workspace_status_projection.py` | all classes | pack: core | Pins core's `workspace-status` primitive and installed behaviour. | `packs/core/tests/` | pack |
| `test_writers_emit_lf.py` | all classes | engine | Engine source and writer behaviour. | stay | sdist |

### Complete class inventory for all-class rows

- `test_adapter_claude_code.py`: `ClaudeCodeAdapterTests`, `ProjectPacksTests`,
  `TestClaudeCodeOrphanSweep`.
- `test_adapter_codex.py`: `CodexAdapterTests`, `TestDirectDirectoryProjection`,
  `TestCodexOrphanSweep`, `TestMigrationStripIntegrated`,
  `TestMigrationStripPureFunction`, `TestCodexProjectsEveryShippedSkill`.
- `test_adapter_copilot.py`: `CopilotAdapterTests`.
- `test_adapter_cursor.py`: `CursorContractTests`, `CursorProjectionTests`,
  `CursorInstallDispatchTests`, `ContractVersionAtLeastTests`,
  `CursorSelfHostTests`.
- `test_adapter_kiro.py`: `KiroAdapterTests`, `ProjectPacksTests`,
  `TestKiroOrphanSweep`.
- `test_adapter_root_bins_projection.py`: `AdapterRootBinsTests`,
  `AdapterRootBinsShimCompanionTests`, `CollectPackRootBinsTests`.
- `test_contract.py`: `ContractSchemaValidationTests`, `AllPairsEnumeratedTests`,
  `ModeEnumTests`, `OnConflictTests`, `SourcePathTests`,
  `CommandProjectionTests`, `FrontmatterTableTests`, `ContractV05Tests`,
  `TestCodexSkillDirectDirectory` (subject to the named method split above).
- `test_contract_scope.py`: `ContractVersionTests`,
  `ClaudeCodeScopeBlockTests`, `OtherAdaptersOmitScopeTests`,
  `AllowedPrefixesRejectionTests`, `StdlibValidatorExtensionsTests`.
- `test_direct_directory_cleanup.py`: `test_removes_orphan_directory`,
  `test_noop_on_full_match`, `test_noop_on_missing_target`,
  `test_ignores_root_files`, `test_symlink_safe_sweep`.
- `test_end_to_end_build.py`: `EndToEndBuildTests`, `CheckCommandTests`,
  `ScaffoldCommandTests`.
- `test_lint_packs.py`: `LintPackTests`, `LintPackVocabTests`.
- `test_pack_schema.py`: `PackSchemaAcceptsValidExamplesTests`,
  `PackSchemaRejectsInvalidExamplesTests`, `PackSchemaEnrichedMetadataTests`,
  `PackSchemaLayoutTests`, `PackSchemaLoadsTests`.
- `test_pack_schema_allowed_adapters.py`: `TestSchemaShapeAllowedAdapters`,
  `TestValidateAllowedAdaptersCrossField`, `TestKiroTargetAdaptersV06Gate`.
- `test_pack_schema_install.py`: `V02PackInstallRequiredTests`,
  `V02PackInstallValidTests`, `DefaultInAllowedInvariantTests`,
  `AllowedScopesOmittedTests`, `V01LegacyTests`, `AllowedScopesShapeTests`.
- `test_pipeline.py`: `PerPackClaudePluginTests`, `PerPackApmPackageTests`,
  `MarketplaceAggregateTests`, `PackInternalCollisionTests`,
  `UnknownRecipeTests`, `UnknownAdapterTargetTests`,
  `Rfc0002RecipeLoadTests`, `EmptyPackEdgeCaseTests`.
- `test_plugin_manifest_schema.py` engine classes:
  `PluginManifestSchemaAcceptsValidExamplesTests`,
  `PluginManifestSchemaRejectsInvalidExamplesTests`,
  `PluginManifestSchemaLoadsTests`, `PluginManifestSchemaProjectableSubsetTests`,
  `PluginManifestSchemaSplitTests`.
- `test_projectable_subset.py`: `DeriveProjectableSubsetTests`,
  `ProjectPackReadmeTests`.
- `test_projections_merge_json.py`: `TestProjectMergeJson`,
  `TestClaudeCodeIntegrationStillGreen`.
- `test_scope_rails.py`: `RailASeedsTests`, `RailBHooksTests`,
  `RailCMarkersTests`, `CliValidateSpecNamedStderrTests`,
  `CliValidateWiringTests`.
- `test_security.py`: `PathTraversalGuardTests`, `SymlinkProjectionTests`,
  `PluginManifestValidationTests`.
- `test_self_host_check.py`: `DryRunCleanTreeTests`, `DirtyTreeRefusalTests`,
  `MarkerResolutionTests`, `WorkingTreeOnConflictTests`,
  `SelfHostAdapterAllowListTests`, `SelfHostCodexProjectionTests`,
  `AgentsMdCompositionTests`, `SelfHostPackFilterTests`, `ExcludedGlobTests`,
  `ExclusionIsHonouredOnDiskTests`, `SeedProjectionTests`,
  `MarketplaceAggregationTests`, `ClaudeSymlinkTests`,
  `ClaudeSymlinkFallbackTests`, `MissingDiscoveryFailFastTests`,
  `DriftSourceNamingTests`, `InfoLineUnclassifiedTests`,
  `ForwardFlowIntegrationTests`, `DirtyTreeStderrMessageTests`,
  `PlainBuildCopiesMarkerThroughTests`, `CrlfNormalisationTests`,
  `FileModeBitsTests`, `SymlinkTargetTests`,
  `StrengthenedDiffRegressionIntegrationTests`, `ClaudeMdEquivalenceTests`,
  `RecreateClaudeBridgeInvariantTests`, `SelfHostAdapterRoutingTests`
  (subject to the named method split above).
- `test_self_host_fixture_guard.py`: `RefuseFixturePacksDirTest`,
  `CmdSelfGuardWiringTest`.
- `test_self_host_recipe_config.py`: `ExtractSelfHostListsTest`,
  `LoadSelfHostListsTest`, `ModuleConstantsMatchRecipeTest`.
- `test_shared_libs_projection.py`: `_FixtureBase`, `CollectSourcesTests`,
  `InterPackCollisionTests`, `ProjectionRetirementGuardTests`,
  `RealTreeInvariantTests` (subject to the method splits above).
- `test_shared_prefix_contract.py`: `SharedPrefixRegistryTests`,
  `CohortSkillRoutingTests`, `ContractMirrorTests`.
- `test_shipped_packs_v07_declarations.py`: `TestUserScopePacksV07`,
  `TestRepoOnlyPacksV07`.
- `test_user_libs_projection.py`: `UserLibsProjectionTests`,
  `UserLibsRealRepoTests` (subject to the method splits above).
- `test_validate.py`: `TypeKeywordTests`, `RequiredKeywordTests`,
  `EnumKeywordTests`, `PatternKeywordTests`, `ItemsKeywordTests`,
  `PropertiesAndAdditionalTests`, `SchemaJsonSelfValidationTests`,
  `CliValidateSubcommandTests`.
- `test_workspace_status_projection.py`: `SourceInvariantTests`,
  `AdapterProjectionTests`, `RealTreeProjectionTests`, `EndToEndCLITests`.
- `test_writers_emit_lf.py`: `TextWritersEmitLF`, `WriterEmitsLFBytes`.

## T1a decisions ratified at T1d

1. `contracts/adapter.toml`: engine input and published mirror.
2. `test_architect_design_reviewer_projection.py`: pack: architect.
3. `test_contract_v07.py` and `test_contract_v08.py`: engine. Their
   hardcoded names are adapters in the engine contract, not pack-roster pins.

## T1b — `tests/unit/`

Current root: `packages/agentbundle/tests/unit/`.

- Modules screened: **135/135**.
- Quoted-directory signal: **29/135**.
- Path-form signal: **27/135**.
- Supplemental candidates: **1**.
- Candidate union inspected: **32 modules**. The two primary signals are
  deliberately non-nested: 25 common, four quoted-only, and two path-form-only.

Quoted-directory candidates:

`test_architect_readme_install_command.py`,
`test_catalogue_tooling_foundation.py`, `test_catalogue_wave2_schema.py`,
`test_contract_parity.py`, `test_contract_v0_3_schema.py`,
`test_credbroker_lint_hardening.py`, `test_credential_broker_contract_docs.py`,
`test_credentials_shim_bin_load_degradation.py`,
`test_credentials_shim_load_credentials.py`, `test_credentials_shim_stdlib.py`,
`test_diff_cmd.py`, `test_docs_agentbundle_reference.py`,
`test_enriched_pack_metadata.py`, `test_flow_metrics_upstream_probe.py`,
`test_init_state_cmd.py`, `test_install_first_value_handoff.py`,
`test_install_messages.py`, `test_install_state_provenance.py`,
`test_kiro_ide_hook_schema.py`, `test_list_installed_cmd.py`,
`test_list_installed_status.py`, `test_local_scope_schema.py`,
`test_local_scope_t7_install_gates.py`,
`test_pipeline_phase_order.py`, `test_plugin_install_doc_drift.py`,
`test_render.py`, `test_render_cmd.py`, and `test_shipped_pack_manifests.py`.
The final quoted-only module is
`test_validate_hook_wiring_per_file_compatibility.py`.

Path-form adds `test_catalogue_ci_contract.py` and
`test_catalogue_tooling_verify.py`. Supplemental inspection adds
`test_catalogue_self_hosted_export_removal.py` (marker walk).

The AC1 whole-suite audit also found four non-candidate modules whose
assertions are not engine-owned. They were outside all three catalogue-path
signals but must still leave the sdist: three repository-governance shape
modules are roster-shaped, and the release-check module is tools-owned.

| Module | Test class or module-level group | Owner | Assertion basis | Destination | Ships |
| --- | --- | --- | --- | --- | --- |
| `test_adapt_spec_shape.py` | all module-level tests | catalogue roster-shaped | Pins one repository initiative's acceptance criteria and changelog. | `tests/roster/` | never |
| `test_architect_readme_install_command.py` | `ArchitectReadmeInstallCommandTests`, except the named method below | pack: architect | Pins architect README commands and flag form. | `packs/architect/tests/` | pack |
| `test_architect_readme_install_command.py` | `test_bare_install_pack_name_is_rejected` | engine | Parser rejection independent of README content. | stay | sdist |
| `test_catalogue_ci_contract.py` | all module-level tests | engine | CLI JSON, exit codes, and package layout; live catalogue is input. | stay; fixture-back | sdist |
| `test_catalogue_self_hosted_export_removal.py` | removal, projection, guide tests; `test_write_jail_comment_no_export_catalogue` | pack: catalogue-curation | Pins removal and retained content of one pack. | `packs/catalogue-curation/tests/` | pack |
| `test_catalogue_self_hosted_export_removal.py` | `test_identity_module_present`; `test_identity_module_exports_expected_symbols` | engine | Engine module placement and API. | stay | sdist |
| `test_catalogue_self_hosted_export_removal.py` | `test_lint_guard_does_not_reference_export_catalogue_in_dup_groups` | tools | Asserts `tools/lint-catalogue-curation-guard.py`. | `tools/` | never |
| `test_catalogue_tooling_foundation.py` | all module-level tests | engine | Engine config, result, and CLI behaviour. | stay; fixture-back | sdist |
| `test_catalogue_tooling_verify.py` | all module-level tests | engine | Verifier steps and rendering; live self-host/build trees are inputs. | stay; fixture-back | sdist |
| `test_catalogue_wave2_schema.py` | all module-level tests | engine | Pack-schema validation and bundled-copy parity. | stay; fixture-back | sdist |
| `test_contract_parity.py` | four `*_synced` tests | engine | Published contract to bundled engine-data parity. | stay; fixture-back | sdist |
| `test_contract_parity.py` | `test_check_contract_parity_tool_exits_0` | tools | Directly exercises `tools/catalogue/check_contract_parity.py`. | `tools/` | never |
| `test_contract_v0_3_schema.py` | `ContractVersionTests`; `KiroScopeBlockTests`; `KiroHookWiringTableTests`; `ClaudeCodeHookWiringTableTests`; `HookBodyScopeConditionalTests`; `ScopeConditionalTargetSchemaTests`; `ScopeConditionalModeSchemaTests`; `AgentEventVocabularySchemaTests`; `PackInstallUserScopeHooksTests`; `DualFormDriftTests`; `AdapterBlockCoverageTests`; `BundledCopiesMatchTests` | engine | Adapter schema and contract semantics plus bundled-copy parity. | stay; fixture-back | sdist |
| `test_credbroker_lint_hardening.py` | `TestIsCanonicalShimPathAnchor`; `TestD3CheckDotfileRead` | engine | Engine catalogue-linter behaviour. | stay; fixture-back | sdist |
| `test_credbroker_lint_hardening.py` | `test_load_cli_module_loads_broker` | pack: credential-brokers | Directly imports and asserts the pack-owned broker. | `packs/credential-brokers/tests/` | pack |
| `test_credential_broker_contract_docs.py` | `test_ac43_guide_walks_broker_first` | pack: credential-brokers | Pins that pack's shipped guide. | `packs/credential-brokers/tests/` | pack |
| `test_credential_broker_contract_docs.py` | remaining module-level tests | catalogue roster-shaped | Pins repository ADRs, conventions, backlog, and historical specs. | `tests/roster/` | never |
| `test_credentials_shim_bin_load_degradation.py` | `ShimDocstringRecordsBinLoadDegradationTests`; `ShimBinLoadTier2BackendIsNoneTests` | pack: credential-brokers | Pack-owned shim content and runtime behaviour. | `packs/credential-brokers/tests/` | pack |
| `test_credentials_shim_load_credentials.py` | `_ShimImportBase`; `ShimTier1Tests`; `ShimMissingKeyTests`; `ShimTier3Tests`; `ShimEnvParseSurfaceTests` | pack: credential-brokers | Pack-owned shim contract. | `packs/credential-brokers/tests/` | pack |
| `test_credentials_shim_stdlib.py` | `ShimStdlibOnlySubprocessTests` | pack: credential-brokers | Pack-owned shim dependency floor. | `packs/credential-brokers/tests/` | pack |
| `test_diff_cmd.py` | all module-level tests | engine | Engine diff behaviour; core is projection input. | stay; fixture-back | sdist |
| `test_distribution_adapters_spec_shape.py` | all module-level tests | catalogue roster-shaped | Pins one repository initiative's acceptance criteria and changelog. | `tests/roster/` | never |
| `test_docs_agentbundle_reference.py` | all module-level tests | catalogue roster-shaped | Pins exact shared-guide pages, headings, and links. | `tests/roster/` | never |
| `test_enriched_pack_metadata.py` | `test_at_least_the_known_packs_are_present` | catalogue roster-shaped | Names required packs and a repository roster floor. | `tests/roster/` | never |
| `test_enriched_pack_metadata.py` | `test_pack_declares_enriched_floor`; `test_pack_toml_version_matches_plugin_json` | catalogue rule-shaped | Portable rules over whatever packs exist. | `tests/conformance/` | catalogue |
| `test_flow_metrics_upstream_probe.py` | all module-level tests | pack: atlassian | Directly imports and asserts atlassian flow-metrics code. | `packs/atlassian/tests/` | pack |
| `test_init_state_cmd.py` | all module-level tests | engine | Init-state behaviour; core is input. | stay; fixture-back | sdist |
| `test_install_first_value_handoff.py` | `EmitFirstValueHandoffUnitTests`; `InstallFirstValueHandoffIntegrationTests`; `InstallFirstValueHandoffDualScopeTests` | engine | Install output and scope behaviour; live packs are inputs. | stay; fixture-back | sdist |
| `test_install_messages.py` | `InstallMessageRailTests` | engine | Install message rails; converters is input. | stay; fixture-back | sdist |
| `test_install_state_provenance.py` | `InstallHTTPSProvenanceTests`; `StateReadWithoutProvenanceFieldsTests` | engine | Install and state provenance. | stay; fixture-back | sdist |
| `test_kiro_ide_hook_schema.py` | `IdeVocabularyAcceptanceTests`; `ExistingContractStillValidates` | engine | Validator and schema semantics. | stay; fixture-back | sdist |
| `test_list_installed_cmd.py` | all 21 module-level tests | engine | List-installed status, table, drift, CLI, and degradation behaviour; pack paths are synthetic. | stay | sdist |
| `test_list_installed_status.py` | all 81 module-level tests | engine | Status computation, source resolution, redaction, rendering, filtering, and non-mutation over fixtures. | stay | sdist |
| `test_local_scope_schema.py` | all module-level tests | engine | Schema validation and bundled-copy parity. | stay; fixture-back | sdist |
| `test_local_scope_t7_install_gates.py` | all 8 module-level tests | engine | Install-route flags, local-scope gates, and dependency resolution over temporary catalogues. | stay | sdist |
| `test_manual_qa_matrix_shape.py` | all module-level tests | catalogue roster-shaped | Pins a repository-specific manual-QA ledger. | `tests/roster/` | never |
| `test_pipeline_phase_order.py` | `PhaseOrderExecutionTests`; `KiroHookWiringMergeDuringBuildTests`; `CrossAdapterIndependenceTests` | engine | Adapter pipeline order and isolation over synthetic packs. | stay | sdist |
| `test_plugin_install_doc_drift.py` | `test_product_engineering_readme_uses_marketplace_qualifier` | pack: product-engineering | Pins one pack README. | `packs/product-engineering/tests/` | pack |
| `test_plugin_install_doc_drift.py` | `test_architect_readme_uses_marketplace_qualifier` | pack: architect | Pins one pack README. | `packs/architect/tests/` | pack |
| `test_plugin_install_doc_drift.py` | site-install and root-README tests | catalogue roster-shaped | Pins repository-specific cross-catalogue documentation. | `tests/roster/` | never |
| `test_render.py` | all module-level tests | engine | Render API and build parity; core is input. | stay; fixture-back | sdist |
| `test_render_cmd.py` | all module-level tests | engine | Render CLI, path jail, and build parity. | stay; fixture-back | sdist |
| `test_release_check.py` | all module-level tests | tools | Directly executes `tools/repo/release_check.sh`. | `tools/` | never |
| `test_shipped_pack_manifests.py` | all module-level tests | catalogue roster-shaped | Hardcodes this repository's pack groups, ranges, versions, scopes, and seed absences. | `tests/roster/` | never |
| `test_validate_hook_wiring_per_file_compatibility.py` | all module-level tests | engine | Validator compatibility and error behaviour; live core is input. | stay; fixture-back | sdist |

### T1b decisions ratified at T1d

1. The global `contracts/` decision controls the starred engine rows. They move
   together if the contract is declared catalogue content.
2. Repository governance and shared-documentation shape tests are provisionally
   catalogue roster-shaped because they pin this repository and are not
   portable. The taxonomy has no separate documentation owner.
3. `ArchitectReadmeInstallCommandTests` has a method-level split; moving the
   entire class would misplace an engine parser assertion.
4. `test_catalogue_self_hosted_export_removal.py` has pack, engine, and tools
   assertions despite presenting as one removal regression.

## T1c — `tests/integration/`

Current root: `packages/agentbundle/tests/integration/`.

- Modules screened: **71/71**.
- Quoted-directory signal: **24/71**.
- Path-form signal: **40/71**; the quoted set is a subset.
- Supplemental candidates: **1**.
- Marker-walking candidates: **0**.
- Candidate union inspected: **41 modules**.

Quoted-directory candidates:

`test_apm_install_route.py`, `test_build_check_drift_gates.py`,
`test_build_derivation_claude_plugins.py`, `test_credbroker_floor_precedence.py`,
`test_credential_brokers_pack_install.py`,
`test_credential_user_scope_invocation.py`, `test_editable_source_detection.py`,
`test_install_adapt_chain.py`, `test_install_cmd.py`,
`test_install_converters_user_scope.py`, `test_install_core_smoke.py`,
`test_install_default_source.py`, `test_install_dropped_primitives_warning.py`,
`test_install_repo_scope_per_adapter.py`, `test_install_research_user_scope.py`,
`test_install_seed_delivery.py`, `test_install_snapshot.py`,
`test_install_upgrade_offer.py`, `test_install_user_scope_allowed_adapters.py`,
`test_kiro_ide_hook_e2e.py`, `test_marketplace_entry_validation.py`,
`test_marketplace_manifest_regression.py`, `test_multi_pack_install.py`, and
`test_shared_prefix_coexistence.py`.

Path-form additionally selects `test_apm_spec_amendments.py`,
`test_build_derivation_apm.py`, `test_cc_user_hooks_fixture.py`,
`test_fixtures_validate.py`, `test_install_copilot_full_parity.py`,
`test_install_profile_live.py`, `test_install_user_hooks.py`,
`test_kiro_repo_hooks_fixture.py`, `test_kiro_user_hooks_fixture.py`,
`test_reconcile.py`, `test_scaffold_projection.py`, `test_show_cmd.py`,
`test_uninstall_user_hooks.py`, `test_upgrade_attach_to_agent.py`,
`test_upgrade_cmd.py`, and `test_upgrade_user_hooks.py`.

Supplemental inspection adds `test_install_orphan_reshape.py`, which passes the
indexed repository root wholesale as a live catalogue and therefore composes no
catalogue path in the module itself.

| Module | Test class or module-level group | Owner | Assertion basis | Destination | Ships |
| --- | --- | --- | --- | --- | --- |
| `test_apm_install_route.py` | all except the named method below | engine | APM writer, scope, dispatch, and marker behaviour. | stay; fixture-back | sdist |
| `test_apm_install_route.py` | `test_apm_writer_to_reader_integration_journey` | pack: core | Loads core's private session-start reader and asserts it against engine output. | `packs/core/tests/` | pack |
| `test_apm_spec_amendments.py` | tests through `test_manual_qa_matrix_apm_rows_carry_verification_transcript` | catalogue roster-shaped | Pins historical specs and the repository QA ledger. | `tests/roster/` | never |
| `test_apm_spec_amendments.py` | four `test_core_readme_*` tests | pack: core | Pins one pack README and target roster. | `packs/core/tests/` | pack |
| `test_build_check_drift_gates.py` | all module-level tests | engine | Exercises engine drift gates; live packs are inputs. | stay; fixture-back | sdist |
| `test_build_derivation_apm.py` | all module-level tests | engine | APM build projection over package fixtures. | stay | sdist |
| `test_build_derivation_claude_plugins.py` | all module-level tests | engine | Claude-plugin build derivation and validation. | stay; fixture-back | sdist |
| `test_cc_user_hooks_fixture.py` | `CCUserHooksFixtureTests` | engine | Engine-owned package fixture validation. | stay | sdist |
| `test_credbroker_floor_precedence.py` | `test_floor_appended_lowest_precedence_never_inserted` | catalogue roster-shaped | Hardcodes a six-entry cross-pack consumer roster. | `tests/roster/` | never |
| `test_credbroker_floor_precedence.py` | `test_setup_floor_is_lowest_precedence` | pack: credential-brokers | Credential-setup behaviour within that pack. | `packs/credential-brokers/tests/` | pack |
| `test_credential_brokers_pack_install.py` | `PackManifestShapeTests`; `PackDirectoryInvariantTests`; `PackInstallTests` | pack: credential-brokers | Pins that pack's manifest, directory shape, and installability. | `packs/credential-brokers/tests/` | pack |
| `test_credential_brokers_pack_install.py` | `SeedsRefusalRailTests`; `UserScopeFloorDeliveryTests.test_lib_no_exec_bit_and_bin_is_0755`; `.test_delivery_stays_under_agentbundle_jail`; `.test_refuses_group_world_writable_floor`; `.test_symlinked_pack_content_is_not_delivered` | engine | Install scope, mode, confinement, and symlink rails. | stay; fixture-back | sdist |
| `test_credential_brokers_pack_install.py` | `UserScopeFloorDeliveryTests.test_floor_lib_bin_and_companion_land`; `.test_setup_py_resolves_credbroker_from_floor` | pack: credential-brokers | Pins exact pack artifacts and own consumer behaviour. | `packs/credential-brokers/tests/` | pack |
| `test_credential_brokers_pack_install.py` | `UserScopeFloorDeliveryTests.test_api_cli_resolves_credbroker_from_floor` | catalogue roster-shaped | Cross-pack credential-brokers to atlassian integration. | `tests/roster/` | never |
| `test_credential_user_scope_invocation.py` | `test_entry_point_imports_resolve_under_user_scope_layout` | catalogue roster-shaped | Pins six entry points across three named packs. | `tests/roster/` | never |
| `test_credential_user_scope_invocation.py` | `test_sso_broker_tier2_backend_loads_under_user_scope_layout` | pack: credential-brokers | Pack broker/backend runtime layout. | `packs/credential-brokers/tests/` | pack |
| `test_editable_source_detection.py` | all module-level tests | engine | Editable-source discovery; clone markers are inputs. | stay; fixture-back | sdist |
| `test_fixtures_validate.py` | `FixturePresenceTests`; `WellFormedFixturesValidateTests`; `MalformedFixturesRefusedTests`; `PascalEventsRefusedByT6Tests`; `FixtureIsolationTests` | engine | Engine package fixtures and validator behaviour. | stay | sdist |
| `test_install_adapt_chain.py` | all module-level tests | engine | Install/adapt chaining and markers; core is input. | stay; fixture-back | sdist |
| `test_install_cmd.py` | all module-level tests | engine | Install behaviour; live core seeds are inputs. | stay; fixture-back | sdist |
| `test_install_converters_user_scope.py` | `ConvertersUserScopeInstallTests` | engine | User-scope install; converters is input. | stay; fixture-back | sdist |
| `test_install_copilot_full_parity.py` | `CopilotRepoScopeCoreTests`; `CopilotUserScopeResearchTests`; `CopilotUserScopeSyntheticHookPackTests` | engine | Copilot projection; live packs are inputs. | stay; fixture-back | sdist |
| `test_install_core_smoke.py` | all module-level tests | engine | Engine install wiring using core as input. | stay; fixture-back | sdist |
| `test_install_default_source.py` | all module-level tests | engine | Default-source resolution and handoff. | stay; fixture-back | sdist |
| `test_install_dropped_primitives_warning.py` | all eight classes | engine | Dropped-primitive warning behaviour by adapter. | stay; fixture-back | sdist |
| `test_install_orphan_reshape.py` | all module-level tests | engine | Install orphan and refusal behaviour; repository root is input. | stay; fixture-back | sdist |
| `test_install_profile_live.py` | all module-level tests | engine | Profile install behaviour against a live catalogue. | stay; fixture-back | sdist |
| `test_install_repo_scope_per_adapter.py` | all seven classes | engine | Repo-scope install, upgrade, diff, and migration. | stay; fixture-back | sdist |
| `test_install_research_user_scope.py` | `ResearchUserScopeInstallTests` | engine | User-scope install; research is input. | stay; fixture-back | sdist |
| `test_install_seed_delivery.py` | all module-level tests | engine | Seed delivery, state, collision, and marker behaviour. | stay; fixture-back | sdist |
| `test_install_snapshot.py` | `test_first_install_snapshot` | catalogue roster-shaped | Pins three packs and exact projected-path golden rosters. | `tests/roster/` | never |
| `test_install_upgrade_offer.py` | all module-level tests | engine | Upgrade-offer and handoff behaviour. | stay; fixture-back | sdist |
| `test_install_user_hooks.py` | all seven classes | engine | User-hook install, merge, path, and refusal behaviour. | stay | sdist |
| `test_install_user_scope_allowed_adapters.py` | `AllowedAdaptersInstallTests` | engine | Adapter-allowance install behaviour. | stay; fixture-back | sdist |
| `test_kiro_ide_hook_e2e.py` | `KiroAdapterDispatchesKiroIdeHook`; `ValidateCommandRailFires` | engine | Kiro adapter and validator behaviour. | stay; fixture-back | sdist |
| `test_kiro_repo_hooks_fixture.py` | `KiroRepoHooksFixtureTests` | engine | Engine-owned fixture shape. | stay | sdist |
| `test_kiro_user_hooks_fixture.py` | `KiroUserHooksFixtureTests` | engine | Engine-owned fixture shape. | stay | sdist |
| `test_marketplace_entry_validation.py` | `test_root_marketplace_entries_validate` | catalogue rule-shaped | Portable entry-schema validation over any root marketplace. | `tests/conformance/` | catalogue |
| `test_marketplace_entry_validation.py` | remaining module-level tests | engine | Validator, schema, aggregation, and build-gate behaviour. | stay; fixture-back | sdist |
| `test_marketplace_manifest_regression.py` | `TestDeriveProjectableSubsetAuthor`; `TestDeriveProjectableSubsetSource`; `TestRunAggregateMarketplaceName` | engine | Metadata derivation and aggregate build output. | stay; fixture-back | sdist |
| `test_marketplace_manifest_regression.py` | `TestSelfHostMarketplace.test_has_name_field`; `.test_has_owner_field`; `.test_every_plugin_has_object_author`; `.test_every_source_is_valid_object` | catalogue rule-shaped | Portable catalogue-marketplace shape checks. | `tests/conformance/` | catalogue |
| `test_marketplace_manifest_regression.py` | `TestSelfHostMarketplace.test_name_is_agent_ready_repo`; `.test_every_plugin_has_source` | catalogue roster-shaped | Pins repository identity and a stronger local source policy. | `tests/roster/` | never |
| `test_multi_pack_install.py` | all module-level tests | engine | Multi-pack dependency, state, reinstall, and orphan behaviour. | stay; fixture-back | sdist |
| `test_reconcile.py` | all seven classes | engine | Reconciliation over engine fixtures. | stay | sdist |
| `test_scaffold_projection.py` | `test_projection_byte_identical_to_repo_root` | tools | Asserts the sync tool's pair list and source-to-copy synchronization. | `tools/` | never |
| `test_scaffold_projection.py` | remaining module-level tests | engine | Bundled scaffold package data and materialisation. | stay; fixture-back | sdist |
| `test_shared_prefix_coexistence.py` | all four classes | engine | Shared-prefix install and coexistence behaviour. | stay; fixture-back | sdist |
| `test_show_cmd.py` | all module-level tests | engine | Show, render, and degraded-state behaviour. | stay; fixture-back | sdist |
| `test_uninstall_user_hooks.py` | all five classes | engine | User-hook uninstall and migration. | stay | sdist |
| `test_upgrade_attach_to_agent.py` | `AttachToAgentRenameTests` | engine | Upgrade rename and attach behaviour. | stay | sdist |
| `test_upgrade_cmd.py` | all module-level tests | engine | Upgrade, dry-run, collision, and recap behaviour. | stay; fixture-back | sdist |
| `test_upgrade_user_hooks.py` | all six classes | engine | User-hook upgrade and migration. | stay | sdist |

### T1c decisions ratified at T1d

1. The global `contracts/adapter.toml` decision affects
   `test_kiro_ide_hook_e2e.py` and contract-backed portions of
   `test_marketplace_entry_validation.py`.
2. `test_apm_writer_to_reader_integration_journey` combines an engine writer
   with a private core reader. Proposed owner: core.
3. Credential-broker modules contain engine rails, one-pack behaviour, and
   cross-pack integrations; whole-module moves would be incorrect.
4. `test_scaffold_projection.py::test_projection_byte_identical_to_repo_root`
   is tools-owned because it asserts synchronization-tool behaviour.
5. `test_install_snapshot.py` remains roster-shaped despite invoking engine
   code because its assertions are exact named-pack golden rosters.
6. `TestSelfHostMarketplace.test_every_plugin_has_source` is roster-shaped:
   the portable entry contract permits missing `source`.

## T1d — loose `packages/agentbundle/tests/test*.py` modules

All **8/8** loose modules are included regardless of either nested-root search
signal.

| Module | Test class or module-level group | Owner | Assertion basis | Destination | Ships |
| --- | --- | --- | --- | --- | --- |
| `test_adapter_permissions_projection.py` | `TestPermissionsAllowProjection` | engine | Deferred projection assertions against the engine installer. | stay | sdist |
| `test_linear_primitive.py` | `TestGetProjectMaxPages`; `TestRetryAfterOn429` | pack: linear | Directly loads and asserts Linear's pack-owned primitive. | `packs/linear/tests/` | pack |
| `test_workspace_mcp_elicit.py` | `TestElicitViaMCP`; `TestElicitResponseFile`; `TestElicitCapabilityNegotiation` | engine | Workspace MCP elicitation and response-file behaviour. | stay | sdist |
| `test_workspace_mcp_event_bridge.py` | `TestEventBridgePoll`; `TestEventBridgeInodeReset`; `TestEventBridgeStop` | engine | Workspace MCP event bridge behaviour. | stay | sdist |
| `test_workspace_mcp_git.py` | `TestGitBranch`; `TestGitCommit`; `TestGitPush` | engine | Workspace MCP Git-tool behaviour. | stay | sdist |
| `test_workspace_mcp_lifecycle.py` | `TestLifecycleManifest`; `TestDefaultSessionInstruction` | engine | Workspace MCP lifecycle manifest and session contract. | stay | sdist |
| `test_workspace_mcp_stdin.py` | `TestFrameSizeCap`; `TestMalformedJSON`; `TestUnknownRequestId`; `TestInitializeHandshake`; `TestStdinClose`; `TestModuleEntryPoint` | engine | Workspace MCP stdio protocol and module entry point. | stay | sdist |
| `test_workspace_mcp_tools.py` | `TestWorkspaceStatusSlugSafety`; `TestPackPresenceFilter`; `TestFSMStateMerge` | engine | Workspace MCP status-tool safety and state merge. | stay | sdist |

## Consolidated decisions ratified at T1d

The human approved all seven dispositions on 2026-08-09 before relocation.

1. Treat `contracts/adapter.toml` as **engine input and published mirror**, not
   catalogue content. Its tests assert the engine's adapter contract and bundled
   parity; every affected row is engine-owned.
2. Move `test_architect_design_reviewer_projection.py` to **pack: architect**.
3. Keep `test_contract_v07.py` and `test_contract_v08.py` **engine-owned**; their
   hardcoded roster is adapters in the engine contract, not packs.
4. Treat repository governance/shared-documentation shape tests as
   **catalogue roster-shaped** because they pin this repository and cannot ship
   portably.
5. Move `test_apm_writer_to_reader_integration_journey` to **pack: core**; its
   load-bearing reader is a private core primitive.
6. Treat the credential-brokers to atlassian API/CLI floor assertion as
   **catalogue roster-shaped** because it pins a named cross-pack integration.
7. Move `test_scaffold_projection.py::test_projection_byte_identical_to_repo_root`
   to **tools** because it asserts the synchronization tool's `_SYNC_PAIRS`
   contract rather than bundled runtime materialisation.

## Completeness status

- Build pipeline: 44/44 modules read; quoted/path signals 29/36; one
  supplemental marker-walk candidate recorded.
- Unit: 135/135 screened; quoted/path signals 29/27; one supplemental
  marker-walk candidate recorded. The non-nested union contains 32 modules.
- Integration: 71/71 screened; quoted/path signals 24/40; one supplemental
  wholesale-root candidate recorded.
- Loose root: 8/8 modules read regardless of search signal.
- Across the three nested roots, the quoted-directory signal totals **82** and
  the path-form signal totals **103**, reproducing RFC-0082 from current paths.
- Every contested row has a ratified disposition; ownership-controlled movement
  may begin.
- The later AC1 whole-suite audit classified four non-candidate modules that
  were invisible to the catalogue-path searches; their destinations follow the
  already-ratified governance/tools rules above.
