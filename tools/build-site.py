#!/usr/bin/env python3
"""
Aggregate repo content into docs-site/src/content/docs/ for the Starlight build.

Copies:
  packs/*/README.md         → docs-site/src/content/docs/packs/<name>.md
  guides/**                 → docs-site/src/content/docs/guides/**
                              (README.md renamed to index.md; frontmatter injected)
  docs/product/changelog.md → docs-site/src/content/docs/changelog.md (links rewritten)
  CONTRIBUTING.md           → docs-site/src/content/docs/contributing.md (links rewritten)

Generates:
  docs-site/src/content/docs/packs/index.md  (pack catalogue summary page)

Copies:
  web/src/styles/tokens.css → docs-site/src/styles/tokens.css
  (gitignored target; imported by docs-site/src/styles/starlight.css at build time)

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
SITE_DOCS = REPO_ROOT / "docs-site" / "src" / "content" / "docs"
GITHUB_BASE = "https://github.com/eugenelim/agent-ready-repo/blob/main"

PACKS: list[tuple[str, str, str, str]] = [
    ("core",               "Core",                "repo", "The build loop — `work-loop`, `new-spec`, `bug-fix`, four specialist reviewers, hooks. **Install this first.**"),
    ("product-engineering","Product Engineering",  "user", "The discovery loop — raw idea to ratified brief with human consent at G0, G1.5, G2."),
    ("release-engineering","Release Engineering",  "repo", "The release loop — autonomous e2e convergence on ephemeral environments; prod gate is always human."),
    ("desk-research",      "Desk Research",         "user", "Evidence-grounded research with typed artifacts, seven skills, and two retrieval subagents."),
    ("architect",          "Architect",            "user", "System design, diagramming, and independent architecture review from a forked-context subagent."),
    ("experience-design",  "Experience Design",    "user", "The full design thread: journey mapping, screen flows, creative direction, surface-genre design (6 types), and the shared quality floor."),
    ("contracts",          "Contracts",            "user", "API-first design — OpenAPI 3.1 for HTTP, AsyncAPI for event streams."),
    ("iac-terraform",      "IaC (Terraform)",       "repo", "Plain-language intent → governed, cloud-agnostic Terraform and a human-gated pipeline; decision-record-gated, stops at `terraform plan`."),
    ("converters",         "Converters",           "user", "Document conversion: PDF/DOCX/PPTX/email → Markdown, Markdown → HTML/Word/PowerPoint/Excel."),
    ("atlassian",          "Atlassian",            "user", "Jira and Confluence from the agent — SSO-cookie authenticated, flow and DORA metrics built in."),
    ("figma",              "Figma",                "user", "Read and render Figma designs — files, nodes, variables, frame renders, FigJam → Mermaid."),
    ("governance-extras",  "Governance Extras",    "repo", "RFC/ADR ceremony for long-lived repos: `new-rfc`, `new-adr`, `update-conventions`."),
    ("user-guide-diataxis","User Guide (Diataxis)", "repo", "Diátaxis docs scaffold — four content modes with the `new-guide` skill."),
    ("monorepo-extras",    "Monorepo Extras",       "repo", "Package scaffolding — `new-package` skill with an example package template."),
    ("catalogue-curation", "Catalogue Curation",    "repo", "Catalogue-operator toolkit — assimilate external primitives, survey repos, propose packs, and export white-label or attributed forks."),
    ("credential-brokers", "Credential Brokers",    "user", "In-process credential resolution: environment → OS keyring → dotfile. Cleartext never reaches the model."),
    ("product-strategy",   "Product Strategy",      "user", "The strategy seat upstream of product engineering — market analysis (SWOT, Porter, PESTLE, BCG), OKR cascade, PRD writing, stakeholder synthesis, UX strategy, and content strategy."),
]

# Starlight requires `title` frontmatter — inject it at the top of the
# index header so the generated packs/index.md has a valid schema.
PACK_INDEX_HEADER = f"""\
---
title: "Pack Catalogue"
description: "{len(PACKS)} curated packs for the AI operating model."
---

# Pack Catalogue

{len(PACKS)} curated packs — each distilled from the best practices of its discipline
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
# Frontmatter injection
# ---------------------------------------------------------------------------

def _inject_frontmatter(text: str, path: Path) -> str:
    """Prepend minimal Starlight frontmatter (title: ) if none present.

    Starlight's docsSchema() requires a `title` field. Files without YAML
    frontmatter get one derived from their first H1 heading, or from the
    filename as a fallback.
    """
    if text.startswith("---"):
        return text  # already has frontmatter
    # Extract first H1 as the title, then strip it from the body so Starlight
    # doesn't render it as a second <h1> beneath its generated page title.
    m = re.search(r"^#\s+(.+)$", text, re.MULTILINE)
    if m:
        title = m.group(1).strip().replace('"', '\\"')
        # Remove the H1 line (and any blank line immediately after it) from body
        body = text[: m.start()] + text[m.end() :]
        body = body.lstrip("\n")
    else:
        title = path.stem.replace("-", " ").replace("_", " ").title()
        body = text
    return f'---\ntitle: "{title}"\n---\n\n' + body


