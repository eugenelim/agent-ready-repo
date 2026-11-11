# Product changelog fragments verification ledger

This ledger records execution observations for the approved spec and plan. It
does not replace either contract.

## T0 — shared historical parser owner

- Approved AC1 stub: materialized byte-identically in
  `tools/test_build_site_routing.py`.
- Intended red: `owner.name` was `build-site.py`, not `changelog.py`.
- Targeted suite: 95 passed, 1 skipped in 6.55 seconds.
- `/now/` payload: 415,060 bytes, 190 groups, SHA-256
  `5a19ca9db841afe0821a3df856f8a1f45416503ee93f4661f3116c845186e874`;
  unchanged by the relocation.

## T1 — confined fragment-reader limits

- Decision authority: scope-owner approval in the active work-loop on
  2026-09-29.
- Maximum directory entries: 65,536.
- Maximum regular fragment files: 65,536.
- Maximum relative path depth: 1; fragments remain direct children of
  `docs/product/changelog.d/`.
- Maximum fragment size: 1 MiB (1,048,576 bytes).
- Grounding: the repository parser found 389 entries on 2026-09-29 and 387 new
  entries over the prior 67 days, about 2,110 per year. The count limit is
  about 168 times the observed corpus and gives about 31 years from an empty
  fragment directory at that rate. Across the 389 entries, the median entry
  was 827 bytes, the 99th percentile was 4,450 bytes, and the largest was
  10,302 bytes; 1 MiB is about 102 times the observed maximum.

## T2 — fragment creation seam

- Discovered callable seam: `create_fragment(...)`; the `new` CLI invokes the
  same function.
- Materialized construction proof: creation round-trips through
  `validate_fragment`, composes the anchor from the fragment's own fields, and
  performs no sibling enumeration.
- Intended red: the focused construction selection reported 4 failures and 10
  deselections. The in-process cases failed because `create_fragment` did not
  exist; the CLI case returned no created path.
- Green: the combined changelog and site-routing suites reported 109 passed and
  1 skipped in 7.67 seconds.

## T3 — merge-base identity boundary

- Approved AC4/AC5 stub: materialized byte-identically in
  `tools/test_changelog.py`.
- Discovered boundary: `_base_fragment_record(...)` resolves the merge base,
  classifies the path, and reads the base blob; `_enforce_committed_identity`
  compares the three permanent identity fields.
- Intended red: the approved date-edit test failed because the committed edit
  was accepted.
- Green: the complete Git boundary matrix reported 9 passed and 14 deselected;
  the combined changelog and site-routing suites reported 118 passed and 1
  skipped in 9.99 seconds.

## T4 — deterministic assembly seam

- Discovered seams: `collect_validated_fragments(...)` is the source boundary;
  `assemble_changelog(...)` is the canonical serializer.
- Intended red: the three assembly tests failed because the collection seam did
  not exist.
- Shuffle proof: 5 enumerations produced 1 canonical digest; bypassing only the
  canonical sort produced 5 digests.
- History proof: two real Git repositories held byte-identical sources but had
  different commit SHAs, authors, emails, and dates; their assemblies were
  byte-identical.
- Green: the combined changelog and site-routing suites reported 121 passed and
  1 skipped in 19.37 seconds.

## T5 — complete-view renderer

- Goal seam: `python3 tools/changelog.py render --output <path>` validates all
  sources before atomically replacing the output.
- Intended red: 4 renderer tests failed because `render` was not a recognized
  subcommand.
- Frozen baseline: 648,314 bytes with SHA-256
  `f1e82733697d6683ccdea62ead0973110b5132e0767dce007f9db5adf107aa2c`;
  the zero-fragment output is byte-identical.
- Git-cleanliness: the generated path is ignored, and the clean-checkout fixture
  remains clean after rendering.
- Green: the combined changelog and site-routing suites reported 125 passed and
  1 skipped in 16.73 seconds.

## T10 — merge-independence measurement

- Base commit: `708ae9cd1c87d16b034e183e7b577d1f80d095c4`.
- Classifier controls: the known-conflicting pair was bucketed as a changelog
  conflict; the known-clean pair was bucketed as clean.
- Delivered fragment arm: 20 branches and 190 pairs created through
  `tools/changelog.py new`; 190 clean, 0 conflicting, 0 errored.
- Monolith control: 20 branches and 190 pairs; 0 clean, 190 conflicting, 0
  errored.
