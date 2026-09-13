"""Construction tests for the decision-record index generator.

Materialized unchanged from docs/specs/index-table-generation/plan.md
## Construction tests, per the tdd-stubs stub-to-EXECUTE handoff.
"""
import importlib.util, pathlib, sys, urllib.parse
import pytest

ROOT = pathlib.Path(__file__).resolve().parents[2]
SCRIPT = ROOT / "packs/governance-extras/.apm/skills/new-adr/scripts/index-records.py"

def _load():
    spec = importlib.util.spec_from_file_location("index_records_adr", SCRIPT)
    mod = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = mod
    spec.loader.exec_module(mod)
    return mod

def _write(d, name, h1, status="Accepted", date="2026-01-01"):
    (d / name).write_text(
        f"# {h1}\n\n- **Status:** {status}\n- **Date:** {date}\n",
        encoding="utf-8", newline="\n")

def test_rows_are_ordered_by_ordinal_not_filesystem_order(tmp_path):
    """AC1: shuffled creation order still renders ascending by ordinal."""
    for n in ("0009", "0001", "0010"):
        _write(tmp_path, f"{n}-r.md", f"ADR-{n}: Title {n}")
    rows = _load().render(tmp_path, record_type="adr").splitlines()
    ordinals = [r.split("|")[1].strip() for r in rows if r.startswith("| 0")]
    assert ordinals == ["0001", "0009", "0010"]

def test_a_non_record_entry_yields_no_row(tmp_path):
    """AC2: a .md file whose H1 is not the record form contributes nothing."""
    _write(tmp_path, "0001-r.md", "ADR-0001: Real")
    (tmp_path / "notes.md").write_text("# Just a note\n", encoding="utf-8", newline="\n")
    rows = [r for r in _load().render(tmp_path, record_type="adr").splitlines()
            if r.startswith("| 0")]
    assert len(rows) == 1

def test_a_qualifying_clause_is_stripped_from_status(tmp_path):
    """AC5: `Accepted — partially amended: ...` renders as `Accepted`."""
    _write(tmp_path, "0001-r.md", "ADR-0001: T",
           status="Accepted — **partially amended:** the guides sub-decision")
    rows = [r for r in _load().render(tmp_path, record_type="adr").splitlines() if r.startswith("| 0")]
    assert rows, "no record row rendered"
    row = rows[0]
    assert row.split("|")[3].strip() == "Accepted"

@pytest.mark.parametrize("title,shown", [
    ("Choose A | B", r"Choose A \| B"),
    ("Brackets [x] and (y)", r"Brackets \[x\] and (y)"),
])
def test_a_delimiter_bearing_title_renders_one_escaped_cell(tmp_path, title, shown):
    """AC6: the title cell displays escaped text and stays one cell."""
    _write(tmp_path, "0001-r.md", f"ADR-0001: {title}")
    rows = [r for r in _load().render(tmp_path, record_type="adr").splitlines() if r.startswith("| 0")]
    assert rows, "no record row rendered"
    row = rows[0]
    assert row.split(" | ")[1] == f"[{shown}](0001-r.md)"

def test_a_delimiter_bearing_filename_yields_a_resolving_link(tmp_path):
    """AC6, filename half: the link destination survives escaping and resolves."""
    name = "0001-a (b).md"
    _write(tmp_path, name, "ADR-0001: T")
    rows = [r for r in _load().render(tmp_path, record_type="adr").splitlines() if r.startswith("| 0")]
    assert rows, "no record row rendered"
    row = rows[0]
    dest = row.split(" | ")[1].split("](")[1].rstrip(")")
    # Decode with the real inverse, not a hard-coded reversal of one
    # character: the assertion must not depend on which delimiters the
    # encoder happens to cover.
    assert (tmp_path / urllib.parse.unquote(dest)).exists()

import os, subprocess

def _git_repo(tmp_path):
    subprocess.run(["git", "init", "-q"], cwd=tmp_path, check=True)
    subprocess.run(["git", "config", "user.email", "t@example.invalid"], cwd=tmp_path, check=True)
    subprocess.run(["git", "config", "user.name", "t"], cwd=tmp_path, check=True)
    return tmp_path

