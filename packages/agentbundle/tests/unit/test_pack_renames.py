"""Unit tests for the rename hint builder."""

from __future__ import annotations

import os
import re
import shlex
import shutil
import subprocess
import sys
from pathlib import Path

import pytest
from agentbundle.config import canonicalize_source
from agentbundle.pack_renames import (
    CREDENTIAL_SENTENCE,
    PLACEHOLDER,
    PLACEHOLDER_SENTENCE,
    Installed,
    RenameHint,
    build_rename_hint,
)

from tests._rename_fixtures import (
    BAD_MAPS,
    DEP,
    DEP_TOML,
    GOOD_MAP,
    NEW,
    OLD,
    PLAIN_TOML,
    REPORTING,
    SKIP_NO_LINKS,
    catalogue,
)


def make_catalogue(
    tmp_path: Path, *, renames: list[tuple[str, str]], packs: list[str]
) -> Path:
    cat = tmp_path / "cat"
    (cat / "contracts" / "renames").mkdir(parents=True)
    body = "schema = 1\n" + "".join(
        f'\n[[rename]]\nfrom = "{a}"\nto = "{b}"\n' for a, b in renames
    )
    (cat / "contracts" / "renames" / "pack-renames.toml").write_text(
        body, encoding="utf-8"
    )
    for name in packs:
        (cat / "packs" / name).mkdir(parents=True)
        (cat / "packs" / name / "pack.toml").write_text(
            f'[pack]\nname = "{name}"\n', encoding="utf-8"
        )
    return cat


def test_hint_names_new_pack(tmp_path):
    cat = make_catalogue(tmp_path, renames=[("governance-extras", "repo-governance")], packs=["repo-governance"])
    hint = build_rename_hint("governance-extras", catalogue_dir=cat, source=str(cat), installed=Installed.empty(), command="install")
    assert hint.lines[0] == "install: pack 'governance-extras' was renamed to 'repo-governance'."


# ---------------------------------------------------------------------------
# Fixtures and helpers (everything is built under tmp_path)
# ---------------------------------------------------------------------------

def inst(rows: dict[tuple[str, str], str | None] | None = None) -> Installed:
    return Installed(dict(rows or {}))


def hint(cat: Path, installed: Installed | None = None, **kw) -> RenameHint:
    kw.setdefault("source", REPORTING)
    kw.setdefault("command", "install")
    return build_rename_hint(
        OLD, catalogue_dir=cat, installed=installed or inst(), **kw
    )


def steps_of(result: RenameHint) -> list[str]:
    return [ln.split(". ", 1)[1] for ln in result.lines if re.match(r"  \d+\. ", ln)]


REFUSAL = (
    "{cmd}: the rename hint for 'governance-extras' is withheld because the "
    "catalogue source, target root or an installed adapter name cannot be "
    "printed safely."
)
HEAD = "install: pack 'governance-extras' was renamed to 'repo-governance'."
RUN = "Run these steps to move to it:"
SRC = shlex.quote(REPORTING)


def both_installed() -> Installed:
    return inst(
        {(OLD, "claude-code"): REPORTING, (DEP, "claude-code"): REPORTING}
    )


# ---------------------------------------------------------------------------
# AC-0013, AC-0014, AC-0015: the steps
# ---------------------------------------------------------------------------


def test_full_layout_one_adapter(tmp_path):
    cat = catalogue(tmp_path, packs={DEP: DEP_TOML})
    result = hint(cat, both_installed(), command="upgrade")
    assert result.lines == (
        "upgrade: pack 'governance-extras' was renamed to 'repo-governance'.",
        RUN,
        "  1. agentbundle uninstall --pack governance-extras --scope repo",
        f"  2. agentbundle install --pack repo-governance --scope repo --adapter claude-code {SRC}",
        f"  3. agentbundle upgrade --pack iac-terraform --scope repo {SRC}",
    )
    assert result.refusal is None


def test_old_pack_not_installed_has_no_uninstall_and_one_install(tmp_path):
    cat = catalogue(tmp_path)
    assert steps_of(hint(cat)) == [
        f"agentbundle install --pack repo-governance --scope repo {SRC}"
    ]


def test_not_installed_with_explicit_install_adapter(tmp_path):
    cat = catalogue(tmp_path)
    assert steps_of(hint(cat, explicit_adapter="cursor")) == [
        f"agentbundle install --pack repo-governance --scope repo --adapter cursor {SRC}"
    ]


