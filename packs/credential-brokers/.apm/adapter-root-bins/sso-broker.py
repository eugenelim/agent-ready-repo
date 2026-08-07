"""SSO-cookie broker.

Six verbs: register / get-cookies / test / refresh / list-profiles / rm.

Performs corporate-SSO cookie capture via Chromium (Playwright) — ``register``
drives a **headed** browser for interactive first capture, ``refresh`` a
**headless** one with a bounded silent-completion window that returns exit 5
rather than putting a login page in front of an operator; stores the
serialised cookie jar in the OS keychain (macOS / Windows) with
continuation-credential chunking for jars > 2048 bytes; falls
back to a 0600 file under ``~/.agentbundle/sso-cookies/`` only on
Linux (the documented Tier-2 deferred path).

Exit codes: 0 ok · 2 no usable session (``get-cookies`` / ``test``) ·
3 engine failure · 4 profile not registered (``refresh``) ·
5 headless refresh needs a human (``refresh``).

Reserved keychain target-name prefix: ``agentbundle:sso:<profile>``
and ``agentbundle:sso:<profile>:<n>`` for continuation slots.

This script lives at ``~/.agentbundle/bin/sso-broker.py`` and is
subprocess-invoked from `auth: sso-cookie` consumer skills.
"""

from __future__ import annotations

import argparse
import contextlib
import json
import os
import pathlib
import re
import secrets
import sys
import time
import tomllib
import urllib.error
import urllib.parse
import urllib.request

# Bootstrap when invoked as ``python ~/.agentbundle/bin/sso-broker.py``
# so the ``from . import _sso_keychain_macos`` dispatch below resolves
# against the projected siblings in the same directory. Gated on
# ``__spec__ is None`` so the block only fires for true file-path
# invocation; an importlib-based test harness is responsible for its
# own package context. The shim companion (``credentials_shim.py``)
# is co-located by the shim-companion projection rule, so the per-platform
# ``_sso_*`` modules' ``from .credentials_shim import Tier2HardFailError``
# resolves under user-scope install.
if __package__ in (None, "") and __spec__ is None:
    # Windows console hardening: stdout defaults to errors="strict" — a
    # non-ASCII write (em-dash messages, cookie-jar data) raises
    # UnicodeEncodeError on a legacy cp1252 console. Reconfigure both streams
    # before any output, including the platform-backend import below. Guarded:
    # a StringIO test-harness replacement or pythonw's None has no reconfigure().
    for _stream in (sys.stdout, sys.stderr):
        with contextlib.suppress(AttributeError, ValueError):
            _stream.reconfigure(encoding="utf-8")
    _here = pathlib.Path(__file__).resolve().parent
    sys.path.insert(0, str(_here.parent))
    __package__ = _here.name


# Chosen explicitly to leave headroom under the Win32
# CRED_MAX_CREDENTIAL_BLOB_SIZE lower-bound of 2560 bytes pre-Windows 7.
# macOS Keychain and Linux dotfile have higher capacity but the same
# threshold is applied uniformly for cross-platform determinism.
CRED_MAX_CREDENTIAL_BLOB_SIZE_BYTES = 2048

# Reserved keychain-target namespace for this broker.
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


# Argv-borne credential flags refused per the argv ban.
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


# ----------------------------------------------------------------------
# Profile grammar + path containment.
#
# Two independent controls, and the split is the point. The grammar is a
# denylist of *shapes*; containment is an allowlist of *locations*. Neither
# subsumes the other, so both run.
#
# This grammar is a deliberate duplicate of ``credbroker.validate_sso_profile``.
# The engine cannot import ``credbroker`` — the dependency runs the other way,
# ``credbroker`` subprocesses this file — so the two copies are pinned equal by
# ``test_sso_recapture.py``'s parity test instead. Change one, change the other.
# ----------------------------------------------------------------------

_SSO_PROFILE_PATTERN = r"^[A-Za-z0-9][A-Za-z0-9._-]{0,63}$"

