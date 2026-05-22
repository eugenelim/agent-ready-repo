"""T1b: Tier classification + path-jail + content-hash helpers."""

from __future__ import annotations

import pytest
from pathlib import Path

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
