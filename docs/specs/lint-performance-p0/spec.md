# Spec: lint-performance-p0

- **Status:** Draft <!-- Draft | Approved | Implementing | Shipped | Archived -->
- **Owner:** eugenelim
- **Plan:** [`plan.md`](plan.md)
- **Constrained by:** ADR-0071 (`evals/` is skill-local runtime content); `docs/guides/_shared/reference/catalogue-authoring-standards.md` § 4 (cross-pack behaviour is not pack-owned); `docs/specs/pack-test-boundary-remaining-packs/spec.md` (Shipped — this spec completes its `plan.md:636` stdin-batching clause and supersedes the literal wording of its `AC10a`)
- **Brief:** none
- **Discovery:** none
- **Contract:** none <!-- no external interface surface; the callable lint APIs are internal repo-tooling seams -->
- **Shape:** service

> **Spec contract:** this document defines what "done" means. The implementing
> PR must match this spec, or update it. Verification must be derivable from it.

**Audit:** [`notes/lint-inventory.md`](notes/lint-inventory.md) is the scope
contract for this spec and the single canonical home for the before/after
performance figures. Every lint-like production entry point and every lint
self-test is classified there with a P0 disposition. A lint may be changed
**only** if its row says `CHANGE`. Figures are not restated here.

## Objective

The repository's lint system runs fast enough to sit inside the work-loop's
five-minute inner loop, and no lint contract is weaker for it. The user is an
agent or engineer running the lint gates repeatedly while iterating: they get
the same verdicts, the same diagnostics and the same exit codes as before, but
the catalogue's runtime-boundary lint completes in seconds rather than tens of
seconds, and its falsification suite completes comfortably inside the budget
rather than sitting on the cutoff.

Three properties deliver that. **Ignore decisions are batched:** no production
lint asks Git about one path at a time; a lint needing Git-ignore semantics
sends its whole candidate set through one resolver call, which launches at most
one `git check-ignore` process and none at all for an empty candidate set.
**One inventory per invocation:** the catalogue-wide runtime boundary lint
builds its pack, projection, runner, destination and ignore data once and all
six of its checks read that one inventory, instead of six checks independently
rebuilding overlapping parts of it. **Falsification is fixture-scoped:** each
planted violation is proven against a small temporary catalogue of tens of
files, with a deliberately minimal real-tree layer retained to prove the
production CLI is actually wired to the real catalogue.

Success is structural and measurable: the boundary lint launches **one** batched
`check-ignore` process, builds **one** inventory, parses each runner file
**once**, and its falsification suite launches the full production lint exactly
four times — with every existing failure message, exit code, failure *count*,
fail-closed refusal and symlink protection intact, and the complete catalogue and
repository terminal gates unchanged.

## Boundaries

The three-tier guard that keeps an implementing agent inside the lines.
*Always do* applies without asking; *Ask first* requires human sign-off
before proceeding; *Never do* is a hard rule, even under time pressure.

### Always do

- Change a lint only when its row in [`notes/lint-inventory.md`](notes/lint-inventory.md)
  says `CHANGE`. Everything else keeps its recorded no-P0-change disposition.
