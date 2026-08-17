# Spec: lint-performance-p0

- **Status:** Draft <!-- Draft | Approved | Implementing | Shipped | Archived -->
- **Owner:** eugenelim
- **Plan:** [`plan.md`](plan.md)
- **Constrained by:** ADR-0071 (`evals/` is skill-local runtime content), `docs/guides/_shared/reference/catalogue-authoring-standards.md` § 4 (cross-pack behaviour is not pack-owned)
- **Brief:** none
- **Discovery:** none
- **Contract:** none <!-- no external interface surface; the callable lint APIs are internal repo-tooling seams -->
- **Shape:** service

> **Spec contract:** this document defines what "done" means. The implementing
> PR must match this spec, or update it. Verification must be derivable from it.

**Audit:** [`notes/lint-inventory.md`](notes/lint-inventory.md) is the scope
contract for this spec. Every lint-like production entry point and every lint
self-test in the repository is classified there with a P0 disposition. A lint
may be changed **only** if its inventory row says `CHANGE`.

## Objective

The repository's lint system runs fast enough to sit inside the work-loop's
five-minute inner loop, and no lint contract is weaker for it. The user is an
agent or engineer running the lint gates repeatedly while iterating: they get
the same verdicts, the same diagnostics and the same exit codes as before, but
the catalogue's runtime-boundary lint completes in seconds rather than tens of
seconds, and its falsification suite completes rather than stalling.

Three properties deliver that. **Ignore decisions are batched:** no production
lint asks Git about one path at a time; a lint that needs Git-ignore semantics
sends its whole candidate set through one resolver call, which launches at most
one `git check-ignore` process per Git root and none at all for an empty
candidate set. **One inventory per invocation:** the catalogue-wide runtime
boundary lint builds its pack, projection, runner, destination and ignore data
once and all six of its checks read that one inventory, instead of six checks
independently rebuilding overlapping parts of it. **Falsification is
fixture-scoped:** each planted violation is proven against a small temporary
catalogue containing tens of files rather than by rerunning the complete
production lint over the real worktree, with a deliberately minimal real-tree
layer retained to prove the production CLI is actually wired.

Success is structural and measurable: `tools/lint-pack-test-boundary.py`
launches **one** batched `check-ignore` process instead of 337, builds **one**
inventory, parses each runner file **once**, and its falsification suite
launches the full production lint a small bounded number of times instead of
twelve — with every existing failure message, exit code, fail-closed refusal
and symlink protection intact, and the complete catalogue and repository
terminal gates unchanged.

## Boundaries

The three-tier guard that keeps an implementing agent inside the lines.
*Always do* applies without asking; *Ask first* requires human sign-off
before proceeding; *Never do* is a hard rule, even under time pressure.

### Always do

- Change a lint only when its row in [`notes/lint-inventory.md`](notes/lint-inventory.md)
  says `CHANGE`. Everything else keeps its recorded no-P0-change disposition.
- Preserve every existing exit code, stdout/stderr split, check code, and
  load-bearing diagnostic substring. The self-tests assert on substrings such
  as `multiple skill suites`, `linked`, `symlink`, `planted-skill`; those are
  contract, not prose.
- Preserve fail-closed behaviour exactly: symlink refusal, junction refusal,
  resolution-error refusal, lexical `..` traversal refusal, dynamic-path
  refusal, and the explicit non-vacuity failures (`no packs found`,
  `no skill test directories found`, a pack in the self-host include list whose
  skills are not projected).
- Pass candidate paths to Git over **stdin**, NUL-delimited, with an explicit
  bounded timeout, no shell, and no `shell=True`.
- Give every real-worktree plant a `try`/`finally` cleanup guarantee, and make
  it refuse to run when its target already exists.
- Keep the callable check API side-effect-free: no argument parsing, no
  `sys.exit`, no printing, no repository mutation.

### Ask first

- Adding any `--pack`, `--skill` or other scoping option to a check whose
  correctness genuinely needs peer catalogue state. A misleading scope switch on
  a global invariant is worse than no switch.
- Removing, weakening or merging any existing falsification case, including any
  reduction in the set of matcher shapes or path-provenance shapes asserted.
