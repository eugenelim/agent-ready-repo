# Spec: phase-policy registry and deterministic selector

- **Status:** Shipped <!-- Draft | Approved | Implementing | Shipped | Archived -->
- **Owner:** eugenelim
- **Plan:** [`plan.md`](plan.md)
- **Constrained by:** ADR-0061, ADR-0093
- **Brief:** docs/product/briefs/phase-scoped-policy-delivery.md
- **Discovery:** none
- **Contract:** none
- **Shape:** data

> **Spec contract:** this document defines what "done" means. The implementing
> PR must match this spec, or update it. Verification must be derivable from it.

## Objective

A maintainer declares which policy families a work-loop phase teaches, in one
registry inside the `work-loop` skill, and a deterministic selector turns a
phase into the exact ordered families that phase selects. The user is the
work-loop controller: it hands the selector one selection key — an
`engine-state.json.state` value, or the reserved constant `DIRECT-LIGHT` for the
light path that creates no engine state — and receives a delivery record naming
which families were selected, in order, each family's enforcement tier, and the
identity and digest of the teaching text that carries each family's rule.

Success is that a phase which should teach something never selects nothing, that
every legal phase has an answer, that the record names teaching text by a
locator resolving to the copy an acting agent reads rather than by a path that
exists only in one repository, and that a malformed registry fails before any
brief is built rather than delivering silently wrong policy. The record
establishes *which file* carries a family's rule and fingerprints it; whether
that file still contains the rule is the arrival validator's question.

Selection is the whole of this contract. Assembling teaching text into a
dispatch brief, and checking that it arrived, belong to later slices.

## Durable Outputs

| Semantic role | Applicability | Destination | Owner | Expected evidence | Closeout condition |
| --- | --- | --- | --- | --- | --- |
| Interface compatibility | Applicable — the delivery record is the binding this slice publishes to `policy-arrival-validator`'s V1 | `packs/core/.apm/skills/work-loop/references/policy-families.md` | work-loop skill | AC1, AC2, AC3 green | The reference documents every delivery-record field, including `assembled_brief_digest`, which this slice declares and leaves unpopulated |
| Current architecture | Applicable — this is the first script-read data under a `references/` tree, which the layout reference currently describes as holding neither data nor a machine-read format | `docs/architecture/pack-layout.md`, the `skill` row of its primitive table | architecture docs | The row names `references/` as able to carry an authored machine-read block | An architecture reader learns the boundary changed without opening a frozen plan |
| User promise | Applicable — adopters declare, classify, and troubleshoot a family | `guides/core/reference/phase-scoped-policy-delivery.md` | guides/core | `tools/validate_guides.py` clean, and the heading and identifier assertions in the registry suite | Guide carries `pack: core` and `kind: reference` frontmatter, names all five family identifiers and the token `DIRECT-LIGHT`, and carries the three literal headings `## Declaring a family`, `## Classifying a family`, and `## Troubleshooting a selection` |
| Decision rationale | Not applicable | — | — | — | ADR-0093 governs and does not fire: its scope is `agentbundle-okf/v1` bundles, and this registry is neither an OKF corpus nor a runtime corpus lookup |
| Release history | Applicable — core gains an adopter-visible capability | `docs/product/changelog.md`, `packs/core/pack.toml`, `packs/core/.claude-plugin/plugin.json` | core pack | `make build-check` green | A `## [core][2.25.0]` section directly beneath `[Unreleased]`, both version strings equal, and `web/src/lib/now-highlights.generated.json` regenerated. Packs carry no `CHANGELOG.md`; only published packages do. |
| Product truth | Applicable — the brief's Spec map and the spec index must name this spec | `docs/product/briefs/phase-scoped-policy-delivery.md`, `docs/specs/README.md` | brief owner | `lint-brief-coverage.py` exits 0 | Spec map carries the bare identifier `phase-policy-registry-and-selector`, and the index's Active-specs table carries its row |

## Boundaries

