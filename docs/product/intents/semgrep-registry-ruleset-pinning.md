# Semgrep registry ruleset pinning

- **Status:** Draft
- **Level:** feature

## Outcome

The SAST gate fails only on the code under change. Today a busy machine can red
it on files the diff never touched, and the only remedy available to a
contributor is to wait and try again.

## The opportunity

`make sast` fetches `p/python` and `p/security-audit` from the Semgrep registry
unpinned, and runs them under `--strict`. `--strict` promotes semgrep's own
diagnostics into a non-zero exit, and a per-file time-budget breach is one of
those diagnostics. So when several tools gate at once on one machine, a registry
rule that is merely slow reds the build on unrelated code.

The Makefile already predicted this. The `Revisit if` note beside `--strict`
states it exactly: "p/python and p/security-audit are fetched unpinned, so a
future registry rule that times out on any file in `SAST_DIRS` reds the gate on
an unrelated diff." That condition has now fired, with measurement.

Measured on 2026-09-04, four runs over one unchanged tree: 3 timeouts on one
file, then 14 across six files, then 3 again, then 0 and a clean exit — at load
95 to 226 on 10 cores. The file set reshuffles between runs and the count tracks
load rather than the diff, which is what distinguishes this from a real defect.
Running the exact failing invocation against a named file alone exits 0.

## What would have to be true

The rulesets resolve to a fixed version rather than to whatever the registry
serves that day, so a rule's timing behaviour cannot change under an unrelated
commit. Pinning and vendoring are both admissible; ADR-0017 already accepts
registry churn and names pin-or-vendor as the mitigation, so choosing between
them is the substance of this intent.

Whichever is chosen needs an update path. A pin that nobody advances becomes a
stale ruleset, which is a slower version of the same problem: the gate stops
reflecting current rules and nothing says so.

## Boundary

Widening `SEMGREP_EXCLUDE` is explicitly not the remedy. It trades a transient
failure for a permanent blind spot, and under ADR-0102 a new exclusion needs a
stated residual and a retirement trigger — neither of which this situation
supplies, because the rule is not wrong, only slow.

This is about which rules run, not about how the gate reports. The reporting
half shipped separately: `tools/run-semgrep-gate.py` prints the timeout count,
the number of distinct files, and the one-minute load average, so a reader can
tell a budget breach from a defect without re-running.

## Provenance

Mechanism and measurement are recorded as captured observation
`kco-202609-eedad38fd2209acf34ec0420454aff1af6624a058c89124f1b77e8b48f5a8f52`
in `docs/knowledge/observations/gotcha/2026-09.jsonl`, distilled to topic
`semgrep-strict-fails-the-build-on-untouched-files-when-the-host-is-contended`.
