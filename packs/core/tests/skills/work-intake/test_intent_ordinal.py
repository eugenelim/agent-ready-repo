# STUB: AC-0001, AC-0003, AC-0004, AC-0005, AC-0006, AC-0007, AC-0010, AC-0011,
#       AC-0012, AC-0013, AC-0015, AC-0017, AC-0018, AC-0019, AC-0020, AC-0021,
#       AC-0024
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
    nested.chmod(0o000)
    try:
        assert MODULE.next_typed_ordinal(nested, TOKENS[0]) is None
    finally:
        nested.chmod(0o700)


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


def test_check_refuses_a_missing_directory(tmp_path: pathlib.Path, monkeypatch) -> None:
    """AC-0011: never report clean for a directory it did not read."""
    monkeypatch.chdir(tmp_path)
    assert MODULE.main(["--check", "absent"]) == 1


def test_check_has_both_halves(tmp_path: pathlib.Path, monkeypatch) -> None:
    """AC-0012: same-type duplicates fail; equal ordinals across types pass."""
    monkeypatch.chdir(tmp_path)
    for token in TOKENS:
        (tmp_path / f"{token}-0001-a.md").write_text("", encoding="utf-8")
    assert MODULE.main(["--check", "."]) == 0
    (tmp_path / f"{TOKENS[0]}-0001-b.md").write_text("", encoding="utf-8")
    assert MODULE.main(["--check", "."]) == 1


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
    monkeypatch.chdir(tmp_path)
    monkeypatch.setattr(
        MODULE,
        "remote_view",
        lambda _d: MODULE.RemoteView(frozenset({f"{TOKENS[0]}-0001-b.md"}), "ok"),
    )
    assert MODULE.main(["--check", "."]) == 0


@pytest.mark.parametrize("token", TOKENS)
def test_the_cli_prints_the_allocated_ordinal(
    token: str, tmp_path: pathlib.Path, capsys
, monkeypatch) -> None:
    """AC-0006: exit 0 and the ordinal on stdout alone."""
    monkeypatch.chdir(tmp_path)
    assert MODULE.main(["--dir", ".", "--token", token]) == 0
    captured = capsys.readouterr()
    assert captured.out.strip() == f"{token}-0001"
    assert captured.err == ""


def test_the_cli_refuses_a_scan_it_could_not_complete(
    tmp_path: pathlib.Path, capsys
, monkeypatch) -> None:
    """AC-0010, AC-0011: exit 1, nothing on stdout, one line on stderr."""
    monkeypatch.chdir(tmp_path)
    token = TOKENS[0]
    (tmp_path / f"{token}-12-y.md").write_text("", encoding="utf-8")
    assert MODULE.main(["--dir", ".", "--token", token]) == 1
    captured = capsys.readouterr()
    assert captured.out == ""
    assert captured.err.strip()


@pytest.mark.parametrize(
    "token",
    ["EPIC", "feature", "FEAT; rm -rf /", "FEAT\nFEAT", "--dir=/etc", "$(id)",
     "`id`", "FEAT'", 'FEAT"', "FEAT\x00", "", "F" * 64],
)
def test_an_out_of_set_token_is_refused(
    token: str, tmp_path: pathlib.Path, capsys
, monkeypatch) -> None:
    """AC-0020: defence in depth behind the caller's own resolution."""
    monkeypatch.chdir(tmp_path)
    assert MODULE.main(["--dir", ".", "--token", token]) == 1
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


def test_a_traversing_or_absolute_dir_argument_is_refused(tmp_path: pathlib.Path, monkeypatch) -> None:
    """AC-0020, AC-0017: --dir is repository-relative with no `..` segment."""
    monkeypatch.chdir(tmp_path)
    for candidate in ("../escape", "/etc", str(tmp_path), "docs/../../escape"):
        assert MODULE.main(["--dir", candidate, "--token", TOKENS[0]]) == 1


