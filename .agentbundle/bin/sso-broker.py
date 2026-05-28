"""SSO-cookie broker — credential-broker-contract T5.

Six verbs: register / get-cookies / test / refresh / list-profiles / rm.

Performs corporate-SSO cookie capture via headed Chromium (Playwright);
stores the serialised cookie jar in the OS keychain (macOS / Windows)
with continuation-credential chunking for jars > 2048 bytes; falls
back to a 0600 file under ``~/.agentbundle/sso-cookies/`` only on
Linux (the documented Tier-2 deferred path).

Reserved keychain target-name prefix: ``agentbundle:sso:<profile>``
and ``agentbundle:sso:<profile>:<n>`` for continuation slots.

This script lives at ``~/.agentbundle/bin/sso-broker.py`` and is
subprocess-invoked from `auth: sso-cookie` consumer skills.

Refs: docs/specs/credential-broker-contract/spec.md (AC9-AC17);
RFC-0013 § 4b.
"""

from __future__ import annotations

import argparse
import json
import os
import pathlib
import re
import sys
import time
import tomllib
import urllib.error
import urllib.request

# Bootstrap when invoked as ``python ~/.agentbundle/bin/sso-broker.py``
# so the ``from . import _sso_keychain_macos`` dispatch below resolves
# against the projected siblings in the same directory. Gated on
# ``__spec__ is None`` so the block only fires for true file-path
# invocation; an importlib-based test harness is responsible for its
# own package context. The shim companion (``credentials_shim.py``)
# is co-located by the AC22b projection rule, so the per-platform
# ``_sso_*`` modules' ``from .credentials_shim import Tier2HardFailError``
# resolves under user-scope install.
if __package__ in (None, "") and __spec__ is None:
    _here = pathlib.Path(__file__).resolve().parent
    sys.path.insert(0, str(_here.parent))
    __package__ = _here.name


# Per AC12 — chosen explicitly to leave headroom under the Win32
# CRED_MAX_CREDENTIAL_BLOB_SIZE lower-bound of 2560 bytes pre-Windows 7.
# macOS Keychain and Linux dotfile have higher capacity but the same
# threshold is applied uniformly for cross-platform determinism.
CRED_MAX_CREDENTIAL_BLOB_SIZE_BYTES = 2048

# Reserved keychain-target namespace for this broker (AC12 / RFC-0013 § 4b).
# Every write_credential / read_credential call site constructs target
# names of shape agentbundle:sso:<profile> (or :<n> for continuation).
_SSO_NAMESPACE = "agentbundle:sso"

# Per-platform Tier-2 backend dispatch — sibling files projected
# alongside this script via adapter-root-bins/. Filename rename only
# vs. agentbundle/creds/_keychain_macos.py and _credman_windows.py.
_tier2_backend = None
if sys.platform == "darwin":
    try:
        from . import _sso_keychain_macos as _tier2_backend  # type: ignore[no-redef]
    except ImportError:
        # Stand-alone invocation: this file lives next to its siblings
        # under ~/.agentbundle/bin/ — set sys.path and import absolutely.
        sys.path.insert(0, str(pathlib.Path(__file__).parent))
        try:
            import _sso_keychain_macos as _tier2_backend  # type: ignore[no-redef]
        except ImportError:
            _tier2_backend = None
elif sys.platform == "win32":
    try:
        from . import _sso_credman_windows as _tier2_backend  # type: ignore[no-redef]
    except ImportError:
        sys.path.insert(0, str(pathlib.Path(__file__).parent))
        try:
            import _sso_credman_windows as _tier2_backend  # type: ignore[no-redef]
        except ImportError:
            _tier2_backend = None


# Argv-borne credential flags refused per RFC-0006 § 4 / argv ban.
_ARGV_BAN = frozenset({
    "--token",
    "--api-token",
    "--api-key",
    "--bearer",
    "--pat",
    "--password",
})

_ARGV_REFUSAL_STDERR = "tokens cannot be passed via argv"

# Catalogue user-scope artifact root for this broker.
_AGENTBUNDLE_HOME = pathlib.Path.home() / ".agentbundle"
_SSO_PROFILE_DIR = _AGENTBUNDLE_HOME / "sso-profiles"
_SSO_COOKIE_FILE_FLOOR = _AGENTBUNDLE_HOME / "sso-cookies"


