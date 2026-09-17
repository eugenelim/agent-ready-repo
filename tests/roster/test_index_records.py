"""Construction tests for the decision-record index generator.

Materialized unchanged from docs/specs/index-table-generation/plan.md
## Construction tests, per the tdd-stubs stub-to-EXECUTE handoff.
"""
import importlib.util
import os
import pathlib
import re
import subprocess
import sys
import urllib.parse

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
    # `#` and `?` were omitted by the old hand-maintained encoder list.
    name = "0001-a (b)#c?d.md"
    _write(tmp_path, name, "ADR-0001: T")
    rows = [r for r in _load().render(tmp_path, record_type="adr").splitlines() if r.startswith("| 0")]
    assert rows, "no record row rendered"
    row = rows[0]
    dest = row.split(" | ")[1].split("](")[1].rstrip(")")
    # Three separate properties. exists() alone passes for an empty destination
    # because `tmp_path / ""` exists; unquote round-tripping alone passes for a
    # raw `#` because unquote does not touch it, which is how an escaping gap
    # survived here. The link resolves only if the destination is fully encoded.
    assert re.fullmatch(r"[A-Za-z0-9._~%-]+", dest), f"destination not encoded: {dest}"
    assert urllib.parse.unquote(dest) == name
    assert (tmp_path / name).exists()


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

_SHIPPED_COPIES = (
    ROOT / "packs/governance-extras/.apm/skills/new-adr/scripts/index-records.py",
    ROOT / "packs/governance-extras/.apm/skills/new-rfc/scripts/index-records.py",
)


@pytest.mark.parametrize("literal", FROZEN)
@pytest.mark.parametrize("copy", _SHIPPED_COPIES, ids=["new-adr", "new-rfc"])
def test_the_generator_source_holds_no_frozen_literal(copy, literal):
    """AC20, over every shipped copy — each is independently the generator."""
    assert literal not in copy.read_text(encoding="utf-8")


def test_a_sentence_after_the_status_token_is_a_qualifying_clause(tmp_path):
    """AC5: `Superseded by ADR-0042. ADR-0042 keeps ...` renders as the token."""
    _write(tmp_path, "0001-r.md", "ADR-0001: T",
           status="Superseded by [ADR-0042](0042-x.md). It keeps the core holding.")
    rows = [r for r in _load().render(tmp_path, record_type="adr").splitlines()
            if r.startswith("| 0")]
    assert rows, "no record row rendered"
    assert rows[0].split(" | ")[2] == "Superseded by ADR-0042"


def test_a_bare_superseded_status_composes_the_pointer_from_its_own_field(tmp_path):
    """AC-0013: a bare `Status: Superseded` plus a populated `Superseded by:`
    still renders a supersession pointer, pinned independently of any one
    record. `_status_token` alone cannot see the target once `Status` carries
    only the lifecycle token."""
    (tmp_path / "0001-r.md").write_text(
        "# ADR-0001: T\n\n- **Status:** Superseded\n- **Date:** 2026-01-01\n"
        "- **Superseded by:** ADR-0042\n", encoding="utf-8", newline="\n")
    rows = [r for r in _load().render(tmp_path, record_type="adr").splitlines()
            if r.startswith("| 0")]
    assert rows, "no record row rendered"
    assert rows[0].split(" | ")[2] == "Superseded by ADR-0042"


def test_a_bare_superseded_status_with_no_pointer_field_stays_bare(tmp_path):
    """No `Superseded by:` field: the bare token renders with nothing composed in."""
    _write(tmp_path, "0001-r.md", "ADR-0001: T", status="Superseded")
    rows = [r for r in _load().render(tmp_path, record_type="adr").splitlines()
            if r.startswith("| 0")]
    assert rows, "no record row rendered"
    assert rows[0].split(" | ")[2] == "Superseded"


def test_a_none_valued_superseded_by_field_composes_nothing(tmp_path):
    """The template's `none` sentinel names no target, so nothing is composed."""
    (tmp_path / "0001-r.md").write_text(
        "# ADR-0001: T\n\n- **Status:** Superseded\n- **Date:** 2026-01-01\n"
        "- **Superseded by:** none\n", encoding="utf-8", newline="\n")
    rows = [r for r in _load().render(tmp_path, record_type="adr").splitlines()
            if r.startswith("| 0")]
    assert rows, "no record row rendered"
    assert rows[0].split(" | ")[2] == "Superseded"


