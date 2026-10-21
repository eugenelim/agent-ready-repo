#!/usr/bin/env python3
"""Rewrite untyped intent-valued spec `Discovery:` headers to `<kind>:<slug>`.

Working material for the typed-discovery-pointers spec. Standard library only.

The cohort is derived from the current `docs/specs/*/spec.md` preambles: every
active `Discovery:` value the shared forward check classifies as
`discovery-untyped` (a path or markdown link naming `product/intents/`, or a bare
live slug). Each is resolved to its target intent file, `Slug:`, and registered
kind (using the shared check's own parser and index). A candidate whose target is
missing, retired, ambiguous, slug-less, or of undeterminable kind is REFUSED:
reported, never rewritten, never guessed.

Only the header value changes. The bullet prefix, a trailing same-line comment,
and the line ending are preserved byte for byte.

Usage:
    sweep_discovery.py [--root DIR] [--check] [--manifest PATH]
    sweep_discovery.py --selftest

Exit: 0 nothing to do, 1 changes pending (--check only), 2 refusals present.
The manifest is written only when files are rewritten, so a repeat run leaves it
and every spec untouched.
"""

from __future__ import annotations

import argparse
import importlib.util
import posixpath
import re
import shutil
import sys
import tempfile
from dataclasses import dataclass
from pathlib import Path
from types import ModuleType

TOOL_ROOT = Path(__file__).resolve().parents[4]
LINT_REL = "packs/core/.apm/skills/work-loop/scripts/lint-graph-pointers.py"
INTENTS_DIR = "docs/product/intents"
_INTENT_FILE_RE = re.compile(r"^docs/product/intents/[^/]+\.md$")
_DISCOVERY_LINE_RE = re.compile(r"^(- \*\*Discovery:\*\*[ \t]*)(.*?)([ \t]*<!--.*)?$", re.DOTALL)


def load_lint(tool_root: Path = TOOL_ROOT) -> ModuleType:
    """Load the shared forward check by path under a unique module name."""
    name = "typed_discovery_sweep_lint_graph_pointers"
    spec = importlib.util.spec_from_file_location(name, tool_root / LINT_REL)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


@dataclass
class Candidate:
    spec: str
    old: str
    target: str = ""
    slug: str = ""
    kind: str = ""
    replacement: str = ""
    refusal: str = ""
    line_no: int = 0


def intent_files(root: Path, lint: ModuleType) -> dict[str, dict[str, list[str]]]:
    """Repo-relative intent file -> its preamble fields."""
    found: dict[str, dict[str, list[str]]] = {}
    base = root / INTENTS_DIR
    if not base.is_dir():
        return found
    for path in sorted(base.glob("*.md")):
        if path.is_symlink() or not path.is_file():
            continue
        found[f"{INTENTS_DIR}/{path.name}"] = lint._preamble(path.read_text(encoding="utf-8"))
    return found


def target_path(value: str, spec_dir: str) -> str:
    """Repository path an intents-path or link value names, '' when not derivable."""
    link = re.match(r"\[[^\]]*\]\(\s*<?([^)\s>]*)", value)
    raw = link.group(1) if link else value
    raw = raw.split("#", 1)[0].split("?", 1)[0].strip("`")
    joined = raw.lstrip("/") if raw.startswith("/") else f"{spec_dir}/{raw}"
    if not link and not raw.startswith("/") and raw.startswith(INTENTS_DIR + "/"):
        joined = raw
    return posixpath.normpath(joined)


def resolve(value: str, spec_dir: str, files: dict[str, dict[str, list[str]]],
            intents: object, lint: ModuleType) -> Candidate:
    cand = Candidate(spec="", old=value)
    if lint._SLUG_RE.fullmatch(value):
        matches = [p for p, f in files.items() if (f.get("Slug") or [""])[0] == value]
        if len(matches) != 1:
            cand.refusal = f"bare slug matches {len(matches)} intent files"
            return cand
        cand.target = matches[0]
    else:
        cand.target = target_path(value, spec_dir)
        if not _INTENT_FILE_RE.fullmatch(cand.target):
            cand.refusal = (
                "value does not resolve to one file directly under docs/product/intents/"
            )
            return cand
        if cand.target not in files:
            cand.refusal = "target intent file is missing"
            return cand
    fields = files[cand.target]
    cand.slug = (fields.get("Slug") or [""])[0]
    if not lint._SLUG_RE.fullmatch(cand.slug):
        cand.refusal = "target has no valid Slug:"
    elif any(fields.get("Tombstone", [])):
        cand.refusal = "target is retired (Tombstone)"
    elif cand.slug in intents.ambiguous:  # type: ignore[attr-defined]
        cand.refusal = "slug names more than one live intent"
    elif cand.slug not in intents.live:  # type: ignore[attr-defined]
        cand.refusal = "slug is not a live intent"
    else:
        cand.kind = lint._registered_kind(fields)
        if intents.live[cand.slug] != cand.kind:  # type: ignore[attr-defined]
            cand.refusal = "registered kind is not determinable consistently"
        else:
            cand.replacement = f"{cand.kind}:{cand.slug}"
    return cand


