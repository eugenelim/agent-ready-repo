# Spec: atomic-write-symlink-harden

- **Status:** Shipped <!-- Draft | Approved | Implementing | Shipped | Archived -->
- **Owner:** eugenelim
- **Plan:** [`plan.md`](plan.md)
- **Constrained by:** none
- **Brief:** none
- **Discovery:** none
- **Contract:** none
- **Shape:** service

> **Spec contract:** this document defines what "done" means. The implementing
> PR must match this spec, or update it. Verification must be derivable from it.
>
> **Not every section is contract.** `Boundaries`, `Testing Strategy` and
> `Acceptance Criteria` are what a completion gate reads, and an amendment
> changes them. `Objective`, `Durable Outputs`, `Follow-ons` and `Assumptions`
> are working material: they orient a reader and an author corrects them in place
> as the work teaches, without an amendment and without a review round.

<!-- Mode: full. Risk trigger: security boundary — this changes a guarding
control on a file-write path. `security-reviewer` is dispatched on the diff. -->

## Objective

An adopter running `agentbundle catalogue init` against a directory they do not
exclusively control — a shared or world-writable parent, or a path under `/tmp`
— cannot have another local user redirect the write by planting a symlink ahead
of the run. The catalogue tooling's atomic write stages its content under a name
nobody can derive from the destination, so a link left lying in the target
directory is never opened, and the file the adopter asked for lands as a regular
file, with its usual permissions, at the path they named.

The control reaches two entries: the staging path and the destination. It does
not reach the directories above them — an ancestor that is already a symlink, or
one swapped for a symlink mid-run, still redirects the whole operation — and it
does not defeat an attacker who watches the directory and substitutes the staging
entry for as long as that entry exists. The two need different missing
primitives — ancestor confinement needs a directory handle held across the whole
operation, and binding the move to the file the helper created needs a
privileged call with no portable equivalent — and both are recorded as residual
risk in the plan.

Success for a legitimate run is narrower than "nothing changed": it is that the
helper's own invariants below hold, that the existing unit suite passes with no
test modified, and that one `catalogue init` into an empty directory reports the
same created-file list and exit code as before.

## Durable Outputs

| Semantic role | Applicability | Destination | Owner | Expected evidence | Closeout condition |
| --- | --- | --- | --- | --- | --- |
| Release history | Applicable — a non-cosmetic package change ships a version | `packages/agentbundle/CHANGELOG.md`, `docs/product/changelog.md`, `packages/agentbundle/README-pypi.md` | implementing PR | An entry naming the hardened write, present in all three, at one version | Entries exist and the three headings agree on the version |
| Interface compatibility | Applicable — the version literal is pinned in three code surfaces | `packages/agentbundle/agentbundle/version.py`, `packages/agentbundle/pyproject.toml`, `tests/roster/test_okf_catalogue_discovery.py` | implementing PR | All three read one version, higher than `origin/main` | The roster pin is green and the version advanced |
| Current product truth | Not applicable | — | — | — | No user-visible behaviour changes; nothing in `docs/guides/` describes the temporary-path mechanism |
| Decision rationale | Not applicable | — | — | — | The function's contract is unchanged, so there is no decision for an ADR to record |
| Current architecture | Not applicable | — | — | — | No module, boundary, or ownership changes |

## Boundaries

### Always do

- Place the temporary file in the destination's own parent directory, so the
  final move stays on one filesystem and remains atomic.
- Remove the temporary file when the write fails partway, leaving no stray
  artifact in the adopter's tree — the behaviour the current implementation
  already provides.
- Keep the exported `atomic_write` alias, its name, and its
  `(dest: Path, content: bytes) -> None` signature exactly as they are.

### Ask first

- Any change to where `--target` is allowed to point.
- Any change to the permission bits a written file ends up with.
- Any test added outside `packages/agentbundle/tests/unit/`.

### Never do

- Do not validate a caller's `dest` and refuse it, and do not add any error path
  the caller's own input can reach. The single new failure is the kernel refusing
  a staging-name collision with `FileExistsError`, which rejects an attacker's
  planted entry; nothing a legitimate caller passes can produce it.
- Do not touch the two sibling helpers in `agentbundle/build/projections/`.
  They are already on the safe pattern, and the owner scoped them out.
- Do not add a module, package, shared-helper boundary, or top-level directory;
  the repair stays inside the existing function.
- Do not add a dependency; `os` and `contextlib` are in the standard library and
  already used by this module.
- Do not change the bytes any caller writes, the set of files a run produces, or
  the order in which they are produced.

