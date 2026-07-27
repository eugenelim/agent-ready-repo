"""Tests for `_step_agent_artifacts`'s `metadata.auth` admission.

Verifies AC3 + AC26 from docs/specs/credential-broker-contract/spec.md:
  - The lint admits `metadata.auth` as an enum (env / cli / creds /
    sso-cookie) under the spec-blessed `metadata:` escape hatch.
  - Unknown `metadata.auth` values are refused with the pinned message:
    `frontmatter key 'metadata.auth' must be one of
    {env, cli, creds, sso-cookie}; got '<value>'`.
  - `metadata.credentialed: true` requires `metadata.auth` to be set;
    omitting it triggers a refuse-and-explain error.

Uses `_step_agent_artifacts` directly against a tempdir fixture root
so the fixture skills don't pollute the repo's `.claude/` tree or get
picked up by Claude Code's skill discovery.
"""

from __future__ import annotations

import tempfile
import textwrap
import unittest
from pathlib import Path

from agentbundle.catalogue_tooling.verify import _step_agent_artifacts

ALL_BROKERS = ("env", "cli", "creds", "sso-cookie")


def _write_skill(root: Path, name: str, body_frontmatter: str) -> None:
    skill_dir = root / ".claude" / "skills" / name
    skill_dir.mkdir(parents=True, exist_ok=True)
    (skill_dir / "SKILL.md").write_text(body_frontmatter, encoding="utf-8")


def _run_lint(root: Path) -> list:
    return _step_agent_artifacts(root, None, None, root)


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
                        result, [],
                        f"broker={broker} should lint clean; "
                        f"errors={[d.message for d in result]}",
                    )


class TestMetadataAuthRefusalShape(unittest.TestCase):
    """Unknown broker values refused with the pinned message."""

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
            self.assertTrue(len(result) > 0)
            messages = " ".join(d.message for d in result)
            self.assertIn(
                "frontmatter key 'metadata.auth' must be one of "
                "{env, cli, creds, sso-cookie}; got 'mystery'",
                messages,
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
            self.assertTrue(len(result) > 0)
            messages = " ".join(d.message for d in result)
            # The pinned message names the missing key explicitly so the
            # author knows what to add.
            self.assertIn("metadata.auth", messages)
            self.assertIn("required when metadata.credentialed: true", messages)

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
                result, [],
                f"non-credentialed skill should lint clean; "
                f"errors={[d.message for d in result]}",
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
                result, [],
                f"credentialed=false + auth declared should lint clean today; "
                f"errors={[d.message for d in result]}",
            )


if __name__ == "__main__":
    unittest.main()
