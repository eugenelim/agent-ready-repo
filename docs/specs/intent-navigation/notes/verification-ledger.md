# Verification ledger: intent navigation — navigator core

Execution observations for slice 1. The spec and plan hold the obligations;
this file holds what execution measured and where it departed from a task
row's literal method.

## Pre-execution

- 2026-10-08, engine run `08208db7-158f-4302-910e-347d55a570c8`: a fresh
  pre-EXECUTE adversarial review ran three rounds over the approved pair.
  Rounds 1 and 2 sustained five findings, all plan wiring; the owner approved
  the revision and re-approved the spec and plan the same day. Round 3 was
  clean.
- The slice branch `eugenelim/intent-navigation-slice-1` was cut from
  `feature/intent-navigation` at `8392ef8d6`, which contains the 2.30.1
  terminality repair merge `aafa2aa1b`; `git merge-base --is-ancestor
  aafa2aa1b HEAD` passed before T1.

## T1

- `python3 -m pytest packs/core/tests/skills/navigate-intents/ -q`: 54
  failed, 24 passed. Every failure is the absent module — 39 on
  `navigate_intents.py`, 15 on `intent_graph.py`. The 24 passes are
  fixture-shape checks over the committed corpora and the test-time builder.
- Interim red, by design: `tools/lint-pack-test-boundary.py` (and its
  self-test, which runs it over the real tree) reports
  `packs/core/tests/skills/navigate-intents` as a suite no runner names. T5
  adds the `Makefile` runner that satisfies it. The slice is one pull request
  whose gates run on its head, and each task's `Done when` runs only its own
  tests, so commits T1 to T4 carry this one finding and the head does not. A
  temporary `_NO_RUNNER` entry was declined because `tools/` is outside T1's
  and T5's pinned `Touches`.

## T2

- Done-when: `test_derivation_contract.py` 45 passed; the copy pin test 3
  passed; `tests/roster/test_intent_delivery_relations_repository.py` 4
  passed; `agentbundle catalogue verify --root .` ok; `make lint-ruff
  lint-mypy` clean.
- Correction inside T2: the first pass returned `dangling` for a spec
  `Discovery:` path or markdown link naming a tombstone. AC-0007 requires
  `retired_target` with the tombstone's `Reissued as:` value. The derivation
  now consults tombstones by path, and three tests prove it over the new
  `fixtures/negative/spec_discovery_retired_target/` corpus.
- `intent_graph.py` first carried internal criterion citations in its
  comments; they were reworded so the canonical shipped-text grep from
  `packs/AGENTS.local.md` returns nothing over the skill and its projections.
- `agentbundle catalogue self-host --root . --write` refuses a dirty tree, so
  it ran with `--force`, which lifts only that guard. It wrote only the two
  `navigate-intents` projections.

## T3

- Done-when: `test_query_contract.py`, `test_text_tree.py`, and
  `test_independence.py` with `test_derivation_contract.py` — 108 passed in
  5.65 s, none skipped, including all five confinement cases; `agentbundle
  catalogue verify --root .` ok; `make lint-ruff lint-mypy` clean; the
  shipped-text grep returns nothing.
- Real invocation over this repository (168 intents, 23 briefs, 543 specs):
  `query --operation summary` exit 0, wall 3.64 s, 3.86 s, 4.43 s, 4.80 s
  across four runs; `query --operation tree --format text --depth 1` exit 0,
  3.84 s, 140 lines, first line
  `capability:digital-experience-doctrine · capability · Accepted`.
- Latency headroom is thin against AC-0019's 5-second median for
  `outstanding`, measured in T4. The de-risk figure was 1.55 s for the
  derivation alone; the gap is the resolver load and query on this machine.
- The AC-0064 equality tests drive the graph module through the navigator's
  own loader function, because the query envelope does not expose the raw
  graph.

## T4

