# Plan: pluggable-api-standards

- **Spec:** [`spec.md`](spec.md)
- **Status:** Done <!-- Drafting | Executing | Done -->

> **Plan contract:** this is the implementation strategy. Unlike the spec, this
> document is allowed to change as you learn. When it changes substantially
> (a different approach, not just a re-ordering), note why in the changelog
> at the bottom.

## Approach

A **behaviour-preserving refactor** of the `api-contract` skill in
`packs/contracts`. The shape: lift the Zalando-specific content *out* of
`SKILL.md` into a self-contained, agent-readable standard **bundle** under the
skill's `references/`, leaving `SKILL.md` as the standard-agnostic *method*
that cites "the active standard." Then document the base + delta authoring and
`.upstream` delivery story.

There is no executable code — the bundle is data the agent reads — so
verification is structural (grep over the extracted files) plus eval-style
behavioural QA. The riskiest part is **behaviour-equivalence**: the extraction
must drop no rule and the rewritten method prose must still drive identical
Zalando-default output. The 138-rule-ID grep guards the first; the 3 existing
evals guard the second.

Order of operations: bundle the Zalando standard (T1) → make the method
standard-agnostic (T2) → author the base + delta guide and delivery doc (T3) →
version-bump, re-project, regression-check (T4).

Layout (agentskills.io `references/` + `scripts/`, no invented subtree):

```
packs/contracts/.apm/skills/api-contract/
  SKILL.md                                  # standard-agnostic method; cites "the active standard"
  references/
    standards-manifest-zalando.yaml         # bundled base manifest (name/version/license/provenance/rule-file map)
    standards-quality-gates-zalando.md       # quality-gate checklist (lifted from SKILL.md)
    standards-authoring.md                   # base+delta format + worked example + delivery
    naming-conventions.md                    # existing → Zalando's phase-grouped rule files (enumerated by the manifest)
    http-methods-and-status-codes.md         #   (7 rule .md files kept in place; minimal diff — no rename in Stage 1)
    … (the other 5 rule .md files) …
    golden-example.yaml                      # standard's exemplar (manifest points to it)
    money-1.0.0.yaml / problem-1.0.1.yaml    # reusable schema fragments the standard provides
  evals/evals.json                           # unchanged; behavioural regression guard
```

## Constraints

- **RFC-0017** — D2 (standard = method + data, base + delta), D3 (delivery by
  `adapt-to-project` Class 2 `.upstream` companion-merge), D7 (agent-read, no
  program parses the bundle). Stage 1 of the staged implementation (D6).
- `docs/architecture/overview.md` — compose around `core`; packs don't import
  each other. No `core` ← `contracts` dependency.
- `AGENTS.md` — no new top-level directory; record any new dependency before
  adding (Stage 1 adds none).
- agentskills.io skill structure — supporting files under `references/` /
  `scripts/`.

## Construction tests

Most construction tests live under **Tasks** (per-task `Tests:`). The
cross-cutting concern is **behaviour-equivalence of the Zalando default**,
verified by the 138-rule-ID completeness grep (T1) together with the 3
existing evals re-read against the rewritten skill body (T4) — these two
together assert the refactor changed *structure*, not *output*.

**Integration tests:** none beyond per-task tests.
**Manual verification:** re-read `evals/evals.json` cases 1–3 against the new
`SKILL.md` + bundle and confirm each still describes correct Zalando-default
output (T4).

## Tasks

### T1: Bundle the Zalando standard (manifest + quality-gates + rule files)

**Depends on:** none

**Touches:** `packs/contracts/.apm/skills/api-contract/references/standards-manifest-zalando.yaml`,
`packs/contracts/.apm/skills/api-contract/references/standards-quality-gates-zalando.md`,
`packs/contracts/.apm/skills/api-contract/SKILL.md`

**Tests:** (goal-based)
- **Token-set preservation:** capture the distinct `#NNN` token set over
  `SKILL.md` + `references/**` from `git show HEAD`
  (`grep -rhoE '#[0-9]+' SKILL.md references/ | sort -u` — today **133**
  distinct), then assert the post-change set over the same scope is a
  **superset** — nothing lost in the method→bundle move. Verifies AC "no rule
  token is lost."
