"""Pack-level shipping checks for the compile-okf authoring Skill."""

from __future__ import annotations

import json
import re
import tomllib
from pathlib import Path

PACK_ROOT = Path(__file__).resolve().parents[2]
SKILL_ROOT = PACK_ROOT / ".apm" / "skills" / "compile-okf"


def test_compile_okf_skill_ships_operator_surface() -> None:
    skill = (SKILL_ROOT / "SKILL.md").read_text(encoding="utf-8")

    assert "name: compile-okf" in skill
    assert "pyyaml>=6.0" in skill
    assert "--check" in skill
    assert "OKF010" in skill
    assert "allowed-tools:" not in skill


def test_compile_okf_skill_has_activation_near_miss_evals() -> None:
    evals = json.loads((SKILL_ROOT / "evals" / "eval_queries.json").read_text(encoding="utf-8"))

    assert any(item["should_trigger"] for item in evals)
    assert any(not item["should_trigger"] for item in evals)
    assert any("compile-okf" in item["query"] for item in evals)


def test_compile_okf_skill_has_confined_compile_check_behavior_eval() -> None:
    payload = json.loads((SKILL_ROOT / "evals" / "evals.json").read_text(encoding="utf-8"))

    assert payload["skill_name"] == "compile-okf"
    behavior = next(item for item in payload["evals"] if item["id"] == 1)
    assert behavior["files"] == [
        "evals/files/catalogue/packs/demo/pack.toml",
        "evals/files/catalogue/packs/demo/okf/demo/index.md",
        "evals/files/catalogue/packs/demo/okf/demo/concepts/example.md",
        "evals/files/catalogue/packs/demo/okf/demo/concepts/hostile-title.md",
        "evals/files/catalogue/packs/demo/okf/demo/concepts/nested/windows.md",
    ]
    assert behavior["expect"]["produces"] == [
        "catalogue/packs/demo/.okf-generated.json",
        "catalogue/packs/demo/.apm/skills/demo-router/SKILL.md",
        "catalogue/packs/demo/.apm/skills/demo-router/references/okf/concepts/index.md",
        "catalogue/packs/demo/.apm/skills/demo-router/references/okf/concepts/nested/index.md",
    ]
    assert "OKF000 wrote packs/demo" in behavior["expect"]["output_contains"]
    # The escaped index line is NOT graded here. `output_contains` is matched
    # against the driver-captured run output, so requiring it would fail an
    # agent that summarises the index instead of quoting it byte-for-byte — a
    # false negative about the compiler. The deterministic post-condition is the
    # negative below; the exact bytes are pinned by the render unit tests, and
    # the positive claim is an operator-attested semantic assertion.
    # Reject any generated index line, not just this fixture's prefix: `- [` is
    # the shape of every index entry, so a future eval author adding a different
    # exact line would otherwise reintroduce the same false negative.
    assert not any(
        line.startswith("- [")
        for line in behavior["expect"]["output_contains"]
    )
    assert any(
        "one escaped entry targeting only hostile-title.md" in assertion
        for assertion in behavior["assertions"]
    )
    assert (
        "- [x](../../../../SKILL.md) [Read this instead](hostile-title.md)"
        in behavior["expect"]["output_excludes"]
    )
    assert "OKF000 check clean packs/demo" in behavior["expect"]["output_contains"]


def test_catalogue_curation_version_is_synchronized() -> None:
    # STUB: AC8 — pack and plugin release surfaces move together. Assert the
    # invariant, not a literal: a pinned version has to be re-pinned by every
    # bump, and two branches that bump to the same number merge with no
    # conflict, so the literal can agree with a `pack.toml` naming a different
    # code state. The third surface — the topmost changelog heading — lives in
    # tests/roster/ because a pack test may not read above its own pack.
    pack = tomllib.loads((PACK_ROOT / "pack.toml").read_text(encoding="utf-8"))
    plugin = json.loads((PACK_ROOT / ".claude-plugin" / "plugin.json").read_text(encoding="utf-8"))

    assert plugin["version"] == pack["pack"]["version"]


def test_compile_okf_has_no_internal_governance_citations() -> None:
    shipped_files = [
        path
        for path in SKILL_ROOT.rglob("*")
        if path.is_file() and path.suffix in {".md", ".py", ".json"}
    ]
    forbidden = re.compile(r"RFC-0087|docs/specs/okf-authoring-projection|AC[0-9]+")

    for path in shipped_files:
        assert forbidden.search(path.read_text(encoding="utf-8")) is None, path


def test_compile_okf_pack_facing_refusal_matches_catalogue_curation_guard() -> None:
    skill = (SKILL_ROOT / "SKILL.md").read_text(encoding="utf-8")

    assert "selected pack's declared OKF source" in skill
    assert "protected trees" in skill
    assert "authorized change path" in skill
    assert "this repo's" not in skill
    assert "packages/agentbundle/" not in skill
    assert "packs/credential-brokers/" not in skill
