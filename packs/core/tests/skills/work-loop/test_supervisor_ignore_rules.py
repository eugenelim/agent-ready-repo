"""A full run needs no ignore rule for the supervisor's local directories.

The fixture repository's `.gitignore` omits both `.supervisor/` and `.loop-run/`,
as an adopter's may when its ignore file predates the seed. The run still reaches
readiness, `.loop-run/` stays untracked, and no commit the supervisor made touches
either directory.
"""

from __future__ import annotations

import importlib.util
import sys
from pathlib import Path
from types import ModuleType

# Each shared helper by literal path, so every file this suite loads stays visibly
# inside this pack.
_HELPER_PATHS = {
    "supervisor_harness": Path(__file__).resolve().parent / "supervisor_harness.py",
    "supervisor_support": Path(__file__).resolve().parent / "supervisor_support.py",
}


def _helper(name: str) -> ModuleType:
    """Load a shared supervisor test helper by path under a pack- and skill-qualified name."""
    alias = f"core_work_loop_{name}"
    if alias not in sys.modules:
        spec = importlib.util.spec_from_file_location(alias, _HELPER_PATHS[name])
        assert spec is not None and spec.loader is not None
        sys.modules[alias] = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(sys.modules[alias])
    return sys.modules[alias]


h = _helper("supervisor_harness")
sup = _helper("supervisor_support")


@sup.INTEGRATION
def test_vi7016_a_full_run_reaches_readiness_without_ignore_rules(tmp_path: Path) -> None:
    """VI-7016: readiness with `.supervisor/` and `.loop-run/` unignored, and never committed."""
    repo = h.make_repo(tmp_path)
    (repo / ".gitignore").write_text("*.log\n__pycache__/\n", encoding="utf-8")
    h.git(repo, "add", "-A")
    h.git(repo, "commit", "-q", "-m", "drop the supervisor ignore rules")

    code, started = h.start(repo)
    assert code == 0, started
    end = h.Controller(repo, tmp_path / "effects.log").drive()
    assert end.get("terminal"), end

    status = h.git(repo, "status", "--porcelain", "--untracked-files=all")
    assert ".loop-run/" in status, status  # the directory exists and nothing ignores it
    assert (repo / h.SPEC_DIR / ".supervisor" / "run.json").is_file()
    assert (repo / ".gitignore").read_text(encoding="utf-8") == "*.log\n__pycache__/\n"
    committed = h.git(repo, "log", "--name-only", "--format=", "--all")
    assert ".supervisor/" not in committed and ".loop-run/" not in committed, committed
