# Verification ledger — ci-gate-main-carve-out-sibling

Mechanical evidence for the carve-out's acceptance criteria. Each entry
names its method, its input revisions, and its result. The standing
control for everything here is the posture test's dispatch-body pin
(`PINNED_DISPATCH_BODY`): any change to the invocation set reddens
`tools/test-build-check-workflow.py` in the same commit, by design.

## AC-0001: command-set preservation (one-to-one invocation match)

- **Method.** A throwaway script (never committed) extracted the two
  moved steps' `run` bodies from the base commit
  (`5499ff9d9:.github/workflows/build-check.yml`) and the dispatch
  body's invocations from the post-change working tree, joining
  backslash continuations the same way bash does. Compared as multisets
  (the shard rebalance deliberately reorders invocations across
  branches; AC-0001 pins presence and count, not sequence).
- **Input revisions.** Before: `6dc12944e` (the plan-approval commit and
  review base — its `.github/workflows/build-check.yml` is byte-identical
  to the originally extracted before-state `5499ff9d9`, a commit that became
  unreachable after the run was re-admitted; the comparison is reproduced
  against the reachable base). After: the delivered T1 commit `3c690bcc6`.
  Both revisions are branch-reachable.
- **Result.** BEFORE: 17 invocations. AFTER: 17 invocations.
  Multiset one-to-one: **true** — zero missing, zero added. The
  27-file tools group extracts as one continuation-joined statement on
  both sides (one pytest process, ADR-0101 discipline preserved).

### The closed set (before = after, 17 invocations)

| # | Invocation (truncated at 72 chars) |
| --- | --- |
| 1 | `python tools/lint-conformance-portability.py --root .` |
| 2 | `python tools/lint-direct-code-table.py --root .` |
| 3 | `python -m pytest tests/ -q` |
| 4 | `python -m pytest packs/architect/tests/pack/ -q` |
| 5 | `python -m pytest packs/architect/tests/skills/architect-assess/ -q` |
| 6 | `python -m pytest packs/architect/tests/skills/architect-design/ -q` |
| 7 | `python -m pytest packs/core/tests/pack/ -q` |
| 8 | `python -m pytest packs/core/tests/skills/workspace-status/ -q` |
| 9 | `python -m pytest packs/credential-brokers/tests/pack/ -q` |
| 10 | `python -m pytest packs/atlassian/tests/pack/ -q` |
| 11 | `python -m pytest packs/atlassian/tests/skills/flow-metrics/ -q` |
| 12 | `python -m pytest packs/atlassian/tests/skills/jira-epic-outcome-view/ -q` |
| 13 | `python -m pytest packs/product-engineering/tests/pack/ -q` |
| 14 | `python -c "import httpx"` |
| 15 | `python -m pytest packs/linear/tests/skills/linear/ -q` |
| 16 | `python -m pytest tools/test_lint_agents_md_diataxis_block.py … (27 files, one statement) … tools/test_check_release_gate.py -q` |
| 17 | `python -m pytest tools/test_local_ci_shared_test_deduplication.py -q` |

### Shard placement (after)

- **shard-1** (~93 s by the WEIGHTS table): #1, #2, #3, #14.
- **shard-2** (~71 s): #4–#9, #16.
- **shard-3** (~69 s, dedup guard ~65 s dominant): #10–#13, #15, #17.

The heaviest single invocation (`pytest tests/`, ~90 s) sets shard-1's
floor; the split is weight-balanced from `tools/shard_test_roster.py`'s
WEIGHTS plus the dedup guard's measured ~65 s.

## Provisioning discovery (spec Assumptions, skip-aware procedure)

