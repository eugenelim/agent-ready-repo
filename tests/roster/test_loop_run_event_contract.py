"""The event-line contract schema, checked against a recorded corpus.

AC-0048, AC-0049, AC-0050 and AC-0053 of `docs/specs/loop-telemetry-export`.

The corpus is **recorded from real transitions**, never authored: its versioned
half was driven through `loop-engine.py` and its legacy half consists of lines
this repository emitted before the `schema` key shipped. That matters, because a
hand-written corpus can only contain line shapes someone thought of, and a schema
validated against it would pass by construction.

These tests are roster-owned. They read `contracts/jsonschema/` and
`packs/core/tests/.../fixtures/`, neither of which exists inside the published
`agentbundle` sdist -- and `packages/agentbundle/tests/` ships in that sdist and
is re-run against the extracted workspace. Sitting there, they failed the sdist
artifact gate with a `FileNotFoundError` on the schema, which is the gate
correctly reporting that a repository-level contract had been packaged as a
package test.

Roster is not auto-discovered, so `build-check.yml` names this file explicitly.
That is the repository's mechanism for a roster-owned contract that must be
checked on every pull request rather than on a dispatch.
"""
from __future__ import annotations

import json
from pathlib import Path

import pytest
from jsonschema import Draft202012Validator

_REPO = Path(__file__).resolve().parents[2]
_SCHEMA_PATH = _REPO / "contracts/jsonschema/loop-run-event.schema.json"
_CORPUS_PATH = _REPO / "packs/core/tests/skills/work-loop/fixtures/event-corpus.jsonl"
_IDENTITY_FIELDS = ("seq", "run_id", "spec", "from", "event", "to", "at")


def _schema() -> dict:
    return json.loads(_SCHEMA_PATH.read_text(encoding="utf-8"))


def _validator() -> Draft202012Validator:
    return Draft202012Validator(_schema())


def _corpus() -> list[dict]:
    return [
        json.loads(line)
        for line in _CORPUS_PATH.read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]


def test_the_schema_is_itself_a_valid_schema() -> None:
    """A malformed schema accepts everything and would pass every test below."""
    Draft202012Validator.check_schema(_schema())


def test_corpus_holds_both_a_versioned_and_a_legacy_record() -> None:
    # AC-0048, first half
    corpus = _corpus()
    versioned = [r for r in corpus if "schema" in r]
    legacy = [r for r in corpus if "schema" not in r]
    assert versioned, "corpus has no record carrying `schema`"
    assert legacy, "corpus has no legacy record without `schema`"


def test_schema_validates_every_corpus_line() -> None:
    # AC-0048, second half
    validator = _validator()
    failures = {
        index: [e.message for e in validator.iter_errors(record)]
        for index, record in enumerate(_corpus(), start=1)
    }
    failures = {i: msgs for i, msgs in failures.items() if msgs}
    assert not failures, f"corpus lines rejected by the schema: {failures}"


@pytest.mark.parametrize(
    "bad_value",
    [0, -1, "1", 1.5, True, None, [], {}],
    ids=["zero", "negative", "string", "float", "bool", "null", "array", "object"],
)
def test_schema_rejects_a_non_positive_integer_schema_value(bad_value: object) -> None:
    """AC-0049, first half.

    `True` is in this list deliberately: Python treats `bool` as a subclass of
    `int`, so a validator that checked with `isinstance` would accept it.
    """
    record = dict(_corpus()[-1])
    record["schema"] = bad_value
    assert list(_validator().iter_errors(record)), f"{bad_value!r} was accepted"


@pytest.mark.parametrize("field", _IDENTITY_FIELDS)
def test_schema_rejects_a_record_missing_an_identity_field(field: str) -> None:
    # AC-0049, second half
    record = {k: v for k, v in _corpus()[-1].items() if k != field}
    assert list(_validator().iter_errors(record)), f"a record without {field!r} was accepted"


def test_a_legacy_record_without_schema_is_still_valid() -> None:
    """The key is optional, not merely unconstrained.

    A replayed pre-versioning record is appended unchanged, so a schema that
    required `schema` would reject a line the engine still legitimately writes.
    """
    record = {k: v for k, v in _corpus()[-1].items() if k != "schema"}
    assert not list(_validator().iter_errors(record))


def test_contracts_readme_names_the_schema() -> None:
    # AC-0050
    readme = (_REPO / "contracts/README.md").read_text(encoding="utf-8")
    rows = [line for line in readme.splitlines() if line.startswith("|")]
    assert any("jsonschema/loop-run-event.schema.json" in row for row in rows), (
        "contracts/README.md's file table does not name the schema"
    )


def test_schema_comment_names_the_owning_spec() -> None:
    # AC-0053
    assert "docs/specs/loop-telemetry-export/spec.md" in _schema()["$comment"]
