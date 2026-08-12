# Scrub judgment record (T2 / AC7)

Rule 3 of the guard fails a `spec/<slug>` or `docs/specs/<slug>` reference only
when `<slug>` names a real directory under `docs/specs/`. A citation of a spec
that does not exist yet is invisible to it. This record is therefore the only
evidence that the judgment half of the scrub was done, and what it decided.

**Method.** Every `guides/**/*.md` hit for a governance link target, an
`ADR`/`RFC` token, or a `spec/`-shaped path was classified against the brief's
rubric: *does this point the reader at a specific, real internal record to go
read it?* Pointer clauses were removed; surrounding teaching prose was kept.

## Removed

| Class | Count |
| --- | --- |
| Markdown link targets with an `/adr/`, `/rfc/`, or `/specs/` segment | 37 |
| `ADR-####` / `RFC-####` token occurrences | 45, spanning 22 distinct records |
| Spec-slug citations of real records | 5 occurrences across 4 distinct specs |
| Spec-slug citations of pending records (judgment only) | 1 |
| Changelog-path links | 0 — none existed in `guides/` |

The changelog rule therefore ships covered by unit tests rather than by a real
removal. It is a fence against a class that had not yet appeared, not a fix.

### Real-record citations removed (rule 3 would also catch these)

- `docs/specs/skill-secrets` — twice. `credential-brokers/explanation/credentialed-skills.md`
  framed it as "the implementation spec"; `_shared/how-to/author-a-skill.md`
  cited it as "Loader contract … § AC3, AC4c". Both are authority framing, the
  clearest signal in the rubric.
- `docs/specs/adapt-to-project` — `core/how-to/adapt-to-project.md` called it
  "the authoritative spec (LLM skill + CLI split, marker formats, exit conditions)".
- `docs/specs/credentialed-cli-exit-code-contract` — `credential-brokers/how-to/add-a-credentialed-skill.md`,
  cited as the source of the banded exit codes. The exit-code *values* stay in
  the guide; only the pointer went.
- `docs/specs/credential-broker-contract` — same page's Related list.

### Pending-record citation removed (judgment only — the guard cannot see this)

- `spec/product-engineering-shaping-doctrine` in
  `core/explanation/digital-experience-contract.md`. The sentence read "The
  product-engineering journey page is pending `spec/product-engineering-shaping-doctrine`."
  No `docs/specs/product-engineering-shaping-doctrine/` directory exists, so
  rule 3 is blind to it, and "pending `spec/X`" is exactly the framing the
  rubric names as a real citation. The clause was dropped and the remaining
  guidance — byte-identical pack copies, the drift-check command, the journey
  page links — was kept intact.

**This is the one item that would silently regress.** If that spec is ever
created, rule 3 starts catching the citation; until then nothing but this record
shows it was considered.

## Retained, and why

All of the following survive in `guides/`. None names a directory under
`docs/specs/`, which is why the guard passes clean with them in place.

**Concepts, not records** — `spec/plan`, `spec/loop`, `spec/slice`, and
`spec/build` (the last in `github/how-to/intake-a-github-milestone-as-a-brief.md`,
prose reading "fall back to your repo's own spec/build process"). These are the
product's vocabulary.

**Rendered CLI output inside a tutorial** — `core/tutorials/your-first-workspace.md`
shows `workspace-status` output containing `spec/capture-work-v2`,
`spec/workspace-status-phase2`, and `spec/workspace-core`. These demonstrate the
tool's display format. Editing them would falsify the tutorial.

**Invented example slugs** — `docs/specs/webhook-retries`,
`docs/specs/walking-skeleton`, `docs/specs/self-service-reset`,
`docs/specs/fix-login-bug`, `docs/specs/workspace-core`,
`docs/specs/capture-work-v2`. Throwaway slugs that teach the workflow.

## Also in scope

`user-guide-diataxis` no longer appears anywhere in `guides/` (0 files); each
site now reads `product-documentation`. The `packs/user-guide-diataxis/`
compatibility shim is untouched, per the spec's Never-do.

## Verification

- `python3 tools/lint-guides-no-repo-only-refs.py` → clean, exit 0.
- No changed guide contains an empty `]()` target or an orphaned link label.
- Every retained slug above was confirmed absent from `docs/specs/`; every
  removed real-record slug was confirmed present.
