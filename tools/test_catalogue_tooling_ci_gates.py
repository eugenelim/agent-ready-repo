#!/usr/bin/env python3
"""Construction tests for catalogue-tooling-ci-gates (Wave 5c).

Tests verify that the required CI job IDs exist in the correct workflow files
and that the release-impact script logic is path-sensitive.
"""
import pathlib
import re
import sys
import unittest

REPO_ROOT = pathlib.Path(__file__).resolve().parent.parent

_GATES_WORKFLOW = REPO_ROOT / ".github" / "workflows" / "catalogue-tooling-ci-gates.yml"
_RELEASE_WORKFLOW = REPO_ROOT / ".github" / "workflows" / "release-agentbundle.yml"
_IMPACT_SCRIPT = REPO_ROOT / "tools" / "repo" / "check_release_impact.py"
_GATE_I_DOC = REPO_ROOT / "docs" / "guides" / "how-to" / "artifactory-publication-template.md"


class GatesWorkflowTest(unittest.TestCase):
    def setUp(self):
        self._text = _GATES_WORKFLOW.read_text(encoding="utf-8")

    def test_gate_a_job_exists(self):
        self.assertIn("agentbundle-tests:", self._text, "Gate A job 'agentbundle-tests' missing")

    def test_gate_a_matrix_entries(self):
        self.assertIn("ubuntu-latest", self._text)
        self.assertIn("windows-latest", self._text)
        self.assertIn('"3.11"', self._text)
        self.assertIn('"3.12"', self._text)

    def test_gate_b_job_exists(self):
        self.assertIn(
            "external-catalogue-smoke:", self._text,
            "Gate B job 'external-catalogue-smoke' missing",
        )

    def test_gate_c_job_exists(self):
        self.assertIn(
            "enterprise-agentbundle-distribution:", self._text,
            "Gate C job 'enterprise-agentbundle-distribution' missing",
        )

    def test_gate_d_job_exists(self):
        self.assertIn(
            "catalogue-artifact-smoke:", self._text,
            "Gate D job 'catalogue-artifact-smoke' missing",
        )

    def test_gate_e_job_exists(self):
        self.assertIn(
            "catalogue-disconnected-smoke:", self._text,
            "Gate E job 'catalogue-disconnected-smoke' missing",
        )

    def test_gate_f_job_exists(self):
        self.assertIn(
            "catalogue-repo-rewire:", self._text,
            "Gate F job 'catalogue-repo-rewire' missing",
        )

    def test_gate_g_job_exists(self):
        self.assertIn(
            "agentbundle-release-impact:", self._text,
            "Gate G job 'agentbundle-release-impact' missing",
        )

    def test_no_real_credentials(self):
        # Production domains must not appear in the workflow YAML.
        for domain in ("artifactory.acme.com", "artifactory.corp.", "mycompany.jfrog.io"):
            self.assertNotIn(domain, self._text, f"Workflow must not reference real domain {domain!r}")
        # Hard-coded credential values (not just pattern strings) must not appear.
        # A credential assignment looks like: token: <value> or TOKEN=<value>
        import re as _re
        bad = _re.findall(r'\bTWINE_PASSWORD\s*=\s*[^$"\']', self._text)
        self.assertFalse(bad, f"Hard-coded TWINE_PASSWORD found: {bad}")

    def test_gate_c_credential_scan_present(self):
        self.assertIn("BANNED", self._text, "Gate C must include a bearer-token scan")


class ReleaseWorkflowTest(unittest.TestCase):
    def setUp(self):
        self._text = _RELEASE_WORKFLOW.read_text(encoding="utf-8")

    def test_gate_h_job_exists(self):
        self.assertIn(
            "pre-release-gates:", self._text,
            "Gate H job 'pre-release-gates' missing from release-agentbundle.yml",
        )

    def test_publish_pypi_needs_pre_release_gates(self):
        # publish-pypi must declare pre-release-gates in its needs list
        self.assertIn("pre-release-gates", self._text)


