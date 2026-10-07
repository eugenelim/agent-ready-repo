"""Construction tests for the composition behavior evaluations.

Verifies that the five composition eval cases exist with their pinned fixture
lists, that every listed fixture exists and parses, that the core-only case
names no provider, that prompts omit graded behavior, and that fixtures retain
only synthetic evidence. Reads only files inside the code-intelligence pack.
"""

from __future__ import annotations

import hashlib
import json
import re
from pathlib import Path

# Resolved at import time; all tests use these constants directly.
PACK_ROOT: Path = Path(__file__).resolve().parents[3]
SKILL_DIR: Path = PACK_ROOT / ".apm" / "skills" / "code-intelligence"
EVALS_JSON: Path = SKILL_DIR / "evals" / "evals.json"
EVALS_FILES_DIR: Path = SKILL_DIR / "evals" / "files"

# All fixture files listed across the five new composition cases, enumerated as
# explicit literals so that tools/lint-pack-test-boundary.py check 8 can resolve
# each path statically (a dynamic variable from JSON iteration would be an
# _UnresolvedPath and flagged).
_COMPOSITION_EVALS_FILES: tuple[Path, ...] = (
    SKILL_DIR / "evals/files/composition-preflight-exit0.txt",
    SKILL_DIR / "evals/files/composition-preflight-exit2.txt",
    SKILL_DIR / "evals/files/composition-stats-fresh.txt",
    SKILL_DIR / "evals/files/composition-stats-lagged.txt",
    SKILL_DIR / "evals/files/composition-blast-radius.json",
    SKILL_DIR / "evals/files/composition-blast-radius-untrusted.json",
    SKILL_DIR / "evals/files/composition-git-log.txt",
    SKILL_DIR / "evals/files/composition-config_loader.py",
    SKILL_DIR / "evals/files/composition-app_main.py",
    SKILL_DIR / "evals/files/composition-cli_entry.py",
    SKILL_DIR / "evals/files/composition-dynamic_registry.py",
)

# The four fixture files that the composition-core-only case seeds.
# Enumerated as literals so check 8 can resolve each path statically.
_CORE_ONLY_FIXTURE_PATHS: tuple[Path, ...] = (
    SKILL_DIR / "evals/files/composition-config_loader.py",
    SKILL_DIR / "evals/files/composition-app_main.py",
    SKILL_DIR / "evals/files/composition-cli_entry.py",
    SKILL_DIR / "evals/files/composition-dynamic_registry.py",
)

# Fixture lists for each of the five new composition cases.
# Changing a fixture list requires updating this pin in the same commit.
_NEW_CASE_FIXTURES: dict[str, tuple[str, ...]] = {
    "composition-provider-fit": (
        "evals/files/composition-preflight-exit0.txt",
        "evals/files/composition-stats-fresh.txt",
        "evals/files/composition-blast-radius.json",
        "evals/files/composition-config_loader.py",
        "evals/files/composition-app_main.py",
        "evals/files/composition-cli_entry.py",
        "evals/files/composition-dynamic_registry.py",
    ),
    "composition-provider-absent": (
        "evals/files/composition-preflight-exit2.txt",
        "evals/files/composition-config_loader.py",
        "evals/files/composition-app_main.py",
        "evals/files/composition-cli_entry.py",
        "evals/files/composition-dynamic_registry.py",
    ),
    "composition-poor-fit": (
        "evals/files/composition-preflight-exit0.txt",
        "evals/files/composition-stats-lagged.txt",
        "evals/files/composition-git-log.txt",
        "evals/files/composition-config_loader.py",
        "evals/files/composition-app_main.py",
        "evals/files/composition-cli_entry.py",
        "evals/files/composition-dynamic_registry.py",
    ),
    "composition-core-only": (
        "evals/files/composition-config_loader.py",
        "evals/files/composition-app_main.py",
        "evals/files/composition-cli_entry.py",
        "evals/files/composition-dynamic_registry.py",
    ),
    "composition-untrusted-output": (
        "evals/files/composition-preflight-exit0.txt",
        "evals/files/composition-stats-fresh.txt",
        "evals/files/composition-blast-radius-untrusted.json",
        "evals/files/composition-config_loader.py",
        "evals/files/composition-app_main.py",
        "evals/files/composition-cli_entry.py",
    ),
}

