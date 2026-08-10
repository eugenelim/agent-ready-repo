# Plan: Claude-plugin route — publish only user-capable packs

- **Spec:** [`spec.md`](spec.md)
- **Status:** Done <!-- Drafting | Approved | Executing | Done -->

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
  surfaces after the first commit, not during editing. Resolved at PLAN — see the spec's *engine change is carried by RFC-0008* criterion.

## Task status

All four waves ran, and every task's Done-when is met.

| Task | State |
|---|---|
| T1 fixtures | done |
| T0 predicate, four sites | done — membership asserted on all three surfaces, both directions, expected side enumerated |
| T1b membership lint | done — joined by `lint-plugin-roster`, which enumerates literally rather than deriving both sides |
| T2 site gating | done — built-output check in `pages.yml` per the accepted Node decision |
| T3 prose docs | done — eight sites, gated by `lint-plugin-route-docs` per-site tuples |
| T4 errata | done — RFC-0008 carries both erratum layers |
| T4b render_pack consumers | done — six consumers plus the pre-change `state.json` case |
| T5 changelogs | done |
| T6 real client | done — transcripts below, alongside the two mutation transcripts |

Five gates now guard the route, each with a sibling test in the chain:
`test-pack-scope` (differential, against the canonical resolver),
`lint-plugin-membership` (derived), `lint-plugin-roster` (literal),
`lint-plugin-route-docs` (per-site), and `test-publish-claude-plugins` (the
three push-time refusals).

## Tasks

### T1 — Fixture scope declarations
**Depends on:** none · *(runs first — the five build fixtures carry only a `[pack]` table, so the predicate resolves them to `["repo"]` and reddens the derivation, pipeline, end-to-end and drift-gate suites the moment T0 lands)* · **Mode:** Goal-based check

**Done when:** every fixture whose tests assert claude-plugins output carries
`.claude-plugin/plugin.json` (the derived set's condition 2, which the recipe
writer does not require today) and declares
`[pack.adapter-contract] version = "0.3"` — the lowest version carrying both
`[pack.install]` and `user-scope-hooks` (`commands/validate.py:597`) — and
`[pack.install] allowed-scopes` including `"user"`, and those tests pass.

**Approach:** derive the fixture list by **glob** over every fixture tree whose
tests assert claude-plugins output, not from a named five — `tests/fixtures/packs/cc-user-hooks`,
`tests/fixtures/install/catalogue/packs/alpha`, `tests/fixtures/list_packs/…`
and `tests/fixtures/local_scope/…` also carry no `plugin.json`. Five fixtures
under `tests/build_pipeline/fixtures/packs/` lack
`[pack.adapter-contract]` and therefore resolve to `["repo"]`. `.../packs/core/`
additionally ships `.apm/hooks/` + `.apm/hook-wiring/`, so Rail B
(`build/scope_rails.py:check_hooks`) also requires
`[pack.install] user-scope-hooks = true` or `validate` refuses it. Declare, don't
rely on defaults.

### T0 — The predicate and its four sites
**Depends on:** T1 · **Mode:** TDD

**Tests:** `stub: true` — `packages/agentbundle/tests/unit/test_plugin_scope_filter.py`
(materialised: the `_allowed_scopes`-gate and implication assertions pass, pinning
premises the spec depends on; the predicate, `aggregate_scope` and emptiness
assertions fail by name until the filter lands — suite exits 1) plus an
integration module. Covers: the predicate over an `allowed-scopes` ×
`adapter-contract.version` matrix including the absent-table case; **set
equality both directions on all three surfaces**, built into `tmp_path`; the
seven absences by name with the tripwire comment; the **envelope**
(`name`/`owner`/`description`) intact; the **property test** over the three resolvers — user-membership
*implication*, not subset (subset is disproved; see the criterion); all three **emptiness** modes (see AC12 — every one of them
warns and continues; the catalogue names each exclusion and says so when the
filter leaves it empty, single-pack is silent, self-host warns inline); the
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

### T1b — The membership lint pair
**Depends on:** T0 · **Mode:** TDD

**Tests:** `stub: true` — `tools/test-lint-plugin-membership.py`, the sibling the
gate chain requires.