- **The SKILL-only tokens land in the bundle.** `comm -23 <(git show
  HEAD:…/SKILL.md | grep -ohE '#[0-9]+' | sort -u) <(grep -rhoE '#[0-9]+'
  references/ | sort -u)` yields **nine** SKILL-only tokens today: the four
  modeling/API-first rules `#100, #102, #139, #140` (→ manifest rule
  enumeration) and the five excluded IDs `#183, #184, #223, #224, #233` (→
  manifest provenance note). Confirm each of the nine has a bundle home after
  the change. Verifies the AC's relocation clause + the excluded-rules AC.
- The 5 excluded IDs (#183, #184, #223, #224, #233) appear **only** in the
  manifest's attribution/provenance note — never in a rule-file rule body or
  the manifest's rule enumeration. Verifies the excluded-rules AC.
- The manifest parses as YAML (one-off `python -c "import yaml,sys;
  yaml.safe_load(open(sys.argv[1]))"` in the dev/CI env — **not** a shipped
  check). Verifies AC "bundled Zalando standard exists as a YAML manifest."
- The relocated quality-gate checklist is **byte-identical** to the block
  lifted from `SKILL.md` (`diff` the new file's checklist region against the
  region in `git show HEAD:…/SKILL.md`); today that is 31 `- [ ]` items, each
  retaining its `#NNN` citation. Verifies the quality-gate AC.

**Approach:**
- Create `references/standards-manifest-zalando.yaml` with `name: zalando`,
  `version`, `license: CC-BY-4.0`, Zalando SE provenance/URL, `extends:` empty
  (it is the base), and a `rules:` / `rule_files:` enumeration mapping the
  method's phase categories (naming, urls, methods/status, representations,
  errors, security, compatibility, events) to the existing rule `.md` files.
  The manifest is the **authoritative enumeration of all applied rule IDs**, so
  it is the home for tokens that no rule file carries — in particular the four
  modeling/API-first rules `#100, #102, #139, #140` (today only in `SKILL.md`)
  and `#101, #103` (today only in `golden-example.yaml`).
- The manifest carries the **attribution/provenance** note — licence and the
  5 excluded internal rules (`#183, #184, #223, #224, #233`) — migrated from
  the `SKILL.md` provenance note (which T2 then drops from the method).
- Move the inlined Quality Gates checklist (the `## Quality Gates` block in
  `SKILL.md`) verbatim into `references/standards-quality-gates-zalando.md`,
  preserving every `- [ ]` item and its `[#NNN]` citation.
- Keep the **7 rule `.md` files** in place as Zalando's phase-grouped rule
  files; the manifest enumerates them by path (no rename — minimal diff; the
  namespacing convention for *future* standards is documented in T3).
- Account for the **3 non-`.md` reference assets** explicitly so none is
  orphaned: `golden-example.yaml` (the standard's exemplar — manifest points to
  it), and `money-1.0.0.yaml` + `problem-1.0.1.yaml` (reusable schema fragments
  the standard provides). These stay standard-provided reference assets, not
  method-shared.

**Done when:** token-set preservation holds, the manifest parses, and the
checklist relocation is byte-identical with all 10 reference files accounted
for.

### T2: Make `SKILL.md` the standard-agnostic method (+ design-discipline section)

**Depends on:** T1

**Touches:** `packs/contracts/.apm/skills/api-contract/SKILL.md`

**Tests:** (goal-based)
- Grep asserts **no literal `[#NNN]`** Zalando references remain in the
  `SKILL.md` method or quality-gate prose; the only rule-level detail is a
  pointer to "the active standard" and its bundled manifest. Verifies AC
  "method prose cites the active standard … no literal `[#NNN]` remain."
- Grep confirms all 7 method phases are still named in `SKILL.md` (the method
  is preserved, only the rule citations move).
- The new **Design discipline** section exists and contains no literal
  `[#NNN]`, and its red flags name **no defaulted rule** — grep confirms no
  "Problem JSON" / specific-media-type / pagination-policy / URL-grammar /
  versioning-strategy assertion stated as law; they are phrased as
  consistency-against-the-active-standard properties. Verifies the AC
  "standard-independent Design discipline section" and its Testing-Strategy
  goal-based mode.

