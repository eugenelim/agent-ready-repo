#!/usr/bin/env python3
"""
Aggregate repo content into site/docs/ for the MkDocs build.

Copies:
  packs/*/README.md         → site/docs/packs/<name>.md
  docs/guides/**            → site/docs/guides/**
  docs/product/changelog.md → site/docs/changelog.md  (links rewritten)
  CONTRIBUTING.md           → site/docs/contributing.md (links rewritten)

Generates:
  site/docs/packs/index.md  (pack catalogue summary page)

Usage:
  python tools/build-site.py
  python tools/build-site.py --dry-run
  python tools/build-site.py --clean
"""
import argparse
import re
import shutil
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).parent.parent.resolve()
SITE_DOCS = REPO_ROOT / "site" / "docs"
GITHUB_BASE = "https://github.com/eugenelim/agent-ready-repo/blob/main"

PACKS: list[tuple[str, str, str, str]] = [
    ("core",               "Core",                "repo", "The build loop — `work-loop`, `new-spec`, `bug-fix`, four specialist reviewers, hooks. **Install this first.**"),
    ("product-engineering","Product Engineering",  "user", "The discovery loop — raw idea to ratified brief with human consent at G0, G1.5, G2."),
    ("release-engineering","Release Engineering",  "repo", "The release loop — autonomous e2e convergence on ephemeral environments; prod gate is always human."),
    ("desk-research",      "Desk Research",         "user", "Evidence-grounded research with typed artifacts, seven skills, and two retrieval subagents."),
    ("architect",          "Architect",            "user", "System design, diagramming, and independent architecture review from a forked-context subagent."),
    ("experience-design",  "Experience Design",    "user", "The full design thread: journey mapping, screen flows, creative direction, surface-genre design (6 types), and the shared quality floor."),
    ("contracts",          "Contracts",            "user", "API-first design — OpenAPI 3.1 for HTTP, AsyncAPI for event streams."),
    ("converters",         "Converters",           "user", "Document conversion: PDF/DOCX/PPTX/email → Markdown, Markdown → HTML/Word/PowerPoint/Excel."),
    ("atlassian",          "Atlassian",            "user", "Jira and Confluence from the agent — SSO-cookie authenticated, flow and DORA metrics built in."),
    ("figma",              "Figma",                "user", "Read and render Figma designs — files, nodes, variables, frame renders, FigJam → Mermaid."),
    ("governance-extras",  "Governance Extras",    "repo", "RFC/ADR ceremony for long-lived repos: `new-rfc`, `new-adr`, `update-conventions`."),
    ("user-guide-diataxis","User Guide (Diataxis)", "repo", "Diátaxis docs scaffold — four content modes with the `new-guide` skill."),
    ("monorepo-extras",    "Monorepo Extras",       "repo", "Package scaffolding — `new-package` skill with an example package template."),
    ("credential-brokers", "Credential Brokers",    "user", "In-process credential resolution: environment → OS keyring → dotfile. Cleartext never reaches the model."),
    ("product-strategy",   "Product Strategy",      "user", "The strategy seat upstream of product engineering — market analysis (SWOT, Porter, PESTLE, BCG), OKR cascade, PRD writing, stakeholder synthesis, UX strategy, and content strategy."),
]

PACK_INDEX_HEADER = """\
# Pack Catalogue

Fifteen curated packs — each distilled from the best practices of its discipline
through practitioner research and RFC-and-ADR governance.

Install any pack in one command:

```bash
agentbundle install --pack <name>               # repo scope (default)
agentbundle install --pack <name> --scope user  # user scope
```

| Pack | Scope | Description |
|---|---|---|
"""

# ---------------------------------------------------------------------------
# Link rewriters
# ---------------------------------------------------------------------------

def _rewrite_changelog(text: str) -> str:
    """Fix links in changelog.md when moved from docs/product/ to site/docs/.

    In source: relative to docs/product/changelog.md
      ../guides/... → guides/...  (in-site, rewrite)
      ../rfc/...    → GitHub URL  (not in site)
      ../specs/...  → GitHub URL  (not in site)
    """
    def replace(m: re.Match) -> str:
        prefix, path, anchor = m.group(1), m.group(2), m.group(3) or ""
        if path.startswith("../guides/"):
            # Strip the leading ../
            return f"{prefix}{path[3:]}{anchor})"
        if path.startswith("../"):
            # Convert to GitHub URL
            clean = path[3:]  # remove ../
            return f"{prefix}{GITHUB_BASE}/{clean}{anchor})"
        return m.group(0)

    # Match markdown links: [text](path#anchor)
    return re.sub(r'(\]\()(\.\./[^)#]*)(#[^)]+)?\)', replace, text)