# Case-insensitive Win32 reserved device names. On Windows ``CON.toml`` resolves
# to the console device regardless of the directory it is written to, so the
# check is applied to the name's first dot-separated component rather than to the
# whole string.
_RESERVED_DEVICE_NAMES = frozenset({
    "CON", "PRN", "AUX", "NUL",
    "COM1", "COM2", "COM3", "COM4", "COM5", "COM6", "COM7", "COM8", "COM9",
    "LPT1", "LPT2", "LPT3", "LPT4", "LPT5", "LPT6", "LPT7", "LPT8", "LPT9",
})

_PROFILE_RE = re.compile(_SSO_PROFILE_PATTERN)


class ProfileConfinementError(Exception):
    """A composed store path escaped its store directory, or ``profile`` was
    not a string. Raised by the path composers so no verb — including the
    grammar-exempt ``rm`` — can reach outside the store."""


def _profile_grammar_error(profile: str) -> str | None:
    """Return a stderr-ready reason *profile* is unsafe, or ``None``."""
    if not isinstance(profile, str):
        return f"profile must be a string, got {type(profile).__name__}"
    if not _PROFILE_RE.fullmatch(profile):
        # fullmatch, not match: the pattern's `$` matches before a trailing
        # newline, so `match` would admit "jira\n".
        return (
            f"profile {profile!r} must match {_SSO_PROFILE_PATTERN} "
            f"(1-64 chars, leading alphanumeric, then alphanumerics, '.', '_', '-')"
        )
    if profile.split(".", 1)[0].upper() in _RESERVED_DEVICE_NAMES:
        return f"profile {profile!r} is a Windows reserved device name"
    return None


def _contained(path: pathlib.Path, parent: pathlib.Path) -> pathlib.Path:
    """Return *path* iff its resolved parent is exactly *parent*.

    Canonicalize-then-verify-parent (the CWE-73 depth), applied independently of
    the grammar so ``rm`` — which is grammar-exempt by AC8, or a legacy profile
    would be undeletable — still cannot reach outside the store. Compared
    case-insensitively on Windows, where the filesystem is.
    """
    resolved_parent = os.path.normcase(str(path.resolve().parent))
    expected = os.path.normcase(str(parent.resolve()))
    if resolved_parent != expected:
        raise ProfileConfinementError(
            f"refusing a store path outside {parent}: resolved to {path.resolve()}"
        )
    return path


def _profile_component(profile: object) -> str:
    """The single path component *profile* contributes, or raise.

    A non-``str`` is refused here rather than f-string-coerced: an ``int`` 5
    would otherwise compose ``5.jar`` and pass containment.
    """
    if not isinstance(profile, str):
        raise ProfileConfinementError(
            f"profile must be a string, got {type(profile).__name__}"
        )
    return profile


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
        with contextlib.suppress(Exception):  # noqa: BLE001 — best-effort delete
            _tier2_backend.delete_credential(namespace, key)


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
    return _contained(
        _SSO_COOKIE_FILE_FLOOR / f"{_profile_component(profile)}.jar",
        _SSO_COOKIE_FILE_FLOOR,
    )


def _browser_state_dir(profile: str) -> pathlib.Path:
    """The persistent Chromium user-data dir for *profile*.

    Guarded like the other two store paths: this one is interpolated straight
    into a directory Chromium then writes a standing, silently-replayable
    corporate session into.
    """
    root = _AGENTBUNDLE_HOME / "browser-state"
    return _contained(root / _profile_component(profile), root)


