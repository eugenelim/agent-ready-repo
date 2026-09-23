"""Repository-level construction tests for `contracts/REGISTRY.md`.

Materialized from docs/specs/contract-backward-traceability-registry/plan.md
## Construction tests (T3).

This assertion cannot live under `packs/core/tests/`: it reads `contracts/` and
`docs/specs/`, both above that pack, which `tools/lint-pack-test-boundary.py`
forbids. `tests/AGENTS.md` owns that boundary.

The expected pair set is never transcribed. It is derived through the lint's own
`contract_header_refs` and `_XSPEC_FORMATS`, so the registry and the check agree
by construction rather than by a maintainer remembering to update both.
"""
import importlib.util
import pathlib
import re
import sys

import pytest

ROOT = pathlib.Path(__file__).resolve().parents[2]
LINT = ROOT / "packs/core/.apm/skills/work-loop/scripts/lint-spec-status.py"
REGISTRY = ROOT / "contracts/REGISTRY.md"
README = ROOT / "contracts/README.md"

# One `| `<contract>` | `<spec dir>/` |` row. The trailing slash is required
# here for the same reason the lint requires it: without it `docs/specs/foo`
# is satisfied by `docs/specs/foo-bar/`.
_ROW = re.compile(r"^\|\s*`([^`]+)`\s*\|\s*`([^`]+)/`\s*\|\s*$")


def _lint_module():
    spec = importlib.util.spec_from_file_location("lint_spec_status_roster", LINT)
    mod = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = mod
    spec.loader.exec_module(mod)
    return mod


def derived_pairs() -> set[tuple[str, str]]:
    """(contract token, spec dir) for every non-`x-spec` contract a spec names."""
    mod = _lint_module()
    pairs = set()
    for spec_path in sorted(ROOT.glob("docs/specs/*/spec.md")):
        feature_dir = spec_path.parent.relative_to(ROOT).as_posix()
        text = spec_path.read_text(encoding="utf-8")
        for _lineno, token in mod.contract_header_refs(text):
            if not token.endswith(mod._XSPEC_FORMATS):
                pairs.add((token, feature_dir))
    return pairs


def load_registry_text(path: pathlib.Path) -> str:
    """The registry's text, refusing a path that does not exist.

    AC-0004 lives here rather than in the comparison. A loader that returned ""
    for a missing file would let every text-level case pass while the registry
    was absent, which is the state this whole module exists to catch.
    """
    if not path.is_file():
        raise FileNotFoundError(f"contract registry missing: {path}")
    return path.read_text(encoding="utf-8")


def registry_pairs(text: str) -> set[tuple[str, str]]:
    return {(m.group(1), m.group(2)) for m in
            (_ROW.match(line) for line in text.splitlines()) if m}


# AC-0004: a registry path that does not exist fails, rather than skipping or
# passing. Driven at the loader, because the comparison never runs on a missing
# path and so cannot observe this state.
def test_absent_registry_path_raises(tmp_path: pathlib.Path) -> None:
    with pytest.raises(FileNotFoundError):
        load_registry_text(tmp_path / "REGISTRY.md")


# AC-0004 control: the loader is not raising unconditionally.
def test_present_registry_path_loads(tmp_path: pathlib.Path) -> None:
    present = tmp_path / "REGISTRY.md"
    present.write_text("| `contracts/a.toml` | `docs/specs/alpha/` |\n", encoding="utf-8")
    assert "contracts/a.toml" in load_registry_text(present)


# AC-0005: a row naming a spec that no longer names that contract fails.
def test_stale_row_fails_the_comparison() -> None:
    live = load_registry_text(REGISTRY)
    derived = derived_pairs()
    token, feature_dir = sorted(derived)[0]
    stale = live.replace(f"`{feature_dir}/`", "`docs/specs/not-a-real-spec/`", 1)
    assert stale != live, "the mutation must change the registry text"
    assert registry_pairs(stale) != derived, (
        "a row pointing at a spec that does not name this contract must not compare equal"
    )


# AC-0005: an emptied registry fails. Distinct from the absent path above; this
# one reaches the comparison, that one never does.
def test_registry_with_no_rows_fails_the_comparison() -> None:
    live = load_registry_text(REGISTRY)
    emptied = "\n".join(line for line in live.splitlines() if not _ROW.match(line))
    assert registry_pairs(emptied) == set()
    assert registry_pairs(emptied) != derived_pairs()


# AC-0001: the live registry covers exactly the derived pair set. Equality, not
# containment — a superset carries a row for a contract no spec names.
def test_live_registry_matches_the_derived_pair_set() -> None:
    derived = derived_pairs()
    actual = registry_pairs(load_registry_text(REGISTRY))
    assert actual == derived, (
        f"missing rows: {sorted(derived - actual)}; "
        f"rows for contracts no spec names: {sorted(actual - derived)}"
    )


# AC-0006: the contracts inventory records REGISTRY.md with `no` in the CLI data
# column. The oracle is the parsed cell: a mention of REGISTRY.md in the prose
# above the table must not satisfy it.
def test_readme_files_table_lists_the_registry() -> None:
    cell = None
    for line in README.read_text(encoding="utf-8").splitlines():
        cells = [c.strip() for c in line.strip().strip("|").split("|")]
        if len(cells) == 3 and cells[0] == "`REGISTRY.md`":
            cell = cells[2]
    assert cell == "no", f"expected CLI data 'no' for REGISTRY.md, got {cell!r}"
