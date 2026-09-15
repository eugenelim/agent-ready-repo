# Plan: atomic-write-symlink-harden

- **Spec:** [`spec.md`](spec.md)
- **Status:** Done <!-- Drafting | Approved | Executing | Done -->
- **Repository anchors:** `packages/AGENTS.md` (version-bump rule, test homes)
  and `packages/agentbundle/AGENTS.md` (package traps). Analogous production
  implementations: `agentbundle/build/projections/merge_into_agent_json.py:236`
  and `agentbundle/build/projections/user_merge_json.py:283`, both already on the
  target pattern. Their test is
  `packages/agentbundle/tests/build_pipeline/test_writers_emit_lf.py:158`.
  Named deviations, both recorded in § Design decisions: those two take a `dict`
  and serialise JSON where this helper takes `bytes`; and they use
  `tempfile.NamedTemporaryFile` and `fsync`, neither of which this helper can use
  without changing behaviour a caller can observe. The shape is adopted, not the
  code.

> **Plan contract:** this is the implementation strategy. It may change
> substantively only while its Status is `Drafting`, before approval records its
> baseline. After approval, `spec.md` and `plan.md` are pinned in substance;
> only lifecycle bookkeeping is permitted, and execution observations belong in
> `docs/specs/atomic-write-symlink-harden/notes/verification-ledger.md`.
>
> **Not every field is contract.** `Touches`, `Tests` and `Done when` are what a
> completion gate reads, and they are pinned. `Design`, `Approach`, `Grounding`
> and `Risks` are working material.

## Approach

One function changes. `_atomic_write` in
`packages/agentbundle/agentbundle/catalogue_tooling/initialise.py:457` stops
deriving its staging path from the destination name. It mints a random one in
the destination's own parent, creates it exclusively with an explicit mode, then
moves it into place with `Path.replace`. The riskiest part is not the write. It
is the two properties the obvious library call silently drops: today's
`except: tmp.unlink(missing_ok=True); raise` leaves nothing behind on failure,
and today's `write_bytes` produces an umask-derived mode.
`tempfile.NamedTemporaryFile` gives neither back, which is why the design below
uses `os.open` directly. Order of operations is the tests first against the
unchanged function, recording the two reds; then the implementation; then the
version and release surfaces, which are bookkeeping and land last so a late
rebase re-checks the version against main once rather than twice.

## Constraints

No ADR or RFC governs this function. Two repository rules do:
`packages/AGENTS.md` § Version bump rule (a non-cosmetic package change updates
both `version.py` and `pyproject.toml`), and the protected-tree trailer rule for
`packages/agentbundle/` enforced by `tools/lint-catalogue-curation-guard.py`.
The trailer is `Engine-Change-RFC: n/a -- <reason>`: the function's signature,
name, export, and observable output are unchanged, so the commit carries no
design content for an RFC to govern.

## Construction tests

**Integration tests:** none beyond per-task tests. The existing
`packages/agentbundle/tests/unit/` suite runs unmodified. What it proves is
bounded by the assertions already in it: no test in that suite compares a run's
complete output manifest against a recorded baseline, so a green suite is
evidence that no asserted behaviour moved, not proof that every byte is
identical. The spec's criterion is worded to that bound.

**Manual verification:** one real `agentbundle catalogue init` run into an empty
directory, recording the created-file list and the exit code, compared against
the same run on the pre-change code. This is what covers the gap the suite
leaves, and a passing unit gate does not substitute for it.

## Durable-output map

| Durable output | Tasks | Implementation evidence | Closeout evidence |
| --- | --- | --- | --- |
| Release history — `packages/agentbundle/CHANGELOG.md`, `docs/product/changelog.md`, `packages/agentbundle/README-pypi.md` | T2 | Three headings naming the same new version, and `tools/test_build_site_routing.py` green on the blank-line rule around `## [` | The three headings agree and the entry describes the hardened write |
| Interface compatibility — `version.py`, `pyproject.toml`, `tests/roster/test_okf_catalogue_discovery.py` | T2 | `python3 -m pytest tests/roster/test_okf_catalogue_discovery.py` green | All three literals read the same version |

## Design (LLD)

### Design decisions

The staging name is the whole defect. `dest.with_suffix(dest.suffix + ".abtmp")`
is a pure function of the destination, so any process that can read the
destination path can pre-create that name; `Path.write_bytes` then opens it with
`O_CREAT|O_WRONLY|O_TRUNC`, which follows a symlink.