def _file_floor_write(profile: str, serialized: bytes) -> None:
    """Atomically write the jar to the file floor via a **unique** temp name.

    The temp name carries the pid and a random suffix rather than a shared
    ``<profile>.jar.tmp``. ``get-cookies`` re-materialises unconditionally now
    (see ``_do_get_cookies``), so this fires on every consumer call rather than
    at most once per profile, and two concurrent calls for one profile would
    otherwise collide on the same temp path. Ordering between concurrent
    materialisers is deliberately *not* specified here — that is a concurrency
    protocol with its own design, tracked as ``sso-materialisation-ordering``.
    """
    _SSO_COOKIE_FILE_FLOOR.mkdir(parents=True, exist_ok=True, mode=0o700)
    if os.name == "posix":
        # `mkdir(mode=...)` does not repair an existing directory, and this now
        # runs on every consumer call rather than once per profile.
        with contextlib.suppress(OSError):
            _SSO_COOKIE_FILE_FLOOR.chmod(0o700)
    path = _cookie_floor_path(profile)
    tmp = path.with_name(f"{path.name}.{os.getpid()}.{secrets.token_hex(4)}.tmp")
    try:
        # Created *with* the mode, not chmod'd afterwards: `write_bytes` would
        # create at the umask default, leaving the cookie jar world-readable for
        # the length of the write — a window that used to open once per profile
        # and now opens on every `get-cookies`.
        flags = os.O_WRONLY | os.O_CREAT | os.O_EXCL
        fd = os.open(tmp, flags, 0o600)
        try:
            os.write(fd, serialized)
        finally:
            os.close(fd)
        tmp.replace(path)
    except OSError:
        # Never leave a partial temp behind for the next glob to trip over.
        with contextlib.suppress(OSError):
            tmp.unlink()
        raise


# ----------------------------------------------------------------------
# Profile TOML I/O.
# ----------------------------------------------------------------------


def _profile_path(profile: str) -> pathlib.Path:
    return _contained(
        _SSO_PROFILE_DIR / f"{_profile_component(profile)}.toml",
        _SSO_PROFILE_DIR,
    )


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


# Characters a TOML basic string cannot carry literally: the quote, the
# backslash, and the whole C0 control range plus DEL. A four-character
# quote/backslash/CR/LF check is not enough — TOML input can encode U+0001 as an
# escape, so after parsing the value holds a bare control character with no
# literal backslash to notice.
_TOML_SHORTHAND_ESCAPES = {
    "\\": "\\\\", '"': '\\"',
    "\b": "\\b", "\t": "\\t", "\n": "\\n", "\f": "\\f", "\r": "\\r",
}


def _toml_basic_string(value: str) -> str:
    """Render *value* as a quoted TOML basic string, escaped.

    Escaping rather than rejecting, deliberately: ``_do_refresh`` reads the
    stored table and re-writes every value back through this function, so a
    profile poisoned before this change would otherwise be re-injected on every
    automatic refresh — or, if we rejected, become permanently unrefreshable.
    Escaping keeps the store parseable, which is the invariant that matters: an
    unparseable profile breaks every later check, refresh and rm.
    """
    out = []
    for ch in value:
        if ch in _TOML_SHORTHAND_ESCAPES:
            out.append(_TOML_SHORTHAND_ESCAPES[ch])
        elif ch < "\x20" or ch == "\x7f":
            out.append(f"\\u{ord(ch):04X}")
        else:
            out.append(ch)
    return '"' + "".join(out) + '"'


def _write_profile(profile: str, table: dict) -> None:
    _SSO_PROFILE_DIR.mkdir(parents=True, exist_ok=True, mode=0o700)
    path = _profile_path(profile)
    lines = ["[profile]"]
    for key, value in table.items():
        if isinstance(value, str):
            lines.append(f"{key} = {_toml_basic_string(value)}")
        elif isinstance(value, int):
            lines.append(f"{key} = {value}")
        elif isinstance(value, list):
            items = ", ".join(_toml_basic_string(v) for v in value)
            lines.append(f"{key} = [{items}]")
    tmp = path.with_suffix(path.suffix + ".tmp")
    tmp.write_text("\n".join(lines) + "\n", encoding="utf-8")
    if os.name == "posix":
        tmp.chmod(0o600)
    tmp.replace(path)


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