- Rewrite phase prose to cite "the active standard" and to load "the active
  standard's rule files" instead of literal `[#NNN]`. This includes the
  `## Your Role` API-first line (`#100`), the Phase-1 modeling citations
  (`#102, #139, #140`), and the **`## Output Format`** section (which today
  carries `[#116][#218]`, `[#215]`, `[#176]`, `[#225]`, etc.) — all three are
  method prose and must lose their literal citations. The four
  modeling/API-first tokens are preserved in the manifest (T1), not the method.
- Drop **both** Zalando-specific attribution surfaces from `SKILL.md`: the
  line-9 provenance note (`138 of 143 rules apply…` + the 5 excluded IDs) and
  the bottom CC-BY-4.0 footer (`_Based on the Zalando RESTful API Guidelines…_`,
  ~line 174). Both move to the manifest (T1); the method keeps at most a generic
  "based on the active standard" pointer. Add the footer to this task's edits.
- De-cite the `## Reference Files` index too: replace the literal
  `All 20 event rules (#194-#247)` span with a generic "event rules"
  description — those tokens survive in `events.md`, so this is method-purity,
  not token loss.
- Replace the inlined `## Quality Gates` section with a pointer to the active
  standard's quality-gate checklist (the file from T1), naming Zalando as the
  default base.
- Update the reference-file table so rule files are described as
  standard-provided, and add a one-line pointer to `standards-authoring.md`.

The no-defaulted-rule grep for the Design-discipline section is scoped to
**`SKILL.md` only** (the lifted quality-gate file legitimately names
`application/problem+json` as bundle data — it must not be in grep scope).
- Keep the frontmatter `description` accurate (it currently says "138 RESTful
  API rules"; reword to "the active standard's rules (Zalando by default)").
- Add a `## Design discipline` section (standard-independent):
  - *Rationalizations to reject* — the contract is the documentation, author
    it first (API-first); Hyrum's Law (every observable behaviour is a de-facto
    commitment); internal APIs still have consumers, so they still need a
    contract; compatibility is a day-one design concern (specifics per the
    active standard).
  - *Red flags* (phrased as consistency-against-the-active-standard, never a
    defaulted rule) — a representation's shape varies across endpoints without
    the active standard sanctioning it; error shape varies across endpoints
    without the active standard sanctioning it; unplanned breaking changes to
    existing fields; authoring without first loading the active standard's
    rules.
  - A one-line note that rule-specific values (pagination, error media type,
    URL grammar, versioning strategy) are owned by the active standard — Zalando
    sets the bundled defaults — **not** restated here as method law.
  - Do **not** import casing/language/code-architecture guidance, and do not
    name any external source catalog ([[feedback_no_external_catalog_attribution]]).

**Done when:** the no-`[#NNN]` grep is clean, all 7 phases remain, the
Design-discipline section passes its standard-independence grep, and the
default-Zalando path reads identically in intent to the pre-refactor skill.

### T3: Author the base + delta guide and delivery doc

**Depends on:** T1

**Touches:** `packs/contracts/.apm/skills/api-contract/references/standards-authoring.md`,
`packs/contracts/.apm/skills/api-contract/SKILL.md`

**Tests:** (manual QA)
- The worked-example delta (`extends: zalando`, one `rules: {"129": false}`,
  one `adds` house rule) is accompanied in the guide by its **explicitly
  enumerated resolved effective ruleset** (base, minus the disabled rule, plus
  the added rule). The check is "the stated resolution matches what the
  override-to-`false` + `adds` semantics dictate" — a checkable artefact, not an
  unobservable agent behaviour. Verifies AC "authoring guide documents the
  base + delta format … plus a worked example."
- The guide names the `adapt-to-project` **Class 2** `.upstream` delivery and
  the scope rule (follows the pack's `allowed-scopes`: user-scope merge once;
  repo-scope when an organisation pins its standard to a single repository),
  plus the explicit "no new resolver, no `adapt` edit" note. Verifies AC
  "delivery via Class 2 companion merge."

**Approach:**
- Write `references/standards-authoring.md`: manifest field reference; base +
  delta resolution; the **filename-namespacing convention**
  (`standards-manifest-<name>.yaml`, `standards-quality-gates-<name>.md`) so
  multiple standards coexist in `references/`; a complete worked example for a
  sample organisation, with its resolved effective ruleset enumerated.
- Add a "Delivering a custom standard" section pointing at `adapt-to-project`
  Class 2 `.upstream` companion-merge, with the scope guidance, and an explicit
  "no new resolver, no `adapt` edit" note.
