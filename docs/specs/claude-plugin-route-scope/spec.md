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

  **Evaluation order:** the name exclusion is applied *first* and is exempt from
  AC5's fail-loud check — otherwise the two criteria give opposite instructions
  for the one input AC5 exists for (`catalogue-curation` is itself repo-only, so
  a stale `dist/` containing it would be both "skip" and "fail").

  Its absence from the **repo-root** marketplace, though, rests entirely on its
  `allowed-scopes` — `EXCLUDE` guards only the dist branch. Widening its scopes
  would re-publish it at the root with only AC3's tripwire in the way. Recorded
  rather than fixed here; operator-only is not yet pack metadata all three
  writers honour.

- [ ] **AC5 — The publish-side check fails loud, and reads the source tree.**
  Scope resolution for both the predicate and this check reads
  `packs/<slug>/pack.toml`, **not** the projected `dist/claude-plugins/<pack>/pack.toml`.
  `_run_aggregate` reads the projected copy today and `make build` has no
  dependency on `clean`, so narrowing a pack's scopes and rebuilding leaves a
  stale dist directory carrying the *old* declaration — which would resolve
  user-capable and publish contrary to the pack's current intent. A
  `dist/claude-plugins/<name>/` with no corresponding source pack is itself a
  fail-loud error. `publish_claude_plugins.py` exits non-zero naming the pack
  if a repo-only pack is present in `dist/`, rather than skipping it silently.

- [ ] **AC6 — The site gates on user-capability, computed not copied.**
  `web/src/content/packs/*.md` are hand-authored with no generator, and their
  `scope` field is `default-scope`, not `allowed-scopes` — so gating on it would
  hide `product-documentation` (`default-scope = "repo"`,
  `allowed-scopes = ["repo","user"]`), which AC1 publishes. A user-capability
  field is added and **a test reads each `packs/<slug>/pack.toml` and asserts the
  corresponding `web/` frontmatter matches**, so the per-pack copies cannot
  drift. `[pack].astro` and `catalogue/index.astro` gate the plugin-install
  command on it. Separately from the consistency test, **a built-output
  assertion**: a repo-only pack's rendered page emits no
  `claude plugin install` command and a user-capable pack's does. The
  consistency test guards the data; only the built-output assertion guards the
  user-visible outcome.

- [ ] **AC7 — The site assertion runs in the one gate that always runs.**
  AC6's check is reachable from **`make build-check`**. That is the only required
  status check on `main` and the only path-unfiltered one. The alternatives all
  fail: `make ci` is a local target no workflow invokes; the full pytest suite
  runs only in `catalogue-tooling-ci-gates.yml` Gate A, which is not required
  *and* carries `paths-ignore: 'web/**'` — so a PR editing only
  `web/src/content/packs/*.md`, exactly the drift AC6 exists to catch, skips it;
  and `pages.yml` is path-filtered away from `packs/**/pack.toml`, missing the
  mirror-image edit. A criterion whose check never executes is not a criterion,
  and that applies to this one.

  The same requirement covers AC3's tripwire: after this spec, editing one line
  of `allowed-scopes` publishes a pack's code to a public marketplace, and a
  non-blocking red X in an unrequired workflow is not a control.

- [ ] **AC8 — Prose docs stop advertising the route for repo-only packs.**
  Re-derived by grep, not from a list. Known sites: `README.md:32-35`;
  `docs-site/src/content/docs/getting-started/install.md:64-71`;
  `guides/_shared/explanation/install-routes.md` (both the route-table row and
  its marker-writer paragraph); `guides/_shared/explanation/pack-catalogue.md:60`
  ("the same pack content reaches you via … `/plugin install`" — now false for
  seven packs); `guides/core/how-to/adapt-to-project.md:53`. The precondition is
  stated once, in `install-routes.md`'s route table.

- [ ] **AC9 — Living architecture statements the change falsifies are fixed,
  re-derived by grep.** Not from this list — the list is the starting point.
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

### Review-round additions

- [ ] **AC15 — The predicate is route-scoped, and says so.** `Recipe` has no
  pack-filter field and the per-pack loop is **shared with
  `per-pack-apm-package`** — an unkeyed predicate would silently filter the APM
  route, which this spec's `Never do` forbids. The filter keys on the
  claude-plugins route explicitly (`output_subdir == "claude-plugins"`) plus the
  two marketplace writers, and nothing else.

  It also applies on **adopter self-host runs**: `_aggregate_marketplace` is what
  an adopter's `run_self_host` calls with their own owner and name, so a legacy
  adopter pack with no `[pack.adapter-contract]` resolves to `["repo"]` and would
  vanish from their own marketplace. Every writer prints a named line per
  excluded pack with the resolved scopes, so an exclusion is never silent.

- [ ] **AC16 — The complement is asserted, and the envelope survives.** The
  published set equals *exactly* the derived user-capable set, globbed from
  `packs/`, asserted in **both** directions — AC3 covers only the seven
  absences, so a predicate bug in the fail-*closed* direction (most plausibly
  the absent-`[pack.adapter-contract]` trap AC2 names) could truncate or empty
  the marketplace uncaught. `_run_aggregate` derives the envelope's `name` and
  `owner` by scanning entries for a GitHub `source.url`, so a truncated set that
  loses those breaks `claude plugin marketplace add` for every adopter; the
  envelope's `name`, `owner`, and `description` are asserted intact.

- [ ] **AC17 — The tripwire is reachable from the required gate.** AC3's by-name
  assertion runs under `make build-check` — the only required, path-unfiltered
  status check on `main`, which requires no PR review and has no CODEOWNERS
  behind it. A non-blocking red X in an unrequired workflow is not a control for
  "editing one line of `allowed-scopes` publishes a pack's code to a public
  marketplace". The failure message names the publication consequence and the
  `Ask first` boundary.

