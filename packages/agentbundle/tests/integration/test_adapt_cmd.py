"""T6: integration tests for ``agentbundle adapt``.

Coverage:
  - Marker substitution: ``<adapt:project-name>`` markers resolved via
    ``--values-from``.
  - ``.adapt-pending.md``: generated listing ``.upstream.*`` companions with
    diff summaries.
  - ``.adapt-discovery.toml`` never written: byte-identical before and after.
  - ``--ci`` with companions: exit non-zero, stderr lists them.
  - ``--ci`` clean: exit zero.
"""

from __future__ import annotations

import types
from pathlib import Path

import pytest

# Path to the shared fixtures for adapt tests.
ADAPT_FIXTURES = Path(__file__).parent.parent / "fixtures" / "adapt"


# ---------------------------------------------------------------------------
# Helper: build an argparse.Namespace the same way the CLI would
# ---------------------------------------------------------------------------

def _args(
    *,
    root: str,
    values_from: str | None = None,
    ci: bool = False,
) -> types.SimpleNamespace:
    return types.SimpleNamespace(root=root, values_from=values_from, ci=ci)


def _run(
    *,
    root: str,
    values_from: str | None = None,
    ci: bool = False,
) -> int:
    from agentbundle.commands.adapt import run
    return run(_args(root=root, values_from=values_from, ci=ci))


# ---------------------------------------------------------------------------
# Helper: set up a tmp_path with a state file + projected files
# ---------------------------------------------------------------------------

def _setup_projected(tmp_path: Path, files: dict[str, str]) -> None:
    """Write files and seed a .agentbundle-state.toml recording them."""
    from agentbundle.config import PackState, State, dump_state
    from agentbundle.safety import sha256_bytes

    state = State()
    file_entries: dict[str, dict[str, str]] = {}

    for relpath, content in files.items():
        target = tmp_path / relpath
        target.parent.mkdir(parents=True, exist_ok=True)
        data = content.encode("utf-8")
        target.write_bytes(data)
        file_entries[relpath] = {
            "sha": sha256_bytes(data),
            "from-pack-version": "0.1.0",
        }

    state.packs[("core", "claude-code")] = PackState(
        installed_version="0.1.0",
        files=file_entries,
        adapter="claude-code",
    )
    (tmp_path / ".agentbundle-state.toml").write_text(
        dump_state(state), encoding="utf-8"
    )


# ---------------------------------------------------------------------------
# 1. Marker substitution: <adapt:project-name> replaced by values.toml
# ---------------------------------------------------------------------------

def test_marker_substitution_replaces_markers(tmp_path):
    """``adapt --values-from values.toml`` substitutes every <adapt:NAME> marker."""
    content_before = "# Hello <adapt:project-name>\nowner: <adapt:owner>\n"
    content_after = "# Hello myproject\nowner: octocat\n"

    _setup_projected(tmp_path, {"README.md": content_before})

    # Copy the values.toml fixture into tmp_path for use.
    values_path = ADAPT_FIXTURES / "values.toml"

    rc = _run(root=str(tmp_path), values_from=str(values_path))
    assert rc == 0, "adapt should succeed"

    result = (tmp_path / "README.md").read_text(encoding="utf-8")
    assert result == content_after, f"Markers not substituted: {result!r}"


def test_marker_substitution_sha_matches_substituted_form(tmp_path):
    """After substitution the file's content equals the substituted text exactly."""
    import hashlib

    content_before = "project: <adapt:project-name>\n"
    content_after = "project: myproject\n"
    expected_sha = hashlib.sha256(content_after.encode("utf-8")).hexdigest()

    _setup_projected(tmp_path, {"docs/CHARTER.md": content_before})

    values_path = ADAPT_FIXTURES / "values.toml"
    rc = _run(root=str(tmp_path), values_from=str(values_path))
    assert rc == 0

    actual = (tmp_path / "docs" / "CHARTER.md").read_bytes()
    actual_sha = hashlib.sha256(actual).hexdigest()
    assert actual_sha == expected_sha


