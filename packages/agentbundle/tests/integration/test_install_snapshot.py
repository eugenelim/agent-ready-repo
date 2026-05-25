"""First-install snapshot test (RFC-0002 amendment 2026-05-25, item (e)).

For each pack with seeds (`core`, `governance-extras`,
`user-guide-diataxis`, `monorepo-extras`), this test runs
`agentbundle scaffold` against the real pack into a fresh tempdir
and verifies two contracts that together close the seed scaffold
leak:

  1. **Path-tree golden.** The sorted list of scaffolded paths matches
     a checked-in golden. Catches "a new scaffold file appeared" or
     "an expected scaffold file disappeared" regressions.

  2. **No catalogue-string leaks.** Each scaffolded file is scanned
     against the same blocklist `tools/lint-seeds.py` uses — no
     `agent-ready-repo`, RFC-NNNN, K-NNNN, or internal-spec names.
     Catches "seed scrub got reverted" regressions.

*Single-route scope (per the 2026-05-25 rescope amendment to AC22;
see `docs/specs/self-hosting/spec.md` § Changelog):* `agentbundle
scaffold` is the only function that drops `packs/<pack>/seeds/` into
an adopter tree. Seed projection is route-agnostic by construction —
the `per-pack-claude-plugin` and `per-pack-apm-package` build recipes
produce no `dist/<route>/<pack>/seeds/` subtree, and the install→adapt
chain reads marker files but never invokes `scaffold`. Testing
`scaffold` directly is therefore sufficient to catch leaks at the
source; AC21's `tools/lint-seeds.py` is the cross-source invariant.

Goldens live at
`packages/agentbundle/tests/fixtures/install_snapshot/<pack>.paths.txt`
— a sorted newline-delimited list of seed-relative scaffolded paths.
Set `UPDATE_GOLDEN=1` to regenerate.
"""

from __future__ import annotations

import argparse
import contextlib
import io
import os
import re
from pathlib import Path

import pytest

from agentbundle.commands import scaffold


REPO_ROOT = Path(__file__).resolve().parents[4]
PACKS_ROOT = REPO_ROOT / "packs"
FIXTURES_DIR = (
    Path(__file__).resolve().parent.parent
    / "fixtures"
    / "install_snapshot"
)

# Mirror lint-seeds.py's blocklist. Sourced from RFC-0002 § Amendments
# § 2026-05-25. Keep in sync; see lint-seeds.py:BLOCKLIST_PATTERNS.
BLOCKLIST_REGEXES = [
    re.compile(p)
    for p in (
        r"agent-ready-repo",
        r"RFC-00\d\d",
        r"K-00\d\d",
        r"\b("
        r"distribution-adapters|self-hosting|agent-spec-cli|"
        r"user-scope-hooks|converters-pack|"
        r"claude-plugins-install-route|codex-native-skills|"
        r"apm-install-route-parity|skill-secrets|wire-session-start-hook|"
        r"kiro-ide-hook|windows-ci-bundler|windows-hooks-phase3"
        r")\b",
    )
]

# Same single-line sentinel lint-seeds.py honours. Catalogue-attribution
# footer at `packs/core/seeds/AGENTS.md:171` is the documented exception.
SENTINEL_RE = re.compile(
    r"^\s*<!--\s*seed-content-lint-ignore:\s*([^>]+?)\s*-->\s*$"
)

PACKS_WITH_SEEDS = ("core", "governance-extras", "user-guide-diataxis", "monorepo-extras")


def _scaffold_pack(pack_name: str, tmp_path: Path) -> Path:
    """Scaffold `packs/<pack_name>/seeds/` into `tmp_path` and return
    the output root the scaffold wrote to."""
    target = tmp_path / "repo"
    target.mkdir()

    args = argparse.Namespace(
        pack=pack_name,
        packs_dir=str(PACKS_ROOT),
        output=str(target),
    )
    out, err = io.StringIO(), io.StringIO()
    with contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
        rc = scaffold.run(args)
    assert rc == 0, f"scaffold {pack_name} failed: {err.getvalue()}"
    return target


def _walk_projected(output_root: Path) -> list[str]:
    """Return sorted POSIX-style relative paths for every file under
    `output_root`."""
    paths: list[str] = []
    for path in output_root.rglob("*"):
        if not path.is_file():
            continue
        paths.append(path.relative_to(output_root).as_posix())
    return sorted(paths)


def _scan_for_leaks(output_root: Path, projected_paths: list[str]) -> list[str]:
    """Return a list of leak violations, honouring sentinel exemptions."""
    violations: list[str] = []
    for rel in projected_paths:
        abs_path = output_root / rel
        try:
            content = abs_path.read_text(encoding="utf-8")
        except UnicodeDecodeError:
            continue  # binary; skip
        lines = content.splitlines()
        pending_sentinel = False
        for lineno, line in enumerate(lines, start=1):
            if SENTINEL_RE.match(line):
                pending_sentinel = True
                continue
            if pending_sentinel:
                # Skip blocklist scan; sentinel exempts this single line.
                pending_sentinel = False
                continue
            for regex in BLOCKLIST_REGEXES:
                if regex.search(line):
                    violations.append(
                        f"{rel}:{lineno}: catalogue-string leak "
                        f"({regex.pattern!r}) — seed scrub may have been "
                        f"reverted"
                    )
    return violations


def _compare_or_update_paths_golden(pack_name: str, actual_paths: list[str]) -> None:
    """Compare actual projected-paths list to the checked-in golden;
    regenerate on `UPDATE_GOLDEN=1`."""
    golden = FIXTURES_DIR / f"{pack_name}.paths.txt"
    actual_text = "\n".join(actual_paths) + "\n" if actual_paths else ""

    if os.environ.get("UPDATE_GOLDEN") == "1":
        golden.parent.mkdir(parents=True, exist_ok=True)
        golden.write_text(actual_text, encoding="utf-8")
        return

    assert golden.exists(), (
        f"Golden not found at {golden}. "
        f"First run? Set UPDATE_GOLDEN=1 to create it."
    )
    expected = golden.read_text(encoding="utf-8")
    assert actual_text == expected, (
        f"Projected-paths diverged from golden for pack {pack_name!r}. "
        f"If the divergence is legitimate (seed structure changed by "
        f"design), regenerate with UPDATE_GOLDEN=1 and review the diff."
    )


@pytest.mark.parametrize("pack_name", PACKS_WITH_SEEDS)
def test_first_install_snapshot(pack_name: str, tmp_path: Path) -> None:
    """For each pack, scaffold via CLI route and verify (i) projected
    paths match the golden, (ii) projected content has no catalogue
    leaks."""
    output_root = _scaffold_pack(pack_name, tmp_path)
    projected_paths = _walk_projected(output_root)

    # Path-tree golden comparison.
    _compare_or_update_paths_golden(pack_name, projected_paths)

    # Content blocklist scan.
    leaks = _scan_for_leaks(output_root, projected_paths)
    assert not leaks, (
        f"Catalogue-string leaks in projected output for pack "
        f"{pack_name!r}:\n  " + "\n  ".join(leaks)
    )
