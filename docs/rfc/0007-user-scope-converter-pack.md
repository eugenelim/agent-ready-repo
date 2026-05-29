# RFC-0007: First user-scope pack — `converters` (file-to-markdown, markdown-to-html, msg-to-markdown)

- **Status:** Accepted
- **Author:** eugenelim
- **Date opened:** 2026-05-24
- **Date closed:** 2026-05-24
- **Related:** [RFC-0004](0004-install-scope-per-pack.md) (the user-scope dimension this RFC consumes); [RFC-0005](0005-user-scope-hook-support.md) (orthogonal hook-user-scope work; this pack carries no hooks); [adapt-to-project spec](../specs/adapt-to-project/spec.md) AC4b user-scope rows (triggered by acceptance); [backlog.md § adapt-to-project](../backlog.md#adapt-to-project--shipped-ac4b-transcripts-deferred).

## Summary

Ship the catalogue's first user-scope pack — `converters` — containing three file-format conversion skills (`file-to-markdown`, `markdown-to-html`, `msg-to-markdown`). The pack declares `default-scope = "user"`, `allowed-scopes = ["user", "repo"]`, ships no `seeds/`, no hooks, and no `<adapt:NAME>` markers, so it passes RFC-0004's three user-scope refusal rails by construction. No contract or schema amendments are required — this RFC is a *consumer* of the dimension RFC-0004 landed.

## Motivation

RFC-0004 landed the user-scope dimension explicitly anticipating "style-only primitives that travel cleanly across every repo an adopter opens" ([RFC-0004 lines 38–52](0004-install-scope-per-pack.md#motivation)), and its acceptance text committed: *"Any follow-up user-scope pack lands as a separate RFC + PR."* No such consumer has landed since. Two costs of inaction:

1. **The dimension stays unexercised.** RFC-0004's `[scope]` table, path-jail-per-scope, `~`-expansion semantics, dual-state-file walking, and `installed: <pack> @ <scope>` rail have unit and integration coverage but no production pack to validate the end-to-end install/upgrade/uninstall path against an adopter's real `~/.claude/` tree. The first user-scope pack is the falsifier the contract has been waiting for.
2. **`adapt-to-project` AC4b stays blocked.** [`docs/backlog.md`](../backlog.md) names "first pack declaring `allowed-scopes = ["user"]` lands" as the trigger to close rows 19–28 of the AC4b manual-QA matrix (user-scope LLM-judgment captures). Until a real user-scope pack ships, those rows can only be simulated.

The three converters in scope are the cheapest correct first consumer: each is a single SKILL.md + a `scripts/` directory of deterministic file processors, with no project-specific vocabulary, no markers, and no `seeds/` to be wrong about. They map cleanly onto the falsifiable test in [RFC-0004 § Per-pack default and allowance](0004-install-scope-per-pack.md#per-pack-default-and-allowance): the same SKILL.md serves every repo verbatim because the skill's input is the adopter's *file*, not the adopter's *project*.

## Proposal

### Pack shape

```
packs/converters/
├── pack.toml
├── .claude-plugin/
│   └── plugin.json
└── .apm/
    └── skills/
        ├── file-to-markdown/
        │   ├── SKILL.md
        │   ├── scripts/
        │   │   ├── convert.py
        │   │   ├── split_image.py
        │   │   └── reconcile.py
        │   ├── references/
        │   │   ├── extractions_schema.md
        │   │   ├── strategy_architecture.md
        │   │   ├── strategy_conceptual.md
        │   │   ├── strategy_domain.md
        │   │   ├── strategy_event-storm.md
        │   │   └── strategy_process.md
        │   └── evals/
        │       └── evals.json
        ├── markdown-to-html/
        │   ├── SKILL.md
        │   ├── package.json       # ecosystem-standard npm manifest; pins marked + highlight.js
        │   ├── scripts/
        │   │   ├── render.js
        │   │   └── template.html
        │   └── evals/
        │       └── evals.json
        └── msg-to-markdown/
            ├── SKILL.md
            └── scripts/
                ├── convert.js
                └── extract-attachments.js
```

No `seeds/` (forbidden by [RFC-0004 § seeds rail](0004-install-scope-per-pack.md#seeds-content-is-repo-only)); no `.apm/hooks/`, no `.apm/hook-wiring/` (forbidden by RFC-0004's hook rail until RFC-0005's user-scope hook-wiring merge ships); no `<adapt:NAME>` markers in any primitive file.

**Rail C verification (run at import time):** `rg -E '<adapt:[A-Z_][A-Z0-9_]*>|<adapt:[a-z][a-z0-9-]*>'` against every file in the source — across both the strict uppercase grammar from [RFC-0004 § *Primitives carrying `<adapt:NAME>` markers are repo-only*](0004-install-scope-per-pack.md#primitives-carrying-adaptname-markers-are-repo-only) and the canonical lowercase-hyphen alternation widened by PR #33 (per the [distribution-adapters spec](../specs/distribution-adapters/spec.md) AC21 carve-out) — returns no matches. The implementation spec re-runs this grep as a plan-task check; `agentbundle validate` re-runs it on install per RFC-0004's enforcement-point rule.

### `pack.toml`

```toml
[pack]
name = "converters"
version = "0.1.0"
description = "File-format conversion skills: documents and images → Markdown; Markdown → styled HTML; Outlook .msg → Markdown."

[pack.adapter-contract]
version = "0.2"

[pack.install]
default-scope = "user"
allowed-scopes = ["user", "repo"]
```

`default-scope = "user"` — the converters' value lands when they're available across every repo the adopter opens (a PDF on the desktop, a Markdown file in any project). `allowed-scopes = ["user", "repo"]` — repo-scope is permitted for adopters who want the converters in exactly one project (e.g. a documentation repo that drives a build pipeline). Both directions pass the falsifiable test: the same SKILL.md serves every repo verbatim.

No `[[pack.dependencies.required]]` block — the converters have no inter-pack catalogue dependencies. They have *runtime* dependencies (`pip`, `npm`) but those are documented in each skill's SKILL.md, not declared in `pack.toml` (see [§ Alternatives considered, item 3](#alternatives-considered)).

### Runtime dependencies

Each skill's SKILL.md documents the one-time install command the agent runs on first invocation. Where an ecosystem-standard manifest already pins versions (npm `package.json`), it ships unchanged in the skill directory:

| Skill | Runtime command | Where deps are pinned |
| --- | --- | --- |
| `file-to-markdown` | `python -m pip install docling Pillow` | SKILL.md prose (no pip lockfile shipped by upstream) |
| `markdown-to-html` | `npm install` (in the skill directory) | `package.json` — `marked ^18.0.2`, `highlight.js ^11.11.1` |
| `msg-to-markdown` | `npm install @nicecode/msg-reader` (with `msgreader` fallback) | SKILL.md prose (no `package.json` shipped by upstream) |

This matches the established pattern — `core`'s reviewer agents already shell out to `gh` and other system tools without a formal dependency declaration in `pack.toml`, and `markdown-to-html`'s `package.json` is the npm ecosystem's settled-standard pin format (we keep it; we don't invent a new TOML field). The pack contract distributes *files*; *runtime provisioning* is the adopter machine's concern. The [agentskills.io specification](https://agentskills.io/specification) is canonical on the layout (`SKILL.md` + `scripts/` + `references/` + `assets/` + optional `evals/`) but has no settled dependency-declaration format as of May 2026 — multiple competing proposals ([discussion #210](https://github.com/agentskills/agentskills/discussions/210), [modelcontextprotocol/registry discussion #895](https://github.com/modelcontextprotocol/registry/discussions/895)) are in active development. Declaring our own per-pack format now risks divergence from whatever the open standard settles on.

### `evals/` directories

Two of three converters ship with `evals/evals.json` in the agentskills.io canonical schema (`skill_name`, `evals[].id`, `prompt`, `expected_output`, `files`, `assertions`); `msg-to-markdown` has no eval suite in the source and ships without one. The rule: **carry `evals/` over verbatim when the source has it; do not synthesise it where absent.** Evals are **carried, not validated** — this PR does not introduce an agentskills.io-runner-style execution step against the imported scripts; running the carried evals is the implementation spec's check (see [Follow-on artifacts](#follow-on-artifacts)) or, if no runner is available at import time, an explicit acknowledgment in the implementation spec's changelog that the suite is preserved without being re-executed. This pack does not propose a wider evals-infrastructure story — that's a separate question for whichever spec eventually owns evaluation.

### Source-attribution scrub

Per `feedback_no_external_catalog_attribution`, every in-tree artifact in this PR avoids naming the source catalogue. The full attribution audit (`rg -i 'dropkit'` against the entire source tree) returns four hits — every one is named below with its disposition:

| # | Hit | Disposition |
| - | --- | ----------- |
| 1 | `markdown-to-html/scripts/render.js:30` — `// dropkit/skills/... or copied into ~/.claude/skills/...` | **Rewrite** in path-neutral terms (`// either at the skill directory or copied into ~/.claude/skills/markdown-to-html/`). |
| 2 | `markdown-to-html/manifest.json:8` — `"author": "dropkit"` | **Drop the whole file** — source-catalogue convention, not agentskills.io-standard. |
| 3 | `file-to-markdown/manifest.json:8` — `"author": "dropkit"` | **Drop the whole file** — same reason. |
| 4 | `msg-to-markdown/manifest.json:8` — `"author": "dropkit"` | **Drop the whole file** — same reason. |

Two further *non-attribution* content decisions get acknowledged here for review-discipline reasons (they're not scrub hits, but they are silent content drops the diff has to own):

- **`msg-to-markdown/manifest.json` `targets` block** — declares per-adapter projection files (`overrides/claude-code.md`, `overrides/kiro.md`, `skill.md`) that don't exist in the source tree. Dropped with the rest of `manifest.json` because (a) it's a source-catalogue convention not part of the agentskills.io standard, (b) the projected files it references don't exist, and (c) per-adapter skill-body forks are an unresolved cross-RFC question, not this pack's to introduce.
- **`markdown-to-html/package.json`** — kept verbatim (the npm ecosystem's settled-standard manifest; carries the version pins for `marked` and `highlight.js`); not in scope for the scrub.

**Enforcement.** The implementation spec lands a pre-merge automated grep (`rg -iE '\bdropkit\b' packs/converters/` exits non-zero on any hit) as a `Tests:` entry on the import task, plus the same grep in CI. Reviewer + commit-message review remains the second line; the automated grep replaces the soft "policed at review time" claim that earlier drafts of this RFC fell back on.

### Distribution-route parity

Handled at system level. The build pipeline ([`docs/specs/distribution-adapters/spec.md` § Recipe set](../specs/distribution-adapters/spec.md#recipe-set-enumerated)) automatically emits `dist/apm/converters/`, `dist/claude-plugins/converters/`, and aggregates the latter into `dist/claude-plugins/marketplace.json` for every pack in `packs/`. Per-pack action is providing `.apm/` source + `pack.toml` + `.claude-plugin/plugin.json`; the recipes do the rest. No new per-pack opt-in.

The *behavioural*-parity gap RFC-0004's roadmap calls out — install-time side effects (`adapt-to-project` install marker, session-start nudge, chained `adapt.run`) only fire via the `agentbundle install` route, not APM or Claude-plugins routes — affects every pack equally and is RFC-0004's follow-on, not RFC-0007's.

## Alternatives considered

1. **Do nothing — keep the catalogue repo-only.** RFC-0004's user-scope dimension stays unexercised; AC4b user-scope rows stay simulation-only; adopters wanting a personal converter copy files into `~/.claude/skills/` by hand (the Tier-3-squatter case RFC-0001 was built to prevent). The dimension was landed deliberately ahead of any consumer; landing the consumer is the deferred half of that decision. *Rejected.*

2. **Three packs (one per converter) instead of one.** Maximum modularity. Rejected: the existing catalogue groups multiple skills per pack by theme (`governance-extras` ships 3, `core` ships 4) — three single-skill packs would multiply the install/uninstall surface and the marketplace entry count for no semantic gain. The three converters share an obvious theme ("convert file X to file Y") and a coherent dependency posture ("runtime deps documented per-skill in SKILL.md").

3. **Declare runtime deps in `pack.toml` via a new `[pack.runtime]` table.** Schema gains `[pack.runtime].python = [...]` / `[pack.runtime].npm = [...]`. Cleaner than SKILL.md prose. Rejected: (a) the agentskills.io ecosystem hasn't settled on a manifest format; competing proposals (`skillpm`, `skills.json`, OCI artifacts, PURL identities) are in active proposal phase, and declaring our own shape now is the recipe for divergence; (b) the pack contract distributes files, not runtime environments — formal deps belong in whatever package manager the adopter's environment uses (`pip`, `npm`, `uv`), not in our pack manifest; (c) the existing `core` pack already shells out to `gh` without a formal declaration. The chosen path is *not* "SKILL.md prose only" — it's **"keep ecosystem-standard manifests where they exist (`package.json` for `markdown-to-html`); fall back to SKILL.md prose where they don't (`pip` deps, single-package npm installs)."** This stays out of the standards bun-fight and respects the npm ecosystem's existing pin format.

4. **Keep the source-catalogue per-skill `manifest.json`.** Preserves originator metadata (deps, file types, tags, author). Rejected: it's a source-catalogue convention, not part of [agentskills.io](https://agentskills.io/specification)'s canonical layout (`SKILL.md` + `scripts/` + `references/` + `assets/` + optional `evals/`); the agentskills.io spec's discovery story uses `/.well-known/agent-skills/index.json` at the *registry* level, not a per-skill `manifest.json`. Keeping it adds non-standard files that confuse the contract and would conflict with `feedback_no_external_catalog_attribution` on the `"author"` field. The information it carries (deps, description, tags) lives more naturally in SKILL.md frontmatter or body.

5. **Declare `default-scope = "repo"` for this pack.** Treat user-scope as adopter-override-only. Rejected: violates the falsifiable test (the converters are exactly the cross-project shape RFC-0004 anticipated) and defeats the whole point of landing a *consumer*. If the pack's natural home is per-repo, the pack shouldn't be user-scope-eligible in the first place. The default-scope is the pack author's recommendation; adopters who want repo-scope override at install time.

6. **Synthesise an `evals/` suite for `msg-to-markdown`.** Uniformity across the three converters. Rejected: writing evals to fill a gap is the inverse of the test-evaluates-behaviour discipline; an eval suite for a converter the author didn't ship one for is a fabrication, not a test. Carry over what exists; don't manufacture.

7. **Bundle the import as a single PR with `adapt-to-project` AC4b row closure.** One-shot fix for the trigger and the rows it unblocks. Rejected: mixing pack ship with manual-QA evidence capture inflates the PR and entangles two reviews (pack content vs transcript validity). The pack PR establishes the trigger; a sibling PR captures the transcripts and closes the rows.

## Drawbacks

- **First-of-its-kind real-world exercise of user-scope mechanics.** Path-jail-per-scope, `~`-expansion failures, dual-state-file walking, and the `installed: <pack> @ <scope>` rail have fixture coverage (see [`docs/specs/agent-spec-cli/spec.md`](../specs/agent-spec-cli/spec.md) AC sections covering scope resolution, path-jail, and dual-state-file walking; and [`docs/specs/distribution-adapters/spec.md`](../specs/distribution-adapters/spec.md) AC sections covering scope-keyed state-file rule and `allowed-prefixes.user` enforcement) but no production pack has exercised the integrated path against a real adopter's `~/.claude/` tree. The three refusal-rail greps (seeds, hooks, markers) run for the first time against a pack that *intends* user scope, not just one that happens to declare it. **Framing reconciled:** RFC-0004 argued the dimension's mechanics could be designed on their own merits; that argument held, and this pack is the integration test — *not* a falsifier that proves the contract wrong by existing, but the first real-world load the contract has carried. The risk is that an environment-specific failure mode (corporate sandbox `$HOME`, locked `~/.claude/`, Windows path handling) surfaces only when an adopter installs. **Mitigation:** (a) the dual `["user", "repo"]` `allowed-scopes` lets adopters fall back to repo scope while a failure is diagnosed, but only if they know to pass `--scope repo` — see the next Drawback for the install-time UX gap that exposes; (b) the implementation spec adds an integration test that installs the pack against a fixture `$HOME` and asserts the resulting state-file shape; (c) the carve-out for environment-specific failures is named in the implementation spec's rollback plan.

- **Dual-scope install-time UX is undefined.** This pack is the first to declare `allowed-scopes = ["user", "repo"]` (every other shipped pack is `["repo"]` only). The CLI's documented behaviour for a *single*-scope pack at user scope is well-pinned in RFC-0004 (refuse-and-explain when `--scope` mismatches `allowed-scopes`), but for a *dual*-scope pack whose default scope fails at install time (e.g. `$HOME` is unset), the CLI emits no hint that the other scope would succeed. Adopters hitting the failure path have to read `agentbundle install --help` to discover `--scope repo`. **Mitigation:** the implementation spec lands an Unresolved-question handoff to a CLI follow-up that adds a `note: pack also installable at scope repo; retry with --scope repo` hint when a dual-scope pack's default-scope install fails. Not gating this RFC, but documented as a known UX gap surfaced by being the first dual-scope consumer.

- **Adopters carry the runtime-dependency burden.** `python -m pip install docling Pillow` is non-trivial in a locked-down environment (Docling downloads ML models on first run, ~1–2 minutes; `pip install` itself may need an internal mirror). Same hazard applies to `npm install marked`. **Mitigation:** each SKILL.md states the deps explicitly upfront; adopters in `pip`/`npm`-hostile environments simply don't invoke the affected converter (the pack itself installs fine; only the runtime steps require the deps). The hazard mirrors [RFC-0006 § rejected `pip install python-dotenv`](0006-skill-secrets-storage.md) — but unlike credential storage, conversion is an opt-in capability per skill.

- **Three new system runtimes enter the catalogue's adopter surface.** Docling + Pillow (Python ML stack), marked + highlight.js (Node front-end stack), msg-reader (Node MAPI parser). Each pulls upstream maintenance dependencies the catalogue does not control. **Mitigation:** runtime deps are declared per-skill, not at pack level; an adopter who installs the pack but never invokes a given converter never resolves its deps. Pinning is the adopter's environment's job (their `requirements.txt`, their `package.json`), not the pack's.

- **`evals/` asymmetry across the three skills.** Two ship with eval suites; one doesn't. Some adopters reading the pack may expect uniform coverage. **Mitigation:** acceptable trade vs the alternative (fabricated tests). Documented in this RFC + in the implementation spec; an issue against `msg-to-markdown` to add an eval suite (sourced from real `.msg` fixtures, not synthesised) is a clean follow-on.

- **Source-catalogue attribution scrub is automated at the pack boundary, not across the repo.** The scrub rule (no in-tree references to the originating catalogue) is enforced by a pre-merge `rg -iE '\bdropkit\b' packs/converters/` exiting non-zero on any hit — landed in the implementation spec as both a `Tests:` entry and a CI check (see [§ Source-attribution scrub](#source-attribution-scrub) above). The remaining risk is repo-wide drift — a contributor adding back the source name in a PR description, a different pack's docs, or a non-`packs/converters/` file (where the grep doesn't run). **Mitigation:** reviewer + commit-message review remains the second line; the memory rule (`feedback_no_external_catalog_attribution`) is canonical for human review. Promoting the grep to a `conventions-check` lint scoped to the whole repo is a follow-on if attribution leaks recur outside `packs/converters/`.

- **npm `node_modules/` install location follows the skill directory.** The runtime `npm install` for `markdown-to-html` writes `node_modules/` into the skill directory — `~/.claude/skills/markdown-to-html/node_modules/` at user scope, `<repo>/.claude/skills/markdown-to-html/node_modules/` at repo scope. The pack does not control whether `.gitignore` covers the latter, and an adopter installing at repo scope can accidentally commit `node_modules/` if their `.gitignore` is silent on `.claude/`. **Mitigation:** the skill's SKILL.md adds a one-line note at the install step naming the location and recommending `.claude/skills/*/node_modules/` in `.gitignore` for repo-scope installs. A pack-shipped `.gitignore` is rejected — pack-shipped dotfiles cross into seed territory, which is forbidden at user scope.

- **Repo's first encounter with shipping third-party-authored content.** The converters were not authored in this repo; importing them creates a maintenance question about upstream sync (do we re-pull future improvements, fork-and-diverge, or treat the import as one-shot?). **Mitigation:** treat as one-shot import in this RFC; if upstream produces meaningful improvements, evaluate a re-import per case. No standing sync obligation.

## Prior art

**In repo:**
- [RFC-0004 § Per-pack default and allowance](0004-install-scope-per-pack.md#per-pack-default-and-allowance) defines the contract this pack consumes; lines 38–52 (Motivation, "style-only primitives") anticipate this pack's shape; line 424 ("Any follow-up user-scope pack lands as a separate RFC + PR") mandates this RFC's existence.
- [RFC-0005](0005-user-scope-hook-support.md) (Draft) — extends the user-scope dimension with hook-wiring merge modes. The converter pack avoids hooks entirely, so RFC-0005's deferral does not constrain it; the contract refuses any user-scope pack that includes hooks until RFC-0005 ships.
- [RFC-0006 § rejected `pip install`-based credential storage](0006-skill-secrets-storage.md) — distinguishes "CLI must not require `pip install`" from "skills the adopter chooses to invoke may require `pip install`." Same reasoning applies here: this pack's *installation* is `pip`-free; only the *running* of certain converters requires runtime deps the adopter resolves.
- [`docs/specs/distribution-adapters/spec.md`](../specs/distribution-adapters/spec.md) § Recipe set — confirms APM and Claude-plugins distribution-route emission is automatic per pack; no per-pack opt-in needed.
- [`docs/backlog.md`](../backlog.md) § `adapt-to-project` AC4b — names the trigger this RFC fires for downstream manual-QA capture.

**External:**
- [agentskills.io Specification](https://agentskills.io/specification) — canonical SKILL.md layout (`SKILL.md` + `scripts/` + `references/` + `assets/`), evals schema (`evals/evals.json` with `skill_name`, `evals[].id`, `prompt`, `expected_output`, `files`, `assertions`), and the discovery manifest at `/.well-known/agent-skills/index.json` (registry-level, not per-skill).
- [agentskills/agentskills discussion #210 — Skill Package Manifest for Dependency Resolution](https://github.com/agentskills/agentskills/discussions/210) — confirms the dependency-declaration question is unsettled across the wider ecosystem as of May 2026; supports the "SKILL.md prose + adopter's package manager" decision.
- [modelcontextprotocol/registry discussion #895 — skills.json format](https://github.com/modelcontextprotocol/registry/discussions/895) — adjacent proposal in the MCP space; same status (active proposal phase, no settled format).
- [Anthropic Skills docs](https://code.claude.com/docs/en/skills) — Claude Code reads `~/.claude/skills/<name>/`; the user-scope install location is well-established at the agent runtime, even if the catalogue distribution model is newer.
- [PEP 723 — Inline script metadata](https://peps.python.org/pep-0723/) — modern Python alternative to `requirements.txt` for single-file scripts (declare deps in a TOML block, run via `uv run`). Not adopted here (requires `uv` as a meta-dep) but a candidate path if a future user-scope pack wants self-resolving Python deps.
- [`anthropics/skills`](https://github.com/anthropics/skills) — Anthropic's reference skill repository; no per-skill `manifest.json`, no `evals/` shipped, flat skill names. Supports dropping the source-catalogue's per-skill `manifest.json`.

## Unresolved questions

- **Will the source catalogue's upstream improvements roll into this pack?** Author's lean: **no, one-shot import — but the import revision is pinned in-repo so re-pull is possible.** Treating this as a vendored snapshot keeps the catalogue's release cadence independent of an upstream we don't control. The implementation spec's changelog records the source commit SHA at import time (in-repo governance text, not in any imported primitive — does not violate the no-attribution rule, which targets imported artifacts and adopter-visible content). A future maintainer evaluating "did upstream fix the docling 3.x bug?" reads the SHA from the spec changelog and diffs upstream from there. No standing sync.
- **Should `conventions-check` grow a "no external-catalog attribution" lint?** Author's lean: **defer until a leak recurs outside `packs/converters/`.** The pack-boundary grep covers the primary risk; a repo-wide lint introduces false-positive risk against legitimate references (spec text discussing other ecosystems by name). Revisit if attribution leaks land elsewhere.
- **Does a future user-scope pack want a `[pack.runtime]` informational field?** Author's lean: **wait for ecosystem signal — defined as either (a) the agentskills.io specification publishes a `dependencies` or `runtime-requirements` section, or (b) [agentskills/agentskills discussion #210](https://github.com/agentskills/agentskills/discussions/210) reaches a merged decision.** Either is an objective trigger a future contributor can answer yes/no on. Until then, ecosystem-standard manifests (`package.json`) carry their pins and SKILL.md prose carries the rest.
- **Should `msg-to-markdown` get an evals suite before merge?** Author's lean: **no, follow-on issue.** Synthesising one defeats the eval discipline (tests must reflect intended behaviour, not be invented to fill a gap). A follow-on with real `.msg` fixtures is the honest path; the implementation spec lists this as a known gap to track.
- **Does landing this RFC by itself close `adapt-to-project` AC4b rows 19–28?** Author's lean: **no.** This RFC's merge produces the *trigger* (first `allowed-scopes = ["user"]` pack lands); the AC4b rows are closed by a sibling PR that captures real-adopter transcripts using the converters pack. If the sibling PR is not written, AC4b stays open with no owner. The Follow-on artifacts section names the sibling PR explicitly; without a committed owner and target date, AC4b is open indefinitely against this RFC's acceptance.

## Follow-on artifacts

On acceptance:

- **Spec:** `docs/specs/converters-pack/spec.md` (via `new-spec`) — defines the import-and-scrub work as a sequence of plan tasks. The spec's Acceptance Criteria pin the following items; the spec author renumbers them as AC-N rather than inheriting these bullets:
  - Source-attribution scrub table (four named hits per [§ Source-attribution scrub](#source-attribution-scrub)) plus the automated pre-merge grep.
  - Rail C grep re-run as a `Tests:` entry — both strict-uppercase and lowercase-hyphen grammars.
  - `evals/` carry-over rule plus an explicit "carried-and-validated" vs "carried-not-validated" line per skill in the spec's changelog.
  - Source commit SHA pinned in the spec's changelog (in-repo revision breadcrumb governance text, not in any imported primitive).
  - Integration-test task that installs the pack against a fixture `$HOME` and asserts the resulting state-file shape (closes the dual-scope-first-consumer integration-test commitment in [Drawbacks § first-of-its-kind](#drawbacks)).
  - `Tests:` entry verifying each skill's `package.json`-vs-SKILL.md-prose disposition matches the [Runtime dependencies table](#runtime-dependencies).
- **Implementation PR (this RFC's primary downstream):** the spec's plan executes — adds `packs/converters/` with the three skills, updates `docs/architecture/overview.md` to name the fifth pack, lands the new `[pack.install]` block in catalogue documentation if any contributor-facing doc enumerates packs. Adds the pre-merge grep + Rail C grep as CI checks.
- **CLI dual-scope-failure UX (separate PR, owner: catalogue maintainers, target: before AC4b sibling PR runs).** Adds the `note: pack also installable at scope <other>; retry with --scope <other>` hint when a dual-scope pack's default-scope install fails per [Drawbacks § dual-scope install-time UX](#drawbacks). Not gating RFC-0007 acceptance, but gating the AC4b sibling PR's real-adopter-transcript capture (so the captures observe the post-fix UX, not the pre-fix gap).
- **`adapt-to-project` AC4b row closure (sibling PR, owner: TBD-with-RFC-reviewer, target: within 30 days of RFC-0007 implementation PR merging).** Captures real-adopter transcripts for rows 19–28 (user-scope LLM-judgment captures) using the converters pack as the falsifying install. Updates [`docs/backlog.md`](../backlog.md) entry; updates [`docs/specs/adapt-to-project/notes/manual-qa-matrix.md`](../specs/adapt-to-project/notes/manual-qa-matrix.md) row-by-row. **Acknowledged: AC4b is not closed by this RFC's merge alone** — the sibling PR is required, and if it is not written, AC4b stays open against this RFC indefinitely (per [Unresolved questions](#unresolved-questions)).
- **`msg-to-markdown` evals follow-up (issue, not PR).** Adds an evals suite sourced from real `.msg` fixtures (not synthesised). No owner committed in this RFC; tracked in the implementation spec's "known gaps" section.
- **No ADR.** This RFC is a consumer of contract decisions already recorded in [ADR-0002](../adr/0002-install-scope-per-pack-default-and-allowance.md); no new architectural choice is made by landing the first consumer.
- **No CONVENTIONS edit.** The pack-author rule "drop source-catalogue attribution from imported skills" already lives in `feedback_no_external_catalog_attribution` memory and is reinforced by the spec's checklist; promoting it to CONVENTIONS is a separate decision if attribution leaks recur outside `packs/converters/`.
