"""The release checker's case table, from the plan's T7.

Every refusing row is directed at one wrong implementation. A single vague
"wrong version" case would be satisfied by a checker that ignores the major
component, by one that ignores the minor, and by one that accepts any patch
inequality -- so it rejects none of them.

Two rows carry decoys: the expected version appears in a *later* changelog
entry, and a valid Highlights bullet appears in a *later* entry. Without those,
a checker that searches the whole file passes while checking nothing about the
topmost entry.
"""

from __future__ import annotations

import importlib.util
import json
import subprocess
from pathlib import Path

import pytest

_SPEC = importlib.util.spec_from_file_location(
    "check_core_release", Path(__file__).resolve().parent / "check-core-release.py"
)
ccr = importlib.util.module_from_spec(_SPEC)
_SPEC.loader.exec_module(ccr)

BASE = "1.4.7"


def _changelog(*entries: tuple[str, bool]) -> str:
    """Entries top-down as (version, has_bullet)."""
    out = ["# Changelog\n"]
    for version, bullet in entries:
        out.append(f"## [core][{version}] — 2026-09-19\n")
        out.append("### Highlights\n")
        out.append("- A consumer-visible change.\n" if bullet else "\n")
    return "\n".join(out)


def _projection(root: Path, body: str) -> None:
    """Install a stub `tools/build-site.py` with the given function body."""
    (root / "tools").mkdir(parents=True, exist_ok=True)
    (root / "tools" / "build-site.py").write_text(body, encoding="utf-8")


def _faithful(version: str, bullets: tuple[str, ...] = ("A consumer-visible change.",)) -> str:
    highlights = ", ".join(f"{{'source': {b!r}}}" for b in bullets)
    return (
        "def project_now_highlights(text):\n"
        "    return {'schemaVersion': 1, 'groups': [{\n"
        f"        'packages': [{{'name': 'core', 'version': {version!r}}}],\n"
        f"        'highlights': [{highlights}],\n"
        "    }]}\n"
    )


def _repo(tmp_path: Path, *, version: str, plugin: str | None = None,
          changelog: str | None = None) -> Path:
    root = tmp_path / "repo"
    (root / "packs/core/.claude-plugin").mkdir(parents=True)
    (root / "docs/product").mkdir(parents=True)
    (root / "packs/core/pack.toml").write_text(
        f'[pack]\nname = "core"\nversion = "{BASE}"\n', encoding="utf-8")
    subprocess.run(["git", "init", "-q"], cwd=root, check=True)
    subprocess.run(["git", "add", "-A"], cwd=root, check=True)
    subprocess.run(
        ["git", "-c", "user.email=t@e", "-c", "user.name=t",
         "commit", "-qm", "base"], cwd=root, check=True)

    (root / "packs/core/pack.toml").write_text(
        f'[pack]\nname = "core"\nversion = "{version}"\n', encoding="utf-8")
    (root / "packs/core/.claude-plugin/plugin.json").write_text(
        json.dumps({"name": "core", "version": plugin or version}), encoding="utf-8")
    (root / "docs/product/changelog.md").write_text(
        changelog if changelog is not None else _changelog((version, True)),
        encoding="utf-8")
    _projection(root, _faithful(version))
    return root


def _refuses(root: Path, base: str = "HEAD") -> str:
    """Drive the executable, not just `check()`.

    Calling `check()` alone leaves the exit code and the operator-facing message
    untested, so both can regress while the suite stays green. Returns stderr so
    a caller can assert the named reason.
    """
    import contextlib
    import io

    err = io.StringIO()
    with contextlib.redirect_stderr(err):
        code = ccr.main(["--base", base, "--root", str(root)])
    assert code == 1, f"expected exit 1, got {code}"
    text = err.getvalue()
    assert text.strip(), "refused without telling the operator why"
    return text


def test_a_valid_patch_successor_is_accepted(tmp_path):
    assert ccr.check(_repo(tmp_path, version="1.4.8"), "HEAD") == []


@pytest.mark.parametrize("version", ["2.4.8", "1.5.8", "1.4.7", "1.4.6", "1.4.9"])
def test_a_version_that_is_not_the_patch_successor_is_refused(tmp_path, version):
    """Major, minor, unchanged, one lower, and overshoot -- each its own case."""
    _refuses(_repo(tmp_path, version=version))


def test_a_wrong_pack_toml_alone_is_refused(tmp_path):
    root = _repo(tmp_path, version="1.4.9", plugin="1.4.8",
                 changelog=_changelog(("1.4.8", True)))
    _refuses(root)


def test_a_wrong_plugin_json_alone_is_refused(tmp_path):
    root = _repo(tmp_path, version="1.4.8", plugin="1.4.9")
    assert "1.4.9" in _refuses(root)


def test_a_wrong_topmost_entry_is_refused_even_when_a_later_entry_matches(tmp_path):
    """Decoy: the expected version is present, but not at the top."""
    root = _repo(tmp_path, version="1.4.8",
                 changelog=_changelog(("1.4.7", True), ("1.4.8", True)))
    assert "topmost" in _refuses(root)


def test_an_unbulleted_target_entry_is_refused_even_when_a_later_entry_has_one(tmp_path):
    """Decoy: a valid bullet exists in the file, but not in the target entry."""
    root = _repo(tmp_path, version="1.4.8",
                 changelog=_changelog(("1.4.8", False), ("1.4.7", True)))
    assert "Highlights" in _refuses(root)


