# Spec: agent-spec-cli (`agentbundle`)

- **Status:** Shipped
- **Owner:** eugenelim
- **Plan:** [`plan.md`](plan.md)
- **Constrained by:** [RFC-0003](../../rfc/0003-spec-and-cli.md) (source);
  hard-depends on [RFC-0001](../../rfc/0001-bundle-distribution-by-adapter-spec.md)
  (F-spec + F-build) and the sibling spec
  [`docs/specs/distribution-adapters/spec.md`](../distribution-adapters/spec.md)
  (defines `pack.toml`, `adapter.toml`, the **Tier-1/2/3 file-safety
  contract**, the **`.agent-ready-state.toml` schema**, the
  **`.upstream.<ext>` companion semantics**, the **six-recipe enumeration**,
  and the **five primitive types** this CLI honours).

> **Spec contract:** this document defines what "done" means. The implementing
> PR must match this spec, or update it. Verification must be derivable from it.

## Objective

Ship `agentbundle`, the reference CLI for the published adapter contract, as a
Python 3.11+ stdlib-only package at `packages/agentbundle/`. The CLI is the
deterministic counterpart to the LLM `adapt-to-project` skill: it imports the
render pipeline from `agentbundle.build` (the F-build library introduced by
the sibling `distribution-adapters` spec) and exposes eleven pack-aware
subcommands — in canonical install-workflow order (discovery-first):
`list-packs`, `list-targets`, `scaffold`, `install`, `validate`, `render`,
`adapt`, `diff`, `upgrade`, `uninstall`, `init-state` — to adopters in constrained-network or CI
environments. Success means an adopter on a corporate-network sandbox can
(1) fetch a `zipapp` build via `gh release download`, (2) `install` the `core`
pack into a brownfield repo without clobbering pre-existing files, (3) `adapt`
against a `--values-from` TOML to resolve `<adapt:NAME>` markers from
`.adapt-discovery.toml` and surface `.upstream.<ext>` companions for human
merge, and (4) round-trip `validate` + `render` against the conformance
fixtures with byte-identical output to RFC-0001's `make build`. The CLI is
library-first: F-build's render code is imported as `agentbundle.build`, not
invoked via `subprocess`. Every subcommand respects the Tier-1/2/3 file-safety
contract defined in the sibling `distribution-adapters` spec — Tier-1 may be
written, Tier-2 is preserved with a `.upstream.<ext>` companion, Tier-3 is
never touched. The CLI handles **five** primitive types (`skill`, `agent`,
`hook-body`, `hook-wiring`, `command`) and **six** recipe types as enumerated
in the sibling spec. No LLM calls, no third-party Python dependencies, no
writes outside the adopter's repo root.

## Boundaries

The three-tier guard that keeps an implementing agent inside the lines.
*Always do* applies without asking; *Ask first* requires human sign-off
before proceeding; *Never do* is a hard rule, even under time pressure.

### Always do

- Honour the Tier-1/2/3 file-safety contract on every subcommand that writes:
  Tier-1 paths (adapter-contract-projected, recorded in
  `.agent-ready-state.toml`) may be created or overwritten; Tier-2 paths (same
  paths, but adopter-edited since install per content-hash comparison) get a
  `.upstream.<ext>` companion next to the original; Tier-3 paths (everything
  else) are read-only to the CLI. The contract, the
  `.agent-ready-state.toml` schema, and the `.upstream.<ext>` semantics are
  owned by the sibling `distribution-adapters` spec (see its Tier-contract
  AC and state-file AC); this CLI consumes them verbatim.
- Import the render pipeline from `agentbundle.build` (the F-build library
  introduced by the sibling spec when it moved F-build under
  `packages/agentbundle/agentbundle/build/`); reuse one implementation rather
  than calling `make build` via `subprocess`. Adapters resolve via the
  imported `agentbundle.build.adapters` registry at runtime, not from baked-in
  constants. The registry contract: `agentbundle.build.adapters` exposes a
  mapping `name → AdapterModule` populated at import time (sibling
  `distribution-adapters` spec pins the `AdapterModule` shape).
- Fetch `git+https://` catalogue URIs via `urllib.request` against GitHub's
  archive endpoint (`https://github.com/<owner>/<repo>/archive/refs/tags/<tag>.tar.gz`,
  `…/archive/refs/heads/<branch>.tar.gz`, or `…/archive/<sha>.tar.gz`) and
  extract with `tarfile` — pure stdlib, no `git`/`gh` subprocess. SSH git URLs
  are deferred to v1.1.
