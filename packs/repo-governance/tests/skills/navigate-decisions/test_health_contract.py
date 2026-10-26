"""Contract tests for the navigate-decisions ``health`` subcommand.

Each test names the acceptance criterion it proves.  Fixture record trees are
built in ``tmp_path`` from strings; the frozen ``health-hostile`` fixture is
only read and copied, and the symbolic link and FIFO are made in the copy.
"""

from __future__ import annotations

import builtins
import errno
import hashlib
import importlib.util
import io
import json
import os
import pathlib
import shutil
import socket
import stat
import subprocess
import sys
import tempfile
import unicodedata
from contextlib import redirect_stdout
from datetime import date
from typing import Any

import pytest

sys.dont_write_bytecode = True
HERE = pathlib.Path(__file__).resolve().parent
SCRIPTS = HERE.parents[2] / ".apm/skills/navigate-decisions/scripts"
HOSTILE = HERE / "fixtures" / "health-hostile"
_SPEC = importlib.util.spec_from_file_location(
    "repo_governance_navigate_decisions_health", SCRIPTS / "navigate_decisions.py"
)
assert _SPEC is not None and _SPEC.loader is not None
NAV = importlib.util.module_from_spec(_SPEC)
_SPEC.loader.exec_module(NAV)

TODAY = "2026-10-26"
BANNED = {"Cc", "Cf", "Zl", "Zp", "Co", "Cs"}

ACCEPTED_PROSE = (
    "# ADR-0001: Prose\n\n- **Status:** Accepted\n\n## Consequences\n\n"
    "**Revisit if:** the team grows.\n"
)


def adr(
    n: int = 1,
    *,
    status: str = "Accepted",
    header: str = "",
    consequences: str | None = None,
    confirmation: str | None = None,
    title: str = "Title",
    extra: str = "",
) -> str:
    """Build an ADR text; ``consequences`` and ``confirmation`` are raw bodies."""
    text = f"# ADR-{n:04d}: {title}\n\n- **Status:** {status}\n{header}\n"
    text += extra
    if consequences is not None:
        text += f"## Consequences\n\n{consequences}\n\n"
    if confirmation is not None:
        text += f"## Confirmation\n\n{confirmation}\n"
    return text


def revisit(body: str) -> str:
    """A ``Consequences`` body holding a one-line key line."""
    return f"**Revisit if:** {body}"


def signal(body: str) -> str:
    """A ``Confirmation`` body with one Signal line."""
    return f"- **Mode:** lint\n- **Signal:** {body}\n- **Owner:** @x"


def make_corpus(
    tmp_path: pathlib.Path, adrs: list[str] | dict[int, str], rfcs: dict[int, str] | None = None
) -> pathlib.Path:
    """Write ADRs (and RFCs) under ``tmp_path`` and return the root."""
    items = adrs if isinstance(adrs, dict) else dict(enumerate(adrs, start=1))
    adr_dir = tmp_path / "docs" / "adr"
    adr_dir.mkdir(parents=True, exist_ok=True)
    for n, text in items.items():
        (adr_dir / f"{n:04d}-x.md").write_text(text, encoding="utf-8")
    if rfcs:
        rfc_dir = tmp_path / "docs" / "rfc"
        rfc_dir.mkdir(parents=True, exist_ok=True)
        for n, text in rfcs.items():
            (rfc_dir / f"{n:04d}-y.md").write_text(text, encoding="utf-8")
    return tmp_path


def run_main(argv: list[str]) -> tuple[int, str]:
    """Run ``main`` and return (exit code, stdout text)."""
    buf = io.StringIO()
    with redirect_stdout(buf):
        code = NAV.main(argv)
    return code, buf.getvalue()


def run_health(root: pathlib.Path, today: str = TODAY) -> dict[str, Any]:
    """Run ``main(["health", ...])`` and return the parsed stdout JSON."""
    _, out = run_main(["health", "--root", str(root), "--today", today])
    return json.loads(out)


def by_id(out: dict[str, Any]) -> dict[str, dict[str, Any]]:
    return {t["id"]: t for t in out["triggers"]}


def one_trigger(tmp_path: pathlib.Path, body: str, today: str = TODAY) -> dict[str, Any]:
    """Health trigger entry for a single ADR whose Consequences is ``body``."""
    out = run_health(make_corpus(tmp_path, [adr(consequences=body)]), today)
    return out["triggers"][0]


def signal_result(tmp_path: pathlib.Path, body: str, files: list[str] | None = None,
                  dirs: list[str] | None = None) -> dict[str, Any]:
    """Health ``signal_paths`` for one ADR whose Signal holds ``body``."""
    root = make_corpus(tmp_path, [adr(consequences=revisit("x"), confirmation=signal(body))])
    for d in dirs or []:
        (root / d).mkdir(parents=True, exist_ok=True)
    for f in files or []:
        (root / f).parent.mkdir(parents=True, exist_ok=True)
        (root / f).write_text("x", encoding="utf-8")
    result: dict[str, Any] = run_health(root)["signal_paths"]
    return result


def paths(items: list[dict[str, str]]) -> list[str]:
    return [i["path"] for i in items]


def copy_hostile(tmp_path: pathlib.Path, *, link: bool = True, fifo: bool = False) -> pathlib.Path:
    """Copy the hostile fixture and add the symbolic link (and FIFO) to the copy."""
    dest = tmp_path / "repo"
    shutil.copytree(HOSTILE, dest)
    if link:
        if not hasattr(os, "symlink"):
            pytest.skip("symlinks unavailable")
        (dest / "linked").symlink_to("tools")
    if fifo:
        if not hasattr(os, "mkfifo"):
            pytest.skip("mkfifo unavailable")
        os.mkfifo(dest / "tools" / "pipe")
    return dest


def all_strings(value: Any) -> list[str]:
    if isinstance(value, str):
        return [value]
    if isinstance(value, dict):
        return [s for v in value.values() for s in all_strings(v)]
    if isinstance(value, list):
        return [s for v in value for s in all_strings(v)]
    return []


