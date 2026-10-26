"""The rename hint through the real CLI, on each catalogue shape.

Local path runs unpatched. The release archive is built here with
``agentbundle catalogue package`` and served from a local HTTPS server whose
throwaway certificate authority reaches the CLI through
``AGENTBUNDLE_CA_BUNDLE``. The git shape runs the real CLI with only the
network tarball download replaced by the same local tree. Every catalogue is
built under ``tmp_path``; nothing here reads this repository's tree.
"""

from __future__ import annotations

import json
import re
import shlex
import shutil
import socket
from collections.abc import Callable, Iterator
from dataclasses import dataclass
from pathlib import Path

import pytest
from agentbundle.catalogue import CatalogueError, resolve_catalogue
from agentbundle.cli import main
from agentbundle.config import canonicalize_source

from tests._rename_fixtures import (
    DEP,
    MAP_BREAKERS,
    OLD,
    post_rename_catalogue,
    pre_rename_catalogue,
)
from tests.integration._https_archive import ServedArchive, serve_archive

GIT_SOURCE = "git+https://github.com/example-org/example-repo"
RUN = "Run these steps to move to it:"
REFUSAL = (
    "{cmd}: the rename hint for 'governance-extras' is withheld because the "
    "catalogue source, target root or an installed adapter name cannot be "
    "printed safely."
)
SHAPES = ["local", "git", "archive"]


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def tree(root: Path) -> dict[str, bytes]:
    """Every file under *root* (state files included), keyed by relative path."""
    return {
        p.relative_to(root).as_posix(): p.read_bytes()
        for p in sorted(root.rglob("*"))
        if p.is_file()
    }


def copy_tree(src: Path, dst: Path) -> Path:
    shutil.copytree(src, dst, symlinks=True)
    return dst


def run_cli(capsys: pytest.CaptureFixture[str], *argv: str) -> tuple[int, str, str]:
    capsys.readouterr()
    code = main(list(argv))
    captured = capsys.readouterr()
    return code, captured.out, captured.err


def set_sources(repo: Path, sources: dict[str, str | None]) -> None:
    """Rewrite the recorded source of every adapter row of the named packs."""
    path = repo / ".agentbundle-state.toml"
    out: list[str] = []
    pack: str | None = None
    for line in path.read_text(encoding="utf-8").splitlines():
        header = re.match(r"\[pack\.([^.\]]+)\.adapters\.[^.\]]+\]$", line)
        if header:
            pack = header.group(1)
        elif line.startswith("["):
            pack = None
        if pack in sources and line.startswith("source = "):
            if sources[pack] is None:
                continue
            line = f"source = {json.dumps(sources[pack], ensure_ascii=False)}"
        out.append(line)
    path.write_text("\n".join(out) + "\n", encoding="utf-8")


def rename_adapter_row(repo: Path, pack: str, old: str, new: str) -> None:
    path = repo / ".agentbundle-state.toml"
    text = path.read_text(encoding="utf-8")
    for suffix in ("", ".files"):
        text = text.replace(
            f"[pack.{pack}.adapters.{old}{suffix}]",
            f"[pack.{pack}.adapters.{new}{suffix}]",
        )
    path.write_text(text, encoding="utf-8")


def hint_lines(
    command: str,
    source: str,
    *,
    root: str | None = None,
    old_adapters: tuple[str, ...] = ("claude-code",),
    dep_adapters: tuple[str, ...] = ("claude-code",),
) -> list[str]:
    """The hint for the fixture where both packs came from the reporting source."""
    q = shlex.quote
    root_text = {"--root": "", "--output": ""}
    if root is not None:
        root_text = {"--root": f" --root {q(root)}", "--output": f" --output {q(root)}"}
    src = q(source)
    lines = [
        f"{command}: pack 'governance-extras' was renamed to 'repo-governance'.",
        RUN,
    ]
    steps = []
    for adapter in old_adapters:
        flag = f" --adapter {adapter}" if len(old_adapters) > 1 else ""
        steps.append(
            f"agentbundle uninstall --pack governance-extras --scope repo{flag}"
            f"{root_text['--root']}"
        )
    for adapter in old_adapters:
        steps.append(
            "agentbundle install --pack repo-governance --scope repo "
            f"--adapter {adapter}{root_text['--output']} {src}"
        )
    for adapter in dep_adapters:
        flag = f" --adapter {adapter}" if len(dep_adapters) > 1 else ""
        steps.append(
            f"agentbundle upgrade --pack iac-terraform --scope repo{flag}"
            f"{root_text['--root']} {src}"
        )
    lines += [f"  {n}. {step}" for n, step in enumerate(steps, start=1)]
    return lines


