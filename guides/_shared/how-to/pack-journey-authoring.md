---
title: How to author a pack-local JOURNEY.md
summary: Author a canonical pack-owned journey with validated metadata, gates, state transitions, and projection-safe migration.
pack: _shared
kind: how-to
---

# How to author a pack-local JOURNEY.md

Use this when you maintain a catalogue whose packs publish canonical journey pages. This guide defines the source, metadata, migration, and projection contract for a pack-owned `JOURNEY.md`.

---

## 1. When a pack needs a JOURNEY.md

Add `JOURNEY.md` to a pack when **all** of the following apply:

- The pack delivers a meaningful multi-stage, human-in-the-loop experience.
- The journey has at least two stages with distinct human decision points.
- The pack is mature enough to have a stable skill set (no skills in active restructuring).
- You want the journey narrative to live with the pack source, not in a central file.
- The journey has already been reviewed and accepted as a web journey (or is being migrated from one).
- A `journey_id` can be chosen that is unique across all packs.

**Do NOT add `JOURNEY.md` when:**

- The pack has only one skill and zero human gates (no meaningful multi-stage flow).
- The pack is a dependency or helper with no first-value journey of its own.
- The journey is still being designed — write the central file first, migrate later.

---

## 2. Journey-level frontmatter contract

Required fields:

```yaml
journey_id: string        # unique kebab-case ID; used as the URL slug of the generated file
pack: string              # must exactly match the pack directory name
scope: user | repo
tagline: string
contract:
  useItWhen: string
  youType: string         # optional; the literal first utterance a reader types
  youProvide: string
  youReceive: string
  yourDecisions: [string]
skills:
  - name: string          # must exist in packs/{pack}/.apm/skills/{name}/
    description: string
    humanTouches: integer # total count must equal the number of .apm/skills/ directories
humanGates:               # list of gate objects; empty list [] is valid
  - id: string
    globalGate: string | null
    label: string
    trigger: string
    duration: string
    whatToCheck: [string]
    whatGoodLooksLike: string
    whatBadLooksLike: string
    consequence: string
typicalSession:
  agentTurns: string
  humanTouches: integer
  wallClockMinutes: string
docsUrl: string
packUrl: string
```

`youType` is what turns a journey from a description into something a reader
can act on. Write the exact words someone sends to start the journey, in one
line:

```yaml
contract:
  useItWhen: "You have a raw product idea and need a build-ready decision brief."
  youType: "Shape this: teams cannot tell which pack to install first."
```

Take the wording from the entry skill's own `Triggers on` phrase where it has
one, so the guide and the dispatcher agree. Do not paraphrase it into a
description — "ask the agent to shape your idea" is not a `youType`.

Optional fields:

```yaml
start_state: StateVocab   # state at journey start (see §4)
end_state: StateVocab     # state at journey end
relatedJourneys: [string]
prerequisitePacks: [string]
whatChanges: string
goodOutputDescription: string
```

---

## 3. Stage contract

Each stage is an h3 heading (`### N. Title`) followed by fixed-label bullet lines.

Label rank order (same as `lint-journey-contract.py`):

| Rank | Label | Required? |
|------|-------|-----------|
| 0 | `You provide` | optional |
| 1 | `Agent does` / `Reviewer does` / `Loop does` | optional |
| 2 | `You do` | optional |
| 3 | `You decide` | **required** when stage state ∈ WRITE_STATES |
| 4 | `Output` | **required** in every stage |
| 5 | `State` | **required** in pack-local stages |

Labels must appear in rank order within a stage. A stage may omit optional labels but must include `Output` and `State`.

Example stage:

```markdown
### 2. Draft the artifact

- **Agent does:** drafts the artifact starting from canonical behavior.
- **You do:** watch the draft take shape.
- **Output:** a draft artifact or findings report.
- **State:** draft
```

---

## 4. State vocabulary

The nine permitted state values and when each requires `**You decide:**`:

