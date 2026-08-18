# T4 verification evidence — 2026-08-18

Commands run from the repository root with `PYTHONDONTWRITEBYTECODE=1` and stray
`__pycache__` under `packs/` cleared first — bytecode left by running the skill
scripts directly gets copied into `dist/` and produces a `CAT-V-014` that looks like
this spec's defect but is not. Exit codes read from each command's own output, never
through a pipe.

## AC10 — the drift gate is satisfiable, and demonstrably fails when it should

**Green:**

    rm -rf dist && make build && SKIP_SAST=1 make build-check

    make build exit=0
    SKIP_SAST=1 make build-check exit=0
    CAT-V-014 occurrences: 0

**Demonstrated red** — `claude-plugin-branch` reverted to `main`, same recipe:

    exit=2
    [ERROR] CAT-V-014    dist/claude-plugins/marketplace.json  generated output differs

Restored afterwards; `git diff --stat catalogue.toml` shows only the intended change.

This is the reported symptom in both directions: the handoff brief recorded exit 2
with `CAT-V-014` on clean `main`, and the corrected value produces exit 0. The two
generators now agree because `catalogue.toml` names the branch the constants name.

### A workaround this obsoletes

The recorded lesson *"dist must be built by the gate chain — `make build` writes a
config-aware `dist/` that catalogue verify rejects; `rm -rf dist && make build-check`
instead"* described this defect's symptom, not a property of the build. With the
value corrected, `rm -rf dist && make build && SKIP_SAST=1 make build-check` passes,
so the workaround is no longer needed.

## AC3–AC9 — the parity gate

    python3 -m pytest tools/test_marketplace_envelope_parity.py -q
    65 passed

54 mutation probes, each asserting the failure names the mutated source; a positive
control on the unmutated fixture; the `resolve`-refused-for-a-fixture-root check;
three resolved-layer probes for rebinds the literal layer cannot see (indirect
`globals()[_n]`, a two-physical-line `globals()` write, and a forged `__file__`); the
`str`-subclass refusal; the unimportable-package refusal; and the in-process-plant
immunity check.

Before T2 wired the gate in, the only failing assertion was its own membership in the
two pytest lists — the gate is red by design until it is actually gated.

## AC12 — the record

    python3 .claude/skills/work-loop/scripts/lint-spec-status.py
    spec metadata clean   (exit 0; remaining warnings belong to other specs)

Index drift measured with the canonical parser (`lint-spec-status.parse_status`, never
a fresh regex — a fresh one produced a false positive in the work this followed):

    163 index rows; 0 drifted
    marketplace-generator-single-source/ -> Shipped == Shipped
    guide-typed-asides-test-gate/        -> Shipped == Shipped

Re-run after the status flip, so the recorded tokens are the ones AC12 pins rather than
the pre-flip values an earlier capture held.

Nine deferrals registered in `workspace.toml [backlog].open`; the file parses and
carries no duplicate slug.

## AC11 — `make ci`

Recorded separately below once the run completes; it exceeds a ten-minute foreground
budget and was run in the background.

## AC11 — `make ci` (recorded 2026-08-18)

    env -u SKIP_SAST PYTHONDONTWRITEBYTECODE=1 TMPDIR="$(mktemp -d)" make PYTHON=python3 ci
    make ci: complete — every leg of this target was invoked, SAST/SCA included.
    EXITCODE=0

`env -u SKIP_SAST` so the SAST/SCA legs actually ran; `PYTHONDONTWRITEBYTECODE=1` and a
cleared `packs/`/`packages/` `__pycache__` because bytecode written mid-run gets copied
into `dist/` and reported as `CAT-V-014` generated-output drift.

**An earlier attempt failed at exit 2 for that exact reason, and the cause was this
change's own gate.** Its child interpreter runs with `-I`, which implies `-E` and
therefore ignores `PYTHONDONTWRITEBYTECODE`, so it wrote four `__pycache__`
directories into the tree it audits — meaning the gate would have reddened the very
check it exists to protect. Fixed by adding `-B` to the child argv, and re-measured at
zero directories. Read the exit code from the command's own output: the harness
reported the wrapper's status as 0 while `make` had exited 2.


## The `self_host.py` writer, verified through the real artifact

`_aggregate_marketplace`'s `description` default changed from a literal to
`_MARKETPLACE_DESCRIPTION`, and that function *is* the writer of the committed root
`.claude-plugin/marketplace.json`. An earlier note claimed the design "touches no
writer" — that was wrong, so the byte-identity result is recorded here rather than
assumed:

    make build-self          # exit 0 (tree clean, so no FORCE needed)
    root marketplace sha before: e8f0a0e3946ee2d9
    root marketplace sha after : e8f0a0e3946ee2d9
    byte-identical: YES
    git status --porcelain   # 0 entries
    emitted description: "Agent skills, subagents, and hooks for Claude Code and other coding agents."

And the defect itself, checked at the level it was reported:

    make build
    diff dist/claude-plugins/marketplace.json <fresh build_catalogue output>
    -> IDENTICAL

That direct comparison is what was failing when this work started; it is the whole
objective, and it now holds.

## Mutation survival of this suite

The probe contract was strengthened after a review mutation-tested it: with probes
asserting only "some failure named the mutated path", 20 of 40 individual refusals could
be deleted with every test still green — including both ADR-0072 literal pins, because
downstream parity caught the mutation first. Each probe now requires the *specific*
refusal it targets.

Re-measured with a correct mutation operator (an earlier sweep of my own used
`if False and <cond>`, which for any condition containing `or` parses as
`(False and A) or B` and therefore neutralised nothing — the instrument was faulty and
overstated survivors):

    11 of 46 guarded refusals survive deletion

All eleven are defensive type-guards against malformed input — a non-string
`catalogue.build` value, an entry that is not an object, `_dig`'s shape guards — not
behavioural controls. Recorded rather than smoothed over.