def test_header_date_wins_over_git_history(tmp_path):
    """AC7: a present Date field is used even inside a git repository."""
    d = _git_repo(tmp_path)
    _write(d, "0001-r.md", "ADR-0001: T", date="2020-02-02")
    subprocess.run(["git", "add", "-A"], cwd=d, check=True)
    env = {**os.environ, "GIT_COMMITTER_DATE": "2024-04-04T00:00:00"}
    subprocess.run(["git", "commit", "-qm", "x", "--date=2024-04-04T00:00:00"],
                   cwd=d, check=True, env=env)
    rows = [r for r in _load().render(d, record_type="adr").splitlines()
            if r.startswith("| 0")]
    assert rows, "no record row rendered"
    assert "2020-02-02" in rows[0]

def test_absent_header_date_falls_back_to_first_commit_date(tmp_path):
    """AC8: the fallback is the file's add date, not today."""
    d = _git_repo(tmp_path)
    (d / "0001-r.md").write_text("# ADR-0001: T\n\n- **Status:** Accepted\n",
                                 encoding="utf-8", newline="\n")
    subprocess.run(["git", "add", "-A"], cwd=d, check=True)
    env = {**os.environ, "GIT_COMMITTER_DATE": "2024-04-04T00:00:00"}
    subprocess.run(["git", "commit", "-qm", "x", "--date=2024-04-04T00:00:00"],
                   cwd=d, check=True, env=env)
    rows = [r for r in _load().render(d, record_type="adr").splitlines() if r.startswith("| 0")]
    assert rows, "no record row rendered"
    row = rows[0]
    assert row.split("|")[4].strip() == "2024-04-04"

def test_absent_date_without_git_warns_and_leaves_the_cell_empty(tmp_path, capsys):
    """AC9 + AC10: empty cell, and a warning naming file and field."""
    (tmp_path / "0001-r.md").write_text("# ADR-0001: T\n\n- **Status:** Accepted\n",
                                        encoding="utf-8", newline="\n")
    rows = [r for r in _load().render(tmp_path, record_type="adr").splitlines() if r.startswith("| 0")]
    assert rows, "no record row rendered"
    row = rows[0]
    assert row.split("|")[4].strip() == ""
    err = capsys.readouterr().err
    assert "0001-r.md" in err and "Date" in err

def test_an_empty_directory_renders_the_type_sentinel(tmp_path):
    """AC14: the adopter's first-install state is a sentinel, not an empty table."""
    out = _load().render(tmp_path, record_type="adr")
    assert "<!-- no ADRs yet -->" in out

@pytest.mark.parametrize("kind,heading", [("ADR", "Architecture Decision Records"),
                                          ("RFC", "Requests For Comments")])
def test_the_record_type_is_inferred_when_not_supplied(tmp_path, kind, heading):
    """AC15, inference half: an RFC corpus must not infer as ADR."""
    _write(tmp_path, "0001-r.md", f"{kind}-0001: T")
    assert heading in _load().render(tmp_path)

def test_a_record_without_status_warns_and_still_renders(tmp_path, capsys):
    """AC11 + AC12: a malformed record never costs the whole index."""
    (tmp_path / "0001-r.md").write_text("# ADR-0001: T\n", encoding="utf-8", newline="\n")
    out = _load().render(tmp_path, record_type="adr")
    assert any(line.startswith("| 0001") for line in out.splitlines())
    assert "0001-r.md" in capsys.readouterr().err

FROZEN = ("docs/adr", "docs/rfc", "docs/specs", "agent-ready-repo", "eugenelim")

@pytest.mark.parametrize("literal", FROZEN)
def test_the_generator_source_holds_no_frozen_literal(literal):
    """AC20: the script carries nothing drawn from this repository."""
    assert literal not in SCRIPT.read_text(encoding="utf-8")


def test_a_sentence_after_the_status_token_is_a_qualifying_clause(tmp_path):
    """AC5: `Superseded by ADR-0042. ADR-0042 keeps ...` renders as the token."""
    _write(tmp_path, "0001-r.md", "ADR-0001: T",
           status="Superseded by [ADR-0042](0042-x.md). It keeps the core holding.")
    rows = [r for r in _load().render(tmp_path, record_type="adr").splitlines()
            if r.startswith("| 0")]
    assert rows, "no record row rendered"
    assert rows[0].split(" | ")[2] == "Superseded by ADR-0042"


