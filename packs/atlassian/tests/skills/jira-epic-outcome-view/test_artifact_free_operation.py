"""The view answers with no repository artifact anywhere in reach.

Three statements, because the criteria ask three different questions.

The run happens from a working directory that is not a repository and holds
none of an adopter's artifacts, and it still returns a correct, non-empty
answer.

Every path under an adopter repository is denied outright while it runs --
denied in the child processes too, because a run is every process it starts.
The repository stood up for this is a real one in shape: a git directory, a
workspace configuration file, a product tree with an intent inside it. So
the denial denies the dependency rather than a directory that happens to be
empty.

And every file the view's own code opens during the run is recorded and held
to a small allowed set: the installed pack, the simulated install location of
the siblings it composes, its working directory, and its scratch directory.
Naming three absent artifacts would let a hidden dependency pass; a record of
everywhere the run actually read cannot, because a repository file anywhere
would be in it.

The fourth statement is on the source side: the sources name none of the
machinery that belongs to a bridge skill.
"""

from __future__ import annotations

import re
import tempfile

import atlassian_jira_epic_outcome_view_guarantees as guarantees
import pytest

#: The machinery confined to bridge skills. A standalone view naming any of
#: it has coupled itself to a host repository's delivery model, which is the
#: dependency this criterion exists to keep out.
CONFINED_MACHINERY = (
    "docs/product/",
    "intent tree",
    "workspace.toml",
    "canonical intent",
    "delivery brief",
    "work-intake",
)

#: Artifacts an adopter's repository carries and a plain directory does not.
REPOSITORY_ARTIFACTS = ("docs/product", "workspace.toml", ".git", "AGENTS.md")


@pytest.fixture
def transport(tmp_path):
    return guarantees.build_recording_transport(tmp_path)


@pytest.fixture
def elsewhere(tmp_path):
    """A working directory that is not a repository and holds none of ours."""
    cwd = tmp_path / "somewhere-that-is-not-a-repository"
    cwd.mkdir()
    (cwd / "notes.txt").write_text("a team's own directory\n", encoding="utf-8")
    for artifact in REPOSITORY_ARTIFACTS:
        assert not (cwd / artifact).exists()
    return cwd


@pytest.fixture
def adopter_repository(tmp_path):
    return guarantees.build_adopter_repository(tmp_path / "an-adopter-repository")


@pytest.fixture
def scratch(tmp_path, monkeypatch):
    """A scratch directory of known location, so reads into it are nameable."""
    directory = tmp_path / "scratch"
    directory.mkdir()
    monkeypatch.setattr(tempfile, "tempdir", str(directory))
    return directory


def _run(
    monkeypatch,
    load_module,
    transport,
    elsewhere,
    capsys,
    *,
    guard=None,
    watch=(),
):
    cli = load_module("")
    env = guarantees.view_environment(transport)
    if guard is not None:
        env.update(guard.env)
    guarantees.apply_environment(monkeypatch, env)
    monkeypatch.chdir(elsewhere)

    denial = guarantees.load_denial_guard(guard) if guard is not None else None
    if denial is not None:
        denial.install(
            deny=[str(entry) for entry in guard.env["ATLASSIAN_DENY_ROOTS"].split(":") if entry],
            allow=[str(entry) for entry in watch],
            deny_log=str(guard.deny_log),
            stray_log=str(guard.stray_log) if watch else None,
        )
    try:
        exit_code = cli.main(list(guarantees.VIEW_ARGV))
    finally:
        if denial is not None:
            denial.uninstall()
    stdout = capsys.readouterr().out
    assert exit_code == 0, f"the view did not complete: {stdout}"
    guarantees.assert_answer_is_correct_and_non_empty(
        guarantees.parse_stdout_document(stdout)
    )
    return stdout


def test_the_view_answers_from_a_non_repository_working_directory(
    monkeypatch, load_module, transport, elsewhere, capsys
):
    """A correct, non-empty answer -- not merely a zero exit. A run that
    printed an empty document would satisfy every other check here."""
    _run(monkeypatch, load_module, transport, elsewhere, capsys)


