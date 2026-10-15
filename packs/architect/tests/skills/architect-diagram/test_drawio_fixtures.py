"""Structure and link-safety checks for architect-diagram draw.io files.

Covers the shipped ``testdata/*.drawio`` fixtures, the fallback skeleton fenced
in ``references/drawio-export.md``, the install allowlist in that reference,
and the ``SKILL.md`` boundaries. Mutation cases prove each check can fail.

Standard library only; no draw.io binary is run.
"""
from __future__ import annotations

import re
import unicodedata
import xml.etree.ElementTree as ET
from collections.abc import Callable
from pathlib import Path

import pytest

HERE = Path(__file__).resolve().parent
TESTDATA = HERE / "testdata"
SKILL = Path(__file__).resolve().parents[3] / ".apm" / "skills" / "architect-diagram"
if not SKILL.is_dir() or not TESTDATA.is_dir():
    # A wrong parents[] depth must be a red suite, not a silent empty pass.
    raise SystemExit(f"expected {SKILL} and {TESTDATA} to exist")

REFERENCE = SKILL / "references" / "drawio-export.md"
REQUIRED_FIXTURES = ("flowchart-tb", "sequence", "architecture-beta")
LINK_ATTRS = {"link", "href"}
TEXT_ATTRS = ("value", "label", "tooltip")
ANCHOR_OR_HREF = re.compile(r"<a[\s/>]|href\s*=")
ALLOWLIST = [
    "brew install --cask drawio",
    "winget install -e --id JGraph.Draw",
    "sudo snap install drawio",
]
BOUNDARIES = ["filesystem_read_untrusted", "filesystem_write", "network_egress"]


def _strip_controls(text: str) -> str:
    """Remove Unicode control characters (category Cc, includes TAB and LF)."""
    return "".join(c for c in text if unicodedata.category(c) != "Cc")


def _local(name: str) -> str:
    """Return an attribute or tag name without any ``{namespace}`` prefix."""
    return name.rsplit("}", 1)[-1].casefold()


def _cells(model: ET.Element) -> list[tuple[ET.Element, ET.Element | None]]:
    """Pair each root child that carries an id with its ``mxCell`` element.

    ``UserObject``/``object`` wrappers hold the id; the inner ``mxCell`` holds
    the vertex/edge/source/target attributes. A bare ``mxCell`` is its own pair.
    """
    root = model.find("root")
    if root is None:
        return []
    out: list[tuple[ET.Element, ET.Element | None]] = []
    for child in root:
        inner = child if child.tag == "mxCell" else child.find("mxCell")
        out.append((child, inner))
    return out


def check_model(model: ET.Element, *, require_endpoints: bool = False) -> list[str]:
    """Return problems found in one ``mxGraphModel``: ids, vertices, edges.

    CLI sequence output legitimately floats one end of a message edge, so an
    absent endpoint fails only when ``require_endpoints`` is set (the fallback
    skeleton); a present endpoint must always name an existing cell.
    """
    problems: list[str] = []
    cells = _cells(model)
    ids = [c.get("id") for c, _ in cells]
    present = [i for i in ids if i is not None]
    if len(present) != len(set(present)):
        problems.append("duplicate cell id")
    id_set = set(present)
    if not any(inner is not None and inner.get("vertex") == "1" for _, inner in cells):
        problems.append("no vertex")
    for _, inner in cells:
        if inner is None or inner.get("edge") != "1":
            continue
        for end in ("source", "target"):
            ref = inner.get(end)
            if ref is None and require_endpoints:
                problems.append(f"edge has no {end}")
            elif ref is not None and ref not in id_set:
                problems.append(f"edge {end} {ref!r} names no cell")
    return problems


def check_link_safety(tree_root: ET.Element) -> list[str]:
    """Return link-safety problems: link attrs, anchor/href text, bad images."""
    problems: list[str] = []
    for el in tree_root.iter():
        for name, raw in el.attrib.items():
            key = _local(name)
            if key in LINK_ATTRS:
                problems.append(f"{el.tag} carries a {key!r} attribute")
            if key in TEXT_ATTRS and ANCHOR_OR_HREF.search(_strip_controls(raw).casefold()):
                problems.append(f"{key!r} holds an anchor tag or href")
            if key == "style":
                for entry in raw.split(";"):
                    k, sep, v = _strip_controls(entry).partition("=")
                    bad = not "".join(v.split()).startswith("data:image/")
                    if sep and k.strip() == "image" and bad:
                        problems.append("style image= is not a data:image/ URI")
    return problems


