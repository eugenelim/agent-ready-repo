# Spec: copilot-skills-and-web

- **Status:** Shipped <!-- Draft | Approved | Implementing | Shipped | Archived -->
- **Owner:** eugenelim
- **Plan:** [`plan.md`](plan.md)
- **Constrained by:** [RFC-0024](../../rfc/0024-copilot-subagent-projection.md) (§ Errata — closes Open Q4, records the skill-surface flip), [ADR-0013](../../adr/0013-copilot-full-parity-user-scope-adapter.md) (§ Errata), [RFC-0009](../../rfc/0009-codex-native-skills.md) (flip-on-upstream-support precedent). Modifies the adapter contract `docs/contracts/adapter.toml` + its byte-identical twin `packages/agentbundle/agentbundle/_data/adapter.toml` (contract version `0.11` → `0.12`; copilot `skill` `instruction-file`→`direct-directory`; `copilot-instruction` frontmatter-default removed; scope prefixes retargeted).
- **Contract:** none <!-- no REST/event/RPC interface surface; the adapter contract (`adapter.toml`) is internal build-pipeline data, named in Constrained by above -->
- **Shape:** integration

> **Spec contract:** this document defines what "done" means. The implementing
> PR must match this spec, or update it. Verification must be derivable from it.

## Objective

The catalogue's Copilot adapter has fallen behind the GitHub Copilot CLI + app.
Two facts changed after RFC-0024 / ADR-0013 froze (both verified against the
official Copilot docs, 2026-06-11):

1. **Copilot shipped first-class Agent Skills** (`.github/skills/<name>/SKILL.md`
   repo, `~/.copilot/skills/<name>/SKILL.md` user), explicitly *distinct* from
   custom instructions. Our adapter still mis-targets the `skill` primitive as
   an always-on `instruction-file` under `.github/instructions/` — a workaround
   for a gap Copilot has now closed.
2. **Copilot custom agents *do* get the `web` tool** on the CLI + app (`web`
   aliases `WebSearch`/`WebFetch`); the only non-coverage is the cloud agent.
   RFC-0024's Run-4 "no web tool" finding was confounded, so our code comments
   and ~6 docs assert a `research`-pack web degradation that does not exist on
   our target surface.

For an adopter installing `core` or `research` to Copilot, success means: their
skills land as native Copilot Agent Skills the CLI + app load on relevance (not
as always-on instructions), and `research`'s retrieval subagents are documented
as fully web-capable on Copilot CLI/app (degraded only on the cloud agent). The
change ships as one PR with a single contract version bump; the web half is
docs/comments-only (pass-through behaviour is already correct and unchanged).

This repo targets the Copilot **CLI + app** (the shared `~/.copilot/` `$HOME`
layout), not the VS Code extension profile and not the cloud agent's user scope.

## Boundaries

The three-tier guard that keeps an implementing agent inside the lines.
*Always do* applies without asking; *Ask first* requires human sign-off
before proceeding; *Never do* is a hard rule, even under time pressure.

### Always do

- Edit the canonical contract `docs/contracts/adapter.toml` and keep the twin
  `packages/agentbundle/agentbundle/_data/adapter.toml` **byte-identical** (the
  drift gate enforces it); the same byte-identical rule binds both
  `adapter.schema.json` copies.
- Reuse the existing `direct-directory` skill projection (the copytree +
  symlink-defence + skill-bounded orphan-sweep already used by
  `claude-code`/`codex`/`kiro`) — do not invent a new mode.
- Record the divergence from frozen Accepted decisions as an **Approver-signed
  `§ Errata`** appended to RFC-0024 (close Open Q4 + record the skill-surface
  flip) and ADR-0013; append only, never rewrite their history.
- Bump `[contract] version` exactly **once** (`0.11` → `0.12`) and update every
  version-pin test in lockstep (lexical version-compare is fragile —
  `"0.10"` vs `"0.8"` vs `"0.12"`).
- Run the **full package pytest in both roots** by hand (`build/tests/` and
  `tests/`) — `make build-check` does not run package pytest.

### Ask first

- Escalating the skill-surface flip from an erratum to a standalone follow-on
  RFC — taken only if the spec-mode adversarial reviewer judges it
  decision-worthy (vehicle (a) was chosen by the owner 2026-06-11).
- Bumping any pack other than `research` + `core` to the new contract level
  (per RFC-0024 § Decision 7 this is **not** an all-pack bump).
- Removing the `instruction-file` *mode* or `direct-file` plumbing from the
  schema enum / shared code (other adapters or future modes may rely on the
  enum value; this PR drops only copilot's *use* of `instruction-file` and the
  now-orphaned `copilot-instruction` frontmatter-default).