def not_found(command: str, catalogue: str) -> str:
    return (
        f"{command}: pack 'governance-extras' not found in catalogue at "
        f"{resolve_catalogue(catalogue)}; expected packs/<pack>/ or "
        "<catalogue>/<pack>/\n"
    )


def multi_adapter_refusal(rows: dict[str, str]) -> str:
    rendered = ", ".join(f"{a} ({rows[a]})" for a in sorted(rows))
    return (
        "upgrade: governance-extras installed for multiple adapters at repo "
        f"scope; pass --adapter to pick one: {rendered}\n"
    )


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class Templates:
    pre: Path
    post: Path
    one: Path  # governance-extras + iac-terraform, claude-code only
    two: Path  # governance-extras on claude-code and cursor, iac on claude-code


def _install(repo: Path, pre: Path, pack: str, adapter: str) -> None:
    code = main([
        "install", "--pack", pack, "--scope", "repo", "--adapter", adapter,
        "--output", str(repo), "--yes", str(pre),
    ])
    assert code == 0


@pytest.fixture(scope="module")
def templates(tmp_path_factory: pytest.TempPathFactory) -> Templates:
    base = tmp_path_factory.mktemp("rename-templates")
    pre = pre_rename_catalogue(base / "pre")
    post = post_rename_catalogue(base / "post")
    one = base / "one"
    one.mkdir()
    _install(one, pre, OLD, "claude-code")
    _install(one, pre, DEP, "claude-code")
    two = base / "two"
    two.mkdir()
    _install(two, pre, OLD, "claude-code")
    _install(two, pre, OLD, "cursor")
    _install(two, pre, DEP, "claude-code")
    return Templates(pre, post, one, two)


@pytest.fixture(scope="module")
def post_archive(tmp_path_factory: pytest.TempPathFactory, templates: Templates) -> Path:
    base = tmp_path_factory.mktemp("rename-archive")
    cat = copy_tree(templates.post, base / "cat")
    out = base / "out"
    code = main([
        "catalogue", "package", "--root", str(cat), "--bundle", "demo",
        "--release", "0.1.0", "--channel", "stable", "--output", str(out),
    ])
    assert code == 0
    return out / "catalogues" / "demo" / "releases" / "0.1.0" / "catalogue-0.1.0.tar.gz"


@pytest.fixture(scope="module")
def served_post(
    tmp_path_factory: pytest.TempPathFactory, post_archive: Path
) -> Iterator[ServedArchive]:
    with serve_archive(post_archive, tmp_path_factory.mktemp("rename-server")) as served:
        yield served


@pytest.fixture
def repo(tmp_path: Path, templates: Templates) -> Path:
    return copy_tree(templates.one, tmp_path / "repo")


@pytest.fixture
def repo_two(tmp_path: Path, templates: Templates) -> Path:
    return copy_tree(templates.two, tmp_path / "repo2")


@pytest.fixture
def guard(monkeypatch: pytest.MonkeyPatch) -> Callable[[int | None], None]:
    """Fail the test on any network connect except to *allowed_port*."""
    allowed: list[int | None] = [None]
    real_connect = socket.socket.connect

    def connect(self: socket.socket, address: object) -> None:
        if isinstance(address, tuple) and address[1] == allowed[0]:
            return real_connect(self, address)  # type: ignore[arg-type]
        raise AssertionError(f"unexpected network connection to {address!r}")

    monkeypatch.setattr(socket.socket, "connect", connect)

    def allow(port: int | None) -> None:
        allowed[0] = port

    return allow


@dataclass(frozen=True)
class Shape:
    name: str
    source: str  # the catalogue argument the command is given
    served: ServedArchive | None = None


