# Spec: core-install-seed-delivery

- **Status:** Shipped <!-- Draft | Approved | Implementing | Shipped | Archived -->
- **Owner:** eugenelim
- **Plan:** [`plan.md`](plan.md)
- **Constrained by:** RFC-0001 (seed-delivery contract + build pipeline), RFC-0008 (Claude-plugin cache mechanics), RFC-0010 (APM HookIntegrator), RFC-0012 (per-IDE projection + orphan-recovery)

> **Spec contract:** this document defines what "done" means. The implementing
> PR must match this spec, or update it. Verification must be derivable from it.

## Objective

Fix issue #190: an adopter who installs the `core` pack the documented way
must actually receive the pack's governance **seeds** (`AGENTS.md`,
`docs/CHARTER.md`, `docs/CONVENTIONS.md`, and the rest of `seeds/`), and a
brownfield install over hand-authored files must **never delete them** — it
drops `*.upstream.<ext>` companions exactly as the file-safety contract
promises.

Today `agentbundle install` projects only `.apm/` primitives and never touches
`seeds/`; the dist build never copies `seeds/` into the APM or Claude-plugin
artifacts either; a first install over pre-existing files at projection paths
is misclassified as an interrupted-install "orphan" and the only escape
(`--force`) `unlink()`s the adopter's files with no companion; and a fresh
install records a phantom `unresolved-markers = ["name"]` sourced from a
documentation example.

Success: across all four install routes the artifact **carries** the pack's
seeds (per RFC-0001 §595/§281); the CLI route **lands and state-tracks** them
with Tier-1/2/3 safety; brownfield collisions land as companions, not
deletions; `--force`'s file-removing behavior is documented; the phantom
marker is gone; and the docs + an Approver-signed RFC-0001 erratum describe
per-route seed delivery honestly. The fix lives entirely in the
agent-agnostic CLI, build pipeline, and docs — it works outside Claude.

## Boundaries

The three-tier guard that keeps an implementing agent inside the lines.
*Always do* applies without asking; *Ask first* requires human sign-off
before proceeding; *Never do* is a hard rule, even under time pressure.

### Always do

- Route every seed write through `safety.write_jailed` / `safety.write_companion`
  using the **bare under-root jail** (no `allowed_prefixes` — seeds land at the
  repo root and `docs/`, outside the adapter projection prefixes), mirroring the
  Tier-1/2/3 logic `scaffold` already uses.
- Honour the composition-fragment convention (`CONVENTIONS.md` §Pack
  source-of-truth split): files whose names start with `_` (e.g.
  `_agents-footer.md`) are **not** delivered standalone; `AGENTS.md` is delivered
  as the body seed composed with the `_agents-footer.md` footer.
- Keep seed delivery **adapter-independent and harness-neutral** — seeds are
  verbatim governance docs, identical for Claude Code / Codex / Copilot / Kiro.
- Preserve the existing file-safety guarantee: an adopter-edited file at a
  collision path is left untouched and gets a `*.upstream.<ext>` companion.
- Record delivered seeds in `.agentbundle-state.toml`'s `files` map (same shape
  as primitives) so upgrades give edited seeds Tier-2 companion safety.
- Cover the build-pipeline change with a test that builds a pack and asserts
  seeds land in the output (`dist/` is gitignored — not a committed snapshot).

### Ask first

- Any change to the *behavior* of the orphan-recovery feature beyond the
  narrow reshape this spec authorizes (filter by current projection + reword).