- **Method.** Static scan (complete enumeration of every
  `skipif`/`pytest.skip`/`importorskip` site across the moved suites:
  46 sites) plus runtime corroboration in a fresh Python 3.11 venv
  holding exactly the candidate set (pytest,
  `tools/requirements.txt`, editable agentbundle) with `-rs` skip
  reporting. The runtime environment's PATH resolved `python3` to the
  venv (a first attempt resolving to the host's Python 3.15 hung on
  `tools/lint-agents-md.py` — a local artifact, not a CI provisioning
  gap; gate-main runs the same suite green on 3.11).
- **Runtime corroboration.** All 11 pack suites, the dedup guard
  (51 passed), both linters, and the httpx import: green, zero
  provisioning-caused skips. `pytest tests/` ran locally to 23% (local
  macOS subprocess/git overhead makes the full run ~30× its ~90 s CI
  weight) with the only skips being the platform set below; the full
  suite's authoritative run is the sibling's own CI (T4).
- **Provisioning-relevant skip sites found (static, complete):**
  `httpx` (importorskip, test_linear_refresh_processor),
  `jsonschema` (test_containment_attestation_parity), `git` +
  full history (baseline-commit and merge-base probes),
  `node` (ECMA-262 engine check, test_delivery_contract_bundle),
  `sh`/`cat`/`grep` (promotion-drain and shell probes),
  `make` (the dedup guard's `make -n` expansions).
- **Probe set (discovered):** modules `yaml, jsonschema, tomlkit,
  httpx`; executables `git, sh, make, node, cat, grep` (cat/grep added
  by the T6 repair: the ledger's own static scan had recorded the
  promotion-drain skip sites, and the probe must cover every recorded
  executable — review finding R2-001). Pinned verbatim by
  `PINNED_PROBE_BODY` in the posture test.
- **Deliberately not probed, stated honestly:**
  - Platform skips (symlinks, junctions, Windows-only cases) —
    environmental on every runner, not provisioning.
  - `dist/apm/` — probed after the round-1 review repair (T5): the
    discovery environment held dist/ from local runs, so its skip-audit
    could not see the projected-variant cases' dependency on it, and the
    original entry here wrongly claimed gate-main skipped those cases too —
    inside gate-main `make build-check` had materialized `dist/` before the
    carve-out step ran. The sibling now materializes the catalogue
    projection in its own step and the probe fails closed when `dist/apm/`
    is absent (finding R1-001, repaired in T5).

## T1 red proof (red-green, never committed red)

Against the unmodified workflow, after extending the tools and before
the workflow edit:

- `python3 tools/test-build-check-workflow.py` — self-test green
  (baseline clean, every mutation caught), then **9 posture
  violations**: `job-id-set[gate-catalogue-tests]`,
  `job-name-written[gate-catalogue-tests]`, `work-jobs-floor`,
  `sibling-matrix-shards`, `sibling-fail-fast`,
  `sibling-dispatch-body-exact`, `sibling-probe-body-exact`,
  `sibling-probe-before-dispatch`, `moved-steps-left-gate-main`.
- `python3 tools/lint-ci-parity.py` — **49 parity violations**: the 42
  repointed `PR_GATED` where strings name a step the workflow does not
  carry, plus dead roster entries for the sibling's steps.

After the single workflow edit (the delivered T1 commit `3c690bcc6`, whose
workflow is byte-identical to the originally extracted `a0ac3a36d` state):
posture test exits 0 (208 mutations, 93 assertion families, all caught);
lint exits 0 (182 steps dispositioned, 258 targets corroborated); lint
self-test 220 cases pass.

## T6: round-2 review repairs (red-green, never committed red)

Round-2 findings (see
`.context/reviews/run-3a659195cba798ec/`):

- **R2-001 (probe executable set incomplete).** The probe's executable
  loop gains `cat grep` (the promotion-drain skip sites the ledger's
  own static scan had recorded); all are coreutils on every runner
  image, so the fail-closed check has no false-positive risk.
- **R2-002 (ledger T1 citation unreachable).** The T1 section above now
  cites the delivered T1 commit `3c690bcc6` (byte-identical workflow).
- **SEC-R3-001 (SHARD env value unpinned).** New posture check
  `sibling-dispatch-env-value-exact` pins the dispatch step's env
  mapping to exactly `SHARD: ${{ matrix.shard }}`; a constant or
  conditional value that silently routes every replica to one branch
  reddens (verified red before the pin landed: both mutations left the
  prior posture test green).
- **SEC-R3-002 (probe conditionality unpinned).** New posture check
  `sibling-no-step-if` rejects any step-level `if:` on any sibling step
  (verified red before: `if: ${{ false }}` on the probe left every gate
  green).
- **QE-R2-001 (release-guide doc drift).**
  `docs/guides/how-to/cut-a-package-release.md` now attributes the
  roster collection to the sibling's shard-1.

Red proof before the workflow edit: `sibling-probe-body-exact` red
against the unmodified workflow; the new guard checks prove via their
mutations (a constant SHARD, a conditional SHARD, a probe `if:`, a
cat/grep drop each redden). Green after: 215 mutations, 97 assertion
families, all caught; `make build-check` green end-to-end at this tree
(all 93 chain steps, SAST delegated; ~75 min local wall-clock).

## T7: round-3 review repairs (red-green via the mutation matrix)

Round-3 findings (see `.context/reviews/run-3a659195cba798ec/`):

- **R3-001 (working-directory dimension unpinned).** The three pinned
  sibling steps (install, materialize, probe, dispatch) join `_NO_CWD_STEPS`,
  so a `working-directory:` key added to any of them reddens
  `no-working-directory[gate-catalogue-tests/<step>]`. Four mutations prove
  it, one per step.
- **SEC-R4-001 (matrix exclude unpinned).** New check
  `sibling-matrix-no-exclude` read the matrix block's keys with a regex
  restricted to the bare spelling at exactly 8 spaces. Mutation: an
  adjacent bare `exclude:` dropping shard-2 reddened the check (the
  declared shard list still satisfies both cross-pins, which is why a
  dedicated check was needed).
  **Correction (round 4, finding QE-R4-002):** the check's original
  record here overclaimed — "any `exclude:`/`include:` entry reddens"
  held only for the bare adjacent spelling. The same run's round-4
  reviews falsified it three ways (quoted `'exclude':`, duplicate
  `matrix:` blocks, blank-line separation), all controller-verified
  against the shipped workflow; see the T8 section for the class-closing
  repair that replaced the check.
- **SEC-R4-002 (install body unpinned).** New `PINNED_INSTALL_BODY` and check
  `sibling-install-body-exact` pin the sibling's dependency-install body by
  equality, closing the addition and re-point directions the probe cannot
  see (it verifies availability, not provenance). Two mutations: a prepended
  `curl … | sh` line and a re-pointed requirements source.

Red proof: unlike T5/T6 (which reddened against the workflow), the T7
assertions pass against an already-correct workflow — the defect was the
MISSING check, so the red is the mutation matrix: all seven new mutations
(each a one-line workflow edit of exactly the shape each finding named)
reddened their families, and the self-test reported 222 mutations,
99 assertion families, all caught, with every pre-existing family still
green. **Scope of that proof (round 4, finding QE-R4-002):** a caught
mutation proves only the mutated spelling — the matrix check's mutation
proved the adjacent bare `exclude:` and nothing else; it did not prove
the quoted, duplicate-block, or blank-line spellings, which the same
run's round-4 reviews then exercised. `make lint-ruff lint-mypy` clean;
lint-ci-parity ok (183 steps, 258
targets); lint self-test 220 cases pass. The full chain re-run at this
tree is recorded in the T4 section's log (controller-recorded; lands as
controller history the owner adopts).

