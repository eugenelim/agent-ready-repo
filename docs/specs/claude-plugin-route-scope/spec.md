# Spec: Claude-plugin route — publish only user-capable packs

- **Status:** Implementing <!-- Draft | Approved | Implementing | Shipped | Archived -->
- **Owner:** eugenelim
- **Plan:** [`plan.md`](plan.md)
- **Constrained by:** [ADR-0002](../../adr/0002-install-scope-per-pack-default-and-allowance.md) (scope is a per-pack default + allowance), [ADR-0072](../../adr/0072-derived-plugin-manifest-mirrors-upstream-schema.md)
- **Engine RFC:** [RFC-0008](../../rfc/0008-claude-plugins-install-route-parity.md) — carried as `Engine-Change-RFC: 0008`, with an erratum. See AC20.
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
means by `repo` — observed 2026-08-08: no entry under `~/.claude.json`'s
`projects` table records plugin enablement at all.

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
- ~~Adding a Node toolchain to the required `make build-check` job.~~
  **Asked and declined, 2026-08-08.** The built-output assertion goes to
  `pages.yml` instead; see AC8's accepted residual. Revisiting this is a
  separate change.

### Never do

- Change any pack's `default-scope` or `allowed-scopes`.
- Change the APM or direct routes' projections. The two marketplace writers and
  the drift gate's pack set are the self-host changes this spec makes, carved out
  by AC1.
- Add a third-party dependency (`pyproject.toml` `dependencies = []`).

## The derived set

Used by every criterion below. A pack is **publishable** when all hold:

1. it lives at `packs/<slug>/` and its slug does not start with `_` — the
   existing guards at `build/main.py:387` (`discover_packs`, which governs the
   dist tree), `build/self_host.py:616` (the repo-root writer), and
   `build/self_host.py:1380` (the drift gate). Not `self_host.py:550`, which is a
   *seed-filename* guard inside `_project_seeds`, not a slug rule. `_example` is
   user-capable by declaration and excluded by this rule, so a naive
   set-equality assertion fails on day one;
2. it carries `pack.toml` and `.claude-plugin/plugin.json`. **The three writers
   differ here today**: `discover_packs` requires only `pack.toml`, while the
   repo-root writer and the drift gate require both. AC5's equality therefore
   adds a `plugin.json` precondition at the recipe writer — stated, not implied;
3. its resolved scopes admit `"user"`.

## What shipped

Every criterion is met **except AC18's removal clause**, which is deferred with
a slug. What ships pins that a stale `claude-plugins/<pack>/` relpath is absent
from a fresh render; what it does not pin is that `upgrade` therefore deletes
it. Two attempts to drive the production comparator failed — `diff.run` returns
0 and prints nothing even on a real divergence — so the changelog's
file-deletion disclosure currently rests on reading the code, not on a test.

Otherwise: the route publishes only user-capable packs, says so everywhere it is
advertised, and each control is asserted by a gate that fails when the thing it
guards breaks — verified by mutating each control and confirming its artifact
goes red.

Two things are worth carrying forward as read:

- **The roster tripwire is separate from the membership lint on purpose.**
  `lint-plugin-membership` derives both sides of its comparison from the same
  predicate, so it is green when the predicate itself is wrong.
  `lint-plugin-roster` enumerates both rosters literally, which makes it the
  gate that turns red when widening a pack's `allowed-scopes` changes what gets
  published. Do not "fix" a failure there by editing the lists to match.
- **The stdlib mirror is differential-tested, not trusted.** `tools/` cannot
  import the canonical resolver, so `tools/pack_scope.py` mirrors it and
  `test-pack-scope.py` compares the two across the whole
  contract-version × install-table matrix. One copy, pinned.

Deferred to the backlog, and out of this spec's scope rather than short of it:
a required reviewer on the publish job (repository settings), an adopter
self-host exemption for the absent-contract case, the post-merge marketplace
re-run, a per-pack content hash, `pages.yml`'s CI-parity disposition, and the
fixture continuation indentation RFC-0082's relocation will carry.

## Acceptance Criteria

- [x] **AC1 — One predicate, four sites.** A pack reaches
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

- [x] **AC2 — Scope resolution reuses the existing helper**
  — and its real gate is named. `commands/validate.py:_allowed_scopes` is reused, not re-derived. Its
  actual behaviour — verified by execution — is that it returns `["repo"]`
  whenever `[pack.adapter-contract].version` is absent or `"0.1"`, **ignoring
  `[pack.install]` entirely**. Any fixture that must publish declares the
  contract version *and* the scopes.

