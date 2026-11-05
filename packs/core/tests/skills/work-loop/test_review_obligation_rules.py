"""The review-tier rules keys (review-obligation-policy T1).

AC-0030: each missing or malformed tier key refuses ``review-rules-invalid``.
AC-0031: the shipped values, and ``max_review_retries`` unchanged from the merge base.
AC-0035: the shipped prose allowlist reaches no specification or decision record.
"""

from __future__ import annotations

import copy
import importlib.util
import json
import subprocess
import sys
from pathlib import Path
from types import ModuleType
from typing import Any

import pytest

_HELPER = Path(__file__).resolve().parent / "supervisor_harness.py"


def _harness() -> ModuleType:
    alias = "core_work_loop_supervisor_harness"
    if alias not in sys.modules:
        spec = importlib.util.spec_from_file_location(alias, _HELPER)
        assert spec is not None and spec.loader is not None
        sys.modules[alias] = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(sys.modules[alias])
    return sys.modules[alias]


h = _harness()
review = h.cli._supervisor("_supervisor_review.py")
Refusal = review.Refusal
RULES: dict[str, Any] = review.load_rules()


def _rules_file(tmp_path: Path, mutate: Any) -> Path:
    data = copy.deepcopy(RULES)
    mutate(data)
    path = tmp_path / "review-rules.json"
    path.write_text(json.dumps(data), encoding="utf-8")
    return path


@pytest.mark.parametrize(
    "mutate",
    [
        lambda d: d.pop("code_review_round_cap"),
        lambda d: d.update(code_review_round_cap=0),
        lambda d: d.update(code_review_round_cap=True),
        lambda d: d.update(code_review_round_cap="2"),
        lambda d: d.pop("minor_fix_max_lines"),
        lambda d: d.update(minor_fix_max_lines=-1),
        lambda d: d.update(minor_fix_max_lines=1.5),
        lambda d: d.pop("prose_allowlist"),
        lambda d: d.update(prose_allowlist=["docs/*.md"]),
        lambda d: d["prose_allowlist"].pop("instruction_names"),
        lambda d: d["prose_allowlist"].update(globs=[]),
        lambda d: d["prose_allowlist"].update(extra=["x"]),
        lambda d: d["prose_allowlist"].update(globs=["docs/*.md", ""]),
        lambda d: d.pop("protected_class_reviewers"),
        lambda d: d["protected_class_reviewers"].pop("migration"),
        lambda d: d["protected_class_reviewers"].update(privacy="security-reviewer"),
        lambda d: d["protected_class_reviewers"].update(migration="nobody"),
    ],
)
def test_ac0030_a_missing_or_malformed_tier_key_refuses(tmp_path: Path, mutate: Any) -> None:
    """AC-0030: every tier-key defect refuses with the named rules error."""
    with pytest.raises(Refusal) as refused:
        review.load_rules(_rules_file(tmp_path, mutate))
    assert refused.value.code == "review-rules-invalid"


def test_ac0031_the_shipped_rules_hold_the_tier_defaults() -> None:
    """AC-0031: the shipped cap is 2 rounds and the minor-fix limit 40 lines."""
    assert RULES["code_review_round_cap"] == 2
    assert RULES["minor_fix_max_lines"] == 40


def _git(*args: str) -> str:
    root = Path(__file__).resolve().parents[5]
    done = subprocess.run(
        ["git", "-C", str(root), *args], capture_output=True, text=True, check=False
    )
    return done.stdout.strip() if done.returncode == 0 else ""


def test_ac0031_max_review_retries_equals_its_merge_base_value() -> None:
    """AC-0031: ``max_review_retries`` keeps the value it has at the merge base."""
    base = _git("merge-base", "origin/main", "HEAD")
    if not base:
        pytest.skip("no origin/main merge base in this checkout")
    blob = _git("show", f"{base}:packs/core/.apm/skills/work-loop/review-rules.json")
    if not blob:
        pytest.skip("review-rules.json is absent at the merge base")
    assert RULES["max_review_retries"] == json.loads(blob)["max_review_retries"]


@pytest.mark.parametrize(
    "path",
    [
        "docs/specs/feature/spec.md",
        "docs/specs/feature/plan.md",
        "docs/specs/feature/notes/ledger.md",
        "docs/adr/0001-example.md",
        "docs/adr/README.md",
        "docs/rfc/0001-example.md",
        "docs/rfc/notes/a.md",
    ],
)
def test_ac0035_the_allowlist_reaches_no_record_path(path: str) -> None:
    """AC-0035: no shipped glob matches a spec, ADR, or RFC path."""
    globs = RULES["prose_allowlist"]["globs"]
    assert not any(review.glob_match(glob, path) for glob in globs)


def test_glob_star_does_not_cross_a_segment() -> None:
    """A single ``*`` matches within one segment; ``**`` spans segments."""
    assert review.glob_match("docs/*.md", "docs/a.md")
    assert not review.glob_match("docs/*.md", "docs/specs/a.md")
    assert review.glob_match("docs/guides/**/*.md", "docs/guides/a.md")
    assert review.glob_match("docs/guides/**/*.md", "docs/guides/x/y/a.md")
    assert not review.glob_match("docs/guides/**/*.md", "docs/guides/a.png")
