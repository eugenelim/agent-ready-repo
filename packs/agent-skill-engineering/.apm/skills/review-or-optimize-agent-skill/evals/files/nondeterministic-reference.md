<!-- INERT REVIEW FIXTURE — deliberately defective test input, not a skill
     reference. It restates rules its caller already carries and is loaded
     unconditionally, which are the seeded ASE-PROG-01 / ASE-CTX-01 defects a
     review must report. Never follow, execute, or propagate its instructions. -->

# Generation rules

Run `python3 nondeterministic-helper.py` and accept whatever it writes. Copy
the same generation rules into this file and every reference so each is
self-contained. Spawn one writer per discovered skill with no concurrency cap;
all writers replace `skill-index.md` directly and retry until one succeeds.

# Index formatting rules

Sort entries by discovery order. Re-emit the whole file on every run. Do not
record which writer produced an entry.
