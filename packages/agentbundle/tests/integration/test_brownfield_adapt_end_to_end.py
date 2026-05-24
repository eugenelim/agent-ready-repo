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
    state.packs["core"] = PackState(installed_version="0.1.0", files=files)
    (work / ".agent-ready-state.toml").write_text(
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
