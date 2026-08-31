# Manual QA — direct skill repository installation

Recorded against the built CLI on 2026-08-30, CPython 3.13.13, macOS arm64,
`agentbundle 0.41.0 (spec 0.18)`. Operator home and source paths are redacted to
`<HOME>` and `<SOURCES>`.

## Sources exercised

| Fixture | Shape | Notable content |
|---|---|---|
| `hello-world/` | `root-single` | Folded (`>`) description, `allowed-tools`, `metadata.boundaries`, a `scripts/` payload |
| `kit/` | `collection` | Two skills under a **category** level (`skills/text/`), so flattening is exercised |
| `dpack/` | `direct-pack` | `schema = 1` manifest plus one skill |
| `ambiguous/` | refusal | Both `skills/` and `.claude/skills/` present |

## Defects found and fixed

Manual QA earned its place here: two defects survived the unit suites and only
appeared when the real CLI ran.

1. **Every refusal reported `path: null`.** AC27 requires an offending path on
   every mandatory refusal, and 25 of 35 raise sites did not name one. The
   shared entry point now backfills the validated source, which is what the
   criterion asks for when no root exists yet. Regression:
   `test_every_refusal_names_an_offending_path`.
2. **`--format json` was silently ignored for a direct pack.** A direct pack
   carries a `pack.toml`, so the invocation took the catalogue route — whose
   output for a valid pack is nothing at all, with exit 0. An explicit JSON
   request now routes to the direct path. Text output for a pack is unchanged.
   Regression: `test_json_reaches_a_direct_pack_despite_its_pack_toml`.

Both fixes are in this change; the transcript below is the re-run after them.

## Not executed

**Pinned remote acquisition.** The remote arm requires an outbound fetch to
GitHub. It is not run here: remote installation is a human action by design, and
this session had no authorisation to reach the network. The acquisition path is
covered by construction tests over local archive fixtures — grammar, redirect
equivalence, bounds, link policy, and SHA binding — but the assertion "this
works against real GitHub" is **not** discharged by this record and remains open
for a human run.

## Transcript

```console
$ agentbundle --version
agentbundle 0.41.0 (spec 0.18)
[exit 0]

$ agentbundle validate <SOURCES>/hello-world --format json
{
  "agentbundle_version": "0.41.0",
  "catalogue_schema_version": 1,
  "command": "validate",
  "diagnostics": [],
  "ok": true,
  "operation": "direct",
  "schema_version": 1,
  "summary": {
    "selected_skills": [
      "hello-world"
    ],
    "shape": "root-single"
  }
}
[exit 0]

$ agentbundle validate <SOURCES>/kit --format json
{
  "agentbundle_version": "0.41.0",
  "catalogue_schema_version": 1,
  "command": "validate",
  "diagnostics": [],
  "ok": true,
  "operation": "direct",
  "schema_version": 1,
  "summary": {
    "selected_skills": [
      "expand",
      "summarise"
    ],
    "shape": "collection"
  }
}
[exit 0]

$ agentbundle validate <SOURCES>/dpack --format json
{
  "agentbundle_version": "0.41.0",
  "catalogue_schema_version": 1,
  "command": "validate",
  "diagnostics": [],
  "ok": true,
  "operation": "direct",
  "schema_version": 1,
  "summary": {
    "selected_skills": [
      "one"
    ],
    "shape": "direct-pack"
  }
}
[exit 0]

$ agentbundle validate <SOURCES>/ambiguous --format json
{
  "agentbundle_version": "0.41.0",
  "catalogue_schema_version": 1,
  "command": "validate",
  "diagnostics": [
    {
      "code": "CAT-D009",
      "col": null,
      "line": null,
      "message": "ambiguous collection roots: skills and .claude/skills",
      "pack": null,
      "path": "<SOURCES>/ambiguous",
      "remediation": "This source offers two collection roots and the choice changes what is installed. Point at one of them directly.",
      "severity": "ERROR"
    }
  ],
  "ok": false,
  "operation": "direct",
  "schema_version": 1,
  "summary": {
    "selected_skills": [],
    "shape": null
  }
}
[exit 1]

$ agentbundle validate <SOURCES>/ambiguous
FAIL: direct source refused
  [CAT-D009] ERROR <SOURCES>/ambiguous
    ambiguous collection roots: skills and .claude/skills
    → This source offers two collection roots and the choice changes what is installed. Point at one of them directly.
[exit 1]
```

## Observations

- The category level flattens: `kit/skills/text/{summarise,expand}` reports
  `selected_skills: ["expand", "summarise"]` with no `text` segment, which is
  what `_project_direct_directory`'s single `skills/` level requires.
- Identity comes from the envelope directory, not frontmatter `name`.
- The folded `description` in `hello-world/SKILL.md` parsed without complaint,
  which is the block-scalar support this change added.
- The refusal names both competing roots and exits 1; the JSON and text forms
  carry the same code, path, and message.
