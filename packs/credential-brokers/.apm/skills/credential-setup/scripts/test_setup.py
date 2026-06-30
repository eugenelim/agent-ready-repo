"""credential-setup tests — credential-setup ships none today.

Exercises the three Tier-selection orchestration paths after the migration onto
credbroker's public write API, plus the import-surface invariant (no
credentials_shim, no underscore-prefixed credbroker name). Run as:
``python -m pytest test_setup.py`` from this directory (credbroker installed).
"""

from __future__ import annotations

import ast
import importlib.util
import os
import pathlib
import subprocess
import sys

import pytest

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
import setup  # noqa: E402

from credbroker import _core  # noqa: E402

_HAS_CRYPTO = (
    importlib.util.find_spec("cryptography") is not None
    and importlib.util.find_spec("argon2") is not None
)
requires_crypto = pytest.mark.skipif(not _HAS_CRYPTO, reason="requires the [crypto] extra")

SECRET = "tok-secret-value"


class _FakeBackend:
    def __init__(self):
        self.written = {}

    def write_credential(self, namespace, key, value):
        self.written[(namespace, key)] = value

    def read_credential(self, namespace, key):
        return self.written.get((namespace, key))


def _schema_file(tmp_path):
    p = tmp_path / "creds-schema.toml"
    p.write_text(
        '[namespace]\nname = "jira"\n\n'
        '[[namespace.keys]]\nname = "API_TOKEN"\nlabel = "Jira API token"\nsecret = true\n',
        encoding="utf-8",
    )
    return p


@pytest.fixture
def env(tmp_path, monkeypatch):
    home = tmp_path / "home"
    (home / ".agentbundle").mkdir(parents=True)
    monkeypatch.setenv("HOME", str(home))
    monkeypatch.setenv("USERPROFILE", str(home))
    monkeypatch.delenv(_core.VAULT_MASTER_ENV, raising=False)
    monkeypatch.setattr(sys.stdin, "isatty", lambda: True)
    # Bypass interactive value entry; the orchestration under test is tier
    # selection + write, not the prompt loop.
    monkeypatch.setattr(setup, "_prompt", lambda schema: {"API_TOKEN": SECRET})
    return home


def _run(tmp_path, *flags):
    return setup.main([*flags, "jira", "--schema-path", str(_schema_file(tmp_path))])


def test_keyring_path(env, tmp_path, monkeypatch):
    fake = _FakeBackend()
    monkeypatch.setattr(_core, "_tier2_backend", fake)
    rc = _run(tmp_path)
    assert rc == 0
    assert fake.written[("jira", "API_TOKEN")] == SECRET


@requires_crypto
def test_no_keyring_crypto_vault_master_from_env(env, tmp_path, monkeypatch):
    monkeypatch.setattr(_core, "_tier2_backend", None)
    monkeypatch.setenv(_core.VAULT_MASTER_ENV, "master-pw")
    rc = _run(tmp_path)
    assert rc == 0
    from credbroker import _vault

    assert _vault.read_credential("jira", "API_TOKEN", master="master-pw", path=_core._vault_path()) == SECRET


@requires_crypto
def test_no_keyring_crypto_prompts_and_establishes_master(env, tmp_path, monkeypatch):
    monkeypatch.setattr(_core, "_tier2_backend", None)
    # No master sourceable -> _write_tier3 prompts via getpass; mock it.
    monkeypatch.setattr(setup.getpass, "getpass", lambda *a, **k: "freshly-set-master")
    rc = _run(tmp_path)
    assert rc == 0
    # The master was established on disk at 0600, and the value is in the vault.
    mf = _core._vault_master_file()
    assert mf.is_file()
    if os.name == "posix":
        assert (mf.stat().st_mode & 0o077) == 0  # not group/other accessible
    from credbroker import _vault

    assert _vault.read_credential("jira", "API_TOKEN", master="freshly-set-master", path=_core._vault_path()) == SECRET


@requires_crypto
def test_wrong_master_against_existing_vault_exits_3_not_traceback(env, tmp_path, monkeypatch):
    monkeypatch.setattr(_core, "_tier2_backend", None)
    from credbroker import _vault

    v = _vault.Vault.create("right-master", path=_core._vault_path())
    v.set("jira", "API_TOKEN", "old")
    v.save()
    # A wrong sourced master must fail cleanly (exit 3), not dump a traceback.
    monkeypatch.setenv(_core.VAULT_MASTER_ENV, "wrong-master")
    assert _run(tmp_path) == 3