- [x] **AC3 — The predicate is route-keyed on `(recipe.name, recipe.adapter)`**,
  matching `_resolve_contract_for_route`'s existing idiom — not on
  `output_subdir`, which is free text on an operator-supplied `--recipe` file.

  The APM route is already safe by construction: `_run_per_pack` dispatches
  `if recipe.adapter == "apm"` and returns before the claude-plugins loop, so
  keying is belt-and-braces rather than the load-bearing separation the first
  draft claimed. Gate 1c independently checks `dist/apm/<pack>/` for every pack
  and would fail loudly if APM were ever filtered.

- [x] **AC4 — `_run_aggregate` gains a source-tree handle.** It is
  `_run_aggregate(recipe, output_dir)` today and resolves scope from the
  *projected* `dist/claude-plugins/<pack>/pack.toml`. `make build` has no
  dependency on `clean`, so narrowing a pack's scopes and rebuilding leaves a
  stale dist directory carrying the *old* declaration, which resolves
  user-capable and publishes contrary to current intent. Scope resolution reads
  `packs/<slug>/pack.toml`. `run_recipe` already holds `packs_list`; threading it
  is a signature change and is named as one.

- [x] **AC5 — Membership is asserted on all three surfaces, both directions.**
  The dist tree, the dist `marketplace.json`, and the repo-root
  `marketplace.json` each equal the derived publishable set exactly. **The
  expected side is enumerated literally in the test**, never computed by calling
  the production predicate — otherwise a predicate bug shifts both sides
  identically and the assertion is a tautology that stays green while the
  marketplace truncates. Both
  directions matter: AC6's by-name absences catch a fail-open bug, and only set
  equality catches a fail-*closed* one — most plausibly AC2's absent-contract
  trap — which could truncate or empty the marketplace uncaught.

  **Manifest-less packs now produce no claude-plugins output.**
  `_run_per_pack_single` emits `dist/claude-plugins/<pack>/` for any pack with a
  `pack.toml`, manifest or not; equality against a set that requires
  `plugin.json` deletes that subtree for `cc-user-hooks`, `list_packs/{alpha,beta}`,
  and `local_scope/local-test-pack`. That is a second behavioural change, named
  here rather than discovered in a red suite.

  Assertions build into `tmp_path`, not against the repo's `dist/`, which is
  gitignored and absent under a plain `pytest` run; an absence assertion against
  a directory that does not exist is green while the feature is broken.

- [x] **AC6 — Both sides of the split are asserted by name.** The seven excluded
  packs absent from all three surfaces, **and the user-capable complement present
  by name** — absences alone leave a fail-closed truncation that drops
  `architect` or `product-documentation` asserted by nothing. The assertion carries a comment naming it the
  **scope-widening-equals-publication tripwire** — a future engineer must not
  "fix" it by deleting a name.

- [x] **AC7 — The envelope survives.** `_run_aggregate` derives the dist
  marketplace's `name` and `owner` from the **first** entry carrying a GitHub
  `source.url` — pack-supplied metadata — so a filtered set can silently re-key
  the marketplace to a different owner. Either the envelope identity is read from
  the catalogue/discovery config as the sibling writer does, or the writer
  refuses when surviving entries disagree on `source.url`. `name`, `owner`, and
  `description` are asserted intact.

- [x] **AC8 — The site gates on user-capability, computed not copied.**
  `web/src/content/packs/*.md` are hand-authored with no generator, and their
  `scope` field is `default-scope`, not `allowed-scopes` — gating on it would
  hide `product-documentation` (`default-scope = "repo"`,
  `allowed-scopes = ["repo","user"]`), which AC1 publishes.

  A user-capability field is added, **required in the Zod schema with no
  default**, so the Astro build fails on omission rather than defaulting to
  advertising the public route.

  Two checks, deliberately on **different gates** (decision recorded
  2026-08-08):

  - **Consistency — required gate.** A pure-stdlib lint iterates the **union**
    of `packs/<slug>/pack.toml` and `web/src/content/packs/<slug>.md` over
    non-`_`-prefixed slugs per *The derived set* § 1 (`_example` has a pack
    directory and no site page), asserting the user-capability field matches.
    This is the check that guards silent data drift across every pack, so it
    runs where merge is blocked.
  - **Built output — `pages.yml`, non-blocking.** A repo-only pack's rendered
    page emits no `claude plugin install` command; a user-capable pack's does.
    `packs/**/pack.toml` joins that workflow's path filter so it fires on both
    sides of the drift, not only on `web/` edits.

  **Why not both in the required gate.** The built-output half needs an Astro
  build, and `make build-check` has no Node on either `build-check.yml` or
  `build-check-windows.yml`. Adding it would make every PR in the repo — most
  touching nothing near the site — wait on `npm ci` in the gate that blocks
  merge, and inherit a registry outage as a merge blocker.

  **Accepted residual.** A PR that deletes the gating conditional from
  `[pack].astro` or `catalogue/index.astro` and changes nothing else goes red in
  `pages.yml` but does not block merge. That failure is a visible edit to one of
  two files in a PR a human reads; the drift the required check catches is
  silent and spread across every pack. A third guard is already in place: the
  Zod field is required with no default, so *omitting* it fails the Astro build
  regardless.

