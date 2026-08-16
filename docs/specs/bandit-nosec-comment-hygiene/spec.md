---
title: Silence Bandit's nosec-parsing warnings without weakening any suppression
slug: bandit-nosec-comment-hygiene
---

# Spec: Bandit stops parsing suppression reasons as test ids, and its stderr becomes a gate

- **Status:** Shipped
- **Owner:** eugenelim
- **Plan:** none — see § Named deviation
- **Mode:** full (governance surface — this edits `bandit.yaml`, which
  `Makefile`'s `SAST_CONFIG` names as the config governing the SAST gate; the
  `sast` recipe itself; and a shipped pack script installed into adopter repos.
  Behaviour-equivalence does not clear the trigger; the trigger reads *touches*,
  not *changes the behaviour of*. Same reading as the sibling
  `pack-script-root-boundary-validation` spec.)
- **Constrained by:** [ADR-0017](../../adr/0017-adopt-bandit-pip-audit-semgrep-sast-gate.md)
  § suppression policy, whose `# nosec <ID> — <reason>` spelling this spec
  reverses — recorded as
  [ADR-0084](../../adr/0084-nosec-reason-delimiter-and-stderr-as-a-gate.md)
- **Contract:** none (comment form + a gate wrapper; no published interface)
- **Shape:** service

## Named deviation from full mode

Three full-mode elements were not run. Naming all three, because a partial
disclosure is worse than none:

1. **The `loop-engine` / `loop-cohort` state machine.** Its primary job is to
   sequence the two human approval gates, and the requester granted both up
   front as a standing instruction to carry this change autonomously through to
   merge. Its state files are gitignored, so it would also have left no record.
2. **`loop-cohort`'s iteration-cap accounting** (`record-attempt`, `check
   --phase gates-failed|review`) rides on that same machine, so it is skipped
   too. This is a real loss, not a nil one: the loop ran three review rounds
   and one gate failure with no mechanical retry ceiling. It stayed bounded by
   judgment, which is weaker than a counter.
3. **A `plan.md` with per-task `Tests:`, verification mode, and `Depends on:`.**
   The task list below is inline and unannotated. Defensible only because every
   task is goal-based against a command that already exists — there is no task
   whose verification had to be invented — but it is a deviation, not a trim.

What full mode required and *was* run: `adversarial-reviewer` to Clean,
`security-reviewer` (warranted — the suppressions sit on `subprocess` and
JWT-bearing `urllib` sinks), and the `quality-engineer` floor.

## Objective

`make sast`'s Bandit leg emits 54 `WARNING` lines on a clean run. None is a
finding — the gate still exits 0 — but the noise buries any warning that
*would* matter, and one class of it is a live foot-gun. Remove every warning
by fixing the comments Bandit is complaining about, changing no suppression
and no runtime behaviour — then make the resulting silence load-bearing by
failing the gate on any future Bandit stderr, so the next malformed
suppression is a red build rather than two more lines of scrollback.

Two classes, both diagnosed against Bandit 1.9.4:

1. **`Test in comment: <word> is not a test name or id, ignoring`** (50 lines).
   `bandit/core/manager.py` parses a nosec comment with
   `NOSEC_COMMENT = re.compile(r"#\s*nosec:?\s*(?P<tests>[^#]+)?#?")` — the
   test-id list runs to the *next `#`*, so the whole prose reason in the
   repo's documented `# nosec <ID> — <reason>` form is tokenised and looked up
   as test names. Today every lookup misses and only warns. It is a foot-gun
   because a reason word that happens to collide with a Bandit test *name*
   (`assert_used`, `weak_cryptographic_key`, …) would silently widen the
   suppression beyond the ID the author wrote — and because a comment that
   *opens* with `nosec` and resolves to no id at all is treated as a blanket
   suppression of every test on the statement. Fix: `# nosec <ID>  # <reason>`
   — the second `#` terminates the id list, so the reason is never parsed.

2. **`nosec encountered (B104), but no failed test`** (4 lines, all
   `tier3.py:43`). `utils.get_nosec` matches a nosec against the whole
   *statement* linerange, so the one-line `frozenset({"", "*", ".", "0.0.0.0",
   "::"})` runs B104 over five string nodes; four produce no finding and each
   warns that the nosec went unused. Splitting the literal across lines does
   not help (the linerange still spans the nosec). Fix: hoist `"0.0.0.0"` to
   its own single-statement constant carrying the nosec.

## Boundaries

