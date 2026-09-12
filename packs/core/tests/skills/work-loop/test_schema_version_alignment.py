"""Schema-version declarations must remain aligned across independent loaders."""

from __future__ import annotations

import ast
import json
import re
import sys
from pathlib import Path
from types import ModuleType

SKILL_DIR = Path(__file__).resolve().parents[3] / ".apm" / "skills" / "work-loop"
SCRIPTS = SKILL_DIR / "scripts"

# A digit stated as the schema version inside authored text: `schema_version=1`,
# `schema version 1`. An f-string that interpolates the constant has no digit
# here, because the interpolated part is a separate node.
_SCHEMA_VERSION_IN_TEXT = re.compile(r"schema[ _]version\b\W{0,3}\d")

# Whole word only. `schema_version_hint` is a different concept and is not this
# check's business.
_SCHEMA_VERSION_NAME = re.compile(r"\bschema_version\b")


def _mentions_schema_version(node: ast.expr) -> bool:
    """True when this operand reads the cohort state's schema version."""
    return bool(_SCHEMA_VERSION_NAME.search(ast.unparse(node)))


def _literal_schema_comparisons(tree: ast.AST) -> list[int]:
    """Line numbers comparing the schema version against an integer literal.

    Direction-agnostic on purpose: `state[...] != 1` and `1 != state[...]` are
    the same defect, and matching only the first would leave the second as a
    documented way past this check.
    """
    lines = []
    for node in ast.walk(tree):
        if not isinstance(node, ast.Compare):
            continue
        operands = [node.left, *node.comparators]
        names = [op for op in operands if _mentions_schema_version(op)]
        literals = [
            op
            for op in operands
            if isinstance(op, ast.Constant) and isinstance(op.value, int)
        ]
        if names and literals:
            lines.append(node.lineno)
    return lines


def _literal_schema_text(tree: ast.AST) -> list[int]:
    """Line numbers of string constants that state the version as a digit."""
    return [
        node.lineno
        for node in ast.walk(tree)
        if isinstance(node, ast.Constant)
        and isinstance(node.value, str)
        and _SCHEMA_VERSION_IN_TEXT.search(node.value)
    ]


def _load(path: Path, name: str) -> ModuleType:
    """Load one standalone script from source without changing ``sys.path``."""
    module = ModuleType(name)
    module.__file__ = str(path)
    sys.modules[name] = module
    try:
        exec(compile(path.read_text(encoding="utf-8"), str(path), "exec"), module.__dict__)
    finally:
        sys.modules.pop(name, None)
    return module


def _declared_schema_versions() -> dict[str, int]:
    """Plain ``SCHEMA_VERSION = <literal>`` assignments, by script name.

    Found by parsing rather than from a fixed list, so a script that starts
    declaring its own is compared too instead of drifting unnoticed.

    Deliberately narrow, and the narrowness is the point: it reads only a
    module-level assignment of a literal to the bare name. An annotated,
    conditional, augmented, tuple-target, or computed declaration is not seen,
    and none is caught elsewhere either — see the residual on the test below.
    Widening this to chase those forms is the arms race this stopped running.
    """
    found = {}
    for script in sorted(SCRIPTS.glob("*.py")):
        tree = ast.parse(script.read_text(encoding="utf-8"), filename=str(script))
        for node in tree.body:
            if not isinstance(node, ast.Assign):
                continue
            for target in node.targets:
                if (
                    isinstance(target, ast.Name)
                    and target.id == "SCHEMA_VERSION"
                    and isinstance(node.value, ast.Constant)
                ):
                    found[script.name] = node.value.value
    return found


def test_schema_version_declarations_match_state_template() -> None:
    """Each plainly declared ``SCHEMA_VERSION`` agrees with the template."""
    template = json.loads((SKILL_DIR / "assets" / "state.json").read_text(encoding="utf-8"))
    expected = template["schema_version"]

    declared = _declared_schema_versions()
    # The three that hold the loop's schema checks must be among them, or an
    # empty scan would agree with the template and prove nothing.
    assert {"loop-engine.py", "loop-cohort.py", "_loop_guards.py"} <= set(declared)
    assert declared == dict.fromkeys(declared, expected)

    # The values above are read from source; confirm the three that matter
    # carry the same value once actually executed.
    engine = _load(SCRIPTS / "loop-engine.py", "_schema_version_engine")
    guards = _load(SCRIPTS / "_loop_guards.py", "_schema_version_guards")
    cohort = _load(SCRIPTS / "loop-cohort.py", "_schema_version_cohort")

    assert (
        engine.SCHEMA_VERSION
        == guards.SCHEMA_VERSION
        == cohort.SCHEMA_VERSION
        == expected
    )


def test_no_script_states_the_schema_version_as_a_bare_literal() -> None:
    """No script states the schema version as a digit in a direct form.

    A tripwire for the way the literals actually got here — a comparison
    written inline, or a number typed into help text — not a proof that none
    can exist. An alias, a `match` arm, or `not in (1,)` all state the version
    without being caught, and no static check over authored syntax closes that
    for good.

    Nothing else catches what this misses, and the two tests do not cover each
    other. A comparison site that states the version literally is not a
    declaration, so a bump could move every declaration and leave such a site
    pinned to the old value with both tests passing. The declaration sweep has
    its own gap in the same direction: it reads only a plain assignment of a
    literal, so a conditional, annotated, or computed declaration escapes it
    without tripping anything here either.

    That is the standing residual. What holds is a convention, enforced for the
    common forms only: declare the version plainly, and compare against the
    constant rather than against a number.

    The scan is over the directory rather than a fixed file list, so a script
    added later is covered.
    """
    scripts = sorted(SCRIPTS.glob("*.py"))
    # An empty or mis-rooted scan would report zero offenders and prove nothing,
    # so the three scripts that hold the declarations must be in reach first.
    assert {"loop-engine.py", "loop-cohort.py", "_loop_guards.py"} <= {
        s.name for s in scripts
    }

    offenders = []
    for script in scripts:
        tree = ast.parse(script.read_text(encoding="utf-8"), filename=str(script))
        for lineno in sorted(
            _literal_schema_comparisons(tree) + _literal_schema_text(tree)
        ):
            offenders.append(f"{script.name}:{lineno}")

    assert offenders == [], "state the schema version as SCHEMA_VERSION:\n" + "\n".join(
        offenders
    )
