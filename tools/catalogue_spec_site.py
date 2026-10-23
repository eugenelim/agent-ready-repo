"""Generate the catalogue specification section of the docs site.

``tools/build-site.py`` calls :func:`generate` to project the ``member`` rows
of ``contracts/catalogue-spec.toml`` into Starlight pages, raw files and the
version index. JSON members reuse the Wave 6 field-table renderer; TOML
members render as a code block. Draft raw JSON gets its ``$id`` rewritten by a
byte-level splice, and no other byte changes. Each released version is served
from its frozen snapshot, and ``latest/`` is a byte copy of the newest release's
raw files plus generated redirects to its pages. Pure standard library.
"""

from __future__ import annotations

import importlib.util
import json
import re
import sys
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parent.parent
DRAFT_BASE_URL = "https://eugenelim.github.io/agent-ready-repo/docs/spec/catalogue/draft/"
SITE_BASE = "/agent-ready-repo/docs/"
REDIRECTS_PATH = REPO_ROOT / "docs-site" / "src" / "generated" / "spec-latest-redirects.json"
_ID_LINE = re.compile(rb'^  "\$id": "[^"]*",?$', re.MULTILINE)


def _load_module(name: str, path: Path) -> Any:
    """Load a sibling module by explicit path, independent of ``sys.path``."""
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:  # pragma: no cover - defensive
        raise ImportError(f"cannot load {name}: {path}")
    module = importlib.util.module_from_spec(spec)
    # Registered before exec so the loaded module's dataclasses resolve.
    sys.modules.setdefault(name, module)
    spec.loader.exec_module(module)
    return module


_here = Path(__file__).resolve().parent
_inventory = _load_module(
    "sync_contract_inventory", _here / "catalogue" / "sync_contract_inventory.py"
)
_fields = _load_module("schema_field_reference", _here / "schema_field_reference.py")


def members(contracts_dir: Path) -> list[Any]:
    """The manifest's ``member`` rows, in manifest order."""
    return [r for r in _inventory.load_manifest(contracts_dir) if r.role == "member"]


def page_name(file_name: str) -> str:
    """Page name for a member file name, for example ``pack-schema-json``."""
    return file_name.replace(".", "-")


def draft_bytes(path: Path) -> bytes:
    """Raw bytes to publish under ``draft/``.

    A ``.json`` file has only its top-level ``$id`` value replaced, or a
    ``$id`` line inserted after the first line when it has none. Any other
    file is returned unchanged.
    """
    data = path.read_bytes()
    if path.suffix != ".json":
        return data
    url = DRAFT_BASE_URL + path.name
    match = _ID_LINE.search(data)
    if match:
        line = match.group(0)
        start = match.start() + line.index(b'"', line.index(b":")) + 1
        end = data.index(b'"', start)
        out = data[:start] + url.encode() + data[end:]
    else:
        nl = data.index(b"\n") + 1
        out = data[:nl] + f'  "$id": "{url}",\n'.encode() + data[nl:]
    parsed = json.loads(out)
    if not isinstance(parsed, dict) or parsed.get("$id") != url:
        raise ValueError(f"{path.name}: draft $id splice did not produce {url}")
    return out


def _routes(name: str, section: str = "draft") -> str:
    return f"{SITE_BASE}spec/catalogue/{section}/{name}/"


def _frontmatter(title: str, description: str, slug: str) -> list[str]:
    return [
        "---",
        f"title: {json.dumps(title, ensure_ascii=False)}",
        f"description: {json.dumps(description, ensure_ascii=False)}",
        f"slug: {slug}",
        "---",
        "",
    ]


