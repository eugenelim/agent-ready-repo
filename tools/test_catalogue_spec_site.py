"""Tests for tools/catalogue_spec_site.py (catalogue-spec-site T1)."""

from __future__ import annotations

import importlib.util
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
_spec = importlib.util.spec_from_file_location(
    "catalogue_spec_site", ROOT / "tools" / "catalogue_spec_site.py"
)
css = importlib.util.module_from_spec(_spec)  # type: ignore[arg-type]
sys.modules["catalogue_spec_site"] = css
_spec.loader.exec_module(css)  # type: ignore[union-attr]

URL = css.DRAFT_BASE_URL
WITH_ID = (
    b'{\r\n  "$schema": "x",\n  "$id": "with-id.schema.json",\n'
    b'  "type": "object",\n  "properties": {"a": {"type": "string", "description": "A."}}\n}\n'
)
NO_ID = (
    b'{\n  "x-spec": "s",\n  "type": "object",\n'
    b'  "properties": {"a": {"type": "string", "description": "A."}}\n}\n'
)
TOML = b'# comment\r\nname = "x"\n'


def _fixture(tmp_path: Path, extra_rows: str = "") -> Path:
    contracts = tmp_path / "contracts"
    contracts.mkdir()
    (contracts / "with-id.schema.json").write_bytes(WITH_ID)
    (contracts / "no-id.schema.json").write_bytes(NO_ID)
    (contracts / "data.toml").write_bytes(TOML)
    (contracts / "bundled.schema.json").write_bytes(NO_ID)
    (contracts / "vendor").mkdir()
    (contracts / "vendor" / "v.schema.json").write_bytes(
        NO_ID.replace(b'"x-spec": "s",', b'"$id": "https://example.test/v.json",')
    )
    rows = [
        ("with-id.schema.json", "member", None),
        ("no-id.schema.json", "member", None),
        ("bundled.schema.json", "bundled", None),
        ("vendor/v.schema.json", "vendored", "https://example.test/v.json"),
    ]
    body = 'release = []\n\n[spec]\nname = "t"\n'
    for path, role, upstream in rows:
        body += f'\n[[contract]]\npath = "{path}"\nrole = "{role}"\n'
        if upstream:
            body += f'upstream = "{upstream}"\n'
    body += extra_rows
    (contracts / "catalogue-spec.toml").write_text(body, encoding="utf-8")
    return contracts


def _run(tmp_path: Path, contracts: Path, **kw):
    content, public = tmp_path / "content", tmp_path / "public"
    spec_src = tmp_path / "spec-src"
    paths = css.generate(content, public, contracts_dir=contracts, spec_src=spec_src, **kw)
    return content, public, paths


def test_only_member_pages_and_raw_files(tmp_path: Path) -> None:
    contracts = _fixture(tmp_path)
    content, public, _ = _run(tmp_path, contracts)
    section = content / "spec" / "catalogue"
    assert sorted(p.name for p in (section / "draft").iterdir()) == [
        "index.md",
        "no-id-schema-json.md",
        "with-id-schema-json.md",
    ]
    assert (section / "index.md").is_file()
    assert sorted(p.name for p in (public / "spec/catalogue/draft").iterdir()) == [
        "no-id.schema.json",
        "with-id.schema.json",
    ]


def test_slugs_explicit_and_page_names_differ_from_raw(tmp_path: Path) -> None:
    contracts = _fixture(tmp_path)
    content, _, _ = _run(tmp_path, contracts)
    draft = content / "spec/catalogue/draft"
    for page in draft.glob("*.md"):
        if page.name == "index.md":
            continue
        expected = f"slug: spec/catalogue/draft/{page.stem}"
        assert expected in page.read_text(encoding="utf-8").splitlines()
        assert page.stem != page.stem.replace("-", ".")
    for row in css.members(contracts):
        file_name = Path(row.path).name
        assert css.page_name(file_name) != file_name
    assert "slug: spec/catalogue" in (content / "spec/catalogue/index.md").read_text()
    assert "slug: spec/catalogue/draft\n" in (draft / "index.md").read_text()


def test_draft_bytes_replaces_only_id_value(tmp_path: Path) -> None:
    src = tmp_path / "with-id.schema.json"
    src.write_bytes(WITH_ID)
    out = css.draft_bytes(src)
    old = b"with-id.schema.json"
    start = WITH_ID.index(b'"$id": "') + len(b'"$id": "')
    assert out[:start] == WITH_ID[:start]
    new = (URL + "with-id.schema.json").encode()
    assert out == WITH_ID[:start] + new + WITH_ID[start + len(old) :]
    assert json.loads(out)["$id"] == URL + "with-id.schema.json"


def test_draft_bytes_inserts_id_line_when_absent(tmp_path: Path) -> None:
    src = tmp_path / "no-id.schema.json"
    src.write_bytes(NO_ID)
    out = css.draft_bytes(src)
    nl = NO_ID.index(b"\n") + 1
    line = f'  "$id": "{URL}no-id.schema.json",\n'.encode()
    assert out == NO_ID[:nl] + line + NO_ID[nl:]


