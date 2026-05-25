"""Worked example credentialed-CLI primitive (skill-secrets spec § AC29).

Bound to a fictional ``example`` API. The CLI is a no-op — it does
not make any real network call — so adopters can read the source
without running it.

Two verbs:

- ``call`` — resolves both schema keys (``API_TOKEN`` and ``BASE_URL``)
  through ``agentbundle.credentials.load_credentials``, demonstrates
  the sibling-key Tier resolution the schema's ``BASE_URL`` entry
  advertises, validates the URL shape, and prints
  ``would call example API at <base_url> (token=*** present)`` to
  stdout. The token bytes never leave the function-local variable;
  the printed ``token=***`` is a deliberate echo-safe placeholder
  and *no length is disclosed* — token-length is a minor side-channel
  adopters should not normalise.
- ``check`` — resolves the same keys and exits 0 if both are present,
  exit 2 if any is missing (matches ``agentbundle creds check``).

Exit codes (the contract adopters should copy):
  0 — success.
  2 — at least one required credential missing (``CredentialsMissingError``).
  3 — Tier-2 keyring backend hard fail (``Tier2HardFailError``) or
       ``BASE_URL`` failed URL-shape validation.

The argv parser does **not** declare any of the banned flags
(``--token`` / ``--api-token`` / ``--api-key`` / ``--bearer`` /
``--pat`` / ``--password``); the credentialed-CLI lint
(``tools/lint-credentialed-skills.sh``) refuses skills that do.
``BASE_URL`` is resolved through the same Tier 1 → 2 → 3 ladder as
``API_TOKEN`` — it is declared ``secret = false`` so the
``agentbundle creds setup`` flow prompts for it via ``input()``
rather than ``getpass``.
"""

from __future__ import annotations

import argparse
import sys
from urllib.parse import urlparse

from agentbundle.credentials import (
    CredentialsMissingError,
    Tier2HardFailError,
    load_credentials,
)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="example-credentialed-skill",
        description="No-op worked example of a credentialed primitive.",
    )
    parser.add_argument(
        "verb",
        choices=("call", "check"),
        help="What the primitive does (no-op smoke test).",
    )
    args = parser.parse_args(argv)

    try:
        creds = load_credentials(
            "example",
            required_keys=["API_TOKEN", "BASE_URL"],
        )
    except CredentialsMissingError as exc:
        sys.stderr.write(f"{exc}\n")
        sys.stderr.write(
            "run `agentbundle creds setup example` to set the missing keys\n"
        )
        return 2
    except Tier2HardFailError as exc:
        # Adopters: copy this catch verbatim. macOS Keychain unlock
        # failures, Windows DPAPI errors (AC11), and similar hard-fails
        # surface here — never let the traceback escape, since the
        # exception's repr can include keyring error strings that
        # narrow attacker reconnaissance.
        sys.stderr.write(f"keychain unavailable: {exc}\n")
        sys.stderr.write(
            "see `agentbundle creds where example` to inspect tier resolution\n"
        )
        return 3

    if args.verb == "check":
        sys.stdout.write("example: credentials resolved\n")
        return 0

    # ``call`` verb — no real network. Validate the URL shape so
    # adopters who copy this don't end up issuing requests to garbage
    # values that resolved at some tier but aren't actually URLs.
    parsed = urlparse(creds.BASE_URL)
    if not parsed.scheme or not parsed.netloc:
        sys.stderr.write(
            f"BASE_URL is not a valid URL: {creds.BASE_URL!r}\n"
        )
        return 3

    # The token is referenced (``creds.API_TOKEN``) to prove resolution
    # but the value bytes are never printed. No length disclosure —
    # token length is a small side-channel; adopters should not
    # normalise leaking it.
    _ = creds.API_TOKEN  # noqa: F841 — resolution proof, deliberately unused
    sys.stdout.write(
        f"would call example API at {creds.BASE_URL} (token=*** present)\n"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