One call replaces all of it. The helper mints a staging name of the fixed form
`.abtmp-<16 hex chars>` — 23 bytes, and deliberately *not* derived from
`dest.name`, because a 240-byte destination basename plus a 23-byte suffix
exceeds the 255-byte `NAME_MAX` that the old 6-byte `.abtmp` suffix stayed
inside. It opens that name with
`os.open(tmp, os.O_CREAT | os.O_EXCL | os.O_WRONLY, 0o666)`. That single line
carries three properties the old code lacked, and an implementer who reaches for
a friendlier API loses at least one of them:

| Property | Comes from | What is lost without it |
| --- | --- | --- |
| The name cannot be guessed in advance | `os.urandom(8).hex()`, with no component derived from `dest` | A planted link at a derivable name receives the write |
| A collision refuses rather than follows | `O_EXCL` | A guessed name is followed into its target |
| The file keeps its usual permissions | mode `0o666`, umask applied by the kernel | Files drop from `0644` to `0600` |

`tempfile.NamedTemporaryFile` — the shape the two sibling helpers use — supplies
the first two and loses the third: it hard-codes mode `0600`. Restoring the
umask-derived mode around it requires reading the umask, and the only portable
read is `os.umask(0)` followed by restoring it, which exposes a process-wide
window where another thread's file is created world-writable. Measured on
2026-09-15: `Path.write_bytes` produced `0o644`, `NamedTemporaryFile` produced
`0o600`, and `os.open(..., 0o666)` produced `0o644`, all in one directory under
umask `022`.

The only new failure this introduces is `FileExistsError` from `O_EXCL`. It is
not a validation of the caller's `dest` — the spec's `Never do` forbids that —
and with a 64-bit random component it is unreachable by accident.

Rejected: an `is_symlink()` check on the staging path before writing. It is a
check-then-act window, not a fix — the attacker re-creates the link between the
check and the open. `O_EXCL` makes the kernel do the check and the create as one
operation, which is the thing a userspace check cannot do.

Rejected: consolidating the package's three atomic-write helpers behind one
shared function. The other two are already safe, so consolidation carries no
security content, and it would add a cross-layer import between
`catalogue_tooling/` and `build/projections/`. Recorded in the spec's
`## Follow-ons` as excluded.

Traces to: the two planted-symlink criteria, the exclusive-creation criterion,
the distinct-staging-path criterion, and the permission criterion · no
`contracts/` file.

### Failure, edge cases & resilience

Three failure paths, all preserved from the current implementation. The helper
adds exactly one new one — `FileExistsError` from a staging-name collision, which
no caller argument can reach.

- The destination's parent does not exist — created first, as today.
- Writing the staging file raises — the exception propagates unchanged and the
  staging file is removed.
- The move raises — same.

There is no `fsync`, on the file or on the parent directory, even though the two
sibling helpers have both. The current helper has never had one, and a failing
`fsync` would raise where the old code placed the file — a new failure mode on a
legitimate write, which the spec's `Never do` forbids. Durability across a crash
is not what this change is for: a `catalogue init` interrupted by one is re-run.

The cleanup spans the whole lifecycle from the moment `os.open` returns, not
just the move. Nothing else will ever remove that entry, so any failure between
creation and a successful move leaks it unless the helper owns the window
itself. The handler catches `Exception`, exactly as the current code does;
widening it to `BaseException` so an interrupt also cleans up would be a
behaviour expansion this change did not accept, and no criterion asks for it.

Cleanup is itself allowed to fail without consequence: the unlink runs under
`contextlib.suppress(OSError)`, so an attacker who has replaced the staging
entry with a directory cannot turn `IsADirectoryError` into a replacement for
the exception the caller should have seen.

Traces to: the two temporary-file criteria and the exception-propagation
criterion · no `contracts/` file.

## Tasks

### T1: A pre-planted symlink no longer receives the write, and nothing else about the helper changes

**Depends on:** none

**Touches:** packages/agentbundle/agentbundle/catalogue_tooling/initialise.py,
packages/agentbundle/tests/unit/test_catalogue_tooling_init.py

**Tests:** (`stub: true` — compilable against the current export; the first two
cases are expected to fail against the current implementation)