def tree_state(root: pathlib.Path) -> dict[str, tuple[str, str | None]]:
    """Map every entry's relative path to (type, sha256 of regular files)."""
    state: dict[str, tuple[str, str | None]] = {}
    for dirpath, dirnames, filenames in os.walk(root):
        for name in dirnames + filenames:
            p = pathlib.Path(dirpath) / name
            st = os.lstat(p)
            rel = p.relative_to(root).as_posix()
            if stat.S_ISREG(st.st_mode):
                state[rel] = ("file", hashlib.sha256(p.read_bytes()).hexdigest())
            elif stat.S_ISDIR(st.st_mode):
                state[rel] = ("dir", None)
            elif stat.S_ISLNK(st.st_mode):
                state[rel] = ("link", None)
            else:
                state[rel] = ("special", None)
    return state


class ProbeSpy:
    """Record filesystem calls made once the health probe phase starts."""

    def __init__(self, monkeypatch: pytest.MonkeyPatch, *, always: bool = False) -> None:
        self.events: list[tuple[str, str, Any, bool]] = []
        self.active = always
        self.in_helper = False
        fs = NAV._get_file_safety()
        orig_root_names = NAV._root_entry_names
        orig_validate = fs.validate_confined_directory

        def start(*a: Any, **k: Any) -> Any:
            self.active = True
            return orig_root_names(*a, **k)

        def validate(root: Any, path: Any) -> Any:
            self.record("validate", path, root)
            self.in_helper = True
            try:
                return orig_validate(root, path)
            finally:
                self.in_helper = False

        monkeypatch.setattr(NAV, "_root_entry_names", start)
        monkeypatch.setattr(fs, "validate_confined_directory", validate)
        for mod, name in ((os, "lstat"), (os, "stat"), (os, "scandir"), (os, "listdir"),
                          (builtins, "open"), (io, "open")):
            self.wrap(monkeypatch, mod, name)
        orig_os_open = os.open

        def os_open(path: Any, flags: int, *a: Any, **k: Any) -> Any:
            self.record("os.open", path, flags)
            return orig_os_open(path, flags, *a, **k)

        monkeypatch.setattr(os, "open", os_open)
        orig_resolve = pathlib.Path.resolve

        def resolve(path_self: pathlib.Path, *a: Any, **k: Any) -> Any:
            self.record("resolve", path_self, None)
            return orig_resolve(path_self, *a, **k)

        monkeypatch.setattr(pathlib.Path, "resolve", resolve)

    def record(self, kind: str, path: Any, extra: Any) -> None:
        if self.active:
            self.events.append((kind, os.fspath(path) if not isinstance(path, int) else "", extra,
                                self.in_helper))

    def wrap(self, monkeypatch: pytest.MonkeyPatch, mod: Any, name: str) -> None:
        orig = getattr(mod, name)

        def spy(path: Any = ".", *a: Any, **k: Any) -> Any:
            mode = a[0] if a else k.get("mode", "r")
            self.record(f"{mod.__name__}.{name}", path, mode)
            return orig(path, *a, **k)

        monkeypatch.setattr(mod, name, spy)


# ── The health command ───────────────────────────────────────────────────────


def test_health_reports_schema_and_today(tmp_path):  # AC-0001
    """AC-0001: schema, status, today and accepted count."""
    out = run_health(make_corpus(tmp_path, adrs=[ACCEPTED_PROSE]), "2026-10-26")
    assert out["schema"] == "decision-navigation.health.v1"
    assert out["status"] == "ok" and out["today"] == "2026-10-26"
    assert out["accepted_adr_count"] == 1


def test_query_surface_unchanged_and_health_refused():
    """AC-0002: query keeps five operations and refuses ``health``."""
    parser = NAV._build_parser()
    sub = next(a for a in parser._actions if a.dest == "command")
    op = next(a for a in sub.choices["query"]._actions if a.dest == "operation")
    assert list(op.choices) == ["summary", "search", "record", "lineage", "context"]
    refused = NAV.run_query(HOSTILE, {"operation": "health"})
    assert refused["status"] == "error" and refused["error"]["code"] == "unknown_operation"


def test_admission_failure_carries_query_error_code(tmp_path):
    """AC-0003: an admission error keeps the code ``query`` reports, with no findings."""
    root = make_corpus(tmp_path, [ACCEPTED_PROSE.replace("# ADR-0001", "ADR-0001")])
    expected = NAV.run_query(root, {"operation": "summary"})["error"]["code"]
    out = run_health(root)
    assert out["status"] == "error" and out["error"]["code"] == expected
    assert "triggers" not in out and "signal_paths" not in out


@pytest.mark.parametrize("bad", ["2026-02-30", "2026/10/26", "20261026", "2026-1-5", "", "x"])
def test_invalid_today(tmp_path, bad):
    """AC-0004: a non-date ``--today`` is ``invalid_today`` with no findings."""
    out = run_health(make_corpus(tmp_path, [ACCEPTED_PROSE]), bad)
    assert out["status"] == "error" and out["error"]["code"] == "invalid_today"
    assert "triggers" not in out and "accepted_adr_count" not in out


def test_every_accepted_adr_listed_once(tmp_path):
    """AC-0005: each accepted ADR once with a class; no other record."""
    root = make_corpus(
        tmp_path,
        {1: adr(1), 2: adr(2, status="Superseded"), 3: adr(3, status="Proposed"),
         4: adr(4, status="Accepted (amended)"), 5: adr(5, status="accepted")},
        rfcs={1: "# RFC-0001: R\n\n- **Status:** Accepted\n"},
    )
    out = run_health(root)
    assert [t["id"] for t in out["triggers"]] == ["ADR-0001", "ADR-0004"]
    assert out["accepted_adr_count"] == 2
    assert all(t["class"] == "none" for t in out["triggers"])


