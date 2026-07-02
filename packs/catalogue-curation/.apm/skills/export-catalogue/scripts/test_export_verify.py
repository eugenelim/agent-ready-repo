"""Tests for export_verify.py (RFC-0059 fail-closed export verify)."""

from __future__ import annotations

from pathlib import Path

import export_verify as V

ANCHORS = {
    "url": "https://github.com/acme/widgets",
    "email": "dev@acme.example",
    "slug": "acme-widgets",
    "owner": "acme",
}


def _tree(tmp: Path, files: dict[str, str]) -> Path:
    root = tmp / "target"
    for rel, content in files.items():
        p = root / rel
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(content, encoding="utf-8")
    return root


def test_clean_tree_passes(tmp_path: Path) -> None:
    root = _tree(tmp_path, {"README.md": "A clean fork.\n", "src/x.py": "print(1)\n"})
    assert V.verify(root, ANCHORS, mode="white-label") == []


def test_white_label_any_hit_fails(tmp_path: Path) -> None:
    root = _tree(tmp_path, {"README.md": "See https://github.com/acme/widgets for more.\n"})
    v = V.verify(root, ANCHORS, mode="white-label")
    assert v and v[0].anchor == "url"


def test_case_insensitive(tmp_path: Path) -> None:
    root = _tree(tmp_path, {"a.md": "contact DEV@ACME.EXAMPLE today\n"})
    v = V.verify(root, ANCHORS, mode="white-label")
    assert any(x.anchor == "email" for x in v)


def test_slug_and_owner_caught(tmp_path: Path) -> None:
    root = _tree(tmp_path, {"pack.toml": 'catalogue = "acme-widgets"\nowner = "acme"\n'})
    anchors_hit = {x.anchor for x in V.verify(root, ANCHORS, mode="white-label")}
    assert {"slug", "owner"} <= anchors_hit


def test_binary_skipped(tmp_path: Path) -> None:
    root = tmp_path / "target"
    (root / "img").mkdir(parents=True)
    (root / "img" / "logo.png").write_bytes(b"\x00acme-widgets\x00")  # binary, out of scope
    assert V.verify(root, ANCHORS, mode="white-label") == []


def test_attributed_allows_anchor_only_in_notice(tmp_path: Path) -> None:
    root = _tree(tmp_path, {
        "NOTICE": "Derived from https://github.com/acme/widgets\n",  # allowed here
        "README.md": "A fork.\n",
    })
    assert V.verify(root, ANCHORS, mode="attributed", attribution_paths=["NOTICE"]) == []
    # same anchor outside the notice surface still fails
    root2 = _tree(tmp_path / "b", {
        "NOTICE": "Derived from https://github.com/acme/widgets\n",
        "docs/x.md": "built by acme\n",
    })
    v = V.verify(root2, ANCHORS, mode="attributed", attribution_paths=["NOTICE"])
    assert v and any(x.anchor == "owner" for x in v)


def test_attribution_directory_prefix(tmp_path: Path) -> None:
    # Listing a directory exempts files under it (not just an exact file path).
    root = _tree(tmp_path, {"legal/NOTICE": "Derived from https://github.com/acme/widgets\n",
                            "README.md": "clean\n"})
    assert V.verify(root, ANCHORS, mode="attributed", attribution_paths=["legal/"]) == []
    assert V.verify(root, ANCHORS, mode="attributed", attribution_paths=["legal"]) == []


def test_literals_only_encoded_not_caught(tmp_path: Path) -> None:
    # Declared blind spot: a base64/encoded form is NOT caught (by design, stated).
    root = _tree(tmp_path, {"a.md": "YWNtZS13aWRnZXRz\n"})  # base64('acme-widgets')
    assert V.verify(root, ANCHORS, mode="white-label") == []