def _refuse_argv_ban(argv: list[str]) -> None:
    for arg in argv:
        head = arg.split("=", 1)[0]
        if head in _ARGV_BAN:
            sys.stderr.write(f"sso-broker: argv-refusal: {_ARGV_REFUSAL_STDERR}\n")
            sys.exit(3)


# ----------------------------------------------------------------------
# Tier-2 storage for cookie jars — write/read with continuation chunking.
# ----------------------------------------------------------------------


def _tier2_capable() -> bool:
    return _tier2_backend is not None


def _profile_target(profile: str, *, chunk: int | None = None) -> tuple[str, str]:
    """Return (namespace, key) suitable for Tier-2 backend dispatch.

    Tier-2 backends accept ``(namespace, key)`` and join with ``:``;
    we squat ``_SSO_NAMESPACE`` as the namespace and use ``profile``
    (or ``profile:<n>``) as the key. Net wire shape:
    ``agentbundle:sso:<profile>`` or ``agentbundle:sso:<profile>:<n>``.
    """
    if chunk is None:
        return _SSO_NAMESPACE, profile
    return _SSO_NAMESPACE, f"{profile}:{chunk}"


def write_credential(namespace: str, key: str, value: str) -> None:
    """Tier-2 write. Asserts target-name shape == agentbundle:sso:*."""
    if namespace != _SSO_NAMESPACE:
        raise RuntimeError(
            f"sso-broker: internal bug: write_credential called with "
            f"non-sso namespace {namespace!r}"
        )
    if not _tier2_capable():
        raise RuntimeError("sso-broker: no Tier-2 backend on this platform")
    _tier2_backend.write_credential(namespace, key, value)


def read_credential(namespace: str, key: str) -> str | None:
    """Tier-2 read. Asserts target-name shape == agentbundle:sso:*."""
    if namespace != _SSO_NAMESPACE:
        raise RuntimeError(
            f"sso-broker: internal bug: read_credential called with "
            f"non-sso namespace {namespace!r}"
        )
    if not _tier2_capable():
        return None
    return _tier2_backend.read_credential(namespace, key)


def _delete_credential(namespace: str, key: str) -> None:
    if _tier2_capable():
        try:
            _tier2_backend.delete_credential(namespace, key)
        except Exception:  # noqa: BLE001 — best-effort delete
            pass


def _store_cookie_jar(profile: str, serialized: bytes) -> str:
    """Write the serialised jar via Tier-2 (with continuation chunking
    when > CRED_MAX_CREDENTIAL_BLOB_SIZE_BYTES); fall back to a 0600
    file under ``~/.agentbundle/sso-cookies/`` when Tier-2 is
    deferred-by-policy (Linux) or refuses continuation.

    Returns one of: "keychain" / "keychain-continuation" /
    "file-floor" / "file-floor-overflow" — for stderr announcement.
    """
    threshold = CRED_MAX_CREDENTIAL_BLOB_SIZE_BYTES

    if not _tier2_capable():
        _file_floor_write(profile, serialized)
        return "file-floor"

    if len(serialized) <= threshold:
        try:
            ns, key = _profile_target(profile)
            write_credential(ns, key, serialized.decode("utf-8"))
            return "keychain"
        except Exception:  # noqa: BLE001 — backend refused; floor
            _file_floor_write(profile, serialized)
            return "file-floor-overflow"

    # Split into header + continuation slots.
    text = serialized.decode("utf-8")
    chunks = [text[i:i + threshold] for i in range(0, len(text), threshold)]
    try:
        ns, key = _profile_target(profile)
        # Header credential stores the count.
        write_credential(ns, key, json.dumps({"continuation_count": len(chunks)}))
        for n, chunk in enumerate(chunks):
            ns_n, key_n = _profile_target(profile, chunk=n)
            write_credential(ns_n, key_n, chunk)
        return "keychain-continuation"
    except Exception:  # noqa: BLE001 — backend refused continuation
        # Roll back any partial writes and floor to file.
        _delete_credential(*_profile_target(profile))
        for n in range(len(chunks)):
            _delete_credential(*_profile_target(profile, chunk=n))
        _file_floor_write(profile, serialized)
        return "file-floor-overflow"


