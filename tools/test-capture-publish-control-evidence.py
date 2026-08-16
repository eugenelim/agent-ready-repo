#!/usr/bin/env python3
"""Self-test for tools/capture-publish-control-evidence.py's `--repo` guard.

`_validate_repo` is the only thing standing between an operator-supplied
`--repo` and the API paths the capture assembles, and `urllib` sends the
selector it is handed without normalising it. So the guard has to reject RFC
3986 dot-segments, not merely constrain the character set — `.` and `..` are
built entirely from legal characters.

The accept cases matter as much as the reject cases, and are the reason this
guard is not simply "each segment must start alphanumeric": `owner/.github` is
a real GitHub repository, and a leading dot is legal in a repository name. A
tightening that broke it would be a regression, not extra safety.
"""

from __future__ import annotations

import contextlib
import importlib.util
import sys
import urllib.request
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8", errors="strict")
sys.stderr.reconfigure(encoding="utf-8", errors="backslashreplace")

_HERE = Path(__file__).resolve().parent
_SPEC = importlib.util.spec_from_file_location(
    "capture_publish_control_evidence", _HERE / "capture-publish-control-evidence.py"
)
assert _SPEC and _SPEC.loader
_MOD = importlib.util.module_from_spec(_SPEC)
_SPEC.loader.exec_module(_MOD)

FAILURES: list[str] = []


def check(label: str, condition: bool, detail: str = "") -> None:
    if condition:
        print(f"  ok   {label}")
    else:
        FAILURES.append(f"{label}{': ' + detail if detail else ''}")
        print(f"  FAIL {label} {detail}")


def rejects(value: str) -> bool:
    try:
        _MOD._validate_repo(value)
    except _MOD.CaptureError:
        return True
    return False


def main() -> int:
    print("capture-publish-control-evidence --repo guard self-test")

    # 1. Dot-segments. Each of these satisfies the two-segment character
    #    pattern, which is exactly why the charset alone was not enough.
    for value in ("../..", "owner/..", "./name", "../name", "owner/."):
        check(f"rejects dot-segment {value!r}", rejects(value))

    # 2. The accept set. A leading dot is legal in a GitHub repository name;
    #    `owner/.github` is the common real case. Rejecting these would be a
    #    regression introduced in the name of hardening.
    for value in ("owner/name", "owner/.github", "my-org/my.repo", "a_b/c-d.e", "owner/..x", "owner/x.."):
        try:
            check(f"accepts {value!r}", _MOD._validate_repo(value) == value)
        except _MOD.CaptureError as exc:
            check(f"accepts {value!r}", False, str(exc))

    # 3. The pre-existing shape checks still hold — the dot-segment rule is
    #    additive, not a replacement.
    for value in ("owner", "owner/name/extra", "", "owner/", "/name", "own er/name", "owner/na me"):
        check(f"rejects malformed {value!r}", rejects(value))

    # 4. The two rules are distinguishable. A dot-segment value must fail with
    #    the dot-segment message, not the generic shape message, or the
    #    operator is sent looking for the wrong defect.
    try:
        _MOD._validate_repo("owner/..")
    except _MOD.CaptureError as exc:
        check("dot-segment error names the real cause", "path segment" in str(exc), str(exc))
    else:
        check("dot-segment error names the real cause", False, "did not raise")

    # 5. Scheme/host confinement is not this guard's job, but the capture's
    #    B310 suppression cites it as its reason, so the reason has to be
    #    pinned by BEHAVIOUR, not by a substring match on the source. An
    #    earlier version of this file grepped for `build_opener(_NoRedirect)`
    #    and passed green with `redirect_request` deleted — at which point
    #    urllib's default handler forwards the `Authorization: Bearer <jwt>`
    #    header across an origin change. A gate that cannot detect the removal
    #    of the control it names is not a gate.
    request = urllib.request.Request("https://api.github.com/repos/o/n")
    try:
        _MOD._NoRedirect().redirect_request(
            request, None, 302, "Found", {}, "https://evil.example/x"
        )
    except _MOD.CaptureError:
        check("a redirect is refused, not followed", True)
    except Exception as exc:  # noqa: BLE001
        check("a redirect is refused, not followed", False, f"raised {type(exc).__name__}")
    else:
        check("a redirect is refused, not followed", False, "returned a request")

    # The override must be defined on _NoRedirect itself, not inherited. The
    # getattr-per-code loop this replaced was a tautology: _NoRedirect
    # subclasses HTTPRedirectHandler, so every http_error_30x is non-None by
    # inheritance and the loop stayed green with redirect_request deleted.
    check("redirect_request is defined on _NoRedirect, not inherited",
          "redirect_request" in _MOD._NoRedirect.__dict__)

    # ...and the production call site must actually install it. Asserting on a
    # locally-built opener only tests urllib's handler substitution; changing
    # _app_api to build_opener() would leave that green while the bearer JWT
    # follows a 302 to another origin. So capture what _app_api really passes.
    captured: list = []
    real_build_opener = _MOD.urllib.request.build_opener

    def _spy(*handlers):
        captured.extend(handlers)
        return real_build_opener(*handlers)

    _MOD.urllib.request.build_opener = _spy
    try:
        # The network call is expected to fail; only the spy's capture matters.
        with contextlib.suppress(Exception):
            _MOD._app_api("repos/o/n/installation", "not-a-real-jwt")
    finally:
        _MOD.urllib.request.build_opener = real_build_opener
    check("_app_api installs _NoRedirect", _MOD._NoRedirect in captured, str(captured))

    # The other half of the B310 rationale: the API base is a fixed literal.
    # Captured from the Request _app_api actually constructs.
    seen: list = []
    real_request = _MOD.urllib.request.Request

    def _request_spy(url, *a, **kw):
        seen.append(url)
        return real_request(url, *a, **kw)

    _MOD.urllib.request.Request = _request_spy
    try:
        with contextlib.suppress(Exception):
            _MOD._app_api("repos/o/n/installation", "not-a-real-jwt")
    finally:
        _MOD.urllib.request.Request = real_request
    check("the API base is a fixed https://api.github.com literal",
          bool(seen) and all(u.startswith("https://api.github.com/") for u in seen), str(seen))

    # 6. `gh api` gets `--`, so a path can never be read as a flag. A
    #    leading-dash owner passes the charset guard, so this is the control
    #    that keeps that from mattering. Pinned behaviourally: the spec's own
    #    Always-do boundary rules out a substring match on the source.
    argv_seen: list = []
    real_run = _MOD.subprocess.run

    def _run_spy(argv, *a, **kw):
        argv_seen.append(argv)
        return real_run([sys.executable, "-c", "raise SystemExit(1)"], *a, **kw)

    _MOD.subprocess.run = _run_spy
    try:
        with contextlib.suppress(_MOD.CaptureError):
            _MOD._gh_api("repos/o/n")
    finally:
        _MOD.subprocess.run = real_run
    check("gh api terminates flag parsing",
          bool(argv_seen) and argv_seen[0][:3] == ["gh", "api", "--"], str(argv_seen))
    try:
        _MOD._validate_repo("-h/name")
    except _MOD.CaptureError:
        check("leading-dash owner is rejected outright", False,
              "if this ever starts rejecting, drop the `--` rationale above")
    else:
        check("leading-dash owner is accepted (hence the `--`)", True)

    print()
    if FAILURES:
        print(f"capture-publish-control-evidence self-test: {len(FAILURES)} case(s) failed.")
        return 1
    print("capture-publish-control-evidence self-test: all cases passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
