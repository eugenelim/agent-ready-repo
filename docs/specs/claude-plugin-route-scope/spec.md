# Spec: Claude-plugin route — publish only user-capable packs

- **Status:** Draft <!-- Draft | Approved | Implementing | Shipped | Archived -->
- **Owner:** eugenelim
- **Plan:** [`plan.md`](plan.md)
- **Constrained by:** [ADR-0002](../../adr/0002-install-scope-per-pack-default-and-allowance.md) (scope is a per-pack default + allowance), [ADR-0072](../../adr/0072-derived-plugin-manifest-mirrors-upstream-schema.md)
- **Contract:** `.claude-plugin/marketplace.json` (both writers), `web/src/content.config.ts`
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
`web/src/pages/packs/[pack].astro:24` and `web/src/pages/catalogue/index.astro:54`
build a plugin-install command for **every** pack.

**Defect 3 — the two marketplace writers have already drifted.**
`catalogue-curation` is listed in the repo-root `.claude-plugin/marketplace.json`
and is absent from `origin/claude-plugins-dist`. The repo-root file is the one
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

### Never do

- Change any pack's `default-scope` or `allowed-scopes`.
- Change the direct or APM routes' projections. `_aggregate_marketplace`'s
  **pack-set predicate** is the one self-host change this spec makes, carved out
  explicitly below.
- Add a third-party dependency (`pyproject.toml` `dependencies = []`).

## Acceptance Criteria

