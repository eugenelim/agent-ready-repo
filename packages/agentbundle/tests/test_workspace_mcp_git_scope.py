"""`git_commit` stages the dispatched item's own files and nothing else.

The oracle here is the real tool. Every row builds a temporary git repository,
sets `WORKSPACE_MCP_DISPATCHED_ITEM`, and calls `_GitTools.git_commit`, then
reads back what git actually staged. A check written over a copy of the scope
grammar would agree with a wrong implementation, which is the whole reason this
suite drives subprocesses instead.

The defect it pins: a configured `output_dir` carrying a glob metacharacter
reached the staging scope, and `git_commit`'s grammar keys on the literal
sequence `/*`. A base of `docs/*` therefore collapsed the scope's static root to
`docs/` with an empty wildcard suffix, and the commit picked up every
uncommitted file under it — an adopter's configuration value widening what a
commit stages.

Two properties are asserted, and the second is the load-bearing one. The staged
set alone is a sampled oracle: it passes wherever the fixture happens to have no
file at the widened location. The structural invariant — for any accepted base
`B`, the resolved pattern is `B` followed by the built-in manifest pattern's own
tail, wildcards included — is decidable over a generated family of bases, which
is what makes "no configured value widens the scope" checkable rather than
sampled at one point.
"""

from __future__ import annotations

import os
import subprocess
from pathlib import Path

import pytest
from agentbundle.workspace_mcp import (
    _LAYOUT_TYPE_BASES,
    _LIFECYCLE_MANIFEST,
    _GitTools,
    _read_layout_bases,
    _read_raw_layout_output_dirs,
)

_SLUG = "alpha"
_INI = "ini-001"

# A file inside the repository that belongs to no item, expressed so it sits
# under `docs/` — the directory a `docs/*` base collapses the scope root to.
_UNRELATED = "docs/unrelated/other.md"

# The dispatched item's own output, as a tail below its type's convention base.
# Fixture data, not grammar: each one satisfies the built-in manifest's first
# pattern for that type (research's wildcard component must end in `-{slug}`).
_ITEM_FILE_TAIL: dict[str, str] = {
    "research": "/01-{slug}/notes.md",
    "shape": "/intents/{slug}.md",
    "strategy": "/shaping/{slug}/plan.md",
    "design": "/journeys/{slug}.md",
}

_PATTERNED_TYPES = tuple(_ITEM_FILE_TAIL)


def _git(root: Path, *args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        ["git", *args],
        cwd=str(root), check=True, capture_output=True, text=True, encoding="utf-8",
    )


def _seed_repo(root: Path) -> None:
    """A repository with one commit, so `HEAD` exists and commits succeed."""
    root.mkdir(parents=True, exist_ok=True)
    _git(root, "init", "-q", "-b", "main")
    _git(root, "config", "user.email", "scope@example.test")
    _git(root, "config", "user.name", "scope")
    _git(root, "config", "commit.gpgsign", "false")
    (root / "seed.txt").write_text("seed\n", encoding="utf-8")
    _git(root, "add", "seed.txt")
    _git(root, "commit", "-qm", "seed")


def _configure(root: Path, toml_key: str, raw: str) -> None:
    # Only the value needs escaping: a Windows absolute path carries backslashes,
    # which TOML reads as escape sequences inside a basic string.
    value = raw.replace("\\", "\\\\")
    (root / "agentbundle-layout.toml").write_text(
        f'[{toml_key}]\noutput_dir = "{value}"\n', encoding="utf-8"
    )


