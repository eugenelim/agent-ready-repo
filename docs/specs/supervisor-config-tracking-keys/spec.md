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

Maintainers who run full-mode `work-loop` in a repository with many linked worktrees get an open attempt that survives another session's branch-tracking writes to the shared Git config — `git push -u`, `git checkout -b <branch> origin/<branch>`, `gh pr checkout`, and `gh repo set-default` — so nobody edits the shared config or re-baselines a stored attempt digest to clear a false `attempt-residue`. Success is that those writes, in the exact form Git writes them, leave an open attempt admissible, while every other byte change to a config file during an attempt still refuses it.

## What Changes

- The digest the attempt manifest records for each `config` and `config.worktree` file covers the file with its canonical tracking blocks removed, not its raw bytes — `work-loop/scripts/_supervisor_attempt.py`.
- The same digest serves the hardened Git helper's pre-call control check — `work-loop/scripts/_supervisor_attempt.py` (`_control_check`).
- A manifest entry is compared in the form it was recorded in, so a manifest recorded with the raw-file fingerprint is still compared against the raw file — `work-loop/scripts/_supervisor_attempt.py`.
- A config-fingerprint suite that needs no repository runs on POSIX CI and on the Windows build-check job, each with a zero-skip check — `packs/core/tests/skills/work-loop/`, `.github/workflows/`.
- The supervisor reference, the controller's effect guidance, and two architecture pages describe the config fingerprint — `work-loop/references/supervisor.md`, `docs/architecture/runtime-security-primitives.md` §11, `docs/architecture/work-loop-execution-supervisor.md` § Attempts.

## Scope and Non-goals

This spec owns which config bytes the attempt manifest fingerprints. It narrows
one term of the
[`execution-supervisor-attempt-security`](../execution-supervisor-attempt-security/spec.md)
contract — the "every repository and worktree `config` file" member of its Git
control state definition — to the config fingerprint defined below. Every other
member of that definition, the manifest's lifecycle, residue, and clearing are
unchanged.

Non-goals:

- The start-time refusal of code-running Git settings (`unsupported-git-config`)
  and the hardened helper's neutralising flags are unchanged.
- No supervisor action depends on an excluded key. The admission read of the
  effective config reads them along with every other key, and nothing the
  supervisor decides or runs uses their values; this spec stops counting them
  as control state and adds no control over what they mean to Git.
- `HEAD`, the branch ref, `packed-refs`, `refs/replace/`, `info/`, `hooks/`,
  `commondir`, `objects/info/alternates`, and the `.git` gitfile keep their
  current fingerprints.
- A sibling session's writes to anything other than a canonical tracking block
  still refuse an attempt; making the supervisor tolerant of other shared-state
  writes is out of scope.

## Durable Outputs

| Semantic role | Applicability | Destination | Owner | Expected evidence | Closeout condition |
| --- | --- | --- | --- | --- | --- |
| User documentation | Adopters read which Git state an open attempt protects and why a sibling's tracking write no longer refuses. | `packs/core/.apm/skills/work-loop/references/supervisor.md` (the open-attempt rule and the `attempt-residue` refusal row) | Core pack maintainers | Link check; self-host projection current | The reference names the excluded keys and states that any other byte change still refuses. |
| Controller guidance | The Accepted Risk holds only while the controller pushes, pulls, and merges with explicit arguments. | `packs/core/.apm/skills/work-loop/references/supervisor.md` § External effects | Core pack maintainers | Self-host projection current | The section tells the controller to pass an explicit remote, ref, and pull request, or to verify them, for every push, pull, and merge. |
| Current architecture | The attempt check's definition of Git control state narrows. | `docs/architecture/runtime-security-primitives.md` §11 | `agentbundle` security maintainers | Security-reviewer pass on the diff | §11 states the config fingerprint, the excluded keys, and that every other byte stays in the digest. |
| Current architecture | The supervisor architecture states what a manifest records. | `docs/architecture/work-loop-execution-supervisor.md` § Attempts | Core pack maintainers | Diff of that section | The section says config entries record the config fingerprint, not size and digest. |
| Decision rationale | The contract this spec narrows has a single owner per fact. | This spec's Definitions (the owner) and a pointer beside the Git control state and Manifest definitions in `docs/specs/execution-supervisor-attempt-security/spec.md`, with no criteria change there | Platform Core decision-maker | Diff of the attempt-security spec limited to that pointer | The older definitions point to this spec and say config entries record the config fingerprint instead of size and sha256; its criteria are unchanged. |
| Release history | Live supervisor code changes. | `packs/core/pack.toml`, `packs/core/.claude-plugin/plugin.json`, a fragment created by `tools/changelog.py new` | Core pack release maintainers | AC-0011, AC-0012 | The release carries one changelog fragment naming the fix. |
| Captured-item closure | The defect has a captured item, which this delivery adds to `main`. | `docs/product/captured/supervisor-common-config-residue.md` | Core pack maintainers | The item's status | The item exists on `main`, is closed, and points at this spec; whichever of this PR and the PR that first captured it merges second resolves the overlap. |