# How long the capture waits for the success URL, by headedness.
#
# Headed means a human is at the keyboard, so the wait is a human-duration
# sign-in poll. Headless means nobody is: the wait is only long enough for a
# warm IdP session's redirect chain to land unaided, and far short of anything a
# person could type into. The two are not interchangeable, which is why
# ``refresh`` is headless *and* short rather than one or the other.
_REGISTER_SIGNIN_POLL_S: float = 300
_REFRESH_SILENT_WINDOW_S: float = 20


def _capture(
    profile: str,
    args: argparse.Namespace,
    *,
    persist: bool,
    headless: bool,
) -> int:
    """Drive a browser to ``success_url_pattern`` and store what it captured.

    Two independent axes, because persistence and headedness vary
    independently:

    * *persist* — capture in the standing ``browser-state/<profile>`` profile
      (the operator's own ``register``, and every ``refresh``), or in a throwaway
      context that is then used to **seed** the standing one
      (``register --ephemeral``, which is what the library API drives).
    * *headless* — a human may complete the flow (``register``), or the browser
      profile must complete it unaided or not at all (``refresh``).

    :returns: ``0`` captured; ``3`` missing arguments, or a headed sign-in that
        was not completed; ``5`` a headless attempt that could not complete
        without a human — the caller's cue to ask for a re-register rather than
        to retry.
    """
    login_url: str = args.login_url
    success_pattern: str = args.success_url_pattern
    cookie_domains: list[str] = list(args.cookie_domain or [])
    session_filename: str = args.session_filename or f"{profile}-session.jar"
    validation_endpoint: str = args.validation_endpoint or ""
    ttl_hint_minutes: int = int(args.ttl_hint_minutes or 480)

    # AC35's matrix has exactly three legal rows. `persist=False, headless=True`
    # would run an ephemeral *headless* capture and then seed a standing profile
    # from a session no human established — refused by construction rather than
    # left unreachable-by-convention. (Collapsing the pair into a named mode is
    # the better shape and is deferred: `sso-capture-mode-enum`.)
    if not persist and headless:
        raise AssertionError(
            "internal bug: an ephemeral capture is never headless — no human "
            "could have established the session it would seed"
        )

    # Names the verb the operator actually ran: `refresh` reaches here too, via
    # the stored profile, and a message telling them to pass `--login-url` to
    # `register` when they typed `refresh` sends them the wrong way.
    verb = "refresh" if headless else "register"

    if not login_url or not success_pattern:
        sys.stderr.write(
            f"sso-broker {verb}: login-url and success-url-pattern are required "
            f"(refresh reads them from the stored profile)\n"
        )
        return 3

    captured_cookies: list[dict] = []
    storage_state: dict | None = None
    success = False
    try:
        success_re = re.compile(success_pattern)
    except re.error as exc:
        # A stored profile can carry a pattern this build of Python will not
        # compile. Uncaught it escapes main() as a traceback and exit 1, on a
        # path whose stdio the consumer inherits.
        sys.stderr.write(
            f"sso-broker {verb}: stored success-url-pattern is not a valid "
            f"regular expression ({exc.msg}); re-register the profile\n"
        )
        return 3

    sync_playwright = _import_playwright()
    poll_seconds = _REFRESH_SILENT_WINDOW_S if headless else _REGISTER_SIGNIN_POLL_S

    # Corporate-network env passthrough. The parent (``credbroker``) already
    # composed this from an allowlist, so forwarding it is a passthrough, not a
    # widening.
    env_for_browser = {**os.environ}

    with sync_playwright() as pw:
        browser = None
        if persist:
            user_data_dir = _browser_state_dir(profile)
            user_data_dir.mkdir(parents=True, exist_ok=True)
            context = pw.chromium.launch_persistent_context(
                user_data_dir=str(user_data_dir),
                headless=headless,
                env=env_for_browser,
            )
        else:
            browser = pw.chromium.launch(headless=headless, env=env_for_browser)
            context = browser.new_context()

        navigated = True
        try:
            page = context.pages[0] if context.pages else context.new_page()
            try:
                page.goto(login_url)
            except Exception as exc:  # noqa: BLE001 — playwright's own error types
                # A navigation timeout on the headless path means the same thing
                # exit 5 means: this could not complete unaided. Uncaught it
                # escapes as a traceback and exit 1, which the consumer maps to
                # "recapture failed" and reports without the re-register hint.
                navigated = False
                sys.stderr.write(
                    f"sso-broker {verb}: could not reach the sign-in destination "
                    f"({type(exc).__name__})\n"
                )

            deadline = time.time() + (poll_seconds if navigated else 0)
            while time.time() < deadline:
                if success_re.search(page.url):
                    success = True
                    break
                page.wait_for_timeout(500)

            if success:
                captured_cookies = context.cookies()
                if not persist:
                    storage_state = context.storage_state()
        finally:
            # Suppressed independently: if closing the context raises, the
            # browser must still be closed, or the ephemeral Chromium survives
            # holding whatever the capture context had. The parent's tree kill
            # only fires on timeout or interrupt, not on a clean-but-erroring
            # engine exit, so nothing else would reclaim it.
            with contextlib.suppress(Exception):  # noqa: BLE001
                context.close()
            if browser is not None:
                with contextlib.suppress(Exception):  # noqa: BLE001
                    browser.close()

        if success and not persist:
            _seed_persistent_profile(pw, profile, storage_state, env_for_browser)

    if not success:
        if headless:
            sys.stderr.write(
                f"sso-broker refresh: the stored browser session could not reach "
                f"{success_pattern!r} unaided within {poll_seconds:g}s — a human "
                f"must sign in. No browser was shown; re-register to capture a "
                f"new session.\n"
            )
            return 5
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