def test_non_default_adapter_carried(tmp_path):
    cat = catalogue(tmp_path)
    steps = steps_of(hint(cat, inst({(OLD, "cursor"): REPORTING})))
    assert steps[1] == (
        f"agentbundle install --pack repo-governance --scope repo --adapter cursor {SRC}"
    )


def test_two_old_adapter_rows(tmp_path):
    cat = catalogue(tmp_path)
    rows = {(OLD, "cursor"): REPORTING, (OLD, "claude-code"): REPORTING}
    assert steps_of(hint(cat, inst(rows))) == [
        "agentbundle uninstall --pack governance-extras --scope repo --adapter claude-code",
        "agentbundle uninstall --pack governance-extras --scope repo --adapter cursor",
        f"agentbundle install --pack repo-governance --scope repo --adapter claude-code {SRC}",
        f"agentbundle install --pack repo-governance --scope repo --adapter cursor {SRC}",
    ]


@pytest.mark.parametrize("n_deps", [0, 1, 2])
def test_dependent_counts(tmp_path, n_deps):
    names = ["iac-terraform", "other-dep"][:n_deps]
    cat = catalogue(tmp_path, packs=dict.fromkeys(names, DEP_TOML))
    rows = {(n, "claude-code"): REPORTING for n in names}
    steps = steps_of(hint(cat, inst(rows)))
    assert steps == [
        f"agentbundle install --pack repo-governance --scope repo {SRC}",
        *[
            f"agentbundle upgrade --pack {n} --scope repo {SRC}"
            for n in sorted(names)
        ],
    ]


def test_dependent_two_adapters_carry_adapter(tmp_path):
    cat = catalogue(tmp_path, packs={DEP: DEP_TOML})
    rows = {(DEP, "cursor"): REPORTING, (DEP, "claude-code"): REPORTING}
    assert steps_of(hint(cat, inst(rows)))[1:] == [
        f"agentbundle upgrade --pack iac-terraform --scope repo --adapter claude-code {SRC}",
        f"agentbundle upgrade --pack iac-terraform --scope repo --adapter cursor {SRC}",
    ]


def test_dependent_at_catalogue_root_layout(tmp_path):
    cat = catalogue(tmp_path, packs={DEP: DEP_TOML}, root_layout=(DEP,))
    rows = {(DEP, "claude-code"): REPORTING}
    assert steps_of(hint(cat, inst(rows)))[1] == (
        f"agentbundle upgrade --pack iac-terraform --scope repo {SRC}"
    )


def test_root_and_output_in_fixed_word_order(tmp_path):
    cat = catalogue(tmp_path, packs={DEP: DEP_TOML})
    result = hint(cat, both_installed(), target_root="/work/repo")
    assert steps_of(result) == [
        "agentbundle uninstall --pack governance-extras --scope repo --root /work/repo",
        f"agentbundle install --pack repo-governance --scope repo --adapter claude-code --output /work/repo {SRC}",
        f"agentbundle upgrade --pack iac-terraform --scope repo --root /work/repo {SRC}",
    ]


# ---------------------------------------------------------------------------
# AC-0020: shell-quoting
# ---------------------------------------------------------------------------

WEIRD = [
    "/tmp/my catalogue",
    "/tmp/it's here",
    "/tmp/a$HOME",
    "/tmp/a;b",
    "/tmp/a`b`",
    'file:///tmp/a "q"',
]


@pytest.mark.parametrize("weird", WEIRD)
def test_sources_round_trip_through_shlex(tmp_path, weird):
    cat = catalogue(tmp_path, packs={DEP: DEP_TOML})
    result = hint(cat, both_installed(), source=weird, target_root=weird)
    for step in steps_of(result):
        words = shlex.split(step)
        if words[1] == "install":
            assert words[-3:] == ["--output", weird, weird]
        elif words[1] == "upgrade":
            assert words[-3:] == ["--root", weird, weird]
        else:
            assert words[-2:] == ["--root", weird]


@pytest.mark.parametrize("root", ["/tmp/a b", "/tmp/$HOME/x"])
def test_target_root_with_space_and_dollar(tmp_path, root):
    cat = catalogue(tmp_path)
    step = steps_of(hint(cat, target_root=root))[0]
    assert shlex.split(step)[-3:-1] == ["--output", root]


# ---------------------------------------------------------------------------
# AC-0014, AC-0018, AC-0019: source rendering
# ---------------------------------------------------------------------------

DIGEST = "sha256=" + "a" * 64
ARCHIVE = "archive+https://example.test/r.tar.gz"


