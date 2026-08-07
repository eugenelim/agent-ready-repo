#!/usr/bin/env python3
"""Self-test for `.apm/skills/work-loop/scripts/lint-knowledge.py`.

Three layers:

1. **Validation rules.** Tempdir JSONL fixtures trip each rule and assert the
   right error fires, driven through the documented
   `python <skill>/scripts/lint-knowledge.py <path>` invocation.
2. **Schema drift.** The field table in `docs/knowledge/README.md` and the
   linter's `REQUIRED_KEYS` / `OPTIONAL_KEYS` / `ALLOWED_KINDS` must agree.
3. **Guidance drift.** Every surface that tells a writer to author an entry
   must name the required keys *inline* and carry an example that lints
   clean. Entries landing without `source` because the guidance named no
   keys is the failure this layer guards.

This suite lives in the pack's test tree and is never installed, so it always
runs against the full catalogue: the pack source, both per-adapter projections,
and both knowledge READMEs. It asserts that surface count rather than assuming
it — a discovery bug that quietly checked fewer would report success while
letting drift through.
"""

from __future__ import annotations

import json
import os
import re
import subprocess
import sys
import tempfile
from pathlib import Path

# Windows cp1252 guard — reconfigure stdout/stderr to UTF-8 before any print.
sys.stdout.reconfigure(encoding="utf-8", errors="strict")
sys.stderr.reconfigure(encoding="utf-8", errors="backslashreplace")

# The pack ships tests under packs/<pack>/tests/ and runtime primitives under
# packs/<pack>/.apm/ — tests are visible in the catalogue and never installed.
_SKILL_DIR = Path(__file__).resolve().parents[3] / ".apm" / "skills" / "work-loop"
SCRIPT_DIR = _SKILL_DIR / "scripts"

if not SCRIPT_DIR.is_dir():  # wrong parents[] depth after a move
    raise SystemExit(f"subject dir not found at {SCRIPT_DIR} — check the parents[] depth")
LINTER = SCRIPT_DIR / "lint-knowledge.py"
SKILL = _SKILL_DIR / "SKILL.md"

FAILURES: list[str] = []
RAN = 0
HERE = Path(__file__).resolve().parent


def _repo_root() -> Path:
    """Anchor on this file, not on cwd.

    `git rev-parse` resolves against the working directory, so running the
    suite from elsewhere silently repointed every layer at the wrong tree:
    discovery fell to the one mandatory surface, two layers skipped, and it
    still exited 0. Same failure shape as the `| tail -2` defect this suite
    exists to prevent.
    """
    candidate = HERE.parents[4]          # packs/core/tests/skills/work-loop -> repo root
    if (candidate / "packs").is_dir():
        return candidate
    try:
        result = subprocess.run(
            ["git", "rev-parse", "--show-toplevel"],
            capture_output=True, text=True, check=False,
        )
        if result.returncode == 0 and result.stdout.strip():
            return Path(result.stdout.strip())
    except FileNotFoundError:
        pass
    return Path.cwd()


ROOT = _repo_root()


def _lint(path: Path) -> subprocess.CompletedProcess[str]:
    """Run the linter over *path* via its documented path argument."""
    return subprocess.run(
        [sys.executable, str(LINTER), str(path)],
        capture_output=True, text=True, encoding="utf-8", check=False,
    )


def ok(name: str) -> None:
    print(f"ok   [{name}]")


def fail(name: str, detail: str) -> None:
    FAILURES.append(name)
    print(f"FAIL [{name}]: {detail}", file=sys.stderr)


# --- Layer 1: validation rules ---------------------------------------------

def run_case(tmp: Path, name: str, body: str, want_exit: int,
             want_substr: str) -> None:
    global RAN
    RAN += 1
    path = tmp / f"{name}.jsonl"
    path.write_text(body, encoding="utf-8")
    proc = _lint(path)
    out = proc.stdout + proc.stderr
    if proc.returncode != want_exit:
        fail(name, f"expected exit {want_exit}, got {proc.returncode}\n  output: {out}")
        return
    if want_substr and want_substr not in out:
        fail(name, f"output missing {want_substr!r}\n  output: {out}")
        return
    ok(name)