def sweep_spec(text: str, spec_rel: str, files: dict[str, dict[str, list[str]]],
               intents: object, lint: ModuleType) -> tuple[str, list[Candidate]]:
    """Return the rewritten text and the candidates found in one spec preamble."""
    spec_dir = posixpath.dirname(spec_rel)
    lines = text.splitlines(keepends=True)
    out: list[Candidate] = []
    inside = False
    for i, line in enumerate(lines):
        visible, inside = lint._visible_line(line, inside)
        if visible.startswith(lint._HEADING_PREFIX):
            break
        match = lint._FIELD_LINE_RE.match(visible)
        if not match or match.group(1).strip() != "Discovery":
            continue
        value = lint._clean(match.group(2))
        if lint._check_discovery(value, intents, spec_dir) != "discovery-untyped":
            continue
        cand = resolve(value, spec_dir, files, intents, lint)
        cand.spec, cand.line_no = spec_rel, i + 1
        body = line.rstrip("\r\n")
        eol = line[len(body):]
        parts = _DISCOVERY_LINE_RE.match(body)
        if not cand.refusal and (not parts or lint._clean(parts.group(2)) != value):
            cand.refusal = "header line shape not rewritable (multi-line comment or odd spacing)"
        if not cand.refusal:
            assert parts
            shown = parts.group(2).strip()
            wrapped = shown.startswith("`") and shown.endswith("`")
            new_value = f"`{cand.replacement}`" if wrapped else cand.replacement
            lines[i] = f"{parts.group(1)}{new_value}{parts.group(3) or ''}{eol}"
        out.append(cand)
    return "".join(lines), out


def run(root: Path, check: bool, manifest: Path, tool_root: Path = TOOL_ROOT) -> int:
    lint = load_lint(tool_root)
    intents, _briefs = lint._build_indexes(root)
    files = intent_files(root, lint)
    rewritten: list[Candidate] = []
    refused: list[Candidate] = []
    for spec in sorted((root / "docs/specs").glob("*/spec.md")):
        if spec.is_symlink() or not spec.is_file():
            continue
        rel = spec.relative_to(root).as_posix()
        raw = spec.read_bytes()
        new_text, cands = sweep_spec(raw.decode("utf-8"), rel, files, intents, lint)
        good = [c for c in cands if not c.refusal]
        refused += [c for c in cands if c.refusal]
        if good:
            rewritten += good
            if not check:
                spec.write_bytes(new_text.encode("utf-8"))
    for c in refused:
        print(f"REFUSED {c.spec}:{c.line_no} {c.old!r}: {c.refusal} (target {c.target or 'n/a'})")
    verb = "would rewrite" if check else "rewrote"
    n_specs = len({c.spec for c in rewritten})
    print(f"{verb} {len(rewritten)} header value(s) in {n_specs} spec(s); {len(refused)} refused")
    if rewritten and not check:
        write_manifest(manifest, rewritten)
    if refused:
        return 2
    return 1 if (check and rewritten) else 0


def write_manifest(path: Path, rows: list[Candidate]) -> None:
    lines = [
        "# Discovery sweep manifest", "",
        f"Generated by `sweep_discovery.py`. {len(rows)} header value(s) in "
        f"{len({c.spec for c in rows})} spec(s) rewritten to the target's registered kind "
        "and slug.", "",
        "| Spec | Old value | Target | Slug | Registered kind | Replacement |",
        "| --- | --- | --- | --- | --- | --- |",
    ]
    for c in rows:
        old = c.old.replace("|", "\\|")
        lines.append(
            f"| `{c.spec}` | `{old}` | `{c.target}` | `{c.slug}` | `{c.kind}` "
            f"| `{c.replacement}` |"
        )
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def selftest() -> int:
    """Fixture check: refusals are reported, never rewritten; accepted values round-trip."""
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        intents = root / INTENTS_DIR
        intents.mkdir(parents=True)
        good = "# G\n\n- **Slug:** good\n- **Kind:** outcome\n"
        (intents / "good.md").write_text(good, encoding="utf-8")
        gone = "# R\n\n- **Slug:** gone\n- **Tombstone:** yes\n"
        (intents / "gone.md").write_text(gone, encoding="utf-8")
        (intents / "noslug.md").write_text("# N\n\n- **Level:** capability\n", encoding="utf-8")
        specs = {
            "ok": "# S\n\n- **Discovery:** `docs/product/intents/good.md` <!-- note -->\n\n"
            "## Outcome\n",
            "missing": "# S\n\n- **Discovery:** docs/product/intents/absent.md\n\n## Outcome\n",
            "retired": "# S\n\n- **Discovery:** docs/product/intents/gone.md\n\n## Outcome\n",
            "noslug": "# S\n\n- **Discovery:** docs/product/intents/noslug.md\n\n## Outcome\n",
        }
        for name, body in specs.items():
            d = root / "docs/specs" / name
            d.mkdir(parents=True)
            data = body.replace("\n", "\r\n") if name == "ok" else body
            (d / "spec.md").write_bytes(data.encode())
        before = {n: (root / "docs/specs" / n / "spec.md").read_bytes() for n in specs}
        manifest = root / "manifest.md"
        code = run(root, False, manifest)
        after = {n: (root / "docs/specs" / n / "spec.md").read_bytes() for n in specs}
        assert code == 2, code
        for n in ("missing", "retired", "noslug"):
            assert after[n] == before[n], f"{n} was rewritten"
        want = before["ok"].replace(b"`docs/product/intents/good.md`", b"`outcome:good`")
        assert after["ok"] == want, after["ok"]
        second = run(root, False, manifest)
        again = {n: (root / "docs/specs" / n / "spec.md").read_bytes() for n in specs}
        assert second == 2 and again == after
        shutil.rmtree(root / "docs/specs/ok")
    print(
        "selftest: refusals reported and unchanged; accepted value rewrote only its value "
        "(CRLF and comment kept); repeat run empty"
    )
    return 0


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--root", default=".")
    ap.add_argument("--check", action="store_true", help="dry run: report, change nothing")
    ap.add_argument("--manifest", default=str(Path(__file__).with_name("sweep-manifest.md")))
    ap.add_argument("--selftest", action="store_true")
    args = ap.parse_args(argv)
    if args.selftest:
        return selftest()
    return run(Path(args.root).resolve(), args.check, Path(args.manifest))


if __name__ == "__main__":
    raise SystemExit(main())
