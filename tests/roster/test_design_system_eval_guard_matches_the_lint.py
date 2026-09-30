"""The design-system eval guard carries the agnosticism lint's value shapes.

`tools/lint-experience-agnostic.py` is the mechanical floor under the pack's
promise to ship no design value, and it reads Markdown only — its own docstring
says so. The `design-system` eval corpus is JSON, so the lint never opens it,
and the pack-local contract suite stands over that gap instead.

That suite cannot import the lint: `tools/lint-pack-test-boundary.py` forbids a
pack test from reading above its own pack, because a pack installs standalone.
So it copies the four value patterns, and a copy drifts. It already did once —
an earlier revision kept the lint's digit-requiring hex lookahead but dropped
the companion rule for `#fff`, and dropped `vmin`/`vmax` and the decimal-seconds
rule, so `#ccc`, `0.3s` and `24vmin` passed the suite while the lint would have
caught every one.

This test is the join. It lives in the roster tree because comparing the two
requires reading both, which only a repository-level test may do. It compares
behaviour on probe strings rather than pattern text, so an equivalent rewrite of
either side stays green and a coverage change does not.
"""

from __future__ import annotations

import importlib.util
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
LINT = ROOT / "tools" / "lint-experience-agnostic.py"
PACK_SUITE = (
    ROOT
    / "packs"
    / "experience-design"
    / "tests"
    / "skills"
    / "design-system"
    / "test_design_system_contract.py"
)

# The lint labels these four rules as value shapes. Its remaining rules name a
# stack (framework names, styling syntax, platform roles), which is a
# portability concern rather than a shipped value, so they are out of scope here.
VALUE_LABELS = frozenset(
    {
        "color literal",
        "dimension / duration literal",
        "ratio literal",
        "named easing curve",
    }
)

# Probes, not pattern text. Each is a value an adopter could plausibly paste
# into an eval, plus the near-misses both sides deliberately allow.
PROBES = (
    "#fff",
    "#ccc",
    "#eee",
    "#1a2b3c",
    "#7c3aed",
    "rgb(0, 0, 0)",
    "rgba(0,0,0,0.6)",
    "hsl(210, 50%, 50%)",
    "4px",
    "8 px",
    "16rem",
    "1.5em",
    "12pt",
    "100vh",
    "50vw",
    "24vmin",
    "12 vmax",
    "200ms",
    "400 ms",
    "0.3s",
    "0.3 s",
    "4.5:1",
    "3:1",
    "cubic-bezier(0.4, 0, 0.2, 1)",
    "ease-in-out",
    "ease-in",
    "ease-out",
    # Deliberate non-matches. Both sides must keep letting these through:
    # `#facade` is a word slug, `1990s` is a decade, `16:9` is an aspect ratio,
    # and `80%` is ordinary prose.
    "#facade",
    "the 1990s",
    "16:9",
    "80% of users",
    "a dense rhythm",
)


def _load_lint_value_rules() -> list[tuple[str, re.Pattern[str]]]:
    """Return the lint's own value-shape rules, by importing it."""
    sys.path.insert(0, str(LINT.parent))
    try:
        spec = importlib.util.spec_from_file_location("experience_agnostic_lint", LINT)
        assert spec is not None and spec.loader is not None
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
    finally:
        sys.path.remove(str(LINT.parent))
    return [(label, pat) for label, pat in module._rules() if label in VALUE_LABELS]


def _load_pack_suite_value_rules() -> tuple[tuple[str, re.Pattern[str]], ...]:
    """Return the copied rules the pack-local contract suite carries."""
    spec = importlib.util.spec_from_file_location(
        "experience_design_design_system_contract", PACK_SUITE
    )
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module.VALUE_SHAPE_RULES


def test_both_sides_name_all_four_value_shapes() -> None:
    """A label dropped from either side would silently narrow the guard."""
    lint = {label for label, _ in _load_lint_value_rules()}
    pack = {label for label, _ in _load_pack_suite_value_rules()}
    assert lint == VALUE_LABELS, f"the lint no longer names {sorted(VALUE_LABELS - lint)}"
    assert pack == VALUE_LABELS, f"the pack suite no longer names {sorted(VALUE_LABELS - pack)}"


def test_the_copy_matches_the_lint_on_every_probe() -> None:
    """Identical verdicts, probe by probe, in both directions.

    Asserting on behaviour rather than on pattern text means an equivalent
    rewrite of either side passes, while a real change in what is caught — or
    in what is deliberately let through — fails and names the probe.
    """
    lint_rules = _load_lint_value_rules()
    pack_rules = _load_pack_suite_value_rules()

    disagreements = []
    for probe in PROBES:
        lint_hit = next((label for label, pat in lint_rules if pat.search(probe)), None)
        pack_hit = next((label for label, pat in pack_rules if pat.search(probe)), None)
        if lint_hit != pack_hit:
            disagreements.append(
                f"{probe!r}: lint says {lint_hit or 'clean'}, pack suite says {pack_hit or 'clean'}"
            )

    assert not disagreements, "the copied value rules have drifted from the lint:\n" + "\n".join(
        disagreements
    )