**Done when:** `tools/lint-plugin-membership.py` is registered in
`tools/repo/build_gate_chain.py`, `lint-ci-parity` is green, and the
distinguishing mutation (one the projected-path drift gate cannot see) makes
`make build-check` exit non-zero **naming this gate** in its output.

**Approach:** the membership tripwire cannot ship as a pytest — `make
build-check` runs no pytest, so the required gate would never run it. This is
its own task rather than a bullet in T0 because T0's Done-when ("tests pass,
`build-check` green") is satisfied without it ever being registered.

### T2 — Site gating, with a consistency test
**Depends on:** T0 · **Mode:** TDD

**Tests:** `stub: true` — a test reading each `packs/<slug>/pack.toml` and
asserting `web/src/content/packs/<slug>.md`'s user-capability field equals
`"user" in allowed-scopes`, plus the built-output assertion.

It is **not** a bare pytest hung off `make build-check` — that target runs no pytest,
and in `build-check.yml` it executes before pytest is installed. The tripwire
lands as a `tools/lint-*.py` + `tools/test-lint-*.py` pair registered in
`build_gate_chain.py`, with the `lint-ci-parity` update that requires.
Verification is by **mutation**: desync a `web/` frontmatter value, assert
`make build-check` exits non-zero.

The built-output half does **not** go in the required job — the Node question
was asked and declined (2026-08-08). It lands in `pages.yml`, with
`packs/**/pack.toml` added to that workflow's path filter so it fires on both
sides of the drift. The residual is recorded in the criterion.

**Done when:** the consistency lint pair is registered in
`tools/repo/build_gate_chain.py` with `lint-ci-parity` green and a frontmatter
desync makes `make build-check` exit non-zero; `pages.yml` gains
`packs/**/pack.toml` in its path filter and a built-output check showing the
install command for a user-capable pack and not for a repo-only one.

**Approach:** add the field to `web/src/content.config.ts` (required, no
default, so the Astro build fails on omission) and each pack's markdown file; gate `[pack].astro` and `catalogue/index.astro` on it, **not** on `scope`
(which is `default-scope` and would hide `product-documentation`).

### T3 — Prose docs
**Depends on:** T0 · **Mode:** Goal-based check

**Done when:** the scripted assertion passes. It enumerates
`(path, pattern, expected state)` **per site** — the sites do not share a
pattern, so one `! grep -q 'claude plugin install'` would pass green on six of
eight — and asserts each file exists, so a rename is not a silent pass. Search
roots widen beyond the spec's list: also
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

**Tests:** `stub: true` — each of `commands/render.py`, `diff.py`,
`init_state.py`, `upgrade.py`, `install.py --emit-install-routes`, and
`validate.py` asserted for its expected output per projection; a pre-change
`state.json` carrying old relpaths exercised through `upgrade`.

**Done when:** each of the six consumers is asserted per projection and the
pre-change `state.json` case passes through `upgrade`.

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
marketplace is a separate recorded step. **This PR registers its deferred work in `workspace.toml [backlog].open` under
`source = "spec/claude-plugin-route-scope"`, which is the canonical register** —
this plan deliberately does not re-list the slugs, because the three prose
copies of that list drifted apart before round nine caught it. No
`(deferred: <slug>)` AC markers: `docs/CONVENTIONS.md` pins that marker to an
*unchecked* criterion, and the deferred items either ship their in-code half
(so the criterion is `[x]`) or correspond to no criterion at all.


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

### Mutation transcripts (AC9)

Each names the gate that produced the non-zero exit — a green `make build-check`
proves the target passes, not that a new check ran. Both reverted after.

```
### Mutation 1 — site frontmatter desync
$ sed -i '' 's/pluginInstallable: false/pluginInstallable: true/' web/src/content/packs/core.md
  # BSD sed (macOS): the empty suffix arg is required — without it sed
  # takes the filename as the backup suffix and edits nothing, which
  # would make this transcript unreproducible on the machine it was
  # captured on. GNU sed: drop the ''.
$ python3 tools/lint-site-scope-parity.py --root .
exit=1
lint-site-scope-parity: core.md says pluginInstallable: true but
  packs/core/pack.toml resolves allowed-scopes=['repo'] (user-capable: false)

### Mutation 2 — roster membership
$ # append a `core` entry to .claude-plugin/marketplace.json
$ python3 tools/lint-plugin-roster.py --root .
exit=1
lint-plugin-roster: 'core' is published but is pinned repo-only. If you widened
  its allowed-scopes, that publishes its code to a public marketplace …
```