def test_a_superseded_by_value_with_both_escaping_classes_renders_inert(tmp_path):
    """AC-0032: a value carrying both the cell-breaking set (`|[]<>`) and the
    destination-terminating set (`) # ? ` whitespace`) in one value. A
    single-class fixture cannot tell `_escape_cell` from `_escape_destination`:
    both neutralize `|`/`[`/`]` (the destination escaper via percent-encoding),
    so only a destination-only character exposes the wrong escaper -- it would
    come out percent-encoded instead of literal. The status cell already runs
    through `_escape_cell(status)`, so composing the pointer ahead of that call
    is what makes this pass with no change to the emission code."""
    value = "ADR-0109|[x]<y>(z) #h?"
    (tmp_path / "0001-r.md").write_text(
        "# ADR-0001: T\n\n- **Status:** Superseded\n- **Date:** 2026-01-01\n"
        f"- **Superseded by:** {value}\n", encoding="utf-8", newline="\n")
    rows = [r for r in _load().render(tmp_path, record_type="adr").splitlines()
            if r.startswith("| 0")]
    assert rows, "no record row rendered"
    cell = rows[0].split(" | ")[2]
    # Cell-breaking characters neutralized: raw `|` would split the row, raw
    # `[`/`]` would open a link, raw `<`/`>` would open markup.
    assert cell == r"Superseded by ADR-0109\|\[x\]&lt;y&gt;(z) #h?"
    # Destination-terminating characters stay literal. Percent-encoding them
    # (`%28`, `%23`) would prove `_escape_destination` ran instead -- wrong for
    # a value that never becomes a link destination.
    assert "(z) #h?" in cell
    assert "%28" not in cell and "%23" not in cell and "%3F" not in cell.upper()


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
    import contextlib
    import io
    err = io.StringIO()
    with contextlib.redirect_stderr(err):
        code = _load().main(list(argv))
    return code, err.getvalue()


def test_check_writes_nothing_and_reports_zero_when_the_index_matches(tmp_path):
    """AC16 + AC17."""
    _write(tmp_path, "0001-r.md", "ADR-0001: T")
    assert _main(str(tmp_path))[0] == 0
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
    victim = tmp_path / "victim.txt"
    victim.write_text("DO NOT OVERWRITE\n", encoding="utf-8", newline="\n")
    recs = tmp_path / "recs"
    recs.mkdir()
    _write(recs, "0001-r.md", "ADR-0001: T")
    try:
        pathlib.Path(recs / "README.md").symlink_to(victim)
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
    # Write mode, not --check: --check on a directory with no index yet reports
    # divergence, which would mask the exit code this case is about.
    code, err = _main(str(tmp_path))
    assert code == 0, "a malformed record warns; it does not fail the run"
    assert "0002-big.md" in err
    assert "ordinal" in err
    rows = [r for r in _load().render(tmp_path, record_type="adr").splitlines()
            if r.startswith("| 0")]
    assert len(rows) == 1, "AC2: the malformed record must contribute no row"


# --- regressions for the second security round ---

def test_a_symlinked_record_directory_is_refused(tmp_path):
    """Resolving a symlinked record directory would index one tree and write another."""
    victim = tmp_path / "victimdir"
    victim.mkdir()
    (victim / "README.md").write_text("DO NOT OVERWRITE\n", encoding="utf-8", newline="\n")
    _write(victim, "0001-r.md", "ADR-0001: X")
    try:
        pathlib.Path(tmp_path / "linkdir").symlink_to(victim)
    except OSError:
        pytest.skip("symlinks unavailable")
    code, err = _main("--type", "adr", str(tmp_path / "linkdir"))
    assert code != 0
    assert "symlink" in err
    assert (victim / "README.md").read_text(encoding="utf-8") == "DO NOT OVERWRITE\n"


def test_an_ordinary_directory_under_a_symlinked_ancestor_still_works(tmp_path):
    """Only the supplied directory is checked: macOS resolves /var through a link."""
    real, link = tmp_path / "real", tmp_path / "link"
    real.mkdir()
    inner = real / "recs"
    inner.mkdir()
    _write(inner, "0001-r.md", "ADR-0001: Fine")
    try:
        pathlib.Path(link).symlink_to(real)
    except OSError:
        pytest.skip("symlinks unavailable")
    assert _main(str(link / "recs"))[0] == 0
    # Assert where it landed, not just that it succeeded.
    assert (inner / "README.md").is_file()