def test_archive_digest_fragment_is_printed(tmp_path):
    cat = catalogue(tmp_path)
    src = f"{ARCHIVE}#{DIGEST}"
    result = hint(cat, source=src)
    assert steps_of(result) == [
        f"agentbundle install --pack repo-governance --scope repo {shlex.quote(src)}"
    ]
    assert PLACEHOLDER_SENTENCE not in result.lines
    assert CREDENTIAL_SENTENCE not in result.lines


@pytest.mark.parametrize(
    "src",
    [
        f"{ARCHIVE}#{DIGEST}&x=1",
        f"{ARCHIVE}#{DIGEST.upper()}",
        f"{ARCHIVE}#sha256=" + "a" * 63,
        f"{ARCHIVE}#",
        f"git+https://example.test/r#{DIGEST}",
    ],
)
def test_other_fragments_use_placeholder(tmp_path, src):
    cat = catalogue(tmp_path)
    result = hint(cat, source=src)
    assert steps_of(result) == [
        f"agentbundle install --pack repo-governance --scope repo {PLACEHOLDER}"
    ]


def test_placeholder_sentence_is_pinned_and_sits_above_step(tmp_path):
    cat = catalogue(tmp_path)
    result = hint(cat, source=f"{ARCHIVE}?x=1")
    assert PLACEHOLDER_SENTENCE == (
        "Edit this step to name a catalogue source before running it; leaving "
        "the source out sends this step to a different catalogue."
    )
    assert result.lines[-2] == PLACEHOLDER_SENTENCE
    assert result.lines[-1].startswith("  1. ")


CRED_SOURCES = [
    "archive+https://tok3n@example.test/r.tar.gz",
    "archive+https://user:pa55word@example.test/r.tar.gz",
    f"{ARCHIVE}?password=pa55",
    f"{ARCHIVE}?secret=s3",
    f"{ARCHIVE}?sig=s1g",
    f"{ARCHIVE}?md5=m5",
    f"{ARCHIVE}?verify=v3",
    f"{ARCHIVE}?Policy=p0l",
    f"{ARCHIVE}?barequerysegment",
    f"{ARCHIVE}?a=1;token=t0k",
    f"{ARCHIVE}?%74oken=t0k",
    f"{ARCHIVE}#%74oken=t0k",
    f"{ARCHIVE}?TOKEN=t0k",
    f"{ARCHIVE}#token=t0k",
]
SECRETS = ["tok3n", "pa55word", "pa55", "s3", "s1g", "m5", "v3", "p0l", "t0k", "barequerysegment"]


@pytest.mark.parametrize("src", CRED_SOURCES)
def test_credential_reporting_source_never_printed(tmp_path, src):
    cat = catalogue(tmp_path, packs={DEP: DEP_TOML})
    rows = {(OLD, "claude-code"): None, (DEP, "claude-code"): None}
    result = hint(cat, inst(rows), source=src)
    text = "\n".join(result.lines)
    assert "example.test" not in text
    for secret in SECRETS:
        assert secret not in text.replace("sha256", "")
    assert steps_of(result)[-1].endswith(PLACEHOLDER)


@pytest.mark.parametrize("src", CRED_SOURCES)
def test_credential_recorded_source_never_printed(tmp_path, src):
    cat = catalogue(tmp_path, packs={DEP: DEP_TOML})
    rows = {(OLD, "claude-code"): src, (DEP, "claude-code"): src}
    result = hint(cat, inst(rows))
    text = "\n".join(result.lines)
    for secret in SECRETS:
        assert secret not in text
    assert "move between catalogues" in text
    assert "archive+https://example.test/r.tar.gz" in text


def test_credential_with_u202e_is_refused_not_printed(tmp_path):
    cat = catalogue(tmp_path)
    result = hint(cat, source="archive+https://tok@example.test/‮")
    assert result.lines == ()
    assert result.refusal == REFUSAL.format(cmd="install")


def test_recorded_credential_with_u202e_is_escaped(tmp_path):
    cat = catalogue(tmp_path)
    src = "archive+https://tok3n@example.test/a‮b?token=t0k"
    text = "\n".join(hint(cat, inst({(OLD, "claude-code"): src})).lines)
    assert "‮" not in text and "tok3n" not in text and "t0k" not in text
    assert "https://example.test/a\\u202eb" in text


def test_credential_sentence_when_bearing(tmp_path):
    cat = catalogue(tmp_path)
    result = hint(cat, source=f"{ARCHIVE}?token=x")
    assert result.lines[2] == CREDENTIAL_SENTENCE
    assert "cannot record" in CREDENTIAL_SENTENCE
    assert "keeps its old recorded source" in CREDENTIAL_SENTENCE


