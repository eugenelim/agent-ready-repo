"""Build one confined graded-run directory from a git revision and record its isolation evidence."""
import io, shutil, subprocess, sys, tarfile
from pathlib import Path
rev, dest, case = sys.argv[1], Path(sys.argv[2]), sys.argv[3]
files = {"pos": ["shared-graph-model.py", "shared-graph-consumers.py", "shared-graph-builders.py", "shared-graph-lifecycle.py", "shared-graph-public.rs"],
         "neg": ["isolated_helper.py", "test_isolated_helper.py"]}[case]
def git(*a): return subprocess.run(["git", *a], check=True, capture_output=True).stdout
shutil.rmtree(dest, ignore_errors=True); (dest / "proj").mkdir(parents=True); (dest / "work/evals/files").mkdir(parents=True)
tarfile.open(fileobj=io.BytesIO(git("archive", rev, ".claude/skills", ".claude/agents"))).extractall(dest / "proj", filter="data")
core_skills = {l.split("/")[4] for l in git("ls-tree", "-r", "--name-only", rev, "packs/core/.apm/skills/").decode().splitlines() if l.endswith("/SKILL.md") and l.count("/") == 5}
core_agents = {Path(l).name for l in git("ls-tree", "--name-only", rev, "packs/core/.apm/agents/").decode().splitlines()}
for d in (dest / "proj/.claude/skills").iterdir():
    if d.name not in core_skills or d.name == "adapt-to-project": shutil.rmtree(d)
for f in (dest / "proj/.claude/agents").iterdir():
    if f.name not in core_agents: (shutil.rmtree if f.is_dir() else Path.unlink)(f)
for e in list((dest / "proj").rglob("evals")):
    if e.is_dir(): shutil.rmtree(e, ignore_errors=True)
for f in files:
    (dest / "work/evals/files" / f).write_bytes(git("show", f"{rev}:packs/core/.apm/skills/new-spec/evals/files/{f}"))
skills = sorted(p.name for p in (dest / "proj/.claude/skills").iterdir())
agents = sorted(p.name for p in (dest / "proj/.claude/agents").iterdir())
expected = sorted(core_skills - {"adapt-to-project"})
found = subprocess.run(["find", str(dest / "proj"), "-type", "d", "-name", "evals"], capture_output=True, text=True).stdout
print(f"rev={rev} dir={dest}\nskills({len(skills)})={' '.join(skills)}\nagents({len(agents)})={' '.join(agents)}\nskills==core-less-adapt: {skills == expected}; agents==core: {agents == sorted(core_agents)}\nfind evals output: {found!r}")