VALID = ('{"id": "K-0001", "kind": "pattern", "scope": "src/**", '
         '"title": "T", "body": "B", "source": "PR#1"}')


def _entry(**over: object) -> str:
    base = {"id": "K-0001", "kind": "pattern", "scope": "x",
            "title": "t", "body": "b", "source": "s"}
    base.update(over)
    return json.dumps(base)


def layer_validation_rules(tmp: Path) -> None:
    # STUB: AC20 — docs/specs/loop-tooling-mandated-writes, task T3.
    # Red until the linter rejects a `\uXXXX` escape for a character that
    # should have been written literally. `_entry` serializes with json.dumps'
    # default ensure_ascii=True, so it produces exactly the drift being closed.
    run_case(tmp, "stub-gratuitous-escape-rejected",
             _entry(body="an em dash — here") + "\n", 1, "\\u2014")
    # The raw character is the correct form and stays clean.
    run_case(tmp, "stub-raw-utf8-accepted",
             json.dumps({"id": "K-0001", "kind": "pattern", "scope": "x",
                         "title": "t", "body": "an em dash — here",
                         "source": "s"}, ensure_ascii=False) + "\n",
             0, "Knowledge lint: passed")
    # U+2028/U+2029/U+0085 split str.splitlines(), which both this linter and
    # session-start.py use to read the file — so the *escaped* form is the only
    # representation that survives, and must stay legal.
    run_case(tmp, "stub-line-separator-escape-stays-legal",
             '{"id": "K-0001", "kind": "pattern", "scope": "x", "title": "t", '
             '"body": "a\\u2028b", "source": "s"}\n',
             0, "Knowledge lint: passed")
    # A literal backslash-u in body text is not an escape.
    run_case(tmp, "stub-literal-backslash-u-accepted",
             json.dumps({"id": "K-0001", "kind": "pattern", "scope": "x",
                         "title": "t", "body": "write \\u2014 to escape",
                         "source": "s"}, ensure_ascii=False) + "\n",
             0, "Knowledge lint: passed")
    # Below U+0020 JSON *requires* the escape. This case is what pins the
    # >= 0x20 threshold — without it, a linter that rejected every \uXXXX
    # escape would pass the whole stub.
    run_case(tmp, "stub-control-escape-stays-legal",
             '{"id": "K-0001", "kind": "pattern", "scope": "x", "title": "t", '
             '"body": "a\\u0009b", "source": "s"}\n',
             0, "Knowledge lint: passed")
    # Non-BMP characters become surrogate PAIRS under ensure_ascii=True — the
    # half of the drift that is not merely cosmetic, since U+D800-U+DFFF are
    # not valid TOML/YAML scalars.
    run_case(tmp, "stub-surrogate-pair-rejected",
             _entry(body="ship it 😀") + "\n", 1, "\\ud83d")

    # AC20 — a literal invisible character, not an escape. The writer refuses
    # these, but the file is hand-editable and session-start replays every
    # entry verbatim into an agent's context, so the gate has to see them too.
    run_case(tmp, "stub-literal-bidi-override-rejected",
             json.dumps({"id": "K-0001", "kind": "pattern", "scope": "x",
                         "title": "t", "body": "boring\u202e", "source": "s"},
                        ensure_ascii=False) + "\n",
             1, "U+202E")
    run_case(tmp, "stub-literal-tag-block-rejected",
             json.dumps({"id": "K-0001", "kind": "pattern", "scope": "x",
                         "title": "t", "body": "h\U000e0053", "source": "s"},
                        ensure_ascii=False) + "\n",
             1, "U+E0053")
    # ZWJ stays legal — text shaping, not hidden payload.
    run_case(tmp, "stub-zwj-sequence-accepted",
             json.dumps({"id": "K-0001", "kind": "pattern", "scope": "x",
                         "title": "t", "body": "\U0001f468\u200d\U0001f469 family",
                         "source": "s"}, ensure_ascii=False) + "\n",
             0, "Knowledge lint: passed")
    # AC20 — a pathological line is refused before the regex sees it, so the
    # gate cannot be hung by the input it exists to reject.
    run_case(tmp, "stub-overlong-line-refused",
             '{"id": "K-0001", "kind": "pattern", "scope": "x", "title": "t", '
             '"body": "' + "\\\\" * 5000 + '", "source": "s"}\n',
             1, "the limit is")

    # AC20a — the writer refuses a literal ESC because session-start replays it
    # as an ANSI sequence; the gate must refuse the escaped spelling too, or the
    # hand-edit path this rule exists for stays open.
    run_case(tmp, "stub-escaped-esc-rejected",
             '{"id": "K-0001", "kind": "pattern", "scope": "x", "title": "t", '
             '"body": "pre \\u001b[31mRED post", "source": "s"}\n',
             1, "\\u001b")
    # AC16 — two joiners in a row are a zero-width alphabet...
    run_case(tmp, "stub-consecutive-joiners-rejected",
             json.dumps({"id": "K-0001", "kind": "pattern", "scope": "x",
                         "title": "t", "body": "a\u200d\u200db", "source": "s"},
                        ensure_ascii=False) + "\n",
             1, "consecutive")
    # ...but a presentation selector next to a joiner is ordinary emoji.
    run_case(tmp, "stub-emoji-zwj-sequence-accepted",
             json.dumps({"id": "K-0001", "kind": "pattern", "scope": "x",
                         "title": "t", "body": "love \u2764\ufe0f\u200d\U0001f525",
                         "source": "s"}, ensure_ascii=False) + "\n",
             0, "Knowledge lint: passed")

    # Empty file (no learnings yet) is valid.
    run_case(tmp, "empty", "", 0, "Knowledge lint: passed")

    # Trailing newlines / blank lines are tolerated.
    run_case(tmp, "valid-one-entry", VALID + "\n", 0, "Knowledge lint: passed")
    run_case(tmp, "blank-lines", "\n\n" + VALID + "\n\n", 0, "Knowledge lint: passed")

    # Malformed JSON.
    run_case(tmp, "malformed-json", "{not json", 1, "not valid JSON")

    # Not an object.
    run_case(tmp, "scalar-line", '"just a string"', 1, "must be a JSON object")
    run_case(tmp, "list-line", "[1, 2, 3]", 1, "must be a JSON object")

    # Missing required keys — the PR#870 failure mode.
    run_case(tmp, "missing-keys", '{"id": "K-0001"}', 1, "missing required keys")
    run_case(tmp, "missing-source-only",
             json.dumps({k: v for k, v in json.loads(_entry()).items()
                         if k != "source"}),
             1, "missing required keys: ['source']")

    # Unknown extra keys.
    run_case(tmp, "unknown-keys", _entry(extra=1), 1, "unknown keys")

    # Optional tier field: valid values pass, invalid value / type fail.
    run_case(tmp, "tier-valid", _entry(tier="invariant"), 0, "Knowledge lint: passed")
    run_case(tmp, "tier-observation", _entry(tier="observation"), 0,
             "Knowledge lint: passed")
    run_case(tmp, "tier-bad-value", _entry(tier="legendary"), 1, "must be one of")
    run_case(tmp, "tier-bad-type", _entry(tier=[]), 1, "tier must be a string")
    run_case(tmp, "tier-null", _entry(tier=None), 1, "tier must be a string")

    # Non-string scope: must error without crashing (type-guard regression).
    run_case(tmp, "scope-list", _entry(scope=[]), 1, "must be a non-empty string")

    # Bad id format.
    run_case(tmp, "bad-id", _entry(id="K-1"), 1, "must match")

    # Duplicate id.
    run_case(tmp, "duplicate-id", _entry() + "\n" + _entry(), 1, "duplicate id")

    # Bad kind.
    run_case(tmp, "bad-kind", _entry(kind="tip"), 1, "must be one of")

    # Empty string field.
    run_case(tmp, "empty-scope", _entry(scope=""), 1, "must be a non-empty string")

    # Non-string field.
    run_case(tmp, "non-string-title", _entry(title=42), 1, "must be a non-empty string")

    # Two valid entries with sequential ids.
    run_case(tmp, "two-valid",
             VALID + "\n" + '{"id": "K-0002", "kind": "gotcha", "scope": "*", '
             '"title": "T2", "body": "B2", "source": "PR#2"}',
             0, "passed")

    # null-valued required field (JSON null is not a string).
    run_case(tmp, "null-title", _entry(title=None), 1, "must be a non-empty string")

    # Trailing garbage after a valid JSON object on the same line: json.loads
    # rejects it ("Extra data") — locks the behaviour.
    run_case(tmp, "trailing-garbage", VALID + " garbage-after", 1, "not valid JSON")

    # Duplicate id where the two entries differ in body — dedup is by id alone.
    run_case(tmp, "duplicate-id-different-body",
             _entry(title="first", body="B1") + "\n" + _entry(title="second", body="B2"),
             1, "duplicate id")

    # Multiple shape errors on a single line surface in one lint run.
    global RAN
    RAN += 1
    path = tmp / "multi.jsonl"
    path.write_text('{"id": "bad", "scope": "x", "title": "t", "body": "b", '
                    '"source": "s", "stray": 1}', encoding="utf-8")
    proc = _lint(path)
    out = proc.stdout + proc.stderr
    if (proc.returncode == 1 and "missing required keys" in out
            and "unknown keys" in out and "must match" in out):
        ok("multi-error-one-line")
    else:
        fail("multi-error-one-line",
             f"expected three error categories in one run\n"
             f"  exit={proc.returncode}\n  output: {out}")