def test_non_credential_unprintable_source_has_no_credential_sentence(tmp_path):
    cat = catalogue(tmp_path)
    assert CREDENTIAL_SENTENCE not in hint(cat, source=f"{ARCHIVE}?page=2").lines


def test_local_path_and_file_uri_are_printed(tmp_path):
    cat = catalogue(tmp_path)
    for src in (str(cat), cat.as_uri()):
        assert steps_of(hint(cat, source=src)) == [
            "agentbundle install --pack repo-governance --scope repo "
            + shlex.quote(src)
        ]


# ---------------------------------------------------------------------------
# AC-0016, AC-0017, AC-0028: recorded sources
# ---------------------------------------------------------------------------


def test_same_recorded_source_has_no_sentence(tmp_path):
    cat = catalogue(tmp_path, packs={DEP: DEP_TOML})
    result = hint(cat, both_installed())
    assert len(result.lines) == 5


def test_different_recorded_source_for_old_pack_and_dependent(tmp_path):
    cat = catalogue(tmp_path, packs={DEP: DEP_TOML})
    other = "https://old.example.test/cat"
    rows = {(OLD, "claude-code"): other, (DEP, "claude-code"): other}
    lines = hint(cat, inst(rows)).lines
    assert lines[3:] == (
        "This step is a move between catalogues: 'governance-extras' was installed from https://old.example.test/cat.",
        f"  2. agentbundle install --pack repo-governance --scope repo --adapter claude-code {SRC}",
        "This step is a move between catalogues: 'iac-terraform' was installed from https://old.example.test/cat.",
        f"  3. agentbundle upgrade --pack iac-terraform --scope repo {SRC}",
    )
    text = "\n".join(lines)
    assert text.count("move between catalogues") == 2


@pytest.mark.parametrize("recorded", [None, "", "agent-ready-repo"])
def test_no_recorded_source(tmp_path, recorded):
    cat = catalogue(tmp_path, packs={DEP: DEP_TOML})
    rows = {(OLD, "claude-code"): recorded, (DEP, "claude-code"): recorded}
    lines = hint(cat, inst(rows)).lines
    assert "Installed pack 'governance-extras' has no recorded source." in lines
    assert "Installed pack 'iac-terraform' has no recorded source." in lines
    # each sentence sits directly above its own step
    for sentence, prefix in (
        ("Installed pack 'governance-extras' has no recorded source.", "  2. "),
        ("Installed pack 'iac-terraform' has no recorded source.", "  3. "),
    ):
        i = lines.index(sentence)
        assert lines[i + 1].startswith(prefix)


def test_equivalent_local_recorded_source_is_same(tmp_path):
    cat = catalogue(tmp_path)
    rows = {(OLD, "claude-code"): cat.as_uri()}
    assert len(hint(cat, inst(rows), source=str(cat)).lines) == 4


def test_sentence_order_above_a_placeholder_step(tmp_path):
    cat = catalogue(tmp_path)
    rows = {(OLD, "claude-code"): "https://old.example.test/c"}
    lines = hint(cat, inst(rows), source=f"{ARCHIVE}?x=1").lines
    assert "move between catalogues" in lines[-3]
    assert lines[-2] == PLACEHOLDER_SENTENCE


# ---------------------------------------------------------------------------
# AC-0021: refusals
# ---------------------------------------------------------------------------

UNSAFE = ["‮", "​", " ", "\u007f", "\n"]


@pytest.mark.parametrize("cmd", ["install", "upgrade"])
@pytest.mark.parametrize(
    "src",
    ["", "-o/evil"] + [f"/tmp/x{c}y" for c in UNSAFE],
)
def test_unsafe_source_is_refused(tmp_path, cmd, src):
    cat = catalogue(tmp_path)
    result = hint(cat, source=src, command=cmd)
    assert result.lines == ()
    assert result.refusal == REFUSAL.format(cmd=cmd)


@pytest.mark.parametrize("root", ["-rf", "/tmp/a\n", "/tmp/a‮b"])
def test_unsafe_target_root_is_refused(tmp_path, root):
    cat = catalogue(tmp_path)
    result = hint(cat, target_root=root, command="upgrade")
    assert (result.lines, result.refusal) == ((), REFUSAL.format(cmd="upgrade"))


@pytest.mark.parametrize("key", ["bogus", "-x", "a\nb", "a‮b"])
def test_bad_old_pack_adapter_is_refused(tmp_path, key):
    cat = catalogue(tmp_path)
    result = hint(cat, inst({(OLD, key): REPORTING}))
    assert (result.lines, result.refusal) == ((), REFUSAL.format(cmd="install"))
    assert "bogus" not in (result.refusal or "")


