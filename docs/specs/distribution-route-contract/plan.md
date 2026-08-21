# Plan: Distribution route contract

- **Spec:** [`spec.md`](spec.md)
- **Status:** Approved

> **Plan contract:** this is the implementation strategy. Unlike the spec, this
> document is allowed to change as implementation evidence arrives. A substantial
> approach change is recorded in the changelog below.

## Approach

First freeze the current APM and Claude plugin derivations as complete deterministic
golden trees. Then add the canonical route TOML/schema and recipe route identity,
with failing parser/resolver tests before production dispatch changes. Migrate APM
and Claude selection behind one deliberately small resolver while retaining their
named writers, remove route-only fields from the adapter contract, and prove the
same golden trees still result. Finish by synchronizing bundled contracts,
architecture and release records, then run the package and repository gates. The
riskiest part is preserving behavior currently spread across the APM bypass and
Claude recipe-name checks; full-tree characterization makes that risk observable.

## Constraints

- RFC-0092 and ADR-0090 fix the route/adapter separation, the six contract
  concerns, the named minimal resolver, and the Phase 2 registry deferral.
- The Ready programme brief fixes Phase 0 as a zero-output-change slice and keeps
  direct `agentbundle install` separate from package routes.
- `contracts/` is the authored public source; every TOML/schema has a
  byte-identical packaged copy and an inventory entry.
- `packages/agentbundle` remains standard-library-only. Package code changes use
  the `Engine-Change-RFC: RFC-0092` commit footer.
- Git references are read-only in this enterprise session. Implementation can
  edit and verify the worktree but cannot stage, commit, tag, or publish here.
- Base-freshness checking is skipped because its current implementation mutates a
  remote-tracking ref, which this environment forbids.

## Construction tests

**Integration tests:** a new route-contract test module validates the canonical
and bundled route files; a route-resolution test module exercises recipe-to-projector
selection; the existing pipeline/end-to-end modules carry full-tree golden comparisons.

**Manual verification:** run the normal local catalogue build twice in an approved
temporary output root, compare both existing route trees to the checked-in golden
manifests, and record the emitted top-level directory set. No external client run is
needed because the emitted packages are byte-identical.

## Design (LLD)

### Design decisions

- Treat the route contract and route resolver as separate things. Phase 0 adds a
  closed data contract plus a two-entry named dispatch map, not registration or a
  generic build engine. Traces to AC1, AC4, AC12 and both route contracts.
- Keep direct CLI install outside the distribution-route set. Its marker identity
  remains a lifecycle input, not a package route. Traces to AC7.
- Capture full output trees before moving ownership. Characterization fixtures are
  the oracle for the no-output-change promise. Traces to AC8.
- Remove the old adapter fields in the same slice; dual ownership without a proven
  external consumer would leave the architectural defect in place. A discovered
  external consumer invokes the spec's Ask-first alias path. Traces to AC2.
- Use a minor AgentBundle version because the package gains two published contract
  files and a new recipe field, even though observable build output is stable.
  Traces to AC10-AC11.

### Data & schema

`contracts/distribution-routes.toml` has contract metadata and closed
`[route.apm]` / `[route.claude-plugins]` declarations. Each declaration contains
the six semantic concerns named in AC1. `component-capabilities` is exhaustive over
the spec's exact current-output nine-primitive matrix. APM is native for all
nine; Claude is native for its five emitted primitives and drops the remaining
four. Projector and lifecycle values are closed
enums including an explicit `none`; absent or `unknown` values are invalid for
these two implemented routes. `manifest-projector` contains the named writer,
optional adapter projector, and closed admission policy (`all-packs` or
`user-publishable-with-consent`), so adapter permission and route membership do
not become seventh top-level concerns. The sibling JSON Schema rejects extra properties. Canonical
and packaged bytes are identical. Traces to AC1, AC9, AC10.

### Interfaces & contracts

`Recipe.route` is the build-facing interface. For a distribution recipe,
the resolver combines the recipe, route declaration, and optional adapter name into
a resolved descriptor containing the named package projector and optional runtime
adapter projector. It validates identity and consistency before output allocation.
The adapter contract remains the sole direct-install projection interface. Traces
to AC2-AC7; implements both route contract files.

### Component / module decomposition

- `contracts/distribution-routes.*` owns route data and schema.
- `packages/agentbundle/agentbundle/build/recipes/*.toml` declares route identity.
- `Recipe`, `_parse_recipe_text`, and a small resolver in
  `packages/agentbundle/agentbundle/build/main.py` parse and resolve route identity.