@pytest.fixture(params=SHAPES)
def shape(
    request: pytest.FixtureRequest,
    templates: Templates,
    served_post: ServedArchive,
    monkeypatch: pytest.MonkeyPatch,
    guard: Callable[[int | None], None],
    tmp_path: Path,
) -> Shape:
    if request.param == "local":
        return Shape("local", str(templates.post))
    if request.param == "git":
        import agentbundle.catalogue as catalogue_module

        def fake_fetch(url: str, dest: Path) -> None:
            shutil.copytree(templates.post, dest / "example-repo-main", symlinks=True)

        monkeypatch.setattr(catalogue_module, "_fetch_and_extract", fake_fetch)
        return Shape("git", GIT_SOURCE)
    monkeypatch.setenv("AGENTBUNDLE_CA_BUNDLE", str(served_post.ca_bundle))
    monkeypatch.setenv("NO_PROXY", "127.0.0.1")
    monkeypatch.setenv("no_proxy", "127.0.0.1")
    for var in ("HTTPS_PROXY", "https_proxy", "ALL_PROXY", "all_proxy"):
        monkeypatch.delenv(var, raising=False)
    guard(int(served_post.source.split(":")[2].split("/")[0]))
    return Shape("archive", served_post.source, served_post)


def reported_source(shape: Shape) -> str:
    """What the command reports: the raw catalogue argument."""
    return shape.source


# ---------------------------------------------------------------------------
# AC-0009, AC-0010, AC-0033: install --pack and upgrade --pack
# ---------------------------------------------------------------------------


@pytest.mark.parametrize("command", ["install", "upgrade"])
def test_pack_hint_on_every_shape(command, shape, repo, capsys):
    set_sources(repo, {OLD: shape.source, DEP: shape.source})
    before = tree(repo)
    fetched = len(shape.served.requests) if shape.served else 0
    if command == "install":
        argv = ["install", "--pack", OLD, "--scope", "repo", "--output", str(repo)]
    else:
        argv = ["upgrade", "--pack", OLD, "--scope", "repo", "--root", str(repo)]
    code, _out, err = run_cli(capsys, *argv, shape.source)
    # install passes no --adapter, so the old pack's own adapter rows decide.
    assert err.splitlines() == hint_lines(command, shape.source, root=str(repo))
    assert err.splitlines()[0] == (
        f"{command}: pack 'governance-extras' was renamed to 'repo-governance'."
    )
    assert code == 1
    assert tree(repo) == before
    if shape.served is not None:
        assert len(shape.served.requests) - fetched == 1  # the one resolve, none for the hint


def test_install_explicit_adapter_when_old_pack_not_installed(shape, tmp_path, capsys):
    empty = tmp_path / "empty"
    empty.mkdir()
    code, _out, err = run_cli(
        capsys, "install", "--pack", OLD, "--adapter", "cursor",
        "--output", str(empty), shape.source,
    )
    assert code == 1
    assert err.splitlines()[2:] == [
        "  1. agentbundle install --pack repo-governance --scope repo "
        f"--adapter cursor --output {shlex.quote(str(empty))} {shlex.quote(shape.source)}"
    ]
    assert tree(empty) == {}


def test_multi_adapter_upgrade_prints_hint_instead_of_refusal(shape, repo_two, capsys):
    set_sources(repo_two, {OLD: shape.source, DEP: shape.source})
    before = tree(repo_two)
    code, _out, err = run_cli(
        capsys, "upgrade", "--pack", OLD, "--root", str(repo_two), shape.source
    )
    assert code == 1
    assert err.splitlines() == hint_lines(
        "upgrade", shape.source, root=str(repo_two),
        old_adapters=("claude-code", "cursor"),
    )
    assert "pass --adapter" not in err
    assert tree(repo_two) == before


# ---------------------------------------------------------------------------
# AC-0034, AC-0035: the multi-adapter refusal stays byte-identical
# ---------------------------------------------------------------------------


def test_direct_row_refusal_resolves_no_catalogue(repo_two, templates, monkeypatch, guard, capsys):
    rows = repo_two / ".agentbundle-state.toml"
    text = rows.read_text(encoding="utf-8")
    marker = "[pack.governance-extras.adapters.cursor]\n"
    rows.write_text(
        text.replace(marker, marker + 'source-kind = "skill"\n', 1), encoding="utf-8"
    )
    import agentbundle.commands.upgrade as upgrade_module

    def boom(*_args: object, **_kwargs: object) -> None:
        raise AssertionError("catalogue resolved for a direct row")

    monkeypatch.setattr(upgrade_module, "resolve_catalogue", boom)
    monkeypatch.setattr(upgrade_module, "resolve_catalogue_uri", boom)
    before = tree(repo_two)
    code, _out, err = run_cli(
        capsys, "upgrade", "--pack", OLD, "--root", str(repo_two), str(templates.post)
    )
    assert code == 1
    assert err == (
        "upgrade: governance-extras installed for multiple adapters at repo "
        "scope; pass --adapter to pick one: claude-code (1.0.3), cursor (—)\n"
    )
    assert tree(repo_two) == before


