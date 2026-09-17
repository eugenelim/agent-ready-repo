# Spec: initiative display metadata

- **Status:** Shipped
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
| User-facing promise | Applicable — the change alters what an adopter's agent prints at session start | `packs/core/.apm/skills/workspace-status/SKILL.md` | maintainer | AC-0003's content assertions over the key list and rendering template | Template renders the two values and no redaction statement survives in any letter case |
| Release history | Applicable — adopter-visible behavior change | `docs/product/changelog.md` | maintainer | Released `[core]` entry with a `Highlights` bullet | Entry is free-standing directly beneath `[Unreleased]` |
| Interface compatibility | Applicable — two projected field meanings change | `packs/core/pack.toml`, `packs/core/.claude-plugin/plugin.json` | maintainer | Matching incremented versions | `catalogue verify`'s version-parity step green, run after the bump |
| Activation eval harness | Applicable — a non-cosmetic pack update owes its eval harness a disposition | `packs/core/.apm/skills/workspace-status/evals/evals.json` | maintainer | T5's recorded disposition of the `Example Initiative` assertions | Every assertion naming an initiative name is satisfiable under the shipped behavior |

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
  `assertNotIn(str(root), ...)` repository-root guard stays exactly as it is.
  `plan.md` T1 owns which assertions invert and why.

## Testing Strategy

- **Values reach the projection unchanged (AC-0001): TDD, plus visual / manual
  QA at the invocation surface.** A compressible invariant over a value domain —
  projected output compared against authored input — so it is expressed as cases
  over the real charset rather than inspected by hand. Two altitudes, one
  outcome: `workspace-status` is a skill a user invokes, so the real script also
  runs against this repository's own `workspace.toml` and the observed
  `initiatives[]` output is recorded. Both altitudes observe the JSON the script
  emits. The line an agent finally renders from that JSON is documented by the
  template AC-0003 pins and is not exercised here.
- **Contract text matches behavior (AC-0003): goal-based check.** The outcome is
  the presence and absence of specific strings in a shipped file. A content
  assertion answers it exactly; a behavioral test cannot see prose.

## Acceptance Criteria

- [x] **AC-0001.** For every active initiative in the workspace under test,
  projected `initiatives[].name` and `initiatives[].milestone` equal the string
  that initiative's `workspace.toml` section assigns, unchanged — including a
  value containing `·`, `–`, `—`, a semicolon, or a straight apostrophe.
  Equality is measured against the decoded JSON value, not raw stdout bytes:
  the emitter serialises with `ensure_ascii` at its default, so a non-ASCII
  character reaches stdout escaped.
- [x] **AC-0003.** `packs/core/.apm/skills/workspace-status/SKILL.md` describes both
  fields as values read from `workspace.toml`, enumerates `name` and `milestone`
  in the `initiatives` summary row alongside `slug`, `status`, `brief_queue` and
  `queue_empty`, renders active initiatives as
  `` `<ini-slug>` — `<name>` (milestone: `<milestone>`) ``, and retains no
  statement anywhere in the file — paragraph, heading, or key-list row, in any
  letter case — that either field is redacted, is the literal `workspace.toml`,
  or should be rendered as the slug alone.

## Retired identifiers

- `AC-0002`

Non-string coercion was a criterion through three review rounds and is now a
design decision with a regression case, recorded in `plan.md`. No `name` or
`milestone` in any initiative section is a non-string, and this spec's
`Never do` forbids constraining `workspace.toml` upstream, so no authoring path
reaches the state. It stayed unfalsifiable or under-quantified in every form it
took, which is the signal that it was never a completion gate's business.

## Assumptions

These were taken as a discovery snapshot on 2026-09-14, before implementation.
Two of them name identifiers this delivery itself changed; both are recorded
as they were observed, with their current form beside them.

- Technical: the sentinel was emitted from one source emitter plus its two
  generated adapter projections — three copies of the same `workspace_status.py`
  under `packs/core/.apm/`, `.agents/` and `.claude/`, which is what the
  repo-wide grep for `"name": "workspace.toml"` returned as 3 hits. It was at
  `:915,917` in each when this snapshot was taken on 2026-09-14. It is now
  emitted nowhere: the `"name"` and `"milestone"` keys in `_build_json`'s
  `initiatives_out` entry hold the coerced reads that replaced it. Those keys
  are named rather than located, because a line number into a generated file
  goes false on the next insertion above it without anything failing.
- Technical: three tests pinned the sentinel —
  `test_initiative_display_prose_is_not_projected`, since renamed to
  `test_initiative_display_prose_projects_verbatim`;
  `test_benign_initiative_display_fields_are_still_redacted`, since renamed to
  `test_initiative_display_fields_project_as_authored`; and
  `test_cli_rich_fixture_shapes`, which kept its name (grep for
  `initiative["name"]` over `tools/`, `tests/`, `packages/`, `packs/`).
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