def _rewrite_pack_readme(text: str, pack_src_path: Path) -> str:
    """Rewrite links in pack READMEs moved from packs/<slug>/README.md to site/docs/packs/<slug>.md.

    Cross-pack links (../other-pack/README.md) → other-pack.md (within site/docs/packs/).
    Links outside packs/ that resolve in the repo → GitHub URL.
    """
    packs_root = (REPO_ROOT / "packs").resolve()
    repo_root = REPO_ROOT.resolve()

    def replace(m: re.Match) -> str:
        prefix, path, anchor = m.group(1), m.group(2), m.group(3) or ""
        if not path or path.startswith("http://") or path.startswith("https://") or path.startswith("#"):
            return m.group(0)
        try:
            resolved = (pack_src_path.parent / path).resolve()
        except Exception:
            return m.group(0)

        if _is_relative_to(resolved, packs_root):
            # e.g. ../credential-brokers/README.md → credential-brokers.md
            rel = resolved.relative_to(packs_root)
            pack_name = rel.parts[0]
            return f"{prefix}{pack_name}.md{anchor})"

        if _is_relative_to(resolved, repo_root):
            rel = resolved.relative_to(repo_root)
            return f"{prefix}{GITHUB_BASE}/{rel}{anchor})"

        return m.group(0)

    return re.sub(r'(\]\()([^)#"\'\s]+)(#[^)]+)?\)', replace, text)


def _rewrite_guide(text: str, guide_src_path: Path) -> str:
    """Rewrite links in guide files that exit the guides tree.

    Links within docs/guides/ are kept as-is (they work in the site).
    Links that resolve within the repo but outside docs/guides/ are
    converted to GitHub URLs so they don't produce dead references.
    """
    guides_root = (REPO_ROOT / "docs" / "guides").resolve()
    repo_root = REPO_ROOT.resolve()

    def replace(m: re.Match) -> str:
        prefix, path, anchor = m.group(1), m.group(2), m.group(3) or ""
        if not path or path.startswith("http://") or path.startswith("https://") or path.startswith("#"):
            return m.group(0)

        # Resolve the link relative to the guide file's source position
        try:
            resolved = (guide_src_path.parent / path).resolve()
        except Exception:
            return m.group(0)

        # Within guides/ → check existence and handle directory links
        if _is_relative_to(resolved, guides_root):
            if resolved.is_dir():
                # Bare directory link (e.g. `_shared/`) → README.md
                readme = resolved / "README.md"
                if readme.exists():
                    # Rewrite to point at the README directly
                    rel_guide = guide_src_path.parent
                    rel_readme = readme.resolve()
                    try:
                        rel = rel_readme.relative_to(rel_guide.resolve())
                        return f"{prefix}{rel}{anchor})"
                    except ValueError:
                        pass
            elif resolved.exists():
                return m.group(0)
            # Stale or unresolvable link within guides/ — fall through to GitHub URL

        # Within repo but outside guides/ → GitHub URL
        if _is_relative_to(resolved, repo_root):
            rel = resolved.relative_to(repo_root)
            return f"{prefix}{GITHUB_BASE}/{rel}{anchor})"

        # Outside repo or unresolvable → leave as-is
        return m.group(0)

    return re.sub(r'(\]\()([^)#"\'\s]+)(#[^)]+)?\)', replace, text)


def _is_relative_to(path: Path, base: Path) -> bool:
    try:
        path.relative_to(base)
        return True
    except ValueError:
        return False


def _rewrite_contributing(text: str) -> str:
    """Fix links in CONTRIBUTING.md when placed at site/docs/contributing.md.

    CONTRIBUTING.md lives at the repo root; links are repo-root-relative.
    Most targets (AGENTS.md, docs/CONVENTIONS.md, etc.) aren't in the site,
    so we convert them to GitHub URLs using proper Path resolution.
    """
    contributing_src = REPO_ROOT / "CONTRIBUTING.md"
    repo_root = REPO_ROOT.resolve()
    guides_root = (REPO_ROOT / "docs" / "guides").resolve()

    def replace(m: re.Match) -> str:
        prefix, path, anchor = m.group(1), m.group(2), m.group(3) or ""
        if not path or path.startswith("http://") or path.startswith("https://") or path.startswith("#"):
            return m.group(0)
        try:
            resolved = (contributing_src.parent / path).resolve()
        except Exception:
            return m.group(0)

        # Links within guides/ → site-relative (guides/ is in the site)
        if _is_relative_to(resolved, guides_root):
            rel = resolved.relative_to(guides_root)
            return f"{prefix}guides/{rel}{anchor})"

        # Any other repo-relative link → GitHub URL
        if _is_relative_to(resolved, repo_root):
            rel = resolved.relative_to(repo_root)
            return f"{prefix}{GITHUB_BASE}/{rel}{anchor})"

        return m.group(0)

    return re.sub(r'(\]\()([^)#"\'\s]+)(#[^)]+)?\)', replace, text)


# ---------------------------------------------------------------------------
# Core operations
# ---------------------------------------------------------------------------

