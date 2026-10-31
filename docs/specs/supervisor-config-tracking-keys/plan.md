# Plan: Supervisor config tracking keys

- **Spec:** [`spec.md`](spec.md)
- **Status:** Executing <!-- Drafting | Approved | Executing | Done -->
- **Repository anchors:** ADR-0144 D11 sets the trust boundary; the
  `execution-supervisor-attempt-security` spec defines Git control state and the
  manifest.
  - `work-loop/scripts/_supervisor_attempt.py`: `Attempts.git_state` digests
    `config`, `config.worktree`, `commondir`, and `objects/info/alternates` in
    the Git and common directories through `_entry`, a confined regular-file
    read; `guard`, `_differences`, and `_control_check` compare
    `issuance.git` with `git_state()` through `differences`.
  - `work-loop/scripts/_supervisor_git.py`: `_CODE_RUNNING_FIXED` and
    `code_running_keys` (the start-time refusal, unchanged); `_fixed_flags` (the
    neutralising flags, unchanged).
  - Tests: `packs/core/tests/skills/work-loop/test_supervisor_attempt.py`
    (git-backed, `sup.INTEGRATION`, run only by the Ubuntu
    `supervisor-integration` lane of `catalogue-tooling-ci-gates.yml`), which
    holds `test_an_unparseable_git_config_is_refused_and_recorded_before_any_git_call`;
    `.github/workflows/build-check-windows.yml`, which runs named
    suites on `windows-latest`.

> **Plan contract:** this is the implementation strategy. After approval, a
> change needs an **amendment** only when it touches the spec's protected
> sections (contract, scope and non-goals, durable outputs, agent rules, testing
> strategy, acceptance criteria, accepted risk) or its `Terminal Intent`. A change
> to tasks, tests, stubs, design, or approach needs none: the controller makes it
> as an in-envelope working-plan change while no execution attempt is open, and
> the run continues with every finished task still finished. Execution
> observations belong in `docs/specs/supervisor-config-tracking-keys/notes/verification-ledger.md`.
> A genuine error in a protected section follows the controlled-amendment path.
>
> **Not every field is contract.** `Touches`, `Tests` and `Done when` are what a
> completion gate reads. `Design`, `Approach`, `Grounding` and `Risks` are working
> material the controller corrects in place while no attempt is open.

## Approach

Build the config fingerprint as a pure function of one read's bytes inside
`_supervisor_attempt.py`, proved first by a suite that needs no repository and
also runs on Windows. Then route the `config` and `config.worktree` entries of `git_state`
through it, and make the manifest comparison form-preserving, so an entry
recorded as a raw-file fingerprint is still compared against the raw file. The
git-backed attempt suite then proves the sibling-worktree cases end to end.
Documentation, release, and
the captured item close last. The riskiest part is the comparison change: it
touches the code that decides every attempt, and a mistake there either admits a
changed config or refuses every regeneration.

## Constraints

- ADR-0144 D11: a worker attempt's change to Git control state refuses its
  result. This plan narrows which config bytes count as control state and keeps
  the refusal itself.
- `execution-supervisor-attempt-security`: the manifest, its lifecycle, the
  hardened helper's pre-call control check by direct file reads (its AC-0010),
  and the start-time `unsupported-git-config` refusal (its AC-0009) are
  unchanged.
- ADR-0150: mechanism lives here, in `## Design (LLD)`; the red test is written
  at EXECUTE.
- `packs/AGENTS.md`: pack content changes bump the core version in `pack.toml`
  and `plugin.json`; `.apm/` is the source and self-host regenerates the
  projections; shipped pack content cites no internal records.
- Python standard library only; the attempt module stays importable without
  launching Git.

## Construction tests

Most construction tests live under **Tasks** below.

**Integration tests:** the sibling-worktree cases in T2 span the fingerprint
(T1) and the manifest comparison (T2); VI-0116 in T1 runs the pinned shapes
through real Git on both platforms.
**Manual verification:** none.

## Durable-output map

