"""Integration test — export-catalogue's fail-closed verify on a realistic
derivative tree (RFC-0059 spec, export-catalogue ACs).

Builds a multi-file fork (README, pack.toml, a source file, a NOTICE) with
seeded upstream identity and asserts the mode-aware gate: white-label fails on
any surviving anchor anywhere; attributed passes only when the sole survivors
are inside the declared attribution surface; a fully-scrubbed tree passes both.
This is the clean-pass / leak-fail scenario the spec names as an integration."""

from __future__ import annotations

from pathlib import Path

import export_verify as V

ANCHORS = {
    "url": "https://github.com/acme/widgets",
    "email": "dev@acme.example",
    "slug": "acme-widgets",
    "owner": "acme",
}


def _fork(tmp: Path, files: dict[str, str]) -> Path:
    root = tmp / "fork"
    for rel, content in files.items():
        p = root / rel
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(content, encoding="utf-8")
    return root


def test_white_label_leak_fails_naming_files(tmp_path: Path) -> None:
    fork = _fork(tmp_path, {
        "README.md": "# Fork\n\nInstall from https://github.com/acme/widgets\n",
        "pack.toml": 'catalogue = "acme-widgets"\n[[maintainers]]\nemail = "dev@acme.example"\n',
        "src/util.py": "OWNER = 'acme'\n",
    })
    v = V.verify(fork, ANCHORS, mode="white-label")
    files_hit = {x.path for x in v}
    anchors_hit = {x.anchor for x in v}
    assert {"README.md", "pack.toml", "src/util.py"} <= files_hit
    assert {"url", "slug", "email", "owner"} <= anchors_hit  # all four caught


def test_clean_fork_passes_both_modes(tmp_path: Path) -> None:
    fork = _fork(tmp_path, {
        "README.md": "# Our fork\n\nInstall with `pip install -e .`\n",
        "pack.toml": 'catalogue = "our-catalogue"\n[[maintainers]]\nemail = "us@ours.example"\n',
        "src/util.py": "OWNER = 'us'\n",
    })
    assert V.verify(fork, ANCHORS, mode="white-label") == []
    assert V.verify(fork, ANCHORS, mode="attributed", attribution_paths=["NOTICE"]) == []


def test_attributed_passes_only_with_credit_in_notice(tmp_path: Path) -> None:
    fork = _fork(tmp_path, {
        "NOTICE": "This catalogue is derived from https://github.com/acme/widgets (acme).\n",
        "README.md": "# Our public fork\n\nA creative-writing catalogue.\n",
    })
    # credit confined to NOTICE → attributed passes
    assert V.verify(fork, ANCHORS, mode="attributed", attribution_paths=["NOTICE"]) == []
    # but the same tree in white-label mode still fails (NOTICE leaks identity)
    assert V.verify(fork, ANCHORS, mode="white-label") != []


def test_attributed_still_fails_on_leak_outside_notice(tmp_path: Path) -> None:
    fork = _fork(tmp_path, {
        "NOTICE": "Derived from https://github.com/acme/widgets\n",
        "docs/guide.md": "built by acme\n",  # leak outside the sanctioned surface
    })
    v = V.verify(fork, ANCHORS, mode="attributed", attribution_paths=["NOTICE"])
    assert v and all(x.path == "docs/guide.md" for x in v)
