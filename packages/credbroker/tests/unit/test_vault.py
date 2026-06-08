"""Encrypted-vault tests (spec task T4; AC5, AC13).

Gated on the `[crypto]` extra — skip cleanly when cryptography/argon2 are
absent (the base install). Verifies the round-trip, fail-closed-on-wrong-master,
tamper detection, encryption-at-rest, the self-describing Profile-A header, and
that no value/master leaks into an error message.
"""

from __future__ import annotations

import json

import pytest

pytest.importorskip("cryptography")
pytest.importorskip("argon2")

from credbroker import _vault  # noqa: E402
from credbroker._vault import Vault, VaultError  # noqa: E402

MASTER = "correct horse battery staple"
WRONG = "Tr0ub4dor&3"
SECRET = "super-secret-token-value-XYZ"


def _vault_file(tmp_path):
    return tmp_path / "credentials.vault"


def test_round_trip(tmp_path):
    path = _vault_file(tmp_path)
    v = Vault.create(MASTER, path=path)
    v.set("jira", "API_TOKEN", SECRET)
    v.save()

    reopened = Vault.open(MASTER, path=path)
    assert reopened.get("jira", "API_TOKEN") == SECRET


def test_module_convenience_round_trip(tmp_path):
    path = _vault_file(tmp_path)
    _vault.set_credential("figma", "API_TOKEN", SECRET, master=MASTER, path=path)
    assert _vault.read_credential("figma", "API_TOKEN", master=MASTER, path=path) == SECRET


def test_missing_entry_returns_none(tmp_path):
    path = _vault_file(tmp_path)
    Vault.create(MASTER, path=path).save()
    assert Vault.open(MASTER, path=path).get("jira", "NOPE") is None


def test_read_credential_none_when_vault_absent(tmp_path):
    path = _vault_file(tmp_path)  # never created
    assert _vault.read_credential("jira", "API_TOKEN", master=MASTER, path=path) is None


def test_wrong_master_fails_closed(tmp_path):
    path = _vault_file(tmp_path)
    v = Vault.create(MASTER, path=path)
    v.set("jira", "API_TOKEN", SECRET)
    v.save()

    with pytest.raises(VaultError) as exc:
        Vault.open(WRONG, path=path)
    # Fail-closed: no plaintext, no master, no raw key bytes in the message.
    msg = str(exc.value)
    assert SECRET not in msg
    assert WRONG not in msg
    assert MASTER not in msg


def test_wrong_master_via_read_credential_raises_not_none(tmp_path):
    # A wrong master must NOT degrade to a clean miss (None) — that would mask a
    # present credential behind a bad master. It must raise.
    path = _vault_file(tmp_path)
    _vault.set_credential("jira", "API_TOKEN", SECRET, master=MASTER, path=path)
    with pytest.raises(VaultError) as exc:
        _vault.read_credential("jira", "API_TOKEN", master=WRONG, path=path)
    # No-leak holds on the read path too (AC13 applies to every failure path).
    msg = str(exc.value)
    assert SECRET not in msg and WRONG not in msg and MASTER not in msg


@pytest.mark.parametrize("value", ["", "pāß-wörd-🔑", 'has "quotes" and $vars', "x" * 4096])
def test_round_trip_edge_values(tmp_path, value):
    # The vault accepts values the plaintext dotfile refuses (embedded " and $)
    # — pin that wider acceptance, plus empty and unicode, as intentional.
    path = _vault_file(tmp_path)
    _vault.set_credential("ns", "K", value, master=MASTER, path=path)
    assert _vault.read_credential("ns", "K", master=MASTER, path=path) == value


def test_overwrite_existing_entry(tmp_path):
    path = _vault_file(tmp_path)
    _vault.set_credential("jira", "API_TOKEN", "old", master=MASTER, path=path)
    _vault.set_credential("jira", "API_TOKEN", "new", master=MASTER, path=path)
    assert _vault.read_credential("jira", "API_TOKEN", master=MASTER, path=path) == "new"


def test_out_of_bounds_memory_cost_fails_closed_not_oom(tmp_path):
    # A hostile/corrupt header with an absurd memory_cost must raise VaultError
    # BEFORE deriving (else it OOMs / raises an uncaught argon2 error).
    path = _vault_file(tmp_path)
    Vault.create(MASTER, path=path).save()
    doc = json.loads(path.read_text())
    doc["kdf"]["memory_cost"] = 99_999_999  # ~95 GiB
    path.write_text(json.dumps(doc))
    with pytest.raises(VaultError):
        Vault.open(MASTER, path=path)


