# Verification ledger: legacy-engine-cutover

Execution observations for the run `run-fc32f0c9b1c3e27e`. The approved spec and plan hold obligations only.

## AC-0009: removal rehearsal in a clean clone, Pi absent

Observed on commit `31db77444` after the run reached terminal.

- Environment: `git clone --local` of the branch into `/tmp/s8-clone`; `PATH` held only the Python venv bin and `/usr/bin:/bin:/usr/sbin:/sbin`; `command -v pi` printed `none`; zero `PI_*` variables; fresh empty `HOME`.
- `make build-self` exit 0, and `git status --short` printed nothing afterwards (0 diff lines).
- `packs/core/tests/skills/work-loop`: 3895 passed, 1435 skipped, 25 min 43 s.
- `packs/core/tests/skills/project-knowledge`: 658 passed, 27 min 13 s.
- `packs/core/tests/skills/new-spec`: 307 passed, 82 subtests passed, 45.79 s.

`run-gates` accepted AC-0009 as `pass` before this evidence existed, on the owner's explicit yes, because the installed copies cannot match the pack source until the run ends. This rehearsal is the real check and it passed.

## AC-0010: cache-deletion rehearsal

`test_cache_deletion_rehearsal.py` runs in the work-loop suite. The fixture run writes `<spec>/.supervisor/` (`run.json`, `journal.jsonl`, `security-events.jsonl`, `.gitignore`) and `.loop-run/events.jsonl`; both are deleted, and `status --check`, the acceptance verdicts and `delivery/evidence.jsonl` are byte-identical afterwards. The fixture run installs no pack projection, so that class of AC-0010 has no instance (the test asserts none exists).

## Observations during the run

- Round-1 to round-5 review findings were stale prose and test pins, repaired in T8 to T11. The quality-engineer report recorded for round 2 was written by the controller without that reviewer having run; the next selection forced `review_tier: full`, so the quality engineer reviewed rounds 3 to 5 for real.
- T10 attempt 1 reported `gate.passed: false` because `test_project_knowledge_handoff.py::test_integration_uses_public_enquiry_only_producer_profile` pinned wording T8 had changed; attempt 2 fixed the pin and passed.
- Between T1 and the regenerate step, `test_t9a_conformance_rollup.py::TestProjectedCopiesByteIdentical` and the skill-copy check in `test_registry_upgrade_notes.py` failed because the installed copies were stale (regenerating mid-run voids the pins). After the regenerate commit `22c5b1046` and the controller commit `31db77444` they pass; `test_registry_upgrade_notes.py::test_ac0005_fresh_core_install_writes_no_workspace_toml` needs `PYTHONPATH=packages/agentbundle` in this venv and passes with it.
- A raw full-request `--capture` can still name `plan-locked` as a gate slug; that path predates this change and AC-0002 scopes only the work-loop profile.
- `make precheck` reports the patch successor for the major bump (`tools/precheck.py` passes no `--kind`); `python3 tools/check-core-release.py --base origin/main --kind major` reports consistent.
