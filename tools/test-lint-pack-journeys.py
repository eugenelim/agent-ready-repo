#!/usr/bin/env python3
"""Self-tests for tools/lint-pack-journeys.py.

Uses fixture directories in a temp dir. Set LPJ_PACKS_DIR and LPJ_JOURNEY_DIR
to point the validator at a fixture tree instead of the real repo.

Exit 0 when all tests pass; exit 1 on any failure.
"""
from __future__ import annotations

import os
import pathlib
import subprocess
import sys
import tempfile

_HERE = pathlib.Path(__file__).resolve().parent
_TOOL = _HERE / "lint-pack-journeys.py"


def _run(packs_dir: pathlib.Path, journey_dir: pathlib.Path) -> subprocess.CompletedProcess:
    env = os.environ.copy()
    env["LPJ_PACKS_DIR"] = str(packs_dir)
    env["LPJ_JOURNEY_DIR"] = str(journey_dir)
    return subprocess.run(
        [sys.executable, str(_TOOL)],
        capture_output=True, text=True, check=False, env=env,
    )


def _make_skill(pack_dir: pathlib.Path, skill_name: str) -> None:
    skill_dir = pack_dir / ".apm" / "skills" / skill_name
    skill_dir.mkdir(parents=True, exist_ok=True)
    (skill_dir / "SKILL.md").write_text(f"# {skill_name}\n", encoding="utf-8")


def _make_journey(pack_dir: pathlib.Path, *, extra_fm: str = "", stages: str = "") -> None:
    """Write a minimal valid JOURNEY.md into pack_dir."""
    pack_name = pack_dir.name
    skill_name = list((pack_dir / ".apm" / "skills").iterdir())[0].name
    fm = f"""---
journey_id: {pack_name}
pack: {pack_name}
scope: user
tagline: "Test journey"
contract:
  useItWhen: "test"
  youProvide: "input"
  youReceive: "output"
  yourDecisions:
    - "confirm"
skills:
  - name: {skill_name}
    description: "A skill"
    humanTouches: 1
humanGates:
  - id: G1
    globalGate: null
    label: "Review"
    trigger: "after draft"
    duration: "5 min"
    whatToCheck: ["looks good?"]
    whatGoodLooksLike: "great"
    whatBadLooksLike: "bad"
    consequence: "revise"
typicalSession:
  agentTurns: "3"
  humanTouches: 1
  wallClockMinutes: "15"
docsUrl: /guides/test/
packUrl: /packs/test/
{extra_fm}---

{stages if stages else _DEFAULT_STAGES}
"""
    (pack_dir / "JOURNEY.md").write_text(fm, encoding="utf-8")


_DEFAULT_STAGES = """\
### 1. Do the thing

- **You provide:** input
- **Agent does:** work
- **You decide:** confirm
- **Output:** result
- **State:** read-only
"""

_WRITE_STAGE = """\
### 1. Write the thing

- **You provide:** input
- **Agent does:** work
- **You decide:** confirm
- **Output:** result
- **State:** confirmed-write
"""

_WRITE_STAGE_NO_DECIDE = """\
### 1. Write the thing

- **You provide:** input
- **Agent does:** work
- **Output:** result
- **State:** confirmed-write
"""

_DECISION_REQUIRED_NO_DECIDE = """\
### 1. Decide the thing

- **You provide:** input
- **Agent does:** work
- **Output:** result
- **State:** decision-required
"""

_STAGE_BOGUS_STATE = """\
### 1. Do the thing

- **You provide:** input
- **Agent does:** work
- **Output:** result
- **State:** bogus
"""

_STAGE_NO_OUTPUT = """\
### 1. Do the thing

- **You provide:** input
- **Agent does:** work
- **State:** read-only
"""

_STAGE_NO_STATE = """\
### 1. Do the thing

- **You provide:** input
- **Agent does:** work
- **Output:** result
"""


def _pass(label: str, r: subprocess.CompletedProcess) -> None:
    if r.returncode != 0:
        print(f"FAIL {label}: expected exit 0, got {r.returncode}")
        print(r.stderr)
        sys.exit(1)
    print(f"pass {label}")


def _fail(label: str, r: subprocess.CompletedProcess, fragment: str = "") -> None:
    if r.returncode == 0:
        print(f"FAIL {label}: expected exit 1, got 0")
        print(r.stdout)
        sys.exit(1)
    if fragment and fragment not in r.stderr:
        print(f"FAIL {label}: expected {fragment!r} in stderr, got:\n{r.stderr}")
        sys.exit(1)
    print(f"pass {label}")


def test_valid_journey_exits_0() -> None:
    with tempfile.TemporaryDirectory() as td:
        p = pathlib.Path(td)
        pack = p / "packs" / "mypak"
        _make_skill(pack, "my-skill")
        _make_journey(pack)
        jd = p / "journeys"
        jd.mkdir()
        _pass("test_valid_journey_exits_0", _run(p / "packs", jd))