def _load_cookie_jar(profile: str) -> bytes | None:
    """Read the serialised jar from Tier-2 (with continuation
    reassembly) or fall back to file-floor read. Returns ``None`` when
    no jar is present."""
    if _tier2_capable():
        ns, key = _profile_target(profile)
        header = read_credential(ns, key)
        if header is not None:
            # Distinguish continuation-header (JSON with count) from
            # a single-credential value (raw cookie-jar text).
            try:
                meta = json.loads(header)
            except json.JSONDecodeError:
                meta = None
            if isinstance(meta, dict) and "continuation_count" in meta:
                parts: list[str] = []
                for n in range(int(meta["continuation_count"])):
                    ns_n, key_n = _profile_target(profile, chunk=n)
                    part = read_credential(ns_n, key_n)
                    if part is None:
                        return None  # corrupted; treat as missing
                    parts.append(part)
                return "".join(parts).encode("utf-8")
            return header.encode("utf-8")

    # Fall through to file floor.
    floor_path = _cookie_floor_path(profile)
    if floor_path.exists():
        return floor_path.read_bytes()
    return None


def _delete_cookie_jar(profile: str) -> None:
    if _tier2_capable():
        # Best-effort: delete header + any continuation slots up to a
        # reasonable cap (the count is in the header but if reading
        # fails we still want to clean up).
        header = None
        try:
            ns, key = _profile_target(profile)
            header = read_credential(ns, key)
        except Exception:  # noqa: BLE001
            pass
        _delete_credential(*_profile_target(profile))
        if header is not None:
            try:
                meta = json.loads(header)
                if isinstance(meta, dict) and "continuation_count" in meta:
                    for n in range(int(meta["continuation_count"])):
                        _delete_credential(*_profile_target(profile, chunk=n))
            except json.JSONDecodeError:
                pass

    floor_path = _cookie_floor_path(profile)
    if floor_path.exists():
        floor_path.unlink()


def _cookie_floor_path(profile: str) -> pathlib.Path:
    return _SSO_COOKIE_FILE_FLOOR / f"{profile}.jar"


def _file_floor_write(profile: str, serialized: bytes) -> None:
    _SSO_COOKIE_FILE_FLOOR.mkdir(parents=True, exist_ok=True, mode=0o700)
    path = _cookie_floor_path(profile)
    tmp = path.with_suffix(path.suffix + ".tmp")
    tmp.write_bytes(serialized)
    if os.name == "posix":
        os.chmod(tmp, 0o600)
    os.replace(tmp, path)


# ----------------------------------------------------------------------
# Profile TOML I/O.
# ----------------------------------------------------------------------


def _profile_path(profile: str) -> pathlib.Path:
    return _SSO_PROFILE_DIR / f"{profile}.toml"


def _load_profile(profile: str) -> dict:
    path = _profile_path(profile)
    if not path.exists():
        raise FileNotFoundError(path)
    with path.open("rb") as fh:
        data = tomllib.load(fh)
    table = data.get("profile")
    if not isinstance(table, dict):
        raise ValueError(f"{path}: missing [profile] table")
    return table


def _write_profile(profile: str, table: dict) -> None:
    _SSO_PROFILE_DIR.mkdir(parents=True, exist_ok=True, mode=0o700)
    path = _profile_path(profile)
    lines = ["[profile]"]
    for key, value in table.items():
        if isinstance(value, str):
            lines.append(f'{key} = "{value}"')
        elif isinstance(value, int):
            lines.append(f"{key} = {value}")
        elif isinstance(value, list):
            items = ", ".join(f'"{v}"' for v in value)
            lines.append(f"{key} = [{items}]")
    tmp = path.with_suffix(path.suffix + ".tmp")
    tmp.write_text("\n".join(lines) + "\n", encoding="utf-8")
    if os.name == "posix":
        os.chmod(tmp, 0o600)
    os.replace(tmp, path)


# ----------------------------------------------------------------------
# Playwright import-guard.
# ----------------------------------------------------------------------


_PLAYWRIGHT_INSTALL_INSTRUCTION = (
    "sso-broker: playwright not installed. "
    "Run: pip install playwright && playwright install chromium\n"
)


