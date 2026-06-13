"""Doc-shape audit for the new reference page (AC18).

Confirms:
  - `docs/guides/_shared/reference/agentbundle.md` exists.
  - It carries the three sections promised by the spec
    (install agentbundle, install a pack, configure the default adapter).
  - The forward-link to the existing install-from-clone how-to is
    present and points at a file that exists.
  - `docs/guides/_shared/reference/README.md` links to the new page.
"""

from __future__ import annotations

from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[4]
REF_DIR = REPO_ROOT / "docs" / "guides" / "_shared" / "reference"
REF_PAGE = REF_DIR / "agentbundle.md"
README = REF_DIR / "README.md"
HOWTO_INSTALL_FROM_CLONE = (
    REPO_ROOT / "docs" / "guides" / "_shared" / "how-to" / "install-agentbundle-from-clone.md"
)


def test_reference_page_exists() -> None:
    assert REF_PAGE.is_file(), f"Expected reference page at {REF_PAGE}"


def test_reference_page_has_three_sections() -> None:
    body = REF_PAGE.read_text()
    # H2 headings, case-insensitive substring matches on the section
    # names. Wording can drift; the *presence* is the audit.
    assert "## Install `agentbundle`" in body
    assert "## Install a pack" in body
    assert "## Configure the default adapter" in body


def test_reference_page_forward_links_to_install_from_clone() -> None:
    body = REF_PAGE.read_text()
    assert "install-agentbundle-from-clone.md" in body
    assert HOWTO_INSTALL_FROM_CLONE.is_file(), (
        f"Forward-link target {HOWTO_INSTALL_FROM_CLONE} does not exist."
    )


def test_reference_readme_links_to_agentbundle_page() -> None:
    body = README.read_text()
    assert "agentbundle.md" in body, (
        "docs/guides/_shared/reference/README.md should link to the new "
        "agentbundle.md page."
    )
