# Manual QA matrix — adapt-to-project (AC4)

Each AC4a row declares its **verification method** per the amended
AC4a (see `spec.md`):

  - `(a) automation` — pinned by a mechanical test in
    `packages/agentbundle/tests/`.
  - `(b) grep` — pinned by a SKILL.md body grep in `tests/skills/`.
  - `(c) transcript` — inline transcript excerpt + before/after tree
    fragment captured against a real adopter session.

**No AC4a row uses method *(c)* in v1.** The amended AC4a mandates
that every row's artifact MUST exist in the repo; method *(c)*
artifacts that cannot be captured in v1 belong under AC4b. The
class-2/3/4 transition rows all require method *(c)* (LLM judgment
against an interactive adopter session); they are enumerated under
AC4b below with named triggers.

AC4b also covers user-scope LLM-judgment rows deferred per RFC-0004
§ *Drawbacks* (no user-scope-eligible pack ships in v1).

## AC4a — v1-shipped rows

### Cross-cutting

| # | Row | Method | Pinned at |
| - | --- | ------ | --------- |
| 1 | idempotency re-run | (a) automation | `tests/integration/test_brownfield_adapt_end_to_end.py::test_idempotent_re_run` runs the round-trip twice; asserts byte-identical files at both passes. |
| 2 | dirty-state-repo (skill body teaches) | (b) grep | `tests/skills/test_adapt_skill_body.py::test_body_names_dirty_state_command` pins `git status --porcelain` in the body. |
| 3 | Tier-2 detection-repo (skill body teaches) | (b) grep | `tests/skills/test_adapt_skill_body.py::test_body_pre_flight_section_references_user_scope_state` pins Tier-2 reference in the Pre-flight section. |
| 4 | cross-scope-restructure × decline | (b) grep | `tests/skills/test_adapt_skill_body.py::test_body_names_split_into_two_prompt` + `test_body_forbids_cross_scope_execution` pin the two contract phrases. End-to-end transcript deferred to AC4b. |
| 17 | dirty-state-repo (porcelain primitive smoke) | (a) automation | `tests/integration/test_adapt_preflight_detection.py::test_repo_scope_dirty_state_porcelain_detects_uncommitted_edit` + `test_repo_scope_dirty_state_porcelain_lists_untracked_seed` exercise `git status --porcelain` against a tmp git repo seeded from the brownfield fixture; assert dirty-path naming + untracked-path surfacing. Pins the deterministic primitive the skill body invokes for repo-scope dirty detection, not the LLM narration of the Pre-flight (still pinned by row 2). |
| 18 | Tier-2 detection (content-hash primitive, scope-agnostic) | (a) automation | `tests/integration/test_adapt_preflight_detection.py::test_user_scope_tier2_content_hash_divergence_detected` seeds a tracked file under the user-scope fixture, records its SHA-256 in a v0.2 `state.toml`, mutates the file, asserts `sha256_bytes(actual) != recorded`. The primitive is scope-agnostic (the same logic detects Tier-2 divergence at repo scope against `.agent-ready-state.toml` and at user scope against `~/.agent-ready/state.toml`); exercising it once against the user-scope fixture is sufficient. Does not replace the LLM narration of the Pre-flight (still pinned by rows 3 and 7). |