- Changing which paths a lint treats as authored versus generated, or otherwise
  altering whether tracked, generated or untracked-ignored files are considered.
- Changing the default terminal behaviour of `agentbundle catalogue lint`,
  `catalogue lint --deep`, `catalogue verify`,
  `tools/catalogue/pre_pr_catalogue.py`, `make pre-pr`, `make build-check`, or
  any CI lint job.

### Never do

- **Never add a new runtime dependency, module boundary or top-level
  directory.** No third-party pathspec or Git library, no daemon, no MCP
  requirement, no control plane, no `uv` requirement, no persistent scan
  service, no SQLite or on-disk lint cache, no `pytest-xdist` or automatic test
  parallelism.
- Never make a shipped pack or skill lint import a repo-only `tools/` helper, and
  never make portable `agentbundle` code import repo-only `tools/`. Portable
  code stays independently installable.
- Never launch one `git check-ignore` process per candidate path from any
  production lint.
- Never persist an inventory or a confinement-scan cache across lint processes,
  and never reuse either across invocations.
- Never make a terminal catalogue or CI gate diff-aware, changed-pack-only or
  changed-file-only.
- Never let a targeted or fixture-scoped invocation emit the complete six-check
  terminal wording, or otherwise present a partial result as a full catalogue
  pass.
- Never raise the work-loop time budget, widen a timeout, or move unbounded work
  into CI as the fix.
- Never edit a gate, test or assertion to make a failure go away.

## Testing Strategy

Each behaviour from the Objective is paired with a mode and a reason.

**Batched ignore resolution — TDD.** The resolver is a pure-ish function over
(repo root, candidate iterable, missing-Git policy) with a compressible
invariant: a set of ignored paths, and a bounded process count. It is the one
piece of genuinely new logic, its edge cases (empty input, duplicates,
NUL-delimited special filenames, exit 0 vs 1, Git error, Git absent, timeout,
ordering determinism) are enumerable up front, and every one is cheap to assert
in-process. Tests come before the implementation.

**Git process-count and inventory-count properties — TDD, at the integration
surface.** "One full lint invocation launches at most one `check-ignore` process
per Git root" and "one inventory construction, runner files parsed once" are
invariants about a whole invocation, so they are asserted by instrumenting the
lint's real process and inventory boundary and running a complete invocation —
not by matching source strings. Source matching cannot see a call added through
an alias, and a passing source grep on a broken lint is exactly the false
confidence this spec exists to remove.

**Source-level enforcement of the batching rule — goal-based check.** "No
production lint constructs a direct `git check-ignore` subprocess outside the
approved helper" is a property of the source tree, verified by walking
production lint sources with an AST-aware assertion. A one-liner over the tree
answers it; there is no runtime behaviour to drive. It complements — and does
not replace — the structural process-count tests above.

**Boundary-lint behavioural equivalence — TDD.** Every existing success and
failure contract (test filename shapes, test directory shapes, `evals/`
exemption, transient-directory exemption, `.apm/` content, projected-skill
content, missing projection refusal, out-of-pack tests, symlink and junction
refusal, source traversal, dynamic path discovery, runner collision,
unregistered suite, workflow `working-directory`, structured Python runner
commands, missing runner file, malformed runner file, clean production tree) is
an assertable invariant with a known expected verdict. Each is exercised against
a temporary fixture catalogue, and the callable API and the CLI are asserted to
reach the **same** pass/fail decision for the same fixture — a parity test,
because two entry points that can disagree are a latent contract split.

**Falsification integrity — TDD.** For each planted violation, four things are
asserted: the lint fails, the failure names the plant or its policy, the failure
comes from the **intended** check rather than an unrelated one, and removal
restores a passing verdict. Check attribution is the load-bearing half: a plant
that fails for the wrong reason is a guard nobody has actually checked.

**Production CLI wiring — visual / manual QA, at the end-to-end surface.** A
minimal real-worktree layer exercises the real built artifact: the clean
production tree passes the complete six-check lint, one representative
runtime-boundary plant is detected and named, one representative runner or
linked-tree plant is detected and named, and cleanup returns the tree to a
passing state. Fixture tests cannot prove the CLI is wired to the real
catalogue; only running it against the real catalogue can. The observed exit
code and stderr are recorded.

