---
journey_id: fixture-journey
pack: pack-with-journey
start_state: read-only
end_state: confirmed-write
scope: repo
tagline: Exercise the neutral catalogue index.
contract:
  useItWhen: You need a deterministic fixture.
  youProvide: A catalogue root.
  youReceive: A validated neutral index.
  yourDecisions:
    - Where to write the index.
docsUrl: https://example.com/catalogue/journey
relatedJourneys:
  - fixture-follow-on
effects:
  - kind: file-write
    description: Writes a validated JSON index when not in dry-run mode.
---

| Say or ask | Outcome |
| --- | --- |
| "Index this catalogue" | Validate the catalogue and produce a neutral index. |

### Orient

Confirm the fixture catalogue root and whether the run should write an output file.

### Primary workflow

#### 1. Validate the catalogue

Say "Index this catalogue." The agent produces a schema-validated index in memory. No
human decision is required, and the resulting state remains `read-only`.

#### 2. Publish the index

Choose the output path. The agent writes the validated JSON document. You decide whether
the destination is correct, and the resulting state is `confirmed-write`.

### Persist and collaborate

Share the generated index path; the fixture itself carries no cross-session state.

### Next steps

Continue with the `fixture-follow-on` journey.
