#!/usr/bin/env python3
"""Self-test for tools/llm-judge-cross-pack-eval.py (ini-003 Wave 4H).

Does NOT call the real Anthropic API. Tests:
  A — argument parsing: --root and --fixture-id flags are accepted
  B — fixture loading: loads cross-pack-fixtures.json from the real repo
  C — fixture filtering: --fixture-id selects the correct fixture
  D — fixture filtering: unknown --fixture-id exits 2
  E — no API key exits 2 with a clear message
  F — _build_user_prompt: includes expected content for golden_path fixture
  G — _parse_judge_response: parses PASS/FAIL verdicts correctly
  H — _parse_judge_response: handles FAIL verdict with rationale
  I — mocked API: all-pass run exits 0, summary mentions 'passed'
  J — mocked API: fixture with FAIL exits 1, ::warning prefix in output
"""

from __future__ import annotations

import importlib.util
import io
import json
import os
import pathlib
import subprocess
import sys
import types
import unittest.mock as mock

REPO_ROOT = pathlib.Path(__file__).resolve().parent.parent
TOOL = REPO_ROOT / "tools" / "llm-judge-cross-pack-eval.py"
FIXTURES_PATH = (
    REPO_ROOT
    / "packs/experience-design/.apm/evals/cross-pack-fixtures.json"
)


# ── Load the module under test without running main() ─────────────────────────

def _load_tool(name: str = "llm_judge_cross_pack_eval") -> types.ModuleType:
    spec = importlib.util.spec_from_file_location(name, TOOL)
    mod = importlib.util.module_from_spec(spec)  # type: ignore[arg-type]
    spec.loader.exec_module(mod)  # type: ignore[union-attr]
    return mod


_tool = _load_tool()


# ── Helpers ────────────────────────────────────────────────────────────────────

def fail(label: str, msg: str, detail: str = "") -> None:
    print(f"✖ {label}: {msg}", file=sys.stderr)
    if detail:
        print("---", file=sys.stderr)
        print(detail[:600], file=sys.stderr)
        print("---", file=sys.stderr)
    sys.exit(1)


def _run_tool(*extra_args: str, env: dict | None = None) -> tuple[int, str]:
    """Run the tool as a subprocess and return (exit_code, combined_output)."""
    run_env = os.environ.copy()
    run_env.pop("ANTHROPIC_API_KEY", None)
    if env:
        run_env.update(env)
    result = subprocess.run(
        [sys.executable, str(TOOL), *extra_args],
        capture_output=True,
        text=True,
        env=run_env,
    )
    return result.returncode, result.stdout + result.stderr


def _run_main_mocked(
    response_text: str,
    extra_argv: list[str] | None = None,
) -> tuple[int, str]:
    """Run main() with a mocked Anthropic client; return (exit_code, stdout)."""
    mock_message = mock.MagicMock()
    mock_message.content = [mock.MagicMock(text=response_text)]
    mock_client = mock.MagicMock()
    mock_client.messages.create.return_value = mock_message
    mock_anthropic_module = mock.MagicMock()
    mock_anthropic_module.Anthropic.return_value = mock_client

    argv = [str(TOOL), "--root", str(REPO_ROOT)]
    if extra_argv:
        argv.extend(extra_argv)

    captured = io.StringIO()
    mod = _load_tool(f"llm_judge_mock_{id(response_text)}")

    # Inject single fixture so the run is deterministic and fast.
    fixtures_data = json.loads(FIXTURES_PATH.read_text(encoding="utf-8"))
    single = [("golden_path", fixtures_data["golden_path"][0])]
    mod._collect_fixtures = lambda f, fid: single  # type: ignore[assignment]

    with (
        mock.patch.dict(os.environ, {"ANTHROPIC_API_KEY": "test-key-not-real"}),
        mock.patch.dict(sys.modules, {"anthropic": mock_anthropic_module}),
        mock.patch("sys.argv", argv),
        mock.patch("sys.stdout", captured),
    ):
        exit_code = mod.main()

    return exit_code, captured.getvalue()


# ── Tests ──────────────────────────────────────────────────────────────────────

def test_a_argument_parsing() -> None:
    label = "A (argument parsing: --root and --fixture-id accepted; exits 2 for missing API key)"
    # With a valid fixture id but no API key, the tool should exit 2 (after
    # fixture validation passes).
    code, out = _run_tool("--root", str(REPO_ROOT), "--fixture-id", "gp-01")
    if code != 2:
        fail(label, f"expected exit 2 (no API key), got {code}", out)
    if "ANTHROPIC_API_KEY" not in out:
        fail(label, "expected API key message in output", out)
    print(f"✓ {label}")


