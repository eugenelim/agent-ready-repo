# Backlog — open items by spec

Single index of **open** work across every spec in `docs/specs/`. Each
item names the spec, the Acceptance Criterion (where one applies),
what's blocking it, and how it gets unblocked. Closed/shipped work is
**not** kept here — see each spec's Changelog and
[`product/changelog.md`](product/changelog.md).

This file is governance about *this repo's* evolution, not adopter
scaffolding. The adopter-facing **product roadmap** (strategy, not a
work index) lives at [`product/roadmap.md`](product/roadmap.md) (a
*Projected* path sourced from `packs/core/seeds/`). This file is the
tactical **backlog**: per-instance, no pack-side source, surfaces as an
`[info]` line under `make build-check` per AC6 of the self-hosting spec.
Deferred acceptance criteria point here by anchor (the `(deferred: <anchor>)`
marker — see RFC-0016).

## How this file is maintained

- Every spec records its own `Status:` field and `Acceptance Criteria`
  checkboxes. This file aggregates the **open** items so they're visible
  in one place — it is not the source of truth.
- When an AC closes or a spec ships, update the spec first, then **remove**
  the now-closed item here in the same PR (closed work lives in the spec
  Changelog / `product/changelog.md`, not here).
- When a new spec lands with open ACs, add a section here.
- If an item here is no longer accurate against the underlying spec,
  trust the spec and fix this file.

---

## `agent-spec-cli`

- **Deferred to a follow-up RFC** (named in RFC-0004): user-scope
  hook-wiring merge story (Rail B keeps hook-bearing packs
  user-scope-refused until it lands); `global` system-wide scope
  (absent, not reserved); new user-scope packs (the dimension shipped
  without a consumer).
- **Deferred to v1.1:** SSH git URL support in `install`
  (`git+ssh://…` exits non-zero with a "deferred to v1.1" message);
  full `--strict` `validate` against the v0.1 conformance fixtures
  (owned by RFC-0003's deferred F-conformance task).
- **Tier-2 upgrade prompt — v0.1 ships companion-drop only.** RFC-0001
  specifies a three-option in-CLI prompt on `agentbundle upgrade` Tier-2
  collisions (keep / overwrite with `.pre-update.bak` / invoke
  `adapt-to-project`). The shipped `upgrade.py` is non-interactive
  (writes a `*.upstream.<ext>` companion and continues); the
  `.pre-update.bak` overwrite path is unimplemented. **Unblocks when:**
  the interactive prompt + backup path are implemented, or RFC-0001's
  Tier-2 contract is amended to match the companion-drop-only shape.

## `adapt-to-project`

- **APM / Claude-plugins install-route nudge parity.** Adopters
  installing via APM or Claude-plugins never hit the install-marker
  write, the session-start nudge, or the chained `adapt.run`. The spec
  is CLI-only by contract; RFC-0004 parity work would close this.
  **Unblocks when:** APM/Claude-plugins adapter parity lands.
- **AC4b — deferred manual-QA rows.** v1 ships the AC4a automation/grep
  rows; AC4b's transcript rows stay open (see
  `specs/adapt-to-project/notes/manual-qa-matrix.md`):
  - Repo-scope class-2/3/4 transcripts (rows 8–16): Claude-simulated
    captures are recorded inline as preparatory evidence. **Closes when:**
    a real-adopter session replaces them with a real transcript.
  - User-scope LLM-judgment rows (rows 19–28). **Closes when:** the first
    pack declaring `allowed-scopes = ["user"]` lands.

## `dropped-primitives-coverage`

- **Auto-detect the v0.7 → v0.8 codex re-projection case** so `--force`
  (or `agentbundle upgrade`) re-projects under the new contract without
  the documented manual `uninstall + install` two-step. Named in the
  spec § Risks; deferred to a future RFC.

## `repo-scope-per-adapter-projection` / `pack-allowed-adapters`

