"""Tests for check 4: the release gate (bundled bytes vs snapshot vs deployed index)."""

from __future__ import annotations

import hashlib
import importlib.util
import json
import ssl
import sys
import threading
from collections.abc import Generator
from contextlib import contextmanager
from http.server import BaseHTTPRequestHandler, HTTPServer
from pathlib import Path

import pytest

SCRIPT = Path(__file__).resolve().parent / "catalogue" / "check_release_gate.py"
_spec = importlib.util.spec_from_file_location("check_release_gate", SCRIPT)
assert _spec is not None and _spec.loader is not None
mod = importlib.util.module_from_spec(_spec)
sys.modules[_spec.name] = mod
_spec.loader.exec_module(mod)
parity = mod.parity

VERSION = "0.1"
ID_BASE = "https://example.invalid/docs/spec/catalogue"


def schema(name: str, version: str = VERSION) -> bytes:
    return json.dumps({"$id": f"{ID_BASE}/{version}/{name}", "title": name}).encode()


SCHEMAS = ["a.schema.json", "b.schema.json"]
OTHERS = {"vocab.toml": b"x = 1\n"}
MEMBERS = {**{n: schema(n) for n in SCHEMAS}, **OTHERS}


def sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def make_tree(
    tmp_path: Path,
    *,
    members: dict[str, bytes] = MEMBERS,
    snapshot: dict[str, bytes] | None = MEMBERS,
    bundled: dict[str, bytes] | None = None,
    inventory: str | None = "\n".join(SCHEMAS) + "\n",
    row_version: str | None = VERSION,
) -> tuple[Path, Path]:
    """A contracts dir and a `_data` dir; `members` are the row's digests."""
    contracts, data = tmp_path / "contracts", tmp_path / "_data"
    data.mkdir()
    contracts.mkdir()
    toml = "[spec]\nname = \"fixture\"\n\n"
    for name in members:
        toml += f'[[contract]]\npath = "{name}"\nrole = "member"\n\n'
    if row_version is not None:
        toml += f'[[release]]\nversion = "{row_version}"\ndate = "2026-01-01"\n'
        toml += 'adapter_contract = "0.1"\n\n[release.members]\n'
        for name, content in members.items():
            toml += f'"{name}" = "{sha(content)}"\n'
        toml += '\n[release.pages]\n"overview.md" = "' + sha(b"page") + '"\n'
    (contracts / "catalogue-spec.toml").write_text(toml)
    for name in members:
        (contracts / name).write_bytes(members[name])
    if snapshot is not None:
        snap = contracts / "releases" / "catalogue" / VERSION
        snap.mkdir(parents=True)
        for name, content in snapshot.items():
            (snap / name).write_bytes(content)
        (snap / "overview.md").write_bytes(b"page")
    for name, content in (members if bundled is None else bundled).items():
        (data / name).write_bytes(content)
    if inventory is not None:
        (data / "catalogue-members.txt").write_text(inventory)
    return contracts, data


@contextmanager
def stub(status: int = 200, body: bytes = b"", location: str | None = None) -> Generator[str]:
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
    threading.Thread(target=server.serve_forever, daemon=True).start()
    try:
        yield f"http://127.0.0.1:{server.server_port}/index.json"
    finally:
        server.shutdown()
        server.server_close()


def index_for(members: dict[str, bytes] = MEMBERS, version: str = VERSION) -> bytes:
    entry = {"version": version, "members": {k: sha(v) for k, v in members.items()}}
    return json.dumps({"releases": [entry]}).encode()


def gate(contracts: Path, data: Path, url: str) -> int:
    return mod.run(contracts, data, url=url, opener=parity.build_opener())


def test_matching_bundle_and_index_pass(tmp_path, capsys):
    contracts, data = make_tree(tmp_path)
    with stub(body=index_for()) as url:
        assert gate(contracts, data, url) == 0
    assert "OK" in capsys.readouterr().out


