"""Stdlib-core purity gate (spec tasks T2/T3; AC4).

The base ``credbroker`` import graph must reach **no** third-party module —
in particular not ``cryptography`` / ``argon2`` (the ``[crypto]`` extra's
deps), which are reached only through the lazily-imported ``_vault`` module
(spec task T4). This is a named regression test: adding a top-level
``import cryptography`` to any base module turns it red.

The check runs the import in an **isolated subprocess** and inspects the
``sys.modules`` delta — the in-pytest snapshot is rejected because pytest
pollutes ``sys.modules`` (pluggy / _pytest / and, once installed, the crypto
deps themselves), so any in-process assertion would compare against a polluted
baseline. Note this host may have ``cryptography`` installed (the ``[crypto]``
extra); the subprocess proves the *base import* does not pull it in regardless.
"""

from __future__ import annotations

import json
import subprocess
import sys
import textwrap
import unittest


def _import_delta() -> dict[str, list[str]]:
    """Return the sys.modules delta from a fresh subprocess that only
    imports the base ``credbroker`` package, plus this interpreter's
    ``sys.stdlib_module_names`` so the assertion can separate stdlib
    transitive imports from third-party ones."""
    script = textwrap.dedent(
        """
        import json
        import sys
        before = set(sys.modules)
        import credbroker  # noqa: F401
        after = set(sys.modules)
        print(json.dumps({
            "delta": sorted(after - before),
            "stdlib": sorted(sys.stdlib_module_names),
        }))
        """
    )
    proc = subprocess.run(
        [sys.executable, "-c", script],
        capture_output=True,
        text=True,
        check=False,
    )
    assert proc.returncode == 0, (
        f"subprocess import failed: stdout={proc.stdout!r} stderr={proc.stderr!r}"
    )
    return json.loads(proc.stdout.strip())


class StdlibPuritySubprocessTests(unittest.TestCase):
    """Base ``credbroker`` import is stdlib-only (+ credbroker's own modules)."""

    def test_no_crypto_in_base_import(self) -> None:
        """AC4 core: the base import never reaches cryptography/argon2/cffi."""
        delta = set(_import_delta()["delta"])
        forbidden_roots = {"cryptography", "argon2", "argon2_cffi", "cffi", "_cffi_backend"}
        leaked = {m for m in delta if m.split(".", 1)[0] in forbidden_roots}
        self.assertEqual(
            leaked,
            set(),
            f"base credbroker import pulled crypto-extra modules: {leaked} — "
            f"the vault import must stay lazy (inside the Tier-3 path), never "
            f"at module top.",
        )

    def test_delta_is_stdlib_plus_credbroker(self) -> None:
        """Loud general guard: nothing outside stdlib + credbroker's own tree."""
        result = _import_delta()
        delta = set(result["delta"])
        stdlib_names = set(result["stdlib"])
        non_stdlib: set[str] = set()
        for mod in delta:
            root = mod.split(".", 1)[0]
            if root in stdlib_names:
                continue
            # Stdlib implementation-detail submodules (_frozen_importlib_external,
            # _collections_abc, _io, …) are stdlib internals.
            if root.startswith("_"):
                continue
            if root == "credbroker":
                continue
            non_stdlib.add(mod)
        self.assertEqual(
            non_stdlib,
            set(),
            f"base credbroker import pulled non-stdlib modules: {non_stdlib}",
        )

    def test_no_known_third_party(self) -> None:
        """Belt-and-braces: explicitly refuse known third-party names a
        credentialed resolver must not pull at the base tier."""
        delta = set(_import_delta()["delta"])
        forbidden_prefixes = ("agentbundle", "keyring", "dotenv", "cryptography", "argon2")
        for mod in delta:
            for prefix in forbidden_prefixes:
                self.assertFalse(
                    mod == prefix or mod.startswith(prefix + "."),
                    f"base credbroker import pulled forbidden module {mod}",
                )


if __name__ == "__main__":
    unittest.main()