def _import_playwright():
    try:
        from playwright.sync_api import sync_playwright  # type: ignore[import-not-found]
    except ImportError:
        sys.stderr.write(_PLAYWRIGHT_INSTALL_INSTRUCTION)
        sys.exit(3)
    return sync_playwright


# ----------------------------------------------------------------------
# Verb: register.
# ----------------------------------------------------------------------


def _do_register(profile: str, args: argparse.Namespace) -> int:
    """Open a headed browser at ``login_url``, capture cookies for
    declared domains on landing at ``success_url_pattern``, persist the
    profile TOML and the cookie jar.

    Required args: ``--login-url``, ``--success-url-pattern``.
    Optional: ``--cookie-domain`` (repeatable), ``--session-filename``,
    ``--validation-endpoint``, ``--ttl-hint-minutes``.
    """
    login_url: str = args.login_url
    success_pattern: str = args.success_url_pattern
    cookie_domains: list[str] = list(args.cookie_domain or [])
    session_filename: str = args.session_filename or f"{profile}-session.jar"
    validation_endpoint: str = args.validation_endpoint or ""
    ttl_hint_minutes: int = int(args.ttl_hint_minutes or 480)

    if not login_url or not success_pattern:
        sys.stderr.write(
            "sso-broker register: --login-url and --success-url-pattern are required\n"
        )
        return 3

    sync_playwright = _import_playwright()

    user_data_dir = _AGENTBUNDLE_HOME / "browser-state" / profile
    user_data_dir.mkdir(parents=True, exist_ok=True)

    captured_cookies: list[dict] = []
    success = False
    success_re = re.compile(success_pattern)

    # Corporate-network env passthrough — explicit per AC14.
    env_for_browser = {**os.environ}

    with sync_playwright() as pw:
        context = pw.chromium.launch_persistent_context(
            user_data_dir=str(user_data_dir),
            headless=False,
            env=env_for_browser,
        )
        page = context.pages[0] if context.pages else context.new_page()
        page.goto(login_url)

        # Wait for the URL pattern to land. Poll for up to 5 minutes.
        deadline = time.time() + 300
        while time.time() < deadline:
            if success_re.search(page.url):
                success = True
                break
            page.wait_for_timeout(500)

        if success:
            captured_cookies = context.cookies()
        context.close()

    if not success:
        sys.stderr.write(
            f"sso-broker register: success URL pattern {success_pattern!r} "
            f"not matched within timeout; cookies not captured\n"
        )
        return 3

    # If cookie_domains was not provided, derive from observed cookies.
    if not cookie_domains:
        cookie_domains = sorted({c["domain"].lstrip(".") for c in captured_cookies})

    # Persist profile TOML.
    _write_profile(profile, {
        "name": profile,
        "login_url": login_url,
        "success_url_pattern": success_pattern,
        "cookie_domains": cookie_domains,
        "session_filename": session_filename,
        "validation_endpoint": validation_endpoint,
        "ttl_hint_minutes": ttl_hint_minutes,
    })

    # Persist cookie jar.
    serialized = json.dumps(captured_cookies, separators=(",", ":")).encode("utf-8")
    storage_label = _store_cookie_jar(profile, serialized)
    sys.stderr.write(
        f"sso-broker register: profile {profile!r} registered "
        f"({len(captured_cookies)} cookies, stored via {storage_label})\n"
    )
    return 0


# ----------------------------------------------------------------------
# Verb: get-cookies.
# ----------------------------------------------------------------------


def _do_get_cookies(profile: str) -> int:
    """Print the path to the on-disk cookie jar. Exit 2 if no jar is
    stored (caller must re-register). Exit 0 if jar resolves."""
    try:
        _load_profile(profile)
    except FileNotFoundError:
        sys.stderr.write(
            f"sso-broker get-cookies: profile {profile!r} not registered; "
            f"run 'sso-broker register {profile} ...'\n"
        )
        return 2

    jar = _load_cookie_jar(profile)
    if jar is None:
        sys.stderr.write(
            f"sso-broker get-cookies: no cookie jar for profile {profile!r}; "
            f"re-auth required (run 'sso-broker register {profile} ...')\n"
        )
        return 2

    # Materialise the jar to a 0600 file under sso-cookies/ and print
    # its path. Consumer skills read the file and never see cookie
    # values via argv / stdout.
    materialised = _cookie_floor_path(profile)
    if not materialised.exists():
        _file_floor_write(profile, jar)
    sys.stdout.write(f"{materialised}\n")
    return 0


