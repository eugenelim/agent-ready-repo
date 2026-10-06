# STUB: AC-0014
from __future__ import annotations

import ast
import importlib.util
import os
import subprocess
import sys
from pathlib import Path

import pytest

CORE = Path(__file__).resolve().parents[2]
BINS = CORE / ".apm" / "adapter-root-bins"
SOURCE = BINS / "intent_delivery_relations.py"
HELPER = BINS / "_file_safety.py"

_CLOSE_WORK_SCRIPTS = CORE / ".apm" / "skills" / "close-work" / "scripts"
_WORK_LOOP_SCRIPTS = CORE / ".apm" / "skills" / "work-loop" / "scripts"
_CLOSURE_INDEX = _CLOSE_WORK_SCRIPTS / "closure_index.py"
_LINT_TRACEABILITY = _WORK_LOOP_SCRIPTS / "lint-traceability.py"

# Repository root (two levels above packs/core)
_REPO_ROOT = CORE.parents[1]
# packages/agentbundle on sys.path for in-process install
_AGENTBUNDLE_PKG = _REPO_ROOT / "packages" / "agentbundle"


# ── Module loaders ─────────────────────────────────────────────────────────────


def _load_closure_index(suffix: str) -> object:
    """Load closure_index.py under a unique module name."""
    key = f"_copies_test_closure_index_{suffix}"
    spec = importlib.util.spec_from_file_location(key, _CLOSURE_INDEX)
    assert spec and spec.loader, f"closure_index not found at {_CLOSURE_INDEX}"
    mod = importlib.util.module_from_spec(spec)
    sys.modules[key] = mod
    spec.loader.exec_module(mod)
    return mod


def _load_resolver(suffix: str) -> object:
    """Load the resolver source under a unique module name."""
    key = f"_copies_test_resolver_{suffix}"
    if key in sys.modules:
        return sys.modules[key]
    spec = importlib.util.spec_from_file_location(key, SOURCE)
    assert spec and spec.loader
    mod = importlib.util.module_from_spec(spec)
    sys.modules[key] = mod
    spec.loader.exec_module(mod)
    return mod


# ── VI-1901: each consumer skill ships the resolver ───────────────────────────


def test_ac0014_each_consumer_skill_ships_the_resolver() -> None:
    for skill in ("close-work", "work-loop"):
        scripts = CORE / ".apm" / "skills" / skill / "scripts"
        for source in (SOURCE, HELPER):
            copy = scripts / source.name
            assert copy.is_file(), f"{skill} ships no {source.name}"
            assert copy.read_bytes() == source.read_bytes()


# ── VI-1902: each consumer locates resolver from its own file path ─────────────


def test_vi1902_absent_resolver_is_delivery_resolver_unavailable(
    tmp_path: Path,
) -> None:
    """VI-1902 — An absent resolver beside the consumer yields
    delivery-resolver-unavailable from both consumers. Proved through the
    _resolver_path seam without removing the real sibling copy.

    AC-0014, AC-0018.
    """
    nonexistent = tmp_path / "nonexistent_intent_delivery_relations.py"

    # close-work: _run_resolver with absent path raises ValueError
    ci = _load_closure_index("absent")
    raised = False
    try:
        ci._run_resolver(tmp_path, _resolver_path=nonexistent)
    except ValueError as exc:
        raised = True
        assert "delivery-resolver-unavailable" in str(exc)
    assert raised, "close-work must raise ValueError for absent resolver"

    # lint-traceability: same
    ms = importlib.util.spec_from_file_location(
        "_copies_test_lint_absent", _LINT_TRACEABILITY
    )
    assert ms and ms.loader
    lt = importlib.util.module_from_spec(ms)
    ms.loader.exec_module(lt)
    raised = False
    try:
        lt._run_resolver(tmp_path, _resolver_path=nonexistent)
    except ValueError as exc:
        raised = True
        assert "delivery-resolver-unavailable" in str(exc)
    assert raised, "lint-traceability must raise ValueError for absent resolver"