# --- Shared: the linter's enforced sets ------------------------------------

def _enforced_sets() -> tuple[set[str], set[str], set[str]]:
    script = LINTER.read_text(encoding="utf-8")
    req = re.search(r"REQUIRED_KEYS\s*=\s*\{([^}]+)\}", script)
    opt = re.search(r"OPTIONAL_KEYS\s*=\s*\{([^}]+)\}", script)
    kinds = re.search(r"ALLOWED_KINDS\s*=\s*\{([^}]+)\}", script)
    if not req or not kinds:
        raise SystemExit("could not find REQUIRED_KEYS / ALLOWED_KINDS in the linter")
    return (
        set(re.findall(r'"([^"]+)"', req.group(1))),
        set(re.findall(r'"([^"]+)"', opt.group(1))) if opt else set(),
        set(re.findall(r'"([^"]+)"', kinds.group(1))),
    )


# --- Layer 2: schema drift (README field table vs linter) -------------------

def layer_schema_drift(required: set[str], optional: set[str],
                       kinds: set[str]) -> None:
    global RAN
    RAN += 1
    readme = ROOT / "docs" / "knowledge" / "README.md"
    if not readme.is_file():
        fail("schema-drift-readme-vs-script",
             f"no docs/knowledge/README.md under {ROOT} — wrong repo root?")
        return
    text = readme.read_text(encoding="utf-8")

    # The README's field table: first column, backticked, one row per line.
    table_keys = set(re.findall(r"^\|\s*`([a-zA-Z_]+)`\s*\|", text, re.MULTILINE))
    kind_lines = [ln for ln in text.splitlines()
                  if re.match(r"^\|\s*`kind`\s*\|", ln)]
    if not kind_lines:
        fail("schema-drift-readme-vs-script", "README missing the canonical kind row")
        return
    readme_kinds = set(re.findall(r"`([a-z]+)`", kind_lines[0])) - {"kind"}

    all_keys = required | optional
    if table_keys != all_keys:
        fail("schema-drift-readme-vs-script",
             f"script={sorted(all_keys)} readme={sorted(table_keys)} "
             f"missing_from_readme={sorted(all_keys - table_keys)} "
             f"extra_in_readme={sorted(table_keys - all_keys)}")
        return
    if kinds != readme_kinds:
        fail("schema-drift-readme-vs-script",
             f"kinds: script={sorted(kinds)} readme={sorted(readme_kinds)}")
        return
    ok("schema-drift-readme-vs-script")


