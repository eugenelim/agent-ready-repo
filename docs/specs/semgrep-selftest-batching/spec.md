# Spec: semgrep-selftest-batching

- **Status:** Shipped (2026-08-17) <!-- Draft | Approved | Implementing | Shipped | Archived -->
- **Owner:** eugenelim
- **Plan:** [`plan.md`](plan.md)
- **Constrained by:** ADR-0017 (custom Semgrep `mode: taint` rules live in
  `tools/semgrep/` and run in `make sast`; this file is what proves the rule fires).
  Note the `argv-path-boundary` rule is deliberately **not** a taint rule — its own
  header records that the taint shape was built, measured at 0 findings on the real
  target, and rejected in favour of guarding the conversion site.
- **Brief:** none
- **Discovery:** none
- **Contract:** none — internal gate self-test. Invocation
  (`python3 tools/test-semgrep-argv-boundary.py`) and exit codes (`0` pass or
  semgrep absent, `1` any failure) are unchanged.
- **Shape:** service

> **Spec contract:** this document defines what "done" means. The implementing
> PR must match this spec, or update it. Verification must be derivable from it.

<!-- Mode: light. The change is a behaviour-preserving refactor of one test's
process usage, in familiar territory, single task, reversible, no new
dependency, and no structural or public-interface change. It alters nothing
about what the SAST gate scans, suppresses, or blocks on — the same rule is
applied to the same five targets with the same assertions.

On the security-boundary trigger, which adversarial review argued should fire:
this file IS the SAST gate's only proof-of-life for the custom
argv-path-boundary rule, so weakening it would be a security-relevant
regression even though the gate's scope is untouched. Light mode was retained
rather than escalating to full, on the basis that the substance full mode would
add here is adversarial depth on exactly one question — can this control still
fail?

That reasoning did not survive contact. The mutation battery and a
`security-reviewer` pass both ran (recorded in plan.md § Verification), and the
second round of each found new Blockers — including a fail-open the batching did
not introduce but does sit on top of (`FIXED_SCRIPTS = []` exits 0), and a
factual error in this spec's own account of semgrep's parse-error signalling.
Two review rounds each finding the documentation claiming more than the evidence
supports is precisely the escalation signal light mode's rules describe. The
disposition was surfaced to the maintainer rather than decided here; see
plan.md § Open, and deliberately not silent. -->

## Objective

`tools/test-semgrep-argv-boundary.py` proves the `argv-path-boundary` boundary rule fires
on its positive fixture and stays silent on its negative fixture and on the three
production scripts it ratchets — using **one** `semgrep` process instead of five. Almost
all of a per-target invocation's cost is semgrep's process startup rather than scanning,
so batching makes this step several times cheaper while proving exactly the same things.
The measured figures, and the machine conditions they were taken under, live once in
§ Assumptions.

The merge is safe because semgrep applies `paths.include`, `--max-target-bytes`,
`nosemgrep`, and its per-path timeout **per file**, so no per-file verdict can change,
and it names the file in every finding, so per-target attribution survives natively.

Every assertion confirms the rule's scope actually **covered** its target before
trusting the target's silence — and that confirmation now covers the two fixtures too,
which the per-invocation version did not check. It is a `paths.include` guarantee and
nothing more: `paths.scanned` membership does **not** prove the file parsed. A partial
parse failure is signalled (`PartialParsing` in `errors`, escalated to exit 3 by
`--strict`); a whole-file one is not signalled at all. Neither is gated here today.
The residue predates this change and is unaltered by it; it is recorded as
`sast-semgrep-unparseable-target-reads-clean`.

## Acceptance Criteria

- [x] The self-test spawns exactly **one** `semgrep` process, over all five targets,
      confirmed by counting invocations rather than by wall-clock. (Timing is
      environment-dependent and deliberately not a criterion — see Assumptions.)
- [x] The same five targets are scanned: the positive and negative fixtures plus
      `lint-traceability.py`, `lint-spec-status.py`, and `loop-cohort.py` under
      `packs/core/.apm/skills/work-loop/scripts/`.
- [x] The positive fixture still asserts **exactly one** finding; the negative fixture
      and all three production scripts still assert **zero**.
- [x] Every one of the five targets is confirmed present in semgrep's reported scanned
      set before its findings are asserted on. A target absent from that set is a
      failure, never a silent pass — including the two fixtures, which the
      per-invocation version did not check.
- [x] A missing fixture fails with a "path drifted?" diagnosis naming the file, rather
      than being dropped from the scan and misdiagnosed as a rule-scope problem.
- [x] An empty target set is refused, rather than allowing semgrep to walk the working
      directory and rediscover the same files via `paths.include` — which would be a
      green run that proved nothing.
- [x] The test still **fails** when the control is broken, proven by mutation rather
      than inspection, covering at least: a ratcheted target that gains a finding, a
      neutered rule pattern, a corrupted path key, a target dropped from the rule's
      `paths.include`, and every target missing. Each must produce a non-zero exit,
      and the `paths.include` case must produce a **named** failure, not a traceback.
- [x] The test still exits 0 with a skip message when `semgrep` is absent from `PATH`,
      and exits 1 when the rule file is missing.
- [x] Exit codes and the `ok [...]` / `FAIL [...]` output contract are unchanged, so
      `make sast`'s recipe needs no edit.