- Done-when, re-run by the controller with the worktree's Python 3.12:
  every navigate-intents suite plus `tools/test_check_closure_terminality_parity.py`
  — 157 passed in 8.07 s (`test_outstanding.py` alone: 43 passed);
  `python3 tools/check_closure_terminality_parity.py` clean, including
  "navigator terminality copy agrees"; `make lint-ruff lint-mypy` exit 0;
  `agentbundle catalogue verify --root .` ok; the shipped-text grep returns
  nothing over the skill and both projections.
- Correction inside T4: spec placements leaked an internal `_in_no_parent`
  key into each placement in the JSON result. `_clean_item` now strips it, and
  an AC-0059 test covers it. A new `fixtures/negative/ambiguous_ordinal/`
  corpus proves `ambiguous_identity` for `outstanding --from`.
- `tools/test_check_closure_terminality_parity.py` did not exist before this
  slice; T4 created it with six mutation tests.
- **AC-0019, first measurement (superseded by the round-2 measurement below): not met.** Seven `outstanding` runs over this repository
  (168 intents, 23 briefs, 543 specs; 199 outstanding items; JSON result
  104,144 bytes, under the 512 KiB limit), each `status: ok`, wall time
  process start to exit:
  - implementer, 2026-10-09: 28.70 (cold), 4.74, 6.38, 7.56, 4.44, 6.29,
    6.33 s — median 6.33 s;
  - controller, 2026-10-09 09:08 CDT: 5.79, 5.30, 5.60, 5.88, 5.72, 5.77,
    7.50 s — median 5.77 s, min 5.30 s, max 7.50 s.
  Load averages at the controller's runs were 18.5, 58.2, and 81.9 on 10
  cores. CPU time per run is about 1.8 s (user 1.0 s, system 0.75 s); the
  rest of the wall time is waiting. A profile attributes 4.3 s of a 10.3 s
  profiled run to 7,480 `open` calls: the confinement helper opens each path
  component, and the derivation and the delivery resolver each read all 748
  artifacts. Halving those reads would change `intent_graph.py`, outside
  T4's `Touches`, and the resolver copy must stay byte-identical.
  AC-0019 is measured at the commit this slice merges, so the seven runs are
  repeated at lower load before the slice pull request; a miss at low load
  goes to the owner.

## T5

- Done-when, implementer and controller: `agentbundle catalogue lint --root .
  --deep` exit 0 with no `navigate-intents` finding;
  `tests/roster/test_skill_census.py` 1 passed; `tools/test_build_gate_chain.py`
  39 passed, 1 skipped; `tools/test_local_ci_shared_test_deduplication.py` 51
  passed; `tools/test-lint-ci-parity.py` 218 cases and `tools/lint-ci-parity.py`
  ok; `tools/lint-pack-test-boundary.py` and its self-test pass, clearing the
  interim red recorded at T1; the navigate-intents suites 151 passed; catalogue
  verify ok; `make lint-ruff lint-mypy` clean; shipped-text grep empty.
- Digest re-pin: standalone `b666effc…` → `c263c9e5…`, composed `45dfc464…` →
  `31633568…`. Removing the added `Makefile` line reproduces both old digests,
  so the line is the sole cause.
- The skill description was trimmed from 1,059 to 878 characters to meet the
  catalogue's 1,024-character limit, keeping every routing signal.
- **Activation run (AC-0033, AC-0034): no valid result yet.** `pack-evals` run
  37949928904 on `bb75c212a`, `packs=core`, concluded `success` (the workflow
  is report-only), but every one of its runs errored for all 15 core skills:
  `navigate-intents` reported 15/35 with 105 harness errors, every trigger rate
  0.00, so its passes are only the near-misses an errored run cannot trigger.
  The job's `ANTHROPIC_API_KEY` is empty. The last scheduled run on `main`,
  37322810666 on 2026-10-05, shows the same empty key and the same errors, so
  this predates the slice. A local run cannot be scoped to one skill:
  `agentbundle pack evals run` evaluates the whole pack.