def test_due_item_names_passed_dates_and_excerpt(tmp_path):
    """AC-0006: due names the passed mentions and the cleaned excerpt."""
    t = one_trigger(tmp_path, revisit("reviewed by 2025-01-31 or after 2027-01-01 again."))
    assert t["class"] == "due"
    assert t["dates"] == ["2025-01-31"]
    assert t["excerpt"] == "reviewed by 2025-01-31 or after 2027-01-01 again."


def test_last_day_today_not_passed(tmp_path):
    """AC-0007: last day == today is not passed; the day before is."""
    assert one_trigger(tmp_path / "a", revisit("2026-10-26"))["class"] == "scheduled"
    assert one_trigger(tmp_path / "b", revisit("2026-10-25"))["class"] == "due"
    assert one_trigger(tmp_path / "c", revisit("October 2026"))["class"] == "scheduled"
    assert one_trigger(tmp_path / "d", revisit("September 2026"))["class"] == "due"
    assert one_trigger(tmp_path / "e", revisit("Q4 2026"), "2026-12-31")["class"] == "scheduled"
    assert one_trigger(tmp_path / "f", revisit("Q3 2026"))["class"] == "due"
    assert one_trigger(tmp_path / "g", revisit("2026"), "2026-12-31")["class"] == "scheduled"
    assert one_trigger(tmp_path / "h", revisit("2026"), "2027-01-01")["class"] == "due"


@pytest.mark.parametrize(
    ("text", "expected"),
    [
        ("2026-10-05", [("2026-10-05", date(2026, 10, 5))]),
        ("2026-02-30", []),
        ("2026-02", [("2026-02", date(2026, 2, 28))]),
        ("2024-02", [("2024-02", date(2024, 2, 29))]),
        ("2026-13", []),
        ("October 5, 2026", [("October 5, 2026", date(2026, 10, 5))]),
        ("5 October 2026", [("5 October 2026", date(2026, 10, 5))]),
        ("October 2026", [("October 2026", date(2026, 10, 31))]),
        ("october 2026", [("2026", date(2026, 12, 31))]),
        ("Q1 2026", [("Q1 2026", date(2026, 3, 31))]),
        ("Q2 2026", [("Q2 2026", date(2026, 6, 30))]),
        ("Q3 2026", [("Q3 2026", date(2026, 9, 30))]),
        ("Q4 2026", [("Q4 2026", date(2026, 12, 31))]),
        ("Q5 2026", [("2026", date(2026, 12, 31))]),
        ("2026", [("2026", date(2026, 12, 31))]),
        ("1899", []),
        ("2100", []),
        ("February 30, 2026", [("2026", date(2026, 12, 31))]),
        ("ADR-2024", []),
        ("20261", []),
        ("x_2026", []),
        ("2026_x", []),
        ("2026-10-05x", []),
        ("by 2026.", [("2026", date(2026, 12, 31))]),
        ("(2026-10-05)", [("2026-10-05", date(2026, 10, 5))]),
    ],
)
def test_date_mention_grammar(text, expected):
    """AC-0008: each date form is recognised and joined digit runs are not."""
    assert NAV._date_mentions(text) == expected


@pytest.mark.parametrize(
    ("text", "expected"),
    [
        ("PyJWT>=2.14.0", ["2.14.0"]),
        ("`>=0.47`", [">=0.47"]),
        ("v1.2.3", ["v1.2.3"]),
        ("~=1.4+", ["~=1.4+"]),
        ("^2.0", ["^2.0"]),
        ("==3.1.4", ["==3.1.4"]),
        ("<=5.0", ["<=5.0"]),
        ("v2", ["v2"]),
        ("reaches 2.0.", ["2.0"]),
        ("gemini-2.5-flash-lite", []),
        ("D1.2", []),
        ("1.2.3-rc1", []),
        ("1.2.x", []),
        ("v2.", []),
        ("v2a", []),
        ("dev1.2", []),
        ("1.23", ["1.23"]),
        ("see 1.2.3 and v4", ["1.2.3", "v4"]),
    ],
)
def test_version_mention_grammar(text, expected):
    """AC-0009: version forms are recognised and near-misses are not."""
    assert NAV._version_mentions(text) == expected


def test_version_item_lists_versions(tmp_path):
    """AC-0009: a version item names its versions; near-misses make it ``judge``."""
    t = one_trigger(tmp_path / "a", revisit("PyJWT>=2.14.0 is replaced"))
    assert t["class"] == "version" and t["versions"] == ["2.14.0"]
    t2 = one_trigger(tmp_path / "b", revisit("gemini-2.5-flash-lite or D1.2 changes"))
    assert t2["class"] == "judge" and t2["versions"] == []


def test_revisit_read_only_from_consequences(tmp_path):
    """AC-0010: a ``Revisit if:`` line elsewhere does not change the class."""
    text = adr(
        extra="## Context\n\n**Revisit if:** 2020-01-01\n\n## Decision\n\n- **Revisit if:** v9.9\n\n",
        consequences="No trigger here.",
    )
    out = run_health(make_corpus(tmp_path, [text]))
    assert out["triggers"][0]["class"] == "none"


def test_list_and_wrapped_triggers_read_whole(tmp_path):
    """AC-0011: the blank-then-list form and a wrapped line are read whole."""
    listed = one_trigger(tmp_path / "a", "**Revisit if:**\n\n- the team grows\n- or 2025-02-01 passes\n\nAfter.")
    assert listed["class"] == "due" and listed["dates"] == ["2025-02-01"]
    wrapped = one_trigger(tmp_path / "b", "- **Revisit if:** the team grows\nand later on 2025-03-01\n\nAfter.")
    assert wrapped["class"] == "due"
    indented = one_trigger(tmp_path / "c", "**Revisit if:**\n\n  indented 2025-03-01\n  more\n\nAfter 2099-01-01.")
    assert indented["class"] == "due" and "After" not in indented["excerpt"]


