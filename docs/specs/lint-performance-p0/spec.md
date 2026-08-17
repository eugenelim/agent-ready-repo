# Spec: lint-performance-p0

- **Status:** Implementing <!-- Draft | Approved | Implementing | Shipped | Archived -->
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
byte-for-byte the same verdicts, diagnostics and exit codes as before, but the
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
lint must reproduce them byte-for-byte. This spec therefore does not enumerate
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
- **Comparison:** stdout and stderr are compared **separately** and
  byte-for-byte as **bytes**, together with the exit code. Both streams are
  stored base64-encoded — a str-decoded baseline cannot round-trip a
  surrogate-escaped path in Git's stderr, and the comparison would then pass on
  two streams that differ.
- **Hermeticity:** every staged-lint subprocess and every resolver subprocess
  runs under a scrubbed Git environment — `GIT_CONFIG_NOSYSTEM=1`,
  `GIT_CONFIG_GLOBAL` and `GIT_CONFIG_SYSTEM` pointed at an empty file,
  `GIT_DIR` / `GIT_WORK_TREE` / `GIT_INDEX_FILE` / `GIT_COMMON_DIR` /
  `GIT_CEILING_DIRECTORIES` unset, and fixture repositories initialised with an
  empty `core.excludesFile`. Without this a maintainer's global ignore file
  silently rewrites the contract: with `core.excludesFile` matching `tests/`, a
  fixture's pack test comes back *ignored*, and because the ignored set is
  subtracted and two findings fire on the emptiness of what remains, those
  failures get captured as required **passes**. The same leak is live outside
  capture — Git sets `GIT_DIR` and `GIT_INDEX_FILE` for hook processes, and these
  lints run from a pre-PR hook. Capture additionally asserts identical bytes
  under a deliberately hostile global ignore file.
- **Determinism:** findings are sorted before the compared surface is formed,
  because the walk returns filesystem order. Any message embedding an
  interpreter-version-dependent string is excluded from the compared surface.
  Determinism is verified on the capture host *and* on the CI platform before
  the baseline is adopted — three same-host runs prove neither filesystem order
  nor CPython-minor stability.

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
success and failure path is verified by byte-identical comparison with the
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

- [ ] `notes/lint-inventory.md` records every production lint entry point with
      all ten inventory fields, and every lint self-test with at least the
      five-field self-test schema (self-test, subject, production-CLI launch
      count, fixture model, P0 disposition). Its census is exhaustive for
      `tools/`, `packs/` and `packages/`, including non-Python self-tests, and
      every count in it is measured rather than asserted.
- [ ] Every audited lint is classified as pack/skill-local, catalogue-wide,
      repo-global, or hybrid, per check where a file spans classes.
- [ ] No lint other than the rows marked `CHANGE` is modified. New helper, gate
      and golden-baseline files, and bookkeeping updates, are listed in
      `plan.md` and are not lint changes.

**Golden baseline**

- [ ] A golden harness captures `(stdout, stderr, exit_code)` for the lint read
      from a pinned Git revision, against the real tree and against each staged
      fixture root, comparing the two streams separately, byte-for-byte, as
      bytes, with both stored base64-encoded.
- [ ] The committed baseline records the pinned full 40-hex SHA **and** the
      SHA-256 of the extracted subject blob; the harness verifies both, and the
      `git show` exit code, before writing the staged file, aborting and naming
      any mismatch. Changing either value is an `Ask first` amendment.
- [ ] Regeneration is a separate explicit action that the ordinary test path
      cannot trigger, and a regeneration performed against any subject other than
      the pinned one fails.
- [ ] The real-tree baseline's `ok` lines embed live catalogue counters, so an
      unrelated pack, skill-test directory or exemption change legitimately
      invalidates it. Its regeneration is therefore reviewable as a
      counters-only diff, and a regeneration whose diff is not counters-only is
      treated as a finding rather than a refresh.
- [ ] Every staged-lint and resolver subprocess runs under a scrubbed hermetic
      Git environment, and capture asserts identical bytes under a deliberately
      hostile global ignore file. Without this a maintainer's `core.excludesFile`
      can freeze non-vacuity failures as required passes.
- [ ] Findings are sorted before the compared surface is formed, and any message
      embedding an interpreter-version-dependent string is excluded from that
      surface. Byte-determinism is verified on the CI platform, not only the
      capture host, before the baseline is adopted.
