#!/usr/bin/env python3
"""Self-test for tools/lint-skill-spec.py.

Pure-stdlib Python so the suite runs on Windows without an MSYS shell.
Pattern: build a fixture tree in a tempdir, point LINT_ROOT at it, run
the linter, and assert the output meets the expected substring set.
Six trees cover the contract:

  Tree A — broken: every error-level rule trips here. Linter must
           exit non-zero; every error substring must appear.
  Tree B — happy: one clean skill per walk root (projection + seed).
           Linter must exit 0; both walk roots must be visited.
  Tree C — warns + allow-listed: cases that should NOT fail but should
           log (warns, infos, allowed prose references). Linter must
           exit 0; expected warns appear; unexpected warns absent.
  Tree D — evals happy: a well-formed evals.json with both int and
           str ids and a resolving files entry — must pass clean.
  Tree E — reliability: bad UTF-8, a symlink loop, and a non-existent
           LINT_ROOT must surface as errors, not Python tracebacks.
  Tree F — YAML shapes: depth-2 nesting under metadata, folded (>-)
           and literal (|) block scalars for description. The prior
           hand-rolled parser hard-failed on depth-2; PyYAML handles
           all three cleanly.

The agentskills.io specification (https://agentskills.io/specification)
is the contract this linter enforces; each fixture pins one mechanical
rule from the spec to a failure mode the linter must catch.
"""

from __future__ import annotations

import os
import pathlib
import subprocess
import sys
import tempfile
import textwrap
from typing import Iterable


REPO_ROOT = pathlib.Path(__file__).resolve().parent.parent
LINTER = REPO_ROOT / "tools" / "lint-skill-spec.py"


def fail(label: str, msg: str, output: str = "") -> None:
    print(f"✖ {label}: {msg}", file=sys.stderr)
    if output:
        print("---", file=sys.stderr)
        print(output, file=sys.stderr)
        print("---", file=sys.stderr)
    sys.exit(1)


def run_linter(root: pathlib.Path) -> tuple[int, str]:
    """Invoke the linter with LINT_ROOT=root and return (exit_code, combined_output)."""
    env = {**os.environ, "LINT_ROOT": str(root)}
    result = subprocess.run(
        [sys.executable, str(LINTER)],
        env=env, capture_output=True, text=True, check=False,
    )
    return result.returncode, result.stdout + result.stderr


