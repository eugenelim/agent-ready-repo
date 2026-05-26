"""RFC-0012 AC30b: refusal-ordering witness.

Defensive regression pin against a future refactor that reorders the
install handler's refusal tiers. Each case supplies inputs that
*simultaneously* satisfy two refusal conditions at adjacent tiers and
asserts only the higher-tier line fires; the lower-tier line must be
absent (i.e., evaluation short-circuited before the lower tier ran).

Tier order per spec § *Boundaries — Always do* (refusal-ordering
invariant) and RFC-0012 § *Pinned refusal messages*' closing paragraph:

  1. ``scope.resolve()`` declared-scope refusals
     (``<pack>: scope '<requested>' not in allowed-scopes <set>``)
  2. Handler-level flag refusals
     (``install: --emit-install-routes is bound to --scope repo``;
      ``install: --adapter and --emit-install-routes are mutually
      exclusive at --scope repo``)
  3. Resolver-internal refusals
     (publisher-drift at step 0;
      ``install: --adapter X not in pack's allowed-adapters set``)

Cases covered:

  * **Case 1 (tier 1 vs tier 2).** Repo-only pack invoked with
    ``--scope user --emit-install-routes``. Tier 1 fires because
    ``user`` is not in the pack's ``allowed-scopes``; tier 2's
    ``--emit-install-routes is bound to --scope repo`` would fire
    next (scope is ``user``) but must not be reached.
  * **Case 2 (tier 2 vs tier 3).** ``--scope repo --adapter kiro
    --emit-install-routes`` against a pack whose ``allowed-adapters``
    excludes kiro. Tier 2's mutex fires; tier 3's resolver-internal
    ``--adapter kiro not in pack's allowed-adapters set`` must not.

The tests pass today by construction. They fail if anyone reorders the
install handler's checks (e.g., moves the handler-level mutex above
``scope.resolve()``, or invokes the resolver before the mutex). Per
spec AC30b's own framing: "without this witness, a refactor that
reorders the tiers passes every per-tier test in AC30/AC32."
"""

from __future__ import annotations

import io
import textwrap
import unittest
from contextlib import redirect_stderr
from pathlib import Path
from tempfile import TemporaryDirectory


def _make_pack(
    packs_dir: Path,
    *,
    name: str,
    allowed_scopes: list[str],
    allowed_adapters: list[str] | None = None,
    default_scope: str | None = None,
) -> Path:
    """Materialise a minimal v0.7 pack with the requested install-table
    constraints. Used by both cases to construct the tier-overlap
    fixtures the witness depends on."""
    pack_dir = packs_dir / name
    pack_dir.mkdir(parents=True)
    install_lines = [
        f"allowed-scopes = {allowed_scopes!r}",
    ]
    if default_scope is not None:
        install_lines.insert(0, f'default-scope = "{default_scope}"')
    if allowed_adapters is not None:
        install_lines.append(f"allowed-adapters = {allowed_adapters!r}")
    install_block = "\n".join(install_lines)
    (pack_dir / "pack.toml").write_text(
        textwrap.dedent(
            f"""\
            [pack]
            name = "{name}"
            version = "0.1.0"
            spec-version = "0.6"

            [pack.adapter-contract]
            version = "0.7"

            [pack.install]
            {install_block}
            """
        ),
        encoding="utf-8",
    )
    skill_dir = pack_dir / ".apm" / "skills" / f"{name}-skill"
    skill_dir.mkdir(parents=True)
    (skill_dir / "SKILL.md").write_text(
        f"---\nname: {name}-skill\ndescription: {name}\n---\nBody.",
        encoding="utf-8",
    )
    return pack_dir


def _run_install(argv: list[str]) -> tuple[int, str]:
    """Invoke install via argparse; return ``(rc, stderr)``."""
    from agentbundle.cli import _build_parser
    from agentbundle.commands import install

    parser = _build_parser()
    args = parser.parse_args(["install"] + argv)
    buf = io.StringIO()
    with redirect_stderr(buf):
        rc = install.run(args)
    return rc, buf.getvalue()


class Tier1BeforeTier2Tests(unittest.TestCase):
    """Case 1: declared-scope refusal (tier 1) short-circuits before
    the handler-level ``--emit-install-routes`` binding (tier 2)."""

    def test_repo_only_pack_at_user_scope_with_emit_install_routes(self) -> None:
        with TemporaryDirectory() as raw:
            tmp = Path(raw)
            packs_dir = tmp / "packs"
            packs_dir.mkdir()
            # Repo-only pack (allowed-scopes = ["repo"]) explicitly
            # default-scoped to repo so the user-passed --scope user
            # *attempt* triggers tier 1 cleanly.
            _make_pack(
                packs_dir,
                name="repoonly",
                allowed_scopes=["repo"],
                default_scope="repo",
                allowed_adapters=["claude-code", "kiro"],
            )
            adopter = tmp / "adopter"
            adopter.mkdir()

            rc, stderr = _run_install(
                [
                    "--pack", "repoonly",
                    "--scope", "user",
                    "--emit-install-routes",
                    "--output", str(adopter),
                    str(packs_dir),
                ]
            )

            self.assertNotEqual(rc, 0)
            # Tier 1 line present.
            self.assertIn(
                "scope 'user' not in allowed-scopes", stderr,
                f"expected tier-1 declared-scope refusal; got: {stderr!r}",
            )
            # Tier 2 line absent — short-circuited.
            self.assertNotIn(
                "--emit-install-routes is bound to --scope repo", stderr,
                "tier-2 binding fired even though tier-1 should have "
                "short-circuited",
            )


class Tier2BeforeTier3Tests(unittest.TestCase):
    """Case 2: handler-level ``--adapter`` + ``--emit-install-routes``
    mutex (tier 2) short-circuits before the resolver-internal
    ``allowed-adapters`` check (tier 3)."""

    def test_mutex_fires_before_resolver_allowed_adapters_check(self) -> None:
        with TemporaryDirectory() as raw:
            tmp = Path(raw)
            packs_dir = tmp / "packs"
            packs_dir.mkdir()
            # Pack admits only claude-code; the --adapter kiro flag
            # would trip the resolver-internal "not in allowed-adapters
            # set" refusal *if* the handler-level mutex didn't fire
            # first.
            _make_pack(
                packs_dir,
                name="ccpack",
                allowed_scopes=["repo"],
                default_scope="repo",
                allowed_adapters=["claude-code"],
            )
            adopter = tmp / "adopter"
            adopter.mkdir()

            rc, stderr = _run_install(
                [
                    "--pack", "ccpack",
                    "--scope", "repo",
                    "--adapter", "kiro",
                    "--emit-install-routes",
                    "--output", str(adopter),
                    str(packs_dir),
                ]
            )

            self.assertNotEqual(rc, 0)
            # Tier 2 line present.
            self.assertIn(
                "--adapter and --emit-install-routes are mutually "
                "exclusive at --scope repo",
                stderr,
                f"expected tier-2 mutex; got: {stderr!r}",
            )
            # Tier 3 line absent — resolver did not run.
            self.assertNotIn(
                "not in pack's allowed-adapters set", stderr,
                "tier-3 resolver allowed-adapters refusal fired even "
                "though tier-2 mutex should have short-circuited",
            )


if __name__ == "__main__":
    unittest.main()