def test_refusal_reason_omits_values(tmp_path):
    cat = catalogue(tmp_path)
    result = hint(cat, source="/tmp/zzz‮", target_root="/tmp/qqq")
    assert "zzz" not in result.refusal and "qqq" not in result.refusal


@pytest.mark.parametrize("map_text", [None, "not toml ==", 'schema = 1\nrename = []\n'])
def test_unsafe_source_with_no_rename_gives_no_hint_and_no_reason(tmp_path, map_text):
    cat = catalogue(tmp_path, map_text=map_text)
    assert hint(cat, source="/x‮") == RenameHint()


def test_unsafe_source_with_map_not_renaming_this_pack(tmp_path):
    other = 'schema = 1\n[[rename]]\nfrom = "old-x"\nto = "repo-governance"\n'
    cat = catalogue(tmp_path, map_text=other)
    assert hint(cat, source="/x‮", target_root="-r") == RenameHint()


# ---------------------------------------------------------------------------
# AC-0022, AC-0027: the map
# ---------------------------------------------------------------------------

@pytest.mark.parametrize("label", sorted(BAD_MAPS))
def test_invalid_map_gives_no_hint(tmp_path, label):
    body = BAD_MAPS[label]
    cat = catalogue(tmp_path, map_text=None)
    (cat / "contracts" / "renames").mkdir(parents=True)
    path = cat / "contracts" / "renames" / "pack-renames.toml"
    path.write_bytes(body if isinstance(body, bytes) else body.encode("utf-8"))
    assert hint(cat) == RenameHint()


def test_missing_map_gives_no_hint(tmp_path):
    assert hint(catalogue(tmp_path, map_text=None)) == RenameHint()


def test_map_naming_other_pack_gives_no_hint(tmp_path):
    other = 'schema = 1\n[[rename]]\nfrom = "other-old"\nto = "repo-governance"\n'
    assert hint(catalogue(tmp_path, map_text=other)) == RenameHint()


def test_target_missing_from_catalogue(tmp_path):
    assert hint(catalogue(tmp_path, with_target=False)) == RenameHint()


def test_target_at_catalogue_root_layout_counts(tmp_path):
    cat = catalogue(tmp_path, root_layout=(NEW,))
    assert hint(cat).lines


def test_oversized_map(tmp_path):
    cat = catalogue(tmp_path, map_text=GOOD_MAP + "#" * (65537 - len(GOOD_MAP)))
    assert (cat / "contracts/renames/pack-renames.toml").stat().st_size == 65537
    assert hint(cat) == RenameHint()


def test_map_at_exact_cap_is_read(tmp_path):
    cat = catalogue(tmp_path, map_text=GOOD_MAP + "#" * (65536 - len(GOOD_MAP)))
    assert hint(cat).lines


@SKIP_NO_LINKS
def test_symlinked_map(tmp_path):
    cat = catalogue(tmp_path)
    real = tmp_path / "real.toml"
    real.write_text(GOOD_MAP, encoding="utf-8")
    path = cat / "contracts/renames/pack-renames.toml"
    path.unlink()
    path.symlink_to(real)
    assert hint(cat) == RenameHint()


@SKIP_NO_LINKS
def test_hard_linked_map(tmp_path):
    cat = catalogue(tmp_path)
    os.link(
        cat / "contracts/renames/pack-renames.toml", tmp_path / "second-name.toml"
    )
    assert hint(cat) == RenameHint()


@SKIP_NO_LINKS
@pytest.mark.parametrize("which", ["contracts", "renames"])
def test_symlinked_map_directories(tmp_path, which):
    cat = catalogue(tmp_path)
    target = cat / "contracts" if which == "contracts" else cat / "contracts/renames"
    moved = tmp_path / f"moved-{which}"
    target.rename(moved)
    target.symlink_to(moved, target_is_directory=True)
    assert hint(cat) == RenameHint()


def test_regular_file_at_renames(tmp_path):
    cat = catalogue(tmp_path, map_text=None)
    (cat / "contracts").mkdir()
    (cat / "contracts" / "renames").write_text(GOOD_MAP, encoding="utf-8")
    assert hint(cat) == RenameHint()


@pytest.mark.skipif(not hasattr(os, "mkfifo"), reason="no FIFOs")
def test_fifo_map(tmp_path):
    cat = catalogue(tmp_path)
    path = cat / "contracts/renames/pack-renames.toml"
    path.unlink()
    os.mkfifo(path)
    assert hint(cat) == RenameHint()


