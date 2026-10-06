# STUB: AC-0016
from __future__ import annotations

import json
import os
import shutil
import subprocess
import sys
from pathlib import Path

import pytest

BINS = Path(__file__).resolve().parents[2] / ".apm" / "adapter-root-bins"
SOURCE = BINS / "intent_delivery_relations.py"
HELPER = BINS / "_file_safety.py"
FILE_SAFETY_CANONICAL = (
    Path(__file__).resolve().parents[4]
    / "packages"
    / "agentbundle"
    / "agentbundle"
    / "catalogue_tooling"
    / "file_safety.py"
)


def test_ac0016_resolver_runs_without_agentbundle(tmp_path: Path) -> None:
    assert HELPER.is_file(), "co-located confinement helper is missing"
    bin_dir = tmp_path / "bin"
    bin_dir.mkdir()
    shutil.copy2(SOURCE, bin_dir / SOURCE.name)
    shutil.copy2(HELPER, bin_dir / HELPER.name)
    repo = tmp_path / "repo"
    (repo / "docs" / "specs").mkdir(parents=True)

    proc = subprocess.run(
        [sys.executable, "-I", "-S", str(bin_dir / SOURCE.name), "--root", str(repo)],
        capture_output=True,
        text=True,
        timeout=60,
    )

    assert proc.returncode == 0
    snapshot = json.loads(proc.stdout)
    assert snapshot["complete"] is True
    assert snapshot["artifacts"] == {}


# ---------------------------------------------------------------------------
# VI-1501: parity and helper-load guarantees
# ---------------------------------------------------------------------------


def test_vi1501_file_safety_is_byte_identical_to_canonical() -> None:
    """_file_safety.py is byte-identical to agentbundle.catalogue_tooling.file_safety."""
    assert FILE_SAFETY_CANONICAL.is_file(), "canonical file_safety.py not found"
    assert HELPER.read_bytes() == FILE_SAFETY_CANONICAL.read_bytes()


def test_vi1501_helper_must_be_regular_non_link_file(tmp_path: Path) -> None:
    """If _file_safety.py is a symlink, the resolver exits 2 before any corpus read."""
    if not hasattr(os, "symlink"):
        pytest.skip("symlinks unavailable")
    bin_dir = tmp_path / "bin"
    bin_dir.mkdir()
    shutil.copy2(SOURCE, bin_dir / SOURCE.name)
    real_helper = tmp_path / "real_file_safety.py"
    shutil.copy2(HELPER, real_helper)
    try:
        (bin_dir / HELPER.name).symlink_to(real_helper)
    except OSError:
        pytest.skip("symlinks unavailable on this platform")

    proc = subprocess.run(
        [sys.executable, "-I", "-S", str(bin_dir / SOURCE.name), "--root", str(tmp_path)],
        capture_output=True,
        text=True,
        timeout=60,
    )
    assert proc.returncode == 2
    # One stable-code line on stderr, no corpus-path exposure
    lines = [ln for ln in proc.stderr.splitlines() if ln.strip()]
    assert len(lines) == 1
    assert "required helper" in proc.stderr


def test_vi1501_missing_helper_exits_2_with_stable_message(tmp_path: Path) -> None:
    """Missing _file_safety.py → exit 2 with one stable-code line before corpus read."""
    bin_dir = tmp_path / "bin"
    bin_dir.mkdir()
    shutil.copy2(SOURCE, bin_dir / SOURCE.name)
    # Do NOT copy the helper.

    repo = tmp_path / "repo"
    (repo / "docs" / "specs").mkdir(parents=True)

    proc = subprocess.run(
        [sys.executable, "-I", "-S", str(bin_dir / SOURCE.name), "--root", str(repo)],
        capture_output=True,
        text=True,
        timeout=60,
    )
    assert proc.returncode == 2
    lines = [ln for ln in proc.stderr.splitlines() if ln.strip()]
    assert len(lines) == 1, f"expected one stderr line, got: {proc.stderr!r}"
    assert "required helper" in proc.stderr


# ---------------------------------------------------------------------------
# VI-1502: identity and unsafe-reference rules
# ---------------------------------------------------------------------------


def _load_resolver():
    import importlib.util
    spec = importlib.util.spec_from_file_location(
        "_core_confinement_resolver", SOURCE
    )
    assert spec and spec.loader
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def _make_intent(
    root: Path,
    *,
    slug: str,
    level: str = "feature",
    decomposed: str = "",
) -> None:
    d = root / "docs" / "product" / "intents"
    d.mkdir(parents=True, exist_ok=True)
    lines = [f"# {slug}\n\n", f"- **Slug:** `{slug}`\n"]
    if level:
        lines.append(f"- **Level:** {level}\n")
    if decomposed:
        lines.append(f"- **Decomposed:** {decomposed}\n")
    lines.append("\n## Outcome\nbody\n")
    (d / f"{slug}.md").write_text("".join(lines), encoding="utf-8")