## Testing Strategy

- **The planted-symlink outcomes: TDD.** Each is a compressible invariant over
  one function — plant a link, call the function, read two paths — so a unit test
  states it directly and can be shown to fail against the current code.
- **The exclusive-creation outcome: TDD.** This is the load-bearing security
  property and it is directly checkable: fix the staging name for the duration of
  one test, plant a symlink there, and observe the call fail with the link's
  target untouched. A test that instead plants links at a list of plausible names
  would only ever prove the names on that list.
- **The distinct-staging-path outcome: TDD.** Two calls and a spy on the move
  observe it directly. It is the weaker half of the pair — exclusive creation is
  what makes a guessed name safe, and this is what makes guessing hard.
- **The temporary-file and exception outcomes: TDD.** Same shape: force a
  failure, then list the directory. A unit test is the only surface that can
  drive those branches.
- **The permission outcome: TDD, driven over several umasks.** A file written
  by the previous implementation is the comparison value, so the test writes one
  in the same directory under the same umask and compares against it masked to
  `0o664`. Naming a literal mode instead would pin the runner's umask rather
  than the property. The test sets the umask itself rather than inheriting it,
  because under the usual `022` several distinct modes produce identical files —
  `002` is what separates a tightened mode from a correct one, and `000` is what
  separates "not world-writable" from "whatever `Path.write_bytes` asked for".
- **Unchanged tooling output: goal-based check, plus one manual run.** The
  existing `packages/agentbundle/tests/unit/` suite is run unmodified; what it
  proves is bounded by the assertions already in it, because no test in it
  compares a run's whole output manifest against a baseline. A single real
  `agentbundle catalogue init` into an empty directory is therefore also
  performed and its file list and exit code recorded. Neither alone establishes
  the outcome, and the Objective claims no more than the two together reach.
- **Version-pin agreement: goal-based check.** `python3 -m pytest
  tests/roster/test_okf_catalogue_discovery.py` reads the literal, so the pin is
  verified by running it rather than by reading six files.

## Acceptance Criteria

- [x] Given a symlink pre-planted at `<dest>.abtmp` — the staging name the helper
  used before this change — when `atomic_write(dest, content)` returns, the file
  that symlink points at holds the bytes it held before the call.
- [x] Given an entry already present at the staging path `atomic_write` is about
  to use, the call fails and that entry's target holds the bytes it held before
  the call — the staging file is created exclusively, so a collision refuses
  rather than being written through.
- [x] Given two successive `atomic_write` calls to the same `dest`, the staging
  path each call moves into place differs between the two calls.
- [x] Given a symlink pre-planted at `dest` itself, when
  `atomic_write(dest, content)` returns, the file that symlink pointed at holds
  the bytes it held before the call.
- [x] After `atomic_write(dest, content)` returns, `dest` is a regular file, not
  a symlink.
- [x] After `atomic_write(dest, content)` returns, `dest` holds exactly
  `content`.
- [x] A file `atomic_write` creates carries the permission bits a file
  `Path.write_bytes` creates in the same directory under the same umask, with
  the other-write bit cleared — identical under every ordinary umask, and not
  world-writable even under a null one.
- [x] After a successful `atomic_write(dest, content)`, the only entry
  `atomic_write` has added to `dest.parent` is `dest`.
- [x] When writing the staging file raises, `atomic_write` adds no entry to
  `dest.parent`.
- [x] When moving the staging file into place raises, `atomic_write` adds no
  entry to `dest.parent`.
- [x] When writing or moving raises, `atomic_write` propagates that exception
  rather than returning normally.
- [x] `packages/agentbundle/tests/unit/` passes with no existing test modified,
  and a real `agentbundle catalogue init` into an empty directory exits 0 and
  reports the same created-file list it reported before the change.
- [x] `packages/agentbundle/agentbundle/version.py`,
  `packages/agentbundle/pyproject.toml`, and the `expected` literal in
  `tests/roster/test_okf_catalogue_discovery.py` read one version, and that
  version is higher than the version `origin/main` carries at the moment the
  release surfaces are last edited.
- [x] The topmost version heading of `packages/agentbundle/CHANGELOG.md`, the
  topmost agentbundle heading of `docs/product/changelog.md`, and the
  `What's new in` heading of `packages/agentbundle/README-pypi.md` name that same
  version.

## Follow-ons