- [ ] **AC18 — The user-capability field is fail-closed and checked both ways.**
  Required in the Zod schema with **no default**, so the Astro build fails on
  omission rather than defaulting to advertising the public install route. AC6's
  consistency test iterates the **union** of `packs/<slug>/pack.toml` and
  `web/src/content/packs/<slug>.md`, not just the `web/` side, so a newly added
  pack cannot be silently skipped.

- [ ] **AC19 — The six `render_pack` consumers are named.** `commands/render.py`,
  `commands/diff.py`, `commands/init_state.py`, `commands/upgrade.py`,
  `commands/install.py --emit-install-routes`, and `commands/validate.py` all run
  the `per-pack-claude-plugin` recipe, so a recipe-level filter removes whole
  subtrees from their output. `init-state` writes those relpaths into the state
  file, so a pre-change `state.json` carries paths the render no longer
  produces and `upgrade` reads them as removals. Each consumer is asserted for
  its expected changed/unchanged status per projection.

- [ ] **AC20 — The three `allowed-scopes` resolvers agree.**
  `commands/validate.py:_allowed_scopes` gates on `[pack.adapter-contract].version`;
  `commands/install.py:_resolved_allowed_scopes` and
  `catalogue_tooling/lint.py:_profile_allowed_scopes` read `[pack.install]` with
  no version gate. Publishing on the strictest while installing on the loosest
  means a pack can be published to a scope `install` would refuse, or withheld
  from one it would permit. A test asserts all three agree for every shipped
  pack; reconciling them is out of scope.

- [ ] **AC21 — AC12's finding is bound to the disclosure.** The real-client
  install-then-delist observation does not just get recorded — it decides the
  remedy. If the client silently retains the cached copy and stops resolving
  updates, the adopter keeps running a permanently unmaintained user-scope copy
  whose only notice is a changelog their client never reads. Either a one-release
  tombstone (`description` prefixed `DEPRECATED — uninstall, then install at repo
  scope`) ships before removal, or the observed behaviour is quoted verbatim in
  both changelogs as an accepted risk.

  AC12 also runs against a **local marketplace path pre-merge** — the repo-root
  marketplace resolves from `main` and the dist branch is written on push to
  `main`, so neither reflects the PR. A post-merge re-run against the published
  marketplace is a separate recorded step.

- [ ] **AC22 — The QA-matrix row gets one outcome, and its frozen owner is
  amended.** `docs/specs/adapt-to-project/notes/manual-qa-matrix.md`'s
  "claude-plugins install of core at project scope" row is **retired**, not
  re-pointed. `tests/unit/test_manual_qa_matrix_shape.py` cites it as required by
  AC19 of `docs/specs/claude-plugins-install-route/spec.md` — a frozen spec — so
  that spec's erratum explicitly retires the matrix requirement rather than the
  test silently dropping it.

- [ ] **AC23 — The seven source `plugin.json` files are retained deliberately.**
  `packs/<repo-only>/.claude-plugin/plugin.json` becomes consumer-less on this
  route but still gates the source-shape drift check and still requires a version
  bump in lockstep with `pack.toml`. Stated in the spec so the next reader does
  not delete them as dead.

## Testing Strategy

Per criterion, with the artifact that would fail if it broke.

| Criterion | Mode | Artifact |
|---|---|---|
| AC1, AC2, AC15, AC20 | Unit | predicate over an `allowed-scopes` × `adapter-contract.version` matrix; resolver-agreement test |
| AC3, AC16 | Integration | build into `tmp_path`; seven absences by name + set equality both directions + envelope intact |
| AC4, AC5 | Unit | evaluation-order test; stale-`dist/` fixture asserting non-zero exit |
| AC6, AC18 | Integration + built output | `pack.toml` ↔ `web/` union consistency; rendered page emits/omits the install command |
| AC7, AC17 | Goal-based | the checks are invoked by `make build-check` — asserted by running that target, not by reading the workflow |
| AC8 | Goal-based | scripted allowlist assertion over an enumerated site list, `! grep -q` form |
| AC9 | Goal-based | repo-wide grep for the falsified statements returns nothing; `make build-check` green after the seed edit + `core` bump |
| AC10, AC21 | Goal-based | both `[Unreleased]` entries contain the pack names and the uninstall-first remedy |
| AC11 | Goal-based | `make build-self` leaves the tree clean; `make build-check` green |
| AC12, AC21 | Visual / manual QA | recorded client transcripts, pre-merge local marketplace and post-merge published |
| AC13, AC22 | Goal-based | each named frozen spec carries an erratum; the matrix row is retired and its shape test updated |
| AC14 | Goal-based | grep confirms the dormancy statement is present where the route is documented |
| AC19 | Integration | each of the six consumers asserted per projection |
| AC23 | Goal-based | the seven source manifests still present and still gated |

## Blast radius

Tests asserting `claude-plugins/<repo-only-pack>/` output go red and are re-pinned
in the same task: `tests/unit/test_render.py:33-34`,
`tests/unit/test_render_cmd.py:84-96`, `build/tests/test_pipeline.py:77-80`,
`build/tests/test_end_to_end_build.py:51,64`,
`tests/integration/test_install_repo_scope_per_adapter.py:238-241`,
`tests/integration/test_install_core_smoke.py:60`, and
`tests/integration/test_build_check_drift_gates.py:104,158` — the real gate at
`build/self_host.py:1374-1405` builds `expected_packs` from **every** pack
carrying `.claude-plugin/plugin.json` and hard-fails on a missing derived
`install-marker.py`, so it produces seven failures after the filter and needs the
same predicate — and
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