```python
_FIXED = b"\xde\xad\xbe\xef\xde\xad\xbe\xef"
_FIXED_STAGING = f".abtmp-{_FIXED.hex()}"


class TestAtomicWriteSymlinkHardening:
    """`atomic_write` must not open a caller-derivable staging path."""

    def test_planted_symlink_at_legacy_staging_path_is_not_written_through(
        self, tmp_path: Path
    ) -> None:
        victim = tmp_path / "victim.txt"
        victim.write_bytes(b"ORIGINAL")
        dest = tmp_path / "catalogue.toml"
        try:
            (tmp_path / "catalogue.toml.abtmp").symlink_to(victim)
        except OSError:  # pragma: no cover - platform without symlink support
            pytest.skip("symlinks unavailable")

        atomic_write(dest, b"WRITTEN")

        assert victim.read_bytes() == b"ORIGINAL"

    def test_entry_at_the_staging_path_refuses_instead_of_being_followed(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        # Pin the random component so the staging name is knowable, then occupy
        # it. Exclusive creation must refuse; following the link would overwrite
        # the victim, which is the whole defect.
        monkeypatch.setattr(os, "urandom", lambda n: _FIXED[:n])
        victim = tmp_path / "victim.txt"
        victim.write_bytes(b"ORIGINAL")
        dest = tmp_path / "catalogue.toml"
        try:
            (tmp_path / _FIXED_STAGING).symlink_to(victim)
        except OSError:  # pragma: no cover - platform without symlink support
            pytest.skip("symlinks unavailable")

        with pytest.raises(FileExistsError):
            atomic_write(dest, b"WRITTEN")

        assert victim.read_bytes() == b"ORIGINAL"

    def test_staging_path_differs_between_calls(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        staged: list[str] = []
        real_replace = os.replace

        def _spy(src, dst, **kwargs):  # type: ignore[no-untyped-def]
            staged.append(str(src))
            return real_replace(src, dst, **kwargs)

        monkeypatch.setattr(os, "replace", _spy)
        dest = tmp_path / "catalogue.toml"
        atomic_write(dest, b"ONE")
        atomic_write(dest, b"TWO")

        assert len(staged) == 2
        assert staged[0] != staged[1]

    def test_planted_symlink_at_dest_is_replaced_not_followed(
        self, tmp_path: Path
    ) -> None:
        victim = tmp_path / "victim.txt"
        victim.write_bytes(b"ORIGINAL")
        dest = tmp_path / "catalogue.toml"
        try:
            dest.symlink_to(victim)
        except OSError:  # pragma: no cover - platform without symlink support
            pytest.skip("symlinks unavailable")

        atomic_write(dest, b"WRITTEN")

        assert victim.read_bytes() == b"ORIGINAL"
        assert not dest.is_symlink()
        assert dest.read_bytes() == b"WRITTEN"

    def test_written_file_keeps_the_umask_derived_mode(self, tmp_path: Path) -> None:
        control = tmp_path / "control.toml"
        control.write_bytes(b"CONTROL")
        dest = tmp_path / "catalogue.toml"

        atomic_write(dest, b"WRITTEN")

        expected = stat.S_IMODE(control.stat().st_mode)
        assert stat.S_IMODE(dest.stat().st_mode) == expected

    def test_successful_write_leaves_no_other_entry(self, tmp_path: Path) -> None:
        dest = tmp_path / "catalogue.toml"
        atomic_write(dest, b"WRITTEN")
        assert sorted(p.name for p in tmp_path.iterdir()) == ["catalogue.toml"]

    @pytest.mark.parametrize("failing_stage", ["write", "move"])
    def test_failure_propagates_and_leaves_no_entry(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch, failing_stage: str
    ) -> None:
        def _boom(*args: object, **kwargs: object) -> None:
            raise OSError("stage refused")

        if failing_stage == "write":
            # A proxy around the real handle: the fd is still owned and closed,
            # but the write itself raises. Injecting only at the move would
            # leave an implementation that guards the move but not the write
            # looking correct.
            real_fdopen = os.fdopen

            class _FailingHandle:
                def __init__(self, inner: object) -> None:
                    self._inner = inner

                def write(self, data: bytes) -> int:
                    raise OSError("stage refused")

                def __getattr__(self, name: str) -> object:
                    return getattr(self._inner, name)

                def __enter__(self) -> "_FailingHandle":
                    return self

                def __exit__(self, *exc: object) -> bool:
                    self._inner.close()  # type: ignore[attr-defined]
                    return False

            monkeypatch.setattr(
                os, "fdopen", lambda *a, **k: _FailingHandle(real_fdopen(*a, **k))
            )
        else:
            monkeypatch.setattr(os, "replace", _boom)

        with pytest.raises(OSError):
            atomic_write(tmp_path / "catalogue.toml", b"WRITTEN")
        assert list(tmp_path.iterdir()) == []
```

- The first case is the historical regression guard: it fails against the
  unchanged function. Run it against the current code and record the red before
  writing the implementation.
