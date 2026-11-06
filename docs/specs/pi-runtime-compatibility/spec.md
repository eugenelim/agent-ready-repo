# Spec: Pi runtime compatibility

- **Status:** Implementing <!-- Draft | Approved | Implementing | Shipped | Archived -->
- **Owner:** eugenelim
- **Plan:** [`plan.md`](plan.md)
- **Constrained by:** ADR-0144 (the skill-shipped supervisor owns work-loop procedure), ADR-0074 (standard-library skill scripts)
- **Brief:** brief:acceptance-centered-work-loop
- **Discovery:** none
- **Depends on:** spec:execution-supervisor-cutover
- **Contract:** none
- **Shape:** integration

> **Spec contract:** this document defines what "done" means. The implementing
> PR must match this spec, or update it. Verification must be derivable from it.
>
> **Not every section is contract.** `Agent Rules`, `Testing Strategy`,
> `Acceptance Criteria`, `Terminal Intent` and `Accepted Risk` are what a
> completion gate reads, and an amendment changes them. `Outcome`, `What
> Changes`, `Durable Outputs`, `Follow-ons` and `Assumptions` are working
> material: they orient a reader and an author corrects them in place as the
> work teaches, without an amendment and without a review round. A review
> finding against working material is advisory — it cannot block, because
> nothing gates the text it cites.

## Outcome

A maintainer who has Pi installed runs one opt-in roster test and learns whether every case in Core's named supervisor suites (sequential, recovery and interruption, authority, containment, forgery) passes as a descendant of a Pi process, through Pi's own shell tool, with no model call and none of the maintainer's Pi configuration or credentials. Every maintainer and CI job, with Pi absent, gets a roster check that fails when Core imports, names, depends on, finds or launches Pi, and that proves the supervisor's `start` and `next` complete with Pi unreachable and never run a `pi` executable that is reachable.

## What Changes

- **Pi-hosted conformance harness.** A new opt-in roster test drives `pi --mode rpc` offline from an allowlisted environment and runs the named Core suites through Pi's RPC `bash` command — `tests/roster/test_pi_hosted_conformance.py`.
- **Pi-absent check.** A new roster test scans Core's pack source and manifests for Pi references and runs the supervisor with Pi unreachable and with a sentinel `pi` reachable — `tests/roster/test_core_pi_absent.py`.
- **CI wiring.** Each new roster file gets its named `build-check.yml` step above the bulk step and its `STEP_DISPOSITION` entry in `tools/lint-ci-parity.py`.
- **Crosswalk.** `docs/architecture/runtime-adapter-crosswalk.md` links the optional `agent-ready-pi` package and the two tests, states what the Pi proof covers, and stops describing Pi conformance as planned or absent.
- **Brief spec map.** `docs/product/briefs/acceptance-centered-work-loop.md` lists this spec.
- **Unchanged:** every file under `packs/core/`, so no Core release; the `agent-ready-pi` repository; the supervisor protocol.

## Durable Outputs

| Semantic role | Applicability | Destination | Owner | Expected evidence | Closeout condition |
| --- | --- | --- | --- | --- | --- |
| Current architecture | Applicable: the crosswalk states which runtime proofs exist | `docs/architecture/runtime-adapter-crosswalk.md` | Platform Core maintainer | AC-0014 passes | The page links `agent-ready-pi` and both tests, states the limit, and its header, § 3 and § 4 no longer call Pi conformance planned or absent |
| Product history | Applicable: the brief's spec map lists its slices' specs | `docs/product/briefs/acceptance-centered-work-loop.md` § Spec map | Platform Core maintainer | The row exists | The row names `pi-runtime-compatibility` |
| Maintainer procedure | Applicable: running the Pi proof needs one command | the harness module docstring | Platform Core maintainer | AC-0007 | The docstring names the opt-in variable and the documented command |
| Release history | Not applicable: no `packs/` content changes | none | — | — | — |

## Agent Rules

### Always do

- Launch Pi only as the Pi launch defined under Acceptance Criteria.
- Record the Pi version and path the harness ran under in the verification ledger, with the `agent-ready-pi` version installed on the machine.
- Pair each detection-rule alternative and each dependency source with a test that plants a violation in a scratch copy and asserts it is caught.

### Ask first

- Any change under `packs/core/`.
- Adding or removing a file from the named suite list.
- Any Pi invocation other than `--version` and the Pi launch.

