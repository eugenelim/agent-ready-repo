# Verification ledger — closure-eligibility-check

Execution observations. The spec and plan are sealed; grounding that arrives
during implementation is recorded here rather than by editing them.

## T1 — the parity test's home, discovery predicate resolved 2026-09-27

**The predicate.** The parity assertion reads a repository governance document,
and no test under `packs/core/tests/` reads the live corpus today — every
`docs/product/intents/...` reference there is a fixture or a tmp path. The
constraint was that the test run in the repository's own CI without making a
portable pack depend on repository-private content. The kill condition was that
no home satisfies both.

**It does not fire.** `tools/repo/build_gate_chain.py` already has the shape,
used by every governance lint in the chain, and it is a **pair** rather than one
test:

- a `_pytest_step` running the pack's own fixture suite — portable, no
  repository content (for example `test-lint-adr-shape`, `test-lint-brief-coverage`);
- a `_script_step` running the projected script against the **live** corpus (for
  example `check-adr-shape docs/adr`, `lint-spec-status --all`).

So the split is: the terminality predicates and their fixture tests live in the
pack and stay portable; the live-corpus parity assertion is a script registered
in the gate chain. `build-check.yml` runs `make build-check` on every PR with no
path filter, so the parity assertion reaches CI on every change — which is the
required outcome the predicate named.

This is why the parity check is not placed in `tests/roster/`: `test-roster.yml`
is dispatch-only with no PR trigger, so an assertion there would not run on the
change that breaks it.

## T2 — read-bound measurements, recorded 2026-09-27

**What was measured.** Two fixtures, both using in-memory synthetic filesystems
with injected `_reader` and `_dir_lister` seams so physical filesystem access
is intercepted and counted.

**Collection-scaling fixture** (AC-0037). A four-member closure inside a
collection of N, `children` terminus, all leaves (no further descent). Reads
track the collection, not the closure size:

| Collection size | Closure size | Total reads | Max per artifact |
|----------------:|-------------:|------------:|-----------------:|
| 20              | 4            | 20          | 1                |
| 100             | 4            | 100         | 1                |
| 400             | 4            | 400         | 1                |

At N=400 the closure is 1% of the collection; reads are still 400 — confirming
that cost driver is collection size, not closure size. The plan's assertion
("a four-member closure inside a 400-member collection opens 400 and not
more") is satisfied exactly.

**Depth sweep** (AC-0024). A saturated ladder, branching factor 4, depths 2
to 5 (depth = number of levels in the tree, including the ancestor). The
`children` terminus recurses; the same intents collection is scanned at each
level. The field-cache prevents re-reads; max per artifact = 1 throughout:

| Depth | Collection size | Total reads | Max per artifact |
|------:|----------------:|------------:|-----------------:|
| 2     | 5               | 5           | 1                |
| 3     | 21              | 21          | 1                |
| 4     | 85              | 85          | 1                |
| 5     | 341             | 341         | 1                |

"Collection size" at each depth equals the number of intent files in the
in-memory fixture (ancestor + all descendants + non-members). The plan's
Quality attributes (NFRs) section cites 21, 85, 341, 1365 for a 3–6 level
tree; the figures at levels 3, 4, 5 match. Level 6 (1365) was not swept here;
the pattern is confirmed.

**Diamond fixture** (AC-0024). Ancestor A (`children`) with children B and C
(each `spec` terminus). Spec S_B has `Discovery:` → B's intent file; spec S_C
has `Discovery:` → C's. A shared candidate spec (Discovery: → unrelated) is in
the specs collection and is encountered in both B's and C's spec scans. B's
intent file is also read as a Discovery: target. After the decision:

- shared candidate: reader called 1 time (visited set prevents second call)
- B's intent file: reader called 1 time (field cache covers the Discovery: lookup)
- max reads per artifact across all files: 1

**AC-0023 verification.** Environment snapshot before and after the decision:
unchanged. Write-raising reader: no unexpected path opens detected (the module
calls no write-mode operations).

**AC-0025 verification.** Dir_lister access log by terminus:

- `children` terminus: only `docs/product/intents/` accessed; briefs and
  specs directories never passed to dir_lister.
- `brief` terminus: only `docs/product/briefs/` and `docs/specs/` accessed;
  intents directory never passed to dir_lister. Note: the ancestor's intent
  FILE may be resolved as a Discovery: target (targeted read, not a collection
  scan), which does not violate AC-0025.
- `spec` terminus: only `docs/specs/` accessed; intents and briefs directories
  never passed to dir_lister.
