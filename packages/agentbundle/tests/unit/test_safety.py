"""T1b: Tier classification + path-jail + content-hash helpers."""

from __future__ import annotations

from collections.abc import Mapping
from pathlib import Path
from unittest import mock

import pytest
from agentbundle import safety
from agentbundle.config import PackState, State


def _state_with(relpath: str, sha: str) -> State:
    state = State()
    state.packs["core"] = PackState(
        installed_version="0.1.0",
        primitives=["skill"],
        files={relpath: {"sha": sha, "from-pack-version": "0.1.0"}},
    )
    return state


def test_sha256_helpers_match(tmp_path):
    data = b"hello world"
    path = tmp_path / "x.txt"
    path.write_bytes(data)
    assert safety.sha256_bytes(data) == safety.sha256_file(path)


def test_classify_tier_1_when_sha_matches(tmp_path):
    f = tmp_path / "AGENTS.md"
    f.write_bytes(b"original")
    sha = safety.sha256_file(f)
    state = _state_with("AGENTS.md", sha)
    assert safety.classify("AGENTS.md", tmp_path, state) is safety.Tier.TIER_1


def test_classify_tier_2_when_sha_differs(tmp_path):
    f = tmp_path / "AGENTS.md"
    f.write_bytes(b"adopter-edited")
    state = _state_with("AGENTS.md", "0" * 64)
    assert safety.classify("AGENTS.md", tmp_path, state) is safety.Tier.TIER_2


def test_classify_tier_3_when_path_not_in_state(tmp_path):
    state = _state_with("AGENTS.md", "0" * 64)
    f = tmp_path / "src" / "app.py"
    f.parent.mkdir(parents=True)
    f.write_bytes(b"adopter code")
    assert safety.classify("src/app.py", tmp_path, state) is safety.Tier.TIER_3


def test_classify_tier_1_when_recorded_path_is_absent_on_disk(tmp_path):
    """Recorded under a pack but missing on disk → about to be (re)written."""
    state = _state_with("AGENTS.md", "deadbeef")
    assert safety.classify("AGENTS.md", tmp_path, state) is safety.Tier.TIER_1


def test_companion_path_basic_extension():
    assert safety.companion_path(Path("AGENTS.md")) == Path("AGENTS.upstream.md")


def test_companion_path_nested_directory():
    assert safety.companion_path(Path("docs/CHARTER.md")) == Path(
        "docs/CHARTER.upstream.md"
    )


def test_companion_path_no_extension():
    assert safety.companion_path(Path("Makefile")) == Path("Makefile.upstream")


def test_write_jailed_refuses_path_escape(tmp_path):
    with pytest.raises(safety.PathJailError, match="refusing to write outside"):
        safety.write_jailed(tmp_path, "../../malicious", b"x")


def test_write_jailed_refuses_absolute_path_escape(tmp_path):
    """An absolute path that points outside `tmp_path` must be refused."""
    outside = Path("/tmp") / "definitely-not-under-the-jail" / "x.txt"
    with pytest.raises(safety.PathJailError):
        # Using a relative form ending up outside is the realistic case;
        # using absolute paths under `root / relpath` would join oddly,
        # so test the realistic case with a `../` escape across symlinks.
        safety.write_jailed(tmp_path, "../" + outside.name, b"x")


def test_write_jailed_writes_inside_root(tmp_path):
    out = safety.write_jailed(tmp_path, "subdir/file.txt", b"hello")
    assert out.read_bytes() == b"hello"
    assert out.is_relative_to(tmp_path.resolve())


def test_write_jailed_is_atomic_no_temp_leftovers(tmp_path):
    safety.write_jailed(tmp_path, "x.txt", b"first")
    safety.write_jailed(tmp_path, "x.txt", b"second")
    files = sorted(p.name for p in tmp_path.iterdir())
    assert files == ["x.txt"]
    assert (tmp_path / "x.txt").read_bytes() == b"second"


def test_write_companion_drops_upstream_file(tmp_path):
    original = tmp_path / "AGENTS.md"
    original.write_bytes(b"adopter-edited")
    safety.write_companion(tmp_path, "AGENTS.md", b"bundle content")
    assert (tmp_path / "AGENTS.upstream.md").read_bytes() == b"bundle content"
    # Original unchanged.
    assert original.read_bytes() == b"adopter-edited"


def test_assert_under_passes_for_path_inside(tmp_path):
    safety.assert_under(tmp_path, tmp_path / "a" / "b")  # no exception


