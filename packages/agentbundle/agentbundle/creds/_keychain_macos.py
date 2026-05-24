"""macOS Keychain Tier-2 backend (spec § AC6-AC8).

Stdlib subprocess against ``/usr/bin/security`` — the system-shipped
Keychain CLI. Guaranteed present on every macOS install per spec §
Boundaries § Never do (no third-party ``keyring`` dependency).

Token bytes never reach argv:

- **Read** uses ``find-generic-password ... -w`` and captures the
  password from stdout.
- **Write** uses ``add-generic-password -U ... -w`` with the trailing
  ``-w`` as the *last* argument — per the ``security(1)`` man page
  ("Put at end of command to be prompted (recommended)"). The token is
  fed to the child via ``subprocess.Popen(stdin=PIPE)`` +
  ``proc.communicate(input=token.encode())``.
- **Delete** uses ``delete-generic-password`` (idempotent on miss).

The loader (``agentbundle.creds.loader``) imports this module **only**
when ``sys.platform == "darwin"`` per AC4b. Tests monkeypatch
``SERVICE`` to a ``tmp_path``-derived prefix so test entries never
collide with the developer's real ``agent-ready`` Keychain entries.
"""

from __future__ import annotations

import subprocess

from .exceptions import Tier2HardFailError

SECURITY_BIN = "/usr/bin/security"
SERVICE = "agent-ready"
# Tests monkeypatch ``SERVICE`` to a ``tmp_path``-derived prefix so test
# entries can't collide with real ``agent-ready`` entries in the
# developer's login Keychain. ``security``'s ``-w`` prompt mode requires
# ``-w`` as the trailing argv element, which forecloses the trailing-
# keychain-positional approach to test isolation; the service-prefix
# approach lets the canonical AC6 argv shape stay untouched.

# errSecItemNotFound (44) — legitimate "no such credential", falls
# through to Tier 3 per AC4 / AC11's macOS-side matrix in AC22.
EXIT_NOT_FOUND = 44


def _account(namespace: str, key: str) -> str:
    """Compose the Keychain account label per spec § AC6."""
    return f"{namespace}:{key}"


def read_credential(namespace: str, key: str) -> str | None:
    """Read ``(namespace, key)`` from the Keychain (spec § AC6, AC7)."""
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
        msg = proc.stderr.strip() or proc.stdout.strip()
        raise Tier2HardFailError(
            f"macOS Keychain read failed for {_account(namespace, key)!r} "
            f"(rc={proc.returncode}): {msg}"
        )
    # ``security -w`` prints the password to stdout, then a newline.
    return proc.stdout.rstrip("\n")


def write_credential(namespace: str, key: str, value: str) -> None:
    """Write ``value`` to ``(namespace, key)``. Token enters via child stdin
    only — never argv (spec § AC6, AC7).

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
        msg = err.decode("utf-8", errors="replace").strip()
        raise Tier2HardFailError(
            f"macOS Keychain write failed for {_account(namespace, key)!r} "
            f"(rc={proc.returncode}): {msg}"
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
        raise Tier2HardFailError(
            f"macOS Keychain delete failed (rc={proc.returncode}): "
            f"{proc.stderr.strip()}"
        )
