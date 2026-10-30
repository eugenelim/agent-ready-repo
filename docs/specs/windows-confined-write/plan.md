# Plan: Windows confined write

- **Spec:** [`spec.md`](spec.md)
- **Status:** Executing <!-- Drafting | Approved | Executing | Done -->
- **Repository anchors:** ADR-0152 governs.
  - **The helper:** `packs/core/.apm/skills/work-loop/scripts/_confined_mutation.py`,
    which refuses at `_require_descriptor_walk` and loads the byte-identical
    `file_safety.py` as `_fs`.
  - **Analogue:** `file_safety.write_confined_regular_file`'s fallback create
    and update paths, which check a created file's identity and containment
    before writing a byte, and are tested in both walk modes by
    `packages/agentbundle/tests/unit/test_catalogue_tooling_file_safety.py`.
  - **Existing tests:** `packs/core/tests/skills/work-loop/test_security_primitives.py`,
    whose fallback cases assert refusal today.
  - **Windows CI:** `.github/workflows/build-check-windows.yml`.

> **Plan contract:** this is the implementation strategy. It may change
> substantively only while its Status is `Drafting`. After approval, execution
> observations belong in
> `docs/specs/windows-confined-write/notes/verification-ledger.md`.

## Approach

T1 adds the path-checked mode and the capability query test-first on a
simulated host. T2 runs the Windows module AC-0009 names on the Windows CI job,
with the host-capability mode not patched. T3 records the decision, the architecture line, and the release.

## Constraints

- ADR-0144 D2: standard library only, runnable from the installed skill.
- ADR-0152 D1 to D5.
- `packs/AGENTS.md`: shipped text cites no internal records, and every `.apm/`
  change bumps the core version.
- `file_safety.py` and `_file_safety.py` stay byte-identical, and the
  catalogue-curation guard's parity layer pins that.

## Construction tests

**Integration tests:** none beyond each task's.

**Manual verification:** none.

## Durable-output map

| Durable output | Tasks | Implementation evidence | Closeout evidence |
| --- | --- | --- | --- |
| Decision rationale | T3 | ADR shape lint | ADR-0152 `Accepted` |
| Current architecture | T3 | Architecture review | The capability line names the gap |
| Release history | T3 | Version parity | Patch entry |

## Design (LLD)

### Design decisions

- **One host-capability point:** `_confined_mutation.py` decides the mode in
  one private function, `_host_mode()`, returning `"descriptor"`, `"path-checked"`,
  or `"unsafe"`. It reads `_fs._supports_descriptor_walk()` and
  `hasattr(os.stat_result, "st_file_attributes")`, with no filesystem call. VI-0101 patches only
  `_host_mode()`, so the file-safety module and `os.lstat` stay real.
  `race_free_mutation()` returns `_host_mode() == "descriptor"`.
