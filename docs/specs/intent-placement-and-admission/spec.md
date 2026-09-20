# Spec: Deterministic intent placement and admission

- **Status:** Draft
- **Owner:** eugenelim
- **Mode:** full
- **Brief:** docs/product/briefs/intent-identity-and-registration.md
- **Discovery:** docs/product/intents/FEAT-0001-intent-identity-and-registration.md
- **Constrained by:** ADR-0098

## Objective

Resolve where a new intent is written — repository or personal scope — from configuration the adopter already owns, instead of re-asking every run or hardcoding a path. `frame-intent` resolves an output directory through three tiers while `intake-intent`'s renderer hardcodes `docs/product/intents/{slug}.md`, so an adopter pointing `output_dir` at a personal vault gets the two skills writing to different places. This slice makes placement one decision with one authority, and keeps admission's existing safety checks intact.

Sequenced first: `max + 1` is directory-scoped, so user-scope allocation cannot proceed until a folder is resolved.

## Testing Strategy

- Resolve placement at both scopes against a configured layout file and assert the directory chosen, with no elicitation.
- Assert refusal when a resolved value escapes the repository or requires following a symlink out of it.
- Assert the behaviour chosen for missing or ambiguous configuration, once this spec decides it.
- Assert admission still applies its confinement, provenance and terse-capture checks after the change.

## Acceptance Criteria

- [ ] A configured scope resolves to its directory at repository and personal scope without asking.
- [ ] A resolved value that escapes the repository, or requires following a symlink out of it, is refused rather than falling back.
- [ ] `intake-intent` resolves its write path through the same authority as `frame-intent` rather than hardcoding one.
- [ ] **Decision owed by this spec:** which authority decides whether an intent is repository or personal work, and what happens when that configuration is missing or ambiguous — including whether an elicited answer is persisted and to which scope.
- [ ] Admission's confinement, provenance and terse-capture checks are unchanged in behaviour.