- **codex-plugins install-route parity** (sibling RFC, not yet opened;
  modeled on RFC-0008's claude-plugins precedent). RFC-0012 § Alternatives
  #2 rejected building it inline.
- **Sibling RFC for repo-only-pack `allowed-adapters`** — deferred during
  RFC-0012 review as out of scope; opens as its own RFC when prioritised.
- **AC19 + plan T (lines 316/321/324) target the retired `add-credentialed-skill`
  skill.** The `add-credentialed-skill` author skill was deleted 2026-05-31
  (credential-broker-contract § Changelog; RFC-0013 § Errata). AC19's
  `allowed-adapters` author-guidance paragraph has no host skill any more —
  when this Draft spec is implemented, add that `allowed-adapters`
  author-guidance paragraph to the how-to
  `docs/guides/how-to/add-a-credentialed-skill.md` instead (the deleted
  skill's "Adapter portability" section was not carried over — it's
  pack-authoring guidance this spec owns). Left unfixed here to avoid
  editing another spec's open ACs out of scope; the references are
  warn-only (invariant iii).

## `user-scope-hooks`

Spec drafted from RFC-0005; **all 31 ACs open** (AC1–AC29 + AC17b + AC19b),
unblocking incrementally as tasks T1–T9 land code (T10/T11 amend sibling
specs). Two forks: Claude Code at user scope (`user-merge-json` into
`~/.claude/settings.json`) and Kiro at both scopes (`merge-into-agent-json`).

- **ADR is post-acceptance** (the array-append merge contract); lands
  after T1–T9, not gating.
- **First user-scope hook-bearing consumer pack — deferred** (RFC-0005
  § First consumer); correctness measured via fixture packs.

## `kiro-ide-hook`

Sibling of `user-scope-hooks` for RFC-0005's third surface (standalone
`.kiro/hooks/<name>.kiro.hook` IDE-event files). Non-probe tasks
(T-A/B/C1-4/D1) are landable in-session.

- **T-CONTRACT (v0.4 contract bump) — probe-gated.** Requires two probes
  against a real Kiro install: **Q6** (does Kiro recurse into
  `.kiro/hooks/<subdir>/`? glob `*.kiro.hook` or read every file?) and
  **Q11** (capture a real IDE-authored `.kiro.hook` to fix the canonical
  `ide-event`/`ide-action` vocabularies).
- **T-F (ADR) — post-implementation:** merge contracts + primitive-per-surface.
- **RFC drift in § State-file impact — deferred:** RFC-0005 describes
  uninstall as unconditional/verbatim; shipped `uninstall.py` is Tier-2
  warn-and-preserve. RFC text edit is a follow-up.
- **First `kiro-ide-hook` consumer pack — deferred.**

## `skill-secrets`

- **AC34, AC35 — inheritance invariants** (orphan-fixture guard; no live
  writes to developer keychain/dotfile). Enforced by every future test PR
  adding fixtures under `packages/agentbundle/tests/fixtures/creds/`.
- **New ADR ("Credential storage for credentialed skills")** is
  post-implementation (RFC-0006 § Follow-on artifacts); verify whether
  ADR-0003 (credential-broker) already subsumes it.

## `wire-session-start-hook`

- **Kiro session-start support — deferred to a separate spec.** Kiro has
  no true session-start event; the right primitive is `steering`, which
  the contract doesn't model. The parallel spec must introduce `steering`,
  decide build- vs install-time render from `patterns.jsonl`, pick
  `inclusion: always|auto`, and resolve scope-filtering.
- **`pre-pr.py` wiring.** No PR-open lifecycle event exists; `Stop` fires
  after every turn (wrong semantics). A behavior decision is required if
  anyone wants it auto-wired.
- **Latent — `cc-user-hooks` fixture produces flat shape** that Claude
  Code's schema rejects; the test only asserts JSON structure. Surfaces
  in `user-scope-hooks` or a follow-up.
- **R4 — pack↔pack `SessionStart` collision.** The merge-json
  `dict.update()` (`claude_code.py:101-103`) is key-level; a second pack
  wiring `SessionStart` wipes the first's array. Latent (no other pack
  wires it today).
- **R5 — repo-scope uninstall doesn't remove the merged entry.**
  `install.py` only populates `hook_wiring_owned` state at user scope.