- [ ] **AC1 — One predicate, three writers.** A pack reaches
  `dist/claude-plugins/`, the dist `marketplace.json`, and the repo-root
  `.claude-plugin/marketplace.json` only when its resolved scopes admit `"user"`.
  The predicate is applied at the recipe, at `build/main.py:_run_aggregate`, and
  at `build/self_host.py:_aggregate_marketplace` — the last carries a contrary
  design note ("intentionally ignores the pack filter — the catalogue advertises
  every pack") which this change overturns *at the note*. ADR-0072 records that
  same function as the writer missed last time.

- [ ] **AC2 — Scope resolution reuses the existing helper, and its real gate is
  named.** `commands/validate.py:_allowed_scopes` is reused, not re-derived.
  Its actual behaviour — verified by execution — is that it returns `["repo"]`
  whenever `[pack.adapter-contract].version` is absent or `"0.1"`, **ignoring
  `[pack.install]` entirely**; a pack declaring `allowed-scopes = ["repo","user"]`
  with no `[pack.adapter-contract]` resolves to `["repo"]`. Any fixture that must
  publish therefore declares the contract version *and* the scopes.

- [ ] **AC3 — The seven excluded packs are asserted by name.** `core`,
  `catalogue-curation`, `governance-extras`, `iac-terraform`, `monorepo-extras`,
  `release-engineering`, `user-guide-diataxis` appear in neither
  `dist/claude-plugins/` nor either `marketplace.json`.

  The assertion carries a comment naming it the **scope-widening-equals-publication
  tripwire**: after this spec, editing one line of `allowed-scopes` publishes a
  pack's code to a public marketplace, and this test is the only thing that turns
  red. A future engineer must not "fix" it by deleting a name.

- [ ] **AC4 — `catalogue-curation` keeps its own exclusion.** Its operator-only
  exclusion in `publish_claude_plugins.py` is retained *alongside* the derived
  predicate, not replaced by it — it drops today for a different reason, and
  folding the two would silently re-publish it if its scopes were widened.

- [ ] **AC5 — The publish-side check fails loud.** `publish_claude_plugins.py`
  exits non-zero naming the pack if a repo-only pack is present in `dist/`,
  rather than skipping it silently. Nothing clears `dist/` before a build, so a
  stale directory must be caught, not republished.

- [ ] **AC6 — The site gates on user-capability, computed not copied.**
  `web/src/content/packs/*.md` are hand-authored with no generator, and their
  `scope` field is `default-scope`, not `allowed-scopes` — so gating on it would
  hide `product-documentation` (`default-scope = "repo"`,
  `allowed-scopes = ["repo","user"]`), which AC1 publishes. A user-capability
  field is added and **a test reads each `packs/<slug>/pack.toml` and asserts the
  corresponding `web/` frontmatter matches**, so 21 hand-copied values cannot
  drift. `[pack].astro` and `catalogue/index.astro` gate the plugin-install
  command on it.

- [ ] **AC7 — The site assertion runs in CI.** `npm run test --prefix web`
  appears in no workflow and `make ci` never touches `web/`, so AC6's test must
  either be wired into `.github/workflows/pages.yml` beside the build or be
  written as a Python test under `packages/agentbundle/tests/` that `make ci`
  runs. A criterion whose check never executes is not a criterion.

- [ ] **AC8 — Prose docs stop advertising the route for repo-only packs.**
  Re-derived by grep, not from a list. Known sites: `README.md:32-35`;
  `docs-site/src/content/docs/getting-started/install.md:64-71`;
  `guides/_shared/explanation/install-routes.md` (both the route-table row and
  its marker-writer paragraph); `guides/_shared/explanation/pack-catalogue.md:60`
  ("the same pack content reaches you via … `/plugin install`" — now false for
  seven packs); `guides/core/how-to/adapt-to-project.md:53`. The precondition is
  stated once, in `install-routes.md`'s route table.

- [ ] **AC9 — Living architecture statements the change falsifies are fixed.**
  `docs/architecture/catalogue.md:32` states the build aggregates *each* pack's
  metadata into `marketplace.json`. `docs/CONVENTIONS.md` classes
  `architecture/*` as Living — drift is a bug.

- [ ] **AC10 — Delisting is disclosed as a breaking change, with revocation as
  step one.** `[Unreleased]` entries in `packages/agentbundle/CHANGELOG.md` and
  `docs/product/changelog.md` name the removal, name the packs, and give the
  remedy: **`claude plugin uninstall <pack>@agent-ready-repo` first**, then
  install at repo scope with `agentbundle install`.

  Delisting is not revocation. The filter removes the marketplace entry and the
  branch directory but uninstalls nothing, so an adopter keeps running a pinned,
  permanently-unmaintained copy; following the remedy without uninstalling leaves
  two unrelated copies of the pack's skills.

- [ ] **AC11 — Projected artifacts regenerated and committed.**
  `.claude-plugin/marketplace.json` is a `make build-check`-gated projected path;
  dropping seven entries requires `make build-self` and committing the result.

- [ ] **AC12 — Real-client verification.** A dropped pack is confirmed absent
  from the marketplace against `claude` 2.1.223, and an install-then-delist run
  records what the client actually does to an installed-but-delisted plugin —
  which source review cannot settle. Transcripts in `plan.md`.

- [ ] **AC13 — Frozen specs carrying the dead premise get errata.**
  `docs/specs/claude-plugins-install-route/spec.md`,
  `docs/specs/claude-plugins-manifest-correctness/spec.md`, and
  `docs/specs/wire-session-start-hook/spec.md` are `Shipped` and therefore
  frozen; each assumes `core` is installable by plugin. Errata only — bodies not
  edited. `docs/specs/adapt-to-project/notes/manual-qa-matrix.md`'s
  "claude-plugins install of core at project scope" row is re-pointed or retired
  along with `tests/unit/test_manual_qa_matrix_shape.py:37-44`, which keeps it
  green while the scenario becomes impossible.

- [ ] **AC14 — RFC-0008's dormancy is recorded where the route is documented.**
  The install→adapt chain's marker keeps being written; both readers
  (`packs/core/.apm/hooks/session-start.py` and the `adapt-to-project` skill)
  live in `core`, so on this route the automatic nudge is reachable only for an
  adopter who also has `core` at repo scope. RFC-0008 is dormant on the
  user-scope path, not falsified, and takes no erratum —
  `docs/architecture/agentbundle.md:245-254` and `install-routes.md` say so.

## Testing Strategy

- **Unit** — the predicate over an `allowed-scopes` × `adapter-contract.version`
  matrix, including the absent-table case AC2 names.
- **Integration** — the seven exclusions by name in all three artifacts; a
  user-capable pack still present; the `web/` frontmatter-vs-`pack.toml`
  consistency test.
- **Goal-based** — the AC8 grep returns nothing; `make build-check` passes on the
  regenerated marketplace.
- **Manual QA** — AC12 against the real client.

## Blast radius

Tests asserting `claude-plugins/<repo-only-pack>/` output go red and are re-pinned
in the same task: `tests/unit/test_render.py:33-34`,
`tests/unit/test_render_cmd.py:84-96`, `build/tests/test_pipeline.py:77-80`,
`build/tests/test_end_to_end_build.py:51,64`,
`tests/integration/test_install_repo_scope_per_adapter.py:238-241`,
`tests/integration/test_install_core_smoke.py:60`, and
`tests/integration/test_build_derivation_claude_plugins.py`, which derives
`FIXTURE_PACK_NAMES` by `iterdir()` over five repo-only build fixtures and
parametrises four assertions on them. Plus any test asserting a marketplace entry
count. Re-derived by glob at task start, not trusted from this list.

## Deferred

- **Hook parity on this route** — `docs/specs/claude-plugin-hook-parity/`. A pack
  shipping `.apm/hook-wiring/` still gets it published inert. No pack that
  qualifies for this route ships hooks today, so nothing regresses; that spec is
  blocked on a spike.
- A compensating control for unrestricted ordinary pushes to
  `claude-plugins-dist`. Force-push and deletion are denied (applied
  2026-08-07); ADR-0072's named threat is narrowed, not closed.
- A per-pack content hash in the marketplace entry, so an installed plugin is
  traceable to the commit that produced it while `ref` stays mutable.
