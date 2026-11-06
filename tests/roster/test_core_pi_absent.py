"""Pi-absent check: Core's source, manifests and supervisor never depend on Pi.

Four claims, each with red evidence:

1. AC-0010: no file under ``packs/core/`` holds a "Pi reference" (the spec's
   term, implemented by ``scan_pi_references``). One planted violation per
   alternative, in a scratch root, turns the scan red; near-misses stay green.
2. AC-0011: no dependency manifest under ``packs/core/`` names a package or
   pack in which ``pi`` is a whole hyphen-, underscore-, dot- or slash-separated
   word (``find_pi_manifest_dependencies``).
3. AC-0012: the projected supervisor's ``start`` then ``next`` exit ``0`` in an
   environment built from scratch where ``pi`` does not resolve.
4. AC-0013: the same run with a sentinel ``pi`` first on ``PATH`` exits ``0``
   and the sentinel records no run.

Roster-owned: reads the pack tree and the projected skill together and runs
subprocesses. Placed above the bulk ``pytest tests/`` step in build-check.yml.

Spec: docs/specs/pi-runtime-compatibility/spec.md
"""

from __future__ import annotations

import ast
import importlib.util
import json
import os
import re
import shutil
import stat
import subprocess
import sys
import tomllib
from collections.abc import Iterator
from pathlib import Path
from types import ModuleType
from typing import Any

import pytest

REPO_ROOT = Path(__file__).resolve().parents[2]
CORE_ROOT = REPO_ROOT / "packs" / "core"
_SUPERVISOR = REPO_ROOT / ".claude" / "skills" / "work-loop" / "scripts" / "work-supervisor.py"
_HARNESS = (
    REPO_ROOT / "packs" / "core" / "tests" / "skills" / "work-loop" / "supervisor_harness.py"
)

# ═══════════════════════════════════════════════════════════════════════════════
# The "Pi reference" term
# ═══════════════════════════════════════════════════════════════════════════════

_SUBSTRINGS = (
    "agent-ready-pi",
    "agent_ready_pi",
    "@mariozechner/pi",
    "@earendil-works/pi",
    "pi-coding-agent",
    "PI_CODING_AGENT_",
    "PI_PACKAGE_DIR",
)
_NO_WORD = r"(?<![A-Za-z0-9_])"
_WORD_END = r"(?![A-Za-z0-9_])"
_TEXT_RULES: dict[str, re.Pattern[str]] = {
    name: re.compile(pattern, re.IGNORECASE)
    for name, pattern in {
        "pi-install": _NO_WORD + r"pi install",
        "dot-pi": _NO_WORD + r"\.pi(?:/|[\"'`])",
        "pi-flag": _NO_WORD + r"pi\s+-",
        "which-pi": _NO_WORD + r"(?:which|command\s+-v|npx|exec)\s+pi" + _WORD_END,
        # A quoted literal whose whole value, or last "/" segment, is `pi`; the
        # value may hold the other quote kinds.
        "quoted-pi": r"([\"'`])(?:(?:(?!\1)[^\n])*/)?pi\1",
    }.items()
}


def _names_pi_module(name: str) -> bool:
    """Return True when a module name is ``pi`` or starts with ``pi.`` or ``pi_``."""
    lowered = name.lower()
    return lowered == "pi" or lowered.startswith(("pi.", "pi_"))


def _call_target(node: ast.Call) -> str:
    """Return the called function's final name, or an empty string."""
    func = node.func
    if isinstance(func, ast.Name):
        return func.id
    if isinstance(func, ast.Attribute):
        return func.attr
    return ""


def _python_hits(source: str) -> list[tuple[int, str]]:
    """Return ``(line, why)`` for each Pi reference an ``ast`` walk finds."""
    try:
        tree = ast.parse(source)
    except (SyntaxError, ValueError):
        return []
    hits: list[tuple[int, str]] = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                if _names_pi_module(alias.name):
                    hits.append((node.lineno, f"[ast-import] import of module {alias.name!r}"))
        elif isinstance(node, ast.ImportFrom):
            if node.level == 0 and node.module and _names_pi_module(node.module):
                hits.append((
                    node.lineno,
                    f"[ast-from-import] from-import of module {node.module!r}",
                ))
        elif isinstance(node, ast.Constant) and isinstance(node.value, str):
            text = node.value.strip().lower()
            if text == "pi" or text.startswith("pi "):
                hits.append((node.lineno, f"[ast-literal] string literal {node.value!r}"))
        elif isinstance(node, ast.Call) and _call_target(node) in {"import_module", "__import__"}:
            first = node.args[0] if node.args else None
            if (
                isinstance(first, ast.Constant)
                and isinstance(first.value, str)
                and _names_pi_module(first.value)
            ):
                hits.append((
                    node.lineno,
                    f"[ast-dynamic-import] dynamic import of {first.value!r}",
                ))
    return hits


