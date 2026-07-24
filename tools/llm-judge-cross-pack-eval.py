#!/usr/bin/env python3
"""LLM judge pass for cross-pack XD eval fixtures (ini-003 Wave 4H / spec/cross-pack-experience-eval).

Advisory complement to the deterministic check-xd-chain.py checker.
Covers semantic invariants the deterministic checker cannot catch:

  1. DEC section coherence   — chain skill output sections are internally
                               consistent with one another across the chain
  2. Persona consistency     — strategy-level persona framing (from
                               journey-mapping, creative-direction) carries
                               through coherently to experience-design outputs
  3. Handoff completeness    — all expected fields described in
                               handoff_completeness_criteria are present and
                               sufficient for a practitioner to move forward

This tool is ADVISORY ONLY and does NOT gate CI on its own (exit 0 means all
judged fixtures passed; it is never a mandatory PR gate). It calls the
Anthropic Messages API; do not invoke in unattended CI without explicit API
cost controls.

Usage:
    python3 tools/llm-judge-cross-pack-eval.py [--root .] [--fixture-id <id>]

Flags:
    --root <dir>         Repo root (default: git toplevel or CWD)
    --fixture-id <id>    Run only the fixture with this id (e.g. gp-01)

Exit codes:
  0 — all evaluated fixtures pass (advisory)
  1 — at least one fixture failed the judge
  2 — tool error (missing API key, unreadable fixture file, invalid root)

Environment:
  ANTHROPIC_API_KEY — required; the tool exits 2 if absent
  ANTHROPIC_MODEL   — override the judge model (default: claude-haiku-4-5)
"""

from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
from pathlib import Path
from typing import Any


# ── Configuration ─────────────────────────────────────────────────────────────

FIXTURES_REL = "packs/experience-design/.apm/evals/cross-pack-fixtures.json"

# All fixture sections that carry judge-relevant fields.
FIXTURE_SECTIONS = ["golden_path", "multi_intent_routing", "boundary_violations", "weak_regression"]

# Default judge model — haiku-class for cost efficiency on an advisory pass.
DEFAULT_MODEL = "claude-haiku-4-5"

# System prompt for the semantic judge.
JUDGE_SYSTEM = """\
You are an expert experience-design (XD) chain evaluator. You assess whether
a described cross-pack XD skill-chain scenario is semantically coherent and
complete. Given a fixture that describes a scenario (including expected skill
sequence, handoff criteria, and coherence indicators), evaluate three dimensions:

1. DEC coherence — Are the handoff_completeness_criteria internally consistent
   with the Digital Experience Contract (DEC) framework and with one another?
   Do adjacent skills' input/output descriptions align?

2. Persona consistency — Does the scenario maintain consistent persona framing
   from strategy inputs (e.g. journey-mapping, creative-direction) through to
   experience-design outputs? Are the coherence_indicators persona-aware?

3. Handoff completeness — Are all required handoff fields described for every
   skill transition in the expected sequence? Would a practitioner following
   this chain have sufficient input at each step?

Respond with EXACTLY these three lines (no other text):
  DEC coherence: PASS -- <one concise sentence>
  Persona consistency: PASS -- <one concise sentence>
  Handoff completeness: PASS -- <one concise sentence>

Replace PASS with FAIL if the dimension has a problem. Be specific.
"""


# ── Helpers ───────────────────────────────────────────────────────────────────

def _repo_root(root_arg: str | None) -> Path:
    if root_arg:
        p = Path(root_arg).resolve()
        if not p.is_dir():
            print(f"error: --root {root_arg!r} is not a directory", file=sys.stderr)
            sys.exit(2)
        return p
    result = subprocess.run(
        ["git", "rev-parse", "--show-toplevel"],
        capture_output=True, text=True, check=False,
    )
    if result.returncode == 0 and result.stdout.strip():
        return Path(result.stdout.strip())
    return Path.cwd()