- Resolve the spec version a pack declares by reading `[pack.adapter-contract]
  version` in its `pack.toml`; refuse to operate on packs whose major version
  disagrees with the CLI's own and emit a clear refuse-and-explain message.
  The CLI's own spec version is parsed at import time from the bundled
  canonical `adapter.toml` (`[contract] version`), not hardcoded.
- Confine every write-capable subcommand to paths under the configured
  `--output <dir>` or the resolved repo root; refuse and exit non-zero on any
  attempt to project outside that root (e.g. a malicious projection rule
  resolving to `../../`).
- Preserve the source extension of hook files when projecting and upgrading:
  `.sh` hooks remain `.sh`, `.py` hooks remain `.py`.
- Exit non-zero with a one-line stderr reason on any failure (validation,
  hash mismatch refusal, version mismatch, missing pack, primitive-not-found,
  unreachable catalogue URI); exit zero only when the subcommand's contract
  was satisfied.
- Read configuration and state exclusively from TOML files (`pack.toml`,
  `.agent-ready-state.toml`, `.adapt-discovery.toml`, `--values-from <file.toml>`).

### Ask first

- Adding a new subcommand or flag beyond the eleven enumerated in
  RFC-0003's F-cli. The shape is fixed at this RFC's resolution; expansion
  goes through a new RFC or spec amendment.
- Changing the CLI's name from `agentbundle` (committed at this spec) or the
  package path from `packages/agentbundle/`.
- Introducing a new persisted on-disk artifact (file the CLI writes that
  isn't already in this list: Tier-1 projected files, `.agent-ready-state.toml`,
  `.adapt-pending.md`, `.upstream.<ext>` companions).

### Never do

- Never write outside the adopter's repo root (the directory containing
  `pack.toml` for the operative pack, or the `--output <dir>` target if
  explicitly passed). A path-jail check fences every write call site.
- Never clobber a Tier-2 file (content hash differs from
  `.agent-ready-state.toml`); always emit a `.upstream.<ext>` companion
  instead and let `adapt` or the LLM skill resolve the merge.
- Never touch a Tier-3 file (a path not recorded in
  `.agent-ready-state.toml` under any installed pack's projection).
- Never add a third-party Python dependency. Stdlib only — `tomllib`,
  `argparse`, `hashlib`, `pathlib`, `urllib`, `tarfile`. The sibling
  `distribution-adapters` spec commits to a stdlib-import audit in its build
  (`lint-build.sh` or equivalent); that audit is the structural enforcement
  for this rail — cite it rather than re-implement here.
- Never `subprocess` anything except `gh` for release download. No shelling
  out to `make`, `git`, `diff`, or any other host binary. `git+https://`
  fetch goes through `urllib.request` + `tarfile`, not a `git` subprocess.
- Never invoke an LLM, spawn a Claude session, or call any external
  inference API. The CLI is the deterministic counterpart to LLM skills.
- Never write `.adapt-discovery.toml` from the CLI; the CLI only *reads*
  it (the `adapt-to-project` LLM skill writes it). `<adapt:NAME>` marker
  resolution is the CLI's job (per the sibling `distribution-adapters` spec
  carve-out: `make build --self` resolves markers; adopter installs leave
  markers unresolved for `agentbundle adapt` to consume). Plugin-installed
  pack marker resolution is deferred to the `adapt-to-project` LLM skill;
  out of scope for v1 (RFC-0001 Open Q3).

## Testing Strategy

Each user-visible outcome from the Objective is paired with a mode:

- **Per-subcommand contract — TDD.** Each of the eleven subcommands has a
  contract (inputs, on-disk outputs, exit code, stderr message on failure)
  small enough to pin with a fast unit/integration test. Tests drive the
  implementation; the test asserts on the post-state of a fixture directory
  and on the captured stdout/stderr, not on internal calls.
- **Tier-1/2/3 file-safety invariants — TDD (cross-cutting integration).**
  A single parametrised integration test walks every write-capable
  subcommand (`scaffold`, `install`, `render`, `adapt`, `init-state`,
  `upgrade`, `uninstall`) against the same Tier-1/2/3 fixture and asserts
  the three invariants per command: Tier-1 may change; Tier-2 produces a
  `.upstream.<ext>` companion (original byte-identical); Tier-3 paths are
  byte-identical before and after. The fixture covers both hook extensions
  (`.sh` and `.py`) to pin extension-preservation for `render` and `upgrade`.
- **F-build parity — goal-based check.** A one-liner diffs `agentbundle render
  packs/core --output /tmp/out` against `make build` output for the `core`
  pack; the two outputs must match byte-for-byte. This pins that the CLI uses
  the same render code as F-build (imported as `agentbundle.build`), not a
  fork.
