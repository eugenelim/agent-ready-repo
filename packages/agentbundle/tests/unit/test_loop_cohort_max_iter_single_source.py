"""T5 (adopter-clean-enforcement-gate AC6): `max_iterations` is single-sourced.

The iteration cap lives in exactly one place — the bundled `state.json` template
(the adopter-visible per-spec knob). `loop-cohort.py` DEFAULTS derives its value
from the template rather than hard-coding a duplicate literal, so an adopter
changes the cap in one place.
"""

from __future__ import annotations

import importlib.util
import json
import re
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[4]
LOOP_COHORT = REPO_ROOT / "packs" / "core" / ".apm" / "skills" / "work-loop" / "scripts" / "loop-cohort.py"
TEMPLATE = REPO_ROOT / "packs" / "core" / ".apm" / "skills" / "work-loop" / "assets" / "state.json"


def _load_module():
    spec = importlib.util.spec_from_file_location("loop_cohort_t5", LOOP_COHORT)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def test_defaults_has_no_hardcoded_max_iterations_literal() -> None:
    """The duplicate literal is gone from loop-cohort.py — it derives instead."""
    src = LOOP_COHORT.read_text(encoding="utf-8")
    assert not re.search(r'"max_iterations"\s*:\s*\d+', src), (
        "loop-cohort.py must not hard-code a max_iterations literal; it derives "
        "the value from the bundled state.json template (single source)."
    )


def test_default_matches_template() -> None:
    """The derived DEFAULT equals the template's value (the single source)."""
    template_val = json.loads(TEMPLATE.read_text())["max_iterations"]
    mod = _load_module()
    assert mod.DEFAULTS["max_iterations"] == template_val


def test_broken_template_fallback_matches_template_value() -> None:
    """The last-resort `_fallback` constant (used only if the template is
    unreadable on a broken install) must stay hand-synced with the template's
    shipped value — otherwise the cap silently diverges on the fallback path.
    This drift-guard fails if someone bumps the template without the fallback."""
    template_val = json.loads(TEMPLATE.read_text())["max_iterations"]
    mod = _load_module()
    fallback_default = mod._template_max_iterations.__defaults__[0]
    assert fallback_default == template_val, (
        "loop-cohort.py `_template_max_iterations` _fallback must equal the "
        f"template's max_iterations ({template_val}); update it in lockstep."
    )
