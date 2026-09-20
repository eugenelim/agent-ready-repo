# Plan: a typed allocator that refuses where the untyped one guesses

- **Spec:** [`spec.md`](spec.md)
- **Status:** Drafting
- **Repository anchors:** `packs/governance-extras/.apm/skills/new-adr/scripts/next-ordinal.py:103` (`_PREFIX = re.compile(r"^(\d{4,})[-.]")` — the anchored pattern that returns `0001` on a typed directory), `:162` (`_remote_ordinals`, which unions records on `refs/remotes/origin/HEAD` — committed-and-pushed records absent from the working tree, *not* a peer's unpushed work, which ADR-0108:41 records as the limit of this whole approach; it returns an empty set when there is no remote to consult and degrades to the working tree on a timeout), `:213` (`duplicate_ordinals`, which refuses rather than reporting clean on a scan it could not complete), `:256` (`next_ordinal`); `packs/governance-extras/tests/skills/new-adr/test_next_ordinal.py:14-20` (load-by-path module loader and the local-Git fixture pattern this suite reuses); `packs/core/.apm/skills/work-intake/SKILL.md:329-340` (§ 6 *Delegate intent admission*, the named integration point) and `:60` (the public routing precedence that sends an explicit `intake-intent` request past § 6); `packs/core/.apm/skills/intake-intent/SKILL.md:100-107` (Procedure steps 3 and 5, the preserve-or-confirm step this slice amends) and `:195-212` (`## Boundaries`, which refuses shell access); `packs/core/.apm/skills/intake-intent/scripts/intent_renderer.py:66` (`repository_intent_target`, which composes `docs/product/intents/{slug}.md`) and `:171` (`admit_repository_intent`, which already accepts `slug` and `level`); `packs/core/.apm/skills/work-loop/scripts/file_safety.py:221` (`list_confined_regular_files`, the blessed confined listing) with `tests/roster/test_close_work_extraction_and_immediate_disposition.py:853-857` (the byte-identity pin every hand-maintained `packs/**` copy needs, per `packs/AGENTS.local.md:54-57`); `tests/AGENTS.md:27-42` (the three edits a new `tests/roster/` file obliges). Named uncertainty: the existing typed corpus was authored by hand, so the allocator's first real run must agree with numbers a human chose — T2's baseline assertion measures it rather than assuming it.

## Approach

The allocator is a new script because the existing one is not extensible into it: `_PREFIX` is anchored at position zero, so on `FEAT-0002-intent-graph-navigation.md` it does not match, and `next_ordinal` then returns `1` with exit 0 while `--check` prints "no duplicate ordinals" for a directory in which it saw nothing. Loosening that pattern to accept an optional prefix would change what `new-adr` and `new-rfc` allocate over their own untyped corpora, which is the one behaviour this slice must not touch. So: a second script, and a test that pins the two to the same answer on comparable inputs.

The shape carries over rather than being reinvented. `next-ordinal.py` already solved the hard parts — the `origin` union that widens the view past the working tree, and a `--check` mode that refuses rather than reporting clean on an incomplete scan. Three things change. The pattern matches the owner's typed filename contract instead of a bare digit run. The maximum is grouped per type token rather than per directory. And a *failed* remote query refuses instead of degrading, because a working-tree-only answer presented as authoritative is the plausible-but-wrong result the slice exists to stop; a directory with no remote to consult is a different case and allocates normally, since the working tree is then the complete available view.

Refusal is the design centre, not an edge case. Where the untyped script's fallback is `0001`, the typed one's is no ordinal at all — for a malformed in-namespace filename, for a scan it could not complete, and for an altitude the parent's table does not map. `intake-intent` already has the receiving shape: `admit_repository_intent` takes `slug` and composes the target from it, so an allocated ordinal is expressed as a prefixed slug and an unmapped level as the bare slug. No new capability is needed to receive either.

The integration covers two entry paths with two mechanisms, because they have two capability sets. `work-intake` § 6 already "passes the confirmed repository destination, and authority mode to `intake-intent`" and already declares `Bash`, so it allocates before that pass, on the destination it was going to supply anyway. The direct path at `SKILL.md:60` reaches `intake-intent` without a caller, and that skill's `## Boundaries` refuses a shell — so it cannot allocate and this slice does not grant it one. Its Procedure step 3 refuses instead: creating a mapped-level intent without an allocated ordinal stops and names the path that allocates, and a prefix supplied with the request is not accepted as proof, because the owner cannot check it against the working tree and `origin`. Preserving an existing path is untouched, prefixed or not, which is what the parent's forward-only guardrail means in practice and covers most of what the direct route is used for.

## Assumption trio

**Written** — `packs/core/.apm/skills/work-intake/scripts/intent_ordinal.py` (new); `packs/core/.apm/skills/work-intake/scripts/file_safety.py` (new, byte-identical copy); `packs/core/.apm/skills/work-intake/SKILL.md` (§ 6); `packs/core/.apm/skills/intake-intent/SKILL.md` (one clause of Procedure step 3); both skills' `evals/evals.json` and `evals/eval_queries.json`; `packs/core/tests/skills/work-intake/test_intent_ordinal.py` (new); `packs/core/tests/skills/work-intake/test_work_intake.py`; `packs/core/tests/skills/intake-intent/test_intake_intent_manifest.py` (new); `tests/roster/test_typed_ordinal_collision_equivalence.py` (new); `tests/roster/test_close_work_extraction_and_immediate_disposition.py` (one added parity assertion); `.github/workflows/build-check.yml`; `tools/lint-ci-parity.py`; `packs/core/pack.toml`; `packs/core/.claude-plugin/plugin.json`; `docs/product/changelog.md`; `docs/specs/typed-intent-ordinal-allocator/notes/verification-ledger.md`.

**Generated, not hand-edited** — `.claude-plugin/marketplace.json` and the adapter projections under `packs/core/`, all written by `make build-self`, regenerated at the end of each `.apm/`-editing task rather than once at the end, because `self-host --check` and T3's sessions both read projections rather than source.

**Read only, asserted against, never written** — `docs/product/intents/FEAT-0001-intent-identity-and-registration.md` (the owner's token table); every file under `docs/product/intents/` (the live-shape assertion); `packs/governance-extras/.apm/skills/new-adr/scripts/next-ordinal.py`.

**Explicitly unamended, and that is the evidence** — `packs/core/tests/skills/intake-intent/test_intake_intent.py`.

**Done is demonstrated by** — the new pack suite and the two roster tests green, `test_intake_intent.py` green unamended, and the six recorded admission sessions in the verification ledger.

**Not changing** — `next-ordinal.py` and its two suites; `intake-intent`'s `allowed-tools`, `## Boundaries` and every control in them; the existing corpus, since the parent intent's guardrail makes adoption forward-only, so an intent carrying no ordinal today keeps none and no file is renumbered.

**Tempted and declined:**

- *Generalise `next-ordinal.py` to handle both shapes.* Declined under rung 7 (minimum correct change preserving ownership and tests): it lives in `governance-extras`, serves two skills there, and widening its pattern changes what those skills allocate over untyped directories.
- *A shared cross-pack ordinal library.* Declined under rung 1 (skip an addition not genuinely needed): two callers in two packs with different matching rules is not a library, and a cross-pack import would put a `governance-extras` path on a `core` skill's load path.
- *A counter file or a retired-ordinal list.* Declined by an explicit requirement rather than a rung: AC-0003 forbids it, and ADR-0108's context records this repository colliding twice on a shared mutable counter across worktrees.
- *Reimplement directory confinement.* Declined under rung 2 (reuse an adequate repository solution): `file_safety.validate_confined_directory` is from the blessed helper named in the root `AGENTS.md`, and `close-work` establishes the per-skill copy plus its byte-identity pin as this repository's carrying pattern. Its `list_confined_regular_files` is deliberately *not* used for entry enumeration — it refuses every symlink, which AC-0004 forbids for an outside-namespace name.
- *Derive a token for an unmapped altitude.* Declined by the parent intent's own decision: the table is closed, and a derived token is exactly the plausible-but-wrong answer this slice exists to stop.
- *Grant `intake-intent` a shell so it can allocate on the direct path.* Declined by a trust-boundary control rather than a rung: its `## Boundaries` refuses shell, network and external-locator access for a skill that handles untrusted intent sources, and a refusal buys the same invariant at no capability cost.

## Constraints

- **This slice fires `work-loop`'s security-boundary trigger** — confinement, untrusted repository content, file validation, subprocess handling, and an output that selects a filesystem destination for a skill that writes. A spec-stage `security-reviewer` pass was run on 2026-09-20 and its five findings are discharged as AC-0003 (tightened), AC-0016, AC-0017, AC-0018 and AC-0019. `AGENTS.md` forbids cutting a trust-boundary control, so each is a criterion rather than plan prose. An implementation pass on the diff is still owed at GATES.

- **Shipped pack content carries no internal-governance citations** (`packs/AGENTS.md`). The script and both skill bodies state their rules directly; the parent intent, ADR-0108 and ADR-0033 are cited in the spec and here, never in pack content.
- **A pack test may not read above its pack** (`tests/AGENTS.md:22-25`, enforced by `tools/test-lint-pack-test-boundary.py`), because pack tests ship with the pack. The core suite therefore runs on synthetic fixtures only, and every test that reads `docs/` or a second pack lives in `tests/roster/`.
- **A new `tests/roster/` file obliges three further edits** (`tests/AGENTS.md:27-42`): a step in `.github/workflows/build-check.yml` naming the file and placed **above** the bulk `pytest tests/ -q` step, because the job is fail-fast with no step-level `if:` and a named step below it never runs; a matching `STEP_DISPOSITION` entry in `tools/lint-ci-parity.py` with the value `LOCAL("test-after-build-check")`; and a `.workspace-prune-protected.toml` entry only if the test names a `docs/specs/<slug>` path as a literal, which T2's does not.
- **A hand-maintained `packs/**` copy of `file_safety.py` is pinned byte-identical by a test** (`packs/AGENTS.local.md:54-57`). The pattern lives at `tests/roster/test_close_work_extraction_and_immediate_disposition.py:853-857`, which pins only the `close-work` copy; a third copy needs its own assertion beside it, or it silently diverges from the canonical helper with nothing red.
- **A non-cosmetic pack update also updates that pack's eval harness** (`packs/AGENTS.md:60`). Both changed skills already carry `evals/evals.json` and `evals/eval_queries.json`, so each gains coverage of its new behaviour.
- **Version bumps are patch-sized here** (`packs/AGENTS.md:43-47`): patch for changed content, minor for a new primitive. A script added inside an existing skill is changed content of that skill, not a new projected primitive, so this is a patch bump.
- **`Level` is an open set** (ADR-0033 D2) while the parent's token table is closed. An unmapped level is a normal, expected input with a defined outcome — no ordinal — not an error condition.
- **Adoption is forward-only**, owned by the parent intent's `## Guardrail` and the brief's renumber non-goal, with ADR-0108 D6 as the cited precedent rather than the governing decision. The allocator reads the existing corpus to compute a maximum; it never rewrites it.
- **Streams reconfigure to UTF-8 before the first print** (`packs/AGENTS.md`), as `next-ordinal.py:main` already does.

## Construction tests

**Unit, in the pack** — `packs/core/tests/skills/work-intake/test_intent_ordinal.py`, on synthetic fixtures only, because it ships with the pack.

**Integration, at the repository** — `tests/roster/test_typed_ordinal_collision_equivalence.py`. It is a roster test because it reads a second pack's script and the repository's own `docs/`, both of which a pack test may not reach. It asserts equivalence over **paired** typed and untyped fixtures, not over the real ADR/RFC corpora: a directory with no typed records is indistinguishable from a valid intent directory holding only legacy names, which AC-0001 requires to yield `0001`, so a real-corpus non-answer assertion would contradict the first-allocation criterion.

**Manual verification** — six sessions, one per end-to-end case the spec enumerates, each recorded in `notes/verification-ledger.md` with its invocation, its observed result, and its stop boundary. A unit test can prove the allocator returns `FEAT-0006`; only a session proves a skill asked it and passed the answer through. Each session stops at the outcome its criterion names — the written file, the registered entry, the in-place edit, or the refusal before any write — and the ledger states which arms were documented but not exercised.

## Durable-output map

No `## Durable Outputs` table in the spec, so nothing to mirror. Each task names the criteria it discharges.

## Tasks

### T1: The allocator — one maximum per type, and a refusal where there is no type

**Depends on:** none

**Mode:** TDD

**Tests:**

- `test_every_token_sequences_independently` (AC-0001) — `stub: true`
- `test_a_recognized_level_maps_to_a_token` (AC-0001) — `stub: true`
- `test_an_unlisted_level_maps_to_nothing` (AC-0002) — `stub: true`
- `test_the_filename_partition_inside_the_namespace` (AC-0004, AC-0013) — `stub: true`
- `test_a_name_with_no_introducer_is_outside` (AC-0004) — `stub: true`
- `test_an_outside_name_is_skipped_and_a_malformed_one_is_fatal` (AC-0004, AC-0010) — `stub: true`
- `test_an_outside_namespace_symlink_does_not_fail_the_scan` (AC-0004) — `stub: true`
- `test_an_in_namespace_symlink_fails_the_scan` (AC-0011) — `stub: true`
- `test_an_unreadable_entry_fails_the_scan` (AC-0011) — `stub: true`
- `test_a_reachable_or_absent_remote_allocates` (AC-0015) — `stub: true`
- `test_a_failed_remote_query_refuses` (AC-0011) — `stub: true`
- `test_allocation_writes_nothing` (AC-0003) — `stub: true`
- `test_check_refuses_a_missing_directory` (AC-0011) — `stub: true`
- `test_check_has_both_halves` (AC-0012) — `stub: true`
- `test_a_malformed_remote_name_fails_the_scan` (AC-0004, AC-0011) — `stub: true`
- `test_a_path_in_both_views_counts_once` (AC-0005) — `stub: true`
- `test_a_remote_only_record_raises_the_maximum` (AC-0005) — `stub: true`
- `test_check_does_not_consult_the_remote_view` (AC-0012) — `stub: true`
- `test_the_cli_uses_a_distinct_code_per_outcome` (AC-0006, AC-0007) — `stub: true`
- `test_the_cli_refuses_with_its_own_code` (AC-0010, AC-0011) — `stub: true`
- `test_a_hostile_level_is_data_not_a_command` (AC-0016) — `stub: true`
- `test_an_outside_namespace_link_is_not_dereferenced` (AC-0017) — `stub: true`
- `test_a_non_regular_in_namespace_entry_fails_closed` (AC-0017) — `stub: true`
- `test_the_git_child_environment_is_scrubbed_and_local` (AC-0018) — `stub: true`
- `test_diagnostics_reflect_no_untrusted_text` (AC-0019) — `stub: true`

The block below is exact and materializes unchanged at `packs/core/tests/skills/work-intake/test_intent_ordinal.py` when the engine enters `CODE-IMPLEMENTATION`. It compiles under `python3 -m py_compile`, and it earned its red from disposable scratch on 2026-09-20 against a deliberately-wrong skeleton (`token_for_level` → `None`, `classify` → `"outside"`, `next_typed_ordinal` → `1`, `remote_view` → `absent`, `main` → `0`): **43 failed, 11 passed**. Every case derives its tokens and levels from `MODULE.LEVEL_TOKENS`, so the owner's table appears nowhere in this file — T2 is the single place the concrete mapping is checked, against the parent intent that owns it.

Deferred to EXECUTE as assertions added to this file rather than a rewrite of it: the `origin`-reachable arm of `test_a_reachable_or_absent_remote_allocates`, whose `"ok"` parametrization needs a local Git fixture this file does not build (T2 carries the equivalent at the repository boundary), and the induced-timeout variant of the failed-query case. Both are construction-level detail on an already-red contract surface.

```python
# STUB: AC-0001, AC-0003, AC-0004, AC-0005, AC-0006, AC-0007, AC-0010, AC-0011,
#       AC-0012, AC-0013, AC-0015, AC-0016, AC-0017, AC-0018, AC-0019
# Stored and validated in PLAN's T1 Tests: subsection. Every case derives its
# tokens and levels from the module's own mapping, so this file never restates
# the owner's closed table — T2 is where the mapping is checked against the
# parent intent that owns it.
"""Unit coverage for the typed intent ordinal allocator."""

import importlib.util
import os
import pathlib
import sys

import pytest

sys.dont_write_bytecode = True

_SCRIPTS = pathlib.Path(__file__).resolve().parents[3] / ".apm/skills/work-intake/scripts"
_SPEC = importlib.util.spec_from_file_location(
    "core_work_intake_intent_ordinal", _SCRIPTS / "intent_ordinal.py"
)
MODULE = importlib.util.module_from_spec(_SPEC)
assert _SPEC.loader is not None
_SPEC.loader.exec_module(MODULE)

TOKENS = sorted(MODULE.LEVEL_TOKENS.values())
LEVELS = sorted(MODULE.LEVEL_TOKENS)


def _snapshot(directory: pathlib.Path) -> set[tuple[str, int]]:
    """Name and size of every entry, so a write of any kind shows up."""
    return {(p.name, p.stat().st_size) for p in directory.rglob("*")}


@pytest.mark.parametrize("token", TOKENS)
def test_every_token_sequences_independently(token: str, tmp_path: pathlib.Path) -> None:
    """AC-0001: each type's maximum is its own, for every token in the table."""
    for other in TOKENS:
        (tmp_path / f"{other}-0001-a.md").write_text("", encoding="utf-8")
    (tmp_path / f"{token}-0002-b.md").write_text("", encoding="utf-8")
    assert MODULE.next_typed_ordinal(tmp_path, token) == 3
    for other in TOKENS:
        if other != token:
            assert MODULE.next_typed_ordinal(tmp_path, other) == 2


@pytest.mark.parametrize("level", LEVELS)
def test_a_recognized_level_maps_to_a_token(level: str) -> None:
    """AC-0001: the lookup is exact and total over its own keys."""
    assert MODULE.token_for_level(level) == MODULE.LEVEL_TOKENS[level]


@pytest.mark.parametrize("level", ["initiative", None, "`feature`", "Feature", ""])
def test_an_unlisted_level_maps_to_nothing(level: str | None) -> None:
    """AC-0002: exact match, so a decorated or cased variant is unmapped."""
    assert MODULE.token_for_level(level) is None


@pytest.mark.parametrize(
    ("name", "expected"),
    [
        ("{t}-0001-x.md", "valid"),
        ("{t}-12345-x.md", "valid"),
        ("{t}-0001.md", "malformed"),
        ("{t}-0001.txt", "malformed"),
        ("{t}-x.md", "malformed"),
        ("{t}-12-y.md", "malformed"),
        ("{t}-0001x.md", "malformed"),
        ("{t}-0001", "malformed"),
        ("{t}-0001-.md", "malformed"),
    ],
)
def test_the_filename_partition_inside_the_namespace(name: str, expected: str) -> None:
    """AC-0004, AC-0013: validity is the owner's <TYPE>-NNNN-<slug>.md shape."""
    assert MODULE.classify(name.format(t=TOKENS[0])) == expected


@pytest.mark.parametrize("name", ["EPIC-0001-x.md", "legacy-slug.md", "README.md", "0042-x.md"])
def test_a_name_with_no_introducer_is_outside(name: str) -> None:
    """AC-0004: no mapped token means outside the namespace."""
    assert MODULE.classify(name) == "outside"


def test_an_outside_name_is_skipped_and_a_malformed_one_is_fatal(
    tmp_path: pathlib.Path,
) -> None:
    """AC-0004, AC-0010: skipping is not the same as an incomplete scan."""
    token = TOKENS[0]
    (tmp_path / "legacy-slug.md").write_text("", encoding="utf-8")
    assert MODULE.next_typed_ordinal(tmp_path, token) == 1
    (tmp_path / f"{token}-12-y.md").write_text("", encoding="utf-8")
    assert MODULE.next_typed_ordinal(tmp_path, token) is None


def test_an_outside_namespace_symlink_does_not_fail_the_scan(
    tmp_path: pathlib.Path,
) -> None:
    """AC-0004: classification precedes the integrity refusal for outside names."""
    (tmp_path / f"{TOKENS[0]}-0001-a.md").write_text("", encoding="utf-8")
    (tmp_path / "notes").symlink_to(tmp_path.parent, target_is_directory=True)
    assert MODULE.next_typed_ordinal(tmp_path, TOKENS[0]) == 2


def test_an_in_namespace_symlink_fails_the_scan(tmp_path: pathlib.Path) -> None:
    """AC-0011: a record-looking link is a scan failure, as in the ADR helper."""
    (tmp_path / "real.md").write_text("", encoding="utf-8")
    (tmp_path / f"{TOKENS[0]}-0001-link.md").symlink_to(tmp_path / "real.md")
    assert MODULE.next_typed_ordinal(tmp_path, TOKENS[0]) is None


def test_an_unreadable_entry_fails_the_scan(tmp_path: pathlib.Path) -> None:
    """AC-0011: a local read failure refuses rather than counting partially."""
    nested = tmp_path / "locked"
    nested.mkdir()
    (nested / f"{TOKENS[0]}-0001-a.md").write_text("", encoding="utf-8")
    os.chmod(nested, 0o000)
    try:
        assert MODULE.next_typed_ordinal(nested, TOKENS[0]) is None
    finally:
        os.chmod(nested, 0o700)


@pytest.mark.parametrize("state", ["absent", "ok"])
def test_a_reachable_or_absent_remote_allocates(state: str, tmp_path: pathlib.Path) -> None:
    """AC-0015: no remote is the complete available view, not a failure."""
    (tmp_path / f"{TOKENS[0]}-0001-a.md").write_text("", encoding="utf-8")
    assert MODULE.remote_view(tmp_path).state == "absent"
    assert MODULE.next_typed_ordinal(tmp_path, TOKENS[0]) == 2


def test_a_failed_remote_query_refuses(tmp_path: pathlib.Path, monkeypatch) -> None:
    """AC-0011: an unknowably incomplete view refuses, unlike the ADR helper."""
    (tmp_path / f"{TOKENS[0]}-0001-a.md").write_text("", encoding="utf-8")
    monkeypatch.setattr(
        MODULE, "remote_view", lambda _d: MODULE.RemoteView(frozenset(), "failed")
    )
    assert MODULE.next_typed_ordinal(tmp_path, TOKENS[0]) is None


def test_allocation_writes_nothing(tmp_path: pathlib.Path) -> None:
    """AC-0003: no counter file, no retired list, no cache."""
    (tmp_path / f"{TOKENS[0]}-0001-a.md").write_text("", encoding="utf-8")
    before = _snapshot(tmp_path)
    MODULE.next_typed_ordinal(tmp_path, TOKENS[0])
    assert _snapshot(tmp_path) == before


def test_check_refuses_a_missing_directory(tmp_path: pathlib.Path) -> None:
    """AC-0011: never report clean for a directory it did not read."""
    assert MODULE.main(["--check", str(tmp_path / "absent")]) == 1


def test_check_has_both_halves(tmp_path: pathlib.Path) -> None:
    """AC-0012: same-type duplicates fail; equal ordinals across types pass."""
    for token in TOKENS:
        (tmp_path / f"{token}-0001-a.md").write_text("", encoding="utf-8")
    assert MODULE.main(["--check", str(tmp_path)]) == 0
    (tmp_path / f"{TOKENS[0]}-0001-b.md").write_text("", encoding="utf-8")
    assert MODULE.main(["--check", str(tmp_path)]) == 1


def test_a_malformed_remote_name_fails_the_scan(
    tmp_path: pathlib.Path, monkeypatch
) -> None:
    """AC-0004, AC-0011: a remote name is classified like a local one."""
    (tmp_path / f"{TOKENS[0]}-0001-a.md").write_text("", encoding="utf-8")
    monkeypatch.setattr(
        MODULE,
        "remote_view",
        lambda _d: MODULE.RemoteView(frozenset({f"{TOKENS[0]}-12-bad.md"}), "ok"),
    )
    assert MODULE.next_typed_ordinal(tmp_path, TOKENS[0]) is None


def test_a_path_in_both_views_counts_once(
    tmp_path: pathlib.Path, monkeypatch
) -> None:
    """The union deduplicates by path, so a pushed local file is one record."""
    name = f"{TOKENS[0]}-0004-a.md"
    (tmp_path / name).write_text("", encoding="utf-8")
    monkeypatch.setattr(
        MODULE, "remote_view", lambda _d: MODULE.RemoteView(frozenset({name}), "ok")
    )
    assert MODULE.next_typed_ordinal(tmp_path, TOKENS[0]) == 5


def test_a_remote_only_record_raises_the_maximum(
    tmp_path: pathlib.Path, monkeypatch
) -> None:
    """AC-0005: allocation unions the remote view."""
    (tmp_path / f"{TOKENS[0]}-0001-a.md").write_text("", encoding="utf-8")
    monkeypatch.setattr(
        MODULE,
        "remote_view",
        lambda _d: MODULE.RemoteView(frozenset({f"{TOKENS[0]}-0009-b.md"}), "ok"),
    )
    assert MODULE.next_typed_ordinal(tmp_path, TOKENS[0]) == 10


def test_check_does_not_consult_the_remote_view(
    tmp_path: pathlib.Path, monkeypatch
) -> None:
    """AC-0012 is a statement about one directory, as in the ADR helper."""
    (tmp_path / f"{TOKENS[0]}-0001-a.md").write_text("", encoding="utf-8")
    monkeypatch.setattr(
        MODULE,
        "remote_view",
        lambda _d: MODULE.RemoteView(frozenset({f"{TOKENS[0]}-0001-b.md"}), "ok"),
    )
    assert MODULE.main(["--check", str(tmp_path)]) == 0


@pytest.mark.parametrize(
    ("level", "expected_exit"),
    [(LEVELS[0], 0), ("initiative", 3)],
)
def test_the_cli_uses_a_distinct_code_per_outcome(
    level: str, expected_exit: int, tmp_path: pathlib.Path, capsys
) -> None:
    """AC-0006, AC-0007: allocated, unmapped and refused are three codes."""
    assert MODULE.main(["--dir", str(tmp_path), "--level", level]) == expected_exit
    captured = capsys.readouterr()
    if expected_exit == 0:
        assert captured.out.strip() == f"{MODULE.LEVEL_TOKENS[level]}-0001"
    else:
        assert captured.out == ""
        assert captured.err.strip()


def test_the_cli_refuses_with_its_own_code(tmp_path: pathlib.Path, capsys) -> None:
    """AC-0010, AC-0011: a scan failure is not the unmapped outcome."""
    token = TOKENS[0]
    (tmp_path / f"{token}-12-y.md").write_text("", encoding="utf-8")
    level = next(k for k, v in MODULE.LEVEL_TOKENS.items() if v == token)
    assert MODULE.main(["--dir", str(tmp_path), "--level", level]) == 1
    captured = capsys.readouterr()
    assert captured.out == ""
    assert captured.err.strip()


@pytest.mark.parametrize(
    "level",
    ["feature; rm -rf /", "feature\nfeature", "--dir=/etc", "/absolute/feature",
     "$(id)", "`id`", "feature&&id"],
)
def test_a_hostile_level_is_data_not_a_command(
    level: str, tmp_path: pathlib.Path, capsys
) -> None:
    """AC-0016: an adopter-controlled open string never gains shell authority."""
    assert MODULE.main(["--dir", str(tmp_path), "--level", level]) == 3
    captured = capsys.readouterr()
    assert captured.out == ""
    assert not list(tmp_path.iterdir())


def test_an_outside_namespace_link_is_not_dereferenced(
    tmp_path: pathlib.Path,
) -> None:
    """AC-0017: skipped without a dereference, so a dangling link is harmless."""
    (tmp_path / f"{TOKENS[0]}-0001-a.md").write_text("", encoding="utf-8")
    (tmp_path / "dangling.md").symlink_to(tmp_path / "does-not-exist.md")
    assert MODULE.next_typed_ordinal(tmp_path, TOKENS[0]) == 2


def test_a_non_regular_in_namespace_entry_fails_closed(
    tmp_path: pathlib.Path,
) -> None:
    """AC-0017: an in-namespace entry that is not a regular file refuses."""
    os.mkfifo(tmp_path / f"{TOKENS[0]}-0001-fifo.md")
    assert MODULE.next_typed_ordinal(tmp_path, TOKENS[0]) is None


def test_the_git_child_environment_is_scrubbed_and_local(
    tmp_path: pathlib.Path, monkeypatch
) -> None:
    """AC-0018: no redirect variables, no shell, closed stdin, no fetch."""
    seen: dict[str, object] = {}

    def _record(arguments, **keywords):
        seen["arguments"] = list(arguments)
        seen["keywords"] = keywords
        raise OSError("no git in this fixture")

    monkeypatch.setattr(MODULE.subprocess, "run", _record)
    monkeypatch.setenv("GIT_DIR", "/elsewhere/.git")
    monkeypatch.setenv("GIT_OBJECT_DIRECTORY", "/elsewhere/objects")
    MODULE.remote_view(tmp_path)

    assert seen["keywords"]["shell"] is False
    assert seen["keywords"]["stdin"] is MODULE.subprocess.DEVNULL
    assert seen["keywords"]["timeout"] is not None
    environment = seen["keywords"]["env"]
    for variable in MODULE.GIT_REDIRECT_VARIABLES:
        assert variable not in environment
    assert "fetch" not in seen["arguments"]


def test_diagnostics_reflect_no_untrusted_text(
    tmp_path: pathlib.Path, capsys
) -> None:
    """AC-0019: bounded, single-line, and free of reflected adopter content."""
    hostile = "feature-\x1b[31m-AKIAIOSFODNN7EXAMPLE\nsecond-line"
    assert MODULE.main(["--dir", str(tmp_path), "--level", hostile]) == 3
    message = capsys.readouterr().err
    assert message.count("\n") == 1
    assert len(message) <= 200
    for fragment in ("AKIAIOSFODNN7EXAMPLE", "\x1b", "second-line"):
        assert fragment not in message
```

**Approach:**

- **One invocation, three exit codes.** `work-intake` calls the script; the contract at that boundary is as much a deliverable as the Python surface, because § 6 has to branch on it:

  ```
  python3 scripts/intent_ordinal.py --dir <repo-relative directory> --level <Level value>
  ```

  | Exit | stdout | stderr | `work-intake` does |
  | --- | --- | --- | --- |
  | 0 | `<TYPE>-NNNN` | empty | supplies `<TYPE>-NNNN-<slug>.md` as the confirmed destination (AC-0006) |
  | 3 | empty | one line naming the unmapped level | supplies the bare `<slug>.md`; admission and registration proceed (AC-0007) |
  | 1 | empty | one line naming the scan failure | stops before any write or registration (AC-0010, AC-0011) |

  Every untrusted value crosses that boundary as a single data argument — `subprocess.run` with a list and `shell=False`, never a string a shell parses — and `work-intake`'s § 6 text says so explicitly, because the router has `Bash` and an adopter controls the `Level` string (AC-0016). § 6 also validates the returned value against `^<TOKEN>-\d{4,}$` before composing a destination from it: an allocator that returned something unexpected must not be able to choose a path.

  Three codes rather than two, so the branch never depends on parsing empty stdout: "no ordinal because the altitude has none" and "no ordinal because I could not look" are different instructions to the caller and must not share a code. The ordinal goes to stdout alone and every diagnostic to stderr, so a caller capturing stdout gets the value or nothing. `--check <dir>` keeps `next-ordinal.py`'s two codes, 0 clean and 1 duplicate-or-unreadable.
- Match the owner's contract, not a prefix. Two patterns, so the classes cannot leave a gap: the introducer `^<TOKEN>-` decides in-or-out of the namespace, and the end-anchored shape `^<TOKEN>-\d{4,}-[^/]+\.md$` decides valid-or-malformed inside it. Both build their alternation from the mapping's own values, so the token set appears once in the module. Deriving malformed as "introducer and not shape" is what makes the partition exhaustive by construction; enumerating malformed shapes instead is how `FEAT-0001x.md` and `FEAT-0001` escaped an earlier draft.
- The anchored shape is narrower than `next-ordinal.py`'s `[-.]`, deliberately (AC-0013). Inheriting `[-.]` would count `FEAT-0001.md` and `FEAT-0001.txt`, letting a file the owner's contract does not admit raise the maximum.
- `token_for_level` is a dict lookup with an exact-match key, transcribing the parent intent's table rather than deciding it. The script states the mapping directly because shipped pack content carries no internal-governance citations, and a comment names the transcription so a future edit knows where the decision lives.
- The three filename classes are the load-bearing design choice, because most files in `docs/product/intents/` carry no typed prefix. Treating an unmatched name as an incomplete scan would make the live corpus unallocatable; treating a malformed typed name as merely uninteresting would let it vanish from duplicate checking. `classify` returns the class rather than a boolean, so a fourth case cannot fall through to a default.
- **The remote view is a tri-state, not a set.** This is the one place the borrowed implementation cannot be carried over: `next-ordinal.py:_git_output` funnels every `OSError`, `SubprocessError`, `UnicodeError` and timeout to `None`, and `_remote_ordinals` turns each of those — plus a genuinely absent remote — into the same empty set, so "nothing there" and "could not look" are indistinguishable at the call site. Changing only the timeout arm would not separate them. `remote_view(directory)` returns `RemoteView(names, state)` instead — **names, not ordinals**, so record identity survives until classification. Carrying only a set of integers would lose three things the criteria need: a malformed name on `origin` could not make the scan incomplete (AC-0004), a path present both locally and remotely would count as two records rather than one, and the classifier would have to run twice on different data. The six outcomes:

  | Condition | `state` | Allocation |
  | --- | --- | --- |
  | not a Git repository | `absent` | proceeds, working tree only |
  | repository with no remote | `absent` | proceeds, working tree only |
  | remote present, no `refs/remotes/origin/HEAD` | `absent` | proceeds, working tree only |
  | `ls-tree` succeeded | `ok` | proceeds, union of both |
  | Git invocation failed, or the ref lookup errored | `failed` | refuses |
  | Git invocation timed out | `failed` | refuses |

  The three `absent` rows are the complete available view, which is why every positive fixture in the suite is an `origin`-less `tmp_path`; conflating them with `failed` makes the suite unsatisfiable. The two `failed` rows are an unknowably incomplete view, and refusing there is the deliberate divergence from the script being modelled. AC-0005's equivalence is scoped to fixtures where `origin` answers, so the two claims do not collide.
- **Allocation unions, `--check` does not.** The two modes read different scopes, and that is inherited rather than invented: `next-ordinal.py` calls `_remote_ordinals` only from `next_ordinal:260`, never from `duplicate_ordinals:213`. So allocation classifies the union of local entries and remote names, deduplicating by repository-relative path so a file present in both counts once; `--check` reports duplicates in the directory it was given. AC-0012 is therefore a statement about one directory, which is also the only scope in which a duplicate is actionable — a remote-only collision is already committed and needs a reissue, not a refusal. The script says so in its own `--help`, because an operator who expects `--check` to see `origin` would read a clean result as more than it is.
- **Zero writes, not "no other writes" (AC-0003).** The allocator only ever reads. Selecting a destination and writing one are different acts, and the write stays inside the existing admission transaction where confinement, provenance and authority transfer already apply. The snapshot assertion covers the repository root as well as the scanned directory, so a stray cache file elsewhere is caught too.
- **Confinement through every component, and a link policy that fails closed (AC-0017).** `file_safety.validate_confined_directory` covers the directory and its ancestors; entry classification then stats without following, so an outside-namespace link is skipped without a dereference — a dangling one included — while an in-namespace symlink, FIFO, device, or entry that became uninspectable between listing and classification refuses. `classify_entry`'s reason for using `stat(follow_symlinks=False)` rather than `is_file()` applies here unchanged: those predicates return `False` on any `OSError`, so an entry removed mid-scan is silently dropped and the scan reports clean without having seen it.
- **Git stays local, bounded and unredirected (AC-0018).** Local refs only and no fetch; a fixed argument list with `shell=False`; `stdin=DEVNULL`; the `GIT_*` redirect variables removed from the child environment so an inherited `GIT_DIR` cannot point the scan at another object store; and bounds on both wall time and the size of the listing consumed, since an oversized remote tree is a memory exhaustion path. Every breach is an AC-0011 refusal, not a partial answer.
- **Diagnostics name the outcome, never the input (AC-0019).** One bounded line, no raw `Level`, no filename, no Git stderr. The `Level` field is open and adopter-controlled, so reflecting it is both a disclosure path and a terminal-injection path; the outcome is what the caller needs and the input is what it already has.
- **Classify by name before applying the integrity refusal.** `file_safety.list_confined_regular_files` refuses *every* symlink, which would let an adopter's `notes -> ../elsewhere` link in the intents directory fail the whole scan even though AC-0004 says an outside-namespace name is skipped without incident. So the directory itself is validated with `file_safety.validate_confined_directory`, and entries are then enumerated with `os.scandir` plus a `stat(follow_symlinks=False)` classification — the shape `next-ordinal.py:213-250` already uses, which raises only on a **record-looking** symlink. An in-namespace link refuses; an outside-namespace one is skipped. The copied `file_safety.py` remains the blessed source of the directory-confinement primitive, which is why the copy and its byte-identity pin stay.
- Carry the rest of `_remote_ordinals` over intact — the `GIT_*` redirect scrub, `--literal-pathspecs`, `-z`, and the root-relative pathspec run from the repository root. Each of those comments in the source records a defect already paid for once.

**Done when:** `python3 -m pytest packs/core/tests/skills/work-intake/ -q` is green, including one case per exit code; then commit, run `make build-self` — it refuses a dirty tree, so the commit comes first — and commit the regenerated projections, after which `python3 -m agentbundle catalogue self-host --root . --check` passes. Regeneration belongs to every task that edits `.apm/`, not to T4: `self-host --check` compares projections to source, and T3's sessions exercise the installed skills, so both need current projections before they can mean anything. T4 keeps only the final drift check.

**Touches:** packs/core/.apm/skills/work-intake/scripts/intent_ordinal.py, packs/core/.apm/skills/work-intake/scripts/file_safety.py, packs/core/tests/skills/work-intake/test_intent_ordinal.py

### T2: Pinned to its owner and to the untyped allocator, and admitted to the roster

**Depends on:** T1

**Mode:** TDD

**Tests:**

- `test_the_mapping_matches_its_owner_in_both_directions` (AC-0014) — `stub: true`
- `test_the_parser_recognizes_exactly_the_owner_tokens` (AC-0014) — `stub: true`
- `test_every_live_typed_file_satisfies_the_owner_shape` (AC-0013) — `stub: true`
- `test_paired_fixtures_agree_with_the_untyped_allocator` (AC-0005) — `stub: true`
- `test_origin_widens_the_view_but_not_to_an_unpushed_peer` (AC-0005) — `stub: true`
- `test_the_baseline_agrees_with_the_hand_authored_corpus` (AC-0001) — `stub: true`

Exact, compiles, and red at collection against the absent module. The seam was not implementation-discovered: T1 fixes the callable surface, and the one genuinely unknown piece — whether the owner's table parses out of Markdown prose — was settled during PLAN by running `_OWNER_ROW` against the real file, which returns exactly the four pairs it should.

```python
# STUB: AC-0001, AC-0005, AC-0013, AC-0014
# Stored and validated in PLAN's T2 Tests: subsection. This is a roster test
# because it reads a second pack's script and the repository's own docs/, which
# a pack test may not reach (tests/AGENTS.md:22-25).
"""Cross-pack equivalence and owner-parity for the typed ordinal allocator."""

import importlib.util
import pathlib
import re
import subprocess
import sys

import pytest

sys.dont_write_bytecode = True

ROOT = pathlib.Path(__file__).resolve().parents[2]
OWNER = ROOT / "docs/product/intents/FEAT-0001-intent-identity-and-registration.md"
INTENTS = ROOT / "docs/product/intents"


def _load(name: str, path: pathlib.Path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


TYPED = _load(
    "typed_intent_ordinal",
    ROOT / "packs/core/.apm/skills/work-intake/scripts/intent_ordinal.py",
)
UNTYPED = _load(
    "adr_next_ordinal",
    ROOT / "packs/governance-extras/.apm/skills/new-adr/scripts/next-ordinal.py",
)

_OWNER_ROW = re.compile(r"^\|\s*`([a-z-]+)`\s*\|\s*`([A-Z]+)`\s*\|")


def owner_table() -> dict[str, str]:
    """Parse the level-to-token table out of the intent's ## Boundary."""
    rows = {}
    for line in OWNER.read_text(encoding="utf-8").splitlines():
        match = _OWNER_ROW.match(line.strip())
        if match:
            rows[match.group(1)] = match.group(2)
    assert rows, "the owner's table did not parse; its shape changed"
    return rows


def test_the_mapping_matches_its_owner_in_both_directions() -> None:
    """AC-0014: no missing entry, no changed token, and no extra one."""
    assert TYPED.LEVEL_TOKENS == owner_table()


def test_the_parser_recognizes_exactly_the_owner_tokens() -> None:
    """AC-0014: the parser namespace cannot be widened past the table."""
    assert set(TYPED.NAMESPACE_TOKENS) == set(owner_table().values())


def test_every_live_typed_file_satisfies_the_owner_shape() -> None:
    """AC-0013: the narrowed grammar reclassifies nothing on disk."""
    introduced = [
        path.name
        for path in INTENTS.glob("*.md")
        if TYPED.classify(path.name) != "outside"
    ]
    assert introduced, "no typed intent found; the corpus or the classifier changed"
    assert [n for n in introduced if TYPED.classify(n) != "valid"] == []


@pytest.mark.parametrize("token", sorted(owner_table().values()))
def test_paired_fixtures_agree_with_the_untyped_allocator(
    token: str, tmp_path: pathlib.Path
) -> None:
    """AC-0005: one max+1 rule across both filename grammars."""
    typed_dir = tmp_path / f"typed-{token}"
    untyped_dir = tmp_path / f"untyped-{token}"
    typed_dir.mkdir()
    untyped_dir.mkdir()
    for ordinal in (3, 7):
        (typed_dir / f"{token}-{ordinal:04d}-x.md").write_text("", encoding="utf-8")
        (untyped_dir / f"{ordinal:04d}-x.md").write_text("", encoding="utf-8")
    assert TYPED.next_typed_ordinal(typed_dir, token) == UNTYPED.next_ordinal(
        str(untyped_dir)
    )


def _git(directory: pathlib.Path, *arguments: str) -> None:
    subprocess.run(
        ["git", *arguments], cwd=directory, check=True,
        stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
    )


def test_origin_widens_the_view_but_not_to_an_unpushed_peer(
    tmp_path: pathlib.Path,
) -> None:
    """AC-0005: committed-and-pushed records count; a peer's unpushed work cannot."""
    token = sorted(owner_table().values())[0]
    upstream = tmp_path / "upstream"
    upstream.mkdir()
    _git(upstream, "init", "--initial-branch=main")
    records = upstream / "records"
    records.mkdir()
    (records / f"{token}-0009-pushed.md").write_text("", encoding="utf-8")
    _git(upstream, "add", "-A")
    _git(upstream, "-c", "user.email=t@example.invalid", "-c", "user.name=t",
         "commit", "-m", "seed")

    clone = tmp_path / "clone"
    _git(tmp_path, "clone", "--quiet", str(upstream), str(clone))
    local_records = clone / "records"
    assert TYPED.next_typed_ordinal(local_records, token) == 10

    peer = tmp_path / "peer"
    _git(tmp_path, "clone", "--quiet", str(upstream), str(peer))
    (peer / "records" / f"{token}-0020-unpushed.md").write_text("", encoding="utf-8")
    _git(peer, "add", "-A")
    _git(peer, "-c", "user.email=t@example.invalid", "-c", "user.name=t",
         "commit", "-m", "peer")
    assert TYPED.next_typed_ordinal(local_records, token) == 10


def test_the_baseline_agrees_with_the_hand_authored_corpus() -> None:
    """AC-0001: the allocator's next number is one above the live maximum."""
    for token in sorted(owner_table().values()):
        live = [
            int(m.group(1))
            for path in INTENTS.glob(f"{token}-*.md")
            if (m := re.match(rf"^{token}-(\d{{4,}})-", path.name))
        ]
        expected = (max(live) + 1) if live else 1
        assert TYPED.next_typed_ordinal(INTENTS, token) == expected
```

**Approach:**

- Load both scripts by path under distinct module names, following `test_next_ordinal.py:14-20`. Do not put either `scripts/` directory on `sys.path`.
- Roster admission is three edits, not one file (`tests/AGENTS.md:27-42`), and they are part of this task rather than a follow-up: the named step in `build-check.yml` must sit **above** the bulk `pytest tests/ -q` step or it never runs, and `tools/lint-ci-parity.py` gains the matching `STEP_DISPOSITION` of `LOCAL("test-after-build-check")`. No `.workspace-prune-protected.toml` entry is needed, because this test names no `docs/specs/<slug>` literal.
- Add the `file_safety.py` byte-identity assertion for the new copy beside the existing `close-work` one at `tests/roster/test_close_work_extraction_and_immediate_disposition.py:853-857`. `packs/AGENTS.local.md:54-57` requires it for every hand-maintained `packs/**` copy; without it a source-side hardening fix never reaches this copy and nothing goes red.
- Run `ruff check .` after adding the file: the repository lint targets do not cover it (`tests/AGENTS.md:44-46`).

**Done when:** `python3 -m pytest tests/roster/test_typed_ordinal_collision_equivalence.py tests/roster/test_close_work_extraction_and_immediate_disposition.py -q` is green, `python3 tools/lint-ci-parity.py` passes, and `ruff check .` is clean.

**Touches:** tests/roster/test_typed_ordinal_collision_equivalence.py, tests/roster/test_close_work_extraction_and_immediate_disposition.py, .github/workflows/build-check.yml, tools/lint-ci-parity.py

### T3: Both entry paths, one without a shell

**Depends on:** T1

**Mode:** Goal-based check for the prose and manifest assertions, plus Visual / manual QA for the six recorded sessions

**Tests:** `no stub (mode)` for the prose assertions; the sessions are manual QA.

- § 6 names the allocation step and its script, and states that the allocated ordinal is expressed as a prefixed slug in the confirmed repository destination it already passes to `intake-intent` (AC-0006).
- § 6 distinguishes the two refusal classes: an absent or unmapped level means the bare slug, and admission and registration proceed unchanged (AC-0007); an allocation, scan or parse failure while **creating** at a mapped level stops before any write or registration (AC-0010). One unprefixed fallback for both would write the very thing AC-0009 forbids.
- `intake-intent`'s Procedure step 3 states that **creating** at a mapped level requires an already-allocated ordinal in the confirmed destination, that a prefix supplied with the request is not accepted as proof of allocation, and that it derives none itself; lacking one it stops and names the path that allocates (AC-0009).
- Procedure step 3 states that an existing repository path is preserved whether or not it carries a prefix, so an existing unprefixed mapped-level intent is updated in place with no allocation and no refusal (AC-0009).
- A construction check over `intake-intent/SKILL.md` frontmatter and its `## Boundaries` block rejects shell, network and any new tool (AC-0008). The existing suite exercises the renderer and never opens `SKILL.md`, so it cannot carry this claim.
- `packs/core/tests/skills/intake-intent/test_intake_intent.py` passes unamended (AC-0008).
- Both skills' `evals/` cover the new behaviour: `work-intake` a mapped-level admission and an unmapped-level one, `intake-intent` the creation refusal and the existing-path preservation (`packs/AGENTS.md:60`).
- Six recorded sessions, one per end-to-end case the spec enumerates (AC-0006, AC-0007, AC-0009). Through `work-intake`: (1) a mapped level lands at `docs/product/intents/<TYPE>-NNNN-<slug>.md`; (2) an unmapped level lands at `docs/product/intents/<slug>.md` **and is registered** — this session continues past the write through registration, because AC-0007's outcome is "admitted *and registered*" and stopping at the file cannot see it. Direct to `intake-intent`: (3) a new mapped-level request refuses; (4) the same request carrying an arbitrary `<TYPE>-9999-` prefix refuses on the same ground rather than being trusted; (5) an existing **unprefixed** mapped-level intent is updated in place, no allocation and no refusal; (6) an existing **prefixed** intent is updated in place with its ordinal unchanged. Each records its stop boundary: sessions 1 and 6 stop at the durable write, session 2 at the registered entry, sessions 3 and 4 at the refusal before any write, session 5 at the in-place edit.

**Approach:**

- `work-intake`: one step before the existing delegation sentence at `SKILL.md:331-333`. It must not restate admission policy — § 6 already forbids this router from copying `intake-intent`'s template or certifying its result — and the allocation step is a destination computation, not an admission decision.
- `intake-intent`: one clause on Procedure step 3, and nothing else in the body. The owner cannot allocate — its `## Boundaries` refuses a shell and this slice does not move that line — so creation at a mapped level refuses, unconditionally on a supplied prefix. One rule, stated once: a prefix the owner cannot verify against the working tree and `origin` proves nothing, so accepting it would readmit the silent-wrong failure through a second door. The cost is real and bounded — direct `intake-intent` no longer creates a new mapped-level intent, and the refusal names `work-intake` as the one-step path that does — while every existing-path update is untouched, which is most of what the direct route is used for.
- AC-0008 needs two pieces of evidence, not one. `test_intake_intent.py` passing unamended shows admission behaviour is intact; it never opens `SKILL.md`, so it cannot show that no capability was added. The manifest check carries that half. That the slice's only body edit there is one clause of Procedure step 3 is a verification choice this plan owns, not part of the criterion.

**Done when:** the prose and manifest assertions pass, `test_intake_intent.py` is green unamended, both eval harnesses cover the new behaviour, `make build-self` has been re-run on a clean tree so the sessions exercise current projections, and the six sessions are recorded in `notes/verification-ledger.md` with their stop boundaries.

**Touches:** packs/core/.apm/skills/work-intake/SKILL.md, packs/core/.apm/skills/intake-intent/SKILL.md, packs/core/.apm/skills/work-intake/evals/, packs/core/.apm/skills/intake-intent/evals/, packs/core/tests/skills/work-intake/test_work_intake.py, packs/core/tests/skills/intake-intent/test_intake_intent_manifest.py, docs/specs/typed-intent-ordinal-allocator/notes/verification-ledger.md

### T4: Release surface

**Depends on:** T1, T2, T3

**Mode:** Goal-based check

This task discharges no acceptance criterion and states so deliberately: it carries no observable outcome of its own, only the repository rails a pack-content change owes. Folding it into T1 or T3 would put a version bump inside a behavioural task and force the bump before the other task settled.

**Tests:**

- `packs/core/pack.toml` and `packs/core/.claude-plugin/plugin.json` carry the same bumped version — **patch**, because a script added inside an existing skill is changed content of that skill rather than a new projected primitive (`packs/AGENTS.md:43-47`).
- `docs/product/changelog.md` has a `core` release heading matching that version, topmost among `core` headings, with a `### Highlights` bullet.
- `make build-self` regenerates `.claude-plugin/marketplace.json` and the adapter projections on a clean tree.

**Approach:**

- Bump last, after T1–T3 are settled, so one version covers all of them. Read the current `core` version at that moment rather than reserving one now — an unpushed bump collides silently with a peer session's.

**Done when:** `make lint-ruff lint-mypy` and `make build-self` pass on a clean tree.

**Touches:** packs/core/pack.toml, packs/core/.claude-plugin/plugin.json, docs/product/changelog.md

## Rollout

Pack content only; adopters pick it up on the next install. New intents created through `work-intake` gain a typed prefix; existing files are untouched and existing references keep resolving. Two behaviour changes to flag in the changelog entry. An adopter whose intents carry no `Level`, or a level outside the parent's table, sees exactly today's behaviour — an unprefixed filename. An adopter who invokes `intake-intent` directly to create a new mapped-level intent now gets a refusal naming `work-intake`; updating an existing intent that way is unchanged.

## Risks

- **The allocator inherits the silent-wrong failure it was built to avoid.** A refusal that returns `0001`, or a `--check` that prints clean over a directory it never read, is the same defect in a new file. T1's refusal cases are the guard, and they assert the absence of a number rather than the presence of an error string.
- **The remote distinction collapses in either direction.** Refusing on a *missing* remote makes every positive fixture in the suite unsatisfiable; degrading on a *failed* query hands back the plausible-but-wrong ordinal. AC-0015 and AC-0011 fail on opposite errors, and T1 asserts both.
- **Equivalence asserted by construction.** A test that runs both scripts over a directory neither can parse agrees trivially. T2's paired fixtures are what make the agreement load-bearing.
- **The bypass reopens, or the refusal is over-applied.** `SKILL.md:60` routes an explicit `intake-intent` request past § 6, so an allocator wired only into § 6 is skipped there — AC-0009 is the guard, and T3's direct-path sessions are the only evidence that reaches it. The opposite error costs more: a refusal firing for an *unmapped* level, or for an existing-path update, would block admissions and edits that must proceed. T3's six sessions exercise a mapped refusal, an unmapped registered success, and both existing-path updates for exactly that reason.
- **The integration proved only in prose.** Both skills are bodies, so T3's assertions establish the instruction, not the behaviour. The six recorded sessions are the only evidence that reaches the written filename, and they are observations rather than a suite.
- **A roster test that runs but attributes nothing.** A named step placed below the bulk `pytest tests/ -q` step in a fail-fast job never executes. T2 owns the placement and `tools/lint-ci-parity.py` is what catches the mismatch.

## Changelog

- 2026-09-20 — Spec-stage security review run, as adversarial round 3 said was owed. Five findings, every one of the shape "the control is in the plan but not in the contract", and `AGENTS.md` forbids cutting a trust-boundary control — so all five are now criteria. The one real gap: an adopter controls the open `Level` string and `work-intake` holds `Bash`, so an implementation that interpolated it into a command would hand over the router's shell authority; AC-0016 fixes the executable, flags and argument count and requires every untrusted value to cross as a single data argument, with the returned value validated against the closed grammar before a destination is composed from it. AC-0003 was also readable as permission to write the intent, and now states zero mutations. AC-0017 covers confinement through every path component and a fail-closed link policy, AC-0018 local-ref-only bounded Git with a scrubbed child environment, and AC-0019 bounded diagnostics that reflect no adopter text. Eleven cases added to T1's stub, re-validated at 43 failed / 11 passed.

- 2026-09-20 — Adversarial round 3 returned 2 blockers and 1 concern, all resolved. `RemoteView` now carries record **names** rather than an ordinal set: integers alone could not let a malformed remote name fail the scan, could not tell one record present in both views from two, and would have forced the classifier to run twice on different data. The scope split that goes with it is inherited rather than invented — `next-ordinal.py` calls `_remote_ordinals` only from `next_ordinal:260`, never from `duplicate_ordinals:213` — so allocation unions and `--check` reports on one directory, stated in the script's own `--help` so a clean result is not read as more than it is. And the `work-intake` boundary now has a contract: one invocation, three exit codes, so the caller never branches on empty stdout and "no ordinal because the altitude has none" cannot be confused with "no ordinal because I could not look". Six cases added to T1's stub, re-validated at 32 failed / 11 passed.

- 2026-09-20 — Adversarial round 2 returned 7 blockers and 1 concern; all eight resolved, and two were real design decisions rather than plan hygiene. The remote view is now an explicit tri-state with six enumerated outcomes, because the borrowed `_git_output` funnels every error *and* a genuinely absent remote into the same empty set, so changing only the timeout arm could never separate AC-0011 from AC-0015. And entry enumeration no longer uses `list_confined_regular_files`, which refuses every symlink: classification now precedes the integrity refusal, so an outside-namespace link is skipped and an in-namespace one refuses, matching `next-ordinal.py`'s record-looking-symlink rule. The rest: both TDD tasks carry exact, compiled, red-validated stubs with `# STUB:` markers and per-test `stub: true` records (T1 26/10, T2 red at collection); T2 no longer claims the implementation-discovered exception, since running the owner-table parser against the real file during PLAN settled the one unknown; T1's stub derives its tokens from the module's own mapping so the owner's table is checked in exactly one place; projection regeneration moved into every `.apm/`-editing task, because `self-host --check` and the sessions both read projections; and T3 now records six sessions, one per enumerated case, with the unmapped admission continuing through registration because that is what AC-0007 promises.

- 2026-09-20 — Adversarial review on the spec+plan pair returned 7 blockers and 5 concerns; all twelve are resolved and eight were repository mechanics this plan had not reached. The pivotal one: every positive fixture was an `origin`-less `tmp_path`, while AC-0011 made a missing `origin` a refusal — no implementation could pass both, so AC-0015 now separates a missing remote from a broken query. The rest: T1's stub is now exact, compiled and red-validated in scratch per `work-loop/SKILL.md:252`; T2 carries the three roster-admission edits from `tests/AGENTS.md:27-42` and the `file_safety.py` byte-identity pin from `packs/AGENTS.local.md:54-57`; T3 carries both skills' eval-harness updates per `packs/AGENTS.md:60` and states the supplied-prefix rule once instead of twice contradictorily; T4 is a patch bump, not minor, and says plainly that it discharges no criterion; the Approach summary's reversed `origin` and filename-class claims are corrected; the construction-test summary no longer describes the abandoned real-corpus design; T3 declares both its modes; and the scope inventory is one list separating written, generated, read-only and deliberately-unamended files.

- 2026-09-20 — Round 9: forward-only was attributed to ADR-0108 D6, which governs spec-directory identifiers. The parent intent's `## Guardrail` and the brief's renumber non-goal own the rule for intents and cite D6 only as precedent, so the attribution moved. The fixed corpus counts came out with it: the brief states that a measured count is evidence of scale and not the obligation, so every corpus claim is now derived at test time.
- 2026-09-20 — Round 8: the no-unprefixed-write invariant was universal and collided with forward-only adoption. Most live intents are unprefixed and sit at a mapped level, so a universal invariant would have made each of them either unwritable or a violation on its next edit. The invariant and AC-0010 are now scoped to creation, and the update-in-place case is stated and tested.
- 2026-09-20 — Round 7: three fixes. Validity was a prefix test inherited from `next-ordinal.py`'s `[-.]`, so a slugless `FEAT-0001.md` or an unanchored `FEAT-0001.txt` would have raised the maximum against the parent's `<TYPE>-NNNN-<slug>.md` contract — AC-0013 anchors it, and all 14 live typed files were checked against the narrower shape first. AC-0014 makes the mapping check bidirectional, since a one-way check would pass a parser that grew a token the owner never listed. AC-0008 dropped its edit-location and named-test clauses to the plan, keeping the criterion behavioural.
- 2026-09-20 — Round 6: the level-to-token table was copied into the spec under an ownership claim that traced to nothing. The parent intent's `## Boundary` has held it as an owner decision since 2026-09-18, and the brief says at `:71` that it is not restated. The spec now cites the owner and keeps only the matching behaviour, which is what this slice actually decides.
- 2026-09-20 — Round 5: four gaps, all in the contract rather than the design. The level-to-token mapping was never stated — ADR-0033 D2 grounds the four recognized `Level` values but maps none of them, so the table is now declared in the spec. AC-0004's classes were enumerated rather than derived, so `FEAT-0001x.md` and `FEAT-0001` fell outside all three; they are now complementary against one introducer. `origin` failures were uncovered by AC-0011, which would have let a Git timeout degrade to a working-tree-only ordinal — the exact named risk — so they refuse, diverging deliberately from `next-ordinal.py`. And AC-0012 adds the duplicate control's positive half: same-type duplicates fail, cross-type equal ordinals pass.
- 2026-09-20 — Round 4: the direct path's supplied-ordinal escape valve closed. The owner cannot check a handed-in `FEAT-9999-` against the working tree and `origin`, so accepting a prefix as proof of allocation was the same silent-wrong failure through a second door; a new mapped-level direct admission now refuses unconditionally, with existing-path updates explicitly unaffected. AC-0004's partition given an exact grammar with scan failures split out to AC-0011, and the ADR/RFC non-answer assertion dropped — it could not be distinguished from AC-0001's first allocation.
- 2026-09-20 — Round 3 cleared the ownership finding and reached the criteria. Four fixes: AC-0007's unprefixed fallback was reachable by an allocation failure on a mapped level, contradicting AC-0009, so AC-0010 splits the refusal classes; AC-0005 claimed the `origin` union catches an unpushed sibling, the opposite of what ADR-0108:41 records, and asserted an undefined equivalence, now defined over paired fixtures; AC-0004 had no parse domain, which would have made the unprefixed live intents unallocatable, so three filename classes are declared; AC-0008's evidence could not see a capability change, so a manifest check carries that half.
- 2026-09-20 — Round 2 held the ownership finding: making the bypass visible is not making the allocator reachable, since a confirmed missing ordinal still writes a mapped intent unprefixed. The direct path changed from confirm to refuse — it writes only a destination that already carries an ordinal and derives none — so AC-0001 is universal on both paths.
- 2026-09-20 — Shaping review found the allocator owned by the router rather than by admission. The premise held: `work-intake/SKILL.md:60` routes an explicit `intake-intent` request directly to the owner, bypassing § 6. Resolved by covering both paths with different mechanisms rather than by relocating the allocator — the owner declares no shell and this slice does not grant one — so T3 gained the direct-path arm and AC-0009, and AC-0008 moved from a whole-file diff to a capability assertion.
- 2026-09-20 — Authored. Integration re-pointed from `intake-intent` to `work-intake`: `work-intake` already supplies the confirmed repository destination and already declares `Bash`, so allocation needs no new capability and ADR-0098 D2 keeps `intake-intent` the owner of admission with its files unchanged. Acceptance criteria labelled per ADR-0108 and each bound to one verification group.