def test_an_empty_status_does_not_capture_the_following_line(tmp_path):
    """The `\\s*` defect lived in two patterns; repairing one left the other."""
    (tmp_path / "0001-a.md").write_text(
        "# RFC-0001: Empty status\n\n- **Status:**\n- **Date opened:** 2026-01-01\n"
        "- **Date closed:**\n", encoding="utf-8", newline="\n")
    rows = [r for r in _load().render(tmp_path, record_type="rfc").splitlines()
            if r.startswith("| 0")]
    assert rows, "no record row rendered"
    assert "Date opened" not in rows[0], f"status captured the next line: {rows[0]}"
    assert rows[0].split(" | ")[2] == ""


def test_an_unfilled_closing_date_is_not_filled_from_git(tmp_path):
    """A record has an add event; an unfilled closing date means no closing event."""
    d = _git_repo(tmp_path)
    (d / "0001-a.md").write_text(
        "# RFC-0001: Open\n\n- **Status:** Open\n- **Date opened:** 2026-01-01\n"
        "- **Date closed:** YYYY-MM-DD\n", encoding="utf-8", newline="\n")
    subprocess.run(["git", "add", "-A"], cwd=d, check=True)
    env = {**os.environ, "GIT_COMMITTER_DATE": "2024-04-04T00:00:00"}
    subprocess.run(["git", "commit", "-qm", "x", "--date=2024-04-04T00:00:00"],
                   cwd=d, check=True, env=env)
    rows = [r for r in _load().render(d, record_type="rfc").splitlines()
            if r.startswith("| 0")]
    assert rows, "no record row rendered"
    assert rows[0].split(" | ")[4].rstrip(" |") == "", f"open RFC shown closed: {rows[0]}"


def test_cell_text_cannot_open_a_raw_html_tag(tmp_path):
    """A record-controlled title must not introduce markup in an adopter's renderer."""
    _write(tmp_path, "0003-x.md", "ADR-0003: <img src=x onerror=alert(1)>")
    rows = [r for r in _load().render(tmp_path, record_type="adr").splitlines()
            if r.startswith("| 0")]
    assert rows, "no record row rendered"
    assert "<img" not in rows[0]
    assert "&lt;img" in rows[0]


def test_angle_brackets_inside_a_code_span_are_left_alone(tmp_path):
    """CommonMark treats raw HTML as literal in a code span; escaping corrupts it."""
    _write(tmp_path, "0004-y.md", "ADR-0004: `packs/<pack>/tests/` is the home")
    rows = [r for r in _load().render(tmp_path, record_type="adr").splitlines()
            if r.startswith("| 0")]
    assert rows, "no record row rendered"
    assert "`packs/<pack>/tests/`" in rows[0]
    assert "&lt;pack&gt;" not in rows[0]


# --- regressions for the third round: every one of these was a repair-origin defect ---

def test_a_symlinked_scratch_path_cannot_be_written_through(tmp_path):
    """The first atomic-write fix created the unguarded twin of the target check."""
    victim = tmp_path / "victim.txt"
    victim.write_text("DO NOT OVERWRITE\n", encoding="utf-8", newline="\n")
    recs = tmp_path / "recs"
    recs.mkdir()
    _write(recs, "0001-r.md", "ADR-0001: X")
    try:
        pathlib.Path(recs / ".README.md.index-records").symlink_to(victim)
    except OSError:
        pytest.skip("symlinks unavailable")
    assert _main(str(recs))[0] == 0
    assert victim.read_text(encoding="utf-8") == "DO NOT OVERWRITE\n"
    index = recs / "README.md"
    assert index.is_file() and not index.is_symlink()


def test_a_successful_write_leaves_no_scratch_file(tmp_path):
    """A unique scratch must not become litter in an adopter's record directory."""
    _write(tmp_path, "0001-r.md", "ADR-0001: X")
    assert _main(str(tmp_path))[0] == 0
    assert [p.name for p in tmp_path.iterdir() if "index-records-" in p.name] == []


def test_an_absent_closing_date_is_not_filled_from_git(tmp_path):
    """The opening-only rule must hold for absence, not only for the placeholder."""
    d = _git_repo(tmp_path)
    (d / "0001-a.md").write_text(
        "# RFC-0001: Open\n\n- **Status:** Open\n- **Date opened:** 2026-01-01\n",
        encoding="utf-8", newline="\n")
    subprocess.run(["git", "add", "-A"], cwd=d, check=True)
    env = {**os.environ, "GIT_COMMITTER_DATE": "2024-04-04T00:00:00"}
    subprocess.run(["git", "commit", "-qm", "x", "--date=2024-04-04T00:00:00"],
                   cwd=d, check=True, env=env)
    rows = [r for r in _load().render(d, record_type="rfc").splitlines()
            if r.startswith("| 0")]
    assert rows, "no record row rendered"
    assert rows[0].split(" | ")[4].rstrip(" |") == "", f"open RFC shown closed: {rows[0]}"