**Terminal gate preservation — goal-based check.** `agentbundle catalogue lint
--deep`, `catalogue verify`, the catalogue pre-PR aggregator and the production
lints are each run once and asserted to pass with unchanged terminal wording.
These are existing gates with existing verdicts; running them is the check.

**Performance — goal-based check, reported as evidence, not asserted in CI.**
Before/after process, traversal, parse and launch counts plus one bounded
wall-clock sample are recorded. The structural counts above are the normative
assertions; a millisecond threshold in CI would be brittle on varying hardware
and is explicitly out of scope.

## Acceptance Criteria

**Audit and scope**

- [ ] `docs/specs/lint-performance-p0/notes/lint-inventory.md` records, for every
      production lint entry point and every lint self-test in the repository, all
      ten inventory fields (entrypoint/check, owner, scope class, gate wiring,
      traversal roots, ignore semantics, Git process shape, repeated work,
      self-test model, P0 disposition), and is committed before any
      implementation commit.
- [ ] Every audited lint is classified into exactly one of pack/skill-local,
      catalogue-wide, repo-global, or hybrid, with classification recorded per
      check where a file carries checks of more than one class.
- [ ] Exactly the three files whose inventory row says `CHANGE`
      (`tools/lint-pack-test-boundary.py`, `tools/test-lint-pack-test-boundary.py`,
      `tools/lint-agents-md.py`) are modified for P0 reasons; every other lint
      carries a recorded justified no-P0-change disposition and is not churned.

**Batched Git-ignore resolver**

- [ ] One repo-only batch resolver module exists under `tools/`, and it is the
      only approved home for direct `git check-ignore` subprocess construction in
      production lint code.
- [ ] Portable `agentbundle` code and shipped pack/skill code import no repo-only
      `tools/` helper, and no portable or shipped-pack helper is added — measured
      zero callers need one.
- [ ] The resolver deduplicates candidates before invoking Git.
- [ ] The resolver returns deterministic, stably ordered results for diagnostics
      and tests.
- [ ] An empty candidate set launches **zero** `git check-ignore` processes.
- [ ] A non-empty candidate set launches **at most one** `git check-ignore`
      process per Git root per batch, verified for a batch of hundreds of
      candidates.
- [ ] Candidates are delivered over stdin, never argv, using NUL-delimited input
      and output (`git check-ignore --stdin -z`).
- [ ] Paths containing spaces, tabs, newlines, Unicode characters and leading
      dashes are resolved correctly through the NUL-delimited round trip.
- [ ] Git exit code 0 and exit code 1 are both treated as normal batch outcomes.
- [ ] Git execution errors and Git absence resolve to the configured
      missing-Git policy, stated explicitly at every call site rather than
      inherited from a silent default.
- [ ] Whether tracked, generated, or untracked-ignored files count as ignored is
      unchanged: `--no-index` is not introduced, so tracked files remain excluded
      from the ignored set exactly as before.
- [ ] The resolver uses no shell and no `shell=True`, and applies an explicit
      bounded timeout.
- [ ] The resolver prints nothing and returns structured data; all diagnostics
      remain the calling lint's responsibility.
- [ ] A deterministic AST-aware regression check walks production lint sources
      and fails on direct `git check-ignore` subprocess construction outside the
      approved helper module, while permitting the helper itself and fixture
      strings used to test detection.

**`lint-pack-test-boundary` architecture**

- [ ] The lint exposes an explicit context object and structured findings; no
      production check depends on module-global mutable execution state, and the
      former `FAILURES` global is gone.
- [ ] One immutable inventory is constructed per invocation, and all six checks
      read that one inventory rather than independently rebuilding overlapping
      portions of it.
- [ ] Runner files are read and parsed exactly once per invocation, and the
      shared destination inventory is built exactly once per invocation.
- [ ] Tree-confinement results are memoised for the duration of one invocation,
      keyed by a safe path identity, with symlink refusal, junction refusal,
      resolution-error fail-closed behaviour, lexical traversal checks and
      existing AST/path-provenance behaviour all preserved.
