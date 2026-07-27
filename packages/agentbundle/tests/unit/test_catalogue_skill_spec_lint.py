"""Pytest port of tools/test-lint-skill-spec.py.

Calls lint_skill_spec() directly (no subprocess); uses tmp_path fixtures.
Requires PyYAML — entire module is skipped when it's absent.

Six fixture trees mirror the original self-test:
  A — broken: every error-level rule trips here.
  B — happy path: clean skill per walk root.
  C — warns: body length, deep same-skill, loose file; dev dirs silent.
  D — evals happy: well-formed evals.json, eval_queries.json variants.
  E — reliability: bad UTF-8 and symlink-loop surface, not crash.
  F — YAML shapes: depth-2 metadata parses clean.
  G — [pack.evals].skills cross-reference coverage.
"""

from __future__ import annotations

import os
import textwrap
from pathlib import Path
from typing import Iterable

import pytest

yaml = pytest.importorskip("yaml", reason="PyYAML not installed; skip deep lint tests")

from agentbundle.catalogue_tooling.results import Severity
from agentbundle.catalogue_tooling.skill_spec_lint import lint_skill_spec


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _messages(diags) -> str:
    return "\n".join(d.message for d in diags)


def _assert_all_in(label: str, text: str, expected: Iterable[str]) -> None:
    for pattern in expected:
        assert pattern in text, (
            f"{label}: expected substring not found: {pattern!r}\n---\n{text}\n---"
        )


def _assert_none_in(label: str, text: str, unexpected: Iterable[str]) -> None:
    for pattern in unexpected:
        assert pattern not in text, (
            f"{label}: unexpected substring present: {pattern!r}\n---\n{text}\n---"
        )


