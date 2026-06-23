# AC5 / AC14 manual-QA record — observable smoke project

AC5 requires a real `start → digest → synthesize` run over 2–3 synthetic source
files, producing the folder, a non-empty `synthesis-matrix.md` with constructed
columns, a typed synthesis, and a self-contained `<topic-slug>-brief.md`. The
four `research-project-*` skill sources are not installed into the implementing
session's loader, so the run was performed by following the **updated** skill
bodies directly (this is how a prompt-only skill executes).

- **Project question:** which config-file format should a cross-platform CLI
  default to? (slug `cli-config-format`, shape `comparison`).
- **Working directory:** `.context/research-project-qa/` (gitignored scratch —
  the scratch / out-of-repo default; no repo pollution).
- **Run:** `research-project-start` scaffolded
  `2026-06-22-cli-config-format/` (overview.md + `sources/`); three synthetic
  source files dropped into `sources/` (with optional `reliability`/
  `credibility` axes); `research-project-digest` built `synthesis-matrix.md`
  with **emergent, constructed columns** (comment support / type ambiguity /
  hand-edit ergonomics / ubiquity — not a pre-set pillar set) and `memos.md`
  (where the empty working hypothesis was formed and revised toward TOML);
  `research-project-synthesize` wrote the typed `comparison-matrix.md` verdict
  **and** `cli-config-format-brief.md`.

Produced tree:

```
2026-06-22-cli-config-format/
  overview.md
  sources/src-01.md  sources/src-02.md  sources/src-03.md
  synthesis-matrix.md     # non-empty, constructed columns
  memos.md
  comparison-matrix.md    # typed synthesis (shape=comparison)
  cli-config-format-brief.md   # governance handoff
```

Brief checks (the file on disk is the signal, not a self-report):

- **Answer-first:** `**Bottom line:** default to TOML …` is the top content line.
- **Self-contained:** zero cross-links to `memos.md` / `synthesis-matrix.md` /
  `sources/` / `overview.md` — safe to copy whole out of the folder
  (`rg 'memos\.md|synthesis-matrix\.md|sources/' cli-config-format-brief.md`
  returns nothing).
- **Cited + per-finding confidence-tagged** (`[high]` / `[moderate]`) and carries
  a `## Known unknowns` section (known-unknown + unknowable).
