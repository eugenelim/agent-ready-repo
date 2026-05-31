# Plan: core-install-seed-delivery

- **Spec:** [`spec.md`](spec.md)
- **Status:** Done <!-- Drafting | Executing | Done -->

> **Plan contract:** this is the implementation strategy. Unlike the spec, this
> document is allowed to change as you learn. When it changes substantially
> (a different approach, not just a re-ordering), note why in the changelog
> at the bottom.

## Approach

Six independent-ish slices. The riskiest is the orphan-recovery reshape (T2):
the orphan check runs in install's Step-3 pre-flight (`_classify_pre_rfc0012_state`),
*before* the projection is rendered in Step 7, so to filter orphans by "is this
path in the current projection?" we must make the projection's relpath set
available at check time. Preferred mechanism: compute the repo-scope projection
relpath set once before the Step-3 orphan call and thread it into the check
(fallback: relocate the orphan check to just before Step 9 — but the call-site
comment notes the Step-3 position is load-bearing for the `(b)+--force` stale-row
drop, so prefer threading the set in over moving the check).

Seed delivery (T1) reuses the Tier-1/2/3 loop `scaffold` already has — extract it
to a shared helper so `scaffold` (no state) and `install` (records state +
companions + marker) both call it. Seeds are adapter-independent and repo-scope
only, so delivery slots into Step 9 for the repo-scope plan and never interacts
with the orphan scan (seeds live at repo root / `docs/`, outside the projection
prefixes the scan walks). The build slice (T5) adds `seeds/` to the two per-pack
recipes; `dist/` is gitignored so it's proven by a test, not a committed snapshot.
The marker fix (T4) strips fenced/inline code before the marker regex runs.
Docs + the RFC-0001 erratum (T6) land last, describing the now-true behavior.

## Constraints

- **RFC-0001** §281-284 / §595 — seeds ship inside both the APM package and the
  Claude plugin; this is the never-implemented mapping T5 restores. The
  divergence on "regardless of route" auto-placement is recorded as an
  Approver-signed `## Errata` entry (T6), not a body rewrite.
- **RFC-0008 / RFC-0010 / apm-install-route-parity** — plugin→cache, APM→primitives,
  and the install-marker SessionStart writer touches 3 paths only. No
  session-time seed copy-out (spec Boundary: Never do).
- **RFC-0012** — per-IDE projection + the orphan-recovery feature T2 reshapes.
- File-safety contract — Tier-1/2/3; companions never overwrite adopter edits.

## Construction tests

**Integration tests:**
- Fresh `core` install into a tmp tree lands the seed set and records each seed
  in `.agentbundle-state.toml`, and records no phantom `unresolved-markers`
  (spans T1 + T4; AC1/AC2/AC10).
- Brownfield install over an edited primitive at a projection path yields a
  companion and exits 0 (T2; AC3).

**Manual verification:**
- The brownfield contract (AC3/AC4/AC5) is covered by automated integration
  tests against the **real** `core` pack in a tmp tree
  (`test_install_orphan_reshape.py`, `test_install_seed_delivery.py`) — these
  ARE the inkwell scenario (hand-authored `work-loop/SKILL.md` collision →
  companion, not refusal). **Status: covered by automation.** An end-to-end run
  against the actual `inkwell` repo (`agentbundle install --pack core <clone>
  --output . --scope repo`) remains available as an optional pre-merge user
  confirmation; not a gating artifact.
- Reviewer read README, file-safety-contract, and the RFC-0001 erratum for
  faithful per-route description (T6; AC11/AC12). **Status: done** — adversarial
  review pass clean on the docs surface.

## Tasks

### T1: CLI `install` delivers and state-tracks the pack's seeds

**Depends on:** none

**Tests:**
- `test_install_*`: install `core` into a tmp output (`--scope repo`); assert
  `AGENTS.md`, `docs/CHARTER.md`, `docs/CONVENTIONS.md`, `docs/backlog.md`,
  `docs/specs/README.md`, `docs/architecture/overview.md` land with seed content. (AC1)
- Composition: `_agents-footer.md` is **not** delivered standalone, and the
  delivered `AGENTS.md` contains the footer line (`AGENTS.local.md` reference). (AC1b)
- Assert `.agentbundle-state.toml` records each delivered seed relpath under
  `core`'s `files` map with `{sha, from-pack-version}`. (AC2)
- Seed collision: pre-create an edited `docs/CHARTER.md`; install drops
  `docs/CHARTER.upstream.md`, leaves the original byte-unchanged. (AC1 Tier-2)
- `.gitignore` collision (highest-probability brownfield case): pre-create a
  repo-root `.gitignore`; install drops `.gitignore.upstream`, original byte-unchanged. (AC1 Tier-2)
- Identical seed present → skipped, no companion. (AC1 Tier-1)
- No-footer pass-through: a seed-bearing pack with no `_agents-footer.md` delivers
  `AGENTS.md` unchanged (body only) — the compose step is guarded on footer existence.
