# Plan: agent-spec-cli (`agentbundle`)

- **Spec:** [`spec.md`](spec.md)
- **Status:** Shipped

> **Plan contract:** this is the implementation strategy. Unlike the spec, this
> document is allowed to change as you learn. When it changes substantially
> (a different approach, not just a re-ordering), note why in the changelog
> at the bottom.

## Approach

Build `packages/agentbundle/` library-first: a thin `argparse` dispatcher
over an `agentbundle` Python package whose modules implement each subcommand
on top of a shared core (config loading, pack discovery, the F-build render
pipeline imported as a sibling library, the path-jail enforcement, and the
Tier-1/2/3 file-safety primitives). The sibling `distribution-adapters` spec
has carved F-build to live under `packages/agentbundle/agentbundle/build/`
(four reference adapters at `agentbundle/build/adapters/{claude_code,kiro,
copilot,codex}.py`); this CLI imports it as a regular Python package — no
`sys.path` tricks, no subprocess to `tools/build/build.py` (that path
remains as a thin shim calling `python -m agentbundle.build`). Land the
shared core first as task T1 (split into T1a/T1b/T1c), the eleven
subcommands then fan out in canonical install-workflow order — each with
`Depends on: T1c`, parallelisable in supervisor mode. After all subcommands
are green, T13 wires up `zipapp` distribution and T14 runs the manual QA
round-trip on a corporate-network sandbox.

## Constraints

- [RFC-0003](../../rfc/0003-spec-and-cli.md) is the source RFC; its F-cli
  enumerates the eleven subcommands and their semantics.
- [RFC-0001](../../rfc/0001-bundle-distribution-by-adapter-spec.md) defines
  the Tier-1/2/3 file-safety contract.
- Sibling spec [`docs/specs/distribution-adapters/spec.md`](../distribution-adapters/spec.md)
  owns the canonical `pack.toml` / `adapter.toml` schemas, the Tier-1/2/3
  contract details, the `.agent-ready-state.toml` schema, the
  `.upstream.<ext>` companion semantics, the six-recipe enumeration, the
  five primitive types (including `command`), and the location of the
  F-build library at `packages/agentbundle/agentbundle/build/`. The CLI
  consumes them; it does not redefine them. **This spec cannot move to
  Approved until `distribution-adapters` is at least Approved** — see Risks.
- Python 3.11+ stdlib only (`tomllib`, `argparse`, `hashlib`, `pathlib`).
  Hard rule from the spec's `Never do`.
- Library-first per RFC-0003 Unresolved Question 3's working assumption,
  resolved by the sibling spec's relocation of F-build into this package.

## Construction tests

Per-task tests carry the bulk of coverage. Cross-cutting work:

