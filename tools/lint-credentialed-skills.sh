#!/usr/bin/env bash
# Reports findings against credentialed-skill conventions
# (skill-secrets spec § AC26). Exits non-zero on any finding so the
# script composes with the existing lint family (lint-agents-md.sh,
# lint-agent-artifacts.sh); the `conventions-check` slash command
# captures stderr and surfaces it.
#
# Three checks, all scoped to skills whose `SKILL.md` frontmatter
# declares `credentialed: true`:
#
#   AC26(a) "Don't" block presence.
#     The body must contain an `### Security rules (non-negotiable)`
#     heading, and within that section the three RFC-0006 § 4
#     substrings:
#       - `**Never** read that file, print it, or echo the token`
#       - `**Never** put the token on the command line`
#       - `do not run it for them`
#
#   AC26(b) Argv-flag detection (credentialed-cli class only).
#     `ast.parse` walks every `scripts/**/*.py` file under the skill
#     and inspects `argparse.ArgumentParser.add_argument` calls. The
#     first positional argument is normalised per AC27 (strip leading
#     `-`, casefold, replace `-` with `_`) and matched against the
#     banned set {token, api_token, api_key, bearer, pat, password}.
#     First-arg shapes recognised (all reducible to a literal string
#     at parse time — no name lookups, no runtime evaluation):
#       - ``Constant(value=str)`` — direct literal.
#       - ``BinOp(op=Add)`` chains of literal-string constants
#         (``"--" + "token"`` obfuscation in AC27).
#       - ``JoinedStr`` (f-string) whose pieces are all literal
#         constants — `f"--{'token'}"` and similar.
#       - ``Starred(Tuple)`` argument spread when the inner tuple is
#         literal — `add_argument(*("--token",))`.
#       - ``Subscript`` constant indexing — `("--token",)[0]` shapes.
#     Names that reach `add_argument` through a variable, an `os.environ`
#     read, or a function call remain out of scope; PR-review picks
#     those up as a defence in depth.
#
#   AC26(c) Dotfile substring + opt-out marker.
#     Per-line substring scan of every `scripts/**/*.py` under a
#     credentialed skill looking for `.agent-ready/credentials.env`.
#     A line containing the substring is skipped iff
#     `# credentialed-primitive: reads-creds-directly` appears on
#     the same line (comparison after `str.rstrip()`).
#
# Discovery: walks SKILL.md files at three locations under LINT_ROOT
# (default: repo root) so the lint composes with both production
# paths and fixture-driven tests:
#
#   LINT_ROOT/.claude/skills/<name>/SKILL.md
#   LINT_ROOT/packs/<pack>/.apm/skills/<name>/SKILL.md
#   LINT_ROOT/skills/<name>/SKILL.md       (fixture-tree shape)

set -uo pipefail

REPO_ROOT="$(git rev-parse --show-toplevel 2>/dev/null || pwd)"
cd "$REPO_ROOT"

LINT_ROOT="${LINT_ROOT:-.}"

python3 - "$LINT_ROOT" <<'PY'
import ast
import pathlib
import re
import sys

root = pathlib.Path(sys.argv[1]).resolve()

BANNED_FLAGS = {"token", "api_token", "api_key", "bearer", "pat", "password"}
DOTFILE_SUBSTRING = ".agent-ready/credentials.env"
OPTOUT_MARKER = "# credentialed-primitive: reads-creds-directly"
SECURITY_HEADING = "### Security rules (non-negotiable)"
REQUIRED_PHRASES = (
    "**Never** read that file, print it, or echo the token",
    "**Never** put the token on the command line",
    "do not run it for them",
)
KEY_RE = re.compile(r"^([a-zA-Z][a-zA-Z0-9_-]*):\s*(.*)$")
HEADING_TERMINATE_RE = re.compile(r"\n#{1,6}\s")

findings = 0


def relpath(p):
    try:
        return p.relative_to(root)
    except ValueError:
        return p


def report(path, message):
    global findings
    findings += 1
    print(f"✖ {relpath(path)}: {message}", file=sys.stderr)


def parse_frontmatter(path):
    """Return (fields, body) or (None, text) if frontmatter is absent.

    Minimal stdlib YAML-subset parser matching ``lint-agent-artifacts.sh``
    — single-line scalars only, no nested structures. Sufficient for
    SKILL.md frontmatter shape pinned in the spec.
    """
    text = path.read_text(encoding="utf-8")
    lines = text.splitlines()
    if not lines or lines[0].strip() != "---":
        return None, text
    end = None
    for i in range(1, len(lines)):
        if lines[i].strip() == "---":
            end = i
            break
    if end is None:
        return None, text
    fields = {}
    for line in lines[1:end]:
        if not line.strip():
            continue
        m = KEY_RE.match(line)
        if m:
            fields[m.group(1)] = m.group(2).strip()
    body = "\n".join(lines[end + 1 :])
    return fields, body


def section_body(body, heading):
    """Slice ``body`` from ``heading`` to the next heading or EOF.

    Returns the section as a single string including the heading line.
    """
    idx = body.find(heading)
    if idx < 0:
        return None
    rest = body[idx:]
    m = HEADING_TERMINATE_RE.search(rest, len(heading))
    if m is None:
        return rest
    return rest[: m.start()]


def normalize_flag(s):
    """AC27 normalisation: strip leading ``-``, casefold, ``-`` → ``_``."""
    return s.lstrip("-").casefold().replace("-", "_")