- Regression: `test_scaffold_cmd.py` still green — `scaffold` delivers seeds and
  does **not** write `.agentbundle-state.toml`. **Add `_agents-footer.md` to the
  `tests/fixtures/scaffold/test-pack/seeds/` fixture** (it has none today, so the
  current test can't exercise compose/skip) and update `_seed_contents`/assertions
  to expect a composed `AGENTS.md` + no standalone `_agents-footer.md` — so the
  scaffold path actually exercises the helper's new behavior.

**Approach:**
- Extract `scaffold.run`'s per-seed Tier loop (`scaffold.py:56-81`) into a shared
  helper (`commands/_common.py`) returning structured records `(relpath, content,
  tier, companion_relpath|None)`; `scaffold` consumes them for its prints, install
  records state.
- The helper **skips `_`-prefixed composition fragments** from standalone delivery
  and **composes `AGENTS.md`** as body + `_agents-footer.md` footer (mirror the
  concatenation in `build/self_host.py:_compose_agents_md:268-281`, minus the
  self-host `EXCLUDED_PATTERNS` gate — Tier classification handles the on-disk
  collision here). Compose the footer **only when `_agents-footer.md` exists**
  (guard as `build/self_host.py:273` does); a footer-less pack passes `AGENTS.md`
  through unchanged. The composed bytes are the "incoming content" the Tier
  comparison uses for `AGENTS.md`.
- Seed writes use the **bare under-root jail** — call `write_jailed`/`write_companion`
  with no `scope`/`allowed_prefixes` (seeds land at repo root / `docs/`, outside the
  adapter prefixes; passing prefixes would raise `PathJailError`). This is how
  `scaffold` already calls them.
- In `install.run` Step 9, for the **repo-scope** plan only and when
  `pack_dir/seeds/` exists, call the helper against `plan.root`; for each record
  set `new_pack_state.files[relpath] = {sha, from-pack-version}`, and append any
  companion to `plan.new_companions` so the marker + `adapt-to-project` see it.
- Mirror the existing primitive Tier-2 state semantics (record incoming-bundle SHA)
  — do not change that semantics here (spec Ask-first).

**Done when:** AC1, AC1b, AC2 cases pass and the `scaffold` regression is green.

### T2: First-install over projection-path files companions instead of refusing/deleting

**Depends on:** none

**Tests:**
- Brownfield, no state: pre-create an **edited** `.claude/skills/work-loop/SKILL.md`;
  install `core` → `.claude/skills/work-loop/SKILL.upstream.md` companion, original
  unchanged, exit 0, no refusal. (AC3)
- Pre-create an **identical** `SKILL.md` → clean Tier-1 no-op, no companion, exit 0. (AC4)
- Pre-create a file under a shipped-primitive dir that is **not** in the current
  projection (e.g. `.claude/skills/work-loop/STALE-EXTRA.md`), no state → orphan
  guard still fires: refuse without `--force`, removed with `--force`. (AC5)
  (Reachable: the scan keys off the current pack's primitive *names* — `work-loop`
  matches the segment — but the file isn't a projected relpath, so the filter keeps it.)
- Assert the refusal message no longer states "prior install interrupted" as fact. (AC6)
- Assert the early-computed projection relpath set key-matches the Step-7
  projection for a multi-adapter pack (no drift between the two render points).

**Approach:**
- Render the repo-scope projection relpath set **once** before the Step-3 orphan
  call, **reusing the already-resolved `repo_target_adapter`** (`install.py:342`, not
  a re-resolve) via `_render_for_repo_scope` so the early set is byte-identical to the
  Step-7 projection; thread the set into `_classify_pre_rfc0012_state` and reuse the
  same projection at Step 7 (render once, not twice). Drop any orphan whose
  relative-to-`output_root` path is in that set (those are companion-protected by
  Step 9, not orphans). Fallback if an early render proves infeasible: relocate the
  orphan check to just after Step 7, preserving the `(b)+--force` stale-row-drop ordering.
- Reword the refusal message (`install.py:1473-1481`): describe the files as
  "unrecognized files at projection paths not shipped by pack <name> — leftover
  from an older/interrupted install, or your own files; rerun with `--force` to
  remove them, or move them aside" (no false "prior install interrupted").
- `--force` keeps unlinking the (now correctly narrowed) genuine orphans.

**Done when:** AC3-AC6 tests pass; the Finding-2 repro no longer refuses.

### T3: `--force` help text documents orphan/file removal

**Depends on:** none

**Tests:**
- Goal-based: assert the `install --force` help string mentions that `--force`
  removes on-disk orphan files (not only the cross-scope-conflict bypass). (AC7)

**Approach:**
- Amend the `--force` help in `cli.py:222-231` to add the orphan-cleanup clause;
  drop/qualify the now-misleading "Does not override the in-place re-install
  refusal" framing so it's consistent with the runtime message.

**Done when:** AC7 test passes; `agentbundle install --help` reads consistently
with the runtime orphan message.

### T4: `_collect_unresolved_markers` ignores markers inside code

**Depends on:** none

**Tests:**
- Unit: marker inside inline-code (`` `<adapt:name>` ``) → not collected. (AC9)
- Unit: marker inside a fenced ```` ``` ```` block → not collected. (AC9)
- Unit: a live (non-code) `<adapt:project>` → still collected. (AC9)
- Integration: fresh `core` install records no `unresolved-markers`. (AC10)

**Approach:**
- In `_collect_unresolved_markers` (`install.py:~1587`), strip fenced code blocks
  then inline-code spans from each file's text before running the marker regex.

**Done when:** AC9 unit cases + AC10 integration pass.

### T5: Build ships `seeds/` inside the APM and Claude-plugin artifacts

**Depends on:** none

**Tests:**
- New build-pipeline test (in `build/tests/`): run the per-pack APM recipe against
  a seed-bearing fixture pack and assert its `seeds/` content is present under
  `dist/apm/<pack>/seeds/`. (Not a mirror of `test_scaffold_copies_seeds_into_output`,
  which exercises the `scaffold` *command*, not these recipes.)
- Same for the Claude-plugin recipe (`_run_per_pack_single`) → `dist/claude-plugins/<pack>/seeds/`. (AC8)

**Approach:**
- In `_run_per_pack_single` (`main.py:365-419`, plugin; authority RFC-0001 §281-284)
  and `_run_per_pack_apm` (`main.py:422-473`, APM; authority RFC-0001 §595),
  `copytree(pack.path/"seeds", per_pack_output/"seeds", symlinks=True)` when the
  source `seeds/` exists, after the existing `.apm/` / pack.toml copies. Match the
  `symlinks=True` exfiltration guard already used.

**Done when:** AC8 tests pass for both recipes.

### T6: Docs + Approver-signed RFC-0001 erratum

**Depends on:** T1, T2, T5

**Tests:**
- Goal-based: `make build-check` doc-drift gate (`tools/lint-spec-status.py`) green.
- Manual QA: reviewer confirms README "Where primitives land"/install sections and
  `docs/guides/explanation/file-safety-contract.md` describe per-route seed delivery
  faithfully (artifact carries seeds on every route; working-tree landing is
  automatic on CLI, via `scaffold`/`adapt` on plugin/APM). (AC11)
- Manual QA: RFC-0001 `## Errata` entry present, easy to read, Approver-signed. (AC12)

**Approach:**
- Add a short, plainly-worded `## Errata` section to RFC-0001 (Approver: eugenelim,
  2026-05-30): §595's seed mapping is now implemented; §281-284's "regardless of
  route the adopter ends up with the layout in their repo" holds automatically only
  for the CLI route — plugin/APM ship seeds in the artifact, landed via the CLI
  `install`/`scaffold`/`adapt`, per RFC-0008/0010 cache mechanics.
- Reconcile README + file-safety-contract wording to match (no claim that
  `/plugin install` or `apm install` auto-place governance docs in the working tree).

**Done when:** AC11/AC12 hold; doc-drift gate green; reviewer clean.

## Rollout

Bug fix to the `agentbundle` CLI + build pipeline. No flag; ships in the next
release. Reversible by revert. No data migration. Existing installs are
unaffected until they re-run `install`/`upgrade`; new installs get seeds.

## Risks

- **T2 projection-availability** — if the repo projection can't be cheaply
  computed before the Step-3 orphan call, fall back to relocating the orphan
  check after Step 7 (carefully preserving the `(b)+--force` stale-row-drop
  ordering). Re-evaluate the structural-change trigger if the fallback grows.
- **Seed marker scanning is a deliberate non-goal with no tracked successor** —
  install does not scan delivered seeds for live `<adapt:NAME>` markers. Verified
  no `core` seed carries one today (`grep '<adapt:' packs/core/seeds/` → empty), and
  install never scanned seeds before, so nothing regresses. Not deferred (no AC
  carries a `(deferred:)` token); if a future pack ships a seed with a live marker,
  that pack's spec owns adding the scan.
- **Helper extraction** touches `scaffold` — covered by the `scaffold` regression
  test so its no-state behavior can't drift.

## Changelog

- 2026-05-30: initial plan.
- 2026-05-30 (during EXECUTE): T2 renders the projection **twice** (once at
  Step-3c for the orphan-filter relpath set, once at Step 7) rather than
  caching one render across ~300 lines of `run()`. Both renders are
  deterministic from identical inputs so they key-match (the planned
  invariant holds); a second in-memory render of a ~30-file pack is negligible
  and avoids threading a cached projection through the intervening steps. The
  Step-3c render is best-effort — on failure the orphan filter degrades to off
  and Step 7 surfaces the canonical render error.
