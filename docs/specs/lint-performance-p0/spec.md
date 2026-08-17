# Spec: lint-performance-p0

- **Status:** Shipped <!-- Draft | Approved | Implementing | Shipped | Archived -->
- **Owner:** eugenelim
- **Plan:** [`plan.md`](plan.md)
- **Constrained by:** ADR-0071 (`evals/` is skill-local runtime content); ADR-0075 (test ownership and homes — this spec adds four `tools/` suites and one committed baseline file); `guides/_shared/reference/catalogue-authoring-standards.md` § 4 (cross-pack behaviour is not pack-owned)
- **Brief:** none
- **Discovery:** none
- **Contract:** none <!-- no external interface surface; the callable lint APIs are internal repo-tooling seams -->
- **Shape:** service

> **Spec contract:** this document defines what "done" means. The implementing
> PR must match this spec, or update it. Verification must be derivable from it.

**Audit:** [`notes/lint-inventory.md`](notes/lint-inventory.md) is the scope
contract and the single canonical home for every before/after figure and count.
A lint may be changed **only** if its row says `CHANGE`. No figure or census
count is restated in this document.

## Objective

The repository's lint system runs fast enough to sit inside the work-loop's
five-minute inner loop, and no lint contract is weaker for it. The user is an
agent or engineer running the lint gates repeatedly while iterating: they get
the same verdicts, diagnostics and exit codes as before — identical bytes for any
given repository state — but the
catalogue's runtime-boundary lint completes in seconds instead of tens of
seconds, and its falsification suite completes comfortably inside the budget
instead of sitting on the cutoff.

Three properties deliver that. **Ignore decisions are batched:** no production
lint asks Git about one path at a time; a lint needing Git-ignore semantics
sends its whole candidate set through one resolver call, which launches at most
one `git check-ignore` process and none for an empty candidate set. **One
inventory per invocation:** the runtime-boundary lint builds its pack,
projection, runner, destination and ignore data once and all six checks read
that one inventory. **Falsification is fixture-scoped:** each planted violation
is proven against a small temporary catalogue, with a minimal real-tree layer
retained to prove the production CLI is wired to the real catalogue.