- [x] **AC9 — The checks are wired into the required gate, and proven wired.**
  `make build-check` is `catalogue verify` + `tools/repo/build_gate_chain.py` +
  SAST. **It runs no pytest**, and in `build-check.yml` the make step runs
  *before* pytest is installed. So a pytest-based tripwire cannot simply "hang
  off `make build-check`": AC6's tripwire lands as a `tools/lint-*.py` +
  `tools/test-lint-*.py` pair registered in `build_gate_chain.py`, with the
  `lint-ci-parity` update that requires.

  This covers AC8's **consistency** half and AC6's membership tripwire. AC8's
  built-output half is out of the required gate by the decision recorded there.

  The verification is **mutation, not a green run**: desync a
  `web/src/content/packs/<slug>.md` user-capability value from its `pack.toml`,
  assert `make build-check` exits non-zero, revert. The mutation target is a
  site frontmatter file, never a `packs/*/pack.toml` — the *Never do* boundary
  forbids touching a pack's scope declaration even transiently.

  A **second** mutation exercises the membership tripwire, which the frontmatter
  desync does not reach. It must be one the **existing** projected-path drift
  gate cannot see: `.claude-plugin/marketplace.json` is regenerated into the
  shadow tree and diffed (`self_host.py:1169-1193`), so hand-injecting an entry
  there exits non-zero on *drift* whether or not the membership lint was ever
  registered — reproducing the very defect this mutation was added to catch.
  Instead: drive the membership lint's own `tools/test-lint-*.py`, or mutate the
  **dist** marketplace, and require the recorded transcript to name *which* gate
  produced the non-zero exit. The transcript
  lands in the plan's `## Verification log`. A passing target proves the target
  passes, not that the new check ran.

- [x] **AC10 — The publish script enforces membership itself.** AC6's tripwire is
  a *pre-merge* control that the publishing actor never consults:
  `publish-claude-plugins.yml` triggers on `push: main` with `contents: write`,
  declares **no `needs:`** on the build-check job, and runs regardless of its
  result; `main` requires no PR review, `enforce_admins` is false, and there is
  no CODEOWNERS. So `publish_claude_plugins.py` re-derives the predicate before
  `git push` — reading `packs/<slug>/pack.toml`, **not** `dist/`, matching AC4;
  re-deriving from `dist/` would compare `dist/` against itself and could not
  catch the stale tree it exists for — and exits non-zero if the set to be
  published differs.

  It also asserts `{plugin names in the published marketplace.json} == {published
  directory names}` and exits non-zero naming the difference — the dangling-entry
  invariant Defect 3 opens on, which no other criterion covers (AC4's check is
  one-directional).

  It additionally asserts `{names in the repo-root marketplace} ⊆ {published
  directory names}`. AC11 leaves `catalogue-curation` un-`EXCLUDE`d at the root
  while the publish script strips it from the branch, so
  `published = derived − EXCLUDE` while `repo_root = derived` — Defect 3's
  asymmetry survives structurally, dormant only because that pack happens to be
  repo-only.

  **The honest residual.** AC10 catches build/publish desync and stale-`dist/`
  republication. It **cannot constrain an actor**: the same push that widens a
  `pack.toml` can edit this script and the workflow, and with no `needs:`, no
  CODEOWNERS, `enforce_admins: false` and no required review, the real trust
  boundary for publication is push access to `main`. AC6 is a declared-intent
  tripwire; AC10 is a consistency check, not a gate on who publishes.

  The achievable in-code control is **`workflow_run` gating** — `build-check.yml`
  already runs on `push: main`, so the publish job can require
  `conclusion == success`. That is Deferred, not the Environment reviewer, which
  is a non-control in a single-maintainer repo.

