"""Exception hierarchy for the credentialed-primitive loader (spec § AC3, AC11).

``CredentialsMissingError`` — at least one required key did not resolve at
any tier; the message names the namespace and the missing keys.

``Tier2HardFailError`` — the OS keyring (Tier 2) returned a non-recoverable
error code (e.g. ``ERROR_NO_SUCH_LOGON_SESSION`` on Windows). Per spec §
AC11, the resolver does **not** fall through to Tier 3 in this case;
silent degradation defeats the security posture the user chose.
"""

from __future__ import annotations


class CredentialsMissingError(Exception):
    """Raised when a required credential key cannot be resolved at any tier.

    Carries structured per-key tier diagnostics so programmatic callers can
    render their own remediation; the default ``str()`` form (built by
    ``load_credentials``) embeds the per-key trailer for human readers.

    Attributes:
        namespace: the namespace requested.
        missing: the list of keys that did not resolve.
        tiers_tried: ``{key: [trailer_line, ...]}`` — for each missing
            key, an ordered list of strings describing which tier was
            checked and why it missed. ``trailer_line`` shape is
            ``"<tier-label>: <reason>"`` (e.g. ``"Tier 1 env
            'JIRA_API_TOKEN' not set"``, ``"Tier 2 macOS Keychain: not
            present"``, ``"Tier 3 dotfile /home/u/.agent-ready/credentials.env
            absent"``).
    """

    def __init__(
        self,
        message: str,
        *,
        namespace: str | None = None,
        missing: list[str] | None = None,
        tiers_tried: dict[str, list[str]] | None = None,
    ) -> None:
        super().__init__(message)
        self.namespace = namespace
        self.missing = list(missing) if missing else []
        self.tiers_tried = dict(tiers_tried) if tiers_tried else {}


class Tier2HardFailError(Exception):
    """Raised when the OS keyring backend returns a hard-fail error code."""


class PermissiveAclError(Exception):
    """Raised when the Windows DACL on the Tier-3 dotfile is too permissive.

    Per spec § AC15: ``icacls`` is invoked after each write; non-default
    ACEs (anything beyond the inherited user / ``NT AUTHORITY\\SYSTEM`` /
    ``BUILTIN\\Administrators``) cause the helper to refuse unless
    ``allow_permissive_acl=True`` was passed.
    """


class SchemaError(Exception):
    """Raised when a ``creds-schema.toml`` file is malformed or missing.

    Per spec § AC24 / AC24b — names the offending file path and the
    specific shape violation (missing ``[namespace]``, empty
    ``namespace.keys``, non-boolean ``secret``, or unresolvable
    canonical path).
    """
