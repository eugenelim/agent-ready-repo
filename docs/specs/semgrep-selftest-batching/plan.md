# Plan: semgrep-selftest-batching

- **Spec:** [`spec.md`](spec.md)
- **Status:** Done <!-- Drafting | Approved | Executing | Done -->

> **Plan contract:** this is the implementation strategy. Unlike the spec, this
> document is allowed to change as you learn — while its Status is `Drafting`
> or `Executing`. When it changes substantially (a different approach, not just
> a re-ordering), note why in the changelog at the bottom. Once it is `Done`
> and the spec is `Shipped`, the directory freezes as a unit
> (`docs/CONVENTIONS.md` § Document lifecycle).

## Approach

One file changes: `tools/test-semgrep-argv-boundary.py`. `scan(target)` — which spawns
one semgrep per target — is replaced by `scan_all(targets)`, which spawns one semgrep
over all of them and returns findings keyed by repo-relative path, containing only the
targets semgrep reports as scanned. The three test functions keep their names, their
assertions, and their output strings; they read from the mapping instead of calling
semgrep.

The one deliberate behaviour addition is that **all five targets** must now appear in
semgrep's scanned set before their findings are asserted on. The per-invocation version
checked this only for the three production scripts. Batching makes the check necessary
for the fixtures too: findings arrive keyed by path, so a key that never matches yields
an empty finding list, and a "zero findings" assertion would pass without the rule
having examined anything. Making absence-from-scanned a failure converts that whole
class of bug from a silent green into a loud red.

Path-key construction is the one place this can go wrong, and it did during
implementation: semgrep echoes paths back in whichever form it was handed, so passing
absolute targets yielded absolute `paths.scanned` entries that matched no
repo-relative key, and every assertion failed at once. Rather than depend on how the
argv is built, `_key()` normalises **both** sides to a repo-relative POSIX path. A
mismatch therefore leaves the target absent from the mapping, which `hits_for` reports
as a named failure — so this class of bug is loud, not silent.

Verification is mutation, not inspection — see § Verification below. A green run proves
nothing about a test's ability to fail.

## Tasks

### T1: The self-test proves the same things in one semgrep process

**Depends on:** none

**Touches:** tools/test-semgrep-argv-boundary.py

**Verification mode:** goal-based check, plus the mandatory mutation pass.

**Tests:** no stub (goal-based). The artifact under change is itself the test; its
construction check is the mutation pass below.

**Approach:**
- Replace `scan(target)` with `scan_all(targets)`: one `subprocess.run` invoking
  `semgrep --config <RULE> --json --quiet --metrics off <t1> … <t5>` with
  `cwd=REPO_ROOT`, unchanged in every other respect.
- Build `{repo_relative_path: [findings]}` from `results[]` grouped by `path`,
  restricted to the paths in `paths.scanned`. Keep the existing
  `RuntimeError` when semgrep produces no stdout.
- Add one helper that resolves a target to its findings and fails the named case if the
  target is absent from the scanned set; route all three test functions through it.
- Call `scan_all` once in `main()` and pass the mapping to the three test functions.
- Guard both fixtures with an explicit presence check and a "path drifted?" message, so
  a renamed fixture is diagnosed rather than dropped from the argv (AC5).
- Refuse an empty target list in `scan_all`, because semgrep with no targets walks the
  working directory and this rule's `paths.include` rediscovers the same files (AC6).
- Enumerate the fixtures directory and fail on any fixture not in the target list: the
  rule's `paths.include` covers that directory by glob, but semgrep scans only the files
  it is named, so an added fixture would otherwise sit unexercised.
- Pass `--` before the targets and an explicit `subprocess` `timeout=`, so a name
  beginning with `-` is scanned rather than parsed as a flag, and a wedged semgrep fails
  the gate instead of hanging it.
- Leave the skip-when-absent branch, the missing-rule branch, the `ok`/`fail` helpers,
  the counters, and the summary block exactly as they are.

**Done when:** every row of § Verification below is recorded, and `make sast`,
`python3 tools/lint-ruff.py` and `python3 -m pytest tools/test_build_gate_chain.py -q`
are green.

## Verification

Mutations are run by patching the loaded module in a harness rather than editing files,
so no mutation can be left behind in the worktree. Rows M1–M5 and M7 must each produce a
non-zero exit; C1 and M6 have their own expectations, stated inline.

| # | Mutation | Expected | Result |
|---|---|---|---|
| M1 | A ratcheted target gains a finding (the known-vulnerable `positive.py` added to `FIXED_SCRIPTS`) | zero-findings assertion fails | detected, exit 1 |
| M2 | Rule neutered with an impossible pattern | positive-fixture assertion fails | detected, exit 1 |
| M3 | `_key` corrupted to a constant | must not pass vacuously | detected, exit 1 |
| M4 | One entry dropped from the rule's `paths.include` | **named** failure, not a traceback | detected, exit 1, named |
| M5 | Every target missing | refuses; semgrep must not walk the repo | detected, exit 1, named |
| M6 | Target argv silently stripped | **no detection expected** — see below | not detected, by design |
| M7 | An unwired fixture added to the fixtures directory | named failure | detected, exit 1, named |
| C1 | `semgrep` absent from `PATH` | **skip message, exit 0** | as specified |
| C2 | Rule file missing | exit 1 | as specified |