Rows 17 and 18 originally enumerated under AC4b as deferred
end-to-end transcripts. **Promoted to AC4a *(a) automation* in
this PR** because the primitives they exercise (`git status
--porcelain`, `sha256_bytes`) are deterministic and don't require
LLM judgment; testing them as primitives gives regression
protection no transcript could provide. These primitive smoke
tests are *complementary* to rows 2 and 3 (which pin the skill
body's narration of the Pre-flight via *(b)* grep) — neither
replaces the other. A future regression to the primitives' shape
(a `git` release that stopped emitting porcelain for an edit, a
Python upgrade that broke `hashlib.sha256` output) would trip
these tests even though the *(b)* grep on the body still passed.

### User-scope plumbing rows (synthetic fixture)

Synthetic fixture: `packages/agentbundle/tests/fixtures/brownfield-adapt-user-home/.agent-ready/`.
All three are *plumbing* (no LLM judgment): the skill's pre-flight
reads the user-scope state and discovery files, and the CLI's
`safety.write_jailed` enforces the path-jail.

| # | Row | Method | Pinned at |
| - | --- | ------ | --------- |
| 5 | user-scope path-jail refusal | (a) automation | `safety.write_jailed` with `scope="user"` + `allowed_prefixes` is exercised by `tests/unit/test_scope.py::test_write_jailed_user_scope_refuses_outside_prefix` (and the four sibling `test_write_jailed_user_scope_*` cases); a class-3 destination escaping `~/.claude/`/`~/.agent-ready/` raises `PathJailError`. |
| 6 | dirty-state-user | (b) grep | SKILL.md body's Pre-flight section documents the content-hash divergence check against `~/.agent-ready/state.toml`. End-to-end fixture deferred to AC4b. |
| 7 | Tier-2 detection-user | (b) grep | SKILL.md body's Pre-flight section names `~/.agent-ready/`, `state.toml`, and `Tier-2` (`test_body_pre_flight_section_references_user_scope_state`). |

## AC4b — deferred rows

Every row below is method *(c)* (inline transcript excerpt +
before/after tree fragment) deferred to a follow-up. The contract
surface (SKILL.md body, automation/grep tests) ships in v1; only
the LLM-judgment transcripts are deferred. Rows are numbered
continuously with AC4a so cross-references are unambiguous.

**Note on the captures recorded below (rows 8–16).** Each row
carries a **Claude-simulated capture** — Claude executing the
SKILL.md body's documented branching against the extended
brownfield fixture under
`packages/agentbundle/tests/fixtures/brownfield-adapt/`. The
adopter side of every exchange is also Claude (selecting one
documented outcome per row). These captures are **preparatory
evidence**: they pin what an LLM following the body would do at
each branch and surface obvious specification gaps, but they are
**not** the (c) artifact AC4a defines. AC4a (c) requires a
transcript "captured against a real adopter session" — a human
adopter exercising the skill against their own brownfield repo.
The simulated captures stay under AC4b until that real-adopter
capture is feasible; the AC4b entry in `docs/ROADMAP.md` tracks
the open work.

### Repo-scope class-2 transcript artifacts (Claude-simulated)

The brownfield fixture seeds the surface (`AGENTS.upstream.md`
next to `AGENTS.md`). Class-1 substitution is assumed to have run
in the same session before each capture below, so `AGENTS.md`
carries the post-substitution bytes (`myproject` /  `octocat` /
`https://example.com/myproject`).

#### Row 8 — repo-scope class-2 × accept

**Captured (Claude-simulated), 2026-05-23.**

Transcript excerpt:

```text
adopter> /adapt-to-project

skill>  Pre-flight clean (repo HEAD clean; no ~/.agent-ready/
        divergence; no .adapt-install-marker.toml present in this
        fixture). One class-2 companion at repo scope:
        AGENTS.upstream.md (sibling of AGENTS.md).

        Proposed merge (companion intro folded into adopter body):

          # myproject
          Owner: octocat
          A brownfield adopter repo for testing class-1 substitution
          end-to-end.

          <!-- merged from AGENTS.upstream.md -->
          This is the canonical upstream AGENTS.md the install
          dropped next to the adopter's pre-existing AGENTS.md.
          …

        Accept / edit / skip / decline?

adopter> accept

skill>  Wrote merged result to AGENTS.md; deleted AGENTS.upstream.md.
        (Companion deletion is the dedup signal for accepted
        class-2 merges — see spec.md Boundaries § class 2.)
        Continuing to class-3 review.
```

Before / after tree fragment:

```text
─ before ───────────────────────────────
brownfield-adapt/
├── AGENTS.md              (post-class-1 substitutions)
├── AGENTS.upstream.md     (class-2 companion)
└── docs/CHARTER.md

─ after ────────────────────────────────
brownfield-adapt/
├── AGENTS.md              (merged result)
└── docs/CHARTER.md
                           (AGENTS.upstream.md removed)
```

#### Row 9 — repo-scope class-2 × edit

**Captured (Claude-simulated), 2026-05-23.**

Transcript excerpt:

```text
adopter> /adapt-to-project

skill>  [proposed merge as in row 8]
        Accept / edit / skip / decline?

adopter> edit — drop the "canonical upstream" sentence, keep the
         rest.

skill>  Revised proposal:

          # myproject
          Owner: octocat
          A brownfield adopter repo for testing class-1 substitution
          end-to-end.

          <!-- merged from AGENTS.upstream.md -->
          The skill proposes a merged result via per-change
          approval; substitution is class-1 only.

        Accept this revision / edit again / skip / decline?

adopter> accept

skill>  Wrote revised merged result to AGENTS.md; deleted
        AGENTS.upstream.md. Continuing to class-3 review.
```

Before / after tree fragment:

```text
─ before ───  same as row 8
─ after ────  AGENTS.md (revised merged result);
              AGENTS.upstream.md removed.
```

#### Row 10 — repo-scope class-2 × skip

**Captured (Claude-simulated), 2026-05-23.**

Transcript excerpt:

```text
adopter> /adapt-to-project

skill>  [proposed merge as in row 8]
        Accept / edit / skip / decline?

adopter> skip — I want to think about this one across sessions.

skill>  Leaving AGENTS.upstream.md on disk; no .adapt-discovery.toml
        write (skip != decline; the companion will be re-surfaced
        on the next session). Continuing to class-3 review.

        At session end, .adapt-pending.md will list this companion
        under *Pending companion merges* so you can audit deferred
        work outside the session.
```

Before / after tree fragment:

```text
─ before ───  same as row 8
─ after ────  AGENTS.md unchanged;
              AGENTS.upstream.md still on disk;
              .adapt-pending.md regenerated, lists
              `AGENTS.upstream.md` under *Pending companion merges*.
```

#### Row 11 — repo-scope class-2 × decline

**Captured (Claude-simulated), 2026-05-23.**

Transcript excerpt:

```text
adopter> /adapt-to-project

skill>  [proposed merge as in row 8]
        Accept / edit / skip / decline?

adopter> decline — we deliberately don't want the upstream body
         here; record so it isn't re-proposed.

skill>  Recorded under [[findings.declined]] in
        <repo>/.adapt-discovery.toml at repo scope with
        kind = "companion-merge",
        source-path = "AGENTS.upstream.md",
        destination-path = "AGENTS.md".
        AGENTS.upstream.md remains on disk (decline does not delete
        the companion; an adopter who wants it gone can `rm` it
        themselves). Future sessions will not re-propose this merge.
```

Before / after tree fragment:

```text
─ before ───  same as row 8
─ after ────  AGENTS.md unchanged;
              AGENTS.upstream.md still on disk;
              .adapt-discovery.toml gains a
              [[findings.declined]] entry with
              kind = "companion-merge".
```

### Repo-scope class-3 transcript artifacts (Claude-simulated)

The brownfield fixture now carries a class-3 surface: a top-level
`DESIGN.md` overlapping the canonical `docs/CHARTER.md`. The skill
proposes a `kind = "restructure"` move/merge from `DESIGN.md` into
`docs/CHARTER.md`.

#### Row 12 — repo-scope class-3 × accept

**Captured (Claude-simulated), 2026-05-23.**

Transcript excerpt:

```text
adopter> /adapt-to-project   (after class-2 resolution)

skill>  Class-3 discovery: top-level DESIGN.md overlaps the
        canonical home for charter/design content at
        docs/CHARTER.md. Proposed action: move DESIGN.md content
        into docs/CHARTER.md (append under a `## Design notes`
        sub-section) and delete DESIGN.md.

        Both paths are at repo scope (no cross-scope crossing).
        Per-change approval — accept / edit / decline?