def test_trigger_text_forms(tmp_path):
    """AC-0011: key-line forms, empty triggers and ``stable`` markers."""
    nonblank = one_trigger(tmp_path / "a", "**Revisit if:**\nwrapped line 2025-01-01\n\nNext.")
    assert nonblank["class"] == "due" and nonblank["excerpt"] == "wrapped line 2025-01-01"
    assert one_trigger(tmp_path / "b", "**Revisit if:**\n\nplain paragraph 2025-01-01")["class"] == "none"
    assert one_trigger(tmp_path / "c", "**Revisit if:** <!-- note -->\n\nAfter")["class"] == "none"
    assert one_trigger(tmp_path / "d", "**Revisit if:**\n**Mode:** x")["class"] == "none"
    stable = one_trigger(tmp_path / "e", revisit("`stable — no foreseeable trigger`"))
    assert stable["class"] == "stable"
    assert one_trigger(tmp_path / "f", revisit("Stable: never"))["class"] == "stable"
    assert one_trigger(tmp_path / "g", revisit("stability matters"))["class"] == "judge"
    comment = one_trigger(tmp_path / "h", revisit("2025-01-01 <!-- 2099-01-01 -->"))
    assert comment["excerpt"] == "2025-01-01"
    crlf = run_health(make_corpus(tmp_path / "i", [adr(consequences="**Revisit if:** 2025-01-01").replace("\n", "\r\n")]))
    assert crlf["triggers"][0]["excerpt"] == "2025-01-01"
    blank = one_trigger(tmp_path / "j", "**Revisit if:**   ")
    assert blank["class"] == "none"
    first_wins = one_trigger(tmp_path / "k", "**Revisit if:** the team grows\n\n- **Revisit if:** 2025-01-01")
    assert first_wins["class"] == "judge"


def test_class_priority(tmp_path):
    """AC-0005: due before version before scheduled before stable before judge."""
    assert one_trigger(tmp_path / "a", revisit("v2.0 or 2025-01-01"))["class"] == "due"
    assert one_trigger(tmp_path / "b", revisit("v2.0 or 2099-01-01"))["class"] == "version"
    assert one_trigger(tmp_path / "c", revisit("2099-01-01"))["class"] == "scheduled"
    assert one_trigger(tmp_path / "d", revisit("stable"))["class"] == "stable"


SUPERSEDED = adr(3, status="Superseded", header="- **Superseded by:** ADR-0004\n")


def test_header_citation_listed_once(tmp_path):
    """AC-0012: each header citation is listed once, with successors and citing record."""
    root = make_corpus(
        tmp_path,
        {3: SUPERSEDED, 4: adr(4, header="- **Supersedes:** ADR-0003\n"),
         5: adr(5, header="- **Related:** ADR-0003 and again ADR-0003\n")},
        rfcs={1: "# RFC-0001: R\n\n- **Status:** Accepted\n- **Related:** ADR-0003\n"},
    )
    out = run_health(root)
    assert out["superseded_citations"] == [
        {"superseded": "ADR-0003", "successors": ["ADR-0004"], "cited_by": "ADR-0005"},
        {"superseded": "ADR-0003", "successors": ["ADR-0004"], "cited_by": "RFC-0001"},
    ]


def test_header_citation_exclusions(tmp_path):
    """AC-0013: body, successor, Supersedes fields and successor-naming headers yield none."""
    root = make_corpus(
        tmp_path,
        {
            3: SUPERSEDED,
            4: adr(4, header="- **Supersedes:** ADR-0003\n", extra="Body names ADR-0003.\n\n"),
            5: adr(5, header="- **Supersedes in part:** ADR-0003\n"),
            6: adr(6, header="- **Related:** ADR-0003 replaced by ADR-0004\n"),
            7: adr(7, extra="## Context\n\nBody cites ADR-0003 only.\n\n"),
            8: adr(8, status="Proposed", header="- **Related:** ADR-0003\n"),
            9: adr(9, header="- **Related:** ADR-00031 and xADR-0003\n"),
            10: adr(10, header="- **Supersedes:** ADR-0003\n"),
        },
    )
    assert run_health(root)["superseded_citations"] == []


def test_missing_signal_listed_once(tmp_path):
    """AC-0014: a missing candidate is listed once with its ADR, even if repeated."""
    res = signal_result(tmp_path, "`tools/gone.py` and `tools/gone.py` again", dirs=["tools"])
    assert res["missing"] == [{"id": "ADR-0001", "path": "tools/gone.py"}]
    assert res["invalid"] == []


def test_present_not_reported(tmp_path):
    """AC-0015: a present candidate is neither missing nor invalid."""
    res = signal_result(tmp_path, "`tools/here.py` and `tools/`", files=["tools/here.py"])
    assert res["missing"] == [] and res["invalid"] == [] and res["present_count"] == 2


def test_invalid_listed_never_missing(tmp_path):
    """AC-0016: invalid candidates carry a reason and never appear as missing."""
    res = signal_result(tmp_path, "`../out.py` and `/etc/passwd` and `tools/gone.py`",
                        dirs=["tools"])
    assert sorted(paths(res["invalid"])) == ["../out.py", "/etc/passwd"]
    assert {i["reason"] for i in res["invalid"]} == {"lexical"}
    assert paths(res["missing"]) == ["tools/gone.py"]