@requires_crypto
def test_permissive_master_file_exits_3(env, tmp_path, monkeypatch):
    if os.name != "posix":
        pytest.skip("POSIX mode check")
    monkeypatch.setattr(_core, "_tier2_backend", None)
    mf = _core._vault_master_file()
    mf.write_text("some-master")
    os.chmod(mf, 0o644)  # group/other-readable -> source rejects -> clean exit 3
    assert _run(tmp_path) == 3


def test_no_keyring_no_crypto_falls_to_dotfile(env, tmp_path, monkeypatch):
    monkeypatch.setattr(_core, "_tier2_backend", None)
    monkeypatch.setattr(setup, "crypto_available", lambda: False)  # simulate no [crypto]
    rc = _run(tmp_path)
    assert rc == 0
    creds = _core.load_credentials("jira", required_keys=["API_TOKEN"])
    assert creds.API_TOKEN == SECRET


def test_missing_credbroker_exits_3_with_install_hint(tmp_path):
    """setup.py with credbroker unresolvable exits 3 with a clean install hint
    to stderr, not a ModuleNotFoundError traceback.

    credbroker is installed in this interpreter, so the only honest way to
    exercise the guard is a subprocess where credbroker resolves through none
    of its three discovery paths: ``-S`` skips site-packages (and any editable
    ``.pth``), a temp ``HOME`` makes the ``~/.agentbundle/lib`` floor absent,
    and ``PYTHONPATH`` is absent from the child env (allowlist dict, not
    inherited — there is no ``delenv``/``pop`` to grep for).
    """
    home = tmp_path / "home"
    home.mkdir()
    # The floor must be absent under the test HOME; if a real ~/.agentbundle/lib
    # leaked in, credbroker would resolve and the guard would silently not fire,
    # leaving this test asserting on the wrong path. Fail loud if so.
    assert not (home / ".agentbundle" / "lib").exists()
    env = {
        "HOME": str(home),
        "USERPROFILE": str(home),
        "PATH": os.environ.get("PATH", ""),
    }
    if os.name == "nt":
        # Python needs SystemRoot to initialise on Windows.
        env["SYSTEMROOT"] = os.environ.get("SYSTEMROOT", "")
    proc = subprocess.run(
        [sys.executable, "-S", str(pathlib.Path(setup.__file__)), "jira"],
        capture_output=True,
        # Pin the decode to the ASCII contract the guard message honours, so a
        # future non-ASCII addition fails the assertion cleanly rather than
        # raising UnicodeDecodeError inside the test harness on an exotic locale.
        encoding="ascii",
        errors="replace",
        env=env,
    )
    assert proc.returncode == 3, (proc.returncode, proc.stderr)
    assert "pip install -e ./packages/credbroker" in proc.stderr
    assert "Traceback" not in proc.stderr


def test_non_credbroker_import_error_is_reraised(tmp_path):
    """A ModuleNotFoundError whose ``.name`` is not ``credbroker`` (credbroker
    present but importing a broken/absent dependency) surfaces unchanged — it is
    NOT reported as "credbroker not found". Guards the ``exc.name``
    narrowing branch against a mutation that drops it and treats every
    ModuleNotFoundError as a missing install.

    A fake ``credbroker`` package that fails on import with a *different*
    missing module is placed first on the child's import path (via PYTHONPATH,
    which precedes site-packages) so it shadows the real installed one.
    """
    fake = tmp_path / "fakelib"
    (fake / "credbroker").mkdir(parents=True)
    (fake / "credbroker" / "__init__.py").write_text(
        "import a_module_that_does_not_exist_zzz\n", encoding="utf-8"
    )
    env = dict(os.environ)
    env["PYTHONPATH"] = str(fake)
    proc = subprocess.run(
        [sys.executable, str(pathlib.Path(setup.__file__)), "jira"],
        capture_output=True,
        text=True,
        env=env,
    )
    # Re-raised: the real fault surfaces (the OTHER module's name, a traceback),
    # and the guard's credbroker install hint is NOT shown.
    assert proc.returncode != 3, (proc.returncode, proc.stderr)
    assert "a_module_that_does_not_exist_zzz" in proc.stderr
    assert "pip install -e ./packages/credbroker" not in proc.stderr


def test_setup_imports_credbroker_not_shim_nor_private():
    src = pathlib.Path(setup.__file__).read_text()
    tree = ast.parse(src)
    target = "credentials" + "_shim"
    imported_credbroker = False
    for node in ast.walk(tree):
        if isinstance(node, ast.ImportFrom):
            assert node.module != target, "setup.py must not import the shim"
            if (node.module or "").split(".")[0] == "credbroker":
                imported_credbroker = True
                for alias in node.names:
                    assert not alias.name.startswith("_"), f"private credbroker import: {alias.name}"
    assert imported_credbroker, "setup.py must import from credbroker"