def _load_fixtures(root: Path) -> dict[str, Any]:
    fixtures_path = root / FIXTURES_REL
    try:
        return json.loads(fixtures_path.read_text(encoding="utf-8"))
    except FileNotFoundError:
        print(f"error: fixture file not found at {fixtures_path}", file=sys.stderr)
        sys.exit(2)
    except json.JSONDecodeError as exc:
        print(f"error: invalid JSON in {fixtures_path}: {exc}", file=sys.stderr)
        sys.exit(2)


def _collect_fixtures(
    fixtures: dict[str, Any], fixture_id: str | None
) -> list[tuple[str, dict[str, Any]]]:
    """Return (section_type, fixture_dict) pairs, optionally filtered by id."""
    results: list[tuple[str, dict[str, Any]]] = []
    for section in FIXTURE_SECTIONS:
        for entry in fixtures.get(section, []):
            if fixture_id is None or entry.get("id") == fixture_id:
                results.append((section, entry))
    if fixture_id and not results:
        print(f"error: no fixture with id {fixture_id!r} found", file=sys.stderr)
        sys.exit(2)
    return results


def _build_user_prompt(section: str, fixture: dict[str, Any]) -> str:
    """Construct the judge prompt for a single fixture."""
    parts: list[str] = []
    parts.append(f"Fixture id: {fixture.get('id', '?')}")
    parts.append(f"Fixture type: {section}")
    parts.append(f"Name: {fixture.get('name', '?')}")

    if scenario := fixture.get("scenario"):
        parts.append(f"\nScenario:\n{scenario}")

    if description := fixture.get("description"):
        parts.append(f"\nDescription:\n{description}")

    if seq := fixture.get("expected_skill_sequence"):
        parts.append("\nExpected skill sequence:\n" + " -> ".join(seq))

    if routing := fixture.get("expected_routing"):
        routing_lines = "\n".join(
            f"  {r['skill']}: {r['role']}" for r in routing
        )
        parts.append(f"\nExpected routing:\n{routing_lines}")

    if criteria := fixture.get("handoff_completeness_criteria"):
        parts.append("\nHandoff completeness criteria:")
        for c in criteria:
            parts.append(f"  - {c}")

    if indicators := fixture.get("coherence_indicators"):
        parts.append("\nCoherence indicators:")
        for i in indicators:
            parts.append(f"  - {i}")

    if persona := fixture.get("persona_lens"):
        parts.append(f"\nPersona lens:\n{persona}")

    if failure_mode := fixture.get("failure_mode"):
        parts.append(f"\nFailure mode:\n{failure_mode}")

    if detection := fixture.get("detection_criterion"):
        parts.append(f"\nDetection criterion:\n{detection}")

    parts.append(
        "\nEvaluate this fixture on the three dimensions (DEC coherence, "
        "Persona consistency, Handoff completeness) and respond with exactly "
        "three PASS/FAIL lines as instructed."
    )
    return "\n".join(parts)


def _parse_judge_response(text: str) -> dict[str, tuple[str, str]]:
    """Parse the three judge verdict lines into {dimension: (verdict, rationale)}.

    Returns a dict with keys 'DEC coherence', 'Persona consistency',
    'Handoff completeness'. Each value is (verdict, rationale) where
    verdict is 'PASS' or 'FAIL'.
    """
    results: dict[str, tuple[str, str]] = {}
    dimension_prefixes = [
        "DEC coherence",
        "Persona consistency",
        "Handoff completeness",
    ]
    for line in text.strip().splitlines():
        line = line.strip()
        for dim in dimension_prefixes:
            if line.lower().startswith(dim.lower() + ":"):
                rest = line[len(dim) + 1:].strip()
                upper_rest = rest.upper()
                if upper_rest.startswith("PASS"):
                    verdict = "PASS"
                    rationale = rest[4:].lstrip(" —-").strip()
                elif upper_rest.startswith("FAIL"):
                    verdict = "FAIL"
                    rationale = rest[4:].lstrip(" —-").strip()
                else:
                    verdict = "UNKNOWN"
                    rationale = rest
                results[dim] = (verdict, rationale)
    return results


def _call_judge(client: Any, user_prompt: str, model: str) -> str:
    """Call the Anthropic Messages API and return the text response."""
    message = client.messages.create(
        model=model,
        max_tokens=512,
        system=JUDGE_SYSTEM,
        messages=[{"role": "user", "content": user_prompt}],
    )
    return message.content[0].text