**Behaviour preservation is proven by capture, not by description.** Before any
refactor, the current lint's exact stdout, stderr and exit code are captured
against the real tree and against a set of staged fixture catalogues. Those
captured baselines *are* the preserved-behaviour contract, and the refactored
lint must reproduce their canonical surface — raw streams stored, four named
normalisation classes applied to both sides before comparison
([§ Golden baseline](#golden-baseline) enumerates them). This spec therefore does not enumerate
failure strings, failure counts, or check attributions in prose — an enumeration
maintained by hand is a second implementation of the lint, and it drifts.

## Boundaries

*Always do* applies without asking; *Ask first* requires human sign-off before
proceeding; *Never do* is a hard rule, even under time pressure.

### Always do

- Change a lint only when its row in [`notes/lint-inventory.md`](notes/lint-inventory.md)
  says `CHANGE`.
- Capture the golden baseline from the **unmodified** lint before changing it,
  and make it regenerable from a pinned Git revision rather than from the
  working tree, so it stays reproducible after the refactor lands.
- Preserve fail-closed behaviour: symlink refusal, junction refusal,
  resolution-error refusal, lexical `..` traversal refusal, dynamic-path
  refusal, and every non-vacuity refusal. The golden baseline is what proves it.
- Pass candidate paths to Git over **stdin**, NUL-delimited, as bytes, with an
  explicit bounded timeout, no shell.
- Give every real-worktree plant a `try`/`finally` cleanup guarantee, and make
  it refuse to run when its target already exists.
- Keep the callable check API side-effect-free: no argument parsing, no
  `sys.exit`, no printing, no repository mutation.
- Relativize every recorded diagnostic and evidence figure to the repository
  root before committing it (`AGENTS.md` § Privacy).

### Ask first

- Adding a scoping option to a check whose correctness needs peer catalogue
  state.
- Any change that makes the refactored lint's output differ from the captured
  golden baseline. A required difference is a spec amendment, recorded with the
  reason and the new expected bytes — never a silently rebaselined golden file.
- Removing or weakening any existing falsification assertion, including the two
  real-tree non-vacuity controls in
  [§ Real-tree controls](#real-tree-controls).
- Changing which paths a lint treats as authored versus generated.
- Changing the default terminal behaviour of `agentbundle catalogue lint`,
  `catalogue lint --deep`, `catalogue verify`,
  `tools/catalogue/pre_pr_catalogue.py`, `make pre-pr`, `make build-check`, or
  any CI lint job.
- Widening `tools/lint-mypy.py`'s target list to cover `tools/`.

### Never do

- **Never add a new runtime dependency, importable package under `tools/`, or
  top-level directory.** No third-party pathspec or Git library, no daemon, no
  MCP requirement, no control plane, no `uv` requirement, no persistent scan
  service, no SQLite or on-disk lint cache, no `pytest-xdist` or automatic test
  parallelism.
- Never make a shipped pack or skill lint import a repo-only `tools/` helper,
  and never make portable `agentbundle` code import repo-only `tools/`.
- Never launch one `git check-ignore` process per candidate path from any
  production lint.
- Never persist an inventory or a confinement-scan cache across lint processes,
  and never reuse either across invocations.
- Never make a terminal catalogue or CI gate diff-aware, changed-pack-only or
  changed-file-only.
- Never let a targeted or fixture-scoped run print the complete six-check
  terminal pass line. (A fixture run legitimately produces zero findings and
  exit 0 — that is a negative case, not a masquerade; what must not appear is
  the six-check wording.)
- Never regenerate a golden baseline to make a failing comparison pass.
- Never raise the work-loop time budget, widen a timeout, or move unbounded work
  into CI as the fix.
- Never edit a gate, test or assertion to make a failure go away.

## Golden baseline

The captured contract. One harness stages a **copy of the lint** into a root and
records the resulting `(stdout, stderr, exit_code)` triple.

- **Capture subject:** the lint as of a pinned revision, read from Git
  (`git show <sha>:tools/lint-pack-test-boundary.py`), never from the working
  tree.
- **Subject integrity:** the pin is a literal full 40-hex commit SHA stored in
  the committed baseline alongside the SHA-256 of the extracted blob. The harness
  verifies **both** before writing the staged file, and verifies the `git show`
  exit code — a shallow clone returns 128 with empty stdout, which must abort
  rather than stage and execute an empty subject. Changing either value is an
  `Ask first` amendment, because repointing the pin at the post-refactor commit
  would make the baseline describe the very code it polices.
- **Why staging works:** the lint derives its root from its own `__file__`, so
  copying it into `<fixture>/tools/` makes `<fixture>` its root.
- **Comparison drive:** the **refactored** lint is compared by co-staging it and
  the resolver module into each fixture root and invoking it with **no
  arguments**. `--root` is deliberately **not** the comparison path: a
  fixture-scoped run prints a partial-run header by design, so it could never
  match a staged baseline.
- **Comparison:** stdout and stderr are stored **raw**, base64-encoded, and
  compared **separately** — never merged — together with the exit code. Raw
  storage is what keeps the baseline honest: a str-decoded baseline cannot
  round-trip a surrogate-escaped path in Git's stderr, and the comparison would
  then pass on two streams that differ.
  What is compared is not the raw bytes but a **canonical surface** derived from
  them. This list is the complete inventory of what `_canonical` normalises, and it
  is normative: a change to that function that is not reflected here is a spec
  violation, not a documentation lag. An earlier draft claimed "exactly four
  classes — nothing else is normalised" and was wrong on two counts, which is why
  the list is now enumerated operation by operation rather than summarised.
  1. **Ambient repository state is redacted** — findings a fixture cannot cause:
     those derived from the real `_NO_RUNNER` map, and runner-inventory misses
     naming files no fixture creates. The acceptance criterion below states the
     mechanism and its one recorded limit.
  2. **The failure tally is adjusted down by exactly the number of lines
     redacted** — not erased, so a double-appended finding stays visible.
  3. **Interpreter-dependent tails are elided on a block's head line** — any
     message embedding a CPython-version string. Head only, which is where both
     such messages appear today; a future multi-line variant would reintroduce
     CPython churn into the surface and would need this widened.
  4. **Order between findings** — `FAIL:` blocks are sorted among themselves,
     because two checks can both contribute and accumulation order must not matter.
  4b. **Order between finding and non-finding blocks** — every `FAIL:` block is
     emitted before every non-`FAIL:` block, whatever order they were printed in.
     A no-op today, because stdout carries the `ok`/`✓` lines and stderr the
     `FAIL`/`✖` ones and the two streams are compared separately; recorded because
     the surface performs it regardless, which is the same standard class 6 is held
     to.
  5. **Order within a finding** — a finding's indented path list is sorted,
     separately from (4), because the walk returns filesystem order. These are two
     distinct normalisations with two distinct reasons; merging them is how the
     earlier draft lost one.
  6. **Position within a finding** — indented path lines are hoisted above
     unindented hint lines. A no-op on today's baselines, where every emitted path
     already precedes its hint, and recorded because it is a normalisation the
     surface performs whether or not it currently changes anything.
  7. **Whitespace** — blank tail lines are dropped, blocks holding only blanks are
     dropped, and the surface is `strip()`ped with one trailing newline. This is
     what stops a redaction from surfacing as a whitespace-only difference.
  How each class is held, stated exactly — an earlier draft of this sentence
  claimed assertion coverage for classes it did not have, and the mutations that
  disproved it are the reason the list below distinguishes three kinds of support
  rather than two:
  - **Mutation-proven** (removing the behaviour reddens a suite): classes 1, 2, 4,
    4b, 5, 6, and the blank-*tail* drop in 7.
  - **Corpus-present but not same-host provable**: class 3. Two baselines
    (`malformed-runner-file`, `pack-test-unparseable`) do carry an
    interpreter-dependent message, but removing the elision leaves *both* sides of
    the comparison equally un-elided, so it stays green on one host. Its purpose is
    stability across CPython minors, which only a second interpreter demonstrates —
    hence the cross-platform determinism check below rather than a mutation.
  - **Redundant, kept defensively**: the blank-only-*block* drop and the final
    `strip()` in class 7. Both are unreachable once blank tails are dropped, and a
    mutation removing either stays green. They are retained because the redaction
    that feeds them deletes whole lines, and cheap belt-and-braces at that seam is
    worth more than the line count it costs — but they are not evidence of
    anything and are recorded here as such.
- **Hermeticity:** every staged-lint subprocess and every resolver subprocess
  runs through one helper, `hermetic_git_env`, which does two things — and both
  halves matter, because an earlier draft of this bullet described only the first
  and got one variable backwards.
  It **removes** every name in `_LEAKING_GIT_VARS` (13 of them): `GIT_DIR`,
  `GIT_WORK_TREE`, `GIT_INDEX_FILE`, `GIT_COMMON_DIR`, `GIT_OBJECT_DIRECTORY`,
  `GIT_ALTERNATE_OBJECT_DIRECTORIES`, `GIT_CONFIG`, `GIT_CONFIG_COUNT` (with its
  `GIT_CONFIG_KEY_n` / `GIT_CONFIG_VALUE_n` pairs), `GIT_CONFIG_PARAMETERS`, and
  the four pathspec vars `GIT_GLOB_PATHSPECS` / `GIT_ICASE_PATHSPECS` /
  `GIT_LITERAL_PATHSPECS` / `GIT_NOGLOB_PATHSPECS`.
  It **sets** eight variables (six when handed `repo_root=None`, the
  root-discovery branch, which sets no ceiling of its own):
  `GIT_CONFIG_NOSYSTEM=1`, `GIT_CONFIG_GLOBAL` and `GIT_CONFIG_SYSTEM` to
  `/dev/null`, and — load-bearing, and absent from the earlier draft —
  `GIT_CONFIG_COUNT=1` with
  `GIT_CONFIG_KEY_0=core.excludesFile` and `GIT_CONFIG_VALUE_0=/dev/null`.
  Pinning `core.excludesFile` is not belt-and-braces: leaving it *unset* is
  exactly what opens Git's `$XDG_CONFIG_HOME/git/ignore` → `~/.config/git/ignore`
  fallback, so dropping the config vars without pinning the key would still read a
  maintainer's personal ignore file.
  `GIT_CEILING_DIRECTORIES` is **set** to the root the helper is handed — the
  *fixture* root during capture, which is the point of fencing there — together
  with `GIT_DISCOVERY_ACROSS_FILESYSTEM=0`. An earlier draft unset the ceiling
  along with the rest, which *widened* discovery rather than fencing it. Scrubbing
  is not the goal; bounding what Git may find is.
  Two of the removed names are the dangerous ones. `GIT_CONFIG_COUNT` and the
  higher-precedence `GIT_CONFIG_PARAMETERS` survive `GIT_CONFIG_NOSYSTEM` and the
  redirected config files, and they leak **silently** — verified: with
  `core.excludesFile` pointed at a hostile file, `check-ignore --stdin -z` reports
  extra paths ignored and exits **0**. The pathspec vars fail closed instead
  (exit 128 → `GitIgnoreError`), which is why they were never the risk.
  Without all of this a maintainer's global ignore file silently rewrites the
  contract: with `core.excludesFile` matching `tests/`, a fixture's pack test comes
  back *ignored*, and because the ignored set is subtracted and two findings fire
  on the emptiness of what remains, those failures get captured as required
  **passes**. The leak is live outside capture too — Git sets `GIT_DIR` and
  `GIT_INDEX_FILE` for hook processes, and these lints run from a pre-PR hook.
  Capture additionally asserts identical bytes under a deliberately hostile global
  ignore file, and fixture repositories are separately initialised with an empty
  `core.excludesFile` via `git config` — a different mechanism from the env pin,
  belt to its braces.
- **Determinism:** the seven normalisation classes above are what make the surface
  reproducible; this bullet does not restate them. Determinism is verified on the
  capture host *and* on the CI platform before the baseline is adopted — three
  same-host runs prove neither filesystem order nor CPython-minor stability.

### What capture cannot observe

The triple is blind to exactly three things. Each has its own criterion, so the
sufficiency of this approach is checkable rather than assumed:

| Not observable in the triple | Proven instead by |
| --- | --- |
| Git subprocess count | the structural process-count criterion, at an instrumented seam |
| inventory / runner-parse count | the one-per-invocation criteria, at named seams |
| filesystem side effects | the callable-API "mutates no file" criterion, plus the suite hashing the real `Makefile`, workflows, recipes and projected trees before and after |

It *does* observe failure count and attribution, because findings print as
`FAIL:` lines plus an `✖ … N failure(s)` summary — so behaviours like one cause
producing two findings are captured automatically, with no hand-written count.
Redaction preserves this rather than costing it: the tally is adjusted **down by
exactly the number of lines redacted**, not erased, and the lint emits one `FAIL:`
line per finding followed by `len(findings)`, so the subtraction is exact. Erasing
it would have discarded the one signal the compared surface has to keep — a
finding appended twice but printed once, which is precisely what the memoised
runner parse in divergence 2 below could regress into.

### Deliberate divergences

Exactly three, recorded here rather than discovered during comparison:

1. **`_NO_RUNNER` becomes injectable.** The map is a module constant of real
   repository paths, so the unmodified lint against any fixture root emits a
   stale-exemption finding per entry. The baseline binds the refactored lint
   **given the real map** (which covers the real tree); injected-map behaviour is
   new specified behaviour with its own criteria and tests.
2. **Runner-parse findings are re-emitted, not re-parsed.** The runner reader
   appends its own findings and is reached by two checks, so one missing or
   malformed runner file produces **two** findings today. Parsing once must not
   delete them: the memoised parse returns its findings alongside its lines, and
   each consuming check re-appends them. The doubled emission is preserved
   behaviour; only the parse is deduplicated.
3. **Degradation becomes fatal.** Unobservable in the baselines only because no
   fixture is captured Git-less.

**Two roots are deliberately not captured.** A root without `packs/` and a root
without the recipe both trip an import-time refusal whose message embeds an
**absolute** path, so their bytes are host-dependent and unreproducible. Those
two refusals are proven by direct assertion on the refactored CLI's exit code and
relativized message instead.

### Knowingly preserved but weak

Capture freezes current behaviour, including current weaknesses. These are
preserved deliberately, reviewed at capture time, and are **not** fixed here —
recording them stops a future reader mistaking them for intended design:

- A pack in the self-host include list whose entire `.apm/skills/` directory is
  missing is skipped before the "nothing was projected" guard, so it passes
  silently — while a pack whose skills exist but stop being projected fails. An
  asymmetric fail-open.
- The source-confinement analysis parses a lossy decode of the test source
  rather than the bytes the interpreter would execute. The failure directions
  land fail-closed (mangling yields a syntax error, which is reported), but the
  divergence is now contract.

## Real-tree controls

Two assertions must stay on the **real tree**, because their whole purpose is to
detect that the real tree has drifted. A fixture makes them trivially true and
they stop proving anything:

- **C1 — the collision fixture still collides.** `markdown-to-docx` and
  `markdown-to-pptx` still share a test basename; if the overlap ever vanishes,
  the runner-isolation guard stops proving anything.
- **C2's precondition — the non-colliding pair is still non-colliding.**
  `adapt-to-project` and `flow-metrics` share **no** test basename and **no**
  subject basename. Only C2's second half — that a runner spanning them fails
  and names both suites — may move to a fixture.

## Testing Strategy

**Batched ignore resolution — TDD.** The resolver is the one piece of genuinely
new logic: a function over (repo root, candidates, missing-Git policy) with a
compressible invariant — an ignored subset plus a bounded process count. Its
edge cases are enumerable and cheap to assert in-process, so prose is the right
tool here and the criteria below are explicit. Tests precede implementation.

**Behaviour preservation — TDD against a captured baseline.** Every existing
success and failure path is verified by canonical-surface comparison with the
golden baseline rather than by a hand-written expectation. This is deliberate:
the previous draft of this spec enumerated 22 failure strings with sites,
counts, and check attributions, and review found that enumeration wrong in a new
place on each pass. Capture removes the class of error.

**Structural process, inventory and traversal properties — TDD at the
integration surface.** "One invocation launches at most one `check-ignore`
process", "one inventory construction", "runner files parsed once" are
invariants about a whole invocation, asserted by instrumenting the lint's real
seams and running a complete invocation. Source-string matching cannot see a
call added through an alias.

**Source-level enforcement of the batching rule — goal-based check.** A property
of the source tree, verified by an AST walk over tracked files. It complements —
never replaces — the structural process-count assertions above, and is
documented as a drift guard: an AST allowlist cannot close obfuscated argv
construction, so the runtime process count carries the strong property.

**Falsification integrity — TDD.** For each planted violation: the lint fails,
the failure names the plant or its policy, the failure comes from the intended
check, and removal restores a passing verdict. Attribution is the load-bearing
half — a plant that fails for the wrong reason is a guard nobody has checked.

**Production CLI wiring — TDD at the end-to-end surface.** A minimal real-tree
layer inside the automated suite drives the real built CLI: the clean tree
passes, one runtime-boundary plant is caught and named, one runner-or-linked-tree
plant is caught and named, and cleanup restores a passing tree. Automated, not
manual QA — the observable is the CLI's exit code and streams, asserted in-suite.

**Terminal gate preservation — goal-based check.** Each affected gate is run
once and asserted to pass with unchanged terminal wording.

**Performance — goal-based check, evidence only.** Before/after counts and one
bounded wall-clock sample are recorded in the audit note. The structural counts
are the normative assertions; no millisecond threshold is asserted in CI.

**Not covered.** `tools/lint-mypy.py` targets only two `packages/` trees, so it
type-checks nothing in this diff and is not claimed as a gate for it.

## Acceptance Criteria

**Audit and scope**

- [x] `notes/lint-inventory.md` records every production lint entry point with
      all ten inventory fields, and every lint self-test with at least the
      five-field self-test schema (self-test, subject, production-CLI launch
      count, fixture model, P0 disposition). Its census is exhaustive for
      `tools/`, `packs/` and `packages/`, including non-Python self-tests, and
      every count in it is measured rather than asserted.
- [x] Every audited lint is classified as pack/skill-local, catalogue-wide,
      repo-global, or hybrid, per check where a file spans classes.
- [x] No lint other than the rows marked `CHANGE` is modified. New helper, gate
      and golden-baseline files, and bookkeeping updates, are listed in
      `plan.md` and are not lint changes.

**Golden baseline**

- [x] A golden harness captures `(stdout, stderr, exit_code)` for the lint read
      from a pinned Git revision against each staged fixture root, comparing the
      two streams separately — never merged — as bytes, with both stored raw and
      base64-encoded, and comparing the canonical surface derived from them rather
      than the raw bytes.
      **Amended during implementation, with the reason:** the real tree is
      deliberately *not* a captured case, because every line it prints except the
      terminal verdict is ambient — live catalogue counters (`(21 packs)`,
      `(32 destinations, 8 declared unrun)`) that any unrelated PR moves. The
      verdict itself carries no ambient value, which is exactly why it is the line
      the real-tree layer pins byte-exact instead. A
      fixture's output is ambient only where it reads repository-level constants,
      and that much is separable: `_canonical` drops the findings derived from the
      real `_NO_RUNNER` map, so adding an exemption — the routine edit — no longer
      touches any baseline. A real-tree snapshot has no such separable part, so
      the only maintenance move left for it would be regeneration, which trains
      exactly the reflex the `Never do` rail forbids. It is pinned instead by
      direct assertion in the falsification suite's real-tree layer (next
      criterion but three), and no captured fixture reaches that path because
      every fixture exits 1.
- [x] The committed baseline records the pinned full 40-hex SHA **and** the
      SHA-256 of the extracted subject blob; the harness verifies both, and the
      `git show` exit code, before writing the staged file, aborting and naming
      any mismatch. Changing either value is an `Ask first` amendment.
- [x] Regeneration is a separate explicit action that the ordinary test path
      cannot trigger, and a regeneration performed against any subject other than
      the pinned one fails.
- [x] The success path is pinned by direct assertion rather than by a snapshot
      that churns: the clean real tree exits 0, prints the six-check pass line
      byte-exact, prints no partial-run header, and prints all six success lines
      in their documented order. This is **narrower** than a byte snapshot, not
      stronger — it deliberately does not pin the counters inside those lines,
      which is the whole reason it survives an unrelated pack being added. What it
      buys is that the assertion states its subject, so a maintainer reading a
      failure learns which property broke. (Supersedes the counters-only-diff
      criterion, which existed only to manage a real-tree snapshot this spec no
      longer captures.)
- [x] Findings a fixture cannot cause are excluded from the compared surface, so
      an ambient repository edit cannot redden the gate. The pinned subject reads
      `_NO_RUNNER` and `_RUNNER_FILES` from its own frozen text, so a fixture
      inherits one finding per real map entry; those are redacted, along with the
      failure tally that counts them and any blank line a redaction leaves behind.
      The redaction is bounded by assertion, not by inspection: a finding naming a
      runner file the fixture *does* create stays compared; every trusted path is
      one a real `_base_fixture` build actually writes; the trusted set equals the
      working-tree lint's runner inventory; and the tally reads exactly
      `original − redacted`. Each property is proven by a mutation that reddens the
      suite.
      **Recorded limit:** adding a `_RUNNER_FILES` entry is a known re-pin
      trigger. Its added `FAIL: runner file … does not exist` lines *are*
      redacted; what cannot be is the consequence — the missing file makes
      `runners-keep-suites-isolated` fail, so that check's `ok` line **disappears**
      from all 22 baselines, and an absent line is not something a redaction can
      restore. Regeneration cannot clear it either, because regeneration re-runs
      the pinned subject, whose older inventory still passes. Repointing the pin
      is accepted for that case: the repo gains a CI runner rarely, and never
      without review, whereas suites are ungated routinely. A new runner path must
      also be added to `_FIXTURE_RUNNER_FILES` *and* written by `_base_fixture`,
      and if it is an underscore-named `tools/*.py` it additionally needs the
      staged-fixture stray-file guard's carve-out extended — that guard refuses any
      importable module in a staged `tools/` — and it was only the
      routine edit that made the gate something to route around.
- [x] Every staged-lint and resolver subprocess runs under a scrubbed hermetic
      Git environment, and capture asserts identical bytes under a deliberately
      hostile global ignore file. Without this a maintainer's `core.excludesFile`
      can freeze non-vacuity failures as required passes.
- [x] Findings are sorted before the compared surface is formed, and any message
      embedding an interpreter-version-dependent string is excluded from that
      surface. Byte-determinism is verified on the CI platform, not only the
      capture host, before the baseline is adopted.
- [x] The refactored lint is compared by co-staging it **and** the resolver
      module into each fixture root and invoking it with no arguments; `--root`
      is not the comparison path.
- [x] The refactored lint reproduces every captured baseline's canonical surface,
      on both streams and with the same exit code. Raw bytes are what is stored;
      the normalisation classes enumerated in
      [§ Golden baseline](#golden-baseline) are what is compared. That section is
      the single statement of both the list and how each class is supported —
      neither its cardinality nor its coverage level is restated here, because
      restating them is how this criterion twice ended up asserting a count and a
      blanket mutation guarantee that the artifact contradicted.
- [x] The three divergences, the normalisation classes, and the two uncaptured
      roots documented in [§ Golden baseline](#golden-baseline) are the only
      permitted differences; any other difference fails the comparison.
      Naming the normalisation classes here is not bookkeeping — an earlier draft
      of this criterion said "the only permitted difference" while the comparison
      already normalised four things, so the criterion asserted something the
      artifact contradicted. The two uncaptured refusals are
      proven instead by direct assertion on the CLI's exit code and relativized
      message.
- [x] The injected-`_NO_RUNNER` semantics are specified and tested on their own:
      a fixture-supplied map produces the stale-exemption and unnamed-suite
      findings against that fixture's own destinations.
- [x] Fixture roots are `git init`-ed with an empty `core.excludesFile`, so the
      ignore layer resolves rather than degrading to a no-op, and a
      fixture-local `.gitignore` entry is asserted to come back ignored.
- [x] A fixture shape covers a `tests/` tree whose **only** content is
      gitignored, with an explicit assertion that the empty-test-tree finding
      still fires. This is the one shape that proves the ignored set is still
      subtracted; without it, a refactor that drops ignore filtering reproduces
      every baseline and passes.
- [x] No fixture builder writes an importable module or package into
      `<fixture>/tools/` other than the staged subject and the resolver, asserted
      before the subject runs — staging makes that directory the subject's
      `sys.path[0]`, so a fixture `os.py`, `ast.py` or `os/__init__.py` would
      shadow the standard library. `tools/test-all.py` is carved out: it is one of
      the lint's six required runner files, and a hyphenated name is not
      importable, so it cannot shadow anything.
- [x] Every fixture link plant's target resolves strictly inside its own fixture
      root, fixture roots live outside the repository worktree, and cleanup never
      follows a link or junction.
- [x] The golden harness is a standing CI gate in the unfiltered required chain,
      triggered by any change to the lint, the resolver or the harness, with its
      job checking out at full depth so the pinned revision resolves.

**Batched Git-ignore resolver**

- [x] One repo-only batch resolver lives in a flat module under `tools/` (no new
      importable package), and is the only approved home for direct
      `git check-ignore` subprocess construction in production lint code.
- [x] Portable `agentbundle` and shipped pack/skill code import no repo-only
      `tools/` helper, and no portable or shipped-pack resolver is added —
      verified by extending the source gate to flag `import tools` / `from tools`
      under `packages/` and `packs/`, not merely asserted.
- [x] Candidates may be absolute-under-root or root-relative, and results are
      keyed so a caller can test membership with the **exact objects it
      supplied** — asserted for absolute, relative and non-existent candidates.
- [x] Containment is decided by **lexical** comparison against the canonical
      root, not by `resolve()`, so a symlinked path cannot raise instead of
      producing the symlink finding the lint owes. A candidate outside the root
      raises `ValueError` naming the path, and each call site converts that into
      a named finding or a diagnosed non-zero exit — never a traceback.
- [x] A candidate whose root-relative form begins with `:` is rejected at the
      boundary. `git check-ignore --stdin` **does** parse pathspec magic and
      exits 128 with a *partial* echo on magic it does not support, so one such
      candidate would otherwise zero every verdict in the batch.
- [x] The resolver deduplicates candidates before invoking Git and returns a
      deterministically sorted sequence, stable across processes.
- [x] An empty candidate set launches **zero** `git check-ignore` processes; a
      non-empty set launches **exactly one**, verified for hundreds of
      candidates.
- [x] Candidates are delivered over stdin, never argv, NUL-delimited, in a
      single `communicate()`-backed call whose bounded timeout covers the whole
      batch — asserted with a payload larger than the OS pipe buffer, so a
      `Popen`+`write`+`wait` shape that could deadlock cannot pass.
- [x] The payload is built with `os.fsencode` and parsed with `os.fsdecode`, so
      a filename that is not valid UTF-8 cannot raise `UnicodeEncodeError`
      outside the policy.
- [x] Spaces, tabs, newlines, Unicode, leading dashes, and a leading `!`
      round-trip correctly. No `:(literal)` prefix is added — this subcommand
      rejects it.
- [x] Exit 0 and 1 are normal outcomes. Any other exit, including a nested-Git-root
      fatal, is surfaced as a hard resolver error carrying Git's stderr and
      naming the offending path, **not** routed through the missing-Git policy.
- [x] The resolver distinguishes "Git ran and nothing is ignored" from "Git was
      absent, errored, or timed out". The missing-Git policy and the timeout are
      both **required** keyword arguments at every call site.
- [x] `--no-index` is not introduced, so tracked files remain excluded from the
      ignored set exactly as before.
- [x] The resolver uses no shell, prints nothing, and returns structured data.
- [x] Any Git stderr the resolver carries is relativized against the canonical
      root and length-bounded before a call site prints or records it — Git's
      fatal messages embed absolute paths, and the stderr stream is both
      byte-compared and committed.

**Ignore-degradation safety**

- [x] Both call sites surface a degraded resolution with a diagnostic naming Git
      unavailability, and neither reports an ignore-derived verdict from an
      unresolved ignore layer. This is load-bearing rather than cosmetic:
      `_walk` *subtracts* the ignored set, and at least two existing findings
      fire on the *emptiness* of what remains, so an empty ignored set converts
      those failures into passes. Git absence already behaves this way today,
      but the bounded timeout introduced here is a new route to it.

**Source-level enforcement**

- [x] An AST-aware gate enumerates via `git ls-files --cached --others
      --exclude-standard` rather than walking the filesystem, so an editable
      install's vendored content cannot enter or drift the scanned set.
      **Amended during implementation, with the reason:** tracked-only was the
      first attempt and left a hole — an author could add a violating file and
      watch the gate pass right up until they committed it. `--others
      --exclude-standard` adds new-but-not-ignored files while still excluding
      build residue. Proven both ways: an untracked planted offender is caught by
      name, and removing it restores exit 0.
- [x] It fails when `check-ignore` appears anywhere in a resolved argv sequence
      — not only at position 1 — or in a shell-string, `os.system` or
      `os.popen` construction.
- [x] A scanned file it cannot read, decode or parse **fails** the gate naming
      the path; it is never silently skipped.
- [x] Exemptions are an explicit allowlist of individual files, each with a
      recorded reason — not a filename pattern. A pattern would exempt
      `tools/test-*.py`, and in this repository those files *are* CI gates. The
      allowlist names at minimum `tools/test-run-pack-evals.py` (asserts a real
      `.gitignore` fact on a single path) and, for the non-Python textual half,
      `tools/test-pre-pr.sh` (documents the probe path in a comment).
- [x] The approved helper is present in the scanned inventory and exempted
      there, and the scanned file count is asserted against a floor recorded in
      the audit note. That floor is measured under the **allowlist** rule, not a
      filename pattern — the two differ by more than a factor of two.
- [x] The non-Python surface (`.sh`, `Makefile`, workflow `run:` blocks) is
      either covered by an equivalent textual search or recorded in the audit
      note as a knowingly accepted gap.
- [x] Both new gates run in CI on a pull request that touches **only** a
      `tools/` or `packages/` Python file. A step behind a `paths:` filter that
      does not cover the tree it scans does not satisfy this.

**`lint-pack-test-boundary` architecture**

- [x] The lint exposes an explicit context and structured findings; no
      production check depends on module-global mutable execution state, and the
      former `FAILURES` global is gone.
- [x] The context carries everything a fixture run needs — including the
      `_NO_RUNNER` map and the packs root — so no check reads a module global,
      and the import-time `packs/` guard no longer fires against the real root
      when the module is loaded for a fixture run.
- [x] One immutable inventory is constructed per invocation and all six checks
      read it. Data no production check consumes is not in it.
- [x] Runner files are read and parsed exactly once per invocation and the
      destination inventory is built exactly once — with the golden comparison,
      not a hand-written count, proving no finding was lost or duplicated.
- [x] The batched ignored-set is applied only where the current lint applies it.
      At least one check deliberately does not ignore-filter, and a case asserts
      a gitignored pack test that climbs above its pack still fails.
- [x] Tree-confinement results are memoised per invocation, keyed by the
      **lexically normalised unresolved** base path, so a symlinked base and its
      real target never share an entry — asserted in **both** scan orders. A
      resolution error caches a refusal; a key-computation error yields a
      refusal without caching.
- [x] Neither the inventory nor the confinement cache is persisted or reused
      across invocations.
- [x] A side-effect-free callable API returns structured findings in
      deterministic order, parses no arguments, calls no `sys.exit`, prints
      nothing, and mutates no file. It exposes the per-check summary data the
      CLI's `ok` lines need, and named seams for inventory construction and
      runner parsing so the structural counts can be instrumented.
- [x] The no-argument CLI's real-tree output is asserted directly: exit 0, the
      six-check pass line byte-exact, no partial-run header, and all six success
      lines present and in order.
- [x] A repeatable `--check <name>` selector accepts the six stable names and an
      explicit `--root` option scopes a run to a fixture catalogue.
- [x] An unrecognised `--check` name, or a selection resolving to zero checks,
      exits non-zero naming the accepted set — from the CLI and as a
      `ValueError` from the callable API.
- [x] A targeted or fixture-scoped run names which checks ran and does not print
      the six-check terminal pass line.
- [x] `--root` is canonicalised once, with `(OSError, RuntimeError)` yielding a
      non-zero exit naming the path; a symlinked or junctioned root is refused;
      every derived path and comparison uses that canonical form; and the
      canonical form is what the resolver receives as its repo root.
- [x] A root missing `packs/` **or** the self-host recipe is refused by the
      **CLI** before traversal. The callable API accepts such a context so the
      non-vacuity refusals remain reachable and testable.
- [x] Every non-vacuity refusal has a case. Several are mutually exclusive
      within one invocation because their checks return early, so each gets its
      own fixture shape rather than sharing one "empty root".

**`lint-agents-md`**

- [x] It resolves its three session-scratch gitignore probes in **exactly one**
      `check-ignore` process.
- [x] A gitignored probe produces no note; a non-ignored probe produces the
      existing note naming that probe, with existing wording and existing fatal
      semantics.
- [x] With Git absent, erroring or timing out it exits 1 **and** names Git
      unavailability — not three notes claiming `.gitignore` drifted, which
      would misdiagnose a real degradation — and raises no traceback.
- [x] Its three existing block self-tests, the aggregator-extraction anchor in
      `tools/test-lint-ci-parity.py`, and `tools/test-pre-pr.sh` (whose sandbox
      is a real Git repository specifically so this probe path can run, and
      which asserts on the agents-md gate failing) all still pass.

**Falsification suite**

- [x] Pure semantic behaviour is asserted in-process without launching the
      production CLI, and no currently-asserted matcher or path-provenance shape
      is removed.
- [x] Each planted case runs against a small temporary fixture catalogue,
      invoking only the check or checks that case targets.
- [x] The suite performs no mutation of the real `Makefile`, workflows, recipes,
      pack trees or projected trees for cases that exercise only a parser or a
      single policy decision — asserted by hashing those paths before and after.
- [x] The real-tree controls C1 and C2's precondition in
      [§ Real-tree controls](#real-tree-controls) stay on the real tree.
- [x] A minimal real-tree layer proves the four wiring outcomes in Testing
      Strategy, with its production-CLI launch count recorded and bounded. That
      bound applies to real-tree launches; fixture-root launches carry their own
      recorded bound.
- [x] Every real-tree plant has `try`/`finally` cleanup and refuses to run when
      its target already exists.
- [x] Every planted violation proves all four falsification properties.
- [x] The suite reports no fewer cases than the measured pre-change count
      recorded in the audit note, **and** a mechanically-derived check asserts
      every finding-emission site in the refactored lint is reached by at least
      one case. A case count is not coverage.

**Preserved gates and governance**

- [x] `agentbundle catalogue lint`, `catalogue lint --deep` and
      `catalogue verify` keep their catalogue-wide default scope and wording.
- [x] `tools/catalogue/pre_pr_catalogue.py` keeps its fail-fast behaviour,
      failure labels, stream forwarding, verification-first ordering, and its
      adopter-facing vs catalogue-only distinction, and still runs distinct lints
      as separate processes.
- [x] No terminal catalogue or CI gate becomes diff-aware, and coverage is not
      narrowed.
- [x] A new ADR records the argv-terminator → stdin-batching reversal. The
      superseded spec and its plan are annotated **only** in their `Status`
      fields, pointing at that ADR, per
      `docs/CONVENTIONS.md § Superseding a frozen document` — no body edit.
- [x] Source-of-truth files, projected files, tests and documentation are
      synchronised per repository policy.

**Measured outcome**

- [x] Before/after evidence is recorded in the audit note for: worktree scans,
      candidate count, `check-ignore` process count, production-CLI launches in
      the falsification suite, repeat parses of shared inputs, and elapsed time
      — all relativized.
- [x] The production lint launches exactly one `check-ignore` process, down from
      the measured baseline.
- [x] The complete optimised falsification suite exits 0 and completes within
      the five-minute inner-loop budget, with its wall clock recorded against
      the measured baseline.
- [x] No millisecond-level wall-clock threshold is asserted in CI.

## Assumptions

Empirical claims are probe-backed; probes were run on git 2.50.1 (Apple
Git-155), macOS APFS, Python 3.13.13, on 2026-08-17.

- Technical: `git check-ignore --stdin -z` accepts NUL-delimited candidates on
  stdin and echoes only the ignored subset, exiting 0 when at least one path is
  ignored and 1 when none is.
- Technical: it **does** parse pathspec magic. Bare `:x`, `!x`, `:/x` and
  `:(top)x` round-trip verbatim, but `:!x`, `:(exclude)x`, `:(glob)x`,
  `:(icase)x`, `:(literal)x` and `:(attr:…)x` each exit 128 — and a batch
  containing one of them returns a **partial** echo of the candidates processed
  before it. An earlier draft of this spec recorded that no pathspec magic was
  applied; that was generalised from probing only the bare forms and is
  corrected here.
- Technical: an out-of-repo candidate likewise exits 128 with a partial echo.
  An *unregistered* nested repository resolves normally; a registered gitlink is
  what fatals, and this repository contains none.
- Technical: omitting `--no-index` keeps tracked files excluded from the ignored
  set, identical to the current call.
- Technical: keying the confinement memo on `base.resolve()` collapses a symlink
  and its target into one entry — losing the symlink refusal when the target is
  scanned first, and falsely refusing the real tree when the link is scanned
  first. Wrong in both directions and dependent on filesystem iteration order;
  the lexically normalised unresolved path is correct and order-independent.
- Technical: staging a copy of the lint into `<fixture>/tools/` makes
  `<fixture>` its root, so the unmodified lint can be characterised against
  synthetic catalogues. Its output is root-relative, contains no absolute path,
  and is byte-identical across three consecutive runs on both streams — which is
  what makes byte-comparison viable.
- Technical: the unmodified lint run against a fixture root emits one
  stale-exemption finding per real `_NO_RUNNER` entry, confirming the map must
  become injectable.
- Technical: a directory that is not a Git worktree makes `check-ignore` exit
  128, which a fail-open policy would render an empty ignored set — so fixture
  roots must be `git init`-ed or the ignore layer silently no-ops.
- Technical: `_walk` subtracts the ignored set, and existing findings fire on
  the emptiness of what remains, so an empty ignored set converts failures into
  passes rather than being uniformly conservative.
- Technical: macOS APFS refuses to create a filename containing an undecodable
  byte (`Errno 92`), so that case is asserted through the encode path rather
  than on disk; Linux CI permits the on-disk form.
- Technical: `tools/lint-mypy.py` targets only two `packages/` trees, so it
  type-checks nothing in this diff.
- Technical: `.github/workflows/docs.yml` is `paths`-filtered to an explicit file
  allowlist with no `tools/**` or `packages/**` entry, and records in-repo that
  `tools/test-all.py` is run by no workflow; `build-check.yml` has no path
  filter and is the required job.
- Process: `docs/specs/pack-test-boundary-remaining-packs/plan.md` already
  specified batching paths over stdin rather than one subprocess per file; only
  its `--` terminator clause shipped. This spec completes the other half.
- Process: `docs/CONVENTIONS.md § Superseding a frozen document` requires the
  supersession pointer to live in the `Status` field only, to cite an ADR rather
  than a spec, and forbids body edits including appends — so an ADR is a
  required deliverable here.
- Process: `tools/lint-ci-parity.py` already pairs a `--root` option with
  fixture-root self-tests plus one real-root end-to-end launch, so the target
  architecture follows existing repository precedent.
- Process: full mode is correct — the structural trigger fires (new shared module
  and callable API) and the governance trigger fires (the change touches
  governance gates and authors an ADR).
- Product: implementation scope is the lints the audit measured as carrying a P0
  pattern, not a broader sweep (user confirmation 2026-08-17).
- Product: exactly one repo-only resolver is built; no portable or shipped-pack
  resolver, because measurement found zero callers needing one (user
  confirmation 2026-08-17).
- Product: the **resolver's** missing-Git policy is deliberately **unified** to
  `FAIL_OPEN` across both call sites; each call site then treats a degraded
  resolution as **fatal** (diagnose and exit non-zero). The two halves are not in
  tension: the resolver does not raise, and the caller does not proceed. This is an authorised divergence from the originating brief's
  instruction to preserve divergent policies behind an option; it was raised
  before adoption and chosen knowingly. The policy parameter is retained and
  required at every call site so the posture stays explicit (user confirmation
  2026-08-17).
- Product: behaviour preservation is proven by captured baseline rather than by
  a prose enumeration, after two review rounds found a hand-maintained
  enumeration wrong in a new place each pass (user confirmation 2026-08-17).
- Process: this spec registers under initiative `ini-007` (user confirmation
  2026-08-17).
