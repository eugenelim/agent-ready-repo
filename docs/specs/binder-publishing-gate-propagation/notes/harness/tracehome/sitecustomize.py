"""Z5 instrumentation: log every Python-level network attempt to $Z5_TRACE.

Injected via PYTHONPATH so the real `python -m zensical build` argv is preserved.
Wraps the socket entry points a Python-level outbound request must pass through,
plus urllib/http.client at the library level, and records a stack for each call.

Caveat recorded with the gate result: this cannot see network calls made from
`zensical.abi3.so` if that extension calls libc directly rather than through
CPython's socket module. The sandboxed run covers that case.
"""

from __future__ import annotations

import os
import pathlib
import socket
import traceback

_PATH = os.environ.get("Z5_TRACE")

if _PATH:

    def _log(what: str, args: object) -> None:
        with pathlib.Path(_PATH).open("a", encoding="utf-8") as fh:
            fh.write(f"=== {what} {args!r}\n")
            fh.write("".join(traceback.format_stack()[:-1]))
            fh.write("\n")

    _real_getaddrinfo = socket.getaddrinfo
    _real_create_connection = socket.create_connection
    _real_connect = socket.socket.connect
    _real_connect_ex = socket.socket.connect_ex

    def getaddrinfo(*a, **k):  # noqa: ANN002, ANN003, ANN201
        _log("getaddrinfo", a)
        return _real_getaddrinfo(*a, **k)

    def create_connection(*a, **k):  # noqa: ANN002, ANN003, ANN201
        _log("create_connection", a)
        return _real_create_connection(*a, **k)

    def connect(self, addr):  # noqa: ANN001, ANN201
        _log("socket.connect", addr)
        return _real_connect(self, addr)

    def connect_ex(self, addr):  # noqa: ANN001, ANN201
        _log("socket.connect_ex", addr)
        return _real_connect_ex(self, addr)

    socket.getaddrinfo = getaddrinfo
    socket.create_connection = create_connection
    socket.socket.connect = connect
    socket.socket.connect_ex = connect_ex

    # Library-level, so an attempt is visible even if it never reaches connect().
    import http.client
    import urllib.request

    _real_urlopen = urllib.request.urlopen
    _real_request = http.client.HTTPConnection.request

    def urlopen(*a, **k):  # noqa: ANN002, ANN003, ANN201
        _log("urllib.urlopen", a)
        return _real_urlopen(*a, **k)

    def request(self, *a, **k):  # noqa: ANN001, ANN002, ANN003, ANN201
        _log("http.client.request", a)
        return _real_request(self, *a, **k)

    urllib.request.urlopen = urlopen
    http.client.HTTPConnection.request = request
