# Spec: pluggable-api-standards

- **Status:** Shipped <!-- Draft | Approved | Implementing | Shipped | Archived -->
- **Owner:** eugenelim
- **Plan:** [`plan.md`](plan.md)
- **Constrained by:** RFC-0017

> **Spec contract:** this document defines what "done" means. The implementing
> PR must match this spec, or update it. Verification must be derivable from it.

## Objective

Turn `api-contract` from a Zalando-hardcoded skill into a **standard-driven
engine**: the skill keeps the API-design *method*, and the ruleset becomes
swappable *data*. An organisation with its own API guidelines can supply a
standard as a **base + delta** YAML bundle — `extends: zalando`, override
inherited rules to `false`, add house rules (the model Spectral popularised) —
and have `api-contract` author against it, **without forking the skill**.
Zalando ships as the bundled, replaceable *base* standard, so existing users
see no change.

The user is an organisation with its own API guidelines: the catalogue must be
ready for many **different organisations**, each with their own standard, not
only Zalando shops. Today such an org would have to fork the skill. Success:
that org authors a short delta bundle, its rules apply during contract
authoring, and the bundled Zalando default still produces identical output for
everyone who doesn't supply a delta.

This is **Stage 1** of RFC-0017 and is deliberately scoped to the `contracts`
pack only. The `new-spec` seam, the repo-level `contracts/<type>/` tree,
bidirectional traceability, and the `adapt-to-project` Class 3 amendment are
**Stage 2** (`spec-contract-seam`) and are out of scope here.

## Boundaries

The three-tier guard that keeps an implementing agent inside the lines.
*Always do* applies without asking; *Ask first* requires human sign-off
before proceeding; *Never do* is a hard rule, even under time pressure.

### Always do

- Preserve all **138 applied** Zalando rule IDs and their normative text
  through the extraction — the bundled Zalando standard must be
  behaviour-equivalent to today's hardcoded skill.
- Preserve the **CC-BY-4.0 attribution** and Zalando SE provenance in the
  standard manifest (a legal requirement, not a style choice).
- Keep existing direct `api-contract` invocations working unchanged — Zalando
  is the default base; no new required input.
- Keep the standard bundle **agent-readable** (YAML manifest + markdown rule
  and quality-gate files); the agent resolves base + delta by *reading*, not a
  program.
- Keep any design-discipline guidance added to the method **standard-
  independent** — name no specific rule (pagination, error media type, URL
  grammar, versioning strategy) as method law; point rule-specifics to "the
  active standard."
- Edit source under `packs/contracts/.apm/skills/api-contract/…`. The
  `contracts` pack is **user-scope-default and not projected by
  `make build-self`** (excluded from `SELF_HOST_PACKS` — core +
  governance-extras only), so verify via the **source-pack** gate:
  `make lint-packs`, `agentbundle validate packs/contracts`, and `make build`
  (dist aggregation) — **not** `build-self` / `pre-pr` / `lint-agent-artifacts`,
  which only see the projected working-tree `.claude/` artifacts.
- Lay bundle files out under the skill's `references/` and `scripts/` per the
  agentskills.io structure — no invented subtree.

### Ask first

- Changing the default base standard away from Zalando.
- Dropping, renaming, or re-numbering any of the 138 applied rules during
  extraction (the 5 excluded Zalando-internal rules stay excluded).
- Changing the `contracts` pack's `allowed-scopes` or `allowed-adapters`.
- Adding **any** runtime or build dependency (e.g. a YAML parser) to ship the
  feature.

### Never do

- Introduce the `new-spec` seam, the `Contract:` spec header, the repo-level
  `contracts/<type>/` tree, bidirectional traceability, or the
  `adapt-to-project` Class 3 amendment — all of those are **Stage 2**
  (`spec-contract-seam`).
- Make `core` import from or depend on `contracts` (preserve the
  no-cross-pack-imports invariant from `docs/architecture/overview.md`).
- Add a **runtime multi-standard resolver** (deferred — RFC-0017 Open Q1).
- Add a new top-level directory or a new package.
- Ship a non-Zalando standard bundle (Google AIP, Microsoft REST, …) — Stage 1
  ships the *mechanism* and the *Zalando starter* only.
- Add a program or linter that parses the bundle — Stage 1 is guidelines-only;
  the first persistent contract lint is Stage 2's traceability gate.
