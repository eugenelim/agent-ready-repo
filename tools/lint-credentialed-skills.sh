#!/usr/bin/env bash
# Reports findings against credentialed-skill conventions
# (skill-secrets spec § AC26). Exits non-zero on any finding so the
# script composes with the existing lint family (lint-agents-md.sh,
# lint-agent-artifacts.sh); the `conventions-check` slash command
# captures stderr and surfaces it.
#
# Three checks, all scoped to skills whose `SKILL.md` frontmatter
# declares `metadata.credentialed: true` (under the agentskills.io
# spec's `metadata:` escape hatch for project-specific fields):
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
#     credentialed skill looking for `.agentbundle/credentials.env`.
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
DOTFILE_SUBSTRING = ".agentbundle/credentials.env"
OPTOUT_MARKER = "# credentialed-primitive: reads-creds-directly"

# RFC-0013 § 4c — build-projected shim files. Shipped by the
# `credential-brokers` pack and projected into every `auth: creds`
# consumer's `scripts/` by `agentbundle.build.shared_libs`. These
# files legitimately read the Tier-3 dotfile — that is the broker's
# entire purpose. The credentialed-skill lint applies consumer-code
# rules; the shim sits below that layer and is exempted from AC26(c)
# (dotfile-substring check). Other rules (argv ban etc.) still apply,
# but the shim defines no argparse surface so they're no-ops.
SHIM_BASENAMES = frozenset({
    "credentials_shim.py",
    "_keychain_macos.py",
    "_credman_windows.py",
})
# Resolve canonical source bytes. A consumer file named
# `credentials_shim.py` is exempted from AC26(c) ONLY if its bytes
# match the canonical source — otherwise a hand-rolled file using
# the same basename would silently bypass the dotfile-substring
# rule. The lookup is cached per-process to avoid re-reading on
# every skill scan.
#
# Resolve from REPO_ROOT (the shell `cd`s here before invoking
# python) — NOT from LINT_ROOT, which tests override to a tmp-path
# that doesn't carry the full pack catalogue. The canonical source
# lives at a fixed path in the project repo; LINT_ROOT picks which
# *skills* the lint scans, not the source pack the exemption
# checks against.
SHIM_SOURCE_DIR = pathlib.Path.cwd() / "packs" / "credential-brokers" / ".apm" / "shared-libs"
_shim_source_bytes_cache: dict[str, bytes | None] = {}


def _shim_source_bytes(basename: str) -> bytes | None:
    if basename not in _shim_source_bytes_cache:
        src = SHIM_SOURCE_DIR / basename
        try:
            _shim_source_bytes_cache[basename] = src.read_bytes()
        except OSError:
            _shim_source_bytes_cache[basename] = None
    return _shim_source_bytes_cache[basename]


def _is_canonical_shim(py: pathlib.Path) -> bool:
    if py.name not in SHIM_BASENAMES:
        return False
    expected = _shim_source_bytes(py.name)
    if expected is None:
        return False
    try:
        return py.read_bytes() == expected
    except OSError:
        return False
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


NESTED_KEY_RE = re.compile(r"^\s+([a-zA-Z][a-zA-Z0-9_-]*):\s*(.*)$")


def parse_frontmatter(path):
    """Return (fields, body) or (None, text) if frontmatter is absent.

    Minimal stdlib YAML-subset parser matching ``lint-agent-artifacts.py``
    — single-line scalars plus nested mappings under an empty-value key
    (the agentskills.io ``metadata:`` escape hatch shape). Sufficient
    for SKILL.md frontmatter shape pinned in the spec.
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
    i = 1
    while i < end:
        line = lines[i]
        if not line.strip():
            i += 1
            continue
        m = KEY_RE.match(line)
        if not m:
            i += 1
            continue
        key, val = m.group(1), m.group(2).strip()
        if val == "":
            # Empty value — peek for an indented nested mapping
            # (`  child: value`). Only one level of nesting is
            # supported: the first child line's indent fixes the
            # depth, and a deeper-indented or shallower line ends
            # the block. A doubly-nested mapping returns ``None``
            # (parse error) so the caller can treat the file as
            # malformed rather than silently flattening the
            # second nesting level.
            mapping = {}
            block_indent = None
            j = i + 1
            while j < end:
                nxt = lines[j]
                if not nxt.strip():
                    j += 1
                    continue
                indent = len(nxt) - len(nxt.lstrip())
                if indent == 0:
                    break
                if block_indent is None:
                    block_indent = indent
                elif indent != block_indent:
                    # Surface the malformed case on stderr rather
                    # than silently skipping the skill — the caller
                    # treats ``(None, text)`` as "no frontmatter", so
                    # a credentialed skill with a doubly-nested
                    # mapping would otherwise be invisible to AC26
                    # checks. The Python catalogue lint raises a
                    # parse error in the same shape; this surfaces
                    # the parallel diagnostic from this script.
                    report(
                        path,
                        f"malformed frontmatter — doubly-nested "
                        f"mapping under {key!r} at line {j + 1} "
                        f"(parser supports one level of nesting only)"
                    )
                    return None, text
                nm = NESTED_KEY_RE.match(nxt)
                if not nm:
                    break
                nval = nm.group(2).strip()
                # Strip a balanced pair of surrounding quotes — the
                # other two parsers (lint-agent-artifacts.py,
                # creds.py) do the same; keeping them aligned matters
                # because a quoted nested scalar would otherwise sneak
                # past the bash linter's argv-ban scope check.
                if (
                    len(nval) >= 2
                    and nval[0] == nval[-1]
                    and nval[0] in ('"', "'")
                ):
                    nval = nval[1:-1]
                mapping[nm.group(1)] = nval
                j += 1
            fields[key] = mapping if mapping else ""
            i = j
            continue
        fields[key] = val
        i += 1
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
    # `credentialed` and `primitive-class` live under the spec-blessed
    # `metadata:` escape hatch per agentskills.io. A non-dict
    # `metadata` (or no metadata at all) means the skill is not a
    # credentialed primitive.
    metadata = fields.get("metadata")
    if not isinstance(metadata, dict):
        continue
    if metadata.get("credentialed") != "true":
        continue
    scanned += 1
    primitive_class = metadata.get("primitive-class", "")
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

    # AC26(c) — dotfile substring + opt-out marker. Build-projected
    # shim files (RFC-0013 § 4c) are exempt: they ARE the broker that
    # reads the dotfile, not consumer code on top of one. The
    # exemption requires byte-equivalence against the canonical
    # source so a hand-rolled file cannot bypass the rule by sharing
    # a basename.
    for py in py_files:
        if _is_canonical_shim(py):
            continue
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