# SHA-256 of each pre-existing case's prompt, computed from the origin/main
# content before this change. A changed prompt fails this pin; an intended
# prompt update re-pins here in the same commit.
_EXISTING_CASE_PROMPT_SHA256: dict[str | int, str] = {
    1: "77578adc0c821ae1c766a5d19354ae09a4903b1c868bedc87ccc87a86d1f1581",
    2: "9239cd08ead4e8419e018fee62d8ff8dedad55934ac3d20c148ba390a6b2735c",
    3: "cca0863fc6b54dd8fa5c3113a7fa4c227ae1acfbd0459fc7e337c85c5c2aeef2",
    4: "deb27d163a19ee8eb6783d37979b4ac8413000cc2d99a03d8faaaa51a3c4db7c",
    5: "b96f1d4bf744fe86c7114ef561640c1a8c781ab5354f5c94939c1a7b18c240b4",
    6: "25d52ecc7c14250c942dcdb1599be5aa1da899e1cdc942def81f9e9e709553ca",
    7: "63a72b47428342283b4d5e71df88c5b73d02d745525717478ace71b9a49469c0",
    "cognitive-load-output-quality": (
        "7bb6ddde04777e8f477aab6f858267649c4de01d588ca8c4149c3d330bd6b5b5"
    ),
}

# Wicked Estate provider terms that must not appear in the core-only case.
# These identify the optional pack; their absence proves the case is provider-neutral.
_PROVIDER_TERMS: tuple[str, ...] = (
    "wicked-estate",
    "wicked_estate",
    "Wicked Estate",
    "WickedEstate",
    "code-intelligence",
    "blast-radius",
)

# Phrases from eval assertions that prompts must not echo back.
# Prompts that contain these phrases are testing the agent for the exact
# behavior they are grading, which invalidates the evaluation.
_GRADED_PHRASES: tuple[str, ...] = (
    "floor",
    "label",
    "base64",
    "refuse",
    "do not install",
    "unresolved",
    "verify",
    "stale",
    "re-index",
)

# Patterns that indicate forbidden content in fixtures (AC-0012).
# Each is a compiled regex for efficient scanning of fixture text.
# Any absolute local path ("/usr/...", "/Users/...", "C:\..."), plus "~/"; a
# relative "../x" is not matched because its slash follows a dot.
_HOME_DIR_PATTERN: re.Pattern[str] = re.compile(
    r"~/|(?<![\w.])/[A-Za-z][\w.-]*/|\b[A-Za-z]:\\"
)
_EMAIL_PATTERN: re.Pattern[str] = re.compile(
    r"[a-zA-Z0-9_.+-]+@(?!example\.com|example\.invalid)[a-zA-Z0-9-]+\.[a-zA-Z]{2,}"
)
_CREDENTIAL_PATTERN: re.Pattern[str] = re.compile(
    r"(?:api_key|secret|password|token|private_key)\s*[:=]\s*\S{16,}"
)
_PRIVATE_IP_PATTERN: re.Pattern[str] = re.compile(
    r"\b(?:192\.168\.|10\.\d+\.|172\.(?:1[6-9]|2[0-9]|3[01])\.)\d+\.\d+\b"
)


def _load_evals() -> dict[str | int, dict]:
    """Load evals.json and return cases keyed by their id field."""
    payload = json.loads(EVALS_JSON.read_text(encoding="utf-8"))
    return {item["id"]: item for item in payload["evals"]}


def test_composition_cases_are_pinned() -> None:
    """The five new case ids exist with their exact fixture lists and all pre-existing
    case ids remain with their prompts unchanged.

    This test is the stability contract for T2: changing a fixture list or rewording a
    pre-existing prompt fails here, so an intended change must update the pin in the
    same commit.
    """
    evals = _load_evals()

    # Five new cases must be present with their exact fixture lists.
    for case_id, expected_files in _NEW_CASE_FIXTURES.items():
        assert case_id in evals, f"Missing composition eval case: {case_id!r}"
        actual_files = tuple(evals[case_id].get("files", []))
        assert actual_files == expected_files, (
            f"Eval {case_id!r}: fixture list changed.\n"
            f"  Expected: {expected_files}\n"
            f"  Got:      {actual_files}"
        )

    # All eight pre-existing cases must still be present with unchanged prompts.
    for case_id, expected_sha in _EXISTING_CASE_PROMPT_SHA256.items():
        assert case_id in evals, (
            f"Pre-existing eval case {case_id!r} was removed from evals.json"
        )
        prompt = evals[case_id]["prompt"]
        actual_sha = hashlib.sha256(prompt.encode("utf-8")).hexdigest()
        assert actual_sha == expected_sha, (
            f"Eval {case_id!r}: prompt was changed (SHA-256 mismatch).\n"
            f"  Expected: {expected_sha}\n"
            f"  Got:      {actual_sha}"
        )