def test_directory_map(tmp_path):
    cat = catalogue(tmp_path, map_text=None)
    (cat / "contracts/renames/pack-renames.toml").mkdir(parents=True)
    assert hint(cat) == RenameHint()


def test_builder_reads_only_the_given_catalogue(tmp_path, monkeypatch):
    import socket

    def boom(*a, **k):
        raise AssertionError("network used")

    monkeypatch.setattr(socket, "socket", boom)
    monkeypatch.setattr(socket, "create_connection", boom)
    assert hint(catalogue(tmp_path)).lines


# ---------------------------------------------------------------------------
# AC-0030: dependents, Absent / Readable / Unchecked
# ---------------------------------------------------------------------------


def notice_unchecked(name: str) -> str:
    return f"Could not check installed pack '{name}' for a dependency on 'repo-governance'."


def one_pack(tmp_path, installed_name="iac-terraform", **kw):
    cat = catalogue(tmp_path, **kw)
    rows = {(installed_name, "claude-code"): REPORTING}
    return cat, hint(cat, inst(rows))


def base_lines(result):
    return result.lines[:2]


def test_absent_no_packs_dir_no_step_no_notice(tmp_path):
    cat = catalogue(tmp_path, with_target=False, map_text=GOOD_MAP)
    # target must exist: place it at the catalogue root so `packs/` is absent
    (cat / NEW).mkdir()
    (cat / NEW / "pack.toml").write_text(PLAIN_TOML, encoding="utf-8")
    result = hint(cat, inst({(DEP, "claude-code"): REPORTING}))
    assert len(result.lines) == 3  # head, run, install step only


def test_absent_nothing_at_candidate(tmp_path):
    _cat, result = one_pack(tmp_path)
    assert len(result.lines) == 3


def test_absent_real_dir_without_pack_toml(tmp_path):
    cat = catalogue(tmp_path)
    (cat / "packs" / DEP).mkdir()
    result = hint(cat, inst({(DEP, "claude-code"): REPORTING}))
    assert len(result.lines) == 3


def test_second_candidate_is_used_when_first_has_no_pack_toml(tmp_path):
    cat = catalogue(tmp_path, packs={DEP: DEP_TOML}, root_layout=(DEP,))
    (cat / "packs" / DEP).mkdir()
    result = hint(cat, inst({(DEP, "claude-code"): REPORTING}))
    assert len(steps_of(result)) == 2


def test_unchecked_invalid_name_is_escaped(tmp_path):
    cat = catalogue(tmp_path)
    bad = "bad‮name"
    result = hint(cat, inst({(bad, "claude-code"): REPORTING}))
    assert result.lines[2] == notice_unchecked("bad\\u202ename")
    assert len(steps_of(result)) == 1


@SKIP_NO_LINKS
def test_unchecked_symlinked_packs_dir(tmp_path):
    cat = catalogue(tmp_path, packs={DEP: DEP_TOML})
    real = tmp_path / "realpacks"
    (cat / "packs").rename(real)
    (cat / "packs").symlink_to(real, target_is_directory=True)
    result = hint(cat, inst({(DEP, "claude-code"): REPORTING}))
    # target is unreadable too, so the rename itself has no hint
    assert result == RenameHint()


def _unchecked_setup(tmp_path):
    """A catalogue whose target sits at the root so `packs/` is free to abuse."""
    cat = catalogue(tmp_path, with_target=False)
    (cat / NEW).mkdir()
    (cat / NEW / "pack.toml").write_text(PLAIN_TOML, encoding="utf-8")
    return cat


def test_unchecked_regular_file_at_packs(tmp_path):
    cat = _unchecked_setup(tmp_path)
    (cat / "packs").write_text("x", encoding="utf-8")
    result = hint(cat, inst({(DEP, "claude-code"): REPORTING}))
    assert notice_unchecked(DEP) in result.lines
    assert len(steps_of(result)) == 1


@SKIP_NO_LINKS
def test_unchecked_symlinked_packs_with_root_target(tmp_path):
    cat = _unchecked_setup(tmp_path)
    real = tmp_path / "realpacks"
    (real / DEP).mkdir(parents=True)
    (real / DEP / "pack.toml").write_text(DEP_TOML, encoding="utf-8")
    (cat / "packs").symlink_to(real, target_is_directory=True)
    result = hint(cat, inst({(DEP, "claude-code"): REPORTING}))
    assert notice_unchecked(DEP) in result.lines
    assert len(steps_of(result)) == 1