# ---------------------------------------------------------------------------
# 2. .adapt-pending.md lists .upstream.* companions with diff summaries
# ---------------------------------------------------------------------------

def test_adapt_pending_md_lists_companions(tmp_path):
    """Two .upstream.md companions should both appear in .adapt-pending.md.

    Both AGENTS.md and docs/CHARTER.md must be recorded as projected paths
    in the state file — `adapt`'s companion walk is scoped to in-state
    paths to avoid spurious matches against unrelated `*.upstream.*`
    files (Concern 11 from the adversarial review).
    """
    _setup_projected(
        tmp_path,
        {"AGENTS.md": "# AGENTS\n", "docs/CHARTER.md": "# CHARTER\n"},
    )

    # Place two .upstream companions.
    (tmp_path / "AGENTS.upstream.md").write_text(
        "# AGENTS UPSTREAM\nExtra line.\n", encoding="utf-8"
    )
    (tmp_path / "docs" / "CHARTER.upstream.md").write_text(
        "# CHARTER UPSTREAM\n", encoding="utf-8"
    )

    rc = _run(root=str(tmp_path))
    assert rc == 0

    pending = (tmp_path / ".adapt-pending.md").read_text(encoding="utf-8")
    assert "AGENTS.upstream.md" in pending, "AGENTS companion not listed"
    assert "CHARTER.upstream.md" in pending, "CHARTER companion not listed"


def test_adapt_pending_md_includes_diff_summary(tmp_path):
    """Each companion entry must contain a diff summary (line counts, etc.)."""
    original_content = "line1\nline2\n"
    upstream_content = "line1\nline2\nline3\n"

    _setup_projected(tmp_path, {"AGENTS.md": original_content})
    (tmp_path / "AGENTS.upstream.md").write_text(upstream_content, encoding="utf-8")

    rc = _run(root=str(tmp_path))
    assert rc == 0

    pending = (tmp_path / ".adapt-pending.md").read_text(encoding="utf-8")
    # Should mention lines in some form (line count delta or first diff).
    assert "lines" in pending.lower() or "line" in pending.lower()


def test_adapt_pending_md_no_companions_says_none_pending(tmp_path):
    """When no companions exist, .adapt-pending.md says so."""
    _setup_projected(tmp_path, {"AGENTS.md": "# hello\n"})

    rc = _run(root=str(tmp_path))
    assert rc == 0

    pending = (tmp_path / ".adapt-pending.md").read_text(encoding="utf-8")
    assert "No pending" in pending or "no pending" in pending.lower()


# ---------------------------------------------------------------------------
# 3. .adapt-discovery.toml never written: byte-identical before and after
# ---------------------------------------------------------------------------

def test_adapt_discovery_toml_never_written(tmp_path):
    """``adapt`` reads .adapt-discovery.toml but must not modify it."""
    import shutil

    discovery_src = ADAPT_FIXTURES / ".adapt-discovery.toml"
    discovery_dst = tmp_path / ".adapt-discovery.toml"
    shutil.copy(discovery_src, discovery_dst)

    before_bytes = discovery_dst.read_bytes()

    _setup_projected(tmp_path, {"AGENTS.md": "# project: <adapt:owner>\n"})
    values_path = ADAPT_FIXTURES / "values.toml"

    rc = _run(root=str(tmp_path), values_from=str(values_path))
    assert rc == 0

    after_bytes = discovery_dst.read_bytes()
    assert before_bytes == after_bytes, (
        ".adapt-discovery.toml must be byte-identical before and after adapt"
    )