- The measurement left the pre-existing worktree status unchanged.

## T11 — release and documentation integration

- Core-release validation now considers only added or modified fragments against
  its explicit base, loads the shared changelog model by path, and retains the
  `/now/` Highlights parity check. An unchanged matching fragment cannot satisfy
  a release.
- Release-impact validation recognizes `docs/product/changelog.d/<id>.md` while
  retaining its no-evidence refusal.
- Both Pages trigger maps and the workflow posture allowlist pin
  `docs/product/changelog.md` and `docs/product/changelog.d/**`.
- Green: the two release suites reported 42 passed in 31.48 seconds; the Pages
  posture checker caught all 40 mutations across 23 assertion families.

## T6 — unreleased-to-released transition

- Decision: on 2026-09-29, eugenelim selected released status derived from the
  packages' released versions. No clearable marker is added, fragment creation
  is not deferred, and merged `packages`, `date`, `id`, and `anchor` remain
  unchanged.
- Discovered seam: `is_fragment_released(fragment, released_versions)` consumes
  an explicit released-version inventory; the deterministic assembler gains no
  clock, Git, network, or implicit filesystem dependency. Missing versions stay
  pending, and malformed inventory values are refused.
- Intended red: 4 transition tests failed because neither the inventory-aware
  assembly argument nor fragment `/now/` projection existed.
- Green: the combined changelog and site-routing suites reported 129 passed and
  1 skipped in 18.41 seconds. The pending record emits no `/now/` group; after
  release the same source bytes and id emit one group, while every other record
  remains byte-identical.

## T7 — shared site and `/now/` model pass

- One historical parse plus one validated fragment collection now feeds both
  the site changelog and the schema-v1 `/now/` projection.
- Approved historical arm: the baseline at `93bf9cc9e` remains byte-identical
  through the shipping projector and has SHA-256
  `72305605f91380cc591c488a956695f8d2856770411f514a7d12a8705d538b40`.
  This proves parity through the shipping projector, not an independent
  re-derivation of the historical payload.
- Supplemental current-head arm: SHA-256
  `5a19ca9db841afe0821a3df856f8a1f45416503ee93f4661f3116c845186e874`.
- Released-version inventory combines frozen historical releases with current
  pack manifests. Exact/current and older numeric versions publish; future,
  missing-pack, and ambiguous non-matching versions remain pending.
- The six web consumers are unchanged. Atomic groups, emitted-anchor coverage,
  one-parse counting, build counts, and both refusal classes are covered.
- Green: the combined changelog and site-routing suites reported 140 passed and
  1 skipped in 19.20 seconds.

## T8 — frozen historical baseline

- Invoking boundary: `.github/workflows/pages.yml`, step `Validate frozen
  product changelog baseline`, invokes
  `python3 tools/changelog.py render --output build/product-changelog.md` before
  either site build.
- `docs/product/changelog.md` gained only the migration notice. Its 330
  versioned release sections retain SHA-256
  `dbd4ca7466f7c04397a05d0aa7c0ddaf13c3daa1c608f5447a0f1e3869566ba5`.
- Intended red: the notice was absent and render accepted an edited historical
  release body.
- Green: render refuses a historical heading/body edit naming its heading and
  accepts a notice-only edit through the same CLI boundary. The combined
  changelog and site-routing suites reported 144 passed and 1 skipped in 21.65
  seconds; the Pages posture checker remained green.

## T9 — historical-anchor counterfactual

- Base commit: `708ae9cd1c87d16b034e183e7b577d1f80d095c4`.
- Instrument control: a deliberate duplicate-heading insertion moved 2
  historical anchors, so the duplicate-suffix detector is live.
- Real 20-update monolith arm: 0 historical anchors moved.
- Same-source fragment arm: 0 historical anchors moved.
- The detached-object measurement left the pre-existing worktree status
  unchanged.

## T12 — author guidance and tracked template

- The three live guidance surfaces now show a runnable `new` invocation with
  package, version, date, and highlight arguments, then direct the author to
  edit the created fragment and stop.
- `docs/product/changelog-fragment-template.md` is tracked outside the scanned
  directory. Its placeholders are refused; after substitution at a matching
  UUID path, the same shape validates.
- The live-guidance search is clean after excluding immutable specs, RFCs,
  ADRs, historical research, and test fixtures. Those frozen records were not
  rewritten.
