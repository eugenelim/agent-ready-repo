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
- **AC-0019: not yet met.** Seven `outstanding` runs over this repository
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
