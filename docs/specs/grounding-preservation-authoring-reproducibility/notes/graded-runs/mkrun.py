"""Build one confined graded-run directory from a git revision and print its isolation.

Usage: python3 -I mkrun.py <rev> <dest-dir> <pos|neg>, run from the repository root.
"""

import io
import shutil
import subprocess
import sys
import tarfile
from pathlib import Path

CASE_FILES = {
    "pos": [
        "shared-graph-model.py",
        "shared-graph-consumers.py",
        "shared-graph-builders.py",
        "shared-graph-lifecycle.py",
        "shared-graph-public.rs",
    ],
    "neg": ["isolated_helper.py", "test_isolated_helper.py"],
}


def git(*args: str) -> bytes:
    """Run a git command and return its stdout."""
    return subprocess.run(["git", *args], check=True, capture_output=True).stdout


def core_entries(rev: str) -> tuple[set[str], set[str]]:
    """Return Core's skill directory names and agent file names at ``rev``."""
    skill_paths = git("ls-tree", "-r", "--name-only", rev, "packs/core/.apm/skills/")
    skills = {
        p.split("/")[4]
        for p in skill_paths.decode().splitlines()
        if p.endswith("/SKILL.md") and p.count("/") == 5
    }
    agent_paths = git("ls-tree", "--name-only", rev, "packs/core/.apm/agents/")
    return skills, {Path(p).name for p in agent_paths.decode().splitlines()}


def build(rev: str, dest: Path, case: str) -> None:
    """Extract the projection, keep only Core entries, and copy the case files.

    Every `evals/` directory and `adapt-to-project` are removed from the copy.
    """
    shutil.rmtree(dest, ignore_errors=True)
    (dest / "proj").mkdir(parents=True)
    (dest / "work/evals/files").mkdir(parents=True)
    archive = git("archive", rev, ".claude/skills", ".claude/agents")
    with tarfile.open(fileobj=io.BytesIO(archive)) as tar:
        tar.extractall(dest / "proj", filter="data")
    skills, agents = core_entries(rev)
    for entry in (dest / "proj/.claude/skills").iterdir():
        if entry.name not in skills or entry.name == "adapt-to-project":
            shutil.rmtree(entry)
    for entry in (dest / "proj/.claude/agents").iterdir():
        if entry.name not in agents:
            shutil.rmtree(entry) if entry.is_dir() else entry.unlink()
    for evals in list((dest / "proj").rglob("evals")):
        if evals.is_dir():
            shutil.rmtree(evals, ignore_errors=True)
    for name in CASE_FILES[case]:
        source = f"{rev}:packs/core/.apm/skills/new-spec/evals/files/{name}"
        (dest / "work/evals/files" / name).write_bytes(git("show", source))
    kept_skills = sorted(p.name for p in (dest / "proj/.claude/skills").iterdir())
    kept_agents = sorted(p.name for p in (dest / "proj/.claude/agents").iterdir())
    found = subprocess.run(
        ["find", str(dest / "proj"), "-type", "d", "-name", "evals"],
        capture_output=True,
        text=True,
    ).stdout
    print(f"rev={rev} dir={dest}")
    print(f"skills({len(kept_skills)})={' '.join(kept_skills)}")
    print(f"agents({len(kept_agents)})={' '.join(kept_agents)}")
    print(
        f"skills==core-less-adapt: {kept_skills == sorted(skills - {'adapt-to-project'})}; "
        f"agents==core: {kept_agents == sorted(agents)}"
    )
    print(f"find evals output: {found!r}")


if __name__ == "__main__":
    build(sys.argv[1], Path(sys.argv[2]), sys.argv[3])