- The 330 historical release sections retain their T8 digest. The focused
  changelog suite reported 42 passed in 21.25 seconds.

## T13 — instrument-validity decision

- Decision authority: eugenelim, before the performance run on 2026-09-29.
- A retained arm is valid only when `(maximum duration - minimum duration) /
  median duration <= 20%`.
- If any arm exceeds that bound, the run is inconclusive and no performance
  ratio is accepted.

## T13 — three-arm build-cost run

- Durable report:
  `docs/product/research/changelog-fragment-build-cost.md`, recorded externally
  in commits `d72fffe55` and `ac54cc871` after the local runtime refused the
  approved build operation.
- Canonical large corpus: 3,300 released records in both physical layouts; the
  normalized 2,970 generated-record set was identical across arms.
- Whole-build medians: today 23.69 seconds, monolith-10x 86.57 seconds,
  fragments-10x 129.41 seconds.
- Validity: today spread 47.4% (fail), monolith-10x 11.2% (pass),
  fragments-10x 17.4% (pass). Per the precommitted rule, the performance run is
  **INCONCLUSIVE** and its recorded +49.5% median ratio is not accepted.
- Published page count: **SURVIVE**. Both large arms emitted 3,369 marketing
  pages, 3,319 `/now/` pages, and 267 docs pages in every sample.
- Pass 1 exposed two implementation defects: missing Starlight frontmatter on
  the generated changelog page and per-fragment Git subprocess fan-out. The
  pass-2 overlay contained the fixes and focused regression tests now present in
  `tools/build-site.py`, `tools/changelog.py`, and their suites.
- Cleanup independently confirmed both recorded disposable clone paths are
  absent.

## T15 — aggregate-build optimization and valid cost rerun

- The aggregate `site-build` recipe now runs `site-sync` once and invokes both
  package builds with npm lifecycle hooks suppressed. The package-local
  `prebuild` hooks remain unchanged for direct builds.
- Construction checks: 2 passed. One real untimed `make site-build` exited 0;
  its output showed one shared projection and no package `prebuild` projection.
- Pass 3 reused the prior canonical large corpus: 3,300 released records in
  both layouts, with the normalized 2,970 generated-record set identical and
  hash-stable across all three passes.
- Whole-build medians: today 17.40 seconds, monolith-10x 77.05 seconds,
  fragments-10x 91.45 seconds.
- Validity: today spread 8.6%, monolith-10x 7.5%, fragments-10x 8.2%. Every arm
  passes the precommitted 20% bound, so the ratio is accepted.
- Build performance: **KILL**. Fragment layout cost is +18.69%, above the § 7
  requirement of strictly under 10%. The owner had already designated that bar
  as a delivery blocker; T14 was not started.
- Published page count: **SURVIVE**. Both large arms emitted 3,369 marketing
  pages, 3,319 `/now/` pages, and 267 docs pages in all six samples per arm.
- The retained report is
  `docs/product/research/changelog-fragment-build-cost.md`. HEAD remained
  `ac54cc871b3078edfe6b13526827767e9e4ebf1e`; no commit was created. The
  disposable clone `/private/tmp/t15rerun.S0gPJ1Nr` was deleted and its exact
  path was confirmed absent.

## T16 — pre-edit profile refutes the locked owner

- The pre-edit profile is retained in
  `docs/product/research/changelog-fragment-build-cost.md#t16-pre-edit-profile-the-locked-hypothesis-is-refuted`.
- Equal-scale fragment projection median: 13.58 seconds. Released-inventory
  re-validation consumed 7.55 seconds (55.6%); repeated file-safety helper
  loading consumed 2.25 seconds (16.6%). The locked loader hypothesis therefore
  failed both its dominance and 6.695-second sufficiency gates.
- Root cause: `is_fragment_released` normalized and revalidated the whole
  released-version inventory on every call. Assembly and `/now/` projection
  produced 8,912 normalizations and 33,183,844 regex matches for 2,970
  fragments, creating quadratic work in the fragment and inventory counts.
- The attribution-only counterfactual preserved byte-identical complete-view
  and `/now/` outputs and 2,970 confined reads at the 1,048,576-byte bound.
  Its four-arm spread failed the 20% validity rule on three arms, so no ratio or
  replacement § 7 verdict was accepted.
- No production code changed and no fourth three-arm pass ran. The approved
  loader-cache stub remains red. The disposable clone
  `/private/tmp/t16prof.d8MdXvJ3` was deleted and its exact path confirmed absent.
