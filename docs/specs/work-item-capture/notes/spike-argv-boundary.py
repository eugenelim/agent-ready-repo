"""Throwaway spike. Verdicts use the catalog codes § D4 adds, and this file
is the derivation for § D6 of docs/specs/work-item-capture/spec.md: settle
§ D6's argv boundary by running it, not by asserting it.

Implements the candidate validator, then runs an admit/refuse case table whose
verdicts become the spec's content. Every case is drawn from a sustained
review finding or from a shape the reviewers said was uncovered.
"""
import json
import pathlib
import re
import sys

SCHEMA = json.loads(
    pathlib.Path(
        "contracts/jsonschema/knowledge-captured-observation.schema.json"
    ).read_text(encoding="utf-8")
)
_RP = SCHEMA["$defs"]["repositoryPath"]["pattern"]
# Same trailing-newline defect as above: the schema pattern ends `.+$`. Slice
# the TRAILING anchor only — the pattern carries three more `$` inside its
# lookaheads, and a global replace would rewrite those too. That is correct by
# accident today and wrong the first time a `$` appears as a literal.
REPO_PATH = re.compile((_RP[:-1] + r"\Z") if _RP.endswith("$") else _RP + r"\Z")

ALLOWED = {"cat", "wc", "grep", "ls"}
MIN_ARITY = {"cat": 2, "wc": 2, "ls": 2, "grep": 3}   # tool + required operand(s)
MAX_ELEMENTS, MAX_ELEMENT_CHARS, MAX_TOTAL_CHARS = 20, 500, 2000
# Positive class for grep's pattern element. It admits no shell metacharacter
# and no glob. Of the BRE metacharacters it admits exactly one: `.`.
# `*`, `[`, `]`, `^`, `$` and backslash are all excluded. So a fixed-string
# and a BRE reading of an admitted pattern agree EXCEPT where it contains a
# dot — ["grep", "a.b", "docs"] is admitted and means different things under
# -F and under BRE. It also admits `+`, a literal under BRE but a
# quantifier under ERE and PCRE, so the divergence is two characters wide,
# not one. Matcher selection is obligation 5 in § D6, carried by the handoff
# spec's execution-envelope decision.
# \Z, not $: `$` matches immediately before a trailing newline, which admitted
# ["cat", "src/a.py\n"] and re-opened the shell re-serialisation escape the
# class exists to close. Found by running this file, not by reading it.
ELEMENT_OK = re.compile(r"\A[A-Za-z0-9_/.,:@#%+=-]{1,500}\Z")


def validate(cmd):
    """Return None when admitted, else a reason code."""
    if not isinstance(cmd, list):
        return "work_item_command_shape"
    if not (1 <= len(cmd) <= MAX_ELEMENTS):
        return "work_item_command_size"
    if any(not isinstance(e, str) for e in cmd):
        return "work_item_command_shape"
    if sum(len(e) for e in cmd) > MAX_TOTAL_CHARS:
        return "work_item_command_size"
    if any(len(e) > MAX_ELEMENT_CHARS for e in cmd):
        return "work_item_command_size"
    if any(e.startswith("-") for e in cmd):
        return "work_item_command_option"
    if cmd[0] not in ALLOWED:
        return "work_item_command_tool"
    if len(cmd) < MIN_ARITY[cmd[0]]:
        return "work_item_command_operand"
    for i, e in enumerate(cmd[1:], start=1):
        # One positive class over every element. It subsumes the metacharacter
        # blocklist, the newline case, and the quote-splitting case, and it is
        # stated rather than emergent.
        if not ELEMENT_OK.match(e):
            return "work_item_command_charset"
        if cmd[0] == "grep" and i == 1:
            continue                          # pattern: charset is the whole rule
        if not REPO_PATH.match(e):
            return "work_item_command_path"
        # Any dot-leading path component: .git/, .env, .ssh/, .aws/ alike.
        if any(part.startswith(".") for part in e.split("/")):
            return "work_item_command_path"
    return None


