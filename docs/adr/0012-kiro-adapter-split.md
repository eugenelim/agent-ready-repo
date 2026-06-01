# ADR-0012: Split `kiro` into `kiro-ide` and `kiro-cli` with `kiro` as a deprecated alias, and activate `kiro-ide-hook` at contract v0.9

- **Status:** Accepted
- **Date:** 2026-06-01
- **Deciders:** eugenelim
- **Supersedes:** none
- **Related:** RFC-0022 (the accepted proposal); RFC-0005 + errata E1-E3 (user-scope hook support; hook-wiring is CLI-only, `kiro-ide-hook` vocabulary closure); RFC-0001 (adapter spec and build pipeline); RFC-0009 (precedent for adapter migration, single-mode bump); RFC-0011 (`allowed-adapters`; existing packs declare `"kiro"`); `kiro-adapter-split` spec; `kiro-ide-hook` spec (PR #99 — primitive-per-surface ADR tracked in `docs/backlog.md § kiro-ide-hook → T-F`)

## Context

The `kiro` adapter was authored against the Kiro CLI documentation and projected hook-wiring (a `hooks` key inside the agent JSON) and tool names that matched Claude Code rather than Kiro's internal IDs. Two silent breakages affected IDE users:

1. **Tool names resolved to nothing.** The IDE's tool filter matches entries by Kiro tool id (`read_file`, `grep_search`, …) or tag (`read`, `write`, …), not by Claude Code names (`Read`, `Grep`, `Bash`). Fixed in PR #221.
2. **`hook-wiring` dropped IDE agents entirely.** The IDE's `CustomAgentFileLoader` checks the raw file for any CLI-only field (`hooks`, `allowedTools`, `toolsSettings`, `mcpServers`). If any is present, it logs a "not loaded: contains unsupported fields" message and returns without registering the agent. The `hook-wiring` primitive merges a `hooks` key into agent JSON — so any pack shipping a hook-wiring TOML targeting a Kiro agent would silently lose that agent in the IDE.
3. **`kiro-ide-hook` was inert.** The primitive shipped in PR #99 (projector, schema, validate rail, test suite) but was never declared in the adapter contract, so it produced no output.

The IDE and CLI are one vendor but two distinct surfaces: different agent formats, different tool vocabularies, and incompatible hook mechanisms. The `kiro` adapter cannot serve both correctly from a single projection table.

## Decision

> We will split `kiro` into **`kiro-ide`** and **`kiro-cli`** as canonical adapters, retaining **`kiro`** as a deprecated alias for `kiro-ide` with no removal timeline, and bump the adapter contract to **v0.9**.

Six specific decisions, recording RFC-0022's six requested decisions:

1. **Split mechanism + `kiro` name (RFC-0022 D1).** Two canonical adapters (`kiro-ide` / `kiro-cli`); `kiro` is a deprecated alias resolving to `kiro-ide`. The alias is implemented at two levels: (a) the Python adapter registry maps `"kiro"` → `kiro_ide.project`; (b) a `[adapter.kiro]` stub block is retained in `adapter.toml` so `_shipped_for_cli` and the `allowed-adapters` validator keep accepting `"kiro"`. A build-time deprecation warning is emitted on alias resolution.

2. **Agent file format per surface (D2).** `kiro-ide` projects `.md` (frontmatter + body as system prompt, loaded by the IDE's `J6`/gray-matter parser). `kiro-cli` projects `.json` (same JSON-emission path as the current `kiro` adapter). Both formats are verified accepted by their respective loaders (`extension.js` `p16` for IDE; `kiro.dev` CLI docs for CLI).

3. **Tool vocabulary per surface (D3).** Two frontmatter-mapping tables: `kiro-ide-agent-frontmatter-v0.9` (IDE; tool-id values from PR #221: `read_file`, `grep_search`, etc.) and `kiro-cli-agent-frontmatter-v1.0` (CLI; short names: `read`, `grep`, `glob`, `write`, `shell`, `web_fetch`, `web_search`). Model id values (`claude-opus-4.6` / `claude-sonnet-4.5` / `claude-haiku-4.5`) carry forward in both tables, manually maintained.

4. **Hook mechanism per surface (D4).** `kiro-ide`: `hook-wiring` is `mode = "dropped"` (IDE loader rejects `hooks` key); `kiro-ide-hook` is activated at repo scope only (`target.repo = ".kiro/hooks/<pack>/<name>.kiro.hook"`, gated on Q6 probe outcome). `kiro-cli`: `hook-wiring` is kept (`mode = "merge-into-agent-json"`); `kiro-ide-hook` is `mode = "dropped"`.

5. **Model ids (D5).** Same values in both mapping tables; no automated cross-check; manually updated when Kiro publishes new model support.

6. **Errata + spec corrections (D6).** RFC-0005 receives Approver-signed errata E1–E3 (single-adapter assumption, hook-wiring CLI-only, Q11 vocabulary closure via static analysis of `extension.js`). `distribution-adapters/spec.md` footnote and primitive table corrected. `agent-spec-cli/spec.md` §v0.4 clarified.

## Consequences

**Positive:**

- IDE adopters get working agents: correct tool ids, no silently-dropped agents, `kiro-ide-hook` event hooks functional.
- CLI adopters are unaffected; the `kiro-cli` adapter is the current `kiro` behavior, cleanly separated.
- Existing packs and adopter scripts declaring `"kiro"` continue to work via the alias — no forced migration.
- The `kiro-ide-hook` primitive (PR #99) becomes live; its projector, schema, and test suite were already in tree.
- Governance drift (RFC-0005 inferred vocabulary, frozen-RFC divergence) is formally resolved via errata.

**Negative:**

- Five adapter names instead of four; marginal increase in adopter cognitive load.
- Two frontmatter-mapping tables whose `model` values must be manually kept in sync — no automated cross-check.
- The deprecated `kiro` alias is maintenance surface if `kiro-ide` behavior diverges from the alias expectation.

**Neutral / to revisit:**

- **`kiro` alias removal.** RFC-0022 sets no removal timeline. Future maintainers decide at a major contract version boundary.
- **User-scope `kiro-ide-hook` lift.** Blocked on kirodotdev/Kiro#5440. Monitor; lift via point amendment to RFC-0022 when the issue closes (RFC-0022 Open Q1).
- **Q6 probe assumption.** This ADR records the `yes-recursion` quadrant as the plan assumption. If the probe lands `no-recursion`, T1's `target.repo` flattens and the plan is amended before merge; the split decision itself is unaffected.

## Alternatives considered

- **Profile flag (`--surface ide|cli`) on a single `kiro` adapter (RFC-0022 Option B)** — rejected: `--surface` is not a concept elsewhere in the CLI (adapters *are* the surface); adds conditional code inside the adapter vs. the data-driven registry; inconsistent with the one-adapter-one-target principle validated by RFC-0009 and RFC-0001's design.
- **`kiro-ide` only, no `kiro-cli` (Option C)** — rejected: leaves CLI users with no supported path; `hook-wiring` becomes dead code; CLI adopters are known to exist.
- **Do nothing (Option D)** — rejected: every IDE adopter gets zero-tool agents and no event hooks; the latent `hook-wiring` bug activates as soon as any pack ships a wiring TOML; cost compounds with each new Kiro pack.

## References

- RFC-0022 — `docs/rfc/0022-kiro-adapter-split.md` (the accepted proposal; six decisions, spike results, risks)
- RFC-0005 — `docs/rfc/0005-user-scope-hook-support.md` (user-scope hook support; errata E1–E3 appended)
- RFC-0001 — `docs/rfc/0001-bundle-distribution-by-adapter-spec.md` (adapter spec + build pipeline)
- RFC-0009 — `docs/rfc/0009-codex-native-skills.md` (precedent: single-mode bump for an adapter migration)
- RFC-0011 — `docs/rfc/0011-pack-allowed-adapters.md` (`allowed-adapters`; packs declare `"kiro"`)
- `kiro-adapter-split` spec — `docs/specs/kiro-adapter-split/spec.md`
- `kiro-ide-hook` spec + probes — `docs/specs/kiro-ide-hook/` (PR #99 shipped code; Q11 closed by RFC-0022 E3)