def _make_brief(
    root: Path,
    *,
    slug: str,
    parent_intent: str = "",
    filename: str | None = None,
) -> None:
    d = root / "docs" / "product" / "briefs"
    d.mkdir(parents=True, exist_ok=True)
    fname = filename or f"{slug}.md"
    lines = [f"# {slug}\n\n", f"- **Slug:** `{slug}`\n"]
    if parent_intent:
        lines.append(f"- **Parent intent:** {parent_intent}\n")
    lines.append("\n## Summary\nbody\n")
    (d / fname).write_text("".join(lines), encoding="utf-8")


def _make_spec(
    root: Path,
    *,
    dir_name: str,
    discovery: str = "",
    brief: str = "",
) -> None:
    d = root / "docs" / "specs" / dir_name
    d.mkdir(parents=True, exist_ok=True)
    lines = ["- **Status:** Draft\n"]
    if discovery:
        lines.append(f"- **Discovery:** {discovery}\n")
    if brief:
        lines.append(f"- **Brief:** {brief}\n")
    (d / "spec.md").write_text("".join(lines), encoding="utf-8")


def _empty_snap() -> dict:
    """Return the expected empty complete snapshot."""
    return {
        "schema_version": 1,
        "complete": True,
        "relations": [],
        "classifications": [],
        "provenance": [],
        "diagnostics": [],
        "artifacts": {},
    }


def test_vi1502_intent_slug_grammar_invalid_slug_not_admitted(tmp_path: Path) -> None:
    """An intent file with an invalid Slug: (uppercase) is not admitted to the index."""
    d = tmp_path / "docs" / "product" / "intents"
    d.mkdir(parents=True, exist_ok=True)
    (d / "BadSlug.md").write_text(
        "# BadSlug\n\n- **Slug:** `BadSlug`\n- **Level:** feature\n"
        "- **Decomposed:** 2026-01-01 spec\n\n## O\nb\n",
        encoding="utf-8",
    )
    snap = _load_resolver().resolve_repository(tmp_path)
    expected = _empty_snap()
    assert snap == expected


def test_vi1502_unsafe_discovery_absolute_path(tmp_path: Path) -> None:
    """Absolute intent-shaped Discovery → delivery-reference-unsafe, full snapshot equality."""
    # Covered by test_ac0010_absolute_discovery_unsafe in test_intent_delivery_relations.py,
    # which now asserts the complete expected snapshot dict including "artifacts".
    # Verified: _make_spec(foo, discovery="`/docs/product/intents/alpha.md`") →
    # diagnostics=[{code:delivery-reference-unsafe,field:Discovery,subject:spec:foo}]


def test_vi1502_unsafe_brief_ref_absolute(tmp_path: Path) -> None:
    """Absolute Brief: value → delivery-reference-unsafe, not malformed."""
    _make_spec(tmp_path, dir_name="foo", brief="/absolute/brief:my-brief")
    snap = _load_resolver().resolve_repository(tmp_path)
    expected = {
        **_empty_snap(),
        "diagnostics": [
            {"code": "delivery-reference-unsafe", "field": "Brief", "subject": "spec:foo"},
        ],
    }
    assert snap == expected


def test_vi1502_unsafe_brief_ref_traversal(tmp_path: Path) -> None:
    """Traversal Brief: value → delivery-reference-unsafe, not malformed."""
    _make_spec(tmp_path, dir_name="foo", brief="../brief:my-brief")
    snap = _load_resolver().resolve_repository(tmp_path)
    expected = {
        **_empty_snap(),
        "diagnostics": [
            {"code": "delivery-reference-unsafe", "field": "Brief", "subject": "spec:foo"},
        ],
    }
    assert snap == expected


def test_vi1502_unsafe_parent_intent_absolute(tmp_path: Path) -> None:
    """Absolute Parent intent: → delivery-reference-unsafe."""
    _make_brief(tmp_path, slug="my-brief", parent_intent="/absolute/intent:feat")
    snap = _load_resolver().resolve_repository(tmp_path)
    expected = {
        **_empty_snap(),
        "diagnostics": [
            {
                "code": "delivery-reference-unsafe",
                "field": "Parent intent",
                "subject": "brief:my-brief",
            },
        ],
    }
    assert snap == expected


