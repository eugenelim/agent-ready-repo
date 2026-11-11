"""Tests for check 3's rendered half: built site vs the fetched deployed index."""

from __future__ import annotations

import hashlib
import importlib.util
import json
import sys
import threading
from collections.abc import Generator
from contextlib import contextmanager
from http.server import BaseHTTPRequestHandler, HTTPServer
from pathlib import Path

import pytest

SCRIPT = Path(__file__).resolve().parent / "check-deployed-release-parity.py"
_spec = importlib.util.spec_from_file_location("check_deployed_release_parity", SCRIPT)
assert _spec is not None and _spec.loader is not None
mod = importlib.util.module_from_spec(_spec)
sys.modules[_spec.name] = mod
_spec.loader.exec_module(mod)

MEMBERS = {"pack.schema.json": b'{"a": 1}\n', "adapter.toml": b"x = 1\n"}


def sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def index_for(members: dict[str, bytes], version: str = "0.1") -> dict:
    return {"releases": [{"version": version, "members": {k: sha(v) for k, v in members.items()}}]}


def make_build(tmp_path: Path, members: dict[str, bytes] = MEMBERS, version: str = "0.1") -> Path:
    build = tmp_path / "build"
    release = build / mod.SITE_SUBDIR / version
    release.mkdir(parents=True)
    for name, data in members.items():
        (release / name).write_bytes(data)
    return build


@contextmanager
def stub(
    status: int = 200, body: bytes = b"", location: str | None = None
) -> Generator[str]:
    """A local server answering every GET with the given status and body."""

    class Handler(BaseHTTPRequestHandler):
        def do_GET(self):  # noqa: N802
            self.send_response(status)
            if location:
                self.send_header("Location", location)
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)

        def log_message(self, *args):  # noqa: D102
            pass

    server = HTTPServer(("127.0.0.1", 0), Handler)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    try:
        yield f"http://127.0.0.1:{server.server_port}/index.json"
    finally:
        server.shutdown()
        server.server_close()


def run_against(tmp_path: Path, url: str, event: str = "pull_request", ref: str = "refs/pull/1/merge",
                build: Path | None = None) -> int:
    return mod.run(build or make_build(tmp_path), event, ref, url=url, opener=mod.build_opener())


def served(payload: object) -> bytes:
    return json.dumps(payload).encode()


def test_matching_index_passes(tmp_path, capsys):
    with stub(body=served(index_for(MEMBERS))) as url:
        assert run_against(tmp_path, url) == 0
    assert "OK" in capsys.readouterr().out


def test_empty_releases_passes(tmp_path):
    with stub(body=b'{"releases": []}') as url:
        assert run_against(tmp_path, url) == 0


def test_released_path_missing_from_build_fails(tmp_path):
    build = make_build(tmp_path, {"pack.schema.json": MEMBERS["pack.schema.json"]})
    with stub(body=served(index_for(MEMBERS))) as url:
        assert run_against(tmp_path, url, build=build) == 1


def test_served_byte_differing_from_fetched_digest_fails(tmp_path, capsys):
    build = make_build(tmp_path, {**MEMBERS, "adapter.toml": b"x = 2\n"})
    with stub(body=served(index_for(MEMBERS))) as url:
        assert run_against(tmp_path, url, build=build) == 1
    assert "differ" in capsys.readouterr().err


@pytest.mark.parametrize("name", ["../x", "a/b", "..", ""])
def test_unconfined_member_name_in_fetched_index_fails(tmp_path, name):
    payload = {"releases": [{"version": "0.1", "members": {name: sha(b"x")}}]}
    with stub(body=served(payload)) as url:
        assert run_against(tmp_path, url) == 1


def test_404_index_fails(tmp_path):
    with stub(status=404, body=b"not found") as url:
        assert run_against(tmp_path, url) == 1


def test_unfetchable_index_fails(tmp_path):
    with stub() as url:
        pass  # server is shut down: connection refused
    assert run_against(tmp_path, url) == 1


def test_non_200_success_status_fails(tmp_path):
    with stub(status=204, body=b"") as url:
        assert run_against(tmp_path, url) == 1


@pytest.mark.parametrize("body", [b"", b"<html>nope</html>", b'{"releases": [', b"[]", b"null"])
def test_non_json_or_truncated_or_wrong_shape_fails(tmp_path, body):
    with stub(body=body) as url:
        assert run_against(tmp_path, url) == 1


def test_releases_key_absent_fails(tmp_path):
    with stub(body=b'{"other": []}') as url:
        assert run_against(tmp_path, url) == 1


@pytest.mark.parametrize("value", ['"x"', "{}", "null", "1"])
def test_releases_not_an_array_fails(tmp_path, value):
    with stub(body=f'{{"releases": {value}}}'.encode()) as url:
        assert run_against(tmp_path, url) == 1


def test_body_past_ceiling_fails_without_being_read_whole(tmp_path, capsys):
    padding = " " * (mod.MAX_BODY_BYTES + 10)
    with stub(body=(b'{"releases": []}' + padding.encode())) as url:
        assert run_against(tmp_path, url) == 1
    assert "ceiling" in capsys.readouterr().err

    # And the read itself is bounded, not read whole and measured afterwards.
    reads: list[int | None] = []

    class Resp:
        status = 200

        def read(self, amt=None):
            reads.append(amt)
            return b"x" * (amt or 0)

        def __enter__(self):
            return self

        def __exit__(self, *a):
            return False

    class Opener:
        def open(self, url, timeout=None):
            return Resp()

    with pytest.raises(mod.ParityError):
        mod.fetch_releases("https://example.invalid/", Opener())  # type: ignore[arg-type]
    assert reads == [mod.MAX_BODY_BYTES + 1]