**Never do:** change `bandit.yaml`'s `skips` / `exclude_dirs`; change which test
ids any line suppresses; filter or `grep -v` the diagnostics out of the `make
sast` recipe (the whole point is to promote them, not hide them); edit **the
body of** ADR-0017 or of the shipped `sast-sca-tooling` spec and plan (frozen —
`docs/CONVENTIONS.md` § Document lifecycle); change any runtime behaviour beyond
the `tier3.py` constant hoist, which is value-identical.

**Always do:** prove suppression equivalence before claiming the rewrite was
safe — the reported-finding diff *and* the resolved-id inventory, because
neither alone can see a suppression widened onto a test that fires nowhere. Give
any new gate a self-test that fails when the gate is removed; that is why
`tools/test-sast-stderr-gate.py` exists rather than a bare recipe line.

**Ask first:** before adding a `# nosec` this change did not already have, or
before widening `exclude_dirs` to quiet a diagnostic. Both move the gate's
coverage rather than its noise floor, and neither is in scope here.

ADR-0017's **Status line** is a third case, and *is* amended: that field stays
mutable on a frozen ADR, and four ADRs (0001, 0013, 0015, 0016) already carry
the same partial-amendment pointer. Without it a reader who starts at the ADR —
the documented source of truth for *why* — never learns the spelling changed.

## Testing Strategy

Goal-based check — the gate is the test:

- `bandit -r tools packs packages tests -c bandit.yaml --severity-level medium
  --confidence-level medium -q` emits zero output and exits 0.
- **Suppression-equivalence check.** The load-bearing one. Base is the pinned
  SHA `1f6b2d2f`, not the moving `origin/main`, so this stays re-runnable after
  merge:

  ```sh
  for ref in 1f6b2d2f HEAD; do
    git worktree add -q --detach "/tmp/wt-$ref" "$ref"
    ( cd "/tmp/wt-$ref" && bandit -r tools packs packages tests -c bandit.yaml \
        --severity-level low --confidence-level low -f json \
        -q -o "/tmp/$ref.json" 2>"/tmp/$ref.warn" )   # exits 1 — findings expected
  done
  python3 - <<'PY'
  import json
  key = lambda p, tag: {(r['filename'].split('wt-%s/' % tag)[-1], r['test_id'],
                         r['issue_text']) for r in json.load(open(p))['results']}
  b, h = key('/tmp/1f6b2d2f.json', '1f6b2d2f'), key('/tmp/HEAD.json', 'HEAD')
  print(len(b), len(h), b ^ h)     # -> 239 239 set()
  PY
  wc -l /tmp/1f6b2d2f.warn /tmp/HEAD.warn   # -> 54 and 0
  ```

  A weakened suppression appears only on the HEAD side, an over-broad one only
  on the base side; the symmetric difference must be empty. Four traps, each of
  which gave a wrong answer when first skipped:
  - **Rows are not keys.** Each side has 362 raw result rows collapsing to 239
    distinct `(filename, test_id, issue_text)` keys. Quote which one you mean.
  - **Both sides must be clean worktrees**, not "a worktree vs. the working
    tree". A development tree carries gitignored build output
    (`packages/agentbundle/build/lib/…`) the worktree does not; scanning one of
    each inflated both totals and produced a 27-key phantom delta.
  - **Relative roots** (`tools packs packages tests`) from each worktree root.
    Absolute paths stop `exclude_dirs: '*/tests/*'` matching, so the two scans
    diff different file sets.
  - **Both scans exit 1** at this floor (findings are expected), so `set -e`
    will abort the loop above if you add it.

  Line numbers are excluded from the key because the `tier3.py` edit shifts
  them.
- **Mutation check on the one runtime change.** Deleting `_REJECT_ANY_IPV4`
  from `_REJECT_LITERALS` must fail
  `test_rejects_wildcard_and_catchall_endpoints`. It did not before this
  change: `"0.0.0.0"` and `"::"` are also caught by the downstream
  `ip.is_unspecified` branch, so a bare `pytest.raises(DeclarationError)`
  stayed green with the constant deleted. The `match="wildcard"` added here
  pins the literal-set branch specifically; verified by re-running the mutation.
- **Gate self-test on the new stderr rule.** `python3
  tools/test-sast-stderr-gate.py` — five cases against a stub `bandit`: clean
  scan passes; one stderr line fails the gate *even though bandit exited 0*;
  findings still fail with bandit's own status; whitespace-only stderr does not
  fail; no scan roots is a usage error. Separately, end-to-end: reintroducing
  the dash form on one real suppression makes `python3
  tools/run-bandit-gate.py tools packs packages tests` exit 1, and the
  unmodified tree exits 0. Both were run.