The three-tier guard that keeps an implementing agent inside the lines.
*Always do* applies without asking; *Ask first* requires human sign-off
before proceeding; *Never do* is a hard rule, even under time pressure.

### Always do

- Resolve a family's teaching text to the file an acting agent would actually
  read in the environment the selector runs in, preferring an installed skill or
  adopter-root copy over the catalogue source.
- Take the legal phase domain from `loop-engine.py`, never from the registry.
- Keep every family's teaching text in the file that already owns that rule. The
  registry records where a rule lives; it never becomes a second copy.

### Ask first

- Adding, removing, or re-tiering a policy family. The family set and its tiers
  are an owner decision dated 2026-09-03 and recorded in this spec's
  § "Assumptions", not an implementation detail. The brief records the candidate
  rule set and delegates classification here.
- Reading any phase signal other than `engine-state.json.state` and the reserved
  token set.
- Giving any selection key an empty family list beyond the five this spec names.
  An empty selection is how a registry silently stops delivering policy.

### Never do

- Create a new top-level directory, a new skill subdirectory outside `scripts`,
  `references`, `assets`, and `evals`, or a new dependency. The selector uses the
  standard library only.
- Assemble a dispatch brief, compute a digest over assembled teaching text, or
  decide whether a policy was obeyed. Those are D2, D3, and V1.
- Infer a phase from headings, prose, filenames, or agent role.
- Give a family a `module` locator that names a generated projection path, or
  edit a projection directly. The locator names the rule's authoring owner; where
  a projection and its seed both exist, the seed is that owner. Resolution is a
  separate question — it deliberately reads the live copy an agent sees, per
  § "Acceptance Criteria" → "Locator resolution".

## Testing Strategy

Every behavior here is deterministic table-driven logic over authored data, so
**TDD** is the mode for all of it, at the **unit** surface — except the
projection landing paths, which are **goal-based** at the **integration**
surface because they can only be observed after a real build.

| Objective behavior | Mode | Why |
| --- | --- | --- |
| A phase that should teach something never selects nothing | TDD, unit | The registry's selection map is a fixed authored value, so a literal comparison catches an emptied or thinned map |
| Every legal phase has an answer | TDD, unit | The domain is derivable from code, so the test enumerates rather than asserting a count |
| The record identifies and fingerprints the teaching text an agent would read | TDD, unit | Resolution and digesting are pure functions over files present in the tree |
| A malformed registry fails before delivery | TDD, unit | Each refusal is a separate authored bad input with its own expected exit status |
| The registry reaches both adapters and selects correctly there | Goal-based, integration | Only a real two-adapter build shows where a file lands and what a projected copy selects |

**Stub tally.** Stubs cover AC3, AC6, AC7 and AC8 — one contract-surface
assertion per TDD task. AC1, AC2, AC4 and AC5 are uncovered by a stub and build
out behind those four in EXECUTE. AC9 and the guide and release obligations are
`no stub (goal-based check)`: their outcomes are only observable after a real
build or are already verified by a shipped gate.

AC9 compares each projected copy against a literal sequence rather than against
the other projection. § "Assumptions" carries that reasoning and is its single
home.

## Acceptance Criteria

Every criterion names a literal string in a named file. A paraphrased criterion
over prose cannot fail, because the implementer supplies the comparison value.

The criterion count sits at the brief's ceiling, raised to nine by an explicit
owner decision; § "Assumptions" is its single home and records what was traded.

**Locator resolution, stated once here rather than inside a criterion.** A
`skill:<name>/<path>` locator resolves to the first of
`.claude/skills/<name>/<path>`, `.agents/skills/<name>/<path>`, or
`packs/core/.apm/skills/<name>/<path>` that exists. A `seed:<path>` locator
resolves to `<path>` if it exists and otherwise `packs/core/seeds/<path>`. Both
orders prefer the copy an acting agent reads over the catalogue source. This is
contract rather than construction, because V1 must know which file was digested;
it sits outside the checklist because a search order is a call sequence, and a
criterion bundling two algorithms is not one predicate.

