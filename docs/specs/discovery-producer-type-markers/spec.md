# Spec: Discovery-producer traceability markers

- **Status:** Shipped <!-- Draft | Approved | Implementing | Shipped | Archived -->
- **Owner:** eugenelim
- **Plan:** [`plan.md`](plan.md)
- **Constrained by:** RFC-0053 (AC36, DRIFT-G), RFC-0048 (note 04, the ladder kind/level split)
- **Shape:** mixed

> **Spec contract:** this document defines what "done" means. The implementing
> PR must match this spec, or update it. Verification must be derivable from it.

Mode: full (a published-interface change — the artifact schemas of shipped
producer skills — across two packs).

## Objective

The structural-orphan traceability lint (`work-loop`'s `lint-traceability.py`)
recognizes discovery-side producer nodes **by marker, not path**: a screen via a
`Type:` field, journey actions / blueprint services via embedded `Action:` /
`Service:` fields, and intent-ladder rungs via `Kind:` / `Level:` fields. The
grammar is documented in `CONVENTIONS.md` § 4 and the recognizer ships in the
lint, but only `frame-domain` currently *emits* markers — and as *frontmatter*,
which the chain recognizers do not read (precedent for the convention, not for the
bold-body form the lint matches). The other producer
skills — `map-screen-flow`, `map-customer-journey`, `blueprint-service`,
`frame-intent`, `decompose-intent` — do not, so a future fail-closed traceability
up-edge would be load-bearing on markers that don't exist. This change makes each
producer's artifact schema emit the exact marker its node type's recognizer reads,
closing the latent gap previously tracked in the backlog as `discovery-loop-type-marker-producers`.
Primarily a format change to the producer skills; it also (operator-directed)
corrects the CONVENTIONS § 4 marker-form description to match the shipped lint, fixes
the `recognize_screens` glob so nested per-screen briefs are found, and lands the
intent↔chain rung mapping the lint's `recognize_ladder` docstring left "degrading."

## Boundaries

### Always do

- Emit the marker in the **exact on-disk form the lint's recognizer reads** — a
  rendered **bold-body field** (`- **Type:** screen-brief`, `- **Action:** <slug>`,
  `- **Service:** <slug>`, `- **Kind:** outcome|opportunity`, `- **Level:** capability`),
  because `field_re` matches `**Label:**`, not a YAML frontmatter key. Confirm each
  against `recognize_specs`/`recognize_screens`/`recognize_entries`/`recognize_ladder`
  and the lint's own `case_container_and_file_recognition` fixture.
- Keep markers **additive**, and ensure an **unfilled template produces no node**,
  verified by running the lint against the verbatim templates. The two gates differ
  by marker: the slug-bearing `Action`/`Service` placeholders (`<slug>`) are skipped
  by `_is_placeholder` (value starts `<`, ends `>`); the backtick-wrapped enum
  placeholders `` **Kind:** `<outcome | opportunity>` `` / `` **Level:** `<…>` ``
  (matching the template's sibling fields) are *not* caught by `_is_placeholder`
  (they start with a backtick) but are rejected by the recognizer's **value/enum
  gate** (`recognize_ladder` accepts only the literal `outcome`/`opportunity`/
  `capability` tokens) — the load-bearing gate for those. **Never write the bold marker syntax inside a template comment** — the
  lint scans every line, so a commented example would mint a phantom node (the
  comment refers to the marker by label only).

### Ask first

- Any change to a marker the lint does not yet read.

### Never do

- Add **operating-model doctrine** to `CONVENTIONS.md` (the § 4 edit here is a
  **factual erratum** correcting the marker-form description to match the shipped
  lint — operator-directed, not a policy change).
- Change the lint's recognition *semantics* (the `**Label:**` field grammar, the
  marker values, the orphan/reachability rules). The `recognize_screens`
  **recursion** fix (operator-directed ride-along) changes *where* it looks, not
  *what* it recognizes; its self-test is extended, not weakened.
- Repurpose the per-screen brief's frontmatter `type: screen-flow-brief` — it is a
  documented brief-internal, deliberately-not-a-discover-anchor marker
  (`map-screen-flow/references/agentbundle-layout.md`); the chain marker is a
  separate bold-body `Type:` field.

## Testing Strategy

Goal-based check, exercised by the lint as an integration oracle. For each
producer, build a small fixture artifact carrying the marker (in the form the
edited template now emits) under the lint's default base, run
`python3 packs/core/.apm/skills/work-loop/scripts/lint-traceability.py --root <fixture>`,
and confirm the lint reports the expected node id and produces no false orphan on a
wired chain. The lint's self-test (`test-lint-traceability.py`) must continue to
pass — extended with a **nested per-screen brief** case for the `recognize_screens`
recursion fix (the only recognizer change), never weakened.

## Acceptance Criteria

- [x] `map-screen-flow`'s per-screen brief schema emits a bold-body
  `- **Type:** screen-brief`; `recognize_screens` recognizes a brief carrying it as a
  `screen:<stem>` node — verified by a fixture asserting the exact node id appears.
  The brief's nested path (`screens/<slug>/<screen>.md`) is now found by the
  recursion fix (AC11), so a real producer brief is recognized, not only a flat
  stand-in.
- [x] `map-customer-journey`'s journey schema emits one bold-body
  `- **Action:** <action-slug>` marker per frontstage action; a fixture journey is
  recognized as `action:<slug>` node(s) by `recognize_entries`.
- [x] `blueprint-service`'s blueprint schema emits one bold-body
  `- **Service:** <service-slug>` marker per backstage service; a fixture blueprint
  is recognized as `service:<slug>` node(s) by `recognize_entries`.
- [x] `frame-intent`'s intent schema emits an additive, optional bold-body
  `- **Kind:**` field with the recognized set `outcome | opportunity`, beside the
  existing `- **Level:**` field. `recognize_ladder` maps an intent carrying
  `Kind: outcome` → `outcome:<slug>`, `Kind: opportunity` → `opportunity:<slug>`,
  and `Level: capability` → `capability:<slug>` (a `Level: feature` / `product-vision`
  / `product-strategy` intent with no `Kind:` produces no ladder node — it maps
  downstream to a brief/spec); verified by a fixture asserting each node id. The
  field is the **discovery-chain rung tag** placing an intent on the OST
  (`outcome → opportunities → …`, RFC-0048 note 04) when the discovery model is run;
  it does **not** change the intent model — an intent still carries both an Outcome
  and an Opportunity section. (Surfaced: the lint's own `recognize_ladder` docstring
  concedes this producer↔chain reconciliation was left "degrading until it lands";
  this lands the *format*, see Surfaced decisions.)
- [x] `decompose-intent` instructs the child-intent emission to carry the `Kind:`
  (and `Level:`) marker, so a decomposed ladder rung is recognized — verified by a
  fixture child intent emitted in the form the edited step describes, run through
  the lint and asserting its node id.
- [x] A fully-wired fixture chain (intent ladder via `Parent intent:` → screen →
  action → service, plus a spec parented via `Discovery:`) recognizes every producer
  node **by its exact id** (the unambiguous recognition signal) and reports **no
  `ORPHAN`/`DANGLING`** on the wired nodes — the absence of orphans is meaningful
  only on a wired chain.
- [x] `test-lint-traceability.py` passes, **extended** with a nested per-screen
  brief case (the recursion fix) — the recognition contract is otherwise untouched.
- [x] **CONVENTIONS § 4 erratum:** the spec-metadata contract describes the
  discovery-producer marker as a **bold-body field** the lint reads (`**Type:**` /
  `**Kind:**` / `**Level:**` / `**Action:**` / `**Service:**`), not a frontmatter
  key, and notes `frame-domain`'s frontmatter `type:` is a document-level
  discover-by-marker anchor distinct from the chain recognizers' fields. A factual
  correction matching the shipped lint, not a policy change.
- [x] **`recognize_screens` recursion (core):** it walks the screens base
  recursively (mirroring `recognize_contracts`'s `_iter_dirs` walk), so a nested
  `screens/<slug>/<screen>.md` brief carrying `**Type:** screen-brief` is recognized;
  the self-test gains a nested-brief case; `core` is version-bumped
  (pack.toml + plugin.json) and `marketplace.json` regenerated. Flow files
  (`type: screen-flow`, no bold-body `**Type:** screen-brief`) are not picked up.
- [x] **Intent↔chain reconciliation landed:** `frame-intent/references/intent-model.md`
  documents the `Kind:`/`Level:` → chain-rung mapping (orthogonal to the intent's
  internal outcome+opportunity structure; grounded in RFC-0048 note 04's OST); the
  lint's `recognize_ladder` docstring drops "degrading until it lands" for the
  now-landed mapping; an RFC-0048 § Amendments dated note records the landing.
- [x] `experience` and `product-engineering` packs are version-bumped — the
  **top-level pack `version`** key in `pack.toml` and the `version` in
  `.claude-plugin/plugin.json` (NOT the `[contract]` layout version) — and
  `marketplace.json` regenerated via `make build-self` with no other drift.
- [x] `docs/product/changelog.md` `[Unreleased]` carries an entry; the
  `discovery-loop-type-marker-producers` backlog entry is closed.

## Assumptions

- Technical: the lint recognizes markers via the **bold-body** `**Label:**` form,
  not frontmatter — verified by reading `field_re` and the
  `case_container_and_file_recognition` fixture (source: probe
  `packs/core/.apm/skills/work-loop/scripts/{lint,test-lint}-traceability.py`).
- Technical: `frame-domain` already emits `type:`/`scope-boundary` markers but as
  **frontmatter** (not read by the lint, since `domain-framing`/`scope-boundary`
  are not chain nodes) — so it is precedent for the marker *convention*, not for the
  on-disk *form* the chain recognizers need (source: probe `frame-domain/SKILL.md`).
- Technical: the per-screen brief frontmatter `type: screen-flow-brief` is
  deliberately distinct and must not be repurposed (source: probe
  `map-screen-flow/references/agentbundle-layout.md` lines 94-97).
- Process: `experience` / `product-engineering` are user-scope-default packs not in
  this repo's working-tree projection, so the version bump drifts `marketplace.json`
  only; `make build-self` regenerates it (source:
  [[non-projected-pack-bump-drifts-marketplace]] memory).

## Resolved here (originally surfaced)

Three items the first cut surfaced for the owner are, on operator direction, resolved
in this PR (AC10–AC12):

1. **CONVENTIONS § 4 marker-form drift** — § 4 described the marker as "frontmatter
   `type:`" while the lint reads a bold-body `**Type:**` field; an adopter following
   § 4 would emit an unrecognized frontmatter marker. Corrected as a **factual
   erratum** (the docs misdescribed the shipped lint), not an operating-model policy
   change — so it does not require the `update-conventions` RFC path. `frame-domain`'s
   frontmatter `type:` is noted as a document-level discover-by-marker anchor, distinct
   from the chain recognizers' bold-body fields.
2. **Screen glob↔nested-path gap** — `recognize_screens` now walks the screens base
   recursively (the `recognize_contracts` precedent), so a real nested
   `screens/<slug>/<screen>.md` brief is recognized, not only a flat stand-in (AC11).
   Flow files lack the bold-body `screen-brief` marker, so they are not picked up.
3. **Intent↔chain reconciliation** — grounded in RFC-0048 note 04's OST, the
   `Kind:`/`Level:` → chain-rung mapping is now documented in `intent-model.md`
   (orthogonal to the intent's internal outcome+opportunity structure), the lint's
   `recognize_ladder` docstring drops "degrading until it lands," and an RFC-0048
   § Amendments note records the landing (AC12). This *implements* note 04's decided
   ontology; it mints no new value call.