# ---------------------------------------------------------------------------
# Link rewriters
# ---------------------------------------------------------------------------

def _strip_md_suffixes(text: str) -> str:
    """Strip .md suffixes from intra-site markdown links.

    Starlight serves content at clean URLs (no .md). Links like
    [label](other-file.md) and [label](path/README.md) must become
    [label](other-file/) and [label](path/) so they resolve correctly.

    External links (http/https) are never touched.
    """
    def replace(m: re.Match) -> str:
        prefix, path, anchor = m.group(1), m.group(2), m.group(3) or ""
        # Skip external links and anchor-only links
        if not path or path.startswith(("http://", "https://", "#")):
            return m.group(0)
        if path.endswith(".md"):
            # README.md → ../../ style; otherwise strip .md, add /
            if path.endswith("/README.md"):
                path = path[: -len("README.md")]  # e.g. "foo/README.md" → "foo/"
            elif path == "README.md":
                path = "./"
            else:
                path = path[:-3] + "/"  # strip .md, add /
        return f"{prefix}{path}{anchor})"

    return re.sub(r"(\]\()([^)#\"'\s]+)(#[^)]+)?\)", replace, text)


def _rewrite_changelog(text: str) -> str:
    """Fix links in changelog.md when moved from docs/product/ to docs-site content.

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

    result = re.sub(r"(\]\()(\.\./[^)#]*)(#[^)]+)?\)", replace, text)
    return _strip_md_suffixes(result)


def _rewrite_pack_readme(text: str, pack_src_path: Path) -> str:
    """Rewrite links in pack READMEs moved from packs/<slug>/README.md
    to docs-site/src/content/docs/packs/<slug>.md.

    Cross-pack links (../other-pack/README.md) → other-pack/
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
            # e.g. ../credential-brokers/README.md → ../credential-brokers/
            rel = resolved.relative_to(packs_root)
            pack_name = rel.parts[0]
            return f"{prefix}{pack_name}/{anchor})"

        if _is_relative_to(resolved, repo_root):
            rel = resolved.relative_to(repo_root)
            return f"{prefix}{GITHUB_BASE}/{rel}{anchor})"

        return m.group(0)

    result = re.sub(r"(\]\()([^)#\"'\s]+)(#[^)]+)?\)", replace, text)
    return _strip_md_suffixes(result)


def _rewrite_guide(text: str, guide_src_path: Path) -> str:
    """Rewrite links in guide files that exit the guides tree.

    Links within guides/ are normalised to relative Starlight URLs.
    Links that resolve within the repo but outside guides/ are
    converted to GitHub URLs so they don't produce dead references.
    """
    guides_root = (REPO_ROOT / "guides").resolve()
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

        # Within guides/ → keep relative (Starlight resolves them)
        if _is_relative_to(resolved, guides_root):
            if resolved.is_dir():
                # Bare directory link → index
                return m.group(0)
            elif resolved.exists():
                return m.group(0)
            # Stale link within guides/ — fall through

        # Within repo but outside guides/ → GitHub URL
        if _is_relative_to(resolved, repo_root):
            rel = resolved.relative_to(repo_root)
            return f"{prefix}{GITHUB_BASE}/{rel}{anchor})"

        return m.group(0)

    result = re.sub(r"(\]\()([^)#\"'\s]+)(#[^)]+)?\)", replace, text)
    return _strip_md_suffixes(result)


def _is_relative_to(path: Path, base: Path) -> bool:
    try:
        path.relative_to(base)
        return True
    except ValueError:
        return False


def _rewrite_contributing(text: str) -> str:
    """Fix links in CONTRIBUTING.md when placed at docs-site content root.

    CONTRIBUTING.md lives at the repo root; links are repo-root-relative.
    Most targets (AGENTS.md, docs/CONVENTIONS.md, etc.) aren't in the site,
    so we convert them to GitHub URLs using proper Path resolution.
    """
    contributing_src = REPO_ROOT / "CONTRIBUTING.md"
    repo_root = REPO_ROOT.resolve()
    guides_root = (REPO_ROOT / "guides").resolve()

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

    result = re.sub(r"(\]\()([^)#\"'\s]+)(#[^)]+)?\)", replace, text)
    return _strip_md_suffixes(result)


# ---------------------------------------------------------------------------
# Core operations
# ---------------------------------------------------------------------------