# --- Layer 3: guidance drift ------------------------------------------------

# Discovered, not enumerated: the guidance is repeated across the pack source,
# every per-adapter projection, and both knowledge READMEs, and that set grows
# whenever an adapter is added. A hardcoded list would silently stop covering
# the new copy; walking the tree cannot.
# (containing directory, filename) pairs — every surface that tells a writer
# how to author an entry.
_SURFACES = frozenset({
    ("work-loop", "SKILL.md"),
    ("knowledge", "README.md"),
})
# `fixtures` / `tests` are excluded because a skill body under a test tree is
# frozen snapshot data — updating it to match current guidance would defeat the
# snapshot. The rest are vendored or generated trees.
_SKIP_DIRS = frozenset({
    ".git", "node_modules", "__pycache__", "dist", "build",
    "fixtures", "tests", ".venv", "site-packages",
})


def _guidance_surfaces() -> list[tuple[str, Path]]:
    """The skill this script ships inside is the floor; everything else is
    whatever the tree actually holds."""
    seen = {SKILL.resolve()}
    surfaces: list[tuple[str, Path]] = [(_rel(SKILL), SKILL)]
    # os.walk(followlinks=False), not Path.glob("**/...") — `**` does not follow
    # symlinks before 3.13 but does from 3.13 on, so glob would silently change
    # behaviour across interpreters and could walk out of the tree.
    for dirpath, dirnames, filenames in os.walk(ROOT, followlinks=False):
        dirnames[:] = [d for d in dirnames if d not in _SKIP_DIRS]
        parent = Path(dirpath).name
        for filename in sorted(filenames):
            if (parent, filename) not in _SURFACES:
                continue
            path = Path(dirpath) / filename
            if path.is_symlink() or path.resolve() in seen:
                continue
            seen.add(path.resolve())
            surfaces.append((_rel(path), path))
    return sorted(surfaces)


