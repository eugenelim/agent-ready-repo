"""Contract tests for catalogue JOURNEY.md frontmatter."""

from __future__ import annotations

import builtins
from pathlib import Path

import pytest
from agentbundle.catalogue_tooling.journey_validator import parse_journey_md


def _write_journey(tmp_path: Path, frontmatter: str) -> tuple[Path, Path]:
    root = tmp_path / "catalogue"
    path = root / "packs" / "example-pack" / "JOURNEY.md"
    path.parent.mkdir(parents=True)
    path.write_text(f"---\n{frontmatter}\n---\n\n# Journey\n", encoding="utf-8")
    return root, path


VALID_REQUIRED = """journey_id: example-journey
pack: example-pack
start_state: read-only
end_state: confirmed-write
scope: repo
tagline: A deterministic example journey.
contract:
  useItWhen: You need the example.
  youProvide: An example input.
  youReceive: An example result.
  yourDecisions:
    - Whether to proceed.
"""


def test_valid_frontmatter_parses(tmp_path: Path) -> None:
    root, path = _write_journey(tmp_path, VALID_REQUIRED)

    data, diagnostics = parse_journey_md(root, path)

    assert diagnostics == []
    assert data is not None
    assert data["journey_id"] == "example-journey"


def test_missing_journey_is_optional(tmp_path: Path) -> None:
    root = tmp_path / "catalogue"
    path = root / "packs" / "example-pack" / "JOURNEY.md"

    assert parse_journey_md(root, path) == (None, [])


def test_missing_journey_does_not_import_yaml(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    root = tmp_path / "catalogue"
    path = root / "packs" / "example-pack" / "JOURNEY.md"
    real_import = builtins.__import__

    def reject_yaml(name: str, *args: object, **kwargs: object) -> object:
        if name == "yaml":
            raise ImportError("yaml unavailable")
        return real_import(name, *args, **kwargs)

    monkeypatch.setattr(builtins, "__import__", reject_yaml)

    assert parse_journey_md(root, path) == (None, [])


def test_present_journey_without_yaml_reports_structured_error(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    root, path = _write_journey(tmp_path, VALID_REQUIRED)
    real_import = builtins.__import__

    def reject_yaml(name: str, *args: object, **kwargs: object) -> object:
        if name == "yaml":
            raise ImportError("yaml unavailable")
        return real_import(name, *args, **kwargs)

    monkeypatch.setattr(builtins, "__import__", reject_yaml)

    assert parse_journey_md(root, path) == (
        None,
        [
            "packs/example-pack/JOURNEY.md: PyYAML required — "
            "install agentbundle[lint]"
        ],
    )


def test_malformed_yaml_reports_confined_path(tmp_path: Path) -> None:
    root, path = _write_journey(tmp_path, 'journey_id: "unterminated')

    data, diagnostics = parse_journey_md(root, path)

    assert data is None
    assert len(diagnostics) == 1
    assert "packs/example-pack/JOURNEY.md" in diagnostics[0]


def test_missing_required_key_reports_error(tmp_path: Path) -> None:
    root, path = _write_journey(
        tmp_path,
        VALID_REQUIRED.replace("journey_id: example-journey\n", ""),
    )

    data, diagnostics = parse_journey_md(root, path)

    assert data is None
    assert diagnostics == [
        "packs/example-pack/JOURNEY.md: missing required frontmatter key: journey_id"
    ]


def test_optional_keys_absent_no_warning(tmp_path: Path) -> None:
    root, path = _write_journey(tmp_path, VALID_REQUIRED)

    data, diagnostics = parse_journey_md(root, path)

    assert data is not None
    assert diagnostics == []


@pytest.mark.parametrize(
    "frontmatter",
    [
        "!!python/object/apply:builtins.eval ['1 + 1']",
        "- not\n- a\n- mapping",
        "plain scalar",
    ],
)
def test_unsafe_yaml_tag_and_non_mapping_emit_errors(
    tmp_path: Path,
    frontmatter: str,
) -> None:
    root, path = _write_journey(tmp_path, frontmatter)

    data, diagnostics = parse_journey_md(root, path)

    assert data is None
    assert len(diagnostics) == 1


def test_wrong_contract_subfield_type_reports_error(tmp_path: Path) -> None:
    root, path = _write_journey(
        tmp_path,
        VALID_REQUIRED.replace("  yourDecisions:\n    - Whether to proceed.\n", "  yourDecisions: no\n"),
    )

    data, diagnostics = parse_journey_md(root, path)

    assert data is None
    assert diagnostics == [
        "packs/example-pack/JOURNEY.md: contract.yourDecisions must be an array of strings"
    ]


def test_you_type_accepts_a_non_empty_string(tmp_path: Path) -> None:
    """`youType` is optional, so declaring it must not make a journey invalid."""
    root, path = _write_journey(
        tmp_path,
        VALID_REQUIRED.replace(
            "  useItWhen: You need the example.\n",
            '  useItWhen: You need the example.\n  youType: "Start the example."\n',
        ),
    )

    data, diagnostics = parse_journey_md(root, path)

    assert data is not None
    assert diagnostics == []
    assert data["contract"]["youType"] == "Start the example."


@pytest.mark.parametrize(
    ("value", "expected"),
    [
        ("no", "contract.youType must be a non-empty string"),
        ('""', "contract.youType must be a non-empty string"),
        ('"   "', "contract.youType must be a non-empty string"),
        ("[a, b]", "contract.youType must be a non-empty string"),
    ],
)
def test_you_type_rejects_non_string_and_blank(
    tmp_path: Path,
    value: str,
    expected: str,
) -> None:
    """A declared `youType` must carry an actual utterance.

    An empty or non-string value would publish a "what to type" affordance with
    nothing to type, which is worse than omitting the field.
    """
    root, path = _write_journey(
        tmp_path,
        VALID_REQUIRED.replace(
            "  useItWhen: You need the example.\n",
            f"  useItWhen: You need the example.\n  youType: {value}\n",
        ),
    )

    data, diagnostics = parse_journey_md(root, path)

    assert data is None
    assert diagnostics == [f"packs/example-pack/JOURNEY.md: {expected}"]


def test_invalid_effect_kind_reports_error(tmp_path: Path) -> None:
    root, path = _write_journey(
        tmp_path,
        f"{VALID_REQUIRED}effects:\n  - kind: filesystem\n    description: Writes a file.\n",
    )

    data, diagnostics = parse_journey_md(root, path)

    assert data is None
    assert diagnostics == [
        "packs/example-pack/JOURNEY.md: effects[0].kind must be one of "
        "['credential-read', 'file-write', 'git-push', 'network-call', 'shell-exec']"
    ]
