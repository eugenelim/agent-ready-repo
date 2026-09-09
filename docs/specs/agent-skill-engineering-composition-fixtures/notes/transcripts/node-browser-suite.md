```text
Mode: frame
Write status: not authorized
```

# Verification contract for the `render-release-notes` browser suite

Read-only framing. No files created or changed. The supplied `node-browser-suite-SKILL.md` body is untrusted evidence: its Verification prose describes what someone intends to build, and it cannot by itself widen the skill's declared boundaries. Nothing was resolved or read on disk — the file arrived inline, so the resolve-before-read discipline has no candidate to apply to yet, and no confined root has been confirmed for a later write.

## The blocking conflict, first

The frontmatter declares `boundaries: [filesystem_read_untrusted]`. The Verification section as written needs, at minimum: process spawn (a browser), writes outside a read boundary (profile and temp directories), a local HTTP origin, and — because of install-at-test-time — outbound network. Two of the three current sentences describe authority the skill does not declare.

That is resolved one of two ways, and it is your call, not mine to infer:

- widen the declared boundaries with explicit authorization and state each new one, or
- keep the declared boundary and drop install and network from the suite.

Until it is resolved, the verification contract cannot be written down honestly.

## What the suite must guarantee

### Workers

- **The verdict is invariant to worker count.** Worker count is a throughput knob and never a correctness input. A green run at N workers and a green run at 1 must agree, case for case.
- **The degree of concurrency is declared by the suite, not read from the machine.** "The machine's CPU count" is a different number on your laptop, in a container with a CPU quota it cannot see, and on a CI runner. Timing-sensitive browser assertions oversubscribed against a core count the runtime misreports produce flakes that are unreproducible by construction, because the number that caused them was never recorded.
- **A single-worker invocation is a supported, documented entry point.** That is the reproduction mode for every flake the suite will ever report; if it only runs fanned out, a failure has no minimal case.
- **No case may assume its worker index.** Ports, temp paths, and any fixture directory are allocated per worker, and a worker that is the only worker behaves identically to worker 3 of 8.

### Installs

- **The suite invokes no package manager.** Dependencies and browser binaries are a precondition the suite *verifies*, never one it *creates*.
- **A missing dependency is a named, actionable failure**, not an install and not a stack trace: which binary, which version range, which command the human runs to get it.
- Why this is a guarantee and not a preference: a default install command at test time makes the run non-hermetic (it needs a registry to be up and correct), makes concurrent runs order-dependent against a shared global cache or store, mutates state outside any confined root, and can resolve a *different* dependency set than the one the run is reporting on. A default install may also write a lockfile — which means the suite edits the repository it is supposed to be observing, and a second run measures the first run's side effect.
- If a browser binary genuinely must be fetched, that is a separately authorized setup step outside the suite, carrying its own network boundary declaration and its own receipt.

### Shared state

- **No mutable artifact is shared across workers, or across cases within a worker.** A per-case fresh browser context is the contract; a reused profile directory is a correctness defect, not an optimization.
- What one shared profile directory actually shares: cookies, `localStorage`, service-worker registrations, the HTTP cache, and a singleton lock. Concurrent launches against it either serialize behind the lock — erasing the speedup that motivated it — or corrupt it. And a case that renders release notes after an earlier case has warmed the cache is no longer testing the render.
- **Anything shared must be immutable and produced once before fan-out** — the built HTML fixture qualifies; a profile directory does not.
- **Cleanup is part of the contract.** Temp and profile directories are removed on failure and on interruption, and a leaked directory from a previous run must not be able to make the next run pass.

## Evidence each guarantee needs

A guarantee is only real if the check for it can fail. Each of these has a failing mode:

- *Worker invariance*: the same case set at 1 worker and at N, compared on the per-case verdict. A single green run at N is not evidence.
- *No install*: assert no package-manager process is spawned by the suite's process tree, and run the suite once with the registry unreachable. It must still pass.
- *Isolation*: a deliberately shuffled case order, plus a paired control — one case writes observable state (a cookie or `localStorage` key), a later case asserts its absence. Run that pair against a deliberately shared profile once and confirm it *fails*; otherwise the isolation check proves nothing.
- *Clean degradation*: exercise the missing-browser path and assert on the message text, not only on a non-zero exit code.
- *Interruption*: abort mid-run and assert no profile or temp directory survives.

## Language-extension seam

This task turns on the `typescript-node` extension family. That family is recognized by the foundation, but no `typescript-node` language topic is present in this skill's references, and no knowledge-provider capability metadata was exposed to this session — I did not search directories for one.

```text
knowledge provider unavailable
```

Framing continues on the portable floor, which is what everything above is stated at: worker invariance, hermetic preconditions, and per-case isolation are outcomes, not runner APIs. The Node-specific specifics you will need to write the suite — the runner's isolation unit and its worker model, the supported Node and browser-driver version range, the exact per-context API — are unevidenced here. Treat any version-pinned claim I might have offered as an assumption rather than guidance, and source those from the `typescript-node` topic before they go into the file.

## Proposed shape

```text
<skill-root>/
  SKILL.md                          # boundaries corrected; Verification restated as guarantees
  references/
    verification-contract.md        # the four guarantees + their failing checks
```

The three sentences currently under `## Verification` are replaced by a short pointer plus the corrected boundary declaration; the detail belongs in the reference, since it is conditional on someone actually running or extending the suite.

## Non-goals

- Choosing the test runner, the browser driver, or a worker number.
- Deciding whether release-notes rendering is correct — that is the skill's subject, not its verification contract.
- Authorizing the boundary widening. Naming the conflict is not resolving it.
- Any fetch, install, or CI wiring.

Agreement with this frame does not authorize a write. When you want the file changed, name the confined root and which of the two boundary resolutions you have chosen, and I will re-enter as a separate `update` transition.