- [x] `make sast`, `python3 tools/lint-ruff.py`, and
      `python3 -m pytest tools/test_build_gate_chain.py -q` are green.

## Testing Strategy

- **The refactor itself is goal-based**: `Done when:` the self-test exits 0 and spawns
  exactly one semgrep process. Wall-clock is deliberately excluded — see Assumptions for
  why absolute timings on this host are not dependable. There is no invariant to compress
  into a unit test here: the artifact *is* a test, and its correctness is whether it
  still discriminates a working rule from a broken one.
- **That discrimination is verified by mutation, which is the load-bearing check.** A
  faster self-test that can no longer fail is strictly worse than the slow one it
  replaced, and the specific failure mode this refactor introduces — findings keyed by
  a path that never matches, so every "zero findings" assertion passes vacuously — is
  invisible to a green run. One mutation is not enough, because the two directions fail
  differently: a zero-findings assertion must fail when a finding appears, and the
  one-finding assertion must fail when the rule stops firing. The battery run is
  recorded in `plan.md` § Verification, including one mutation that was **not** detected
  and why that is a property of the rule's scope rather than a defect.
- **Skip and missing-rule paths are goal-based**, exercised by invoking with `semgrep`
  off `PATH` and with the rule path pointed elsewhere.

## Assumptions

- Technical: semgrep accepts multiple target paths in one invocation and reports
  `results[].path` per finding plus `paths.scanned` listing every file it examined
  (source: probe — one invocation over all five targets returned all five in
  `paths.scanned` with 1 finding on `positive.py` and 0 elsewhere, 2026-08-17)
- Technical: `paths.scanned` reflects the rule's `paths.include` **per file** even in a
  batched run — a target passed on the command line but outside `paths.include` is
  absent from it (source: probe — passing `tools/lint-ruff.py` alongside `positive.py`
  yielded only `positive.py` in `paths.scanned`, 2026-08-17). This is what makes the
  ratchet assertion survive batching.
- Technical: `paths.scanned` membership does **not** prove the file parsed, and the
  available signal depends on the failure shape. A *partial* parse failure (unbalanced
  bracket, nonsense token) surfaces as a path-attributed `PartialParsing` entry in
  `errors` and `--strict` escalates it to exit 3 — gateable. A whole-file or
  whole-construct failure (`def broken(:`, `3 = x`) yields empty `errors`, empty
  `skipped`, empty stderr and exit 0 even under `--strict` — not gateable (source:
  four probe shapes, 2026-08-17). An earlier revision of this spec claimed no signal
  existed at all, generalising from the whole-file shape; security review caught it.
  Pre-existing and unchanged by this work; tracked as
  `sast-semgrep-unparseable-target-reads-clean`.
- Technical: semgrep has a ~7.4s process-startup floor independent of the registry — a
  local-rule-only scan of one trivial file still costs it (source: probe, 2026-08-17).
  This is what the saving comes from.
- Technical: the batched form is **3.4–5.0× faster** than the per-target form (mean
  ~4.4×), measured as three interleaved A/B pairs under identical machine load —
  5 invocations 54.1 / 35.5 / 46.3s versus 1 invocation 11.4 / 10.5 / 9.3s
  (source: probe, 2026-08-17). On an idle machine the absolute figures were 29.8s → 8.9s.
  Absolute timings on this host proved unreliable (load average reached 60 on 10 cores
  from unrelated work), which is why the ratio is the reported figure and no wall-clock
  bar is an acceptance criterion.
- Technical: semgrep applies `paths.include`/`paths.exclude`, `--max-target-bytes`,
  `nosemgrep`, and its timeout per file rather than per run, and dedupes findings per
  `(rule, path, range)`, so batching cannot change a per-file verdict (source: semgrep
  1.166.0 behaviour, corroborated by adversarial review's independent source read;
  contrast `tools/audit-requirements.py`, where pip-audit resolves all `-r` inputs into
  one shared environment — see `docs/specs/pip-audit-batching/spec.md`)
- Technical: the target argv is **redundant** with the rule's `paths.include` — strip
  the target arguments and semgrep walks the working directory, where the rule
  rediscovers the same five files and returns the same verdict; and conversely semgrep
  never *widens* an explicit file argv, so a sibling fixture matching the glob is not
  scanned (source: two probes, 2026-08-17). No assertion here can therefore prove the
  argv is load-bearing. A first attempt shipped an `unrequested()` check claiming to;
  it was unfireable in both directions and is replaced by `unwired_fixtures()`, which
  enumerates the fixtures directory and *can* fire — verified by adding a file.
- Technical: semgrep echoes target paths back in whichever form it was handed — an
  absolute argument yields absolute `paths.scanned` entries, a relative one yields
  relative — so `cwd=REPO_ROOT` is *not* what aligns the keys; `_key()` normalising both
  sides is. Passing absolute targets against repo-relative keys was the bug that bit
  during implementation (source: probe, 2026-08-17; see
  `tools/test-semgrep-argv-boundary.py` `_key`)
- Process: the security-boundary trigger **does** fire — this file is the SAST gate's
  only proof-of-life for the custom rule — and light mode was retained rather than
  absent; see the Mode comment above for the reasoning and its limits (source:
  `AGENTS.md` § *How we work* risk-trigger list)
