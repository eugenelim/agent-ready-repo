#!/usr/bin/env python3
"""Behavioural coverage for `tools/check-docs-contrast.py`.

# STUB: AC3 — red stub materialised at PLAN per CONVENTIONS § Stub → EXECUTE handoff.

Two seams, deliberately separated:

- The **ratio maths** is imported and exercised directly. `ratio()` and
  `luminance()` are pure, so a WCAG reference value is the honest assertion.
- The **CLI contract** is exercised as a subprocess against a temp tree. The
  script reads a module-level relative `CSS_PATH`, so `cwd` is the whole
  interface — which is why no `--css` flag is added here. Adding one would be a
  public interface no acceptance criterion authorises, and the shipped
  `docs-site/src/styles/starlight.css` is never mutated by these tests.

The threshold case does not assert a pair measuring exactly 4.5:1 — none exists.
No gray-on-gray 6-hex pair lands on 4.5 (all 65 536 were measured), and the
shipped palette has none either, so a fixture claiming to sit exactly on the
boundary would be asserting a fiction.
What is asserted instead is the comparison's *inclusivity* (a synthetic ratio at
the floor passes) plus the tightest real pairs either side of it.
"""

from __future__ import annotations

import importlib.util
import subprocess
import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent
SCRIPT = REPO_ROOT / "tools" / "check-docs-contrast.py"
if not SCRIPT.is_file():  # wrong parents[] depth after a move
    raise SystemExit(f"subject not found at {SCRIPT} — check the parents[] depth")


def _load():
    """Import the hyphenated script by path — it is not an importable module name."""
    spec = importlib.util.spec_from_file_location("_docs_contrast", SCRIPT)
    assert spec and spec.loader
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


mod = _load()


def _css(pairs: str, light_overrides: str = "") -> str:
    """A minimal two-theme sheet defining every name PAIRS references.

    `light_overrides` is written ONLY into the `[data-theme='light']` block, so a
    fixture can make the themes differ. Without that, both blocks carried identical
    declarations and no test could distinguish them — deleting the light theme from
    `theme_tables` left the whole suite green while silently dropping 14 pairs,
    including the three closest to the floor in the shipped palette.
    """
    return (
        ":root {\n" + pairs + "}\n"
        "[data-theme='light'] {\n" + pairs + light_overrides + "}\n"
    )


def _all_pairs_ok() -> str:
    return ("".join(f"  {fg}: #000000;\n" for fg, _ in mod.PAIRS)
            + "".join(f"  {bg}: #ffffff;\n" for _, bg in mod.PAIRS))


def _run(root: Path) -> subprocess.CompletedProcess[str]:
    css = root / "docs-site" / "src" / "styles" / "starlight.css"
    css.parent.mkdir(parents=True, exist_ok=True)
    return subprocess.run(
        [sys.executable, str(SCRIPT)], cwd=root, capture_output=True, text=True,
    )


# --------------------------------------------------------------------------
# Ratio maths — pure, so assert against WCAG reference values
# --------------------------------------------------------------------------

def test_ratio_black_on_white_is_the_wcag_maximum() -> None:
    assert round(mod.ratio("#000000", "#ffffff"), 2) == 21.0


def test_ratio_is_symmetric() -> None:
    assert mod.ratio("#000000", "#ffffff") == mod.ratio("#ffffff", "#000000")


def test_identical_colours_have_no_contrast() -> None:
    assert round(mod.ratio("#7f7f7f", "#7f7f7f"), 2) == 1.0


def test_threshold_is_inclusive_at_the_floor() -> None:
    """A ratio measuring exactly FLOOR must PASS, not fail.

    WCAG's threshold is inclusive. Asserted through `passes()`, the seam `main()`
    actually calls, so flipping it to `>` fails here — an earlier draft of this
    test compared `FLOOR <= FLOOR`, which is true regardless of the production
    comparison and stayed green when the operator was flipped.
    """
    assert mod.passes(mod.FLOOR) is True
    assert mod.passes(mod.FLOOR - 1e-9) is False
    assert mod.passes(mod.FLOOR + 1e-9) is True