def test_an_unclosed_code_span_does_not_suppress_html_escaping(tmp_path):
    """An odd backtick count leaves the trailing segment outside a span."""
    _write(tmp_path, "0005-b.md", "ADR-0005: Use `npm audit <img src=x onerror=alert(1)>")
    rows = [r for r in _load().render(tmp_path, record_type="adr").splitlines()
            if r.startswith("| 0")]
    assert rows, "no record row rendered"
    assert "<img" not in rows[0]
    assert "&lt;img" in rows[0]


def test_an_unreadable_index_target_is_named_not_a_traceback(tmp_path):
    """The target read was the one read outside every handler."""
    _write(tmp_path, "0001-r.md", "ADR-0001: X")
    (tmp_path / "README.md").write_bytes(b"\xff\xfe not utf-8")
    code, err = _main("--check", str(tmp_path))
    assert code != 0
    assert "cannot read" in err


_SHIPPED_HELPERS = (
    ROOT / "packs/governance-extras/.apm/skills/new-adr/scripts/_record_paths.py",
    ROOT / "packs/governance-extras/.apm/skills/new-rfc/scripts/_record_paths.py",
)


def test_the_two_shipped_generator_copies_stay_byte_identical():
    """They were identical until one skill's copy was changed alone.

    Nothing pinned it, so the divergence passed every gate: the frozen-literal
    check above runs each copy independently and never compares them. The
    sibling `next-ordinal.py` pair has carried this assertion for longer
    (`packs/governance-extras/tests/skills/new-adr/test_next_ordinal.py`), and
    the generator pair needs it for the same reason — one confinement change
    landing in one copy leaves the other reading records the old way.
    """
    first, second = (path.read_bytes() for path in _SHIPPED_COPIES)
    assert first == second


def test_the_two_shipped_confinement_helpers_stay_byte_identical():
    """One definition per shipped skill, kept identical rather than merged.

    A single shared module is not reachable: each skill's scripts run standalone
    from their own projected directory, and a pack-level `shared-libs/` is not
    projected. Two copies is the shape the projection forces; this assertion is
    what keeps "two copies" from becoming "two implementations".
    """
    first, second = (path.read_bytes() for path in _SHIPPED_HELPERS)
    assert first == second


def _render_one(tmp_path, field_line: str, newline: str = "\n") -> str:
    """Render a one-record directory and return its status cell."""
    (tmp_path / "0001-r.md").write_text(
        "# ADR-0001: T\n\n- **Status:** Superseded\n- **Date:** 2026-01-01\n"
        f"{field_line}\n", encoding="utf-8", newline=newline)
    rows = [r for r in _load().render(tmp_path, record_type="adr").splitlines()
            if r.startswith("| 0")]
    assert rows, "no record row rendered"
    return rows[0].split(" | ")[2]


def test_an_embedded_carriage_return_does_not_reach_the_status_cell(tmp_path):
    """AC-0032's same-line pin, against the character that actually breaks it.

    `_escape_cell` neutralizes no line break, and CommonMark treats a bare CR
    as a line ending -- so a CR reaching the cell terminates the table row and
    everything after it renders as page text. `.` under `re.MULTILINE` excludes
    LF but *matches* CR, so the same-line read was not same-line for CR.

    The value is refused rather than sanitised: a field carrying a control
    character is malformed, and rendering a bare `Superseded` is the
    fail-closed outcome.
    """
    cell = _render_one(tmp_path, "- **Superseded by:** ADR-0109\rINJECTED")
    assert "\r" not in cell
    assert "INJECTED" not in cell
    assert cell == "Superseded"


def test_a_crlf_record_still_reads_its_superseded_by_field(tmp_path):
    """The discriminating negative for the test above.

    Refusing every value with a CR in it would also refuse every field in a
    CRLF checkout, which this repository supports. A trailing CR is a line
    ending; only an embedded one is an injection.
    """
    cell = _render_one(
        tmp_path, "- **Superseded by:** ADR-0109", newline="\r\n")
    assert cell == "Superseded by ADR-0109"


def test_an_empty_superseded_by_field_leaves_the_bare_token(tmp_path):
    """A present-but-empty field composed a dangling `Superseded by ` pointer."""
    cell = _render_one(tmp_path, "- **Superseded by:**")
    assert cell == "Superseded"