def copy_file(src: Path, dst: Path, rewriter=None, dry_run: bool = False) -> None:
    """Copy src to dst, applying an optional rewriter(text) → text transform.

    For .md files, injects Starlight frontmatter (title:) if none present.
    """
    if dry_run:
        print(f"  copy  {src.relative_to(REPO_ROOT)} → {dst.relative_to(REPO_ROOT)}")
        return
    dst.parent.mkdir(parents=True, exist_ok=True)
    text = src.read_text(encoding="utf-8")
    if rewriter:
        text = rewriter(text)
    if dst.suffix == ".md" and not text.startswith("---"):
        text = _inject_frontmatter(text, src)
    dst.write_text(text, encoding="utf-8")


def mirror_dir(src: Path, dst: Path, rewriter=None, dry_run: bool = False) -> int:
    """Mirror src into dst, applying an optional per-file rewriter to .md files.

    README.md files are renamed to index.md to preserve directory-index URLs
    in Starlight (prevents /guides/core/readme/ instead of /guides/core/).
    Starlight frontmatter (title:) is injected into .md files that lack it.
    """
    count = 0
    if not src.exists():
        print(f"  warn  source dir missing: {src.relative_to(REPO_ROOT)}", file=sys.stderr)
        return 0
    for path in sorted(src.rglob("*")):
        if path.is_file():
            rel = path.relative_to(src)
            # Rename README.md → index.md to preserve Starlight directory-index URLs
            rel_parts = list(rel.parts)
            if rel_parts[-1] == "README.md":
                rel_parts[-1] = "index.md"
            target = dst / Path(*rel_parts)
            if dry_run:
                action = "rename" if path.name == "README.md" else "copy"
                print(f"  {action} {path.relative_to(REPO_ROOT)} → {target.relative_to(REPO_ROOT)}")
            else:
                target.parent.mkdir(parents=True, exist_ok=True)
                if path.suffix == ".md":
                    text = path.read_text(encoding="utf-8")
                    if rewriter:
                        text = rewriter(text, path)
                    if not text.startswith("---"):
                        text = _inject_frontmatter(text, path)
                    target.write_text(text, encoding="utf-8")
                else:
                    shutil.copy2(path, target)
            count += 1
    return count


def build_pack_index(packs_dir: Path, out_dir: Path, dry_run: bool = False) -> None:
    lines = [PACK_INDEX_HEADER]
    for slug, display, scope, description in PACKS:
        # Use clean URL (no .md suffix) — Starlight serves at /packs/<slug>/
        lines.append(f"| [**{display}**]({slug}/) | `{scope}` | {description} |\n")

    content = "".join(lines)
    index_md = out_dir / "index.md"
    if dry_run:
        print(f"  gen   docs-site/src/content/docs/packs/index.md ({len(content)} bytes)")
    else:
        index_md.write_text(content, encoding="utf-8")


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
    guides_src = REPO_ROOT / "guides"
    guides_out = SITE_DOCS / "guides"

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
    print(f"  {n} files from guides/")

    print("build-site: copying changelog …")
    changelog_src = REPO_ROOT / "docs" / "product" / "changelog.md"
    changelog_dst = SITE_DOCS / "changelog.md"
    if changelog_src.exists():
        copy_file(changelog_src, changelog_dst, rewriter=_rewrite_changelog, dry_run=args.dry_run)
    else:
        print("  warn  docs/product/changelog.md missing", file=sys.stderr)

    print("build-site: copying contributing guide …")
    contributing_src = REPO_ROOT / "CONTRIBUTING.md"
    contributing_dst = SITE_DOCS / "contributing.md"
    if contributing_src.exists():
        copy_file(contributing_src, contributing_dst, rewriter=_rewrite_contributing, dry_run=args.dry_run)
    else:
        print("  warn  CONTRIBUTING.md missing", file=sys.stderr)

    print("build-site: copying design tokens …")
    tokens_src = REPO_ROOT / "web" / "src" / "styles" / "tokens.css"
    # Copy to docs-site/src/styles/ (gitignored) where starlight.css imports it
    tokens_dst = REPO_ROOT / "docs-site" / "src" / "styles" / "tokens.css"
    if tokens_src.exists():
        if args.dry_run:
            print(f"  copy  {tokens_src.relative_to(REPO_ROOT)} → {tokens_dst.relative_to(REPO_ROOT)}")
        else:
            tokens_dst.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(tokens_src, tokens_dst)
    else:
        print(f"error  web/src/styles/tokens.css missing — docs-site CSS depends on it", file=sys.stderr)
        sys.exit(1)

    print("build-site: done." + (" (dry run)" if args.dry_run else ""))


if __name__ == "__main__":
    main()
