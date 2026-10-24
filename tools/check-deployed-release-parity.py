#!/usr/bin/env python3
"""Check 3, rendered half: the built site must match the DEPLOYED release index.

RFC-0109 D7 check 3. The anchor is the body fetched from the live site, which
lives outside this repository: a change that rewrites a released member and its
in-checkout record together cannot also rewrite what is already deployed. For
every release the fetched index lists, each released path must exist in the
built site with bytes whose SHA-256 equals the digest THAT FETCHED ENTRY
carries. No in-checkout manifest row and no file under the build directory is
ever read as the anchor.

The fetch is hardened: a literal https URL, redirects refused, a 30-second
timeout, a read bounded at 1 MiB, an opener without the environment-reading
``ProxyHandler`` (``build_opener`` installs one that honours ``https_proxy``),
and an explicitly built TLS context whose trust anchor is taken from neither
``SSL_CERT_FILE`` nor ``SSL_CERT_DIR``. Only a 200 that parses as JSON and
carries a ``releases`` array is an index; an empty array admits the first
deploy and any retry of it.

The check skips only on a ``workflow_dispatch`` whose ref is not ``main``: that
build cannot deploy. It runs on every other event, including an unknown one.
Pure stdlib (tools/AGENTS.md).
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import ssl
import sys
import urllib.error
import urllib.request
from pathlib import Path

INDEX_URL = "https://eugenelim.github.io/agent-ready-repo/docs/spec/catalogue/index.json"
FETCH_TIMEOUT_SECONDS = 30
MAX_BODY_BYTES = 1024 * 1024  # 1 MiB
# Where the built site carries a release: <build>/docs/spec/catalogue/<version>/<member>.
SITE_SUBDIR = Path("docs") / "spec" / "catalogue"
# Used only when this Python's compiled-in default CA file is absent. Fixed
# paths, never read from the environment.
_FALLBACK_CA_FILES = (
    "/etc/ssl/certs/ca-certificates.crt",
    "/etc/pki/tls/certs/ca-bundle.crt",
    "/etc/ssl/cert.pem",
)
_SEGMENT = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._-]*$")
_DIGEST = re.compile(r"^[a-f0-9]{64}$")


class ParityError(Exception):
    """The deployed anchor could not be read, or the build disagrees with it."""


class _NoRedirect(urllib.request.HTTPRedirectHandler):
    """Refuse every redirect: the anchor must come from the one literal host."""

    def redirect_request(self, req, fp, code, msg, headers, newurl):  # noqa: D102
        raise ParityError(f"refusing a {code} redirect to {newurl!r}")


def build_context() -> ssl.SSLContext:
    """A verifying TLS context whose trust anchor ignores SSL_CERT_FILE/DIR.

    ``ssl.create_default_context`` calls ``set_default_verify_paths``, which
    OpenSSL resolves through those variables. This context instead loads the
    compiled-in default locations (``openssl_cafile``/``openssl_capath``, which
    are not environment-derived) or a fixed fallback file.
    """
    ctx = ssl.SSLContext(ssl.PROTOCOL_TLS_CLIENT)
    ctx.verify_mode = ssl.CERT_REQUIRED
    ctx.check_hostname = True
    ctx.minimum_version = ssl.TLSVersion.TLSv1_2
    paths = ssl.get_default_verify_paths()
    cafile = paths.openssl_cafile if Path(paths.openssl_cafile or "-").is_file() else None
    capath = paths.openssl_capath if Path(paths.openssl_capath or "-").is_dir() else None
    if cafile is None and capath is None:
        cafile = next((p for p in _FALLBACK_CA_FILES if Path(p).is_file()), None)
    if cafile is not None or capath is not None:
        ctx.load_verify_locations(cafile=cafile, capath=capath)
    return ctx


def build_opener(context: ssl.SSLContext | None = None) -> urllib.request.OpenerDirector:
    """An opener with no ProxyHandler, redirects refused, the given TLS context."""
    opener = urllib.request.OpenerDirector()
    for handler in (
        urllib.request.UnknownHandler(),
        urllib.request.HTTPHandler(),
        urllib.request.HTTPSHandler(context=context if context is not None else build_context()),
        urllib.request.HTTPDefaultErrorHandler(),
        urllib.request.HTTPErrorProcessor(),
        _NoRedirect(),
    ):
        opener.add_handler(handler)
    return opener


def fetch_releases(url: str, opener: urllib.request.OpenerDirector) -> list[object]:
    """Return the ``releases`` array of the index at ``url``, or raise ParityError."""
    try:
        with opener.open(url, timeout=FETCH_TIMEOUT_SECONDS) as response:  # nosec B310
            if response.status != 200:
                raise ParityError(f"deployed index answered HTTP {response.status}, not 200")
            body = response.read(MAX_BODY_BYTES + 1)
    except urllib.error.HTTPError as exc:
        raise ParityError(f"deployed index fetch failed: HTTP {exc.code}") from None
    except (urllib.error.URLError, OSError, ValueError) as exc:
        raise ParityError(f"deployed index unreachable: {exc}") from None
    if len(body) > MAX_BODY_BYTES:
        raise ParityError(f"deployed index exceeds the {MAX_BODY_BYTES}-byte ceiling")
    try:
        parsed = json.loads(body)
    except ValueError:
        raise ParityError("deployed index body is not valid JSON") from None
    if not isinstance(parsed, dict) or "releases" not in parsed:
        raise ParityError("deployed index carries no `releases` key")
    releases = parsed["releases"]
    if not isinstance(releases, list):
        raise ParityError("deployed index `releases` is not an array")
    return releases


def compare(releases: list[object], build_dir: Path) -> list[str]:
    """Problems found comparing the build to the fetched releases (empty = match)."""
    problems: list[str] = []
    site = build_dir / SITE_SUBDIR
    for entry in releases:
        if not isinstance(entry, dict):
            problems.append("a fetched release entry is not an object")
            continue
        version, members = entry.get("version"), entry.get("members")
        if not isinstance(version, str) or not _SEGMENT.match(version) or ".." in version:
            problems.append(f"a fetched release has an unusable version {version!r}")
            continue
        if not isinstance(members, dict):
            problems.append(f"release {version}: fetched `members` is not an object")
            continue
        for name, digest in members.items():
            if not _SEGMENT.match(name) or ".." in name:
                problems.append(f"release {version}: unusable member name {name!r}")
                continue
            if not isinstance(digest, str) or not _DIGEST.match(digest):
                problems.append(f"release {version}: {name}: fetched digest is not a SHA-256")
                continue
            path = site / version / name
            if path.is_symlink() or not path.is_file():
                problems.append(f"release {version}: {name} is missing from the build")
            elif hashlib.sha256(path.read_bytes()).hexdigest() != digest:
                problems.append(f"release {version}: {name} bytes differ from the deployed digest")
    return problems


def should_skip(event_name: str, ref: str) -> bool:
    """Skip only a manual dispatch from a ref other than main (it cannot deploy)."""
    return event_name == "workflow_dispatch" and ref not in ("main", "refs/heads/main")


def run(build_dir: Path, event_name: str, ref: str, url: str = INDEX_URL,
        opener: urllib.request.OpenerDirector | None = None) -> int:
    """Fetch the anchor and compare; return the process exit status."""
    if should_skip(event_name, ref):
        print(f"check-deployed-release-parity: SKIPPED ({event_name} on {ref}: "
              "this build cannot deploy)")
        return 0
    try:
        releases = fetch_releases(url, opener if opener is not None else build_opener())
    except ParityError as exc:
        print(f"check-deployed-release-parity: FAIL: {exc}", file=sys.stderr)
        return 1
    problems = compare(releases, build_dir)
    if problems:
        print(f"check-deployed-release-parity: FAIL: {len(problems)} problem(s)",
              file=sys.stderr)
        for problem in problems:
            print(f"  - {problem}", file=sys.stderr)
        return 1
    print(f"check-deployed-release-parity: OK ({len(releases)} deployed "
          "release(s) match the build)")
    return 0


def main(argv: list[str]) -> int:
    """CLI entry point. The URL is not an argument or an environment input."""
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--build-dir", type=Path, required=True)
    args = parser.parse_args(argv)
    return run(args.build_dir, os.environ.get("GITHUB_EVENT_NAME", ""),
               os.environ.get("GITHUB_REF", ""))


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