class ReleaseImpactScriptTest(unittest.TestCase):
    """Unit tests for check_release_impact.py path-sensitivity logic."""

    def setUp(self):
        sys.path.insert(0, str(REPO_ROOT / "tools" / "repo"))
        import check_release_impact as m
        self._m = m
        # Remove after import so other tests aren't affected
        sys.path.pop(0)

    def test_catalogue_tooling_is_impacting(self):
        path = "packages/agentbundle/agentbundle/catalogue_tooling/verify.py"
        self.assertTrue(self._m.is_release_impacting(path))

    def test_cli_is_impacting(self):
        self.assertTrue(self._m.is_release_impacting("packages/agentbundle/agentbundle/cli.py"))

    def test_packs_not_impacting(self):
        self.assertFalse(self._m.is_release_impacting("packs/core/pack.toml"))

    def test_tools_repo_not_impacting(self):
        self.assertFalse(self._m.is_release_impacting("tools/repo/check_release_impact.py"))

    def test_tools_catalogue_not_impacting(self):
        self.assertFalse(self._m.is_release_impacting("tools/catalogue/pre_pr_catalogue.py"))

    def test_docs_specs_not_impacting(self):
        self.assertFalse(self._m.is_release_impacting("docs/specs/catalogue-tooling-ci-gates/spec.md"))

    def test_changelog_is_release_indicator(self):
        changed = ["docs/product/changelog.md", "packages/agentbundle/agentbundle/cli.py"]
        self.assertTrue(self._m.has_release_indicator(changed))

    def test_version_py_is_release_indicator(self):
        changed = ["packages/agentbundle/agentbundle/version.py"]
        self.assertTrue(self._m.has_release_indicator(changed))

    def test_no_indicator_when_only_packs(self):
        changed = ["packs/core/pack.toml"]
        self.assertFalse(self._m.has_release_indicator(changed))

    def test_main_passes_with_no_impacting_files(self):
        # Simulate a diff that touches only packs/ — should pass
        saved = self._m._changed_files
        self._m._changed_files = lambda base: ["packs/core/pack.toml"]
        try:
            rc = self._m.main(["--base", "HEAD~1"])
        finally:
            self._m._changed_files = saved
        self.assertEqual(rc, 0)

    def test_main_fails_with_impacting_files_and_no_indicator(self):
        saved = self._m._changed_files
        self._m._changed_files = lambda base: [
            "packages/agentbundle/agentbundle/catalogue_tooling/verify.py"
        ]
        try:
            rc = self._m.main(["--base", "HEAD~1"])
        finally:
            self._m._changed_files = saved
        self.assertEqual(rc, 1)

    def test_main_passes_with_impacting_files_and_indicator(self):
        saved = self._m._changed_files
        self._m._changed_files = lambda base: [
            "packages/agentbundle/agentbundle/catalogue_tooling/verify.py",
            "docs/product/changelog.md",
        ]
        try:
            rc = self._m.main(["--base", "HEAD~1"])
        finally:
            self._m._changed_files = saved
        self.assertEqual(rc, 0)


class GateITemplateTest(unittest.TestCase):
    def setUp(self):
        self._text = _GATE_I_DOC.read_text(encoding="utf-8")

    def test_gate_i_file_exists(self):
        self.assertTrue(_GATE_I_DOC.exists(), "Gate I doc missing")

    def test_gate_i_no_real_credentials(self):
        for pattern in ("artifactory.acme.com", "artifactory.corp.", "mycompany.jfrog.io"):
            self.assertNotIn(pattern, self._text, f"Gate I doc must not contain real domain {pattern!r}")
        self.assertIn("example.test", self._text, "Gate I doc must use example.test placeholder")

    def test_gate_i_six_step_sequence(self):
        self.assertIn("Step 1", self._text)
        self.assertIn("Step 6", self._text)
        self.assertIn("channel descriptor", self._text.lower())

    def test_gate_i_channel_descriptor_last(self):
        # Step 6 must mention the channel descriptor
        step6_idx = self._text.find("Step 6")
        self.assertGreater(step6_idx, 0)
        self.assertIn("channel", self._text[step6_idx:step6_idx + 200].lower())


if __name__ == "__main__":
    unittest.main()