# ----------------------------------------------------------------------
# Verb: test.
# ----------------------------------------------------------------------


def _do_test(profile: str) -> int:
    """Make a request to the profile's ``validation_endpoint``;
    exit 0 on 2xx, exit 2 on 401, exit 3 on other failures."""
    try:
        table = _load_profile(profile)
    except FileNotFoundError:
        sys.stderr.write(
            f"sso-broker test: profile {profile!r} not registered\n"
        )
        return 2

    base = table.get("login_url", "")
    endpoint = table.get("validation_endpoint", "")
    if not endpoint:
        sys.stderr.write(
            f"sso-broker test: profile {profile!r} has no validation_endpoint\n"
        )
        return 3

    jar = _load_cookie_jar(profile)
    if jar is None:
        sys.stderr.write(
            f"sso-broker test: no cookie jar for profile {profile!r}\n"
        )
        return 2

    # Construct a Cookie header from the jar.
    try:
        cookies = json.loads(jar.decode("utf-8"))
    except json.JSONDecodeError:
        sys.stderr.write(f"sso-broker test: cookie jar for {profile!r} is corrupt\n")
        return 3
    cookie_header = "; ".join(f"{c['name']}={c['value']}" for c in cookies)

    url = base.rstrip("/") + endpoint
    req = urllib.request.Request(url, headers={"Cookie": cookie_header})
    try:
        # Corporate-network env passthrough is the parent's responsibility;
        # urllib honours HTTPS_PROXY / NO_PROXY / SSL_CERT_FILE / SSL_CERT_DIR
        # from the environment automatically.
        with urllib.request.urlopen(req, timeout=15) as resp:
            status = resp.status
    except urllib.error.HTTPError as exc:
        status = exc.code
    except urllib.error.URLError as exc:
        sys.stderr.write(f"sso-broker test: URL error: {exc}\n")
        return 3

    if 200 <= status < 300:
        return 0
    if status == 401:
        sys.stderr.write(
            f"sso-broker test: 401 from {url}; session expired — "
            f"run 'sso-broker register {profile} ...' to re-auth\n"
        )
        return 2
    sys.stderr.write(f"sso-broker test: unexpected status {status} from {url}\n")
    return 3


# ----------------------------------------------------------------------
# Verb: refresh.
# ----------------------------------------------------------------------


def _do_refresh(profile: str, args: argparse.Namespace) -> int:
    """Equivalent to ``register`` but bypasses any 'already registered' check.

    The current implementation of ``register`` is idempotent — every call
    overwrites the profile TOML and the cookie jar — so ``refresh``
    delegates straight through.
    """
    try:
        table = _load_profile(profile)
    except FileNotFoundError:
        sys.stderr.write(
            f"sso-broker refresh: profile {profile!r} not registered; "
            f"run 'register' first\n"
        )
        return 3

    # Re-use any saved knobs if the caller didn't override them on the CLI.
    if not args.login_url:
        args.login_url = table.get("login_url", "")
    if not args.success_url_pattern:
        args.success_url_pattern = table.get("success_url_pattern", "")
    if not args.session_filename:
        args.session_filename = table.get("session_filename", "")
    if not args.validation_endpoint:
        args.validation_endpoint = table.get("validation_endpoint", "")
    if not args.ttl_hint_minutes:
        args.ttl_hint_minutes = table.get("ttl_hint_minutes", 480)
    if not args.cookie_domain:
        args.cookie_domain = list(table.get("cookie_domains") or [])

    return _do_register(profile, args)


# ----------------------------------------------------------------------
# Verb: list-profiles.
# ----------------------------------------------------------------------