def test_floor_is_the_wcag_aa_threshold() -> None:
    """Pin the constant itself.

    Every other assertion here is FLOOR-relative, so without this the threshold
    could be moved a long way with the whole suite green — and changing it is an
    "Ask first" boundary in the spec.
    """
    assert mod.FLOOR == 4.5


def test_tightest_real_pairs_straddle_the_floor() -> None:
    """#767676 on white is the canonical just-above-4.5 web pair; #777777 just fails.

    Both are within 0.03 of the floor, so this brackets it tightly — an earlier
    draft used #8a8a8a (3.45), loose enough that FLOOR could drift ~24% undetected.
    """
    assert mod.ratio("#767676", "#ffffff") >= mod.FLOOR
    assert mod.ratio("#777777", "#ffffff") < mod.FLOOR


# --------------------------------------------------------------------------
# Invalid input — each named case refuses, none crashes with a raw traceback
# --------------------------------------------------------------------------

@pytest.mark.parametrize("value", ["#xyzxyz", "#12345", "", "#"])
def test_malformed_hex_refuses_clearly(value: str) -> None:
    with pytest.raises(mod.ColourError):
        mod.luminance(value)


def test_three_digit_shorthand_is_refused_not_silently_wrong() -> None:
    """`#abc` is legal CSS but unsupported here.

    It must refuse rather than misparse: `int("ab", 16)` would succeed and yield a
    plausible-but-wrong luminance, which is worse than an error.
    """
    with pytest.raises(mod.ColourError):
        mod.luminance("#abc")


def test_unresolvable_var_chain_refuses_clearly() -> None:
    with pytest.raises(mod.ColourError):
        mod.resolve("--doc-text", {"--doc-text": "var(--nope)"})


def test_var_cycle_refuses_rather_than_recursing() -> None:
    table = {"--a": "var(--b)", "--b": "var(--a)"}
    with pytest.raises(mod.ColourError):
        mod.resolve("--a", table)


# --------------------------------------------------------------------------
# CLI contract — exit status is the gate CI depends on
# --------------------------------------------------------------------------

def test_passing_palette_exits_zero(tmp_path: Path) -> None:
    pairs = "".join(f"  {fg}: #000000;\n" for fg, _ in mod.PAIRS) + \
            "".join(f"  {bg}: #ffffff;\n" for _, bg in mod.PAIRS)
    (tmp_path / "docs-site" / "src" / "styles").mkdir(parents=True)
    (tmp_path / "docs-site" / "src" / "styles" / "starlight.css").write_text(
        _css(pairs), encoding="utf-8")
    r = _run(tmp_path)
    assert r.returncode == 0, r.stdout + r.stderr
    assert "all pairs pass" in r.stdout


def test_one_failing_registered_pair_exits_non_zero(tmp_path: Path) -> None:
    """The seeded-failure case AC4's CI gate depends on.

    Seeded in a temp tree, never in the shipped palette.
    """
    fg0, bg0 = mod.PAIRS[0]
    pairs = "".join(f"  {fg}: #000000;\n" for fg, _ in mod.PAIRS) + \
            "".join(f"  {bg}: #ffffff;\n" for _, bg in mod.PAIRS)
    # Collapse one registered pair onto near-identical greys → ~1:1.
    pairs += f"  {fg0}: #808080;\n  {bg0}: #858585;\n"
    (tmp_path / "docs-site" / "src" / "styles").mkdir(parents=True)
    (tmp_path / "docs-site" / "src" / "styles" / "starlight.css").write_text(
        _css(pairs), encoding="utf-8")
    r = _run(tmp_path)
    assert r.returncode != 0, r.stdout + r.stderr
    assert "below" in r.stdout