def write(path: pathlib.Path, body: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(body, encoding="utf-8")


def assert_all_in(label: str, output: str, expected: Iterable[str]) -> None:
    for pattern in expected:
        if pattern not in output:
            fail(label, f"expected substring not found: {pattern!r}", output)


def assert_none_in(label: str, output: str, unexpected: Iterable[str]) -> None:
    for pattern in unexpected:
        if pattern in output:
            fail(label, f"unexpected substring present (should be silent): "
                        f"{pattern!r}", output)


# ── Tree A — broken fixtures (every error rule) ──────────────────────────

def build_tree_broken(root: pathlib.Path) -> None:
    skills = root / ".claude" / "skills"

    # Frontmatter — name regex (uppercase).
    write(skills / "BadNameUpper" / "SKILL.md", textwrap.dedent("""\
        ---
        name: BadNameUpper
        description: Uppercase in name — must fail the kebab regex.
        ---

        Body.
        """))

    # Frontmatter — name regex (leading hyphen).
    write(skills / "-bad-leading" / "SKILL.md", textwrap.dedent("""\
        ---
        name: -bad-leading
        description: Leading hyphen — must fail the kebab regex.
        ---

        Body.
        """))

    # Frontmatter — name regex (double hyphen).
    write(skills / "bad--double" / "SKILL.md", textwrap.dedent("""\
        ---
        name: bad--double
        description: Double hyphen — must fail the kebab regex.
        ---

        Body.
        """))

    # Frontmatter — name >64 chars (regex passes but length check fires).
    long_name = "name-too-long-" * 5 + "x"  # 71 chars
    write(skills / long_name / "SKILL.md", textwrap.dedent(f"""\
        ---
        name: {long_name}
        description: 71-char name — must fail the 1–64 length check.
        ---

        Body.
        """))

    # Frontmatter — name does not match parent directory.
    write(skills / "wrong-dir-name" / "SKILL.md", textwrap.dedent("""\
        ---
        name: actually-this-name
        description: Name does not match the parent directory name.
        ---

        Body.
        """))

    # Frontmatter — description missing entirely.
    write(skills / "missing-desc" / "SKILL.md", textwrap.dedent("""\
        ---
        name: missing-desc
        ---

        Body.
        """))

    # Frontmatter — description >1024 chars.
    write(skills / "long-desc" / "SKILL.md", textwrap.dedent(f"""\
        ---
        name: long-desc
        description: {"x" * 1100}
        ---

        Body.
        """))

    # Frontmatter — compatibility >500 chars.
    write(skills / "long-compat" / "SKILL.md", textwrap.dedent(f"""\
        ---
        name: long-compat
        description: Compatibility exceeds 500 chars.
        compatibility: {"y" * 600}
        ---

        Body.
        """))

    # Frontmatter — non-spec top-level key.
    write(skills / "forbidden-key" / "SKILL.md", textwrap.dedent("""\
        ---
        name: forbidden-key
        description: Has a key outside the spec set; lint must refuse.
        not-a-spec-key: surprise
        ---

        Body.
        """))

    # Frontmatter — allowed-tools as a block-style list.
    write(skills / "tools-as-list" / "SKILL.md", textwrap.dedent("""\
        ---
        name: tools-as-list
        description: allowed-tools rendered as a YAML block list — spec requires a string.
        allowed-tools:
          - Read
          - Grep
        ---

        Body.
        """))

    # Frontmatter — allowed-tools as a flow-style list.
    write(skills / "tools-as-flow-list" / "SKILL.md", textwrap.dedent("""\
        ---
        name: tools-as-flow-list
        description: allowed-tools rendered as a YAML flow-style list — spec requires a string.
        allowed-tools: [Read, Grep]
        ---

        Body.
        """))

    # Frontmatter — duplicate top-level key (spec requires uniqueness).
    write(skills / "duplicate-top-key" / "SKILL.md", textwrap.dedent("""\
        ---
        name: duplicate-top-key
        description: First description.
        description: Second description (duplicate key).
        ---

        Body.
        """))

    # Frontmatter — duplicate nested key under metadata.
    write(skills / "duplicate-nested-key" / "SKILL.md", textwrap.dedent("""\
        ---
        name: duplicate-nested-key
        description: Duplicate key inside the metadata mapping.
        metadata:
          version: "1.0"
          version: "2.0"
        ---

        Body.
        """))

    # Body — absolute system path.
    write(skills / "abs-path" / "SKILL.md", textwrap.dedent("""\
        ---
        name: abs-path
        description: Body contains an absolute /Users/ path.
        ---

        Run `python /Users/somebody/scratch/run.py` to reproduce.
        """))

    # Body — cross-skill .claude/skills/<other>/ path.
    write(skills / "cross-skill-path" / "SKILL.md", textwrap.dedent("""\
        ---
        name: cross-skill-path
        description: Body references a sibling skill by install path; lint must refuse.
        ---

        See `.claude/skills/work-loop/scripts/loop-cohort.py` for the state machine.
        """))

    # Body — self-reference using install path (also banned).
    write(skills / "self-skill-path" / "SKILL.md", textwrap.dedent("""\
        ---
        name: self-skill-path
        description: Body references itself by install path; rewrite to skill-relative.
        ---

        Run `.claude/skills/self-skill-path/scripts/foo.py` — the install prefix is forbidden.
        """))

    # Body — packs/<pack>/.apm/skills/<X>/ seed path.
    write(skills / "seed-path" / "SKILL.md", textwrap.dedent("""\
        ---
        name: seed-path
        description: Body references a seed path; lint must refuse.
        ---

        Worked example at `packs/core/.apm/skills/example-credentialed-skill/SKILL.md`.
        """))

    # Body — bare install-path mention (no skill name after the slash).
    # Brief § work-loop:412 cites this: the install path itself is
    # environment-specific. Exercise both alternation branches in one
    # fixture so a regression on either side fails.
    write(skills / "bare-install-path" / "SKILL.md", textwrap.dedent("""\
        ---
        name: bare-install-path
        description: Body mentions the install roots with no skill name; lint must refuse both branches.
        ---

        Look for any skill in `.claude/skills/` — rewrite to "any skill in this repo".
        Worked examples live under `packs/core/.apm/skills/` — rewrite to "any skill in core/".
        """))

    # Body — line count >1000 (error).
    filler = "\n".join(f"filler line {i}" for i in range(1100))
    write(skills / "body-too-long" / "SKILL.md",
          f"---\nname: body-too-long\ndescription: Body exceeds 1000 lines — must error.\n---\n\n{filler}\n")
    # Add a blessed subdir so the unblessed-dir signal doesn't fire here.
    write(skills / "body-too-long" / "scripts" / "noop.py", "# not lint-relevant\n")

    # Directory layout — unblessed top-level subdir.
    write(skills / "unblessed-dir" / "SKILL.md", textwrap.dedent("""\
        ---
        name: unblessed-dir
        description: Has a non-blessed top-level subdirectory — must warn.
        ---

        Body.
        """))
    write(skills / "unblessed-dir" / "extras" / "x.txt", "placeholder\n")

    # Evals — directory exists but evals.json missing.
    write(skills / "evals-missing-json" / "SKILL.md", textwrap.dedent("""\
        ---
        name: evals-missing-json
        description: evals/ dir present but no evals.json — must error.
        ---

        Body.
        """))
    (skills / "evals-missing-json" / "evals").mkdir(parents=True, exist_ok=True)

    # Evals — malformed JSON.
    write(skills / "evals-bad-json" / "SKILL.md", textwrap.dedent("""\
        ---
        name: evals-bad-json
        description: evals.json is malformed JSON.
        ---

        Body.
        """))
    write(skills / "evals-bad-json" / "evals" / "evals.json", "{not valid json\n")

    # Evals — skill_name does not match the parent skill's frontmatter name.
    write(skills / "evals-wrong-name" / "SKILL.md", textwrap.dedent("""\
        ---
        name: evals-wrong-name
        description: evals.json skill_name disagrees with the skill's own name.
        ---

        Body.
        """))
    write(skills / "evals-wrong-name" / "evals" / "evals.json", textwrap.dedent("""\
        {
          "skill_name": "some-other-skill",
          "evals": [
            {"id": 1, "prompt": "P", "expected_output": "E"}
          ]
        }
        """))

    # Evals — files entry that does not resolve.
    write(skills / "evals-missing-file" / "SKILL.md", textwrap.dedent("""\
        ---
        name: evals-missing-file
        description: evals.json refers to a fixture file that does not exist.
        ---

        Body.
        """))
    write(skills / "evals-missing-file" / "evals" / "evals.json", textwrap.dedent("""\
        {
          "skill_name": "evals-missing-file",
          "evals": [
            {"id": 1, "prompt": "P", "expected_output": "E",
             "files": ["evals/files/does-not-exist.txt"]}
          ]
        }
        """))

    # Evals — duplicate ids within one evals.json.
    write(skills / "evals-duplicate-ids" / "SKILL.md", textwrap.dedent("""\
        ---
        name: evals-duplicate-ids
        description: evals.json reuses an id.
        ---

        Body.
        """))
    write(skills / "evals-duplicate-ids" / "evals" / "evals.json", textwrap.dedent("""\
        {
          "skill_name": "evals-duplicate-ids",
          "evals": [
            {"id": 1, "prompt": "P1", "expected_output": "E1"},
            {"id": 1, "prompt": "P2", "expected_output": "E2"}
          ]
        }
        """))

    # Evals — boolean id slips through Python's `isinstance(True, int)`
    # unless explicitly excluded. Quality-engineer round-1 catch.
    write(skills / "evals-bool-id" / "SKILL.md", textwrap.dedent("""\
        ---
        name: evals-bool-id
        description: evals.json uses a boolean as the id — must error, not silently coerce.
        ---

        Body.
        """))
    write(skills / "evals-bool-id" / "evals" / "evals.json", textwrap.dedent("""\
        {
          "skill_name": "evals-bool-id",
          "evals": [
            {"id": true, "prompt": "P", "expected_output": "E"}
          ]
        }
        """))

    # Evals — path traversal in files entry. Even if the target exists,
    # the linter must refuse anything that resolves outside the skill dir.
    write(skills / "evals-path-traversal" / "SKILL.md", textwrap.dedent("""\
        ---
        name: evals-path-traversal
        description: evals.json files entry escapes the skill directory.
        ---

        Body.
        """))
    write(skills / "evals-path-traversal" / "evals" / "evals.json", textwrap.dedent("""\
        {
          "skill_name": "evals-path-traversal",
          "evals": [
            {"id": 1, "prompt": "P", "expected_output": "E",
             "files": ["../../../etc/hosts"]}
          ]
        }
        """))


TREE_A_EXPECTED = [
    # name regex / length / dir-mismatch
    "name 'BadNameUpper'",
    "name '-bad-leading'",
    "name 'bad--double'",
    "must match",
    "must be 1–64 chars",
    "does not match directory",
    # description
    "missing required key: description",
    "description exceeds 1024 chars",
    # compatibility
    "compatibility exceeds 500 chars",
    # forbidden top-level
    "unknown top-level frontmatter keys: ['not-a-spec-key']",
    # allowed-tools shape — both list shapes are spec violations
    "'allowed-tools' must be a space-separated string, not a YAML block list",
    "'allowed-tools' must be a space-separated string, not a YAML flow-style list",
    # duplicate keys — top-level and nested both surface with the same shape
    "duplicate frontmatter key 'description'",
    "duplicate frontmatter key 'version'",
    # body paths
    "absolute system path",
    ".claude/skills/work-loop/",
    ".claude/skills/self-skill-path/",
    "packs/core/.apm/skills/example-credentialed-skill/",
    # bare install-path mention (no kebab-name after the slash) — both branches
    "install-path reference in body: '.claude/skills/'",
    "install-path reference in body: 'packs/core/.apm/skills/'",
    # body length error
    "body exceeds 1000 lines",
    # evals
    "evals/ directory present but evals/evals.json is missing",
    "evals/evals.json is not valid JSON",
    "evals.json skill_name 'some-other-skill' does not match skill name 'evals-wrong-name'",
    "evals/files/does-not-exist.txt",
    "duplicate id 1",
    "evals[0].id must be int or str (got bool)",
    "resolves outside the skill directory",
    # unblessed dir (warn) — appears in output regardless of exit code
    "non-blessed top-level subdirectory: 'extras'",
]


def run_tree_a(root: pathlib.Path) -> None:
    build_tree_broken(root)
    rc, out = run_linter(root)
    if rc == 0:
        fail("tree-A", "linter exited 0; expected non-zero on broken fixtures.", out)
    assert_all_in("tree-A", out, TREE_A_EXPECTED)
    print(f"✓ tree-A: {len(TREE_A_EXPECTED)} expected substrings observed; linter refused as expected.")


# ── Tree B — happy path: one skill per walk root ─────────────────────────

def build_tree_happy(root: pathlib.Path) -> None:
    projection = root / ".claude" / "skills" / "clean-projection"
    write(projection / "SKILL.md", textwrap.dedent("""\
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
    write(projection / "scripts" / "foo.py", "# noop\n")
    write(projection / "references" / "REF.md", "# noop\n")
    write(projection / "assets" / "template.md", "# noop\n")

    seed = root / "packs" / "core" / ".apm" / "skills" / "clean-seed"
    write(seed / "SKILL.md", textwrap.dedent("""\
        ---
        name: clean-seed
        description: Conforming seed skill — proves the linter walks packs/*/.apm/skills/ too.
        ---

        A short body. No install-path prefixes; skill-relative paths only.
        """))


def run_tree_b(root: pathlib.Path) -> None:
    build_tree_happy(root)
    rc, out = run_linter(root)
    if rc != 0:
        fail("tree-B", f"linter exited {rc} on happy-path; expected 0.", out)
    assert_all_in("tree-B", out, [
        ".claude/skills/clean-projection/SKILL.md",
        "packs/core/.apm/skills/clean-seed/SKILL.md",
    ])
    print("✓ tree-B: happy path clean; both walk roots exercised.")


# ── Tree F — YAML shapes the prior hand-rolled parser couldn't reach ─────

def build_tree_yaml_shapes(root: pathlib.Path) -> None:
    skills = root / ".claude" / "skills"

    # Depth-2 nesting under metadata: a mapping whose value is a list.
    # The prior hand-rolled parser hard-failed on this; PyYAML handles it.
    write(skills / "deep-metadata" / "SKILL.md", textwrap.dedent("""\
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

    # Multi-line folded block scalar (>-) for description. PyYAML folds
    # newlines to spaces and strips the trailing newline; the result is
    # a single logical string that still fits under the 1024-char cap.
    write(skills / "folded-description" / "SKILL.md", textwrap.dedent("""\
        ---
        name: folded-description
        description: >-
          A multi-line folded description. PyYAML joins this and the next
          line with a space, producing one logical string that the lint
          treats as a normal scalar.
        ---

        Body.
        """))

    # Literal block scalar (|) for description preserves newlines. The
    # length check counts newlines as chars; the result is well under
    # the 1024-char cap.
    write(skills / "literal-description" / "SKILL.md", textwrap.dedent("""\
        ---
        name: literal-description
        description: |
          Line one of a literal description.
          Line two preserves the newline between them.
        ---

        Body.
        """))


def run_tree_f(root: pathlib.Path) -> None:
    build_tree_yaml_shapes(root)
    rc, out = run_linter(root)
    if rc != 0:
        fail("tree-F", f"linter exited {rc} on YAML-shape fixtures; expected 0.", out)
    assert_all_in("tree-F", out, [
        ".claude/skills/deep-metadata/SKILL.md",
        ".claude/skills/folded-description/SKILL.md",
        ".claude/skills/literal-description/SKILL.md",
    ])
    print("✓ tree-F: depth-2 metadata + folded + literal block scalars all parsed clean.")


# ── Tree C — warns and allow-listed prose ────────────────────────────────

def build_tree_warns(root: pathlib.Path) -> None:
    skills = root / ".claude" / "skills"

    # Allowed: `.claude/agents/<name>` references in body — agents aren't skills.
    write(skills / "agent-ref-ok" / "SKILL.md", textwrap.dedent("""\
        ---
        name: agent-ref-ok
        description: Body references a subagent at .claude/agents/foo.md — allowed by spec.
        ---

        See `.claude/agents/adversarial-reviewer.md` for the reviewer subagent.
        Same-skill deep path: `scripts/sub/foo.py` (one level deeper — must warn, not error).
        """))
    write(skills / "agent-ref-ok" / "scripts" / "sub" / "foo.py", "# noop\n")

    # Allowed: `~/.claude/...` user-scope prose.
    write(skills / "tilde-ref-ok" / "SKILL.md", textwrap.dedent("""\
        ---
        name: tilde-ref-ok
        description: Body references the user-scope install at ~/.claude — allowed prose.
        ---

        Edit `~/.claude/settings.json` to enable the hook.
        """))

    # Body line count >500 but ≤1000 — must warn, not error.
    filler = "\n".join(f"filler line {i}" for i in range(600))
    write(skills / "body-warn-only" / "SKILL.md",
          f"---\nname: body-warn-only\ndescription: Body sits at 600 lines — must warn, not error.\n---\n\n{filler}\n")

    # Loose file at the skill root (info-level — markdown-to-html ships package.json).
    write(skills / "loose-file" / "SKILL.md", textwrap.dedent("""\
        ---
        name: loose-file
        description: Has a stray file at the skill root — info only, not an error.
        ---

        Body.
        """))
    write(skills / "loose-file" / "package.json", "{}\n")

    # Dev-artifact directories must NOT trip the unblessed-subdir warn.
    write(skills / "dev-artifacts" / "SKILL.md", textwrap.dedent("""\
        ---
        name: dev-artifacts
        description: Ships node_modules / .venv / venv / __pycache__ — must not warn.
        ---

        Body.
        """))
    write(skills / "dev-artifacts" / "scripts" / "run.js", "# noop\n")
    write(skills / "dev-artifacts" / "node_modules" / "some-pkg" / "package.json", "{}\n")
    write(skills / "dev-artifacts" / ".venv" / "lib" / "marker", "# noop\n")
    write(skills / "dev-artifacts" / "venv" / "lib" / "marker", "# noop\n")
    write(skills / "dev-artifacts" / "__pycache__" / "marker", "# noop\n")

    # Canonical evals layout: `evals/files/<fixture>` body reference must
    # NOT trip the deep-same-skill warn (depth check scoped to
    # scripts/references/assets only; evals/ has its own canonical
    # layout per agentskills.io/skill-creation/evaluating-skills).
    write(skills / "evals-canonical-layout" / "SKILL.md", textwrap.dedent("""\
        ---
        name: evals-canonical-layout
        description: Body documents evals/files/sample.csv — canonical layout, no warn.
        ---

        The fixture lives at `evals/files/sample.csv` and is loaded by id-1.
        """))
    write(skills / "evals-canonical-layout" / "evals" / "files" / "sample.csv",
          "fixture content\n")
    write(skills / "evals-canonical-layout" / "evals" / "evals.json", textwrap.dedent("""\
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


def run_tree_c(root: pathlib.Path) -> None:
    build_tree_warns(root)
    rc, out = run_linter(root)
    if rc != 0:
        fail("tree-C", f"linter exited {rc} on warn-only fixtures; expected 0.", out)
    assert_all_in("tree-C", out, TREE_C_EXPECTED_WARNS)
    assert_none_in("tree-C", out, TREE_C_UNEXPECTED_WARNS)
    print("✓ tree-C: warns/infos surfaced; allowed prose (.claude/agents, ~/.claude) accepted; "
          "dev-artifact dirs + evals/files/ stayed silent.")


# ── Tree D — evals happy path (clean evals.json passes) ──────────────────

def build_tree_evals_ok(root: pathlib.Path) -> None:
    skill = root / ".claude" / "skills" / "evals-clean"
    write(skill / "SKILL.md", textwrap.dedent("""\
        ---
        name: evals-clean
        description: Skill ships a well-formed evals.json — must pass clean.
        ---

        Body.
        """))
    write(skill / "evals" / "files" / "sample.txt", "fixture content\n")
    write(skill / "evals" / "evals.json", textwrap.dedent("""\
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


def run_tree_d(root: pathlib.Path) -> None:
    build_tree_evals_ok(root)
    rc, out = run_linter(root)
    if rc != 0:
        fail("tree-D", f"evals happy-path lint exited {rc}; expected 0.", out)
    print("✓ tree-D: evals.json with both int and str ids + a resolving files entry passed clean.")


# ── Tree E — reliability: bad inputs must surface, not crash ─────────────

def run_tree_e(scratch_root: pathlib.Path) -> None:
    # E1: missing LINT_ROOT must exit non-zero with a clear message.
    missing = scratch_root / "does-not-exist"
    rc, out = run_linter(missing)
    if rc == 0:
        fail("tree-E (missing LINT_ROOT)", "linter exited 0; expected 1.", out)
    if "does not exist" not in out:
        fail("tree-E (missing LINT_ROOT)", "missing 'does not exist' message.", out)

    # E2: malformed UTF-8 must surface as an err, not a traceback.
    utf8_root = scratch_root / "utf8"
    utf8_skill = utf8_root / ".claude" / "skills" / "bad-utf8"
    utf8_skill.mkdir(parents=True, exist_ok=True)
    raw = b"---\nname: bad-utf8\ndescription: SKILL.md body contains a non-UTF-8 byte.\n---\n\xff\xfe garbage\n"
    (utf8_skill / "SKILL.md").write_bytes(raw)
    rc, out = run_linter(utf8_root)
    if rc == 0:
        fail("tree-E (bad-utf8)", "linter exited 0; expected 1.", out)
    if "SKILL.md is not valid UTF-8" not in out:
        fail("tree-E (bad-utf8)", "missing 'SKILL.md is not valid UTF-8' message.", out)
    if "Traceback" in out:
        fail("tree-E (bad-utf8)", "leaked a Python traceback.", out)

    # E3: symlink-loop SKILL.md must surface as an err, not a traceback.
    # Skipped on Windows where symlink creation requires elevated privileges
    # and `os.symlink` typically raises OSError — the OSError handler in
    # the linter is what we'd be testing anyway.
    if hasattr(os, "symlink"):
        loop_root = scratch_root / "symloop"
        loop_skill = loop_root / ".claude" / "skills" / "symlink-loop"
        loop_skill.mkdir(parents=True, exist_ok=True)
        try:
            os.symlink("SKILL.md", loop_skill / "SKILL.md")
        except (OSError, NotImplementedError):
            print("ℹ tree-E (symlink-loop): symlink creation unavailable; "
                  "skipping the OSError-handler sub-case.")
        else:
            rc, out = run_linter(loop_root)
            if rc == 0:
                fail("tree-E (symlink-loop)", "linter exited 0; expected 1.", out)
            if "could not read skill" not in out:
                fail("tree-E (symlink-loop)",
                     "missing 'could not read skill' message.", out)
            if "Traceback" in out:
                fail("tree-E (symlink-loop)", "leaked a Python traceback.", out)

    print("✓ tree-E: malformed UTF-8, symlink loop, and missing LINT_ROOT all "
          "surface as errors (no tracebacks).")


# ── Driver ───────────────────────────────────────────────────────────────

def main() -> int:
    if not LINTER.exists():
        fail("setup", f"linter not found at {LINTER}")

    with tempfile.TemporaryDirectory() as tmp_a, \
         tempfile.TemporaryDirectory() as tmp_b, \
         tempfile.TemporaryDirectory() as tmp_c, \
         tempfile.TemporaryDirectory() as tmp_d, \
         tempfile.TemporaryDirectory() as tmp_e, \
         tempfile.TemporaryDirectory() as tmp_f:
        run_tree_a(pathlib.Path(tmp_a))
        run_tree_b(pathlib.Path(tmp_b))
        run_tree_c(pathlib.Path(tmp_c))
        run_tree_d(pathlib.Path(tmp_d))
        run_tree_e(pathlib.Path(tmp_e))
        run_tree_f(pathlib.Path(tmp_f))

    print()
    print("Self-test: passed.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