def test_journey_id_differs_from_pack_name_valid() -> None:
    with tempfile.TemporaryDirectory() as td:
        p = pathlib.Path(td)
        pack = p / "packs" / "mypak"
        _make_skill(pack, "my-skill")
        _make_journey(pack, extra_fm="journey_id: different-slug\n")
        # Overwrite the default JOURNEY.md — the extra_fm line dupes journey_id;
        # write a clean one manually with journey_id that differs from pack name
        skill_name = "my-skill"
        fm = f"""---
journey_id: different-slug
pack: mypak
scope: user
tagline: "Test journey"
contract:
  useItWhen: "test"
  youProvide: "input"
  youReceive: "output"
  yourDecisions: ["confirm"]
skills:
  - name: {skill_name}
    description: "A skill"
    humanTouches: 1
humanGates:
  - id: G1
    globalGate: null
    label: "Review"
    trigger: "after"
    duration: "5 min"
    whatToCheck: ["ok?"]
    whatGoodLooksLike: "great"
    whatBadLooksLike: "bad"
    consequence: "revise"
typicalSession:
  agentTurns: "3"
  humanTouches: 1
  wallClockMinutes: "15"
docsUrl: /guides/test/
packUrl: /packs/test/
---

{_DEFAULT_STAGES}
"""
        (pack / "JOURNEY.md").write_text(fm, encoding="utf-8")
        jd = p / "journeys"
        jd.mkdir()
        _pass("test_journey_id_differs_from_pack_name_valid", _run(p / "packs", jd))


def test_missing_journey_id() -> None:
    with tempfile.TemporaryDirectory() as td:
        p = pathlib.Path(td)
        pack = p / "packs" / "mypak"
        _make_skill(pack, "my-skill")
        skill_name = "my-skill"
        fm = f"""---
pack: mypak
scope: user
tagline: "No journey_id"
contract:
  useItWhen: "test"
  youProvide: "input"
  youReceive: "output"
  yourDecisions: ["confirm"]
skills:
  - name: {skill_name}
    description: "A skill"
    humanTouches: 1
humanGates: []
typicalSession:
  agentTurns: "3"
  humanTouches: 1
  wallClockMinutes: "15"
docsUrl: /guides/test/
packUrl: /packs/test/
---

{_DEFAULT_STAGES}
"""
        (pack / "JOURNEY.md").write_text(fm, encoding="utf-8")
        jd = p / "journeys"
        jd.mkdir()
        _fail("test_missing_journey_id", _run(p / "packs", jd), "journey_id")


def test_invalid_state_in_stage() -> None:
    with tempfile.TemporaryDirectory() as td:
        p = pathlib.Path(td)
        pack = p / "packs" / "mypak"
        _make_skill(pack, "my-skill")
        _make_journey(pack, stages=_STAGE_BOGUS_STATE)
        jd = p / "journeys"
        jd.mkdir()
        _fail("test_invalid_state_in_stage", _run(p / "packs", jd), "bogus")


def test_invalid_start_state() -> None:
    with tempfile.TemporaryDirectory() as td:
        p = pathlib.Path(td)
        pack = p / "packs" / "mypak"
        _make_skill(pack, "my-skill")
        _make_journey(pack, extra_fm="start_state: invalid-state\n")
        jd = p / "journeys"
        jd.mkdir()
        _fail("test_invalid_start_state", _run(p / "packs", jd), "start_state")


def test_invalid_end_state() -> None:
    with tempfile.TemporaryDirectory() as td:
        p = pathlib.Path(td)
        pack = p / "packs" / "mypak"
        _make_skill(pack, "my-skill")
        _make_journey(pack, extra_fm="end_state: invalid-state\n")
        jd = p / "journeys"
        jd.mkdir()
        _fail("test_invalid_end_state", _run(p / "packs", jd), "end_state")


def test_nonexistent_skill() -> None:
    with tempfile.TemporaryDirectory() as td:
        p = pathlib.Path(td)
        pack = p / "packs" / "mypak"
        _make_skill(pack, "my-skill")
        # JOURNEY.md references a skill that does not exist in .apm/skills/
        fm = """\
---
journey_id: mypak
pack: mypak
scope: user
tagline: "Test journey"
contract:
  useItWhen: "test"
  youProvide: "input"
  youReceive: "output"
  yourDecisions: ["confirm"]
skills:
  - name: nonexistent-skill
    description: "Ghost skill"
    humanTouches: 1
humanGates: []
typicalSession:
  agentTurns: "3"
  humanTouches: 1
  wallClockMinutes: "15"
docsUrl: /guides/test/
packUrl: /packs/test/
---

""" + _DEFAULT_STAGES
        (pack / "JOURNEY.md").write_text(fm, encoding="utf-8")
        jd = p / "journeys"
        jd.mkdir()
        _fail("test_nonexistent_skill", _run(p / "packs", jd), "nonexistent-skill")


