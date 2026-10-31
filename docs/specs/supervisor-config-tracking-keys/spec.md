# Spec: Supervisor config tracking keys

- **Status:** Draft <!-- Draft | Approved | Implementing | Shipped | Archived -->
- **Owner:** Platform Core
- **Plan:** [`plan.md`](plan.md)
- **Constrained by:** ADR-0144
- **Brief:** none
- **Discovery:** docs/product/captured/supervisor-common-config-residue.md
- **Depends on:** none
- **Contract:** none — no schema or published interface changes; the refusal codes `attempt-residue`, `attempt-refused`, and `denied-git-control-state` keep their meaning and wording
- **Shape:** service

> **Spec contract:** this document defines what "done" means. The implementing
> PR must match this spec, or update it. Verification must be derivable from it.
>
> **Protected semantic-policy contract.** `Contract`, `Scope and Non-goals`,
> `Durable Outputs`, `Agent Rules`, `Testing Strategy`, `Acceptance Criteria`,
> `Terminal Intent`, and `Accepted Risk` are approval-bound or explicitly
> review-authorized. A change follows its owning amendment, review, or risk
> decision. `Outcome`, `What Changes`, `Follow-ons`, and `Assumptions` are
> working material that may be corrected without changing accepted authority.

## Outcome

Maintainers who run full-mode `work-loop` in a repository with many linked worktrees get an open attempt that survives another session's branch-tracking writes to the shared Git config — `git push -u`, `git checkout -b <branch> origin/<branch>`, `gh pr checkout`, and `gh repo set-default` — so nobody edits the shared config or re-baselines a stored attempt digest to clear a false `attempt-residue`. Success is that those writes leave an open attempt admissible, while every other config change during an attempt still refuses it, and a config the supervisor cannot read with certainty still refuses on any byte change.

## What Changes

- The digest the attempt manifest records for each `config` and `config.worktree` file covers a filtered view of the file, not its raw bytes — `work-loop/scripts/_supervisor_attempt.py`.
- The same filtered digest serves the hardened Git helper's pre-call control check — `work-loop/scripts/_supervisor_attempt.py` (`_control_check`).
- A manifest recorded with a raw-file digest is still compared against the raw file — `work-loop/scripts/_supervisor_attempt.py`.
- A Git-free config-filter suite runs on POSIX CI and on the Windows build-check job — `packs/core/tests/skills/work-loop/`, `.github/workflows/build-check-windows.yml`.
- The supervisor reference and the runtime security architecture describe the filtered fingerprint — `work-loop/references/supervisor.md`, `docs/architecture/runtime-security-primitives.md` §11.

## Scope and Non-goals

This spec owns which config lines the attempt manifest fingerprints. It narrows
one term of the
[`execution-supervisor-attempt-security`](../execution-supervisor-attempt-security/spec.md)
contract — the "every repository and worktree `config` file" member of its Git
control state definition — to the config fingerprint defined below. Every other
member of that definition, the manifest's lifecycle, residue, and clearing are
unchanged.

Non-goals:

- The start-time refusal of code-running Git settings (`unsupported-git-config`)
  and the hardened helper's neutralising flags are unchanged.
- No supervisor `git` call reads branch tracking or `gh` settings, so this spec
  adds no control over what those keys mean to Git; it only stops counting them
  as control state.
- `HEAD`, the branch ref, `packed-refs`, `refs/replace/`, `info/`, `hooks/`,
  `commondir`, `objects/info/alternates`, and the `.git` gitfile keep their
  current fingerprints.
- A sibling session's writes to anything other than the allowlisted keys still
  refuse an attempt; making the supervisor tolerant of other shared-state writes
  is out of scope.

## Durable Outputs

