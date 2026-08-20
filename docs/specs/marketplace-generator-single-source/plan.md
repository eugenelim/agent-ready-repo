# Plan: marketplace generator single source

- **Spec:** [`spec.md`](spec.md)
- **Status:** Done <!-- Drafting | Approved | Executing | Done -->

> **Plan contract:** this is the implementation strategy. Unlike the spec, this
> document is allowed to change as you learn — while its Status is `Drafting`
> or `Executing`.

## Approach

`catalogue.toml` says `claude-plugin-branch = "main"`. ADR-0072 pins the
advertised `ref` to `claude-plugins-dist` and rests that decision on branch
protection, which exists for `claude-plugins-dist` and not for `main`. So the
config value is a latent contradiction of an accepted ADR; the reason it has not
bitten is that the only build path reading it is the one nothing publishes from.

That is what produces `CAT-V-014`. `make build` runs `python -m
agentbundle.build build --packs-dir packs --output-dir dist` (`Makefile:24`),
whose `cmd_build` reads the module constants `_DIST_BRANCH` and
`_MARKETPLACE_DESCRIPTION`. The verifier's drift step builds a fresh tree
**in-process** — `build_catalogue(root, output=fresh_dir, pack=pack)` at
`verify.py:1330` — and `build_catalogue` monkey-patches those two globals from
`catalogue.toml` (`catalogue_tooling/build.py:106-109`) before calling the same
`cmd_build`. Correcting the config value clears the diagnostic on its own. The
second, independent defect is that nothing *keeps* the statements in agreement,
which is why the divergence sat undetected.

The instinct is to remove the duplication by making `catalogue.toml` the
authority. That is the wrong change here, and not for diff-size reasons.
`render.py`'s `render_pack_to_dir` / `render_packs_to_dir` call `run_recipe`
directly (`render.py:78,125`), so six shipped entrypoints — `install`, `upgrade`,
`render`, `diff`, `init_state`, `validate --strict` — reach
`derive_projectable_subset` and `_run_aggregate` without passing through
`cmd_build` at all; a resolution site in `cmd_build` would leave all six on the
constants while an acceptance criterion claimed otherwise. And `toml_emit.py:100`
scaffolds an adopter's `claude-plugin-branch` as `"main"`, so making config
authoritative would make an adopter's own `make build-self` advertise `ref: main`
with `path: <pack-name>`, which does not exist on a tree whose packs live under
`packs/`. That is a regression introduced into an adopter-facing surface under
cover of a drift fix.

So: correct the value, and install the control the repository already uses when a
fact must be stated in more than one place — a parity gate, following
`tools/test_contract_parity.py`. The branch is anchored five ways, including to
the ruleset's `branch.target` and to the committed marketplace an adopter
actually resolves, because two copies of a name agreeing tells you nothing if a
single change moves both. The one removable duplicate — `self_host.py`'s
hardcoded description default — is deleted rather than anchored.

The riskiest part is the parity check itself. An equality assertion across nine
sources is the classic shape that passes without being able to fail, and its
`ast` reads bridge "the constant's source text" to "the value the build emits" by
an assumption about source shape. T2 therefore does not consider the work done
until every anchor and every structural failure mode has an automated probe that
has been observed red.

## Constraints

- **ADR-0072** pins the advertised `ref` to `claude-plugins-dist` and makes branch
  protection on it a precondition of the decision. `_DIST_BRANCH` is that pin's
  home; this plan does not move it.
- **ADR-0079** restricts who may update the publish branch (the publisher App
  identity), the other half of the compensating control.
- The catalogue schema lists `claude-plugin-branch` and `marketplace-description`
  under `[catalogue.build]`'s `required`, so neither key can be deleted.
- `docs/CONVENTIONS.md` § *Stub → EXECUTE handoff* requires a TDD task's
  construction test to be materialised at PLAN as a compiling red stub.

## Construction tests

All of them live in the per-task `Tests:` subsections. Summary: T1 writes the parity
check as a compiling red stub and corrects the drifted values; T2 wires it into the
gate chain; T3 adds the mutation suite — one probe per anchor the check reads and one
per failure mode the spec enumerates, plus the `sys.modules`-injection probes that
are the only shape reaching layer 1; T4 runs the end-to-end recipe in both directions
and completes the record. Counts live in the spec and in `ANCHOR_PATHS`; they are
not restated here, because three copies of one roster drifted apart once already.