- **Lexical refusals first:** in the path-checked mode only, every component
  of the target's path relative to its root passes a check for `:`, reserved device names (case-insensitive, with any
  extension), a trailing dot or space, and an absolute, drive-relative,
  `\\?\`, `\\.\`, or UNC form, before any filesystem call. The
  descriptor-walk mode keeps its own checks unchanged.
- **Recorded identities:** before writing, the operation records the root's and
  each ancestor's `(st_dev, st_ino)` from `os.lstat`, refusing a link or reparse
  point at any of them. Containment compares `os.path.normcase` of
  `os.path.realpath` for the target's parent and the root.
- **Create and replace:** the staging file is created by path with
  `O_CREAT|O_EXCL|O_BINARY` and a random name. Before any byte is written, its
  `fstat` identity must equal the `lstat` of its path, its link count must be 1,
  it must not be a reparse point, and its resolved path must be inside the
  resolved root. The bytes are written and fsynced. Exclusive create commits by
  `os.link` then unlinking the staging file; replace commits by `os.replace`.
  After the commit, the target's `lstat` must be a regular file, not a reparse
  point, with link count 1 and the staging file's identity, and every ancestor's
  identity must equal its recorded identity. Any difference raises
  `denied-rollback-failed`.
- **Append:** the target is `lstat`ed and opened by path with
  `O_WRONLY|O_APPEND|O_BINARY`; its `fstat` identity, link count, and reparse
  state must equal the `lstat`. After writing and fsyncing, the open file's
  identity must still equal the in-root path's `lstat` identity and every
  ancestor's recorded identity, or the operation raises `denied-rollback-failed`.
  A failed write before that check truncates back to the prior length, or
  raises `denied-rollback-failed`.
- **Pre-commit point:** a module-level test seam, `_PRE_COMMIT_HOOK`, is called
  with the target path just before the commit call (`os.replace`, `os.link`, or
  the append's write). It is `None` in production. VI-0101 and VI-0201 use it to
  swap an ancestor for a junction or a symlink on a real filesystem.
- **Untrusted admission:** `work-supervisor.py` `_main` runs the check for
  every verb, after parsing arguments and before dispatch, so it precedes the
  run lock that creates `.supervisor/` and its `.gitignore`. It reads the trust
  from the latest pair of `delivery/approvals.jsonl` read at `HEAD` through the
  hardened Git helper, a read with no write, for every verb but `start`. For
  `start` it reads `--code-trust`, the trust the call would record, so an
  owner's re-approval to trusted proceeds and a re-approval to untrusted
  refuses. When the trust is untrusted or
  undetermined and `race_free_mutation()` is false, it refuses
  `untrusted-unsafe-host`. `_supervisor_admission.start` keeps the same check
  beside its `code_trust` validation, for any caller that enters admission
  directly.
- **Means left to code:** whether the path-checked helpers reuse
  `write_confined_regular_file`'s fallback logic or mirror it inside
  `_confined_mutation.py` is `implementation-discovered`. The required property
  is the checks above, with `file_safety.py` and `_file_safety.py` unchanged.

Owned by: T1.

## Tasks

### T1: Path-checked confined writes on a simulated host

- **Depends on:** none
- **Spec behavior:** AC-0001, AC-0002, AC-0003, AC-0004, AC-0005, AC-0006, AC-0007, AC-0008, AC-0010, AC-0011, AC-0012; TDD.
- **Touches:** `packs/core/.apm/skills/work-loop/scripts/_confined_mutation.py`,
  `_supervisor_admission.py`, `work-supervisor.py`, a new
  `packs/core/tests/skills/work-loop/test_confined_mutation_path_checked.py`,
  the admission tests, and the regenerated `.claude/` and `.agents/` copies
  (self-host).
- **Verification mode:** TDD
- **Tests:**
  - **VI-0101 (AC-0001, AC-0002, AC-0003, AC-0004, AC-0005, AC-0006, AC-0007,
    AC-0008, AC-0010):** with `_host_mode()` patched to `"path-checked"`, drive
    each of the three operations on a real temporary directory through:
    - success, with the exact resulting bytes;
    - a symlinked ancestor and a symlinked target;
    - a non-regular target and a hard-linked target;
    - every lexical form AC-0004 lists, asserting no filesystem call ran;
    - a mixed-case target name, which on POSIX only proves the comparison is
      applied (VI-0201 proves case folding);
    - a staging file whose `lstat` differs from its `fstat` (patched there only);
    - a late detection through `_PRE_COMMIT_HOOK`: an ancestor swapped for a
      symlink, a hard link added to the committed target, and an append whose
      in-root path is renamed away.
    With `_host_mode()` patched to `"unsafe"`, each operation refuses
    `denied-unsafe-host`. `race_free_mutation()` follows `_host_mode()`. Each
    refusal before the commit also asserts the prior target's bytes.
  - **VI-0102 (AC-0011):** with `race_free_mutation()` patched false, and a
    snapshot of names, sizes, and digests of the working tree,
    `<spec>/.supervisor/`, and the Git directory unchanged after each refusal:
    - `start --code-trust untrusted` refuses `untrusted-unsafe-host`;
    - a run admitted untrusted with the query true, then resumed with it false,
      refuses on every verb `work-supervisor.py` defines (`next`, `report`,
      `status`, `resolve-effect`), the list read from its argument parser so a
      new verb is covered;
    - an approvals file at `HEAD` that is malformed, or whose working copy says
      trusted while `HEAD` says untrusted, refuses the same way;
    - a re-approval `start --code-trust untrusted` over a trusted `HEAD`
      approval refuses;
    - a re-approval `start --code-trust trusted` over an untrusted `HEAD`
      approval proceeds;
    - `next` with no approvals file at `HEAD` refuses;
    - a trusted run proceeds.
  - **VI-0103 (AC-0012):** `test_security_primitives.py` passes with no edit.
- **Done when:** VI-0101, VI-0102, and VI-0103 pass; `make lint-ruff lint-mypy`
  is clean; and self-host reports no drift. No work-loop eval covers this
  helper, and the ledger records that.

### T2: The Windows module runs unpatched on a real host

- **Depends on:** T1
- **Spec behavior:** AC-0009; goal-based.
- **Touches:** `packs/core/tests/skills/work-loop/test_confined_mutation_windows.py`,
  `.github/workflows/build-check-windows.yml`, and `tools/lint-ci-parity.py`.
- **Verification mode:** goal-based
- **Tests:**
  - **VI-0201 (AC-0009):** on Windows, with nothing patched but
    `_PRE_COMMIT_HOOK`, the module creates real junctions and covers the cases
    AC-0009 lists. For AC-0005 it passes the root and the target in a different
    letter case and expects success, which default NTFS's case-insensitive
    lookup makes possible. It reads the root's short-name alias with
    `cmd /c for %I in ("<path>") do @echo %~sI`, passes that alias as the root
    and the target in long form, and expects success, which only a resolved,
    case-folded comparison allows. The module fails when the alias equals the
    long name. The job step runs it with JUnit output
    and fails when any case is skipped or none is collected.
- **CI setup:** before that step, the job runs `fsutil 8dot3name set <drive> 0`
  on the volume holding the test's temporary directory, so new directories get
  short names.
- **Done when:** VI-0201 passes in the `build-check-windows` job on the PR.

### T3: Decision, architecture, and release

- **Depends on:** T1
- **Spec behavior:** Durable Outputs rows; goal-based.
- **Touches:** `docs/adr/0152-*.md`, `docs/adr/README.md`,
  `docs/architecture/runtime-security-primitives.md`, the `Status` line of
  `docs/specs/acceptance-authority-and-evidence/spec.md`, core manifests, and
  `docs/product/changelog.d/`.
- **Verification mode:** goal-based
- **Tests:**
  - **VI-0301:** the ADR shape lint and the spec-status lint pass, ADR-0152 is
    `Accepted`, Slice 1's `Status` reads `Shipped (superseded in part by
    ADR-0152 — …; everything else stands)`, and the architecture page names the
    path-checked mode, the residual race, and the untrusted refusal.
- **Done when:** VI-0301 passes and core's version is patch-bumped in both manifests.

## Rollout

- **Delivery:** one core patch. Rollback is reinstalling the prior core release.
- **Infrastructure:** none.
- **External-system integration:** none.
- **Deployment sequencing:** this ships before `execution-supervisor-cutover`'s
  switch, which needs it for that spec's Windows run.

## Risks

- **Windows behaviour only CI can see:** `os.link`, `os.replace`, reparse
  attributes, and `st_ino` stability on NTFS. Mitigation: T2 gates on a real
  host before merge.
- **Junction creation in tests:** VI-0201 uses `_winapi.CreateJunction`, which
  CPython ships on Windows without documenting, and falls back to
  `cmd /c mklink /J` when it is absent. The Windows job settles which.

## Changelog

<!-- Approvals only. -->

- 2026-10-29: spec approved by eugenelim
- 2026-10-29: plan approved by eugenelim
