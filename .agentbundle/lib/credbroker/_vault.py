"""Encrypted-at-rest credential vault for the `credbroker[crypto]` extra.

RFC-0023's Tier-3 floor upgrade: instead of a plaintext `0600` dotfile, the
optional `[crypto]` extra stores values in an AEAD-encrypted file. This module
imports `cryptography` and `argon2` at top level, so it is imported **lazily**
(never from `credbroker/__init__.py` or `credbroker/_core.py`) — the base import
graph stays third-party-free (spec AC4). A consumer reaches it only through the
Tier-3 dispatch path (T5) or the credential-setup write path (T8).

Key hierarchy (authsome's scheme):

    master secret ──Argon2id(salt)──▶ KEK (32B)
    KEK ──AES-256-GCM-wrap──▶ DEK (32B, random, generated once per vault)
    DEK ──AES-256-GCM(nonce)──▶ each value

The DEK indirection lets the master/KEK rotate by re-wrapping the DEK without
re-encrypting every value. Each vault is **self-describing**: it stores its own
salt and Argon2 parameters, so the defaults below apply only to *newly created*
vaults — an existing vault always decrypts with the parameters it was written
with, even if these defaults change later.

Argon2id parameters are **Profile A** — RFC 9106 §4's second recommended option
(t=3, m=64 MiB, p=4), the argon2-cffi default. Signed off 2026-06-08 (spec
Boundaries → Ask first).

Entry *names* (`<NAMESPACE>_<KEY>`) are stored in cleartext as map keys — they
are which-service/which-field metadata, not secrets; only values are encrypted.
Each value's entry name is bound as AES-GCM associated data, so a ciphertext
cannot be relocated to a different entry without failing authentication.
"""

from __future__ import annotations

import base64
import json
import os
import pathlib
import tempfile

from argon2.low_level import Type, hash_secret_raw
from cryptography.exceptions import InvalidTag
from cryptography.hazmat.primitives.ciphers.aead import AESGCM

# Reuse the stdlib core's entry-name composition + filesystem discipline so the
# vault and the plaintext dotfile agree on names and write semantics. Importing
# _core from _vault is fine — _core stays third-party-free; only the reverse
# (importing _vault from _core) would break the base-import purity gate.
from ._core import _dotfile_env_name, _ensure_parent, _vault_path, _verify_icacls

VAULT_VERSION = 1

# Upper bound on the vault file, mirroring the Tier-3 dotfile's DOTFILE_MAX_BYTES.
# A vault holds a few dozen base64'd entries; 1 MiB is orders of magnitude over
# the realistic ceiling. A larger file is corruption or a misconfigured/hostile
# path — refuse it before json.loads pulls the whole thing into memory.
VAULT_MAX_BYTES = 1 << 20  # 1 MiB

# Profile A — RFC 9106 §4 second-recommended (argon2-cffi default). Stored in
# each vault's header so these are defaults for *new* vaults only.
ARGON2_TIME_COST = 3
ARGON2_MEMORY_COST = 65536  # KiB == 64 MiB
ARGON2_PARALLELISM = 4

KEY_LEN = 32  # AES-256 KEK / DEK
SALT_LEN = 16
NONCE_LEN = 12  # AES-GCM standard nonce

# Associated data binding the DEK wrap to this purpose + version.
_DEK_WRAP_AAD = b"credbroker:dek-wrap:v1"

# Sanity bounds for KDF params parsed from a vault header.
#
# Note the params are already *implicitly authenticated*: a tampered cost or
# salt yields a different KEK, so the wrapped-DEK tag check fails for every
# master guess — a work-factor *downgrade* therefore can't speed up offline
# cracking (the wrap was made under the original-cost KEK; no guess validates
# under a different cost). These bounds are not about cracking; they defend
# availability — an absurd memory_cost from a corrupt or hostile header would
# OOM (or raise an uncaught argon2 MemoryError) *before* the wrap-tag check can
# run, so we refuse out-of-range params up front and convert any derivation
# failure into a clean VaultError.
_MEMORY_COST_BOUNDS = (8 * 1024, 2 * 1024 * 1024)  # KiB: 8 MiB .. 2 GiB
_TIME_COST_BOUNDS = (1, 16)
_PARALLELISM_BOUNDS = (1, 16)


def _check_param_bounds(params: dict[str, int]) -> None:
    """Raise ``VaultError`` if any parsed KDF cost is outside sane bounds."""
    for name, (lo, hi) in (
        ("memory_cost", _MEMORY_COST_BOUNDS),
        ("time_cost", _TIME_COST_BOUNDS),
        ("parallelism", _PARALLELISM_BOUNDS),
    ):
        if not (lo <= params[name] <= hi):
            raise VaultError(
                f"vault KDF parameter {name}={params[name]} out of accepted "
                f"range [{lo}, {hi}] — refusing (corrupt or hostile header)"
            )