- Import casing/language-specific or implementation-level guidance into the
  standard-agnostic method (camelCase-vs-snake_case, TypeScript patterns,
  validation-placement or third-party-sanitization code flags) — these conflict
  with the active standard or aren't about the contract artefact.

## Testing Strategy

There is **no executable code** in Stage 1: the standard bundle is agent-read
data (no program parses it — matching RFC-0017 D7 and the agent-skills
ecosystem norm). So TDD has nothing to bind to; correctness is "the bundle is
complete and the agent applies it." The modes:

- **Extraction completeness & behaviour-equivalence** — *goal-based check.*
  Grep/structural assertions over the extracted files (all 138 rule IDs
  survive; no orphaned literal `[#NNN]` in the method prose; quality-gate
  checklist item count preserved). Run once at gate time; nothing shipped.
  *Why:* a compiler/grep proves these objectively; a unit test would be a
  tautology.
- **Base + delta format is well-formed and resolvable** — *manual QA.* A
  worked-example delta (`extends: zalando`, one `rules: {id: false}`, one
  `adds`) in the authoring guide, which an agent reading guide + delta can
  resolve into the correct effective ruleset. *Why:* resolution is agent
  behaviour, not program output — verify the artefact the agent reads.
- **No behavioural regression for the Zalando default** — *manual QA via the
  existing evals.* The 3 cases in `evals/evals.json` still describe correct
  Zalando-default output against the rewritten skill body. *Why:* the evals are
  the behavioural guard that the refactor changed structure, not output.
- **Standard-independence of the design-discipline section** — *goal-based
  check.* The section exists in the method and contains no literal `[#NNN]`
  and no rule-specific assertion (pagination/error-format/URL-grammar/
  versioning) stated as law. *Why:* a grep proves the no-rehardcode invariant
  objectively.
- **Custom-standard delivery is documented** — *manual QA.* The authoring guide
  names `adapt-to-project` Class 2 `.upstream` companion-merge, the scope rule,
  and the explicit "no new resolver, no `adapt` edit" constraint. *Why:* the AC
  is a documentation obligation; the check is that the doc says the right thing.

## Acceptance Criteria

- [x] `api-contract/SKILL.md` method prose cites **"the active standard"**
  generically; no literal Zalando `[#NNN]` rule references remain in the
  method or quality-gate prose (they live only in the standard bundle).
- [x] A bundled Zalando standard exists as a **YAML manifest** at
  `references/standards-manifest-zalando.yaml`, declaring `name`, `version`,
  `license` (CC-BY-4.0), Zalando SE provenance, and an enumeration of its
  phase-grouped rule files.
- [x] **No rule token is lost in the method→bundle move:** the set of distinct
  `#NNN` tokens over `SKILL.md` + `references/**` after the change is a
  **superset** of the `git show HEAD` baseline over the **same** scope. That
  baseline today is **133 distinct tokens** (token count ≠ rule count: the
  standard applies 138 of Zalando's 143 rules, but rules co-cite and some tokens
  appear only in `golden-example.yaml`). Nine tokens are cited **only** in
  `SKILL.md` today and so must be given a bundle home before the method is
  de-cited: the four modeling/API-first rules #100, #102, #139, #140 (→ manifest
  rule enumeration, as they exist in no rule file) and the five excluded IDs
  (→ manifest provenance note, per the next criterion).
- [x] The **manifest** is the authoritative enumeration of the standard's
  applied rule IDs and carries the attribution/provenance — licence (CC-BY-4.0)
  and the 5 excluded internal rules (#183, #184, #223, #224, #233). The 5
  excluded IDs appear in that provenance note only, never as an active rule in a
  rule-file body or the manifest's rule enumeration (as `SKILL.md`'s provenance
  note holds them today, before that note moves to the manifest).
- [x] The quality-gate checklist is carried in
  `references/standards-quality-gates-zalando.md` (lifted out of `SKILL.md`) as
  an agent-verifiable `- [ ]` checklist that is **byte-identical** to the block
  lifted from `SKILL.md` (verified by diff against `git show HEAD`); today that
  is **31** `- [ ]` items, each retaining its `#NNN` citation.
- [x] An authoring guide at `references/standards-authoring.md` documents the
  base + delta format — `extends: zalando`, `rules` override-to-`false`
  (the Spectral model), `adds` for house rules — plus a worked example and the
  filename-namespacing convention for multiple standards coexisting in
  `references/`.
- [x] The authoring guide documents delivery via `adapt-to-project` **Class 2**
  `.upstream` companion-merge at the pack's scope (no new resolver, no edit to
  `adapt-to-project`).