adopter> accept

skill>  Wrote merged docs/CHARTER.md (existing charter body +
        appended `## Design notes` block from DESIGN.md). Deleted
        DESIGN.md. Recorded under [[findings.accepted]] in
        <repo>/.adapt-discovery.toml at repo scope:
          kind             = "restructure"
          source-path      = "DESIGN.md"
          destination-path = "docs/CHARTER.md"
          action           = "move-and-merge"
```

Before / after tree fragment:

```text
─ before ───────────────────────────────
brownfield-adapt/
├── DESIGN.md
└── docs/CHARTER.md         (canonical, post-class-1)

─ after ────────────────────────────────
brownfield-adapt/
└── docs/CHARTER.md         (merged: charter + Design notes)
                            (DESIGN.md removed)
                            .adapt-discovery.toml:
                              [[findings.accepted]] (restructure)
```

#### Row 13 — repo-scope class-3 × edit

**Captured (Claude-simulated), 2026-05-23.**

Transcript excerpt:

```text
adopter> /adapt-to-project

skill>  [class-3 proposal as in row 12]
        Per-change approval — accept / edit / decline?

adopter> edit — fold DESIGN.md content under `## Architecture`
         instead of `## Design notes`; that's our convention.

skill>  Revised proposal: append the DESIGN.md body to
        docs/CHARTER.md under `## Architecture`. Same source/dest;
        only the destination heading changes.

        Accept this revision / edit again / decline?