Task order note: the gate asserts its own membership in both pytest lists, so it is
red until T2 wires it. T3's fixture is therefore a straight copy of a clean tree only
after T2 — which is why the mutation suite follows the wiring rather than preceding it.

**Integration tests:** none — every check reads committed sources or a fixture built
from the anchor paths.
**Manual verification:** T4's `rm -rf dist && make build && SKIP_SAST=1 make
build-check`, run once green and once with the branch reverted, with observed
output recorded.

## Design (LLD)

### Design decisions

- **A parity gate, not a resolution refactor.** Where the schema requires a key
  and an ADR pins a constant, one home is impossible; the enforceable property is
  that every statement agrees. Traces to: AC5, AC4, AC5.
  - *Rejected: resolve both values from `catalogue.toml` inside `cmd_build`.*
    Leaves `render.py`'s six shipped entrypoints on the constants, so the
    "one source" criterion would have shipped false.
  - *Rejected: resolve inside `run_recipe` / `_run_aggregate` so every writer is
    downstream.* The coherent version of the refactor and the right shape for the
    follow-up, but it changes adopter `build-self` output via `toml_emit.py`'s
    `"main"` default and crosses the spec's "Ask first" boundary. Registered as
    `marketplace-envelope-config-authority`.
  - *Rejected: set `catalogue.toml`'s `claude-plugin-branch = ""`.* This is the
    cheapest option and the only one that makes "single source" literally true:
    the schema requires the *key*, not a non-empty value, and
    `catalogue_tooling/build.py:106`'s truthiness guard then leaves the
    ADR-pinned constant standing — clearing `CAT-V-014` with no second statement
    of the value at all. Rejected because it makes the design depend on a
    fail-open this plan simultaneously registers as a bug
    (`catalogue-branch-empty-falls-back-to-upstream-constant`), and it would break
    the moment that bug is fixed with a `minLength: 1`. Building on a defect you
    have already agreed to remove is not a single source; it is a hidden
    dependency between two open items. Recorded because it is the first thing a
    reader will propose.
  - *Rejected: make `_aggregate_marketplace`'s `description` default resolve from
    config at call time.* Python evaluates default arguments once at `def` time,
    so a default cannot carry call-time resolution — the mechanism
    `derive_projectable_subset` uses is a module-global read in the body. Moot
    now that no call-time resolution is wanted; recorded so the follow-up does not
    repeat it.
- **Delete the removable duplicate rather than anchor it.**
  `self_host.py:655-657` hardcodes the description as a parameter default that no
  caller overrides (`:1326`, `:1397`), so *that literal* — not
  `_MARKETPLACE_DESCRIPTION` — is what writes the committed root marketplace.
  `self_host.py` imports *from* `build.main` at `:60-66` — but that block carries
  only public names (`CONTRACT_PATH`, `REPO_ROOT`, `derive_projectable_subset`,
  `discover_packs`, `validate_pack_uniqueness`), **not** `_MARKETPLACE_DESCRIPTION`,
  which appears nowhere in the module. T1 must extend that block, or the default
  raises `NameError` at import. Verified on a fixture tree before applying. Def-time evaluation is correct here: the
  constant is the pin's home and no call-time resolution is wanted. The check then
  asserts that default is an `ast.Name`, not a `Constant`, so the duplicate cannot
  be reintroduced. Traces to: AC6.
- **Anchor `source.url`, not only `source.ref`.** Branch protection is scoped to a
  repository, so ref parity against a url no ruleset governs delivers none of
  ADR-0072's property: a one-line `[pack.links].repository` edit would have
  adopters clone and execute a third-party repo at a branch name that looks
  protected. The only prior assertion on that field checks
  `startswith("https://github.com/")` — any owner
  (`test_marketplace_manifest_regression.py:293`). Traces to: AC6.
- **Compare the resolved value; keep the literal check as a second layer.** The
  authority is `importlib.import_module(...)` plus `getattr` — the value the build
  actually emits — because four review rounds of a static reader kept surfacing
  admitted rebinding forms (`AnnAssign` shadow, then `import`, `def`, `class`,
  `except as`, `case`, `del`, `globals().update`, `vars()`, `setattr(sys.modules)`,
  `exec`). Enumerating rebinding syntax was the wrong instrument for "what does the
  build emit"; reading the resolved value answers it directly and does not enumerate.
  The literal check is retained because a resolved value alone would accept
  `_DIST_BRANCH = os.environ.get(...)` — correct today, environment-dependent
  tomorrow. Note `import agentbundle.build.main as m` binds the re-exported `main()`
  *function*, not the submodule; `importlib.import_module` is required, the trap
  `catalogue_tooling/build.py:68-71` documents. Traces to: AC7.
- **Resolve symbols by whole-tree binding scan for the second layer.**
  `build/main.py:306` and the publisher read these names as globals at call time,
  so the last binding executed wins. Probed: with `_DIST_BRANCH = "..."` followed
  by `_DIST_BRANCH: str = "attacker"`, a first-match reader returns the correct
  literal and the gate goes green while the build emits the shadow. Traces to: AC7.
- **Anchor to `branch.target` and to the published artifact.** The ruleset file is
  the desired-state document; the committed marketplace's fourteen
  `plugins[].source.ref` values are what an adopter resolves. The latter is
  otherwise guarded only by `CAT-V-015` (`verify.py:1485-1509`), which returns
  `[]` when `config is None` or `.adapt-discovery.toml` is absent — the same
  fail-open shape this spec exists to compensate for. Traces to: AC5.
- **The check lives in `tools/`, wired like `test_contract_parity.py`.** It
  asserts a repository-level invariant across `catalogue.toml`, `.github/`,
  `tools/`, and the package — not a package-internal one — so it does not belong
  in `packages/agentbundle/tests/`, which must stay runnable against the package
  alone. Traces to: AC9.
- **Per-source readers take a root path.** Every anchor is read by a function
  taking the tree root, so T2's probes can point the whole check at a temp copy.
  This is what makes falsifiability automated and repeatable instead of a one-time
  hand-run log that mutates tracked security-control files in the live worktree.
  Traces to: AC8.

### Failure, edge cases & resilience

- Read every source with a parser, never a line grep: `tomllib` for
  `catalogue.toml`, `json` for the two JSON files, `ast` for the three Python
  symbols. A `grep '^claude-plugin-branch'` matches the key under any table.
  Layer 1 *does* import `build.main`, and that coupling is deliberate: it is what
  makes the comparison read the value the build emits rather than the value the
  source appears to hold. The coupling has a precondition — the import must resolve
  *this* checkout — which is asserted, not assumed, after an editable install was
  measured resolving a sibling worktree.
- **Symbol resolution is the gate's weakest bridge and is specified, not assumed.**
  For each of `_DIST_BRANCH`, `BRANCH`, and `_MARKETPLACE_DESCRIPTION`: exactly
  one module-scope binding — an `ast.Assign` or `ast.AnnAssign`; an annotated
  assignment is accepted — whose value is an `ast.Constant` of type `str`.
  Zero matches, more than one, an assignment nested inside `if` / `try` / a
  function, or a non-literal value (`os.environ.get(...)`, a `BinOp` — which `ast`
  does *not* fold, unlike implicit adjacent-string concatenation) each fail
  loudly. A first-match read would silently pin the wrong assignment; a
  "find any Constant" read would return a default that is not what the build
  emits.
- For `_aggregate_marketplace`'s `description` default: exactly one module-level
  `FunctionDef` of that name, with a `description` parameter whose default is an
  `ast.Name` bound to `_MARKETPLACE_DESCRIPTION`. A `Constant` there is a
  reintroduced duplicate and fails.
- `branch.target` carries a `refs/heads/` prefix the other sources do not. Strip
  exactly that prefix and fail if it is absent, rather than tolerating either
  form — tolerance would let a bare-name `target` pass while the ruleset guarded
  nothing.
- The committed marketplace's `plugins[].source.ref` is a list of fourteen values.
  Assert every one equals the branch and that the list is non-empty; an empty
  `plugins` array must fail rather than trivially satisfying "all agree".

## Tasks

### T1: the advertised branch agrees with the protected branch and the published artifact

**Depends on:** none · **Verification mode:** TDD · `stub: true`

**Touches:** tools/test_marketplace_envelope_parity.py, catalogue.toml, packages/agentbundle/agentbundle/build/self_host.py

**Tests:** materialised as a compiling red stub before any fix
(`tools/test_marketplace_envelope_parity.py`, markers `# STUB: AC5` / `AC4` /
`AC5`).
- `# STUB: AC5` — the branch is identical across all five anchors. Red on the
  current tree (`main` vs `claude-plugins-dist`).
