# Spec: Claude-plugin route — publish only user-capable packs

- **Status:** Draft <!-- Draft | Approved | Implementing | Shipped | Archived -->
- **Owner:** eugenelim
- **Plan:** [`plan.md`](plan.md)
- **Constrained by:** [ADR-0002](../../adr/0002-install-scope-per-pack-default-and-allowance.md) (scope is a per-pack default + allowance), [ADR-0072](../../adr/0072-derived-plugin-manifest-mirrors-upstream-schema.md)
- **Engine RFC:** required before EXECUTE — see AC20.
- **Contract:** `contracts/marketplace-entry.schema.json`
- **Shape:** integration

> **Spec contract:** this document defines what "done" means. The implementing
> PR must match this spec, or update it. Verification must be derivable from it.

## Objective

**The Claude-plugin route is a user-scope distribution channel. It publishes,
and advertises, packs that forbid the only install it offers.** This spec makes
the published set match the declarations, and makes the docs tell the truth.

A Claude plugin's code always lives in the adopter's global cache
(`~/.claude/plugins/cache/<marketplace>/<plugin>/<version>`). `project` and
`local` install scopes record an *enablement pointer* in a repo settings file;
they do not place the plugin in the repo. `claude plugin install` defaults to
`--scope user`. There is no repo-scoped plugin install in the sense agentbundle
means by `repo` — confirmed: `~/.claude.json` carries 53 project entries and
none records plugin enablement.

**Defect 1 — the route publishes packs that forbid user scope.** Seven packs
declare `allowed-scopes = ["repo"]`: `core`, `catalogue-curation`,
`governance-extras`, `iac-terraform`, `monorepo-extras`, `release-engineering`,
`user-guide-diataxis`. Six are on `claude-plugins-dist` today. ADR-0002 defines
`allowed-scopes` as a refusal contract — a scope outside the set "is refused with
stderr naming the pack and the declared set" — and the route installs them at
user scope anyway.

**Defect 2 — the docs and the site advertise it for those packs.**
`README.md:32-35`, the front door, says `claude plugin install core@agent-ready-repo`.
`web/src/pages/packs/[pack].astro` and `web/src/pages/catalogue/index.astro`
build a plugin-install command for **every** pack.

**Defect 3 — membership is decided in four places and has already drifted.**
`catalogue-curation` is listed in the repo-root `.claude-plugin/marketplace.json`
and absent from `origin/claude-plugins-dist`. The repo-root file is what
`claude plugin marketplace add eugenelim/agent-ready-repo` resolves, so an entry
whose `source.path` no longer exists on the branch is a dangling fetch rather
than a clean "not offered".

Pack scopes are **not** changed to make this work. Repo-scoped packs are
repo-scoped deliberately; adopters reach them through the direct adapter.

## Boundaries

### Always do

- Derive the filter from `allowed-scopes`, never from a name list.
- Regenerate projected artifacts with `make build-self`; never hand-edit them.

### Ask first

- **Widening any pack's `allowed-scopes`.** After AC1 that is a decision to
  publish that pack's code to a public marketplace, not a metadata tweak.
- **Adding a Node toolchain to the required `make build-check` job**, if AC8's
  built-output assertion is wired there rather than into the site build.

### Never do

- Change any pack's `default-scope` or `allowed-scopes`.
- Change the APM or direct routes' projections. The two marketplace writers and
  the drift gate's pack set are the self-host changes this spec makes, carved out
  by AC1.
- Add a third-party dependency (`pyproject.toml` `dependencies = []`).

## The derived set

Used by every criterion below. A pack is **publishable** when all hold:

1. it lives at `packs/<slug>/` and its slug does not start with `_` — the
   existing guard at `build/self_host.py:528,550,616`. `_example` is
   user-capable by declaration and excluded by this rule, so a naive
   set-equality assertion fails on day one;
2. it carries `pack.toml` and `.claude-plugin/plugin.json`;
3. its resolved scopes admit `"user"`.

## Acceptance Criteria