## T8: round-4 review repairs (the matrix pin closed as a class)

Round-4 findings (see `.context/reviews/run-3a659195cba798ec/`):

- **SEC-R5-001, SEC-R5-002, SEC-R6-001 (the matrix check bypassable three
  ways).** The T7 regex matrix model is REPLACED, not patched:
  `PINNED_STRATEGY_BODY` pins the sibling's entire `strategy:` section by
  equality (comment-stripped, blank-line-free), and exactly-one key counts
  (`sibling-strategy-single`, `sibling-matrix-single`) close the
  duplicate-key class directly. Controller verification against the
  shipped workflow: all seven recorded shapes redden — bare `exclude:`,
  quoted `'exclude':`, quoted flow `"exclude": [{…}]`, blank-line-separated
  `exclude:`, duplicate `matrix:` with `exclude:`, duplicate `matrix:` with
  `shard: [shard-1]` (each reddening the strategy pin, the duplicates also
  the count check). A seventh shape — a duplicate `strategy:` binding — is
  carried by the mutation matrix and caught by the count checks alone
  (`sibling-strategy-single`, with `sibling-matrix-single` and
  `sibling-fail-fast` reddening too); the strategy pin itself stays green
  for it, because its extractor reads only the first `strategy:` block —
  the count checks are load-bearing, not redundant with the pin
  (attribution corrected per round-5 finding QE-R5-001).