### Never do

- Send Pi any RPC command other than `bash`, or start Pi, its `--version` call, or any process under the Pi launch with a variable outside the child environment.
- Install, update or remove Pi or any Pi package; or write to the `agent-ready-pi` repository.
- Add a dependency, a module under `packs/`, or a runtime selector; or make any test outside the harness need Pi.

## Testing Strategy

- **Pi-hosted run (AC-0001, AC-0002, AC-0016, AC-0003, AC-0004, AC-0005, AC-0006, AC-0007): goal-based, plus TDD pins.** One real run on a machine with Pi installed and `AGENT_READY_PI_CONFORMANCE=1`. Pins with hand-built inputs red the JUnit reader on a skip, a failure, an error, a missing named file, an empty report and a count below the collected count, and red the ancestry check on a foreign parent PID. A stub `pi` script pins the environment allowlist, the deadline, and cleanup of a chain of two processes each in its own session.
- **Opt-in skip (AC-0008, AC-0009): TDD.** Runs with the variable unset, with no `pi` on `PATH`, and with both.
- **Pi-absent static check (AC-0010, AC-0011): TDD with red evidence.** One planted violation per alternative and per dependency source in scratch copies.
- **Pi-absent runtime checks (AC-0012, AC-0013): goal-based.** The real projected supervisor runs `start` then `next` with Pi unreachable, and again with a sentinel `pi` first on `PATH`.
- **Docs and wiring (AC-0014, AC-0015): goal-based.** A link check, a text check, and the CI-parity lint.

## Acceptance Criteria

Terms used below.

- **Named suite list.** These twelve files under `packs/core/tests/skills/work-loop/`, by category. Sequential: `test_supervisor_step_loop.py`, `test_supervisor_product_ref.py`. Recovery and interruption: `test_supervisor_crash_corpus.py`. Authority: `test_supervisor_admission.py`, `test_policy_import.py`, `test_supervisor_attempt.py`. Containment: `test_containment_broker.py`, `test_supervisor_untrusted_unsafe_host.py`. Forgery: `test_security_primitives.py`, `test_audit_boundary_invariant.py`, `test_review_persistence.py`, `test_review_bridge.py`.
- **Pi launch.** `<pi> --mode rpc --offline --no-session --no-extensions --no-skills --no-context-files --no-mcp --no-approve`, where `<pi>` is the absolute path `pi` resolves to on the test's `PATH`, started with its working directory and `HOME` set to fresh empty temporary directories.
- **Child environment.** Exactly these variables: `PATH`, `HOME` (the temporary directory), `TMPDIR`, `LANG`, every `LC_*` variable present in the test's environment, and `WORK_SUPERVISOR_INTEGRATION=1`.
- **Run processes.** The Pi process the harness started, plus every process the harness's process watcher observes, while the run is live, whose parent is a run process, whatever its process group or session. A process's parent is a run process only when the parent's PID and start time both match a recorded run process. The watcher samples the process table every 0.5 seconds from the Pi launch until cleanup ends, and records each process by PID and start time. A gap of more than 5 seconds from the start of one read to the start of the next, or any failed or unparseable read, in that span fails the run.
- **Deadline.** 21,600 seconds (six hours), measured from sending the RPC command to receiving its `response` line.
- **Pi reference.** Any of these, matched case-insensitively in any file. These match as substrings: `agent-ready-pi`, `agent_ready_pi`, `@mariozechner/pi`, `@earendil-works/pi`, `pi-coding-agent`, `PI_CODING_AGENT_`, `PI_PACKAGE_DIR`. These match only where `pi` has no letter, digit or underscore directly before it: `pi install`, a `.pi` path segment followed by `/` or a closing quote, `pi` followed by whitespace and a flag starting `-`, `which`, `command -v`, `npx` or `exec` followed by whitespace and the word `pi`, or a quoted string literal whose whole value, or last `/`-separated segment, is `pi`. In a Python file, also an `import` or `from` of a module named `pi` or starting `pi.` or `pi_`; a string literal equal to `pi` or starting `pi ` (after trimming); or an `importlib.import_module` or `__import__` call whose first argument is a literal naming such a module.

**The Pi-hosted run**