# ---------------------------------------------------------------------------
# Windows reserved-name guard (Windows-portability)
#
# Windows reserves a small set of device names regardless of extension
# (CON.txt → CON), forbids names ending in `.` or ` `, and forbids
# certain characters in filenames. A pack carrying such a path is
# poisonous on Windows even when authored on macOS, so the check fires
# on every OS at the path-jail layer.
# ---------------------------------------------------------------------------


_INVALID_RESERVED_NAMES = [
    "CON",
    "con",
    "Con",
    "PRN",
    "AUX",
    "NUL",
    "COM1",
    "COM9",
    "LPT1",
    "LPT9",
    "con.txt",
    "NUL.log",
    "foo/NUL",
    "foo/bar/PRN.log",
    "deep/path/COM3.tar.gz",
    "lpt5.md",
]


@pytest.mark.parametrize("relpath", _INVALID_RESERVED_NAMES)
def test_assert_portable_name_rejects_reserved_devices(relpath):
    with pytest.raises(safety.PathJailError, match="reserved"):
        safety.assert_portable_name(relpath)


@pytest.mark.parametrize(
    "relpath",
    [
        "bar.",
        "bar ",
        "bar. ",
        "foo/bar.",
        "trailing dot.",
        "trailing space ",
    ],
)
def test_assert_portable_name_rejects_trailing_dot_or_space(relpath):
    with pytest.raises(safety.PathJailError, match="trailing"):
        safety.assert_portable_name(relpath)


@pytest.mark.parametrize(
    "relpath",
    [
        "foo<bar",
        "foo>bar",
        'foo"bar',
        "foo|bar.txt",
        "foo?baz",
        "foo*",
        "weird:colon.txt",
        "nested/has<lt",
    ],
)
def test_assert_portable_name_rejects_forbidden_chars(relpath):
    with pytest.raises(safety.PathJailError, match="forbidden character"):
        safety.assert_portable_name(relpath)


@pytest.mark.parametrize(
    "relpath",
    [
        "AGENTS.md",
        "docs/CHARTER.md",
        "Makefile",
        "foo/bar.txt",
        "con_artist.md",  # prefix only, not exact-stem
        "COM0",           # only COM1-9 are reserved
        "COM10",          # only single digit
        "LPT0.txt",
        "lptastic.md",
        "nul_pointer.c",
        ".gitignore",
        "deep/nested/path/with-dashes.toml",
    ],
)
def test_assert_portable_name_accepts_valid_paths(relpath):
    safety.assert_portable_name(relpath)  # no exception


def test_write_jailed_refuses_reserved_name(tmp_path):
    with pytest.raises(safety.PathJailError, match="reserved"):
        safety.write_jailed(tmp_path, "CON.md", b"x")


def test_write_jailed_refuses_forbidden_character(tmp_path):
    with pytest.raises(safety.PathJailError, match="forbidden character"):
        safety.write_jailed(tmp_path, "weird|file.md", b"x")


def test_copy_jailed_refuses_reserved_name(tmp_path):
    """`copy_jailed` is a sibling write primitive — the portability
    guard runs on it too, so an install-time `cp` of pack content
    cannot land a `CON.md` on a Windows adopter."""
    source = tmp_path / "src.md"
    source.write_text("x\n", encoding="utf-8", newline="\n")
    with pytest.raises(safety.PathJailError, match="reserved"):
        safety.copy_jailed(tmp_path, source, "CON.md")


def test_assert_portable_name_handles_backslash_segments():
    """Defense-in-depth: even though CLI normalises `\\` → `/` at the
    boundary, the guard treats backslashes as separators so a path that
    sneaks past normalisation still hits the check."""
    with pytest.raises(safety.PathJailError, match="reserved"):
        safety.assert_portable_name("foo\\NUL")


def test_classify_returns_tier_2_when_recorded_path_lacks_sha(tmp_path):
    """Defensive branch: a hand-edited state file with a `[pack.X.files] foo`
    entry that lacks the `sha` key. classify can't prove Tier-1 vs Tier-2
    here, so it conservatively returns Tier-2 — and a write goes via
    `.upstream.<ext>` rather than overwriting adopter content.
    """
    from agentbundle.config import PackState, State
    state = State()
    state.packs["weird"] = PackState(
        installed_version="0.1",
        files={"AGENTS.md": {"from-pack-version": "0.1"}},  # no `sha`
    )
    f = tmp_path / "AGENTS.md"
    f.write_bytes(b"anything")
    assert safety.classify("AGENTS.md", tmp_path, state) is safety.Tier.TIER_2