def test_symbolic_links_invalid(tmp_path):
    """AC-0017: any candidate through a symbolic link is invalid, never followed."""
    if not hasattr(os, "symlink"):
        pytest.skip("symlinks unavailable")
    root = make_corpus(tmp_path, [adr(consequences=revisit("x"), confirmation=signal(
        "`l-dir/x.py` `real/sub/l-mid/x.py` `l-file.py` `l-dir/` `l-missing.py`"))])
    (root / "real" / "sub").mkdir(parents=True)
    (root / "real" / "file.txt").write_text("x", encoding="utf-8")
    (root / "l-file.py").symlink_to("real/file.txt")  # inside the repository
    (root / "l-missing.py").symlink_to("nowhere")
    (root / "l-dir").symlink_to("real")
    (root / "real" / "sub" / "l-mid").symlink_to("..")
    out = run_health(root)["signal_paths"]
    inv = {i["path"]: i["reason"] for i in out["invalid"]}
    assert inv == {"l-file.py": "link", "l-missing.py": "link", "l-dir/x.py": "link",
                   "real/sub/l-mid/x.py": "link", "l-dir/": "link"}
    assert out["missing"] == []


@pytest.mark.parametrize(
    "bad",
    ["/ABS", "~/x.md", "C:/x.md", "a\\b.md", "docs/../x.md", "tools/a\x07b.md",
     "tools/a\u202eb.md", "tools//x.md", "./x.md", "tools/./x.md", "a/b/../c.md",
     "tools/a\ue000b.md"],
)
def test_lexically_invalid_backtick_candidates(tmp_path, bad):
    """AC-0018: lexically invalid backtick candidates are invalid, even if the file exists."""
    target = tmp_path / "exists.md"
    target.write_text("x", encoding="utf-8")
    text = str(target) if bad == "/ABS" else bad
    if bad == "/ABS" and ("\\" in text):
        pytest.skip("platform path")
    res = signal_result(tmp_path / "repo", f"`{text}`")
    assert len(res["invalid"]) == 1 and res["invalid"][0]["reason"] in {"lexical", "outside-root"}
    assert res["missing"] == [] and res["present_count"] == 0


def test_link_targets_resolve_from_adr_directory(tmp_path):
    """AC-0019: link targets resolve from ``docs/adr`` and may not leave the root."""
    body = ("[a](0001-notes/data.md) [b](../rfc/0001-y.md#frag) [c](../rfc/0002-gone.md?q=1 \"t\") "
            "[d](../../../outside.md) [e](#top) [f](https://example.com/x) [g](/abs/x.md) "
            "[h](docs/adr/../adr/0001-notes/data.md)")
    root = make_corpus(tmp_path, [adr(consequences=revisit("x"), confirmation=signal(body))],
                       rfcs={1: "# RFC-0001: R\n\n- **Status:** Draft\n"})
    (root / "docs" / "adr" / "0001-notes").mkdir()
    (root / "docs" / "adr" / "0001-notes" / "data.md").write_text("x", encoding="utf-8")
    res = run_health(root)["signal_paths"]
    assert sorted(paths(res["missing"])) == [
        "docs/adr/docs/adr/0001-notes/data.md", "docs/rfc/0002-gone.md"]
    inv = {i["path"]: i["reason"] for i in res["invalid"]}
    assert inv["../outside.md"] == "outside-root" and inv["/abs/x.md"] == "lexical"
    assert res["present_count"] == 2  # data.md and the rfc, the two forms merging per target


def test_backtick_and_link_merge_to_one_item(tmp_path):
    """AC-0014: a backtick span and a link naming one checked form are one signal item."""
    res = signal_result(tmp_path, "`docs/adr/0001-notes/data.md` and [d](0001-notes/data.md)")
    assert paths(res["missing"]) == ["docs/adr/0001-notes/data.md"]


def test_confinement_helper_validates_before_inspecting(tmp_path, monkeypatch):
    """AC-0020: root and each directory prefix are validated before entries inside it."""
    root = make_corpus(tmp_path, [adr(consequences=revisit("x"),
                                      confirmation=signal("`a/b/c/file.py`"))])
    (root / "a" / "b" / "c").mkdir(parents=True)
    (root / "a" / "b" / "c" / "file.py").write_text("x", encoding="utf-8")
    spy = ProbeSpy(monkeypatch)
    assert run_health(root)["signal_paths"]["present_count"] == 1
    validated: set[str] = set()
    inspected = []
    for kind, path, _, in_helper in spy.events:
        if kind == "validate":
            validated.add(path)
        elif kind == "os.lstat" and not in_helper:
            inspected.append(path)
            parent = str(pathlib.Path(path).parent)
            assert parent in validated, f"{path} inspected before {parent} was validated"
    assert inspected == [str(root / "a"), str(root / "a" / "b"), str(root / "a" / "b" / "c"),
                         str(root / "a" / "b" / "c" / "file.py")]


def test_helper_refusal_makes_candidate_invalid(tmp_path, monkeypatch):
    """AC-0020: a refusal by the confinement helper makes the candidate invalid."""
    root = make_corpus(tmp_path, [adr(consequences=revisit("x"),
                                      confirmation=signal("`tools/a.py`"))])
    (root / "tools").mkdir()
    fs = NAV._get_file_safety()
    orig = fs.validate_confined_directory

    def refuse(r: Any, p: Any) -> None:
        if pathlib.Path(p).name == "tools":
            raise fs.UnsafeContentError("refused")
        orig(r, p)

    monkeypatch.setattr(fs, "validate_confined_directory", refuse)
    res = run_health(root)["signal_paths"]
    assert res["invalid"] == [{"id": "ADR-0001", "path": "tools/a.py", "reason": "unconfined"}]
    assert res["missing"] == []


def test_no_candidate_is_opened_listed_or_executed(tmp_path, monkeypatch):
    """AC-0021: no candidate is opened, listed, imported or read during probing."""
    root = copy_hostile(tmp_path)
    spy = ProbeSpy(monkeypatch)
    refuse_process_starts(monkeypatch)
    before = set(sys.modules)
    assert run_health(root)["status"] == "ok"
    opened = [(k, p) for k, p, _, _ in spy.events
              if k in {"builtins.open", "io.open", "os.open", "os.scandir", "os.listdir"}]
    assert not [p for _, p in opened if "present-check" in p or "missing-check" in p
                or "linked" in p or "passwd" in p]
    assert set(sys.modules) == before