- [x] **AC1:** `packs/core/.apm/skills/work-loop/references/policy-families.md`
      carries exactly one fenced block, its info string is the literal
      `json policy-registry.v1`, it parses as JSON, and its `schema_version` is
      the integer `1` such that the info string's trailing token is `v` followed
      by that integer.
- [x] **AC2:** that block's `families` array is exactly these five records, by
      `id`, `tier`, and `module`, in this order — `observable-outcome` /
      `precise` / `skill:new-spec/assets/spec.md`; `repository-anchoring` /
      `precise` / `skill:new-spec/assets/plan.md`; `new-spec-step-5a` /
      `advisory` / `skill:new-spec/SKILL.md`; `the-razor` / `advisory` /
      `seed:AGENTS.md`; `cognitive-load` / `advisory` /
      `seed:.agents/rules/cognitive-load.md`.
- [x] **AC3:** that block's `selection` object is exactly this mapping —
      `SPEC-PLAN-DRAFTING` and `SPEC-PLAN-REVIEW` each to
      `["observable-outcome", "repository-anchoring", "new-spec-step-5a", "the-razor", "cognitive-load"]`;
      `CODE-IMPLEMENTATION`, `CODE-VERIFICATION` and `CODE-REVIEW` each to
      `["the-razor", "cognitive-load"]`; `DIRECT-LIGHT` to
      `["the-razor", "cognitive-load"]`; and `SPEC-HUMAN-GATE`,
      `PLAN-HUMAN-GATE`, `SPEC-PLAN-APPROVED`, `CODE-HUMAN-GATE` and `DONE` each
      to `[]`.
- [x] **AC4:** the `selection` object's key set equals the set of state strings
      reachable as a transition source or target in
      `packs/core/.apm/skills/work-loop/scripts/loop-engine.py`, plus the literal
      key `DIRECT-LIGHT`, with that state set obtained from `loop-engine.py`
      rather than transcribed into the test or read from the registry.
- [x] **AC5:** `select-policy-families.py --registry <file> --root <dir> <key>`
      exits `0` and writes to stdout one JSON object and nothing else, whose
      top-level keys are exactly `selection_key`, `families`, and
      `assembled_brief_digest`, with `selection_key` equal to the positional key
      argument and `assembled_brief_digest` `null` for every key. Diagnostics go
      to stderr on every path, so `json.loads` over the whole of stdout succeeds.
- [x] **AC6:** for every selection key, the `id` sequence of the printed
      `families` array equals that key's list in the registry's `selection`
      object, element for element and in the same order.
- [x] **AC7:** each printed family entry equals that `id`'s record in the
      registry's `families` array — same `tier`, same `module` — extended with a
      `module_digest` holding the SHA-256 of the file that record's `module`
      resolves to under `--root`, as 64 lowercase hexadecimal characters with no
      prefix, matching the repository idiom pinned at
      `packs/core/.apm/skills/work-loop/scripts/loop-cohort.py:505`
      (`_SHA256_RE = re.compile(r"^[0-9a-f]{64}$")`).
- [x] **AC8:** the selector exits non-zero, printing a message beginning with the
      literal `select-policy-families:` to stderr, for each of these registry or
      argument states — an unknown selection key; a `families` array containing a
      duplicate `id`; a `selection` entry naming an `id` absent from `families`;
      a selected family whose `module` does not resolve to a regular file whose
      canonical path stays under `--root` — covering an unresolvable target, a
      `..`-bearing or absolute remainder, a symlink leaving the boundary, and a
      hard link to an inode outside it, the last being canonically inside the
      root and so invisible to a resolve-then-compare check; a
      `tier` that is neither `precise` nor `advisory`; a `module` whose namespace
      prefix is neither `skill:` nor `seed:`; a `selection` list repeating the
      same `id`; a fenced info string whose trailing token is not `v` followed by
      the block's `schema_version`; and a `schema_version` other than `1`. Each
      version member is independently killable only under its own pair: the
      `schema_version` member requires a *consistent unsupported* pair — info
      string `json policy-registry.v2` with `schema_version: 2` — and the
      info-string member requires a *supported* `schema_version` with a
      mismatched info string — `json policy-registry.v2` with
      `schema_version: 1`.
