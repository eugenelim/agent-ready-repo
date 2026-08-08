# Plan: Claude-plugin route — publish only user-capable packs

- **Spec:** [`spec.md`](spec.md)
- **Status:** Drafting <!-- Drafting | Approved | Executing | Done -->

> **Plan contract:** this is the implementation strategy. Unlike the spec, this
> document is allowed to change as you learn. When it changes substantially
> (a different approach, not just a re-ordering), note why in the changelog
> at the bottom.

> **Cross-reference convention.** Criteria are cited by **name**, not number.
> The predecessor spec's numeric references went stale three times under
> renumbering.

## Approach

One predicate, four sites, plus the docs that advertise the route. Nothing here
touches the hook pipeline — that is
[`../claude-plugin-hook-parity/`](../claude-plugin-hook-parity/plan.md), blocked
on a spike. Nothing in this spec depends on it.

The spec carries the substance; this plan **cites criteria by name and does not
restate them**. Three of the four disagreements the last review round found were
spec-vs-plan drift from restating — the two-file `core` bump, the retired-vs-
re-pointed QA row, and the writer count. Restatement is the hazard, so it is
gone.

Sequencing notes not in the spec:

- **T1 before T0.** The five build fixtures carry only a `[pack]` table, so the
  predicate resolves them to `["repo"]` and reddens the derivation, pipeline,
  end-to-end and drift-gate suites the moment the filter lands.
- **T0 owns every re-pin it breaks**, including the `render_pack`-consumer tests.
  Carving them out into T4b left the tree red between tasks —
  `tests/unit/test_render.py:33` drives a live `render_pack(packs/core)`. T4b
  keeps only the *new* characterization assertions.
- **The engine gate fires on the committed range**, so `Engine-Change-RFC: 0008`
  must be on the first commit that touches `build/main.py` or
  `build/self_host.py`, not added later.

## Constraints

- **ADR-0002** owns the scope model. **ADR-0072** governs the marketplace shape
  and names `_aggregate_marketplace` as the previously-missed writer.
- `.claude-plugin/marketplace.json` is a `make build-check`-gated projected path.
- `agentbundle` is stdlib-only.
- **Engine path-gate.** `tools/lint-catalogue-curation-guard.py` carves out only
  `build/recipes/` and `/tests/`; T0 edits `build/main.py` and
  `build/self_host.py`, so the committed changeset needs an
  `Engine-Change-RFC:` trailer. The gate fires on the *committed* range, so it
  surfaces after the first commit, not during editing. Resolved at PLAN (AC20).

## Tasks

### T0 — The predicate and its three writers
**Depends on:** T1 · **Mode:** TDD

**Tests:** `stub: pending` (materialise before EXECUTE) —
`packages/agentbundle/tests/unit/test_plugin_scope_filter.py` plus an
integration module. Covers: the predicate over an `allowed-scopes` ×
`adapter-contract.version` matrix including the absent-table case; **set
equality both directions on all three surfaces**, built into `tmp_path`; the
seven absences by name with the tripwire comment; the **envelope**
(`name`/`owner`/`description`) intact; the **property test** over the three
resolvers (`_allowed_scopes ⊆` the other two); the **empty-set** exit; the
publish script's predicate re-derivation and its entry-vs-directory equality;
Gate 1's narrowed `expected_packs`.