def test_composition_fixtures_exist_and_parse() -> None:
    """Every fixture listed in _COMPOSITION_EVALS_FILES exists, and every JSON
    fixture among them parses as valid JSON.

    Verifies that a file added to the evals.json fixture list actually exists on
    disk and is not corrupt.
    """
    for fixture_path in _COMPOSITION_EVALS_FILES:
        assert fixture_path.is_file(), (
            f"Composition eval fixture missing: {fixture_path.name}"
        )
        if fixture_path.suffix == ".json":
            src = fixture_path.read_text(encoding="utf-8")
            try:
                json.loads(src)
            except json.JSONDecodeError as exc:
                raise AssertionError(
                    f"JSON fixture {fixture_path.name!r} is not valid JSON: {exc}"
                ) from exc


def test_core_only_case_names_no_provider() -> None:
    """The composition-core-only case contains no Wicked Estate name, wicked-estate
    command, output field from the capability map, or pack name in its prompt,
    expected output, assertions, or fixture file content.

    This case must be provider-neutral so it can assert that Core's inquiry owner
    answers the acceptance question without the optional pack present.
    """
    evals = _load_evals()
    assert "composition-core-only" in evals, (
        "composition-core-only case is missing from evals.json"
    )
    case = evals["composition-core-only"]

    # Collect all text that the case exposes to inspection.
    texts_to_check: list[tuple[str, str]] = [
        ("prompt", case.get("prompt", "")),
        ("expected_output", case.get("expected_output", "")),
    ]
    for i, assertion in enumerate(case.get("assertions", [])):
        texts_to_check.append((f"assertion[{i}]", assertion))

    # Also check each core-only fixture file's text content.
    # Use the pre-enumerated literal-path tuple so check 8 can resolve these statically.
    for fixture_path in _CORE_ONLY_FIXTURE_PATHS:
        if fixture_path.is_file():
            texts_to_check.append((
                f"fixture:{fixture_path.name}",
                fixture_path.read_text(encoding="utf-8"),
            ))

    for field_name, text in texts_to_check:
        for term in _PROVIDER_TERMS:
            assert term not in text, (
                f"composition-core-only {field_name!r} contains provider term "
                f"{term!r}, which must not appear in a provider-neutral case"
            )


def test_composition_prompts_omit_graded_behavior() -> None:
    """No composition eval prompt contains a phrase that is also graded in its assertions.

    A prompt that tells the agent exactly what behavior to produce pre-determines
    the result and invalidates the evaluation. Each graded phrase is checked
    against every composition prompt.
    """
    evals = _load_evals()
    for case_id in _NEW_CASE_FIXTURES:
        assert case_id in evals, f"Missing composition eval case: {case_id!r}"
        prompt = evals[case_id].get("prompt", "")
        for phrase in _GRADED_PHRASES:
            assert phrase not in prompt, (
                f"Eval {case_id!r} prompt contains graded phrase {phrase!r}. "
                f"Remove it from the prompt; the agent must not be told what to produce."
            )


def test_composition_fixtures_retain_only_synthetic_evidence() -> None:
    """No composition fixture holds an absolute home-directory path, email address,
    credential-shaped key, private IP address, or hostname outside example.com and
    example.invalid.

    Provider output in fixtures is untrusted data (AC-0012). Fixtures must contain
    only synthetic, task-minimized content.
    """
    for fixture_path in _COMPOSITION_EVALS_FILES:
        if not fixture_path.is_file():
            continue
        text = fixture_path.read_text(encoding="utf-8")
        name = fixture_path.name

        assert not _HOME_DIR_PATTERN.search(text), (
            f"Fixture {name!r} contains a home-directory or absolute local path. "
            f"Use synthetic paths instead."
        )
        assert not _EMAIL_PATTERN.search(text), (
            f"Fixture {name!r} contains a real email address. "
            f"Use example.invalid addresses only."
        )
        assert not _CREDENTIAL_PATTERN.search(text), (
            f"Fixture {name!r} contains a credential-shaped string. "
            f"Remove credentials from fixtures."
        )
        assert not _PRIVATE_IP_PATTERN.search(text), (
            f"Fixture {name!r} contains a private IP address. "
            f"Use only public or example-range addresses."
        )