- **Brownfield end-to-end — TDD on fixture + manual QA on a real sandbox.**
  A fixture repo at `packages/agentbundle/tests/fixtures/brownfield/` carries
  pre-existing `AGENTS.md`, `docs/CHARTER.md`, and adopter-owned source files;
  an integration test runs `install` → `adapt --values-from values.toml` →
  `diff` and asserts the resulting tree. The corporate-network sandbox path
  (`gh release download` → `python agentbundle.pyz install`) is **manual QA**
  recorded in the plan because we can't simulate Artifactory + PAT in CI.
- **`zipapp` distribution — goal-based check.** A build step produces
  `dist/agentbundle.pyz`; `python dist/agentbundle.pyz --version` prints the
  CLI version plus the spec version it ships against. Exit 0 is the check.
- **Conformance suite execution — TDD (partial at v1).** `agentbundle
  validate packs/core` runs schema conformance now. `agentbundle validate
  --strict packs/core` runs the conformance fixtures (one per target adapter
  at v0.1) and asserts pass/fail; **behavioural `--strict` is partial at v1
  because the F-conformance fixtures are owned by RFC-0003's deferred
  conformance work** — when fixtures are absent, `--strict` warns and exits
  zero on the schema portion. Full `--strict` lands at v1.1 once
  F-conformance ships.

The typical mix is heavy on TDD because most CLI behaviour is contract-shaped;
`zipapp` distribution and the sandbox round-trip are the goal-based and manual
QA tails respectively.

## Acceptance Criteria

- [ ] `packages/agentbundle/` exists with `pyproject.toml`, `agentbundle/`,
      and `tests/`, following the `packages/_example/` layout. The package
      contains `agentbundle/build/` (F-build library, owned by the sibling
      `distribution-adapters` spec) and the CLI imports it cleanly as
      `import agentbundle.build` — no `sys.path` manipulation, no subprocess
      to `tools/build/build.py`.
- [ ] `python -m agentbundle --version` prints both the CLI version and the
      spec version it ships against (`v0.1` at first release). The spec
      version value is parsed **at import time** from the bundled canonical
      `adapter.toml`'s `[contract] version` field. A test proves the
      read-at-import semantics: it captures the on-disk value, imports the
      package, mutates `adapter.toml` on disk to a different version, then
      asserts that `python -m agentbundle --version` still prints the
      original (import-time) value — not the post-mutation value.
- [ ] All eleven subcommands from RFC-0003 F-cli, in canonical
      install-workflow order (discovery-first: `list-packs`, `list-targets`,
      `scaffold`, `install`, `validate`, `render`, `adapt`, `diff`,
      `upgrade`, `uninstall`, `init-state`), are implemented, each with a
      passing contract test asserting exit code, stdout/stderr, and on-disk
      post-state for at least one happy-path fixture. RFC-0003 enumerates
      the same eleven subcommands in a different (descriptive) order; this
      spec freezes the canonical install-workflow order.
- [ ] `agentbundle render packs/core --output /tmp/out` produces a tree that
      is byte-identical to `make build` output for `packs/core` (F-build parity
      gate). `render` handles all five primitive types (`skill`, `agent`,
      `hook-body`, `hook-wiring`, `command`) and preserves source extensions
      for hook files (`.sh` and `.py`).
- [ ] A single cross-cutting integration test proves the Tier-1/2/3
      invariants hold for every write-capable subcommand (`scaffold`,
      `install`, `render`, `adapt`, `init-state`, `upgrade`, `uninstall`)
      against one shared fixture: Tier-1 may change; Tier-2 paths produce a
      `.upstream.<ext>` companion and the original is unchanged; Tier-3
      paths are byte-identical before and after. The fixture covers both
      `.sh` and `.py` hooks to pin extension preservation.
- [ ] Every write-capable subcommand refuses to write outside the configured
      `--output` / repo root: a fixture pack with a projection rule
      attempting `../../malicious` is rejected with exit non-zero and a
      one-line stderr "refusing to write outside repo root: <path>".
- [ ] `agentbundle install --pack core <catalogue-uri>` at v1 accepts two
      catalogue URI forms: local paths (relative or absolute, e.g.
      `./catalogues/foo` or `/abs/path`) and git over HTTPS
      (`git+https://github.com/<owner>/<repo>[@<ref>]` where `<ref>` is a
      tag, branch, or commit SHA). HTTPS fetch goes through
      `urllib.request` + `tarfile` against GitHub's
      `https://github.com/<owner>/<repo>/archive/...` endpoint (no `git`
      subprocess). Unreachable URLs exit non-zero with a one-line stderr
      naming the tarball URL the CLI tried to fetch. `git+ssh://...` URLs
      exit non-zero with stderr "SSH git URLs deferred to v1.1; use https
      or local path."