def _do_list_profiles() -> int:
    if not _SSO_PROFILE_DIR.is_dir():
        sys.stderr.write("sso-broker: no profiles registered\n")
        return 0
    profiles = sorted(p.stem for p in _SSO_PROFILE_DIR.glob("*.toml"))
    if not profiles:
        sys.stderr.write("sso-broker: no profiles registered\n")
        return 0
    for name in profiles:
        has_jar = _load_cookie_jar(name) is not None
        sys.stdout.write(f"{name}\t{'valid' if has_jar else 'no-jar'}\n")
    return 0


# ----------------------------------------------------------------------
# Verb: rm.
# ----------------------------------------------------------------------


def _do_show_tier2_backend() -> int:
    """Print ``repr(_tier2_backend)`` and exit 0.

    Test surface for the AC22b shim-companion projection regression
    (`packages/agentbundle/tests/integration/test_credential_user_scope_invocation.py`):
    invoking ``python bin/sso-broker.py show-tier2-backend`` under the
    documented user-scope layout asserts the Tier-2 backend module
    loaded successfully — `_sso_keychain_macos` on darwin /
    `_sso_credman_windows` on win32 / `None` on linux.

    Does not touch the Tier-2 store, the cookie jar, the file floor,
    profile TOMLs, or any credential bytes — purely an introspection
    echo of the module-load result that already happened at import
    time.
    """
    sys.stdout.write(f"{_tier2_backend!r}\n")
    return 0


def _do_rm(profile: str) -> int:
    path = _profile_path(profile)
    if not path.exists():
        sys.stderr.write(
            f"sso-broker rm: profile {profile!r} not registered\n"
        )
        return 0
    _delete_cookie_jar(profile)
    path.unlink()
    sys.stderr.write(f"sso-broker rm: profile {profile!r} removed\n")
    return 0


# ----------------------------------------------------------------------
# Argparse + main.
# ----------------------------------------------------------------------


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="sso-broker", description="SSO-cookie broker.")
    sub = parser.add_subparsers(dest="verb", required=True)

    p_register = sub.add_parser("register", help="Interactively capture cookies.")
    p_register.add_argument("profile")
    p_register.add_argument("--login-url", default="")
    p_register.add_argument("--success-url-pattern", default="")
    p_register.add_argument(
        "--cookie-domain", action="append", default=None,
        help="Repeatable; if omitted, derived from observed cookies.",
    )
    p_register.add_argument("--session-filename", default="")
    p_register.add_argument("--validation-endpoint", default="")
    p_register.add_argument("--ttl-hint-minutes", type=int, default=0)

    p_get = sub.add_parser("get-cookies", help="Print cookie-jar path.")
    p_get.add_argument("profile")

    p_test = sub.add_parser("test", help="Validate session against the endpoint.")
    p_test.add_argument("profile")

    p_refresh = sub.add_parser("refresh", help="Re-register without checks.")
    p_refresh.add_argument("profile")
    p_refresh.add_argument("--login-url", default="")
    p_refresh.add_argument("--success-url-pattern", default="")
    p_refresh.add_argument("--cookie-domain", action="append", default=None)
    p_refresh.add_argument("--session-filename", default="")
    p_refresh.add_argument("--validation-endpoint", default="")
    p_refresh.add_argument("--ttl-hint-minutes", type=int, default=0)

    sub.add_parser("list-profiles", help="List registered profiles.")

    p_rm = sub.add_parser("rm", help="Remove a profile + its cookie jar.")
    p_rm.add_argument("profile")

    sub.add_parser(
        "show-tier2-backend",
        help="Print repr(_tier2_backend) (AC22b shim-companion probe).",
    )

    return parser


def main(argv: list[str] | None = None) -> int:
    raw = list(sys.argv[1:]) if argv is None else list(argv)
    _refuse_argv_ban(raw)
    parser = _build_parser()
    args = parser.parse_args(raw)

    verb = args.verb
    if verb == "register":
        return _do_register(args.profile, args)
    if verb == "get-cookies":
        return _do_get_cookies(args.profile)
    if verb == "test":
        return _do_test(args.profile)
    if verb == "refresh":
        return _do_refresh(args.profile, args)
    if verb == "list-profiles":
        return _do_list_profiles()
    if verb == "rm":
        return _do_rm(args.profile)
    if verb == "show-tier2-backend":
        return _do_show_tier2_backend()
    raise AssertionError(f"unreachable verb: {verb}")  # pragma: no cover


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