- [x] **AC11 — `catalogue-curation` keeps its own exclusion**, retained
  *alongside* the derived predicate, applied **first**, and exempt from AC10's
  fail-loud check — otherwise the two give opposite instructions for the one
  input AC10 exists for, since `catalogue-curation` is itself repo-only.

  Its absence from the **repo-root** marketplace rests entirely on its
  `allowed-scopes`; `EXCLUDE` guards only the dist branch. Widening its scopes
  would re-publish it at the root with only AC6's tripwire in the way. Recorded,
  not fixed: operator-only is not yet pack metadata all writers honour.

- [x] **AC12 — Emptying the set is an error only where emptiness is a defect.**
  A build exits non-zero when **the discovered pack set was non-empty and the
  filter emptied it**. Not when the catalogue was empty to begin with:
  `tests/fixtures/blank_catalogue/packs/` holds only `_example`, so
  `discover_packs` returns `[]` and the filter does nothing — a blank catalogue
  is a shipped, valid state (`tests/integration/test_blank_catalogue.py`).

  **The caller says which mode it is.** `_run_aggregate` is the *same* function
  under whole-catalogue (`run_default_build`) and single-pack (`render_pack_to_dir`
  → `run_recipe(recipe, [pack], …)`), driven by the *same* `marketplace` recipe
  with `adapter` unset — so AC3's route key cannot separate them, and
  `len(packs_list) == 1` misclassifies the four genuine one-pack catalogues in
  the fixtures plus `make build PACK=<x>`. AC4's signature change therefore
  carries an explicit `aggregate_scope: "catalogue" | "single-pack"`, and each
  caller passes its own.

  - **catalogue** — non-zero exit, one summary line naming how many packs were
    dropped and why.
  - **single-pack** — empty `plugins` list, success, summary line to **stderr**
    so it does not become stdout noise in `diff`, `validate`, `init-state`,
    `upgrade`, and `install --emit-install-routes`, all of which call
    `render_pack`.
  - **adopter self-host** — `_aggregate_marketplace` runs on `run_self_host`
    *after* adapters and seeds are written, so a non-zero exit there leaves a
    half-projected tree. `contracts/pack.schema.json` requires only `[pack].name`
    and `[pack].version` — `[pack.adapter-contract]` is **optional** — so a
    schema-valid adopter pack resolves `["repo"]` through no fault of its own.
    That path warns loudly and continues **with the filtered, possibly empty
    set** — "continues" must not be read as "continues unfiltered".

- [x] **AC13 — The engine behaviour change is disclosed to self-hosting
  adopters.** `packages/agentbundle`'s `[Unreleased]` describes the filter as an
  engine change affecting anyone running `run_self_host`, separately from AC14's
  this-repo delisting notice.

- [x] **AC14 — Delisting is disclosed as a breaking change, with revocation as
  step one.** `[Unreleased]` in `packages/agentbundle/CHANGELOG.md` and
  `docs/product/changelog.md` name the removal, the seven packs, and the remedy:
  **`claude plugin uninstall <pack>@agent-ready-repo` first**, then install at
  repo scope with `agentbundle install`. Delisting is not revocation — the filter
  removes the entry and the directory but uninstalls nothing.

- [x] **AC15 — Real-client verification, and it decides AC14's remedy.**
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

- [x] **AC16 — Prose docs stop advertising the route for repo-only packs.**
  Enforced by a scripted assertion enumerating **`(path, pattern, expected
  state)` per site**, not one grep form — the sites do not share a pattern.
  `README.md` and `docs-site/.../install.md` carry the literal
  `claude plugin install`; `pack-catalogue.md` and `adapt-to-project.md` say
  `/plugin install`; `install-routes.md` needs **two** entries — the route-table row
  (`/plugin install <pack>@<catalogue>`) and the marker-writer paragraph, which
  carries no such pattern and would otherwise pass green on the half this
  criterion calls the harder one;
  `tools/hooks/README.md` and `session-start.toml` say
  `<output>/claude-plugins/core/…`. A single `! grep -q 'claude plugin install'`
  passes green on six of the eight. Each entry also asserts the file **exists**,
  so a deleted or renamed site is not a silent pass, and the canonical
  precondition sentence in `install-routes.md`'s route table is asserted
  **present**. Sites: `README.md`;
  `docs-site/src/content/docs/getting-started/install.md`;
  `guides/_shared/explanation/install-routes.md` (route-table row **and** its
  marker-writer paragraph); `guides/_shared/explanation/pack-catalogue.md`;
  `guides/core/how-to/adapt-to-project.md`;
  `.github/workflows/publish-claude-plugins.yml`'s header ("adopters can install
  **any pack**"); `tools/hooks/README.md`;
  `packs/core/.apm/hook-wiring/session-start.toml`. The precondition is stated
  once, in `install-routes.md`'s route table.