- Link the guide from `SKILL.md`.
- *(Optional, recommended)* note that adopters may add a 4th eval exercising a
  custom-standard delta as their own behavioural guard — not shipped here.

**Done when:** the guide is complete with a worked example whose resolved
effective ruleset is enumerated, the Class 2 delivery section is present, and
the guide is linked from `SKILL.md`.

### T4: Version bump and source-pack regression gate

**Depends on:** T1, T2, T3

**Touches:** `packs/contracts/pack.toml`, `packs/contracts/.claude-plugin/plugin.json`

**Tests:** (goal-based + manual QA)
- The pack version is `0.2.0` in **both** `pack.toml` and
  `.claude-plugin/plugin.json`; `[pack.adapter-contract]` is still `0.8`.
  Verifies the version-bump AC.
- **Source-pack gate green** — `contracts` is *not* projected by `build-self`
  (it's a user-scope-default pack, excluded from `SELF_HOST_PACKS`), so the gate
  is: `make lint-packs` passes; `agentbundle validate packs/contracts` passes;
  `make build` succeeds and `contracts` aggregates into the dist marketplace;
  and the shipped-pack-manifest pytest
  (`packages/agentbundle/tests/unit/test_shipped_pack_manifests.py` +
  `…/build/tests/test_shipped_packs_v08_declarations.py`) stays green. Do
  **not** run `build-self` / `pre-pr` / `lint-agent-artifacts` for this change —
  they only see projected working-tree `.claude/` artifacts, which exclude
  `contracts`. Verifies the source-pack-gate AC.
- (Manual QA) re-read `evals/evals.json` cases 1–3 against the new skill body;
  each still describes correct Zalando-default output. Verifies the
  no-regression AC.
- `git status` shows no `core` edit and no repo-level `contracts/` dir
  (Stage 2 boundary); generated `dist/` artifacts stay gitignored
  ([[feedback_gitignore_silent_skip]]). Verifies the Stage 2-boundary AC.

**Approach:**
- Bump `version` to `0.2.0` in `pack.toml` **and** `.claude-plugin/plugin.json`
  (kept in sync); leave `[pack.adapter-contract]` at `0.8`.
- Run the source-pack gate above (lint-packs → validate → build → pytest).
- Re-read the evals; if any case now reads ambiguously against the rewritten
  body, that's a T2 regression — fix T2, not the eval.

**Done when:** the source-pack gate is green, evals still valid, the version is
synced across both manifests, and the boundary is intact.

## Rollout

Ships in `contracts` **0.2.0**. Backward-compatible: Zalando is the default
base, so existing users need no action. Adopters who want a custom standard use
the documented `adapt` Class 2 flow. Fully reversible — revert the pack.

## Risks

- **Extraction drops a rule.** → 138-ID completeness grep (T1) is the gate.
- **Rewritten prose subtly changes default behaviour.** → the 3 existing evals
  (T4) are the behavioural guard; a regression fails the eval re-read, not the
  grep.
- **`references/` namespacing collides when a 2nd standard arrives** via
  `.upstream`. → the filename-prefix convention (`standards-…-<name>`) is
  documented in T3 before any second standard exists.
- **Refactoring shipped `contracts` 0.1.0 regresses existing Zalando users.** →
  behaviour-equivalence ACs + evals; the diff is structure-only.

## Changelog

- 2026-05-31: initial plan. YAML manifest (enterprise-portable, agent-read,
  no parser dependency); no Stage-1 linter (authoring guidelines only); bundle
  laid out under `references/` per agentskills.io. T2 also adds a
  standard-independent design-discipline section (rejected rationalizations +
  red flags); rule-specific items deferred to the active standard, and
  casing/language/code-architecture guidance excluded. Decisions per RFC-0017
  and user confirmation 2026-05-31.
- 2026-05-31: assumption-verification correction. Confirmed `contracts` is **not**
  projected by `make build-self` (excluded from `SELF_HOST_PACKS`,
  self_host.py:86,93). T4 retargeted from the projected-artifact gate
  (`build-self` / `lint-agent-artifacts`) to the **source-pack** gate
  (`lint-packs` + `agentbundle validate packs/contracts` + `make build` +
  shipped-pack pytest). Version bump now spans both `pack.toml` and
  `.claude-plugin/plugin.json`, leaving `[pack.adapter-contract]` at `0.8`.