- **Resolved-id inventory.** Complementary to the equivalence check above and
  necessary because that check only sees *reported* findings: running every
  suppression comment at both revisions through Bandit's own
  `_parse_nosec_comment` must give the same result — one resolved id per
  directive, no blanket suppressions, at either revision. It does, which is
  what rules out a suppression widened onto a test that fires nowhere today.
- `python3 tools/lint-ruff.py`, `make lint-mypy`, and `SKIP_SAST=1 make
  build-check` pass.
- `python3 -m pytest packages/agentbundle/tests/unit/test_system_trust.py
  packs/converters/tests/skills/file-to-markdown/ -q` passes (the two edited
  runtime files are covered there).

## Acceptance Criteria

- [x] Every `# nosec` comment that carries a prose reason uses the
      `# nosec <ID>  # <reason>` form; no reason text reaches Bandit's test-id
      parser. That includes `tools/audit-npm.py` ×2, which landed on `main`
      while this branch was in review — not a drive-by: the stderr gate below
      fails on them, so converting them is what makes the gate green on the
      tree it lands in
- [x] The explanatory block above `_app_api`'s opener in
      `tools/capture-publish-control-evidence.py` no longer begins with
      `# nosec` (it is prose, not a directive; the real directive is on the
      `opener.open` line)
- [x] `"0.0.0.0"` in `tier3.py` is a single-statement constant carrying
      `# nosec B104`, and `_REJECT_LITERALS` references it. It is named
      `_REJECT_ANY_IPV4`, not `_ANY_IPV4`: the constant is pre-suppressed for
      B104, so a name that reads as a reusable bind address would let a future
      `bind` use in this module escape the check entirely
- [x] `bandit … --severity-level medium --confidence-level medium -q` produces
      no output and exits 0
- [x] The suppression-equivalence check above reports identical finding sets on
      both sides — 362 raw result rows collapsing to 239 distinct
      `(filename, test_id, issue_text)` keys each way, empty symmetric
      difference — while the warning count goes 54 → 0
- [x] `make sast`'s Bandit leg fails on non-empty stderr, so the silence this
      change buys is enforced rather than merely achieved (ADR-0084). Verified
      both ways: clean tree exits 0, one reintroduced dash-form suppression
      exits 1
- [x] That gate has a self-test that fails if the gate is removed —
      `tools/test-sast-stderr-gate.py`, driven against a stub `bandit`, running
      ahead of the scan in the `sast` recipe alongside the two self-tests
      already there
- [x] `_REJECT_ANY_IPV4` is pinned by an assertion that fails when it is
      removed from `_REJECT_LITERALS` (`match="wildcard"` in
      `test_rejects_wildcard_and_catchall_endpoints`)
- [x] ADR-0084 records the form change and the stderr rule; ADR-0017's Status
      line points at it, so a reader starting from the frozen ADR finds the
      live rule
- [x] `bandit.yaml` documents the required `# nosec <ID>  # <reason>` form and
      why, so the fix does not regress on the next suppression added — including
      that the ID is mandatory, because a `# nosec` whose id list resolves to
      nothing suppresses every test on the statement and, under the two-`#`
      form, does so silently. The id-less case is the one shape Bandit never
      warns about, so it stays unenforced — see § Deferred
- [x] No suppression rationale overstates its guarantee: `diagnose-tls-trust.py`
      says `list argv` rather than `fixed argv`, since `argv[0]` at both call
      sites comes from `shutil.which`
- [x] `python3 tools/lint-ruff.py`, `make lint-mypy`, `SKIP_SAST=1 make
      build-check`, and the touched packages' tests pass

## Tasks

1. Rewrite the seven prose-carrying nosec comments to the `# nosec <ID>  #
   <reason>` form (`tools/diagnose-tls-trust.py` ×2, `tools/audit-npm.py` ×2,
   `packages/agentbundle/agentbundle/system_trust.py` ×2, and the block comment
   in `tools/capture-publish-control-evidence.py`)
2. Hoist `"0.0.0.0"` in `packs/converters/.apm/skills/file-to-markdown/scripts/tier3.py`
   to its own constant carrying the B104 nosec
3. Document the comment form in `bandit.yaml`
4. Run the gates (bandit at both floors, ruff, mypy, build-check, tests)
5. Review (`adversarial-reviewer`, `security-reviewer`, `quality-engineer`),
   apply findings, re-run the gates, then PR and merge