def test_pack_present_in_catalogue_keeps_refusal(repo_two, templates, capsys, guard):
    code, _out, err = run_cli(
        capsys, "upgrade", "--pack", OLD, "--root", str(repo_two), str(templates.pre)
    )
    assert code == 1
    assert err == multi_adapter_refusal({"claude-code": "1.0.3", "cursor": "1.0.3"})


def test_failed_resolution_keeps_refusal(repo_two, tmp_path, capsys, guard):
    before = tree(repo_two)
    code, _out, err = run_cli(
        capsys, "upgrade", "--pack", OLD, "--root", str(repo_two),
        str(tmp_path / "does-not-exist"),
    )
    assert code == 1
    assert err == multi_adapter_refusal({"claude-code": "1.0.3", "cursor": "1.0.3"})
    assert tree(repo_two) == before


def test_failed_git_fetch_keeps_refusal(repo_two, monkeypatch, capsys, guard):
    import agentbundle.catalogue as catalogue_module

    def fail(url: str, dest: Path) -> None:
        raise CatalogueError("network down")

    monkeypatch.setattr(catalogue_module, "_fetch_and_extract", fail)
    code, _out, err = run_cli(
        capsys, "upgrade", "--pack", OLD, "--root", str(repo_two), GIT_SOURCE
    )
    assert code == 1
    assert err == multi_adapter_refusal({"claude-code": "1.0.3", "cursor": "1.0.3"})


def _break(name: str):
    def make(templates: Templates, tmp_path: Path) -> str:
        cat = copy_tree(templates.post, tmp_path / "broken")
        MAP_BREAKERS[name](cat, tmp_path)
        return str(cat)

    return make


@pytest.mark.parametrize("breaker", sorted(MAP_BREAKERS))
def test_every_map_fixture_keeps_multi_adapter_refusal(
    breaker, repo_two, templates, tmp_path, capsys, guard
):
    source = _break(breaker)(templates, tmp_path)
    before = tree(repo_two)
    code, _out, err = run_cli(
        capsys, "upgrade", "--pack", OLD, "--root", str(repo_two), source
    )
    assert code == 1
    assert err == multi_adapter_refusal({"claude-code": "1.0.3", "cursor": "1.0.3"})
    assert "Traceback" not in err
    assert tree(repo_two) == before


UNSAFE_NAMES = ["a‮b", "a​b", "a b", "a\u007fb"]


@pytest.mark.parametrize("fragment", UNSAFE_NAMES)
def test_unsafe_source_keeps_multi_adapter_refusal(
    fragment, repo_two, templates, tmp_path, capsys, guard
):
    source = copy_tree(templates.post, tmp_path / f"cat-{fragment}")
    code, _out, err = run_cli(
        capsys, "upgrade", "--pack", OLD, "--root", str(repo_two), str(source)
    )
    assert code == 1
    assert err == multi_adapter_refusal({"claude-code": "1.0.3", "cursor": "1.0.3"})


@pytest.mark.parametrize("root_name", ["-dash", "a\nb", "a‮b"])
def test_unsafe_target_root_keeps_multi_adapter_refusal(
    root_name, templates, tmp_path, monkeypatch, capsys, guard
):
    monkeypatch.chdir(tmp_path)
    repo = copy_tree(templates.two, tmp_path / root_name)
    code, _out, err = run_cli(
        capsys, "upgrade", "--pack", OLD, f"--root={root_name}", str(templates.post)
    )
    assert code == 1
    assert err == multi_adapter_refusal({"claude-code": "1.0.3", "cursor": "1.0.3"})
    assert tree(repo) == tree(templates.two)


@pytest.mark.parametrize("key", ["bogus", "-x"])
def test_bad_adapter_key_keeps_multi_adapter_refusal(
    key, repo_two, templates, capsys, guard
):
    rename_adapter_row(repo_two, OLD, "cursor", key)
    code, _out, err = run_cli(
        capsys, "upgrade", "--pack", OLD, "--root", str(repo_two), str(templates.post)
    )
    assert code == 1
    assert err == multi_adapter_refusal({"claude-code": "1.0.3", key: "1.0.3"})