- [x] **AC9:** building `packs/core` lands `policy-families.md` at
      `.claude/skills/work-loop/references/policy-families.md` under the
      `claude-code` adapter and at
      `.agents/skills/work-loop/references/policy-families.md` under `codex`,
      and invoking the selector with `--registry` set to each of those two
      copies in turn, `--root` set to the repository root, and the key
      `CODE-IMPLEMENTATION`, prints a `families` array whose `id` sequence is
      exactly `["the-razor", "cognitive-load"]`. The two roots are necessarily
      different trees: an adapter projection carries the skill, while seeds reach
      a consumer through the separate `scaffold` command
      (`packages/agentbundle/agentbundle/build/__init__.py:213`), so a projection
      output tree contains no `seed:` target to resolve.

## Follow-ons

- brief owner, `docs/product/briefs/phase-scoped-policy-delivery.md` § "Proposed
  slices" (D2) — assembling selected teaching into the `spec-author` dispatch
  brief and emitting the digest over what was included.
- brief owner, `docs/product/briefs/phase-scoped-policy-delivery.md` § "Proposed
  slices" (D3) — the same assembly for the sequential implementer envelope.
- brief owner, `docs/product/briefs/policy-arrival-validator.md` (V1) — checking
  that every selected family arrived, against D2's digest.
- work-loop skill, `packs/core/.apm/skills/work-loop/scripts/loop-engine.py:530`
  — the transition-table comment reads `Key: (mode, source_state, event)` while
  the keys are two-tuples and `mode` is the outer `_TRANSITIONS_BY_MODE` mapping.
  Left standing here because correcting it is unrelated to this slice; `plan.md`
  T1 names the real shape for this slice's implementer.

## Assumptions

- Technical: runtime is Python 3.11 or newer, so `json` and `hashlib` cover the
  registry and the digest with no new dependency
  (`packages/agentbundle/pyproject.toml:9`, `requires-python = ">=3.11"`).
- Technical: `references/` is a blessed skill subdirectory and a top-level
  `policies/` directory would warn under `CAT-S004`
  (`packages/agentbundle/agentbundle/catalogue_tooling/skill_spec_lint.py:42`,
  `BLESSED_SUBDIRS = frozenset({"scripts", "references", "assets", "evals"})`).
- Technical: no module-level name holds the legal FSM state set, so AC4's domain
  comes from the transition tables at
  `packs/core/.apm/skills/work-loop/scripts/loop-engine.py:533-565`;
  `_CODE_STATES` holds four of the ten.
