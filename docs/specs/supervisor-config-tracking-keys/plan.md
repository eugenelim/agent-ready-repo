# Plan: Supervisor config tracking keys

- **Spec:** [`spec.md`](spec.md)
- **Status:** Drafting <!-- Drafting | Approved | Executing | Done -->
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
    `.github/workflows/build-check-windows.yml`, which runs named Git-free
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

Build the config fingerprint as a pure function of a file's bytes inside
`_supervisor_attempt.py`, proved first by a Git-free suite that also runs on
Windows. Then route the `config` and `config.worktree` entries of `git_state`
through it, and make the manifest comparison like-for-like, so a manifest that
holds a raw-file digest is still compared against the raw file. The git-backed
attempt suite then proves the sibling-worktree cases end to end. Documentation,
release, and the captured item close last. The riskiest part is the comparison
change: it touches the code that decides every attempt, and a mistake there
either admits a changed config or refuses every regeneration.

## Constraints

- ADR-0144 D11: a worker attempt's change to Git control state refuses its
  result. This plan narrows which config lines count as control state and keeps
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

**Integration tests:** the sibling-worktree cases in T2 span the filter (T1)
and the manifest comparison (T2).
**Manual verification:** none.

## Durable-output map

| Durable output | Tasks | Implementation evidence | Closeout evidence |
| --- | --- | --- | --- |
| User documentation — `work-loop/references/supervisor.md` | T3 | Reference diff; self-host check clean | The open-attempt rule names the excluded keys and the raw-file fallback. |
| Current architecture — `runtime-security-primitives.md` §11 | T3 | Architecture diff; security-reviewer pass | §11 states the config fingerprint and fallback. |
| Decision rationale — the narrowed Git control state term | T3 | Spec Definitions; the one-sentence pointer in the attempt-security spec | The pointer resolves to this spec and the attempt-security criteria are byte-identical. |
| Release history — core manifests and changelog fragment | T3 | VI-0111, VI-0112 | Version parity and changelog validation green. |
| Captured-item closure | T3 | The added item and its status line | The item is on `main`, closed, and points at this spec. |

## Design (LLD)

### Design decisions

- **Filter, don't ask Git.** The fingerprint is computed from the file's bytes
  by a line parser, because the check runs inside the hardened helper's pre-call
  control check, where a `git config` call would recurse into the helper and
  would read state the worker may have changed. Rejected: `git config --list`
  (a Git call, and it resolves includes). Rests on: no supervisor `git` call
  reads a branch-tracking or gh-resolved key (bounded search of
  `_supervisor_*.py`: the verbs used are `add`, `cat-file`, `commit`, `diff`,
  `hash-object`, `log`, `ls-tree`, `read-tree`, `rev-parse`, `show`, `status`,
  `update-ref`, `worktree`, `write-tree`; none pushes, pulls, fetches, or calls
  `gh`). Traces to: AC-0001, AC-0006.
- **Allowlist, fail closed.** Only the excluded lines leave the digest; any line
  outside the clean-parse grammar sends the whole file to the raw-file
  fingerprint. Rejected: a denylist of security keys, which silently admits any
  key it does not name. Rests on: real shared configs hold only Git- and
  `gh`-written lines. A read-only probe of this repository's shared config
  (76 lines, 21 `[branch]` sections, 24 linked worktrees, no `config.worktree`)
  found only `remote` and `merge` inside branch sections, no continuation or
  unbalanced-quote line, and so parses cleanly. Traces to: AC-0002, AC-0003.
- **Includes force the fallback.** An `include` or `includeIf` section sends the
  file to the raw-file fingerprint rather than being followed or filtered,
  because the parser never reads a second file. `include.path` is also refused
  at `start`, so an include present during an attempt was added during it.
  Traces to: AC-0003.
- **Domain-separated digest.** The filtered digest is
  `"config-view:" + sha256(b"agentbundle-config-view.v1\0" + retained bytes)`,
  so it never equals a raw-file digest (a bare sha256 hex string). Traces to:
  AC-0004, AC-0009.
- **Like-for-like comparison.** When the manifest's value for a `config` or
  `config.worktree` entry is a bare hex digest, the current value is the
  raw-file fingerprint; otherwise the config fingerprint. This covers a
  `regenerate` request, whose manifest the pre-change supervisor records and
  whose `report` the post-change supervisor checks (`issue` → `_record` →
  `git_state()` at issue time; `guard` compares at `report`). Without it, the
  self-hosted regeneration that installs this change refuses on
  `common:config` with nothing a controller can restore. Rejected: a manifest
  schema bump, which `_valid` would refuse for every open attempt. Traces to:
  AC-0009.

Owned by: T1, T2.

### Data & schema

- The manifest record shape (`schema_version`, `git` map of label to digest
  string) is unchanged. Only the value stored under `git:config`,
  `git:config.worktree`, `common:config`, and `common:config.worktree` changes
  form, to `config-view:<hex>` when the file parses cleanly. The labels stay, so
  refusal details keep naming `common:config`.
- Retained bytes: every line of the file except excluded lines, each with its
  line terminator normalised to `\n`, in file order. A `[branch "<name>"]`
  section ends at the next header.

Traces to: AC-0001, AC-0004, AC-0005.

Owned by: T1, T2.

### Interfaces & contracts

- One private function in `_supervisor_attempt.py` takes the file's bytes and
  returns the config fingerprint string; a second returns the raw-file digest.
  Their names are `implementation-discovered`; constraint: pure, standard
  library, no I/O, importable by path without loading a sibling.
- `git_state` routes the four config labels through the function; `differences`
  callers (`guard`, `_differences`, `_control_check`) compare config labels
  like-for-like. Discovery predicate for the seam: the single place where both
  the manifest value and the current file bytes are in hand. Verification: T2's
  integration cases.