- Corpus limitation: the prior generator was not retained. The reconstruction
  matched all recorded counts and fragment bytes but its monolith was 780 bytes
  smaller (0.015%) and the old normalized hash could not be reproduced because
  its serialization and UUID namespace were never recorded. A later pass may
  decide the bar from its own equal-record arms, but cross-pass median comparison
  must be labeled non-comparable.

## T16 — production change and pass-4 measurement

- Production behavior: `assemble_changelog` and `project_fragment_now_highlights`
  each validate and normalize the released-version inventory exactly once per
  projection and then use the private `_fragment_in_released_inventory`
  predicate once per fragment. `is_fragment_released` remains a validating
  public boundary that normalizes and delegates to the same predicate. Nothing
  is memoized.
- Intended red reproduced before acceptance: restoring only the pre-edit call
  pattern on a scratch copy, with no source file edited, fails the approved stub
  with `assert 5 == 1` for two fragments.
- Green: focused T16 checks 2 passed; `tools/test_changelog.py` 51 passed;
  `tools/test_build_site_routing.py` 110 passed. Ruff and `py_compile` pass.
- Output equivalence on the 2,970-fragment pass-4 corpus, before versus after
  the optimization: complete changelog 5,368,312 bytes with SHA-256
  `3fe1d172fe7f886a56babaf2a888a52bc0827a21e7befb334f312e219ec03cbb`, and
  `/now/` payload 3,924,027 bytes with SHA-256
  `d6d2fb92e50a182d5989b6be481ca6156259fe9d53231e0216a893d4c63f71af` — both
  byte-identical. Confined fragment reads stayed at 2,970 under the unchanged
  1,048,576-byte bound. Released-inventory normalizations fell from 8,912 to 2,
  and 8,912 is exactly the figure the pre-edit profile recorded.
- Pass-4 corpus: 3,300 released records in both layouts — 2,970 generated plus
  330 historical — producing 3,160 released highlight groups and 5,648
  highlights in each large arm. Read back from disk, both layouts yielded 2,970
  records with 0 unique to either side and the same normalized set SHA-256
  `9338c9a0d45c9f350bf56d9589b07c3e607ff7f0d86a8c4cab532cbe7556c99b`. The
  generator lived only in the disposable clone; its SHA-256, UUID namespace,
  canonical serialization rule and input manifests are recorded in the report.
- Pass 4 ran the locked protocol twice on 2026-10-01. Validity: run 4a today
  29.47% (fail), monolith-10x 9.51%, fragments-10x 8.20%; run 4b today 27.60%
  (fail), monolith-10x 5.58%, fragments-10x 14.72%. Per the precommitted 20%
  bound both runs are **INCONCLUSIVE** and no ratio is accepted from either.
  Run 4b was agreed after a 1,955-second untimed stall was identified in 4a,
  before 4b's numbers were seen; 4b was undisturbed and still failed the same
  arm. Bare process-spawn latency measured 1.8 times pass 3's on the same
  machine, so the instrument detected a loaded machine rather than a build
  property.
- Build performance: **unchanged**. § 7 continues to read pass 3's `KILL` at
  +18.69%. The unaccepted pass-4 large-arm figures (+18.41% and +14.66%) are
  retained as provenance only.
- Published page count: **SURVIVE**. Both large arms emitted 3,369 marketing
  pages, 3,319 `/now/` pages and 267 docs pages in all ten retained large-arm
  samples across both runs, matching pass 3 exactly. This criterion reads no
  duration, so the timing invalidity does not touch it.
- The aggregate build ran the shared projection once and emitted no package
  `prebuild` projection in all 30 retained samples; both standalone `prebuild`
  hooks remain in `web/package.json` and `docs-site/package.json`.
- HEAD remained `ac54cc871b3078edfe6b13526827767e9e4ebf1e`; no commit was
  created in the source worktree, and a re-manifest after the run matched the
  pre-run manifest exactly. The disposable clone `/private/tmp/t16pass4.NBOeM5lA`
  was deleted and its exact path confirmed absent.

## T16 — pass 5, the one readiness-gated final run

- Readiness: samples 18–22, 16:49:05–16:53:05 UTC on 2026-10-03, were five
  consecutive one-minute passes, with one-minute load 3.22–9.56 and ten-spawn
  means 19.15–27.50 ms. The 60-spawn confirmation measured 19.72 ms at load
  6.53, and admission came at 16:53:07.088 UTC. All 22 samples are in the
  report.
