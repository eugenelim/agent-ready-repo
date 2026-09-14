# Spec: initiative display metadata

- **Status:** Draft
- **Owner:** eugenelim
- **Plan:** [`plan.md`](plan.md)
- **Constrained by:** none
- **Discovery:** `docs/product/intents/initiative-display-metadata-restoration.md`
- **Contract:** none — the projection's shape is documented in the skill's own `SKILL.md`, not a `contracts/` artifact
- **Shape:** service

> **Spec contract:** this document defines what "done" means. The implementing
> PR must match this spec, or update it. Verification must be derivable from it.

## Objective

A session that runs `workspace-status` can tell which initiative is which.
The `initiatives[]` projection carries the `name` and `milestone` each
initiative declares in `workspace.toml`, so orientation reads
`ini-002 — Platform Core (milestone: P5 · Adopt (M1–M5 shipped))` instead of a
bare slug. `workspace.toml` is working material for developers in the same
repository and carries the same trust as the source beside it, so its display
prose reaches the reader as written, exactly as the sibling `[backlog].open`
`summary` already does.

## Durable Outputs

| Semantic role | Applicability | Destination | Owner | Expected evidence | Closeout condition |
| --- | --- | --- | --- | --- | --- |
| User-facing promise | Applicable — the change alters what an adopter's agent prints at session start | `packs/core/.apm/skills/workspace-status/SKILL.md` | maintainer | AC-0003's content assertions over the key list and rendering template | Template renders the two values and no redaction paragraph remains |
| Release history | Applicable — adopter-visible behavior change | `docs/product/changelog.md` | maintainer | Released `[core]` entry with a `Highlights` bullet | Entry is free-standing directly beneath `[Unreleased]` |
| Interface compatibility | Applicable — two projected field meanings change | `packs/core/pack.toml`, `packs/core/.claude-plugin/plugin.json` | maintainer | Matching incremented versions | `check-release-impact` passes |

## Boundaries

### Always do

- Emit both fields through one code path, so `name` and `milestone` cannot
  diverge in how they are treated.
- Regenerate the adapter projections with `catalogue self-host` after editing
  anything under `.apm/`, and keep all three copies byte-identical.
- Bump `pack.toml` and `.claude-plugin/plugin.json` together and add the
  changelog entry in the same change.

### Ask first

- Adding any length, charset, or content bound to either field. The accepted
  intent leaves this open and the threat model does not require one; choosing a
  bound is a new policy decision, not an implementation detail.
- Changing what any other `_public_*` filter in the module does.
- Removing rather than converting a test that currently asserts redaction.

### Never do

- Introduce a new module, helper module, or abstraction layer for two field
  reads. **Structural rule:** no new file, no new top-level directory, and no
  new dependency.
- Reintroduce the redaction sentinel as a fallback for either field on any
  input path.
- Change `workspace.toml`'s schema, or what an author is permitted to write
  into it. This changes what the projection emits, nothing upstream of it.
- Weaken, delete, or narrow any assertion in the touched test files other than
  the display-field assertions inside the three named tests, which invert. The
  `assertNotIn(str(root), ...)` repository-root guard stays exactly as it is:
  it catches a path leaked from the running process, which no decision here
  touches. An absolute path a fixture itself authored into `name` or
  `milestone` is a display-field assertion and inverts with the rest, because
  projecting authored content verbatim is the decision.

## Testing Strategy

- **Values reach the projection unchanged (AC-0001): TDD, plus visual / manual
  QA at the invocation surface.** A compressible invariant over a value domain —
  projected output compared against authored input — so it is expressed as cases
  over the real charset rather than inspected by hand. Two altitudes, one
  outcome: `workspace-status` is a skill a user invokes, so the real script also
  runs against this repository's own `workspace.toml` and the observed
  `initiatives[]` output is recorded. A passing unit gate does not establish
  what a session actually prints.
- **Non-string coercion (AC-0002): TDD.** One input class with one stated output
  type; the cheapest possible red, and the case has never occurred in the
  corpus so nothing else would catch a regression.
- **Contract text matches behavior (AC-0003): goal-based check.** The outcome is
  the presence and absence of specific strings in a shipped file. A content
  assertion answers it exactly; a behavioral test cannot see prose.

## Acceptance Criteria

- [ ] **AC-0001.** For every active initiative in the workspace under test,
  projected `initiatives[].name` and `initiatives[].milestone` equal the string
  that initiative's `workspace.toml` section assigns, unchanged — including a
  value containing `·`, `–`, `—`, a semicolon, or a straight apostrophe.
- [ ] **AC-0002.** A non-string TOML value assigned to `name` or `milestone`
  projects as a JSON string, at every non-string TOML type: integer, float,
  boolean, array, inline table, and each date-time form. Two projected texts
  differ from what the author wrote and are fixed here: `true` → `"True"`, and
  `1979-05-27T07:32:00Z` → `"1979-05-27 07:32:00+00:00"`.
- [ ] **AC-0003.** `packs/core/.apm/skills/workspace-status/SKILL.md` describes both
  fields as values read from `workspace.toml`, enumerates `name` and `milestone`
  in the `initiatives` summary row alongside `slug`, `status`, `brief_queue` and
  `queue_empty`, renders active initiatives as
  `` `<ini-slug>` — `<name>` (milestone: `<milestone>`) ``, and contains no
  paragraph instructing the consumer to render the slug alone or to treat either
  field as redacted.

## Assumptions

- Technical: the sentinel is emitted from one source emitter,
  `workspace_status.py:915,917`, plus two generated adapter projections
  (repo-wide grep for `"name": "workspace.toml"` returned 3 hits, all the same
  file).
- Technical: three tests pin the sentinel —
  `test_initiative_display_prose_is_not_projected`,
  `test_benign_initiative_display_fields_are_still_redacted`, and
  `test_cli_rich_fixture_shapes` (grep for `initiative["name"]` over `tools/`,
  `tests/`, `packages/`, `packs/`).
- Technical: no test pins the `SKILL.md` rendering template; the only
  `Active initiatives` match in `tools/test_workspace_status.py` is a comment.
- Technical: `workspace-mcp` does not re-emit `initiatives`, so the skill is
  the projection's only consumer (grep for `initiatives` in
  `workspace_mcp.py` returned no hits).
- Technical: `Initiative.name` and `.milestone` are populated by
  `section.get(...)` with no coercion, so a non-string TOML value survives the
  `str` annotation (`workspace_status_engine.py:3822-3825`).
- Technical: the four active initiatives' real milestone values carry `·`, `–`
  and `—`, a semicolon and a straight apostrophe between them, and contain no
  newline (probe over `workspace.toml`).
- Product: a non-string value is coerced with `str()` rather than emitted as a
  JSON number or redacted (user confirmation 2026-09-14).
- Product: the hostile-payload test is converted to assert verbatim
  projection rather than deleted, keeping the decision legible in the suite
  (user confirmation 2026-09-14).
- Process: a non-cosmetic pack-content change bumps `pack.toml` and
  `.claude-plugin/plugin.json` and owes a changelog entry
  (`packs/AGENTS.md` § Version bump rule).
- Process: this spec lands stacked on the branch carrying its accepted intent
  (user confirmation 2026-09-14).
