# Give native Windows and macOS verification a coverage contract worth running

- **Status:** Draft
- **Level:** feature

## Outcome

A maintainer dispatching native-platform verification gets evidence that depends
on the platform it ran on: each admitted check fails on the wrong host, the
expected-skip set is explicit, and a degraded runner fails the lane instead of
skipping quietly. The platform classification behind that admission is recorded
where a reader can act on it and enforced where a mechanism can decide it.

## Boundary

- Deliver independently of the remote dispatch surface. That surface provides
  the trigger, the pinned revision and the receipt; this item provides the
  native coverage worth dispatching and does not re-specify either.
- Cover native Windows by making the existing curated Windows contract callable
  without changing what its automatic path verifies, and by giving it the
  collection floor and expected-skip set it currently lacks.
- Cover native macOS only with checks whose result depends on Darwin. Admit a
  simulated check as native evidence for nothing.
- Record the platform classification for every admitted check, and enforce
  mechanically only the part a mechanism can decide.
- Exclude Xcode builds, signing identities, simulators, nested virtualization,
  Apple deployment, larger or self-hosted runners, and any weakening of an
  existing gate or required check.

## Owner

- eugenelim

## Unresolved questions

- Whether native macOS coverage is worth a controlled runner before native
  Darwin tests exist. The measured position below argues the lane's present
  value is one assertion; the decision is whether to write native tests first,
  run the thin lane meanwhile, or defer the lane entirely.
- Whether the projected and self-hosted copies of a Darwin-dispatching module
  are separate coverage sites or one site with several tracked locations.
- Whether `macos-15` on arm64 supports the toolchain the lane needs. Unproven.

## Opportunity

Measured on 2026-09-04, and each figure is the reason this is a separate item
rather than a paragraph in the dispatch-surface spec.

- **Exactly one test in the repository reads a live platform identifier for
  Darwin**: `packs/credential-brokers/tests/pack/test_sso_broker_user_scope.py`.
  It branches on `sys.platform` and asserts the Darwin backend is selected, so
  on a Darwin host it proves native dispatch. Every other Darwin-facing test
  forces an identifier and passes on Linux. A macOS runner today would therefore
  execute one meaningful native assertion.
- **The forcing shapes are heterogeneous**, so a single predicate cannot
  separate simulated from native: `monkeypatch.setattr(sys, "platform", …)`, a
  keyword argument such as `_user_config_path(platform="darwin", …)`, and a
  docstring mention with no platform code. Scope is per test function, not per
  file.
- **The Darwin-dispatching modules ship in many tracked copies** — under
  `packages/credbroker/`, three trees beneath
  `packs/credential-brokers/.apm/`, and the self-host projection in
  `.agentbundle/`. A hand-written site list names one copy and misses the rest;
  three attempts at such a list were each wrong.
- **Classification is not derivable.** A lint can decide whether a test reads a
  live platform identifier. It cannot decide `host-neutral` versus
  `posix-shared` versus `platform-simulated`; that is a judgement, so a
  criterion asserting a derived classification cannot be discharged.
- **The macOS credential backend takes no keychain operand.** Its
  `security add-generic-password` and `find-generic-password` argv name no
  keychain, so every operation targets the *default* keychain. Overriding `HOME`
  does not redirect it; only setting the default keychain and the search list,
  and unlocking it, does — and a shipped record already notes that runners
  require the unlock.
- **The existing Windows workflow asserts no collection floor and no
  expected-skip set**, so a suite that stops collecting, or one that skips
  because provisioning degraded, passes it today.
- **Making that workflow callable is not free**: it declares no `workflow_call`,
  carries two dependency-cache steps whose behaviour must differ per trigger
  path, and its three checkouts do not disable credential persistence. Its
  posture test drives a position-sensitive mutation matrix, so an edit can leave
  a mutation pointed at the wrong job while still passing.
- **The lint that enforces suite-addressing rules reads a hand-listed set of
  runner files** that contains neither a new dispatch workflow nor the Windows
  workflow, so those rules are unenforced for any new caller until that set
  admits it.

## Assumptions

- The public macOS runner labels move between stable images, so a versioned
  label is required rather than `-latest`. Standard macOS concurrency is capped
  well below the Ubuntu and Windows caps.
- Writing native Darwin tests is a different feature from dispatching them. This
  item may conclude that the tests must come first.

## Projection

- Decide the macOS question in the Unresolved list before specifying the lane;
  the measured one-assertion position is the input.
- Give the census a scope statement that says which tracked copies count, and
  enforce only the live-versus-forced distinction, which is decidable.
- Give both native lanes a collection floor per invocation and an expected-skip
  set in which a dependency-conditional or binary-on-PATH-conditional skip is
  inadmissible, since those are what a degraded runner produces.
- Extend the suite-addressing lint's runner set as part of the change that adds
  a caller, so its rules are enforced rather than asserted.

## Source

- Mode: chat-only
- Locator: chat/remote-ci-uplift
- Revision: 2026-09-04
- Authority: transferred-to-repository
