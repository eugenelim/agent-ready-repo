"""Construction tests for ini-005 Wave 5: catalogue-tooling-rewire.

Verifies that:
- Makefile targets use canonical agentbundle catalogue commands
- Old tool paths still exist as shims
- New canonical tool paths exist
- pre_pr_catalogue.py delegates portable verification to agentbundle
- No portable catalogue logic remains implemented only in tools/
"""

from __future__ import annotations

import re
import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent


class MakefileRewireTest(unittest.TestCase):
    """Makefile targets must use canonical agentbundle catalogue commands."""

    @classmethod
    def setUpClass(cls):
        cls.makefile = (REPO_ROOT / "Makefile").read_text(encoding="utf-8")

    def _target_body(self, target: str) -> str:
        """Extract the recipe lines for a given Makefile target, including ifeq blocks."""
        lines = self.makefile.splitlines()
        in_target = False
        body_lines: list[str] = []
        for line in lines:
            if line.startswith((f"{target}:", f"{target} :")):
                in_target = True
                continue
            if in_target:
                # include tab-indented lines AND Makefile conditional keywords
                if (line.startswith(("\t", "ifeq", "ifneq", "else", "endif"))):
                    body_lines.append(line)
                elif line.strip() and not line.startswith(" ") and not line.startswith("#"):
                    break
        return "\n".join(body_lines)

    def test_lint_packs_calls_catalogue_lint(self):
        body = self._target_body("lint-packs")
        self.assertIn("agentbundle catalogue lint", body,
                      "lint-packs must call agentbundle catalogue lint")
        self.assertNotIn("agentbundle.build lint-packs", body,
                         "lint-packs must not use old agentbundle.build surface")

    def test_build_self_calls_catalogue_self_host(self):
        body = self._target_body("build-self")
        self.assertIn("agentbundle catalogue self-host", body,
                      "build-self must call agentbundle catalogue self-host")
        self.assertIn("--write", body,
                      "build-self must use --write flag")

    def test_build_self_dry_run_calls_self_host_check(self):
        body = self._target_body("build-self-dry-run")
        self.assertIn("agentbundle catalogue self-host", body)
        self.assertIn("--check", body)

    def test_build_check_delegates_portable_verify_to_gate_chain(self):
        body = self._target_body("build-check")
        self.assertNotIn("agentbundle catalogue verify", body,
                         "build-check must not verify before the gate chain")
        chain = (REPO_ROOT / "tools/repo/build_gate_chain.py").read_text(encoding="utf-8")
        self.assertIn('"catalogue", "verify"', chain,
                      "the gate chain must own portable catalogue verification")

    def _resolved_body(self, target: str, *, hops: int = 2) -> str:
        """A target's recipe, following `$(MAKE) <target>` delegation.

        `build-check` delegates through the cooperative run-slot wrapper
        (`with-lease -- $(MAKE) -f <makefile> build-check-unleased`), so the
        gate-chain call it must reach is one hop away. Reading only the literal
        recipe reports a missing delegation that is in fact present -- and, worse, a
        guard that reads only the first recipe stops protecting the chain the moment
        any wrapper is introduced. Following the hop keeps it pointed at the
        property that matters: the gate chain actually runs.
        """
        seen: set[str] = set()
        pending = [target]
        collected: list[str] = []
        for _ in range(hops):
            if not pending:
                break
            current = pending.pop(0)
            if current in seen:
                continue
            seen.add(current)
            body = self._target_body(current)
            collected.append(body)
            for line in body.splitlines():
                for call in re.finditer(r"\$\(MAKE\)(.*)", line):
                    # Skip flags and make-variable arguments: the call carries
                    # `-f $(firstword $(MAKEFILE_LIST))`, so taking the first token
                    # after $(MAKE) captures "-f" and the target is never followed.
                    for token in call.group(1).split():
                        if token.startswith(("-", "$(")) or token.endswith("))"):
                            continue
                        pending.append(token)
                        break
        return "\n".join(collected)

    def test_build_check_calls_repo_build_gate_chain(self):
        resolved = self._resolved_body("build-check")
        self.assertIn("tools/repo/build_gate_chain.py", resolved,
                      "build-check must reach tools/repo/build_gate_chain.py")

    def test_wrapped_targets_keep_their_lease_and_forward_the_makefile(self):
        """Each wrapped target is guarded, so a dropped wrapper reddens something.

        The plan's participant matrix requires one dropped-wrapper mutation per
        wrapped target. The `-f` forwarding is asserted too: without it a recursive
        sub-make launched from inside the wrapper loses `-f` and re-reads the default
        Makefile, which silently disarms `assert-sast-chain-reachable`'s self-test.
        """
        for target, inner in (
            ("test", "test-unleased"),
            ("build-check", "build-check-unleased"),
            ("sast", "sast-unleased"),
        ):
            body = self._target_body(target)
            self.assertIn("with-lease", body, f"{target} must run under the wrapper")
            self.assertIn(inner, body, f"{target} must delegate to {inner}")
            self.assertIn("$(firstword $(MAKEFILE_LIST))", body,
                          f"{target} must forward the makefile currently in use")

    def test_package_target_exists(self):
        body = self._target_body("package")
        self.assertIn("agentbundle catalogue package", body,
                      "package target must call agentbundle catalogue package")

    def test_pre_pr_calls_new_path(self):
        body = self._target_body("pre-pr")
        self.assertIn("tools/catalogue/pre_pr_catalogue.py", body,
                      "pre-pr must call tools/catalogue/pre_pr_catalogue.py directly")