- `# STUB: AC6` — the description is identical across its three anchors, and
  `_aggregate_marketplace`'s `description` default is the name
  `_MARKETPLACE_DESCRIPTION`. Red on the current tree twice over: the config text
  differs, and the default is still a literal.
- `# STUB: AC7` — the reader contract: one module-level `str`-`Constant`
  assignment per symbol; a `branch.target` without `refs/heads/` fails.

**Approach:**
- Write the check first with per-source readers taking a root path; confirm every
  assertion is red for the right reason before changing anything.
- Set `claude-plugin-branch = "claude-plugins-dist"`, with a comment naming
  ADR-0072 and the parity gate as the two reasons it cannot drift.
- Set `marketplace-description` to the published text.
- Add `_MARKETPLACE_DESCRIPTION` to the existing
  `from agentbundle.build.main import (...)` block at `self_host.py:60-66`. This
  step is not optional: without it the next step is an import-time `NameError`,
  and the by-name shape check alone cannot see that.
- Change `_aggregate_marketplace`'s `description` default to
  `_MARKETPLACE_DESCRIPTION` and confirm `make build-self FORCE=1` leaves the
  committed root marketplace byte-identical (`git diff --exit-code` on that path)
  — `FORCE=1` because `self_host.py:1257-1263` returns 2 without writing on a
  dirty tree, so without it the diff would be empty for the wrong reason.