## `apm-install-route-parity`

- **Deferred per AC17** (manual-QA rows 32-34): three live-install
  transcripts — `apm install` of core at project scope, `apm install -g`
  of converters at user scope, per-target characterisation at
  Copilot/Cursor/Gemini. Verification = transcript; rows exist (AC17
  closed), transcripts pending. Three uncovered HookIntegrator targets
  (Codex, OpenCode, Windsurf) run the documented `agentbundle adapt`
  fallback.

## `credential-broker-contract`

- **Manual-QA matrix — transcripts pending** (recorded under
  `specs/credential-broker-contract/notes/`):
  - `creds` × macOS — `/usr/bin/security` Tier-2; consuming skill resolves PAT.
  - `creds` × Windows — `advapi32.CredReadW`/`CredWriteW` Tier-2; consuming skill resolves PAT.
  - `creds` × Linux — dotfile floor; consuming skill resolves PAT.
  - `sso-cookie` × macOS — real corporate-SSO endpoint; headed Chromium `register`; `test` returns 0.
  - `sso-cookie` × Windows — same against the same endpoint.
  - `sso-cookie` × Linux — file-floor cookie jar; same flow.
- **Deferred security-hardening** (spec changelog 2026-05-26):
  - **D3 dotfile-read substring scan is bypassable by part-composition.**
    Rewrite as an AST walk over `open(…)` / `Path.read_text` /
    `Path.read_bytes` using `_path_chain_components`, asserting the
    resolved tail doesn't match the dotfile path under `Path.home()`.
  - **`_is_canonical_shim` byte-equality is a lint-time check, not a
    runtime tampering guard.** Path-anchor the exemption, or sign the
    canonical shim and verify at build time.
  - **Integration tests don't cover the projection path.**
    `_load_cli_module()` loads from pack source, not the projected
    `.claude/skills/…` mirror; parametrise over both.

## `agentbundle-wheel-release`

Implementation shipped (`.github/workflows/release-agentbundle.yml`, three
jobs: build-and-smoke / publish-pypi / publish-artifactory). Three ACs remain
open, all gated on the out-of-band first release.

### readme-route3-after-first-publish

AC11 — the README install-route-3 headline edit (replacing the legacy
"once you've pip-installed `agentbundle`" phrasing in `README.md`) lands only
**after** `pip install agentbundle` is true at PyPI. **Unblocks when:** the
first PyPI publish succeeds.

### pypi-first-publish-gesture

AC13 — end-to-end PyPI publish: push an `agentbundle-v*` tag, Trusted-Publisher
OIDC first-firing, then a clean-venv `pip install agentbundle` plus a
credentialed-skill smoke. **Unblocks when:** the first release tag is pushed.

### artifactory-first-publish-gesture

AC14 — corp Artifactory publish first-firing. **Unblocks when:** the three
Artifactory secrets (`ARTIFACTORY_URL` / `ARTIFACTORY_USER` /
`ARTIFACTORY_TOKEN`) are configured and a tag is pushed.

## `event-contract-engine`

Shipped. AC8's drift-by-number quality gate is present as a prose checklist item,
as RFC-0018's resolved Open Q1 specified ("anchor both copies on the shared
`[#NNN]` numbers + a diff-by-number quality-gate item; no cross-skill file
dependency; escalate only if drift is observed in practice").

### drift-by-number-mechanical-gate

Quality-engineer review (post-ship) noted the by-number check is trivially
mechanizable: extract `[#NNN]` tokens from `api-contract/references/events.md`
ch. 19-21 and from the six `event-contract` phase rule files, fail on any
asymmetric difference (two `grep -oE '#[0-9]+' | sort -u` lists, compared).
**Deferred** — RFC-0018's Open Q1 deliberately chose the prose gate now and
"escalate to a shared file only if drift is observed in practice", and a CI lint
reading both skills' files is exactly the cross-skill dependency the RFC declined.
**Unblocks when:** drift between the two copies is observed in practice, or the
team decides to override the RFC's wait-and-see stance (then build a stdlib
`tools/` lint — mind the Windows bash→py and two-lint-surface wiring traps — and
wire it into `make build-check`).

