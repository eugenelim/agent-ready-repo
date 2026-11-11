"""The catalogue specification version report, read lazily from bundled members."""

from __future__ import annotations

import contextlib
import io
import json

import pytest
from agentbundle import cli, version

_BASE = "https://example.test/docs/spec/catalogue"


def _member(name: str, ver: str = "0.1") -> str:
    return json.dumps({"$id": f"{_BASE}/{ver}/{name}"})


@pytest.fixture
def data(monkeypatch: pytest.MonkeyPatch) -> dict[str, str]:
    """Replace the bundled-resource reader with an in-memory `_data/` folder."""
    files: dict[str, str] = {
        "catalogue-members.txt": "a.schema.json\nb.schema.json\n",
        "a.schema.json": _member("a.schema.json"),
        "b.schema.json": _member("b.schema.json"),
    }

    def read(name: str) -> str:
        if name not in files:
            raise FileNotFoundError(f"bundled contract missing: _data/{name}")
        return files[name]

    monkeypatch.setattr(version, "_read_bundled_text", read)
    return files


def _run(*argv: str) -> tuple[int, str, str]:
    out, err = io.StringIO(), io.StringIO()
    with contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
        try:
            code = cli.main(list(argv))
        except SystemExit as exc:
            code = int(exc.code or 0)
    return code, out.getvalue(), err.getvalue()


def test_version_comes_from_member_ids(data: dict[str, str]) -> None:
    data["a.schema.json"] = _member("a.schema.json", "3.7")
    data["b.schema.json"] = _member("b.schema.json", "3.7")
    assert version.catalogue_spec_version() == "3.7"


def test_bundled_members_agree_with_real_package() -> None:
    assert version.catalogue_spec_version().count(".") == 1


@pytest.mark.parametrize(
    "broken",
    [None, "{not json", json.dumps({"x": 1}), _member("b.schema.json", "0.1").replace("b.schema", "z.schema")],
    ids=["missing", "unparsable", "no-id", "wrong-name"],
)
def test_bad_member_fails_naming_it(data: dict[str, str], broken: str | None) -> None:
    if broken is None:
        del data["b.schema.json"]
    else:
        data["b.schema.json"] = broken
    with pytest.raises((ValueError, FileNotFoundError), match="_data/b.schema.json"):
        version.catalogue_spec_version()


def test_disagreeing_id_fails(data: dict[str, str]) -> None:
    data["b.schema.json"] = _member("b.schema.json", "0.2")
    with pytest.raises(ValueError, match="_data/catalogue-members.txt"):
        version.catalogue_spec_version()


@pytest.mark.parametrize("content", [None, "", "\n  \n"], ids=["absent", "empty", "zero-entry"])
def test_bad_inventory_fails_naming_it(data: dict[str, str], content: str | None) -> None:
    if content is None:
        del data["catalogue-members.txt"]
    else:
        data["catalogue-members.txt"] = content
    with pytest.raises(ValueError, match="_data/catalogue-members.txt"):
        version.catalogue_spec_version()


def test_unreadable_inventory_fails_naming_it(
    data: dict[str, str], monkeypatch: pytest.MonkeyPatch
) -> None:
    def read(name: str) -> str:
        raise ValueError(f"bundled contract unreadable: _data/{name}: bad bytes")

    monkeypatch.setattr(version, "_read_bundled_text", read)
    with pytest.raises(ValueError, match="_data/catalogue-members.txt"):
        version.catalogue_spec_version()


def test_reports_carry_and_agree_on_version(data: dict[str, str]) -> None:
    code, out, _ = _run("--version")
    assert code == 0 and "catalogue specification 0.1" in out
    code, table, _ = _run("catalogue", "contracts", "list")
    assert code == 0 and "Catalogue specification 0.1" in table


def test_json_envelope_keeps_rows(data: dict[str, str]) -> None:
    code, out, _ = _run("catalogue", "contracts", "list", "--format", "json")
    assert code == 0
    document = json.loads(out)
    assert set(document) == {"catalogue_specification", "contracts"}
    assert document["catalogue_specification"] == "0.1"
    assert isinstance(document["contracts"], list)
    assert all(set(row) == {"name", "kind", "file"} for row in document["contracts"])


def test_malformed_id_fails_only_the_two_reports(data: dict[str, str]) -> None:
    data["a.schema.json"] = json.dumps({"no": "id"})
    code, out, err = _run("--version")
    assert code != 0 and out == "" and "_data/a.schema.json" in err
    code, out, err = _run("catalogue", "contracts", "list")
    assert code != 0 and "_data/a.schema.json" in err
    code, out, err = _run("catalogue", "contracts", "list", "--format", "json")
    assert code != 0 and out == ""
    code, out, _ = _run("adapt", "--help")
    assert code == 0 and "usage" in out.lower()
