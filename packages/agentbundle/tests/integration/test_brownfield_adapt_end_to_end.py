"""T11: class-1 substitution end-to-end against the brownfield fixture.

Load the `brownfield-adapt` fixture into a tmp working tree; write a
canonical `<repo>/.adapt-discovery.toml` with `[markers]`; invoke
`agentbundle adapt --values-from <repo>/.adapt-discovery.toml`; assert
the resulting tree matches `brownfield-adapt-expected/` byte-for-byte.

Then re-run the same command and assert idempotency (zero filesystem
diff on the second pass).
"""

from __future__ import annotations

import argparse
import shutil
from pathlib import Path

from agentbundle.commands import adapt
from agentbundle.config import PackState, State, dump_state
from agentbundle.safety import sha256_bytes


FIXTURES = Path(__file__).parent.parent / "fixtures"
BROWNFIELD = FIXTURES / "brownfield-adapt"
EXPECTED = FIXTURES / "brownfield-adapt-expected"


def _setup_brownfield(tmp_path: Path) -> Path:
    """Copy the brownfield fixture into tmp_path; seed a v0.2 state
    file recording the substitution-target files; return the working
    tree path."""
    work = tmp_path / "repo"
    shutil.copytree(BROWNFIELD, work)
    # Drop the EXPECTED_TREE.md doc — it's metadata, not part of the
    # adopter's working tree.
    (work / "EXPECTED_TREE.md").unlink()

    files = {}
    for rel in ("AGENTS.md", "docs/CHARTER.md"):
        data = (work / rel).read_bytes()
        files[rel] = {
            "sha": sha256_bytes(data),
            "from-pack-version": "0.1.0",
        }
    state = State()
    state.packs[("core", "claude-code")] = PackState(
        installed_version="0.1.0", files=files, adapter="claude-code"
    )
    (work / ".agentbundle-state.toml").write_text(
        dump_state(state), encoding="utf-8"
    )
    # Hand-write the canonical discovery file with [markers].
    (work / ".adapt-discovery.toml").write_text(
        'discovery-schema-version = "0.1"\n'
        "[markers]\n"
        'project-name = "myproject"\n'
        'owner = "octocat"\n'
        'repo-url = "https://example.com/myproject"\n',
        encoding="utf-8",
    )
    return work


def _assert_matches_expected(work: Path) -> None:
    for rel in ("AGENTS.md", "docs/CHARTER.md"):
        actual = (work / rel).read_bytes()
        expected = (EXPECTED / rel).read_bytes()
        assert actual == expected, (
            f"{rel}: post-adapt bytes differ from expected.\n"
            f"actual:   {actual!r}\n"
            f"expected: {expected!r}"
        )


def _ns(work: Path) -> argparse.Namespace:
    return argparse.Namespace(
        root=str(work),
        values_from=str(work / ".adapt-discovery.toml"),
        ci=False,
    )


def test_class_one_end_to_end(tmp_path):
    """`agentbundle adapt --values-from <repo>/.adapt-discovery.toml`
    substitutes every `<adapt:NAME>` in the projected tree."""
    work = _setup_brownfield(tmp_path)
    rc = adapt.run(_ns(work))
    assert rc == 0
    _assert_matches_expected(work)


def test_idempotent_re_run(tmp_path):
    """A second invocation against the fully-adapted tree produces
    zero filesystem changes (byte-identical files)."""
    work = _setup_brownfield(tmp_path)
    assert adapt.run(_ns(work)) == 0

    before = {
        p.relative_to(work).as_posix(): p.read_bytes()
        for p in work.rglob("*")
        if p.is_file()
    }
    assert adapt.run(_ns(work)) == 0
    after = {
        p.relative_to(work).as_posix(): p.read_bytes()
        for p in work.rglob("*")
        if p.is_file()
    }
    assert before == after, (
        "Re-run is not idempotent. Differing paths: "
        + ", ".join(sorted(set(before) ^ set(after))
                    + [k for k in before if k in after and before[k] != after[k]])
    )


def test_pending_report_byte_identical_with_multiple_companions(tmp_path):
    """AC10: `.adapt-pending.md` is byte-identical across re-runs and
    lists companion paths in lex order — load-bearing for the
    deterministic-sort contract, not the trivial one-element case.

    The fixture records three projected paths chosen so the lex sort
    of their companion relpaths is non-trivial:

      Projected paths:    AGENTS.md, docs/CHARTER.md, AAA-extra.md
      Companion lex sort: AAA-extra.upstream.md, AGENTS.upstream.md,
                          docs/CHARTER.upstream.md

    The byte-identity check pins the no-timestamp contract; the
    sequence-equals-sorted check pins lex ordering. Caveat:
    `State.projected_paths()` returns a `set[str]`, and `adapt.py`
    currently sorts at *two* sites (`_find_upstream_companions` and
    the report-write loop). Dropping *one* sort leaves the other to
    recover lex order, so this test is not load-bearing against a
    single-site regression. It is load-bearing against dropping
    *both* sites, where set iteration of `projected_paths()` (hash-
    dependent) takes over and almost always disagrees with lex order
    for three or more relpaths.
    """
    from agentbundle.config import PackState, State, dump_state
    from agentbundle.safety import companion_path, sha256_bytes

    work = tmp_path / "repo"
    work.mkdir()
    (work / "docs").mkdir()

    # Three projected files (original + companion each). The three
    # relpaths have a non-trivial lex sort (capital-A < capital-A-then-G
    # < lowercase-d).
    bodies = {
        "AGENTS.md": "# AGENTS\nbody\n",
        "docs/CHARTER.md": "# CHARTER\nbody\n",
        "AAA-extra.md": "# AAA extra\nbody\n",
    }
    files: dict = {}
    for rel, body in bodies.items():
        (work / rel).write_text(body, encoding="utf-8")
        comp_rel = companion_path(Path(rel)).as_posix()
        (work / comp_rel).parent.mkdir(parents=True, exist_ok=True)
        (work / comp_rel).write_text(
            f"upstream variant of {rel}\n", encoding="utf-8"
        )
        files[rel] = {
            "sha": sha256_bytes(body.encode("utf-8")),
            "from-pack-version": "0.1.0",
        }

    state = State()
    state.packs[("core", "claude-code")] = PackState(
        installed_version="0.1.0", files=files, adapter="claude-code"
    )
    (work / ".agentbundle-state.toml").write_text(
        dump_state(state), encoding="utf-8"
    )
    (work / ".adapt-discovery.toml").write_text(
        'discovery-schema-version = "0.1"\n[markers]\n', encoding="utf-8"
    )

    assert adapt.run(_ns(work)) == 0
    first = (work / ".adapt-pending.md").read_bytes()

    assert adapt.run(_ns(work)) == 0
    second = (work / ".adapt-pending.md").read_bytes()

    assert first == second, (
        "pending.md must be byte-identical across runs "
        "(deterministic sort, no timestamps); diff:\n"
        f"first:  {first!r}\nsecond: {second!r}"
    )

    # Parse the companion entries; assert the full sequence equals the
    # lex-sorted variant. With the deliberate insertion-vs-lex
    # inversion, this assertion fails on a dropped sort.
    text = first.decode("utf-8")
    listed = [
        line.split("`")[1]
        for line in text.splitlines()
        if line.startswith("- `")
    ]
    assert len(listed) == 3, (
        f"expected 3 companion entries; got {listed!r}\nreport:\n{text}"
    )
    assert listed == sorted(listed), (
        f"companion entries not in lex order — sort regression?\n"
        f"got:    {listed!r}\nsorted: {sorted(listed)!r}\n{text}"
    )