- [ ] Neither the inventory nor the confinement cache is persisted to disk or
      reused across processes or invocations.
- [ ] A side-effect-free callable API returns structured findings in deterministic
      order, parses no CLI arguments, calls no `sys.exit`, prints nothing, and
      mutates no repository file.
- [ ] The no-argument CLI still runs all six checks in their existing order and
      emits the existing per-check `ok   [<check>] (…)` lines, the existing
      `FAIL:` formatting, the existing `✓ lint-pack-test-boundary: passed
      (6 cases).` terminal line, and the existing exit codes.
- [ ] A repeatable `--check <name>` selector accepts the six stable check names
      (`apm-carries-no-tests`, `projection-carries-no-tests`,
      `tests-live-in-the-pack-tree`, `runners-keep-suites-isolated`,
      `every-suite-dir-has-a-runner`, `pack-tests-stay-in-pack`), and an explicit
      fixture-root option lets self-tests run against a small synthetic catalogue.
- [ ] A targeted or fixture-scoped run names which checks ran and does **not**
      emit the six-check terminal wording, so no partial run can be mistaken for
      a complete catalogue pass.
- [ ] For one complete six-check invocation: exactly one inventory construction,
      at most one batched `check-ignore` process, runner files parsed once, and
      the destination inventory built once — each asserted by instrumenting the
      real boundary, not by source-string matching.

**Falsification suite**

- [ ] Pure semantic behaviour (matcher shapes, AST path-provenance, runner
      parsing, lexical traversal, symlink and junction predicates) is asserted
      in-process without launching the production CLI.
- [ ] Each individual planted case runs against a small temporary fixture
      catalogue of tens of files, invoking only the check that case targets.
- [ ] The suite performs no mutation of the real repository `Makefile`, workflows,
      recipes, pack trees or projected trees for cases that only exercise a parser
      or a single policy decision.
- [ ] A minimal real-worktree layer remains and proves: the clean production tree
      passes the complete lint; one representative runtime-boundary plant is
      detected and named; one representative runner or linked-tree plant is
      detected and named; and cleanup returns the tree to a clean passing state.
- [ ] Every real-tree plant has `try`/`finally` (or equivalent) cleanup and
      refuses to run when its intended target already exists.
- [ ] Every planted violation proves all four of: the lint fails; the failure
      names the plant or expected policy; the failure originates from the intended
      check; and removal or restoration makes the relevant check pass.
- [ ] Every pre-existing boundary-lint contract listed in Testing Strategy is
      still covered, and the callable API and CLI produce equivalent pass/fail
      decisions for the same fixture.

**Preserved gates and terminal semantics**

- [ ] `agentbundle catalogue lint`, `catalogue lint --deep` and `catalogue verify`
      keep their catalogue-wide default scope and terminal wording.
- [ ] `tools/catalogue/pre_pr_catalogue.py` keeps its fail-fast behaviour, failure
      labels, stdout/stderr forwarding, verification-first ordering, and its
      distinction between adopter-facing and catalogue-only gates, and continues
      to run distinct lints as separate processes.
- [ ] No terminal catalogue or CI gate becomes diff-aware, and terminal catalogue
      and CI coverage are not narrowed.
- [ ] Source-of-truth files, projected files, tests and documentation are
      synchronised per repository policy (`make build-self` run after any
      `packs/` change).

**Measured outcome**

- [ ] Before/after evidence is recorded for: complete worktree scans, candidate
      path count, `git check-ignore` process count, complete lint CLI launches in
      the falsification suite, repeat parses of shared runner/catalogue inputs,
      and elapsed time.
- [ ] `python3 tools/lint-pack-test-boundary.py` launches at most one
      `check-ignore` process, down from a measured 337.
- [ ] The complete optimised falsification suite **runs to completion and
      passes**, within the work-loop's five-minute inner-loop budget on the
      development machine, and the previous 71%-then-stall behaviour is not
      reproducible for the same slow cases.
- [ ] No millisecond-level wall-clock threshold is asserted in CI.

## Assumptions