@SKIP_NO_LINKS
def test_unchecked_symlinked_candidate_dir_whatever_later_holds(tmp_path):
    cat = catalogue(tmp_path, packs={DEP: DEP_TOML}, root_layout=(DEP,))
    real = tmp_path / "realdep"
    real.mkdir()
    (cat / "packs" / DEP).symlink_to(real, target_is_directory=True)
    result = hint(cat, inst({(DEP, "claude-code"): REPORTING}))
    assert notice_unchecked(DEP) in result.lines
    assert len(steps_of(result)) == 1


def test_unchecked_regular_file_at_candidate(tmp_path):
    cat = catalogue(tmp_path)
    (cat / "packs" / DEP).write_text("x", encoding="utf-8")
    result = hint(cat, inst({(DEP, "claude-code"): REPORTING}))
    assert notice_unchecked(DEP) in result.lines


def _pack_toml_variants(tmp_path):
    """Yield (label, callable(cat) installing a bad pack.toml for DEP)."""
    def write_bytes(data):
        def make(path):
            path.write_bytes(data)
        return make

    def symlink(path):
        real = path.parent / "real.toml"
        real.write_text(DEP_TOML, encoding="utf-8")
        path.symlink_to(real)

    def dangling(path):
        path.symlink_to(path.parent / "missing.toml")

    def hardlink(path):
        other = path.parent.parent.parent / "other.toml"
        other.write_text(DEP_TOML, encoding="utf-8")
        os.link(other, path)

    def directory(path):
        path.mkdir()

    def fifo(path):
        os.mkfifo(path)

    variants = {
        "oversize": write_bytes(b"#" * 65537),
        "non-utf8": write_bytes(b"\xff\xfe\xfa"),
        "invalid-toml": write_bytes(b"a = = 1"),
        "deep-nesting": write_bytes(b"a = " + b"[" * 1000),
        "directory": directory,
    }
    if sys.platform != "win32":
        variants.update(symlink=symlink, dangling=dangling, hardlink=hardlink)
        if hasattr(os, "mkfifo"):
            variants["fifo"] = fifo
    return variants


@pytest.mark.parametrize("label", sorted(_pack_toml_variants(None)))
def test_unchecked_pack_toml_variants(tmp_path, label):
    cat = catalogue(tmp_path)
    (cat / "packs" / DEP).mkdir()
    _pack_toml_variants(tmp_path)[label](cat / "packs" / DEP / "pack.toml")
    result = hint(cat, inst({(DEP, "claude-code"): REPORTING}))
    assert result.lines[2] == notice_unchecked(DEP)
    assert len(steps_of(result)) == 1  # the install step; rest of hint prints
    assert result.lines[0] == HEAD


@pytest.mark.parametrize(
    "toml_text",
    [
        '[pack]\nname = "x"\n[pack.dependencies]\nrequired = "x"\n',
        '[pack]\nname = "x"\n[[pack.dependencies.required]]\npack = 5\n',
        '[pack]\nname = "x"\n[[pack.dependencies.required]]\npack = "other"\n',
    ],
)
def test_readable_non_dependents_print_nothing(tmp_path, toml_text):
    cat, result = one_pack(tmp_path, packs={DEP: toml_text})
    assert len(result.lines) == 3


@pytest.mark.parametrize(
    "extra",
    ['', 'catalogue = "https://elsewhere.example.test/cat"\n'],
)
def test_readable_dependents_ignore_catalogue_key(tmp_path, extra):
    text = (
        '[pack]\nname = "x"\n[[pack.dependencies.required]]\n'
        f'pack = "repo-governance"\n{extra}'
    )
    cat, result = one_pack(tmp_path, packs={DEP: text})
    assert len(steps_of(result)) == 2


@pytest.mark.parametrize("key", ["bogus", "-x", "a\nb", "a‮b"])
def test_dependent_with_bad_adapter_gets_notice_and_no_step(tmp_path, key):
    cat = catalogue(tmp_path, packs={DEP: DEP_TOML})
    result = hint(cat, inst({(DEP, key): REPORTING}))
    assert result.lines[2] == (
        "Installed pack 'iac-terraform' has an adapter that is not a shipped "
        "adapter; upgrade it by hand."
    )
    assert len(steps_of(result)) == 1
    assert result.refusal is None