def _text_of(path: Path) -> str | None:
    """Return a file's text, or None for a binary or undecodable file."""
    try:
        data = path.read_bytes()
    except OSError:
        return None
    if b"\0" in data:
        return None
    try:
        return data.decode("utf-8")
    except UnicodeDecodeError:
        return None


def scan_pi_references(root: Path) -> list[str]:
    """Return ``file:line: [rule] why`` for every Pi reference in a text file under root."""
    findings: set[str] = set()
    for path in sorted(p for p in root.rglob("*") if p.is_file()):
        text = _text_of(path)
        if text is None:
            continue
        rel = path.relative_to(root).as_posix()
        for number, line in enumerate(text.splitlines(), start=1):
            lowered = line.lower()
            for needle in _SUBSTRINGS:
                if needle.lower() in lowered:
                    findings.add(f"{rel}:{number}: [substring] {needle!r}")
            for rule, pattern in _TEXT_RULES.items():
                if pattern.search(line):
                    findings.add(f"{rel}:{number}: [{rule}] pattern {pattern.pattern!r}")
        if path.suffix == ".py":
            for number, why in _python_hits(text):
                findings.add(f"{rel}:{number}: {why}")
    return sorted(findings)


# ═══════════════════════════════════════════════════════════════════════════════
# Manifest dependencies (AC-0011)
# ═══════════════════════════════════════════════════════════════════════════════

_NAME_WORDS = re.compile(r"[-_./]")
_REQUIREMENT_NAME_END = re.compile(r"[\s<>=!~;\[@(,]")
_EGG = re.compile(r"[#&]egg=([^\s&]+)")
_NPM_DEPENDENCY_KEYS = (
    "dependencies",
    "devDependencies",
    "peerDependencies",
    "optionalDependencies",
)


def _is_pi_name(name: str) -> bool:
    """Return True when ``pi`` is a whole separator-delimited word of name."""
    return "pi" in _NAME_WORDS.split(name.lower())


def _requirement_name(line: str) -> str:
    """Return the package name of one requirement line (text before a version or marker)."""
    return _REQUIREMENT_NAME_END.split(line.strip(), maxsplit=1)[0]


def _url_requirement_name(text: str) -> str:
    """Return the package name a URL requirement names: its ``#egg=`` or file name."""
    egg = _EGG.search(text)
    if egg:
        return egg.group(1)
    tail = text.split("#", 1)[0].split("?", 1)[0].rstrip("/").rsplit("/", 1)[-1]
    tail = re.sub(r"\.(?:tar\.gz|tgz|zip|whl|git)$", "", tail)
    return re.split(r"-(?=\d)", tail, maxsplit=1)[0]


def _requirements_line_name(line: str) -> str | None:
    """Return the package a requirements line names, or None for a comment or option."""
    text = line.strip()
    if not text or text.startswith("#"):
        return None
    if text.startswith("-"):
        option, _, rest = text.partition(" ")
        if option not in {"-e", "--editable"} or not rest.strip():
            return None
        text = rest.strip()
    if "://" in text and not re.match(r"[A-Za-z0-9._-]+\s*@", text):
        return _url_requirement_name(text)
    return _requirement_name(text)


def _pyproject_names(data: dict[str, Any]) -> Iterator[str]:
    """Yield dependency names from a parsed ``pyproject.toml``'s ``[project]`` table."""
    project = data.get("project", {})
    for spec in project.get("dependencies", []):
        yield _requirement_name(str(spec))
    for specs in project.get("optional-dependencies", {}).values():
        for spec in specs:
            yield _requirement_name(str(spec))