**Approach:** one predicate reusing `_allowed_scopes`, route-keyed on
`(recipe.name, recipe.adapter)`, applied at **four** sites: the recipe,
`_run_aggregate`, `_aggregate_marketplace` (overturning its "advertises every
pack" note at the note), and `run_build_check_drift_gates` **Gate 1**, whose
`expected_packs` is production code that would otherwise hard-fail seven times in
the required gate. Gate 1c (APM) and Gate 2 (source-shape) are not narrowed.

`_run_aggregate(recipe, output_dir)` gains a source-tree handle so scope resolves
from `packs/<slug>/pack.toml` rather than the projected copy — a signature
change; `run_recipe` already holds `packs_list`. Re-pin the blast-radius tests here,
re-derived by glob first. `publish_claude_plugins.py` keeps `catalogue-curation`
for its operator-only reason, gains the derived filter beside it, and its check
becomes a fail-loud assertion so a stale `dist/` is caught rather than
republished.

**Done when:** the unit and integration tests pass and `make build-self` +
`make build-check` are green with the regenerated marketplace committed.

### T1 — Fixture scope declarations
**Depends on:** none · *(runs first — the five build fixtures carry only a `[pack]` table, so the predicate resolves them to `["repo"]` and reddens the derivation, pipeline, end-to-end and drift-gate suites the moment T0 lands)* · **Mode:** Goal-based check

**Done when:** every fixture whose tests assert claude-plugins output declares
the lowest `[pack.adapter-contract] version` that carries **both**
`[pack.install]` and `user-scope-hooks` (the latter recorded at v0.3 in
`commands/validate.py`), pinned to an exact value in the task and justified in
one clause — and
`[pack.install] allowed-scopes` including `"user"`, and those tests pass.

**Approach:** derive the fixture list by **glob** over every fixture tree whose
tests assert claude-plugins output, not from a named five — `tests/fixtures/packs/cc-user-hooks`,
`tests/fixtures/install/catalogue/packs/alpha`, `tests/fixtures/list_packs/…`
and `tests/fixtures/local_scope/…` also carry no `plugin.json`. Five fixtures
under `build/tests/fixtures/packs/` lack
`[pack.adapter-contract]` and therefore resolve to `["repo"]`. `.../packs/core/`
additionally ships `.apm/hooks/` + `.apm/hook-wiring/`, so Rail B
(`build/scope_rails.py:check_hooks`) also requires
`[pack.install] user-scope-hooks = true` or `validate` refuses it. Declare, don't
rely on defaults.

### T2 — Site gating, with a consistency test
**Depends on:** T0 · **Mode:** TDD

**Tests:** `stub: pending` (materialise before EXECUTE) — a test reading each `packs/<slug>/pack.toml` and
asserting `web/src/content/packs/<slug>.md`'s user-capability field equals
`"user" in allowed-scopes`, plus the built-output assertion. Reachable from
**not** a bare pytest hung off `make build-check` — that target runs no pytest,
and in `build-check.yml` it executes before pytest is installed. The tripwire
lands as a `tools/lint-*.py` + `tools/test-lint-*.py` pair registered in
`build_gate_chain.py`, with the `lint-ci-parity` update that requires.
Verification is by **mutation**: desync a `web/` frontmatter value, assert
`make build-check` exits non-zero. The built-output half needs a Node toolchain
in the required job — an `Ask first` boundary, resolved before wiring.

**Approach:** add the field to `web/src/content.config.ts` (required, no
default, so the Astro build fails on omission) and each pack's markdown file; gate `[pack].astro` and `catalogue/index.astro` on it, **not** on `scope`
(which is `default-scope` and would hide `product-documentation`).

### T3 — Prose docs
**Depends on:** T0 · **Mode:** Goal-based check

**Done when:** a scripted assertion — `! grep -q` form over an enumerated site
list, not the failure-prone absence form (`grep -c` exits 1 on no-match) —
passes. Search roots widen beyond the spec's list: also
`.github/workflows/publish-claude-plugins.yml` (its header comment says
"adopters can install **any pack**"), `tools/hooks/README.md`, and
`packs/core/.apm/hook-wiring/session-start.toml`. A bare grep cannot decide
"for a repo-only pack" — the assertion enumerates the sites and the expected
state of each.

**Approach:** re-derive the file list by grep. State the precondition once in
`install-routes.md`'s route table; fix its marker-writer paragraph and every
living architecture statement the grep finds. **Sub-step:**
`docs/CONVENTIONS.md:597` is seed-projected from
`packs/core/seeds/docs/CONVENTIONS.md`, so it is edited in the seed, then
`make build-self`, then the `core` version bump AC19 specifies — **two** files,
since AC6 deletes `core`'s marketplace entry in the same PR. Verification is the
agentbundle pytest suite, not `build-check`, per AC19. Record RFC-0008's dormancy in
`docs/architecture/agentbundle.md`.

### T4 — Errata and the QA matrix
**Depends on:** T0 · **Mode:** Goal-based check

**Done when:** each of the three frozen specs named in AC23 carries an erratum;
the QA-matrix row and its shape test (including the module docstring) are gone;
and RFC-0008 carries the erratum AC20 requires.

**Approach:** errata only — frozen bodies are not edited. The QA-matrix row is
**retired**, not re-pointed (AC24), and the erratum on
`claude-plugins-install-route` explicitly retires the AC19 requirement the shape
test cites, so the test is not silently dropping a live obligation.

### T4b — `render_pack` consumers
**Depends on:** T0 · **Mode:** Integration (characterization)

**Tests:** `stub: pending` (materialise before EXECUTE) — each of `commands/render.py`, `diff.py`,
`init_state.py`, `upgrade.py`, `install.py --emit-install-routes`, and
`validate.py` asserted for its expected output per projection; a pre-change
`state.json` carrying old relpaths exercised through `upgrade`.

**Approach:** assertions only — characterization of behaviour T0 ships, not
red-green. T0 owns re-pinning the existing consumer tests; this task adds only
the *new* assertions, so the tree is never red between the two. Also covers the
`--emit-install-routes` route-summary rail (`commands/install.py:1723-1732`),
which prints a path that no longer exists. The recipe-level filter removes whole
subtrees from six consumers' output; `init-state` writes those relpaths into the state
file, so the pre-change case is the one most likely to surprise an adopter.

### T5 — Changelogs
**Depends on:** T0 · **Mode:** Goal-based check

**Done when:** both `[Unreleased]` sections carry AC14's delisting notice, and
`packages/agentbundle`'s additionally carries AC13's engine note for
self-hosting adopters — the filter changes `run_self_host` behaviour for anyone
outside this repo.

### T6 — Real client
**Depends on:** T0, T2, T3, T5 · **Mode:** Visual / manual QA

**Done when:** run against a **local marketplace path** (the repo-root
marketplace resolves from `main` and the dist branch is written on push, so
neither reflects the PR); a dropped pack confirmed absent against
`claude` 2.1.223; a post-delist `claude plugin update` and marketplace refresh
recorded, since that is the observation AC14's remedy is written against; and an install-then-delist run records what the client does to
an installed-but-delisted plugin. Transcripts below. **Scope boundary:** one
dropped pack and one user-capable pack are exercised by hand; the other 19 are
covered by T0's assertions. The **post-merge** re-run against the published
marketplace is a separate recorded step. **This PR adds the backlog slug** —
`workspace.toml [backlog].open` has no entry for it today, so the claim would
otherwise be false on landing.

## Risks

- **Delisting is not revocation.** Adopters keep a pinned copy running. The
  changelog remedy is the only signal, and it is in a repo their client does not
  read. Accepted; recorded in the spec.
- **No compensating control ships for unrestricted pushes to
  `claude-plugins-dist`.** Force-push and deletion are denied; ordinary pushes
  are not, and the marketplace `ref` stays mutable. Deferred in the spec.
- **The `web/` field is hand-copied.** T2's consistency test is what makes that
  survivable; without it the site can advertise a repo-only pack indefinitely.

## Verification log

_(T6 transcripts land here.)_

## Changelog

- **2026-08-07** — split out of `docs/specs/claude-plugin-hook-parity/` after
  five review rounds. The scope filter and the docs fix survived rounds 4 and 5
  unchallenged and are independently shippable; the hook compiler kept
  generating new findings each round and now blocks on a spike. Carries forward
  every verified correction from those rounds: `_aggregate_marketplace` as the
  third writer, `_allowed_scopes`' real gate, the hand-authored `web/`
  frontmatter, the fail-loud publish check, and revocation-before-remedy.