adopter> accept

skill>  Wrote revised docs/CHARTER.md; deleted DESIGN.md. Recorded
        under [[findings.accepted]] in
        <repo>/.adapt-discovery.toml at repo scope.
```

Before / after tree fragment:

```text
─ before ───  same as row 12
─ after ────  docs/CHARTER.md carries an `## Architecture` section;
              DESIGN.md removed;
              .adapt-discovery.toml gains a
              [[findings.accepted]] entry (kind = "restructure",
              action = "move-and-merge").
```

#### Row 14 — repo-scope class-3 × decline

**Captured (Claude-simulated), 2026-05-23.**

Transcript excerpt:

```text
adopter> /adapt-to-project

skill>  [class-3 proposal as in row 12]
        Per-change approval — accept / edit / decline?

adopter> decline — DESIGN.md is owned by a downstream tool; leave
         it where it is and don't re-propose.

skill>  Recorded under [[findings.declined]] in
        <repo>/.adapt-discovery.toml at repo scope:
          kind             = "restructure"
          source-path      = "DESIGN.md"
          destination-path = "docs/CHARTER.md"
        (no `action` field on declined findings — `action` is set
        only when a write happens; see spec.md § Canonical schema
        for the declined-finding example.)
        DESIGN.md remains on disk; docs/CHARTER.md unchanged.
        Future sessions will not re-propose this restructure.
```

Before / after tree fragment:

```text
─ before ───  same as row 12
─ after ────  DESIGN.md unchanged;
              docs/CHARTER.md unchanged;
              .adapt-discovery.toml gains a
              [[findings.declined]] entry (kind = "restructure").
```

### Repo-scope class-4 transcript artifacts (Claude-simulated)

The brownfield fixture now carries a class-4 surface: overlapping
`docs/howto/` (adopter-original, containing
`getting-started.md`) and `docs/guides/how-to/` (diátaxis-
projection, containing `index.md`). The skill proposes folding
one into the other (`kind = "consolidate"`); the canonical
destination is `docs/guides/how-to/` per the diátaxis layout the
pack ships. Filenames deliberately differ in the fixture so the
consolidation doesn't surface a same-name collision (SKILL.md
doesn't currently specify a collision-handling sub-protocol; the
fixture sidesteps the gap rather than the transcript inventing
one).

#### Row 15 — repo-scope class-4 × accept

**Captured (Claude-simulated), 2026-05-23.**

Transcript excerpt:

```text
adopter> /adapt-to-project   (after class-3 resolution)