- Existing `_run_per_pack_apm` and Claude per-pack code remain named projectors;
  their selection inputs change, not their emitted content.
- `tools/catalogue/check_contract_parity.py` and
  `sync_contract_inventory.py` continue to enforce packaging parity without a new
  source list.

### State & control flow

The build loads and validates the adapter and route contracts, parses a recipe,
resolves its explicit route, verifies any adapter relationship, and only then
creates output. `apm` selects the APM writer; `claude-plugins` selects the Claude
projector plus the `claude-code` adapter projector. Aggregate marketplace behavior
uses the same explicit Claude route identity. Unknown/inconsistent state stops
before filesystem mutation. Traces to AC3-AC6, AC9.

### Behavior & rules

Route declarations own package layout, route component modes, marketplace choice,
and lifecycle-trigger identity. Adapter declarations own direct runtime target
paths and modes. Code never rewrites adapter contract rows for package use. Route
membership and consent behavior retain the existing Claude predicates; APM retains
its existing all-pack behavior. Traces to AC2, AC5-AC8.

### Failure, edge cases & resilience

Schema errors identify the contract path and validation location. Resolver errors
identify recipe, route, and inconsistent field. All validation precedes cleanup or
directory creation, so a malformed recipe cannot delete a prior good build. Golden
comparisons distinguish missing, added, byte-different, link-different, and
mode-different entries. Traces to AC8-AC9.

### Quality attributes (NFRs)

The build remains deterministic, offline, standard-library-only, and confined to
the caller-selected output root. Full-tree byte parity is the compatibility bar;
closed schemas and early refusal are the maintainability and safety bars. No extra
runtime network, dependency, daemon, or telemetry is introduced. Traces to
AC8-AC13.

### Dependencies & integration

No external dependency or service is added. The change integrates with existing
JSON-Schema validation, recipe loading, route writers, contract inventory/parity,
catalogue build gates, and AgentBundle release records. Traces to AC10-AC13.

## Tasks

### T1: Current APM and Claude route outputs have complete golden oracles

**Depends on:** none

**Verification mode:** TDD for the inventory comparator; goal-based integration
for characterizing the current route trees.

**Construction-test artifact:**
`packages/agentbundle/tests/build_pipeline/test_distribution_route_golden.py`.

**Tests:**
- `test_golden_oracle_declares_both_route_trees` — requires a checked-in,
  lossless APM and Claude route oracle whose entries carry exact type, mode, and
  file bytes or link target; requires every AC8 surface and the repo-only
  inclusion/exclusion witness (AC8, AC14).
  `stub: true`
- `test_golden_oracle_preserves_safe_links_without_dereference` — requires the
  lossless oracle to record the same relative source link as a link on both
  routes, never as target bytes (AC14). `stub: true`

- Add a fixture-tree inventory helper/test that compares relative paths, entry
  type, regular-file bytes, symlink target, and permission mode.
- Build a representative publishable fixture pack and repo-only fixture pack with
  the unmodified implementation; assert the baseline includes every surface named
  in AC8 and the expected Claude exclusion.
- Run the same baseline twice and assert identical inventories.

**Approach:**
- Extend `packages/agentbundle/tests/build_pipeline/test_end_to_end_build.py` or a
  focused sibling with deterministic fixture packs.
- Check in the small expected trees or a lossless manifest plus file payloads under
  `packages/agentbundle/tests/fixtures/distribution-routes/`; never derive expected
  bytes from the post-migration implementation.

**Done when:** the current implementation passes a complete, mutation-sensitive
golden comparison for both routes and a deliberate byte/mode/link mutation fails.

### T2: The route contract and recipe route identity are validated public data

**Depends on:** T1

**Verification mode:** TDD.

**Construction-test artifacts:**
`packages/agentbundle/tests/build_pipeline/test_distribution_route_contract.py`
and the recipe cases in
`packages/agentbundle/tests/build_pipeline/test_pipeline.py`.

**Tests:**
- `test_route_contract_declares_exact_phase_zero_routes` — requires the bundled
  route contract, closed schema validation, exact six-concern route objects,
  exhaustive nine-primitive capability objects, and the complete status matrix
  (AC1). `stub: true`
- `test_default_distribution_recipes_declare_explicit_routes` — requires the
  three default distribution recipes to expose their route identity (AC3).
  `stub: true`
- `test_non_distribution_recipe_rejects_route_only_fields` — requires overlay,
  composite, and self-host parsing to stay route-less and reject an injected
  route field (AC3, AC9). `stub: true`
- Start `test_distribution_route_contract.py` with failing tests for the exact two
  routes, six required concerns, exhaustive primitive maps, closed status/projector
  enums, extra-property refusal, and canonical/bundled parity.