def _seed_persistent_profile(
    pw, profile: str, storage_state: dict | None, env_for_browser: dict
) -> bool:
    """Copy an ephemeral capture's cookies into ``browser-state/<profile>``.

    ``launch_persistent_context`` takes no ``storage_state`` — a persistent
    context owns its own state directory — so seeding is a second, *headless*
    persistent launch plus ``add_cookies``.

    **Named limitation:** ``localStorage`` and ``sessionStorage`` are not seeded.
    ``storage_state()`` reports them under ``origins``, but there is no
    context-level API to restore them into a persistent profile. Where the IdP
    session depends on either, the seed silently under-delivers and the first
    automatic ``refresh`` returns ``5`` — the operator re-registers. That is a
    UX cost, not an exposure: the automatic path never renders a login page.

    :returns: whether the seed was written. A failed seed is not a failed
        capture — the session itself was captured and stored.
    """
    cookies = (storage_state or {}).get("cookies") or []
    if not cookies:
        sys.stderr.write(
            f"sso-broker register: nothing to seed into browser-state for "
            f"{profile!r}; the next automatic refresh will need a re-register\n"
        )
        return False
    user_data_dir = _browser_state_dir(profile)
    user_data_dir.mkdir(parents=True, exist_ok=True)
    # One guard over the launch *and* the write. Seeding runs before the profile
    # TOML and the jar are stored, so anything escaping here throws away a
    # sign-in the human has already completed — which is the opposite of this
    # function's contract.
    context = None
    try:
        context = pw.chromium.launch_persistent_context(
            user_data_dir=str(user_data_dir),
            headless=True,
            env=env_for_browser,
        )
        context.add_cookies(cookies)
    except Exception as exc:  # noqa: BLE001 — a failed seed must not fail capture
        sys.stderr.write(
            f"sso-broker register: could not seed browser-state for {profile!r} "
            f"({type(exc).__name__}); the next automatic refresh will need a "
            f"re-register\n"
        )
        return False
    finally:
        if context is not None:
            with contextlib.suppress(Exception):  # noqa: BLE001
                context.close()
    return True