| Durable output | Tasks | Implementation evidence | Closeout evidence |
| --- | --- | --- | --- |
| User documentation — `work-loop/references/supervisor.md` open-attempt rule and refusal row | T3 | Reference diff; self-host check clean | Names the excluded keys and that any other byte change refuses. |
| Controller guidance — `work-loop/references/supervisor.md` § External effects | T3 | Reference diff; self-host check clean | States the explicit remote, ref, and pull-request condition. |
| Current architecture — `runtime-security-primitives.md` §11 | T3 | Architecture diff; security-reviewer pass | States the config fingerprint and the excluded keys. |
| Current architecture — `work-loop-execution-supervisor.md` § Attempts | T3 | Architecture diff | Config entries record the config fingerprint. |
| Decision rationale — the narrowed Git control state term | T3 | Spec Definitions; the pointer in the attempt-security spec | The pointer resolves to this spec, says config entries record the config fingerprint, and the attempt-security criteria are byte-identical. |
| Release history — core manifests and changelog fragment | T3 | VI-0111, VI-0112 | Version parity and changelog validation green. |
| Captured-item closure | T3 | The added item and its status line | The item is on `main`, closed, and points at this spec. |

## Design (LLD)

### Design decisions

- **Strip canonical blocks; never parse.** The fingerprint removes only bytes in
  the exact form Git itself writes and keeps every other byte verbatim, so any
  shape Git reads differently from a line pattern changes the digest as it does
  today. Rejected: a grammar that classifies lines and falls back to the raw
  file, because it is safe only if its tokenisation equals Git's, and Git reads
  `[branch "x"][core]hooksPath = /evil` as `core.hookspath`. Rejected:
  `git config --list`, a Git call inside the helper's own pre-check. Rests on:
  Git writes tracking keys only as `[branch "<name>"]\n` then
  `\t<key> = <value>\n`, and appends `\tgh-resolved = <value>\n` inside the
  existing `[remote "<name>"]` block (probe below). Traces to: AC-0001,
  AC-0002, AC-0003, AC-0014.
- **A file-wide precondition stops joined lines.** Stripping removes anything
  only from a strippable file: one that ends in `\n`, holds no `\r`, and has no
  line ending in `\` before `\n`. Git joins a line ending in `\` to the next,
  and it normalises `\r\n` before reading escapes, so `\` + `\r\n` also joins;
  a canonical-looking block after a joined line is part of a value, and its
  removal would shift what Git reads next. A per-line check cannot see every
  way Git joins or splits, so the precondition is file-wide: any `\r` or
  trailing `\` anywhere leaves the whole file in the digest. Traces to:
  AC-0003.
- **Block boundaries stop sections from moving.** A branch block is removed only
  when the next line begins with `[` or the block ends the file. Otherwise
  deleting `[branch "x"]\n\tremote = origin\n` from
  `[core]…[branch "x"]\n\tremote = origin\n\thookspath = /evil\n` leaves the same
  bytes as a file that sets `core.hookspath` (Git reads the first as
  `branch.x.hookspath`). The gh-resolved rule requires every line from the
  remote header to it to begin with `\t` and a lower-case letter, so an
  indented header cannot end the block unseen. Traces to: AC-0002, AC-0003.
- **Form-preserving comparison.** The manifest value's form selects the
  comparison, from a closed set: `config-view:` → the config fingerprint;
  `<size>:<sha256hex>` (exactly today's `_digest` value,
  `f"{len(data)}:{sha256(data).hexdigest()}"`) → the raw-file fingerprint;
  `link:…`, `special`, `unsafe` → the current `_entry` result verbatim. This
  covers a `regenerate` request, whose manifest the pre-change supervisor
  records (`issue` → `_record` → `git_state()`) and whose `report` the
  post-change supervisor checks in `guard`; without it, the self-hosted
  regeneration that installs this change refuses on `common:config` with
  nothing to restore. Rejected: a manifest schema bump, because `_valid`
  requires `schema_version == _SCHEMA_VERSION` and refuses older records as
  `denied-attempt-record`. Traces to: AC-0004, AC-0009.
- **One read.** The fingerprint is derived from the bytes `_entry` already
  obtains through `read_confined_regular_file`; no second open, so there is no
  window between a read that is checked and a read that is digested. Traces
  to: AC-0015.

Probe (read-only, 2026-10-31, `git config --file <f> --list` under Git 2.56.0
in a `mktemp` directory with `GIT_CONFIG_GLOBAL=/dev/null` and
`GIT_CONFIG_NOSYSTEM=1`):

- `git push -u`, `git checkout -b … --track`, and `git config` write exactly the
  canonical form.
- `[branch "x"][core]hookspath = /evil` gives `core.hookspath`;
  `[branch "x"] [remote "origin"]url = …` gives `remote.origin.url`;
  `[branch "x\\"][filter "y"]clean = "/evil"]` gives `filter.y.clean`.
- A `\r` inside a value line is a value byte
  (`core.bare=false\r[core]hookspath=/evil`), but after a header Git reads the
  content that follows `]`: `[branch "x"]\r[core]\n\thookspath = /evil` gives
  `core.hookspath`.
- A leading byte-order mark is skipped, with exit 0.
- `\` + `\r\n` joins lines: `[remote "origin"]\n\turl = /x\\\r\n[branch "b"]\n\tremote = o\n[core]\n\thooksPath = /evil\n`
  gives `remote.origin.url=/x[branch b]`, `remote.origin.remote=o`, and a live
  `core.hookspath`; the `gh-resolved` and `include.path` variants join the same
  way.
- Every headered key and value literal in AC-0003 gives `branch.x.remote=o`
  (`[branch "x"]\n\tRemote = o\n`, `remote=o`, `remote = "o"`, `o;x`, `o#x`, and
  the byte-order-mark file alike); `[branch "x"]\n\tremote = o\\\n[core]\n\tbare = false\n`
  gives `branch.x.remote=o[core]` and `branch.x.bare=false`; the `include` and
  `includeIf` files give `include.path` and `includeif.gitdir:/x/.path`.