- The second case is the mutation proof for the exclusive-creation criterion,
  and it is the one that stays red if someone swaps `O_EXCL` for a plain open or
  re-derives the staging name from `dest`. Confirm both mutations red before the
  task closes. It pins `os.urandom` as the source of the random component, which
  the design table records as a deliberate choice rather than an incidental one.
- `monkeypatch.setattr(os, "replace", ...)` observes the staging path because
  `Path.replace` calls `os.replace`; a probe on 2026-09-15 confirmed the spy sees
  it and the move still completes. The spy performs the real move, so that case
  asserts the write, not merely the call.
- The mode case takes its comparison value from a sibling file written by
  `Path.write_bytes` in the same directory, so it holds under any umask the test
  runner happens to have. A literal `0o644` would pin the runner instead.
- Both failure stages are injected *after* exclusive creation, so each exercises
  cleanup rather than a create that never happened. Patching the create, or
  making the parent read-only, leaves the branch under test unreached. The
  `write` stage is injected at the handle rather than only at the move, because
  an implementation that guards the move but leaves the write outside the
  handler still leaks on a real write failure.
- These live beside the module's existing tests in
  `packages/agentbundle/tests/unit/test_catalogue_tooling_init.py`, per
  `packages/AGENTS.md` § Test conventions (engine distribution → `tests/unit/`).

**Approach:**
- Write the cases, run them, record the red on the first two.
- Replace the body of `_atomic_write`: mint the staging name as
  `.abtmp-<os.urandom(8).hex()>`, open it with
  `os.O_CREAT | os.O_EXCL | os.O_WRONLY` and mode `0o666`, write it through
  `os.fdopen`, then `Path.replace` it onto `dest`. Add no `fsync` — see
  § Failure, edge cases & resilience for why.
- Keep the signature, the docstring's promise, and the parent `mkdir`.
- Wrap everything from the moment `os.open` returns in a `try`, unlinking the
  staging file on `Exception` before re-raising, with the unlink itself under
  `contextlib.suppress(OSError)` so a failed cleanup cannot mask the real error.
- Leave the `atomic_write` alias, `_commit_files`, and both self-hosted call
  sites untouched.

**Done when:** every test in this task's `Tests:` passes; the mutations named in
the first two bullets have each been observed red; and
`python3 -m pytest packages/agentbundle/tests/unit/ -q` passes with no existing
test modified.

### T2: The shipped version advances and agrees across all six pinned surfaces

**Depends on:** T1

**Touches:** packages/agentbundle/agentbundle/version.py,
packages/agentbundle/pyproject.toml, packages/agentbundle/CHANGELOG.md,
packages/agentbundle/README-pypi.md, docs/product/changelog.md,
tests/roster/test_okf_catalogue_discovery.py

**Tests:**
- `python3 -m pytest tests/roster/test_okf_catalogue_discovery.py -q` — the
  `expected` literal is the only mechanical reader of the version, so this is
  what turns a half-applied bump red.
- `python3 -m pytest tools/test_build_site_routing.py -q` — the only check that
  sees the blank line required above and below every `## [` heading in both
  changelogs, so it is what establishes the edits are well-formed.
- No suite compares the three release headings to the three code literals, and
  none compares either to `origin/main`. Both comparisons are performed by hand
  at `Done when:` below; recording that here is what stops a green roster run
  from being read as proof of the whole criterion.

**Approach:**
- Re-read `origin/main` for the current version immediately before editing, and
  again immediately before pushing; main
  moves several commits an hour and a taken version collides silently.