- [ ] `agentbundle install --pack <new>` against the brownfield fixture
      leaves all pre-existing adopter files unchanged and drops
      `.upstream.<ext>` companions for every Tier-2 collision. When an
      `.agent-ready-state.toml` already exists (e.g. from a prior `install
      --pack <other>`), the new install **merges**: adds a `[pack.<new>]`
      table without modifying existing `[pack.<other>]` tables.
- [ ] `agentbundle adapt --values-from tests/fixtures/values.toml` resolves
      every `<adapt:NAME>` marker in projected files (the CLI is the
      resolver for adopter installs, per the sibling spec's carve-out),
      writes a `.adapt-pending.md` report listing each `.upstream.<ext>`
      companion with a one-line diff summary, and reads
      `.adapt-discovery.toml` accepted/declined entries without writing to
      it.
- [ ] `agentbundle adapt --ci` exits non-zero whenever any `.upstream.<ext>`
      companion remains on disk (so CI flags pending companions for human
      review). "Resolved" means the companion file no longer exists; the
      `--ci` exits-zero path is verified by a fixture where every companion
      has been removed.
- [ ] `agentbundle upgrade --pack <name> --skill <skill> --to <version>`
      moves only the named primitive; `.agent-ready-state.toml` records the
      resulting mixed-version pack state and subsequent whole-pack upgrades
      surface the mixed state before proceeding. The same flag shape works
      for `--agent`, `--hook`, `--seed`, and `--command`. **Flag-to-primitive
      mapping:** `--skill` → `skill`, `--agent` → `agent`, `--command` →
      `command`, `--seed` → `seeds/` content (not a primitive type per the
      sibling spec, but a movable unit), and `--hook <name>` is atomic over
      the matching `hook-body` (`.apm/hooks/<name>.{sh,py}`) **and** the
      matching `hook-wiring` (`.apm/hook-wiring/<name>.toml`) of the same
      name — wiring co-moves with its body so a per-hook upgrade can never
      land a torn pair. Naming a non-existent primitive (`--skill foo`
      where `foo` isn't in the pack) exits non-zero with one-line stderr
      "primitive 'foo' not in pack <pack>".
- [ ] `agentbundle validate packs/core` exits 0 on schema-valid v0.1
      fixtures and exits 1 with a one-line reason on a schema-invalid
      fixture. `agentbundle validate --strict packs/core` additionally runs
      the v0.1 conformance fixtures **when they exist** (full strict
      behaviour deferred to v1.1 alongside F-conformance from RFC-0003);
      when fixtures are absent, `--strict` warns on stderr and exits zero
      on the schema portion. `validate` checks recipes against the
      six-type enumerated set defined in the sibling `distribution-adapters`
      spec.
- [ ] `dist/agentbundle.pyz` runs end-to-end on a Python 3.11 environment
      with no third-party packages installed (`pip list` shows only stdlib).
      Manual QA in a corporate-network sandbox confirms `gh release download`
      → `python agentbundle.pyz install` works.
- [ ] **Ship-time prerequisite:** the git tag `contract-v<version>` (e.g.
      `contract-v0.1`) exists in this repo's history before
      `dist/agentbundle.pyz` is uploaded as a release asset, so the
      `--version` spec field has a canonical referential anchor in git
      history.
- [ ] `pip list --format=freeze` inside `packages/agentbundle/` lists zero
      runtime dependencies (test-only dev-deps allowed). The sibling
      `distribution-adapters` spec's stdlib-import audit (its build's
      `lint-build.sh` equivalent) provides the structural lint that
      catches drift; cite it here rather than duplicate.
- [ ] `agentbundle.build.adapters` exposes a mapping `name → AdapterModule`
      populated at import time (the `AdapterModule` shape is pinned by the
      sibling `distribution-adapters` spec's registry contract AC). A test
      asserts: `import agentbundle.build.adapters as A; assert isinstance(
      A.registry, Mapping); assert set(A.registry).issuperset({"claude_code",
      "kiro", "copilot", "codex"})`.
- [ ] A version-mismatch fixture (pack declares spec `v2.0`, CLI ships
      `v0.1`) causes every subcommand to refuse with a stderr line naming
      both versions; no partial behaviour observed.
