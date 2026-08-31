"""Regression contracts promoted from the catalogue-curation QA record.

Roster-owned rather than pack-owned: the accelerator-pack admission rule spans
`docs/CHARTER.md` and the pack's own skills, and `lint-pack-test-boundary.py`
refuses a `packs/**` test that reads above its owning pack.
"""

from __future__ import annotations

import json
import re
import tomllib
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
PACK_ROOT = REPO_ROOT / "packs/catalogue-curation"


def test_assimilation_closes_target_release_contract() -> None:
    """A landed primitive must follow the target catalogue's release rules.

    The skill must defer the *order* to the target, not pick one. This repo
    writes the changelog entry after `build-self` (``packs/AGENTS.local.md``
    step 3), so a skill that hardcodes release history before projection
    contradicts both this catalogue and its own ``references/hook-landing.md``.
    """
    skill_root = PACK_ROOT / ".apm/skills/assimilate-primitive"
    body = " ".join((skill_root / "SKILL.md").read_text(encoding="utf-8").split())

    assert "target catalogue's established rules for pack versioning" in body
    assert "inventory or manifest text" in body
    assert "release history" in body
    assert "ask rather than inventing one" in body
    assert "in the order those rules specify" in body
    assert "Apply every required update before its supported" not in body

    # The eval is the behavior register for this step; a corrected step with a
    # stale eval would still teach the ordering it was fixed to remove.
    payload = json.loads((skill_root / "evals/evals.json").read_text(encoding="utf-8"))
    case = next(
        item
        for item in payload["evals"]
        if item["id"] == "landed-primitive-closes-target-release-contract"
    )
    assert "in the order those rules specify" in case["expected_output"]
    assert "before running its supported" not in case["expected_output"]

    # The hook-landing reference and packs/AGENTS.local.md are the authorities
    # the step defers to; if either stops saying so, the step lost its anchor.
    hook_landing = " ".join(
        (skill_root / "references/hook-landing.md").read_text(encoding="utf-8").split()
    )
    assert "after `build-self` completes" in hook_landing


def test_pack_proposal_uses_canonical_rfc_workflow() -> None:
    """Pack proposals must reuse the target catalogue's RFC authoring owner."""
    body = (PACK_ROOT / ".apm/skills/propose-catalogue-pack/SKILL.md").read_text(
        encoding="utf-8"
    )
    normalized = " ".join(body.split())

    assert "target catalogue's canonical RFC workflow" in body
    assert "When `new-rfc` is installed, use it" in normalized
    assert "rather than reproducing its template" in normalized
    assert "applicable Charter admission path" in normalized
    assert "four-principles bar" not in body
    assert "four charter principles" not in body
    assert "Principles 2-4" not in normalized
    assert "Principles 2–4" not in normalized
    assert "all three extra gates" not in body
    assert "Depends on `core` + `governance-extras`" not in body

    shell_reference = " ".join(
        (
            PACK_ROOT
            / ".apm/skills/propose-catalogue-pack/references/pack-shell.md"
        )
        .read_text(encoding="utf-8")
        .split()
    )
    assert "applicable Charter admission path" in shell_reference
    assert "four-principles" not in shell_reference


def test_resync_eval_is_self_contained() -> None:
    """The three RFC routing forms must be runnable from a fresh checkout."""
    eval_root = PACK_ROOT / ".apm/skills/assimilate-repo/evals"
    payload = json.loads((eval_root / "evals.json").read_text(encoding="utf-8"))
    case = next(item for item in payload["evals"] if item["id"] == "resync-rfc-routing-self-contained")

    assert len(case["files"]) == 3
    for relative_path in case["files"]:
        assert (PACK_ROOT / ".apm/skills/assimilate-repo" / relative_path).is_file()

    assert "Open RFC receives an in-place Amendment" in case["expected_output"]
    assert "Approver sign-off" in case["expected_output"]
    assert "require a new RFC" in case["expected_output"]


def test_new_activation_corpora_are_measured() -> None:
    """The pack eval allowlist must include every newly covered skill."""
    with (PACK_ROOT / "pack.toml").open("rb") as handle:
        manifest = tomllib.load(handle)

    assert set(manifest["pack"]["evals"]["skills"]) >= {
        "assimilate-primitive",
        "assimilate-repo",
        "propose-catalogue-pack",
    }


def test_admission_bars_are_stated_without_a_mutable_count() -> None:
    """No admission passage may restate how many principles there are.

    Covers the operator guides as well as the Charter: a curator follows the
    guide, so a count left there rejects a legitimate accelerator proposal on
    Universal no matter how the Charter reads. Whitespace-normalized, because
    pinning a line wrap would let a count reintroduced on one line pass.
    """
    charter_path = REPO_ROOT / "docs/CHARTER.md"
    charter = " ".join(charter_path.read_text(encoding="utf-8").split())

    assert "Each accelerator pack is exempt from the Universal principle" in charter
    assert "must clear every other catalogue principle" in charter
    assert "every applicable non-Universal catalogue principle" in charter

    # The Charter is the definition, so a bare count there is always about the
    # principles and the strict phrase list is safe.
    for count_phrase in ("four principles", "four bars", "all four", "remaining three"):
        assert count_phrase not in charter, f"CHARTER.md: {count_phrase}"

    # The guides count other things legitimately ("all four skills", "two
    # primitive types ... the no-merge-back principle"), so require the count to
    # directly modify "principle(s)" rather than merely share a sentence with it.
    counted_principle = re.compile(
        r"\b(?:two|three|four|five|\d+)\s+(?:\w+\s+){0,1}principles?\b",
        re.IGNORECASE,
    )
    guides = sorted((REPO_ROOT / "guides/catalogue-curation").rglob("*.md"))
    assert guides, "guide corpus went missing"
    for path in guides:
        body = " ".join(path.read_text(encoding="utf-8").split())
        hit = counted_principle.search(body)
        assert hit is None, f"{path.name}: {hit.group(0) if hit else ''}"