**Done when:** the branch, description, `self_host` default and import anchors all
agree, and the gate's only remaining failure is the wiring assertion T3 satisfies —
the gate asserts its own membership in both pytest groups, so it is red by design
until wired. The committed root marketplace is byte-unchanged.

### T2: the check is run by a gate

**Depends on:** T1 · **Verification mode:** goal-based check

**Touches:** Makefile, .github/workflows/build-check.yml

**Tests:**
- `grep -c test_marketplace_envelope_parity` returns 1 for the Makefile and 1 for
  `build-check.yml` (AC9).
- The Makefile group's file list and the `build-check.yml` step's file list are
  identical as sets (AC9). Note: `tools/lint-ci-parity.py` is *not* coverage here
  — it holds a disposition per step and its own docstring says it does not catch a
  gate added inside a step that already has one, so it passes identically before
  and after. It is run as a no-regression check only.

**Approach:**
- Append the file to the Makefile `test` target's final pytest group, beside
  `tools/test_contract_parity.py`.
- Append the same path to the parallel list in the `build-check.yml` step
  "pytest catalogue-test carve-out destinations (RFC-0082)", keeping the two
  lists identical.

**Done when:** both greps return 1 and the two lists match as sets.

### T3: every anchor and every structural failure mode has a probe that goes red

**Depends on:** T2 · **Verification mode:** TDD, demonstrated red

**Touches:** tools/test_marketplace_envelope_parity.py, docs/specs/marketplace-generator-single-source/notes/verification.md

**Tests:**
- One probe per anchor read by `check_envelope_parity`, and one per failure mode
  AC5 enumerates — referenced rather than restated here, so the roster has one home
  and cannot drift against the spec. Each materialises only `ANCHOR_PATHS` into a
  fixture, mutates one source, and asserts the check fails naming that source.
- Every attack payload the pre-EXECUTE reviewers demonstrated is included as a named
  probe, so each is regression-protected rather than fixed once. Fifteen were
  verified in an ad-hoc harness during PLAN; that harness is not in the repository,
  so until this task lands the protection is a claim rather than an inheritance: import/`def`
  shadow of `_DIST_BRANCH` and `BRANCH`, a second `_MARKETPLACE_DESCRIPTION` import
  in `self_host.py`, a `setattr(sys.modules[...])` rebind, a duplicate-named entry
  carrying a hostile `ref`, a hostile `source.url`, a coordinated `repo` move to a
  confusable owner, an extra redirect key on `source`, symmetric pytest-list
  narrowing plus a one-sided deletion, `branch.target == "refs/heads/"`, and the
  gate removed from the Makefile group.
- A positive control: the unmutated temp copy passes, so a probe that fails for
  the copy mechanism rather than the mutation is caught.