- A throwaway implementation of the rules above removes nothing from any
  AC-0003 file. Without the file-wide precondition it removes 19–27 bytes from
  each file AC-0003 marks *(precondition)* and nothing from the others. The
  control file `[core]\n\tbare = false\n[branch "x"]\n\tremote = o\n[core]\n\teditor = e\n`,
  the `\r\n` precondition case without its stray `\r`, has its 25-byte block
  removed.

Owned by: T1, T2.

### Data & schema

- The manifest record shape (`schema_version`, `git` map of label to value) is
  unchanged. Only the value stored under `git:config`, `git:config.worktree`,
  `common:config`, and `common:config.worktree` changes form, to
  `config-view:<size>:<sha256hex>` of the retained bytes. The labels stay, so
  refusal details keep naming `common:config`.
- Retained bytes: the file's bytes with each canonical tracking block's lines
  removed, every other byte in place, including `\r`, a byte-order mark, and a
  final unterminated segment.

Traces to: AC-0001, AC-0004.

Owned by: T1, T2.

### Interfaces & contracts

- One private function in `_supervisor_attempt.py` takes a file's bytes and
  returns the retained bytes; `git_state` digests them with `_digest` and the
  `config-view:` prefix. Its name is `implementation-discovered`; constraint:
  pure, standard library, no I/O, importable by path without loading a sibling.
- `git_state` routes the four config labels through it from `_entry`'s read;
  the comparison in `guard`, `_differences`, and `_control_check` selects the
  form per entry. Discovery predicate for the seam: the single place where both
  the manifest value and the current file bytes are in hand.
- Test seam for AC-0006: a `sys.addaudithook` hook, installed once for the test
  process and active only while a flag is set, that fails on the
  `subprocess.Popen`, `os.system`, `os.posix_spawn`, `os.spawn`, `os.exec`,
  `os.fork`, and `os.startfile` audit events while `git_state()` runs.
- Test seam for AC-0015: `read_confined_regular_file` wrapped to count calls
  and to return bytes that differ from the file on disk; the fingerprint follows
  the returned bytes and the count per config file is one.

Traces to: AC-0006, AC-0009, AC-0015.