def test_probe_never_names_escaping_paths(tmp_path, monkeypatch):
    """AC-0047: no call names an invalid or escaping candidate; paths are root plus a prefix."""
    adr_text = adr(consequences=revisit("x"), confirmation=signal(
        "`/etc/passwd` `//host/share/x.md` `../../outside.md` `tools/present.py` "
        "[o](../../../outside.md) [n](0001-notes/data.md)"))
    root = make_corpus(tmp_path / "repo", [adr_text])
    (root / "tools").mkdir()
    (root / "tools" / "present.py").write_text("x", encoding="utf-8")
    (root / "docs" / "adr" / "0001-notes").mkdir()
    (root / "docs" / "adr" / "0001-notes" / "data.md").write_text("x", encoding="utf-8")
    spy = ProbeSpy(monkeypatch)
    res = run_health(root)["signal_paths"]
    assert len(res["invalid"]) == 4 and res["present_count"] == 2
    allowed = set()
    for cand in ("tools/present.py", "docs/adr/0001-notes/data.md"):
        parts = cand.split("/")
        allowed.update(str(root.joinpath(*parts[:i])) for i in range(1, len(parts) + 1))
    allowed.add(str(root))
    for kind, path, _, in_helper in spy.events:
        if kind in {"resolve"} and in_helper:
            continue
        if kind == "validate" or (kind in {"os.lstat", "os.stat"} and not in_helper):
            assert path in allowed, path
        for forbidden in ("passwd", "host", "outside"):
            assert forbidden not in path, (kind, path)


@pytest.mark.parametrize("failure", ["permission", "toolong"])
def test_inspection_error_is_invalid(tmp_path, monkeypatch, failure):
    """AC-0048: a permission or name-too-long error is invalid, never missing or present."""
    root = make_corpus(tmp_path, [adr(consequences=revisit("x"),
                                      confirmation=signal("`tools/a.py`"))])
    (root / "tools").mkdir()
    (root / "tools" / "a.py").write_text("x", encoding="utf-8")
    target = str(root / "tools")
    orig = os.lstat

    def failing(path: Any, *a: Any, **k: Any) -> Any:
        if os.fspath(path) == target:
            if failure == "permission":
                raise PermissionError(errno.EACCES, "denied")
            raise OSError(errno.ENAMETOOLONG, "too long")
        return orig(path, *a, **k)

    monkeypatch.setattr(os, "lstat", failing)
    res = run_health(root)["signal_paths"]
    assert res["invalid"] == [{"id": "ADR-0001", "path": "tools/a.py", "reason": "uninspectable"}]
    assert res["missing"] == [] and res["present_count"] == 0


def test_health_opens_nothing_for_writing(tmp_path, monkeypatch):
    """AC-0052: no file is opened for writing, appending or creating anywhere."""
    root = copy_hostile(tmp_path)
    spy = ProbeSpy(monkeypatch, always=True)

    def refuse(*a: Any, **k: Any) -> Any:
        raise AssertionError("tempfile used")

    for name in ("mkstemp", "NamedTemporaryFile", "mkdtemp"):
        monkeypatch.setattr(tempfile, name, refuse)
    before = tree_state(root)
    assert run_health(root)["status"] == "ok"
    assert tree_state(root) == before
    write_flags = os.O_WRONLY | os.O_RDWR | os.O_CREAT | os.O_APPEND | os.O_TRUNC
    for kind, _, extra, _ in spy.events:
        if kind == "os.open":
            assert not extra & write_flags
        if kind in {"builtins.open", "io.open"}:
            assert not set(str(extra)) & set("wax+")


def test_fifo_is_invalid_and_returns(tmp_path):
    """AC-0045: a FIFO named as a signal path is invalid and the command returns."""
    if not hasattr(os, "mkfifo"):
        pytest.skip("mkfifo unavailable")
    root = make_corpus(tmp_path, [adr(consequences=revisit("x"),
                                      confirmation=signal("`tools/pipe`"))])
    (root / "tools").mkdir()
    os.mkfifo(root / "tools" / "pipe")
    res = run_health(root)["signal_paths"]
    assert res["invalid"] == [{"id": "ADR-0001", "path": "tools/pipe", "reason": "special"}]


def test_hard_linked_file_is_invalid(tmp_path):
    """AC-0016: a regular file with more than one hard link is invalid."""
    root = make_corpus(tmp_path, [adr(consequences=revisit("x"),
                                      confirmation=signal("`tools/a.py`"))])
    (root / "tools").mkdir()
    (root / "tools" / "a.py").write_text("x", encoding="utf-8")
    os.link(root / "tools" / "a.py", root / "tools" / "b.py")
    res = run_health(root)["signal_paths"]
    assert res["invalid"] == [{"id": "ADR-0001", "path": "tools/a.py", "reason": "hard-link"}]


def test_regular_file_before_last_component_is_missing(tmp_path):
    """AC-0014: a regular file where a directory is expected means missing."""
    res = signal_result(tmp_path, "`tools/a.py/b.py`", files=["tools/a.py"])
    assert paths(res["missing"]) == ["tools/a.py/b.py"]


def test_unlocated_items_counted_not_listed(tmp_path):
    """AC-0022: unlocated items are counted, and are neither missing nor invalid."""
    res = signal_result(
        tmp_path, "`nowhere/file.py` `bare.py` `tools/here.py` `tools/gone.py`",
        files=["tools/here.py"])
    assert res["unlocated_count"] == 2 and res["present_count"] == 1
    assert paths(res["missing"]) == ["tools/gone.py"] and res["invalid"] == []