def test_map_only_in_another_catalogue_prints_not_found_only(
    repo, templates, tmp_path, monkeypatch, capsys, guard
):
    """AC-0023: the recorded and default catalogues carry the map; the reporting one does not."""
    import agentbundle.source_defaults as source_defaults

    monkeypatch.setattr(
        source_defaults,
        "resolve_default_source",
        lambda explicit=None, **_kw: explicit or str(templates.post),
    )
    set_sources(repo, {OLD: str(templates.post), DEP: str(templates.post)})
    reporting = copy_tree(templates.post, tmp_path / "reporting")
    MAP_BREAKERS["missing-map"](reporting, tmp_path)
    before = tree(repo)
    for command, argv in (
        ("install", ["install", "--pack", OLD, "--output", str(repo)]),
        ("upgrade", ["upgrade", "--pack", OLD, "--root", str(repo)]),
    ):
        code, _out, err = run_cli(capsys, *argv, str(reporting))
        assert code == 1
        assert err == not_found(command, str(reporting))
    assert tree(repo) == before


# ---------------------------------------------------------------------------
# AC-0010, AC-0021, AC-0022, AC-0027 at the not-found points
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class NotFoundCase:
    catalogue: str
    repo: Path
    root_arg: str
    refusal: bool


def _case_unsafe_source(name: str):
    def make(templates: Templates, tmp_path: Path, repo: Path) -> NotFoundCase:
        cat = copy_tree(templates.post, tmp_path / name)
        return NotFoundCase(str(cat), repo, str(repo), True)

    return make


def _case_unsafe_root(name: str):
    def make(templates: Templates, tmp_path: Path, repo: Path) -> NotFoundCase:
        target = copy_tree(repo, tmp_path / "roots" / name)
        return NotFoundCase(str(templates.post), target, str(target), True)

    return make


def _case_map(breaker: str):
    def make(templates: Templates, tmp_path: Path, repo: Path) -> NotFoundCase:
        cat = copy_tree(templates.post, tmp_path / "broken")
        MAP_BREAKERS[breaker](cat, tmp_path)
        return NotFoundCase(str(cat), repo, str(repo), False)

    return make


CASES = {
    "unsafe-source-bidi": _case_unsafe_source("cat‮"),
    "unsafe-source-newline": _case_unsafe_source("cat\nx"),
    "unsafe-target-root-bidi": _case_unsafe_root("r‮"),
    "unsafe-target-root-newline": _case_unsafe_root("r\nx"),
    "invalid-map": _case_map("invalid-invalid-toml"),
    "symlinked-map": _case_map("symlinked-map" if "symlinked-map" in MAP_BREAKERS else "oversized"),
}


@pytest.mark.parametrize("case_id", sorted(CASES))
@pytest.mark.parametrize("command", ["install", "upgrade"])
def test_not_found_point_refusals(case_id, command, templates, repo, tmp_path, capsys, guard):
    case = CASES[case_id](templates, tmp_path, repo)
    before = tree(case.repo)
    if command == "install":
        argv = ["install", "--pack", OLD, "--output", case.root_arg]
    else:
        argv = ["upgrade", "--pack", OLD, "--root", case.root_arg]
    code, _out, err = run_cli(capsys, *argv, case.catalogue)
    expected = not_found(command, case.catalogue)
    if case.refusal:
        expected += REFUSAL.format(cmd=command) + "\n"
    assert code == 1
    assert err == expected
    assert "Traceback" not in err
    assert tree(case.repo) == before


@pytest.mark.parametrize("case_id", sorted(CASES))
def test_all_row_reports_pack_not_found_without_hint(
    case_id, templates, repo, tmp_path, capsys, guard
):
    if case_id.startswith("unsafe-target-root"):
        pytest.skip("upgrade --all passes no target root to the hint")
    case = CASES[case_id](templates, tmp_path, repo)
    set_sources(repo, {OLD: case.catalogue, DEP: case.catalogue})
    before = tree(repo)
    code, out, err = run_cli(
        capsys, "upgrade", "--all", "--scope", "repo", "--root", str(repo),
        "--format", "json", "--dry-run",
    )
    assert code == 1
    assert "Traceback" not in err
    rows = {r["pack"]: r for r in json.loads(out)["rows"]}
    assert rows[OLD]["status_reason"] == "pack-not-found"
    assert "rename_hint" not in rows[OLD]
    assert "renamed to" not in out + err
    assert tree(repo) == before


# ---------------------------------------------------------------------------
# AC-0011: upgrade --all
# ---------------------------------------------------------------------------