def test_redirect_is_refused(tmp_path):
    with stub() as target, stub(status=302, location=target) as url:
        assert run_against(tmp_path, url) == 1
        with pytest.raises(mod.ParityError, match="redirect"):
            mod.fetch_releases(url, mod.build_opener())


def test_timeout_is_thirty_seconds_and_passed_to_open():
    assert mod.FETCH_TIMEOUT_SECONDS == 30
    seen: dict[str, object] = {}

    class Opener:
        def open(self, url, timeout=None):
            seen["timeout"] = timeout
            raise OSError("stop")

    with pytest.raises(mod.ParityError):
        mod.fetch_releases("https://example.invalid/", Opener())  # type: ignore[arg-type]
    assert seen["timeout"] == 30


def test_url_is_a_literal_no_environment_variable_changes(monkeypatch):
    assert mod.INDEX_URL.startswith("https://eugenelim.github.io/")
    for key in ("INDEX_URL", "GITHUB_SERVER_URL", "GITHUB_REPOSITORY", "https_proxy", "PAGES_URL"):
        monkeypatch.setenv(key, "https://attacker.invalid/")
    spec = importlib.util.spec_from_file_location("reloaded_parity", SCRIPT)
    assert spec is not None and spec.loader is not None
    fresh = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(fresh)
    assert fresh.INDEX_URL == mod.INDEX_URL


def test_https_proxy_does_not_change_destination(monkeypatch, tmp_path):
    with stub(body=served(index_for(MEMBERS))) as proxy_url:
        monkeypatch.setenv("http_proxy", proxy_url.rsplit("/", 1)[0])
        monkeypatch.setenv("https_proxy", proxy_url.rsplit("/", 1)[0])
        opener = mod.build_opener()
        assert not any(isinstance(h, mod.urllib.request.ProxyHandler) for h in opener.handlers)
    # The stdlib default WOULD have installed one, which is the control's reason.
    default = mod.urllib.request.build_opener()
    assert any(isinstance(h, mod.urllib.request.ProxyHandler) for h in default.handlers)
    # With the proxy set and a dead target, the fetch goes to the target and fails.
    with stub() as dead:
        pass
    with pytest.raises(mod.ParityError):
        mod.fetch_releases(dead, opener)


def test_context_verifies_and_ignores_cert_environment(monkeypatch, tmp_path):
    import ssl

    for key in ("SSL_CERT_FILE", "SSL_CERT_DIR"):
        monkeypatch.delenv(key, raising=False)
    baseline = mod.build_context()
    assert baseline.verify_mode == ssl.CERT_REQUIRED
    assert baseline.check_hostname is True
    empty = tmp_path / "empty"
    empty.mkdir()
    for key, value in (("SSL_CERT_FILE", str(tmp_path / "nonexistent.pem")),
                       ("SSL_CERT_DIR", str(empty))):
        monkeypatch.setenv(key, value)
        ctx = mod.build_context()
        assert ctx.cert_store_stats() == baseline.cert_store_stats()
        assert ctx.verify_mode == ssl.CERT_REQUIRED and ctx.check_hostname is True
        monkeypatch.delenv(key)


def test_build_tree_index_cannot_substitute_for_fetched_anchor(tmp_path):
    tampered = {**MEMBERS, "adapter.toml": b"x = 999\n"}
    build = make_build(tmp_path, tampered)
    # A self-consistent index sits inside the build output...
    (build / mod.SITE_SUBDIR / "index.json").write_bytes(served(index_for(tampered)))
    # ...but the fetched anchor carries the released digests, so the check fails.
    with stub(body=served(index_for(MEMBERS))) as url:
        assert run_against(tmp_path, url, build=build) == 1
    # And with the anchor unreachable the in-build index is not a fallback.
    with stub(status=404) as url:
        assert run_against(tmp_path, url, build=build) == 1


def test_skips_on_dispatch_from_a_non_main_ref(tmp_path, capsys):
    # An unreachable URL proves no fetch was attempted.
    assert mod.run(make_build(tmp_path), "workflow_dispatch", "refs/heads/feature",
                   url="http://127.0.0.1:1/", opener=mod.build_opener()) == 0
    assert "SKIPPED" in capsys.readouterr().out


@pytest.mark.parametrize("event,ref", [
    ("pull_request", "refs/pull/7/merge"),
    ("push", "refs/heads/main"),
    ("workflow_dispatch", "refs/heads/main"),
    ("", ""),
])
def test_runs_rather_than_skips(tmp_path, capsys, event, ref):
    # The anchor is unreachable, so a run FAILS; a skip would pass.
    assert mod.run(make_build(tmp_path), event, ref, url="http://127.0.0.1:1/",
                   opener=mod.build_opener()) == 1
    assert "SKIPPED" not in capsys.readouterr().out


def test_cli_reads_event_and_ref_from_the_environment(tmp_path, monkeypatch, capsys):
    monkeypatch.setenv("GITHUB_EVENT_NAME", "workflow_dispatch")
    monkeypatch.setenv("GITHUB_REF", "refs/heads/feature")
    assert mod.main(["--build-dir", str(make_build(tmp_path))]) == 0
    assert "SKIPPED" in capsys.readouterr().out