- Preserve every existing exit code, stdout/stderr split, check code, load-bearing
  diagnostic substring, **and failure count**. The canonical enumeration of
  preserved failure strings is [§ Preserved failure
  contract](#preserved-failure-contract) below; tasks reference it rather than
  restating it.
- Preserve fail-closed behaviour exactly: symlink refusal, junction refusal,
  resolution-error refusal, lexical `..` traversal refusal, dynamic-path
  refusal, and every deliberate non-vacuity failure.
- Pass candidate paths to Git over **stdin**, NUL-delimited, as bytes, with an
  explicit bounded timeout, no shell, and no `shell=True`.
- Give every real-worktree plant a `try`/`finally` cleanup guarantee, and make
  it refuse to run when its target already exists.
- Keep the callable check API side-effect-free: no argument parsing, no
  `sys.exit`, no printing, no repository mutation.
- Relativize every recorded diagnostic, stderr capture and evidence figure to the
  repository root before committing it — absolute home-directory paths are
  forbidden in git artifacts (`AGENTS.md` § Privacy).

### Ask first

- Adding any `--pack`, `--skill` or other scoping option to a check whose
  correctness genuinely needs peer catalogue state.
- Removing, weakening or merging any existing falsification case, including any
  reduction in the set of matcher shapes or path-provenance shapes asserted, and
  including the two non-vacuity controls named in
  [§ Preserved falsification controls](#preserved-falsification-controls).
- Changing which paths a lint treats as authored versus generated, or otherwise
  altering whether tracked, generated or untracked-ignored files are considered.
- Changing the default terminal behaviour of `agentbundle catalogue lint`,
  `catalogue lint --deep`, `catalogue verify`,
  `tools/catalogue/pre_pr_catalogue.py`, `make pre-pr`, `make build-check`, or
  any CI lint job.
- Widening `tools/lint-mypy.py`'s `TYPED_PACKAGES` to cover `tools/`.

### Never do

- **Never add a new runtime dependency, importable package under `tools/`, or
  top-level directory.** `tools/catalogue/` and `tools/repo/` carry no
  `__init__.py`; the shared resolver is a flat module, not the first package
  under `tools/`. No third-party pathspec or Git library, no daemon, no MCP
  requirement, no control plane, no `uv` requirement, no persistent scan
  service, no SQLite or on-disk lint cache, no `pytest-xdist` or automatic test
  parallelism.
- Never make a shipped pack or skill lint import a repo-only `tools/` helper, and
  never make portable `agentbundle` code import repo-only `tools/`.
- Never launch one `git check-ignore` process per candidate path from any
  production lint.
- Never persist an inventory or a confinement-scan cache across lint processes,
  and never reuse either across invocations.
- Never make a terminal catalogue or CI gate diff-aware, changed-pack-only or
  changed-file-only.
- Never let a targeted or fixture-scoped invocation emit the complete six-check
  terminal wording, and never let an unrecognised selector, an empty selection,
  or a fixture root produce a zero-finding exit 0 that reads as a pass.
- Never apply the batched ignored-set to a check that today deliberately does not
  ignore-filter.
- Never raise the work-loop time budget, widen a timeout, or move unbounded work
  into CI as the fix.
- Never edit a gate, test or assertion to make a failure go away.

## Preserved failure contract

The canonical enumeration. Every string below exists in
`tools/lint-pack-test-boundary.py` today and must still be reachable, with the
same attribution and count, after the refactor. `plan.md`'s task tests reference
this list by name.

| # | Failure string (substring) | Site | Notes |
| --- | --- | --- | --- |
| F1 | `no packs found under packs/` | `:198`, `:269` | non-vacuity; reached from two checks |
| F2 | `self-host recipe not found at` | `:189` | non-vacuity |
| F3 | `self-host recipe lists no packs to project` | `:220` | non-vacuity |
| F4 | `no projected skills tree found under .claude/skills or .agents/skills` | `:225` | non-vacuity |
| F5 | `is in the self-host include list but none of its skills is projected` | `:246` | non-vacuity |
| F6 | `a pack's .apm/ is the runtime export boundary but carries test content` | `:206` | |
| F7 | `projected skills carry test content` | `:253` | |
| F8 | `exists but holds no test content` | `:278` | empty test tree |
| F9 | `pack test root is linked` | `:756` | fail-closed |
| F10 | `pack test tree contains a linked directory` | `:771` | fail-closed |
| F11 | `pack test is a symlink` | `:783` | fail-closed |
| F12 | `pack test reaches above` | `:792` | source confinement |
| F13 | `test is not below packs/<pack>/` | `:726` | |
| F14 | `unparseable Python:` | `:720` | |
| F15 | `one pytest invocation covers multiple skill suites` | `:1005` | |
| F16 | `no skill test directories found` | `:1025` | non-vacuity |
| F17 | `is declared unrun in _NO_RUNNER but a runner names it` | `:1035` | inverse exemption |
| F18 | `holds a suite that no runner names` | `:1041` | |
| F19 | `names <path>, which holds no suite` (stale exemption) | `:1048` | |
| F20 | `does not exist — the collision and coverage checks silently stop reading it` | `:969` | missing runner file |
| F21 | `is not parseable:` (runner file) | `:942` | malformed runner file |

**Count and attribution.** F20 and F21 are emitted from `_runner_lines()`, which
is called from **both** `runners-keep-suites-isolated` and
`every-suite-dir-has-a-runner`. One missing runner file therefore produces
**two** identical findings today, `✖ lint-pack-test-boundary: 2 failure(s)`, and
suppresses **both** checks' `ok` lines. Parsing runners once must not silently
reduce that to one finding or restore an `ok` line.

## Preserved falsification controls

Two existing assertions are non-vacuity controls, not ordinary cases, and are
named here so a fixture migration cannot quietly drop them:

- **C1 — the collision fixture still collides.**
  `tools/test-lint-pack-test-boundary.py:645-660` asserts that
  `markdown-to-docx` and `markdown-to-pptx` still share a test basename, on the
  grounds that if the overlap ever vanishes the collision guard stops proving
  anything. This is an assertion about the **real tree**.
- **C2 — a broad runner fails even without a collision.**
  `tools/test-lint-pack-test-boundary.py:586-624` asserts a runner spanning
  `adapt-to-project` + `flow-metrics` fails **and names both suites**, proving
  the check keys on invocation shape rather than on today's filenames.

## Testing Strategy

Each behaviour from the Objective is paired with a mode and a reason.

**Batched ignore resolution — TDD.** The resolver is a function over (repo root,
candidate iterable, missing-Git policy) with a compressible invariant: an ignored
subset plus a bounded process count. It is the one piece of genuinely new logic,
its edge cases are enumerable up front, and each is cheap to assert in-process.
Tests come before the implementation.

**Git process-count and inventory-count properties — TDD, at the integration
surface.** "One full lint invocation launches at most one `check-ignore`
process" and "one inventory construction, runner files parsed once" are
invariants about a whole invocation, so they are asserted by instrumenting the
lint's real process and inventory boundary and running a complete invocation —
not by matching source strings. Source matching cannot see a call added through
an alias, and a passing source grep on a broken lint is exactly the false
confidence this spec exists to remove.

**Source-level enforcement of the batching rule — goal-based check.** "No
production lint constructs a direct `git check-ignore` subprocess outside the
approved helper" is a property of the source tree, verified by an AST-aware walk.
A one-liner over the tree answers it; there is no runtime behaviour to drive. It
complements — and does not replace — the structural process-count tests above.

**Boundary-lint behavioural equivalence — TDD.** Every contract in
[§ Preserved failure contract](#preserved-failure-contract), plus every existing
success path (test filename shapes, test directory shapes, `evals/` exemption,
transient-directory exemption, workflow `working-directory`, structured Python
runner commands, clean production tree), is an assertable invariant with a known
expected verdict. Each is exercised against a temporary fixture catalogue, and
the callable API and the CLI are asserted to reach the **same** pass/fail
decision for the same fixture — a parity test, because two entry points that can
disagree are a latent contract split.

**Falsification integrity — TDD.** For each planted violation, four things are
asserted: the lint fails, the failure names the plant or its policy, the failure
comes from the **intended** check rather than an unrelated one, and removal
restores a passing verdict. Check attribution is the load-bearing half: a plant
that fails for the wrong reason is a guard nobody has actually checked.

**Production CLI wiring — TDD at the end-to-end surface.** A minimal real-tree
layer inside the automated suite drives the real built CLI four times: the clean
production tree passes the complete six-check lint; one representative
runtime-boundary plant is detected and named; one representative runner or
linked-tree plant is detected and named; and cleanup returns the tree to a
passing state. Fixture tests cannot prove the CLI is wired to the real
catalogue; only running it against the real catalogue can. This is automated,
not manual QA — there is no human gesture and no recorded screenshot; the
observable is the CLI's exit code and stderr, asserted in-suite.

**Terminal gate preservation — goal-based check.** `agentbundle catalogue lint
--deep`, `catalogue verify`, the catalogue pre-PR aggregator and the production
lints are each run once and asserted to pass with unchanged terminal wording.
These are existing gates with existing verdicts; running them is the check.

**Performance — goal-based check, reported as evidence, not asserted in CI.**
Before/after process, traversal, parse and launch counts plus one bounded
wall-clock sample are recorded in the audit note. The structural counts above are
the normative assertions; a millisecond threshold in CI would be brittle on
varying hardware and is out of scope.

**Not covered by this spec's gates.** `make lint-mypy` targets only
`packages/agentbundle/agentbundle` and `packages/credbroker/credbroker`
(`tools/lint-mypy.py:19-22`). This diff is entirely under `tools/`, so mypy does
not type-check any changed file and is **not** claimed as a gate for it.
Widening its targets is an `Ask first` item, deliberately not taken here.

## Acceptance Criteria

**Audit and scope**

- [ ] `notes/lint-inventory.md` records, for every production lint entry point
      and every lint self-test under `tools/`, `packs/` and `packages/`, all ten
      inventory fields, and is committed before any implementation commit. Its
      census is complete for that universe: 38 production lints, 7 pack-owned
      lint scripts, 67 `tools/` self-tests (35 hyphen-named + 32
      underscore-named) and `tools/test-lint-build.sh`.
- [ ] Every audited lint is classified into exactly one of pack/skill-local,
      catalogue-wide, repo-global, or hybrid, with classification recorded per
      check where a file carries checks of more than one class.
- [ ] No lint other than the three rows marked `CHANGE`
      (`tools/lint-pack-test-boundary.py`,
      `tools/test-lint-pack-test-boundary.py`, `tools/lint-agents-md.py`) is
      modified. New helper and gate files, and bookkeeping updates to
      `workspace.toml`, `docs/specs/**` and the two wiring files named in AC
      *gates are wired*, are listed in `plan.md` and are not lint changes.
- [ ] `docs/specs/pack-test-boundary-remaining-packs/spec.md` `AC10a` carries a
      supersession annotation recording that stdin delivery replaces its `--`
      terminator requirement, per `docs/CONVENTIONS.md § Superseding a frozen
      document`.

**Batched Git-ignore resolver**

- [ ] One repo-only batch resolver lives in a **flat** module under `tools/`
      (no new importable package), and it is the only approved home for direct
      `git check-ignore` subprocess construction in production lint code.
- [ ] Portable `agentbundle` code and shipped pack/skill code import no repo-only
      `tools/` helper, and no portable or shipped-pack resolver is added.
- [ ] The resolver accepts candidates that are either absolute-under-`repo_root`
      or `repo_root`-relative, and returns results keyed so that a caller can
      test membership using the **exact objects it supplied** — asserted for
      absolute, relative and non-existent candidates.
- [ ] A candidate that resolves outside `repo_root` is rejected at the boundary
      with a `ValueError` naming the path, never silently dropped and never
      forwarded to Git. (Git exits 128 with a *partial* result for such a path,
      so forwarding it would silently under-report the whole batch.)
- [ ] The resolver deduplicates candidates before invoking Git.
- [ ] The resolver returns a deterministically **sorted sequence**, so ordering
      is stable across processes under hash randomisation.
- [ ] An empty candidate set launches **zero** `git check-ignore` processes.
- [ ] A non-empty candidate set launches **exactly one** `git check-ignore`
      process, verified for a batch of hundreds of candidates. Candidates
      spanning more than one Git root are outside the resolver's domain and are
      rejected rather than silently split.
- [ ] Candidates are delivered over stdin, never argv, NUL-delimited, in a single
      `communicate()`-backed call whose bounded timeout covers the whole batch —
      asserted with a payload larger than the OS pipe buffer, so a
      `Popen`+`write`+`wait` implementation that could deadlock cannot satisfy
      the criterion.
- [ ] The payload is built with `os.fsencode` and parsed with `os.fsdecode` as
      **bytes**, so a filename that is not valid UTF-8 cannot raise
      `UnicodeEncodeError` outside the missing-Git policy.
- [ ] Paths containing spaces, tabs, newlines, Unicode characters, leading
      dashes, a leading `:` and a leading `!` are resolved correctly through the
      NUL round trip. (`check-ignore --stdin` does not apply pathspec magic, and
      a `:(literal)` prefix is rejected by this subcommand — it must not be
      added.)
- [ ] Git exit codes 0 and 1 are both treated as normal batch outcomes.
- [ ] Any other exit code is surfaced to the caller as a resolver error carrying
      Git's stderr, never collapsed into "nothing is ignored".
- [ ] The resolver reports **degradation explicitly** — a caller can distinguish
      "Git ran and nothing is ignored" from "Git was absent, errored, or timed
      out". Git absence, execution error and timeout all resolve through the
      configured missing-Git policy, which is a **required** keyword argument at
      every call site, as is the timeout.
- [ ] Whether tracked, generated, or untracked-ignored files count as ignored is
      unchanged: `--no-index` is not introduced, so tracked files remain excluded
      from the ignored set exactly as before.
- [ ] The resolver uses no shell and no `shell=True`.
- [ ] The resolver prints nothing to stdout or stderr and returns structured
      data; all diagnostics remain the calling lint's responsibility.
- [ ] A deterministic AST-aware regression check scans **every** `*.py` under
      `tools/`, `packs/` and `packages/`, excluding test files by an explicit
      documented rule, and fails when `check-ignore` appears **anywhere** in a
      resolved argv sequence (not only at position 1, so
      `["git","-C",root,"check-ignore",…]` is caught) or in a shell-string,
      `os.system` or `os.popen` construction. It permits the approved helper and
      fixture strings used to test detection, asserts the approved helper is
      **present in the scanned inventory**, and asserts the scanned file count
      against a recorded floor so an unmatched path cannot make it pass
      vacuously.
- [ ] Both new gates are wired into standing CI — a step in
      `.github/workflows/docs.yml` and an entry in `tools/test-all.py`, matching
      the boundary lint's existing precedent — not merely run once by hand.

**`lint-pack-test-boundary` architecture**

- [ ] The lint exposes an explicit context object and structured findings; no
      production check depends on module-global mutable execution state, and the
      former `FAILURES` global is gone.
- [ ] The context carries everything a fixture run needs, including the
      `_NO_RUNNER` exemption map and the packs root, so no check reads a module
      global. Against a synthetic root the lint must not emit the eight real
      stale-exemption findings, and a fixture pack test must not fail with
      `test is not below packs/<pack>/`.
- [ ] One immutable inventory is constructed per invocation, and all six checks
      read that one inventory rather than independently rebuilding overlapping
      portions of it. Test basenames are **not** in the inventory — no production
      check consumes them.
- [ ] Runner files are read and parsed exactly once per invocation, and the shared
      destination inventory is built exactly once per invocation, **without**
      changing the failure count or `ok`-line suppression documented in
      [§ Preserved failure contract](#preserved-failure-contract): a fixture with
      one missing and one malformed runner file yields the same number of
      findings, the same suppressed checks, and the same `✖ … N failure(s)` line
      as before.
- [ ] The batched ignored-set is applied only where `_walk` applies it today.
      `pack-tests-stay-in-pack` continues to inspect gitignored `.py` files under
      a pack's test tree — asserted by a case where a gitignored
      `packs/<p>/tests/test_x.py` that climbs above its pack still fails.
- [ ] Tree-confinement results are memoised for the duration of one invocation,
      keyed by the **lexically normalised unresolved** base path, so a symlinked
      base and its real target never share a cache entry. Asserted
      order-independently: a linked base and its direct target each receive their
      own verdict regardless of which is scanned first. A key-computation or
      resolution error yields and caches a refusal.
- [ ] Neither the inventory nor the confinement cache is persisted to disk or
      reused across processes or invocations.
- [ ] A side-effect-free callable API returns structured findings in deterministic
      order, parses no CLI arguments, calls no `sys.exit`, prints nothing, and
      mutates no repository file.
- [ ] The no-argument CLI still runs all six checks in their existing execution
      order — `apm-carries-no-tests`, `projection-carries-no-tests`,
      `tests-live-in-the-pack-tree`, `pack-tests-stay-in-pack`,
      `runners-keep-suites-isolated`, `every-suite-dir-has-a-runner` — and emits
      the existing per-check `ok   [<check>] (…)` lines, the existing `FAIL:`
      formatting, the existing `✓ lint-pack-test-boundary: passed (6 cases).`
      terminal line, and the existing exit codes.
- [ ] A repeatable `--check <name>` selector accepts those six stable names, and
      an explicit `--root` option lets self-tests run against a synthetic
      catalogue.
- [ ] An unrecognised `--check` name, or a selection that resolves to zero
      checks, exits non-zero naming the accepted set — from the CLI and as a
      `ValueError` from the callable API. It must never be a zero-finding exit 0.
- [ ] A targeted or fixture-scoped run names which checks ran and does **not**
      emit the six-check terminal wording.
- [ ] `--root` is canonicalised once, with `(OSError, RuntimeError)` yielding a
      non-zero exit naming the path; a root that is itself a symlink or junction
      is refused; a root lacking `packs/` and the self-host recipe is refused
      **before** any traversal begins; and every derived path and prefix
      comparison uses that one canonical form.
- [ ] Under `--root`, the resolver's repo root is the fixture root, fixture roots
      are created outside the real worktree, and a fixture-scoped run asserts its
      ignore layer actually resolved — one fixture file made ignored by a
      fixture-local `.gitignore` comes back ignored — so the ignore layer cannot
      silently degrade to a no-op.
- [ ] All four non-vacuity refusals (F1, F3, F4, F5 and F16 of
      [§ Preserved failure contract](#preserved-failure-contract)) still fire
      against a deliberately empty fixture root; `--root` does not relax them.
- [ ] For one complete six-check invocation: exactly one inventory construction,
      exactly one batched `check-ignore` process, runner files parsed once, and
      the destination inventory built once — each asserted by instrumenting the
      real boundary, not by source-string matching.

**`lint-agents-md`**

- [ ] `tools/lint-agents-md.py` resolves its three session-scratch gitignore
      probes in **exactly one** `check-ignore` process, down from three.
- [ ] A probe that is gitignored produces no note; a probe that is not produces
      the existing `drift-watch:` note naming that probe with its existing
      wording, and the existing fatal `note()` semantics.
- [ ] With Git absent, erroring or timing out, the lint exits 1 **and** emits a
      diagnostic naming Git unavailability — not three `drift-watch:` notes
      claiming `.gitignore` drifted, which would be a false diagnosis of a real
      degradation — and does not raise an unhandled traceback.
- [ ] Checks 8, 10d and 10g still behave as
      `tools/test_lint_agents_md_{diataxis,legacy,risk}_block.py` assert, and the
      aggregator-extraction anchor `tools/test-lint-ci-parity.py:292` still holds.

**Falsification suite**

- [ ] Pure semantic behaviour (matcher shapes, AST path-provenance, runner
      parsing, lexical traversal, symlink and junction predicates) is asserted
      in-process without launching the production CLI.
- [ ] Each individual planted case runs against a small temporary fixture
      catalogue of tens of files — including projected-skill roots — invoking only
      the check that case targets.
- [ ] The suite performs no mutation of the real repository `Makefile`,
      workflows, recipes, pack trees or projected trees for cases that only
      exercise a parser or a single policy decision, asserted by hashing those
      paths before and after the run.
- [ ] Both non-vacuity controls C1 and C2 in
      [§ Preserved falsification controls](#preserved-falsification-controls) are
      retained as named cases.
- [ ] A minimal real-worktree layer launches the production CLI exactly **four**
      times and proves: the clean tree passes the complete lint; one
      representative runtime-boundary plant is detected and named; one
      representative runner or linked-tree plant is detected and named; and
      cleanup returns the tree to a clean passing state.
- [ ] Every real-tree plant has `try`/`finally` (or equivalent) cleanup and
      refuses to run when its intended target already exists.
- [ ] Every planted violation proves all four of: the lint fails; the failure
      names the plant or expected policy; the failure originates from the intended
      check; and removal or restoration makes the relevant check pass.
- [ ] Every failure string F1–F21 in
      [§ Preserved failure contract](#preserved-failure-contract) has at least one
      case, and the callable API and CLI produce equivalent pass/fail decisions
      for the same fixture.
- [ ] The suite reports **at least 82** cases — the measured pre-change runtime
      count recorded in the audit note.

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
      synchronised per repository policy.

**Measured outcome**

- [ ] Before/after evidence is recorded in `notes/lint-inventory.md` for:
      complete worktree scans, candidate path count, `check-ignore` process
      count, complete lint CLI launches in the falsification suite, repeat parses
      of shared runner/catalogue inputs, and elapsed time — relativized, with no
      absolute home-directory paths.
- [ ] `python3 tools/lint-pack-test-boundary.py` launches exactly one
      `check-ignore` process, down from the measured 337.
- [ ] The complete optimised falsification suite exits 0, launches the production
      CLI exactly four times, and completes within the work-loop's five-minute
      inner-loop budget on the development machine, with its wall clock recorded
      against the measured 306.4 s baseline.
- [ ] No millisecond-level wall-clock threshold is asserted in CI.

## Assumptions

- Technical: `git check-ignore --stdin -z` accepts NUL-delimited candidates on
  stdin and echoes back only the ignored subset, NUL-delimited, exiting 0 when at
  least one path is ignored and 1 when none is (source: probe against git 2.50.1,
  2026-08-17).
- Technical: spaces, tabs, newlines, Unicode, and leading dashes survive the NUL
  round trip intact (source: probe in an isolated scratch Git repository,
  2026-08-17).
- Technical: `check-ignore --stdin` does **not** apply pathspec magic — a leading
  `:` or `!` round-trips verbatim — and a `:(literal)` prefix is rejected by this
  subcommand with `fatal: pathspec magic not supported by this command`. A
  proposed `:(literal)` escaping fix was therefore rejected: it would have broken
  every candidate (source: probe, 2026-08-17).
- Technical: an out-of-repo candidate makes `check-ignore` exit **128 with a
  partial result** — the paths processed before it are still echoed. Neither
  discarding nor trusting that output is safe, so candidates are confined before
  the call and non-0/1 exits are surfaced (source: probe, 2026-08-17).
- Technical: omitting `--no-index` keeps tracked files excluded from the ignored
  set, identical to the current `git check-ignore -q --` call (source: probe,
  2026-08-17).
- Technical: keying the confinement memo on `base.resolve()` collapses a symlink
  and its target to one key, losing the symlink refusal when the target is
  scanned first and falsely refusing the real tree when the link is scanned
  first — wrong in both directions and dependent on filesystem iteration order.
  The lexically normalised unresolved path is correct and order-independent
  (source: fixture probe, 2026-08-17).
- Technical: macOS APFS refuses to create a filename containing an undecodable
  byte (`OSError: [Errno 92]`), so the non-UTF-8 filename case cannot be built on
  the development host; Linux ext4 in CI permits it. The bytes payload via
  `os.fsencode` is correct on both, and its unit test asserts the encode path
  directly rather than creating the file (source: probe, 2026-08-17).
- Technical: measured baselines for the boundary lint and its suite are recorded
  in `notes/lint-inventory.md § Baseline evidence`, which is the single canonical
  home; the suite passes in 306.4 s reporting 82 cases (source: isolated-worktree
  run at `63c71012`, 2026-08-17).
- Technical: `case_pack_tests_stay_in_pack` walks with a raw `os.walk` rather than
  `_walk`, so it deliberately does **not** ignore-filter; `_test_basenames` has no
  production caller (source: `tools/lint-pack-test-boundary.py:763`, `:855`, and a
  callers grep).
- Technical: `_runner_lines()` is called from two checks and appends its own
  failures, so one missing runner file yields two findings today (source:
  `tools/lint-pack-test-boundary.py:942,969,999,1029`).
- Technical: `tools/lint-mypy.py` targets only two `packages/` trees, so it
  type-checks nothing in this diff (source: `tools/lint-mypy.py:19-22`).
- Process: `docs/specs/pack-test-boundary-remaining-packs/plan.md:636` already
  specified "batch paths over stdin rather than one subprocess per file"; only its
  `--` terminator clause shipped. This spec completes the unimplemented half and
  supersedes the literal wording of that spec's `AC10a` (source: that spec and
  plan, read 2026-08-17).
- Process: `tools/lint-ci-parity.py` already pairs a `--root` option with
  fixture-root self-tests plus one real-root end-to-end launch, so the target
  architecture follows an existing repository precedent (source:
  `tools/lint-ci-parity.py:983`, `tools/test-lint-ci-parity.py:482,505,517`).
- Process: full mode is correct — the structural trigger fires (new shared module
  and callable API) and the governance trigger fires (the change touches
  governance gates) (source: `work-loop` risk triggers).
- Product: implementation scope is the three files the audit measured as carrying
  a P0 pattern, not a broader sweep (source: user confirmation 2026-08-17).
- Product: exactly one repo-only resolver is built; no portable `agentbundle` or
  shipped-pack resolver is added, because measurement found zero callers needing
  one (source: user confirmation 2026-08-17).
- Product: the two lints' Git-missing behaviour is deliberately **unified** to the
  fail-open policy. This is an authorised divergence from the originating brief's
  instruction to preserve divergent fail-open/fail-closed policies behind an
  option; it was raised before adoption and chosen knowingly. The
  missing-Git-policy parameter is retained and required at every call site so the
  policy stays explicit and the divergence can be re-established without redesign
  (source: user confirmation 2026-08-17).
- Process: this spec registers under initiative `ini-007` (source: user
  confirmation 2026-08-17).