def test_all_table_carries_hint(shape, repo, capsys):
    set_sources(repo, {OLD: shape.source, DEP: shape.source})
    before = tree(repo)
    code, out, _err = run_cli(
        capsys, "upgrade", "--all", "--scope", "repo", "--root", str(repo)
    )
    assert code == 1
    expected = hint_lines("upgrade", canonicalize_source(shape.source) or "")
    for line in expected:
        assert f"  {line}" in out.splitlines()
    assert tree(repo) == before


def test_all_json_rename_hint_on_renamed_row_only(shape, repo, capsys):
    set_sources(repo, {OLD: shape.source, DEP: shape.source})
    before = tree(repo)
    code, out, _err = run_cli(
        capsys, "upgrade", "--all", "--scope", "repo", "--root", str(repo),
        "--format", "json", "--dry-run",
    )
    assert code == 1
    doc = json.loads(out)
    assert doc["schema_version"] == 1
    rows = {r["pack"]: r for r in doc["rows"]}
    assert rows[OLD]["rename_hint"] == hint_lines(
        "upgrade", canonicalize_source(shape.source) or ""
    )
    assert rows[OLD]["status_reason"] == "pack-not-found"
    assert "rename_hint" not in rows[DEP]
    assert rows[DEP]["outcome"] == "blocked"
    assert all(r["outcome"] == "blocked" for r in doc["rows"])
    assert tree(repo) == before


@pytest.mark.parametrize(
    "recorded",
    [
        "git+https://ghp_SECRETTOKEN@example.test/o/r",
        "git+https://user:pw0rdSECRET@example.test/o/r",
        "archive+https://example.test/a.tgz?sig=SECRETSIG#sha256=" + "0" * 64,
        "archive+https://example.test/a.tgz?a=1;token=SECRETTOK",
        "git+https://example.test/o/r?password=SECRETPW",
        "git+https://example.test/o/r#%74oken=SECRETFRAG",
        "git+https://TOKEN@example.test/o/r‮",
    ],
)
def test_all_json_never_prints_recorded_credentials(recorded, repo, templates, capsys, guard):
    set_sources(repo, {OLD: str(templates.post), DEP: recorded})
    code, out, _err = run_cli(
        capsys, "upgrade", "--all", "--scope", "repo", "--root", str(repo),
        "--format", "json", "--dry-run",
    )
    assert code == 1
    row = next(r for r in json.loads(out)["rows"] if r["pack"] == OLD)
    text = "\n".join(row["rename_hint"])
    assert "SECRET" not in text and "TOKEN" not in text.replace("token", "")
    assert "‮" not in text


# ---------------------------------------------------------------------------
# AC-0012: a pre-rename archive row upgrades as it does today
# ---------------------------------------------------------------------------


def test_pre_rename_archive_row_upgrades_without_hint(
    repo, tmp_path, monkeypatch, capsys, guard
):
    pre = pre_rename_catalogue(tmp_path / "pre-newer", version="1.0.4")
    out_dir = tmp_path / "pre-out"
    assert main([
        "catalogue", "package", "--root", str(pre), "--bundle", "demo",
        "--release", "0.1.0", "--channel", "stable", "--output", str(out_dir),
    ]) == 0
    archive = out_dir / "catalogues" / "demo" / "releases" / "0.1.0" / "catalogue-0.1.0.tar.gz"
    with serve_archive(archive, tmp_path / "server") as served:
        monkeypatch.setenv("AGENTBUNDLE_CA_BUNDLE", str(served.ca_bundle))
        monkeypatch.setenv("NO_PROXY", "127.0.0.1")
        monkeypatch.setenv("no_proxy", "127.0.0.1")
        for var in ("HTTPS_PROXY", "https_proxy", "ALL_PROXY", "all_proxy"):
            monkeypatch.delenv(var, raising=False)
        guard(int(served.source.split(":")[2].split("/")[0]))
        set_sources(repo, {OLD: served.source, DEP: served.source})
        code, out, err = run_cli(
            capsys, "upgrade", "--all", "--scope", "repo", "--root", str(repo), "--yes"
        )
    assert code == 0, (out, err)
    assert "renamed" not in out + err
    state = (repo / ".agentbundle-state.toml").read_text(encoding="utf-8")
    assert re.search(
        r"\[pack\.governance-extras\.adapters\.claude-code\]\ninstalled-version = \"1\.0\.4\"",
        state,
    )
