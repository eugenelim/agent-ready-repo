#!/usr/bin/env python3
"""Self-test for the sibling lint-first-value-contract.py.

Builds fixture packs in a tempdir and runs the linter as a subprocess
against `python tools/lint-first-value-contract.py --root <dir>` —
the same invocation the CI gate uses. Covers the positive path (valid
Level A and Level B packs) and each enforced negative case from the
Testing Strategy in docs/specs/portfolio-pack-first-value-contract/spec.md.
"""

from __future__ import annotations

import subprocess
import sys
import tempfile
from pathlib import Path

LINTER = Path(__file__).resolve().parent / "lint-first-value-contract.py"

FAILURES: list[str] = []


def expect(cond: bool, msg: str) -> None:
    if not cond:
        FAILURES.append(msg)


def run(root: Path, *extra: str) -> tuple[int, str, str]:
    proc = subprocess.run(
        [sys.executable, str(LINTER), "--root", str(root), *extra],
        capture_output=True, text=True,
    )
    return proc.returncode, proc.stdout, proc.stderr


def write(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def make_pack(
    root: Path,
    name: str,
    first_value: dict | None,
    *,
    allowed_adapters: list[str] | None = None,
    version: str = "0.1.0",
) -> None:
    lines = [
        "[pack]",
        f'name = "{name}"',
        f'version = "{version}"',
    ]
    if allowed_adapters is not None:
        adapter_str = ", ".join(f'"{a}"' for a in allowed_adapters)
        lines += [
            "\n[pack.install]",
            'default-scope = "user"',
            'allowed-scopes = ["user"]',
            f"allowed-adapters = [{adapter_str}]",
        ]
    if first_value is not None:
        lines.append("\n[pack.first-value]")
        for k, v in first_value.items():
            if isinstance(v, bool):
                lines.append(f"{k} = {'true' if v else 'false'}")
            elif isinstance(v, list):
                items = ", ".join(f'"{i}"' for i in v)
                lines.append(f"{k} = [{items}]")
            else:
                escaped = str(v).replace('"', '\\"')
                lines.append(f'{k} = "{escaped}"')
    write(root / "packs" / name / "pack.toml", "\n".join(lines) + "\n")


def _valid_level_a() -> dict:
    return {
        "audience-posture": "technical",
        "surfaces": ["claude-code"],
        "prerequisites": [],
        "verification": "Run the skill and confirm output.",
        "recovery": "Re-install the pack and retry.",
    }


def _valid_level_b() -> dict:
    fv = _valid_level_a()
    fv.update({
        "level-b": True,
        "starter-task": "Do the first useful thing",
        "starter-prompt": "Show me something useful about this project.",
        "expected-result": "A file with useful content.",
        "next-action": "Share the result with your team.",
    })
    return fv


# ── Positive fixtures ────────────────────────────────────────────────────────


def test_level_a_valid() -> None:
    """Level A pack with all required fields → exit 0."""
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        make_pack(root, "core", _valid_level_a(), allowed_adapters=["claude-code"])
        rc, out, err = run(root)
        expect(rc == 0, f"test_level_a_valid: expected exit 0, got {rc}\nstderr: {err}")


def test_level_b_valid() -> None:
    """Level B pack (level-b = true) with all required fields → exit 0."""
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        make_pack(root, "architect", _valid_level_b(), allowed_adapters=["claude-code"])
        rc, out, err = run(root)
        expect(rc == 0, f"test_level_b_valid: expected exit 0, got {rc}\nstderr: {err}")


def test_level_b_writes_to_repo_valid() -> None:
    """Level B pack with writes-to-repo = true + safety-gate present → exit 0."""
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        fv = _valid_level_b()
        fv["writes-to-repo"] = True
        fv["safety-gate"] = "The skill shows a preview before writing."
        make_pack(root, "governance-extras", fv, allowed_adapters=["claude-code"])
        rc, out, err = run(root)
        expect(rc == 0, f"test_level_b_writes_to_repo_valid: expected exit 0, got {rc}\nstderr: {err}")


def test_tutorial_declared_file_exists() -> None:
    """tutorial field declared and target file exists → exit 0."""
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        fv = _valid_level_b()
        fv["tutorial"] = "docs/guides/architect/tutorials/first-session.md"
        make_pack(root, "architect", fv, allowed_adapters=["claude-code"])
        write(root / "docs/guides/architect/tutorials/first-session.md", "# Tutorial\n")
        rc, out, err = run(root)
        expect(rc == 0, f"test_tutorial_declared_file_exists: expected exit 0, got {rc}\nstderr: {err}")


def test_no_packs_directory() -> None:
    """packs/ absent → exit 0 (nothing to lint, same as lint-profiles.py)."""
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        rc, out, err = run(root)
        expect(rc == 0, f"test_no_packs_directory: expected exit 0, got {rc}\nstderr: {err}")


# ── Negative fixtures ────────────────────────────────────────────────────────


def test_missing_first_value_section() -> None:
    """Pack with no [pack.first-value] section at all → exit 1 with pack name."""
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        make_pack(root, "core", None, allowed_adapters=["claude-code"])
        rc, out, err = run(root)
        expect(rc == 1, f"test_missing_first_value_section: expected exit 1, got {rc}\nstderr: {err}")
        expect("core" in err, f"test_missing_first_value_section: pack name not in stderr\nstderr: {err}")


def test_missing_audience_posture() -> None:
    """audience-posture absent (section present, field missing) → exit 1."""
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        fv = _valid_level_a()
        del fv["audience-posture"]
        make_pack(root, "core", fv, allowed_adapters=["claude-code"])
        rc, out, err = run(root)
        expect(rc == 1, f"test_missing_audience_posture: expected exit 1, got {rc}\nstderr: {err}")


def test_invalid_audience_posture() -> None:
    """audience-posture = 'executive' (bad vocabulary) → exit 1."""
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        fv = _valid_level_a()
        fv["audience-posture"] = "executive"
        make_pack(root, "core", fv, allowed_adapters=["claude-code"])
        rc, out, err = run(root)
        expect(rc == 1, f"test_invalid_audience_posture: expected exit 1, got {rc}\nstderr: {err}")


def test_surfaces_empty_list() -> None:
    """surfaces = [] (zero entries) → exit 1."""
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        fv = _valid_level_a()
        fv["surfaces"] = []
        make_pack(root, "core", fv, allowed_adapters=["claude-code"])
        rc, out, err = run(root)
        expect(rc == 1, f"test_surfaces_empty_list: expected exit 1, got {rc}\nstderr: {err}")


def test_prerequisite_entry_too_long() -> None:
    """A prerequisites entry > 80 chars → exit 1."""
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        fv = _valid_level_a()
        fv["prerequisites"] = ["x" * 81]
        make_pack(root, "core", fv, allowed_adapters=["claude-code"])
        rc, out, err = run(root)
        expect(rc == 1, f"test_prerequisite_entry_too_long: expected exit 1, got {rc}\nstderr: {err}")


def test_verification_too_long() -> None:
    """verification > 160 chars → exit 1."""
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        fv = _valid_level_a()
        fv["verification"] = "x" * 161
        make_pack(root, "core", fv, allowed_adapters=["claude-code"])
        rc, out, err = run(root)
        expect(rc == 1, f"test_verification_too_long: expected exit 1, got {rc}\nstderr: {err}")


def test_recovery_too_long() -> None:
    """recovery > 300 chars → exit 1."""
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        fv = _valid_level_a()
        fv["recovery"] = "x" * 301
        make_pack(root, "core", fv, allowed_adapters=["claude-code"])
        rc, out, err = run(root)
        expect(rc == 1, f"test_recovery_too_long: expected exit 1, got {rc}\nstderr: {err}")


def test_level_b_missing_starter_task() -> None:
    """level-b = true but starter-task absent → exit 1."""
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        fv = _valid_level_b()
        del fv["starter-task"]
        make_pack(root, "architect", fv, allowed_adapters=["claude-code"])
        rc, out, err = run(root)
        expect(rc == 1, f"test_level_b_missing_starter_task: expected exit 1, got {rc}\nstderr: {err}")


def test_starter_task_too_long() -> None:
    """starter-task > 120 chars → exit 1."""
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        fv = _valid_level_b()
        fv["starter-task"] = "x" * 121
        make_pack(root, "architect", fv, allowed_adapters=["claude-code"])
        rc, out, err = run(root)
        expect(rc == 1, f"test_starter_task_too_long: expected exit 1, got {rc}\nstderr: {err}")


def test_starter_prompt_with_placeholder() -> None:
    """starter-prompt contains <word> token (pattern <[a-zA-Z][a-zA-Z0-9 _-]*>) → exit 1."""
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        fv = _valid_level_b()
        fv["starter-prompt"] = "Show me <your topic> in this project."
        make_pack(root, "architect", fv, allowed_adapters=["claude-code"])
        rc, out, err = run(root)
        expect(rc == 1, f"test_starter_prompt_with_placeholder: expected exit 1, got {rc}\nstderr: {err}")


def test_starter_prompt_too_long() -> None:
    """starter-prompt > 500 chars → exit 1."""
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        fv = _valid_level_b()
        fv["starter-prompt"] = "x" * 501
        make_pack(root, "architect", fv, allowed_adapters=["claude-code"])
        rc, out, err = run(root)
        expect(rc == 1, f"test_starter_prompt_too_long: expected exit 1, got {rc}\nstderr: {err}")


def test_expected_result_too_long() -> None:
    """expected-result > 200 chars → exit 1."""
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        fv = _valid_level_b()
        fv["expected-result"] = "x" * 201
        make_pack(root, "architect", fv, allowed_adapters=["claude-code"])
        rc, out, err = run(root)
        expect(rc == 1, f"test_expected_result_too_long: expected exit 1, got {rc}\nstderr: {err}")


def test_next_action_too_long() -> None:
    """next-action > 120 chars → exit 1."""
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        fv = _valid_level_b()
        fv["next-action"] = "x" * 121
        make_pack(root, "architect", fv, allowed_adapters=["claude-code"])
        rc, out, err = run(root)
        expect(rc == 1, f"test_next_action_too_long: expected exit 1, got {rc}\nstderr: {err}")


def test_writes_to_repo_missing_safety_gate() -> None:
    """writes-to-repo = true, safety-gate absent → exit 1."""
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        fv = _valid_level_b()
        fv["writes-to-repo"] = True
        make_pack(root, "governance-extras", fv, allowed_adapters=["claude-code"])
        rc, out, err = run(root)
        expect(rc == 1, f"test_writes_to_repo_missing_safety_gate: expected exit 1, got {rc}\nstderr: {err}")


def test_safety_gate_too_long() -> None:
    """safety-gate > 200 chars → exit 1."""
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        fv = _valid_level_b()
        fv["writes-to-repo"] = True
        fv["safety-gate"] = "x" * 201
        make_pack(root, "governance-extras", fv, allowed_adapters=["claude-code"])
        rc, out, err = run(root)
        expect(rc == 1, f"test_safety_gate_too_long: expected exit 1, got {rc}\nstderr: {err}")


def test_surfaces_not_subset_of_allowed_adapters() -> None:
    """surfaces contains adapter not in pack's allowed-adapters → exit 1."""
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        fv = _valid_level_a()
        fv["surfaces"] = ["claude-code", "kiro-ide"]  # kiro-ide not in allowed
        make_pack(root, "core", fv, allowed_adapters=["claude-code"])
        rc, out, err = run(root)
        expect(rc == 1, f"test_surfaces_not_subset_of_allowed_adapters: expected exit 1, got {rc}\nstderr: {err}")


def test_tutorial_declared_file_missing() -> None:
    """tutorial field declared but target file absent → exit 1."""
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        fv = _valid_level_b()
        fv["tutorial"] = "docs/guides/architect/tutorials/nonexistent.md"
        make_pack(root, "architect", fv, allowed_adapters=["claude-code"])
        rc, out, err = run(root)
        expect(rc == 1, f"test_tutorial_declared_file_missing: expected exit 1, got {rc}\nstderr: {err}")


def test_tutorial_declared_not_md() -> None:
    """tutorial field points at a .txt file (wrong suffix) → exit 1."""
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        fv = _valid_level_b()
        fv["tutorial"] = "docs/guides/architect/tutorials/first-session.txt"
        make_pack(root, "architect", fv, allowed_adapters=["claude-code"])
        write(root / "docs/guides/architect/tutorials/first-session.txt", "# Not a markdown file\n")
        rc, out, err = run(root)
        expect(rc == 1, f"test_tutorial_declared_not_md: expected exit 1, got {rc}\nstderr: {err}")


def test_tutorial_declared_is_directory() -> None:
    """tutorial field points at a directory (not a file) → exit 1."""
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        fv = _valid_level_b()
        fv["tutorial"] = "docs/guides/architect/tutorials"
        make_pack(root, "architect", fv, allowed_adapters=["claude-code"])
        (root / "docs/guides/architect/tutorials").mkdir(parents=True, exist_ok=True)
        rc, out, err = run(root)
        expect(rc == 1, f"test_tutorial_declared_is_directory: expected exit 1, got {rc}\nstderr: {err}")


def main() -> int:
    tests = [
        test_level_a_valid,
        test_level_b_valid,
        test_level_b_writes_to_repo_valid,
        test_tutorial_declared_file_exists,
        test_no_packs_directory,
        test_missing_first_value_section,
        test_missing_audience_posture,
        test_invalid_audience_posture,
        test_surfaces_empty_list,
        test_prerequisite_entry_too_long,
        test_verification_too_long,
        test_recovery_too_long,
        test_level_b_missing_starter_task,
        test_starter_task_too_long,
        test_starter_prompt_with_placeholder,
        test_starter_prompt_too_long,
        test_expected_result_too_long,
        test_next_action_too_long,
        test_writes_to_repo_missing_safety_gate,
        test_safety_gate_too_long,
        test_surfaces_not_subset_of_allowed_adapters,
        test_tutorial_declared_file_missing,
        test_tutorial_declared_not_md,
        test_tutorial_declared_is_directory,
    ]
    for fn in tests:
        fn()
    if FAILURES:
        for f in FAILURES:
            print(f"FAIL: {f}", file=sys.stderr)
        print(f"\n{len(FAILURES)} failure(s) / {len(tests)} test(s).", file=sys.stderr)
        return 1
    print(f"{len(tests)} test(s) passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