- Changing the recorded-SHA semantics for Tier-2 files (the existing primitive
  behavior records the incoming-bundle SHA; seeds mirror it — don't "fix" it here).
- Extending seed delivery to user scope (core is repo-only; seeds-bearing packs
  are repo-scope by Rail A — out of scope).

### Never do

- **No new top-level directory and no new runtime dependency** — the fix is
  contained to existing `agentbundle` modules, build pipeline, seeds, and docs.
- Never `unlink()` or overwrite a file that exists at a path the **current
  projection** ships — that path is companion-protected, not an orphan.
- Never make seed delivery or any new hook copy files at adopter *session*
  time (the install-marker writer's 3-path Never-do, `apm-install-route-parity`
  spec, stays intact) — that auto-copy design is explicitly out of scope (an
  RFC if ever wanted).
- Never silently edit a frozen Accepted RFC — RFC-0001 changes land as an
  Approver-signed `## Errata` entry, not a body rewrite.

## Testing Strategy

- **B1 CLI seed delivery + state-tracking** — **TDD.** Integration test: install
  `core` into a tmp tree; assert the seed files land (with `AGENTS.md` composed
  from body+footer and `_agents-footer.md` absent) and each delivered seed is
  recorded in `.agentbundle-state.toml`. Logic with a checkable invariant.
- **B2 first-install companion / orphan reshape** — **TDD.** Unit + integration:
  a pre-existing *edited* file at a projection path yields a `*.upstream.<ext>`
  companion and no refusal; a pre-existing *identical* file is a clean Tier-1
  no-op/overwrite; a file under the prefix that is **not** in the current
  projection still triggers the (reworded) orphan guard.
- **B3 `--force` help text** — **goal-based.** Assert the help string names the
  orphan-cleanup/file-removal behavior.
- **B4 orphan message wording** — **TDD.** Assert the reworded message no longer
  asserts "prior install interrupted" as fact.
- **B5 build ships seeds in artifacts** — **TDD.** A build-pipeline test that
  runs the per-pack APM and Claude-plugin recipes against a seed-bearing pack and
  asserts `seeds/` content is present in each per-pack dist output.
- **B6 phantom-marker fix** — **TDD.** Unit test on `_collect_unresolved_markers`:
  a marker inside inline-code / a fenced block is **not** collected; a live
  marker is. Plus an install assertion that a fresh `core` install records no
  phantom `unresolved-markers`.
- **B7 docs + erratum accuracy** — **goal-based + manual QA.** `tools/lint-spec-status.py`
  / doc-drift invariants hold; reviewer confirms README, file-safety-contract,
  and the RFC-0001 erratum describe per-route seed delivery faithfully.

## Acceptance Criteria

- [x] **AC1** `agentbundle install --pack core <catalogue> --output <dir> --scope repo`
      writes the pack's `seeds/` content into `<dir>` with Tier-1/2/3 safety
      (absent → write; identical → skip; adopter-edited → `*.upstream.<ext>` companion).
- [x] **AC1b** `_`-prefixed composition fragments are **not** delivered standalone:
      `_agents-footer.md` is absent from `<dir>`, and the delivered `AGENTS.md` is
      the body seed composed with the footer (the footer's content is present in `AGENTS.md`).
- [x] **AC2** Each seed file the CLI delivers is recorded in
      `<dir>/.agentbundle-state.toml` under the installing pack's `files` map
      (same `{sha, from-pack-version}` shape as primitives).
- [x] **AC3** A first install (no prior state) over a pre-existing **edited**
      file at a current-projection path drops a `*.upstream.<ext>` companion,
      leaves the adopter's file byte-unchanged, and exits 0 — no orphan refusal.
- [x] **AC4** A first install over a pre-existing **identical** file at a
      current-projection path is a clean no-op for that file (no companion, no refusal).
- [x] **AC5** A pre-existing file under a projection prefix that is **not** in
      the current projection still triggers the orphan guard; with `--force` it
      is removed, without `--force` the install refuses.
- [x] **AC6** The orphan refusal message no longer asserts "prior install
      interrupted" as fact; it acknowledges the files may be adopter-authored.
- [x] **AC7** `agentbundle install --help` documents that `--force` can remove
      on-disk orphan files (not only the cross-scope-conflict bypass).
- [x] **AC8** The per-pack APM (authority: RFC-0001 §595) and Claude-plugin
      (authority: RFC-0001 §281-284 prose) build recipes copy each pack's `seeds/`
      into `dist/apm/<pack>/seeds/` and `dist/claude-plugins/<pack>/seeds/`, proven
      by a build-pipeline test that runs the per-pack recipes and asserts the seeds
      are present in both per-pack outputs (`dist/` is gitignored — verified by test, not snapshot).
- [x] **AC9** `_collect_unresolved_markers` does not collect a `<adapt:NAME>`
      token that appears inside inline-code or a fenced code block; it still
      collects a live (non-code) marker.
- [x] **AC10** A fresh `core` install records no phantom `unresolved-markers`
      entry — the leaking token is the inline-code `<adapt:name>` in the
      `adapt-to-project` SKILL.md, a **projected primitive** (independent of seed
      delivery), so the fix lives in the marker scanner (T4), not T1.
- [x] **AC11** README "Where primitives land" / install sections and
      `docs/guides/_shared/explanation/file-safety-contract.md` accurately state that the
      artifact carries seeds on every route while the working-tree landing is
      automatic on the CLI route and via `scaffold`/`adapt` on plugin/APM.
- [x] **AC12** RFC-0001 carries an Approver-signed `## Errata` entry recording
      that §595's mapping is now implemented and §281-284's "regardless of route"
      auto-placement is CLI-route-only (plugin/APM ship-in-artifact + CLI/scaffold landing).

## Assumptions

- Technical: `install.py` has zero `seeds/` references; only `scaffold.py` delivers seeds and deliberately does not write state (source: `packages/agentbundle/agentbundle/commands/scaffold.py:11-12,56-81`).
- Technical: `_classify_for_install` already returns Tier-2→companion for on-disk-differs-no-recorded-SHA, so Step-9 already drops first-install companions; the bug is the Step-3c orphan check refusing first (source: `packages/agentbundle/agentbundle/commands/install.py:2671-2691` and `:1424-1482`).
- Technical: `scan_for_pack_artifacts` flags any pre-existing file matching a pack-primitive name and does not filter against the current projection (source: `packages/agentbundle/agentbundle/safety.py:451-544`).
- Technical: the phantom marker is the literal `<adapt:name>` documentation example matched by the marker regex (source: `packs/core/.apm/skills/adapt-to-project/SKILL.md:154`, `install.py:_collect_unresolved_markers`).
- Technical: the build never copies `seeds/` into either dist artifact; RFC-0001 §595 specified `seeds/ → seeds/` for APM but it was never implemented (source: `packages/agentbundle/agentbundle/build/main.py:365-419,422-473`; `docs/rfc/0001-...md:595`).
- Technical: plugin→managed cache, APM→primitives-only projection; the install-marker SessionStart hook touches 3 paths only and is forbidden from copying files (source: `docs/specs/apm-install-route-parity/spec.md:331-336`; `packages/agentbundle/templates/install-marker.py`).
- Technical: runtime is Python >=3.11 (source: `packages/agentbundle/pyproject.toml:9`).
- Process: RFC-0001 is Accepted/frozen (closed 2026-05-22), so diverging from §281-284 requires an Approver-signed `## Errata` entry (source: `docs/rfc/0001-...md:3`; user confirmation 2026-05-30).
- Process: `dist/` is gitignored (`.gitignore:42`) — build artifacts are not committed, so the build change is verified by test; `make build` runs inside `make build-check` (`Makefile:72`) (source: verified during planning).
- Product: Option 2 chosen (ship-in-artifact + CLI/scaffold landing + erratum); seeds state-tracked in the same `files` map; phantom-marker fix ignores code-fenced markers; fix must work outside Claude (source: user confirmation 2026-05-30).
