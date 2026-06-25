"""Guard: every text-mode file writer in the package emits LF, not CRLF.

`Path.write_text(...)`, text-mode `open(...)` / `os.fdopen(...)`, and
`tempfile.NamedTemporaryFile(mode="w")` apply universal-newline translation
on write — on Windows that turns every ``\\n`` into ``\\r\\n``. Passing an
explicit ``newline="\\n"`` pins the output to LF on every platform, so a repo
populated by the CLI on Windows is byte-identical to one populated on
macOS/Linux. This guard fails if any text-mode writer is added without that
kwarg. Byte-preserving writers (`write_bytes`, ``os.write(fd, bytes)``,
binary-mode opens) are correct as-is and are not flagged.

Scope: the walk covers the inner `agentbundle/` package only. The sibling
canonical copy `packages/agentbundle/templates/install-marker.py` is outside
it — that copy writes via `os.write(fd, bytes)` (byte-safe), so it carries no
text writer to guard today; a text writer added there would not be caught here.

See `docs/specs/lf-line-endings/spec.md`.
"""

from __future__ import annotations

import ast
import unittest
from pathlib import Path

# Package root: tests -> build -> agentbundle
_PACKAGE_ROOT = Path(__file__).resolve().parents[2]

# Call targets that open a text stream and so honor `newline=`.
_WRITE_TEXT_ATTR = "write_text"
_TEMPFILE_FACTORIES = {"NamedTemporaryFile", "TemporaryFile"}


def _is_test_path(path: Path) -> bool:
    return "tests" in path.parts or path.name.startswith("test_")


def _string_literal(node: ast.expr | None) -> str | None:
    if isinstance(node, ast.Constant) and isinstance(node.value, str):
        return node.value
    return None


def _mode_is_text(mode: str | None, *, default_is_text: bool) -> bool:
    """A mode string opens a text stream when it has no 'b' flag.

    `mode is None` means the caller omitted it; the open-like branch treats a
    missing mode as a read (not flagged) before calling here, so `default` only
    matters for the tempfile factories, whose omitted mode defaults to binary
    (``w+b``). A non-literal mode (a variable) is treated as unknown and not
    flagged; the idiom in this codebase is always a literal.
    """
    if mode is None:
        return default_is_text
    return "b" not in mode and any(flag in mode for flag in ("w", "a", "x", "+"))


def _has_newline_kwarg(call: ast.Call) -> bool:
    return any(kw.arg == "newline" for kw in call.keywords)


def _kwarg(call: ast.Call, name: str) -> ast.expr | None:
    for kw in call.keywords:
        if kw.arg == name:
            return kw.value
    return None


def _is_text_writer_missing_newline(call: ast.Call) -> bool:
    func = call.func

    # Path.write_text(...) — always a text write.
    if isinstance(func, ast.Attribute) and func.attr == _WRITE_TEXT_ATTR:
        return not _has_newline_kwarg(call)

    # tempfile.NamedTemporaryFile / TemporaryFile — mode= kwarg, default w+b (binary).
    factory_name = None
    if isinstance(func, ast.Attribute) and func.attr in _TEMPFILE_FACTORIES:
        factory_name = func.attr
    elif isinstance(func, ast.Name) and func.id in _TEMPFILE_FACTORIES:
        factory_name = func.id
    if factory_name is not None:
        mode = _string_literal(_kwarg(call, "mode"))
        if _mode_is_text(mode, default_is_text=False):
            return not _has_newline_kwarg(call)
        return False

    # open(...) / os.fdopen(...) / path.open(...). Exclude os.open (raw fd).
    # The positional index of `mode` differs: builtin open(file, mode) and
    # os.fdopen(fd, mode) carry it at args[1]; the method path.open(mode) at
    # args[0] (the file/fd is the receiver, not an argument).
    is_open_like = False
    mode_pos = 1
    if isinstance(func, ast.Name) and func.id == "open":
        is_open_like = True
        mode_pos = 1
    elif isinstance(func, ast.Attribute):
        if func.attr == "fdopen":
            is_open_like = True
            mode_pos = 1
        elif func.attr == "open":
            # path.open(...) yes; os.open(...) is a raw fd — exclude it.
            receiver = func.value
            is_open_like = not (isinstance(receiver, ast.Name) and receiver.id == "os")
            mode_pos = 0
    if is_open_like:
        mode = None
        if len(call.args) > mode_pos:
            mode = _string_literal(call.args[mode_pos])
        if mode is None:
            mode = _string_literal(_kwarg(call, "mode"))
        # A write always names its mode; a bare open(...) / path.open() with no
        # mode is a text *read*, which doesn't honor newline= and isn't flagged.
        if mode is not None and _mode_is_text(mode, default_is_text=False):
            return not _has_newline_kwarg(call)
    return False


def _violations() -> list[str]:
    found: list[str] = []
    for py in sorted(_PACKAGE_ROOT.rglob("*.py")):
        if _is_test_path(py):
            continue
        tree = ast.parse(py.read_text(encoding="utf-8"), filename=str(py))
        for node in ast.walk(tree):
            if isinstance(node, ast.Call) and _is_text_writer_missing_newline(node):
                rel = py.relative_to(_PACKAGE_ROOT)
                found.append(f"{rel}:{node.lineno}")
    return found


class TextWritersEmitLF(unittest.TestCase):
    def test_no_text_writer_lacks_explicit_newline(self) -> None:
        violations = _violations()
        self.assertEqual(
            violations,
            [],
            'Text-mode file writers must pass newline="\\n" so generated '
            "files are LF on every platform. Offending sites:\n  "
            + "\n  ".join(violations),
        )


class WriterEmitsLFBytes(unittest.TestCase):
    """A real production writer produces LF bytes regardless of platform.

    Exercises `user_merge_json._atomic_write` — one of the fixed
    `NamedTemporaryFile(mode="w", newline="\\n")` sites. Its `json.dumps(...,
    indent=2)` emits real ``\\n`` line breaks between keys, so a regression that
    dropped the kwarg would turn this red on Windows (where it would write
    ``\\r\\n``). This is the AC5 "representative writer" check; the AST guard is
    the package-wide invariant.
    """

    def test_atomic_write_emits_no_crlf(self) -> None:
        import tempfile

        from agentbundle.build.projections import user_merge_json

        with tempfile.TemporaryDirectory() as d:
            target = Path(d) / "settings.json"
            user_merge_json._atomic_write(target, {"alpha": 1, "beta": 2})
            data = target.read_bytes()
        self.assertNotIn(b"\r\n", data)
        self.assertIn(b"\n", data)


if __name__ == "__main__":
    unittest.main()
