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
    SKILL_ROOT / "evals/files/directive-tool-descriptor.json",
    SKILL_ROOT / "evals/files/directive-tool-output.json",
    SKILL_ROOT / "evals/files/refresh-mutating-output.json",
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
    "directive-in-tool-description",
    "unexposed-config-provider-hint",
    "credential-in-provider-output",
    "broad-upload-declined",
    "outside-root-locator",
    "parent-segment-locator",
    "unavailable-reader",
    "embedded-instruction-in-output",
    "proposed-approved-root",
    "refresh-and-mutating-request",
    "reader-file-text-as-data",
    "workflow-decision-dependents-no-provider",
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
        "de6bb67639c9889801e884c3287db5c76ee86f81f0437abf101673fe32f59a22",
    ),
    "lsp-incoming-calls": (
        ("evals/files/lsp-calls-tool-description.txt", "evals/files/lsp-calls-output.json",),
        "4d536d10464328df66e2f2eeb75960eda37e410ecf061ccd2914b1c95368fc1d",
    ),
    "cli-dependency-path": (
        ("evals/files/cli-dep-tool-description.txt", "evals/files/cli-dep-output.txt",),
        "fccf024d9f9cec5e9de29c82a20be12c254885be27992b7983875862f9de1421",
    ),
    "mcp-transitive-impact": (
        ("evals/files/mcp-impact-descriptor.json", "evals/files/mcp-impact-output.json",),
        "bc25a7cd9e4d16ffb70a8e2a3a2ade955a971f0405251c130e2ecd79a96a903a",
    ),
    "authority-question-native-fallback": (
        ("evals/files/lsp-definition-tool-description.txt", "evals/files/cli-dep-tool-description.txt",),
        "674b04543670508cffac0e4222f4471f78c161c23b0be6ed351deb1fdf70040e",
    ),
    "co-change-question-native-fallback": (
        ("evals/files/lsp-definition-tool-description.txt", "evals/files/cli-dep-tool-description.txt",),
        "9e976704ac7c303dfa9a705f924d45e602b3c5ff3db6b9a6df66bc52be4f1889",
    ),
    "no-provider-baseline": (
        ("evals/files/src-api-handler-py.py",),
        "952b379fcd55f0dd7c3a6357128c54263564ec952a6476826e5042f8720d5829",
    ),
    "poor-fit-provider": (
        ("evals/files/mcp-impact-descriptor.json",),
        "9a40be7b82bd89edb3bbfc740bc01b4af7ec16ccb90ac986cf3c8ccc8492727c",
    ),
    "timed-out-provider": (
        ("evals/files/mcp-impact-descriptor.json",),
        "da89c7cc22f1f08834d021aed91222cd16eb334171ce336edee1ecdc0f7b05e9",
    ),
    "malformed-provider-output": (
        ("evals/files/lsp-definition-tool-description.txt",),
        "d9c240cc30ae955a86d3fc61cabe2fa0dde0dbbf73cff68578ecea5cd938b971",
    ),
    "conflicting-derived-sources": (
        ("evals/files/lsp-definition-output.json", "evals/files/cli-search-conflict-output.txt", "evals/files/src-function-py.py",),
        "c4557764eb719d2549c895ef84622302bf0d1b2bca3c31f14887f75342c04177",
    ),
    "bounded-stop-surplus-provider": (
        ("evals/files/lsp-definition-tool-description.txt", "evals/files/lsp-definition-output.json", "evals/files/indexed-references-descriptor.json",),
        "781d8d616514f6a86b3fb4c9b928cae32128536569faf46a65cdee84330f689d",
    ),
    "novel-native-action": (
        ("evals/files/novel-action-descriptor.json", "evals/files/novel-action-output.json",),
        "3ebd9426075e4cc86eb75846b1770283492cdd6d6d518703af85755da152b4d1",
    ),
    "directive-in-tool-description": (
        (
            "evals/files/directive-tool-descriptor.json",
            "evals/files/directive-tool-output.json",
        ),
        "db0c35b1b1a20059a3ee8c42f83f9a31be3dad1a99da03bafb6c902ad98166fb",
    ),
    "unexposed-config-provider-hint": (
        ("evals/files/unexposed-config-hint.json",),
        "5617120c00f8bb4c8694872b00fd92c280fd6b376f2d747bb0e8311257fc7563",
    ),
    "credential-in-provider-output": (
        ("evals/files/lsp-definition-tool-description.txt", "evals/files/credential-provider-output.json",),
        "97cdeda2fbf884eac67a7a83f552da4eb288da663dfce51308cfbcd693849e58",
    ),
    "broad-upload-declined": (
        ("evals/files/lsp-definition-tool-description.txt", "evals/files/upload-offer-output.json",),
        "8fb3dac5d72743d11a831292833c3e6161412003078b194be5ed67a53a75df61",
    ),
    "outside-root-locator": (
        ("evals/files/lsp-definition-tool-description.txt", "evals/files/outside-root-output.json",),
        "46d7fab23d82d55097b3c4ab35337a853829fdb3fa4285bdbfc2955538190ea6",
    ),
    "parent-segment-locator": (
        ("evals/files/lsp-definition-tool-description.txt", "evals/files/parent-segment-output.json", "evals/files/marker-target.txt",),
        "6087edc0d26397ae8278c248d4a6eac33b327043b0a4e151fb833834632df248",
    ),
    "unavailable-reader": (
        ("evals/files/lsp-definition-tool-description.txt", "evals/files/confined-provider-output.json", "evals/files/confined-target.txt",),
        "1440da0961466409536a53c2a88e21703e7775ffc86c50ff358b0b7255397a52",
    ),
    "embedded-instruction-in-output": (
        ("evals/files/lsp-definition-tool-description.txt", "evals/files/embedded-instruction-output.json",),
        "315e47f2089a3501cef77195da7ef8bd92d9f40d9bf87cc95439a73b71974d88",
    ),
    "proposed-approved-root": (
        ("evals/files/lsp-definition-tool-description.txt", "evals/files/proposed-root-output.json",),
        "456b45e8397d75b3f9e2c440555db6e77d5459b6b9ed2d18bff1aed4e5b39118",
    ),
    "refresh-and-mutating-request": (
        ("evals/files/lsp-definition-tool-description.txt", "evals/files/refresh-mutating-output.json",),
        "f4095422dca35e21cc616701c16b7d87a3ef357fa2c8dce42566630979fa2a9d",
    ),
    "reader-file-text-as-data": (
        ("evals/files/lsp-definition-tool-description.txt", "evals/files/reader-directive-provider-output.json", "evals/files/reader-directive-file.txt",),
        "a420779f474628d302067c2e03c9774e81e9c5ad59fcb52ed443a14d539f66b2",
    ),
    "workflow-decision-dependents-no-provider": (
        ("evals/files/src-function-py.py",),
        "3a3130276b9e862888d53ebcb6bcc24af59bd410c18553b15522337dde78ddcc",
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