def _manifest_names(path: Path) -> Iterator[str]:
    """Yield every dependency name a recognised manifest declares."""
    name = path.name
    if name == "pack.toml":
        pack = tomllib.loads(path.read_text(encoding="utf-8")).get("pack", {})
        for entry in pack.get("runtime-dependencies", []):
            yield str(entry.get("package", ""))
        for entry in pack.get("integrations", []):
            yield str(entry.get("pack", ""))
    elif name == "pyproject.toml":
        yield from _pyproject_names(tomllib.loads(path.read_text(encoding="utf-8")))
    elif name in {"plugin.json", "package.json"}:
        data = json.loads(path.read_text(encoding="utf-8"))
        if isinstance(data, dict):
            for key in _NPM_DEPENDENCY_KEYS:
                section = data.get(key)
                if isinstance(section, dict):
                    yield from (str(k) for k in section)
    elif name.startswith("requirements") and name.endswith(".txt"):
        for line in path.read_text(encoding="utf-8").splitlines():
            dep = _requirements_line_name(line)
            if dep:
                yield dep


def find_pi_manifest_dependencies(root: Path) -> list[str]:
    """Return ``file: name`` for every dependency name under root with a ``pi`` word."""
    findings: list[str] = []
    for path in sorted(p for p in root.rglob("*") if p.is_file()):
        n = path.name
        if not (
            n in {"pack.toml", "pyproject.toml", "plugin.json", "package.json"}
            or (n.startswith("requirements") and n.endswith(".txt"))
        ):
            continue
        for dep in _manifest_names(path):
            if _is_pi_name(dep):
                findings.append(f"{path.relative_to(root).as_posix()}: {dep!r}")
    return findings


# ═══════════════════════════════════════════════════════════════════════════════
# AC-0010: static scan
# ═══════════════════════════════════════════════════════════════════════════════


def _plant(root: Path, name: str, content: str) -> Path:
    """Write one scratch file under root and return its path."""
    path = root / name
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")
    return path


def test_core_pack_holds_no_pi_reference() -> None:
    """AC-0010: the real ``packs/core/`` tree has no Pi reference."""
    assert CORE_ROOT.is_dir(), CORE_ROOT
    hits = scan_pi_references(CORE_ROOT)
    assert not hits, (
        f'{len(hits)} Pi reference(s) under packs/core/ (the spec\'s "Pi reference" term):\n'
        + "\n".join(hits)
    )


# case -> (file, content, the exact set of rules the scan reports). A case whose
# set holds only an ``ast-`` rule is invisible to every text pattern, so it reds
# only through that AST rule.
_RED_PLANTS: dict[str, tuple[str, str, frozenset[str]]] = {
    "sub-agent-ready-pi": ("a.md", "see agent-ready-pi for details\n", frozenset({"substring"})),
    "sub-agent_ready_pi": ("a.txt", "import agent_ready_pi_stuff\n", frozenset({"substring"})),
    "sub-mariozechner": ("a.json", '{"x": "@mariozechner/pi-ai"}\n', frozenset({"substring"})),
    "sub-earendil": ("a.json", '{"x": "@earendil-works/pi-tui"}\n', frozenset({"substring"})),
    "sub-coding-agent": ("a.md", "uses Pi-Coding-Agent here\n", frozenset({"substring"})),
    "sub-env-dir": ("a.sh", "export PI_CODING_AGENT_DIR=/x\n", frozenset({"substring"})),
    "sub-package-dir": ("a.sh", "export pi_package_dir=/x\n", frozenset({"substring"})),
    "text-pi-install": ("a.md", "run `pi install foo`\n", frozenset({"pi-install"})),
    "text-dot-pi-slash": ("a.sh", "cat .pi/settings.json\n", frozenset({"dot-pi"})),
    "text-dot-pi-quote": ("a.js", 'const d = ".pi";\n', frozenset({"dot-pi"})),
    "text-pi-flag": ("a.sh", "pi --mode rpc\n", frozenset({"pi-flag"})),
    "text-which-pi": ("a.sh", "which pi\n", frozenset({"which-pi"})),
    "text-command-v-pi": ("a.sh", "command -v pi >/dev/null\n", frozenset({"which-pi"})),
    "text-npx-pi": ("a.sh", "npx pi\n", frozenset({"which-pi"})),
    "text-exec-pi": ("a.sh", "exec  pi\n", frozenset({"which-pi"})),
    "text-bin-pi-literal": ("a.sh", 'BIN="bin/pi"\n', frozenset({"quoted-pi"})),
    "text-other-quote-literal": ("a.sh", 'BIN="it\'s/pi"\n', frozenset({"quoted-pi"})),
    "text-js-spawn": ("a.js", 'spawn("pi", []);\n', frozenset({"quoted-pi"})),
    "py-import-pi": ("a.py", "import pi\n", frozenset({"ast-import"})),
    "py-from-pi": ("a.py", "from pi import x\n", frozenset({"ast-from-import"})),
    "py-import-pi-runtime": ("a.py", "import pi_runtime\n", frozenset({"ast-import"})),
    "py-import-dotted": ("a.py", "import pi.sub\n", frozenset({"ast-import"})),
    "py-literal-pi": ("a.py", "NAME = 'pi'\n", frozenset({"ast-literal", "quoted-pi"})),
    "py-literal-pi-flag": (
        "a.py",
        "CMD = 'pi --mode rpc'\n",
        frozenset({"ast-literal", "pi-flag"}),
    ),
    "py-literal-pi-run-ast-only": ("a.py", 'CMD = "pi run"\n', frozenset({"ast-literal"})),
    "py-literal-padded-ast-only": ("a.py", 'NAME = "  Pi  "\n', frozenset({"ast-literal"})),
    "py-import-module": (
        "a.py",
        "import importlib\nimportlib.import_module('pi')\n",
        frozenset({"ast-dynamic-import", "ast-literal", "quoted-pi"}),
    ),
    "py-import-module-dotted-ast-only": (
        "a.py",
        'import importlib\nimportlib.import_module("pi.sub")\n',
        frozenset({"ast-dynamic-import"}),
    ),
    "py-dunder-import": ("a.py", "__import__('pi_x')\n", frozenset({"ast-dynamic-import"})),
    "py-literal-bin-pi": ("a.py", "P = 'bin/pi'\n", frozenset({"quoted-pi"})),
    "py-literal-dot-pi": ("a.py", "P = '.pi'\n", frozenset({"dot-pi"})),
}