**Integration tests:**
- End-to-end brownfield round-trip: `install → adapt → diff → render` against
  `packages/agentbundle/tests/fixtures/brownfield/` (verifies AC #7, #8, #9).
- F-build parity: byte-for-byte diff of `agentbundle render packs/core` vs.
  `make build` output (verifies AC #4).
- **Cross-cutting Tier-1/2/3 invariant test:** one parametrised integration
  test walks every write-capable subcommand (`scaffold`, `install`,
  `render`, `adapt`, `init-state`, `upgrade`, `uninstall`) against a single
  shared fixture; asserts the Tier invariants per command. Fixture includes
  both a `.sh` hook and a `.py` hook to pin extension preservation. Verifies
  AC #5 across the surface.

**Manual verification:**
- Corporate-network sandbox round-trip: `gh release download` → `python
  agentbundle.pyz install --pack core` against a brownfield repo on a host
  that only sees Artifactory + git (verifies AC #11's manual QA tail).
  Recorded in `packages/agentbundle/tests/manual/sandbox-round-trip.md`.

## Tasks

### T1a: Package scaffold + argparse skeleton + version

**Depends on:** none

**Tests:**
- Goal-based check: `python -c "import agentbundle; print(agentbundle.__version__)"`
  exits 0 and prints a version string (verifies AC #2's package shape).
- Goal-based check: `python -c "import agentbundle.build"` exits 0 — proves
  the F-build library (landed by `distribution-adapters` T1a) is importable
  as a regular package from this CLI, no `sys.path` tricks (verifies AC #1's
  library-first import boundary).
- Unit test: `python -m agentbundle --version` prints a value parsed
  **at import time** from the bundled `adapter.toml`'s `[contract] version`
  field. The test reads the on-disk value, imports the package, mutates
  the on-disk `adapter.toml` to a different version, then asserts that
  `--version` still prints the original (import-time) value — proves
  read-at-import, not read-on-every-call (verifies AC #2's parsed-and-pinned
  invariant).

**Approach:**
- Create `packages/agentbundle/{pyproject.toml,agentbundle/__init__.py,tests/}`
  following `packages/_example/` layout; declare zero runtime deps in
  `pyproject.toml`. **Build backend: `setuptools` with PEP 621 metadata;
  no plugins.**
- Add `cli.py` (argparse skeleton with all eleven subcommands registered as
  no-op stubs, in canonical install-workflow order — discovery-first:
  `list-packs`, `list-targets`, `scaffold`, `install`, `validate`, `render`,
  `adapt`, `diff`, `upgrade`, `uninstall`, `init-state`).
- Register a `validate` subcommand stub now (sibling `distribution-adapters`
  fix-pass 2 commits to `validate` being present at T1a).
- Add `version.py` parsing the spec version at import time from the bundled
  canonical `adapter.toml` (`[contract] version`); the CLI version is a
  package-level constant.
- Assert F-build's location: `agentbundle.build` resolves under
  `packages/agentbundle/agentbundle/build/`. If `distribution-adapters` T1a
  hasn't landed the relocation yet, this task blocks on it (escalate, don't
  workaround).

**Done when:** the three tests above pass; `pip install -e .` inside
`packages/agentbundle/` succeeds; `pip list --format=freeze` shows zero
runtime deps (AC #13).

### T1b: Config loader + safety primitives (Tier classifier + path-jail)

**Depends on:** T1a

**Tests:**
- Unit test: `agentbundle.config.load_pack_toml(path)` returns a parsed dict
  for the `core` pack's `pack.toml`; raises a typed error on malformed TOML
  (verifies the config-loading invariant under AC #3's contract).
- Unit test: `agentbundle.config.load_state(path)` round-trips a
  `.agent-ready-state.toml` per the schema documented in the sibling
  `distribution-adapters` spec (Tier-contract / state-file AC).
- Unit test: `agentbundle.safety.classify(path, state)` returns
  `Tier1 | Tier2 | Tier3` for a fixture set covering each tier (verifies
  AC #5's classification primitive against the sibling spec's Tier
  contract).
- Unit test: `agentbundle.safety.write_jailed(root, relpath, content)`
  refuses any `relpath` that resolves outside `root` (e.g. `../../foo`),
  exiting with a typed error; verifies AC #6 (no-writes-outside-root) at
  the primitive level.

**Approach:**
- Add `config.py`: TOML loaders for `pack.toml`, `.agent-ready-state.toml`,
  `.adapt-discovery.toml`, `--values-from`.
- Add `safety.py`: Tier classifier per the sibling spec's contract;
  `.upstream.<ext>` companion writer; content-hash helpers (SHA-256);
  path-jail enforcement (`write_jailed`) fences every write call site in
  later tasks.

**Done when:** the four unit tests pass.

### T1c: `render.py` library wrapper over `agentbundle.build`

**Depends on:** T1b; **also depends on** the sibling
`distribution-adapters` task that lands the F-build render module at its
final path under `agentbundle/build/`.

**Tests:**
- Unit test: `agentbundle.render.render_pack(pack, target)` calls into the
  imported `agentbundle.build` render entry-point and returns the same
  dict-of-bytes that `make build` would produce for the same pack/target
  (verifies the library-first invariant under AC #4).
- Unit test: the adapter list surfaced by `agentbundle.render.list_adapters()`
  matches the registry exposed by `agentbundle.build.adapters` at runtime
  (no baked-in constants).

**Approach:**
- Add `render.py` as a thin wrapper / re-export over `agentbundle.build`'s
  render entry point. The F-build module path resolves at the sibling
  `distribution-adapters` T1c (expected `agentbundle.build.render`); cite
  that task's outcome and import the path it lands. If the sibling lands
  it under a different module name, update this task before T2–T12 land.

**Done when:** both unit tests green; T2–T12 can `from agentbundle.render
import render_pack`.

### T2: `validate` subcommand

**Depends on:** T1c

**Tests:**
- TDD: `agentbundle validate packs/core` exits 0 on a valid fixture pack;
  exits 1 with a one-line stderr reason on a fixture with malformed
  `adapter.toml` (verifies AC #12 happy + sad path, schema portion).
- TDD: `agentbundle validate packs/core` checks recipes against the
  six-recipe enumerated set from the sibling `distribution-adapters` spec
  — a fixture with an unknown recipe type fails with a one-line stderr
  naming the offending recipe.
- TDD: `--strict` runs the conformance fixtures when present and reports
  per-target pass/fail; when fixtures are absent (F-conformance from
  RFC-0003 not yet landed at v1), `--strict` warns on stderr and exits zero
  on the schema portion (verifies AC #12's partial-at-v1 carve-out).
- TDD: a version-mismatch fixture (pack declares `[pack.adapter-contract]
  version = "2.0"`, CLI ships `0.1`) causes `validate` to refuse with a
  stderr line naming both versions; same refusal applies uniformly to
  every other subcommand via the shared core gate (verifies AC #14).

**Approach:**
- Implement `agentbundle.commands.validate.run(args)`; wire it into the
  `cli.py` dispatcher.
- Schema conformance: parse `adapter.toml`, assert required keys per the
  schema documented in the sibling `distribution-adapters` spec; validate
  recipe types against the six-type set.
- Semantic conformance (`--strict`): import conformance fixtures from
  `packages/agentbundle/tests/fixtures/conformance/` when they exist; call
  `render.render_pack`; diff against expected output trees. When fixtures
  are missing (v1 ship state), warn on stderr and skip.
- **Depends on:** F-conformance fixtures from RFC-0003 (deferred to v1.1)
  for full `--strict` mode; v1 ships schema conformance + partial strict.

**Done when:** all four tests green; AC #12 holds in its partial-at-v1
shape.

### T3: `render` subcommand + F-build parity gate

**Depends on:** T1c

**Tests:**
- TDD: `agentbundle render packs/core --output <tmpdir>` writes the expected
  file tree for the `core` pack (per-target), covering all five primitive
  types (`skill`, `agent`, `hook-body`, `hook-wiring`, `command`).
- TDD: hooks under `packs/core/.apm/hooks/*.sh` project as `.sh`; hooks
  under `*.py` project as `.py` (extension preservation under AC #4 and
  the cross-cutting Tier invariant test under AC #5).
- Goal-based: `diff -r <tmpdir>/apm/core <make-build-output>/apm/core` is
  empty (AC #4 — F-build parity).

**Approach:**
- Wire `agentbundle.commands.render.run(args)` to call
  `render.render_pack(pack, target)` and write the result to disk via
  `safety.write_jailed` (path-jail enforcement is non-optional).
- Honour `--output <dir>` (defaults to `dist/<target>/<pack>/`).

**Done when:** parity diff is empty for `core` against current `make build`;
both hook extensions preserved.

### T4: `scaffold` subcommand

**Depends on:** T1c

**Tests:**
- TDD: `agentbundle scaffold --output <tmpdir>` against an empty target
  renders the `core` pack's `seeds/` tree byte-identical to expected.
- TDD: against a target with a pre-existing `AGENTS.md`, `scaffold` leaves
  it untouched and writes `AGENTS.upstream.md` (Tier-2 fast-path; covered
  by the cross-cutting Tier invariant test under AC #5).

**Approach:**
- Iterate the `seeds/` content of installed packs; for each file, classify
  the target path via `safety.classify` and either write (Tier-1 / absent)
  or emit a companion (Tier-2 fast-path), all through `safety.write_jailed`.

**Done when:** both tests green; cross-cutting Tier test (under T15) covers
this command.

### T5: `install` subcommand (constrained-network)

**Depends on:** T1c

**Tests:**
- TDD: `agentbundle install --pack core <fixture-catalogue-uri>` into the
  brownfield fixture leaves all pre-existing files unchanged and produces
  `.upstream.<ext>` companions for every collision (AC #7).
- TDD: after install, `.agent-ready-state.toml` records a SHA-256 hash for
  every Tier-1 path the install wrote, per the schema owned by the sibling
  `distribution-adapters` spec.
- TDD: install pack B into a tree that already has pack A installed; the
  resulting `.agent-ready-state.toml` contains both `[pack.A]` and
  `[pack.B]` tables — existing tables untouched, new table merged (AC #7
  merge clause).
- TDD: catalogue URI grammar — one test row each for:
  - Local relative path (`./catalogues/foo`) — resolved directly; **assert
    no `subprocess` is invoked** (mock-or-trace at `subprocess.run` /
    `subprocess.Popen`, asserting zero invocations).
  - Local absolute path (`/abs/path/to/catalogue`).
  - Git over HTTPS with tag (`git+https://github.com/owner/repo@v1.0`) —
    fetched via `urllib.request` against
    `https://github.com/owner/repo/archive/refs/tags/v1.0.tar.gz`,
    extracted via `tarfile`; assert no `subprocess` invocation.
  - Git over HTTPS with branch (`git+https://github.com/owner/repo@main`)
    — fetched via `.../archive/refs/heads/main.tar.gz`; assert no
    `subprocess` invocation.
  - Git over HTTPS with SHA (`git+https://github.com/owner/repo@deadbeef`)
    — fetched via `.../archive/deadbeef.tar.gz`; assert no `subprocess`
    invocation.
  - Git over HTTPS pointing at unreachable host — exits non-zero with a
    one-line stderr naming the tarball URL the CLI tried to fetch.
  - Git over SSH (`git+ssh://git@github.com:owner/repo`) — exits
    non-zero with stderr "SSH git URLs deferred to v1.1; use https or
    local path." (Deferred at v1 per Option A.)
- TDD: a malicious fixture pack whose projection rule resolves to
  `../../malicious` is refused with exit non-zero (cross-cutting AC #6
  no-writes-outside-root).

**Approach:**
- Resolve the catalogue URI to a local pack directory:
  - Local paths: used directly.
  - `git+https://github.com/<owner>/<repo>[@<ref>]`: parse with `urllib`;
    construct the GitHub archive URL
    (`https://github.com/<owner>/<repo>/archive/refs/tags/<ref>.tar.gz`
    for tags, `…/archive/refs/heads/<ref>.tar.gz` for branches,
    `…/archive/<ref>.tar.gz` for commit SHAs — disambiguate by trying
    tag first, then branch, then SHA, with a small retry budget); fetch
    via `urllib.request`; extract via `tarfile` into a tempdir.
  - `git+ssh://...`: refuse with the v1.1-deferral message.
  - No `subprocess` invocation in any `install` path.
- For each file in the pack's projection, apply the Tier-1/2/3 contract via
  `safety.classify`; write hashes to `.agent-ready-state.toml` atomically
  (tmp-file + `os.replace`); merge into existing tables rather than
  overwriting.

**Done when:** all five test rows green; AC #7 holds (no-clobber + merge);
state file is valid TOML.

### T6: `adapt` subcommand

**Depends on:** T1c, T5

**Tests:**
- TDD: against a fixture with `<adapt:PROJECT_NAME>` markers, `adapt
  --values-from values.toml` substitutes every marker (AC #8). The CLI is
  the resolver for adopter installs per the sibling spec's carve-out.
- TDD: for every `.upstream.<ext>` companion in the fixture, the resulting
  `.adapt-pending.md` lists the companion path and a one-line diff summary
  (AC #8).
- TDD: `adapt` reads `.adapt-discovery.toml` accepted/declined entries and
  applies accepted ones; the file is byte-identical before and after the run
  (AC #8 — CLI never writes it).
- TDD: `adapt --ci` against a fixture with unresolved `.upstream.<ext>`
  companions exits non-zero with stderr listing the pending companions
  (AC #9).
- TDD: `adapt --ci` against a fixture where every companion has been
  removed exits zero (AC #9 — "resolved" means no companion file on disk).

**Approach:**
- Walk projected files for substitution; walk `.upstream.<ext>` companions
  for report generation; read `.adapt-discovery.toml` and apply accepted
  moves deterministically.
- Refuse to write `.adapt-discovery.toml` — surface in tests via a
  pre/post hash comparison.

**Done when:** AC #8 and AC #9 both hold; cross-cutting Tier test (under
T15) covers Tier invariants for this command.

### T7: `list-targets` subcommand

**Depends on:** T1c

**Tests:**
- TDD: `agentbundle list-targets` prints one row per adapter the CLI
  supports, in stable order; exit 0.
- TDD: the printed adapter list matches the runtime registry exposed by
  `agentbundle.build.adapters` (no baked-in constants — a test injects a
  monkey-patched extra adapter and the output reflects it).

**Approach:**
- Query the imported `agentbundle.build.adapters` registry at runtime;
  format as a stable table.

**Done when:** both tests green; output is deterministic across runs.

### T8: `list-packs` subcommand

**Depends on:** T1c

**Tests:**
- TDD: against a fixture catalogue with two packs, `list-packs <uri>`
  prints both rows with name, version, description, dependencies.

**Approach:**
- Resolve the catalogue URI (same grammar as T5); enumerate
  `packs/*/pack.toml`; format as a stable table.

**Done when:** test green.

### T9: `diff` subcommand

**Depends on:** T1c, T3

**Tests:**
- TDD: against a pack whose projection is in sync with `pack.toml`, `diff`
  exits 0; against a tampered projection, exits 1 with a one-line list of
  drifted paths.

**Approach:**
- Re-run `render.render_pack` in memory; compare against on-disk projection
  byte-by-byte; report drift.

**Done when:** both rows of the test green.

### T10: `init-state` subcommand

**Depends on:** T1c

**Tests:**
- TDD: against a directory whose tree matches a known pack's projection,
  `init-state --pack core` writes `.agent-ready-state.toml` with the right
  SHA-256 hashes (matches T5's hashing logic).
- TDD (Tier invariant — local; cross-cutting test in T15 also covers this):
  `init-state` writes only `.agent-ready-state.toml` (a Tier-1 path per the
  sibling spec's contract); no Tier-2 or Tier-3 path is touched.

**Approach:**
- Hash every projected path; write the state file atomically via
  `safety.write_jailed`.

**Done when:** both tests green; state file is parseable by
`config.load_state`.

### T11: `uninstall` subcommand

**Depends on:** T1c, T5

**Tests:**
- TDD: `uninstall --pack core` against the post-install brownfield fixture
  removes every Tier-1 file the install wrote, warns on Tier-2 (offers
  keep-or-remove-with-backup; defaults to keep in non-interactive mode),
  and leaves all Tier-3 files **byte-identical** before and after (explicit
  byte-identity assertion, not just an existence check). Covered by the
  cross-cutting Tier invariant test in T15.
- TDD: `.agent-ready-state.toml` no longer references the uninstalled pack
  after the run (the `[pack.<name>]` table is removed; other packs'
  tables remain untouched).

**Approach:**
- Read `.agent-ready-state.toml` for the pack's Tier-1 paths; for each,
  hash-compare against current content; if matched, remove; if drifted
  (Tier-2), preserve and warn.

**Done when:** both tests green.

### T12: `upgrade` subcommand with per-primitive granularity

**Depends on:** T1c, T5

**Tests:**
- TDD: `upgrade --pack core --to v0.2` against the post-install fixture
  applies the whole-pack delta and updates `.agent-ready-state.toml`.
- TDD (parametrised over primitive type): `upgrade --pack core --skill X
  --to v0.2`, `--agent X`, `--hook X`, `--seed X`, `--command X` each
  move only that primitive's files; `.agent-ready-state.toml` records the
  mixed-version pack state with per-primitive `tier-1-files` /
  `tier-2-files` lists under e.g. `[pack.core.skill.X]` (verifies AC #10
  first clause across all five primitive types).
- TDD: a subsequent whole-pack `upgrade --pack core --to v0.3` against the
  mixed-state fixture surfaces the mixed state on stderr before proceeding
  (verifies AC #10 second clause).
- TDD: `--skill foo` where `foo` is not a primitive in the pack exits
  non-zero with one-line stderr "primitive 'foo' not in pack core"
  (verifies AC #10 error clause). Equivalent test for each of the other
  four primitive flags.
- TDD: a `.sh` hook upgraded retains its `.sh` extension; a `.py` hook
  upgraded retains its `.py` extension (extension-preservation under
  AC #4 / AC #5).

**Approach:**
- Identify a primitive's file set from `pack.toml`: the named primitive's
  `source-path` (or equivalent key per the sibling spec) is resolved to a
  glob, intersected with the projection adapter set the install used.
- Compare current pack version (from `.agent-ready-state.toml`) against
  `--to`; compute file delta; apply Tier-1/2/3 contract per file via
  `safety.classify` + `safety.write_jailed`; record per-primitive versions
  in the state file when `--skill`/`--agent`/`--hook`/`--seed`/`--command`
  is passed.
- State-file shape for mixed-version: under `[pack.<name>]`, sub-tables
  per primitive (e.g. `[pack.core.skill.work-loop]` with `tier-1-files =
  [...]`, `tier-2-files = [...]`, `version = "v0.2"`) when that primitive's
  version diverges from the pack-wide version.

**Done when:** all test rows green.

### T13: `zipapp` distribution build

**Depends on:** T2, T3, T4, T5, T6, T7, T8, T9, T10, T11, T12, T15

(T15 added so `zipapp` distribution can't ship before the Tier invariants
are proven across the write-capable subcommand matrix.)

**Tests:**
- Goal-based: `python -m zipapp packages/agentbundle/agentbundle -o
  dist/agentbundle.pyz -m agentbundle.cli:main` produces a runnable file.
- Goal-based: `python dist/agentbundle.pyz --version` exits 0 and prints
  the CLI + spec versions (AC #2, AC #11).

**Approach:**
- Add a `make zipapp` target (or `scripts/build-zipapp.sh`) that bundles
  `agentbundle/` (including the embedded `agentbundle/build/` library)
  into a single `.pyz`; verify it loads with stdlib only.

**Done when:** both checks green; the `.pyz` runs on a Python 3.11 venv
with `--no-site-packages`.

### T14: Manual QA — corporate-network sandbox round-trip

**Depends on:** T13

**Tests:**
- Manual QA: `gh release download` → `python agentbundle.pyz install --pack
  core <catalogue-git-url>` against a brownfield repo on a host that only
  reaches Artifactory + git. Result recorded at
  `packages/agentbundle/tests/manual/sandbox-round-trip.md` per the
  *Visual / manual QA* contract in the work-loop skill.

**Approach:**
- Provision a sandbox VM (corporate-network image); follow the recorded
  steps; capture stdout/stderr and resulting tree state; note any
  deviation in the recorded report.

**Done when:** the recorded report shows all install + adapt steps
succeeded; AC #11's manual QA tail holds.

### T15: Cross-cutting Tier-1/2/3 invariant integration test

**Depends on:** T4, T5, T3, T6, T10, T12, T11

**Tests:**
- One parametrised integration test walks every write-capable subcommand
  against a single shared fixture and asserts the three Tier invariants per
  command: Tier-1 may change; Tier-2 produces a `.upstream.<ext>` companion
  (original byte-identical); Tier-3 paths are byte-identical before and
  after. The parametrisation pins the **exact invocation** tested per
  subcommand:
  - `scaffold --output <root>`
  - `install --pack core <fixture-catalogue-uri>`
  - `render packs/core --output <root>`
  - `adapt --values-from <fixture-values.toml>` (the write-capable form)
  - `init-state --pack core`
  - `upgrade --pack core --to v0.2`
  - `uninstall --pack core`
- Negative invariant row: `adapt` **without** `--values-from` makes no
  Tier-1 changes (read-only mode — only writes `.adapt-pending.md`, which
  is a Tier-1 path; assert no other Tier-1 file is modified).
- Fixture includes one `.sh` hook and one `.py` hook to pin
  extension-preservation across `render` and `upgrade`.
- Fixture includes a path-jail probe pack (projection rule resolving to
  `../../malicious`) that every write-capable command refuses with exit
  non-zero (cross-cutting AC #6).

**Approach:**
- Lives at `packages/agentbundle/tests/integration/test_tier_invariants.py`;
  parametrises over the seven subcommands and the two hook extensions.

**Done when:** matrix of (subcommand × tier × hook-extension) all green.

## Rollout

`packages/agentbundle/` lands as a new package — no behaviour change to
existing surfaces. Distribution channels light up in order: `zipapp` via
GitHub Releases (T13) → `pip install` via Artifactory (deferred past v1)
→ Homebrew formula (deferred past v1). The CLI is opt-in by definition;
adopters who installed via APM or Claude plugins keep using those tools.
No flag-gating required.

## Risks

- **Hard dependency on `distribution-adapters` spec.** This spec consumes
  `pack.toml`'s `[pack.adapter-contract]` table, the Tier-1/2/3 file-safety
  contract, the `.agent-ready-state.toml` schema, the `.upstream.<ext>`
  semantics, the six-recipe enumeration, the five primitive types, and the
  relocated F-build library at `packages/agentbundle/agentbundle/build/`.
  If `distribution-adapters` lands with a different shape than this plan
  assumes, every subcommand reading those structures has to chase it.
  **Mitigation:** don't move this spec to Approved until
  `distribution-adapters` is at least Approved; track its status during
  PLAN review; T1c explicitly blocks on the sibling's F-build relocation
  task.
- **F-build render code not importable as a regular package.** Resolved by
  the sibling spec's relocation to `packages/agentbundle/agentbundle/build/`.
  T1a's second test (`import agentbundle.build` exits 0) is the canary;
  if the sibling lands the relocation differently (e.g. under a different
  module name), pin the import path in T1c and update this plan.
- **Conformance fixtures not yet defined.** T2's `--strict` mode needs the
  F-conformance fixtures (sibling work under RFC-0003, deferred to v1.1).
  v1 ships schema conformance now and `--strict` is partial — warns on
  stderr when fixtures absent. **Mitigation:** explicit `Depends on:`
  marker in T2; AC #12 carves out the partial-at-v1 behaviour.
- **Tier-2 hash-comparison cost on large projections.** Hashing every
  projected file on every `install`/`upgrade` call is O(projection size).
  Acceptable at the `core` pack scale; revisit if a future pack ships
  hundreds of files. **Mitigation:** measure on the brownfield fixture and
  surface if it exceeds a perceptible threshold.
- **`zipapp` distribution under stdlib-only is unusual.** Most Python CLIs
  carry dependencies; the stdlib-only constraint is harder to maintain
  over time (every contributor will want to add `click` or `rich`).
  **Mitigation:** the `Never do` rail catches this in review, and the
  sibling `distribution-adapters` spec's `lint-build.sh` stdlib-import
  audit catches non-stdlib imports structurally.
- **GitHub archive endpoint availability.** If GitHub's
  `archive/refs/tags/...`, `archive/refs/heads/...`, or `archive/<sha>...`
  endpoint changes path, rate-limits, or quota-restricts unauthenticated
  fetches, `install` for `git+https://` breaks. **Mitigation:** small
  retry budget on transient errors; on failure, the one-line stderr names
  the exact tarball URL the CLI tried to fetch, so the adopter can
  reproduce out-of-band. If the endpoint is permanently displaced, ship a
  patch release switching to whichever GitHub-supported HTTPS path works
  — still stdlib, still no `git` subprocess.

## Changelog

- 2026-05-22: initial plan.
- 2026-05-22: fix-pass 2. Switched `install` `git+https://` fetch from a
  documented single `git` subprocess call site to pure stdlib
  `urllib.request` + `tarfile` against GitHub's archive endpoint — closes
  the `Never do` subprocess carve-out entirely. `git+ssh://` deferred to
  v1.1 with an explicit refuse-and-explain message. T5 test grammar
  rewritten to cover tag/branch/SHA HTTPS, SSH-deferred refusal,
  unreachable URL, plus a `subprocess`-not-invoked assertion. T13 now
  depends on T15 so `zipapp` can't ship before Tier invariants are
  proven. T15 parametrisation pins exact invocations per subcommand and
  adds a negative-invariant row (`adapt` without `--values-from` makes no
  Tier-1 changes). Spec `--version` AC and T1a test rephrased to verify
  read-at-import (mutate-on-disk-after-import check). Added AC for
  `agentbundle.build.adapters` registry contract (`name → AdapterModule`
  at import time). Promoted "tag the repo at release" from a Risk
  mitigation to a ship-time AC. Reordered the canonical subcommand list
  discovery-first across spec and plan, with a note acknowledging
  RFC-0003's descriptive ordering. Cited the sibling spec's
  stdlib-import audit (`lint-build.sh`) as the structural enforcement
  for the no-third-party-dep rail. Added GitHub archive endpoint risk
  row.
- 2026-05-22: post-adversarial-review fix pass. T1 split into T1a/T1b/T1c
  (scaffold, safety primitives, render wrapper). Added T15 (cross-cutting
  Tier invariant integration test). Pinned setuptools/PEP 621 as build
  backend. Tightened subprocess rail to "never except `gh`" (with a
  documented single `git` call site in `install`). Added explicit
  dependencies on the sibling `distribution-adapters` spec for F-build
  relocation, Tier contract, `.agent-ready-state.toml` schema,
  `.upstream.<ext>` semantics, the six-recipe enumeration, and the five
  primitive types (including `command`). Canonicalised subcommand order
  to install-workflow sequence. Expanded T5 with full catalogue URI
  grammar test rows and state-file merge semantics. Expanded T12 with
  per-primitive file-set identification, mixed-version state shape, and
  primitive-not-found error. Added F-conformance dependency marker to T2.
  Added `command` primitive to T3 and T12. Added hook extension
  preservation (`.sh` and `.py`) across T3, T12, and T15. Added
  spec-version-tag risk row.
- 2026-05-22: adapter contract files moved from
  `docs/specs/adapter-contract/` to `docs/contracts/` with `<name>.schema.json`
  filenames. Bare-`contract.toml` references throughout this spec and
  plan updated to `adapter.toml`; the `[pack.adapter-contract]` TOML
  key (a conceptual table identifier in pack manifests) is unchanged.
  See [RFC-0001 § Amendments](../../rfc/0001-bundle-distribution-by-adapter-spec.md#amendments).