Owned by: T1, T2.

### Failure, edge cases & resilience

- Unreadable, oversized, symlinked, or special config entries keep their
  current `_entry` results (`denied-attempt-unreadable`, `unsafe`, `link:…`,
  `special`); only a regular file read in full is stripped.
- A file that a writer rewrites from canonical to non-canonical form (or back)
  changes its retained bytes and therefore refuses, which is the fail-closed
  direction.
- A downgrade with an attempt open refuses that attempt; the spec's Accepted
  Risk states the recovery.

Traces to: AC-0003, AC-0008, AC-0016.

Owned by: T1.

### Quality attributes (NFRs)

- Security posture: every byte outside a canonical tracking block stays
  fingerprinted; a security-reviewer pass is required on the diff.
- Platform: the config-fingerprint suite runs on `windows-latest` in
  `build-check-windows.yml` and on a POSIX lane, each step writing a JUnit
  report that `tools/require-junit-ran-without-skips.py` checks, as the
  confined-write step does. The POSIX lane is `implementation-discovered`:
  a step beside the Windows one in a POSIX job of `build-check.yml` or of
  `catalogue-tooling-ci-gates.yml` that runs on every pull request touching the
  suite.

Traces to: AC-0013.

Owned by: T1.


### Means grounded in T1

Owned by: T1.

- The filter is `_strip_tracking_blocks(data: bytes) -> bytes` beside `_digest` in
  `_supervisor_attempt.py`, a line scan over `splitlines(keepends=True)` that checks
  the strippable-file precondition first (`endswith(b"\n")`, no `\r`, no `b"\\\n"`).
  A branch block is removed only with at least one matching key line and when the next
  line starts with `[` or the block ends the file; a gh-resolved line walks back over
  `\t[a-z]` lines to a `[remote "<sub>"]` header.
- Tracking value bytes: `[^"\\;#\x00-\x1f\x7f]*`; subsection bytes:
  `[^"\\\x00-\x1f\x7f]+`.
- `_entry` takes `config: bool`; `git_state` passes it for `config` and
  `config.worktree` in both the Git and common directories, so the fingerprint comes
  from the one confined read and `link:`/`special`/`unsafe` are unchanged.
- Test seams: `git_state()` is driven with a namespace of pins and no repository;
  VI-0115 patches `read_confined_regular_file` and `_MAX_FILE_BYTES`; VI-0106 uses a
  `sys.addaudithook` process-event hook.
- The POSIX zero-skip lane is `build-check.yml`'s `gate-main` job; the Windows lane is
  a `build-check-windows.yml` step after the confined-write step. Both run
  `tools/require-junit-ran-without-skips.py`.
- `gh pr checkout` and `gh repo set-default` need the network (a probe with an
  unreachable proxy and a fake token failed on GraphQL and wrote no config), so their
  exact bytes stay unprobed and the fail-closed rule covers them.


### Means grounded in T2

Owned by: T2.

- The comparison seam is `Attempts.git_state(recorded=None)`. The three comparison
  sites (`_differences`, `_control_check`, `guard`) pass the manifest's Git map;
  issuing and recording call it with no argument, so new manifests record
  `config-view:`.
- Form selection: `_RAW_ENTRY = re.compile(r"\d+:[0-9a-f]{64}")`. A recorded config
  entry that fully matches it is recomputed as the raw-file fingerprint; any other
  recorded value, or none, as the config fingerprint. `link:`, `special` and `unsafe`
  come out the same either way, so they compare verbatim. A manifest from before this
  change with no `config.worktree` entry means the file was absent; it is compared in
  config-view form, and an appearing file differs either way.
- Test seams: VI-0109 builds the old raw manifest by patching `Attempts._entry` to
  `config=False` only while `next` issues the attempt (no store edit); its `link`
  fixture symlinks `.git/config` to `config.real` and retargets it to a byte-equal
  `config.other`. The `[core]`-after-branch case appends `[core]` by hand, because
  Git appends new sections at the end.

## Tasks

### T1: The config fingerprint strips only canonical tracking blocks, proved on both platforms

**Depends on:** none

