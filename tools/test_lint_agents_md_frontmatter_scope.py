"""Regression checks for the scope-declaration lint on projected AGENTS.md files.

A projected copy of an AGENTS.md carries YAML frontmatter where the repository
source carries an ATX heading. The scope-declaration check reads the first
non-heading line, so before frontmatter was skipped it read the opening `---`
delimiter: a correct projection failed, and the check never inspected the
sentence it exists to enforce.

These assert stderr because scratch repositories intentionally fail unrelated
structure checks; the scope-declaration diagnostic is the signal under test.
Each case builds its own scratch repository so no case can be made to pass or
fail by another case's fixture.
"""

from __future__ import annotations

import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
LINTER = REPO_ROOT / "tools" / "lint-agents-md.py"
# File-specific: a scratch repository emits unrelated "is missing" diagnostics
# (absent charter, Diátaxis directories), so a bare substring would match noise
# and let a case pass or fail for the wrong reason.
MARKER = "web/AGENTS.md is missing"
DECLARATION = (
    "Applies to `web/`. Inherits the root `AGENTS.md`. Scope-specific deltas only."
)


def run(root: Path) -> str:
    result = subprocess.run(
        [sys.executable, str(LINTER)],
        cwd=root,
        env={**os.environ, "PYTHONDONTWRITEBYTECODE": "1"},
        capture_output=True,
        text=True,
        encoding="utf-8",
    )
    return result.stderr


def scratch(root: Path, scoped_body: str) -> None:
    (root / "AGENTS.md").write_text("# AGENTS.md\n", encoding="utf-8")
    (root / "CLAUDE.md").symlink_to("AGENTS.md")
    scoped = root / "web" / "AGENTS.md"
    scoped.parent.mkdir(parents=True)
    scoped.write_text(scoped_body, encoding="utf-8")


FRONTMATTER = '---\ntitle: "AGENTS.md — `web/`"\n---\n\n'


class FrontmatterScopeDeclarationTests(unittest.TestCase):
    def test_projected_file_with_declaration_is_silent(self) -> None:
        """The defect under repair: this correct projection used to fail."""
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            scratch(root, f"{FRONTMATTER}{DECLARATION}\n")
            self.assertNotIn(MARKER, run(root))

    def test_source_file_with_declaration_is_silent(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            scratch(root, f"# AGENTS.md — `web/`\n\n{DECLARATION}\n")
            self.assertNotIn(MARKER, run(root))

    def test_projected_file_missing_the_declaration_still_fails(self) -> None:
        """Skipping frontmatter must not turn the check into one that cannot fail."""
        for body in (
            "An opening sentence that declares nothing.",
            "Applies to `web/`. Scope-specific deltas only.",
            "Inherits the root `AGENTS.md`. Scope-specific deltas only.",
        ):
            with self.subTest(body=body), tempfile.TemporaryDirectory() as tmp:
                root = Path(tmp)
                scratch(root, f"{FRONTMATTER}{body}\n")
                self.assertIn(MARKER, run(root))

    def test_source_file_missing_the_declaration_still_fails(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            scratch(root, "# AGENTS.md — `web/`\n\nDeclares nothing.\n")
            self.assertIn(MARKER, run(root))

    def test_indented_horizontal_rule_is_not_frontmatter(self) -> None:
        """A YAML document marker sits at column zero.

        Treating an indented `---` as frontmatter would skip past a leading
        Markdown horizontal rule and accept a document that declares nothing —
        loosening the check in a case that has no frontmatter at all.
        """
        # The body below carries a VALID declaration on purpose. Treating the
        # indented rule as frontmatter would skip to that line and pass; only
        # the column-zero rule leaves ` --- ` as the first content and fails.
        # A body that declares nothing would fail either way and prove nothing.
        for opener, closer in ((" --- ", " --- "), ("\t---", "\t---")):
            with self.subTest(opener=opener), tempfile.TemporaryDirectory() as tmp:
                root = Path(tmp)
                scratch(root, f"{opener}\nA rule, not frontmatter\n{closer}\n\n{DECLARATION}\n")
                self.assertIn(MARKER, run(root))

    def test_unterminated_frontmatter_does_not_crash(self) -> None:
        """An unclosed block falls back to the whole document rather than raising."""
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            scratch(root, f'---\ntitle: "x"\n\n{DECLARATION}\n')
            self.assertIn(MARKER, run(root))


if __name__ == "__main__":
    unittest.main()