def test_toml_bytes_identical(tmp_path: Path) -> None:
    contracts = _fixture(tmp_path)
    src = contracts / "data.toml"
    assert css.draft_bytes(src) == TOML


def test_generated_raw_matches_draft_bytes(tmp_path: Path) -> None:
    contracts = _fixture(tmp_path)
    _, public, _ = _run(tmp_path, contracts)
    raw = public / "spec/catalogue/draft"
    for name in ("with-id.schema.json", "no-id.schema.json"):
        assert (raw / name).read_bytes() == css.draft_bytes(contracts / name)


def test_json_page_has_table_and_raw_link(tmp_path: Path) -> None:
    contracts = _fixture(tmp_path)
    content, _, _ = _run(tmp_path, contracts)
    page = (content / "spec/catalogue/draft/with-id-schema-json.md").read_text()
    assert "| Field | Type | Required | Rules | Description |" in page
    assert "| `a` | string |" in page
    assert "(/agent-ready-repo/docs/spec/catalogue/draft/with-id.schema.json)" in page


def test_toml_page_block_raw_link_and_adapter_link(tmp_path: Path) -> None:
    contracts = _fixture(tmp_path)
    (contracts / "adapter.toml").write_bytes(b'k = "v"\n')
    manifest = contracts / "catalogue-spec.toml"
    manifest.write_text(
        manifest.read_text() + '\n[[contract]]\npath = "adapter.toml"\nrole = "member"\n'
    )
    (contracts / "data.toml").unlink()
    content, _, _ = _run(tmp_path, contracts)
    page = (content / "spec/catalogue/draft/adapter-toml.md").read_text()
    assert '```toml\nk = "v"\n```' in page
    assert "(/agent-ready-repo/docs/spec/catalogue/draft/adapter.toml)" in page
    assert "/spec/catalogue/draft/adapter-schema-json/" in page


def test_pack_and_skill_pages_link_wave6(tmp_path: Path) -> None:
    contracts = _fixture(tmp_path)
    for name in ("pack.schema.json", "skill.schema.json"):
        (contracts / name).write_bytes(NO_ID)
    manifest = contracts / "catalogue-spec.toml"
    manifest.write_text(
        manifest.read_text()
        + '\n[[contract]]\npath = "pack.schema.json"\nrole = "member"\n'
        + '\n[[contract]]\npath = "skill.schema.json"\nrole = "member"\n'
    )
    content, _, _ = _run(tmp_path, contracts)
    draft = content / "spec/catalogue/draft"
    assert "/reference/pack-toml/" in (draft / "pack-schema-json.md").read_text()
    assert "/reference/skill-frontmatter/" in (draft / "skill-schema-json.md").read_text()


def test_index_json_and_index_page_link(tmp_path: Path) -> None:
    contracts = _fixture(tmp_path)
    content, public, _ = _run(tmp_path, contracts)
    assert json.loads((public / "spec/catalogue/index.json").read_text()) == {"releases": []}
    assert "/spec/catalogue/draft/" in (content / "spec/catalogue/index.md").read_text()


def test_dry_run_writes_nothing(tmp_path: Path) -> None:
    contracts = _fixture(tmp_path)
    _, _, paths = _run(tmp_path, contracts, dry_run=True)
    assert paths
    assert not (tmp_path / "content").exists()
    assert not (tmp_path / "public").exists()


def test_real_manifest_page_count_equals_member_count(tmp_path: Path) -> None:
    contracts = ROOT / "contracts"
    rows = css.members(contracts)
    content, public, _ = _run(tmp_path, contracts)
    pages = [p for p in (content / "spec/catalogue/draft").glob("*.md") if p.name != "index.md"]
    assert len(pages) == len(rows) == 10
    for row in rows:
        file_name = Path(row.path).name
        assert (public / "spec/catalogue/draft" / file_name).is_file()
    for p in (public / "spec/catalogue/draft").glob("*.json"):
        assert json.loads(p.read_bytes())["$id"] == URL + p.name
    assert re.search(r"^slug: ", pages[0].read_text(), re.M)


def test_overview_carries_ac6_phrases_and_one_section_per_member(tmp_path: Path) -> None:
    contracts = ROOT / "contracts"
    content = tmp_path / "content"
    css.generate(content, tmp_path / "public", contracts_dir=contracts)
    text = (content / "spec/catalogue/draft/index.md").read_text(encoding="utf-8")
    for phrase in (
        "agentbundle catalogue lint",
        "agentbundle catalogue verify",
        "agentbundle catalogue package",
        "CAT-V-ARC",
        "JOURNEY.md",
        "agentbundle catalogue init",
        "`draft/`",
        "not a release",
        "/guides/_shared/reference/pack-journey-format/",
        "/guides/_shared/how-to/create-a-catalogue/",
        "/_data/catalogue-scaffold",
    ):
        assert phrase in text, phrase
    headings = re.findall(r"^#{2,3} (.+)$", text, re.M)
    assert len(headings) == len(set(headings)), headings
    for row in css.members(contracts):
        file_name = Path(row.path).name
        assert css.page_name(file_name) in headings
        assert f"]({css.SITE_BASE}spec/catalogue/draft/{file_name})" in text, file_name
