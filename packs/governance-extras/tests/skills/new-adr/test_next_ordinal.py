#!/usr/bin/env python3
"""Smoke test for next-ordinal.py — covers the edge cases the adversarial
review surfaced: empty dir, missing dir, README-only, multi-digit prefixes
including 5-digit ones that must not collide with 4-digit ones.

Run: python3 test_next_ordinal.py
Exit code 0 = all assertions pass.
"""
import pathlib
import sys
import tempfile

# This harness loads next-ordinal.py from .apm/skills/<skill>/scripts/, so a
# .pyc written on import lands inside the runtime payload and the bundler's
# self-host check flags it as drift. The test moved out of .apm/; the module
# it exercises did not, so this guard is still the live one.
sys.dont_write_bytecode = True

HERE = pathlib.Path(__file__).resolve().parents[3] / ".apm" / "skills" \
    / "new-adr" / "scripts"
if not HERE.is_dir():                     # wrong parents[] depth after a move
    raise SystemExit(f"skill scripts dir not found at {HERE}")

# next-ordinal.py is hyphenated, so we load it by path rather than by
# import statement (Python's import grammar doesn't accept hyphens).
import importlib.util  # noqa: E402

spec = importlib.util.spec_from_file_location("next_ordinal", HERE / "next-ordinal.py")
next_ordinal_mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(next_ordinal_mod)
next_ordinal = next_ordinal_mod.next_ordinal


def _populate(dirpath, names):
    for n in names:
        (pathlib.Path(dirpath) / n).touch()


def main() -> int:
    with tempfile.TemporaryDirectory() as tmp:
        tmp_path = pathlib.Path(tmp)

        missing = tmp_path / "does-not-exist"
        assert next_ordinal(missing) == 1, "missing dir → 1"

        empty = tmp_path / "empty"
        empty.mkdir()
        assert next_ordinal(empty) == 1, "empty dir → 1"

        readme_only = tmp_path / "readme_only"
        readme_only.mkdir()
        _populate(readme_only, ["README.md", "index.html"])
        assert next_ordinal(readme_only) == 1, "no numeric entries → 1"

        normal = tmp_path / "normal"
        normal.mkdir()
        _populate(normal, ["0001-foo.md", "0002-bar.md", "0007-baz.md", "README.md"])
        assert next_ordinal(normal) == 8, "0007 max → 8"

        five = tmp_path / "five_digit"
        five.mkdir()
        _populate(five, ["0099-foo.md", "00099-bar.md", "0010-baz.md"])
        # 00099 must parse as 99, not 0009; max is 99 → next 100.
        assert next_ordinal(five) == 100, "5-digit prefix must parse fully"

        big = tmp_path / "big"
        big.mkdir()
        _populate(big, ["12345-foo.md"])
        assert next_ordinal(big) == 12346, "5-digit-only must not collide with 4-digit"

        loose = tmp_path / "loose"
        loose.mkdir()
        # bare 0042.md counts; 0042foo.md and 42-foo.md do not (prefix
        # must be 4+ digits terminated by - or .).
        _populate(loose, ["0042.md", "0042foo.md", "42-foo.md"])
        assert next_ordinal(loose) == 43, "bare 0042.md counts; siblings don't"

    print("ok")
    return 0


if __name__ == "__main__":
    sys.exit(main())