def test_the_git_child_environment_is_scrubbed_and_local(
    tmp_path: pathlib.Path, monkeypatch
) -> None:
    """AC-0018: no redirect variables, no shell, closed stdin, no fetch.

    Seams `Popen`, not `run`: AC-0021 requires the byte bound enforced while
    reading, and `run` buffers the whole result before anything can check it.
    """
    seen: dict[str, object] = {}

    def _record(arguments, **keywords):
        seen["arguments"] = list(arguments)
        seen["keywords"] = keywords
        raise OSError("no git in this fixture")

    monkeypatch.setattr(MODULE.subprocess, "Popen", _record)
    monkeypatch.setenv("GIT_DIR", "/elsewhere/.git")
    monkeypatch.setenv("GIT_OBJECT_DIRECTORY", "/elsewhere/objects")
    MODULE.remote_view(tmp_path)

    assert seen["keywords"]["shell"] is False
    assert seen["keywords"]["stdin"] is MODULE.subprocess.DEVNULL
    assert seen["keywords"]["stdout"] is MODULE.subprocess.PIPE
    environment = seen["keywords"]["env"]
    for variable in MODULE.GIT_REDIRECT_VARIABLES:
        assert variable not in environment
    assert "fetch" not in seen["arguments"]


def test_the_child_environment_forbids_a_lazy_fetch(
    tmp_path: pathlib.Path, monkeypatch
) -> None:
    """AC-0018: verified on a --filter=tree:0 fixture, not inferred from argv."""
    seen: dict[str, object] = {}

    def _record(arguments, **keywords):
        seen["keywords"] = keywords
        raise OSError("no git in this fixture")

    monkeypatch.setattr(MODULE.subprocess, "Popen", _record)
    MODULE.remote_view(tmp_path)
    assert seen["keywords"]["env"]["GIT_NO_LAZY_FETCH"] == "1"


@pytest.mark.parametrize(
    "config",
    [
        {"remote.origin.promisor": "true"},
        {"extensions.partialClone": "origin"},
        {"remote.origin.promisor": "false", "extensions.partialClone": "origin"},
    ],
)
def test_a_promisor_designation_refuses_before_any_object_read(
    config: dict[str, str], tmp_path: pathlib.Path, monkeypatch
) -> None:
    """AC-0018: no object-reading command runs, which isolates this from the env var.

    On a git that honours GIT_NO_LAZY_FETCH the transport is blocked either
    way, so a test that only observes a refusal cannot tell this check from
    its absence — and its absence is what fails on an older git. `git config`
    is allowed to run first: it resolves no object and cannot lazily fetch.
    """
    launched: list[list[str]] = []

    def _record(arguments, **keywords):
        launched.append(list(arguments))
        raise OSError("no git in this fixture")

    monkeypatch.setattr(MODULE.subprocess, "Popen", _record)
    monkeypatch.setattr(MODULE, "git_config_values", lambda _d: dict(config))
    view = MODULE.remote_view(tmp_path)
    assert view.state == "failed"
    assert not [a for a in launched if "ls-tree" in a]


def test_the_refusal_causes_are_a_closed_set(tmp_path: pathlib.Path) -> None:
    """AC-0010, AC-0024: a marker is selected from tokens, never composed."""
    assert MODULE.REFUSAL_CAUSES == (
        "unparsed-name",
        "incomplete-scan",
        "remote-unavailable",
        "bound-exceeded",
    )


def test_the_bounds_are_module_constants(tmp_path: pathlib.Path) -> None:
    """AC-0021: every bound is lowerable, so no test builds an oversized input."""
    assert MODULE.GIT_TIMEOUT_SECONDS == 5
    assert MODULE.TOTAL_TIMEOUT_SECONDS == 10
    assert MODULE.MAX_ENTRIES == 65_536
    assert MODULE.MAX_GIT_RESULT_BYTES == 8 * 1024 * 1024