**Through the required gate.** Both mutations were also run under
`tools/repo/build_gate_chain.py build-check` — the chain `make build-check`
invokes:

```
$ sed -i '' 's/pluginInstallable: false/pluginInstallable: true/' web/src/content/packs/core.md
  # BSD sed (macOS): the empty suffix arg is required — without it sed
  # takes the filename as the backup suffix and edits nothing, which
  # would make this transcript unreproducible on the machine it was
  # captured on. GNU sed: drop the ''.
$ python3 tools/repo/build_gate_chain.py build-check --packs-dir packs --output-dir dist
…
68 passed, 0 failed
build chain: ✖ lint-site-scope-parity failed (exit 1)
exit 1
```

The chain stops at its first failure, so the `68 passed` line is load-bearing:
`test-pack-scope`, both membership steps, both roster steps,
`test-publish-claude-plugins` and both route-docs steps ran and passed before
this one fired. That establishes reachability from the required gate, not just
that the lint works standalone — which is what AC9 asks for.

The one thing this shape cannot do is isolate a *late* step: a mutation
targeting the roster gate trips the projected-path drift gate first, because
`.claude-plugin/marketplace.json` is regenerated into a shadow tree and diffed.
The synthetic-tree sibling tests cover those in isolation.


Real-client run against `claude` 2.1.223, pre-merge, using a **local
marketplace path** — the repo-root marketplace resolves from `main` and the
dist branch is written on push, so neither reflects this PR. Throwaway
`CLAUDE_CONFIG_DIR`.

**A dropped pack is not installable.**

```
$ claude plugin install core@agent-ready-repo
✘ Failed to install plugin "core@agent-ready-repo": Plugin "core" not found in
  marketplace "agent-ready-repo".
```

**A user-capable pack installs, at user scope.**

```
$ claude plugin install architect@agent-ready-repo
✔ Successfully installed plugin: architect@agent-ready-repo (scope: user)

$ claude plugin details architect@agent-ready-repo
Architect (architect) 0.14.3
  Skills (3)  architect-design, architect-diagram, architect-review
  Agents (1)  design-reviewer
  Hooks (1)  SessionStart  (harness-only — no model context cost)

$ claude plugin validate /tmp/t6/claude-plugins/architect
✔ Validation passed
```

**Delist behaviour — the observation that decides the remedy.** Removed the
entry and the directory, as a publish does, then refreshed:

```
$ claude plugin marketplace update agent-ready-repo
✔ Successfully updated marketplace: agent-ready-repo

$ claude plugin list
  ❯ architect@agent-ready-repo
    Scope: user
    Status: ✘ failed to load
    Error: Plugin architect not found in marketplace agent-ready-repo

$ claude plugin update architect@agent-ready-repo
✘ Failed to update plugin: Plugin "architect" not found

$ claude plugin uninstall architect@agent-ready-repo
✔ Successfully uninstalled plugin: architect (scope: user)
```

**What this settles — and its precondition.** The transcript runs
`marketplace update` *first*. After that refresh the delisted plugin fails to
load, loudly, and `update` refuses. **Before** it, the cached copy keeps
loading and its hooks keep running, which is the AST07 stale-copy condition —
so the remedy is uninstall, not wait. The
enablement entry survives until uninstalled, so the residual is a broken entry
in the adopter's plugin list, not silent execution of stale code. That is
milder than the changelogs originally assumed, and they were corrected to state
the observed behaviour rather than the feared one. `claude plugin uninstall`
remains step one of the remedy — it is what clears the dead entry.

## Changelog

- **2026-08-07** — split out of `docs/specs/claude-plugin-hook-parity/` after
  five review rounds. The scope filter and the docs fix survived rounds 4 and 5
  unchallenged and are independently shippable; the hook compiler kept
  generating new findings each round and now blocks on a spike. Carries forward
  every verified correction from those rounds: `_aggregate_marketplace` as the
  third writer, `_allowed_scopes`' real gate, the hand-authored `web/`
  frontmatter, the fail-loud publish check, and revocation-before-remedy.
