# Plan: work-loop pre-existing failure capture + progressive disclosure

## Tasks

### T1. Create `references/pre-flight-failures.md`
**Verification:** Goal-based — file exists; grep confirms slug/source schema, three-condition heuristic, stash-check method, "made it worse" test, dedup procedure, examples.
**Depends on:** none

**Approach:** Write new file at `packs/core/.apm/skills/work-loop/references/pre-flight-failures.md` following the loaded-when header pattern of `infra-verification.md`. Content: detection methods, entry schema, known-skip heuristic, "made it worse" test, dedup procedure, examples.

### T2. Create `references/self-coverage/protocol.md`
**Verification:** Goal-based — file exists; contains all 6 steps extracted from SKILL.md lines 61–82.
**Depends on:** none

**Approach:** Extract the six-step numbered list from the current self-coverage gate section verbatim, wrap in a loaded-when header, and write to `packs/core/.apm/skills/work-loop/references/self-coverage/protocol.md`.

### T3. Edit SKILL.md — collapse self-coverage gate section
**Verification:** Goal-based — section is ≤8 lines; three net-new items named; non-skippability statement present; pointer to `references/self-coverage/protocol.md`.
**Depends on:** T2 (reference must exist before the pointer is written)

**Approach:** Replace lines 53–82 (the body of the self-coverage gate section) with a 7-line collapsed version naming all three net-new items and pointing to `protocol.md`.

### T4. Edit SKILL.md — remove infra/deploy multi-artifact preflight paragraph
**Verification:** Goal-based — lines 296–304 absent; "Spikes and throwaway exploration" line immediately follows "doesn't feel like one."
**Depends on:** none (parallel with T3)

**Approach:** Remove the paragraph starting "  For **infra/deploy** the mechanism is rarely one artifact..." (source lines 296–304).

### T5. Edit SKILL.md — add GATES pre-existing failure triage paragraph
**Verification:** Goal-based — paragraph present between gate-fail line and doc-drift blockquote; ≤8 sentences; references `pre-flight-failures.md`.
**Depends on:** T1 (reference must exist before the pointer is written)

**Approach:** Insert 6-sentence paragraph after "Don't move past a failing gate by editing the gate." and before "> **Mechanical doc-drift check...".

### T6. Bump core pack version
**Verification:** Goal-based — `packs/core/pack.toml` version incremented; `packs/core/.claude-plugin/plugin.json` version matches.
**Depends on:** none

**Approach:** Read current version (0.13.4), bump to 0.13.5 (patch — prose-only change, no new skill/command/agent primitive).

### T7. Run `make build-self FORCE=1` and `make build-check`
**Verification:** Both exit 0; projected files updated.
**Depends on:** T1–T6 all complete