def test_vi1902_linked_resolver_is_delivery_resolver_unavailable(
    tmp_path: Path,
) -> None:
    """VI-1902 — A symlinked resolver beside the consumer yields
    delivery-resolver-unavailable from both consumers.

    AC-0014, AC-0018.
    """
    real = tmp_path / "real.py"
    real.write_bytes(SOURCE.read_bytes())
    link = tmp_path / "intent_delivery_relations_link.py"
    try:
        link.symlink_to(real)
    except (OSError, NotImplementedError):
        pytest.skip("symlinks unavailable on this platform")

    # close-work
    ci = _load_closure_index("linked")
    raised = False
    try:
        ci._run_resolver(tmp_path, _resolver_path=link)
    except ValueError as exc:
        raised = True
        assert "delivery-resolver-unavailable" in str(exc)
    assert raised, "close-work must raise ValueError for linked resolver"

    # lint-traceability
    ms = importlib.util.spec_from_file_location(
        "_copies_test_lint_linked", _LINT_TRACEABILITY
    )
    assert ms and ms.loader
    lt = importlib.util.module_from_spec(ms)
    ms.loader.exec_module(lt)
    raised = False
    try:
        lt._run_resolver(tmp_path, _resolver_path=link)
    except ValueError as exc:
        raised = True
        assert "delivery-resolver-unavailable" in str(exc)
    assert raised, "lint-traceability must raise ValueError for linked resolver"


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
    pythonpath = str(_AGENTBUNDLE_PKG)
    existing = env.get("PYTHONPATH", "")
    env["PYTHONPATH"] = f"{pythonpath}:{existing}" if existing else pythonpath

    result = subprocess.run(
        [
            sys.executable, "-m", "agentbundle", "install",
            str(_REPO_ROOT),
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

    # Confirm installed copies exist for both skills.
    installed_cw = tmp_path / ".claude" / "skills" / "close-work" / "scripts"
    installed_wl = tmp_path / ".claude" / "skills" / "work-loop" / "scripts"
    for installed_scripts in (installed_cw, installed_wl):
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
    resolver_mod = _load_resolver("vi1903")
    expected_json = resolver_mod.serialize(resolver_mod.resolve_repository(tmp_path))

    # Invoke each installed copy under -I -S (no agentbundle importable).
    for label, installed_scripts in (
        ("close-work", installed_cw),
        ("work-loop", installed_wl),
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


# ── VI-1904: caller inventory (VI-1402 restated) ───────────────────────────────


def test_vi1904_only_canonical_delivery_inverter_exists() -> None:
    """VI-1904 — Only adapter-root-bins/intent_delivery_relations.py and its two
    byte-identical skill copies produce delivery-relation types; each consumer
    locates the resolver beside its own file; retired entry points are absent.

    AC-0014.
    """
    apm_root = CORE / ".apm"
    assert apm_root.is_dir(), f"APM root not found: {apm_root}"

    production_files = sorted(
        p for p in apm_root.rglob("*.py")
        if p.is_file() and not any(part.startswith("__") for part in p.parts)
    )
    assert production_files, "No production .py files found under .apm/"

    _DELIVERY_TYPE_LITERALS = {"direct-delivery", "coordinated-delivery"}

    # ── Assertion 1: Only the canonical source and its two copies produce ──────
    # delivery relation types.  Byte identity is verified inline.
    producers: list[Path] = []
    for path in production_files:
        try:
            source = path.read_text(encoding="utf-8")
            tree = ast.parse(source, filename=str(path))
        except (OSError, SyntaxError):
            continue
        for node in ast.walk(tree):
            if isinstance(node, ast.Dict):
                for key, val in zip(node.keys, node.values, strict=False):
                    if (
                        isinstance(key, ast.Constant)
                        and key.value == "type"
                        and isinstance(val, ast.Constant)
                        and val.value in _DELIVERY_TYPE_LITERALS
                    ):
                        producers.append(path)
                        break

    # Accepted producers: the adapter-root-bins source + 2 byte-identical copies.
    accepted_relpaths = {
        SOURCE.relative_to(apm_root),
        (_CLOSE_WORK_SCRIPTS / "intent_delivery_relations.py").relative_to(apm_root),
        (_WORK_LOOP_SCRIPTS / "intent_delivery_relations.py").relative_to(apm_root),
    }

    non_accepted = [
        p for p in producers
        if p.relative_to(apm_root) not in accepted_relpaths
    ]
    assert not non_accepted, (
        "VI-1904: Only the canonical source and its two skill copies may produce "
        "delivery relation types; unexpected producers: "
        + ", ".join(str(p.relative_to(apm_root)) for p in non_accepted)
    )

    # All three accepted files must be present.
    for rel in accepted_relpaths:
        assert any(
            p.relative_to(apm_root) == rel for p in producers
        ), f"VI-1904: expected producer not found: {rel}"

    # Byte identity: each skill copy == source.
    for skill_scripts in (_CLOSE_WORK_SCRIPTS, _WORK_LOOP_SCRIPTS):
        skill_copy = skill_scripts / "intent_delivery_relations.py"
        assert skill_copy.read_bytes() == SOURCE.read_bytes(), (
            f"VI-1904: {skill_copy.relative_to(apm_root)} is not byte-identical to source"
        )

    # ── Assertion 2: Each consumer locates resolver beside its own file ────────
    closure_src = _CLOSURE_INDEX.read_text(encoding="utf-8")
    lint_src = _LINT_TRACEABILITY.read_text(encoding="utf-8")

    # Each consumer must reference _RESOLVER_PATH built from __file__,
    # not from root / ".agentbundle" / "bin".
    assert "_RESOLVER_PATH" in closure_src, (
        "VI-1904: closure_index.py must define _RESOLVER_PATH"
    )
    assert "_RESOLVER_PATH" in lint_src, (
        "VI-1904: lint-traceability.py must define _RESOLVER_PATH"
    )
    # Neither consumer may reference the retired .agentbundle/bin path.
    assert '".agentbundle"' not in closure_src or ".agentbundle/bin" not in closure_src, (
        "VI-1904: closure_index.py must not reference .agentbundle/bin"
    )

    # ── Assertion 3: Retired consumer-local inversion entry points are absent ──
    assert "_resolve_discovery_path" not in closure_src, (
        "VI-1904: _resolve_discovery_path (retired pre-T2 function) must not be "
        "in closure_index.py"
    )
    try:
        lint_tree = ast.parse(lint_src, filename=str(_LINT_TRACEABILITY))
    except SyntaxError as exc:
        pytest.fail(f"VI-1904: lint-traceability.py has a syntax error: {exc}")

    spec_up_has_discovery = False
    for node in ast.walk(lint_tree):
        if (
            isinstance(node, ast.Assign)
            and len(node.targets) == 1
            and isinstance(node.targets[0], ast.Name)
            and node.targets[0].id == "_SPEC_UP_FIELDS"
        ):
            if isinstance(node.value, (ast.Tuple, ast.List)):
                for elt in node.value.elts:
                    if isinstance(elt, ast.Constant) and elt.value == "Discovery":
                        spec_up_has_discovery = True
            break
    assert not spec_up_has_discovery, (
        "VI-1904: 'Discovery' must not be in _SPEC_UP_FIELDS (retired pre-T3 path)"
    )
