Mode: frame
Write status: not authorized

# Frame — verification contract for `render-release-notes`'s browser test suite

Target resolved: `evals/files/node-browser-suite-SKILL.md`, supplied inline in the request. Read-only; nothing written, and agreement with this frame does not authorize a later write.

## Activation boundary

Should activate: "frame the verification contract for the browser suite I'm adding to this skill", "what must the suite guarantee before I write it", "does the Verification section of `render-release-notes` hold up".

Should not activate: "write the Playwright config", "run the suite and fix the failures", "review the rendered HTML output" — the first is a `create`/`update` request that needs its own authorization, the last two are not skill-authoring work.

## Observable outcome

The suite makes one thing observable: **a layout problem in the rendered page is reported when and only when it is present in the page, independent of how many workers ran, what was installed at test time, and what a previous run left behind.** Every clause below exists to protect that biconditional. A suite that can flip either direction under concurrency, install drift, or residue is not a verification of the skill — it is a second source of noise.

## The three guarantees the suite must carry

### 1. Workers — bounded, declared, and outcome-neutral

- The result of the suite must be identical at one worker and at N workers. Worker count is a cost knob, never an input to the assertion set.
- Worker count must be a declared, pinned value the suite owns, not a value read from the executing machine. `workers = CPU count` makes the concurrency level a property of the laptop or runner that happens to execute it, so a flake reproduces on one machine and not another and the failing configuration is never named in the artifact.
- The suite must state a serial-execution escape: any test that cannot hold guarantee 3 is pinned to a single worker explicitly, rather than the whole suite being detuned.
- Evidence to capture: same suite, same commit, run at 1 worker and at the pinned count, identical pass/fail set.

### 2. Installs — resolved before the suite runs, never by it

- The suite must not invoke a package manager. Installation is a precondition of the run, satisfied by the environment, and a test that shells out to an install command has made network reachability and registry state part of its pass condition.
- Whatever the suite needs — the runner, the browser binary — must be resolved from a locked, pinned manifest, so two runs of the same commit exercise the same versions. "The package manager's default install command at test time" is unpinned twice over: the default command may or may not respect the lockfile, and "at test time" places resolution inside the measurement window.
- Missing dependency is a clean, named setup failure with the expected version stated — not an install attempt, and not a silent skip that reports green.
- **Authority note:** as supplied, the skill declares `boundaries: [filesystem_read_untrusted]`. Installing at test time requires network access and write authority the skill has not declared. Either the install moves out of the suite (preferred, and what this contract requires) or the boundary declaration must be widened deliberately — that widening is a separate change needing its own authorization, and I am not assuming it.

### 3. Shared state — no mutable state crosses a worker or a run

- Each worker gets its own browser profile directory. A profile is mutable: cookies, storage, cache, lock files. One profile reused across concurrent workers means workers race on the same files, and the failure mode is not a clean error but an intermittent one that looks like a layout bug in the page under test. That is the exact confusion this suite exists to prevent, so the startup cost the sharing buys is not payable.
- Directories must be per-worker *and* per-run, created fresh and torn down, so a previous run cannot make a later one pass. Reuse across runs is state leakage even when the run is serial.
- The same rule extends past the profile to every writable location the suite touches: output directories, temp files, any port or lock. If two workers can name the same path, they must not both be able to write it.
- If startup cost is genuinely the constraint, the legitimate lever is a widely-scoped read-only fixture (a built artifact, a served static page) shared across workers, never a shared writable directory. Cost belongs in assertions, not in weakened isolation.
- Evidence to capture: interleaved concurrent run produces no cross-test failure; a deliberately poisoned profile from a prior run does not change the current run's result.

## Failure, interruption, and clean degradation

- Browser unavailable or dependency missing: named setup failure stating what was expected, distinguishable in the report from a layout assertion failure. Never a pass, never an implicit skip.
- Interrupted run: per-worker directories are still removable; a leaked directory is reported as incomplete cleanup rather than swallowed.
- The suite reports the worker count and the resolved versions it ran under, so a failure is reproducible from its own artifact.

## Contracts that stay authoritative

- The skill's declared `metadata.boundaries` govern the suite. The suite may not quietly exercise authority the skill has not declared.
- The skill's stated purpose — report layout problems in the rendered page — bounds the assertion set. Verification of the renderer's internals is a different concern.

## Unavailable capability

This skill is TypeScript/Node-shaped, and the foundation recognizes `typescript-node` as an extension family whose claims must rest on that ecosystem's own topic and stated version range. **That language topic is not present in this skill's references.** So the contract above is stated at the portable floor and deliberately names no runner, config key, worker-scoped fixture API, or browser-automation product. Before you write the suite, source the `typescript-node` topic for the concrete mechanisms — the config surface that pins workers, the per-worker unique identifier, the locked-install command, the pinned browser-download step — and treat any such mechanism I would have named here as unevidenced rather than as guidance.

## Proposed shape (no files created)

```text
render-release-notes/
  SKILL.md                  # Verification section rewritten to the three guarantees
  references/
    verification.md         # the contract: workers, installs, shared state, evidence
```

The `SKILL.md` Verification section should shrink to the invariant and the pointer; the conditional detail — pinned counts, isolation recipe, setup-failure wording — belongs in the reference.

## Non-goals

- Not choosing or naming a test runner, browser-automation library, or package manager.
- Not writing config, fixtures, or test code.
- Not widening `metadata.boundaries` to accommodate installs or network.
- Not adding CI wiring, retries, or flake-quarantine policy.
- Not verifying the HTML renderer itself, only the rendered page's layout claims.

---

```text
Mode: frame
Write status: not authorized
```

Files changed: none. Checks run: mode and target resolution; boundary declaration checked against the behavior the supplied Verification section implies (mismatch found and reported, not resolved); extension-family routing attempted for `typescript-node`. Retained behavior: not applicable, no mutation performed. Unavailable capabilities encountered: the `typescript-node` language topic is absent, so all ecosystem-specific mechanism is withheld. Cleanup: none required.