- **SEC-R6-002 (job-level defaults channel).** New check
  `no-job-defaults-block` rejects a `defaults:` key at job indent in every
  job, closing the `run: working-directory:` channel the step-level
  `_NO_CWD_STEPS` pins cannot see. Controller verification: a job-level
  `defaults: run: working-directory: tools` on the sibling reddens it.
- **QE-R4-001 (the modeling approach was the defect).** The repair follows
  the file's own pin-the-whole-set doctrine — one equality pin plus counts
  instead of another regex arm; the removed check is not kept alongside a
  replacement (a check that can be bypassed records a held dimension that
  is not held).
- **QE-R4-002 (ledger overclaim).** The T7 section above now records what
  was actually proven and cites this section for the falsified spellings
  (corrected in this same commit).

Red proof: the mutation matrix carries all five new bypass mutations
(quoted exclude, blank-line exclude, duplicate matrix, duplicate strategy,
job-level defaults) plus the original bare exclude, now targeting the
strategy pin — 227 mutations, 102 assertion families, all caught, every
pre-existing family still green. Posture OK against the shipped workflow;
lint-ci-parity ok; lint self-test 220 cases; ruff and mypy clean.
(controller-recorded; lands as controller history the owner adopts.)

## T9: round-5 review repairs (anchor/alias/merge syntax rejected)

Round-5 findings (see `.context/reviews/run-3a659195cba798ec/`):

- **R5-001 (merge-key delivery).** New check `no-anchor-alias-merge`
  rejects YAML `&anchor` definitions, `*alias` references, and `<<:` merge
  keys anywhere in the workflow — the declared-canonical-subset doctrine
  (fail closed on every unmodelled form) rather than modeling merge
  semantics. Controller verification against the shipped workflow: the
  reviewer's exact shapes — an anchor block plus a `<<: *anchor` merge line
  under the sibling job and under the aggregator job, each carrying a live
  job-level `defaults: run: shell: 'true {0}'` (PyYAML resolves it) — now
  redden. Four mutations: the two merge-key shapes, an `*alias` value
  reference, and an `&anchor` definition on the job id.
- **QE-R5-001 (ledger count and attribution).** The T8 section's shape
  count now matches its enumeration (six listed), the seventh shape
  (duplicate `strategy:`) is enumerated with its correct attribution (the
  count checks, not the strategy pin), and the pinned-constant comment no
  longer overclaims ("every structural edit inside the block").

Red proof: the mutation matrix carries all four new mutations — 231
mutations, 103 assertion families, all caught, every pre-existing family
still green. Posture OK against the shipped workflow; lint-ci-parity ok;
lint self-test 220 cases; ruff and mypy clean. (controller-recorded; lands
as controller history the owner adopts.)