def _rules_of(findings: list[str]) -> set[str]:
    """Return the rule names in ``file:line: [rule] why`` findings."""
    rules: set[str] = set()
    for finding in findings:
        found = re.search(r": \[([a-z-]+)\] ", finding)
        assert found, f"finding carries no rule identifier: {finding!r}"
        rules.add(found.group(1))
    return rules


@pytest.mark.parametrize("case", sorted(_RED_PLANTS))
def test_scan_reds_on_each_planted_alternative(case: str, tmp_path: Path) -> None:
    """AC-0010 red evidence: each alternative is detected, and by the rule it targets."""
    name, content, rules = _RED_PLANTS[case]
    _plant(tmp_path, name, content)
    findings = scan_pi_references(tmp_path)
    assert findings, f"{case}: scan missed {content!r}"
    assert all(f.startswith(f"{name}:") for f in findings)
    assert _rules_of(findings) == rules, f"{case}: {findings}"


_GREEN_PLANTS: dict[str, tuple[str, str]] = {
    "pip-install": ("a.sh", "pip install x\n"),
    "sibling-assignment": ("a.py", 'pi = sibling("_policy_import.py")\n'),
    "spec-from-file-location": (
        "a.py",
        'import importlib.util\nimportlib.util.spec_from_file_location("pi_t5", "p.py")\n',
    ),
    "openapi-install": ("a.md", "openapi install the client\n"),
    "pipx-word": ("a.md", "pipx install tool; the pipeline runs\n"),
}


@pytest.mark.parametrize("case", sorted(_GREEN_PLANTS))
def test_scan_stays_green_on_near_misses(case: str, tmp_path: Path) -> None:
    """Near-misses that merely contain the letters ``pi`` are not Pi references."""
    name, content = _GREEN_PLANTS[case]
    _plant(tmp_path, name, content)
    assert scan_pi_references(tmp_path) == []


def test_scan_skips_binary_and_undecodable_files(tmp_path: Path) -> None:
    """Binary and non-UTF-8 files are skipped, not crashed on."""
    (tmp_path / "a.bin").write_bytes(b"agent-ready-pi\0\x01")
    (tmp_path / "b.dat").write_bytes(b"\xff\xfeagent-ready-pi")
    assert scan_pi_references(tmp_path) == []


def test_scan_reports_file_and_line(tmp_path: Path) -> None:
    """A hit names its file and 1-based line."""
    _plant(tmp_path, "d/x.md", "ok\nok\nwhich pi\n")
    findings = scan_pi_references(tmp_path)
    assert len(findings) == 1 and findings[0].startswith("d/x.md:3: [which-pi] ")