- Technical: a fenced JSON record inside a work-loop reference is established —
  `references/review-verdict-record.md:15` opens ` ```json review-verdict.v1 ` —
  while the only script-read data file today is `assets/state.json`
  (`scripts/_loop_guards.py:354`), so this selector is the first `references/`
  reader.
- Technical: `.agents/rules/cognitive-load.md` is byte-identical to
  `packs/core/seeds/.agents/rules/cognitive-load.md`, so it is a projection and
  the seed owns that rule; root `AGENTS.md` differs from
  `packs/core/seeds/AGENTS.md`, so in this repository the root file is its own
  owner while an adopter receives the seeded copy. The order in
  § "Acceptance Criteria" → "Locator resolution" covers both by preferring the
  live file, and the difference between those two `seed:` candidates is what
  gives that order an oracle.
- Technical: confinement is the repository's blessed helper, mirrored into the
  skill's `scripts/` and loaded as a sibling — the pattern
  `packs/core/.apm/skills/close-work/scripts/file_safety.py` already
  establishes. A local canonicalize-then-prefix check was written first and
  replaced: it missed hard links, the check-to-read swap window, Windows reparse
  points, and a byte bound on the digest.
- Technical: a `seed:` locator resolves against the repository root, so it can
  name any confined file in the tree rather than only seed material. That reach
  is deliberate — `the-razor` is root `AGENTS.md` — and is stated in the registry
  reference so a reviewer reading a registry change knows what a locator can
  reach.
- Technical: `claude-code` projects skills to `.claude/skills/` and `codex` to
  `.agents/skills/` (`contracts/adapter.toml:188` and `:515`), and both roots are
  present here — but all three `skill:` candidates in this repository are
  byte-identical, so the `skill:` order is behaviourally inert in this tree and
  every permutation yields the same digest. Its oracle is `plan.md` T3's
  temporary fixture root, not the repository tree.
- Technical: no policy-family registry exists; the brief's recorded search still
  exits 1, and `rg --hidden "DIRECT-LIGHT|DIRECT_LIGHT"` returns no hit outside
  `docs/product/briefs/`.
- Process: core release history is `docs/product/changelog.md` as
  `## [core][<version>] — YYYY-MM-DD` directly beneath `[Unreleased]`, with
  `packs/core/pack.toml` and `packs/core/.claude-plugin/plugin.json` bumped
  together; both read `2.24.0` at merge `d7cf1b741`.
- Process: `contracts/` is scoped to "the published interface this catalogue
  exposes to consumers" (`contracts/README.md:4-5`), which the delivery record is
  not, so it stays inside the skill (user confirmation 2026-09-03).
- Process: `work-loop/SKILL.md` gains no routing row in this slice, because that
  table routes references an agent loads on a predicate and this registry is
  script-read data with no consumer until D2 (user confirmation 2026-09-03).
- Process: the brief's D1 ceiling was raised from eight to nine by owner decision
  (user confirmation 2026-09-03), recorded in that brief's AC-ceiling column in
  the form U1 established. Eight was reached by keeping the teaching-text digest
  rather than deferring it or splitting the slice; the ninth restores the
  two-adapter verification the brief's D1 row requires, in a form that can fail.
  A criterion comparing the two projections against *each other* cannot: adapters
  copy a skill directory byte-for-byte, so it passes on an empty or wrong
  registry. AC9 compares each projected copy against a literal expected sequence,
  which also subsumes the landing-path check, because the selector cannot run
  against a copy that never landed. The adopter guide moved from a criterion to the
  § "Durable Outputs" user-promise row in the same decision. It is safe because
  that row states more than the criterion did — three literal headings, the
  frontmatter keys, and every identifier — and `plan.md` T6 gives those
  assertions a test home in the registry suite. It is weaker in one respect worth
  recording: `lint-spec-status.py` mechanically blocks a `Shipped` spec carrying
  an open `- [ ]`, whereas a durable-output row's freshness is agent-attested.
- Process: guides are validated on frontmatter `title`, `summary`, `pack`, and
  `kind` (`tools/validate_guides.py:177`); no fixed reference-guide roster
  exists.
- Product: the initial family set is five of the six rules in the floor measured
  2026-09-02, with `work-intake` public routing precedence excluded because it
  fires before any loop exists and no selection key reaches it (user confirmation
  2026-09-03).
- Product: the tier of each family is an owner decision dated 2026-09-03, not a
  derivation. It is *informed* by two measured inputs — the floor table's
  gradability column and the parent intent's decidable-part table
  (`cross-adapter-behavior-enforcement.md`, § "A policy needing a reasoned
  verdict decomposes") — but neither records enforceability, and a gradability
  verdict is not a blocking verdict. AC2 pins the tiers as literals here, so a
  later revision of either input does not silently re-tier a shipped family.
- Product: the registry carries `schema_version` in this first cut rather than
  deferring it to the first consumer (user confirmation 2026-09-03).