def test_malformed_palette_value_exits_non_zero_without_traceback(tmp_path: Path) -> None:
    pairs = "".join(f"  {fg}: #zzzzzz;\n" for fg, _ in mod.PAIRS) + \
            "".join(f"  {bg}: #ffffff;\n" for _, bg in mod.PAIRS)
    (tmp_path / "docs-site" / "src" / "styles").mkdir(parents=True)
    (tmp_path / "docs-site" / "src" / "styles" / "starlight.css").write_text(
        _css(pairs), encoding="utf-8")
    r = _run(tmp_path)
    assert r.returncode != 0, r.stdout + r.stderr
    assert "Traceback" not in r.stderr, f"must refuse, not crash: {r.stderr}"


def test_below_floor_in_light_theme_only_is_caught(tmp_path: Path) -> None:
    """The light theme must be enumerated, not just dark.

    `theme_tables` builds light as `{**dark, **light}`. Deleting the light entry, or
    swapping the merge order so light no longer overrides, both left every other test
    green — while dropping 14 pairs including the three tightest in the shipped
    palette. This fixture is clean in `:root` and fails only under
    `[data-theme='light']`, so it can only pass if light is actually checked.
    """
    fg0, bg0 = mod.PAIRS[0]
    (tmp_path / "docs-site" / "src" / "styles").mkdir(parents=True)
    (tmp_path / "docs-site" / "src" / "styles" / "starlight.css").write_text(
        _css(_all_pairs_ok(), light_overrides=f"  {fg0}: #808080;\n  {bg0}: #858585;\n"),
        encoding="utf-8")
    r = _run(tmp_path)
    assert r.returncode != 0, r.stdout + r.stderr
    assert "light" in r.stdout, f"the light theme must be named in the failure: {r.stdout}"


def test_both_themes_are_enumerated(tmp_path: Path) -> None:
    """A clean palette must still report BOTH themes, so a dropped theme is visible."""
    (tmp_path / "docs-site" / "src" / "styles").mkdir(parents=True)
    (tmp_path / "docs-site" / "src" / "styles" / "starlight.css").write_text(
        _css(_all_pairs_ok()), encoding="utf-8")
    r = _run(tmp_path)
    assert r.returncode == 0, r.stdout + r.stderr
    assert "dark" in r.stdout and "light" in r.stdout, r.stdout
    # Every registered pair, in both themes.
    assert r.stdout.count("on ") == 2 * len(mod.PAIRS), r.stdout


def test_unresolvable_var_in_palette_exits_non_zero_without_traceback(tmp_path: Path) -> None:
    """Covers the `resolve()` handler in `main()` at the CLI boundary.

    Deleting that try/except left the suite green: the unresolvable-var case was
    asserted only at the `resolve()` unit level, so AC3's no-traceback promise was
    unproven for that handler.
    """
    fg0, _ = mod.PAIRS[0]
    (tmp_path / "docs-site" / "src" / "styles").mkdir(parents=True)
    (tmp_path / "docs-site" / "src" / "styles" / "starlight.css").write_text(
        _css(_all_pairs_ok() + f"  {fg0}: var(--nope);\n"), encoding="utf-8")
    r = _run(tmp_path)
    assert r.returncode != 0, r.stdout + r.stderr
    assert "Traceback" not in r.stderr, f"must refuse, not crash: {r.stderr}"


def test_missing_css_exits_non_zero_without_traceback(tmp_path: Path) -> None:
    r = _run(tmp_path)  # creates the dir but no file
    assert r.returncode != 0
    assert "Traceback" not in r.stderr, f"must refuse, not crash: {r.stderr}"


def test_undecodable_css_exits_non_zero_without_traceback(tmp_path: Path) -> None:
    """`UnicodeDecodeError` is a ValueError, not an OSError.

    An earlier draft caught only `OSError`, so a non-UTF8 sheet escaped as a raw
    traceback printing absolute repo paths — from a required CI step, which reads
    as tooling breakage rather than the contract violation it is.
    """
    css = tmp_path / "docs-site" / "src" / "styles"
    css.mkdir(parents=True)
    (css / "starlight.css").write_bytes(b"\xff\xfe:root{--doc-text:#000000;}")
    r = _run(tmp_path)
    assert r.returncode != 0
    assert "Traceback" not in r.stderr, f"must refuse, not crash: {r.stderr}"