## T10: round-6 review repairs (the anchor/alias/merge check closed and scoped)

Round-6 findings (see `.context/reviews/run-3a659195cba798ec/`):

- **R6-001 (non-canonical spellings escape).** The three arms are now
  separator-agnostic (any whitespace after the `:`/`-` separator),
  charset-agnostic (any name characters, digit-initial included), and
  position-agnostic (merge keys at line start, in sequence position, in
  flow position). Controller verification against the shipped workflow:
  the sequence-position merge with double-space separation and the
  digit-initial anchor name — both previously green with a live merged
  `shell:` payload — now redden.
- **QE-R6-001 (no exclusive mutation for the merge arm).** A new
  flow-mapping merge mutation (`<<: {shell: 'true {0}'}` — a merge key
  with no anchor or alias token anywhere) proves the merge arm alone:
  controller verification confirms the other two arms do not match it,
  and the anchor-only and alias-only mutations do not match the merge
  arm. Deleting any one arm now reddens its exclusive mutation.
- **QE-R6-002 (run-body false positives).** The arms run against a
  run-body-free view of the workflow (`_strip_run_bodies`: block scalars
  are literal shell text, not YAML nodes — the `no-duplicate-step-keys`
  scoping precedent). Controller verification: an `echo "- *note: …"`
  line inside the dispatch body no longer reddens the check.

Red proof: the mutation matrix carries all three new mutations (two
non-canonical spellings plus the exclusive flow-mapping merge) — 234
mutations, 103 assertion families, all caught, every pre-existing family
still green. Posture OK against the shipped workflow; lint-ci-parity ok;
lint self-test 220 cases; ruff and mypy clean. (controller-recorded;
lands as controller history the owner adopts.)

## T13: round-9 review repairs (env mappings pinned whole; run bodies pinned whole)

Round-9 findings (see `.context/reviews/run-3a659195cba798ec/`):

- **R9-001 + QE-R9-003 (env VALUES pinned; set-equality over the
  enumerable pairs).** `PINNED_ENV_KEYS` (keys only) is replaced by
  `PINNED_ENV_MAPPINGS` in `tools/lint-ci-parity.py`: the pin is the
  complete (owner → key → value) set for every step- and job-level env
  binding in the workflow, checked by whole-set equality via the new
  `env_mapping_violations` parse-layer check. Rebinding a pinned key's
  value (BASE_SHA from `base.sha` to `head.sha`), adding a new key
  (MAKEFLAGS), and adding a new binding step each redden with a label
  naming the step and the differing key. The set is enumerable and the
  comparison is whole-set, so the closure is structural: the shipped
  workflow's (owner, mapping) pairs must equal the pin exactly — no
  spelling, placement, or flow-style variation escapes it.