## Agent Rules

### Always do

- Fail closed: remove a byte from the digest only when it lies inside a
  canonical tracking block; every other byte stays in, verbatim.
- Compute the config fingerprint from the bytes of the confined regular-file
  read the attempt check already makes, so the check stays valid inside the
  hardened helper's pre-call control check.
- Get a security-reviewer pass on the spec and on the implementation diff
  before merge.

### Ask first

- Adding any key to the excluded set, or widening the canonical form.
- Changing the start-time code-running refusal list or the hardened helper's
  fixed flags.
- Editing the shipped `execution-supervisor-attempt-security` spec beyond the
  pointer to this spec's config fingerprint.

### Never do

- Launch a process, or read effective config through Git, to compute a
  fingerprint.
- Parse a config file into sections and keys, follow an include, or read any
  file other than the `config` or `config.worktree` being fingerprinted.
- Clear a refusal by editing a shared `.git/config` or rewriting a digest in the
  supervisor store, in a test or anywhere else; tests build their own temporary
  repositories.
- Add a new module under `work-loop/scripts/` or a dependency outside the
  Python standard library.

## Testing Strategy

- **Config fingerprint (AC-0001, AC-0002, AC-0003, AC-0004, AC-0006, AC-0014, AC-0015, AC-0016):**
  TDD over config bytes in a suite that needs no repository and no supervisor
  run, because the fingerprint is a pure function of one read's bytes and the
  same suite must run on Windows, where the git-backed supervisor suites do not
  run. Its only process is `git config --file` over AC-0003's files, which
  checks that each shape means to Git what the case claims, on the POSIX CI Git
  and on Git for Windows.
- **Attempt check over a shared common directory (AC-0007, AC-0008, AC-0009):**
  TDD as integration tests in the git-backed attempt suite, with a real linked
  sibling worktree whose own `git push -u`, `git config`, and `git branch -D`
  write the common config during an open attempt.
- **Regression and platforms (AC-0010, AC-0013):** goal-based: the existing
  git-backed supervisor suites pass unmodified in the `supervisor-integration`
  lane, and the config-fingerprint suite passes with a zero-skip check on POSIX
  CI and on the Windows build-check job.
- **Release (AC-0011, AC-0012):** goal-based: version parity and changelog
  validation, checked against freshly fetched `origin/main` right before push.

## Acceptance Criteria

### Definitions

Bytes are split into lines only at `\n`; a line includes its `\n`. Every match
below is exact and case-sensitive, in the lower-case form Git writes.

- **Strippable file.** A file that ends in `\n`, contains no `\r` byte anywhere,
  and has no line whose last byte before `\n` is `\`. The precondition is
  file-wide: when any part of the file fails it, nothing in the file is a
  canonical tracking block.

- **Excluded keys.** Exactly `branch.<name>.remote`, `branch.<name>.merge`,
  `branch.<name>.pushremote`, `branch.<name>.rebase`,
  `branch.<name>.description`, and `remote.<name>.gh-resolved`.
- **Subsection.** One or more bytes, none of them `"`, `\`, a control byte
  (0x00–0x1F), or 0x7F.
- **Tracking value.** Zero or more bytes, none of them `"`, `\`, `;`, `#`, a
  control byte, or 0x7F.
- **Canonical branch block.** In a strippable file, a line exactly
  `[branch "<subsection>"]\n`, followed by one or more lines each exactly
  `\t<key> = <tracking value>\n` with `<key>` one of `remote`, `merge`,
  `pushremote`, `rebase`, `description`, where the line after the block begins
  with `[` or the block ends the file.