def check_drawio_text(
    text: str, sibling: Path | None = None, *, require_endpoints: bool = False
) -> list[str]:
    """Run every structural and link-safety check; return all problems.

    Pass ``sibling`` (the expected ``.mmd`` path) to include the sibling check,
    and ``require_endpoints`` to demand both ends on every edge.
    """
    problems: list[str] = []
    if sibling is not None and not sibling.is_file():
        problems.append(f"missing sibling {sibling.name}")
    try:
        root = ET.fromstring(text)
    except ET.ParseError as exc:
        return [*problems, f"not well-formed XML: {exc}"]
    if root.tag != "mxfile":
        return [*problems, f"root element is {root.tag!r}, not 'mxfile'"]
    diagrams = root.findall("diagram")
    if not diagrams:
        problems.append("no diagram element")
    for diagram in diagrams:
        model = diagram.find("mxGraphModel")
        if model is None:
            problems.append("diagram has no inline mxGraphModel (compressed?)")
        else:
            problems.extend(check_model(model, require_endpoints=require_endpoints))
    problems.extend(check_link_safety(root))
    return problems


def _fixtures() -> list[Path]:
    """Return the shipped ``.drawio`` fixtures, failing loudly if one is absent."""
    found = sorted(TESTDATA.glob("*.drawio"))
    missing = sorted(set(REQUIRED_FIXTURES) - {f.stem for f in found})
    if missing:
        raise SystemExit(f"missing draw.io fixtures: {missing}")
    return found


FIXTURES = _fixtures()


def _fenced(text: str, info: str) -> list[str]:
    """Return bodies of every code fence whose info string is exactly ``info``."""
    pattern = r"^```" + re.escape(info) + r"[ \t]*\n(.*?)^```[ \t]*$"
    return re.findall(pattern, text, flags=re.S | re.M)


@pytest.mark.parametrize("fixture", FIXTURES, ids=[f.stem for f in FIXTURES])
def test_fixture_is_valid(fixture: Path) -> None:
    problems = check_drawio_text(
        fixture.read_text(encoding="utf-8"), fixture.with_suffix(".mmd")
    )
    assert not problems, problems


def test_reference_skeleton_is_valid() -> None:
    blocks = _fenced(REFERENCE.read_text(encoding="utf-8"), "xml")
    assert len(blocks) == 1, f"expected exactly one xml block, found {len(blocks)}"
    assert not check_drawio_text(blocks[0], require_endpoints=True)
    root = ET.fromstring(blocks[0])
    html_cells = [
        el.get("style")
        for el in root.iter()
        if re.search(r"(^|;)\s*html=1\s*(;|$)", el.get("style") or "")
    ]
    assert not html_cells, f"skeleton styles set html=1: {html_cells}"


def test_reference_install_allowlist() -> None:
    blocks = _fenced(REFERENCE.read_text(encoding="utf-8"), "text install-allowlist")
    assert len(blocks) == 1, f"expected one install-allowlist block, found {len(blocks)}"
    lines = [ln.strip() for ln in blocks[0].splitlines() if ln.strip()]
    assert lines == ALLOWLIST


def test_skill_boundaries() -> None:
    text = (SKILL / "SKILL.md").read_text(encoding="utf-8")
    front = re.match(r"---\n(.*?)\n---", text, flags=re.S)
    assert front, "SKILL.md has no frontmatter"
    match = re.search(
        r"^metadata:\s*\n(?:[ \t]+.*\n)*?[ \t]+boundaries:\s*\[(.*?)\]",
        front.group(1) + "\n",
        flags=re.M,
    )
    assert match, "frontmatter has no metadata.boundaries list"
    assert [b.strip() for b in match.group(1).split(",")] == BOUNDARIES