- **QE-R9-002 (docstring rationale corrected).** The mapping pin's
  docstring now states the real boundary: workflow-text env VALUES are
  fixed template expressions and are pinned here; only rendered runtime
  values differ per run. (The old key-only rationale — "values differ
  per run and carry no pin" — was false for the workflow text.)
- **SEC-R10-001 (SAST detect step's run body pinned whole).** The
  detect step that produces `skip_sast` — the sole producer, consumed by
  the pinned `Run make sast` condition — is now pinned byte-exact by
  `PINNED_SAST_DETECT_BODY` (comment-stripped form; every executable
  byte pinned). A prepended `skip_sast=true`/`exit 0` pair and a deleted
  config-surface loop each redden `sast-detect-body-exact`.
- **SEC-R10-002 (work-loop guard run body pinned whole).** The three
  substring checks on the guard's body (`guard-archives-base-scripts`,
  `guard-isolated-interpreter`, `guard-fallback-reads-base-tree`) fold
  into one `guard-body-exact` equality pin over the whole body — a
  prepended `exit 0` keeps every substring present but reddens
  immediately. Their three mutations are retargeted to the new family.
- **QE-R9-001 (stripper fifth body form).** A `run:` key line WITH a
  value can still continue onto deeper-indented following lines (YAML
  folds them into one scalar); `_strip_run_bodies` now strips from the
  key's indent onward, and the committed regression control carries the
  `plain-continuation` form (`run: grep --` + a deeper `*.md` line),
  which reddens the `no-anchor-alias-merge` view against the old
  behavior.

Red proof: committed assertions — the lint self-test's env-mapping cases
  (clean on the shipped workflow, value-rebind on the real detect step,
  new-key on the real detect step, new binding step, quoted-key flow,
  next-line flow, job level) plus the forged-real-workflow end-to-end
  case (BASE_SHA rebound to `head.sha` in `.github/workflows/build-
  check.yml` content → exit 1 naming BASE_SHA); the end-to-end fixtures
  are rebuilt from the real workflow plus only the mutation under test
  (the whole-mapping pin reddens synthetic minimal workflows before the
  arm under test runs). Posture self-test: baseline clean, 246 mutations
  each caught (three new: guard-exit-0-prefix, sast-detect-skip-prefix,
  sast-detect-config-loop-dropped), 110 assertion families, 12 guard
  bodies agreed with bash; the baseline fixture grafts the live detect
  body (the guard graft already existed). Lint self-test 243 cases
  green; lint-ci-parity ok on the shipped workflow; ruff and mypy clean.
  (controller-recorded; lands as controller history the owner adopts.)

## T12: round-8 review repairs (env allowlist closed at the parse layer; indirection wiring pinned)

Round-8 findings (see `.context/reviews/run-3a659195cba798ec/`):

- **R8-001 + SEC-R9-002 (the env class closure).** The env allowlist now
  has a parse-layer owner: `env_key_violations` in `tools/lint-ci-parity.py`
  reads every in-scope workflow's parsed job- and step-level `env` keys and
  reddens on any key outside `PINNED_ENV_KEYS` — an equality pin over the
  enumerable key set, spelling- and placement-independent (a quoted key, a
  spaced key, a same-line flow mapping, and a next-line flow mapping all
  yield the same parsed keys). Controller verification: a quoted-key flow
  env and a next-line flow mapping on the sibling install step each redden
  the lint end to end (exit 1 with the env diagnosis), and the shipped
  workflow's key set matches the pin exactly. The stdlib
  `no-flow-style-env` check stays as defense-in-depth for the bare
  same-line spelling only — the boundary is now recorded at the posture
  test's `no-anchor-alias-merge` comment (QE-R8-005's repair).
- **R8-002 (stripper: plain multi-line run scalars).** `_strip_run_bodies`
  treats a valueless `run:` key with a deeper-indented multi-line plain
  scalar as body text, and the committed regression control carries the
  `plain-multiline` form — an alias-matching body in that form no longer
  false-positives `no-anchor-alias-merge`, and narrowing the stripper
  reddens the self-test.
- **QE-R8-001 (wiring pinned end to end).** The lint self-test runs
  `lint-ci-parity` as a subprocess against fixture workflows bearing an
  indirection payload and an env violation, asserting exit 1 and each
  arm's specific diagnosis — deleting either arm's invocation from
  `main()` reddens the committed suite.
- **QE-R8-002 (merge arm pinned exclusively).** Two committed cases carry
  no anchor or alias token (`indirection-flow-merge-only`,
  `indirection-quoted-merge-key-only`), so deleting the merge-key arm of
  `yaml_indirection_violations` reddens exactly those cases.
- **QE-R8-004 (ledger corrections).** The T11 section below is corrected
  in place: `no-flow-style-env` holds only the bare same-line spelling
  (the parse-layer pin owns the class); `_strip_run_bodies`'s T11 state
  did not cover the plain multi-line form (T12 adds it); five of the seven
  T11 `indirection-*` cases carried anchor or alias tokens, so they did
  not pin the merge arm exclusively (T12's exclusive cases and wiring
  cases do).