- [x] **AC17 — The `--emit-install-routes` route summary stops printing a path
  that does not exist.** `commands/install.py:1723-1732` unconditionally emits
  `{output_root}/claude-plugins/{pack_name}/`; after the filter that directory is
  absent for the seven, including `core`.

- [ ] **AC18 — The six `render_pack` consumers are named and asserted.** *(deferred: plugin-upgrade-removal-artifact)*
  `commands/render.py`, `diff.py`, `init_state.py`, `upgrade.py`,
  `install.py --emit-install-routes`, `validate.py`. `init-state` writes rendered
  relpaths into the state file, so a pre-change `state.json` carries paths the
  render no longer produces and `upgrade` reads them as removals — exercised, not
  assumed.

- [x] **AC19 — Living statements the change falsifies are fixed, re-derived by
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

- [x] **AC20 — The engine change is carried by RFC-0008, with an erratum.**
  `tools/lint-catalogue-curation-guard.py` protects `packages/agentbundle/`
  (carve-outs: `build/recipes/` and `/tests/` only), so the committed changeset
  carries `Engine-Change-RFC: 0008`. The gate reads the *committed* range, so it
  fires after the first commit, not while editing.

  **RFC-0008 governs — it already owns this contract.** Its §"Enforces
  `allowed-scopes`" says: *"an adopter could install a repo-only pack
  (`allowed-scopes = ["repo"]`) at Claude-plugins user scope. The writer
  refuses-and-warns in that case."* This spec strengthens that control from
  writer-layer refusal to publish-time exclusion — the same decision, moved
  upstream, not a new one. No new RFC is opened.

  Because RFC-0008 is Accepted and therefore Frozen, the strengthening lands as
  an `## Errata` entry per RFC-0055's convention, recording that the
  writer-layer rail is now unreachable for repo-only packs (they are never
  published, so their marker never runs) and that publish-time exclusion is the
  primary control. RFC-0008 already carries one Approver-signed erratum entry, so
  this one crosses RFC-0055's two-entry threshold: it adds an authoritative
  current-state layer over the existing dated entry, Approver-signed.

  The guard only tests for the marker's *presence* — `Engine-Change-RFC: 9999`
  passes identically — so the verification is the trailer's presence plus a human
  reading the number, not a mechanical resolution.

- [x] **AC21 — The three `allowed-scopes` resolvers are pinned**
  — by a property test. `validate.py:_allowed_scopes(pack_data)` gates on
  `[pack.adapter-contract].version`; `install.py:_resolved_allowed_scopes(pack_install)`
  and `catalogue_tooling/lint.py:_profile_allowed_scopes(pack_toml)` read
  `[pack.install]` with no version gate — note the three take different argument
  shapes.

  The invariant is **user-membership implication**, not subset:

      "user" ∈ _allowed_scopes(p)  ⇒  "user" ∈ _resolved_allowed_scopes(p)
                                   ∧  "user" ∈ _profile_allowed_scopes(p)

  Subset is false on schema-valid input — verified by execution: with
  `[pack.adapter-contract]` absent and `[pack.install] allowed-scopes = ["user"]`,
  `_allowed_scopes` returns `["repo"]` while both siblings return `["user"]`, so
  `⊆` fails. Implication holds across the whole
  `contract-version × install-table` matrix and is the property that matters:
  the publish resolver may be *stricter* than the install gate, never looser.
  A later reconciliation that loosens it fires the test. Every shipped pack
  declares version ≥ 0.7, so the test runs over a synthetic matrix — asserting
  over shipped packs alone would be vacuously green.

- [x] **AC22 — Projected artifacts regenerated and committed.**
  `.claude-plugin/marketplace.json` is a `make build-check`-gated projected path.

- [x] **AC23 — Frozen specs carrying the dead premise get errata.**
  `docs/specs/claude-plugins-install-route/spec.md`,
  `docs/specs/claude-plugins-manifest-correctness/spec.md`, and
  `docs/specs/wire-session-start-hook/spec.md` are `Shipped` and frozen; each
  assumes `core` is plugin-installable. Errata only — bodies not edited.

