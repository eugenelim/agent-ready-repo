#!/usr/bin/env python3
"""AC9 worktree dry-run (spec docs/specs/wave-scheduled-supervisor/).

Exercises the opt-in parallel-write path end-to-end with REAL git worktrees
+ real `git merge-tree` (via loop-cohort's own `wave_is_disjoint`) +
`dispatch_decision` + a real merge — the dry-run CONVENTIONS "Known
limitation" mandates before trusting the worktree/merge surface. Throwaway
repo, own .git; never touches the host repo.

Reproduce:  python3 docs/specs/wave-scheduled-supervisor/notes/ac9_worktree_dryrun.py
Exit 0 = PASS. See ac9-worktree-dryrun.md for the recorded result.
"""
from __future__ import annotations
import importlib.util, os, subprocess, sys, tempfile
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[4]
LC_PATH = REPO_ROOT / "packs/core/.apm/skills/work-loop/scripts/loop-cohort.py"
_spec = importlib.util.spec_from_file_location("lc_ac9", LC_PATH)
lc = importlib.util.module_from_spec(_spec); _spec.loader.exec_module(lc)


def run(cmd, cwd):
    return subprocess.run(cmd, cwd=cwd, capture_output=True, text=True)


tmp = Path(tempfile.mkdtemp(prefix="ac9-"))
repo = tmp / "repo"; repo.mkdir()
run(["git", "init", "-q", "-b", "main"], repo)
run(["git", "config", "user.email", "a@x"], repo); run(["git", "config", "user.name", "a"], repo)
(repo / "x.py").write_text("X = 1\n"); (repo / "y.py").write_text("Y = 1\n")
run(["git", "add", "-A"], repo); run(["git", "commit", "-q", "-m", "base"], repo)

# task-a edits x.py; task-b edits y.py (disjoint); task-c also edits x.py (overlap)
for br, f, val in [("task-a", "x.py", "X = 2"), ("task-b", "y.py", "Y = 2"),
                   ("task-c", "x.py", "X = 3")]:
    wt = tmp / br
    run(["git", "worktree", "add", "-q", "-b", br, str(wt), "main"], repo)
    (wt / f).write_text(val + "\n")
    run(["git", "add", "-A"], wt); run(["git", "commit", "-q", "-m", br], wt)

os.chdir(repo)  # wave_is_disjoint runs git in cwd
disjoint = lc.wave_is_disjoint(["task-a", "task-b"])
overlap = lc.wave_is_disjoint(["task-a", "task-c"])
d_safe_disjoint = lc.dispatch_decision(["cannot-collide", "cannot-collide"], merge_tree_clean=disjoint)
d_safe_overlap = lc.dispatch_decision(["cannot-collide", "cannot-collide"], merge_tree_clean=overlap)
# real sequential merge of the disjoint pair (the merge of record)
m1 = run(["git", "merge", "--no-ff", "-m", "mA", "task-a"], repo)
m2 = run(["git", "merge", "--no-ff", "-m", "mB", "task-b"], repo)
merge_clean = m1.returncode == 0 and m2.returncode == 0

print("=== AC9 worktree/merge dry-run ===")
print(f"git worktree add x3                : ok")
print(f"wave_is_disjoint(task-a, task-b)   : {disjoint}  (expect True — disjoint files)")
print(f"wave_is_disjoint(task-a, task-c)   : {overlap}  (expect False — both edit x.py)")
print(f"dispatch_decision(safe, disjoint)  : {d_safe_disjoint}  (expect parallel)")
print(f"dispatch_decision(safe, overlap)   : {d_safe_overlap}  (expect serial — fail closed)")
print(f"real merge of disjoint pair        : {'CLEAN' if merge_clean else 'CONFLICT'}")
ok = (disjoint and not overlap and d_safe_disjoint == "parallel"
      and d_safe_overlap == "serial" and merge_clean)
print(f"\nVERDICT: {'PASS — worktree/merge surface + gate behave as specified' if ok else 'FAIL'}")
sys.exit(0 if ok else 1)