6. From review: record the reversal as ADR-0084 and point ADR-0017's Status
   line at it; pin the `tier3.py` hoist with `match="wildcard"`
7. From review: promote Bandit's stderr to a gate failure — `tools/run-bandit-gate.py`
   replaces the bare recipe line, and `tools/test-sast-stderr-gate.py` proves it
   against a stub `bandit` so the rule cannot be simplified away unnoticed

## Deferred

- `bandit-nosec-form-lint` — a `tools/` check that enforces the form (ID
  mandatory; reason only after a second `#`), wired into `make build-check`.
  Recorded in `workspace.toml [backlog].open`.
- `capture-evidence-repo-dot-segments` — `_validate_repo` accepts `..` path
  segments, so a `--repo` value can reach an endpoint other than the one named.
  Pre-existing, no privilege gain, and the JWT still cannot leave
  `api.github.com`; a behaviour change with its own test belongs in its own PR.
  Recorded in `workspace.toml [backlog].open`.

## Bundled fixes

- `bandit.yaml`'s invocation comment duplicated the Makefile's scanned-roots
  list and had already drifted (missing `tests`). It now points at `SAST_DIRS`
  — one line, in a file this change already edits, three lines above the block
  it adds.
- `docs/adr/README.md` was missing its row for ADR-0083 (the npm SCA gate),
  which landed without one; added while adding ADR-0084's row directly below
  it. Same shape as the earlier `docs(adr): add the missing ADR-0074 row`.
- `tools/diagnose-tls-trust.py`'s B603/B404 reasons claimed "fixed argv", but
  `argv[0]` at both call sites comes from `shutil.which`; corrected to "list
  argv" while rewriting those same two comments. (`system_trust.py`'s "argv is
  constant" is accurate and stands — every element there is a module constant.)

## Assumptions

- Bandit's `NOSEC_COMMENT` / `get_nosec` behaviour is stable across the 1.9.x
  line the repo pins in `tools/requirements-sast.txt`; both were read from the
  installed 1.9.4 source and confirmed empirically in a scratch file before
  planning.
- Warnings go to stderr and never affect the gate's exit code, so this change
  cannot make CI redder — only quieter.

## Declined

- **A repo policy gate rejecting prose-after-`# nosec`.** A new `tools/` check
  plus a CI wiring for a five-site problem; the `bandit.yaml` comment carries
  the same information at the point of use. Deferred, not dismissed.
- **Amending the *bodies* of the three frozen documents that still teach the
  old form** — `docs/adr/0017-…:107`, `docs/specs/sast-sca-tooling/spec.md:44`
  and its `plan.md:146,151,154,159,161,164,166`. Bodies are immutable. What is
  done instead: ADR-0084 records the reversal, ADR-0017's *Status* line points
  at it (a field that stays mutable), and `bandit.yaml` carries the operative
  instruction. The shipped `sast-sca-tooling` spec and plan cannot be annotated
  at all — an accepted cost, flagged in the PR description per `AGENTS.md` §
  When this file is wrong.
- **A `tools/` script for the equivalence check** (a
  `compare-bandit-suppressions` shape). The
  check is needed whenever a suppression is touched, which argues for a script,
  but its shape is still settling — this run changed the procedure twice. The
  literal commands are pasted into Testing Strategy against a pinned SHA so the
  next person can run it; promoting it to a tool rides with
  `bandit-nosec-form-lint`.
- **Fixing `packs/converters/tests/skills/file-to-markdown/test_tier3.py:40`.**
  Same shape, but the test tree is excluded by `bandit.yaml`, so it emits no
  warning — out of scope for "fix the warnings".
- **Pinning or bumping Bandit, or filtering the recipe's output.** Both hide
  the signal rather than fix the comments producing it.

## Known skip

`make ci` is red on `origin/main` as of `1f6b2d2f`, independently of this
change: `tools/test_catalogue_navigation.py::test_markdown_entry_points_keep_canonical_outcome_labels`
asserts every canonical outcome title from the docs-site navigation appears
verbatim in each markdown entry point, and `guides/README.md` no longer carries
"Build and review software". Reproduced on a clean `origin/main` worktree;
`guides/README.md` is not in this diff. Treated as a known skip and recorded as
`pre-existing-guides-readme-outcome-label-drift` in `workspace.toml
[backlog].open`. Every other leg of `make ci` is green on this branch.