def _member_page(
    path: str,
    source_path: Path,
    source_label: str,
    section: str = "draft",
) -> str:
    """One member's page under ``section`` (``draft`` or a released version)."""
    file_name = Path(path).name
    name = page_name(file_name)
    slug = f"spec/catalogue/{section}/{name}"
    raw_href = f"{SITE_BASE}spec/catalogue/{section}/{file_name}"
    overview = f"[the overview section for this file]({SITE_BASE}spec/catalogue/{section}/#{name})"
    if source_path.suffix == ".json":
        schema = json.loads(source_path.read_text(encoding="utf-8"))
        page = _fields.render_page(
            schema,
            title=file_name,
            source=source_label,
            narrative_href=raw_href,
            narrative_label="the raw schema, which states every rule",
            slug=slug,
        )
        extra = [f"See {overview}."]
        if file_name == "pack.schema.json":
            extra.append(f"See also [pack.toml fields]({SITE_BASE}reference/pack-toml/).")
        if file_name == "skill.schema.json":
            extra.append(
                f"See also [SKILL.md frontmatter fields]({SITE_BASE}reference/skill-frontmatter/)."
            )
        return page + "\n" + "\n\n".join(extra) + "\n"
    text = source_path.read_text(encoding="utf-8")
    fence = "```"
    while fence in text:
        fence += "`"
    lines = _frontmatter(
        file_name, f"The {file_name} member of the catalogue specification.", slug
    )
    lines += [
        f"This is `{source_label}`, shown as published.",
        "",
        f"{fence}toml",
        text.rstrip("\n"),
        fence,
        "",
        f"Download the [raw file]({raw_href}).",
        "",
        f"See {overview}.",
    ]
    if file_name == "adapter.toml":
        lines += [
            "",
            f"Its schema is [adapter.schema.json]({_routes('adapter-schema-json', section)}).",
        ]
    return "\n".join(lines) + "\n"


def _write(dest: Path, data: bytes) -> None:
    dest.parent.mkdir(parents=True, exist_ok=True)
    dest.write_bytes(data)


def _file_names(release: Any) -> list[str]:
    """Member file names of a release row, from its ``members`` key set."""
    return [Path(key).name for key in release.members]


def _release_outputs(
    release: Any, contracts_dir: Path, section: Path, raw_dir: Path
) -> list[tuple[Path, bytes]]:
    """Pages and raw files of one release, read only from its snapshot."""
    version = release.version
    snap = _inventory.snapshot_dir(contracts_dir, version)
    out: list[tuple[Path, bytes]] = []
    overview_src = snap / "overview.md"
    prose = (
        overview_src.read_text(encoding="utf-8").rstrip("\n")
        if overview_src.is_file()
        else f"# Catalogue specification {version}"
    )
    table = ["", "## All member files", "", "| File | Page | Raw file |", "| --- | --- | --- |"]
    for file_name in _file_names(release):
        raw_href = f"{SITE_BASE}spec/catalogue/{version}/{file_name}"
        table.append(
            f"| `{file_name}` | [{page_name(file_name)}]({_routes(page_name(file_name), version)})"
            f" | [{file_name}]({raw_href}) |"
        )
    index = _frontmatter(
        f"Catalogue specification {version}",
        f"Release {version} of the catalogue specification: every member contract.",
        f"spec/catalogue/{version}",
    ) + [prose, *table]
    out.append((section / version / "index.md", ("\n".join(index) + "\n").encode()))
    for key in release.members:
        file_name = Path(key).name
        label = f"contracts/releases/catalogue/{version}/{key}"
        page = _member_page(key, snap / key, label, version)
        out.append((section / version / f"{page_name(file_name)}.md", page.encode()))
        out.append((raw_dir / version / file_name, (snap / key).read_bytes()))
    return out


