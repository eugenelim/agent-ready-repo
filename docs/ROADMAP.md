# Roadmap — open items by spec

Single index of open work across every spec in `docs/specs/`. Each open
item names the spec, the Acceptance Criterion (where one applies),
what's blocking it, and how it gets unblocked.

This file is governance about *this repo's* evolution, not adopter
scaffolding. The adopter-facing product roadmap template lives at
[`product/roadmap.md`](product/roadmap.md) (a *Projected* path
sourced from `packs/core/seeds/`). This file is per-instance: it lives
on disk here, has no pack-side source, and surfaces as an `[info]`
line under `make build-check` per AC6 of the self-hosting spec.

For shipped work, see [`product/changelog.md`](product/changelog.md)
and each spec's own Changelog section.

**Last updated:** 2026-05-25 (later same day: closed the AC22 install-route coverage extension follow-on under `self-hosting` as moot — `make build` confirmed neither the `per-pack-claude-plugin` nor the `per-pack-apm-package` recipe projects a `dist/<route>/<pack>/seeds/` subtree and the install→adapt chain never invokes `scaffold`, so the route axis was empty by construction; AC22 wording rescoped single-route in the spec, paired RFC-0002 § Amendments entry added, cross-source invariant remains enforced by AC21's `tools/lint-seeds.py`. Earlier today: added `apm-install-route-parity` — Approved → Shipped after T1-T12 implementation via work-loop in a single session; canonical install-marker writer now serves both claude-plugins and APM routes via a required `--install-route` argparse flag, build pipeline projects matching artifacts under `dist/apm/<pack>/.apm/hooks/`, contract bumped v0.4 → v0.5 with `"apm"` on `[adapter."claude-code"].install-routes`, sibling specs amended in-PR for AC1 allow-list / AC9 hook command / AC27 stale-entry drop / `per-pack-apm-package` recipe note / `apm-route conformance` AC; live-install transcripts at three targets (Copilot, Cursor, Gemini) deferred per AC17's manual-QA matrix rows with `verification = transcript`, gated on adopter availability rather than on the PR. Mid-EXECUTE Cohort C surfaced a pre-existing drift in `tools/hooks/pre-pr.py` vs `packs/core/.apm/hooks/pre-pr.py` from PR #111 — projection had `lint-skill-spec` but source did not; closed the drift in-PR by adding the same `lint-skill-spec` line to the source pack hook so `make build-self` produces a stable projection.) Earlier today: added `kiro-ide-hook` — Draft, sibling of `user-scope-hooks` covering RFC-0005's third hook surface (Kiro standalone `.kiro.hook` files for IDE events); new `kiro-ide-hook` primitive, contract bumps `0.3 → 0.4`; non-probe tasks A/B/C1-4/D1/G land in-session, T-CONTRACT gated on Q6 / Q11 probes against real Kiro install, T-F ADR carries bullets (a)+(b) from RFC § Follow-on artifacts; the RFC-text drift on uninstall semantics in § State-file impact is recorded as a deferred follow-up. Earlier today: shipped `wire-session-start-hook` — Approved → Shipped after T1-T7 implementation via work-loop; PR #98 also fixed a latent `self_host.py` drift-loop bug uncovered by CI (`diff_against_working_tree` now consults `EXCLUDED_PATTERNS` the same way the unclassified-path enumeration does). Mid-EXECUTE the spec was amended to correct AC1/AC2/AC3/AC9/AC10 paths from flat to dist-tree shape after work-loop discovered repo-scope install produces `<output>/claude-plugins/<pack>/...`, not the flat shape the original spec assumed. Kiro support deferred to a parallel spec that needs a new `steering` primitive. Earlier today: closed `skill-secrets` — all T1–T13c shipped; status flipped Draft → Shipped; round-1 end-of-spec review fixes landed via PRs #81/#82/#83; round-2 review-pass follow-ons (windows-latest CI matrix, AC22 macOS symbolic exit-code matrix, `CredentialsMissingError` tier observability, robustness pass, lint widening) landed as separate focused PRs. AC34/AC35 inheritance invariants and the post-implementation "Credential storage" ADR remain as cross-spec items.)

## How this file is maintained

- Every spec records its own `Status:` field and `Acceptance Criteria`
  checkboxes. This file aggregates the open items so they're visible in
  one place — it is not the source of truth.
- When a spec ships or an AC closes, update the spec first, then update
  the relevant entry here in the same PR.
- When a new spec lands, add a section for it here even if every AC is
  open (so the file stays a complete index).
- If an item here is no longer accurate against the underlying spec,
  trust the spec and fix this file.

---

## `self-hosting` — shipped (Phase 1 + Phase 2 + 2026-05-25 amendment closed)

Spec: [`specs/self-hosting/spec.md`](specs/self-hosting/spec.md).
Phase 1 cutover landed via PR #18; AC3 closed by PR #20; AC1b artifact
recorded via PR #21. AC8 (`AGENTS.md` composition) closed by the
2026-05-23 Codex multi-pack aggregation pass. Phase 2's comparison-rule
strengthening — CRLF→LF normalisation for text-like files, file-mode
permission-bit comparison for regular files, and symlink-target
comparison via `lstat` (never following) — closed by PR #34. The
2026-05-25 amendment (RFC-0002 § Amendments § 2026-05-25; PR #112) and
its implementation closed AC9 (superseded) plus AC18-AC23: seed
scaffold leak closure, override shrink, seed-content lint, first-install
snapshot test, APPROACH→CHARTER fold-in.

Open follow-ons (not gating this spec):

- ~~**AC22 install-route coverage extension.**~~ Closed as moot
  2026-05-25 (paired with the AC22 rescope amendment): `make build`
  confirmed that neither the `per-pack-claude-plugin` nor the
  `per-pack-apm-package` recipe projects a `dist/<route>/<pack>/seeds/`
  subtree, and the install→adapt chain (`install` → in-process `adapt`)
  never invokes `scaffold`. Seed projection is route-agnostic by
  construction — only `agentbundle scaffold` drops `packs/<pack>/seeds/`
  — so per-route snapshots would have been three runners ending at the
  same code path. AC22 wording rescoped to single-route; the cross-route
  invariant is enforced at the source by AC21's `tools/lint-seeds.py`,
  which scans every `packs/<pack>/seeds/` tree for the catalogue-leak
  blocklist. A future RFC that wires seed projection into the
  Claude-plugins or APM routes would re-open this item; until then
  there is no route axis to cover.
- ~~**AGENTS.md footer attribution rewording.**~~ Closed in the same
  PR as the 2026-05-25 amendment implementation (per direction during
  EXECUTE): the trailing *"Generated from the `agent-ready-repo`
  template…"* line was removed from both `packs/core/seeds/AGENTS.md`
  and the projected root `AGENTS.md`.

## `distribution-adapters` — shipped (v0.2 contract bump landed)

Spec: [`specs/distribution-adapters/spec.md`](specs/distribution-adapters/spec.md).
Shipped via the build-pipeline PRs that introduced
`packages/agentbundle/agentbundle/build/` and the four reference
adapters. The [RFC-0004](rfc/0004-install-scope-per-pack.md) v0.2
amendment (install-scope dimension; `[scope]` table on the adapter
contract; `[pack.install]` table on `pack.toml`; user-scope refusal
rails A/B/C; state-file v0.2 + `init-state --migrate`; four shipped
packs declare `[pack.adapter-contract] version = "0.2"`) landed in
the same PR; ACs #14–#18 are satisfied. The AC21 carve-out (code-side
Rail-C grep widening to the canonical lowercase-hyphen form) closed
by PR #33: `_MARKER_REGEX` in `agentbundle.build.scope_rails` now
accepts both legacy UPPER_SNAKE and canonical lowercase-hyphen
grammars via alternation. No open items.

## `agent-spec-cli` — shipped (v0.2 CLI surface landed)

Spec: [`specs/agent-spec-cli/spec.md`](specs/agent-spec-cli/spec.md).
Shipped via PR #23 (commit `cd4f3e5`) — 11 subcommands, library-first
CLI importing `agentbundle.build`. The
[RFC-0004](rfc/0004-install-scope-per-pack.md) v0.2 amendment
(argparse `--scope` on six subcommands + `--force` on `install`;
scope-resolution helper; path-jail per scope; `~`-expansion refusal;
v0.1 state-file refuse-and-explain at write; dual-scope install
conflict + `installed: <pack> @ <scope>` rail; `recommends`
cross-scope warning text split; `adapt` dual-state-file walk) landed
in the same PR; the ten `(RFC-0004)`-tagged ACs are satisfied.

- **Deferred to a follow-up RFC** (called out in RFC-0004 itself, not
  net-new scope): user-scope hook-wiring merge story (Rail B keeps
  hook-bearing packs user-scope-refused until that lands); `global`
  (system-wide) scope (not reserved, not refused — absent); new
  user-scope packs (the dimension lands without a consumer).
- **Deferred to v1.1** (carried over from the prior roadmap entry):
  SSH git URL support in `install` (`git+ssh://...` currently exits
  non-zero with a "deferred to v1.1" message); the full `--strict`
  `validate` behaviour against the v0.1 conformance fixtures (which
  themselves are owned by RFC-0003's deferred F-conformance task).
- **Tier-2 upgrade prompt — v0.1 ships companion-drop only.**
  RFC-0001 § *Adopter file safety contract* § *Tier-2 behaviour on
  detection* specifies a three-option in-CLI prompt on `agentbundle
  upgrade` Tier-2 collisions (keep / overwrite with
  `<path>.pre-update.bak` / invoke `adapt-to-project` interactively).
  The shipped binary (`packages/agentbundle/agentbundle/commands/upgrade.py`)
  is non-interactive: it writes a `*.upstream.<ext>` companion via
  `safety.write_companion` and continues without prompting; the
  `.pre-update.bak` overwrite path is unimplemented. The merge UI
  lives in the `adapt-to-project` skill, which the adopter re-invokes
  after the upgrade to walk the new companions. This is functionally
  non-destructive (your edited file is left alone either way), but
  the README's *Existing files are never silently overwritten*
  section now discloses the gap explicitly. **Unblocks when:** the
  interactive prompt + backup path are implemented in `upgrade.py`,
  or RFC-0001's Tier-2 contract is amended to match v0.1's
  companion-drop-only shape.

## `adapt-to-project` — shipped (AC4b transcripts deferred)

Spec: [`specs/adapt-to-project/spec.md`](specs/adapt-to-project/spec.md).
Drafted per RFC-0001 § *Post-install adaptation* and RFC-0004 § *Drawbacks
→ `adapt-to-project` discovery doubles its artifact surface*. Cross-
references: `self-hosting`, `agent-spec-cli`, **and RFC-0004**.

The v1 implementation lands the typed `AdaptDiscovery` schema, the
`adapt`/self-host consumers' migration from legacy `[accepted]` /
`[adapt]` tables to canonical `[markers]`, install-gate enforcement
of `[pack.dependencies.required]`, the install→adapt marker-write +
chained in-process `adapt.run`, the session-start hook's dual-scope
marker walk, and the SKILL.md body authoring (class-1 shell-out;
classes 2–4 LLM-judgment writes under the per-scope path-jail).

- **APM / Claude-plugins install-route nudge parity.** Adopters
  installing via APM or Claude-plugins routes (rather than
  `agentbundle install`) never hit the install marker write, never
  see the session-start nudge, and never get the chained
  `adapt.run`. The spec is explicit (CLI-only contract), but the
  RFC-0004 parity work would close this gap. **Unblocks when:**
  APM/Claude-plugins adapter parity lands.
- **AC4b — deferred manual-QA rows (real-adopter captures + user-scope-pack).**
  v1 ships the AC4a automation/grep rows. AC4b's remaining open
  shape (see `notes/manual-qa-matrix.md` for the canonical per-row
  table):
  - **Repo-scope class-2 transcripts (rows 8–11).** Brownfield
    fixture seeds the `AGENTS.upstream.md` surface; **Claude-
    simulated captures recorded inline** as preparatory evidence
    against the four documented outcomes (accept / edit / skip /
    decline). *Trigger to close:* real-adopter session against
    `brownfield-adapt/AGENTS.upstream.md` (or an installed core
    pack in an adopter's own repo); replaces the simulated
    captures with the real transcript + tree fragment inline.
  - **Repo-scope class-3 transcripts (rows 12–14).** Brownfield
    fixture extended in this PR with the class-3 surface
    (`DESIGN.md` overlapping canonical `docs/CHARTER.md`); **Claude-
    simulated captures recorded inline** for accept / edit /
    decline. *Trigger to close:* real-adopter session; same shape
    as rows 8–11.
  - **Repo-scope class-4 transcripts (rows 15–16).** Brownfield
    fixture extended in this PR with the class-4 surface
    (`docs/howto/` + `docs/guides/how-to/`); **Claude-simulated
    captures recorded inline** for accept / decline. *Trigger to
    close:* real-adopter session; same shape as above.
  - **Cross-cutting end-to-end primitives (rows 17–18).** ~~Deferred
    end-to-end transcripts.~~ **Promoted to AC4a method (a)
    automation** via `tests/integration/test_adapt_preflight_detection.py`,
    which exercises the deterministic detection primitives
    (`git status --porcelain`, content-hash divergence against
    `state.toml`) the skill body's Pre-flight invokes. Closed
    against AC4a *(a)*; no AC4b transcript needed for these rows.
    The skill-body narration of the Pre-flight remains pinned by
    AC4a *(b)* rows 2 and 3.
  - **User-scope LLM-judgment rows (rows 19–28).** *Trigger:* first
    pack declaring `allowed-scopes = ["user"]` lands (RFC-0004 §
    *Drawbacks* + *Unresolved questions*).

  AC4b stays open: simulated captures for rows 8–16 are
  preparatory evidence, not closing per AC4a's *(c)* contract
  ("captured against a real adopter session").

## `repo-scope-per-adapter-projection` — in flight (T1-T9 landed)

Spec: [`specs/repo-scope-per-adapter-projection/spec.md`](specs/repo-scope-per-adapter-projection/spec.md).
RFC: [`rfc/0012-repo-scope-per-adapter-projection.md`](rfc/0012-repo-scope-per-adapter-projection.md)
(Accepted 2026-05-26). Drafted same day as the RFC's acceptance;
mirrors `pack-allowed-adapters/spec.md` in shape per RFC-0012's
*Follow-on artifacts* bullet.

The spec lifts RFC-0011's adapter resolution to **repo scope**:
`agentbundle install --pack X --scope repo --adapter <ide> .` lands
the pack at `<repo>/.<ide>/skills/` (per-IDE direct write) instead of
the dist-tree shape today produces. Contract v0.6 → v0.7 adds
`allowed-prefixes.repo` to every shipped adapter and introduces
`[adapter.copilot.scope]` for the first time. The resolver renames
to `_resolve_target_adapter` with a `scope` kwarg and a six-step
(0–5) lookup that scope-branches at steps 0, 4, and 5; repo scope
**does not probe** `<repo>/.<ide>/` (load-bearing asymmetry pin).
`DEFAULT_USER_SCOPE_ADAPTER` → `DEFAULT_ADAPTER` rename plus a
one-release deprecation alias. `--emit-install-routes` opt-in
restores the dist-tree producer for catalogue-publishing
workflows; a handler-level mutex refuses it combined with
`--adapter` at repo scope. The eight shipped packs (four
user-scope-capable + four repo-only) bump to v0.7 in one PR per
RFC-0004 atomicity; the repo-only bump is load-bearing per
RFC-0012 Drawback #7. A new `safety.scan_for_pack_artifacts`
helper closes the projection-vs-state crash-window with an
orphan-projection refusal + `--force` clean-and-retry. A
three-trigger in-band detection (shape-mismatch /
adapter-disagreement / orphan recovery) carries adopters across
the v0.6 → v0.7 transition.

- **Status as of 2026-05-26 (this session):** T1-T9 landed via a
  single work-loop execution. ACs closed: AC1-AC23, AC25-AC33,
  AC35-AC37 (subject to T11 final gate verification on the PR).
  ACs partially closed / deferred to follow-up:
  - **AC24** — in-band detection of pre-RFC-0012 state. The
    orphan-recovery (c) trigger ships with T7; the (a)
    adapter-disagreement and (b) shape-mismatch triggers are a
    follow-up amendment.
  - **AC34** — passing on the new tests + green elsewhere; will
    re-verify on PR CI.
- **Tasks landed (this session):**
  - **AC1, AC2, AC3, AC4** close with T1 (contract bump + scope
    tables + schema validator).
  - **AC7, AC8, AC9, AC10, AC11, AC12, AC13, AC30, AC31** close
    with T2 (safety helper + path-jail widening + resolver rename
    + scope-branching + schema validator widening).
  - **AC14, AC15, AC16, AC17, AC32** close with T3 (CLI flag +
    handler-level mutex + binding removal).
  - **AC18, AC19** close with T4 (constant rename + deprecation
    alias).
  - **AC5, AC6** close with T5 (eight packs bump to v0.7).
  - **AC9 (Step 4 repo-scope branch), AC13 (path-jail
    enforcement)** further close with T6 (`_render_for_repo_scope`
    dispatch).
  - **AC20, AC21, AC22, AC23, AC24** close with T7 (install-time
    messages + in-band detection + orphan refusal).
  - **AC33** closes with T8 (end-to-end integration).
  - **AC25, AC26, AC27, AC28, AC29** close with T9 (README +
    migration guide + RFC-0011 erratum + ROADMAP).
  - **T10** amends three sibling specs (`pack-allowed-adapters`,
    `agent-spec-cli`, `distribution-adapters`) per the spec's
    *Constrained by* line.
  - **AC34, AC35, AC36, AC37** stay green throughout (T11's final
    gate sweep).
- **ADR-0004 is post-acceptance.** RFC-0012 § *Follow-on
  artifacts* names "ADR at `docs/adr/0004-repo-scope-per-adapter-projection.md`" as the
  follow-on; the ADR lands after T1-T11 are done, in its own PR.
  Not gating this spec.
- **Sibling RFC for repo-only-pack `allowed-adapters`
  (RFC-0013 candidate) — deferred.** Resolved during RFC-0012's
  adversarial review as out of scope (Drawback #7 already touches
  the repo-only packs by forcing the v0.2 → v0.7 bump). The sibling
  RFC opens after this spec ships; ROADMAP entry will land then.
- **Codex-plugins install-route parity — deferred (sibling RFC).**
  RFC-0012 § *Alternatives* #2 rejects building a `codex-plugins`
  route here; a separate RFC modeled on RFC-0008 is the path.

## `pack-allowed-adapters` — shipped

Spec: [`specs/pack-allowed-adapters/spec.md`](specs/pack-allowed-adapters/spec.md).
RFC: [`rfc/0011-pack-allowed-adapters.md`](rfc/0011-pack-allowed-adapters.md).
`allowed-adapters` landed — Kiro and Codex user-scope installs now
exercise the integrated path against the catalogue's four
user-scope-capable packs (`atlassian`, `figma`, `converters`,
`contracts`). The adapter contract bumped v0.5 → v0.6 with a new
`[adapter.codex.scope]` table; `_resolve_user_scope_target_adapter`
rewrote to the six-step lookup (publisher-drift refusal → `--adapter`
override → state-hint short-circuit → contract-version gate + probe
→ legacy heuristic); `[pack.install] allowed-adapters` validates
through both the schema (array-of-strings shape) and the Python
cross-field check (contract-shipped + user-scope-capable membership).

**Next:** codex-plugins install-route parity (sibling RFC, not yet
opened; will be modeled on RFC-0008's claude-plugins precedent).

## `user-scope-hooks` — drafted

Spec: [`specs/user-scope-hooks/spec.md`](specs/user-scope-hooks/spec.md).
Drafted from [RFC-0005](rfc/0005-user-scope-hook-support.md) (which
merged at Draft in #35 and was amended in #36 to extend Kiro support
at both scopes). The spec is the implementation contract for both
forks the RFC designs:

- **Claude Code at user scope:** `user-merge-json` mode merging
  `hook-wiring` into `~/.claude/settings.json`; `hook-body` reroots
  to `~/.claude/hooks/<pack>/<name>.{sh,py}`.
- **Kiro at both scopes:** `merge-into-agent-json` mode merging
  `hook-wiring` into pack-owned `<scope-root>/.kiro/agents/<attach-to-agent>.json`;
  closes RFC-0001 Open Q1 (Kiro `hook-wiring` `degraded-info-log`).

The plan breaks the work into thirteen tasks (T1 schema accept →
T11 agent-spec-cli amendment, with T8 split into T8a/T8b/T8c —
state schema, install/uninstall, upgrade reconciliation). Tasks
T1–T9 land code; T10 and T11 amend the two sibling specs
RFC-0005's follow-on artifacts name.

- **All 31 ACs open** (AC1–AC29 plus AC17b for Claude Code event
  pass-through and AC19b for `attach-to-agent`-rename upgrade).
  Coverage unblocks incrementally as tasks land:
  - **AC1, AC2, AC3, AC4, AC5, AC7** close with T1 (schema +
    contract version bump).
  - **AC6** closes with T2 (validate rails) and T3 (fixture-on-disk
    coverage).
  - **AC8–AC14** close with T5 (`user-merge-json` mode).
  - **AC15–AC19, AC17b** close with T6 (`merge-into-agent-json`
    mode).
  - **AC16** also touches T7 (phase-order invariant).
  - **AC20–AC22** close with T8a (state schema + migration).
  - **AC23–AC25, AC12, AC11, AC19** close with T8b
    (install/uninstall threading + `--force-merge`).
  - **AC19b** closes with T8c (upgrade reconciliation).
  - **AC26** closes with T9 (`reconcile` reporter).
  - **AC27** stays green throughout (every PR runs
    `make build-check`).
  - **AC28, AC29** close with T3 (fixtures) and inheritance
    through every test PR after.
- **ADR is post-acceptance.** RFC-0005 named the ADR
  ("CLI may write to hand-edited shared user-settings files under
  an ID-tagged array-append merge contract, and to pack-owned
  agent files under a per-agent variant of the same contract").
  Lands after T1–T9 are done; not gating the spec.
- **First user-scope hook-bearing consumer pack — deferred.** Per
  RFC-0005 § First consumer (and § Unresolved Q4). The spec
  measures contract correctness via fixture packs, not via a
  shipped consumer.

## `kiro-ide-hook` — drafted

Spec: [`specs/kiro-ide-hook/spec.md`](specs/kiro-ide-hook/spec.md)
(stub — RFC drives implementation). Sibling of `user-scope-hooks`,
covering RFC-0005's third hook surface that the parent spec did not
ship: standalone `.kiro/hooks/<name>.kiro.hook` JSON files Kiro
reads on IDE-surface events (file save, prompt submit, etc.). A new
primitive `kiro-ide-hook` carries them — source
`.apm/kiro-ide-hooks/<name>.kiro.hook`, projected `direct-file` to
`.kiro/hooks/<pack>/<name>.kiro.hook` for the Kiro adapter,
`dropped` elsewhere, repo-scope only in v1 (user scope is gated on
upstream Kiro [#5440](https://github.com/kirodotdev/Kiro/issues/5440)).

The plan amends two specs in-place (`distribution-adapters` and
`agent-spec-cli`) rather than drafting a third spec. Contract
bumps `0.3 → 0.4` with the addition.

- **All non-probe tasks landable in-session.** T-A, T-B, T-C1, T-C2,
  T-C3, T-C4, T-D1 cover the spec amendments, schema additions,
  validate rail (`check_kiro_ide_hook`), projector module
  (`projections/kiro_ide_hook.py`), Kiro adapter wiring, and
  synthetic fixtures.
- **T-CONTRACT (v0.4 contract bump) — probe-gated.** RFC-0005
  § *Gating verifications before contract version 0.4 ships*
  requires two probes against a real Kiro install before the
  declaration lands:
  - **Q6 — recursion + extension filter.** Does Kiro recurse into
    `.kiro/hooks/<subdir>/`? Does it glob `*.kiro.hook` or read
    every file? The 2×2 decides the canonical `target.repo` string.
    The `yes-recursion × no-extension-filter` quadrant additionally
    triggers a cross-primitive `hook-body` user-scope retarget
    (tracked as conditional task T-E1b).
  - **Q11 — vocabulary fixture.** Capture at least one
    IDE-UI-authored `.kiro.hook` file; the captured `when.type` /
    `then.type` strings become the canonical
    `ide-event-vocabulary` / `ide-action-vocabulary` in
    `adapter.toml`.
- **T-F (ADR) — post-implementation.** Records both bullets from
  RFC § Follow-on artifacts ADR: (a) merge contracts for
  hand-edited and pack-owned files (`user-merge-json` /
  `merge-into-agent-json`); (b) primitive-per-surface for Kiro
  hooks. Per the pre-EXECUTE adversarial review, `docs/adr/`
  carries only 0001/0002 today and the user-scope-hooks track
  produced no ADR — bullet (a) is currently orphaned and this PR
  picks it up alongside bullet (b).
- **RFC drift in § State-file impact — deferred.** RFC-0005 lines
  1067-1086 describe uninstall as "unconditional / verbatim", but
  shipped `uninstall.py` is Tier-2 warn-and-preserve. The T-B
  amendment describes actual code behaviour; the RFC text edit is
  not in scope for this PR and lands as a follow-up.
- **First `kiro-ide-hook` consumer pack — deferred.** Tracked as a
  separate open item per RFC § Follow-on artifacts ROADMAP bullet
  ("A separate item tracks the first `kiro-ide-hook` consumer
  pack"). The spec measures contract correctness via fixture packs,
  not via a shipped consumer — same precedent as the
  `user-scope-hooks` first-consumer deferral above.

## `skill-secrets` — shipped

Spec: [`specs/skill-secrets/spec.md`](specs/skill-secrets/spec.md).
Shipped from [RFC-0006](rfc/0006-skill-secrets-storage.md) (Accepted
2026-05-24). Delivered the two-layer architecture (skills don't hold
credentials; credentialed primitives do), the three storage tiers
(env → OS keyring → dotfile floor at `~/.agentbundle/credentials.env`),
the stdlib-only loader + `agentbundle creds` verb
(`setup`/`check`/`where`/`rm` only; no `get`), the argv ban +
`SKILL.md` "Don't" block, the `conventions-check` extensions, the
worked example, and the ADR-0002 amendment freezing the narrow
"hook-shaped" definition.

Per-task closure (15 tasks; T13 split into T13a/T13b/T13c):

- [x] **T1** — ADR-0002 amendment (closed AC1; landed in spec PR).
- [x] **T2** — stdlib `.env` parser (closed AC2).
- [x] **T3** — loader API + Tier-1 + platform dispatch + wheel-installability
      (closed AC3, AC4, AC4b, AC4c, AC5).
- [x] **T4** — macOS Keychain Tier-2 (closed AC6, AC7, AC8).
- [x] **T5** — Windows Credential Manager Tier-2 (closed AC9, AC10,
      AC11, AC12).
- [x] **T6** — Tier-3 dotfile incl. shared-parent behavior (closed
      AC13, AC14, AC15).
- [x] **T7** — `creds-schema.toml` parser + canonical-path resolution
      (closed AC24, AC24b).
- [x] **T8** — `agentbundle creds` CLI verb; tombstone args; per-platform
      exit-code matrices (closed AC16–AC23). AC22's macOS symbolic
      exit-code matrix was completed in a round-2 follow-on PR alongside
      a Windows CI matrix; see the *Round-2 review-pass disposition*
      section below for the merge SHAs.
- [x] **T9** — SKILL.md frontmatter + lint allow-list (closed AC25).
- [x] **T10** — `conventions-check` AST-walker extensions (closed
      AC26, AC27).
- [x] **T11** — `add-credentialed-skill` author skill + template variants
      (closed AC28).
- [x] **T12** — `example-credentialed-skill` worked example (closed AC29).
- [x] **T13a** — seed-side CONVENTIONS.md edit (closed AC30).
- [x] **T13b** — Diátaxis how-to (closed AC31).
- [x] **T13c** — this entry's per-task closure (closed AC32).
- [x] **AC33** — `make build-check` clean across every PR.
- [ ] **AC34, AC35** — inheritance invariants (orphan-fixture guard;
      no live writes to developer keychain / dotfile). Enforced by
      every future test PR that adds fixtures under
      `packages/agentbundle/tests/fixtures/creds/`.

Round-2 review-pass disposition (post-Shipped):

The end-of-spec review pass surfaced items that didn't warrant
re-opening Shipped status but did warrant focused follow-on PRs.
Captured here so a future ROADMAP reader can see the disposition:

- **PR #84 — `windows-latest` CI matrix** (precursor; closes
  Security § Not-checked "no live exercise of the Windows ctypes
  path"). Adds the verification home AC10 / AC11 / AC15 had been
  missing.
- **PR #85 — AC22 macOS symbolic exit-code matrix** (closes
  Adversarial Blocker #5 + Quality Concern #7). Adds module
  constants and `_classify_macos_exit_code` parallel to the Windows-
  side classifier; embeds the symbolic name in `Tier2HardFailError`
  messages. No behavior change to the existing
  `--allow-insecure-fallback` flow.
- **PR #86 — `CredentialsMissingError` tier observability**
  (closes Quality Concerns #5 + #6). Per-key tier trailers + structured
  attributes; adds the AC4 cross-tier composability construction test.
- **Robustness pass** — per-finding micro-fixes (`Credentials.__repr__`,
  `Credentials.__getattr__` resolved-keys hint, `_quote_for_dotfile`
  raises on unsafe chars, `EnvParseError` ordering, `credentialed:`
  YAML normalisation, `resolve_schema_path` → `_relative_schema_path`
  rename, `creds rm`
  continue-on-Tier-2-fail, AC23 stderr-prefix categorisation).
- **Lint widening** — AST walker f-string / Starred(Tuple) /
  Subscript shapes; `icacls` SID-based matching to harden non-English
  Windows installs.
- **Spec / plan / doc cleanup** — inline-fixture amendment;
  `docs/product/release-checklist.md` for the three Windows manual-QA
  rows; this very ROADMAP audit.
- **PR #97 — `schema_path=` kwarg removal** (closes Quality Blocker
  #4). Path (a) chosen: `load_credentials` is *resolution only*; schema
  validation lives in `agentbundle creds check`, not on the loader's
  public surface. AC24b amended accordingly.

Open follow-ons (not gating shipped status):

- **New ADR ("Credential storage for credentialed skills") is
  post-implementation.** RFC-0006 § Follow-on artifacts names it; with
  T1–T13c shipped, this is the next item (precedent:
  `user-scope-hooks`'s ADR).
- **Linux `libsecret` tier deferred.** v2 RFC scoped alongside an
  adopter-profile audit per RFC-0006 § Unresolved Q1; not gating
  v1 (Linux lands on Tier 3 floor). The `v2-libsecret` stub stays
  open under cross-spec items below.

---

## `wire-session-start-hook` — shipped

Spec: [`specs/wire-session-start-hook/spec.md`](specs/wire-session-start-hook/spec.md).
Approved 2026-05-24 after four rounds of spec-mode adversarial review;
T1-T7 implementation via work-loop in PR #98 (with a mid-EXECUTE spec
amendment correcting paths flat → dist-tree across AC1/AC2/AC3/AC9/AC10
when implementation surfaced the wrong path assumption). On
`agentbundle install core`, the merge-json adapter writes the Claude
Code `SessionStart` binding into the dist-tree at
`<output>/claude-plugins/core/.claude/settings.local.json` (Claude
Code's plugin marketplace consumes from there); self-host also writes
it to the workspace flat path `<workspace>/.claude/settings.local.json`
(gitignored). Adopters no longer hand-paste the snippet from
`tools/hooks/README.md`. Core stays at adapter-contract v0.2. Wiring
TOML uses Claude Code's documented nested SessionStart schema (per
[code.claude.com/docs/en/hooks](https://code.claude.com/docs/en/hooks)).
Bundled a legacy-fixture rewrite for three stale `pre-commit.toml`
upgrade-catalogue fixtures from `[hook] name/trigger/matcher` shape
to live `[[hooks.<Event>]]` shape with a static stub command. PR #98
also fixed a latent `self_host.py` drift-loop bug (now honours
`EXCLUDED_PATTERNS` like the unclassified-path enumeration does).

Per-task closure (7 tasks):

- [x] **T1** — Construction test (synthetic minimal pack →
      `install.run(...)` → assert nested SessionStart binding lands at
      `<target>/claude-plugins/<pack>/.claude/settings.local.json` with
      matcher-absence). Closes AC9.
- [x] **T2** — Wiring TOML at `packs/core/.apm/hook-wiring/session-start.toml`.
      Flips T1 green. Closes AC1, AC2.
- [x] **T3** — `tools/hooks/README.md` two-surface reframe (umbrella
      intro + `### Claude Code` subsection) + fix the pre-existing
      `.claude/settings.json` → `.claude/settings.local.json` path bug.
      Closes AC6.
- [x] **T4** — `packs/core/seeds/docs/CONVENTIONS.md` reframe (two
      paragraphs: enforcement-triplet and Profile-C). Closes AC7.
- [x] **T5** — `make build-self` projects only the T4 seed edit; no
      projected-path drift elsewhere. Closes AC8.
- [x] **T6** — Legacy fixture rewrite for `catalogue_v{1,2,3}/.../pre-commit.toml`.
      Substring `matcher = "Bash|Edit"` survives in v2. Closes AC5,
      AC4 (regression).
- [x] **T7** — Full-suite regression + AC10 smoke test against real
      `packs/core/` + PR description with latent-limitation notes
      (R1, R4, R5). Closes AC3, AC10.

Open follow-ons (not gating this spec):

- **Kiro session-start support.** Deferred to a separate spec.
  Neither Kiro IDE nor Kiro CLI has a true session-start lifecycle
  event; the architecturally-right Kiro primitive is `steering`,
  which the adapter contract does not model today. The parallel
  spec needs to (a) introduce a `steering` primitive, (b) decide
  on a build-time vs install-time render pipeline from
  `patterns.jsonl`, (c) pick `inclusion: always` vs `auto`, (d)
  resolve the scope-filtering gap (steering doesn't support
  `--scope` filtering the way the CC hook does), (e) decide
  whether to model Kiro IDE hooks at all or rely entirely on
  steering. Tracked separately; parallel-session prompt drafted.
- **`pre-pr.py` wiring.** Claude Code has no PR-open lifecycle event;
  the closest event (`Stop`) fires after every agent turn, wrong
  semantics. Separate behavior decision required if anyone wants
  it auto-wired.
- **Latent: `cc-user-hooks` fixture produces flat shape.** The
  existing `cc-user-hooks` test fixture produces the flat
  `{command, matcher}` shape on disk, which Claude Code's
  documented schema rejects. The test only asserts JSON
  structure — never verifies Claude Code honors the hook. Out of
  scope here; surfaces in `user-scope-hooks` or a follow-up.
- **R4 (pack↔pack `SessionStart` collision).** Merge-json adapter's
  `dict.update()` at `claude_code.py:101-103` is a key-level merge —
  if a second pack wires `SessionStart`, the second install wipes
  the first's array. Today no other pack wires `SessionStart`, so
  this is latent. Documented in T7's PR description.
- **R5 (repo-scope uninstall doesn't remove merged entry).**
  `install.py:566-602` only populates `hook_wiring_owned` state rows
  at user scope; at repo scope `uninstall core` leaves the
  `.claude/settings.local.json` entry behind. RFC-0005 T8b's design
  would generalise cleanly if a future spec wants this.

## `apm-install-route-parity` — shipped (live-install transcripts deferred per AC17)

Spec: [`specs/apm-install-route-parity/spec.md`](specs/apm-install-route-parity/spec.md);
[RFC-0010](rfc/0010-apm-install-route-parity.md).
T1–T12 landed via work-loop on 2026-05-25: the canonical
`packages/agentbundle/templates/install-marker.py` template gained a
`required` `--install-route {claude-plugins,apm}` flag, a data-directory
precedence shim (`${CLAUDE_PLUGIN_DATA}` → `${PLUGIN_ROOT}/.data` →
`${CURSOR_PLUGIN_ROOT}/.data` → exit 0), and an APM scope-detection path
that reads its own `Path(__file__).resolve()` for cwd / `$HOME`
containment. Adapter contract bumped v0.4 → v0.5 with `"apm"` appended to
`[adapter."claude-code"].install-routes`. Build pipeline now derives
`dist/apm/<pack>/.apm/hooks/install-marker.{json,py}` and projects
`pack.toml` for every pack; the claude-plugins-side
`hooks.SessionStart` command picked up the matching
`--install-route claude-plugins` flag in the same PR (lockstep
projection means a refreshed writer always ships next to a refreshed
command). Self-host drift gate (`make build-check`) extended to assert
byte-identity on the APM-projected writer. Sibling specs amended
in-PR: `claude-plugins-install-route` AC1 allow-list grew by `argparse`
and AC9 hook command + `shlex.split` token list extended by the new
flag; `adapt-to-project` schema permits `install-route = "apm"`, AC27
added (APM-route stale-entry drop-on-read); `distribution-adapters`
recipe row notes the install-marker artifact derivation and a new AC
documents APM-route conformance + four-of-seven HookIntegrator coverage.
Adopter disclosure shipped at `packs/core/README.md`.

- **Deferred per AC17** (manual-QA matrix rows 32-34): three live-install
  transcripts (`apm install` of core at project scope, `apm install -g`
  of converters at user scope, per-target characterisation at Copilot
  / Cursor / Gemini). Verification = transcript; rows exist with named
  close triggers per the matrix's existing deferral pattern. RFC-0010
  §Unresolved questions Q6 is the close trigger for the RFC; AC17
  closes when the rows exist (now done), not when transcripts land.
- **Coverage caveat (AC15):** APM *marker presence* asserted on
  session 2 or later at Claude Code targets per the
  [`anthropics/claude-code#10997`](https://github.com/anthropics/claude-code/issues/10997)
  first-session quirk — applies regardless of route (CLI / claude-plugins
  / APM all hit it). Three uncovered HookIntegrator targets (Codex,
  OpenCode, Windsurf) silently lack the hook surface in upstream APM;
  adopters there run the documented
  `agentbundle adapt --scope <project|user>` manual fallback per
  the per-pack README disclosure.

## `credential-broker-contract` — shipped (T1-T15 landed; manual-QA matrix pending)

Spec: [`specs/credential-broker-contract/spec.md`](specs/credential-broker-contract/spec.md).
ADR: [`adr/0003-credential-broker-contract.md`](adr/0003-credential-broker-contract.md)
(Accepted 2026-05-26 — records the four-broker decision, two transports, brokers-not-skills with the credential-setup exception, no PyPI shim package, and rejection of alternatives B / D / E / F / G / H / I / J).
RFC: [`rfc/0013-credential-broker-contract.md`](rfc/0013-credential-broker-contract.md)
(Accepted 2026-05-26). Amends RFC-0006: promotes the security
invariants to a broker-agnostic contract; demotes the env →
keychain → dotfile resolver from "the convention" to "one of four
brokers" (`env`, `cli`, `creds`, `sso-cookie`); ships the `creds`
broker as a build-pipeline-projected vendored Python shim (no PyPI
dependency) and the `sso-cookie` broker as an adapter-root
subprocess at `~/.agentbundle/bin/sso-broker.py`. Adapter contract
bumps to the next label above whatever T1 reads at PR-open time
(governance record-keeping — the `allowed-prefixes.user` widening
RFC-0013 § 4d describes is already in place since v0.3's
`.agent-ready/` rename). **Version-label collision with RFC-0012:**
RFC-0013's body targets v0.7 but RFC-0012 (`repo-scope-per-adapter-projection`,
Accepted) also targets v0.7 with a substantive scope-table change;
per RFC-0013 § 4's disjoint-label rule the two cannot share v0.7,
so the implementing PR resolves to v0.7 → v0.8 if RFC-0012's spec
lands first, or v0.6 → v0.7 if this lands first. See spec AC1's
post-merge revision for the reconciliation logic. Two new build-pipeline
primitive classes (`shared-libs/` for many-to-many shim projection
into consumer skills' `scripts/`; `adapter-root-bins/` for
single-target projection to `~/.agentbundle/bin/`). 48 ACs / 15 tasks
across three phases: Phase 1 broker contract + pack + lint + docs
(T1-T10); Phase 2 in-tree consumer migration (T11-T14, six skills +
the `add-credentialed-skill` teaching block); Phase 3 cleanup —
remove `agentbundle.credentials` + `agentbundle/creds/`, bump
`agentbundle` 0.1.x → 0.2.0 (T15).

**Manual-QA matrix** (transcript pending until each row is recorded
under `docs/specs/credential-broker-contract/notes/`):

- `creds` × macOS — `/usr/bin/security` Tier-2; consuming skill resolves PAT.
- `creds` × Windows — `advapi32.CredReadW`/`CredWriteW` Tier-2; consuming skill resolves PAT.
- `creds` × Linux — dotfile floor; consuming skill resolves PAT.
- `sso-cookie` × macOS — real corporate-SSO endpoint (downstream consumer environment); headed Chromium `register` flow; `test` returns 0.
- `sso-cookie` × Windows — same against same endpoint.
- `sso-cookie` × Linux — file-floor cookie jar; same flow.

**Depends on:** RFC-0011 (`pack-allowed-adapters`, Accepted 2026-05-26)
— the v0.6 baseline this spec bumps above; and RFC-0012 sequencing
for the concrete version label per the collision note above.
Acceptance-ordering
gate is met; the implementation spec can proceed.

**Deferred security-hardening follow-ups** (named in spec changelog
2026-05-26 (T8 security-hardening revision); the lint is one layer,
PR-review is the other):

- **D3 dotfile-read substring scan is bypassable by part-composition.**
  Today `tools/lint-credentialed-skills.sh` matches the literal
  `.agentbundle/credentials.env` substring. A malicious skill can
  compose the path from concatenated parts and evade the rule.
  Follow-up: rewrite D3 as an AST walk over `open(...)` /
  `Path.read_text` / `Path.read_bytes` call sites using
  `_path_chain_components`, asserting the resolved tail does not
  match the dotfile path under `Path.home()`.

- **`_is_canonical_shim` byte-equality is a lint-time integrity check,
  not a runtime tampering guard.** A post-install hook could mutate
  the projected shim after the lint has read it. Follow-up: either
  path-anchor the exemption (admit only files at the canonical
  projection target under a recognised consumer-skill `scripts/`
  directory), or sign the canonical shim and verify the signature at
  build time.

- **Lint script's Python heredoc bypasses static analysis.** The 900-line
  rule engine lives inside a `python3 - <<'PY' ... PY` heredoc in
  `tools/lint-credentialed-skills.sh`, so ruff / mypy / IDE tooling see
  it as a single bash string. Quality-engineer round-4 Concern 4. Follow-
  up: extract the body to `tools/lint_credentialed_skills.py` (importable
  module); leave the `.sh` shim as a 5-line wrapper. Unlocks `ruff check`
  on the lint and lets `tools/test-lint-credentialed-skills.py` `import`
  the helpers directly instead of round-tripping through subprocess.

- **Integration tests don't cover the projection path.** `_load_cli_module()`
  in `packages/agentbundle/tests/integration/test_example_credentialed_skill.py`
  loads from the pack-source `SKILL_DIR`, not from the projected
  `.claude/skills/...` mirror. A one-sided edit (source only or
  projection only — per `feedback_self_host_projection` and
  `feedback_build_self_undoes_projection_only_edits`) can pass the
  in-process test while the projection drifts. Follow-up: parametrise
  the test over both paths.

## Cross-spec / outside-the-spec-tree

These are open items called out by accepted RFCs or by multiple specs,
but don't have a spec of their own yet.

- **F-conformance fixtures (RFC-0003).** The per-adapter conformance
  suite that `agentbundle validate --strict` would consume. RFC-0003
  scoped this out of v1; needs its own spec when prioritised.
- **v2 RFC: Linux `libsecret` tier (RFC-0006).** RFC-0006 § Unresolved
  Q1 defers the Linux keyring tier to a v2 RFC alongside an
  adopter-profile audit (headless / SSH dev boxes, WSL2, Docker dev
  containers, corporate fleet defaults). Three integration paths are
  on the table (`secret-tool` CLI, `gi.repository.Secret` Python
  bindings, `ctypes.CDLL("libsecret-1.so.0")` direct); choosing
  among them is part of the audit. Until then, Linux adopters land
  on Tier 3 (dotfile).