def test_an_unfilled_date_placeholder_is_not_a_date(tmp_path):
    """A record still carrying the template's placeholder has no date."""
    _write(tmp_path, "0001-r.md", "ADR-0001: T", date="YYYY-MM-DD")
    rows = [r for r in _load().render(tmp_path, record_type="adr").splitlines()
            if r.startswith("| 0")]
    assert rows, "no record row rendered"
    assert rows[0].split(" | ")[3].rstrip(" |") == ""


# --- main(): the CLI surface the plan declared and the first pass never landed ---

def _main(*argv):
    """Run the CLI in-process and return (exit_code, stderr)."""
    import contextlib, io
    err = io.StringIO()
    with contextlib.redirect_stderr(err):
        code = _load().main(list(argv))
    return code, err.getvalue()


def test_check_writes_nothing_and_reports_zero_when_the_index_matches(tmp_path):
    """AC16 + AC17."""
    _write(tmp_path, "0001-r.md", "ADR-0001: T")
    assert _main(str(tmp_path)) [0] == 0
    before = (tmp_path / "README.md").read_bytes()
    code, _ = _main("--check", str(tmp_path))
    assert code == 0
    assert (tmp_path / "README.md").read_bytes() == before


def test_check_reports_nonzero_and_names_the_first_differing_line(tmp_path):
    """AC18: divergence is reported, and --check still writes nothing."""
    _write(tmp_path, "0001-r.md", "ADR-0001: T")
    _main(str(tmp_path))
    (tmp_path / "README.md").write_text("# Wrong\n", encoding="utf-8", newline="\n")
    code, err = _main("--check", str(tmp_path))
    assert code != 0
    assert "line 1 differs" in err
    assert (tmp_path / "README.md").read_text(encoding="utf-8") == "# Wrong\n"


def test_an_index_target_that_is_a_symlink_is_refused_and_named(tmp_path):
    """AC13 at the write path: the reader refusing a link is not enough."""
    import os
    victim = tmp_path / "victim.txt"
    victim.write_text("DO NOT OVERWRITE\n", encoding="utf-8", newline="\n")
    recs = tmp_path / "recs"
    recs.mkdir()
    _write(recs, "0001-r.md", "ADR-0001: T")
    try:
        os.symlink(victim, recs / "README.md")
    except OSError:
        pytest.skip("symlinks unavailable")
    code, err = _main(str(recs))
    assert code != 0
    assert "symlink" in err
    assert victim.read_text(encoding="utf-8") == "DO NOT OVERWRITE\n"


def test_an_untyped_empty_directory_refuses_and_writes_nothing(tmp_path):
    """AC15a: a directory with no records carries no evidence of its own type."""
    code, err = _main(str(tmp_path))
    assert code != 0
    assert "record type" in err
    assert not (tmp_path / "README.md").exists()


def test_an_empty_field_does_not_capture_the_following_line(tmp_path):
    """AC3 + AC9: `\\s*` after a label matches a newline; this is the regression."""
    (tmp_path / "0001-r.md").write_text(
        "# RFC-0001: T\n\n- **Status:** Open\n- **Date opened:** 2026-01-01\n"
        "- **Date closed:**\n- **Decision weight:** heavy\n",
        encoding="utf-8", newline="\n")
    rows = [r for r in _load().render(tmp_path, record_type="rfc").splitlines()
            if r.startswith("| 0")]
    assert rows, "no record row rendered"
    cells = rows[0].split(" | ")
    assert "Decision weight" not in rows[0]
    assert cells[4].rstrip(" |") == "", f"open RFC carries a closed date: {rows[0]}"


def test_a_record_heading_without_a_usable_ordinal_is_warned_about(tmp_path):
    """AC11's other half: the class was empty, so its warning could not fire."""
    _write(tmp_path, "0001-ok.md", "ADR-0001: Fine")
    (tmp_path / "0002-big.md").write_text(
        "# ADR-10000: Too many digits\n\n- **Status:** Accepted\n",
        encoding="utf-8", newline="\n")
    code, err = _main("--check", str(tmp_path))
    assert "0002-big.md" in err
    assert "ordinal" in err
