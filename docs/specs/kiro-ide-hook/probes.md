# kiro-ide-hook v0.4 ship-gate probes

Per RFC-0005 § *Gating verifications before contract version 0.4
ships*, two probes against a real Kiro install must complete before
`adapter.toml`'s `[contract] version` writes `"0.4"`. This file
records the outcomes; the `adapter.toml` declaration follows the
recorded values in T-CONTRACT.

## Q6 — recursion + extension filter

Two independent runtime properties gate the `target.repo` string:

- **Recursion:** does Kiro recurse into `.kiro/hooks/<subdir>/`?
- **Extension filter:** does Kiro glob `*.kiro.hook` only, or does
  it parse every file regardless of extension?

The 2×2 decides the projection layout (RFC-0005 § Unresolved Q6
verbatim):

| Recursion | Extension filter | Projection layout |
|---|---|---|
| yes | yes | `kiro-ide-hook`: `.kiro/hooks/<pack>/<name>.kiro.hook` (RFC lean). `hook-body`: unchanged. |
| yes | no  | `kiro-ide-hook`: `.kiro/hooks/<pack>/<name>.kiro.hook`. `hook-body` cross-primitive relocation: user-scope target moves from `.kiro/hooks/<pack>/` to `.kiro/hook-bodies/<pack>/`. **T-E1b fires.** |
| no  | yes | `kiro-ide-hook`: `.kiro/hooks/<pack>--<name>.kiro.hook` (flat-with-prefix). `hook-body`: unchanged. |
| no  | no  | Same as `no × yes` — top-level read only, extension filter is moot. |

### Probe protocol

Scaffolding under [`.context/probes/kiro/probe-workspace/`](../../../.context/probes/kiro/probe-workspace/)
(gitignored). Three canary files plus a workspace README:

- `.kiro/hooks/canary-flat.kiro.hook` — `fileSave` askAgent at the
  top level.
- `.kiro/hooks/subdir/canary-nested.kiro.hook` — same shape inside
  `subdir/`. Fires alongside flat ⇒ recursion = yes.
- `.kiro/hooks/canary-other.txt` — same payload, wrong extension.
  Fires alongside flat ⇒ extension filter = no.

The operator opens the workspace in Kiro (`kiro -n
/path/to/probe-workspace`), saves any file inside it, and observes
which canaries fire from Kiro's hook UI. Each canary's prompt
carries a distinct ALL-CAPS marker (`PROBE_FLAT_FIRED`,
`PROBE_NESTED_FIRED`, `PROBE_OTHER_EXTENSION_FIRED`) so the
operator can read off the result unambiguously.

### Outcome

> **Not yet run.** This row is the surface-to-operator gate. The
> operator opens the workspace in Kiro, drives a fileSave, and
> records observations below.

- **Recursion observed:** _<yes | no>_  ← fill in
- **Extension filter observed:** _<yes | no>_  ← fill in
- **2×2 quadrant:** _<yes-yes | yes-no | no-yes | no-no>_
- **Canonical `target.repo` string for `adapter.toml`:**
  _<filled in once the quadrant is known>_
- **Cross-primitive `hook-body` retarget (T-E1b) fires?**
  _<yes if `yes × no` quadrant, otherwise no>_
- **Date of observation:** _<YYYY-MM-DD>_
- **Kiro version observed:** _<e.g. 0.2.13 — `kiro --version`>_

## Q11 — vocabulary fixture

RFC-0005 § Unresolved Q11 — Kiro's published docs expose
human-readable labels ("File Save", "Prompt Submit") but the actual
`when.type` string the JSON file carries is not in the published
reference. The canonical strings must come from at least one
IDE-UI-authored fixture.

### Probe protocol

1. Open the Kiro IDE.
2. Use the hook-author UI to create one askAgent-shaped hook (any
   trigger).
3. If the UI exposes runCommand-shaped hooks too, author one of
   those.
4. Save each. Locate the `.kiro.hook` file Kiro wrote (likely
   under the active workspace's `.kiro/hooks/`).
5. Copy each into
   `packages/agentbundle/tests/fixtures/kiro_ide_hook/captured/`.
6. Read off the canonical `when.type` and `then.type` strings and
   record them below.

### Floor

Per RFC-0005 Q11: "at least one IDE-UI-authored `.kiro.hook` file
as a fixture" is the floor. Preferred — one of each action type
(`askAgent` + `runCommand`) if the UI exposes both in the
operator's installed Kiro version. If only one action type is
reachable, document the gap here so the conformance suite knows
which paths skip.

### Outcome

> **Not yet run.** This row is the surface-to-operator gate.

- **Captured fixture(s):** _<list filenames under `tests/fixtures/kiro_ide_hook/captured/`>_
- **Canonical `when.type` strings observed:** _<comma-separated list>_
- **Canonical `then.type` strings observed:** _<comma-separated list>_
- **`ide-event-vocabulary` to declare in `adapter.toml`:**
  _<probe-pinned list — superset of the captured `when.type` values plus any documented event names from Kiro's reference; see RFC § Pack-side source for the working list>_
- **`ide-action-vocabulary` to declare in `adapter.toml`:**
  _<at minimum `["askAgent", "runCommand"]` if both reachable; otherwise document the gap>_
- **Date of observation:** _<YYYY-MM-DD>_
- **Kiro version observed:** _<e.g. 0.2.13>_

## When both probes complete

1. Edit `packages/agentbundle/agentbundle/_data/adapter.toml`:
   bump `[contract] version` to `"0.4"`, add the
   `[primitive."kiro-ide-hook"]` table, add the
   `[adapter.kiro.projections.kiro-ide-hook]` table with the
   probe-pinned `target.repo` and vocabulary values, add the
   explicit `mode = "dropped"` rows for claude-code / codex /
   copilot.
2. Mirror to `docs/contracts/adapter.toml`.
3. Bump `pack.schema.json`'s `adapter-contract.version` enum to
   include `"0.4"`. Mirror to `docs/contracts/pack.schema.json`.
4. Add `"kiro-ide-hook"` to `adapter.schema.json`'s
   `primitive.required` array. Mirror to `docs/contracts/`.
5. If Q6 lands the `yes × no` quadrant, also retarget
   `[adapter.kiro.projections.hook-body].target.user` to
   `.kiro/hook-bodies/<name>.{sh,py}` in lockstep (T-E1b).
6. Re-run `make build-check` / the test suite; verify the
   pre-existing v0.3 contract tests still pass and the new v0.4
   conformance cases pass.
7. Flip T-CONTRACT's ACs to `[x]` in
   [`docs/specs/distribution-adapters/spec.md`](../distribution-adapters/spec.md)'s
   § *Acceptance Criteria*.
8. Land T-F (ADR) and finalise T-G (ROADMAP) entries.