def _rel(path: Path) -> str:
    """Repo-relative display name — an absolute path in a CI failure message
    leaks the runner's filesystem layout and is harder to act on."""
    try:
        return str(path.resolve().relative_to(ROOT.resolve()))
    except ValueError:
        return str(path)


def _check_key_list(name: str, text: str, required: set[str],
                    optional: set[str]) -> list[str]:
    """The required-key list must be stated inline.

    Scoped to the **bolded** key run inside the sentence naming it: the prose
    wraps, so a line-scoped search would silently see only half the list, and a
    whole-sentence scan would trip over any other backticked word the sentence
    happens to use (`grep`, `json`) as well as the trailing optional-key
    mention.
    """
    flat = re.sub(r"\s+", " ", text)
    sentences = [s for s in re.split(r"(?<=\.)\s", flat)
                 if "required keys" in s.lower()]
    if not sentences:
        return [f"{name} names no required-key list"]
    named: set[str] = set()
    for sentence in sentences:
        for run in re.findall(r"\*\*(.+?)\*\*", sentence):
            if "required keys" in run.lower():
                named |= set(re.findall(r"`([a-z]+)`", run))
    if not named:
        return [f"{name} names 'required keys' but no backticked key list sits "
                f"inside a bolded **...** run in that sentence — the key list "
                f"must be bolded so this check can find it"]
    problems = []
    if not required <= named:
        problems.append(f"{name} omits required key(s) {sorted(required - named)} "
                        f"from its inline key list")
    if not named <= (required | optional):
        problems.append(f"{name} names non-schema key(s) "
                        f"{sorted(named - required - optional)}")
    return problems