Red proof: twelve new committed assertions — five direct `env-keys-*`
  cases (clean, out-of-allowlist step and job, quoted-key flow,
  next-line flow), two merge-arm-exclusive `indirection-*` cases, and five
  end-to-end wiring assertions (`indirection-arm-is-wired-into-main-*`,
  `env-arm-is-wired-into-main-*`). Lint self-test 239 cases green; posture
  self-test green (243 mutations, 111 families, now including the
  `plain-multiline` stripper regression form); lint-ci-parity ok on the
  shipped workflow; ruff and mypy clean. (controller-recorded; lands as
  controller history the owner adopts.)

## T11: round-7 review repairs (env allowlist fail-closed; parse-layer class closure)

Round-7 findings (see `.context/reviews/run-3a659195cba798ec/`):

- **SEC-R9-001 (flow-style env passes the allowlist vacuously).** New check
  `no-flow-style-env` reddens on any `env:` line carrying a non-empty inline
  value — *corrected per round-8 QE-R8-004: this holds the bare same-line
  spelling only; quoted keys and next-line flow mappings were falsified by
  R8-001 and SEC-R9-002, and the class is now owned by the parse-layer
  `PINNED_ENV_KEYS` check added in T12.* Controller
  verification at the time: a flow-style `env: {PIP_INDEX_URL: …}` on the
  install step and a flow-style `env: {MAKEFLAGS: '-n'}` on gate-main's
  anchor each redden (previously both green).
- **R7-001 + QE-R7-002 (the class closure).** The anchor/alias/merge class
  now has a parse-layer owner: `yaml_indirection_violations` in
  `tools/lint-ci-parity.py` walks PyYAML's event stream and rejects every
  anchor binding, alias resolution, and `<<` scalar token — position-,
  spelling-, and flow-style-independent. Controller verification: all five
  recorded bypass shapes (job-level merge, flow-position alias, tag-prefixed
  anchor, sequence-position merge, flow-mapping merge) are caught at token
  level; the clean workflow yields zero. The stdlib regex arms in the
  posture test stay as defense-in-depth; the boundary is recorded in the
  owning check's docstring — the regex reader models canonical spellings,
  the parse-layer check owns the class.
- **R7-002 (stripper coverage).** `_strip_run_bodies` now treats every
  `run:` scalar as body text: block scalars (either indicator, blank lines
  included) and plain/quoted inline values (key kept, value blanked).
  *Corrected per round-8 QE-R8-004: the T11 state did not cover the plain
  multi-line form (a valueless `run:` key with a deeper-indented body),
  falsified by R8-002 as a false positive; T12 adds the form and its
  committed regression.*
- **QE-R7-001 (no committed regression control for the stripper).** The
  self-test carries a direct regression assertion: for each body form
  (block-pipe-post-blank, folded, plain-inline), alias-matching shell text
  inside the body must not reach the anchor/alias/merge view — removing or
  narrowing the stripper reddens the self-test.

Red proof: two new mutations (flow-style env on install and anchor) prove
`no-flow-style-env`; seven new lint self-test cases
(`indirection-*`) pin the parse-layer check's detection — *corrected per
round-8 QE-R8-004: five of the seven carried anchor or alias tokens, so
they did not pin the merge arm exclusively and two recorded shapes had no
case; T12 adds the exclusive cases and the end-to-end wiring assertions*;
the stripper regression assertions run on every invocation. 236
mutations, 104 assertion families, all caught; lint self-test 227 cases;
lint-ci-parity ok (now carrying the parse-layer check); ruff and mypy
clean. (controller-recorded; lands as controller history the owner
adopts.)

## T4: runtime verification

- [x] `python -m pytest tools/test_local_ci_shared_test_deduplication.py -q`
      local run (moved dedup guard against the unchanged Makefile):
      **51 passed, 99.36 s**.
