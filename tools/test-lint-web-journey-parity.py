#!/usr/bin/env python3
"""Self-test for lint-web-journey-parity.py.

Uses WJP_JOURNEY_DIR / WJP_PACKS_DIR env-override (fixture mode) to run
the linter against controlled fixture trees rather than the real repo.

Exit 0 when all assertions pass; exit 1 on the first failure.
"""

from __future__ import annotations

import os
import pathlib
import subprocess
import sys
import tempfile


_SCRIPT = pathlib.Path(__file__).parent / "lint-web-journey-parity.py"


def _run(
    journey_dir: pathlib.Path,
    packs_dir: pathlib.Path,
    profiles_dir: pathlib.Path | None = None,
) -> subprocess.CompletedProcess[str]:
    env = {**os.environ, "WJP_JOURNEY_DIR": str(journey_dir), "WJP_PACKS_DIR": str(packs_dir)}
    if profiles_dir is not None:
        env["WJP_PROFILES_DIR"] = str(profiles_dir)
    return subprocess.run(
        [sys.executable, str(_SCRIPT)],
        capture_output=True, text=True, env=env, check=False,
    )


def _make_journey(d: pathlib.Path, filename: str, pack: str, skill_names: list[str]) -> None:
    skills_block = "\n".join(
        f"  - name: {name}\n    description: \"Test skill.\"\n    humanTouches: 0"
        for name in skill_names
    )
    (d / filename).write_text(
        f"---\npack: {pack}\nscope: user\nskills:\n{skills_block}\n---\n"
    )


def _make_pack_skills(packs_dir: pathlib.Path, pack: str, skill_names: list[str]) -> None:
    skills_root = packs_dir / pack / ".apm" / "skills"
    skills_root.mkdir(parents=True, exist_ok=True)
    for name in skill_names:
        (skills_root / name).mkdir(exist_ok=True)


def _assert(condition: bool, msg: str) -> None:
    if not condition:
        print(f"FAIL: {msg}", file=sys.stderr)
        sys.exit(1)


def test_all_in_parity() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        j = pathlib.Path(tmp) / "journeys"
        p = pathlib.Path(tmp) / "packs"
        j.mkdir()
        _make_journey(j, "alpha.md", "alpha", ["skill-a", "skill-b"])
        _make_pack_skills(p, "alpha", ["skill-a", "skill-b"])
        r = _run(j, p)
        _assert(r.returncode == 0, f"expected exit 0 for in-parity case; got {r.returncode}\n{r.stderr}")


def test_drift_detected() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        j = pathlib.Path(tmp) / "journeys"
        p = pathlib.Path(tmp) / "packs"
        j.mkdir()
        _make_journey(j, "alpha.md", "alpha", ["skill-a"])
        _make_pack_skills(p, "alpha", ["skill-a", "skill-b"])
        r = _run(j, p)
        _assert(r.returncode == 1, f"expected exit 1 for drifted case; got {r.returncode}")
        _assert("drift" in r.stderr.lower(), f"expected drift message in stderr; got:\n{r.stderr}")


def test_missing_pack_field() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        j = pathlib.Path(tmp) / "journeys"
        p = pathlib.Path(tmp) / "packs"
        j.mkdir()
        (j / "broken.md").write_text("---\nscope: user\nskills:\n  - name: foo\n    humanTouches: 0\n---\n")
        r = _run(j, p)
        _assert(r.returncode == 1, f"expected exit 1 when pack: field is absent; got {r.returncode}")


def test_missing_skills_dir() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        j = pathlib.Path(tmp) / "journeys"
        p = pathlib.Path(tmp) / "packs"
        j.mkdir()
        _make_journey(j, "no-pack.md", "ghost-pack", ["skill-a"])
        r = _run(j, p)
        _assert(r.returncode == 1, f"expected exit 1 when pack directory is absent; got {r.returncode}")


def test_profile_page_skipped() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        j = pathlib.Path(tmp) / "journeys"
        p = pathlib.Path(tmp) / "packs"
        pr = pathlib.Path(tmp) / "profiles"
        j.mkdir()
        pr.mkdir()
        _make_journey(j, "my-profile.md", "my-profile", [])
        (pr / "my-profile.toml").write_text("scope = \"user\"\n")
        _make_journey(j, "real.md", "real-pack", ["s1"])
        _make_pack_skills(p, "real-pack", ["s1"])
        r = _run(j, p, pr)
        _assert(r.returncode == 0, f"expected exit 0 when profile page is present; got {r.returncode}\n{r.stderr}")
        _assert("my-profile" not in r.stderr, f"profile page should not appear in stderr; got:\n{r.stderr}")


def test_multiple_journeys_one_drifted() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        j = pathlib.Path(tmp) / "journeys"
        p = pathlib.Path(tmp) / "packs"
        j.mkdir()
        _make_journey(j, "good.md", "good-pack", ["s1", "s2"])
        _make_pack_skills(p, "good-pack", ["s1", "s2"])
        _make_journey(j, "bad.md", "bad-pack", ["s1"])
        _make_pack_skills(p, "bad-pack", ["s1", "s2", "s3"])
        r = _run(j, p)
        _assert(r.returncode == 1, f"expected exit 1 when one of several journeys drifts; got {r.returncode}")
        _assert("bad.md" in r.stderr, f"expected drifted file named in stderr; got:\n{r.stderr}")
        _assert("good.md" not in r.stderr, f"expected clean file absent from stderr; got:\n{r.stderr}")


def main() -> None:
    tests = [
        test_all_in_parity,
        test_drift_detected,
        test_missing_pack_field,
        test_missing_skills_dir,
        test_profile_page_skipped,
        test_multiple_journeys_one_drifted,
    ]
    for t in tests:
        t()
        print(f"  ok: {t.__name__}")
    print(f"test-lint-web-journey-parity: all {len(tests)} tests passed")


if __name__ == "__main__":
    main()