def test_dependent_with_one_shipped_and_one_bogus_row(tmp_path):
    cat = catalogue(tmp_path, packs={DEP: DEP_TOML})
    rows = {(DEP, "claude-code"): REPORTING, (DEP, "bogus"): REPORTING}
    result = hint(cat, inst(rows))
    notices = [ln for ln in result.lines if "not a shipped adapter" in ln]
    assert len(notices) == 1
    assert len(steps_of(result)) == 1


def test_non_dependent_with_bad_adapter_has_no_notice(tmp_path):
    cat = catalogue(tmp_path, packs={"plain": PLAIN_TOML})
    result = hint(cat, inst({("plain", "bogus"): REPORTING}))
    assert len(result.lines) == 3


def test_notices_sorted_by_raw_name(tmp_path):
    names = ("b-pack", "a-pack", "Zed")
    cat = catalogue(tmp_path, packs={n: "a = = 1" for n in names if n != "Zed"})
    rows = {(n, "claude-code"): REPORTING for n in names}
    assert hint(cat, inst(rows)).lines[2:5] == tuple(
        notice_unchecked(n) for n in ("Zed", "a-pack", "b-pack")
    )


def test_notices_sit_after_credential_sentence_before_steps(tmp_path):
    cat = catalogue(tmp_path)
    rows = {("Zed", "claude-code"): REPORTING}
    lines = hint(cat, inst(rows), source=f"{ARCHIVE}?token=x").lines
    assert lines[2] == CREDENTIAL_SENTENCE
    assert lines[3] == notice_unchecked("Zed")
    assert lines[4] == PLACEHOLDER_SENTENCE


def test_installed_state_other_than_old_name_is_the_only_input(tmp_path):
    # `install` with no --scope reads repo-scope state only: the builder takes
    # the Installed it is handed and nothing else.
    cat = catalogue(tmp_path, packs={DEP: DEP_TOML})
    result = hint(cat, inst({(DEP, "claude-code"): REPORTING}))
    assert len(steps_of(result)) == 2


# ---------------------------------------------------------------------------
# AC-0031: placeholder steps are never runnable
# ---------------------------------------------------------------------------


def _placeholder_steps(tmp_path):
    cat = catalogue(tmp_path, packs={DEP: DEP_TOML})
    one = hint(cat, both_installed(), source=f"{ARCHIVE}?x=1")
    rows = {
        (OLD, "claude-code"): REPORTING,
        (OLD, "cursor"): REPORTING,
        (DEP, "claude-code"): REPORTING,
        (DEP, "cursor"): REPORTING,
    }
    two = hint(cat, inst(rows), source=f"{ARCHIVE}?x=1")
    empty = hint(cat, source=f"{ARCHIVE}?x=1")
    return [
        s
        for result in (one, two, empty)
        for s in steps_of(result)
        if PLACEHOLDER in s
    ]


def test_placeholder_is_last_bare_word(tmp_path):
    steps = _placeholder_steps(tmp_path)
    assert len(steps) >= 6
    for step in steps:
        assert step.endswith(f" {PLACEHOLDER}")
        assert step.count(PLACEHOLDER) == 1


def _shell(name: str) -> str | None:
    path = shutil.which(name)
    if path is None and sys.platform in ("linux", "darwin") and name in ("bash", "sh"):
        pytest.fail(f"{name} is required on this platform and is missing")
    return path


@pytest.mark.skipif(sys.platform == "win32", reason="POSIX shells")
@pytest.mark.parametrize("shell", ["bash", "zsh", "sh"])
def test_placeholder_steps_are_shell_syntax_errors(tmp_path, shell):
    exe = _shell(shell)
    if exe is None:
        pytest.skip(f"{shell} not installed")
    for step in _placeholder_steps(tmp_path):
        done = subprocess.run(
            [exe, "-n", "-c", step], capture_output=True, text=True, check=False
        )
        assert done.returncode != 0, f"{shell} -n accepted: {step}"


def test_non_placeholder_steps_parse_in_a_shell(tmp_path):
    exe = shutil.which("sh")
    if exe is None:
        pytest.skip("no sh")
    cat = catalogue(tmp_path, packs={DEP: DEP_TOML})
    for step in steps_of(hint(cat, both_installed())):
        assert subprocess.run([exe, "-n", "-c", step], check=False).returncode == 0


# ---------------------------------------------------------------------------
# canonicalize_source stays as it was
# ---------------------------------------------------------------------------


def test_canonicalize_source_unchanged_for_credential_rules():
    assert canonicalize_source("https://u@h/x") is None
    assert canonicalize_source("https://h/x?token=1") is None
    assert canonicalize_source("https://h/x#secret") is None
    assert canonicalize_source("HTTPS://H/x/") == "https://h/x"