def test_b_fixture_loading() -> None:
    label = "B (fixture loading: fixtures file exists and is valid JSON)"
    if not FIXTURES_PATH.exists():
        fail(label, f"fixture file not found at {FIXTURES_PATH}")
    try:
        data = json.loads(FIXTURES_PATH.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        fail(label, f"fixture file is not valid JSON: {exc}")
    for section in ["golden_path", "multi_intent_routing", "boundary_violations", "weak_regression"]:
        if section not in data:
            fail(label, f"expected section '{section}' not found in fixture file")
    print(f"✓ {label}")


def test_c_fixture_filtering_known_id() -> None:
    label = "C (_collect_fixtures: --fixture-id gp-01 returns exactly one fixture)"
    fixtures = json.loads(FIXTURES_PATH.read_text(encoding="utf-8"))
    results = _tool._collect_fixtures(fixtures, "gp-01")
    if len(results) != 1:
        fail(label, f"expected 1 fixture, got {len(results)}")
    section, fixture = results[0]
    if fixture.get("id") != "gp-01":
        fail(label, f"expected id 'gp-01', got {fixture.get('id')!r}")
    if section != "golden_path":
        fail(label, f"expected section 'golden_path', got {section!r}")
    print(f"✓ {label}")


def test_d_fixture_filtering_unknown_id() -> None:
    label = "D (unknown --fixture-id exits 2 with error message)"
    code, out = _run_tool("--root", str(REPO_ROOT), "--fixture-id", "does-not-exist-xyz")
    if code != 2:
        fail(label, f"expected exit 2, got {code}", out)
    if "does-not-exist-xyz" not in out:
        fail(label, "expected unknown id in error output", out)
    print(f"✓ {label}")


def test_e_no_api_key_exits_2() -> None:
    label = "E (no ANTHROPIC_API_KEY exits 2 with clear message)"
    # Pass a valid fixture id so we get past fixture validation to the key check.
    code, out = _run_tool("--root", str(REPO_ROOT), "--fixture-id", "gp-01")
    if code != 2:
        fail(label, f"expected exit 2, got {code}", out)
    if "ANTHROPIC_API_KEY" not in out:
        fail(label, "expected ANTHROPIC_API_KEY mention in error output", out)
    print(f"✓ {label}")


def test_f_build_user_prompt() -> None:
    label = "F (_build_user_prompt: includes fixture id, name, skill sequence, handoff criteria)"
    fixtures = json.loads(FIXTURES_PATH.read_text(encoding="utf-8"))
    fixture = fixtures["golden_path"][0]  # gp-01
    prompt = _tool._build_user_prompt("golden_path", fixture)
    if "gp-01" not in prompt:
        fail(label, "expected fixture id 'gp-01' in prompt")
    if "Public marketing" not in prompt:
        fail(label, "expected fixture name in prompt")
    if "creative-direction" not in prompt:
        fail(label, "expected skill name 'creative-direction' in prompt")
    if "handoff" not in prompt.lower():
        fail(label, "expected handoff criteria in prompt")
    print(f"✓ {label}")


def test_g_parse_judge_response_all_pass() -> None:
    label = "G (_parse_judge_response: parses three PASS verdicts)"
    response = (
        "DEC coherence: PASS -- Handoff criteria align with DEC framework.\n"
        "Persona consistency: PASS -- Persona framing is consistent throughout.\n"
        "Handoff completeness: PASS -- All required fields are described.\n"
    )
    verdicts = _tool._parse_judge_response(response)
    for dim in ["DEC coherence", "Persona consistency", "Handoff completeness"]:
        if dim not in verdicts:
            fail(label, f"dimension '{dim}' not parsed")
        verdict, rationale = verdicts[dim]
        if verdict != "PASS":
            fail(label, f"expected PASS for '{dim}', got {verdict!r}")
        if not rationale:
            fail(label, f"expected rationale for '{dim}'")
    print(f"✓ {label}")


def test_h_parse_judge_response_fail() -> None:
    label = "H (_parse_judge_response: parses FAIL verdict with rationale)"
    response = (
        "DEC coherence: PASS -- All criteria align.\n"
        "Persona consistency: FAIL -- Persona is not carried forward to outputs.\n"
        "Handoff completeness: PASS -- All fields present.\n"
    )
    verdicts = _tool._parse_judge_response(response)
    verdict, rationale = verdicts.get("Persona consistency", ("?", ""))
    if verdict != "FAIL":
        fail(label, f"expected FAIL for 'Persona consistency', got {verdict!r}")
    if not rationale:
        fail(label, "expected rationale to be non-empty")
    print(f"✓ {label}")


def test_i_summary_all_pass() -> None:
    label = "I (mocked API: all-pass run exits 0, summary mentions 'passed')"
    response_text = (
        "DEC coherence: PASS -- Criteria are internally consistent.\n"
        "Persona consistency: PASS -- Persona framing is maintained.\n"
        "Handoff completeness: PASS -- All fields described.\n"
    )
    exit_code, output = _run_main_mocked(response_text, ["--fixture-id", "gp-01"])
    if exit_code != 0:
        fail(label, f"expected exit 0, got {exit_code}", output)
    if "passed" not in output.lower():
        fail(label, "expected 'passed' in summary output", output)
    print(f"✓ {label}")


def test_j_summary_with_failure() -> None:
    label = "J (mocked API: fixture with FAIL exits 1, ::warning prefix in output)"
    response_text = (
        "DEC coherence: PASS -- Criteria are consistent.\n"
        "Persona consistency: FAIL -- No persona framing in outputs.\n"
        "Handoff completeness: PASS -- All fields present.\n"
    )
    exit_code, output = _run_main_mocked(response_text, ["--fixture-id", "gp-01"])
    if exit_code != 1:
        fail(label, f"expected exit 1, got {exit_code}", output)
    if "::warning" not in output:
        fail(label, "expected '::warning' prefix in failure output", output)
    print(f"✓ {label}")


def main() -> int:
    print("Running test-llm-judge-cross-pack-eval.py...")
    test_a_argument_parsing()
    test_b_fixture_loading()
    test_c_fixture_filtering_known_id()
    test_d_fixture_filtering_unknown_id()
    test_e_no_api_key_exits_2()
    test_f_build_user_prompt()
    test_g_parse_judge_response_all_pass()
    test_h_parse_judge_response_fail()
    test_i_summary_all_pass()
    test_j_summary_with_failure()
    print("\n✓ All tests passed.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