- [ ] The refactored lint is compared by co-staging it **and** the resolver
      module into each fixture root and invoking it with no arguments; `--root`
      is not the comparison path.
- [ ] The refactored lint reproduces every captured baseline byte-for-byte when
      given the real `_NO_RUNNER` map, including the real-tree baseline.
- [ ] The three divergences and the two uncaptured roots documented in
      [§ Golden baseline](#golden-baseline) are the only permitted differences;
      any other difference fails the comparison. The two uncaptured refusals are
      proven instead by direct assertion on the CLI's exit code and relativized
      message.
- [ ] The injected-`_NO_RUNNER` semantics are specified and tested on their own:
      a fixture-supplied map produces the stale-exemption and unnamed-suite
      findings against that fixture's own destinations.
- [ ] Fixture roots are `git init`-ed with an empty `core.excludesFile`, so the
      ignore layer resolves rather than degrading to a no-op, and a
      fixture-local `.gitignore` entry is asserted to come back ignored.
- [ ] A fixture shape covers a `tests/` tree whose **only** content is
      gitignored, with an explicit assertion that the empty-test-tree finding
      still fires. This is the one shape that proves the ignored set is still
      subtracted; without it, a refactor that drops ignore filtering reproduces
      every baseline and passes.
- [ ] No fixture builder writes any `.py` into `<fixture>/tools/` other than the
      staged subject and the resolver, asserted before the subject runs —
      staging makes that directory the subject's `sys.path[0]`, so a fixture
      `os.py` or `ast.py` would shadow the standard library.
- [ ] Every fixture link plant's target resolves strictly inside its own fixture
      root, fixture roots live outside the repository worktree, and cleanup never
      follows a link or junction.
- [ ] The golden harness is a standing CI gate in the unfiltered required chain,
      triggered by any change to the lint, the resolver or the harness, with its
      job checking out at full depth so the pinned revision resolves.

**Batched Git-ignore resolver**

- [ ] One repo-only batch resolver lives in a flat module under `tools/` (no new
      importable package), and is the only approved home for direct
      `git check-ignore` subprocess construction in production lint code.
- [ ] Portable `agentbundle` and shipped pack/skill code import no repo-only
      `tools/` helper, and no portable or shipped-pack resolver is added —
      verified by extending the source gate to flag `import tools` / `from tools`
      under `packages/` and `packs/`, not merely asserted.
- [ ] Candidates may be absolute-under-root or root-relative, and results are
      keyed so a caller can test membership with the **exact objects it
      supplied** — asserted for absolute, relative and non-existent candidates.
- [ ] Containment is decided by **lexical** comparison against the canonical
      root, not by `resolve()`, so a symlinked path cannot raise instead of
      producing the symlink finding the lint owes. A candidate outside the root
      raises `ValueError` naming the path, and each call site converts that into
      a named finding or a diagnosed non-zero exit — never a traceback.
- [ ] A candidate whose root-relative form begins with `:` is rejected at the
      boundary. `git check-ignore --stdin` **does** parse pathspec magic and
      exits 128 with a *partial* echo on magic it does not support, so one such
      candidate would otherwise zero every verdict in the batch.
- [ ] The resolver deduplicates candidates before invoking Git and returns a
      deterministically sorted sequence, stable across processes.
- [ ] An empty candidate set launches **zero** `git check-ignore` processes; a
      non-empty set launches **exactly one**, verified for hundreds of
      candidates.
- [ ] Candidates are delivered over stdin, never argv, NUL-delimited, in a
      single `communicate()`-backed call whose bounded timeout covers the whole
      batch — asserted with a payload larger than the OS pipe buffer, so a
      `Popen`+`write`+`wait` shape that could deadlock cannot pass.
- [ ] The payload is built with `os.fsencode` and parsed with `os.fsdecode`, so
      a filename that is not valid UTF-8 cannot raise `UnicodeEncodeError`
      outside the policy.
- [ ] Spaces, tabs, newlines, Unicode, leading dashes, and a leading `!`
      round-trip correctly. No `:(literal)` prefix is added — this subcommand
      rejects it.
- [ ] Exit 0 and 1 are normal outcomes. Any other exit, including a nested-Git-root
      fatal, is surfaced as a hard resolver error carrying Git's stderr and
      naming the offending path, **not** routed through the missing-Git policy.
- [ ] The resolver distinguishes "Git ran and nothing is ignored" from "Git was
      absent, errored, or timed out". The missing-Git policy and the timeout are
      both **required** keyword arguments at every call site.
- [ ] `--no-index` is not introduced, so tracked files remain excluded from the
      ignored set exactly as before.
- [ ] The resolver uses no shell, prints nothing, and returns structured data.
- [ ] Any Git stderr the resolver carries is relativized against the canonical
      root and length-bounded before a call site prints or records it — Git's
      fatal messages embed absolute paths, and the stderr stream is both
      byte-compared and committed.

**Ignore-degradation safety**

- [ ] Both call sites surface a degraded resolution with a diagnostic naming Git
      unavailability, and neither reports an ignore-derived verdict from an
      unresolved ignore layer. This is load-bearing rather than cosmetic:
      `_walk` *subtracts* the ignored set, and at least two existing findings
      fire on the *emptiness* of what remains, so an empty ignored set converts
      those failures into passes. Git absence already behaves this way today,
      but the bounded timeout introduced here is a new route to it.

**Source-level enforcement**

- [ ] An AST-aware gate enumerates **tracked** files (`git ls-files`) rather
      than the filesystem, so an editable install or build residue cannot enter
      or drift the scanned set.
- [ ] It fails when `check-ignore` appears anywhere in a resolved argv sequence
      — not only at position 1 — or in a shell-string, `os.system` or
      `os.popen` construction.
- [ ] A scanned file it cannot read, decode or parse **fails** the gate naming
      the path; it is never silently skipped.
- [ ] Exemptions are an explicit allowlist of individual files, each with a
      recorded reason — not a filename pattern. A pattern would exempt
      `tools/test-*.py`, and in this repository those files *are* CI gates. The
      allowlist names at minimum `tools/test-run-pack-evals.py` (asserts a real
      `.gitignore` fact on a single path) and, for the non-Python textual half,
      `tools/test-pre-pr.sh` (documents the probe path in a comment).
- [ ] The approved helper is present in the scanned inventory and exempted
      there, and the scanned file count is asserted against a floor recorded in
      the audit note. That floor is measured under the **allowlist** rule, not a
      filename pattern — the two differ by more than a factor of two.
- [ ] The non-Python surface (`.sh`, `Makefile`, workflow `run:` blocks) is
      either covered by an equivalent textual search or recorded in the audit
      note as a knowingly accepted gap.
- [ ] Both new gates run in CI on a pull request that touches **only** a
      `tools/` or `packages/` Python file. A step behind a `paths:` filter that
      does not cover the tree it scans does not satisfy this.

**`lint-pack-test-boundary` architecture**

- [ ] The lint exposes an explicit context and structured findings; no
      production check depends on module-global mutable execution state, and the
      former `FAILURES` global is gone.
- [ ] The context carries everything a fixture run needs — including the
      `_NO_RUNNER` map and the packs root — so no check reads a module global,
      and the import-time `packs/` guard no longer fires against the real root
      when the module is loaded for a fixture run.
- [ ] One immutable inventory is constructed per invocation and all six checks
      read it. Data no production check consumes is not in it.
- [ ] Runner files are read and parsed exactly once per invocation and the
      destination inventory is built exactly once — with the golden comparison,
      not a hand-written count, proving no finding was lost or duplicated.
- [ ] The batched ignored-set is applied only where the current lint applies it.
      At least one check deliberately does not ignore-filter, and a case asserts
      a gitignored pack test that climbs above its pack still fails.
- [ ] Tree-confinement results are memoised per invocation, keyed by the
      **lexically normalised unresolved** base path, so a symlinked base and its
      real target never share an entry — asserted in **both** scan orders. A
      resolution error caches a refusal; a key-computation error yields a
      refusal without caching.
- [ ] Neither the inventory nor the confinement cache is persisted or reused
      across invocations.
- [ ] A side-effect-free callable API returns structured findings in
      deterministic order, parses no arguments, calls no `sys.exit`, prints
      nothing, and mutates no file. It exposes the per-check summary data the
      CLI's `ok` lines need, and named seams for inventory construction and
      runner parsing so the structural counts can be instrumented.
- [ ] The no-argument CLI reproduces the real-tree golden baseline exactly.
- [ ] A repeatable `--check <name>` selector accepts the six stable names and an
      explicit `--root` option scopes a run to a fixture catalogue.
- [ ] An unrecognised `--check` name, or a selection resolving to zero checks,
      exits non-zero naming the accepted set — from the CLI and as a
      `ValueError` from the callable API.
- [ ] A targeted or fixture-scoped run names which checks ran and does not print
      the six-check terminal pass line.
- [ ] `--root` is canonicalised once, with `(OSError, RuntimeError)` yielding a
      non-zero exit naming the path; a symlinked or junctioned root is refused;
      every derived path and comparison uses that canonical form; and the
      canonical form is what the resolver receives as its repo root.
- [ ] A root missing `packs/` **or** the self-host recipe is refused by the
      **CLI** before traversal. The callable API accepts such a context so the
      non-vacuity refusals remain reachable and testable.
- [ ] Every non-vacuity refusal has a case. Several are mutually exclusive
      within one invocation because their checks return early, so each gets its
      own fixture shape rather than sharing one "empty root".

**`lint-agents-md`**

- [ ] It resolves its three session-scratch gitignore probes in **exactly one**
      `check-ignore` process.
- [ ] A gitignored probe produces no note; a non-ignored probe produces the
      existing note naming that probe, with existing wording and existing fatal
      semantics.
- [ ] With Git absent, erroring or timing out it exits 1 **and** names Git
      unavailability — not three notes claiming `.gitignore` drifted, which
      would misdiagnose a real degradation — and raises no traceback.
- [ ] Its three existing block self-tests, the aggregator-extraction anchor in
      `tools/test-lint-ci-parity.py`, and `tools/test-pre-pr.sh` (whose sandbox
      is a real Git repository specifically so this probe path can run, and
      which asserts on the agents-md gate failing) all still pass.

**Falsification suite**

- [ ] Pure semantic behaviour is asserted in-process without launching the
      production CLI, and no currently-asserted matcher or path-provenance shape
      is removed.
- [ ] Each planted case runs against a small temporary fixture catalogue,
      invoking only the check or checks that case targets.
- [ ] The suite performs no mutation of the real `Makefile`, workflows, recipes,
      pack trees or projected trees for cases that exercise only a parser or a
      single policy decision — asserted by hashing those paths before and after.
- [ ] The real-tree controls C1 and C2's precondition in
      [§ Real-tree controls](#real-tree-controls) stay on the real tree.
- [ ] A minimal real-tree layer proves the four wiring outcomes in Testing
      Strategy, with its production-CLI launch count recorded and bounded. That
      bound applies to real-tree launches; fixture-root launches carry their own
      recorded bound.
- [ ] Every real-tree plant has `try`/`finally` cleanup and refuses to run when
      its target already exists.
- [ ] Every planted violation proves all four falsification properties.
- [ ] The suite reports no fewer cases than the measured pre-change count
      recorded in the audit note, **and** a mechanically-derived check asserts
      every finding-emission site in the refactored lint is reached by at least
      one case. A case count is not coverage.

**Preserved gates and governance**

- [ ] `agentbundle catalogue lint`, `catalogue lint --deep` and
      `catalogue verify` keep their catalogue-wide default scope and wording.
- [ ] `tools/catalogue/pre_pr_catalogue.py` keeps its fail-fast behaviour,
      failure labels, stream forwarding, verification-first ordering, and its
      adopter-facing vs catalogue-only distinction, and still runs distinct lints
      as separate processes.
- [ ] No terminal catalogue or CI gate becomes diff-aware, and coverage is not
      narrowed.
- [ ] A new ADR records the argv-terminator → stdin-batching reversal. The
      superseded spec and its plan are annotated **only** in their `Status`
      fields, pointing at that ADR, per
      `docs/CONVENTIONS.md § Superseding a frozen document` — no body edit.
- [ ] Source-of-truth files, projected files, tests and documentation are
      synchronised per repository policy.

**Measured outcome**

- [ ] Before/after evidence is recorded in the audit note for: worktree scans,
      candidate count, `check-ignore` process count, production-CLI launches in
      the falsification suite, repeat parses of shared inputs, and elapsed time
      — all relativized.
- [ ] The production lint launches exactly one `check-ignore` process, down from
      the measured baseline.
- [ ] The complete optimised falsification suite exits 0 and completes within
      the five-minute inner-loop budget, with its wall clock recorded against
      the measured baseline.
- [ ] No millisecond-level wall-clock threshold is asserted in CI.

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