- Add failing recipe tests for required `route`, unknown route, and route-only
  fields on a non-route recipe; add positive tests for route-less overlay,
  composite, and self-host recipes; assert the exact route values in both bundled
  per-pack recipes and `marketplace.toml`.
- Add public-contract inventory and README table assertions.

**Approach:**
- Author `contracts/distribution-routes.toml` and
  `contracts/distribution-routes.schema.json`, then copy them byte-identically to
  `packages/agentbundle/agentbundle/_data/` and regenerate
  `public-contracts.txt` with the existing inventory tool.
- Add `route` to `Recipe` / `_parse_recipe_text` and to
  `per-pack-apm-package.toml`, `per-pack-claude-plugin.toml`, and
  `marketplace.toml`.
- Update `contracts/README.md` with authority and governance links.

**Done when:** the new public contract validates, malformed variants fail, packaged
parity passes, and recipe parsing exposes explicit route identity without changing
emitted output.

### T3: One fail-closed resolver selects only the two named route projectors

**Depends on:** T2

**Verification mode:** TDD.

**Construction-test artifact:**
`packages/agentbundle/tests/build_pipeline/test_distribution_route_resolution.py`.

**Tests:**
- `test_resolver_selects_only_named_phase_zero_routes` — requires the typed
  route resolver surface and both named route results, including their exact
  projector identities (AC4, AC9). `stub: true`
- `test_resolver_rejects_admission_policy_projector_conflict` — requires a
  Claude route whose admission policy conflicts with its named projector to
  fail with route/admission context (AC9). `stub: true`
- `test_route_layout_refuses_traversal_and_absolute_paths_before_output` —
  requires route/recipe layout mismatch to fail before creating the output root
  for both traversal and absolute values (AC14). `stub: true`
- `test_route_output_refuses_symlink_parent_escape` — requires a valid route
  build to refuse a pre-existing output-layout symlink that resolves outside the
  caller-selected root without touching the external target (AC14). `stub: true`
- Add failing tests for missing/unknown projector, APM with a fabricated adapter,
  Claude without `claude-code`, route/recipe identity mismatch, layout,
  admission-policy, and lifecycle mismatch, and validation before output
  mutation.
- Add positive tests that resolve APM to the existing APM writer and Claude to the
  existing Claude writer plus adapter projector.
- Add a structural test proving no generic registration API or output-subdir/name
  inference drives selection.

**Approach:**
- Add a typed resolved-route value and one small resolver beside recipe parsing in
  `build/main.py`; keep the two named projector mappings explicit.
- Load the bundled route contract alongside the adapter contract in build entry
  points and pass the validated declaration through dispatch.
- Do not create `routes/`, a registry class, plugin discovery, or dynamic import.
- Keep build-layer path enforcement on the existing `_assert_under` and
  projection-I/O no-follow rails. The catalogue-tooling `file_safety` helpers
  retain their own catalogue-content boundary; do not fork or bypass them.

**Done when:** route resolution is explicit and fail-closed before writes, while
only the existing two named projector functions are callable.

### T4: APM and Claude package behavior is owned by routes, not adapters

**Depends on:** T3

**Verification mode:** TDD for dispatch/refusal invariants; goal-based integration
for full-tree compatibility.

**Construction-test artifacts:**
`test_distribution_route_contract.py`, `test_distribution_route_resolution.py`,
and `test_distribution_route_golden.py`. The T1-T3 stubs above are reused here;
the post-migration golden comparison is `no stub (goal-based integration)`.

**Tests:**
- `test_apm_route_resolves_without_a_runtime_adapter` — requires the APM
  package writer/layout/marker descriptor to resolve from `route = "apm"` with
  no fabricated adapter (AC5). `stub: true`
- `test_claude_route_resolves_package_and_adapter_projectors` — requires Claude
  package layout, compiled hook-wiring capability, consent admission, marker,
  marketplace, and the optional `claude-code` projector to resolve from the
  route declaration (AC6). `stub: true`
- Rewrite the existing `install-routes` and Claude plugin-field tests to assert
  absence from adapters and exact ownership in the route contract.
- Add focused APM assertions that writer/layout/marker selection comes from route
  resolution and preserves `--install-route apm`.
- Add focused Claude assertions that route layout/capability overrides are applied
  without mutating adapter data and preserve publishability, consent, hook, marker,
  and marketplace behavior.
- Run T1's full-tree golden comparison after each migration.

**Approach:**
- Replace `recipe.adapter == "apm"` with resolved APM-route dispatch and remove the
  fabricated adapter value from the APM recipe.