def test_vi1502_unsafe_parent_intent_traversal(tmp_path: Path) -> None:
    """Traversal Parent intent: → delivery-reference-unsafe."""
    _make_brief(tmp_path, slug="my-brief", parent_intent="../intent:feat")
    snap = _load_resolver().resolve_repository(tmp_path)
    expected = {
        **_empty_snap(),
        "diagnostics": [
            {
                "code": "delivery-reference-unsafe",
                "field": "Parent intent",
                "subject": "brief:my-brief",
            },
        ],
    }
    assert snap == expected


def test_vi1502_non_intent_discovery_absolute_emitted_without_target(tmp_path: Path) -> None:
    """Non-intent-shaped absolute Discovery: stays contextual provenance but target is omitted."""
    _make_spec(tmp_path, dir_name="foo", discovery="/absolute/tool-ref")
    snap = _load_resolver().resolve_repository(tmp_path)
    # /absolute/tool-ref is not intent-shaped (no 'intent:' prefix, no 'product/intents/')
    # AC-0010: "A Discovery: value that is not intent-shaped stays contextual-provenance
    # under AC-0007 whatever its form, and an absolute or parent-traversing one is
    # emitted without its target."
    assert snap["complete"] is True
    assert len(snap["provenance"]) == 1
    prov = snap["provenance"][0]
    assert prov["subject"] == "spec:foo"
    assert prov["field"] == "Discovery"
    # No "target" key because the value is unsafe
    assert "target" not in prov


def test_vi1502_duplicate_brief_slugs_ambiguous(tmp_path: Path) -> None:
    """Two brief files with the same Slug: → delivery-relation-ambiguous, slug removed."""
    d = tmp_path / "docs" / "product" / "briefs"
    d.mkdir(parents=True, exist_ok=True)
    # Two different files claiming slug "dup"
    (d / "brief-a.md").write_text(
        "# A\n\n- **Slug:** `dup`\n\n## Summary\nbody\n",
        encoding="utf-8",
    )
    (d / "brief-b.md").write_text(
        "# B\n\n- **Slug:** `dup`\n\n## Summary\nbody\n",
        encoding="utf-8",
    )
    snap = _load_resolver().resolve_repository(tmp_path)
    assert snap["complete"] is True
    assert snap["relations"] == []
    ambig = [d for d in snap["diagnostics"] if d["code"] == "delivery-relation-ambiguous"]
    assert len(ambig) == 1
    assert sorted(ambig[0]["targets"]) == [
        "docs/product/briefs/brief-a.md",
        "docs/product/briefs/brief-b.md",
    ]


def test_vi1502_underscore_prefixed_spec_dir_not_admitted(tmp_path: Path) -> None:
    """A spec directory starting with _ is not admitted as a delivery artifact."""
    _make_intent(tmp_path, slug="feat", decomposed="2026-01-01 spec")
    _make_spec(tmp_path, dir_name="_internal", discovery="`intent:feat`")
    snap = _load_resolver().resolve_repository(tmp_path)
    expected = {
        "schema_version": 1,
        "complete": True,
        "relations": [],
        "classifications": [
            {"classification": "unresolved", "intent": "intent:feat", "route": "spec"},
        ],
        "provenance": [],
        "diagnostics": [
            {"code": "delivery-target-missing", "subject": "intent:feat"},
        ],
        "artifacts": {},
    }
    assert snap == expected


def test_vi1502_symlink_at_intermediate_path_makes_snapshot_incomplete(tmp_path: Path) -> None:
    """A symlink at an intermediate artifact-root path component → complete=False."""
    if not hasattr(os, "symlink"):
        pytest.skip("symlinks unavailable")
    # Create a symlink at docs/product (intermediate path to intents root)
    real = tmp_path / "real_product"
    real.mkdir()
    docs = tmp_path / "docs"
    docs.mkdir()
    try:
        (docs / "product").symlink_to(real)
    except OSError:
        pytest.skip("symlinks unavailable on this platform")
    snap = _load_resolver().resolve_repository(tmp_path)
    assert snap["complete"] is False
    assert snap["diagnostics"] == []
    assert snap["artifacts"] == {}


# ---------------------------------------------------------------------------
# VI-1504: hostile values never appear in resolver JSON
# ---------------------------------------------------------------------------