- [x] `make lint-ruff lint-mypy` (local gate pair): **green** (ruff clean;
      mypy: no issues in 158 source files).
- [x] `make build-check` end-to-end (chains the posture test and
      lint-ci-parity; the PR's own gate is the integration proof):
      **green** — all 93 chain steps, SAST/SCA delegated as gate-main runs
      it; ~85 min wall-clock locally (macOS subprocess overhead; CI runs
      the same chain in minutes). Re-run green after the T5 repair at the
      same tree (~50 min).
- [ ] Post-merge: gate-main docs-only median vs the ≤ 600 s target
      (the intent's success metric; the rebalance path is a deliberate
      pinned edit if three shards under-deliver).

## T5: round-1 review repairs (red-green, never committed red)

Round-1 adversarial findings R1-001…R1-005 (see
`.context/reviews/run-3a659195cba798ec/1-adversarial-reviewer-raw.md`):

- **R1-001 (six projected-variant cases would silently skip in the
  sibling).** Repaired: the sibling gains a `Materialize catalogue
  projections (gate-catalogue-tests)` step (the same catalogue-build
  invocation gate-main's `make build-check` chain runs) and the probe
  gains a fail-closed `dist/apm/` check. Red proof before the workflow
  edit: `sibling-probe-body-exact`, `sibling-materialize-body-exact`,
  `sibling-materialize-before-probe` each red against the unmodified
  workflow. Green after: 212 mutations, 95 assertion families, all
  caught; four new mutations (step removed, body emptied, step moved
  after the probe, probe dist-check dropped) each redden.
- **R1-002 / SEC-001 (stray root `uv.lock`).** Deleted; nothing consumes
  it (no uv invocation in Makefile or workflows; the root pyproject is
  tooling-only).
- **R1-003 (24 stale gate-main placement comments).** All reworded for
  the two-job layout: the broad `pytest tests/ -q` run they referenced
  now lives in the sibling's shard-1 (a parallel job), so the named
  gate-main steps are what attribute failures precisely.
- **R1-004 (T4 section unchecked).** Completed above.
- **R1-005 (ledger cited unreachable revisions).** Input-revision record
  corrected above.

## Rounds 11-15 (T15-T18) and closeout

- **Round 11 (T15).** Open sibling step set closed by a named check; about 25
  `gate-main` placement comments reworded; `tests/AGENTS.md` roster section
  rewritten for the two-job layout.
- **Round 12 (T16).** Two roster guards the move broke
  (`test_workspace_status_progressive_disclosure` content pin,
  `test_capture_rename_guide` ordering guard) restated for the two-job layout;
  the step enumerator made total so a bare-dash first step fails closed; the
  last stale comments and eight roster docstrings reworded.
- **Round 13 (T17).** Retirement-inventory rows added for the two tools paths
  the move adds to the scan; non-YAML line breaks rejected in both tools.
- **Round 14 (T18).** The rejection widened to all eight characters
  `str.splitlines` breaks on that YAML 1.2 does not; one end-to-end
  `main()` case added to the parity lint's self-test.
- **Round 15.** All three roles clean or closed. One security finding was
  resolved as out of scope: a Unicode space before a comparison in the
  aggregator's existing guard body. The guard body predates this change and
  is not edited by it; actionlint's shellcheck pass in `ci-security.yml`
  (SC1018) reports the edit and runs on every pull request.
- **Regenerate.** The supervisor's `regenerate` step rebuilt the installed
  work-loop copies from the pack source after a merge of `main` earlier in
  the run had advanced it; gates and reviews were re-run on the result.
- **Full `tests/` run (shard 1's invocation).** The T16 run showed failures
  outside this change: stale `.vlx-worktrees` schema copies, the
  work-loop projection byte-identity (cleared by `regenerate`), the
  credbroker wheel build (no `pip` in the local venv), and checks on files
  this change does not touch. The workspace-retirement inventory entries for
  this spec's own files clear when the spec is `Shipped`.