def add_argument_flags(py_path):
    """Yield (raw, normalized, lineno) for every ``add_argument`` call.

    Recognises two first-arg shapes per AC27:
      - ``Constant(value=str)`` — direct literal.
      - ``BinOp(op=Add, left=Constant(str), right=Constant(str))`` —
        the ``"--" + "token"`` obfuscation pattern. Recursively
        concatenates chains of literal string adds.
    """
    try:
        tree = ast.parse(py_path.read_text(encoding="utf-8"),
                         filename=str(py_path))
    except SyntaxError:
        return
    for node in ast.walk(tree):
        if not isinstance(node, ast.Call):
            continue
        func = node.func
        if not isinstance(func, ast.Attribute) or func.attr != "add_argument":
            continue
        if not node.args:
            continue
        first = node.args[0]
        # Direct literal / BinOp / f-string / subscript-of-tuple shapes.
        value = _literal_string(first)
        if value is None:
            # Argument-spread shape: add_argument(*("--token",))
            value = _starred_first_literal(first)
        if value is None:
            continue
        if not value.startswith("-"):
            continue
        yield value, normalize_flag(value), node.lineno


def _literal_string(node):
    """Return a string if ``node`` reduces to a string literal at parse
    time, ``None`` otherwise.

    Shapes handled:
      - ``Constant(value=str)`` — direct literal.
      - ``BinOp(op=Add)`` chain of literal strings.
      - ``JoinedStr`` (f-string) whose ``FormattedValue`` parts are
        all literal constants (``f"--{'token'}"`` collapses to
        ``"--token"``); a non-literal `{name}` returns ``None``.
      - ``Tuple(elts=[Constant(str), ...])`` returning the first
        element — covers the inner shape of ``Starred(Tuple)``.
      - ``Subscript(value=Tuple|List, slice=Constant(int))`` — pulls
        the indexed element when both sides are literal.
    """
    if isinstance(node, ast.Constant) and isinstance(node.value, str):
        return node.value
    if isinstance(node, ast.BinOp) and isinstance(node.op, ast.Add):
        left = _literal_string(node.left)
        right = _literal_string(node.right)
        if left is not None and right is not None:
            return left + right
        return None
    if isinstance(node, ast.JoinedStr):
        parts: list[str] = []
        for piece in node.values:
            if isinstance(piece, ast.Constant) and isinstance(piece.value, str):
                parts.append(piece.value)
                continue
            if isinstance(piece, ast.FormattedValue):
                inner = _literal_string(piece.value)
                if inner is None:
                    return None
                parts.append(inner)
                continue
            return None
        return "".join(parts)
    if isinstance(node, ast.Subscript):
        # ("--token",)[0] / ["--token"][0] — only pull when both
        # sides are literal.
        container = node.value
        if not isinstance(container, (ast.Tuple, ast.List)):
            return None
        slice_node = node.slice
        if not (
            isinstance(slice_node, ast.Constant)
            and isinstance(slice_node.value, int)
        ):
            return None
        if not (0 <= slice_node.value < len(container.elts)):
            return None
        return _literal_string(container.elts[slice_node.value])
    return None


def _starred_first_literal(node):
    """If ``node`` is ``Starred(Tuple(elts=[Constant(str), ...]))``,
    return that first literal — argparse sees it as the flag name.
    Anything else returns ``None``."""
    if not isinstance(node, ast.Starred):
        return None
    inner = node.value
    if not isinstance(inner, (ast.Tuple, ast.List)) or not inner.elts:
        return None
    return _literal_string(inner.elts[0])


# Discovery: three glob patterns covering production paths + fixture trees.
skill_md_files = []
for pattern in (
    ".claude/skills/*/SKILL.md",
    "packs/*/.apm/skills/*/SKILL.md",
    "skills/*/SKILL.md",
):
    skill_md_files.extend(sorted(root.glob(pattern)))

scanned = 0

for skill_md in skill_md_files:
    fields, body = parse_frontmatter(skill_md)
    if fields is None:
        continue
    if fields.get("credentialed") != "true":
        continue
    scanned += 1
    primitive_class = fields.get("primitive-class", "")
    skill_dir = skill_md.parent

    # AC26(a) — Don't-block presence.
    section = section_body(body, SECURITY_HEADING)
    if section is None:
        report(skill_md, f"missing heading: {SECURITY_HEADING}")
    else:
        for phrase in REQUIRED_PHRASES:
            if phrase not in section:
                report(skill_md,
                       f"security section missing required phrase: {phrase!r}")

    scripts_dir = skill_dir / "scripts"
    if not scripts_dir.exists():
        continue

    py_files = sorted(p for p in scripts_dir.rglob("*.py") if p.is_file())

    # AC26(b) — argv-flag detection. Scoped to credentialed-cli class.
    if primitive_class == "credentialed-cli":
        for py in py_files:
            for raw, norm, lineno in add_argument_flags(py):
                if norm in BANNED_FLAGS:
                    report(
                        py,
                        f"line {lineno}: argv-borne credential flag "
                        f"{raw!r} accepted by argparse (normalised "
                        f"{norm!r} ∈ {sorted(BANNED_FLAGS)})",
                    )

    # AC26(c) — dotfile substring + opt-out marker.
    for py in py_files:
        try:
            content = py.read_text(encoding="utf-8")
        except OSError:
            continue
        for lineno, line in enumerate(content.splitlines(), start=1):
            if DOTFILE_SUBSTRING not in line:
                continue
            if OPTOUT_MARKER in line.rstrip():
                continue
            report(
                py,
                f"line {lineno}: skill reads {DOTFILE_SUBSTRING} directly "
                f"(architectural violation — opt-out marker absent)",
            )

print(f"Credentialed-skill lint: {scanned} skill(s) scanned, "
      f"{findings} finding(s).")

if findings:
    sys.exit(1)
PY
