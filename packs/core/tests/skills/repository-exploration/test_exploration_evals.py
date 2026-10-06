"""Construction tests for the repository-exploration behavior evaluations.

Pins each case's id, fixture list, and a digest of its assertion list so that
removing a fixture or rewording an assertion fails immediately. Also checks that
every fixture exists, every JSON fixture parses, and that no two JSON fixtures
share a parsed top-level key set across provider shapes — which would imply a
common envelope and contradict AC-0004.
"""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

PACK_ROOT = Path(__file__).resolve().parents[3]
SKILL_ROOT = PACK_ROOT / ".apm" / "skills" / "repository-exploration"
EVALS_PATH = SKILL_ROOT / "evals" / "evals.json"


def _evals_by_id() -> dict[str, dict]:
    """Load behavior evaluations keyed by stable identifier."""
    payload = json.loads(EVALS_PATH.read_text(encoding="utf-8"))
    return {item["id"]: item for item in payload["evals"]}


# All fixture files listed across all evals cases, as explicit literals so that
# tools/lint-pack-test-boundary.py can resolve each path statically (a dynamic
# variable from JSON iteration would be an _UnresolvedPath and flagged).
_EVALS_FILES = (
    SKILL_ROOT / "evals/files/lsp-definition-tool-description.txt",
    SKILL_ROOT / "evals/files/lsp-definition-output.json",
    SKILL_ROOT / "evals/files/lsp-calls-tool-description.txt",
    SKILL_ROOT / "evals/files/lsp-calls-output.json",
    SKILL_ROOT / "evals/files/cli-dep-tool-description.txt",
    SKILL_ROOT / "evals/files/cli-dep-output.txt",
    SKILL_ROOT / "evals/files/mcp-impact-descriptor.json",
    SKILL_ROOT / "evals/files/mcp-impact-output.json",
    SKILL_ROOT / "evals/files/indexed-references-descriptor.json",
    SKILL_ROOT / "evals/files/novel-action-descriptor.json",
    SKILL_ROOT / "evals/files/novel-action-output.json",
    SKILL_ROOT / "evals/files/unexposed-config-hint.json",
    SKILL_ROOT / "evals/files/credential-provider-output.json",
    SKILL_ROOT / "evals/files/upload-offer-output.json",
    SKILL_ROOT / "evals/files/outside-root-output.json",
    SKILL_ROOT / "evals/files/parent-segment-output.json",
    SKILL_ROOT / "evals/files/confined-provider-output.json",
    SKILL_ROOT / "evals/files/embedded-instruction-output.json",
    SKILL_ROOT / "evals/files/proposed-root-output.json",
    SKILL_ROOT / "evals/files/reader-directive-provider-output.json",
    SKILL_ROOT / "evals/files/src-api-handler-py.py",
    SKILL_ROOT / "evals/files/cli-search-conflict-output.txt",
    SKILL_ROOT / "evals/files/src-function-py.py",
    SKILL_ROOT / "evals/files/marker-target.txt",
    SKILL_ROOT / "evals/files/confined-target.txt",
    SKILL_ROOT / "evals/files/reader-directive-file.txt",
)

# Subset of _EVALS_FILES whose basenames end in .json and must parse as valid JSON.
_EVALS_JSON_FILES = tuple(p for p in _EVALS_FILES if p.suffix == ".json")

# Subset of _EVALS_FILES that are Python source and must parse without syntax errors.
_EVALS_PY_FILES = (
    SKILL_ROOT / "evals/files/src-api-handler-py.py",
    SKILL_ROOT / "evals/files/src-function-py.py",
)

_EXPECTED_EVAL_IDS: tuple[str, ...] = (
    "lsp-goto-definition",
    "lsp-incoming-calls",
    "cli-dependency-path",
    "mcp-transitive-impact",
    "authority-question-native-fallback",
    "co-change-question-native-fallback",
    "no-provider-baseline",
    "poor-fit-provider",
    "timed-out-provider",
    "malformed-provider-output",
    "conflicting-derived-sources",
    "bounded-stop-surplus-provider",
    "novel-native-action",
    "unexposed-config-provider-hint",
    "credential-in-provider-output",
    "broad-upload-declined",
    "outside-root-locator",
    "parent-segment-locator",
    "unavailable-reader",
    "embedded-instruction-in-output",
    "proposed-approved-root",
    "reader-file-text-as-data",
)


def test_evals_all_required_ids_present() -> None:
    """Every required evaluation case id is present in evals.json."""
    evals = _evals_by_id()
    for eid in _EXPECTED_EVAL_IDS:
        assert eid in evals, f"Missing eval case: {eid}"


def test_evals_fixture_files_exist() -> None:
    """Every file in _EVALS_FILES exists on disk."""
    for p in _EVALS_FILES:
        assert p.is_file(), f"Eval fixture file missing: {p.name}"