def test_version_is_read_from_the_bundled_member_ids(tmp_path):
    contracts, data = make_tree(tmp_path)
    assert mod.read_version(data, SCHEMAS) == VERSION
    (data / "a.schema.json").write_bytes(schema("a.schema.json", "0.2"))
    with pytest.raises(mod.GateError, match="disagree"):
        mod.read_version(data, SCHEMAS)
    (data / "b.schema.json").write_bytes(schema("b.schema.json", "0.2"))
    assert mod.read_version(data, SCHEMAS) == "0.2"
    # With V = 0.2 there is no row, so the gate fails on the missing row.
    with stub(body=index_for()) as url:
        assert gate(contracts, data, url) == 1


def test_compared_set_is_the_row_member_keys_not_the_inventory(tmp_path):
    contracts, data = make_tree(tmp_path)
    _, digests = mod.check_bundle(contracts, data)
    assert set(digests) == set(MEMBERS)  # includes the non-JSON member the inventory omits
    # A differing non-JSON member, invisible to the inventory, still fails.
    (data / "vocab.toml").write_bytes(b"x = 2\n")
    with stub(body=index_for()) as url:
        assert gate(contracts, data, url) == 1


def test_pages_table_is_not_compared(tmp_path):
    contracts, data = make_tree(tmp_path)
    # No bundled page source exists, and the snapshot page may be anything.
    assert not (data / "overview.md").exists()
    (contracts / "releases" / "catalogue" / VERSION / "overview.md").write_bytes(b"edited")
    with stub(body=index_for()) as url:
        assert gate(contracts, data, url) == 0


def test_no_snapshot_for_v_fails(tmp_path, capsys):
    contracts, data = make_tree(tmp_path, snapshot=None)
    with stub(body=index_for()) as url:
        assert gate(contracts, data, url) == 1


def test_no_release_row_for_v_fails(tmp_path):
    contracts, data = make_tree(tmp_path, row_version="0.2")
    with stub(body=index_for()) as url:
        assert gate(contracts, data, url) == 1


def test_bundled_bytes_differing_from_snapshot_fail(tmp_path, capsys):
    contracts, data = make_tree(tmp_path)
    (data / "a.schema.json").write_bytes(schema("a.schema.json") + b" ")
    with stub(body=index_for()) as url:
        assert gate(contracts, data, url) == 1
    assert "differs" in capsys.readouterr().err


def test_a_member_absent_from_the_bundle_fails(tmp_path):
    contracts, data = make_tree(tmp_path)
    (data / "vocab.toml").unlink()
    with stub(body=index_for()) as url:
        assert gate(contracts, data, url) == 1


def test_deployed_index_not_listing_v_fails(tmp_path, capsys):
    contracts, data = make_tree(tmp_path)
    with stub(body=index_for(version="0.9")) as url:
        assert gate(contracts, data, url) == 1
    assert "does not list" in capsys.readouterr().err
    with stub(body=b'{"releases": []}') as url:
        assert gate(contracts, data, url) == 1


def test_deployed_digest_differing_fails(tmp_path):
    contracts, data = make_tree(tmp_path)
    with stub(body=index_for({**MEMBERS, "vocab.toml": b"x = 9\n"})) as url:
        assert gate(contracts, data, url) == 1


@pytest.mark.parametrize("status,body", [
    (404, b"nope"), (204, b""), (200, b""), (200, b"<html>"), (200, b'{"other": []}'),
    (200, b'{"releases": "x"}'), (200, b"[]"),
])
def test_non_200_or_unacceptable_index_fails(tmp_path, status, body):
    contracts, data = make_tree(tmp_path)
    with stub(status=status, body=body) as url:
        assert gate(contracts, data, url) == 1


def test_unreachable_index_fails(tmp_path):
    contracts, data = make_tree(tmp_path)
    with stub() as url:
        pass
    assert gate(contracts, data, url) == 1


@pytest.mark.parametrize("inventory", [
    "a.schema.json\n",                              # missing one
    "a.schema.json\nb.schema.json\nvocab.toml\n",   # extra, non-JSON
    "a.schema.json\nb.schema.json\nc.schema.json\n",  # extra unknown
    "a.schema.json\na.schema.json\nb.schema.json\n",  # duplicate
    "",                                             # empty
    "\n\n",                                         # blank only
    "a.schema.json\n..\n",                          # unreducible
    "a.schema.json\nb.schema.json\n/\n",            # unreducible
])
def test_inventory_not_exactly_the_json_subset_fails(tmp_path, inventory):
    contracts, data = make_tree(tmp_path, inventory=inventory)
    with stub(body=index_for()) as url:
        assert gate(contracts, data, url) == 1