# --- AC-0005: every check must be able to fail -------------------------------

BASE = TESTDATA / "flowchart-tb.drawio"


def _vertex_pair(root: ET.Element) -> ET.Element:
    """Return the first label-bearing wrapper element in the base fixture."""
    return next(el for el in root.iter() if el.tag in {"UserObject", "object"})


def _edge_cell(root: ET.Element) -> ET.Element:
    """Return the first ``mxCell`` that is an edge with a source."""
    return next(
        el for el in root.iter("mxCell") if el.get("edge") == "1" and el.get("source")
    )


def _compress(root: ET.Element) -> None:
    diagram = root.find("diagram")
    assert diagram is not None
    model = diagram.find("mxGraphModel")
    assert model is not None
    diagram.remove(model)
    diagram.text = "7VpLc9s2EP41PHaGLz107DjtoXXjTpq0nR4ZEiJhgwQLgJL8613wAYIAKT"


def _no_vertex(root: ET.Element) -> None:
    for el in root.iter("mxCell"):
        el.attrib.pop("vertex", None)


def _dup_id(root: ET.Element) -> None:
    wrappers = [el for el in root.iter() if el.tag in {"UserObject", "object"}]
    wrappers[1].set("id", wrappers[0].get("id", ""))


def _dangling(root: ET.Element) -> None:
    _edge_cell(root).set("source", "no-such-cell")


def _link_attr(root: ET.Element) -> None:
    _vertex_pair(root).set("link", "https://example.invalid/")


def _anchor_label(root: ET.Element) -> None:
    _vertex_pair(root).set("label", '<a href="x">go</a>')


def _bad_image(root: ET.Element) -> None:
    _vertex_pair(root).find("mxCell").set("style", "shape=image;image=java\tscript:alert(1);")  # type: ignore[union-attr]


def _label(text: str) -> Callable[[ET.Element], None]:
    def apply(root: ET.Element) -> None:
        _vertex_pair(root).set("label", text)

    return apply


def _mutated(mutate: Callable[[ET.Element], None], tmp_path: Path, *, sibling: bool = True) -> list[str]:
    """Apply ``mutate`` to a copy of the base fixture and run the checker."""
    root = ET.fromstring(BASE.read_text(encoding="utf-8"))
    mutate(root)
    out = tmp_path / "case.drawio"
    out.write_text(ET.tostring(root, encoding="unicode"), encoding="utf-8")
    if sibling:
        (tmp_path / "case.mmd").write_text("graph TD\n  A-->B\n", encoding="utf-8")
    return check_drawio_text(out.read_text(encoding="utf-8"), out.with_suffix(".mmd"))


REJECTED = {
    "compressed": _compress,
    "no-vertex": _no_vertex,
    "duplicate-id": _dup_id,
    "dangling-edge": _dangling,
    "link-attribute": _link_attr,
    "anchor-in-label": _anchor_label,
    "script-image": _bad_image,
}


def test_unmutated_copy_passes(tmp_path: Path) -> None:
    assert _mutated(lambda root: None, tmp_path) == []


def test_missing_sibling_rejected(tmp_path: Path) -> None:
    assert _mutated(lambda root: None, tmp_path, sibling=False)


@pytest.mark.parametrize("name", list(REJECTED))
def test_mutation_rejected(name: str, tmp_path: Path) -> None:
    assert _mutated(REJECTED[name], tmp_path), f"{name} was not rejected"


@pytest.mark.parametrize("text", ["Metadata: store", "a < b", "x <and y"])
def test_control_label_passes(text: str, tmp_path: Path) -> None:
    assert _mutated(_label(text), tmp_path) == []


def test_skeleton_edge_without_source_rejected() -> None:
    block = _fenced(REFERENCE.read_text(encoding="utf-8"), "xml")[0]
    root = ET.fromstring(block)
    edge = next(el for el in root.iter("mxCell") if el.get("edge") == "1")
    del edge.attrib["source"]
    problems = check_drawio_text(ET.tostring(root, encoding="unicode"), require_endpoints=True)
    assert "edge has no source" in problems