- **Activation run (AC-0033, AC-0034), owner-directed in-harness run,
  2026-10-09: `navigate-intents` 35/35 on both detectors.** Because the CI
  key is empty, the owner directed the activation check through Claude and
  Codex sub-contexts, using the in-harness procedure in
  `guides/_shared/how-to/author-a-skill.md`. Each of the 35 queries ran 3
  times per detector, each run a fresh tool-less process (`claude -p
  --safe-mode --disable-slash-commands --tools ""`, or `codex exec -s
  read-only --ephemeral`) started in an empty directory. Each run saw the
  descriptions of every `core` skill plus `navigate-decisions`, which was
  added because the "how many roadmap intents" near-miss routes there, and
  the query as delimited data. Graded with `agentbundle pack evals run
  --pack core --mode in-harness --reports <file>`: `navigate-intents: 35/35
  queries passed` for each detector, no errored runs.
  - Positives: all 20 at trigger rate 1.00 on both detectors.
  - Near-misses, all at 0.00. Queue order and repair routed to
    `workspace-status`; ADR and RFC lookup and "how many roadmap intents" to
    `navigate-decisions`; closure to `close-work`. ADR and RFC authoring went
    to `new-adr` and `new-rfc` (Claude) or no skill (Codex). Intent authoring,
    de-risking, and decomposition went to `work-intake` (Claude) or
    `intake-intent` or no skill (Codex).
  - Limits: the harness labels this mode `fidelity: reported`. It measures a
    description-match judgement, not the real activation router, so it is
    not the headless calibration CI would give once the key is set. The
    first Claude pass ran 4 calls in parallel on the loaded machine and most
    errored; it was re-run one call at a time with up to two retries, and
    the runner was widened to accept any well-formed skill name after Claude
    named `new-adr` and `new-rfc`, which were outside the listed set.
  - The guide's grading command names `tools/run-pack-evals.py`, which does
    not exist in this tree; `agentbundle pack evals run --mode in-harness`
    is the shipped grader.

## Review round 1 fixes

- The post-gates adversarial review sustained 21 findings (13 Blockers, 7
  Concerns, 1 Nit) under `.context/reviews/08208db7-158f-4302-910e-347d55a570c8/`.
  The first adjudication carried a stray indeterminate marker with an empty
  indeterminate audit; it is kept beside the replacement verdict, which the
  same adjudicator re-emitted clean.
- Every sustained finding was fixed inside the files T2 to T6 already own.
  Delivery relations now attach through the resolver's real
  `intent:<slug>` field; ancestor chains run past terminal ancestors to the
  root; outstanding JSON carries `placed` and `no_parent` in node-id order,
  and text prints every outstanding item; slug duplicates, typed
  non-intent parents, spec-pointer `multiple_values`, backtick-and-suffix
  node ids, heading search, `provenance.root`, `unrecorded` levels, selector
  type errors, and tab escaping are corrected; the parity tool now checks
  intent and brief sets against their upstreams in both directions, and its
  tests drive the tool's own checks.
- Controller corrections during the fix round: the first unsafe-entry fix
  silently skipped a symlinked spec directory or `spec.md`; it was replaced
  by a direct-children listing that refuses both with `unsafe_input` and
  ignores deeper entries, with tests shown red against the replaced
  walker. The new `coordinated_delivery/` corpus, on which the real
  resolver emits two coordinated-delivery relations, lacked its manifest;
  it was written by hand. The AC-0058 manifest test now discovers every
  corpus with a manifest instead of a hand-kept list, comparing 23 corpora
  and excluding four declared whole-operation failures.
- GATES after the fix round: 308 passed, 1 skipped across the touched
  suites (176 in navigate-intents); the ten tool checks, brief coverage,
  spec status, and catalogue verify pass; `make lint-ruff lint-mypy` clean;
  shipped-text grep empty; both projections match their source.

## Review round 2 fixes