## Cross-spec / outside-the-spec-tree

Open items called out by accepted RFCs or multiple specs, without a spec
of their own yet.

- **F-conformance fixtures (RFC-0003).** The per-adapter conformance suite
  `agentbundle validate --strict` would consume. Scoped out of v1; needs
  its own spec.
- **Copilot `agent`-projection enablement (RFC-0016 open question 1).** The
  sharpened `adversarial-reviewer` "Spec drift" check reaches 3/4 adapters;
  copilot's `agent` primitive is `dropped` in `docs/contracts/adapter.toml`.
  Flipping it to enabled is a contract change (with its own conformance work in
  `distribution-adapters`) — needs its own spec. The other four doc-drift
  mechanisms (template, work-loop, CONVENTIONS, backlog seed) already reach
  copilot via skill/seed surfaces.
- **Tier-1 lint invariant (iii) — promote to hard? (RFC-0016 open question 3).**
  Code-path references **shipped** in the `spec-code-ref-lint` spec (warn-only):
  `work-loop`'s `scripts/lint-spec-status.py` invariant (iii) now flags dangling repo-relative
  doc *and* code references. **Residual:** promoting (iii) from warn-only to a
  hard (exit-non-zero) invariant stays deferred — the measured baseline is ~16
  dangling code references in the corpus, almost all on Frozen specs whose
  bodies cannot be edited, so a hard gate would need that backlog cleaned first.
  Revisit once the warn rate is driven down (or a cleanup pass lands).
- **v2 RFC: Linux `libsecret` tier (RFC-0006).** Defers the Linux keyring
  tier to a v2 RFC alongside an adopter-profile audit (headless/SSH, WSL2,
  Docker, corporate fleet). Three integration paths on the table
  (`secret-tool` CLI, `gi.repository.Secret`, `ctypes` direct). Until then
  Linux lands on Tier 3 (dotfile).

- **`core-install-seed-delivery` reviewer nits (deferred, non-blocking).** Two
  cosmetic items from the issue #190 review, deferred as out of the change's
  scope: (a) `deliver_seeds`' `PathJailError` raise-path is exercised via
  `scaffold`'s monkeypatch test but `install`'s identical catch arm has no
  dedicated test — add one if the catch arms are ever touched; (b)
  `_strip_markdown_code` and `_collect_unresolved_markers` each carry a local
  `import re` (matches install.py's local-import idiom; hoist if the module is
  ever refactored to module-level imports). Neither affects behaviour.

- **`lint-plan-deps.py` is unwired (RFC-0015 / `wave-scheduled-supervisor` AC7).**
  AC7's deliverable `tools/lint-plan-deps.py` (repo-wide plan-DAG sweep) is invoked
  by **no gate** — not in `Makefile`, `.github/workflows/`, or `pre-pr` — and has no
  test; `adopter-clean-enforcement-gate` removed its last anchor (the `new-spec`
  `plan.md` template now points adopters at the shipped per-spec `loop-cohort
  schedule`). Decide in `wave-scheduled-supervisor`: wire it into `build-check` to
  enforce AC7 continuously, or retire it as redundant with `loop-cohort schedule`.
- **Credentialed-authoring skills don't belong in adopter-facing `core` (RFC-0013 /
  `credential-broker-contract`).** From first principles the adopter artifact for
  *authoring* a credentialed skill is the **how-to** — which already exists
  (`docs/guides/how-to/add-a-credentialed-skill.md` + `docs/guides/explanation/credentialed-skills.md`).
  The `add-credentialed-skill` **skill** is redundant for adopters and bound to the
  catalogue build pipeline (`make build-self`, `assets/` templates), and
  `example-credentialed-skill` is `auth: creds` (same coupling). Reconcile their
  adopter-shipping — demote to catalogue-local / retire in favour of the how-to —
  against `credential-broker-contract` AC27/AC43 and RFC-0013 §7. Not touched by
  `adopter-clean-enforcement-gate` (that spec owns these primitives).