| Semantic role | Applicability | Destination | Owner | Expected evidence | Closeout condition |
| --- | --- | --- | --- | --- | --- |
| User documentation | Adopters read which Git state an open attempt protects and why a sibling's tracking write no longer refuses. | `packs/core/.apm/skills/work-loop/references/supervisor.md` (the open-attempt rule and the `attempt-residue` refusal row) | Core pack maintainers | Link check; self-host projection current | The reference names the excluded keys and the raw-file fallback in one place. |
| Current architecture | The attempt check's definition of Git control state narrows. | `docs/architecture/runtime-security-primitives.md` §11 | `agentbundle` security maintainers | Security-reviewer pass on the diff | §11 states the config fingerprint, the excluded keys, and the fail-closed fallback. |
| Decision rationale | The contract this spec narrows has a single owner per fact. | This spec's Definitions (the owner) and a one-sentence pointer beside the Git control state definition in `docs/specs/execution-supervisor-attempt-security/spec.md`, with no criteria change there | Platform Core decision-maker | Shaping review; diff of the attempt-security spec limited to that sentence | The older definition points to this spec's config fingerprint and its criteria are unchanged. |
| Release history | Live supervisor code changes. | `packs/core/pack.toml`, `packs/core/.claude-plugin/plugin.json`, a fragment created by `tools/changelog.py new` | Core pack release maintainers | AC-0011, AC-0012 | The release carries one changelog fragment naming the fix. |
| Captured-item closure | The defect has a captured item, which this delivery adds to `main`. | `docs/product/captured/supervisor-common-config-residue.md` | Core pack maintainers | The item's status | The item exists on `main`, is closed, and points at this spec; whichever of this PR and the PR that first captured it merges second resolves the overlap. |

## Agent Rules

### Always do

- Fail closed: when any doubt exists about a config line, fingerprint the whole
  raw file exactly as the raw-file fingerprint does.
- Read config files directly, through the confined regular-file read the
  attempt check already uses, so the check stays valid inside the hardened
  helper's pre-call control check.
- Get a security-reviewer pass on the spec and on the implementation diff
  before merge.

### Ask first

- Adding any key to the excluded set beyond the five branch-tracking variables
  and `remote.<name>.gh-resolved`.
- Changing the start-time code-running refusal list or the hardened helper's
  fixed flags.
- Editing the shipped `execution-supervisor-attempt-security` spec beyond the one-sentence pointer to this spec's config fingerprint.

### Never do

- Launch a `git` process, or read effective config through Git, to compute a
  fingerprint.
- Follow an include, or read any file other than the `config` or
  `config.worktree` being fingerprinted.
- Clear a refusal by editing a shared `.git/config` or rewriting a digest in the
  supervisor store, in a test or anywhere else; tests build their own temporary
  repositories.
- Add a new module under `work-loop/scripts/` or a dependency outside the
  Python standard library.

## Testing Strategy

- **Config filter (AC-0001, AC-0002, AC-0003, AC-0004, AC-0005, AC-0006):** TDD
  over config bytes in a Git-free suite, because the filter is a pure function
  of a file's bytes and the same suite must run on Windows, where the git-backed
  supervisor suites do not run.
- **Attempt check over a shared common directory (AC-0007, AC-0008, AC-0009):**
  TDD as integration tests in the git-backed attempt suite, with a real linked
  sibling worktree whose own `git push -u`, `git config`, and `git branch -D`
  write the common config during an open attempt.
- **Regression and platforms (AC-0010, AC-0013):** goal-based: the existing
  git-backed supervisor suites pass unmodified in the `supervisor-integration`
  lane, and the config-filter suite passes with no skipped case on POSIX CI and
  on the Windows build-check job.
- **Release (AC-0011, AC-0012):** goal-based: version parity and changelog
  validation, checked against freshly fetched `origin/main` right before push.

## Acceptance Criteria

### Definitions

- **Branch-tracking key.** In a `[branch "<name>"]` section, the variable
  `remote`, `merge`, `pushremote`, `rebase`, or `description`, compared
  case-insensitively. A `[branch]` section with no subsection holds no
  branch-tracking key.
- **gh-resolved key.** `gh-resolved` in a `[remote "<name>"]` section, compared
  case-insensitively.
- **Excluded line.** A branch-tracking key line, a gh-resolved key line, a
  `[branch "<name>"]` header, and a blank or comment line inside a
  `[branch "<name>"]` section.
- **Clean parse.** A config file parses cleanly when it decodes as UTF-8 and
  every line, with a trailing `\n` or `\r\n` removed, is blank, a comment, a
  `[section]` or `[section "subsection"]` header, or a `name` or `name = value`
  line whose value has balanced double quotes and does not end in a
  continuation backslash; when no section is `include` or `includeIf`; and when
  every key inside a `[branch "<name>"]` section is a branch-tracking key.
- **Config fingerprint.** For a `config` or `config.worktree` file in the
  pinned Git directory or common directory: when the file parses cleanly, the
  digest of the file with every excluded line removed, in a form no raw-file
  digest can equal; otherwise the raw-file fingerprint.