def test_inventory_listing_directory_prefixed_names_reduces_to_base(tmp_path):
    contracts, data = make_tree(tmp_path, inventory="x/a.schema.json\nb.schema.json\n")
    with stub(body=index_for()) as url:
        assert gate(contracts, data, url) == 0


def test_absent_inventory_fails(tmp_path):
    contracts, data = make_tree(tmp_path, inventory=None)
    with stub(body=index_for()) as url:
        assert gate(contracts, data, url) == 1


def test_unreadable_inventory_fails(tmp_path):
    contracts, data = make_tree(tmp_path)
    (data / "catalogue-members.txt").write_bytes(b"\xff\xfe\x00bad")
    with stub(body=index_for()) as url:
        assert gate(contracts, data, url) == 1
    (data / "catalogue-members.txt").unlink()
    (data / "catalogue-members.txt").mkdir()  # a directory, not a file
    with stub(body=index_for()) as url:
        assert gate(contracts, data, url) == 1


def test_fetch_is_checks_three_shared_implementation():
    sibling = Path(__file__).resolve().parent / "check-deployed-release-parity.py"
    assert Path(parity.__file__) == sibling
    assert parity.FETCH_TIMEOUT_SECONDS == 30
    assert parity.MAX_BODY_BYTES == 1024 * 1024
    assert parity.INDEX_URL.startswith("https://eugenelim.github.io/")
    src = SCRIPT.read_text()
    assert "os.environ" not in src and "getenv" not in src and "import os" not in src  # no environment input


def test_fetch_refuses_redirects(tmp_path):
    contracts, data = make_tree(tmp_path)
    with stub(body=index_for()) as target, stub(status=302, location=target) as url:
        assert gate(contracts, data, url) == 1
        with pytest.raises(parity.ParityError, match="redirect"):
            parity.fetch_releases(url, parity.build_opener())


def test_fetch_carries_timeout_and_ceiling(tmp_path):
    seen: dict[str, object] = {}

    class Opener:
        def open(self, url, timeout=None):
            seen["timeout"] = timeout
            raise OSError("stop")

    contracts, data = make_tree(tmp_path)
    assert mod.run(contracts, data, url="https://example.invalid/", opener=Opener()) == 1  # type: ignore[arg-type]
    assert seen["timeout"] == 30
    padding = b" " * (parity.MAX_BODY_BYTES + 10)
    with stub(body=b'{"releases": []}' + padding) as url:
        assert gate(contracts, data, url) == 1


def test_https_proxy_is_ignored(monkeypatch, tmp_path):
    contracts, data = make_tree(tmp_path)
    with stub(body=index_for()) as proxy_url:
        monkeypatch.setenv("https_proxy", proxy_url.rsplit("/", 1)[0])
        monkeypatch.setenv("http_proxy", proxy_url.rsplit("/", 1)[0])
        opener = parity.build_opener()
        assert not any(isinstance(h, parity.urllib.request.ProxyHandler) for h in opener.handlers)
    with stub() as dead:
        pass
    monkeypatch.setenv("https_proxy", "http://127.0.0.1:9")
    assert mod.run(contracts, data, url=dead, opener=opener) == 1


def test_trust_anchor_ignores_cert_environment(monkeypatch, tmp_path):
    for key in ("SSL_CERT_FILE", "SSL_CERT_DIR"):
        monkeypatch.delenv(key, raising=False)
    baseline = parity.build_context()
    empty = tmp_path / "empty"
    empty.mkdir()
    for key, value in (("SSL_CERT_FILE", str(tmp_path / "none.pem")), ("SSL_CERT_DIR", str(empty))):
        monkeypatch.setenv(key, value)
        ctx = parity.build_context()
        assert ctx.cert_store_stats() == baseline.cert_store_stats()
        assert ctx.verify_mode == ssl.CERT_REQUIRED and ctx.check_hostname is True
        monkeypatch.delenv(key)


def test_cli_takes_no_arguments(capsys):
    assert mod.main(["--url", "https://attacker.invalid/"]) == 2