class VaultError(Exception):
    """Raised when the vault cannot be unlocked or an entry fails to decrypt.

    Fail-closed: a wrong master secret, a corrupted vault, or a tampered entry
    raises this rather than returning partial or garbage plaintext. The message
    never embeds a credential value, the master, or raw ciphertext/key bytes.
    """


def _b64e(raw: bytes) -> str:
    return base64.b64encode(raw).decode("ascii")


def _b64d(text: str) -> bytes:
    return base64.b64decode(text.encode("ascii"))


def _derive_kek(master: str, salt: bytes, *, time_cost: int, memory_cost: int,
                parallelism: int) -> bytes:
    """Derive the 32-byte KEK from the master secret via Argon2id."""
    return hash_secret_raw(
        secret=master.encode("utf-8"),
        salt=salt,
        time_cost=time_cost,
        memory_cost=memory_cost,
        parallelism=parallelism,
        hash_len=KEY_LEN,
        type=Type.ID,
    )


class Vault:
    """An encrypted credential vault, opened or created from a master secret.

    Open once (one Argon2id derivation), then ``set``/``get``/``delete`` many
    entries and ``save`` once — the credential-setup write path (T8) uses this
    shape; the per-invocation Tier-3 read (T5) uses the module-level
    ``read_credential`` convenience instead.
    """

    __slots__ = ("_path", "_salt", "_params", "_kek", "_dek", "_entries")

    def __init__(self, path: pathlib.Path, salt: bytes, params: dict[str, int],
                 kek: bytes, dek: bytes, entries: dict[str, dict[str, str]]) -> None:
        self._path = path
        self._salt = salt
        self._params = params
        self._kek = kek
        self._dek = dek
        self._entries = entries

    # ── construction ──────────────────────────────────────────────────

    @classmethod
    def create(cls, master: str, *, path: pathlib.Path | None = None) -> "Vault":
        """Create a fresh (unsaved) vault with a new random salt + DEK."""
        path = path or _vault_path()
        salt = os.urandom(SALT_LEN)
        params = {
            "time_cost": ARGON2_TIME_COST,
            "memory_cost": ARGON2_MEMORY_COST,
            "parallelism": ARGON2_PARALLELISM,
        }
        kek = _derive_kek(master, salt, **params)
        dek = os.urandom(KEY_LEN)
        return cls(path, salt, params, kek, dek, entries={})

    @classmethod
    def open(cls, master: str, *, path: pathlib.Path | None = None) -> "Vault":
        """Open an existing vault; raise ``VaultError`` if the master is wrong.

        Derives the KEK from the *stored* salt + parameters, then unwraps the
        DEK — a wrong master yields a wrong KEK and the AEAD tag check fails,
        which is the fail-closed signal. Entry payloads are validated **lazily**
        on ``get()`` (a single corrupt entry errors only when read, leaving the
        rest of the vault usable), not eagerly at unlock.
        """
        path = path or _vault_path()
        try:
            size = path.stat().st_size
        except OSError:
            size = 0
        if size > VAULT_MAX_BYTES:
            raise VaultError(
                f"vault {path} is {size} bytes; refusing to read more than "
                f"{VAULT_MAX_BYTES} — verify the path is the credentials vault, "
                f"not a misconfigured target"
            )
        try:
            doc = json.loads(path.read_text(encoding="utf-8"))
        except FileNotFoundError as exc:
            raise VaultError(f"vault not found: {path}") from exc
        except (json.JSONDecodeError, OSError) as exc:
            raise VaultError(f"vault unreadable or malformed: {path}") from exc

        kdf = doc.get("kdf") or {}
        try:
            salt = _b64d(kdf["salt"])
            params = {
                "time_cost": int(kdf["time_cost"]),
                "memory_cost": int(kdf["memory_cost"]),
                "parallelism": int(kdf["parallelism"]),
            }
            wrapped = doc["wrapped_dek"]
            wrap_nonce = _b64d(wrapped["nonce"])
            wrapped_ct = _b64d(wrapped["ct"])
            entries = dict(doc.get("entries") or {})
        except (KeyError, TypeError, ValueError, base64.binascii.Error) as exc:
            raise VaultError(f"vault header malformed: {path}") from exc

        if int(doc.get("version", 0)) != VAULT_VERSION:
            raise VaultError(
                f"unsupported vault version {doc.get('version')!r} "
                f"(this credbroker reads version {VAULT_VERSION})"
            )
        # Make `algo` load-bearing rather than decorative: the reader is hardwired
        # to Argon2id, so refuse any other declared algo now — closes the latent
        # downgrade footgun before a future algo-agile reader could honour it.
        if (kdf.get("algo") or "").lower() != "argon2id":
            raise VaultError(
                f"unsupported vault KDF algo {kdf.get('algo')!r} (expected argon2id)"
            )
        _check_param_bounds(params)  # refuse OOM-class params before deriving
        try:
            kek = _derive_kek(master, salt, **params)
        except Exception as exc:  # e.g. argon2 MemoryError on an absurd cost
            raise VaultError("vault key derivation failed (corrupt KDF parameters?)") from exc
        try:
            dek = AESGCM(kek).decrypt(wrap_nonce, wrapped_ct, _DEK_WRAP_AAD)
        except InvalidTag as exc:
            # Wrong master secret or tampered DEK wrap — fail closed.
            raise VaultError(
                "could not unlock vault — wrong master secret or corrupted vault"
            ) from exc
        return cls(path, salt, params, kek, dek, entries)

    @staticmethod
    def exists(path: pathlib.Path | None = None) -> bool:
        return (path or _vault_path()).is_file()

    # ── entry access ──────────────────────────────────────────────────

    def set(self, namespace: str, key: str, value: str) -> None:
        """Encrypt ``value`` under ``<NAMESPACE>_<KEY>`` (in memory; call save)."""
        name = _dotfile_env_name(namespace, key)
        nonce = os.urandom(NONCE_LEN)
        # AAD == the storage key (entry name): binds the ciphertext to its slot
        # so it can't be relocated to another entry without failing the tag.
        ct = AESGCM(self._dek).encrypt(nonce, value.encode("utf-8"), name.encode("utf-8"))
        self._entries[name] = {"nonce": _b64e(nonce), "ct": _b64e(ct)}

    def get(self, namespace: str, key: str) -> str | None:
        """Decrypt ``<NAMESPACE>_<KEY>``; ``None`` if absent, raise if tampered."""
        name = _dotfile_env_name(namespace, key)
        entry = self._entries.get(name)
        if entry is None:
            return None
        try:
            nonce = _b64d(entry["nonce"])
            ct = _b64d(entry["ct"])
            pt = AESGCM(self._dek).decrypt(nonce, ct, name.encode("utf-8"))
        except InvalidTag as exc:
            raise VaultError(f"entry {name!r} failed authentication (tampered or corrupt)") from exc
        except (KeyError, TypeError, ValueError, base64.binascii.Error) as exc:
            raise VaultError(f"entry {name!r} malformed") from exc
        return pt.decode("utf-8")

    def delete(self, namespace: str, key: str) -> None:
        self._entries.pop(_dotfile_env_name(namespace, key), None)

    # ── persistence ───────────────────────────────────────────────────

    def _serialize(self) -> str:
        wrap_nonce = os.urandom(NONCE_LEN)
        wrapped_ct = AESGCM(self._kek).encrypt(wrap_nonce, self._dek, _DEK_WRAP_AAD)
        doc = {
            "version": VAULT_VERSION,
            "kdf": {
                "algo": "argon2id",
                "salt": _b64e(self._salt),
                **self._params,
            },
            "wrapped_dek": {"nonce": _b64e(wrap_nonce), "ct": _b64e(wrapped_ct)},
            "entries": self._entries,
        }
        return json.dumps(doc, indent=2, sort_keys=True) + "\n"

    def save(self, *, allow_permissive_acl: bool = False) -> None:
        """Atomically write the vault at mode 0600 (same discipline as the dotfile).

        The DEK is re-wrapped with a fresh nonce on every save.
        """
        content = self._serialize().encode("utf-8")
        parent = self._path.parent
        _ensure_parent(parent)
        fd, tmp_path_str = tempfile.mkstemp(dir=str(parent), prefix=".vault.")
        tmp_path = pathlib.Path(tmp_path_str)
        try:
            # Write all bytes (os.write may write fewer than requested), set
            # 0600 before close on POSIX, and fsync so the rename can't expose
            # a torn vault after a crash.
            mv = memoryview(content)
            while mv:
                mv = mv[os.write(fd, mv):]
            if os.name == "posix":
                os.fchmod(fd, 0o600)
            os.fsync(fd)
            os.close(fd)
            if os.name == "nt":
                _verify_icacls(tmp_path, allow_permissive_acl=allow_permissive_acl)
            os.replace(tmp_path, self._path)
        except Exception:
            try:
                os.unlink(tmp_path)
            except OSError:
                pass
            raise


# ── module-level convenience (per-invocation open) ─────────────────────


def set_credential(namespace: str, key: str, value: str, *, master: str,
                   path: pathlib.Path | None = None) -> None:
    """Open-or-create the vault, set one entry, and save. One Argon2id pass."""
    path = path or _vault_path()
    vault = Vault.open(master, path=path) if Vault.exists(path) else Vault.create(master, path=path)
    vault.set(namespace, key, value)
    vault.save()


def read_credential(namespace: str, key: str, *, master: str,
                    path: pathlib.Path | None = None) -> str | None:
    """Read one entry from the vault. ``None`` if the vault is absent.

    Raises ``VaultError`` on a wrong master or a tampered entry — the caller
    (Tier-3 dispatch, T5) must surface that rather than treat it as a clean
    miss, so a wrong master never silently degrades to "credential missing".
    """
    path = path or _vault_path()
    if not Vault.exists(path):
        return None
    return Vault.open(master, path=path).get(namespace, key)