def test_an_unresolvable_base_is_refused(tmp_path):
    assert "does not resolve" in _refuses(_repo(tmp_path, version="1.4.8"), "not-a-commit")


# ------------------------------------------------------------------- AC-0016

# AC-0016's live-tree comparison lives in the checker, which runs once at
# delivery. A standing test asserting that the CURRENT core version carries
# Highlights would fail on a future consumer-neutral release that legitimately
# has none -- a delivery-time criterion must not become a permanent constraint.


def test_a_projection_that_drops_the_entry_is_refused(tmp_path):
    """Fixture-based: the payload must carry this release's bullets."""
    root = _repo(tmp_path, version="1.4.8")
    _projection(root, "def project_now_highlights(text):\n"
                      "    return {'schemaVersion': 1, 'groups': []}\n")
    _refuses(root)


def test_a_projection_that_alters_the_bullets_is_refused(tmp_path):
    root = _repo(tmp_path, version="1.4.8")
    _projection(root, _faithful("1.4.8", ("Something the changelog never said.",)))
    reasons = ccr.check(root, "HEAD")
    assert reasons and "differ from" in reasons[0]


def test_a_faithful_projection_is_accepted(tmp_path):
    assert ccr.check(_repo(tmp_path, version="1.4.8"), "HEAD") == []


# ------------------------------------- the executable interface, not just check()


def test_the_cli_reports_its_exit_code_and_names_the_reason(tmp_path, capsys):
    """Driving `check()` alone leaves exit codes and operator messages untested."""
    root = _repo(tmp_path, version="1.4.9", changelog=_changelog(("1.4.9", True)))
    code = ccr.main(["--base", "HEAD", "--root", str(root)])
    assert code == 1
    assert "expected the patch successor" in capsys.readouterr().err


def test_the_cli_exits_zero_and_says_so_when_consistent(tmp_path, capsys):
    root = _repo(tmp_path, version="1.4.8")
    assert ccr.main(["--base", "HEAD", "--root", str(root)]) == 0
    assert "consistent" in capsys.readouterr().out


def test_a_missing_manifest_is_a_named_refusal_not_a_traceback(tmp_path):
    root = _repo(tmp_path, version="1.4.8")
    (root / "packs/core/.claude-plugin/plugin.json").unlink()
    assert "cannot read" in _refuses(root)


def test_a_malformed_manifest_is_a_named_refusal(tmp_path):
    root = _repo(tmp_path, version="1.4.8")
    (root / "packs/core/.claude-plugin/plugin.json").write_text("{not json", encoding="utf-8")
    assert "not valid JSON" in _refuses(root)


def test_a_missing_changelog_is_a_named_refusal(tmp_path):
    root = _repo(tmp_path, version="1.4.8")
    (root / "docs/product/changelog.md").unlink()
    assert "cannot read" in _refuses(root)


def test_a_changelog_with_no_core_entry_is_a_named_refusal(tmp_path):
    root = _repo(tmp_path, version="1.4.8", changelog="# Changelog\n\nNothing yet.\n")
    assert "no core release entry" in _refuses(root)


def test_a_broken_projection_is_a_named_refusal(tmp_path):
    root = _repo(tmp_path, version="1.4.8")
    _projection(root, "raise RuntimeError('projection exploded')\n")
    assert "could not be built" in _refuses(root)


def test_a_non_utf8_manifest_is_a_named_refusal(tmp_path):
    root = _repo(tmp_path, version="1.4.8")
    (root / "packs/core/.claude-plugin/plugin.json").write_bytes(b'{"version": "\xff\xfe"}')
    assert "UTF-8" in _refuses(root)


def test_a_non_utf8_pack_toml_is_a_named_refusal(tmp_path):
    root = _repo(tmp_path, version="1.4.8")
    (root / "packs/core/pack.toml").write_bytes(b'[pack]\nversion = "\xff\xfe"\n')
    assert "UTF-8" in _refuses(root)


def test_a_malformed_payload_shape_is_a_named_refusal(tmp_path):
    """The traversal sat outside the refusal boundary and raised instead."""
    root = _repo(tmp_path, version="1.4.8")
    _projection(root, "def project_now_highlights(text):\n"
                      "    return {'schemaVersion': 1, 'groups': [{'packages': None}]}\n")
    assert "unexpected shape" in _refuses(root)


def test_an_unexpected_failure_fails_closed(tmp_path):
    """A delivery check must never pass because something threw."""
    root = _repo(tmp_path, version="1.4.8")
    (root / "packs/core/pack.toml").unlink()
    (root / "packs/core/pack.toml").mkdir()          # a directory where a file is expected
    assert _refuses(root)


def test_a_release_heading_inside_a_fence_is_not_a_release(tmp_path):
    """Sample changelog markup must not be read as this repository's release."""
    changelog = (
        "# Changelog\n\n"
        "Example of the shape an entry takes:\n\n"
        "```markdown\n"
        "## [core][9.9.9] — 2026-01-01\n\n"
        "### Highlights\n\n"
        "- A sample bullet.\n"
        "```\n\n"
        "## [core][1.4.8] — 2026-09-18\n\n"
        "### Highlights\n\n"
        "- A consumer-visible change.\n"
    )
    assert ccr.check(_repo(tmp_path, version="1.4.8", changelog=changelog), "HEAD") == []