- **Raw-file fingerprint.** The sha256 of the file's bytes, as the attempt
  manifest records every other Git control state file.

### Criteria

Config filter

- [ ] **AC-0001.** Two config files that differ only in excluded lines have the
  same config fingerprint.
- [ ] **AC-0002.** Two cleanly parsing config files that differ in any line
  that is not an excluded line — including `core.hooksPath`, `remote.origin.url`,
  `remote.origin.fetch`, `user.email`, a `[branch]` section with no subsection,
  and a `[core]` section placed after a `[branch "<name>"]` section — have
  different config fingerprints.
- [ ] **AC-0003.** A config file that does not parse cleanly — one holding a
  continuation line, a multi-line quoted value, a `[branch.<name>]` legacy
  header, an `include` or `includeIf` section, a key inside a
  `[branch "<name>"]` section that is not a branch-tracking key, or bytes that
  are not UTF-8 — has the raw-file fingerprint as its config fingerprint.
- [ ] **AC-0004.** No cleanly parsing config file's config fingerprint equals
  any file's raw-file fingerprint.
- [ ] **AC-0005.** A config file and the same file with every `\n` replaced by
  `\r\n` have the same config fingerprint.
- [ ] **AC-0006.** Computing Git control state launches no process.

Attempt check over a shared common directory

- [ ] **AC-0007.** During an open attempt in a linked worktree, each of these
  writes to the common config by a sibling linked worktree leaves the attempt
  admissible — `report` admits its result and the following `next` answers no
  `attempt-residue`: `git push -u` of a new branch, setting
  `branch.<name>.remote`, `merge`, `pushremote`, `rebase`, or `description`,
  setting `remote.origin.gh-resolved`, and `git branch -D` of a branch whose
  section carries only branch-tracking keys.
- [ ] **AC-0008.** During an open attempt in a linked worktree, each of these
  changes to the common config or to the worktree's `config.worktree` refuses
  the attempt with `attempt-residue` at `next` and `attempt-refused` at
  `report`, naming that config file: setting `core.hooksPath`, adding
  `include.path`, changing `remote.origin.url`, changing `user.email`, adding a
  `[core]` section after a `[branch "<name>"]` section, adding a non-tracking
  key inside a `[branch "<name>"]` section, and, in a config that does not parse
  cleanly, changing a branch-tracking key.
- [ ] **AC-0009.** An open attempt whose manifest holds the raw-file
  fingerprint for a config file — as one recorded by a supervisor release
  without the config fingerprint does, including a `regenerate` request issued
  before the installed skill is regenerated — is admissible when the file's
  bytes are unchanged and refuses on any byte change to that file.

Regression, platforms, and release

- [ ] **AC-0010.** The git-backed supervisor suites the `supervisor-integration`
  lane runs pass with no existing test case modified or removed.
- [ ] **AC-0011.** `packs/core/pack.toml` and
  `packs/core/.claude-plugin/plugin.json` carry the same version, which is the
  next patch above the core version at the merge base with freshly fetched
  `origin/main`.
- [ ] **AC-0012.** `tools/changelog.py validate` passes with one new fragment
  for this change.
- [ ] **AC-0013.** The config-filter suite passes with zero skipped cases on a
  POSIX CI lane and on the Windows build-check job.

## Follow-ons

none

## Terminal Intent

`code` — implement the config fingerprint, its use in the attempt manifest and
the hardened helper's pre-call check, the raw-file comparison for older
manifests, the Git-free suite on both platforms, and the reference updates.

## Accepted Risk

The excluded keys change what a later Git command run outside the supervisor
does: `branch.<name>.pushremote` and `remote.<name>.gh-resolved` choose where a
controller's own `git push` or `gh pr create` goes. A worker attempt can change
them without refusal. No supervisor `git` call reads them, and the push and
pull-request effects run outside the supervisor under controller authority, so
this narrows what ADR-0144 D11 protects to state a supervisor call consumes.
The controller is trusted and owns every push and pull request.

A `[branch "<name>"]` key outside the five branch-tracking variables — one a
future `gh` release or an editor writes — makes the file fail the clean parse.
The attempt then refuses on any change to that file, as it does without this
spec; that false refusal is the accepted cost of keeping the excluded set
narrow.

The Platform Core decision-maker accepted this risk on 2026-10-31.

## Assumptions

none