- Bump to the next patch level in `version.py` and `pyproject.toml`.
- Add the entry to `packages/agentbundle/CHANGELOG.md` as the topmost `## [`
  heading, mirror it into `docs/product/changelog.md`'s topmost agentbundle
  heading, and update `README-pypi.md`'s `What's new in` heading.
- Update the roster `expected` literal last.

**Done when:** both named suites pass; reading the six surfaces shows one
version in all of them; and that version is higher than the one `origin/main`
carries when those surfaces are last edited. The Finish checklist re-reads
`origin/main` once more before the PR opens, because nothing in the task can
bind a moment after it ends.

## Rollout

Pure-logic change to a library function. No flag, no migration, no infrastructure,
no external system, no sequencing. Rollback is reverting the commit; nothing it
writes is irreversible.

## Risks

### Residual attack surface this change does not close

Named here because the spec's Objective bounds its claim to the staging entry
and the destination entry. Everything below is outside that bound. The first is
not a race at all — it needs no timing and works on a link left lying there
beforehand — which is why it is listed first rather than folded in with the two
that do need a race.

- **An ancestor directory that is already a symlink.** The control reaches the
  final component only. If `dest.parent`, or anything above it, is a symlink when
  the run starts, exclusive creation and the move both resolve through it into
  another tree, and every criterion in the spec still passes. `validate_target`
  (`initialise.py:255-280`) resolves and rejects a symlinked *target root*, so
  the plain `catalogue init` path has partial cover; the owned-file overwrite at
  `initialise_self_hosted.py:1477` has none. Closing it needs every operation to
  go through a directory file descriptor opened once with `O_NOFOLLOW`, which is
  a rewrite of the commit path rather than a repair of this helper, and a
  different missing primitive from the one the next bullet needs.
- **Live substitution of the staging entry.** `os.open` creates the entry;
  `os.replace` then commits it *by pathname*. An attacker watching the directory
  can unlink the staging entry and put their own file or symlink at the same name
  in between, and the move commits theirs. The window lasts as long as the write
  takes, not a fixed instant. Closing it needs the commit
  bound to the created file's identity, which on Linux means `linkat` with
  `AT_EMPTY_PATH` — a privileged call — and has no macOS or Windows equivalent.
  Not closable within this change.
- **Ancestor substitution mid-run.** The timed variant of the first bullet:
  `_commit_files` checks `dest` itself (`initialise.py:495`), not its ancestors,
  so an attacker who swaps a directory *after* that check redirects the rest.
  Same unavailable remedy.
- **Cleanup unlinks by path.** The failure branch removes the staging entry by
  name, so an attacker who substituted it has the substitute unlinked instead,
  and an attacker who substituted a *directory* leaves it in place because the
  unlink cannot remove one. The bounded consequence is a leaked entry in a
  directory the attacker already controls; the sharper consequence — the
  cleanup's own error masking the caller's exception — is closed by the
  `contextlib.suppress(OSError)` named in the design. Proving the helper removed
  what it created needs the same unavailable primitive as the bullet above.

### Delivery risks

- **Main takes the version first.** Two PRs bumping to the same patch level
  merge without conflict and leave the six surfaces disagreeing. Mitigated by
  re-checking `origin/main` at T2 rather than at plan time.
- **The curation guard cannot fail locally.** `tools/lint-catalogue-curation-guard.py`
  skips its path-gate layer on a local run and exits 0, so a missing trailer is
  invisible until CI. Run it as
  `python3 tools/lint-catalogue-curation-guard.py --base origin/main` before
  pushing, which is CI's own invocation.
- **The obvious refactor re-breaks it.** The helper now deliberately does not
  use `tempfile.NamedTemporaryFile`, which is what the two sibling helpers use
  and what a later reader will reach for. Doing so silently tightens every
  written file from `0644` to `0600`. The permission criterion is the only thing
  standing between that refactor and a regression, and the design table above is
  the only place the reason is written down.

## Changelog

- 2026-09-15: initial plan.
- 2026-09-15: pre-EXECUTE review round 1. Split the conjoined criteria; generalised the
  security criterion from the `.abtmp` name to an unguessable staging path;
  added the permission-preservation criterion after a probe showed
  `NamedTemporaryFile` tightens `0644` to `0600`; widened cleanup from the move
  to the whole staging lifecycle; narrowed the behaviour-preservation claim and
  added a manual CLI run beside it; recorded the three unclosable race paths as
  residual risk.
- 2026-09-15: pre-EXECUTE review round 2. Two of round 1's own repairs were
  defective: "the staging path differs between calls" admits an implementation
  that alternates two predictable names, and restoring the mode around
  `NamedTemporaryFile` needs a process-global umask window. Both are answered by
  one change of mechanism to `os.open` with `O_EXCL` and an explicit `0o666`,
  which supplies unguessability, refusal-on-collision, and the umask-derived mode
  without touching global state. Owner approved the mechanism change on
  2026-09-15. Also separated a pre-planted ancestor symlink from the race-class
  residuals, narrowed the Objective to what the criteria reach, moved the
  write-stage failure patch to a point where a staging entry exists, and bound the version criterion to a moment a task can observe.
- 2026-09-15: pre-EXECUTE review rounds 3 and 4. Staging name became the fixed
  23-byte `.abtmp-<16 hex>` form after a `NAME_MAX` overflow was found in the
  round-2 name; the `BaseException` cleanup widening was dropped as unaccepted
  scope; cleanup moved under `contextlib.suppress(OSError)` so it cannot mask the
  caller's exception; and both `fsync` calls were removed, because the helper has
  never had one and a failing `fsync` would raise where the old code placed the
  file. Two dead test seams were corrected: the write-stage injection now fires
  at the file handle, and the move-stage patch names `os.replace` rather than a
  nonexistent `os.move`.