# ── Main ──────────────────────────────────────────────────────────────────────

def main() -> int:
    parser = argparse.ArgumentParser(
        description=(
            "LLM judge pass for cross-pack XD eval fixtures. "
            "Advisory only -- never gates CI on its own."
        ),
    )
    parser.add_argument(
        "--root",
        metavar="DIR",
        default=None,
        help="Repo root (default: git toplevel or CWD).",
    )
    parser.add_argument(
        "--fixture-id",
        metavar="ID",
        default=None,
        help="Run only the fixture with this id (e.g. gp-01).",
    )
    args = parser.parse_args()

    # Load and validate fixtures before the API key check so that
    # structural errors (bad fixture id, missing file) are caught early
    # without requiring credentials.
    root = _repo_root(args.root)
    fixtures = _load_fixtures(root)
    to_evaluate = _collect_fixtures(fixtures, args.fixture_id)

    # API key check -- exit 2 after fixture validation so bad ids get
    # their own clear error first.
    api_key = os.environ.get("ANTHROPIC_API_KEY", "")
    if not api_key:
        print(
            "error: ANTHROPIC_API_KEY is not set. "
            "This tool calls the Anthropic API.",
            file=sys.stderr,
        )
        sys.exit(2)

    model = os.environ.get("ANTHROPIC_MODEL", DEFAULT_MODEL)

    try:
        import anthropic  # noqa: PLC0415
    except ImportError:
        print(
            "error: 'anthropic' package is not installed. "
            "Run: pip install anthropic",
            file=sys.stderr,
        )
        sys.exit(2)

    client = anthropic.Anthropic(api_key=api_key)

    print(f"\n[llm-judge-cross-pack-eval] model={model}")
    print(f"[llm-judge-cross-pack-eval] fixtures={FIXTURES_REL}")
    if args.fixture_id:
        print(f"[llm-judge-cross-pack-eval] filter=--fixture-id {args.fixture_id}")

    all_failures: list[str] = []

    for section, fixture in to_evaluate:
        fid = fixture.get("id", "?")
        fname = fixture.get("name", "?")
        print(f"\n[llm-judge-cross-pack-eval] [{section}] {fid}: {fname}")

        user_prompt = _build_user_prompt(section, fixture)
        try:
            response_text = _call_judge(client, user_prompt, model)
        except Exception as exc:  # noqa: BLE001
            print(f"  ✖ API error for fixture {fid}: {exc}", file=sys.stderr)
            all_failures.append(f"{fid}: API error -- {exc}")
            continue

        verdicts = _parse_judge_response(response_text)

        dimensions = ["DEC coherence", "Persona consistency", "Handoff completeness"]
        fixture_passed = True
        for dim in dimensions:
            if dim not in verdicts:
                print(f"  ? {dim}: (no verdict parsed from response)")
                continue
            verdict, rationale = verdicts[dim]
            symbol = "✓" if verdict == "PASS" else "✖"
            rationale_short = rationale[:120] if rationale else "(no rationale)"
            print(f"  {symbol} {dim}: {verdict} -- {rationale_short}")
            if verdict != "PASS":
                fixture_passed = False
                all_failures.append(f"{fid} {dim}: {rationale_short}")

        if fixture_passed:
            print(f"  -> fixture {fid} passed all dimensions")
        else:
            print(f"  -> fixture {fid} FAILED one or more dimensions")

    print()
    total = len(to_evaluate)
    failed_ids = {f.split()[0] for f in all_failures}
    n_failed = len(failed_ids)

    if not all_failures:
        print(f"[llm-judge-cross-pack-eval] All {total} fixture(s) passed (advisory).")
        return 0

    print(f"[llm-judge-cross-pack-eval] {n_failed}/{total} fixture(s) with failures:")
    for failure in all_failures:
        print(f"  ::warning ::[llm-judge] {failure}")
    print("[llm-judge-cross-pack-eval] Advisory only -- not a CI gate.")
    return 1


if __name__ == "__main__":
    sys.exit(main())