def copy_file(src: Path, dst: Path, rewriter=None, dry_run: bool = False) -> None:
    """Copy src to dst, applying an optional rewriter(text) → text transform."""
    if dry_run:
        print(f"  copy  {src.relative_to(REPO_ROOT)} → {dst.relative_to(REPO_ROOT)}")
        return
    dst.parent.mkdir(parents=True, exist_ok=True)
    text = src.read_text(encoding="utf-8")
    if rewriter:
        text = rewriter(text)
    dst.write_text(text, encoding="utf-8")


def mirror_dir(src: Path, dst: Path, rewriter=None, dry_run: bool = False) -> int:
    """Mirror src into dst, applying an optional per-file rewriter to .md files."""
    count = 0
    if not src.exists():
        print(f"  warn  source dir missing: {src.relative_to(REPO_ROOT)}", file=sys.stderr)
        return 0
    for path in sorted(src.rglob("*")):
        if path.is_file():
            rel = path.relative_to(src)
            target = dst / rel
            if dry_run:
                print(f"  copy  {path.relative_to(REPO_ROOT)} → {target.relative_to(REPO_ROOT)}")
            else:
                target.parent.mkdir(parents=True, exist_ok=True)
                if rewriter and path.suffix == ".md":
                    text = path.read_text(encoding="utf-8")
                    target.write_text(rewriter(text, path), encoding="utf-8")
                else:
                    shutil.copy2(path, target)
            count += 1
    return count


def build_pack_index(packs_dir: Path, out_dir: Path, dry_run: bool = False) -> None:
    lines = [PACK_INDEX_HEADER]
    for slug, display, scope, description in PACKS:
        lines.append(f"| [**{display}**]({slug}.md) | `{scope}` | {description} |\n")

    content = "".join(lines)
    index_md = out_dir / "index.md"
    if dry_run:
        print(f"  gen   site/docs/packs/index.md ({len(content)} bytes)")
    else:
        index_md.write_text(content, encoding="utf-8")


def write_siteignore(paths: list[Path], dry_run: bool = False) -> None:
    lines = [
        "# Generated by tools/build-site.py — do not commit these paths.\n",
        "# These are listed in .gitignore at the repo root.\n\n",
    ]
    for p in sorted(paths):
        try:
            rel = str(p.relative_to(SITE_DOCS))
        except ValueError:
            rel = str(p)
        lines.append(f"{rel}\n")
    if not dry_run:
        (SITE_DOCS / ".siteignore").write_text("".join(lines), encoding="utf-8")


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--clean", action="store_true")
    args = parser.parse_args()

    packs_dir = REPO_ROOT / "packs"
    packs_out = SITE_DOCS / "packs"
    guides_src = REPO_ROOT / "docs" / "guides"
    guides_out = SITE_DOCS / "guides"
    generated = [packs_out, guides_out]

    if args.clean and not args.dry_run:
        for d in (packs_out, guides_out):
            if d.exists():
                shutil.rmtree(d)
                print(f"  clean {d.relative_to(REPO_ROOT)}/")

    print("build-site: copying pack READMEs …")
    packs_out.mkdir(parents=True, exist_ok=True)
    for slug, *_ in PACKS:
        src = packs_dir / slug / "README.md"
        dst = packs_out / f"{slug}.md"
        if src.exists():
            copy_file(src, dst, rewriter=lambda t, p=src: _rewrite_pack_readme(t, p), dry_run=args.dry_run)
        else:
            print(f"  warn  packs/{slug}/README.md missing", file=sys.stderr)

    print("build-site: generating packs/index.md …")
    build_pack_index(packs_dir, packs_out, dry_run=args.dry_run)

    print("build-site: mirroring guides …")
    n = mirror_dir(guides_src, guides_out, rewriter=_rewrite_guide, dry_run=args.dry_run)
    print(f"  {n} files from docs/guides/")

    print("build-site: copying changelog …")
    changelog_src = REPO_ROOT / "docs" / "product" / "changelog.md"
    changelog_dst = SITE_DOCS / "changelog.md"
    if changelog_src.exists():
        copy_file(changelog_src, changelog_dst, rewriter=_rewrite_changelog, dry_run=args.dry_run)
        generated.append(changelog_dst)
    else:
        print("  warn  docs/product/changelog.md missing", file=sys.stderr)

    print("build-site: copying contributing guide …")
    contributing_src = REPO_ROOT / "CONTRIBUTING.md"
    contributing_dst = SITE_DOCS / "contributing.md"
    if contributing_src.exists():
        copy_file(contributing_src, contributing_dst, rewriter=_rewrite_contributing, dry_run=args.dry_run)
        generated.append(contributing_dst)
    else:
        print("  warn  CONTRIBUTING.md missing", file=sys.stderr)

    write_siteignore(generated, dry_run=args.dry_run)
    print("build-site: done." + (" (dry run)" if args.dry_run else ""))


if __name__ == "__main__":
    main()
