"""Tests for `tools/lint-agent-artifacts.py`'s `metadata.auth` admission.

Verifies AC3 + AC26 from docs/specs/credential-broker-contract/spec.md:
  - The lint admits `metadata.auth` as an enum (env / cli / creds /
    sso-cookie) under the spec-blessed `metadata:` escape hatch.
  - Unknown `metadata.auth` values are refused with the pinned message:
    `frontmatter key 'metadata.auth' must be one of
    {env, cli, creds, sso-cookie}; got '<value>'`.
  - `metadata.credentialed: true` requires `metadata.auth` to be set;
    omitting it triggers a refuse-and-explain error.

The lint is invoked as a subprocess against a tempdir `LINT_ROOT` so the
fixture skills don't pollute the repo's `.claude/` tree or get picked up
by Claude Code's skill discovery.
"""

from __future__ import annotations

import os
import subprocess
import sys
import tempfile
import textwrap
import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[4]
LINT_SCRIPT = REPO_ROOT / "tools" / "lint-agent-artifacts.py"

ALL_BROKERS = ("env", "cli", "creds", "sso-cookie")


def _write_skill(root: Path, name: str, body_frontmatter: str) -> None:
    skill_dir = root / ".claude" / "skills" / name
    skill_dir.mkdir(parents=True, exist_ok=True)
    (skill_dir / "SKILL.md").write_text(body_frontmatter, encoding="utf-8")


def _run_lint(root: Path) -> subprocess.CompletedProcess:
    # Inherit the parent's full env (so the linter's `git rev-parse`
    # invocation resolves `git` on any PATH shape — NixOS / Alpine /
    # custom CI images don't always carry `git` under /usr/bin).
    # LINT_ROOT redirects the linter to the fixture tempdir.
    return subprocess.run(
        [sys.executable, str(LINT_SCRIPT)],
        capture_output=True, text=True,
        env={**os.environ, "LINT_ROOT": str(root)},
    )


class TestMetadataAuthAdmission(unittest.TestCase):
    """Each of the four broker ids must lint clean when used in `metadata.auth`."""

    def test_each_broker_id_admitted(self) -> None:
        for broker in ALL_BROKERS:
            with self.subTest(broker=broker):
                with tempfile.TemporaryDirectory() as tmp:
                    root = Path(tmp)
                    _write_skill(root, f"ok-{broker}", textwrap.dedent(f"""\
                        ---
                        name: ok-{broker}
                        description: A credentialed skill declaring auth={broker}; lint must accept it.
                        metadata:
                          credentialed: true
                          auth: {broker}
                        ---

                        Body.
                        """))
                    result = _run_lint(root)
                    self.assertEqual(
                        result.returncode, 0,
                        f"broker={broker} should lint clean; "
                        f"stderr=\n{result.stderr}",
                    )


class TestMetadataAuthRefusalShape(unittest.TestCase):
    """Unknown broker values refused with the pinned stderr."""

    def test_unknown_broker_refused_with_pinned_message(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            _write_skill(root, "bad-broker", textwrap.dedent("""\
                ---
                name: bad-broker
                description: Unknown auth broker id — lint must refuse with the pinned message.
                metadata:
                  credentialed: true
                  auth: mystery
                ---

                Body.
                """))
            result = _run_lint(root)
            self.assertNotEqual(result.returncode, 0)
            self.assertIn(
                "frontmatter key 'metadata.auth' must be one of "
                "{env, cli, creds, sso-cookie}; got 'mystery'",
                result.stderr,
            )


class TestCredentialedRequiresAuth(unittest.TestCase):
    """`metadata.credentialed: true` without `metadata.auth` is refused."""

    def test_credentialed_true_without_auth_refused(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            _write_skill(root, "credentialed-without-auth", textwrap.dedent("""\
                ---
                name: credentialed-without-auth
                description: credentialed=true but no auth broker declared; lint must refuse.
                metadata:
                  credentialed: true
                ---

                Body.
                """))
            result = _run_lint(root)
            self.assertNotEqual(result.returncode, 0)
            # The pinned message names the missing key explicitly so the
            # author knows what to add.
            self.assertIn("metadata.auth", result.stderr)
            self.assertIn("required when metadata.credentialed: true", result.stderr)

    def test_credentialed_false_without_auth_clean(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            _write_skill(root, "not-credentialed", textwrap.dedent("""\
                ---
                name: not-credentialed
                description: credentialed=false — lint must not require an auth broker.
                metadata:
                  credentialed: false
                ---

                Body.
                """))
            result = _run_lint(root)
            self.assertEqual(
                result.returncode, 0,
                f"non-credentialed skill should lint clean; "
                f"stderr=\n{result.stderr}",
            )

    def test_credentialed_false_with_auth_declared_clean(self) -> None:
        # Pins current behaviour: AC26 is silent on the `credentialed:
        # false` + `auth: <id>` combination. The lint admits `metadata.
        # auth` unconditionally under the metadata escape hatch (so any
        # skill may declare it); the "requires" rail only fires when
        # `credentialed: true`. A future spec amendment may want to
        # surface this combination as a warning — for now it lints
        # clean and this test pins that contract.
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            _write_skill(root, "auth-without-credentialed", textwrap.dedent("""\
                ---
                name: auth-without-credentialed
                description: auth declared without credentialed=true — admitted today.
                metadata:
                  credentialed: false
                  auth: creds
                ---

                Body.
                """))
            result = _run_lint(root)
            self.assertEqual(
                result.returncode, 0,
                f"credentialed=false + auth declared should lint clean today; "
                f"stderr=\n{result.stderr}",
            )


if __name__ == "__main__":
    unittest.main()