- Technical: `git check-ignore --stdin -z` accepts NUL-delimited candidates on
  stdin and echoes back only the ignored subset, NUL-delimited, exiting 0 when at
  least one path is ignored and 1 when none is (source: probe against git 2.50.1,
  2026-08-17 — mixed ignored/non-ignored batch returned only the ignored path,
  exit 0; all-clean batch exit 1).
- Technical: spaces, tabs, newlines, Unicode characters and leading dashes all
  survive the NUL-delimited round trip intact (source: probe in an isolated
  scratch Git repository, 2026-08-17 — all five shapes returned byte-identical).
- Technical: omitting `--no-index` keeps tracked files excluded from the ignored
  set, identical to the current `git check-ignore -q --` call, so batching
  preserves authored-versus-generated semantics (source: probe, 2026-08-17 —
  tracked `tools/lint-ruff.py` was not reported as ignored).
- Technical: `tools/lint-pack-test-boundary.py` currently launches 337
  `check-ignore` subprocesses and takes 32.35 s per invocation; `_walk` runs 141
  times over 109 distinct bases; `_glob_tree_is_confined` runs 45 times over 16
  distinct bases; runner files and destinations are each built twice (source:
  counting Git shim on `PATH` plus counter-instrumented in-process `main()`,
  2026-08-17).
- Technical: `tools/test-lint-pack-test-boundary.py` launches the full production
  lint 12 times against the real worktree and rewrites the real root `Makefile`
  twice (source: `tools/test-lint-pack-test-boundary.py:421,436,450,459,478,498,519,551,573,613,634,661`;
  Makefile writes at lines 568 and 606).
- Technical: portable `agentbundle catalogue lint --deep` completes in 5.89 s with
  zero Git subprocesses, and `catalogue verify` in 13.47 s with one already-batched
  `git ls-files`; all seven shipped pack/skill lints issue Git subprocesses only at
  loop depth zero and none calls `check-ignore` (source: Git shim counts plus an
  AST loop-depth scan, 2026-08-17).
- Technical: every production lint other than the two named ones runs in
  0.13 s–5.33 s with zero `check-ignore` calls (source: 27-lint timing sweep with
  Git shim, 2026-08-17).
- Technical: in `tools/lint-agents-md.py`, `note()` is fatal (sets `fail = 1`,
  returning exit 1) and its three gitignore probes assert the probes **are**
  ignored — an inverted assertion relative to the boundary lint. A resolver that
  reports nothing as ignored therefore yields a clean `exit 1` with three drift
  notes on a Git-less machine, replacing today's unhandled `FileNotFoundError`
  (source: `tools/lint-agents-md.py:45-56,313-322,378-384`).
- Process: `tools/lint-ci-parity.py` already pairs a `--root` option with
  fixture-root self-tests plus one real-root end-to-end launch, so the target
  architecture follows an existing repository precedent rather than introducing a
  new pattern (source: `tools/lint-ci-parity.py:983`,
  `tools/test-lint-ci-parity.py:482,505,517`).
- Process: full mode is correct for this work — the structural/public-interface
  trigger fires (new module boundary for the shared resolver, new callable API)
  and the compliance/governance trigger fires (the change touches governance
  gates) (source: `work-loop` risk triggers).
- Product: the implementation scope is the three files the audit measured as
  carrying a P0 pattern, not a broader sweep; clean lints keep a recorded
  no-change disposition (source: user confirmation 2026-08-17).
- Product: exactly one repo-only resolver is built; no portable `agentbundle` or
  shipped-pack resolver is added, because measurement found zero callers needing
  one (source: user confirmation 2026-08-17).
- Product: the two lints' Git-missing behaviour is deliberately **unified** to the
  fail-open policy (resolver reports nothing as ignored). This is an authorised
  divergence from the originating brief's instruction to preserve divergent
  fail-open/fail-closed policies behind an option; it was raised before adoption
  and chosen knowingly. The `missing_git_policy` parameter is retained and
  required at every call site so the policy stays explicit and the divergence can
  be re-established without redesign (source: user confirmation 2026-08-17).
- Process: this spec registers under initiative `ini-007` (Catalogue Contracts,
  Composition, Semantics, and Discovery), which already shipped
  `pack-test-boundary-remaining-packs` (source: user confirmation 2026-08-17).
