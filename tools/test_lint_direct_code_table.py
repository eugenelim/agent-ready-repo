"""Mutation control for `tools/lint-direct-code-table.py`.

A lint that only ever runs against a correct repository proves nothing. Each
test here breaks the pairing in one direction and asserts the lint notices.
"""

from __future__ import annotations

import shutil
import subprocess
import sys
import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
LINT = REPO_ROOT / "tools" / "lint-direct-code-table.py"
REGISTRY = Path("packages/agentbundle/agentbundle/catalogue_tooling/diagnostics.py")
TABLE = Path("guides/catalogue-curation/reference/direct-install-diagnostics.md")


def _run(root: Path) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, str(LINT), "--root", str(root)],
        capture_output=True,
        text=True,
    )


class DirectCodeTableLintTests(unittest.TestCase):
    def setUp(self) -> None:
        self.tmp = Path(
            __import__("tempfile").mkdtemp(prefix="direct-code-table-")
        )
        self.addCleanup(shutil.rmtree, self.tmp, ignore_errors=True)
        for relpath in (REGISTRY, TABLE):
            destination = self.tmp / relpath
            destination.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(REPO_ROOT / relpath, destination)

    def test_the_real_repository_passes(self) -> None:
        result = _run(REPO_ROOT)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("registered codes", result.stdout)

    def test_digest_row_names_every_uncomparable_stored_shape(self) -> None:
        table = (REPO_ROOT / TABLE).read_text(encoding="utf-8")
        row = next(line for line in table.splitlines() if "`CAT-D032`" in line)
        for shape in ("absent", "malformed", "unsupported"):
            self.assertIn(shape, row)

    def test_unlink_and_malformed_ownership_rows_stay_distinct(self) -> None:
        table = (REPO_ROOT / TABLE).read_text(encoding="utf-8")
        rows = {
            code: next(line for line in table.splitlines() if f"`{code}`" in line)
            for code in ("CAT-D020", "CAT-D035")
        }
        self.assertIn("obsolete owned file", rows["CAT-D020"])
        self.assertNotIn("state entry", rows["CAT-D020"])
        self.assertIn("malformed state entry", rows["CAT-D035"])

    def test_reference_qualifies_recovery_line_promise(self) -> None:
        table = (REPO_ROOT / TABLE).read_text(encoding="utf-8")
        introduction = table.split("| Code | Meaning |", 1)[0]
        self.assertIn("when an actionable next step exists", introduction)
        self.assertNotIn("the path it objects\nto, and a recovery line", introduction)

    def test_a_registered_code_missing_from_the_table_fails(self) -> None:
        table = self.tmp / TABLE
        kept = [
            line
            for line in table.read_text(encoding="utf-8").splitlines()
            if "`CAT-D011`" not in line
        ]
        table.write_text("\n".join(kept) + "\n", encoding="utf-8")
        result = _run(self.tmp)
        self.assertEqual(result.returncode, 1)
        self.assertIn("registered but not published", result.stderr)
        self.assertIn("CAT-D011", result.stderr)

    def test_a_table_row_with_no_registered_code_fails(self) -> None:
        table = self.tmp / TABLE
        table.write_text(
            table.read_text(encoding="utf-8") + "| `CAT-D999` | Invented. |\n",
            encoding="utf-8",
        )
        result = _run(self.tmp)
        self.assertEqual(result.returncode, 1)
        self.assertIn("published but not registered", result.stderr)
        self.assertIn("CAT-D999", result.stderr)

    def test_a_new_registered_code_must_be_published(self) -> None:
        # The growth case AC23 names: a fixed-size table could only fail as the
        # set grows, so this is the direction that matters most.
        registry = self.tmp / REGISTRY
        text = registry.read_text(encoding="utf-8")
        # Anchored on the FIRST member, which never moves. Anchoring on the
        # current last member made every task that registers a code edit this
        # fixture, and the injected ordinal is held far above any real
        # allocation for the same reason.
        text = text.replace(
            '    CAT_D001 = "CAT-D001"',
            '    CAT_D090 = "CAT-D090"   # a newly registered refusal\n'
            '    CAT_D001 = "CAT-D001"',
        ).replace(
            "        DiagnosticCode.CAT_D001,",
            "        DiagnosticCode.CAT_D001,\n        DiagnosticCode.CAT_D090,",
        )
        registry.write_text(text, encoding="utf-8")
        result = _run(self.tmp)
        self.assertEqual(result.returncode, 1, result.stdout)
        self.assertIn("CAT-D090", result.stderr)

    def test_a_non_literal_registry_is_refused(self) -> None:
        # The lint reads the frozenset by `ast` parse rather than importing it,
        # so a comprehension would be invisible. It refuses rather than
        # silently reading an empty set and passing.
        registry = self.tmp / REGISTRY
        text = registry.read_text(encoding="utf-8")
        start = text.index("DIRECT_CODES: frozenset[DiagnosticCode] = frozenset(")
        end = text.index(")", text.index("}", start)) + 1
        text = (
            text[:start]
            + "DIRECT_CODES: frozenset[DiagnosticCode] = frozenset(\n"
            "    code for code in DiagnosticCode if code.value.startswith('CAT-D')\n"
            ")"
            + text[end:]
        )
        registry.write_text(text, encoding="utf-8")
        result = _run(self.tmp)
        self.assertEqual(result.returncode, 1)
        self.assertIn("explicit frozenset literal", result.stderr)

    def test_the_lint_does_not_import_agentbundle(self) -> None:
        # A stale editable install or an unrelated copy on `sys.path` must not
        # be able to satisfy the check.
        source = LINT.read_text(encoding="utf-8")
        self.assertNotIn("import agentbundle", source)
        self.assertNotIn("from agentbundle", source)
        self.assertIn("ast.parse", source)

    def test_a_missing_table_is_an_error_not_a_pass(self) -> None:
        (self.tmp / TABLE).unlink()
        result = _run(self.tmp)
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("missing", result.stderr)


if __name__ == "__main__":
    unittest.main()