**Touches:** `packs/core/.apm/skills/work-loop/scripts/_supervisor_attempt.py`, a new config-fingerprint suite under `packs/core/tests/skills/work-loop/` that needs no repository, `.github/workflows/build-check-windows.yml`, the POSIX workflow that hosts the zero-skip step

**Verification mode:** TDD

**Tests:**
- **VI-0101 (AC-0001):** table cases over bytes: a base config, then the base
  plus a new canonical `[branch "x"]` block, plus changed `remote`, `merge`,
  `pushremote`, `rebase`, and `description` values, plus a canonical
  `gh-resolved` line in `[remote "origin"]`, minus a whole canonical block at
  the end of the file and before a header; every case has the base's
  fingerprint.
- **VI-0102 (AC-0002):** one case per enumerated change against the same base,
  including `uploadpack`, `receivepack`, `pushurl`, `vcs`, and `proxy` beside a
  canonical gh-resolved line, and each `_CODE_RUNNING_FIXED` key directly
  before and after a canonical block; each fingerprint differs from the base's.
- **VI-0103 (AC-0003):** one case per AC-0003 file, with the bytes the spec
  lists; each returns `"config-view:" + _digest(whole file)`, computed in the
  test from the shipped `_digest`.
- **VI-0116 (AC-0003):** each VI-0103 file, and the canonical base, is read with
  `git config --file <f> --list` under `GIT_CONFIG_GLOBAL` set to the null
  device and `GIT_CONFIG_NOSYSTEM=1`; the keys and values Git reports equal the
  case table's expected list, recorded from the probe in `## Design (LLD)`.
  For each headered key and value shape the expected list holds the
  `branch.x.*` key Git reports, so a key line Git attributes to the branch is
  proved to stay in the digest. It runs in the same suite, so it runs on the POSIX CI Git and on Git for
  Windows.
- **VI-0104 (AC-0004):** every value from VI-0101 to VI-0103 begins
  `config-view:`, and the raw-file fingerprint of each case does not.
- **VI-0106 (AC-0006):** `git_state()` over a prepared Git and common directory
  runs under the audit-hook seam with no audit event fired.
- **VI-0114 (AC-0014):** near-miss cases (`gh-resolved-x`, `remotes`, `Merge`,
  `gh-resolved` in a branch block) each change the fingerprint when their value
  changes.
- **VI-0115 (AC-0015, AC-0016):** the read-counting seam shows one read per
  config file and a fingerprint of the returned bytes. An oversized file gives
  `unsafe` on every platform. The symlink and FIFO cases give `link:…` and
  `special`; their case list is built at collection time from what the platform
  can create, so a platform without a file type never collects that case,
  rather than skipping it.
- **VI-0113 (AC-0013):** the suite runs as its own step on the Windows
  build-check job and on the POSIX lane, each with a JUnit report checked by
  `tools/require-junit-ran-without-skips.py`; both green.

**Approach:**
- Before the red test, try `gh pr checkout` and `gh repo set-default` against a
  `mktemp` repository with network disabled. If either writes config offline,
  record its exact bytes in `## Design (LLD)` and add them to VI-0101 when
  canonical, or to VI-0103 when not. If neither runs offline, record that, and
  the fail-closed rule stands with no contract change.

**Done when:** VI-0101–VI-0106 and VI-0114–VI-0116 pass locally, VI-0113's Windows and POSIX steps are green on the PR, and the security-reviewer returns clean on the fingerprint.

### T2: An open attempt ignores sibling tracking writes and still refuses every other config change

**Depends on:** T1

**Touches:** `packs/core/.apm/skills/work-loop/scripts/_supervisor_attempt.py`, `packs/core/tests/skills/work-loop/test_supervisor_attempt.py`

**Verification mode:** TDD

**Tests:**
- **VI-0107 (AC-0007):** the attempt fixture is a linked worktree of a temporary
  repository with a bare remote and a second linked sibling worktree; with an
  attempt open, the sibling runs each enumerated write with its own `git`, then
  the controller reports and runs `next`; the result is admitted and no
  `.refused.json` mark exists.
