"""macOS Keychain Tier-2 backend.

Stdlib subprocess against ``/usr/bin/security`` — the system-shipped
Keychain CLI. Guaranteed present on every macOS install (no third-party
``keyring`` dependency).

Token bytes never reach argv:

- **Read** uses ``find-generic-password ... -w`` and captures the
  password from stdout.
- **Write** uses ``add-generic-password -U ... -w`` with the trailing
  ``-w`` as the *last* argument — per the ``security(1)`` man page
  ("Put at end of command to be prompted (recommended)"). The token is
  fed to the child via ``subprocess.Popen(stdin=PIPE)`` +
  ``proc.communicate(input=token.encode())``.
- **Delete** uses ``delete-generic-password`` (idempotent on miss).

``credbroker._core`` imports this module **only**
when ``sys.platform == "darwin"``. Tests monkeypatch
``SERVICE`` to a ``tmp_path``-derived prefix so test entries never
collide with the developer's real ``agentbundle`` Keychain entries.
"""

from __future__ import annotations

import subprocess

from ._core import Tier2HardFailError

SECURITY_BIN = "/usr/bin/security"
SERVICE = "agentbundle"
# Tests monkeypatch ``SERVICE`` to a ``tmp_path``-derived prefix so test
# entries can't collide with real ``agentbundle`` entries in the
# developer's login Keychain. ``security``'s ``-w`` prompt mode requires
# ``-w`` as the trailing argv element, which forecloses the trailing-
# keychain-positional approach to test isolation; the service-prefix
# approach lets the canonical argv shape stay untouched.

# macOS Security framework OSStatus codes:
#   44      errSecItemNotFound          — legitimate "no such credential",
#                                         falls through to Tier 3.
#   45      errSecDuplicateItem         — only relevant on add; the ``-U``
#                                         upsert flag means we never see it.
#   25308   errSecInteractionNotAllowed — Keychain locked / no UI.
#   -25291  errSecNotAvailable          — Keychain service unavailable.
#
# Names taken from ``<Security/SecBase.h>``. The two "Keychain locked /
# unavailable" codes (25308 / -25291) MUST raise ``Tier2HardFailError``
# so ``run_setup`` can route the fallback gate — silently
# degrading to Tier 3 defeats the security posture the user chose.
EXIT_NOT_FOUND = 44
EXIT_DUPLICATE_ITEM = 45
EXIT_INTERACTION_NOT_ALLOWED = 25308
EXIT_NOT_AVAILABLE = -25291


def _classify_macos_exit_code(rc: int, op: str) -> str | None:
    """Map a ``security`` exit code to a symbolic name string.

    Returns the symbolic name (e.g. ``"errSecInteractionNotAllowed
    (25308) — Keychain locked or no UI available"``) so the caller can
    embed it in a ``Tier2HardFailError`` message. Returns ``None`` for
    ``EXIT_NOT_FOUND`` (the caller treats that as a legitimate miss).

    Parallel in shape to ``_credman_windows._classify_last_error``.
    """
    if rc == 0:
        return None
    if rc == EXIT_NOT_FOUND:
        return None
    if rc == EXIT_INTERACTION_NOT_ALLOWED:
        return (
            f"errSecInteractionNotAllowed ({EXIT_INTERACTION_NOT_ALLOWED}) "
            f"— Keychain locked or no UI available"
        )
    if rc == EXIT_NOT_AVAILABLE:
        return (
            f"errSecNotAvailable ({EXIT_NOT_AVAILABLE}) "
            f"— Keychain service unavailable"
        )
    if rc == EXIT_DUPLICATE_ITEM:
        # The ``-U`` upsert flag means add-generic-password should never
        # surface this; document anyway so a future argv change that
        # drops ``-U`` produces a readable error rather than a generic
        # "rc=45".
        return (
            f"errSecDuplicateItem ({EXIT_DUPLICATE_ITEM}) "
            f"— entry already exists (missing ``-U`` upsert flag?)"
        )
    return f"security exit code {rc}"