Also verified: exactly **one** semgrep invocation over five targets, counted by
patching `subprocess.run`; and the asymmetric-key bug (normalising targets but not
reported paths) was hit for real during implementation and failed loudly rather than
passing.

**M6 is a known non-detection, not a defect.** Stripping the target arguments makes
semgrep walk the working directory, where the rule's `paths.include` rediscovers exactly
the same five files and returns an identical verdict — so the argv is redundant with the
rule's scope and no assertion can prove otherwise. Two attempts to close it failed: an
exact set-equality check (`unrequested()`) could not fire in either direction, because
semgrep neither widens an explicit file argv nor, with the argv stripped, returns
anything but the rule's own five files. It was replaced by `unwired_fixtures()` (M7),
which guards the risk the old docstring merely claimed to. Recorded because a check that
cannot fail, presented as a guarantee, is worse than no check — and this one shipped
briefly.

**M1 is a proxy for the AC's wording.** The acceptance criterion asks for "a ratcheted
target that gains a finding"; rather than edit a projected pack script — which would
risk `make build-self` drift — the known-vulnerable fixture was added to the ratchet
list, exercising the same assertion path a real regression would hit.

## Open, and deliberately not silent

Round-2 `security-reviewer` findings that are **not** addressed by this change. Surfaced
to the maintainer, who chose to ship the batching and track these separately
(2026-08-17). None is a regression this change introduced; each is a pre-existing
property of the control it sped up. All four are recorded in
`workspace.toml [backlog].open` with the slugs below.

1. `sast-ratchet-scope-duplicated-fails-open` — **the ratchet's scope is duplicated,
   and shrinking it exits 0.** `FIXED_SCRIPTS` in
   this script re-declares the production-script half of `paths.include` in
   `tools/semgrep/argv-path-boundary.yml`, and nothing reconciles the two. Verified by
   mutation: `FIXED_SCRIPTS = []` prints `2/2 passed` and exits **0** — the ratchet's
   entire production half proves nothing and the gate is green. Pre-existing; the
   per-target version had the same structure. The fix is to derive the target list from
   the rule's `paths.include` (`pyyaml` is already a `tools/` dependency) so the rule
   file is the single scope definition.
2. `sast-semgrep-unparseable-target-reads-clean` — **`--strict` plus an `errors` check
   would close the partial-parse hole.** Verified
   free to adopt: the real five-target invocation exits 0 with empty `errors` under
   `--strict` today. ADR-0084 is the repo's precedent for promoting a scanner diagnostic
   that does not move its own exit code into a gate signal, and it names this file as a
   model — so this is an ADR-shaped decision, not a detail.
3. `sast-nosemgrep-has-no-form-lint` — **a single `# nosemgrep` silently neuters the
   ratchet** on any of the five targets,
   with no repo-wide form-lint equivalent to ADR-0084's `tools/lint-nosec-form.py` for
   bandit's pragma.
4. `sast-selftest-findings-not-keyed-by-check-id` — **findings are keyed by path, not
   by `check_id`**, so if the rule file ever grows a
   second rule, a finding from any rule in it satisfies the positive-fixture proof.

Items 1, 3 and 4 are control-integrity gaps a scanner cannot see; item 2 is a decision.
All four are larger than the batching change and belong to a scoped follow-up.

## Risks

- **A faster self-test that can no longer fail is worse than the slow one.** This is the
  whole risk of the change, and the reason the mutation battery gates it rather than a
  passing run. M3 targets the failure mode the refactor itself introduces; M6 is the
  reminder that a check can look like a guarantee and be incapable of firing.
- **`tools/` is in `SAST_DIRS`**, so this diff makes the run SAST-relevant and
  `gate-sast` executes — the intended safety property, and also why CI feedback is slow.
- Semgrep's `paths.scanned` semantics are load-bearing for the covered-the-file
  assertion, and they carry a known limit: membership proves `paths.include` matched,
  **not** that the file parsed. Verified by probe in both directions; a semgrep
  major-version bump is a re-probe point (`tools/requirements-sast.txt` pins
  `semgrep>=1.166,<2`).

## Changelog

- 2026-08-17: initial plan.
- 2026-08-17: revised after the adversarial pass. Four substantive changes. (1) The
  "the rule reached the file" claim was narrowed to a `paths.include` guarantee —
  probing showed semgrep reports an unparseable target as scanned with no signal of any
  kind (empty `errors`, empty `skipped`, empty stderr, exit 0), so the reviewer's
  proposed `payload["errors"]` fix is not implementable on 1.166.0; the hole is
  pre-existing and is now tracked as `sast-semgrep-unparseable-target-reads-clean`.
  (2) The two fixtures gained explicit presence guards, and `scan_all` now refuses an
  empty target list rather than letting semgrep walk the repo and rediscover the same
  files. (3) `findings.setdefault` was replaced with an explicit raise, because
  `setdefault` created the key its own comment said it would surface. (4) The
  wall-clock acceptance bar was dropped in favour of the invocation count after machine
  load reached 60 on 10 cores and made absolute timings undependable; the reported
  figure is now a load-robust interleaved A/B ratio.
