#!/usr/bin/env python3
"""Minimal violation fixtures for the 12 in-scope lint scripts.

`build(rule, root)` populates an existing, empty, `git init`-ed directory so
that the named rule reports at least one violation. Every builder writes the
smallest tree that trips one concrete rule in the script, and nothing else.

Content is synthetic placeholder text throughout: no real maintainer address,
no copied repository prose.

Known limit -- `lint-nosec-form` and `lint-nosemgrep-form`: both scripts pin
`base = REPO_ROOT` from `Path(__file__).resolve().parent.parent` and run
`git ls-files` with `cwd=REPO_ROOT`. Invoked from `tools/` in the real
repository, they refuse an absolute path outside it ("is outside repository",
exit 2) and can never read a fixture tree. The builders below still write a
correct violating tree, which trips the rule when the script itself is invoked
from a copy inside the fixture root. See the report accompanying this file.
"""

from __future__ import annotations

import subprocess
from pathlib import Path

__all__ = ["build"]


def _write(path: Path, text: str) -> None:
    """Create parents and write `text` as UTF-8."""
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def _git_add(root: Path) -> None:
    """Stage everything so `git ls-files` can see it. Never commits."""
    subprocess.run(
        ["git", "add", "-A"], cwd=str(root), check=False, capture_output=True
    )


# --- one builder per rule ---------------------------------------------------


def _conformance_portability(root: Path) -> None:
    """Rule 2: a conformance test reaching a repository-only directory.

    `_ROOT_JOIN` matches the `/ "tools"` join. The pack-name pass runs first
    and finds nothing, because the fixture has no `packs/`.
    """
    _write(
        root / "tests" / "conformance" / "test_placeholder.py",
        'def test_placeholder():\n'
        '    target = CATALOGUE_ROOT / "tools"\n'
        '    assert target\n',
    )


def _experience_agnostic(root: Path) -> None:
    """Stack-token rule: a UI-framework proper noun in pack Markdown."""
    _write(
        root / "packs" / "experience-design" / "placeholder.md",
        "# Placeholder method\n\nBuild the placeholder surface in React.\n",
    )


def _guides_no_repo_only_refs(root: Path) -> None:
    """Rule 2: an `ADR-NNNN` governance token in a shipped guide.

    `docs/specs/` must exist beside the guides root or the scan exits 2 with a
    usage error instead of reporting the violation.
    """
    (root / "docs" / "specs").mkdir(parents=True, exist_ok=True)
    _write(
        root / "guides" / "placeholder.md",
        "# Placeholder guide\n\nBackground lives in ADR-0001.\n",
    )


def _nosec_form(root: Path) -> None:
    """`blanket`: a bandit suppression with no test ID."""
    _write(
        root / "tools" / "placeholder.py",
        '"""Placeholder module."""\n\n'
        "import subprocess  # nosec\n\n"
        "PLACEHOLDER = subprocess\n",
    )
    _git_add(root)


def _nosemgrep_form(root: Path) -> None:
    """`blanket`: a Semgrep suppression with no rule-id list."""
    token = "nose" + "mgrep"
    _write(
        root / "tools" / "placeholder.sh",
        "#!/bin/sh\n" f"echo placeholder  # {token}\n",
    )
    _git_add(root)


def _zone_violations(root: Path) -> None:
    """A raw hex colour used as a CSS value outside the canonical token file."""
    _write(
        root / "web" / "src" / "placeholder.css",
        ".placeholder {\n  color: #abc123;\n}\n",
    )


def _guide_titles(root: Path) -> None:
    """Frontmatter `title` and the leading body H1 say different things."""
    _write(
        root / "guides" / "placeholder.md",
        "---\ntitle: Placeholder Alpha\n---\n\n"
        "# Placeholder Beta\n\nBody text.\n",
    )


def _journey_contract(root: Path) -> None:
    """Missing `contract:` frontmatter and no fixed-format stages."""
    _write(
        root / "web" / "src" / "content" / "journeys" / "placeholder.md",
        "# Placeholder journey\n\nNo contract block and no stages.\n",
    )


def _pack_descriptions(root: Path) -> None:
    """`[pack].description` past the 800-character drift backstop."""
    description = ("placeholder description sentence. " * 30)[:900]
    assert len(description) > 800
    _write(
        root / "packs" / "placeholder" / "pack.toml",
        "[pack]\n"
        'name = "placeholder"\n'
        f'description = "{description}"\n',
    )


def _pack_journeys(root: Path) -> None:
    """A pack-local stage with `**Output:**` but no required `**State:**`."""
    _write(
        root / "packs" / "placeholder" / "JOURNEY.md",
        "---\n"
        "journey_id: placeholder-journey\n"
        "pack: placeholder\n"
        "---\n\n"
        "## The journey\n\n"
        "### 1. Placeholder stage\n\n"
        "- **Output:** a placeholder artifact\n",
    )


def _pack_maintainer_emails(root: Path) -> None:
    """A maintainer address on a host outside `ALLOWED_HOSTS`."""
    _write(
        root / "packs" / "placeholder" / "pack.toml",
        "[pack]\n"
        'name = "placeholder"\n'
        'description = "Placeholder pack."\n\n'
        "[[pack.maintainers]]\n"
        'name = "Placeholder Maintainer"\n'
        'email = "placeholder.person@placeholder.example.test"\n',
    )


def _sso_config(root: Path) -> None:
    """`auth_default` is not `creds`, and the `[sso]` table is absent."""
    _write(
        root
        / "packs"
        / "placeholder"
        / ".apm"
        / "skills"
        / "placeholder-skill"
        / "references"
        / "sso-config.toml",
        'auth_default = "sso"\n',
    )


_BUILDERS = {
    "lint-conformance-portability": _conformance_portability,
    "lint-experience-agnostic": _experience_agnostic,
    "lint-guides-no-repo-only-refs": _guides_no_repo_only_refs,
    "lint-nosec-form": _nosec_form,
    "lint-nosemgrep-form": _nosemgrep_form,
    "lint_zone_violations": _zone_violations,
    "lint-guide-titles": _guide_titles,
    "lint-journey-contract": _journey_contract,
    "lint-pack-descriptions": _pack_descriptions,
    "lint-pack-journeys": _pack_journeys,
    "lint-pack-maintainer-emails": _pack_maintainer_emails,
    "lint-sso-config": _sso_config,
}


def build(rule: str, root: Path) -> None:
    """Populate `root` so that `rule` reports at least one violation."""
    try:
        builder = _BUILDERS[rule]
    except KeyError:
        raise KeyError(rule) from None
    builder(Path(root))