def test_unsupported_version_fails_closed(tmp_path):
    path = _vault_file(tmp_path)
    Vault.create(MASTER, path=path).save()
    doc = json.loads(path.read_text())
    doc["version"] = 999
    path.write_text(json.dumps(doc))
    with pytest.raises(VaultError):
        Vault.open(MASTER, path=path)


def test_oversize_vault_refused_before_read(tmp_path):
    # Symmetric with the dotfile's DOTFILE_MAX_BYTES: a vault file larger than
    # the cap is refused (VaultError) rather than json-loaded into memory.
    path = _vault_file(tmp_path)
    Vault.create(MASTER, path=path).save()
    with path.open("a", encoding="utf-8") as fh:
        fh.write(" " * (_vault.VAULT_MAX_BYTES + 1))
    with pytest.raises(VaultError) as exc:
        Vault.open(MASTER, path=path)
    assert "refusing to read more than" in str(exc.value)


def test_unknown_algo_fails_closed(tmp_path):
    path = _vault_file(tmp_path)
    Vault.create(MASTER, path=path).save()
    doc = json.loads(path.read_text())
    doc["kdf"]["algo"] = "pbkdf2"
    path.write_text(json.dumps(doc))
    with pytest.raises(VaultError):
        Vault.open(MASTER, path=path)


def test_param_tamper_fails_closed(tmp_path):
    # Downgrading the cost params changes the derived KEK, so the wrapped-DEK
    # tag check fails — params are implicitly KDF-authenticated.
    path = _vault_file(tmp_path)
    Vault.create(MASTER, path=path).save()
    doc = json.loads(path.read_text())
    doc["kdf"]["time_cost"] = 1  # in-bounds but different from what was used
    path.write_text(json.dumps(doc))
    with pytest.raises(VaultError):
        Vault.open(MASTER, path=path)


def test_tampered_entry_fails_closed(tmp_path):
    path = _vault_file(tmp_path)
    v = Vault.create(MASTER, path=path)
    v.set("jira", "API_TOKEN", SECRET)
    v.save()

    doc = json.loads(path.read_text())
    # Flip the last base64 char of the ciphertext to a different value.
    ct = doc["entries"]["JIRA_API_TOKEN"]["ct"]
    doc["entries"]["JIRA_API_TOKEN"]["ct"] = ct[:-1] + ("A" if ct[-1] != "A" else "B")
    path.write_text(json.dumps(doc))

    with pytest.raises(VaultError):
        Vault.open(MASTER, path=path).get("jira", "API_TOKEN")


def test_value_is_encrypted_at_rest(tmp_path):
    path = _vault_file(tmp_path)
    v = Vault.create(MASTER, path=path)
    v.set("jira", "API_TOKEN", SECRET)
    v.save()
    raw = path.read_text()
    assert SECRET not in raw  # the plaintext value never appears on disk


def test_header_is_self_describing_profile_a(tmp_path):
    path = _vault_file(tmp_path)
    Vault.create(MASTER, path=path).save()
    kdf = json.loads(path.read_text())["kdf"]
    assert kdf["algo"] == "argon2id"
    assert kdf["time_cost"] == 3
    assert kdf["memory_cost"] == 65536
    assert kdf["parallelism"] == 4
    assert "salt" in kdf


def test_entry_name_binding_rejects_relocation(tmp_path):
    # A ciphertext is bound to its entry name via AES-GCM associated data;
    # copying it under a different name must fail authentication.
    path = _vault_file(tmp_path)
    v = Vault.create(MASTER, path=path)
    v.set("jira", "API_TOKEN", SECRET)
    v.save()

    doc = json.loads(path.read_text())
    doc["entries"]["FIGMA_API_TOKEN"] = doc["entries"]["JIRA_API_TOKEN"]
    path.write_text(json.dumps(doc))

    with pytest.raises(VaultError):
        Vault.open(MASTER, path=path).get("figma", "API_TOKEN")


def test_0600_mode_on_posix(tmp_path):
    import os
    import stat

    if os.name != "posix":
        pytest.skip("POSIX mode check")
    path = _vault_file(tmp_path)
    Vault.create(MASTER, path=path).save()
    mode = stat.S_IMODE(path.stat().st_mode)
    assert mode == 0o600