### Never do

- Re-probe a live Copilot CLI for this task — the source of truth is the
  official docs cited in the plan (prior live probes were confounded).
- Add a Claude→Copilot tool-name **mapping** for `WebFetch`/`WebSearch` — they
  already pass through verbatim and Copilot resolves them to `web`; the web
  change is docs/comments-only with **zero behaviour change**.
- Add a new top-level directory, a new projection mode, or a new dependency.
- Hand-edit any projected/generated path (`.claude/`, `.agents/`, `AGENTS.md`,
  `dist/**`, `marketplace.json`) — edit contract + pack `.apm` sources, then
  `make build-self`.

## Testing Strategy

- **Contract shape (skill mode, scope prefixes, version, byte-identical twins):**
  goal-based check + TDD. The existing `build/tests/test_contract*.py` and
  `test_adapter_copilot.py` assert the contract dict; extend them to assert the
  copilot `skill` mode is `direct-directory` → `.github/skills/`, the new
  allowed-prefixes, and `version == "0.12"`.
- **Projection behaviour (copilot skills emit `.github/skills/<name>/SKILL.md`;
  an agent declaring `WebFetch` still projects with no build error):** TDD —
  focused construction tests rendering a synthetic pack and asserting the
  on-disk tree + a clean `project()` call.
- **User-scope rewrite (`~/.copilot/skills/...`):** TDD — extend
  `tests/unit/test_copilot_user_scope_wiring.py` to assert the
  `.github/skills/` → `.copilot/skills/` prefix rewrite.
- **Safety prefixes (`.github/skills/` admitted at repo scope, `.copilot/skills/`
  at user scope):** TDD — extend `test_safety_repo_scope_prefixes.py` /
  `test_safety_scan_per_pack_scoping.py`.
- **Web comments + docs are correct and no degradation wording survives on the
  CLI/app surface:** goal-based check — `grep` the agreed degradation phrases
  across `docs/`, code comments, and pack content and confirm each remaining
  hit is scoped to the *cloud agent* only.
- **Doc-drift invariants (this spec's status/ACs; backlog anchor resolves):**
  goal-based — `scripts/lint-spec-status.py` at the finish checklist.

## Acceptance Criteria

- [x] The copilot `skill` projection in both `adapter.toml` copies is
  `mode = "direct-directory"`, `target-path = ".github/skills/"`, with no
  `frontmatter-default`; the `copilot-instruction` frontmatter-default table is
  removed; both copies remain byte-identical. The single-copy
  `docs/contracts/target-vocab.toml` `[target.copilot]` comment names
  `.github/skills/` rather than `.github/instructions/` (no `_data/` twin — the
  byte-identical rule does not apply to target-vocab).
- [x] `[adapter.copilot.scope]` admits `.github/skills/` under
  `allowed-prefixes.repo` and `.copilot/skills/` under `allowed-prefixes.user`
  (in both copies); the legacy `.github/instructions/` repo prefix and
  `.copilot/instructions/` user prefix are removed (copilot no longer projects
  any instruction file).
- [x] The install handler's hardcoded copilot user-scope rewrite map
  (`install.py::_rewrite_copilot_user_scope_paths`, `prefix_map`) and the
  orphan-scan KeyError default for copilot rewrite `.github/skills/` →
  `.copilot/skills/` (no longer `.github/instructions/`), so a user-scope
  copilot install lands skills at `~/.copilot/skills/<name>/SKILL.md` and passes
  the path-jail.
- [x] `[contract] version` is `"0.12"` in both copies; every version-pin test
  asserts `"0.12"` and the lexical-compare tests (`test_contract_v07.py`,
  `test_contract_v08.py`) still pass.
- [x] Building a pack that ships a skill through the copilot adapter emits
  `.github/skills/<name>/SKILL.md` (full directory tree, byte-equal source
  body), exercised by a construction test; the orphan sweep removes a stale
  skill dir on re-projection, and is **bounded to the `skill` primitive's
  expected source names** — it never touches sibling `.github/agents/` or
  `.github/hooks/` content.
- [x] An agent declaring `tools: …, WebFetch, WebSearch` projects through
  `copilot-agent-md` with no build error (regression test), and the
  `copilot_agent_md.py` module docstring + `_KNOWN_TOOLS` comment state that
  `WebFetch`/`WebSearch` resolve to Copilot's `web` tool on CLI/app (the only
  non-coverage is the cloud agent) — the "no web tool / research degradation"
  wording is gone.