def test_diagnostics_reflect_no_untrusted_text(
    tmp_path: pathlib.Path, capsys
, monkeypatch) -> None:
    """AC-0019: bounded, single-line, and free of reflected adopter content."""
    monkeypatch.chdir(tmp_path)
    hostile = "FEAT-\x1b[31m-AKIAIOSFODNN7EXAMPLE\nsecond-line"
    assert MODULE.main(["--dir", ".", "--token", hostile]) == 1
    message = capsys.readouterr().err
    assert message.count("\n") == 1
    assert len(message.encode("utf-8")) <= MODULE.DIAGNOSTIC_BYTE_LIMIT == 200
    for fragment in ("AKIAIOSFODNN7EXAMPLE", "\x1b", "second-line"):
        assert fragment not in message


# ── Deferred assertions, filled after the module existed ──────────────────────
# Each needed a fixture the approved stub could not build, and each is recorded
# as deferred in the plan's T1 Tests: subsection.


def test_a_real_invocation_writes_no_bytecode(tmp_path: pathlib.Path) -> None:
    """AC-0003: bytecode is a write, and the production path must not make one.

    Runs the CLI as a subprocess, which is how a skill invokes it: the
    in-process cases cannot see this, because the suite itself sets
    `sys.dont_write_bytecode` and would mask a script that does not.
    """
    import subprocess

    script = _SCRIPTS / "intent_ordinal.py"
    cache = script.parent / "__pycache__"
    existing = set(cache.iterdir()) if cache.is_dir() else set()
    (tmp_path / f"{TOKENS[0]}-0001-a.md").write_text("", encoding="utf-8")
    result = subprocess.run(
        [sys.executable, os.fspath(script), "--dir", ".", "--token", TOKENS[0]],
        cwd=tmp_path, capture_output=True, text=True, check=False,
    )
    assert result.returncode == 0, result.stderr
    assert result.stdout.strip() == f"{TOKENS[0]}-0002"
    current = set(cache.iterdir()) if cache.is_dir() else set()
    assert current == existing


def test_an_origin_without_a_resolvable_head_refuses(
    tmp_path: pathlib.Path, monkeypatch
) -> None:
    """AC-0015: `origin` present and its default branch unreadable is a failure.

    Not `absent`: `refs/remotes/origin/main` can hold records while the
    symbolic ref is missing, so a working-tree-only answer here is the
    plausible duplicate the allocator exists to avoid.
    """
    answers = {
        "config": "",
        "rev-parse": os.fspath(tmp_path),
        "remote": "origin",
        "symbolic-ref": "",
    }

    def _fake(directory, arguments, deadline):
        for key, value in answers.items():
            if key in arguments:
                return value
        return None

    monkeypatch.setattr(MODULE, "_git", _fake)
    assert MODULE.remote_view(tmp_path).state == "failed"
    (tmp_path / f"{TOKENS[0]}-0001-a.md").write_text("", encoding="utf-8")
    assert MODULE.next_typed_ordinal(tmp_path, TOKENS[0]) is None


def test_an_oversized_listing_refuses_before_buffering(
    tmp_path: pathlib.Path, monkeypatch
) -> None:
    """AC-0021: the byte bound is checked inside the read loop.

    Driven by lowering the bound rather than by building an 8 MiB listing: the
    shipped value proves nothing the lowered one does not, and a real fixture
    that size is slow.
    """
    monkeypatch.setattr(MODULE, "MAX_GIT_RESULT_BYTES", 8)

    class _Child:
        returncode = 0

        def __init__(self) -> None:
            self.stdout = self
            self.reads = 0

        def read(self, size: int) -> bytes:
            self.reads += 1
            assert self.reads < 100, "the bound did not stop the read loop"
            return b"x" * 64

        def kill(self) -> None:
            pass

        def wait(self, timeout=None) -> int:
            return 0

    monkeypatch.setattr(MODULE.subprocess, "Popen", lambda *a, **k: _Child())
    with pytest.raises(MODULE._ScanRefused) as refusal:
        MODULE._git(tmp_path, ["config", "--list"], MODULE._deadline())
    assert refusal.value.cause == "bound-exceeded"