def test_evals_fixture_files_match_manifest() -> None:
    """Every fixture path in evals.json is covered by _EVALS_FILES.

    Catches the case where a new fixture is added to evals.json but the
    corresponding entry is not added to _EVALS_FILES.
    """
    evals = _evals_by_id()
    manifest: frozenset[str] = frozenset(p.name for p in _EVALS_FILES)
    for eid, case in evals.items():
        for rel in case.get("files", []):
            name = rel.split("/")[-1]
            assert name in manifest, (
                f"Eval {eid}: fixture {rel!r} is not covered by _EVALS_FILES. "
                f"Add SKILL_ROOT / {rel!r} to the tuple."
            )


def test_evals_json_fixtures_parse() -> None:
    """Every JSON fixture file in _EVALS_JSON_FILES parses as valid JSON."""
    for p in _EVALS_JSON_FILES:
        src = p.read_text(encoding="utf-8")
        try:
            json.loads(src)
        except json.JSONDecodeError as exc:
            raise AssertionError(
                f"JSON fixture {p.name} is not valid JSON: {exc}"
            ) from exc


def test_evals_python_fixtures_parse() -> None:
    """Every Python fixture file in _EVALS_PY_FILES parses without syntax errors."""
    import ast

    for p in _EVALS_PY_FILES:
        src = p.read_text(encoding="utf-8")
        try:
            ast.parse(src, filename=str(p))
        except SyntaxError as exc:
            raise AssertionError(
                f"Python fixture {p.name} has a syntax error: {exc}"
            ) from exc


def test_evals_json_fixtures_no_shared_top_level_key_set() -> None:
    """No two JSON fixtures share a parsed top-level key set.

    A shared key set across provider shapes would imply a common envelope and
    contradict the native-shapes requirement. Each JSON fixture must have a
    top-level key set distinct from every other JSON fixture in the evals.
    """
    seen: dict[frozenset[str], str] = {}
    for p in _EVALS_JSON_FILES:
        obj = json.loads(p.read_text(encoding="utf-8"))
        key_set = frozenset(obj.keys())
        if key_set in seen:
            raise AssertionError(
                f"JSON fixtures {p.name!r} and {seen[key_set]!r} share the "
                f"same top-level key set {set(key_set)!r}. Each provider shape "
                f"must have a distinct top-level structure."
            )
        seen[key_set] = p.name


