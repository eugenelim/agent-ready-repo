#!/usr/bin/env python3
"""Repo-policy lint: keep published pack maintainer addresses non-identifying.

``agentbundle`` copies ``[[pack.maintainers]].email`` into published
marketplace manifests. That makes a personal maintainer address in a source
``pack.toml`` a release-path privacy concern, rather than merely repository
metadata. This lint permits no-reply addresses, plus reviewed exceptions in
``ALLOWED_EMAILS``.

It deliberately does not try to decide whether an address is personal. That
judgment is undecidable from an email string: a role mailbox can look personal,
and a personal mailbox can look like a role. The explicit allowlist is the
reviewed human decision for the cases a mechanical rule cannot classify.

**Why this lives in ``tools/`` and not in the ``agentbundle`` package.** The
published package validates adopter catalogues; imposing this repository's
privacy policy there would turn it into an adopter build break. This lint runs
only over this repository's own ``packs/`` tree through ``make build-check``.

Pure-stdlib, ``--root`` flagged, exit 0=pass / 1=violation / **2=scanned
nothing**.

**Why exit 2 exists, and why this diverges from its sibling.**
``lint-pack-descriptions.py`` returns "clean" when ``packs/`` is absent, so a
wrong ``--root`` prints a pass line for a run that examined zero files. That is
survivable for a drift backstop on display copy. It is not survivable for a
privacy control on a release path: a run that gated nothing would read
identically to a run that gated everything, which is the failure this
repository has already been bitten by elsewhere (see ``[backlog].open``
``curation-guard-silent-base-skip``, a false green reproduced three times in
one session). So finding no ``pack.toml`` at all is an error here, not a pass.
``find_violations`` stays a pure function returning ``[]``; the fail-closed
decision lives in ``main``, where the operator's intent — "lint this root" — is
what went unmet.

Usage:
    python3 tools/lint-pack-maintainer-emails.py [--root .]
"""

from __future__ import annotations

import argparse
import sys
import tomllib
from pathlib import Path

# Each exception must carry a reason in this reviewed diff. Keeping this empty
# until one is needed prevents a role address from becoming an unexamined rule.
ALLOWED_EMAILS: frozenset[str] = frozenset()


def _is_no_reply_address(email: str) -> bool:
    """Return whether *email* uses one of the repository's no-reply forms."""
    local, separator, host = email.strip().lower().partition("@")
    if not separator or not host:
        return False
    if local in {"noreply", "no-reply"}:
        return True
    prefix, marker, domain = host.partition(".noreply.")
    return bool(prefix and marker and domain)


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
            normalised = email.strip().lower()
            if normalised in ALLOWED_EMAILS or _is_no_reply_address(normalised):
                continue
            violations.append(
                f"lint-pack-maintainer-emails: {pack_dir.name}: "
                f"[[pack.maintainers]].email {email!r} is neither a no-reply "
                "address nor an explicit reviewed allowlist entry. Use a "
                "noreply/no-reply local part or a *.noreply.<domain> host; for "
                "a role mailbox, add the exact address to ALLOWED_EMAILS with "
                "its reason."
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
        "lint-pack-maintainer-emails: all maintainer emails are no-reply or "
        "reviewed."
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