**Approach:**
- Follow `tools/test-lint-claude-plugin-publish-control.py`'s shape — drive
  `check_envelope_parity(root)` over mutated fixtures rather than re-implementing
  its logic in the test. That entry point exists precisely so a probe cannot
  degenerate into a mirror test asserting its own arithmetic.
- Materialise the fixture from `ANCHOR_PATHS` by content copy (`shutil.copyfile`,
  never `copytree`): the check reads eight files, while the tree is ~70 MB before
  `docs-site/node_modules` and carries three symlinked context files
  (`CLAUDE.md`, `docs-site/CLAUDE.md`, `web/CLAUDE.md`) that a symlink-following
  copy would resolve back into the live worktree — writing a probe's mutation
  through to the tracked file, which is the failure mode this replaced.
- Never mutate the live worktree; every probe operates on the fixture.
- Record the measured mutation-survival number in `notes/verification.md` as
  evidence, not as the coverage — the suite is the coverage.

**Done when:** every probe is green (i.e. every mutation is detected), the
positive control passes, and `notes/verification.md` records the run.

### T4: the drift gate is satisfiable, and the record is complete

**Depends on:** T3 · **Verification mode:** goal-based check, demonstrated red

**Touches:** docs/specs/README.md, docs/product/changelog.md, workspace.toml, docs/specs/marketplace-generator-single-source/notes/verification.md

**Tests:**
- `rm -rf dist && make build && SKIP_SAST=1 make build-check` exits 0 with no
  `CAT-V-014` (AC10). Read the exit code from the command's own output, never
  through a pipe.
- The same recipe with `claude-plugin-branch` reverted to `main` reports
  `CAT-V-014` (AC7, demonstrated red), and the pre-fix `source.ref` divergence is
  recorded.
- `make ci` passes (AC11).

**Approach:**
- Run both directions of the recipe and record the commands and observed output in
  `notes/verification.md`.
- Add the `docs/specs/README.md` row and the `docs/product/changelog.md` entry,
  naming forks whose own `build-self` reads this `catalogue.toml` as the audience
  (AC12).
- Flip the metadata: `spec.md` to `Shipped`, `plan.md` to `Done`, every acceptance
  criterion to `[x]`, and the `docs/specs/README.md` row's Status token to match
  the spec — the drift commit `cf46953e` had to hand-sync eight such rows.
- Register the deferrals listed below in `workspace.toml [backlog].open`, each following
  the existing convention there — a comment block giving the defect, the fix, why
  it was deferred rather than bundled, and an `Unblocks when:` line, then
  `{slug = "...", source = "spec/marketplace-generator-single-source (review blocker N)"}`:
  `marketplace-envelope-config-authority`,
  `output-drift-silent-without-dist`,
  `marketplace-ref-not-git-ref-validated`,
  `catalogue-branch-empty-falls-back-to-upstream-constant`,
  `publish-control-evidence-freshness-unbounded`,
  `make-build-uses-deprecated-entrypoint`,
  `marketplace-maintainer-email-unlinted`,
  `marketplace-envelope-post-import-rebind-unbounded`,
  `marketplace-publisher-branch-layer-2-only`.

**Done when:** both directions of the recipe are recorded, `make ci` passes, the
index row and changelog entry exist, and every deferral resolves to a
`[backlog].open` slug.

## Rollout