- **Canonical gh-resolved line.** In a strippable file, a line exactly
  `\tgh-resolved = <tracking value>\n` that follows a line exactly
  `[remote "<subsection>"]\n`, where every line between them begins with `\t`
  followed by a lower-case ASCII letter.
- **Canonical tracking block.** A canonical branch block or a canonical
  gh-resolved line.
- **Raw-file fingerprint.** The size-and-sha256 entry, `<size>:<sha256hex>`,
  that the manifest records for every other Git control state file.
- **Config fingerprint.** For a `config` or `config.worktree` file in the
  pinned Git directory or common directory that the attempt check reads as a
  regular file: `config-view:` followed by the raw-file fingerprint form of the
  file's bytes with every canonical tracking block removed.

### Criteria

Config fingerprint

- [ ] **AC-0001.** Two config files that differ only in canonical tracking
  blocks have the same config fingerprint.
- [ ] **AC-0002.** Two config files that differ in any byte outside canonical
  tracking blocks have different config fingerprints, including when the
  differing line is `core.hooksPath`, `remote.origin.url`,
  `remote.origin.fetch`, `user.email`, a `[branch]` section with no
  subsection, a `[core]` section placed after a canonical branch block, an
  `uploadpack`, `receivepack`, `pushurl`, `vcs`, or `proxy` key in the same
  `[remote "<name>"]` block as a canonical gh-resolved line, or a code-running
  key the start-time refusal names placed directly before or after a canonical
  tracking block.