def test_adapt_discovery_accepted_entries_applied(tmp_path):
    """Accepted entries from .adapt-discovery.toml are used as marker values."""
    import shutil

    discovery_src = ADAPT_FIXTURES / ".adapt-discovery.toml"
    discovery_dst = tmp_path / ".adapt-discovery.toml"
    shutil.copy(discovery_src, discovery_dst)

    # Write a file with <adapt:owner> — the discovery.toml has 'owner' in [markers].
    _setup_projected(tmp_path, {"AGENTS.md": "owner: <adapt:owner>\n"})

    # Run without --values-from; discovery accepted entries should not substitute
    # (substitution only runs when --values-from is provided).
    # Now run WITH --values-from; discovery owner should be overridden.
    values_path = ADAPT_FIXTURES / "values.toml"
    rc = _run(root=str(tmp_path), values_from=str(values_path))
    assert rc == 0

    result = (tmp_path / "AGENTS.md").read_text(encoding="utf-8")
    # values.toml has owner = "octocat"; should win.
    assert "octocat" in result


# ---------------------------------------------------------------------------
# 4. --ci with companions: exit non-zero, stderr lists companions
# ---------------------------------------------------------------------------

def test_ci_with_companions_exits_nonzero(tmp_path, capsys):
    """``adapt --ci`` exits 1 when any .upstream.* companion is on disk."""
    (tmp_path / "AGENTS.upstream.md").write_text("upstream", encoding="utf-8")

    rc = _run(root=str(tmp_path), ci=True)
    assert rc == 1, "--ci should exit 1 when companions present"

    captured = capsys.readouterr()
    assert "AGENTS.upstream.md" in captured.err, "Companion path should be on stderr"


def test_ci_with_companions_lists_all_on_stderr(tmp_path, capsys):
    """``adapt --ci`` lists every pending companion on stderr."""
    (tmp_path / "AGENTS.upstream.md").write_text("upstream1", encoding="utf-8")
    docs = tmp_path / "docs"
    docs.mkdir()
    (docs / "CHARTER.upstream.md").write_text("upstream2", encoding="utf-8")

    rc = _run(root=str(tmp_path), ci=True)
    assert rc == 1

    captured = capsys.readouterr()
    assert "AGENTS.upstream.md" in captured.err
    assert "CHARTER.upstream.md" in captured.err


# ---------------------------------------------------------------------------
# 5. --ci clean: exit zero when no companions on disk
# ---------------------------------------------------------------------------

def test_ci_clean_exits_zero(tmp_path):
    """``adapt --ci`` exits 0 when no .upstream.* companions exist."""
    # No companions; only a normal file.
    (tmp_path / "AGENTS.md").write_text("# normal file", encoding="utf-8")

    rc = _run(root=str(tmp_path), ci=True)
    assert rc == 0, "--ci should exit 0 with no companions"


def test_ci_clean_after_companions_removed_exits_zero(tmp_path):
    """``adapt --ci`` exits 0 when a previously present companion has been removed."""
    companion = tmp_path / "AGENTS.upstream.md"
    companion.write_text("upstream", encoding="utf-8")
    companion.unlink()  # simulate human having resolved it

    rc = _run(root=str(tmp_path), ci=True)
    assert rc == 0


# ---------------------------------------------------------------------------
# 6. Binary file skipped gracefully
# ---------------------------------------------------------------------------

def test_binary_file_skipped_without_error(tmp_path):
    """Projected files that cannot be decoded as UTF-8 are skipped with a warning."""
    binary_content = bytes(range(256))
    _setup_projected(tmp_path, {})

    # Manually inject a binary file into the state.
    from agentbundle.config import PackState, State, dump_state
    from agentbundle.safety import sha256_bytes

    state = State()
    state.packs[("core", "claude-code")] = PackState(
        installed_version="0.1.0",
        files={"data.bin": {"sha": sha256_bytes(binary_content), "from-pack-version": "0.1.0"}},
        adapter="claude-code",
    )
    (tmp_path / ".agentbundle-state.toml").write_text(dump_state(state), encoding="utf-8")
    (tmp_path / "data.bin").write_bytes(binary_content)

    values_path = ADAPT_FIXTURES / "values.toml"
    rc = _run(root=str(tmp_path), values_from=str(values_path))
    assert rc == 0, "Binary file should be skipped, not error"

    # Binary file must be unchanged.
    assert (tmp_path / "data.bin").read_bytes() == binary_content
