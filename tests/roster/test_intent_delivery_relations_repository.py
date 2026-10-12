"""Repository-level checks for the intent-delivery resolver and its copies.

Pack tests stay inside their own pack, so the checks that need the in-tree
`agentbundle` package or the whole `packs/` tree live here: the confinement
helper's parity with its canonical source, a real repo-scope install, and the
real adapter-root projection.
"""

from __future__ import annotations

import importlib.util
import json
import os
import subprocess
import sys
from pathlib import Path
from types import ModuleType

import pytest

REPO_ROOT = Path(__file__).resolve().parents[2]
CORE = REPO_ROOT / "packs" / "core"
AGENTBUNDLE_PKG = REPO_ROOT / "packages" / "agentbundle"
BINS = CORE / ".apm" / "adapter-root-bins"
SOURCE = BINS / "intent_delivery_relations.py"
HELPER = BINS / "_file_safety.py"
FILE_SAFETY_CANONICAL = (
    AGENTBUNDLE_PKG / "agentbundle" / "catalogue_tooling" / "file_safety.py"
)


def _load(name: str, path: Path) -> ModuleType:
    """Load a pack test module so its fixture helpers can be reused."""
    spec = importlib.util.spec_from_file_location(name, path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


_copies = _load(
    "_roster_resolver_copies",
    CORE / "tests" / "pack" / "test_intent_delivery_relations_copies.py",
)
_integration = _load(
    "_roster_resolver_integration",
    CORE / "tests" / "integration" / "test_intent_delivery_traceability.py",
)


# STUB: AC-0014
def test_ac0014_each_consumer_skill_ships_the_resolver() -> None:
    for skill in ("close-work", "work-loop", "navigate-intents"):
        scripts = CORE / ".apm" / "skills" / skill / "scripts"
        for source in (SOURCE, HELPER):
            copy = scripts / source.name
            assert copy.is_file(), f"{skill} ships no {source.name}"
            assert copy.read_bytes() == source.read_bytes()


def test_vi1501_file_safety_is_byte_identical_to_canonical() -> None:
    """_file_safety.py is byte-identical to agentbundle.catalogue_tooling.file_safety."""
    assert FILE_SAFETY_CANONICAL.is_file(), "canonical file_safety.py not found"
    assert HELPER.read_bytes() == FILE_SAFETY_CANONICAL.read_bytes()


# ── VI-1903: real agentbundle install delivers resolver copies ─────────────────


def _make_fixture(root: Path) -> None:
    """Write a minimal fixture: one feature intent, one spec, one brief anchor."""
    (root / "docs" / "product" / "intents").mkdir(parents=True, exist_ok=True)
    (root / "docs" / "product" / "briefs").mkdir(parents=True, exist_ok=True)
    (root / "docs" / "specs" / "vi1903-spec").mkdir(parents=True, exist_ok=True)
    (root / "docs" / "product" / "intents" / "vi1903-feat.md").write_text(
        "# VI-1903 Feature\n\n"
        "- **Slug:** `vi1903-feat`\n"
        "- **Level:** feature\n"
        "- **Status:** Accepted\n"
        "- **Decomposed:** 2026-10-06 spec\n",
        encoding="utf-8",
    )
    (root / "docs" / "specs" / "vi1903-spec" / "spec.md").write_text(
        "# Spec\n\n"
        "- **Status:** Shipped\n"
        "- **Discovery:** `intent:vi1903-feat`\n",
        encoding="utf-8",
    )
    (root / "docs" / "product" / "briefs" / "anchor.md").write_text(
        "# Brief\n\n- **Slug:** `anchor`\n",
        encoding="utf-8",
    )


def test_vi1903_real_agentbundle_install_delivers_resolver_copies(
    tmp_path: Path,
) -> None:
    """VI-1903 — A real ``agentbundle install --pack core --scope repo`` places
    the resolver and helper beside each consumer's installed scripts.  Invoking
    either installed copy with ``sys.executable -I -S`` returns JSON byte-
    identical to ``serialize(resolve_repository(fixture))``.  The installed
    lint-traceability exits 0 with no ``delivery-resolver-unavailable`` on a
    fixture with a brief anchor.

    AC-0015.
    """
    # Initialise a clean git repo in tmp_path.
    subprocess.run(["git", "init", "-q", str(tmp_path)], check=True)

    # Run agentbundle install with the in-tree package on sys.path.
    env = dict(os.environ)
    pythonpath = str(AGENTBUNDLE_PKG)
    existing = env.get("PYTHONPATH", "")
    env["PYTHONPATH"] = f"{pythonpath}:{existing}" if existing else pythonpath

    result = subprocess.run(
        [
            sys.executable, "-m", "agentbundle", "install",
            str(REPO_ROOT),
            "--pack", "core",
            "--scope", "repo",
            "--adapter", "claude-code",
            "--yes",
        ],
        cwd=str(tmp_path),
        capture_output=True,
        env=env,
        timeout=120,
    )
    assert result.returncode == 0, (
        f"agentbundle install failed: {result.stderr.decode('utf-8', errors='replace')}"
    )

    # Confirm installed copies exist for all skills.
    installed_cw = tmp_path / ".claude" / "skills" / "close-work" / "scripts"
    installed_wl = tmp_path / ".claude" / "skills" / "work-loop" / "scripts"
    installed_ni = tmp_path / ".claude" / "skills" / "navigate-intents" / "scripts"
    for installed_scripts in (installed_cw, installed_wl, installed_ni):
        resolver_copy = installed_scripts / "intent_delivery_relations.py"
        helper_copy = installed_scripts / "_file_safety.py"
        assert resolver_copy.is_file(), (
            f"installer did not place resolver at {resolver_copy}"
        )
        assert helper_copy.is_file(), (
            f"installer did not place helper at {helper_copy}: "
            f"underscore files are filtered — report blocked"
        )

    # Build a fixture inside tmp_path and get the expected snapshot bytes.
    _make_fixture(tmp_path)
    resolver_mod = _copies._load_resolver("vi1903")
    expected_json = resolver_mod.serialize(resolver_mod.resolve_repository(tmp_path))

    # Invoke each installed copy under -I -S (no agentbundle importable).
    for label, installed_scripts in (
        ("close-work", installed_cw),
        ("work-loop", installed_wl),
        ("navigate-intents", installed_ni),
    ):
        proc = subprocess.run(
            [
                sys.executable, "-I", "-S",
                str(installed_scripts / "intent_delivery_relations.py"),
                "--root", str(tmp_path),
            ],
            capture_output=True,
            timeout=60,
        )
        assert proc.returncode == 0, (
            f"{label}: installed copy must exit 0; "
            f"stderr={proc.stderr.decode('utf-8', errors='replace')}"
        )
        actual_json = proc.stdout.decode("utf-8")
        assert actual_json == expected_json, (
            f"{label}: installed copy stdout must be byte-identical to source snapshot"
        )

    # Run the installed lint-traceability on the fixture (has brief anchor).
    installed_lint = installed_wl / "lint-traceability.py"
    assert installed_lint.is_file(), f"lint-traceability.py not installed at {installed_lint}"
    lint_proc = subprocess.run(
        [sys.executable, str(installed_lint), "--root", str(tmp_path)],
        capture_output=True,
        timeout=60,
    )
    assert lint_proc.returncode == 0, (
        f"installed lint must exit 0; "
        f"stderr={lint_proc.stderr.decode('utf-8', errors='replace')}"
    )
    combined = (
        lint_proc.stdout.decode("utf-8", errors="replace")
        + lint_proc.stderr.decode("utf-8", errors="replace")
    )
    assert "delivery-resolver-unavailable" not in combined, (
        "installed lint must not emit delivery-resolver-unavailable when "
        "resolver copy is present beside it"
    )


def test_vi1802_real_projection_installs_and_matches_source(tmp_path: Path) -> None:
    """VI-1802 — apply_projection delivers the resolver to .agentbundle/bin/;
    the installed binary invoked with ``sys.executable -I -S`` (isolated mode,
    no site-packages — so ``agentbundle`` is not importable) produces JSON
    byte-identical to ``serialize(resolve_repository(fixture))``.

    Proves the projected resolver is self-contained via its co-located
    ``_file_safety.py`` helper (decision 1) and does not silently import
    ``agentbundle`` from the environment.

    Also asserts a symlinked corpus entry forces exit 1 (incomplete snapshot).
    """
    from agentbundle.build.adapter_root_bins import apply_projection  # type: ignore[import]

    # Minimal fixture repository.
    _integration._make_intent(tmp_path, "feat-proj", decomposed="2026-10-05 spec")
    _integration._make_spec(tmp_path, "proj-spec", discovery="intent:feat-proj", status="Shipped")
    _integration._make_brief(tmp_path, "anchor-brief")

    # Project adapter-root-bins from the real packs tree to tmp_path.
    packs_dir = REPO_ROOT / "packs"
    apply_projection(tmp_path, packs_dir)

    projected = tmp_path / ".agentbundle" / "bin" / "intent_delivery_relations.py"
    assert projected.exists(), f"VI-1802: projected resolver not found at {projected}"
    helper = tmp_path / ".agentbundle" / "bin" / "_file_safety.py"
    assert helper.exists(), f"VI-1802: projected _file_safety.py not found at {helper}"

    # Invoke with -I -S: isolated (no user site-packages, no PYTHONPATH) and
    # no site module — agentbundle must not be importable.
    result = subprocess.run(
        [sys.executable, "-I", "-S", str(projected), "--root", str(tmp_path)],
        capture_output=True,
        timeout=60,
        cwd=str(tmp_path),
    )
    assert result.returncode == 0, (
        f"VI-1802: projected CLI must exit 0 for a complete snapshot; "
        f"got {result.returncode}\n"
        f"stderr={result.stderr.decode('utf-8', errors='replace')}"
    )

    # Byte-identical comparison with in-process serialization.
    in_process_snap = _integration._resolver_mod.resolve_repository(tmp_path)
    expected_json = _integration._resolver_mod.serialize(in_process_snap)
    actual_json = result.stdout.decode("utf-8")
    assert actual_json == expected_json, (
        "VI-1802: projected CLI stdout must be byte-identical to "
        "serialize(resolve_repository(fixture))"
    )

    # Symlinked corpus entry forces exit 1 (incomplete snapshot).
    intents_dir = tmp_path / "docs" / "product" / "intents"
    real_file = tmp_path / "real_intent_for_symlink.md"
    real_file.write_text(
        "# Real\n\n- **Slug:** `real-sl`\n- **Level:** feature\n", encoding="utf-8"
    )
    try:
        (intents_dir / "symlinked.md").symlink_to(real_file)
    except OSError:
        pytest.skip("VI-1802: symlinks unavailable on this platform")

    result2 = subprocess.run(
        [sys.executable, "-I", "-S", str(projected), "--root", str(tmp_path)],
        capture_output=True,
        timeout=60,
        cwd=str(tmp_path),
    )
    assert result2.returncode == 1, (
        f"VI-1802: projected CLI must exit 1 for incomplete snapshot; "
        f"got {result2.returncode}"
    )
    snap2 = json.loads(result2.stdout.decode("utf-8"))
    assert snap2["complete"] is False, (
        "VI-1802: snapshot must be incomplete when corpus contains a symlink"
    )