def test_skill_count_mismatch() -> None:
    with tempfile.TemporaryDirectory() as td:
        p = pathlib.Path(td)
        pack = p / "packs" / "mypak"
        _make_skill(pack, "skill-a")
        # JOURNEY.md lists 2 skills but pack has only 1 directory
        fm = """\
---
journey_id: mypak
pack: mypak
scope: user
tagline: "Test journey"
contract:
  useItWhen: "test"
  youProvide: "input"
  youReceive: "output"
  yourDecisions: ["confirm"]
skills:
  - name: skill-a
    description: "Skill A"
    humanTouches: 1
  - name: skill-b
    description: "Skill B (not in pack)"
    humanTouches: 1
humanGates: []
typicalSession:
  agentTurns: "3"
  humanTouches: 1
  wallClockMinutes: "15"
docsUrl: /guides/test/
packUrl: /packs/test/
---

""" + _DEFAULT_STAGES
        (pack / "JOURNEY.md").write_text(fm, encoding="utf-8")
        jd = p / "journeys"
        jd.mkdir()
        # After removing count-parity: the failure is reference-validity (skill-b not in pack)
        _fail("test_skill_count_mismatch", _run(p / "packs", jd), "not found")


def test_journey_may_omit_pack_skills() -> None:
    """A primary journey listing a subset of pack skills must pass.

    Regression for the count-parity rule that was removed in Phase 2E:
    a journey should reference only the skills its stages use, not every
    skill in the pack.
    """
    with tempfile.TemporaryDirectory() as td:
        p = pathlib.Path(td)
        pack = p / "packs" / "bigpack"
        # Pack has three skills
        for skill in ("skill-a", "skill-b", "skill-c"):
            _make_skill(pack, skill)
        # JOURNEY.md lists only 2 of the 3 — a valid primary journey subset
        fm = """\
---
journey_id: bigpack
pack: bigpack
scope: user
tagline: "Test journey — primary subset"
contract:
  useItWhen: "test"
  youProvide: "input"
  youReceive: "output"
  yourDecisions: ["confirm"]
skills:
  - name: skill-a
    description: "First skill used by this journey"
    humanTouches: 1
  - name: skill-b
    description: "Second skill used by this journey"
    humanTouches: 1
humanGates: []
typicalSession:
  agentTurns: "3"
  humanTouches: 1
  wallClockMinutes: "15"
docsUrl: /guides/test/
packUrl: /packs/test/
---

""" + _DEFAULT_STAGES
        (pack / "JOURNEY.md").write_text(fm, encoding="utf-8")
        jd = p / "journeys"
        jd.mkdir()
        _pass("test_journey_may_omit_pack_skills", _run(p / "packs", jd))


def test_duplicate_journey_id() -> None:
    with tempfile.TemporaryDirectory() as td:
        p = pathlib.Path(td)
        # Two packs with the same journey_id
        for pack_name in ("pack-a", "pack-b"):
            pack = p / "packs" / pack_name
            _make_skill(pack, "skill-x")
            skill_name = "skill-x"
            fm = f"""\
---
journey_id: shared-id
pack: {pack_name}
scope: user
tagline: "Test"
contract:
  useItWhen: "test"
  youProvide: "input"
  youReceive: "output"
  yourDecisions: ["confirm"]
skills:
  - name: {skill_name}
    description: "A skill"
    humanTouches: 1
humanGates: []
typicalSession:
  agentTurns: "3"
  humanTouches: 1
  wallClockMinutes: "15"
docsUrl: /guides/test/
packUrl: /packs/test/
---

{_DEFAULT_STAGES}
"""
            (pack / "JOURNEY.md").write_text(fm, encoding="utf-8")
        jd = p / "journeys"
        jd.mkdir()
        _fail("test_duplicate_journey_id", _run(p / "packs", jd), "duplicate")


def test_dual_ownership_same_slug() -> None:
    with tempfile.TemporaryDirectory() as td:
        p = pathlib.Path(td)
        pack = p / "packs" / "mypak"
        _make_skill(pack, "my-skill")
        _make_journey(pack)
        jd = p / "journeys"
        jd.mkdir()
        # Central legacy file with same slug (no generated: true)
        (jd / "mypak.md").write_text("---\npack: mypak\n---\n", encoding="utf-8")
        _fail("test_dual_ownership_same_slug", _run(p / "packs", jd), "dual")