# Each case's fixture list and a digest of its exact assertion list. Removing a
# fixture, or dropping or rewording an assertion, changes one of these and fails
# the pin below; an intended change re-pins here in the same commit.
_PINNED_EVAL_CASES: dict[str, tuple[tuple[str, ...], str]] = {
    "lsp-goto-definition": (
        ("evals/files/lsp-definition-tool-description.txt", "evals/files/lsp-definition-output.json",),
        "a0b97eab113096e1d92f8a00833338f1aae245106d3d5d231f9033533727bf88",
    ),
    "lsp-incoming-calls": (
        ("evals/files/lsp-calls-tool-description.txt", "evals/files/lsp-calls-output.json",),
        "518465a90d8bab191ad4f16fa4e65a556c00090201aaff7623ee8034eb6093ef",
    ),
    "cli-dependency-path": (
        ("evals/files/cli-dep-tool-description.txt", "evals/files/cli-dep-output.txt",),
        "baadf8e3ee7b9c4b7724d2da72c2280378965daec3191eec02e6460fdd76df22",
    ),
    "mcp-transitive-impact": (
        ("evals/files/mcp-impact-descriptor.json", "evals/files/mcp-impact-output.json",),
        "ce493e124e059e346712eddf9f60913507131a2e504e24f922296b956c5f7e77",
    ),
    "authority-question-native-fallback": (
        ("evals/files/lsp-definition-tool-description.txt", "evals/files/cli-dep-tool-description.txt",),
        "c045d453d02f2e0b37581de22a5cbbd477830b2dde89dc9f7c354ad473d89f17",
    ),
    "co-change-question-native-fallback": (
        ("evals/files/lsp-definition-tool-description.txt", "evals/files/cli-dep-tool-description.txt",),
        "85ee4c2309f6415759bc29e617cae79b645a9059caabfd2687b3219d5fd33767",
    ),
    "no-provider-baseline": (
        ("evals/files/src-api-handler-py.py",),
        "053659e453d6ff22938e5882d90a1fe69fa9c8b5284d70f0194713e1d97f6aae",
    ),
    "poor-fit-provider": (
        ("evals/files/mcp-impact-descriptor.json",),
        "95b5710788f4fc91cbd97bc1cbbc8be3decda489eabe6b2d2fb35da5396c6c9a",
    ),
    "timed-out-provider": (
        ("evals/files/mcp-impact-descriptor.json",),
        "09098a8cd29924ab656961eb2352fd8faa4347e4911ed6f817035164c8f6053b",
    ),
    "malformed-provider-output": (
        ("evals/files/lsp-definition-tool-description.txt",),
        "952abe58e7231ff133c5e4483410d82ee30226261c8bb9ba214ce86ad9076431",
    ),
    "conflicting-derived-sources": (
        ("evals/files/lsp-definition-output.json", "evals/files/cli-search-conflict-output.txt", "evals/files/src-function-py.py",),
        "eaf1842a370548efa2ea4c8b3e925781c31a2a6ddabf50756b152d1c3ef37dc3",
    ),
    "bounded-stop-surplus-provider": (
        ("evals/files/lsp-definition-tool-description.txt", "evals/files/lsp-definition-output.json", "evals/files/indexed-references-descriptor.json",),
        "fd49efab721e7a546c53ddef897fb3b3a80d8ccdb388a5eaa486ab0927b1046e",
    ),
    "novel-native-action": (
        ("evals/files/novel-action-descriptor.json", "evals/files/novel-action-output.json",),
        "c9440715f73f49353585ac6a311be3ed0bb8107374938f4ef649949ce3cd2222",
    ),
    "unexposed-config-provider-hint": (
        ("evals/files/unexposed-config-hint.json",),
        "5a42a7352763c73ed4aa0a0525ae09203668e9d7e4655fcfcdf92f38cf84f1d1",
    ),
    "credential-in-provider-output": (
        ("evals/files/lsp-definition-tool-description.txt", "evals/files/credential-provider-output.json",),
        "bf17e8d2e4d687d8ae1f3263a7cb9989c7a414f6df1b6c7642cb307f9fc54990",
    ),
    "broad-upload-declined": (
        ("evals/files/lsp-definition-tool-description.txt", "evals/files/upload-offer-output.json",),
        "d8340ec32f9b10b4dca366df4b9752500aaf3ae8e6e1ee0c76b914fc94c74f8a",
    ),
    "outside-root-locator": (
        ("evals/files/lsp-definition-tool-description.txt", "evals/files/outside-root-output.json",),
        "129d49126f8e4407f8a45a11185890078dd48e110aff2e924f8b764c22dbf8be",
    ),
    "parent-segment-locator": (
        ("evals/files/lsp-definition-tool-description.txt", "evals/files/parent-segment-output.json", "evals/files/marker-target.txt",),
        "ca14fff151ee44d4bf3bbe21c44ca3333bf6ba88c84489429fbe64d9777e08b9",
    ),
    "unavailable-reader": (
        ("evals/files/lsp-definition-tool-description.txt", "evals/files/confined-provider-output.json", "evals/files/confined-target.txt",),
        "5edf75b13c4c03ef8dfed02ff108c955f4b05e05f401c0b4061fd2cec5963121",
    ),
    "embedded-instruction-in-output": (
        ("evals/files/lsp-definition-tool-description.txt", "evals/files/embedded-instruction-output.json",),
        "947e9ba3860b38b7d0682655b5a026f4691e72444cf2243c07ee4699ab00af2a",
    ),
    "proposed-approved-root": (
        ("evals/files/lsp-definition-tool-description.txt", "evals/files/proposed-root-output.json",),
        "c555e34d487189f88076d6c78571c33214d2efc1b2286f88d7fc86c4752d3cc1",
    ),
    "reader-file-text-as-data": (
        ("evals/files/lsp-definition-tool-description.txt", "evals/files/reader-directive-provider-output.json", "evals/files/reader-directive-file.txt",),
        "85e0a773a4637f03449f4bf0e561c8940dfc136dde3e77bb3fe9fbfa89c56f40",
    ),
}


def _assertions_digest(assertions: list[str]) -> str:
    """Hash an assertion list exactly as the pin table records it."""
    encoded = json.dumps(assertions, ensure_ascii=False).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def test_evals_each_case_has_assertions() -> None:
    """Every eval case has at least one assertion."""
    evals = _evals_by_id()
    for eid, case in evals.items():
        assertions = case.get("assertions", [])
        assert len(assertions) >= 1, f"Eval {eid}: no assertions"


def test_evals_cases_match_their_pinned_files_and_assertions() -> None:
    """Each case keeps exactly its pinned fixtures and assertion text."""
    evals = _evals_by_id()
    assert set(evals) == set(_PINNED_EVAL_CASES), (
        f"Eval case IDs do not match pins.\n"
        f"  Extra in evals.json: {set(evals) - set(_PINNED_EVAL_CASES)}\n"
        f"  Missing from evals.json: {set(_PINNED_EVAL_CASES) - set(evals)}"
    )
    for eid, (files, digest) in _PINNED_EVAL_CASES.items():
        case = evals[eid]
        assert tuple(case["files"]) == files, (
            f"Eval {eid}: fixture list changed.\n"
            f"  Expected: {files}\n"
            f"  Got: {tuple(case['files'])}"
        )
        actual_digest = _assertions_digest(case["assertions"])
        assert actual_digest == digest, (
            f"Eval {eid}: assertions removed or reworded.\n"
            f"  Expected digest: {digest}\n"
            f"  Actual digest:   {actual_digest}"
        )