- [x] `packs/research/pack.toml` and `packs/core/pack.toml` declare
  `[pack.adapter-contract] version = "0.12"`; no other pack is bumped;
  `make build-self` runs clean (it is a no-op for `marketplace.json` — the
  marketplace tracks each pack's `[pack] version` semver, not the
  `[pack.adapter-contract]` version — so no projected file changes; no hand edit).
- [x] `packs/research/` content (`pack.toml` caveat, `.apm/skills/research/SKILL.md`,
  `references/retriever-interface.md`) no longer asserts a Copilot web
  degradation for the CLI/app surface; any retained caveat is scoped to the
  cloud agent only.
- [x] An Approver-signed `§ Errata` is appended to `docs/rfc/0024-copilot-subagent-projection.md`
  (closes Open Q4: web supported per docs, Run-4 confounded; records the
  skill-surface flip instruction-file → SKILL.md) and to
  `docs/adr/0013-copilot-full-parity-user-scope-adapter.md`; neither file's
  prior content is rewritten.
- [x] The doc blast radius is reconciled to reflect SKILL.md skills +
  web-on-CLI/app, with **every** copilot-skill/web assertion corrected (not just
  the headline cell): `docs/guides/reference/adapter-support.md` — the Copilot
  table row (Skill cell, Subagent cell + its status word), the dedicated
  no-web-tool caveat block, **and** the summary guidance line that tells readers
  to "plan around the no-web-tool caveat"; `docs/guides/reference/research-pack.md`;
  `docs/guides/tutorials/research-first-session.md`; `docs/architecture/agentbundle.md`;
  `AGENTS.local.md`; `docs/backlog.md` (the deferred Copilot-web item);
  `docs/specs/distribution-adapters/spec.md` (projection table); and
  `docs/specs/README.md` (the copilot-full-parity entry's "no web" phrasing **and**
  a new `copilot-skills-and-web` active-list entry). Any blast-radius file
  deliberately left untouched is named in the PR description with a reason.
- [x] The prior spec `docs/specs/copilot-full-parity/spec.md` + `plan.md` have
  their now-superseded ACs/caveats (instruction-file skills, no-web) updated
  with a forward pointer to this spec; their history is not rewritten.
- [x] Full package pytest passes in both roots (`build/tests/` and `tests/`),
  `make build-check` is green, and `lint-spec-status.py` reports no drift.

## Assumptions

- Technical: Copilot Agent Skills load from `.github/skills/<name>/SKILL.md`
  (repo) and `~/.copilot/skills/<name>/SKILL.md` (user); filename must be
  `SKILL.md` in a per-skill subdir; required `name` (lowercase-hyphen) +
  `description`, optional `license`; distinct from custom instructions; Copilot
  also accepts `.claude/skills`/`.agents/skills` repo paths (so our canonical
  Claude `SKILL.md` sources pass through unchanged). (source: https://docs.github.com/en/copilot/how-tos/copilot-cli/customize-copilot/add-skills, fetched 2026-06-11)
- Technical: Copilot custom agents support `tools: web` with aliases
  `WebSearch`/`WebFetch`; `tools` unset defaults to all tools; the only caveat
  is web is "Currently not applicable for cloud agent". (source: https://docs.github.com/en/copilot/reference/custom-agents-configuration, fetched 2026-06-11)
- Technical: copilot `skill` is the **only** consumer of the `instruction-file`
  mode and the `copilot-instruction` frontmatter-default in the contract, so
  both are orphaned by the flip and safe to drop from copilot's use. (source: `grep instruction-file/copilot-instruction docs/contracts/adapter.toml`, 2026-06-11)
- Technical: copilot is installed per-pack via `copilot.project(pack_dir, …)`
  (`install.py:2415/2484`) and is **not** in `SELF_HOST_ADAPTERS`
  (`claude-code`, `codex`), so the skill flip needs only a `direct-directory`
  branch in copilot's single-pack `project()` mirroring codex, not a
  `project_packs` refactor; `build-self` is still required because the pack
  version bumps re-drift `marketplace.json`. (source: `self_host.py:83,235`, `install.py:2415`, 2026-06-11)
- Process: divergence from a frozen Accepted RFC/ADR is recorded in governance
  via an Approver-signed `§ Errata` (append, not rewrite); vehicle (a) over a
  follow-on RFC, with reviewer escalation reserved. (source: user confirmation 2026-06-11; RFC-0024 § Governance precedent)
- Product: this repo's guaranteed Copilot surface is the CLI + app
  (`~/.copilot/` + `.github/`); VS Code extension profile and the cloud agent's
  user scope are out of scope. (source: user confirmation 2026-06-11; RFC-0024 § Non-goals)