- The second post-gates review sustained 13 findings (7 Blockers, 4 Concerns,
  2 Nits) and refuted one; its first adjudication broke the one-line finding
  shape and is kept beside the replacement. Several round-1 fixes had not
  held: delivery relations still missed `outcome:` and `opportunity:` feature
  intents, diagnostics and placement relation types were absent, text output
  still dropped items under terminal or out-of-scope parents, outstanding
  JSON was not ordered, and four regression tests passed on the code they
  were meant to catch. The round-1 spec listing also refused the plain
  `docs/specs/README.md`, so every query failed on this repository.
- The controller made this round's fixes directly. Relations and
  diagnostics map to the navigator node through the resolver's slug; spec
  placements carry the resolver relation type; text output attaches every
  item under its resolved parent and prints terminal or out-of-scope
  ancestors as context, and `--from` text prints only placements inside the
  subtree; `placed` and `no_parent` are sorted by node id; `ancestors` keeps
  the refused edge that ends a chain; only `<artifact-type>:<slug>` is typed,
  and a value carrying a colon is never a path; `multiple_values` edges carry
  a basis (`form` is the values' shared form, `unrecognized` when they
  differ, with each value's form kept in `basis.values`); outstanding JSON
  shows `unrecorded` levels; plain files directly under `docs/specs/` are
  skipped.
- `test_review_regressions.py` holds one test per finding. Corrected after
  round 3: the 16 failures first counted at `58fda2c49` were confounded,
  because `mixed/docs/specs/README.md` makes every `mixed/` query fail on
  those scripts. Measured again with that file removed: at `58fda2c49`, the
  tests for the README, outcome-kind relations, diagnostics, placement
  relation types, terminal-parent text, `--from` text, JSON ordering,
  refused ancestor edges, URL and free-text values, Discovery
  `multiple_values`, and `unrecorded` levels fail. The terminal-ancestor
  chain, `docs/other/x.md`, `brief:bravo-delivery`, and refused-brief-edge
  tests pass at `58fda2c49` and fail at `3c84ccdc1`, the pre-round-1 code,
  so their defects predate round 1. Failures at `3c84ccdc1` are partly
  confounded by its older outstanding JSON shape, which has no `placed`
  key. The AC-0002 and
  AC-0035 tests now change one root in place and strip only `generated_at`,
  and AC-0035 compares every operation and both formats. The parity tool has
  a `main()`-level mutation test.
- GATES: 348 passed, 5 skipped across the touched suites (215 passed, 4
  skipped in navigate-intents, the skips being whole-operation integrity
  failures); the ten tool checks, brief coverage, spec status, catalogue
  verify, and `make lint-ruff lint-mypy` pass; shipped-text grep empty; both
  projections match their source.
- **AC-0019: met.** Seven `outstanding` runs over this repository at this
  code, 2026-10-09 16:13 CDT, each `status: ok`, wall time process start to
  exit: 3.09, 2.79, 2.85, 3.06, 2.83, 2.91, 2.89 s. Median 2.89 s, minimum
  2.79 s, maximum 3.09 s. Corpus: 168 intents, 23 briefs, 543 specs; 199
  outstanding items (93 placed, 106 no parent). JSON result 105,419 bytes,
  under the 512 KiB limit. Load averages during the runs were 95.8 to 124.8
  on 10 cores. AC-0019 is measured at the merged commit; a later code change
  re-opens this measurement.

## Review round 3 and the AC-0071 owner decision

- The third post-gates review sustained 2 Concerns and 2 Nits, refuted one
  (AC-0010 covers intent-subject diagnostics only), and left one finding to
  the owner: which `form` a `multiple_values` edge carries when its values
  have different forms. Three rounds was the owner's cap; the loop stopped
  there.
- **Owner decision, 2026-10-09 (eugenelim):** amend AC-0071 to codify the
  current behaviour. A `multiple_values` refusal carries its field and each
  value with its own form in `basis.values`; its `form` is the values'
  shared form when they all match one shape, and `unrecognized` when they
  differ. The owner also authorised a fourth review round past the cap to
  close the remaining Concerns and Nits.

## Round 3 fixes

- A spec placement takes a resolver relation type only when the relation's
  `basis.spec` names that placement's pointer field. A terminal ancestor
  printed as context in outstanding text ends with `· (terminal ancestor)`,
  and SKILL.md and the guide say so. Only a URL scheme keeps a slash-bearing
  value out of the path form, so a repository path containing a colon is a
  `path`. A test pins the owner-approved `multiple_values` form for values
  of different shapes.
- Against the scripts at `67d99fe6a`, the placement-type, terminal-marker,
  and colon-path tests fail and pass now; the differing-form test passes on
  both, as it pins the behaviour the AC-0071 amendment codifies.
- navigate-intents suites: 218 passed, 4 skipped.
- Engine: the first `contract-amendment` call omitted the completed-task
  evidence bindings and failed validation after preparing its transition
  marker. The marker now conflicts with every later transition, a replay
  repeats the failure, and no verb clears it, so the run is wedged at
  `CODE-IMPLEMENTATION` pending an owner decision on recovery.

## AC-0071 amendment

- The owner chose "Reset and restart" on 2026-10-09 to recover the wedged
  engine. The prior run's state is archived under
  `.context/engine-archive/`; the new run is
  `08597a69-171a-46fd-b0d0-08be49d7092b`.
- The amendment took three pre-EXECUTE review rounds. Round 1 sustained that
  the sentence did not say which values `basis.values` holds per field; round
  2 sustained that a repository-escaping `Discovery:` link and an intent's
  `none` `Parent intent:` value both joined a conflict, against AC-0003 and
  AC-0006; round 3 was clean. The code was corrected to match: a
  `Discovery:` conflict counts only intent-valued values, and an empty or
  `none` intent parent value never counts. Three tests fail on the code at
  `dd3fbc4a3` and pass now.
- The owner re-approved the amended spec and the plan on 2026-10-09.
- GATES on `d25963c63`: 354 passed, 5 skipped across the touched suites; the
  ten tool checks, brief coverage, spec status, catalogue verify and deep
  lint, and `make lint-ruff lint-mypy` pass. AC-0019 at this code, 2026-10-09
  22:02 CDT, load 22 to 31 on 10 cores: 3.71, 3.85, 3.41, 3.44, 3.07, 3.40,
  3.68 s, median 3.44 s, minimum 3.07 s, maximum 3.85 s, result 105,419
  bytes, every run `status: ok`.

## Remote CI on d25963c63 and the fourth review round

- Dispatched on `d25963c63`: `build-check` 38018880276, `test-corpus`
  38018882383, `test-roster` 38018884246 — all three failed, for three
  causes:
  - `test_pack_delivery_contract_is_complete_and_version_increased` requires
    a `core` bump against `origin/main` (2.30.1 to 2.31.0, a new primitive)
    and its changelog entry. The owner reversed the earlier no-bump decision
    on 2026-10-09: `core` is now 2.31.0 in `pack.toml` and `plugin.json`, with
    a `## [core][2.31.0]` entry and Highlights; slice 4 updates that entry
    rather than adding the bump.
  - `test_eval_allowlist_has_balanced_activation_sets` keeps its own list of
    eval files; `navigate-intents` is added to it in
    `packs/core/tests/pack/test_work_intake_surface.py`, a file outside T5's
    `Touches` that no task named.
  - `gate-sast` raised bandit B613 (trojansource) on literal bidirectional
    controls in `navigate_intents.py`; those characters, and three in
    `test_text_tree.py`, are now `\u` escapes, with each file's parse tree
    unchanged. Full-repository bandit at the configured thresholds passes.
- The fourth adversarial round (first post-gates round of run `08597a69`)
  sustained one Concern and one Nit and refuted two: a spec `Brief:` path
  outside `docs/product/briefs/` is now `unparseable`, not `dangling`, with
  two tests red on `d25963c63`; the module docstring now states the
  `multiple_values` edge shape.