| State | Meaning | Requires You decide? |
|-------|---------|----------------------|
| `read-only` | Agent reads; nothing written to disk | No |
| `draft` | Agent produces a draft artifact, not yet committed | No |
| `proposed-write` | Agent proposes a write; human must confirm | **Yes** |
| `confirmed-write` | Human has confirmed; artifact is written | **Yes** |
| `publish` | Artifact is published or deployed externally | **Yes** |
| `destructive` | Files deleted, data lost, or hard to reverse | **Yes** |
| `no-action-required` | Agent analysis only; no output artifact | No |
| `decision-required` | Human must choose between options before continuing | **Yes** |
| `blocked` | Prerequisite not met; journey cannot proceed | No |

`decision-required` requires `**You decide:**` because a stage explicitly named as requiring a decision must carry the label — omitting it would be contradictory.

---

## 5. Skill reference validation

`lint-pack-journeys.py` checks two things:

1. **Existence**: every skill `name` listed in the `skills:` array must have a corresponding directory at `packs/{pack}/.apm/skills/{name}/`.
2. **Count parity**: the number of skills listed must equal the number of `.apm/skills/` directories in the pack.

If a skill is being added or removed from the pack, update `JOURNEY.md` in the same PR.

---

## 6. Route preservation

`journey_id` becomes the URL slug of the generated central file:

```
packs/{pack}/JOURNEY.md  →  web/src/content/journeys/{journey_id}.md
                         →  /journeys/{journey_id}/
```

When migrating an existing journey, set `journey_id` equal to the legacy file stem to preserve the existing URL. Example:

```
web/src/content/journeys/product-documentation.md  →  journey_id: product-documentation
```

A `journey_id` that differs from the pack directory name is valid — the validator does not require them to match.

---

## 7. Installation exclusion

`JOURNEY.md` is never included in the `agentbundle install` output. The install command reads only `.apm/skills/*/SKILL.md` and `.apm/agents/*.md`. No configuration is needed to exclude `JOURNEY.md`.

To verify after a migration:

```bash
tmpdir=$(mktemp -d)
catalogue="$(git rev-parse --show-toplevel)"
python -m agentbundle install --pack <pack-name> --output "$tmpdir" "$catalogue"
find "$tmpdir" -name "JOURNEY.md"   # should produce no output
rm -rf "$tmpdir"
```

---

## 8. Migration procedure

Step-by-step to migrate a central journey file to pack-owned:

a. **Choose `journey_id`** equal to the legacy file stem (e.g., `product-documentation`).

b. **Create `packs/{pack}/JOURNEY.md`** by copying the central file's frontmatter and body. Add:
   - `journey_id: {slug}` as the first frontmatter field
   - `start_state: {vocab}` and `end_state: {vocab}` (optional but recommended)
   - `**State:** {vocab}` after `**Output:**` in every stage

c. **Validate** the new file:
   ```bash
   python tools/lint-pack-journeys.py
   ```
   Fix any errors before proceeding.

d. **Remove the legacy central file**:
   ```bash
   git rm web/src/content/journeys/{slug}.md
   ```

e. **Add the slug to `.gitignore`** in `web/src/content/journeys/`:
   ```
   {slug}.md
   ```

f. **Generate the central file** from the pack-local source:
   ```bash
   python tools/build-site.py --journeys-only
   ```

g. **Verify the generated file**:
   ```bash
   grep "generated: true" web/src/content/journeys/{slug}.md
   python tools/lint-pack-journeys.py
   ```

h. **Run the full pre-PR gate**:
   ```bash
   make pre-pr
   ```

---

## 9. Avoiding duplicate canonical sources

`lint-pack-journeys.py` and `sync_pack_journeys()` in `build-site.py` both enforce:

- **Same-slug ownership**: if a non-generated central file exists at `web/src/content/journeys/{journey_id}.md`, the validator errors. Fix: `git rm` the central file and add it to `.gitignore`.

- **Same-pack ownership**: if a non-generated central file has `pack: {pack}` in its frontmatter (even at a different slug), the validator errors. Fix: remove or migrate that central file before adding `JOURNEY.md`.

- **Duplicate `journey_id`**: two packs may not share a `journey_id`. Pick a unique slug.

A central file with `generated: true` in its frontmatter is never treated as a duplicate — it is the sync output and is deliberately co-located with the pack-local source.