# A JSON fence may hold something other than a knowledge entry; treat a line as
# an example when it uses any schema key, so an example that *omits* `id` — a
# required-key omission, the drift this guards — is checked rather than skipped.
def _check_examples(name: str, text: str, tmp: Path,
                    schema_keys: set[str]) -> list[str]:
    """Every documented example entry must lint clean. `K-NNNN` is the
    documented id placeholder; give each a distinct concrete id first, so two
    placeholder examples on one surface don't collide into a false duplicate."""
    examples: list[str] = []
    problems: list[str] = []
    for block in re.findall(r"```jsonl?\n(.*?)```", text, re.DOTALL):
        for line in block.splitlines():
            line = line.strip()
            if not line:
                continue
            try:
                entry = json.loads(line)
            except json.JSONDecodeError as exc:
                # Only a knowledge-shaped line is our business; a fence holding
                # some other JSON is not. Look for the tell before complaining.
                if '"kind"' in line or '"scope"' in line or line.startswith('{"id"'):
                    problems.append(f"{name} has an unparseable example entry "
                                    f"({exc.msg}): {line[:70]}")
                continue
            if isinstance(entry, dict) and set(entry) & schema_keys:
                examples.append(line.replace("K-NNNN",
                                             f"K-{9000 + len(examples):04d}"))
    if not examples:
        return problems + [f"{name} carries no example entry"]
    fixture = tmp / (re.sub(r"[^\w]+", "_", name) + ".example.jsonl")
    fixture.write_text("\n".join(examples) + "\n", encoding="utf-8")
    proc = _lint(fixture)
    if proc.returncode != 0:
        return problems + [f"example entry in {name} does not lint clean\n"
                           f"{proc.stdout}{proc.stderr}"]
    return problems


# The pack source, both projections, and both knowledge READMEs. A discovery
# bug that silently found fewer would let real drift through while reporting
# success, so the floor is asserted rather than assumed.
_MIN_SURFACES = 5


def layer_guidance_drift(tmp: Path, required: set[str], optional: set[str]) -> None:
    global RAN
    RAN += 1
    surfaces = _guidance_surfaces()
    for name, _ in surfaces:
        print(f"     surface: {name}")
    problems: list[str] = []
    if len(surfaces) < _MIN_SURFACES:
        problems.append(
            f"discovered {len(surfaces)} guidance surface(s), expected at least "
            f"{_MIN_SURFACES} — discovery is broken or the tree is incomplete"
        )
    for name, path in surfaces:
        text = path.read_text(encoding="utf-8")
        problems += _check_key_list(name, text, required, optional)
        problems += _check_examples(name, text, tmp, required | optional)
    problems += _check_readme_parity()
    if problems:
        fail("guidance-names-required-keys", "\n  ".join(problems))
    else:
        ok("guidance-names-required-keys")


def _check_readme_parity() -> list[str]:
    """The repo README and its seed must state verification identically.

    A comment asking two files to stay in sync is not a guard; every other
    duplicated block in this repo is checked mechanically.
    """
    pair = [ROOT / "docs" / "knowledge" / "README.md",
            ROOT / "packs" / "core" / "seeds" / "docs" / "knowledge" / "README.md"]
    sections = []
    for path in pair:
        if not path.is_file():
            return [f"{_rel(path)} missing — cannot check Verify-section parity"]
        match = re.search(r"## Verify before committing\n(.*?)\n## ",
                          path.read_text(encoding="utf-8"), re.DOTALL)
        if not match:
            return [f"{_rel(path)} has no '## Verify before committing' section"]
        sections.append(match.group(1))
    if sections[0] != sections[1]:
        return ["docs/knowledge/README.md and its seed have drifted in "
                "'## Verify before committing' — they must be byte-identical"]
    return []


# --- Layer 4: the live knowledge base lints clean ---------------------------

def layer_production_file() -> None:
    global RAN
    RAN += 1
    live = ROOT / "docs" / "knowledge" / "patterns.jsonl"
    if not live.is_file():
        fail("production-file",
             f"no docs/knowledge/patterns.jsonl under {ROOT} — wrong repo root?")
        return
    proc = _lint(live)
    if proc.returncode == 0:
        ok("production-file")
    else:
        fail("production-file",
             f"docs/knowledge/patterns.jsonl is not clean\n"
             f"{proc.stdout}{proc.stderr}")


def main() -> int:
    required, optional, kinds = _enforced_sets()
    with tempfile.TemporaryDirectory() as td:
        tmp = Path(td)
        layer_validation_rules(tmp)
        layer_schema_drift(required, optional, kinds)
        layer_guidance_drift(tmp, required, optional)
        layer_production_file()

    print()
    if FAILURES:
        print(f"✖ test-lint-knowledge: {len(FAILURES)} of {RAN} cases failed",
              file=sys.stderr)
        return 1
    print(f"✓ test-lint-knowledge: passed ({RAN} cases).")
    return 0


if __name__ == "__main__":
    sys.exit(main())