def test_candidate_extraction(tmp_path):
    """AC-0014: URL and scheme spans skip, line suffixes strip, drive letters stay."""
    body = ("`https://example.com/x` `git+ssh://host/x.git` `tools/cli.py:247` `tools/foo.py::test` "
            "`tools/a.py:3-9` `C:/x.md` `bare` `a b/c.py` `tools/*.py` `mailto:me@x.org` `.md`")
    res = signal_result(tmp_path, body, dirs=["tools"])
    assert sorted(paths(res["missing"])) == ["tools/a.py", "tools/cli.py", "tools/foo.py"]
    assert paths(res["invalid"]) == ["C:/x.md"]


def test_confirmation_presence_listed(tmp_path):
    """AC-0023: accepted ADRs without a Confirmation section are counted and named."""
    root = make_corpus(tmp_path, {
        1: adr(1, confirmation=signal("`a.py`")), 2: adr(2), 3: adr(3, status="Proposed"),
        4: adr(4, status="Superseded"), 5: adr(5)})
    nc = run_health(root)["no_confirmation"]
    assert nc == {"count": 2, "ids": ["ADR-0002", "ADR-0005"]}


def test_signal_text_boundaries(tmp_path):
    """AC-0014: signal text spans continuation lines up to the next Mode, Signal or Owner."""
    conf = ("- **Mode:** lint\n  - **Signal:** `tools/one.py` and\n    `tools/two.py`\n"
            "- **Signal:** `tools/three.py`\n- **Owner:** `tools/owner.py`\n- **Note:** `tools/note.py`")
    root = make_corpus(tmp_path, [adr(consequences=revisit("x"), confirmation=conf)])
    (root / "tools").mkdir()
    res = run_health(root)["signal_paths"]
    assert sorted(paths(res["missing"])) == ["tools/one.py", "tools/three.py", "tools/two.py"]


def test_reported_text_has_no_banned_characters(tmp_path, capsys):
    """AC-0024: no reported text, error object or stderr holds a removed category."""
    out = run_health(copy_hostile(tmp_path))
    strings = all_strings(out)
    assert strings
    assert not [s for s in strings if any(unicodedata.category(c) in BANNED for c in s)]
    excerpt = by_id(out)["ADR-0001"]["excerpt"]
    assert "\u202e" not in excerpt and "\x07" not in excerpt
    assert excerpt.startswith("the cache review set for 2025-01-31")
    broken = tmp_path / "broken"
    (broken / "docs" / "adr").mkdir(parents=True)
    (broken / "docs" / "adr" / "0001-\u202ex\x07.md").write_text("no heading\n", encoding="utf-8")
    err = run_health(broken)
    assert err["status"] == "error"
    assert not [s for s in all_strings(err) if any(unicodedata.category(c) in BANNED for c in s)]
    assert "u202e" in err["error"]["message"]
    captured = capsys.readouterr()
    assert not [c for c in captured.err if unicodedata.category(c) in BANNED]


def test_reported_text_is_cut_and_missing_paths_are_not(tmp_path):
    """AC-0046: reported text is at most 161 code points; valid missing paths are never cut."""
    long_trigger = "word " * 100
    long_title = "T" * 300
    exact = "tools/" + "a" * 151 + ".py"  # 160 code points
    assert len(exact) == 160
    root = make_corpus(tmp_path, [adr(
        title=long_title, consequences=revisit(long_trigger),
        confirmation=signal(f"`{exact}` `tools/{'b' * 200}.py`"))])
    (root / "tools").mkdir()
    out = run_health(root)
    t = out["triggers"][0]
    assert len(t["excerpt"]) == 161 and t["excerpt"].endswith("…")
    assert len(t["title"]) == 161
    assert paths(out["signal_paths"]["missing"]) == [exact]
    (bad,) = out["signal_paths"]["invalid"]
    assert bad["reason"] == "too-long" and len(bad["path"]) == 161
    assert all(len(s) <= 161 for s in all_strings({k: out[k] for k in (
        "triggers", "signal_paths", "superseded_citations", "no_confirmation")}))


def test_oversized_stdout_is_input_too_large(tmp_path):
    """AC-0050: a result over 524,288 stdout bytes prints ``input_too_large`` instead."""
    names = [f"tools/{i:04d}{'x' * 112}.py" for i in range(4000)]
    body = " ".join(f"`{n}`" for n in names)
    root = make_corpus(tmp_path, [adr(consequences=revisit("x"), confirmation=signal(body))])
    (root / "tools").mkdir()
    code, text = run_main(["health", "--root", str(root), "--today", TODAY])
    out = json.loads(text)
    assert code == 1 and out["status"] == "error" and out["error"]["code"] == "input_too_large"
    assert "signal_paths" not in out and len(text.encode("utf-8")) < 524288


def test_long_or_deep_candidates_invalid(tmp_path):
    """AC-0051: more than 160 code points or 32 segments is invalid; the limits themselves pass."""
    deep32 = "/".join(["a"] * 31 + ["b.md"])
    deep33 = "/".join(["a"] * 32 + ["b.md"])
    res = signal_result(tmp_path, f"`{deep32}` `{deep33}` `a/{'c' * 160}`", dirs=["a"])
    assert paths(res["missing"]) == [deep32]
    assert {i["reason"] for i in res["invalid"]} == {"too-long"}
    assert len(res["invalid"]) == 2


@pytest.mark.parametrize(("count", "ok"), [(5000, True), (5001, False)])
def test_candidate_occurrence_bound(tmp_path, count, ok):
    """AC-0025: the 5,001st occurrence is the first that yields ``input_too_large``."""
    body = " ".join(["`tools/a.py`"] * count)
    root = make_corpus(tmp_path, [adr(consequences=revisit("x"), confirmation=signal(body))])
    (root / "tools").mkdir()
    out = run_health(root)
    if ok:
        assert out["status"] == "ok" and len(out["signal_paths"]["missing"]) == 1
    else:
        assert out["error"]["code"] == "input_too_large" and "signal_paths" not in out
        assert out["error"]["observed"] == {"path_candidates": 5001}


