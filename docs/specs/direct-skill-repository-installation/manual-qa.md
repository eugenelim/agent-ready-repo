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

## Pinned remote acquisition

Run on 2026-08-30 against `git+https://github.com/anthropics/skills@3b3fad96af16a10759d930941b4520ba0c40edae`,
a real public repository pinned to a full 40-hex commit SHA.

| Observation | Result |
|---|---|
| Archive fetched | 3,731,428 bytes, 510 members — inside the 256 MiB / 20,000-member bounds |
| Revision binding | `pax_global_header` SHA equalled the requested ref exactly |
| Redirect | `github.com/.../archive/<sha>.tar.gz` → `codeload.github.com/.../tar.gz/<sha>`, an equivalent target |
| Admission | `collection`, 19 skills, 411 files, 10,730,611 bytes |
| Install without `--yes` | refused, **0 files written** |
| Install with `--yes` | 83 files for `canvas-design`, state row at schema 0.5 recording the SHA |
| Temporary tree | removed on the success path and on the refusal path alike |

### Two defects this arm found

Both were invisible to the construction tests, because each half was correct in
isolation and the two never met.

1. **Acquisition and admission did not join.** A GitHub source archive prefixes
   every member with a `<repo>-<ref>/` wrapper, and admission looks for
   `SKILL.md`, `skills/`, or `pack.toml` — none of which sit beside that
   wrapper. Every local archive fixture had placed members at the archive root,
   so acquisition returned a tree admission refused with "no supported shape".
   Acquisition now descends the wrapper, derived from the member names rather
   than by listing the extracted tree, so an archive whose members genuinely sit
   at its root is left alone. Regressions:
   `test_the_github_wrapper_directory_is_descended` and its
   `..._not_descended_into` control.
2. **The cleanup could have deleted the system temporary directory.** The
   working tree was found by walking two parents up from the extracted root.
   That is correct only when a wrapper was descended; without one, two levels up
   is the system temp directory. `AcquiredArchive` now declares its `working`
   directory. Regression: `test_the_working_directory_is_carried_not_derived`.

A third gap surfaced at the same time: the CLI had no remote arm at all — a
`git+https://` positional is not a directory, so it fell through to the usage
error. Remote sources now route through acquisition, and a remote install
requires `--yes`, because the bytes are fetched before the reader has seen
anything.

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