# ---------------------------------------------------------------------------
# assert_projection_jailed — TDD stubs (unify-path-jail-projection-probe)
# ---------------------------------------------------------------------------

def test_assert_projection_jailed_valid_with_prefixes(tmp_path):
    """Valid relpath inside root and within allowed_prefixes → no exception."""
    safety.assert_projection_jailed(
        tmp_path, [".claude/SKILL.md"], [".claude/"], command="test"
    )


def test_assert_projection_jailed_valid_none_prefixes(tmp_path):
    """Valid relpath inside root with allowed_prefixes=None → no exception."""
    safety.assert_projection_jailed(
        tmp_path, ["tools/hook.py"], None, command="test"
    )


def test_assert_projection_jailed_root_escape(tmp_path):
    """Relpath that escapes root via ../ → raises PathJailError."""
    with pytest.raises(safety.PathJailError):
        safety.assert_projection_jailed(
            tmp_path, ["../escape.txt"], None, command="test"
        )


def test_assert_projection_jailed_outside_prefix(tmp_path):
    """Relpath inside root but outside all allowed_prefixes → raises PathJailError."""
    with pytest.raises(safety.PathJailError):
        safety.assert_projection_jailed(
            tmp_path, ["tools/hook.py"], [".claude/"], command="test"
        )


def test_assert_projection_jailed_empty_relpaths(tmp_path):
    """Empty relpaths iterable → no exception."""
    safety.assert_projection_jailed(tmp_path, [], [".claude/"], command="test")


class TestWriteFilesNoFollow:
    """Direct tests for the batch write primitive.

    Reaching it only through `contracts_inspector` with the real 12-contract
    inventory leaves its rejection branches, its retry loop, and its entire
    portable fallback unexercised.
    """

    def test_writes_a_flat_batch(self, tmp_path: Path) -> None:
        written = safety.write_files_no_follow(
            tmp_path / "out", {"a.json": b"alpha", "b.toml": b"beta"}
        )

        assert [path.name for path in written] == ["a.json", "b.toml"]
        assert (tmp_path / "out" / "a.json").read_bytes() == b"alpha"
        assert (tmp_path / "out" / "b.toml").read_bytes() == b"beta"

    def test_default_mode_is_readable_and_mode_is_honoured(
        self, tmp_path: Path
    ) -> None:
        safety.write_files_no_follow(tmp_path / "d", {"a.json": b"x"})
        assert (tmp_path / "d" / "a.json").stat().st_mode & 0o444

        safety.write_files_no_follow(tmp_path / "e", {"a.json": b"x"}, mode=0o600)
        assert not (tmp_path / "e" / "a.json").stat().st_mode & 0o044

    @pytest.mark.parametrize(
        "name", ["", ".", "..", "nested/a.json", "back\\a.json", "CON.json", "a. "]
    )
    def test_refuses_unsafe_filenames(self, tmp_path: Path, name: str) -> None:
        with pytest.raises(safety.PathJailError):
            safety.write_files_no_follow(tmp_path / "out", {name: b"x"})

    def test_content_pairs_with_its_own_name_for_any_mapping(
        self, tmp_path: Path
    ) -> None:
        """A Mapping with unstable iteration order must not cross-pair.

        The writers pair content to filenames positionally, so re-iterating
        the caller's Mapping would write one entry's bytes under another
        entry's name.
        """

        class ShufflingMapping(Mapping):
            def __init__(self, data: dict[str, bytes]) -> None:
                self._data = data
                self._calls = 0

            def __getitem__(self, key: str) -> bytes:
                return self._data[key]

            def __len__(self) -> int:
                return len(self._data)

            def __iter__(self):
                # Reverse the order on every subsequent traversal.
                self._calls += 1
                keys = list(self._data)
                return iter(keys if self._calls % 2 else list(reversed(keys)))

        payload = {"a.json": b"alpha", "b.json": b"beta", "c.json": b"gamma"}
        safety.write_files_no_follow(tmp_path / "out", ShufflingMapping(payload))

        for name, content in payload.items():
            assert (tmp_path / "out" / name).read_bytes() == content

    def test_revalidates_destinations_after_temporaries_exist(
        self, tmp_path: Path
    ) -> None:
        """The TOCTOU revalidation must actually fire.

        Planting the unsafe destination *before* the call only exercises the
        first preflight; this plants it during the temp-write phase, which is
        the window the held descriptor exists to defend.
        """
        output = tmp_path / "out"
        output.mkdir()
        external = tmp_path / "external"
        external.write_text("unchanged", encoding="utf-8")

        real_write_all = safety._write_all
        planted = False

        def plant_then_write(fd: int, content: bytes) -> None:
            nonlocal planted
            result = real_write_all(fd, content)
            if not planted:
                planted = True
                try:
                    (output / "b.json").symlink_to(external)
                except OSError:
                    pytest.skip("symlink creation unavailable")
            return result

        with (
            mock.patch.object(safety, "_write_all", plant_then_write),
            pytest.raises(ValueError, match="symlink|reparse"),
        ):
            safety.write_files_no_follow(output, {"a.json": b"alpha", "b.json": b"beta"})

        assert external.read_text(encoding="utf-8") == "unchanged"
        assert not (output / "a.json").exists()

    def test_revalidation_detects_a_swapped_destination(self, tmp_path: Path) -> None:
        """The identity comparison branch of the revalidation must fire.

        A destination swapped for a *different regular file* mid-write passes
        the symlink/regular-file preflight, so only the recorded
        (dev, ino, mode) comparison can catch it.
        """
        output = tmp_path / "out"
        output.mkdir()
        (output / "b.json").write_text("original", encoding="utf-8")

        real_write_all = safety._write_all
        swapped = False

        def swap_then_write(fd: int, content: bytes) -> None:
            nonlocal swapped
            result = real_write_all(fd, content)
            if not swapped:
                swapped = True
                replacement = tmp_path / "replacement"
                replacement.write_text("swapped", encoding="utf-8")
                replacement.replace(output / "b.json")
            return result

        with (
            mock.patch.object(safety, "_write_all", swap_then_write),
            pytest.raises(ValueError, match="changed during export preflight"),
        ):
            safety.write_files_no_follow(output, {"a.json": b"alpha", "b.json": b"beta"})

        assert not (output / "a.json").exists()