- **VI-0108 (AC-0008):** same fixture; each enumerated change is applied, then
  `next` answers `attempt-residue` and, in a fresh attempt, `report` answers
  `attempt-refused`, each detail naming `common:config` or
  `git:config.worktree`.
- **VI-0109 (AC-0009):** for each recorded form, the attempt is issued with the
  config entry recorded in that form — a raw entry built with the shipped
  `_digest`, a `config-view:` entry, and a symlinked config giving `link:…` —
  and reported with the real code. Unchanged state is admitted in every form;
  one changed byte of an excluded key refuses the raw form, one changed byte
  outside a canonical block refuses the `config-view:` form, and a retargeted
  link refuses the `link:…` form.
- **VI-0110 (AC-0010):** the `supervisor-integration` lane's suites pass, and
  `git diff origin/main -- packs/core/tests/skills/work-loop/` shows no existing
  test function modified or removed.

**Done when:** VI-0107–VI-0110 pass in the `supervisor-integration` lane and the security-reviewer returns clean on the diff.

### T3: Adopters, controllers, and maintainers read the config fingerprint, and the release ships it

**Depends on:** T2

**Touches:** `packs/core/.apm/skills/work-loop/references/supervisor.md`, `docs/architecture/runtime-security-primitives.md`, `docs/architecture/work-loop-execution-supervisor.md`, `packs/core/pack.toml`, `packs/core/.claude-plugin/plugin.json`, a changelog fragment, the self-host projections, `docs/product/captured/supervisor-common-config-residue.md` (added, then closed), `docs/specs/execution-supervisor-attempt-security/spec.md` (pointer only)

**Verification mode:** goal-based

**Tests:**
- **VI-0111 (AC-0011):** right before push, after `git fetch origin main`,
  compare `pack.toml` and `plugin.json` versions with each other and with the
  next patch above `packs/core/pack.toml` at `git merge-base HEAD origin/main`.
- **VI-0112 (AC-0012):** `tools/changelog.py new` creates the fragment, and
  `tools/changelog.py validate` exits 0.

**Approach:**
- The captured item is added with the content of
  `git show vlx/Fix-a-defect-in-the-core-98977ccb-950d-4502-ad7f-990b9ade9b50:docs/product/captured/supervisor-common-config-residue.md`,
  then closed with a pointer to this spec. That branch adds the same path, so
  whichever PR merges second resolves the overlap, keeping the closed status.
- The attempt-security spec gains one sentence beside its Git control state and
  Manifest definitions: config entries record this spec's config fingerprint
  instead of size and sha256. Nothing else in that file moves.
- `references/supervisor.md` § External effects tells the controller to pass an
  explicit remote, ref, and pull request to every push, pull, and merge, or to
  verify them first; it states the rule directly, citing no internal record.

**Done when:** VI-0111 and VI-0112 pass, `git diff origin/main -- docs/specs/execution-supervisor-attempt-security/spec.md` adds one sentence and changes no criterion, `agentbundle catalogue self-host --root . --write` leaves no drift, and every T3 row of the durable-output map is met.

## Rollout

Delivery is a normal core patch release; there is no flag and no data
migration. A run admitted before the release keeps working: its pinned
supervisor refuses `supervisor-changed` until regenerated, and the
form-preserving comparison admits the regeneration's own attempt. Reversal is
reinstalling the prior core release while no attempt is open and no refusal
stands; attempts close at `report`. The spec's Accepted Risk states what
happens after a downgrade with an attempt open.

## Risks

- The comparison change touches every attempt decision; T2's refusal cases run
  before its admission cases are trusted.
- A `gh` or editor write in a non-canonical form keeps the false refusal for
  the repositories that carry it; the spec's Accepted Risk accepts that cost.
- The captured item is added by two branches; the second to merge resolves the
  overlap.
- The Windows and POSIX steps add CI time; the suite needs no repository, and
  its only processes are VI-0116's `git config --file` reads.

## Changelog

<!-- Approvals only. -->

- 2026-10-31: spec approved by eugenelim
- 2026-10-31: plan approved by eugenelim