CASES = [
    # (argv, why this case exists)
    (["cat", "src/a.py"], "baseline admission"),
    (["wc", "docs/x.md"], "baseline admission"),
    (["ls", "docs"], "baseline admission"),
    (["grep", "AKIA", "src/a.py"], "baseline admission, fixed-string pattern"),
    ("cat src/a.py", "R1: string command"),
    (["find", ".", "-delete"], "R1 sec: find -delete destroyed a file"),
    (["find", "d", "-maxdepth", "0", "-fprint", "o"], "R1 sec: find -fprint wrote a file"),
    (["git", "log", "--output=o"], "R1 sec: git --output wrote a file"),
    (["rg", "--pre", "./pre.sh", "q", "a.txt"], "R1 sec: rg --pre executed a script"),
    (["git", "-c", "diff.external=tee p", "diff"], "R2 sec: git -c reached execution"),
    (["cat", "-n", "src/a.py"],
     "R4 adv 12: option on an ADMITTED tool — the only rows above use tools "
     "the allowlist refuses anyway, so scoping the option rule to "
     "non-allowlisted tools reproduced every verdict"),
    (["ls", "-la", "docs"],
     "R4 adv 12: second admitted tool with an option, so the case is not one "
     "tool's quirk"),
    (["grep", "-i", "x", "docs"], "R4 adv 12: option ahead of grep's exempt pattern slot"),
    (["git", "cat-file", "blob", "a" * 40], "R2 sec: reads a deleted blob"),
    (["git", "show", "HEAD:docs/x.md"], "R2 sec: anchored read, now excluded"),
    (["cat", ".git/config"], "R3 sec F3: credential disclosure"),
    (["cat", ".env"], "R3 sec F3: untracked secret"),
    (["cat"], "R3 sec F4: blocks on stdin"),
    ([], "R3 sec F4: argv[0] undefined"),
    (["grep", "pattern"], "R3 sec F4: grep with no operand"),
    ([1, 2], "R3 sec F5: non-string elements"),
    ([None], "R3 sec F5: null element"),
    ([["cat"]], "R3 sec F5: nested list"),
    (["grep", "a*", "docs"], "R3 sec F6: glob survives re-serialisation"),
    (["cat", "a' '-delete"], "R3 sec F6: quote-split survives wrapping"),
    (["cat", "docs\\x.md"], "R3 sec F7: backslash, enforcers disagreed"),
    (["cat", "../etc/passwd"], "traversal"),
    (["cat", "/etc/passwd"], "absolute path"),
    (["cat", "a" * 501], "element length"),
    (["cat"] + ["x"] * 20, "element count"),
    (["cat"] + ["y" * 400] * 6, "aggregate length"),
    (["cat", "a\nb"], "newline in element"),
    (["cat", "a;b"], "shell metacharacter"),
    (["cat", ".ssh/id_rsa"], "iter2: dotdir beyond .git"),
    (["cat", "docs/.hidden"], "iter2: dotfile in a subdir"),
    (["grep", "foo.*", "docs"], "iter2: BRE metachar in pattern"),
    (["cat", "a b"], "iter2: space element"),
    (["cat", 'a"b'], "iter2: double quote"),
    (["cat", "docs/a-b_c.py"], "iter2: ordinary path must survive"),
    (["grep", "TODO:fix", "docs/x.md"], "iter2: ordinary pattern must survive"),
    (["cat", "src/a.py\n"], "R4 sec B1: TRAILING newline, $ admitted it"),
    (["grep", "AKIA\n", "src/a.py"], "R4 sec B1: trailing newline in a pattern"),
    (["grep", "a", "b\n"], "R4 sec B1: trailing newline in a later path"),
    (["grep", ".env", "docs"], "R4 sec N9: pattern is exempt from the dot rule"),
    (["grep", "../../etc/passwd", "docs"], "R4 sec C4: pattern exempt from repositoryPath"),
    (["cat"] + [1] * 21, "R5 sec C6: pins count-before-type ordering"),
]

rows = [(validate(c), c, why) for c, why in CASES]
admitted = [r for r in rows if r[0] is None]


def _cell(c):
    """Render one case for the spec table, and prove it parses back.

    Two earlier drafts of the table were corrupted here: one mangled the rows
    carrying shell quotes, one mixed two renderers so a case appeared twice.
    The assertion is what makes the spec's "emitted" claim true.
    """
    rendered = json.dumps(c)
    assert json.loads(rendered) == c, f"render/parse mismatch: {c!r}"
    return rendered


def emit_markdown() -> str:
    """The § D6 cases table, emitted. The spec's table is this output."""
    out = ["| argv | Verdict | Why this case exists |", "| --- | --- | --- |"]
    for code, c, why in rows:
        verdict = "**admit**" if code is None else f"`{code}`"
        out.append(f"| `{_cell(c)}` | {verdict} | {why} |")
    return "\n".join(out)


if __name__ == "__main__":
    if "--markdown" in sys.argv:
        print(emit_markdown())
    else:
        print(f"{len(CASES)} cases: {len(admitted)} admitted, "
              f"{len(CASES) - len(admitted)} refused\n")
        print(f"{'verdict':<24} {'argv':<46} why")
        print("-" * 112)
        for code, c, why in rows:
            v = "ADMIT" if code is None else code
            print(f"{v:<24} {str(c)[:44]:<46} {why}")