- [ ] **AC-0003.** Each of these files has nothing removed, so its config
  fingerprint is `config-view:` followed by the raw-file fingerprint form of the
  whole file. Bytes are written as Python bytes literals.
  - Header shapes: `[branch "x"][core]hooksPath = /evil\n`,
    `[branch "x\\\\"][filter "y"]clean = "/evil"]\n`,
    `[branch "x"] [remote "origin"]url = /evil\n`,
    `[branch "x"]\r[core]\n\thookspath = /evil\n`, `[Branch "x"]\n\tremote = o\n`,
    and a byte-order mark before the first header.
  - Key and value shapes: `\tRemote = o\n`, `\tremote=o\n`, `\tremote = "o"\n`,
    a value holding `;` or `#`, a value ending in `\`, an `include` or
    `includeIf` section, and a tracking key followed by a line that is not a
    header (`[branch "x"]\n\tremote = o\n\thookspath = /evil\n`).
  - Continuation shapes, each with a canonical block after a line Git joins to
    the next: `[remote "origin"]\n\turl = /x\\\r\n[branch "b"]\n\tremote = o\n[core]\n\thooksPath = /evil\n`;
    `[remote "origin"]\n\turl = /x\\\r\n\tgh-resolved = base\n\tpushurl = /evil\n`;
    `[remote "o"]\n\turl = /good\\\r\n[branch "b"]\n\tremote = one\n[core]\n\tbare = false\n`
    and the same with `remote = two`;
    `[remote "o"]\n\turl = /good\\\r\n\tgh-resolved = one\n` and the same with
    `gh-resolved = two`;
    `[include]\n\tpath = /x\\\r\n[branch "b"]\n\tremote = o\n[core]\n\tbare = false\n`;
    and `[remote "o"]\n\turl = /good\\\n[branch "b"]\n\tremote = o\n[core]\n\tbare = false\n`.
  - Line-ending shapes: a file with `\r\n` line endings, a `\r` inside a value,
    and a file whose last byte is not `\n`.
- [ ] **AC-0004.** Every config fingerprint begins `config-view:`, and no
  raw-file fingerprint does.
- [ ] **AC-0006.** Computing Git control state creates no process.
- [ ] **AC-0014.** A key is removed only under its exact excluded name; near
  misses such as `gh-resolved-x`, `remotes`, `Merge`, and `gh-resolved` inside a
  `[branch "<name>"]` block stay in the config fingerprint.
- [ ] **AC-0015.** The config fingerprint is computed from the bytes of the
  single confined read the attempt check makes of that file.
- [ ] **AC-0016.** A symlinked, special, or oversized config entry keeps its
  `link:…`, `special`, or `unsafe` value.

Attempt check over a shared common directory

- [ ] **AC-0007.** During an open attempt in a linked worktree, each of these
  writes to the common config by a sibling linked worktree leaves the attempt
  admissible — `report` admits its result and the following `next` answers no
  `attempt-residue`: `git push -u` of a new branch, setting
  `branch.<name>.remote`, `merge`, `pushremote`, `rebase`, or `description`,
  setting `remote.origin.gh-resolved`, and `git branch -D` of a branch whose
  section carries only excluded keys.
- [ ] **AC-0008.** During an open attempt in a linked worktree, each of these
  changes to the common config or to the worktree's `config.worktree` refuses
  the attempt with `attempt-residue` at `next` and `attempt-refused` at
  `report`, naming that config file: setting `core.hooksPath`, adding
  `include.path`, changing `remote.origin.url`, changing `user.email`, adding a
  `[core]` section after a `[branch "<name>"]` block, adding a non-excluded key
  inside a `[branch "<name>"]` block, and changing an excluded key written in a
  non-canonical shape.
- [ ] **AC-0009.** During an open attempt, each manifest entry for a config file
  is compared in the form it was recorded in: a `config-view:` value against
  the config fingerprint, a `<size>:<sha256hex>` value against the raw-file
  fingerprint, and a `link:…`, `special`, or `unsafe` value against the attempt
  check's current result for that entry; so a manifest recorded by a release
  without the config fingerprint — including a `regenerate` request issued
  before the installed skill is regenerated — admits unchanged bytes and
  refuses any byte change.

Regression, platforms, and release

- [ ] **AC-0010.** The git-backed supervisor suites the `supervisor-integration`
  lane runs pass with no existing test case modified or removed.
- [ ] **AC-0011.** `packs/core/pack.toml` and
  `packs/core/.claude-plugin/plugin.json` carry the same version, which is the
  next patch above the core version at the merge base with freshly fetched
  `origin/main`.
- [ ] **AC-0012.** `tools/changelog.py validate` passes with one new fragment
  for this change.
- [ ] **AC-0013.** The config-fingerprint suite passes with zero skipped cases,
  as `tools/require-junit-ran-without-skips.py` reports over its JUnit output,
  on a POSIX CI lane and on the Windows build-check job.

## Retired identifiers

- AC-0005
- VI-0105

## Follow-ons

none

## Terminal Intent

`code` — implement the config fingerprint, its use in the attempt manifest and
the hardened helper's pre-call check, form-preserving comparison for older
manifests, the config-fingerprint suite on both platforms, and the documentation updates.

## Accepted Risk

A worker attempt can change any excluded key without refusal, and each one
steers a later command the controller runs outside the supervisor:

- `branch.<name>.remote` sets where a bare `git push` or `git pull` goes, and
  its value may be a URL rather than a remote name.
- `branch.<name>.merge` sets the destination branch of a push under
  `push.default=upstream`, and which pull request a `gh pr view`, `gh pr checks`,
  or `gh pr merge` with no argument resolves.
- `branch.<name>.pushremote` sets where a bare `git push` goes.
- `branch.<name>.rebase` sets how `git pull` integrates; `interactive` opens an
  editor.
- `branch.<name>.description` is shown by `git branch` and used in
  request-pull and format-patch cover text.
- `remote.<name>.gh-resolved` sets the base repository `gh` uses.

No supervisor action depends on these values. The risk is acceptable on one
condition: the controller, which is trusted and owns every push, pull, and
merge, passes an explicit remote, ref, and pull request to each, or verifies
them before acting.

A `[branch "<name>"]` key outside the excluded set, or an excluded key in a
shape Git does not write, stays in the digest, so the attempt refuses on any
change to it, as it does without this spec. That false refusal is the accepted
cost of keeping the excluded set and the canonical form narrow.

Reinstalling an older core release is safe only when no attempt is open and no
refusal stands; attempts close at `report`. If the older release is installed
while an attempt is open, it cannot match a `config-view:` value, so it
refuses that attempt and records the refusal in the store. Reinstalling the
newer release leaves that refusal standing: `next` answers `attempt-residue`
until the paths match and `next` clears it, and the attempt's work is then
re-issued as a new request, not reported. No store edit is a recovery.

The Platform Core decision-maker accepted this risk, in full, on 2026-10-31.

## Assumptions

- Technical: which `[branch "<name>"]` and `[remote "<name>"]` keys
  `gh pr checkout` and `gh repo set-default` write, and in what form — a key
  outside the excluded set, or a non-canonical form, keeps the false refusal for
  repositories where those commands run (settled by: a T1 probe if `gh` can run
  those commands offline; otherwise the fail-closed rule decides and nothing in
  the contract moves).