- Corpus: pass 4's generator, SHA-256 `5799a245…`, rebuilt the corpus byte for
  byte. Monolith manifest `571d2a8a…`, fragment manifest `bb8b1939…`,
  normalized set `9338c9a0…`, 3,300 released records (2,970 + 330), 3,160
  groups, 5,648 highlights, 2,970 read back per layout, 0 unique to either.
- Guards before timing: focused 2 passed; `tools/test_changelog.py` 51 passed;
  `tools/test_build_site_routing.py` 110 passed; Ruff and `py_compile` pass.
  Changelog and `/now/` output byte-identical before and after T16; 2,970
  confined reads at 1,048,576 bytes; normalizations 8,912 → 2.
- Valid: spreads were today 11.98%, monolith-10x 7.21%, fragments-10x 10.89%.
  Medians were 16.1735 s, 74.7709 s and 83.8331 s. All 18 samples exited 0.
- Build performance: **KILL**. Fragment layout cost is +12.12%, which is not
  strictly below 10%. Release growth cost is +362.30%. Published page count:
  **SURVIVE**, at 3,369 / 3,319 / 267 in both large arms. Per T16's done-when,
  delivery stops and T14 must not run.
- Integrity: three setup attempts stopped before readiness on harness defects,
  each in its own clone, and each clone was deleted. The measured clone
  `/private/tmp/t16pass5.yvunLRUp`, 1.1 GB, was deleted: `test -e` false, and
  no `/private/tmp/t16pass5.` path remains. The source manifest
  `94e1cfee…`, 7,005 files, matched after every teardown. HEAD stayed
  `ac54cc871b3078edfe6b13526827767e9e4ebf1e`. No commit or push.

## Rebase onto `origin/main` at `afcc1eeb8` — 2026-10-04

- The delivery was rebased from `ac54cc871b30` onto
  `afcc1eeb8b9111bb44d90d37fb37ee468a93c260`, which is 76 upstream commits
  later. It went through one local WIP commit that was then undone. Nothing was
  pushed, and the rebase had no conflicts.
- Upstream added release sections dated 2026-09-23 to 2026-10-03 to
  `docs/product/changelog.md` before cutover. They are pre-cutover history, so
  three pins moved to the rebased file:
  - the render digest is now
    `89d3cc8264927569146db1cb825b44ed43465587851fcede214af541d18dec86`, which
    still equals the file's own hash;
  - the historical-section digest is now
    `a034963223dad5ea4e8dbff2564787b39a3eba8fd83f4c4118673c8f960d4408`;
  - the zero-fragment `/now/` digest is now
    `853873f08a7c146273b2ba36bc501b9f8073542743e302e2c6b9bdb2a19e2d45`.
- The anchor test passed after a fresh `make site-build`, which built 273 docs
  pages in 26.8 s.
- Ruff's context-manager rule required `Generator` in
  `tools/measure-changelog-anchor-drift.py`.
- Results: `tools/test_changelog.py` and `tools/test_build_site_routing.py`
  passed 161 tests; `tools/test_check_core_release.py` passed 31;
  `tools/test_check_release_impact.py` passed 11; the pages-workflow self-test
  passed; Ruff passed; mypy found no issues in 149 files.
- T18 restores pass 4's baseline `changelog.md` bytes (`ff02ab91…`) in its
  clone, so the corpus stays byte-identical to passes 4 and 5.

## T18 — one readiness-gated pass at the bundle ceiling, valid and a survive

- **Readiness:** admitted at 21:47:23.764 UTC on 2026-10-12. Samples 25–29
  passed consecutively, with load 9.66 down to 6.80. The 60-spawn
  confirmation measured 16.71 ms at load 6.80. The report records all 29
  samples, including a spike to load 80.14 at 21:31 that reset the streak.
- **Corpus:** pass 4's corpus, byte for byte, on base `6dc2ba5f5`:
  - the pass-4 baseline came from `ac54cc871` plus the migration notice,
    `ff02ab91…`, 648,990 bytes;
  - the generator ran unchanged (`5799a245…`), with its pack list pinned to
    pass 4's 22 packs, because upstream's `code-intelligence` pack shifted
    the substitution index;
  - manifests `571d2a8a…` and `bb8b1939…`, and normalized set `9338c9a0…`.