def _write(path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("x\n", encoding="utf-8")


def _resolved_base(repo: Path, raw: str) -> str:
    """The base as `_read_layout_bases` yields it: expanded, anchored, resolved."""
    return str((repo / Path(raw).expanduser()).resolve())


def _manifest_tails(item_type: str) -> list[str]:
    """Each built-in pattern with its convention base sliced off, wildcards intact."""
    _, convention = _LAYOUT_TYPE_BASES[item_type]
    tails: list[str] = []
    for pattern in _LIFECYCLE_MANIFEST[item_type]["output_pattern"]:
        assert pattern.startswith(convention + "/"), pattern
        tails.append(pattern[len(convention):])
    return tails


def _dispatch(monkeypatch: pytest.MonkeyPatch, item_type: str) -> None:
    monkeypatch.delenv("WORKSPACE_MCP_SPEC_PATH", raising=False)
    monkeypatch.setenv("WORKSPACE_MCP_DISPATCHED_ITEM", f"{_INI}/{item_type}:{_SLUG}")


def _staged(result: dict) -> list[str]:
    return sorted(result.get("committed", []))


# ── Accepted bases: a generated family, crossed with every patterned type ─────

# Each class names one way an adopter's value can differ in shape. None of them
# carries a reserved character, so all of them must keep working unchanged.
_ACCEPTED_BASES: dict[str, str] = {
    "single segment": "artifacts",
    "nested": "artifacts/product",
    "deep": "a/b/c/d/output",
    "dot underscore hyphen": "team.out_dir-1",
    "dot segments that normalise away": "artifacts/./nested/../nested",
}


def _accepted_case(
    repo: Path, monkeypatch: pytest.MonkeyPatch, item_type: str, raw_base: str | None
) -> tuple[dict, list[str]]:
    """Run one accepted-base row; return (the tool's own result, resolved patterns).

    The raw result, not a staged set: `_staged` turns every error shape into
    `[]`, so a row that asserts nothing was staged would also pass on a tool
    that failed for an unrelated reason.
    """
    _seed_repo(repo)
    if raw_base is None:
        base = str(repo.resolve() / _LAYOUT_TYPE_BASES[item_type][1])
    else:
        _configure(repo, _LAYOUT_TYPE_BASES[item_type][0], raw_base)
        base = _resolved_base(repo, raw_base)

    _write(Path(base + _ITEM_FILE_TAIL[item_type].format(slug=_SLUG)))
    _write(repo / _UNRELATED)

    _dispatch(monkeypatch, item_type)
    tools = _GitTools(repo)
    return tools.git_commit({"message": "scope"}), list(tools._output_pattern or [])


def _expected_staged(repo: Path, base: str, item_type: str) -> list[str]:
    """The item's own file, repository-relative — or nothing, when `base` is
    outside the repository and `git status` therefore never reports it."""
    item = Path(base + _ITEM_FILE_TAIL[item_type].format(slug=_SLUG)).resolve()
    if not item.is_relative_to(repo.resolve()):
        return []
    return [item.relative_to(repo.resolve()).as_posix()]


@pytest.mark.parametrize("item_type", _PATTERNED_TYPES)
def test_an_unconfigured_type_stages_only_its_own_file(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, item_type: str
) -> None:
    repo = tmp_path / "repo"
    result, patterns = _accepted_case(repo, monkeypatch, item_type, None)
    staged = _staged(result)

    convention = _LAYOUT_TYPE_BASES[item_type][1]
    assert staged == _expected_staged(repo, str(repo.resolve() / convention), item_type)
    assert _UNRELATED not in staged
    assert patterns == [
        (convention + tail).format(slug=_SLUG) for tail in _manifest_tails(item_type)
    ]


@pytest.mark.parametrize("item_type", _PATTERNED_TYPES)
@pytest.mark.parametrize("shape", sorted(_ACCEPTED_BASES), ids=lambda s: s.replace(" ", "-"))
def test_an_accepted_base_keeps_the_manifest_wildcard_structure(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, item_type: str, shape: str
) -> None:
    repo = tmp_path / "repo"
    raw_base = _ACCEPTED_BASES[shape]
    result, patterns = _accepted_case(repo, monkeypatch, item_type, raw_base)
    staged = _staged(result)
    base = _resolved_base(repo, raw_base)

    assert staged == _expected_staged(repo, base, item_type)
    assert _UNRELATED not in staged
    # The static root is the configured base followed by the manifest pattern's
    # own literal tail, and every wildcard component comes from the manifest.
    assert patterns == [base + tail.format(slug=_SLUG) for tail in _manifest_tails(item_type)]


@pytest.mark.parametrize("item_type", _PATTERNED_TYPES)
def test_an_absolute_base_inside_the_repository_is_accepted(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, item_type: str
) -> None:
    repo = tmp_path / "repo"
    raw_base = str((tmp_path / "repo" / "inside" / "base").resolve())
    result, patterns = _accepted_case(repo, monkeypatch, item_type, raw_base)
    staged = _staged(result)
    base = _resolved_base(repo, raw_base)

    assert staged == _expected_staged(repo, base, item_type)
    assert _UNRELATED not in staged
    assert patterns == [base + tail.format(slug=_SLUG) for tail in _manifest_tails(item_type)]


@pytest.mark.parametrize("item_type", _PATTERNED_TYPES)
def test_an_absolute_base_outside_the_repository_stages_nothing_and_leaks_nothing(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, item_type: str
) -> None:
    """A user-scope value is legitimately outside the repository. `git_commit`
    matches only paths `git status` reports, all of them repository-relative, so
    the scope names a location git never lists — it stages nothing, and above
    all it does not fall back to anything inside the repository."""
    repo = tmp_path / "repo"
    raw_base = str((tmp_path / "vault" / "base").resolve())
    result, patterns = _accepted_case(repo, monkeypatch, item_type, raw_base)
    base = _resolved_base(repo, raw_base)

    assert result == {
        "error": "no uncommitted files match the dispatched item's output_pattern"
    }
    assert patterns == [base + tail.format(slug=_SLUG) for tail in _manifest_tails(item_type)]


# ── Reserved characters: none of them may widen the staged set ───────────────

# One base per reserved character, isolating it so no row can pass on another
# character's account. `docs/*` is the measured leak; the other four reach
# neither the staging grammar nor slug formatting in a way that widens scope,
# and are reserved so the rule stays one an adopter can hold.
_RESERVED_BASES: dict[str, str] = {
    "*": "docs/*",
    "?": "docs/produc?",
    "[": "docs/produc[t",
    "{": "docs/produc{t",
    "}": "docs/produc}t",
}


@pytest.mark.parametrize("character", sorted(_RESERVED_BASES))
@pytest.mark.parametrize("item_type", _PATTERNED_TYPES)
def test_a_reserved_character_never_widens_the_staged_set(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, item_type: str, character: str
) -> None:
    repo = tmp_path / "repo"
    _seed_repo(repo)
    _configure(repo, _LAYOUT_TYPE_BASES[item_type][0], _RESERVED_BASES[character])
    _write(repo / "docs" / "product" / "shaping" / _SLUG / "own.md")
    _write(repo / _UNRELATED)

    _dispatch(monkeypatch, item_type)
    staged = _staged(_GitTools(repo).git_commit({"message": "scope"}))

    assert _UNRELATED not in staged, (
        f"a configured base carrying {character!r} staged a file outside the "
        f"dispatched item's own output: {staged}"
    )


def _head(root: Path) -> str:
    return _git(root, "rev-parse", "HEAD").stdout.strip()


@pytest.mark.parametrize("character", sorted(_RESERVED_BASES))
@pytest.mark.parametrize("item_type", _PATTERNED_TYPES)
def test_a_reserved_character_is_refused_and_leaves_the_repository_alone(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
    item_type: str,
    character: str,
) -> None:
    """The refusal is the whole behaviour: an error the caller can act on, a
    warning on the channel that is not the MCP protocol channel, and a
    repository in exactly the state it was in before the call."""
    repo = tmp_path / "repo"
    _seed_repo(repo)
    section = _LAYOUT_TYPE_BASES[item_type][0]
    _configure(repo, section, _RESERVED_BASES[character])
    _write(repo / "docs" / "product" / "shaping" / _SLUG / "own.md")
    _write(repo / _UNRELATED)
    before = _head(repo)

    _dispatch(monkeypatch, item_type)
    result = _GitTools(repo).git_commit({"message": "scope"})
    captured = capsys.readouterr()

    assert "committed" not in result
    assert f"[{section}]" in result["error"]
    assert "output_dir" in result["error"]
    assert f"[{section}]" in captured.err
    assert captured.out == "", "a diagnostic must not reach the MCP protocol channel"
    assert _head(repo) == before
    assert _git(repo, "diff", "--cached", "--name-only").stdout == ""


# The three types whose pattern's static prefix already contains `{slug}`, so
# their wildcard component carries an empty literal suffix. That shape is
# correct, and the refusal must not reach it.
_SLUG_PREFIXED_TYPES = ("shape", "strategy", "design")

_DEEP_FILE_TAIL: dict[str, str] = {
    "shape": "/shaping/{slug}/one/two/three/note.md",
    "strategy": "/shaping/{slug}/one/two/three/note.md",
    "design": "/screens/{slug}/one/two/three/note.md",
}


@pytest.mark.parametrize("item_type", _SLUG_PREFIXED_TYPES)
@pytest.mark.parametrize("raw_base", [None, "artifacts/product"])
def test_a_deep_file_under_a_slug_bearing_prefix_is_still_staged(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, item_type: str, raw_base: str | None
) -> None:
    repo = tmp_path / "repo"
    _seed_repo(repo)
    if raw_base is None:
        base = str(repo.resolve() / _LAYOUT_TYPE_BASES[item_type][1])
    else:
        _configure(repo, _LAYOUT_TYPE_BASES[item_type][0], raw_base)
        base = _resolved_base(repo, raw_base)

    deep = Path(base + _DEEP_FILE_TAIL[item_type].format(slug=_SLUG))
    _write(deep)
    _write(repo / _UNRELATED)

    _dispatch(monkeypatch, item_type)
    staged = _staged(_GitTools(repo).git_commit({"message": "deep"}))

    assert staged == [deep.resolve().relative_to(repo.resolve()).as_posix()]


def _sibling_results(
    repo: Path, monkeypatch: pytest.MonkeyPatch, item_type: str, raw_base: str | None
) -> tuple[dict, dict]:
    """`git_branch` and `git_push` results for one configuration."""
    _seed_repo(repo)
    origin = repo.parent / "origin.git"
    subprocess.run(
        ["git", "init", "--bare", "-q", str(origin)],
        check=True, capture_output=True, text=True,
    )
    _git(repo, "remote", "add", "origin", str(origin))
    if raw_base is not None:
        _configure(repo, _LAYOUT_TYPE_BASES[item_type][0], raw_base)

    _dispatch(monkeypatch, item_type)
    tools = _GitTools(repo)
    branch = f"{_INI}/{item_type}/{_SLUG}"
    return tools.git_branch({"name": branch}), tools.git_push({"branch": branch})


@pytest.mark.parametrize("character", sorted(_RESERVED_BASES))
@pytest.mark.parametrize("item_type", _PATTERNED_TYPES)
def test_a_refused_base_leaves_the_sibling_git_tools_working(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, item_type: str, character: str
) -> None:
    """Only `git_commit` loses its scope. Representing the refusal by clearing
    the dispatched item would engage discovery mode and answer `git_branch` and
    `git_push` with the generic discovery error instead."""
    refused = _sibling_results(
        tmp_path / "refused" / "repo", monkeypatch, item_type, _RESERVED_BASES[character]
    )
    unconfigured = _sibling_results(
        tmp_path / "unconfigured" / "repo", monkeypatch, item_type, None
    )

    assert refused == unconfigured
    assert refused[0] == {"branch": f"{_INI}/{item_type}/{_SLUG}"}
    assert refused[1] == {"pushed": f"{_INI}/{item_type}/{_SLUG}"}


# ── The screen reads the configured value, not the resolved one ──────────────

def test_a_reserved_character_normalised_away_by_resolution_is_still_refused(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """AC-0002 is about the value the adopter configured. `scratch*/../artifacts`
    contains `*` and resolves to `artifacts`, so a screen over the resolved base
    reads a path the adopter never wrote and lets this one through."""
    repo = tmp_path / "repo"
    _seed_repo(repo)
    _configure(repo, "product", "scratch*/../artifacts")
    _write(repo / _UNRELATED)

    _dispatch(monkeypatch, "shape")
    tools = _GitTools(repo)

    assert tools._refused_layout_key == "product"
    assert "[product]" in tools.git_commit({"message": "scope"})["error"]


@pytest.mark.skipif(os.name == "nt", reason="`*` is not a legal Windows filename")
def test_a_clean_base_is_accepted_under_a_repository_path_carrying_a_reserved_character(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """The mirror of the case above, and the reason the screen cannot simply be
    moved earlier without being narrowed to the adopter's own value: resolution
    splices in the repository's location, so a repository directory named
    `pro*ject` would refuse every configured base under it."""
    repo = tmp_path / "pro*ject" / "repo"
    _seed_repo(repo)
    _configure(repo, "product", "artifacts")
    base = _resolved_base(repo, "artifacts")
    _write(Path(base + _ITEM_FILE_TAIL["shape"].format(slug=_SLUG)))
    _write(repo / _UNRELATED)

    _dispatch(monkeypatch, "shape")
    tools = _GitTools(repo)
    staged = _staged(tools.git_commit({"message": "scope"}))

    assert tools._refused_layout_key is None
    assert staged == _expected_staged(repo, base, "shape")
    assert _UNRELATED not in staged


def _write_layout(path: Path, layout: dict[str, str]) -> None:
    """Write a layout file. A value already carrying a TOML bracket or brace is
    emitted unquoted, so a row can configure an array or an inline table — the
    shapes `Path(raw)` refuses and a quoted-string-only matrix can never reach.
    """
    path.parent.mkdir(parents=True, exist_ok=True)
    lines = []
    for key, value in layout.items():
        literal = (
            value
            if value.startswith(("[", "{"))
            else '"' + value.replace("\\", "\\\\") + '"'
        )
        lines.append(f"[{key}]\noutput_dir = {literal}\n")
    path.write_text("".join(lines), encoding="utf-8")


# `both-scopes` is the load-bearing row. Every other case configures one file,
# so a precedence flip in the raw reader would still agree with the shared one —
# the property the whole test exists for would go unchecked. Here the two scopes
# disagree on every key, so whichever one each key must prefer is decided.
_AGREEMENT_LAYOUTS: dict[str, tuple[dict[str, str], dict[str, str]]] = {
    "nothing-configured": ({}, {}),
    "one-key": ({"product": "artifacts"}, {}),
    "every-key": ({"research": "r/one", "product": "p/two", "design": "d/three"}, {}),
    "dot-segments": ({"product": "./a/../artifacts"}, {}),
    "reserved-character": ({"research": "vault*/../notes"}, {}),
    "user-scope-only": ({}, {"research": "USER", "product": "USER", "design": "USER"}),
    "both-scopes": (
        {"research": "repo/r", "product": "repo/p", "design": "repo/d"},
        {"research": "USER", "product": "USER", "design": "USER"},
    ),
    # A value `Path(raw)` cannot take. The shared reader drops it and falls back
    # to the other scope; a raw reader that keeps it would disagree, and the
    # disagreement is what the screen refuses on.
    "container-typed-preferred-value": (
        {"product": '["x"]'},
        {"product": "USER"},
    ),
}


@pytest.mark.parametrize("shape", sorted(_AGREEMENT_LAYOUTS))
def test_the_raw_reader_and_the_resolved_reader_agree(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, shape: str
) -> None:
    """`_read_raw_layout_output_dirs` reproduces `_read_layout_bases`'s per-key
    precedence because it may not share it — the shared reader is one the spec
    forbids modifying. Duplicated precedence drifts silently, so this pins the
    two to one answer: every key one returns, the other returns, and resolving
    the raw value reproduces the resolved one exactly.

    A user-scope value must be absolute to count at all, so the `USER` marker
    below stands for an absolute path under this test's own home.
    """
    repo = tmp_path / "repo"
    repo.mkdir(parents=True)
    home = tmp_path / "home"
    repo_layout, user_layout = _AGREEMENT_LAYOUTS[shape]
    user_layout = {
        key: str((home / "vault" / key).resolve()) if value == "USER" else value
        for key, value in user_layout.items()
    }
    if repo_layout:
        _write_layout(repo / "agentbundle-layout.toml", repo_layout)
    if user_layout:
        _write_layout(home / ".agentbundle" / "agentbundle-layout.toml", user_layout)
    monkeypatch.setenv("HOME", str(home))
    monkeypatch.setenv("USERPROFILE", str(home))

    raw = _read_raw_layout_output_dirs(repo)
    resolved = _read_layout_bases(repo)

    if shape == "container-typed-preferred-value":
        # The two readers disagree here by construction, which is the point: the
        # screen refuses on the disagreement rather than trusting either answer.
        assert raw["product"] == ["x"]
        assert resolved["product"] == _resolved_base(repo, user_layout["product"])
        return

    assert set(raw) == set(resolved)
    assert {key: _resolved_base(repo, value) for key, value in raw.items()} == resolved
    if shape == "both-scopes":
        # research takes the user-scope value; product and design take the repo's.
        assert raw["research"] == user_layout["research"]
        assert raw["product"] == repo_layout["product"]
        assert raw["design"] == repo_layout["design"]


def test_the_raw_reader_drops_a_user_scope_relative_value_like_the_shared_reader(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """A user-scope relative value never reaches a staging scope, so screening it
    would refuse a session over a value that does not apply to it."""
    repo = tmp_path / "repo"
    repo.mkdir(parents=True)
    home = tmp_path / "home"
    (home / ".agentbundle").mkdir(parents=True)
    (home / ".agentbundle" / "agentbundle-layout.toml").write_text(
        '[research]\noutput_dir = "relative*/vault"\n', encoding="utf-8"
    )
    monkeypatch.setenv("HOME", str(home))
    monkeypatch.setenv("USERPROFILE", str(home))

    assert _read_raw_layout_output_dirs(repo) == {}
    assert _read_layout_bases(repo) == {}


def test_a_container_typed_value_cannot_smuggle_a_reserved_base_past_the_screen(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """The shape that reopened this defect once. A repository-scope `output_dir`
    of `["x"]` is kept by the raw reader and dropped by the shared one, whose
    `Path(raw)` raises into a suppressed block, so the user-scope value wins.
    The screen then ran `"*" in ["x"]` — element equality, not a substring test —
    answered `False`, and spliced a `*`-bearing base into the staging scope.

    The refusal now keys on the two readers disagreeing at all, so this passes
    without anyone having enumerated container types as a case.
    """
    repo = tmp_path / "repo"
    _seed_repo(repo)
    home = tmp_path / "home"
    _write_layout(repo / "agentbundle-layout.toml", {"product": '["x"]'})
    _write_layout(
        home / ".agentbundle" / "agentbundle-layout.toml",
        {"product": str((repo / "docs" / "*").resolve())},
    )
    monkeypatch.setenv("HOME", str(home))
    monkeypatch.setenv("USERPROFILE", str(home))
    _write(repo / "docs" / "product" / "shaping" / _SLUG / "own.md")
    _write(repo / _UNRELATED)
    before = _head(repo)

    _dispatch(monkeypatch, "shape")
    tools = _GitTools(repo)
    result = tools.git_commit({"message": "scope"})

    assert tools._refused_layout_key == "product"
    assert "[product]" in result["error"]
    assert "committed" not in result
    assert _head(repo) == before
    assert _git(repo, "diff", "--cached", "--name-only").stdout == ""