- Test seam for AC-0006: the module's process-launch entry
  (`_supervisor_git._launch`, and `subprocess.run`) replaced by a function that
  fails the test, while `git_state()` runs over a prepared directory.

Traces to: AC-0006, AC-0007, AC-0008, AC-0009.

Owned by: T1, T2.

### Failure, edge cases & resilience

- Unreadable, oversized, symlinked, or special config entries keep their
  current `_entry` results (`unsafe`, `special`, `link:…`, or
  `denied-attempt-unreadable`); the filter applies only to a regular file read
  in full.
- Non-UTF-8 bytes, a legacy `[section.subsection]` header, a continuation
  backslash, an unbalanced double quote, an include, and a non-tracking key in a
  branch section each select the raw-file fingerprint.
- Case: section names and variable names compare case-insensitively; a
  subsection name compares exactly.
- A file that changes from cleanly parsing to not parsing (or back) changes form
  and therefore refuses, which is the fail-closed direction.

Traces to: AC-0003, AC-0008.

Owned by: T1.

### Quality attributes (NFRs)

- Security posture: every key outside the excluded set stays fingerprinted;
  a security-reviewer pass is required on the diff.
- Platform: the filter suite runs on `windows-latest` in
  `build-check-windows.yml` and on POSIX CI, and fails its step on a skipped
  case through `tools/require-junit-ran-without-skips.py`, as the confined-write
  step does.

Traces to: AC-0013.

Owned by: T1.

## Tasks

### T1: The config fingerprint is a pure, fail-closed filter proved on both platforms

**Depends on:** none

**Touches:** `packs/core/.apm/skills/work-loop/scripts/_supervisor_attempt.py`, a new Git-free suite under `packs/core/tests/skills/work-loop/`, `.github/workflows/build-check-windows.yml`

**Verification mode:** TDD

**Tests:**
- **VI-0101 (AC-0001):** table cases over bytes: a base config, then the base
  plus a new `[branch "x"]` section, plus changed `remote`/`merge`/`pushremote`/
  `rebase`/`description` values with mixed-case names, plus
  `gh-resolved = base` inside `[remote "origin"]`, minus a whole branch section;
  every case has the base's fingerprint.
- **VI-0102 (AC-0002):** one case per enumerated non-excluded change against the
  same base; each fingerprint differs from the base's.
- **VI-0103 (AC-0003):** one case per enumerated unclean shape; each returns
  exactly `sha256(bytes)` hex, compared with `hashlib` in the test.
- **VI-0104 (AC-0004):** every cleanly parsing case from VI-0101 and VI-0102
  returns a value with the `config-view:` prefix, which no bare hex string has.
- **VI-0105 (AC-0005):** each VI-0101 case with `\r\n` terminators matches its
  `\n` form.
- **VI-0106 (AC-0006):** `git_state()` over a prepared Git and common directory
  with launch entries replaced by a failing stub returns the config entries.
- **VI-0113 (AC-0013):** the suite runs as its own `build-check-windows.yml`
  step with a JUnit report checked by `tools/require-junit-ran-without-skips.py`,
  and in the POSIX pack-suite lane; both green.

**Done when:** VI-0101–VI-0106 pass locally, VI-0113's Windows and POSIX steps are green on the PR, and the security-reviewer returns clean on the filter.

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
- **VI-0109 (AC-0009):** the attempt is issued with the config fingerprint
  function replaced by the raw-file digest, as a pre-change supervisor records
  it, and reported with the real function; with the config unchanged it is
  admitted, and with one byte of a branch-tracking key changed it refuses.
- **VI-0110 (AC-0010):** the `supervisor-integration` lane's suites pass, and
  `git diff origin/main -- packs/core/tests/skills/work-loop/` shows no existing
  test function modified or removed.

**Done when:** VI-0107–VI-0110 pass in the `supervisor-integration` lane and the security-reviewer returns clean on the diff.

### T3: Adopters and maintainers read the filtered fingerprint, and the release ships it

**Depends on:** T2

**Touches:** `packs/core/.apm/skills/work-loop/references/supervisor.md`, `docs/architecture/runtime-security-primitives.md`, `packs/core/pack.toml`, `packs/core/.claude-plugin/plugin.json`, a changelog fragment, the self-host projections, `docs/product/captured/supervisor-common-config-residue.md` (added, then closed), `docs/specs/execution-supervisor-attempt-security/spec.md` (one-sentence pointer only)

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
- The attempt-security spec gains one sentence beside its Git control state
  definition, pointing to this spec's config fingerprint; nothing else in that
  file moves.

**Done when:** VI-0111 and VI-0112 pass, `git diff origin/main -- docs/specs/execution-supervisor-attempt-security/spec.md` adds one sentence and changes no criterion, `agentbundle catalogue self-host --root . --write` leaves no drift, and the durable-output map rows for documentation and the captured item are met.

## Rollout

Delivery is a normal core patch release; there is no flag and no data
migration. A run admitted before the release keeps working: its pinned
supervisor refuses `supervisor-changed` until regenerated, and the
like-for-like comparison admits the regeneration's own attempt. Reversal is
reinstalling the prior core release; manifests recorded with `config-view:`
values would then never match and refuse once, cleared by a fresh `start`.

## Risks

- The comparison change touches every attempt decision; T2's refusal cases run
  before its admission cases are trusted.
- A `gh` or editor key not in the excluded set keeps the false refusal for the
  repositories that carry it; the spec's Accepted Risk accepts that cost.
- The captured item is added by two branches; the second to merge resolves the
  overlap.
- The Windows step adds CI time to `build-check-windows.yml`; the suite is
  Git-free so its cost is in assertions, not processes.

## Changelog

none