- **Arm:** T17's part writer bundled 1,970 records into 4 parts and left the
  newest 1,000 loose: all released, 0 pending. Complete changelog
  `3fe1d172…` and `/now/` `d6d2fb92…` are identical to the all-fragments
  layout.
- **Guards before the baseline restore:** focused T16 and AC-B1 checks 2
  passed; `tools/test_changelog.py` 118 passed;
  `tools/test_build_site_routing.py` 115 passed; Ruff and `py_compile` pass.
  `validate` accepted the committed corpus.
- **Result:** valid. Medians and spreads:
  - today 16.1773 s, spread 11.12%;
  - monolith-10x 72.0607 s, spread 4.68%;
  - bundled-10x 77.2652 s, spread 5.05%.
- **Verdicts:** fragment layout cost **+7.22%**, so **Build performance:
  SURVIVE**. Release growth cost is +345.44%. **Published page count:
  SURVIVE**, at 3,371 / 3,319 / 273 in both large arms. All 18 builds and
  all 24 attribution samples exited 0.
- **ADR-0138 Revisit is triggered:** 7.22% ≥ 5%. That decision belongs to
  the owner.
- **Integrity:** the admitted clone `/private/tmp/t18pass.rt0Vc6ZY` (999 MB)
  and the setup-only clone `/private/tmp/t18pass.r8pTNG4A` were both deleted,
  with `test -e` false. No `t18pass.*` path remains. The source manifest
  matched after both teardowns. No commit or push.

## Pre-PR amendment — 2026-10-12

- **What changed:** ADR-0138 was renumbered to ADR-0143, because 0138–0142
  had been taken on other branches. Its D9 ceiling changed to 500, with the
  warning at 375, and the owner re-accepted it. AC-B9 was narrowed to Git's
  rename behaviour for one-record parts. Plan task T19 was added, and T14 now
  runs after it.
- **Review:** round 16 sustained three advisory adversarial findings, which
  were applied, and one security finding, which was refuted. Round 17 was
  clean.
- **Record correction:** the engine's `contract-amendment` event (sequence
  68) carries an owner-authority reference dated 2026-10-13. The approval was
  given on 2026-10-12; engine records are immutable, so this entry is the
  correction.

## Post-gates review and finish — 2026-10-12

- **Review:** 9 post-gates rounds ran across `adversarial-reviewer`,
  `security-reviewer` and `quality-engineer`, every non-clean report through
  `finding-adjudicator`. The final round left no sustained finding: adversarial
  and security clean at round 8, quality's whole-spec coverage pass clean at
  round 9. Reports live under
  `.context/reviews/d1063609-fa75-4f31-964c-edd148c9f7b3/`.
- **Production fixes from review:**
  - `validate` also runs the historical-baseline freeze, so build-check refuses
    an edited historical release section;
  - merge-base lookups fail closed except Git's "no merge base";
  - compact's rerun dispatch is typed (`DuplicateRecordIdError`);
  - the `compact` CLI derives the site build's released-version inventory and
    finishes an interrupted move;
  - rerun recovery applies the retraction refusal and the unique-id record cap;
  - Refusal 1b refuses a bundled record moved into an added part with changed
    bytes;
  - a merge-base part repeating one id is refused;
  - the unreachable separator guard was removed.
- **Acceptance fixtures added:** every spec-named case now has a test. Each new
  test was shown to fail with its guard disabled. The `ident` fixture builds a
  real repository where `git diff --quiet` reports an edited `$Id: … $` part as
  unchanged and `validate` still refuses it.
- **Gates at finish:** Ruff and mypy pass; 312 tests pass across the four
  touched suites; `test-pages-workflow.py`, `lint-ci-parity.py`,
  `changelog.py validate` and `lint-spec-status.py` pass.
- **End-to-end:** `changelog.py new` wrote a valid fragment to a scratch
  directory, and `render` produced the complete changelog including it.
- **Retry cap:** the review retry cap (5) fired at round 7; the owner directed
  the run to continue with `--allow-retry-cap-override`.
- **Record correction:** engine event sequence 91 (`gates-clean`) was recorded
  while Ruff reported one blank-line error in `tools/test_changelog.py`. The
  error was fixed and every gate re-run green before any later review counted;
  engine records are immutable, so this entry is the correction.
- **Status:** spec `Shipped`, plan `Done`, all 62 acceptance criteria checked.