def test_the_view_answers_with_every_adopter_repository_path_denied(
    monkeypatch, load_module, transport, tmp_path, elsewhere, adopter_repository, capsys
):
    """The same answer, with the adopter's repository unreadable."""
    guard = guarantees.build_denial_guard(tmp_path, deny=[adopter_repository])

    _run(monkeypatch, load_module, transport, elsewhere, capsys, guard=guard)

    assert not guard.denied_attempts(), (
        f"the run tried to read the adopter's repository: {guard.denied_attempts()}"
    )


def test_every_file_the_run_opens_is_the_skill_or_its_scratch(
    monkeypatch, load_module, transport, tmp_path, elsewhere, scratch, capsys
):
    """Deny-by-default in observation form. Any repository file, this one
    included, would appear here -- so no list of named artifacts has to be
    complete for the check to be."""
    guard = guarantees.build_denial_guard(tmp_path, deny=[])
    allowed = [guarantees.PACK_ROOT, transport.skills_root, elsewhere, scratch]

    _run(
        monkeypatch, load_module, transport, elsewhere, capsys,
        guard=guard, watch=allowed,
    )

    stray = guard.reads_outside_the_allowed_set()
    assert not stray, f"the run read outside the skill and its scratch: {stray}"


def test_the_denial_would_actually_stop_a_repository_read(
    tmp_path, adopter_repository
):
    """The control. A guard that denied nothing would make the check above
    green for a view that read the adopter's whole repository."""
    guard = guarantees.build_denial_guard(tmp_path, deny=[adopter_repository])
    denial = guarantees.load_denial_guard(guard)
    denial.install(deny=[str(adopter_repository)], deny_log=str(guard.deny_log))
    try:
        for artifact in ("workspace.toml", "AGENTS.md", "docs/product/changelog.md"):
            with pytest.raises(PermissionError):
                (adopter_repository / artifact).read_text(encoding="utf-8")
        # The skill's own installed files stay readable, which is what keeps
        # the denial about the adopter's repository.
        assert guarantees.VIEW_MANIFEST.read_text(encoding="utf-8")
    finally:
        denial.uninstall()

    assert len(guard.denied_attempts()) == 3


def test_the_denial_reaches_the_child_processes_too(tmp_path, adopter_repository):
    """A run is every process it starts. A guard installed only in the
    calling process would leave a composed skill free to read anything."""
    import subprocess
    import sys

    guard = guarantees.build_denial_guard(tmp_path, deny=[adopter_repository])
    target = adopter_repository / "workspace.toml"

    probe = subprocess.run(
        [sys.executable, "-c", f"from pathlib import Path; Path({str(target)!r}).read_text()"],
        capture_output=True,
        env={"PATH": "/usr/bin:/bin", **guard.env},
        check=False,
    )

    assert probe.returncode != 0
    assert "denied repository path" in probe.stderr.decode("utf-8", "replace")


def test_the_sources_name_none_of_the_confined_machinery():
    """A standalone view carries no reference to a host repository's delivery
    model: not its product tree, not its intent tree, not its workspace
    configuration file, not its intake route."""
    offences = []
    for path, text in guarantees.shipped_source_text(guarantees.VIEW_SKILL_DIR).items():
        lowered = text.lower()
        for token in CONFINED_MACHINERY:
            if token in lowered:
                offences.append(f"{path.relative_to(guarantees.PACK_ROOT)}: {token!r}")

    assert not offences, f"the sources reach for confined machinery: {offences}"


def test_the_shipped_files_cite_no_internal_governance_record():
    """Shipped pack content is portable guidance. A decision record's number,
    an acceptance criterion or a path only this repository has means nothing
    to an adopter who installed the pack and nothing else."""
    patterns = {
        "decision-record number": re.compile(r"\b(?:ADR|RFC)-\d{2,4}\b"),
        "acceptance criterion": re.compile(r"\bAC\d{1,3}\b"),
        "repository-only path": re.compile(r"\b(?:docs/specs|docs/adr|docs/rfc|tools)/"),
    }
    offences = []
    for path, text in guarantees.shipped_source_text(guarantees.VIEW_SKILL_DIR).items():
        for label, pattern in patterns.items():
            match = pattern.search(text)
            if match:
                offences.append(
                    f"{path.relative_to(guarantees.PACK_ROOT)}: {label} {match.group(0)!r}"
                )

    assert not offences, f"shipped pack content cites internal records: {offences}"