def test_vi1504_hostile_slug_value_not_in_output(tmp_path: Path) -> None:
    """Control characters in Slug: are sanitized; hostile text never appears in JSON."""
    d = tmp_path / "docs" / "product" / "intents"
    d.mkdir(parents=True, exist_ok=True)
    hostile = "feat\x00\x01\x1b[31mInjected"
    (d / "feat.md").write_text(
        f"# Feat\n\n- **Slug:** `{hostile}`\n- **Level:** feature\n"
        "- **Decomposed:** 2026-01-01 spec\n\n## O\nb\n",
        encoding="utf-8",
    )
    mod = _load_resolver()
    snap = mod.resolve_repository(tmp_path)
    out = mod.serialize(snap)
    assert hostile not in out
    # Slug doesn't match _SLUG_RE → intent not admitted → no classifications
    assert snap["classifications"] == []


def test_vi1504_hostile_discovery_value_not_in_output(tmp_path: Path) -> None:
    """Hostile Discovery: value (control chars, bidi) never appears in resolver JSON."""
    hostile_discovery = "intent:feat\x00\x1b[31m injected"
    _make_spec(tmp_path, dir_name="foo", discovery=f"`{hostile_discovery}`")
    mod = _load_resolver()
    snap = mod.resolve_repository(tmp_path)
    out = mod.serialize(snap)
    assert hostile_discovery not in out
    assert "\x00" not in out
    assert "\x1b" not in out


def test_vi1504_hostile_decomposed_value_not_in_output(tmp_path: Path) -> None:
    """Hostile Decomposed: value never appears in resolver JSON."""
    d = tmp_path / "docs" / "product" / "intents"
    d.mkdir(parents=True, exist_ok=True)
    hostile_dec = "2026-01-01 spec\x00\x1b[31m injected"
    (d / "feat.md").write_text(
        f"# Feat\n\n- **Slug:** `feat`\n- **Level:** feature\n"
        f"- **Decomposed:** {hostile_dec}\n\n## O\nb\n",
        encoding="utf-8",
    )
    mod = _load_resolver()
    snap = mod.resolve_repository(tmp_path)
    out = mod.serialize(snap)
    assert hostile_dec not in out
    assert "\x00" not in out
    assert "\x1b" not in out


# ── Real-corpus artifact names ────────────────────────────────────────────────


def test_ordinal_prefixed_intent_file_and_capitalised_spec_dir_resolve(
    tmp_path: Path,
) -> None:
    """An ordinal-prefixed intent file and a capitalised, dotted spec dir resolve."""
    d = tmp_path / "docs" / "product" / "intents"
    d.mkdir(parents=True)
    (d / "FEAT-0012-alpha.md").write_text(
        "# Alpha\n\n- **Slug:** `alpha`\n- **Level:** feature\n"
        "- **Decomposed:** 2026-10-05 spec\n",
        encoding="utf-8",
    )
    _make_spec(tmp_path, dir_name="spec-A-alpha-0.1", discovery="`intent:alpha`")

    snap = _load_resolver().resolve_repository(tmp_path)

    assert snap["relations"] == [
        {
            "basis": {"intent": "Decomposed", "spec": "Discovery"},
            "intent": "intent:alpha",
            "route": "spec",
            "spec": "spec:spec-A-alpha-0.1",
            "type": "direct-delivery",
        }
    ]
    assert snap["artifacts"] == {
        "intent:alpha": "docs/product/intents/FEAT-0012-alpha.md",
        "spec:spec-A-alpha-0.1": "docs/specs/spec-A-alpha-0.1/spec.md",
    }


@pytest.mark.parametrize(
    "dir_name", ["bad\x1bname", "bad name", "-leading"], ids=["control", "space", "dash"]
)
def test_spec_dir_outside_grammar_is_not_admitted(tmp_path: Path, dir_name: str) -> None:
    """A spec directory whose name breaks the spec grammar never becomes an identity."""
    _make_intent(tmp_path, slug="alpha", decomposed="2026-10-05 spec")
    _make_spec(tmp_path, dir_name=dir_name, discovery="`intent:alpha`")

    snap = _load_resolver().resolve_repository(tmp_path)

    assert snap["relations"] == []
    assert all(dir_name not in key for key in snap["artifacts"])
    assert {"code": "delivery-target-missing", "subject": "intent:alpha"} in snap["diagnostics"]


def test_intent_file_name_outside_grammar_is_not_admitted(tmp_path: Path) -> None:
    """An intent file whose name breaks the file grammar is not admitted."""
    d = tmp_path / "docs" / "product" / "intents"
    d.mkdir(parents=True)
    (d / "alpha\x1b.md").write_text(
        "# Alpha\n\n- **Slug:** `alpha`\n- **Level:** feature\n"
        "- **Decomposed:** 2026-10-05 spec\n",
        encoding="utf-8",
    )

    snap = _load_resolver().resolve_repository(tmp_path)

    assert snap == _empty_snap()