- [x] `SKILL.md` carries a **standard-independent "Design discipline" section**
  — rationalizations to reject (contract-is-the-docs / Hyrum's Law /
  internal-APIs-are-contracts / compatibility-is-a-day-one-concern) and red
  flags phrased as **consistency properties** (a representation's shape varies
  across endpoints without the active standard sanctioning it; error shape
  varies across endpoints without the active standard sanctioning it; unplanned
  breaking changes to existing fields; authoring without first reading the
  active standard) — with rule-specific values (pagination, error media type,
  URL grammar, versioning) explicitly deferred to the active standard, no
  literal `[#NNN]` and no defaulted rule (e.g. "apply Problem JSON") stated as
  method law.
- [x] Existing direct `api-contract` invocations produce Zalando-default output
  unchanged — the 3 existing evals still describe correct output against the
  new skill body.
- [x] The `contracts` pack version is bumped `0.1.0` → `0.2.0` in **both**
  `packs/contracts/pack.toml` and `packs/contracts/.claude-plugin/plugin.json`
  (kept in sync) — a **minor** bump: additive standard-bundle surface, no
  breaking change to existing direct invocations. `[pack.adapter-contract]`
  version is left at `0.8` (pinned by the shipped-pack-manifest test).
- [x] The source-pack gate is green: `make lint-packs`,
  `agentbundle validate packs/contracts`, and `make build` (dist build succeeds
  and `contracts` aggregates into the marketplace), and the shipped-pack-manifest
  pytest still passes.
- [x] No `core` edit, no repo-level `contracts/` directory, and no `new-spec`
  change — the Stage 2 boundary is respected.

## Assumptions

- Technical: the Zalando rules are already file-separated into 7
  `references/*.md` and the quality-gate checklist is inlined in `SKILL.md`
  (lines 74–128), so extraction is mechanical (source: repo read,
  `packs/contracts/.apm/skills/api-contract/`).
- Technical: the manifest is **YAML** for enterprise portability and toolchain
  alignment (OpenAPI/AsyncAPI/Spectral/CI all YAML); it is agent-read and no
  program parses it, so no YAML-parser/lint dependency is taken (source: user
  confirmation 2026-05-31).
- Technical: **no Stage-1 linter** — authoring guidelines only; the first
  persistent contract lint is Stage 2's traceability gate (source: user
  confirmation 2026-05-31).
- Technical: Spectral is Node-only with no official Python port; it remains the
  adopter's external validator of the *emitted* OpenAPI, out of scope here
  (source: web search, stoplight.io / github.com/stoplightio/spectral
  2026-05-31).
- Technical: the agent-skills ecosystem norm for API-design skills is
  prose + checklist, opinionated, with no pluggable ruleset and no in-skill
  linter — so base + delta is novel and the no-lint shape is idiomatic
  (source: web survey of public agent-skill catalogs; Claude skills docs;
  2026-05-31).
- Technical: `adapt-to-project` (in `packs/core`) Class 2 companion-merge is
  generic and already shipped — Stage 1 ships a `.upstream`-mergeable bundle
  and edits no `adapt` machinery (source: repo read,
  `packs/core/.apm/skills/adapt-to-project/SKILL.md` §Class 2).
- Process: RFC-0017 is Accepted and stages this as Stage 1, independent of the
  Stage 2 seam (source: `docs/rfc/0017-pluggable-api-contract-standards.md`).
- Process: `contracts` is **not** projected by `make build-self` (excluded from
  `SELF_HOST_PACKS` — `self_host.py:86,93`; verified: `.claude/skills/` has no
  `api-contract`), so the gate is the source-pack path —
  `make lint-packs` + `agentbundle validate packs/contracts` + `make build` +
  the shipped-pack-manifest pytest, not the projected-artifact lints (source:
  repo read 2026-05-31).
- Product: the catalogue must be ready for many different organisations, each
  with its own API guidelines, needing a non-Zalando standard applied without
  forking the skill (source: confirmed by author 2026-05-31).
- Decision: a standard-independent **design-discipline** section (rejected
  rationalizations + red flags) is included in the method this stage;
  rule-specific items (pagination, error format, URL grammar, versioning) are
  deferred to the active standard, and casing/language/code-architecture
  guidance (camelCase-vs-snake_case, TypeScript patterns, validation placement)
  is excluded as conflicting or out-of-lane (source: analysis 2026-05-31).
