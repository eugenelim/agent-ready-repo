# Evidence-led skill changes — architect first-run pilot

**Date:** 2026-07-22
**Pilot transcript:** `notes/transcript.md`

## Result

No skill changes made.

## Evidence

The pilot transcript (Finding 1 — no-skill route) confirmed that the `starter-prompt` routes through no installed skill. The model reads the codebase directly and writes `docs/architecture/reference.md` without invoking `architect-design`, `architect-review`, `architect-diagram`, or `adapt-to-project`.

Because no skill fired, there is no skill behavior that deviated from its spec. No evidence-led changes to any skill file are warranted.

## Tutorial correction

One tutorial accuracy correction was made (T2 step 8): the phrase "it may ask you a few confirming questions before writing the file. Follow its prompts" was removed from the tutorial's Step 2 paragraph. The pilot observed the agent reads the codebase and writes the file without asking. This is a tutorial-to-evidence alignment fix, not a skill change.

## adapt-to-project (core pack) — out of scope

The pilot confirmed that `adapt-to-project` does not fire during a standalone starter-prompt session (no `.adapt-install-marker.toml` present). The `reference.md` creation behavior inside `adapt-to-project` (Class 2/3) is a separate, post-install flow. No gap in `adapt-to-project` was observed — it behaved correctly by not triggering. Any changes to `adapt-to-project` are out of scope for this pilot.
