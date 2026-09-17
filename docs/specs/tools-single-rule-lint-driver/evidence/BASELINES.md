# Two baselines, and why

`corpus-pristine.json` — captured 2026-09-16 before ANY file was added or
changed. The true pre-change state of the twelve rules.

`corpus-before.json` — re-captured after `tools/lint_harness.py`,
`tools/selftest_harness.py` and `tools/test_lint_harness.py` were added, but
before any rule was migrated. THIS is the comparison value for the migration.

Why two. `lint-nosemgrep-form`'s success line reports a repo-wide file count
("every suppression in 2983 UTF-8 text file(s)"). Adding three files to
`tools/` moved it to 2986. That is a true observable change, but it is caused
by adding files to the repository, not by moving the rule onto the driver.
Comparing the migration against the pristine capture would attribute it to the
refactor and hide whatever the refactor actually did.

So the migration is measured against `corpus-before.json`, and the count drift
is accounted for separately: it is the only difference between the two files,
and `diff-pristine.txt` records it.

## Final result, and the one case that is not byte-identical

With the three new files untracked, the oracle reports IDENTICAL for all 48
cases. With them tracked, exactly one field differs:

    lint-nosec-form [clean] stdout:  "... in 1216 tracked file(s) ..."
                                  -> "... in 1219 tracked file(s) ..."

That is +3, the three files this change adds. Both SAST-form lints report a
repo-wide count of the files they scanned, so *any* commit that adds a tracked
file moves that number. It is a true observable change and it is not caused by
the refactor; the differential above isolates it — untrack the three files and
the difference disappears entirely.

Nothing else in the 48 cases moved.