skill>  Class-4 discovery: docs/howto/ overlaps
        docs/guides/how-to/ (diátaxis-projected). Proposed action:
        fold docs/howto/* into docs/guides/how-to/, preserving
        filenames (no same-name collisions in this tree). After
        consolidation, remove docs/howto/.

        Per-change approval — accept / decline?

adopter> accept

skill>  Moved docs/howto/getting-started.md
              → docs/guides/how-to/getting-started.md.
        Removed docs/howto/. Recorded under
        [[findings.accepted]] in <repo>/.adapt-discovery.toml at
        repo scope:
          kind             = "consolidate"
          source-path      = "docs/howto/"
          destination-path = "docs/guides/how-to/"
          action           = "fold-into-destination"
```

Before / after tree fragment:

```text
─ before ───────────────────────────────
brownfield-adapt/
└── docs/
    ├── howto/getting-started.md  (adopter-original)
    └── guides/how-to/index.md    (diátaxis-projection)

─ after ────────────────────────────────
brownfield-adapt/
└── docs/
    └── guides/how-to/
        ├── index.md              (unchanged)
        └── getting-started.md    (folded from docs/howto/)
                                  (docs/howto/ removed)
                                  .adapt-discovery.toml:
                                    [[findings.accepted]] (consolidate)
```

#### Row 16 — repo-scope class-4 × decline

**Captured (Claude-simulated), 2026-05-23.**

Transcript excerpt:

```text
adopter> /adapt-to-project

skill>  [class-4 proposal as in row 15]
        Per-change approval — accept / decline?

adopter> decline — we use docs/howto/ for adopter how-tos and
         docs/guides/how-to/ for the pack's; keep them separate
         and don't re-propose.

skill>  Recorded under [[findings.declined]] in
        <repo>/.adapt-discovery.toml at repo scope:
          kind             = "consolidate"
          source-path      = "docs/howto/"
          destination-path = "docs/guides/how-to/"
        Both directories remain on disk. Future sessions will not
        re-propose this consolidation.
```

Before / after tree fragment:

```text
─ before ───  same as row 15
─ after ────  docs/howto/ unchanged;
              docs/guides/how-to/ unchanged;
              .adapt-discovery.toml gains a
              [[findings.declined]] entry (kind = "consolidate").
```

### Cross-cutting end-to-end transcripts

Rows 17 and 18 moved from this section to AC4a above as method
*(a) automation*; see the cross-cutting table for their pins. No
transcript captures recorded here — the automation tests are the
durable evidence.

### User-scope LLM-judgment rows

Deferred per RFC-0004 § *Drawbacks* + *Unresolved questions* — no
user-scope-eligible pack ships in v1 (all four shipped packs lock
`allowed-scopes = ["repo"]`).

**Trigger to unblock (rows 19–28):** first pack declaring
`allowed-scopes = ["user"]` lands.

| # | Deferred row | Trigger |
| - | ------------ | ------- |
| 19 | user-scope class-2 × accept | first user-scope-eligible pack |
| 20 | user-scope class-2 × edit | first user-scope-eligible pack |
| 21 | user-scope class-2 × skip | first user-scope-eligible pack |
| 22 | user-scope class-2 × decline | first user-scope-eligible pack |
| 23 | user-scope class-3 × accept | first user-scope-eligible pack |
| 24 | user-scope class-3 × edit | first user-scope-eligible pack |
| 25 | user-scope class-3 × decline | first user-scope-eligible pack |
| 26 | user-scope class-4 × accept | first user-scope-eligible pack |
| 27 | user-scope class-4 × decline | first user-scope-eligible pack |
| 28 | cross-scope-restructure × split-into-two (both halves end-to-end) | first user-scope-eligible pack |

## Notes

The *split-into-two* path is verified by SKILL.md body greps
(`test_body_names_split_into_two_prompt` +
`test_body_forbids_cross_scope_execution`); end-to-end exercise of
both halves is row 28 under AC4b.

Method *(b) grep* rows verify the SKILL.md body *teaches* the
contract; they don't replace end-to-end exercise. The AC4b
enumeration captures the deferred work so reviewers can spot
omissions in the follow-up.