def _account(namespace: str, key: str) -> str:
    """Compose the Keychain account label."""
    return f"{namespace}:{key}"


def read_credential(namespace: str, key: str) -> str | None:
    """Read ``(namespace, key)`` from the Keychain."""
    argv = [
        SECURITY_BIN, "find-generic-password",
        "-s", SERVICE,
        "-a", _account(namespace, key),
        "-w",
    ]
    proc = subprocess.run(argv, capture_output=True, text=True, check=False)
    if proc.returncode == EXIT_NOT_FOUND:
        return None
    if proc.returncode != 0:
        symbolic = _classify_macos_exit_code(proc.returncode, "read")
        stderr = proc.stderr.strip() or proc.stdout.strip()
        raise Tier2HardFailError(
            f"macOS Keychain read failed for {_account(namespace, key)!r}: "
            f"{symbolic}"
            + (f": {stderr}" if stderr else "")
        )
    # ``security -w`` prints the password to stdout, then a newline.
    return proc.stdout.rstrip("\n")


def write_credential(namespace: str, key: str, value: str) -> None:
    """Write ``value`` to ``(namespace, key)``. Token enters via child stdin
    only — never argv.

    Refuses values containing ``\\n`` or ``\\r`` up front. ``security -w``
    prompts twice and the stdin payload is ``token + b"\\n" + token + b"\\n"``;
    a token containing a newline mismatches the confirmation and
    ``security`` silently stores an empty password. Tier-3 dotfile quoting
    (``_quote_for_dotfile``) likewise cannot safely round-trip embedded
    newlines. One early refusal beats two silent corruption paths.
    """
    if "\n" in value or "\r" in value:
        raise Tier2HardFailError(
            f"macOS Keychain write refused for {_account(namespace, key)!r}: "
            f"token value contains an embedded newline (\\n or \\r). The "
            f"`security -w` re-prompt confirmation and Tier-3 dotfile "
            f"quoting both break on newlines; strip or replace the "
            f"character before writing."
        )
    argv = [
        SECURITY_BIN, "add-generic-password",
        "-U",  # upsert: replace if entry already exists
        "-s", SERVICE,
        "-a", _account(namespace, key),
        "-w",  # MUST be the last argv element — triggers prompt-from-stdin
    ]
    proc = subprocess.Popen(
        argv,
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    # ``security add-generic-password -w`` prompts twice ("password data
    # for new item:" then "retype password for new item:") — both lines
    # must match for the write to succeed. Mismatched lines silently
    # write an empty password. The value is sent twice on stdin with
    # newline terminators; the token still never reaches argv.
    token_bytes = value.encode("utf-8")
    stdin_payload = token_bytes + b"\n" + token_bytes + b"\n"
    _, err = proc.communicate(input=stdin_payload)
    if proc.returncode != 0:
        symbolic = _classify_macos_exit_code(proc.returncode, "write")
        stderr = err.decode("utf-8", errors="replace").strip()
        raise Tier2HardFailError(
            f"macOS Keychain write failed for {_account(namespace, key)!r}: "
            f"{symbolic}"
            + (f": {stderr}" if stderr else "")
        )


def delete_credential(namespace: str, key: str) -> None:
    """Idempotent delete — missing entry is not an error."""
    argv = [
        SECURITY_BIN, "delete-generic-password",
        "-s", SERVICE,
        "-a", _account(namespace, key),
    ]
    proc = subprocess.run(argv, capture_output=True, text=True, check=False)
    if proc.returncode == EXIT_NOT_FOUND:
        return
    if proc.returncode != 0:
        symbolic = _classify_macos_exit_code(proc.returncode, "delete")
        stderr = proc.stderr.strip()
        raise Tier2HardFailError(
            f"macOS Keychain delete failed: {symbolic}"
            + (f": {stderr}" if stderr else "")
        )