- [x] **AC24 — The QA-matrix row is retired, and its frozen owner amended.**
  `docs/specs/adapt-to-project/notes/manual-qa-matrix.md`'s "claude-plugins
  install of core at project scope" row is **retired**, not re-pointed.
  `tests/unit/test_manual_qa_matrix_shape.py` cites it as required by AC19 of
  `docs/specs/claude-plugins-install-route/spec.md` — a frozen spec — so that
  spec's erratum explicitly retires the matrix requirement rather than the test
  silently dropping it. The test module's own docstring enumerates the same rows
  and is in scope.

- [x] **AC25 — RFC-0008's dormancy is recorded where the route is documented.**
  The install→adapt marker keeps being written; both readers
  (`packs/core/.apm/hooks/session-start.py` and the `adapt-to-project` skill)
  live in `core`, so on this route the automatic nudge is reachable only for an
  adopter who also has `core` at repo scope. Dormant on the user-scope path, not
  falsified; takes no erratum.

- [x] **AC26 — Two implementation guards, recorded because they change
  observable behaviour.** Added during EXECUTE, so they belong in the contract
  (`CONVENTIONS.md` § 4):

  - `--pack` on an **aggregate** recipe exits 1 with a named refusal.
    `make build RECIPE=marketplace PACK=x` previously succeeded and rewrote the
    shared marketplace down to one entry — a silent truncation of an artifact
    other packs share.
  - `aggregate_scope` outside `AGGREGATE_SCOPES` raises, validated at
    `run_recipe`'s boundary rather than only inside `aggregate_exit_code`, which
    per-pack recipes never reach.

## Assumptions

- **The seven source `plugin.json` files are retained deliberately.** They become
  consumer-less on this route but still feed Gate 2 (source-shape), which AC1
  does **not** narrow, and still require a version bump in lockstep with
  `pack.toml`. Recorded here rather than as a criterion: nothing can fail it, and
  the Testing Strategy should not promise an artifact that does not exist.



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
| AC19, AC22 | Goal-based | `! grep -q <pattern>` per site (not a bare no-match grep, which exits 1); agentbundle suite green after the seed edit + two-file bump; `make build-self` leaves the tree clean |
| AC20 | Goal-based | the trailer is present and the engine gate passes; the number is checked by review, not mechanically |
| AC21 | Unit | property test over the synthetic matrix |
| AC26 | Integration | `--pack` on an aggregate recipe exits 1; `run_recipe` raises on an unknown scope at a per-pack call site |
| AC23–AC25 | Goal-based | each named artifact carries its erratum / statement; matrix row and docstring retired |

## Blast radius

Re-derived by glob at task start, not trusted from this list. Tests asserting
`claude-plugins/<repo-only-pack>/` output: `tests/unit/test_render.py:33-34`,
`tests/unit/test_render_cmd.py:84-96`, `tests/build_pipeline/test_pipeline.py:77-80`,
`tests/build_pipeline/test_end_to_end_build.py:51,64`,
`tests/integration/test_install_repo_scope_per_adapter.py:238-241`,
`tests/integration/test_install_core_smoke.py:60`,
`tests/integration/test_build_derivation_claude_plugins.py` (derives
`FIXTURE_PACK_NAMES` by `iterdir()` and parametrises on it), and
`tests/integration/test_build_check_drift_gates.py:104,158`. **Second re-derivation query — direct callers of `_run_aggregate` and
`run_recipe`**, which break on arity and are not reachable from the path glob:
`tests/integration/test_marketplace_entry_validation.py:134` and
`tests/integration/test_marketplace_manifest_regression.py:186`. Plus any test
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
  denial protects **history**, not the tip — an ordinary fast-forward push can
  replace every file, which is exactly what the publish script does each run, and
  adopters resolve `ref: claude-plugins-dist` at the tip with no hash to compare
  against. The residual is tip *content* integrity plus the detection window.
- A per-pack content hash in the marketplace entry — the compensating control
  for the tip-content residual above: with directories removed at the same `ref`,
  an adopter can neither prove what they installed nor re-fetch it. Deferred
  rather than omitted because ADR-0072 constrains the entry schema to mirror an
  upstream contract we do not own, so a non-upstream field is a spike;
  `catalogue_tooling/package.py` already records a whole-marketplace
  `marketplace_digest` as a partial mitigation.