- **Delivery:** single PR, fully reversible. The only output change is that the
  verifier's fresh build now emits what `make build` already emitted; a `make
  build`-produced `dist/` and the committed root `.claude-plugin/marketplace.json`
  are byte-unchanged.
- **Infrastructure:** none. The `claude-plugins-dist` branch, its ruleset, and
  `publish-claude-plugins.yml` are unchanged.
- **External-system integration:** nothing needs republishing. The committed root
  marketplace already advertises `claude-plugins-dist`, so live adopters of *this*
  repo's marketplace are unaffected. Adopters of the `agentbundle` package see one
  behaviour change: `_aggregate_marketplace`'s description default now resolves to
  `_MARKETPLACE_DESCRIPTION`, which is the same string, so their output is
  byte-identical too.
- **Deployment sequencing:** T1 → T2 → T3 (wiring a red check into a gate would
  redden the required check).

## Risks

- **The parity gate cannot see live repository state.** No gate here reads GitHub;
  `tools/lint-claude-plugin-publish-control.py` compares the desired-state file
  against hardcoded literals and a hand-committed capture with unbounded
  freshness, and the desired file records `live_branch_negative_tested: false`. So
  the ruleset could be removed in repository settings with zero commits and every
  gate would stay green — while ADR-0072 treats that protection as a precondition
  of its decision. This gate closes the gap between the desired-state file and
  what the build advertises; it does not close the gap to live state. Registered
  as `publish-control-evidence-freshness-unbounded`; confirming the live ruleset
  is a repository-settings action for a maintainer.
- **The refactor stays undone.** Six shipped entrypoints still read the constants
  directly. Registered as `marketplace-envelope-config-authority`; it needs a
  decision about `toml_emit.py`'s `"main"` scaffold default first, since that
  default is what makes the refactor adopter-visible.
- **`ref` and `sha` are unvalidated strings on an *ingress* path.**
  `marketplace-entry.schema.json` declares both as bare `"type": "string"` while
  `url` and `path` carry patterns — and that schema validates *foreign* content:
  `catalogue_tooling/archive.py:288-317` extracts `.claude-plugin/marketplace.json`
  from a tarball and validates its entries, and `verify.py:1252` does the same for
  an arbitrary root. So a foreign entry whose `ref` is `--upload-pack=…` is
  stamped valid before a human or agent hands it to a client that clones; the
  `if`/`then`/`else` makes `sha`-pinning *look* like the safe branch while
  accepting anything. An earlier draft justified deferring this as "the parity gate
  closes the reachable path here" — that was false, because a parity gate checks
  equality, not shape. AC5 now validates `branch.target`'s shape directly, so the
  deferral is narrowed to the schema twins and their ingress role. Registered as
  `marketplace-ref-not-git-ref-validated`.
- **A fork's install route silently resolves to upstream.** With
  `claude-plugin-branch = ""` the truthiness guard at
  `catalogue_tooling/build.py:106` leaves the upstream constant standing, and
  `source.url` is derived per pack from `[pack.links].repository`
  (`build/main.py:286-306`), which in a fork still points upstream unless every
  `pack.toml` is edited — so the fork's users install upstream code from
  upstream's branch, bypassing the fork's own review. A third hardcoded `"main"`
  at `catalogue_tooling/config.py:377` is worse in kind: an *absent* key overrides
  the ADR pin with a branch carrying no packs, rather than falling back to it.
  Registered as `catalogue-branch-empty-falls-back-to-upstream-constant`, covering
  both.
- **The Makefile ↔ workflow list identity is now asserted by the gate itself.**
  Deferring it was misfiled: a change whose thesis is "where a fact is stated
  twice, install a parity gate" cannot defer exactly that gate for its own
  two-place fact, and the two lists are identical today so the assertion is ~20
  lines in a file already being added.
- **`make build` stays on a deprecated entrypoint.** `_cmd_build_shim` prints its
  own deprecation notice pointing at `agentbundle catalogue build`, yet the
  Makefile still calls it. Registered as `make-build-uses-deprecated-entrypoint`.

## Changelog

- 2026-08-17: initial plan — resolve both values from `catalogue.toml` inside
  `cmd_build`, making config the single authority.
- 2026-08-17: replaced that approach with a parity gate after pre-EXECUTE review
  round 1. Three findings drove it: `render.py`'s `render_pack_to_dir` /
  `render_packs_to_dir` reach the marketplace writers without passing through
  `cmd_build`; ADR-0072 pins `_DIST_BRANCH` and rests on branch protection; and
  `toml_emit.py`'s `"main"` scaffold default would have made the refactor change
  adopter `build-self` output.
- 2026-08-17: round 2 hardened the gate itself. Added the committed marketplace's
  fourteen `source.ref` values and the ruleset's `branch.target` as anchors (the
  artifact an adopter resolves was previously unanchored for the branch); deleted
  `self_host.py`'s hardcoded description default — the fourth statement, and the
  one that actually writes that artifact — rather than anchoring it, and gated
  against its reintroduction; specified the `ast` reader contract (exactly one
  module-level `str`-`Constant` assignment) because a first-match or
  find-any-Constant read is a silent-pass; replaced AC5's seven hand-run probes
  with an automated in-CI mutation suite over a temp tree, following
  `tools/test-lint-claude-plugin-publish-control.py`; materialised the TDD stub
  (the round-1 waiver expired with the redesign); and dropped the byte-equality
  AC, which could not fail once AC3/AC4 made the monkey-patch a no-op by
  construction. Corrected two wrong citations: the verifier's fresh build is
  in-process `build_catalogue()`, not an argv path, and `make build` passes
  `--packs-dir` / `--output-dir`.
- 2026-08-17: round 3 found three holes in the gate materialised that round, all
  confirmed by probe. `read_module_str_constant` counted only module-level
  `ast.Assign`, so an appended `_DIST_BRANCH: str = "attacker"` left the gate green
  while the build emitted the shadow — replaced with a whole-tree binding scan.
  `source.url` was unanchored, so a one-line `pack.toml` edit could point adopters
  at a third-party repository at a protected-looking ref — added as an anchor.
  `branch.target` of exactly `refs/heads/` yielded an empty branch the gate
  certified as protected — branch shape is now validated, which also falsified and
  narrowed the `marketplace-ref-not-git-ref-validated` deferral rationale. Also:
  extracted `check_envelope_parity(root)` (T2's specified probe shape was
  unwritable without it); wrapped every read in `ParityError` naming its source;
  fixed an offset bug that returned a neighbouring parameter's default; folded in
  the Makefile↔workflow list-identity assertion and dropped its slug; and corrected
  the `self_host.py:60` citation — the module is imported, the symbol is not, so T1
  gained an explicit import step. Every assertion has since been observed firing on
  an anchor-only fixture tree.
- 2026-08-17: round 4 found four more ways the static reader could pass while the
  build emitted something else — an `import`/`def`/`class`/`except`/`case`/`del`
  shadow, four dynamic rebinds beyond the one `globals()[...]` form handled, a
  `branches` dict keyed by the marketplace entry's own (non-unique) `name` so a
  duplicate-named entry masked a hostile `ref`, and a `_pytest_group` line-walk that
  narrowed its own comparison scope. Rather than add a fifth round of arms to the
  enumeration, the authority moved to the **resolved value** (`importlib` +
  `getattr`), which answers "what does the build emit" directly; the literal check
  stays as a second layer so the value remains reviewable rather than computed. Also
  pinned `repo` to a literal (no PR-time gate pins it), keyed comparisons by index,
  put the reference source in every failure message, asserted the gate's own
  membership in both pytest groups, refused a non-`git-subdir` `source.source` and
  unexpected sibling keys, replaced the line-walk with a join-continuations read, and
  named the one residual neither layer bounds
  (`marketplace-envelope-post-import-rebind-unbounded`). All twelve demonstrated
  attacks were verified blocked in an ad-hoc harness; T3 lands them as probes in the
  repository, which is where the regression protection actually lives.
- 2026-08-18: round 5 found a verified bypass composing three defects, and one of
  them invalidated the verification method itself. (1) `_DYNAMIC_REBIND` enumerated
  `globals()` and `vars()` but not `locals()`, which at module scope *is* the module
  dict — the enumeration failure the instrument change was meant to retire, still
  present. (2) `resolved_attr` used `isinstance`, admitting a `str` subclass whose
  `__eq__`/`__ne__` lie; a subclass also wins reflected-operand priority, so flipping
  the comparison does not help. (3) Most seriously, layer 1 never asserted *which
  file* it imported — and on this machine the editable install resolved a **different
  worktree** of this repository, so every resolved-value reading taken during
  development validated a sibling checkout and coincidentally matched. Fixes: exact
  `type(value) is str` at the boundary and `str.__eq__` comparisons; a `__file__`
  provenance assertion (measured: bare `python3` resolves the sibling tree,
  `PYTHONPATH=packages/agentbundle` as `make test` sets it resolves this one, so the
  assertion passes under the gate's real invocation and fails loudly under the one
  that misled me); `locals()`/`__dict__[` added to the tripwire and the tripwire
  extended over `self_host.py`; the documented `resolve=True` root refusal
  implemented as code rather than prose; `source.path` pinned to the entry `name`;
  and the dead `allow_import` parameter removed. The two load-bearing defences are
  now non-enumerable checks rather than enumerations, which is the qualitative change
  the earlier rounds lacked. Fifteen attacks blocked, 19/19 shadow forms detected.