- [ ] **AC1 — One predicate, four sites.** A pack reaches
  `dist/claude-plugins/`, the dist `marketplace.json`, the repo-root
  `.claude-plugin/marketplace.json`, and the drift gate's expected set only when
  it is publishable.

  The fourth site is the one the first review round missed:
  `run_build_check_drift_gates` Gate 1 (`build/self_host.py:1376-1414`) builds
  `expected_packs` from every pack carrying `.claude-plugin/plugin.json` and
  hard-fails on a missing derived `install-marker.py` — seven failures in the
  *required* gate. It is production code, not a test, so re-pinning tests does
  not reach it. Gate 1c (APM) and Gate 2 (source-shape) are **not** narrowed:
  both legitimately cover every pack.

  `_aggregate_marketplace` carries a contrary design note ("intentionally ignores
  the pack filter — the catalogue advertises every pack") which this change
  overturns *at the note*. ADR-0072 records that same function as the writer
  missed last time.

- [ ] **AC2 — Scope resolution reuses the existing helper, and its real gate is
  named.** `commands/validate.py:_allowed_scopes` is reused, not re-derived. Its
  actual behaviour — verified by execution — is that it returns `["repo"]`
  whenever `[pack.adapter-contract].version` is absent or `"0.1"`, **ignoring
  `[pack.install]` entirely**. Any fixture that must publish declares the
  contract version *and* the scopes.

- [ ] **AC3 — The predicate is route-keyed on `(recipe.name, recipe.adapter)`**,
  matching `_resolve_contract_for_route`'s existing idiom — not on
  `output_subdir`, which is free text on an operator-supplied `--recipe` file.

  The APM route is already safe by construction: `_run_per_pack` dispatches
  `if recipe.adapter == "apm"` and returns before the claude-plugins loop, so
  keying is belt-and-braces rather than the load-bearing separation the first
  draft claimed. Gate 1c independently checks `dist/apm/<pack>/` for every pack
  and would fail loudly if APM were ever filtered.

- [ ] **AC4 — `_run_aggregate` gains a source-tree handle.** It is
  `_run_aggregate(recipe, output_dir)` today and resolves scope from the
  *projected* `dist/claude-plugins/<pack>/pack.toml`. `make build` has no
  dependency on `clean`, so narrowing a pack's scopes and rebuilding leaves a
  stale dist directory carrying the *old* declaration, which resolves
  user-capable and publishes contrary to current intent. Scope resolution reads
  `packs/<slug>/pack.toml`. `run_recipe` already holds `packs_list`; threading it
  is a signature change and is named as one.

- [ ] **AC5 — Membership is asserted on all three surfaces, both directions.**
  The dist tree, the dist `marketplace.json`, and the repo-root
  `marketplace.json` each equal the derived publishable set exactly. Both
  directions matter: AC6's by-name absences catch a fail-open bug, and only set
  equality catches a fail-*closed* one — most plausibly AC2's absent-contract
  trap — which could truncate or empty the marketplace uncaught.

  Assertions build into `tmp_path`, not against the repo's `dist/`, which is
  gitignored and absent under a plain `pytest` run; an absence assertion against
  a directory that does not exist is green while the feature is broken.

- [ ] **AC6 — The seven excluded packs are asserted by name**, absent from all
  three surfaces. The assertion carries a comment naming it the
  **scope-widening-equals-publication tripwire** — a future engineer must not
  "fix" it by deleting a name.

- [ ] **AC7 — The envelope survives.** `_run_aggregate` derives the dist
  marketplace's `name` and `owner` from the **first** entry carrying a GitHub
  `source.url` — pack-supplied metadata — so a filtered set can silently re-key
  the marketplace to a different owner. Either the envelope identity is read from
  the catalogue/discovery config as the sibling writer does, or the writer
  refuses when surviving entries disagree on `source.url`. `name`, `owner`, and
  `description` are asserted intact.

- [ ] **AC8 — The site gates on user-capability, computed not copied.**
  `web/src/content/packs/*.md` are hand-authored with no generator, and their
  `scope` field is `default-scope`, not `allowed-scopes` — gating on it would
  hide `product-documentation` (`default-scope = "repo"`,
  `allowed-scopes = ["repo","user"]`), which AC1 publishes.

  A user-capability field is added, **required in the Zod schema with no
  default**, so the Astro build fails on omission rather than defaulting to
  advertising the public route. A consistency test iterates the **union** of
  `packs/<slug>/pack.toml` and `web/src/content/packs/<slug>.md`, so a newly
  added pack cannot be skipped. Plus a **built-output** assertion: a repo-only
  pack's rendered page emits no `claude plugin install` command; a user-capable
  pack's does.

- [ ] **AC9 — The checks are wired into the required gate, and proven wired.**
  `make build-check` is `catalogue verify` + `tools/repo/build_gate_chain.py` +
  SAST. **It runs no pytest**, and in `build-check.yml` the make step runs
  *before* pytest is installed. So a pytest-based tripwire cannot simply "hang
  off `make build-check`": AC6's tripwire lands as a `tools/lint-*.py` +
  `tools/test-lint-*.py` pair registered in `build_gate_chain.py`, with the
  `lint-ci-parity` update that requires.

  The verification is **mutation, not a green run**: perturb the data (widen a
  fixture's `allowed-scopes`; desync a `web/` frontmatter value) and assert
  `make build-check` exits non-zero. A passing target proves the target passes,
  not that the new check ran.

- [ ] **AC10 — The publish script enforces membership itself.** AC6's tripwire is
  a *pre-merge* control that the publishing actor never consults:
  `publish-claude-plugins.yml` triggers on `push: main` with `contents: write`,
  declares **no `needs:`** on the build-check job, and runs regardless of its
  result; `main` requires no PR review, `enforce_admins` is false, and there is
  no CODEOWNERS. So `publish_claude_plugins.py` re-derives the predicate before
  `git push` and exits non-zero if the set to be published differs from it.

  It also asserts `{plugin names in the published marketplace.json} == {published
  directory names}` and exits non-zero naming the difference — the dangling-entry
  invariant Defect 3 opens on, which no other criterion covers (AC4's check is
  one-directional).

  AC6 is a declared-intent tripwire; AC10 is the enforcement boundary. Putting
  the publish job behind a GitHub Environment with a required reviewer is
  **Deferred** — repository settings, not a code change.

- [ ] **AC11 — `catalogue-curation` keeps its own exclusion**, retained
  *alongside* the derived predicate, applied **first**, and exempt from AC10's
  fail-loud check — otherwise the two give opposite instructions for the one
  input AC10 exists for, since `catalogue-curation` is itself repo-only.

  Its absence from the **repo-root** marketplace rests entirely on its
  `allowed-scopes`; `EXCLUDE` guards only the dist branch. Widening its scopes
  would re-publish it at the root with only AC6's tripwire in the way. Recorded,
  not fixed: operator-only is not yet pack metadata all writers honour.

- [ ] **AC12 — Emptying the set is an error, not an outcome.** Both marketplace
  writers exit non-zero if the filter would leave zero entries, and print one
  summary line naming how many packs were dropped and why.

  This matters for **adopters**, not this repo: `_aggregate_marketplace` is what
  an adopter's `run_self_host` calls with their own owner and name.
  `contracts/pack.schema.json` requires only `[pack].name` and `[pack].version`
  — `[pack.adapter-contract]` is **optional** in the normative contract — so a
  schema-valid adopter pack resolves `["repo"]` and vanishes from their own
  marketplace. A log line inside a build that prints hundreds is not a
  proportional signal for that.

- [ ] **AC13 — The engine behaviour change is disclosed to self-hosting
  adopters.** `packages/agentbundle`'s `[Unreleased]` describes the filter as an
  engine change affecting anyone running `run_self_host`, separately from AC14's
  this-repo delisting notice.

- [ ] **AC14 — Delisting is disclosed as a breaking change, with revocation as
  step one.** `[Unreleased]` in `packages/agentbundle/CHANGELOG.md` and
  `docs/product/changelog.md` name the removal, the seven packs, and the remedy:
  **`claude plugin uninstall <pack>@agent-ready-repo` first**, then install at
  repo scope with `agentbundle install`. Delisting is not revocation — the filter
  removes the entry and the directory but uninstalls nothing.

- [ ] **AC15 — Real-client verification, and it decides AC14's remedy.**
  Pre-merge against a **local marketplace path** — the repo-root marketplace
  resolves from `main` and the dist branch is written on push, so neither
  reflects the PR. Recorded: `claude plugin details` on a dropped pack; a
  post-delist `claude plugin update` and marketplace refresh, since the publish
  script wipes the worktree so a delisted pack's directory vanishes *at the very
  `ref` every installed copy points at*. That observation — not "silently retains
  a cached copy" — is what AC14's remedy is written against. A post-merge re-run
  against the published marketplace is a separate recorded step.

  **No tombstone option.** A `DEPRECATED` prefix in `description` is
  unimplementable: there is one `description` field, copied into both
  marketplaces, `agentbundle list-packs`, the packaged catalogue artifact, and
  the site — so it would misinform direct-route and APM adopters for whom nothing
  changed, and it violates the authoring standard that bans lifecycle and meta
  copy from `description`. It also requires the pack to stay published one more
  release, which AC6 forbids in the same PR.

- [ ] **AC16 — Prose docs stop advertising the route for repo-only packs.**
  Re-derived by grep, and enforced by a scripted allowlist assertion (`! grep -q`
  form, not `grep -c`, which exits 1 on no-match). Known sites: `README.md`;
  `docs-site/src/content/docs/getting-started/install.md`;
  `guides/_shared/explanation/install-routes.md` (route-table row **and** its
  marker-writer paragraph); `guides/_shared/explanation/pack-catalogue.md`;
  `guides/core/how-to/adapt-to-project.md`;
  `.github/workflows/publish-claude-plugins.yml`'s header ("adopters can install
  **any pack**"); `tools/hooks/README.md`;
  `packs/core/.apm/hook-wiring/session-start.toml`. The precondition is stated
  once, in `install-routes.md`'s route table.

- [ ] **AC17 — The `--emit-install-routes` route summary stops printing a path
  that does not exist.** `commands/install.py:1723-1732` unconditionally emits
  `{output_root}/claude-plugins/{pack_name}/`; after the filter that directory is
  absent for the seven, including `core`.

- [ ] **AC18 — The six `render_pack` consumers are named and asserted.**
  `commands/render.py`, `diff.py`, `init_state.py`, `upgrade.py`,
  `install.py --emit-install-routes`, `validate.py`. `init-state` writes rendered
  relpaths into the state file, so a pre-change `state.json` carries paths the
  render no longer produces and `upgrade` reads them as removals — exercised, not
  assumed.

- [ ] **AC19 — Living statements the change falsifies are fixed, re-derived by
  grep.** Known: `docs/architecture/catalogue.md:32`,
  `docs/architecture/pack-manifest.md:63-66`,
  `docs/architecture/pack-layout.md:113-115`, and `docs/CONVENTIONS.md:597`,
  which is **seed-projected** from `packs/core/seeds/docs/CONVENTIONS.md` — so it
  is edited in the seed, then `make build-self`, then a `core` version bump.

  The bump is **two files**, not three: `pack.toml` and
  `.claude-plugin/plugin.json`. AC6 deletes `core`'s marketplace entry in the
  same PR, so the usual three-file rule collapses. `catalogue verify`'s CAT-V-005
  reads `pack_dir/plugin.json`, not `pack_dir/.claude-plugin/plugin.json`, so
  `make build-check` stays green on a stale manifest — the agentbundle pytest
  suite is the verification, not `build-check`.

- [ ] **AC20 — The engine RFC is named before EXECUTE.**
  `tools/lint-catalogue-curation-guard.py` carves out only `build/recipes/` and
  `/tests/`; this change edits `build/main.py` and `build/self_host.py`, so the
  committed changeset fails `make build-check` without an `Engine-Change-RFC:`
  trailer naming an engine-scoped RFC. ADR-0002 and ADR-0072 are ADRs, not RFCs.
  Either an existing RFC governs this, or one is opened — decided at PLAN, not
  discovered at EXECUTE, where the temptation is to borrow an unrelated number to
  clear a gate that exists to force this conversation.

- [ ] **AC21 — The three `allowed-scopes` resolvers are pinned, not asserted
  equal.** `validate.py:_allowed_scopes` gates on
  `[pack.adapter-contract].version`; `install.py:_resolved_allowed_scopes` and
  `catalogue_tooling/lint.py:_profile_allowed_scopes` read `[pack.install]` with
  no version gate. Every shipped pack declares version ≥ 0.7, so "all three agree
  for every shipped pack" would be vacuously green.

  Instead: a property test over a synthetic `contract-version × install-table`
  matrix asserting `_allowed_scopes(p) ⊆ _resolved_allowed_scopes(p)` and
  `⊆ _profile_allowed_scopes(p)`. The reachable divergence is fail-*closed*
  withholding, never over-publication; the property fires if a later
  reconciliation loosens the publish resolver. Reconciling them is out of scope.

- [ ] **AC22 — Projected artifacts regenerated and committed.**
  `.claude-plugin/marketplace.json` is a `make build-check`-gated projected path.

- [ ] **AC23 — Frozen specs carrying the dead premise get errata.**
  `docs/specs/claude-plugins-install-route/spec.md`,
  `docs/specs/claude-plugins-manifest-correctness/spec.md`, and
  `docs/specs/wire-session-start-hook/spec.md` are `Shipped` and frozen; each
  assumes `core` is plugin-installable. Errata only — bodies not edited.

- [ ] **AC24 — The QA-matrix row is retired, and its frozen owner amended.**
  `docs/specs/adapt-to-project/notes/manual-qa-matrix.md`'s "claude-plugins
  install of core at project scope" row is **retired**, not re-pointed.
  `tests/unit/test_manual_qa_matrix_shape.py` cites it as required by AC19 of
  `docs/specs/claude-plugins-install-route/spec.md` — a frozen spec — so that
  spec's erratum explicitly retires the matrix requirement rather than the test
  silently dropping it. The test module's own docstring enumerates the same rows
  and is in scope.

- [ ] **AC25 — RFC-0008's dormancy is recorded where the route is documented.**
  The install→adapt marker keeps being written; both readers
  (`packs/core/.apm/hooks/session-start.py` and the `adapt-to-project` skill)
  live in `core`, so on this route the automatic nudge is reachable only for an
  adopter who also has `core` at repo scope. Dormant on the user-scope path, not
  falsified; takes no erratum.

- [ ] **AC26 — The seven source `plugin.json` files are retained deliberately.**
  They become consumer-less on this route but still feed Gate 2 (source-shape),
  which AC1 does **not** narrow, and still require a version bump in lockstep
  with `pack.toml`. Stated so the next reader does not delete them as dead.

## Testing Strategy

| Criterion | Mode | Artifact that fails if it breaks |
|---|---|---|
| AC1, AC2, AC3, AC4 | Unit | predicate over an `allowed-scopes` × `adapter-contract.version` matrix; Gate 1 `expected_packs` narrowed |
| AC5, AC6, AC7 | Integration | build into `tmp_path`; three-surface set equality both directions; seven absences by name; envelope intact |
| AC8 | Integration + built output | union consistency test; rendered page emits/omits the command |
| AC9 | Goal-based, by mutation | perturb the data → `make build-check` exits non-zero |
| AC10, AC11, AC12 | Unit | publish-script predicate re-derivation; entry-vs-directory equality; empty-set exit; evaluation order |
| AC13, AC14 | Goal-based | both `[Unreleased]` entries carry the pack names, the uninstall-first remedy, and the engine note |
| AC15 | Visual / manual QA | recorded transcripts: local marketplace pre-merge, `plugin update` post-delist, published post-merge |
| AC16 | Goal-based | scripted allowlist assertion over the enumerated sites |
| AC17, AC18 | Integration | each consumer asserted per projection; pre-change `state.json` through `upgrade` |
| AC19, AC22 | Goal-based | grep returns nothing; agentbundle suite green after the seed edit + two-file bump; `make build-self` leaves the tree clean |
| AC20 | Goal-based | the trailer is present and names a real RFC; the engine gate passes |
| AC21 | Unit | property test over the synthetic matrix |
| AC23–AC26 | Goal-based | each named artifact carries its erratum / statement; matrix row and docstring retired |

## Blast radius

Re-derived by glob at task start, not trusted from this list. Tests asserting
`claude-plugins/<repo-only-pack>/` output: `tests/unit/test_render.py:33-34`,
`tests/unit/test_render_cmd.py:84-96`, `build/tests/test_pipeline.py:77-80`,
`build/tests/test_end_to_end_build.py:51,64`,
`tests/integration/test_install_repo_scope_per_adapter.py:238-241`,
`tests/integration/test_install_core_smoke.py:60`,
`tests/integration/test_build_derivation_claude_plugins.py` (derives
`FIXTURE_PACK_NAMES` by `iterdir()` and parametrises on it), and
`tests/integration/test_build_check_drift_gates.py:104,158`. Plus any test
asserting a marketplace entry **count**, and `catalogue_tooling/package.py` —
`catalogue package` embeds `.claude-plugin/marketplace.json` and records a
`marketplace_digest`, so the offline distribution artifact's content and digest
both change.

## Deferred

- **Hook parity on this route** — `docs/specs/claude-plugin-hook-parity/`,
  blocked on a spike. No pack that qualifies for this route ships hooks today,
  so nothing regresses.
- **A required reviewer on the publish job** (GitHub Environment). Repository
  settings, not code. AC10 is the in-code half.
- **An adopter self-host exemption** for the absent-`[pack.adapter-contract]`
  case. AC12 makes the failure loud; making it fail-open is a separate decision.
- Unrestricted ordinary pushes to `claude-plugins-dist`. Force-push and deletion
  denied 2026-08-07; the residual is the detection window, not tip integrity.
- A per-pack content hash in the marketplace entry. Sharper than the push
  residual: with directories removed at the same `ref`, an adopter can neither
  prove what they installed nor re-fetch it.