none. The package holds three near-identical atomic-write helpers —
`catalogue_tooling/initialise.py`, `build/projections/merge_into_agent_json.py`,
and `build/projections/user_merge_json.py`. Only the first is vulnerable, so
consolidating them is maintainability work with no security content. It is
excluded from this repair and recorded in the PR's considered-but-not-changed
answer rather than as a durable follow-on.

## Assumptions

- Technical: `Path.write_bytes()` follows a symlink, so the current
  `<dest>.abtmp` write lands on the link's target and the subsequent rename
  leaves `dest` itself a symlink to that target (source: read-only probe,
  2026-09-15 — planted link, victim file's contents replaced, `dest.is_symlink()`
  returned `True`).
- Technical: `os.open(path, O_CREAT|O_EXCL|O_WRONLY, 0o664)` under a random name
  supplies all three properties the repair needs at once — the name is
  unguessable, a pre-existing entry raises `FileExistsError` instead of being
  followed, and the kernel applies the caller's umask (source: read-only probe,
  2026-09-15 — mode `0o644` under umask `022`, `FileExistsError` raised against a
  planted symlink, victim file intact).
- Technical: `Path.write_bytes` requests `0o666`, so under a null umask the code
  this change replaces produced a world-writable file. Requesting `0o664` instead
  reproduces the old mode exactly at umask `022`, `002`, `077`, `027` and `007`,
  and differs only at `000`, where it drops the other-write bit (source:
  read-only probe, 2026-09-15, measured at all six umasks; and CodeQL
  `py/overly-permissive-file` on PR #1327, which flagged the `0o666` literal that
  `Path.write_bytes` had been hiding inside CPython). `0o644` was rejected: it
  also drops the group-write bit, which under umask `002` is what a
  group-shared catalogue tree relies on.
- Technical: `py/overly-permissive-file` objects to the other-read bit as well
  as other-write, so no mode a published catalogue can use satisfies it. The
  residual alert is suppressed on the line, with the reasoning beside it
  (source: the alert text changed from "world writable" at `0o666` to "world
  readable" at `0o664`, same rule and line, on PR #1327; owner authorised the
  suppression 2026-09-15).
- Technical: the package's two existing atomic writers
  (`build/projections/merge_into_agent_json.py:236` and
  `build/projections/user_merge_json.py:283`) stage into the target's parent and
  `replace` into position, and both add an `fsync` this helper does not — theirs
  is durability for an adopter's hand-tracked dotfile, and adding one here would
  introduce a failure mode on a legitimate write (source: those two files).
- Technical: the helper has three callers — `initialise.py:520`,
  `initialise_self_hosted.py:1167`, and `initialise_self_hosted.py:1623` — all
  reaching it through the `atomic_write` alias at `initialise.py:564` (source:
  repository-wide grep for `atomic_write`).
- Technical: the package targets Python `>=3.11` (source:
  `packages/agentbundle/pyproject.toml:9`).
- Process: `packages/agentbundle/` is a protected tree whose commits carry an
  `Engine-Change-RFC:` trailer, and the `n/a -- <reason>` form is in use on main
  (source: commit `d97ce17a1`).
- Process: defect repairs to this package take a patch-level bump; `0.44.1`,
  `0.44.2`, `0.44.3`, and `0.43.1` are all present (source:
  `packages/agentbundle/CHANGELOG.md`).
- Product: the hardened helper validates nothing and refuses no caller input.
  The owner's decision was that it stops being predictable rather than starting
  to validate; the `FileExistsError` a staging-name collision raises is the
  kernel rejecting a planted entry, and is unreachable from any caller argument
  (source: user confirmation 2026-09-15, revised 2026-09-15 when the mechanism
  moved to `O_EXCL`).
- Technical: `tempfile.NamedTemporaryFile` creates its file at mode `0600`,
  where `Path.write_bytes` creates at `0666 & ~umask` — `0644` under the common
  `022` umask. Adopting the pattern verbatim would therefore tighten the
  permissions of every file `catalogue init` writes, which is why the helper uses
  `os.open` with an explicit mode instead (source: read-only probe, 2026-09-15 —
  in one directory under umask `022`, `write_bytes` gave `0o644`,
  `NamedTemporaryFile` gave `0o600`, and `os.open` with an explicit mode gave
  `0o644`).
- Technical: `Path.replace` calls `os.replace`, so a test can observe the
  staging path the helper moves into place without naming the helper's internals
  (source: read-only probe, 2026-09-15 — a spy installed on `os.replace`
  recorded the staging path and the move still completed).
- Product: the repair stays inside `catalogue_tooling/initialise.py`; the two
  sibling helpers are untouched (source: user confirmation 2026-09-15).