- Replace Claude recipe-name/adapter inference with resolved route identity; build
  a route-scoped projection input without rewriting adapter contract rows.
- Remove `install-routes`, `plugin-target-path`, and `plugin-mode` from canonical
  and bundled adapter TOML/schema only after both route paths consume the new data.

**Done when:** AC2 and AC5-AC9 pass and both golden trees are unchanged.

### T5: Architecture and release surfaces publish the bounded contract change

**Depends on:** T4

**Verification mode:** goal-based check.

**Construction-test artifact:** no stub (goal-based); exact documentation,
version, changelog, and diff commands are the task checks below.

**Tests:**
- Goal checks find the route/adapter sibling model and six concerns in
  `docs/architecture/reference.md` and the contract index.
- Version tests assert `packages/agentbundle/pyproject.toml` and
  `agentbundle/version.py` agree; changelog tests find the same released version.
- A diff assertion proves no pack/plugin manifest version changed and no new output
  directory or publisher workflow entered the change.

**Approach:**
- Update the architecture reference and any existing route vocabulary section in
  place; do not add a new top-level document.
- Append the approver-signed RFC-0092 P6 erratum that corrects the three
  non-emitted Claude library/binary cells and points to the golden evidence; do
  not use the erratum to add a projection or reopen the route decision.
- Bump AgentBundle from 0.38.6 to 0.39.0 unless current refs contain a later
  release when implementation begins, in which case choose the next available
  minor and update the plan changelog.
- Add matching `packages/agentbundle/CHANGELOG.md` and
  `docs/product/changelog.md` entries; refresh PyPI-facing contract inventory prose
  only if its current claims enumerate public contracts.

**Done when:** public documentation and release metadata describe the new contract,
state zero output change, and introduce no Phase 1/3 behavior.

### T6: Phase 0 passes focused, package, and repository verification

**Depends on:** T5

**Verification mode:** goal-based checks plus manual QA for the twice-built local
catalogue output.

**Construction-test artifact:** no stub (goal-based/manual); the durable manual
record lands at `docs/specs/distribution-route-contract/notes/manual-qa.md`.

**Tests:**
- Run focused route contract, recipe, pipeline, and end-to-end tests first.
- Run `python3 -m pytest packages/agentbundle/tests/ -q` with bytecode/cache writes
  confined or disabled.
- Run contract parity, `make lint-ruff`, `make build-self`, and
  `SKIP_SAST=1 make build-check`; inspect the final worktree diff for generated
  drift and Phase 1/3 leakage.
- Run a normal catalogue build twice in an approved temporary root and record the
  output directory set and golden comparison.
- Run spec-status lint and confirm every AC has evidence before moving lifecycle
  status.

**Approach:**
- Fix only failures attributable to this slice; report unrelated pre-existing gate
  failures with evidence rather than broadening scope.
- Run secure-design review before EXECUTE for recipe/contract deserialization and
  route-derived filesystem paths. After gates, run implementation security review
  against the same boundaries, followed by the required adversarial and quality
  reviews.

**Done when:** AC1-AC14 have durable evidence, required gates are green or an
unrelated failure is explicitly dispositioned, and reviewers report clean.

## Rollout

Ship as one atomic internal migration and AgentBundle minor release. There is no
infrastructure migration, remote publication workflow, data backfill, or external
client sequencing. Rollback reverts the resolver, recipe fields, route contracts,
adapter-contract removal, and version/changelog entries together; golden fixtures
then continue to validate the restored implementation. Nothing is irreversible.
This enterprise session cannot perform commit, tag, or publication actions; those
remain maintainer steps after review on an authorized `main` workflow.

## Risks

- A golden fixture can accidentally omit a route behavior and falsely certify
  parity. The representative surface checklist and mutation tests counter this.
- An unknown external reader may depend on adapter `install-routes`. Discovery
  pauses removal and invokes the ask-first compatibility path.
- Transitional dual ownership can drift if contract and code migrate in separate
  changes. T2-T4 keep each intermediate state tested and the final removal atomic.
- A resolver can quietly become the premature registry. Structural assertions and
  the explicit two-entry mapping keep the abstraction bounded.
- Package version 0.39.0 may be consumed before implementation starts. T5 recomputes
  the next available minor from current refs and records any change.
- Fixture modes or symlinks can vary by platform. The fixture helper records the
  portable executable-bit contract and link targets explicitly rather than relying
  on archive-tool defaults.

## Changelog

- 2026-08-21: Initial Phase 0 plan derived from the Ready distribution-routes
  programme brief and the user's confirmed contract, boundary, and slice choices.
