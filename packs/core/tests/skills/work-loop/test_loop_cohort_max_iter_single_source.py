"""T5 (adopter-clean-enforcement-gate): `max_implementation_retries` is single-sourced.

The implementation-retry cap lives in exactly one place — the bundled `state.json` template
(the adopter-visible per-spec knob). `loop-cohort.py` DEFAULTS derives its value
from the template rather than hard-coding a duplicate literal, so an adopter
changes the cap in one place.
"""

from __future__ import annotations

import importlib.util
import json
import re
from pathlib import Path

PACK_ROOT = Path(__file__).resolve().parents[3]
LOOP_COHORT = (
    PACK_ROOT / ".apm" / "skills" / "work-loop" / "scripts" / "loop-cohort.py"
)
TEMPLATE = PACK_ROOT / ".apm" / "skills" / "work-loop" / "assets" / "state.json"


def _load_module():
    spec = importlib.util.spec_from_file_location("loop_cohort_t5", LOOP_COHORT)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def test_defaults_has_no_hardcoded_max_iterations_literal() -> None:
    """The old max_iterations literal is gone from loop-cohort.py."""
    src = LOOP_COHORT.read_text(encoding="utf-8")
    assert not re.search(r'"max_iterations"\s*:\s*\d+', src), (
        "loop-cohort.py must not contain a max_iterations literal; "
        "Phase 1 renamed the field to max_implementation_retries."
    )


def test_default_matches_template() -> None:
    """DEFAULTS['max_implementation_retries'] equals the template's value (single source)."""
    template_val = json.loads(TEMPLATE.read_text())["max_implementation_retries"]
    mod = _load_module()
    assert mod.DEFAULTS["max_implementation_retries"] == template_val


def test_broken_template_fallback_matches_template_value() -> None:
    """The last-resort _fallback in `_template_max_implementation_retries` must
    stay hand-synced with the template's shipped value — otherwise the cap
    silently diverges on a broken-install path."""
    template_val = json.loads(TEMPLATE.read_text())["max_implementation_retries"]
    mod = _load_module()
    fallback_default = mod._template_max_implementation_retries.__defaults__[0]
    assert fallback_default == template_val, (
        "loop-cohort.py `_template_max_implementation_retries` fallback must equal "
        f"the template's max_implementation_retries ({template_val}); "
        "update it in lockstep."
    )
