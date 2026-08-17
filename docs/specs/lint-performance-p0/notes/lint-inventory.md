# Lint surface inventory — task zero for `lint-performance-p0`

**Status:** complete · **Captured:** 2026-08-17 · **Host:** darwin 25.5.0, Python 3.13.13

This is the audit that scopes the P0 work. Every lint-like production entry
point and every lint self-test in the repository is classified here, with a
recorded P0 disposition. The disposition column is the scope contract: the
implementation may change a lint **only** if its row says `CHANGE`.

Findings are measured, not inferred. Method is recorded in
[§ Measurement method](#measurement-method) so the after-numbers are
comparable.

> **This file is the single canonical home for the before/after performance
> figures.** `spec.md`, `plan.md`, `workspace.toml` and `docs/specs/README.md`
> reference [§ Baseline evidence](#baseline-evidence-before) rather than
> restating the numbers, so the copies cannot drift as the after-column is
> filled in.

---

## Headline result

Audited, all counts measured:

| Universe | Count |
| --- | --- |
| production lint / policy-gate entry points (§ 1 + § 2 rows) | **41** |
| pack/skill-owned lint scripts (§ 3) | **7** |
| `tools/test-*.py` self-tests | **33** |
| `tools/test_*.py` self-tests | **32** |
| non-Python self-tests (`tools/test-lint-build.sh`, `tools/test-pre-pr.sh`) | **2** |
| **total self-tests** | **67** |

An earlier draft said "38 production lints" and broke the self-test total down as
"35 hyphen-named + 32 underscore-named". Both were wrong: the row count is 41,
and the hyphen-named `.py` count is 33 — the earlier 35 conflated the two `.sh`
files into the `.py` glob. Corrected here.

Exactly **three files** exhibit a P0 pattern:

| File | P0 patterns present |
| --- | --- |
| `tools/lint-pack-test-boundary.py` | per-path Git subprocess · Git subprocess inside traversal · repeated same-root traversal · repeated runner/catalogue parsing · catalogue-wide checks independently rebuilding one inventory |
| `tools/test-lint-pack-test-boundary.py` | falsification rerunning the complete worktree lint for every planted case · real-checkout Makefile mutation · real-checkout file plants |
| `tools/lint-agents-md.py` | one Git subprocess per candidate path |

Everything else is measured clean and carries a justified **no P0 change**
disposition. The single dominant cost is `lint-pack-test-boundary`: **337
`git check-ignore` subprocesses and 32.4 s per invocation**, launched **12
times** by its own falsification suite. Measured end to end: the suite **passes
in 306.4 s**, six seconds past the 300 s inner-loop budget — which is why it
presented as "71% then stall" rather than as a failure.

**No second Git-ignore helper is required.** Portable `agentbundle`
catalogue lint/verify and every shipped pack lint were measured at **zero**
`git check-ignore` calls, so a package-local portable resolver would have no
caller. See [§ Distribution boundaries](#distribution-boundaries).

---

## Measurement method

Reproducible; all numbers below come from these three probes.

1. **Git process count** — a counting shim earlier on `PATH` that appends its
   argv to `$GITSHIM_LOG` and `exec`s the real `git`. Counts every Git
   subprocess a lint launches, by subcommand.
2. **Traversal / parse counts** — the lint module loaded via
   `importlib.util`, its internal helpers (`_walk`, `_is_ignored`, `_packs`,
   `_destinations`, `_runner_lines`, `_glob_tree_is_confined`,
   `_projected_packs`) wrapped with counters, then `main()` invoked in-process.
   Distinct-vs-total base paths recorded to separate real work from repeated
   work.
3. **Wall clock** — `/usr/bin/time -p` on the bare CLI with no shim, warm
   filesystem cache.

Structural counts (1) and (2) are the normative evidence. Wall clock (3) is
supporting evidence only and is deliberately **not** asserted in CI.

---

## Scope classes

Per the three execution models this spec adopts:

- **pack/skill-local** — complete correctness boundary is one owning pack or
  one owning skill; needs no peer catalogue state.
- **catalogue-wide** — enforces a relationship *across* packs, projections,
  profiles, rosters, runners, or shared contracts; one pack can conflict with
  another.
- **repo-global** — non-catalogue repository surface (CI parity, docs
  structure, site/workflow parity, release policy, security-gate form, root
  config).
- **hybrid** — a file carrying checks in more than one class.

Classification is **per check**, not per file. `lint-pack-test-boundary.py`
is the case that matters: three of its six checks read one pack at a time,
but its runner, projection, coverage and confinement contracts all depend on
the complete catalogue, so the **file is catalogue-wide** and its checks are
individually annotated in
[§ lint-pack-test-boundary, per check](#lint-pack-test-boundary-per-check).

---

## 1. Catalogue-wide lints

| Entrypoint/check | Owner | Scope class | Gate wiring | Traversal roots | Ignore semantics | Git process shape | Repeated work | Self-test model | P0 disposition |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| `tools/lint-pack-test-boundary.py` (6 checks) | repo tooling | catalogue-wide (hybrid per check) | `.github/workflows/docs.yml:161`; `tools/test-all.py:120`. Not in `pre_pr_catalogue.py`, not a direct Make target | `packs/*/.apm`, `packs/*/tests`, `packs/*/tests/skills/*`, `.claude/skills/*`, `.agents/skills/*`, 6 runner files | **skips** gitignored paths — build residue (`__pycache__` etc.) is not authored content, so not a boundary violation | **337 `check-ignore`, one per candidate path**, launched from inside `_walk()` | `_walk` 141 calls / 109 distinct bases; `_glob_tree_is_confined` 45 / 16 distinct; `_runner_lines` ×2; `_destinations` ×2; `_packs` ×5 | real-worktree mutation | **CHANGE** — every P0 pattern |
| `agentbundle catalogue lint` / `--deep` | portable agentbundle | catalogue-wide | `build-check` chain; `pre_pr_catalogue.py` step 1 | per-pack `glob`/`rglob` under `packs/*`, `profiles/*.toml`, seeds via `os.walk(followlinks=False)` | does not consult Git ignore | **0 Git subprocesses** | none observed; bounded per-pack globs | pytest, fixture catalogues | **no change** — 5.89 s, zero Git calls; bounded per-pack globs only. Churning it is explicitly out of scope |
| `agentbundle catalogue verify` | portable agentbundle | catalogue-wide | `build-check` chain; `pre_pr_catalogue.py` step 1 | `dist/`, `packs/*/.apm/skills/*`, `agents/`, `commands/` | uses `git ls-files` for tracked-file set | **1 `ls-files`, already batched** for the whole tree | none observed | pytest, fixture catalogues | **no change** — 13.47 s, one batched Git call. Already the target shape |
| `agentbundle` skill-spec lint (`skill_spec_lint.py`) | portable agentbundle | catalogue-wide | invoked by catalogue lint; `pre_pr_catalogue.py:114` | `packs/*/.apm/skills`, `packs/*/pack.toml` | no Git ignore use | 0 | bounded `glob("*/…")` per root | pytest unit | **no change** — bounded globs, no Git |
| `agentbundle` `build/lint_packs.py` | portable agentbundle | catalogue-wide | build pipeline | per-subtree `rglob("*")` | no Git ignore use | 0 | per-subtree walk, single pass | pytest unit | **no change** — one bounded pass per subtree |
| `tools/lint-pack-descriptions.py` | repo tooling | catalogue-wide | `pre_pr_catalogue.py` | `packs/*/pack.toml` | no Git ignore use | 0 | none | `tools/test-lint-pack-descriptions.py`, temp fixture | **no change** — 0.22 s, no Git |
| `tools/lint-plugin-roster.py` | repo tooling | catalogue-wide | `pre_pr_catalogue.py` | `packs/*`, roster files | no Git ignore use | 0 | none | temp fixture | **no change** — 0.18 s, no Git |
| `tools/lint-plugin-membership.py` | repo tooling | catalogue-wide | `pre_pr_catalogue.py` | `packs/*`, plugin manifests | no Git ignore use | 0 | none | temp fixture | **no change** — 0.29 s, no Git |
| `tools/lint-plugin-route-docs.py` | repo tooling | catalogue-wide | `pre_pr_catalogue.py` | plugin route docs | no Git ignore use | 0 | none | temp fixture | **no change** — 0.27 s, no Git |
| `tools/lint-pack-journeys.py` | repo tooling | catalogue-wide | `pre_pr_catalogue.py:132` | `packs/*` journey files | no Git ignore use | 1 (`rev-parse`, root discovery, loop depth 0) | none | temp fixture | **no change** — 0.52 s; one root-discovery call |
| `tools/lint-journey-contract.py` | repo tooling | catalogue-wide | `pre_pr_catalogue.py:134` | journey contracts across packs | no Git ignore use | 1 (`rev-parse`) | none | temp fixture | **no change** — 0.43 s |
| `tools/lint-knowledge-surface-parity.py` | repo tooling | catalogue-wide | `pre_pr_catalogue.py:123` | knowledge surfaces across packs | no Git ignore use | 1 (`rev-parse`) | none | temp fixture | **no change** — 0.28 s |
| `tools/lint-catalogue-curation-guard.py` | repo tooling | catalogue-wide | `pre_pr_catalogue.py` | `catalogue.toml`, `packs/*` | no Git ignore use | 1 (`rev-parse`) | none | temp fixture | **no change** — 2.68 s; single pass |
| `tools/lint-experience-agnostic.py` | repo tooling | catalogue-wide | `pre_pr_catalogue.py` | `packs/*` skill text | no Git ignore use | 1 (`rev-parse`) | none | temp fixture | **no change** — 0.44 s |
| `tools/lint-conformance-portability.py` | repo tooling | catalogue-wide | `build-check` | `tests/conformance` | no Git ignore use | 0 | none | none | **no change** — 0.18 s, one bounded `rglob` |
| `tools/lint_zone_violations.py` | repo tooling | catalogue-wide | `build-check` | pack zone trees | no Git ignore use | 0 | none | none | **no change** — 0.37 s; three bounded `rglob`s over distinct roots |
| `tools/catalogue/check_contract_parity.py` | catalogue tooling | catalogue-wide | `pre_pr_catalogue.py` | `contracts/` | no Git ignore use | 0 | none | pytest | **no change** — no Git, single pass |
| `tools/catalogue/sync_contract_inventory.py` | catalogue tooling | catalogue-wide | `pre_pr_catalogue.py` | `contracts/` | no Git ignore use | 0 | none | pytest | **no change** |
| `tools/catalogue/sync_authoring_scaffold.py` | catalogue tooling | catalogue-wide | `pre_pr_catalogue.py` | scaffold trees | no Git ignore use | 0 | none | pytest | **no change** |
| `tools/check-artifact-contents.py` | repo tooling | catalogue-wide | `build-check` | `dist/` archives | no Git ignore use | 0 observed | none | none | **no change** — 0.19 s; needs a built `dist/` (exit 2 bare) |
| `tools/check-contract-drift.py` / `tools/repo/check_contract_drift.py` | repo tooling | catalogue-wide | `build-check` | `contracts/` | no Git ignore use | 0 | none | `tools/test-check-contract-drift.py`, temp fixture | **no change** — 2.10 s, no Git |
| `tools/check-atlassian-phase3-readiness.py` | repo tooling | catalogue-wide (one pack's readiness) | invoked by no workflow (recorded in `_NO_RUNNER`) | `packs/atlassian/**` | no Git ignore use | 3, loop depth 0 | none | 4 CLI launches, bounded to one pack | **no change** — bounded to a single pack; no ignore-query loop |

### `lint-pack-test-boundary`, per check

Recorded per check because the file is hybrid and the spec's scope-class
treatment differs by class. The **file** stays catalogue-wide: a partial run
must never print the six-check terminal wording.

| Check | Class of the check itself | Why the file is still catalogue-wide |
| --- | --- | --- |
| `apm-carries-no-tests` | pack-local per pack | must enumerate **all** packs; a vacuous empty iteration is an explicit failure |
| `projection-carries-no-tests` | catalogue-wide | asserts each pack in the self-host recipe's include list is actually projected — needs the recipe **and** the projected trees |
| `tests-live-in-the-pack-tree` | pack-local per pack | must enumerate all packs; vacuity is a failure |
| `runners-keep-suites-isolated` | catalogue-wide | one pytest invocation spanning two packs' suites is a cross-pack conflict |
| `every-suite-dir-has-a-runner` | catalogue-wide | global coverage relation between all destinations and all runner files |
| `pack-tests-stay-in-pack` | pack-local per pack, global exemption set | needs every pack's test tree; `_NO_RUNNER` staleness is a global relation |

---

## 2. Repo-global, non-catalogue lints

| Entrypoint/check | Owner | Scope class | Gate wiring | Traversal roots | Ignore semantics | Git process shape | Repeated work | Self-test model | P0 disposition |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| `tools/lint-agents-md.py` | repo tooling | repo-global | `.github/workflows/docs.yml:86`; `pre_pr_catalogue.py:113` | root `AGENTS.md`, `packs/core/seeds/AGENTS.md`, projected docs; **3 fixed gitignore probe paths** | **asserts probes ARE ignored** — inverted vs. the boundary lint; a non-ignored probe calls `note()`, which is **fatal** (`fail = 1` → exit 1) | **3 `check-ignore`, one per probe path** (line 313, inside a `for probe in (...)` loop) | none beyond the 3 probes | 3 fixture-based self-tests (see § 4) | **CHANGE** — one Git subprocess per candidate path. 3 → 1 batched. Git-missing contract **differs today**: no `FileNotFoundError` guard, so absent Git raises. The **resolver's** policy is unified to fail-open by authorised decision (2026-08-17), but the **call site treats a degraded resolution as fatal**: it exits 1 naming **Git unavailability**, and must NOT emit three `drift-watch:` notes claiming `.gitignore` drifted — that would misdiagnose a real degradation as a content finding |
| `tools/lint-ci-parity.py` | repo tooling | repo-global | `build-check`; Make | `Makefile`, `.github/workflows/*.yml`, gate chain | no Git ignore use | 0 | none | `tools/test-lint-ci-parity.py` — **fixture roots via `--root` + one real-root e2e launch** | **no change** — 0.13 s. Already the exact target architecture; used as the repo precedent for the boundary-lint refactor |
| `tools/lint-build.py` | repo tooling | repo-global | `pre_pr_catalogue.py:120` | build outputs | no Git ignore use | 3; `git merge-base` in a **bounded 2-element base-ref fallback loop** that returns on first success | none | none | **no change** — not an ignore query; bounded fallback, not per-candidate |
| `tools/lint-nosec-form.py` | repo tooling | repo-global (security-gate form) | `build-check` | `tools/`, `packs/`, `packages/` Python sources | no Git ignore use | 1 (`rev-parse`) | none | `tools/test-lint-nosec-form.py`, temp fixture | **no change** — 5.33 s, the slowest non-P0 lint, but one bounded pass and zero ignore queries. Recorded as P1 watch item only |
| `tools/lint-sso-config.py` | repo tooling | repo-global | `pre_pr_catalogue.py:121` | SSO config | no Git ignore use | 0 | none | temp fixture | **no change** — 0.25 s |
| `tools/lint-site-scope-parity.py` | repo tooling | repo-global (site parity) | `pre_pr_catalogue.py` | `site.toml`, `docs-site/` | no Git ignore use | 0 | none | temp fixture | **no change** — 0.35 s |
| `tools/lint-web-journey-parity.py` | repo tooling | repo-global (site parity) | `pre_pr_catalogue.py:129` | `web/`, journeys | no Git ignore use | 1 (`rev-parse`) | none | temp fixture | **no change** — 0.40 s |
| `tools/lint-claude-plugin-publish-control.py` | repo tooling | repo-global (release policy) | `build-check` | plugin publish config | no Git ignore use | 0 | none | temp fixture | **no change** — 0.18 s |
| `tools/lint-guide-titles.py` | repo tooling | repo-global (docs structure) | `.github/workflows/docs.yml` | `docs/guides/`, `guides/` | no Git ignore use | 0 | none | none | **no change** — 1.46 s, one bounded `rglob` |
| `tools/lint-guides-no-repo-only-refs.py` | repo tooling | repo-global (docs structure) | `.github/workflows/docs.yml` | `guides/` | no Git ignore use | 0 | none | none | **no change** — 1.46 s |
| `tools/validate_guides.py` | repo tooling | repo-global (docs structure) | `.github/workflows/docs.yml` | `docs/guides/`, `guides/` | no Git ignore use | 0 | none | none | **no change** — 0.87 s, one bounded `rglob` |
| `tools/check-guide-index.py` | repo tooling | repo-global (docs structure) | `.github/workflows/docs.yml` | guide index + tree | no Git ignore use | 0 | none | none | **no change** — 0.43 s |
| `tools/check-docs-contrast.py` | repo tooling | repo-global (docs a11y) | `.github/workflows/docs.yml` | docs theme tokens | no Git ignore use | 0 | none | none | **no change** — 0.55 s |
| `tools/check-rendered-site-links.py` | repo tooling | repo-global (site parity) | `.github/workflows/docs.yml` | rendered site output | no Git ignore use | 0 | single `os.walk` of rendered output | none | **no change** — 0.24 s; needs rendered site (exit 2 bare) |
| `tools/check-site-plugin-offers.py` | repo tooling | repo-global (site parity) | `.github/workflows/docs.yml` | site plugin offers | no Git ignore use | 0 | none | `tools/test-check-site-plugin-offers.py`, temp fixture | **no change** — 0.41 s |
| `tools/lint-ruff.py` | repo tooling | repo-global (style) | `make lint-ruff`; `make ci` | delegates to `ruff` | ruff's own ignore handling | 1 (`ruff`, not Git) | none | none | **no change** — thin delegator |
| `tools/lint-mypy.py` | repo tooling | repo-global (types) | `make lint-mypy`; `make ci` | delegates to `mypy` | mypy's own handling | 1 (`mypy`, not Git) | none | none | **no change** — thin delegator |
| `tools/repo/check_release_impact.py` | repo tooling | repo-global (release policy) | release gate | changed-file list | no Git ignore use | `git diff --name-only` in a **bounded 2-form fallback loop**, returns on first success | none | none | **no change** — not an ignore query; not per-candidate |
| `tools/repo/build_gate_chain.py` | repo tooling | repo-global (gate orchestration) | `build-check` | gate chain declaration | n/a | 0 | none | covered by ci-parity | **no change** — orchestration only |

---

## 3. Pack/skill-local lints (shipped)

All are shipped pack content and must **not** depend on repo-only helpers.

| Entrypoint/check | Owner | Scope class | Gate wiring | Traversal roots | Ignore semantics | Git process shape | Repeated work | Self-test model | P0 disposition |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| `packs/core/.apm/skills/work-loop/scripts/lint-spec-status.py` | core pack (work-loop skill) | pack/skill-local (one spec dir) | work-loop finish checklist | one `docs/specs/<slug>/` | no Git ignore use | 4, all loop depth 0 (`rev-parse` ×2, bounded base-ref resolve, `git show`) | none | `packs/core/tests/skills/work-loop/test_lint_spec_status*.py`, temp fixture | **no change** — already bounded to one spec dir; no ignore query |
| `packs/core/.apm/skills/work-loop/scripts/lint-traceability.py` | core pack (work-loop skill) | pack/skill-local | work-loop | one spec dir + bounded roots | no Git ignore use | 1 (`rev-parse`, loop depth 0) | single `os.walk(followlinks=False)` per root | `test_lint_traceability.py`, temp fixture | **no change** — one bounded walk; `followlinks=False` already correct |
| `packs/core/.apm/skills/work-loop/scripts/lint-knowledge.py` | core pack | pack/skill-local | work-loop | knowledge journal partitions | no Git ignore use | 1 (`rev-parse`) | none | pytest | **no change** |
| `packs/core/.apm/skills/work-loop/scripts/check-spec-status.py` | core pack | pack/skill-local | work-loop | one spec file | n/a | 0 | none | pytest | **no change** — no subprocess at all |
| `packs/core/.apm/skills/work-loop/scripts/check-base-freshness.py` | core pack | pack/skill-local | work-loop preflight | git refs | n/a | `git config --get` in a bounded key loop | none | `test_check_base_freshness.py`, temp git repos | **no change** — not an ignore query; base-freshness optimization is an explicit non-goal |
| `packs/core/.apm/skills/receive-brief/scripts/lint-brief-coverage.py` | core pack (receive-brief skill) | pack/skill-local (one brief) | receive-brief | one brief file | no Git ignore use | 1 (`rev-parse`) | none | `test_lint_brief_coverage.py`, temp fixture | **no change** |
| `packs/core/.apm/skills/workspace-status/scripts/workspace_status.py` | core pack | repo-global (workspace index) | session start; work-loop ORIENT | `workspace.toml`, `docs/specs/*/spec.md` | no Git ignore use | 0 | bounded by subcommand (`status` = Type 2+3 only; `reconcile` adds Type 1) | `tools/test_workspace_status_cli.py`, temp fixture | **no change** — already has bounded/full scan modes by design |

---

## 4. Lint self-tests (falsification suites)

Measured by full-production-CLI launch count and by whether plants mutate the
real checkout.

| Self-test | Subject | Full-lint CLI launches | Real-tree mutation | P0 disposition |
| --- | --- | --- | --- | --- |
| `tools/test-lint-pack-test-boundary.py` | `lint-pack-test-boundary.py` | **12** (lines 421, 436, 450, 459, 478, 498, 519, 551, 573, 613, 634, 661) | **yes** — plants into `packs/figma/.apm/**`, `packs/figma/tests/**`, `packs/contracts/tests`, and **rewrites the real root `Makefile` twice** (lines 568, 606) | **CHANGE** — measured 306.4 s for the whole suite, exit 0, 82 cases. Reduce to fixture-based plants + a minimal real-tree e2e layer |
| `tools/test-lint-ci-parity.py` | `lint-ci-parity.py` | 3 (1 real-root, 2 fixture-root via `--root`) | no — fake roots in temp dirs | **no change** — already the target architecture. Note it anchors aggregator extraction: line 292 asserts `run_call_targets(AGGREGATOR) == {"tools/lint-agents-md.py"}`, so the agents-md `_run` line in `pre_pr_catalogue.py` must stay byte-stable |
| `tools/test_lint_agents_md_legacy_block.py` | `lint-agents-md.py` check 10d | 1 | no — temp fixture (heavy `tmp_path` use) | **no change** — fixture-based already; asserts a warning shape unrelated to the probe loop |
| `tools/test_lint_agents_md_diataxis_block.py` | `lint-agents-md.py` check 8 | 1 | no — temp fixture | **no change** — fixture-based already |
| `tools/test_lint_agents_md_risk_block.py` | `lint-agents-md.py` check 10g | 1 | no — temp fixture | **no change** — fixture-based already; asserts risk-trigger block byte-equality, not the probe loop |
| `tools/test-check-atlassian-phase3-readiness.py` | readiness checker | 4 | no | **no change** — bounded to one pack; no worktree scan |
| `tools/test-lint-sso-config.py` | `lint-sso-config.py` | 2 | no — temp fixture | **no change** |
| `tools/test-lint-experience-agnostic.py` | `lint-experience-agnostic.py` | 1 | no — temp fixture | **no change** |
| `tools/test-lint-journey-contract.py` | `lint-journey-contract.py` | 1 | no — temp fixture | **no change** |
| `tools/test-lint-knowledge-surface-parity.py` | parity lint | 1 | no — temp fixture | **no change** |
| `tools/test-lint-pack-journeys.py` | `lint-pack-journeys.py` | 1 | no — temp fixture | **no change** |
| `tools/test-lint-web-journey-parity.py` | parity lint | 1 | no — temp fixture | **no change** |
| `tools/test-check-contract-drift.py` | drift check | 1 | no — temp fixture | **no change** |
| `tools/test-run-pack-evals.py` | pack-evals runner | 1 | no | **no change** — contains **one** `git check-ignore` on a **single** path (line 686) asserting a real `.gitignore` fact. One candidate, one process; it is a self-test, not a production lint, so it is outside the source-enforcement scope. Documented, not migrated |
| `tools/test-lint-nosec-form.py` | `lint-nosec-form.py` | 0 (in-process) | no — temp fixture | **no change** |
| `tools/test-lint-catalogue-curation-guard.py` | curation guard | 0 | no — temp fixture | **no change** |
| `tools/test-lint-claude-plugin-publish-control.py` | publish control | 0 | no — temp fixture | **no change** |
| `tools/test-lint-pack-descriptions.py` | pack descriptions | 0 | no — temp fixture | **no change** |
| `tools/test-lint-plugin-membership.py` | plugin membership | 0 | no — temp fixture | **no change** |
| `tools/test-lint-plugin-roster.py` | plugin roster | 0 | no — temp fixture | **no change** |
| `tools/test-lint-plugin-route-docs.py` | route docs | 0 | no — temp fixture | **no change** |
| `tools/test-lint-site-scope-parity.py` | site scope parity | 0 | no — temp fixture | **no change** |
| `tools/test-check-site-plugin-offers.py` | site plugin offers | 0 | no — temp fixture | **no change** |
| `packs/core/tests/skills/work-loop/test_lint_spec_status*.py` | spec-status lint | 0 | no — temp fixture | **no change** |
| `packs/core/tests/skills/work-loop/test_lint_traceability.py` | traceability lint | 0 | no — temp fixture | **no change** |
| `packs/core/tests/skills/receive-brief/test_lint_brief_coverage.py` | brief coverage | 0 | no — temp fixture | **no change** |
| `packages/agentbundle/tests/**` (catalogue lint/verify/skill-spec) | portable lints | pytest in-process | no — fixture catalogues | **no change** |

### The 32 underscore-named self-tests under `tools/`

A first pass of this audit globbed only `tools/test-*.py` and missed the
underscore-named family entirely. Corrected: all 32 were enumerated and
scanned. **Aggregate result — 0 contain `check-ignore`, 0 mutate the real
worktree, 0 write the real `Makefile`**; every one that needs a tree builds a
temporary fixture. None reruns a complete catalogue or worktree lint per planted
case, so the `CHANGE` scope is unaffected.

| Self-test | Subject | `sys.executable` launches | Fixture | P0 disposition |
| --- | --- | --- | --- | --- |
| `test_build_gate_chain.py` | gate-chain parity | 20 | temp | **no change** — fixture gate chains; also anchors `tools/lint-agents-md.py` into the chain (line 235) |
| `test_lint_guides_no_repo_only_refs.py` | guides ref lint | 6 | temp | **no change** |
| `test_export_work_index.py` | work-index export | 6 | temp | **no change** |
| `test_check_artifact_contents.py` | artifact contents | 4 | temp | **no change** |
| `test_contract_parity.py` | contract parity | 4 | temp | **no change** |
| `test_workspace_status_cli.py` | workspace-status CLI | 4 | temp | **no change** |
| `test_lint_agents_md_{diataxis,legacy,risk}_block.py` | agents-md checks 8/10d/10g | 1 each | temp | **no change** |
| `test_build_site_dry_run.py`, `test_check_rendered_site_links.py` | site build / links | 1 each | temp | **no change** |
| `test_lint_guide_titles.py`, `test_validate_guides.py`, `test_conformance_portability.py`, `test_workspace_status.py`, `test_build_site_{inventory,projection,routing,sidebar}.py` | assorted | 0 | temp | **no change** — in-process |
| `test_build_site_link_rewrites.py`, `test_catalogue_curation_guard.py`, `test_catalogue_navigation.py`, `test_catalogue_tooling_docs.py`, `test_catalogue_tooling_rewire.py`, `test_check_guide_index.py`, `test_check_release_impact.py`, `test_documentation_entry_links.py`, `test_enterprise_rollout_playbook.py`, `test_guide_typed_asides.py`, `test_live_demo_guide.py`, `test_release_check.py`, `test_scaffold_projection.py` | assorted | 0 | in-process | **no change** — pure in-process assertions |

Correction to § 1–3: production rows previously recording self-test model
"none" for `lint-guide-titles`, `lint-guides-no-repo-only-refs`,
`validate_guides`, `check-guide-index`, `check-artifact-contents`,
`check-rendered-site-links`, `lint-conformance-portability` and
`lint-catalogue-curation-guard` are wrong — each has a self-test in the table
above. Their P0 dispositions are unchanged.

### The two non-Python self-tests

| Self-test | Subject | Wiring | Fixture | P0 disposition |
| --- | --- | --- | --- | --- |
| `tools/test-lint-build.sh` | `lint-build.py` | `tools/test-all.py` | temp sandbox | **no change** — no `check-ignore`, no real-tree mutation |
| `tools/test-pre-pr.sh` | the pre-PR hook chain | `tools/test-all.py:123`; **`docs.yml:195` (a real gate step)** | temp sandbox that is a **real Git repo** | **no change to the file**, but it is a **dependent gate**: its header records that the sandbox is `git init`-ed *specifically so the drift-watch can call `git check-ignore` against the same `.gitignore`*, and it asserts `pre-pr: ✖ agents-md hygiene failed`. It therefore exercises the exact probe path the `lint-agents-md` migration rewrites, and must be run as part of that task's verification |

An earlier draft called `test-lint-build.sh` "the one non-Python lint self-test"
and omitted `tools/test-pre-pr.sh` entirely. That omission mattered: the missing
file is a wired CI gate over the code being changed.

---

## 5. Gate wiring and aggregators

Terminal behaviour of all of these is preserved unchanged by this spec.

| Aggregator / target | Invokes | Note |
| --- | --- | --- |
| `.github/workflows/docs.yml:161` | `python3 tools/lint-pack-test-boundary.py` | the production CI gate for the boundary lint |
| `.github/workflows/docs.yml:166` | `python3 tools/test-lint-pack-test-boundary.py` | the falsification gate — comment records that `test-all.py` is run by no workflow, so **this step is the gate** |
| `.github/workflows/docs.yml:86` | `python tools/lint-agents-md.py` | agents-md CI gate |
| `tools/catalogue/pre_pr_catalogue.py` | ~30 lints as separate processes, verification-first, fail-fast | process-per-guard shape retained; in-process conversion is explicitly P1 |
| `tools/test-all.py:120,122` | boundary lint + its self-test | umbrella runner; invoked by no workflow |
| `make pre-pr` (`Makefile:62`) | `pre_pr_catalogue.py` | unchanged |
| `make build-check` (`Makefile:123`) | portable verify + repo policy gates + SAST | unchanged |
| `make ci` (`Makefile:381`) | `build-check pre-pr lint-ruff lint-mypy test` | unchanged |

---

## Distribution boundaries

The spec permits one shared Git-ignore resolver **per legitimate distribution
boundary**. Measured, only **one** boundary has a caller:

| Boundary | Callers needing batched ignore resolution | Decision |
| --- | --- | --- |
| repo-only `tools/` | `lint-pack-test-boundary.py`, `lint-agents-md.py` | **one helper**, repo-only |
| portable `agentbundle` | **none** — catalogue lint 0 Git calls, verify 1 batched `ls-files` | **no helper.** Adding one would have no caller; forbidden by *add an option only when a second caller actually needs to differ* |
| shipped pack/skill content | **none** — all 7 pack lints measured at 0 `check-ignore` | **no helper.** Shipped code must stay independent of repo-only `tools/`; nothing needs it |

Consequence: exactly **one** helper module — a flat
`tools/lint_git_ignore.py`, not a package. `tools/catalogue/` and `tools/repo/`
carry no `__init__.py`, so an importable `tools/lintlib/` package would be the
first of its kind under `tools/` and would collide with the spec's own *never add
a new module boundary* rail. A flat module needs no new boundary and is matched
by the `tools/lint_*.py` glob, so the source-enforcement gate scans the very file
it whitelists rather than exempting something it never looked at.

## Golden-capture technique, and the one behaviour it cannot preserve

Verified working. The lint derives its root from its own `__file__`, so copying
it into `<fixture>/tools/` makes `<fixture>` its root. Probed against a
synthetic catalogue: the unmodified lint ran, five checks passed, all emitted
paths were **root-relative with no absolute path in either stream**, and three
consecutive runs produced **byte-identical stdout and byte-identical stderr**.
That is what makes byte-for-byte comparison across roots viable, and it is why
the preserved-behaviour contract is a captured baseline rather than a prose
enumeration.

Two constraints the probe surfaced:

1. **Fixture roots must be `git init`-ed.** In a directory that is not a Git
   worktree, `git check-ignore` exits 128; under a fail-open policy that becomes
   an empty ignored set, silently no-opping the layer the fixture is meant to
   exercise.
2. **`_NO_RUNNER` cannot be captured — it must become injectable.** The
   unmodified lint staged into a fixture root emitted one stale-exemption finding
   for **every** real `_NO_RUNNER` entry (8 findings, the only failing check).
   The captured baseline therefore binds the refactored lint when given the
   *real* map; the injected-map behaviour is new specified behaviour tested on
   its own. This is the single intentional divergence between captured and
   required output.

## A 22nd fail-closed emission, outside the `FAILURES` list

`tools/lint-pack-test-boundary.py:59-60` raises `SystemExit` at **import time**
when `packs/` is absent, with a load-bearing message. It is not a
`FAILURES.append` site — an AST sweep finds exactly 20 of those — but it is a
fail-closed refusal, and it is the emission most disturbed by the refactor:
`PACKS` becomes context-derived, and an import-time guard against the real root
would fire when the suite loads the module for a fixture run. The refactor moves
it into `--root` canonicalisation.

Related precision: two diagnostics are **not** independent findings.
`test is not below packs/<pack>/` (`:726`) and `unparseable Python:` (`:720`) are
returned by `_pack_test_escapes` as `(lineno, message)` tuples and surface inside
the `pack test reaches above …` message's `{expression}` slot at `:791`. A test
asserting them as standalone findings would be written wrong.

## Enforcement-gate scan set and allowlist

The gate enumerates **tracked** files via `git ls-files` over `tools/`,
`packs/`, `packages/`, and exempts an explicit **allowlist of individual files**
— filename *patterns* are forbidden, because `tools/test-*.py` files are CI gates
in this repository.

Superseded by the measured after-figures in
[§ After evidence](#after-evidence-measured-2026-08-17-same-host): the scanned set
is **817 files with 4 allowlist entries**, against a recorded floor of **700**.
The mid-work estimate below (765 tracked `.py`, 2 allowlist entries, ≈763 floor)
predates two corrections — the enumeration adding new-but-not-ignored files, and
`SCAN_ROOTS` gaining `.github` and `Makefile` — and is retained only so the
correction is legible.

| Quantity (superseded estimate) | Count |
| --- | --- |
| tracked `*.py` under `tools/`, `packs/`, `packages/` | 765 |
| explicit allowlist entries | 2 |
| floor for the scanned set | ≈763 |

Allowlist, each with its reason:

| File | Reason |
| --- | --- |
| `tools/test-run-pack-evals.py` | contains a real `git check-ignore` call on a **single** path, asserting a genuine `.gitignore` fact |
| `tools/test-pre-pr.sh` | non-Python textual half only; documents the probe path in a comment |

**Superseded measurement.** An earlier draft recorded 765 total / 473 excluded /
**292 scanned**, measured under an exclusion rule of "basename starts
`test-`/`test_`, or the path contains a `tests/` segment". That is the *pattern*
rule the spec now forbids, so 292 is **not** the gate's floor and is 2.6× too
low. Retained here only so the correction is legible.

## Two behavioural details the refactor must not flatten

1. **`case_pack_tests_stay_in_pack` is deliberately not ignore-filtered.** It
   walks `packs/<pack>/tests` with a raw `os.walk`
   (`tools/lint-pack-test-boundary.py:763`), **not** through `_walk`, so a
   gitignored `.py` file under a pack's test tree is still inspected for climbing
   above its owning pack. The single batched ignored-set therefore applies only
   to `_walk` outputs. Applying it universally would newly exempt gitignored pack
   tests from source confinement — a contract weakening disguised as
   deduplication.
2. **`_test_basenames` has no production caller.**
   `tools/lint-pack-test-boundary.py:855` is called only from the self-test
   (`tools/test-lint-pack-test-boundary.py:601,653`); no `case_*` uses it. Adding
   test basenames to the per-invocation inventory would add a `_walk` over every
   destination that no check consumes — more traversal, not less. It stays a
   lazily-called helper.

---

## Baseline evidence (before)

`tools/lint-pack-test-boundary.py`, one full six-check invocation:

| Metric | Before |
| --- | --- |
| `git check-ignore` subprocesses | **337** |
| all other Git subprocesses | 0 |
| `_walk()` calls / distinct bases | **141 / 109** (32 redundant) |
| `_glob_tree_is_confined()` calls / distinct bases | **45 / 16** (29 redundant) |
| `_runner_lines()` invocations (re-reads + re-parses 6 runner files) | **2** |
| `_destinations()` invocations (re-walks 32 skill dirs) | **2** |
| `_packs()` invocations | **5** |
| `_projected_packs()` invocations | 1 |
| inventory constructions | **none — no inventory exists** |
| wall clock, one invocation | **32.35 s** |

`tools/test-lint-pack-test-boundary.py` — **measured** in an isolated worktree
at `63c71012`, not derived:

| Metric | Before |
| --- | --- |
| full production-lint CLI launches | **12** |
| implied `check-ignore` subprocesses across the suite | **~4 044** (12 × 337) |
| real-worktree scans | **12** |
| real `Makefile` rewrites | **2** |
| real pack-tree plants | 7 distinct plant sites |
| **measured wall clock** | **306.4 s (5.1 min)** |
| **exit code** | **0 — the suite passes** |
| **cases reported at runtime** | **82** — the floor the refactor must not regress |
| static `cases += 1` sites | **47** (loops make the runtime count higher) |

306.4 s exceeds the 300 s inner-loop budget by ~6 s. The suite is *correct* and
sits almost exactly on the cutoff, which is why the earlier run presented as
"71% then stall" rather than as a failure: any additional load tips it over.

An earlier draft of this audit estimated a "≈6.5 min floor" by multiplying
12 × 32.35 s. That was an over-estimate and is withdrawn — later launches hit a
warm filesystem cache. The measured 306.4 s is the figure of record.

`tools/lint-agents-md.py`:

| Metric | Before |
| --- | --- |
| `git check-ignore` subprocesses | **3** (one per probe) |
| wall clock | 0.82 s |

Every other production lint: **0.13 s – 5.33 s**, and **0** `check-ignore`
subprocesses. Full sweep in the P0 spec's evidence section.

---

## A shipped spec already committed to this work, and only half shipped

`docs/specs/pack-test-boundary-remaining-packs/spec.md` is **Shipped**. Its
`plan.md:636` reads:

> Add the `--` terminator to `git check-ignore` **and batch paths over stdin
> rather than one subprocess per file.**

Only the first clause landed. `tools/lint-pack-test-boundary.py:162` carries the
`--` terminator; the stdin batching was never implemented, which is why the
per-path subprocess loop survived into this audit. This spec completes the
unimplemented half.

That shipped spec's `AC10a` (`spec.md:395`, marked `[x]`) asserts as part of its
contract:

> `git check-ignore` is invoked with a `--` terminator.

The batched resolver invokes `git check-ignore --stdin -z` with **no** path
arguments at all, so the `--` terminator becomes meaningless — there is no argv
path for it to disambiguate. The protection `--` provided (a path that looks
like an option cannot be parsed as one) is *strengthened*, not lost: candidates
move off argv entirely onto NUL-framed stdin, which no option parser reads.
`AC10a`'s literal wording is nonetheless superseded and must be annotated in the
frozen document per `docs/CONVENTIONS.md § Superseding a frozen document`.

This is a correction to the audit: the first pass of this inventory recorded
`lint-pack-test-boundary.py`'s Git process shape without noticing that a shipped
spec had already specified the fix.

## Existing backlog item this audit closes

`workspace.toml [backlog].open` already carries
`selftest-mutates-tracked-makefile`:

> Stop `tools/test-lint-pack-test-boundary.py` from mutating the real
> `Makefile` in place; a concurrent `git add -A` commits its injected
> violation and the failure surfaces only in CI.

The recorded history is concrete — *"That happened on PR #961"* — and the
recorded fix (*"build the fixture in a tmpdir copy, or drive the linter with a
`--makefile` argument, so no tracked file is ever mid-mutation"*) is the same
change this spec makes via the fixture-root option. The Wave 2 falsification
refactor closes this item; it moves to `[backlog].closed` at finish time rather
than being deferred again.

Its trailing note — *"Same pattern is worth auditing across `tools/test-*`"* —
is discharged by § 4 of this inventory: all 66 other lint self-tests were
audited and none mutates a tracked file.

## After evidence (measured 2026-08-17, same host)

Same probes as [§ Measurement method](#measurement-method): a counting Git shim
on `PATH`, counter-instrumented seams, and `/usr/bin/time`-equivalent wall clock
on a warm cache. All paths relativized.

### `tools/lint-pack-test-boundary.py`, one full six-check invocation

| Metric | Before | After |
| --- | --- | --- |
| `git check-ignore` subprocesses | 337 | **1** |
| inventory constructions | none — no inventory existed | **1** |
| runner-file parses | 2 | **1** |
| destination-inventory builds | 2 | **1** |
| tree-confinement scans | 45 over 16 distinct bases | **16** (one per distinct base) |
| lazy walk misses (bases not pre-batched) | n/a | **0** |
| wall clock | 32.35 s | **1.43 s** (≈23× faster) |
| stdout / stderr | — | **byte-identical** across all 20 captured baselines |

### `tools/test-lint-pack-test-boundary.py`, complete suite

| Metric | Before | After |
| --- | --- | --- |
| wall clock | **306.4 s** (6 s over the 300 s budget) | **16.7 s** |
| cases reported | 82 | **134** |
| exit code | 0 | 0 |
| production-CLI launches against the real tree | 12 | **4** (budget asserted by the suite) |
| real `Makefile` rewrites | 2 | **0** |
| real-tree plant sites | 7 | 2, both `try`/`finally`-guarded and refusing a pre-existing target |
| `check-ignore` processes across the whole suite | ~4 044 | **45** (one per invocation) |

### `tools/lint-agents-md.py`

| Metric | Before | After |
| --- | --- | --- |
| `git check-ignore` subprocesses | 3 (one per probe) | **1** |
| Git-absent behaviour | unhandled `FileNotFoundError` traceback | exit 1 naming Git unavailability |
| Broken-Git behaviour (exit 127) | 3 notes falsely claiming `.gitignore` drifted | exit 1 naming Git unavailability |

### Enforcement-gate scan set

Measured under the specified allowlist rule, via
`git ls-files --cached --others --exclude-standard` over `tools/`, `packs/`,
`packages/`, `.github/` and the root `Makefile`: **817 files scanned, 4
allowlisted**, against a recorded floor of **700**.

Two earlier figures are withdrawn: **292** was measured under the
filename-pattern exclusion the spec forbids, and **800 / 5 allowlisted** predates
adding `.github` + `Makefile` to the scan roots and dropping the
`tools/test-pre-pr.sh` entry (its only mention of the probe is a comment, which
the textual matcher already skips, so an allowlist entry would have hidden a
future real invocation there).

### Discriminating power, verified by mutation

The captured baseline is only worth what it detects, so it was tested against
deliberate weakenings of the lint rather than assumed:

| Mutation | Detected? |
| --- | --- |
| `_walk` stops subtracting the ignored set | **yes** — exactly one fixture (`only-gitignored-tests`), 2 findings → 9 |
| symlink/junction refusal removed | **yes** — `linked-test-dir`, `linked-test-root`, both streams |
| `evals/` skip removed | **yes** — 2 fixtures |

That run also exposed a defect in the fixture itself: the original plant was
`test_demo.gitignored`, which `_TEST_FILE` never matches, so the fixture produced
the right output for entirely the wrong reason. It now plants a real `.py` file
ignored by an explicit path rule — both conditions at once.

### Gate-run evidence

For a goal-based task the record *is* the artifact, so each command is listed
with the exit code it actually returned. Terminal wording unchanged throughout.

| Command | Exit | Note |
| --- | --- | --- |
| `python3 tools/lint-pack-test-boundary.py` | 0 | six `ok` lines + `✓ … passed (6 cases).` |
| `python3 tools/test-lint-pack-test-boundary.py` | 0 | 128 cases; 4 real-tree CLI launches |
| `python3 tools/test-lint-boundary-golden.py` | 0 | 22 captured baselines reproduced |
| `python3 tools/test-lint-boundary-structural.py` | 0 | 48 cases |
| `python3 tools/test-lint-git-ignore.py` | 0 | 88 cases |
| `python3 tools/lint-no-direct-check-ignore.py` | 0 | 817 files scanned, 4 allowlisted |
| `python3 tools/test-lint-no-direct-check-ignore.py` | 0 | 37 cases |
| `python3 tools/lint-agents-md.py` | 0 | unchanged terminal wording |
| `python3 tools/test-lint-agents-md-gitignore-probes.py` | 0 | 17 cases |
| `python3 tools/test_lint_agents_md_{legacy,diataxis,risk}_block.py` | 0 | 3 suites, unchanged |
| `python3 tools/test-lint-ci-parity.py` | 0 | 102 cases; aggregator-extraction anchor holds |
| `python3 tools/test_build_gate_chain.py` | 0 | 19 tests; ordered chain list updated |
| `python3 tools/test-test-all.py` | 0 | 16 cases |
| `python3 -m pytest tests/roster/test_core_pre_pr_hook.py` | 0 | 11 tests |
| `bash tools/test-pre-pr.sh` | 0 | 4 sandbox cases, incl. `agents-md-fail` |
| `agentbundle catalogue lint --deep` | 0 | `ok: 58 finding(s)` (warnings only) |
| `agentbundle catalogue verify` | 0 | `catalogue verify: ok` |
| `python3 tools/catalogue/pre_pr_catalogue.py` | 0 | 19/19 steps `✓`, fail-fast order intact |
| `SKIP_SAST=1 make build-check` | 0 | full required chain incl. the 5 new steps |
| `python3 tools/lint-ruff.py` | 0 | `All checks passed!` |
| `scripts/lint-spec-status.py --root .` | 0 | `spec metadata clean` |

`make lint-mypy` is deliberately **absent**: `tools/lint-mypy.py` targets only
`packages/agentbundle/agentbundle` and `packages/credbroker/credbroker`, so it
type-checks nothing in this diff. Claiming it would be a vacuous pass.

### Budget

The work-loop inner-loop budget is 300 s. The complete optimised falsification
suite finishes in **16.7 s**, and the production lint in **1.43 s**. The
71%-then-stall behaviour is not reproducible: the suite that previously sat 6 s
past the cutoff now completes in 5.6% of it.

---

## Recorded P1 residuals

Out of scope here; captured so they are not silently lost.

1. **Cross-process duplicate scans in `pre_pr_catalogue.py`.** ~30 lints run
   as separate processes; several independently enumerate `packs/*`. Sharing
   one inventory across processes needs a persistent cache or an in-process
   aggregator — both explicit non-goals.
2. **`lint-nosec-form.py` at 5.33 s** is the slowest non-P0 lint. One bounded
   pass over three source roots, no ignore queries; a P0 change is not
   warranted.
3. **`agentbundle catalogue verify` at 13.47 s** is the slowest single gate.
   Its one Git call is already batched; cost is filesystem traversal of
   `dist/`.