def generate(
    content_dir: Path,
    public_dir: Path,
    *,
    contracts_dir: Path = REPO_ROOT / "contracts",
    spec_src: Path = REPO_ROOT / "docs-site" / "spec-src" / "catalogue",
    dry_run: bool = False,
    redirects_path: Path | None = None,
) -> list[Path]:
    """Write the section; return its paths (written unless ``dry_run``).

    ``redirects_path``, when given, receives the generated ``latest/`` redirect map.
    """
    rows = members(contracts_dir)
    releases, _ = _inventory.load_releases(contracts_dir)
    releases = sorted(releases, key=lambda r: _inventory.version_key(r.version), reverse=True)
    section = content_dir / "spec" / "catalogue"
    raw_dir = public_dir / "spec" / "catalogue"
    outputs: list[tuple[Path, bytes]] = []

    index = _frontmatter(
        "Catalogue specification",
        "The agentbundle catalogue specification and its released versions.",
        "spec/catalogue",
    ) + [
        "The specification is published as the contract files a catalogue is checked against.",
        "",
    ]
    if releases:
        newest = releases[0].version
        index += [
            f"- [Latest (currently {newest})]({SITE_BASE}spec/catalogue/latest/)",
            *(
                f"- [Release {r.version}]({SITE_BASE}spec/catalogue/{r.version}/)"
                f" ({r.date}, adapter contract {r.adapter_contract})"
                for r in releases
            ),
        ]
    index += [f"- [Draft (the live `main` state)]({SITE_BASE}spec/catalogue/draft/)"]
    if not releases:
        index += ["", "No released versions are listed yet."]
    outputs.append((section / "index.md", ("\n".join(index) + "\n").encode()))

    overview_src = spec_src / "overview.md"
    prose = (
        overview_src.read_text(encoding="utf-8").rstrip("\n")
        if overview_src.is_file()
        else "# Catalogue specification (draft)"
    )
    table = ["", "## All member files", "", "| File | Page | Raw file |", "| --- | --- | --- |"]
    for row in rows:
        file_name = Path(row.path).name
        raw_href = f"{SITE_BASE}spec/catalogue/draft/{file_name}"
        table.append(
            f"| `{file_name}` | [{page_name(file_name)}]({_routes(page_name(file_name))})"
            f" | [{file_name}]({raw_href}) |"
        )
    draft = _frontmatter(
        "Catalogue specification (draft)",
        "The draft catalogue specification: every member contract.",
        "spec/catalogue/draft",
    ) + [prose, *table]
    outputs.append((section / "draft" / "index.md", ("\n".join(draft) + "\n").encode()))

    for row in rows:
        file_name = Path(row.path).name
        outputs.append((
            section / "draft" / f"{page_name(file_name)}.md",
            _member_page(row.path, contracts_dir / row.path, f"contracts/{row.path}").encode(),
        ))
        outputs.append((raw_dir / "draft" / file_name, draft_bytes(contracts_dir / row.path)))

    redirects: dict[str, str] = {}
    for release in releases:
        outputs += _release_outputs(release, contracts_dir, section, raw_dir)
    if releases:
        newest = releases[0]
        snap = _inventory.snapshot_dir(contracts_dir, newest.version)
        for file_name in _file_names(newest):
            outputs.append((raw_dir / "latest" / file_name, (snap / file_name).read_bytes()))
        # Keys are base-relative (Astro adds the base to a key); values are
        # base-absolute (a value is emitted as written). Composed separately.
        redirects = {"/spec/catalogue/latest/": f"{SITE_BASE}spec/catalogue/{newest.version}/"}
        for file_name in _file_names(newest):
            name = page_name(file_name)
            redirects[f"/spec/catalogue/latest/{name}/"] = _routes(name, newest.version)
    index_json = {
        "releases": [
            {
                "version": r.version,
                "date": r.date,
                "adapter_contract": r.adapter_contract,
                "members": dict(r.members),
            }
            for r in releases
        ]
    }
    outputs.append((raw_dir / "index.json", (json.dumps(index_json, indent=2) + "\n").encode()))
    if redirects_path is not None:
        outputs.append((redirects_path, (json.dumps(redirects, indent=2) + "\n").encode()))

    if not dry_run:
        for dest, data in outputs:
            _write(dest, data)
    return [dest for dest, _ in outputs]