# ═══════════════════════════════════════════════════════════════════════════════
# AC-0011: manifests
# ═══════════════════════════════════════════════════════════════════════════════


def test_core_manifests_name_no_pi_dependency() -> None:
    """AC-0011: no manifest under ``packs/core/`` names a Pi dependency."""
    manifests = [
        p for p in CORE_ROOT.rglob("*") if p.name in {"pack.toml", "plugin.json", "package.json"}
    ]
    assert manifests, "expected at least pack.toml under packs/core"
    assert find_pi_manifest_dependencies(CORE_ROOT) == []


_MANIFEST_PLANTS: dict[str, tuple[str, str]] = {
    "runtime-dependencies": (
        "pack.toml",
        '[[pack.runtime-dependencies]]\necosystem = "npm"\npackage = "@scope/pi-agent"\n',
    ),
    "integrations": ("pack.toml", '[[pack.integrations]]\nid = "x"\npack = "pi"\n'),
    "plugin-json": ("plugin.json", '{"dependencies": {"pi": "1"}}'),
    "package-json-dev": ("package.json", '{"devDependencies": {"foo.pi": "1"}}'),
    "package-json-peer": ("package.json", '{"peerDependencies": {"pi_core": "1"}}'),
    "package-json-optional": ("package.json", '{"optionalDependencies": {"a/pi": "1"}}'),
    "requirements": (
        "requirements-dev.txt",
        "# c\nrequests>=2\nPi-tools==1.0 ; python_version>'3'\n",
    ),
    "requirements-editable-egg": (
        "requirements.txt",
        "-e git+https://example.test/x.git#egg=pi\n",
    ),
    "requirements-url-egg": ("requirements.txt", "https://example.test/x.zip#egg=pi-tools\n"),
    "requirements-url-file": ("requirements.txt", "https://example.test/dl/pi-1.0.tar.gz\n"),
    "pyproject-deps": ("pyproject.toml", '[project]\nname = "x"\ndependencies = ["pi>=1"]\n'),
    "pyproject-optional": (
        "pyproject.toml",
        '[project]\nname = "x"\n[project.optional-dependencies]\nextra = ["x-pi[y]"]\n',
    ),
}


@pytest.mark.parametrize("case", sorted(_MANIFEST_PLANTS))
def test_manifest_check_reds_on_each_source(case: str, tmp_path: Path) -> None:
    """AC-0011 red evidence: one plant per manifest source is detected."""
    name, content = _MANIFEST_PLANTS[case]
    _plant(tmp_path, name, content)
    assert find_pi_manifest_dependencies(tmp_path), case


def test_manifest_check_stays_green_on_near_miss_names(tmp_path: Path) -> None:
    """``pipx`` and ``api-client`` do not hold ``pi`` as a whole word."""
    _plant(tmp_path, "requirements.txt", "pipx>=1\napi-client==2\n")
    _plant(tmp_path, "package.json", '{"dependencies": {"pipx": "1", "api-client": "2"}}')
    _plant(tmp_path, "pack.toml", '[[pack.runtime-dependencies]]\npackage = "pipx"\n')
    _plant(
        tmp_path,
        "requirements-extra.txt",
        "-r other.txt\n-e git+https://x.test/a.git#egg=api-client\n",
    )
    assert find_pi_manifest_dependencies(tmp_path) == []


# ═══════════════════════════════════════════════════════════════════════════════
# AC-0012 / AC-0013: supervisor with Pi unreachable, and with a sentinel Pi
# ═══════════════════════════════════════════════════════════════════════════════


def _load_harness() -> ModuleType:
    """Load the supervisor test harness by path."""
    spec = importlib.util.spec_from_file_location("supervisor_harness_for_pi_absent", _HARNESS)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules["supervisor_harness_for_pi_absent"] = module
    spec.loader.exec_module(module)
    return module


def _pi_free_path(extra_first: list[Path], tmp_path: Path) -> str:
    """Return a ``PATH`` whose entries hold no ``pi`` executable, git still resolvable."""
    kept = [
        entry
        for entry in os.environ.get("PATH", os.defpath).split(os.pathsep)
        if entry and shutil.which("pi", path=entry) is None
    ]
    path = os.pathsep.join([str(p) for p in extra_first] + kept)
    if shutil.which("git", path=path) is None:
        git = shutil.which("git")
        assert git is not None, "git is not installed"
        bin_dir = tmp_path / "gitbin"
        bin_dir.mkdir()
        (bin_dir / "git").symlink_to(git)
        path = os.pathsep.join([str(bin_dir), path])
    return path


