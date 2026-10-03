# Extracted controller artifacts

46 files, 3.46 MB, extracted 2026-10-02 from gitignored `.context/` directories.
These are the artifacts that tracked research records cite, many of them by
SHA-256, and that until now existed only in one local checkout.

## Why

Across the plan-evolution research records, **78 distinct `.context/` paths are
cited as evidence**. `.context/` is gitignored, so none of that evidence was in
the repository, and **7 of the cited paths were already gone** by 2026-10-02.
Records were pinning digests against files a reader could not obtain.

This extraction takes the cited *individual files* — dispatch manifests, hidden
registries, release profiles, scoring rules, calibration gates, adjudication
decisions, launch orders, measures, and the four headless run result files. The
bulk per-slot prompt and transcript directories (~46 MB, 7,600 files) were
deliberately left out.

## Digest verification

**38 of the 46 files are pinned by a digest in a tracked record** and verify
unchanged against it.

One file does not, by deliberate choice:

| File | Status |
| --- | --- |
| `experiments/codex-collaboration-r1/run-0b/controller/release-profile.json` | **redacted** |

It contained an absolute path under the controller's home directory, which the
repository forbids committing. The path was rewritten to `~`. That changes the
file, so its digest intentionally no longer matches the pin in
`codex-collaboration-evidence-index.json`:

- pinned / original: `f891faac6706c3a86b59f6c663cf417f1639b2dc75ade3f4780dd7ac8fafb08f`
- redacted copy: `ff9f91f89e0ce25cd85943e636df2db037df5e60422e831370eca09599e6eecd`

The privacy rule is not waivable, so the redaction stands and the mismatch is
recorded here rather than hidden. No other file was modified. All 46 were
screened for emails, tokens and credentials; none were found.

## Layout

Mirrors the source tree under `.context/`, so a path cited as
`.context/experiments/<run>/<file>` is here at
`controller-artifacts/experiments/<run>/<file>`.

## What is still not in the repository

The bulk evidence for the headless runs — per-slot prompts, receipts and
terminal reports across `codex-headless-via-claude-r1`, `-run6-r1`, `-run7-r1`
and `-runs2-5-r1` — remains untracked and local-only, roughly 46 MB in 7,600
files. It survives on one machine and will not outlive that checkout. The seven
already-missing cited paths are listed in the records that cite them.