def test_bound_is_checked_before_probing(tmp_path, monkeypatch):
    """AC-0025: nothing is probed when the occurrence bound fires."""
    body = " ".join(["`tools/a.py`"] * 5001)
    root = make_corpus(tmp_path, [adr(consequences=revisit("x"), confirmation=signal(body))])
    (root / "tools").mkdir()
    monkeypatch.setattr(NAV, "_probe", lambda *a, **k: pytest.fail("probed"))
    assert run_health(root)["error"]["code"] == "input_too_large"


def refuse_process_starts(monkeypatch: pytest.MonkeyPatch) -> None:
    """Make every standard-library way to start a process or run a file raise."""
    def refuse(*a: Any, **k: Any) -> Any:
        raise AssertionError("forbidden call")

    monkeypatch.setattr(subprocess, "Popen", refuse)
    names = [n for n in dir(os) if n in {"system", "popen", "fork", "forkpty", "startfile"}
             or n.startswith(("exec", "spawn", "posix_spawn"))]
    for name in names:
        monkeypatch.setattr(os, name, refuse)


def test_no_network_or_subprocess(tmp_path, monkeypatch):
    """AC-0026: health starts no subprocess or process and opens no socket."""
    def refuse(*a: Any, **k: Any) -> Any:
        raise AssertionError("forbidden call")

    refuse_process_starts(monkeypatch)
    monkeypatch.setattr(socket, "socket", refuse)
    assert run_health(copy_hostile(tmp_path))["status"] == "ok"


def test_probe_join_never_reanchors_on_windows(monkeypatch):
    """AC-0047: a drive-carrying segment stays under the root under Windows path rules."""
    seen: list[str] = []
    last = {"name": ""}

    class DirStat:
        st_mode = stat.S_IFDIR | 0o755
        st_file_attributes = 0
        st_nlink = 1

    class Helper:
        @staticmethod
        def validate_confined_directory(root: Any, path: Any) -> None:
            return None

    def fake_lstat(path: Any) -> Any:
        seen.append(str(path))
        if str(path).endswith(last["name"]):
            raise FileNotFoundError(path)
        return DirStat()

    monkeypatch.setattr(NAV, "Path", pathlib.PureWindowsPath)
    monkeypatch.setattr(NAV.os, "lstat", fake_lstat)
    root = pathlib.PureWindowsPath("X:/repo")
    for checked in ("docs/D:secret.txt", "docs/adr/D:evil.md", "docs/C:/w.md"):
        seen.clear()
        last["name"] = checked.rstrip("/").split("/")[-1]
        assert NAV._probe(Helper(), root, checked) == ("missing", None)
        assert seen and all(pathlib.PureWindowsPath(p).drive == "X:" for p in seen), seen
        assert all(p.startswith("X:\\repo") for p in seen), seen


def test_link_target_scan_is_linear_on_hostile_text(tmp_path):
    """AC-0025: a 2 MB signal line of unclosed link openers is scanned quickly."""
    import time
    hostile = "](" * 1_000_000
    root = make_corpus(tmp_path, [adr(consequences=revisit("x"), confirmation=signal(hostile))])
    start = time.monotonic()
    res = run_health(root)
    assert res["status"] == "ok"
    assert time.monotonic() - start < 20


def test_repeated_sections_do_not_join_text(tmp_path):
    """AC-0010, AC-0014: trigger and signal text stop at a repeated section heading."""
    text = (
        "# ADR-0001: T\n\n- **Status:** Accepted\n\n"
        "## Consequences\n\n**Revisit if:** soon\n## Consequences\n2020-01-01\n\n"
        "## Confirmation\n\n- **Signal:** `tools/a.py`\n## Confirmation\n`tools/b.py`\n"
    )
    root = make_corpus(tmp_path, [text])
    (root / "tools").mkdir()
    res = run_health(root)
    assert [t["class"] for t in res["triggers"]] == ["judge"]
    assert {m["path"] for m in res["signal_paths"]["missing"]} == {"tools/a.py"}


def test_health_writes_nothing(tmp_path):
    """AC-0027: a run leaves every path, type and file hash unchanged."""
    root = copy_hostile(tmp_path, fifo=True)
    before = tree_state(root)
    assert any(kind == "special" for kind, _ in before.values())
    assert any(kind == "link" for kind, _ in before.values())
    assert run_health(root)["status"] == "ok"
    assert tree_state(root) == before


def test_hostile_fixture_findings(tmp_path):
    """AC-0016: the hostile fixture's findings, with the link and FIFO in a copy."""
    out = run_health(copy_hostile(tmp_path, fifo=True))
    assert out["accepted_adr_count"] == 4
    assert {t["id"]: t["class"] for t in out["triggers"]} == {
        "ADR-0001": "due", "ADR-0002": "version", "ADR-0004": "judge", "ADR-0005": "judge"}
    assert [(c["superseded"], c["cited_by"]) for c in out["superseded_citations"]] == [
        ("ADR-0003", "ADR-0005"), ("ADR-0003", "RFC-0001")]
    sp = out["signal_paths"]
    assert paths(sp["missing"]) == ["tools/missing-check.py"]
    assert {i["path"]: i["reason"] for i in sp["invalid"]} == {
        "../outside-check.py": "lexical", "/etc/passwd": "lexical", "linked/check.py": "link"}
    assert sp["present_count"] == 1 and sp["unlocated_count"] == 0
    assert out["no_confirmation"]["ids"] == ["ADR-0002", "ADR-0005"]


def test_health_cli_exit_codes(tmp_path):
    """AC-0001/AC-0004: exit 0 for ok and 1 for an error result."""
    root = make_corpus(tmp_path, [ACCEPTED_PROSE])
    assert run_main(["health", "--root", str(root), "--today", TODAY])[0] == 0
    assert run_main(["health", "--root", str(root), "--today", "nope"])[0] == 1
    code, text = run_main(["health", "--root", str(root)])
    assert code == 0 and json.loads(text)["today"] == NAV.datetime.now(NAV.UTC).date().isoformat()