def _scratch_env(path: str, home: Path) -> dict[str, str]:
    """Build an environment from scratch: no ``PI_`` variable, the given PATH and HOME."""
    env = {
        "PATH": path,
        "HOME": str(home),
        "PYTHONPATH": "",
        "PYTHONNOUSERSITE": "1",
        **{k: v for k, v in os.environ.items() if k.startswith("DYLD_")},
        **{k: v for k, v in os.environ.items() if k in ("SYSTEMROOT", "TEMP", "TMP")},
    }
    assert not any(k.upper().startswith("PI_") for k in env)
    return env


_SUPERVISOR_TIMEOUT_S = 900


def _as_text(data: str | bytes | None) -> str:
    """Return captured output as text; a timeout can hand back bytes or None."""
    if data is None:
        return ""
    return data.decode("utf-8", errors="replace") if isinstance(data, bytes) else data


def _run_supervisor_start_and_next(tmp_path: Path, env: dict[str, str]) -> None:
    """Run the projected supervisor's ``start`` then ``next``; both must exit 0."""
    harness = _load_harness()
    repo = harness.make_repo(tmp_path / "fixture")

    def run(*args: str) -> dict[str, Any]:
        command = [sys.executable, "-S", str(_SUPERVISOR), *args]
        try:
            result = subprocess.run(
                command,
                capture_output=True,
                text=True,
                encoding="utf-8",
                env=env,
                cwd=str(repo),
                timeout=_SUPERVISOR_TIMEOUT_S,
            )
        except subprocess.TimeoutExpired as exc:
            pytest.fail(
                f"work-supervisor {args[0]} timed out after {_SUPERVISOR_TIMEOUT_S} s:\n"
                f"command: {command!r}\n"
                f"stdout: {_as_text(exc.stdout)!r}\nstderr: {_as_text(exc.stderr)!r}"
            )
        assert result.returncode == 0, (
            f"work-supervisor {args[0]} failed:\n"
            f"stdout: {result.stdout!r}\nstderr: {result.stderr!r}"
        )
        parsed: dict[str, Any] = json.loads(result.stdout)
        return parsed

    started = run(
        "start",
        harness.SPEC_DIR,
        "--intent",
        "code",
        "--code-trust",
        "trusted",
        "--authority-ref",
        "owner:0123456789ab",
        "--review-authority-ref",
        "plan-reviewer:0123456789ab",
        *harness.digest_args(repo),
    )
    assert started["status"] == "admitted", started
    issued = run("next", harness.SPEC_DIR)
    assert "request" in issued, issued


def test_supervisor_completes_with_pi_unreachable(tmp_path: Path) -> None:
    """AC-0012: ``start`` then ``next`` exit 0 where ``pi`` does not resolve."""
    home = tmp_path / "home"
    home.mkdir()
    env = _scratch_env(_pi_free_path([], tmp_path), home)
    assert shutil.which("pi", path=env["PATH"]) is None
    assert not any(k.startswith("PI_") for k in env)
    _run_supervisor_start_and_next(tmp_path, env)


def test_supervisor_never_starts_a_reachable_pi(tmp_path: Path) -> None:
    """AC-0013: a sentinel ``pi`` first on PATH records no run during start and next."""
    home = tmp_path / "home"
    home.mkdir()
    sentinel_dir = tmp_path / "sentinel-bin"
    sentinel_dir.mkdir()
    record = tmp_path / "pi-runs.log"
    sentinel = sentinel_dir / "pi"
    sentinel.write_text(f'#!/bin/sh\necho "run $$" >> "{record}"\n', encoding="utf-8")
    sentinel.chmod(sentinel.stat().st_mode | stat.S_IXUSR | stat.S_IXGRP | stat.S_IXOTH)
    env = _scratch_env(_pi_free_path([sentinel_dir], tmp_path), home)
    assert shutil.which("pi", path=env["PATH"]) == str(sentinel)
    assert not any(k.startswith("PI_") for k in env)

    # Control: calling the sentinel directly proves it records.
    subprocess.run([str(sentinel)], env=env, check=True, timeout=60)
    assert record.read_text(encoding="utf-8").startswith("run ")
    record.unlink()

    _run_supervisor_start_and_next(tmp_path, env)
    assert not record.exists(), f"sentinel pi ran: {record.read_text(encoding='utf-8')!r}"