def _write(path: Path, body: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(body, encoding="utf-8")


# ---------------------------------------------------------------------------
# Tree A — broken fixtures (every error-level rule)
# ---------------------------------------------------------------------------


def _build_tree_broken(root: Path) -> None:
    skills = root / ".claude" / "skills"

    _write(skills / "BadNameUpper" / "SKILL.md", textwrap.dedent("""\
        ---
        name: BadNameUpper
        description: Uppercase in name — must fail the kebab regex.
        ---

        Body.
        """))

    _write(skills / "-bad-leading" / "SKILL.md", textwrap.dedent("""\
        ---
        name: -bad-leading
        description: Leading hyphen — must fail the kebab regex.
        ---

        Body.
        """))

    _write(skills / "bad--double" / "SKILL.md", textwrap.dedent("""\
        ---
        name: bad--double
        description: Double hyphen — must fail the kebab regex.
        ---

        Body.
        """))

    long_name = "name-too-long-" * 5 + "x"  # 71 chars
    _write(skills / long_name / "SKILL.md", textwrap.dedent(f"""\
        ---
        name: {long_name}
        description: 71-char name — must fail the 1–64 length check.
        ---

        Body.
        """))

    _write(skills / "wrong-dir-name" / "SKILL.md", textwrap.dedent("""\
        ---
        name: actually-this-name
        description: Name does not match the parent directory name.
        ---

        Body.
        """))

    _write(skills / "missing-desc" / "SKILL.md", textwrap.dedent("""\
        ---
        name: missing-desc
        ---

        Body.
        """))

    _write(skills / "long-desc" / "SKILL.md", textwrap.dedent(f"""\
        ---
        name: long-desc
        description: {"x" * 1100}
        ---

        Body.
        """))

    _write(skills / "long-compat" / "SKILL.md", textwrap.dedent(f"""\
        ---
        name: long-compat
        description: Compatibility exceeds 500 chars.
        compatibility: {"y" * 600}
        ---

        Body.
        """))

    _write(skills / "forbidden-key" / "SKILL.md", textwrap.dedent("""\
        ---
        name: forbidden-key
        description: Has a key outside the spec set; lint must refuse.
        not-a-spec-key: surprise
        ---

        Body.
        """))

    _write(skills / "tools-as-list" / "SKILL.md", textwrap.dedent("""\
        ---
        name: tools-as-list
        description: allowed-tools rendered as a YAML block list — spec requires a string.
        allowed-tools:
          - Read
          - Grep
        ---

        Body.
        """))

    _write(skills / "tools-as-flow-list" / "SKILL.md", textwrap.dedent("""\
        ---
        name: tools-as-flow-list
        description: allowed-tools rendered as a YAML flow-style list — spec requires a string.
        allowed-tools: [Read, Grep]
        ---

        Body.
        """))

    _write(skills / "duplicate-top-key" / "SKILL.md", textwrap.dedent("""\
        ---
        name: duplicate-top-key
        description: First description.
        description: Second description (duplicate key).
        ---

        Body.
        """))

    _write(skills / "duplicate-nested-key" / "SKILL.md", textwrap.dedent("""\
        ---
        name: duplicate-nested-key
        description: Duplicate key inside the metadata mapping.
        metadata:
          version: "1.0"
          version: "2.0"
        ---

        Body.
        """))

    bom_path = skills / "utf8-bom" / "SKILL.md"
    bom_path.parent.mkdir(parents=True, exist_ok=True)
    bom_path.write_bytes(
        b"\xef\xbb\xbf"
        b"---\nname: utf8-bom\ndescription: Clean description after the BOM.\n---\n\nBody.\n"
    )

    utf16_path = skills / "utf16-bom" / "SKILL.md"
    utf16_path.parent.mkdir(parents=True, exist_ok=True)
    utf16_path.write_bytes(b"\xff\xfe" + b"\x00" * 4)

    _write(skills / "folded-description-broken" / "SKILL.md", textwrap.dedent("""\
        ---
        name: folded-description-broken
        description: >-
          A multi-line folded description.
        ---

        Body.
        """))

    _write(skills / "literal-description-broken" / "SKILL.md", textwrap.dedent("""\
        ---
        name: literal-description-broken
        description: |
          Line one of a literal description.
          Line two preserves the newline.
        ---

        Body.
        """))

    _write(skills / "continuation-description" / "SKILL.md", textwrap.dedent("""\
        ---
        name: continuation-description
        description: First line of a continued
          description that spills onto the next.
        ---

        Body.
        """))

    _write(skills / "colon-space-description" / "SKILL.md", textwrap.dedent("""\
        ---
        name: colon-space-description
        description: Convert X: then do Y unquoted.
        ---

        Body.
        """))

    _write(skills / "hash-comment-description" / "SKILL.md", textwrap.dedent("""\
        ---
        name: hash-comment-description
        description: Real description # silently truncated to the # mark.
        ---

        Body.
        """))

    _write(skills / "anchor-description" / "SKILL.md", textwrap.dedent("""\
        ---
        name: anchor-description
        description: &anchor leading-anchor causes silent value mutation.
        ---

        Body.
        """))

    _write(skills / "flow-bracket-description" / "SKILL.md", textwrap.dedent("""\
        ---
        name: flow-bracket-description
        description: [not, a, list, but, looks, like, one]
        ---

        Body.
        """))

    _write(skills / "abs-path" / "SKILL.md", textwrap.dedent("""\
        ---
        name: abs-path
        description: Body contains an absolute /Users/ path.
        ---

        Run `python /Users/somebody/scratch/run.py` to reproduce.
        """))

    _write(skills / "cross-skill-path" / "SKILL.md", textwrap.dedent("""\
        ---
        name: cross-skill-path
        description: Body references a sibling skill by install path; lint must refuse.
        ---

        See `.claude/skills/work-loop/scripts/loop-cohort.py` for the state machine.
        """))

    _write(skills / "self-skill-path" / "SKILL.md", textwrap.dedent("""\
        ---
        name: self-skill-path
        description: Body references itself by install path; rewrite to skill-relative.
        ---

        Run `.claude/skills/self-skill-path/scripts/foo.py` — the install prefix is forbidden.
        """))

    _write(skills / "seed-path" / "SKILL.md", textwrap.dedent("""\
        ---
        name: seed-path
        description: Body references a seed path; lint must refuse.
        ---

        Worked example at `packs/core/.apm/skills/new-spec/SKILL.md`.
        """))

    _write(skills / "bare-install-path" / "SKILL.md", textwrap.dedent("""\
        ---
        name: bare-install-path
        description: Body mentions install roots with no skill name; both branches must refuse.
        ---

        Look for any skill in `.claude/skills/` — rewrite to name only.
        Worked examples live under `packs/core/.apm/skills/` — rewrite to name only.
        """))

    filler = "\n".join(f"filler line {i}" for i in range(1100))
    _write(skills / "body-too-long" / "SKILL.md",
           f"---\nname: body-too-long\ndescription: Body exceeds 1000 lines — must error.\n---\n\n{filler}\n")
    _write(skills / "body-too-long" / "scripts" / "noop.py", "# not lint-relevant\n")

    _write(skills / "unblessed-dir" / "SKILL.md", textwrap.dedent("""\
        ---
        name: unblessed-dir
        description: Has a non-blessed top-level subdirectory — must warn.
        ---

        Body.
        """))
    _write(skills / "unblessed-dir" / "extras" / "x.txt", "placeholder\n")

    _write(skills / "evals-missing-json" / "SKILL.md", textwrap.dedent("""\
        ---
        name: evals-missing-json
        description: evals/ dir present but no evals.json — must error.
        ---

        Body.
        """))
    (skills / "evals-missing-json" / "evals").mkdir(parents=True, exist_ok=True)

    _write(skills / "evals-bad-json" / "SKILL.md", textwrap.dedent("""\
        ---
        name: evals-bad-json
        description: evals.json is malformed JSON.
        ---

        Body.
        """))
    _write(skills / "evals-bad-json" / "evals" / "evals.json", "{not valid json\n")

    _write(skills / "evals-wrong-name" / "SKILL.md", textwrap.dedent("""\
        ---
        name: evals-wrong-name
        description: evals.json skill_name disagrees with the skill's own name.
        ---

        Body.
        """))
    _write(skills / "evals-wrong-name" / "evals" / "evals.json", textwrap.dedent("""\
        {
          "skill_name": "some-other-skill",
          "evals": [
            {"id": 1, "prompt": "P", "expected_output": "E"}
          ]
        }
        """))

    _write(skills / "evals-missing-file" / "SKILL.md", textwrap.dedent("""\
        ---
        name: evals-missing-file
        description: evals.json refers to a fixture file that does not exist.
        ---

        Body.
        """))
    _write(skills / "evals-missing-file" / "evals" / "evals.json", textwrap.dedent("""\
        {
          "skill_name": "evals-missing-file",
          "evals": [
            {"id": 1, "prompt": "P", "expected_output": "E",
             "files": ["evals/files/does-not-exist.txt"]}
          ]
        }
        """))

    _write(skills / "evals-duplicate-ids" / "SKILL.md", textwrap.dedent("""\
        ---
        name: evals-duplicate-ids
        description: evals.json reuses an id.
        ---

        Body.
        """))
    _write(skills / "evals-duplicate-ids" / "evals" / "evals.json", textwrap.dedent("""\
        {
          "skill_name": "evals-duplicate-ids",
          "evals": [
            {"id": 1, "prompt": "P1", "expected_output": "E1"},
            {"id": 1, "prompt": "P2", "expected_output": "E2"}
          ]
        }
        """))

    _write(skills / "evals-bool-id" / "SKILL.md", textwrap.dedent("""\
        ---
        name: evals-bool-id
        description: evals.json uses a boolean as the id — must error, not silently coerce.
        ---

        Body.
        """))
    _write(skills / "evals-bool-id" / "evals" / "evals.json", textwrap.dedent("""\
        {
          "skill_name": "evals-bool-id",
          "evals": [
            {"id": true, "prompt": "P", "expected_output": "E"}
          ]
        }
        """))

    _write(skills / "evals-path-traversal" / "SKILL.md", textwrap.dedent("""\
        ---
        name: evals-path-traversal
        description: evals.json files entry escapes the skill directory.
        ---

        Body.
        """))
    _write(skills / "evals-path-traversal" / "evals" / "evals.json", textwrap.dedent("""\
        {
          "skill_name": "evals-path-traversal",
          "evals": [
            {"id": 1, "prompt": "P", "expected_output": "E",
             "files": ["../../../etc/hosts"]}
          ]
        }
        """))

    _write(skills / "eq-not-array" / "SKILL.md", textwrap.dedent("""\
        ---
        name: eq-not-array
        description: eval_queries.json is a JSON object, not the required array.
        ---

        Body.
        """))
    _write(skills / "eq-not-array" / "evals" / "eval_queries.json", '{"queries": []}\n')

    _write(skills / "eq-bad-element" / "SKILL.md", textwrap.dedent("""\
        ---
        name: eq-bad-element
        description: eval_queries.json element has an empty query and an int should_trigger.
        ---

        Body.
        """))
    _write(skills / "eq-bad-element" / "evals" / "eval_queries.json", textwrap.dedent("""\
        [
          {"query": "", "should_trigger": 1}
        ]
        """))


TREE_A_EXPECTED = [
    "name 'BadNameUpper'",
    "name '-bad-leading'",
    "name 'bad--double'",
    "must match",
    "must be 1–64 chars",
    "does not match directory",
    "missing required key: description",
    "description exceeds 1024 chars",
    "compatibility exceeds 500 chars",
    "unknown top-level frontmatter keys: ['not-a-spec-key']",
    "'allowed-tools' must be a space-separated string, not a YAML block list",
    "'allowed-tools' must be a space-separated string, not a YAML flow-style list",
    "duplicate frontmatter key 'description'",
    "duplicate frontmatter key 'version'",
    "UTF-8 BOM detected at file start",
    "UTF-16 BOM detected",
    "folded/literal block syntax ('>-') is not portable",
    "folded/literal block syntax ('|') is not portable",
    "continuation lines (indented next line) are not portable",
    "description contains ': ' in an unquoted scalar",
    "kirodotdev/Kiro#8329",
    "description contains whitespace-then-'#' in an unquoted scalar",
    "description starts with YAML anchor indicator '&'",
    "description starts with YAML indicator '['",
    "absolute system path",
    ".claude/skills/work-loop/",
    ".claude/skills/self-skill-path/",
    "packs/core/.apm/skills/new-spec/",
    "install-path reference in body: '.claude/skills/'",
    "install-path reference in body: 'packs/core/.apm/skills/'",
    "body exceeds 1000 lines",
    "evals/ directory present but neither evals/evals.json nor evals/eval_queries.json is present",
    "evals/evals.json is not valid JSON",
    "evals/eval_queries.json must be a JSON array at top level",
    "eval_queries[0].query must be a non-empty string",
    "eval_queries[0].should_trigger must be a boolean (got int)",
    "evals.json skill_name 'some-other-skill' does not match skill name 'evals-wrong-name'",
    "evals/files/does-not-exist.txt",
    "duplicate id 1",
    "evals[0].id must be int or str (got bool)",
    "resolves outside the skill directory",
    "non-blessed top-level subdirectory: 'extras'",
]


def test_tree_a_broken_fixtures(tmp_path):
    _build_tree_broken(tmp_path)
    diags = lint_skill_spec(tmp_path)
    errors = [d for d in diags if d.severity == Severity.ERROR]
    assert errors, "expected errors on broken fixtures, got none"
    msg = _messages(diags)
    _assert_all_in("tree-A", msg, TREE_A_EXPECTED)


# ---------------------------------------------------------------------------
# Tree B — happy path
# ---------------------------------------------------------------------------


def _build_tree_happy(root: Path) -> None:
    projection = root / ".claude" / "skills" / "clean-projection"
    _write(projection / "SKILL.md", textwrap.dedent("""\
        ---
        name: clean-projection
        description: Conforming skill — clean frontmatter, blessed subdirs, no path violations.
        license: MIT
        compatibility: Claude Code, Codex CLI
        metadata:
          credentialed: false
          primitive-class: credentialed-cli
        allowed-tools: Read Grep Bash
        ---

        A short body. Skill-relative paths only: `scripts/foo.py`, `references/REF.md`,
        `assets/template.md`. Cross-skill references go by name: see the work-loop skill.
        """))
    _write(projection / "scripts" / "foo.py", "# noop\n")
    _write(projection / "references" / "REF.md", "# noop\n")
    _write(projection / "assets" / "template.md", "# noop\n")

    seed = root / "packs" / "core" / ".apm" / "skills" / "clean-seed"
    _write(seed / "SKILL.md", textwrap.dedent("""\
        ---
        name: clean-seed
        description: Conforming seed skill — proves the linter walks packs/*/.apm/skills/ too.
        ---

        A short body. No install-path prefixes; skill-relative paths only.
        """))


def test_tree_b_happy_path(tmp_path):
    _build_tree_happy(tmp_path)
    diags = lint_skill_spec(tmp_path)
    # Clean skills produce no diagnostics — verify both walk roots exist on disk
    errors = [d for d in diags if d.severity == Severity.ERROR]
    assert not errors, f"unexpected errors on happy path: {_messages(diags)}"
    # Verify both walk roots were actually created (guards against build_tree_happy bugs)
    assert (tmp_path / ".claude" / "skills" / "clean-projection" / "SKILL.md").exists()
    assert (tmp_path / "packs" / "core" / ".apm" / "skills" / "clean-seed" / "SKILL.md").exists()


# ---------------------------------------------------------------------------
# Tree C — warns and allow-listed prose
# ---------------------------------------------------------------------------


def _build_tree_warns(root: Path) -> None:
    skills = root / ".claude" / "skills"

    _write(skills / "agent-ref-ok" / "SKILL.md", textwrap.dedent("""\
        ---
        name: agent-ref-ok
        description: Body references a subagent at .claude/agents/foo.md — allowed by spec.
        ---

        See `.claude/agents/adversarial-reviewer.md` for the reviewer subagent.
        Same-skill deep path: `scripts/sub/foo.py` (one level deeper — must warn, not error).
        """))
    _write(skills / "agent-ref-ok" / "scripts" / "sub" / "foo.py", "# noop\n")

    _write(skills / "tilde-ref-ok" / "SKILL.md", textwrap.dedent("""\
        ---
        name: tilde-ref-ok
        description: Body references the user-scope install at ~/.claude — allowed prose.
        ---

        Edit `~/.claude/settings.json` to enable the hook.
        """))

    filler = "\n".join(f"filler line {i}" for i in range(600))
    _write(skills / "body-warn-only" / "SKILL.md",
           f"---\nname: body-warn-only\ndescription: Body sits at 600 lines — must warn, not error.\n---\n\n{filler}\n")

    _write(skills / "loose-file" / "SKILL.md", textwrap.dedent("""\
        ---
        name: loose-file
        description: Has a stray file at the skill root — info only, not an error.
        ---

        Body.
        """))
    _write(skills / "loose-file" / "package.json", "{}\n")

    _write(skills / "dev-artifacts" / "SKILL.md", textwrap.dedent("""\
        ---
        name: dev-artifacts
        description: Ships node_modules / .venv / venv / __pycache__ — must not warn.
        ---

        Body.
        """))
    _write(skills / "dev-artifacts" / "scripts" / "run.js", "# noop\n")
    _write(skills / "dev-artifacts" / "node_modules" / "some-pkg" / "package.json", "{}\n")
    _write(skills / "dev-artifacts" / ".venv" / "lib" / "marker", "# noop\n")
    _write(skills / "dev-artifacts" / "venv" / "lib" / "marker", "# noop\n")
    _write(skills / "dev-artifacts" / "__pycache__" / "marker", "# noop\n")

    _write(skills / "evals-canonical-layout" / "SKILL.md", textwrap.dedent("""\
        ---
        name: evals-canonical-layout
        description: Body documents evals/files/sample.csv — canonical layout, no warn.
        ---

        The fixture lives at `evals/files/sample.csv` and is loaded by id-1.
        """))
    _write(skills / "evals-canonical-layout" / "evals" / "files" / "sample.csv",
           "fixture content\n")
    _write(skills / "evals-canonical-layout" / "evals" / "evals.json", textwrap.dedent("""\
        {
          "skill_name": "evals-canonical-layout",
          "evals": [
            {"id": 1, "prompt": "P", "expected_output": "E",
             "files": ["evals/files/sample.csv"]}
          ]
        }
        """))


TREE_C_EXPECTED_WARNS = [
    "body exceeds 500 lines",
    "same-skill file reference deeper than one level: 'scripts/sub/foo.py'",
    "loose file at skill root",
]

TREE_C_UNEXPECTED_WARNS = [
    "non-blessed top-level subdirectory: 'node_modules'",
    "non-blessed top-level subdirectory: '.venv'",
    "non-blessed top-level subdirectory: 'venv'",
    "non-blessed top-level subdirectory: '__pycache__'",
    "same-skill file reference deeper than one level: 'evals/files/sample.csv'",
]


def test_tree_c_warns_and_allowed_prose(tmp_path):
    _build_tree_warns(tmp_path)
    diags = lint_skill_spec(tmp_path)
    errors = [d for d in diags if d.severity == Severity.ERROR]
    assert not errors, f"unexpected errors on warn-only fixtures: {_messages(diags)}"
    msg = _messages(diags)
    _assert_all_in("tree-C", msg, TREE_C_EXPECTED_WARNS)
    _assert_none_in("tree-C", msg, TREE_C_UNEXPECTED_WARNS)


# ---------------------------------------------------------------------------
# Tree D — evals happy path
# ---------------------------------------------------------------------------


def _build_tree_evals_ok(root: Path) -> None:
    skill = root / ".claude" / "skills" / "evals-clean"
    _write(skill / "SKILL.md", textwrap.dedent("""\
        ---
        name: evals-clean
        description: Skill ships a well-formed evals.json — must pass clean.
        ---

        Body.
        """))
    _write(skill / "evals" / "files" / "sample.txt", "fixture content\n")
    _write(skill / "evals" / "evals.json", textwrap.dedent("""\
        {
          "skill_name": "evals-clean",
          "evals": [
            {"id": 1, "prompt": "P1", "expected_output": "E1",
             "assertions": ["asserts something"]},
            {"id": "two", "prompt": "P2", "expected_output": "E2",
             "files": ["evals/files/sample.txt"]}
          ]
        }
        """))

    eq_only = root / ".claude" / "skills" / "eval-queries-only"
    _write(eq_only / "SKILL.md", textwrap.dedent("""\
        ---
        name: eval-queries-only
        description: Ships only eval_queries.json — the Tier-A trigger-eval layout.
        ---

        Body.
        """))
    _write(eq_only / "evals" / "eval_queries.json", textwrap.dedent("""\
        [
          {"query": "do the thing this skill is for", "should_trigger": true},
          {"query": "a near-miss that needs a different skill", "should_trigger": false}
        ]
        """))

    both = root / ".claude" / "skills" / "evals-both-files"
    _write(both / "SKILL.md", textwrap.dedent("""\
        ---
        name: evals-both-files
        description: Ships both evals.json (Tier B) and eval_queries.json (Tier A).
        ---

        Body.
        """))
    _write(both / "evals" / "evals.json", textwrap.dedent("""\
        {
          "skill_name": "evals-both-files",
          "evals": [
            {"id": 1, "prompt": "P1", "expected_output": "E1"}
          ]
        }
        """))
    _write(both / "evals" / "eval_queries.json", textwrap.dedent("""\
        [
          {"query": "trigger this skill", "should_trigger": true}
        ]
        """))


def test_tree_d_evals_happy_path(tmp_path):
    _build_tree_evals_ok(tmp_path)
    diags = lint_skill_spec(tmp_path)
    errors = [d for d in diags if d.severity == Severity.ERROR]
    assert not errors, f"unexpected errors on evals happy path: {_messages(diags)}"


# ---------------------------------------------------------------------------
# Tree E — reliability: bad inputs must surface, not crash
# ---------------------------------------------------------------------------


def test_tree_e_bad_utf8(tmp_path):
    skill = tmp_path / ".claude" / "skills" / "bad-utf8"
    skill.mkdir(parents=True)
    raw = (
        b"---\nname: bad-utf8\ndescription: SKILL.md body contains a non-UTF-8 byte.\n---\n"
        b"\xff\xfe garbage\n"
    )
    (skill / "SKILL.md").write_bytes(raw)

    diags = lint_skill_spec(tmp_path)
    msg = _messages(diags)
    assert "SKILL.md is not valid UTF-8" in msg
    errors = [d for d in diags if d.severity == Severity.ERROR]
    assert errors


@pytest.mark.skipif(not hasattr(os, "symlink"), reason="symlinks unavailable on this platform")
def test_tree_e_symlink_loop(tmp_path):
    skill_dir = tmp_path / ".claude" / "skills" / "symlink-loop"
    skill_dir.mkdir(parents=True)
    try:
        os.symlink("SKILL.md", skill_dir / "SKILL.md")
    except (OSError, NotImplementedError):
        pytest.skip("symlink creation unavailable")

    diags = lint_skill_spec(tmp_path)
    errors = [d for d in diags if d.severity == Severity.ERROR]
    msg = _messages(diags)
    assert errors, "expected error diagnostic for symlink loop"
    assert "could not read skill" in msg


# ---------------------------------------------------------------------------
# Tree F — YAML shapes
# ---------------------------------------------------------------------------


def _build_tree_yaml_shapes(root: Path) -> None:
    skills = root / ".claude" / "skills"
    _write(skills / "deep-metadata" / "SKILL.md", textwrap.dedent("""\
        ---
        name: deep-metadata
        description: Skill declares runtime packages via depth-2 metadata.
        metadata:
          credentialed: false
          requires-packages:
            - Pillow
            - playwright
        ---

        Body.
        """))


def test_tree_f_yaml_shapes(tmp_path):
    _build_tree_yaml_shapes(tmp_path)
    diags = lint_skill_spec(tmp_path)
    errors = [d for d in diags if d.severity == Severity.ERROR]
    assert not errors, f"unexpected errors on YAML shape fixtures: {_messages(diags)}"


# ---------------------------------------------------------------------------
# Tree G — [pack.evals].skills coverage
# ---------------------------------------------------------------------------


def _eval_queries_skill(pack_skills: Path, name: str, with_eval_queries: bool) -> None:
    _write(pack_skills / name / "SKILL.md", textwrap.dedent(f"""\
        ---
        name: {name}
        description: A fixture skill for the [pack.evals] coverage pass.
        ---

        Body.
        """))
    if with_eval_queries:
        _write(pack_skills / name / "evals" / "eval_queries.json", textwrap.dedent("""\
            [
              {"query": "trigger me", "should_trigger": true},
              {"query": "near miss", "should_trigger": false}
            ]
            """))


def _build_tree_pack_evals(root: Path) -> None:
    packs = root / "packs"

    _write(packs / "cov-good" / "pack.toml", textwrap.dedent("""\
        [pack]
        name = "cov-good"

        [pack.evals]
        skills = ["good-skill"]
        """))
    _eval_queries_skill(packs / "cov-good" / ".apm" / "skills", "good-skill", True)

    _write(packs / "cov-missing-skill" / "pack.toml", textwrap.dedent("""\
        [pack]
        name = "cov-missing-skill"

        [pack.evals]
        skills = ["ghost-skill"]
        """))

    _write(packs / "cov-no-file" / "pack.toml", textwrap.dedent("""\
        [pack]
        name = "cov-no-file"

        [pack.evals]
        skills = ["bare-skill"]
        """))
    _eval_queries_skill(packs / "cov-no-file" / ".apm" / "skills", "bare-skill", False)

    _write(packs / "cov-no-block" / "pack.toml", textwrap.dedent("""\
        [pack]
        name = "cov-no-block"
        """))
    _eval_queries_skill(packs / "cov-no-block" / ".apm" / "skills", "lonely-skill", False)


TREE_G_EXPECTED = [
    "[pack.evals].skills names 'ghost-skill' but",
    "is not a skill directory",
    "[pack.evals].skills names 'bare-skill' but it ships no evals/eval_queries.json",
]

TREE_G_UNEXPECTED = [
    "[pack.evals].skills names 'good-skill'",
    "[pack.evals].skills names 'lonely-skill'",
]


def test_tree_g_pack_evals_coverage(tmp_path):
    _build_tree_pack_evals(tmp_path)
    diags = lint_skill_spec(tmp_path)
    errors = [d for d in diags if d.severity == Severity.ERROR]
    assert errors, "expected errors on bad pack.evals coverage"
    msg = _messages(diags)
    _assert_all_in("tree-G", msg, TREE_G_EXPECTED)
    _assert_none_in("tree-G", msg, TREE_G_UNEXPECTED)


# ---------------------------------------------------------------------------
# --deep integration: exit 2 when PyYAML absent (tested at unit level)
# ---------------------------------------------------------------------------


def test_lint_skill_spec_raises_import_error_without_pyyaml(tmp_path, monkeypatch):
    """lint_skill_spec raises ImportError when yaml is not importable.

    This tests the error path; the import is satisfied in CI but we simulate
    absence by patching builtins.__import__.
    """
    import builtins
    real_import = builtins.__import__

    def _block_yaml(name, *args, **kwargs):
        if name == "yaml":
            raise ImportError("yaml")
        return real_import(name, *args, **kwargs)

    monkeypatch.setattr(builtins, "__import__", _block_yaml)
    with pytest.raises(ImportError, match="PyYAML"):
        lint_skill_spec(tmp_path)