class TestWriteFilesNoFollowPortableBranch:
    """Force the non-POSIX fallback on a POSIX host.

    The branch is selected by `_secure_dir_fd_available()`, so on Linux and
    macOS CI it is never executed — it would otherwise ship to Windows
    adopters with no assertion behind it on any platform.
    """

    @pytest.fixture(autouse=True)
    def _force_portable(self):
        with mock.patch.object(safety, "_secure_dir_fd_available", lambda: False):
            yield

    def test_writes_a_flat_batch(self, tmp_path: Path) -> None:
        written = safety.write_files_no_follow(
            tmp_path / "out", {"a.json": b"alpha", "b.toml": b"beta"}
        )

        assert [path.name for path in written] == ["a.json", "b.toml"]
        assert (tmp_path / "out" / "a.json").read_bytes() == b"alpha"

    def test_refuses_symlinked_output_directory(self, tmp_path: Path) -> None:
        real = tmp_path / "real"
        real.mkdir()
        link = tmp_path / "link"
        try:
            link.symlink_to(real, target_is_directory=True)
        except OSError:
            pytest.skip("symlink creation unavailable")

        with pytest.raises(ValueError, match="symlink|reparse"):
            safety.write_files_no_follow(link, {"a.json": b"x"})

        assert list(real.iterdir()) == []

    def test_accepts_symlinked_ancestor(self, tmp_path: Path) -> None:
        real = tmp_path / "real"
        real.mkdir()
        link = tmp_path / "link"
        try:
            link.symlink_to(real, target_is_directory=True)
        except OSError:
            pytest.skip("symlink creation unavailable")

        safety.write_files_no_follow(link / "nested", {"a.json": b"alpha"})

        assert (real / "nested" / "a.json").read_bytes() == b"alpha"

    def test_refuses_symlinked_destination_without_writing(
        self, tmp_path: Path
    ) -> None:
        output = tmp_path / "out"
        output.mkdir()
        external = tmp_path / "external"
        external.write_text("unchanged", encoding="utf-8")
        try:
            (output / "b.json").symlink_to(external)
        except OSError:
            pytest.skip("symlink creation unavailable")

        with pytest.raises(ValueError, match="symlink|reparse"):
            safety.write_files_no_follow(
                output, {"a.json": b"alpha", "b.json": b"beta"}
            )

        assert external.read_text(encoding="utf-8") == "unchanged"
        assert not (output / "a.json").exists()