def _do_register(profile: str, args: argparse.Namespace) -> int:
    """Interactive first capture: a **headed** browser at ``login_url``.

    Persistent by default, so a direct operator invocation is unchanged.
    ``--ephemeral`` captures in a throwaway context and seeds the persistent
    profile from it; ``credbroker.register_sso_session`` is its only user.

    Required args: ``--login-url``, ``--success-url-pattern``.
    Optional: ``--cookie-domain`` (repeatable), ``--session-filename``,
    ``--validation-endpoint``, ``--ttl-hint-minutes``, ``--ephemeral``.
    """
    return _capture(
        profile,
        args,
        persist=not getattr(args, "ephemeral", False),
        headless=False,
    )


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
    except (OSError, ValueError) as exc:
        # Unparseable or unreadable TOML — including the state `_write_profile`'s
        # escaping exists to stop *creating*, but which a profile written before
        # that landed can already be in. Uncaught this is a traceback and exit 1
        # on stdio the consumer inherits.
        sys.stderr.write(
            f"sso-broker get-cookies: profile {profile!r} is unreadable "
            f"({type(exc).__name__}); re-register it\n"
        )
        return 2

    jar = _load_cookie_jar(profile)
    if jar is None:
        sys.stderr.write(
            f"sso-broker get-cookies: no cookie jar for profile {profile!r}; "
            f"re-auth required (run 'sso-broker register {profile} ...')\n"
        )
        return 2

    # Materialise the jar to a 0600 file under sso-cookies/ and print its path.
    # Consumer skills read the file and never see cookie values via argv/stdout.
    #
    # The rewrite is **unconditional**. On Tier-2-capable platforms the primary
    # store is the keychain and this file is only a materialisation surface, so
    # skipping the write when the file already exists serves the *pre-refresh*
    # jar after every successful re-capture: the consumer's retry 401s and the
    # recapture was for nothing. It looked correct only on Linux, where the two
    # surfaces are the same file — which is where CI runs.
    materialised = _cookie_floor_path(profile)
    try:
        _file_floor_write(profile, jar)
    except OSError as exc:
        sys.stderr.write(
            f"sso-broker get-cookies: could not materialise the jar for "
            f"profile {profile!r}: {type(exc).__name__}\n"
        )
        return 3
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
    except (OSError, ValueError) as exc:
        sys.stderr.write(
            f"sso-broker test: profile {profile!r} is unreadable "
            f"({type(exc).__name__}); re-register it\n"
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
    # Reject non-web schemes before the request. B310's real danger is urllib
    # honouring file:// / ftp:// / gopher:// — a corrupt or hand-edited profile
    # whose login-url points elsewhere is treated as corrupt config (exit 3).
    # http and https both stay valid, so this breaks no legitimate endpoint.
    if urllib.parse.urlparse(url).scheme not in ("https", "http"):
        sys.stderr.write(f"sso-broker test: refusing non-http(s) URL scheme for {profile!r}\n")
        return 3
    req = urllib.request.Request(url, headers={"Cookie": cookie_header})
    try:
        # Corporate-network env passthrough is the parent's responsibility;
        # urllib honours HTTPS_PROXY / NO_PROXY / SSL_CERT_FILE / SSL_CERT_DIR
        # from the environment automatically.
        # B310: scheme asserted http(s) above; base is the operator-configured
        # SSO endpoint (not attacker input).
        with urllib.request.urlopen(req, timeout=15) as resp:  # nosec B310
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


# Every argument that could carry, or narrow, a sign-in destination. `refresh`
# refuses all of them: the destination comes from the stored profile, which only
# a completed operator-authorised `register` writes.
_REFRESH_REFUSED_ARGS = (
    ("login_url", "--login-url"),
    ("success_url_pattern", "--success-url-pattern"),
    ("cookie_domain", "--cookie-domain"),
    ("validation_endpoint", "--validation-endpoint"),
    ("session_filename", "--session-filename"),
    ("ttl_hint_minutes", "--ttl-hint-minutes"),
)


def _do_refresh(profile: str, args: argparse.Namespace) -> int:
    """Re-capture an existing profile's session **without a human**.

    Differs from ``register`` in three ways, all of them load-bearing:

    * it is **headless**, with a bounded silent-completion window — if the warm
      browser profile cannot complete the IdP flow unaided it returns ``5``
      rather than leaving a login page in front of whoever is at the machine;
    * it **rejects every connection argument** — the destination comes only from
      the stored profile, so an automated caller cannot choose where the browser
      goes;
    * it returns ``4``, not ``3``, when the profile is not registered.
    """
    supplied = [flag for attr, flag in _REFRESH_REFUSED_ARGS if getattr(args, attr, None)]
    if supplied:
        sys.stderr.write(
            f"sso-broker refresh: {', '.join(supplied)} not accepted — refresh "
            f"reads the destination from the stored profile. Use 'register' to "
            f"change it.\n"
        )
        return 3

    try:
        table = _load_profile(profile)
    except FileNotFoundError:
        sys.stderr.write(
            f"sso-broker refresh: profile {profile!r} not registered; "
            f"run 'register' first\n"
        )
        # Exit 4, not 3. `3` is returned from ten distinct sites in this file —
        # playwright absent, sign-in not completed, a corrupt jar — so a consumer
        # reading it as "not registered" would attempt a browser recapture on
        # every internal failure. Not-registered gets a code of its own.
        return 4
    except (OSError, ValueError) as exc:
        # An unreadable profile is not refreshable, and the remediation is the
        # same as never-registered: capture a new one. Same code, so the
        # consumer routes it to the same message.
        sys.stderr.write(
            f"sso-broker refresh: profile {profile!r} is unreadable "
            f"({type(exc).__name__}); re-register it\n"
        )
        return 4

    # The destination is the stored one, unconditionally: nothing was supplied.
    args.login_url = table.get("login_url", "")
    args.success_url_pattern = table.get("success_url_pattern", "")
    args.session_filename = table.get("session_filename", "")
    args.validation_endpoint = table.get("validation_endpoint", "")
    args.ttl_hint_minutes = table.get("ttl_hint_minutes", 480)
    args.cookie_domain = list(table.get("cookie_domains") or [])

    return _capture(profile, args, persist=True, headless=True)


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

    Test surface for the shim-companion projection regression
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
    p_register.add_argument(
        "--ephemeral", action="store_true",
        help=(
            "Capture in a throwaway context and seed browser-state/<profile> "
            "from it, instead of capturing in the persistent profile directly. "
            "Used by credbroker.register_sso_session; the verb's default is "
            "unchanged."
        ),
    )

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
        help="Print repr(_tier2_backend) (shim-companion probe).",
    )

    return parser


# Verbs whose ``profile`` must satisfy the grammar before any path is composed.
# ``rm`` is deliberately absent: a profile registered before this change under a
# now-invalid name must stay deletable, or ``list-profiles`` keeps advertising a
# live corporate cookie jar the operator cannot remove. ``rm`` is gated on
# containment alone, which the path composers enforce for every verb.
_GRAMMAR_GUARDED_VERBS = frozenset({"register", "get-cookies", "test", "refresh"})


def main(argv: list[str] | None = None) -> int:
    raw = list(sys.argv[1:]) if argv is None else list(argv)
    _refuse_argv_ban(raw)
    parser = _build_parser()
    args = parser.parse_args(raw)

    verb = args.verb
    if verb in _GRAMMAR_GUARDED_VERBS:
        reason = _profile_grammar_error(args.profile)
        if reason is not None:
            sys.stderr.write(f"sso-broker {verb}: {reason}\n")
            return 3

    try:
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
    except ProfileConfinementError as exc:
        sys.stderr.write(f"sso-broker {verb}: {exc}\n")
        return 3
    raise AssertionError(f"unreachable verb: {verb}")  # pragma: no cover


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