def test_dual_ownership_same_pack_diff_slug() -> None:
    with tempfile.TemporaryDirectory() as td:
        p = pathlib.Path(td)
        pack = p / "packs" / "mypak"
        _make_skill(pack, "my-skill")
        _make_journey(pack)  # journey_id: mypak
        jd = p / "journeys"
        jd.mkdir()
        # Central legacy file with DIFFERENT slug but same pack: field
        (jd / "other-slug.md").write_text(
            "---\npack: mypak\n---\n", encoding="utf-8"
        )
        _fail("test_dual_ownership_same_pack_diff_slug", _run(p / "packs", jd), "dual")


def test_generated_central_not_dual() -> None:
    with tempfile.TemporaryDirectory() as td:
        p = pathlib.Path(td)
        pack = p / "packs" / "mypak"
        _make_skill(pack, "my-skill")
        _make_journey(pack)
        jd = p / "journeys"
        jd.mkdir()
        # Central file with generated: true — not dual ownership
        (jd / "mypak.md").write_text(
            "---\ngenerated: true\npack: mypak\n---\n", encoding="utf-8"
        )
        _pass("test_generated_central_not_dual", _run(p / "packs", jd))


def test_write_stage_missing_decide() -> None:
    with tempfile.TemporaryDirectory() as td:
        p = pathlib.Path(td)
        pack = p / "packs" / "mypak"
        _make_skill(pack, "my-skill")
        _make_journey(pack, stages=_WRITE_STAGE_NO_DECIDE)
        jd = p / "journeys"
        jd.mkdir()
        _fail("test_write_stage_missing_decide", _run(p / "packs", jd), "You decide")


def test_decision_required_missing_decide() -> None:
    with tempfile.TemporaryDirectory() as td:
        p = pathlib.Path(td)
        pack = p / "packs" / "mypak"
        _make_skill(pack, "my-skill")
        _make_journey(pack, stages=_DECISION_REQUIRED_NO_DECIDE)
        jd = p / "journeys"
        jd.mkdir()
        _fail("test_decision_required_missing_decide", _run(p / "packs", jd), "You decide")


def test_missing_output_label() -> None:
    with tempfile.TemporaryDirectory() as td:
        p = pathlib.Path(td)
        pack = p / "packs" / "mypak"
        _make_skill(pack, "my-skill")
        _make_journey(pack, stages=_STAGE_NO_OUTPUT)
        jd = p / "journeys"
        jd.mkdir()
        _fail("test_missing_output_label", _run(p / "packs", jd), "Output")


def test_missing_state_label() -> None:
    with tempfile.TemporaryDirectory() as td:
        p = pathlib.Path(td)
        pack = p / "packs" / "mypak"
        _make_skill(pack, "my-skill")
        _make_journey(pack, stages=_STAGE_NO_STATE)
        jd = p / "journeys"
        jd.mkdir()
        _fail("test_missing_state_label", _run(p / "packs", jd), "State")


def test_pack_field_mismatch() -> None:
    with tempfile.TemporaryDirectory() as td:
        p = pathlib.Path(td)
        pack = p / "packs" / "mypak"
        _make_skill(pack, "my-skill")
        # pack field says "wrong-name" but directory is "mypak"
        fm = """\
---
journey_id: mypak
pack: wrong-name
scope: user
tagline: "Test journey"
contract:
  useItWhen: "test"
  youProvide: "input"
  youReceive: "output"
  yourDecisions: ["confirm"]
skills:
  - name: my-skill
    description: "A skill"
    humanTouches: 1
humanGates: []
typicalSession:
  agentTurns: "3"
  humanTouches: 1
  wallClockMinutes: "15"
docsUrl: /guides/test/
packUrl: /packs/test/
---

""" + _DEFAULT_STAGES
        (pack / "JOURNEY.md").write_text(fm, encoding="utf-8")
        jd = p / "journeys"
        jd.mkdir()
        _fail("test_pack_field_mismatch", _run(p / "packs", jd), "wrong-name")


def main() -> int:
    tests = [
        test_valid_journey_exits_0,
        test_journey_id_differs_from_pack_name_valid,
        test_missing_journey_id,
        test_invalid_state_in_stage,
        test_invalid_start_state,
        test_invalid_end_state,
        test_nonexistent_skill,
        test_skill_count_mismatch,
        test_journey_may_omit_pack_skills,
        test_duplicate_journey_id,
        test_dual_ownership_same_slug,
        test_dual_ownership_same_pack_diff_slug,
        test_generated_central_not_dual,
        test_write_stage_missing_decide,
        test_decision_required_missing_decide,
        test_missing_output_label,
        test_missing_state_label,
        test_pack_field_mismatch,
    ]
    for t in tests:
        t()
    print(f"\ntest-lint-pack-journeys: all {len(tests)} tests passed")
    return 0


if __name__ == "__main__":
    sys.exit(main())