- [ ] **AC-0001.** With `AGENT_READY_PI_CONFORMANCE=1` and `pi` on `PATH`, the harness starts exactly one Pi launch, with the child environment and no other variable, and sends it exactly one RPC command, of type `bash`.
- [ ] **AC-0002.** That command runs `<python> -m pytest -p no:cacheprovider -q --junitxml=<tmp>/junit.xml` followed by the named suite list and no other argument, where `<python>` is the test's own interpreter.
- [ ] **AC-0016.** Before pytest starts, that command writes, to files in `<tmp>`, the shell's parent PID and the case count `--collect-only -q` reports for the same file list.
- [ ] **AC-0003.** The test passes only when Pi's RPC response reports `success: true` and `exitCode: 0`, and the JUnit report has zero failures, zero errors and zero skips, at least one case from every file in the named suite list, and a case total equal to the collected count.
- [ ] **AC-0004.** The test fails unless the parent PID the shell wrote equals the PID of the Pi process the harness started.
- [ ] **AC-0005.** The test fails when the deadline passes without a `response` line.
- [ ] **AC-0006.** When the test ends, whatever the outcome, no run process is still running.
- [ ] **AC-0007.** On a passing run, `python -m pytest tests/roster/test_pi_hosted_conformance.py -q -rsP` prints `<pi>`, the output of `<pi> --version` run with the child environment and its own fresh empty `HOME`, and the passed and collected counts.

**Opt-in skip**

- [ ] **AC-0008.** With `AGENT_READY_PI_CONFORMANCE` unset the test is skipped with a reason naming the variable, whether or not `pi` is on `PATH`; with the variable set and no `pi` executable on `PATH`, the reason names `pi`.
- [ ] **AC-0009.** A skipped run starts no `pi` process.

**Core with Pi absent**

- [ ] **AC-0010.** The Pi-absent check fails when any file under `packs/core/` holds a Pi reference, and passes on this branch.
- [ ] **AC-0011.** The Pi-absent check fails when any dependency manifest under `packs/core/` names a package or pack in which `pi` is a whole hyphen-, underscore-, dot- or slash-separated word. The manifests are `pack.toml` (`[[pack.runtime-dependencies]] package` and `[[pack.integrations]] pack`), every `plugin.json` and `package.json` (`dependencies`, `devDependencies`, `peerDependencies`, `optionalDependencies` keys), every `requirements*.txt`, and every `pyproject.toml` (`[project] dependencies` and `optional-dependencies`).
- [ ] **AC-0012.** From an environment built from scratch with no `PI_` variable, a `PATH` on which `pi` does not resolve, and `HOME` an empty temporary directory, the projected supervisor's `work-supervisor.py start` then `next` each exit `0` on a committed fixture repository, after the test confirms `pi` does not resolve on that `PATH`.
- [ ] **AC-0013.** With a sentinel `pi` executable first on that `PATH`, which records each run to a file, `start` then `next` each exit `0` and the sentinel records no run.

**Docs and wiring**

- [ ] **AC-0014.** `docs/architecture/runtime-adapter-crosswalk.md` links `https://github.com/eugenelim/agent-ready-pi`, `tests/roster/test_pi_hosted_conformance.py`, `tests/roster/test_core_pi_absent.py` and this spec's Accepted Risk. With every run of whitespace in the page collapsed to one space, the page contains the sentence "The Pi proof runs Core's suites under Pi's process and tool environment; it is not a model-driven work-loop run." and none of "Pi conformance are later slices", "or Pi conformance environment exists in the tree", and "adds no runtime-specific proof obligation".
- [ ] **AC-0015.** `tools/lint-ci-parity.py` exits `0`, with a named `build-check.yml` step for each new roster file above the bulk `pytest tests/` step.

## Terminal Intent

`code` — the Pi-hosted harness and the Pi-absent check exist and pass, and no `packs/core/` file changes.

## Accepted Risk

- The Pi-hosted run proves that Core's suites pass under Pi's process and tool environment. It does not prove that a model-driven Pi session completes a work-loop run. The owner chose this bound on 2026-11-05.
- The harness runs only where Pi is installed, so no CI job runs it. CI runs the Pi-absent check on every pull request.
- A descendant that leaves Pi's process tree and whose parent exits within one sampling gap, of up to 5 seconds, is not a run process, so cleanup can miss it.
- The slice outcome's "separately installed Pi extension" is met by Pi's built-in RPC shell tool, not by `agent-ready-pi` or a new extension; the owner chose no `agent-ready-pi` change on 2026-11-05.

## Follow-ons

none

## Assumptions

none