class OldPathsExistTest(unittest.TestCase):
    """Old tool paths must still exist as shims."""

    def _assert_shim(self, rel_path: str) -> None:
        p = REPO_ROOT / rel_path
        self.assertTrue(p.exists(), f"shim {rel_path} must still exist")
        content = p.read_text(encoding="utf-8", errors="replace")
        self.assertIn("Shim", content,
                      f"{rel_path} must be a shim (contain 'Shim')")

    def test_build_gate_chain_shim_exists(self):
        self._assert_shim("tools/build_gate_chain.py")

    def test_pre_pr_catalogue_shim_exists(self):
        self._assert_shim("tools/pre-pr-catalogue.py")

    def test_publish_claude_plugins_shim_exists(self):
        self._assert_shim("tools/publish-claude-plugins.py")

    def test_check_contract_drift_shim_exists(self):
        self._assert_shim("tools/check-contract-drift.py")

    def test_release_check_shim_exists(self):
        p = REPO_ROOT / "tools/release-check.sh"
        self.assertTrue(p.exists())
        content = p.read_text(encoding="utf-8", errors="replace")
        self.assertIn("Shim", content)


class NewPathsExistTest(unittest.TestCase):
    """Real implementations must exist at new canonical paths."""

    def _assert_real(self, rel_path: str, marker: str) -> None:
        p = REPO_ROOT / rel_path
        self.assertTrue(p.exists(), f"{rel_path} must exist")
        content = p.read_text(encoding="utf-8", errors="replace")
        self.assertIn(marker, content,
                      f"{rel_path} must contain '{marker}'")

    def test_catalogue_publish_claude_plugins_exists(self):
        p = REPO_ROOT / "tools/catalogue/publish_claude_plugins.py"
        self.assertTrue(p.exists())

    def test_catalogue_pre_pr_catalogue_exists(self):
        p = REPO_ROOT / "tools/catalogue/pre_pr_catalogue.py"
        self.assertTrue(p.exists())

    def test_repo_build_gate_chain_exists(self):
        p = REPO_ROOT / "tools/repo/build_gate_chain.py"
        self.assertTrue(p.exists())

    def test_repo_check_contract_drift_exists(self):
        p = REPO_ROOT / "tools/repo/check_contract_drift.py"
        self.assertTrue(p.exists())

    def test_repo_release_check_exists(self):
        p = REPO_ROOT / "tools/repo/release_check.sh"
        self.assertTrue(p.exists())


class PrePrCatalogueCallsVerifyTest(unittest.TestCase):
    """tools/catalogue/pre_pr_catalogue.py must call agentbundle catalogue verify."""

    @classmethod
    def setUpClass(cls):
        p = REPO_ROOT / "tools/catalogue/pre_pr_catalogue.py"
        cls.content = p.read_text(encoding="utf-8")

    def test_calls_agentbundle_catalogue_verify(self):
        self.assertIn("agentbundle", self.content)
        self.assertIn("catalogue", self.content)
        self.assertIn("verify", self.content)

    def test_verify_step_is_before_repo_specific_checks(self):
        verify_idx = self.content.find("catalogue verify")
        agents_md_idx = self.content.find("lint-agents-md")
        self.assertLess(verify_idx, agents_md_idx,
                        "agentbundle catalogue verify must run before repo-specific linters")


class NoPortableLogicInToolsTest(unittest.TestCase):
    """No portable catalogue logic may be implemented only inside tools/.

    Portable surfaces (lint, build, verify, package) must be called via
    the agentbundle CLI, not re-implemented or called as internal Python
    imports from tools/.
    """

    BANNED_PATTERNS = [
        "agentbundle.build.lint_packs",
        "agentbundle.build.main",
        "cmd_build",
        "cmd_lint_packs",
        "cmd_check",
    ]
    # Shims and test files may reference old names in comments/strings only.
    EXCLUDE_SUFFIXES = {".pyc"}

    def _scan_tools(self) -> list[tuple[Path, str]]:
        hits: list[tuple[Path, str]] = []
        tools_dir = REPO_ROOT / "tools"
        for p in tools_dir.rglob("*.py"):
            if p.suffix in self.EXCLUDE_SUFFIXES:
                continue
            # Skip the shims (they're allowed to reference old paths in comments)
            # and test files (which may reference old names for coverage).
            # Only check real implementations: catalogue/ and repo/ subdirs.
            if p.parent.name not in ("catalogue", "repo"):
                continue
            content = p.read_text(encoding="utf-8", errors="replace")
            for pat in self.BANNED_PATTERNS:
                if pat in content:
                    hits.append((p, pat))
        return hits

    def test_no_banned_portable_imports_in_new_tools(self):
        hits = self._scan_tools()
        if hits:
            msg = "Portable logic found in tools/ real implementations:\n"
            for path, pat in hits:
                msg += f"  {path.relative_to(REPO_ROOT)}: {pat!r}\n"
            self.fail(msg)


if __name__ == "__main__":
    unittest.main()
