#!/usr/bin/env python3
"""Repo-policy lint: keep published pack maintainer addresses non-identifying.

``agentbundle`` copies ``[[pack.maintainers]].email`` into published
marketplace manifests. That makes a personal maintainer address in a source
``pack.toml`` a release-path privacy concern, rather than merely repository
metadata. This lint permits addresses on a reviewed host set
(``ALLOWED_HOSTS``), plus whole-address exceptions in ``ALLOWED_EMAILS``.

It deliberately does not try to decide whether an address is personal. That
judgment is undecidable from an email string: a role mailbox can look personal,
and a personal mailbox can look like a role. The explicit allowlists are the
reviewed human decision for the cases a mechanical rule cannot classify.

**Why a host allowlist and not a no-reply pattern.** The first draft accepted
any address whose host contained a ``.noreply.`` label, or whose local part was
``noreply``. Review broke it in three ways, and the bypasses were the point of
the control rather than edge cases:
``alice.smith@alice-smith.noreply.example.test`` is personally identifying and
matched the host pattern; ``noreply@alice-smith.example.test`` put the person in
the host instead; and ``noreply@alice-smith@example.test`` -- not a valid
address at all -- passed because splitting on the first ``@`` left the local
part reading ``noreply``. A pattern over an attacker- or author-chosen string
cannot be made safe by adding more pattern. An allowlist can: the set of hosts
this repository publishes from is small, known, and changes in a reviewed diff.
Structural parsing (``_split_address``) runs first, and anything it cannot
resolve to exactly one ordinary ``local@host`` is refused rather than cleared.

**Why this lives in ``tools/`` and not in the ``agentbundle`` package.** The
published package validates adopter catalogues; imposing this repository's
privacy policy there would turn it into an adopter build break. This lint runs
only over this repository's own ``packs/`` tree through ``make build-check``.

Pure-stdlib, ``--root`` flagged, exit 0=pass / 1=violation / **2=scanned
nothing**.

**Why exit 2 exists.** A run that gated nothing must not read identically to a
run that gated everything — the failure this repository has been bitten by
elsewhere (a false green reproduced three times in one session by the catalogue
curation guard, since fixed). So finding no ``pack.toml`` at
all is an error here, not a pass. ``find_violations`` stays a pure function
returning ``[]``; the fail-closed decision lives in ``main``, where the
operator's intent — "lint this root" — is what went unmet.

This originally read as a deliberate divergence from
``lint-pack-descriptions.py``, which then printed a pass line over an empty
scan. That is no longer true: the same guard was added there on 2026-08-25, so
the two agree and the sentence is kept only to stop the divergence being
reintroduced as a "consistency" fix in the wrong direction.

Usage:
    python3 tools/lint-pack-maintainer-emails.py [--root .]
"""

from __future__ import annotations

import argparse
import sys
import tomllib
from pathlib import Path

# Hosts whose addresses cannot identify a person no matter the local part.
# This is an allowlist, not a pattern, and that is the point -- see the module
# docstring's § "Why a host allowlist and not a no-reply pattern". Adding a host
# is a reviewed diff; state the reason beside it.
ALLOWED_HOSTS: frozenset[str] = frozenset(
    {
        # GitHub's per-user no-reply host. The local part is a GitHub account id,
        # which is already public, and the address does not deliver mail.
        "users.noreply.github.com",
    }
)

# Whole addresses admitted by review, for the cases a host rule cannot classify
# -- typically a role mailbox on a real delivering domain. Each entry must carry
# a reason in this reviewed diff. Empty until one is genuinely needed.
ALLOWED_EMAILS: frozenset[str] = frozenset()


def _split_address(email: str) -> tuple[str, str] | None:
    """Return ``(local, host)`` for a structurally single, ordinary address.

    Returns ``None`` for anything this lint refuses to reason about: an address
    with no ``@`` or more than one, an empty side, or internal whitespace. Those
    are not classified as no-reply by default -- an address the lint cannot
    parse is an address it cannot clear.
    """
    candidate = email.strip().lower()
    if candidate.count("@") != 1:
        return None
    local, _, host = candidate.partition("@")
    if not local or not host:
        return None
    if any(character.isspace() for character in candidate):
        return None
    return local, host


def _is_allowed_address(email: str) -> bool:
    """Return whether *email* is on a reviewed host or is a reviewed address.

    Structural parsing runs before EITHER allowlist, deliberately. Consulting
    ``ALLOWED_EMAILS`` first would let a malformed entry -- one carrying two
    ``@`` signs or internal whitespace -- clear the very check that exists to
    refuse malformed addresses, reintroducing the round-1 defect through the
    escape hatch instead of through the rule.
    """
    parts = _split_address(email)
    if parts is None:
        return False
    local, host = parts
    if f"{local}@{host}" in ALLOWED_EMAILS:
        return True
    return host in ALLOWED_HOSTS


def find_violations(packs_dir: Path) -> list[str]:
    """Return one message per maintainer email outside the allowed forms.

    Missing maintainer data and malformed manifests are left to schema
    validation. This is only the address-class control, so duplicating those
    failures would make its output noisier without adding coverage.
    """
    violations: list[str] = []
    if not packs_dir.is_dir():
        return violations
    for pack_dir in sorted(packs_dir.iterdir()):
        manifest = pack_dir / "pack.toml"
        if not manifest.is_file():
            continue
        try:
            parsed = tomllib.loads(manifest.read_text(encoding="utf-8"))
        except (tomllib.TOMLDecodeError, OSError, UnicodeDecodeError):
            continue
        maintainers = parsed.get("pack", {}).get("maintainers")
        if not isinstance(maintainers, list):
            continue
        for maintainer in maintainers:
            if not isinstance(maintainer, dict):
                continue
            email = maintainer.get("email")
            if not isinstance(email, str):
                continue
            if _is_allowed_address(email):
                continue
            violations.append(
                f"lint-pack-maintainer-emails: {pack_dir.name}: "
                f"[[pack.maintainers]].email {email!r} is not on a reviewed "
                "host and is not a reviewed address. Publish from one of "
                f"{sorted(ALLOWED_HOSTS)}, or add the host to ALLOWED_HOSTS "
                "(or the exact address to ALLOWED_EMAILS) with its reason."
            )
    return violations


def main(argv: list[str] | None = None) -> int:
    """Run the policy lint and return its process exit status."""
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument(
        "--root", default=".", help="repository root to lint (default: .)"
    )
    args = parser.parse_args(argv)

    packs_dir = Path(args.root) / "packs"
    # Fail closed before reporting anything: see the module docstring. A pass
    # line printed over zero scanned manifests is the defect, not the absence.
    if not packs_dir.is_dir() or not any(packs_dir.glob("*/pack.toml")):
        print(
            f"lint-pack-maintainer-emails: no pack.toml found under {packs_dir} "
            "— scanned nothing, so this is not a pass. Check --root.",
            file=sys.stderr,
        )
        return 2

    violations = find_violations(packs_dir)
    for violation in violations:
        print(violation, file=sys.stderr)
    if violations:
        print(
            f"lint-pack-maintainer-emails: {len(violations)} maintainer email(s) "
            "outside the repository privacy policy.",
            file=sys.stderr,
        )
        return 1
    print(
        "lint-pack-maintainer-emails: every maintainer email is on a reviewed "
        "host or is a reviewed address."
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
