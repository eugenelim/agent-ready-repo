# Spec: the publisher trigger-parity check covers any publisher, not only Claude's

- **Status:** Draft <!-- Draft | Approved | Implementing | Shipped | Archived -->
- **Owner:** eugenelim
- **Plan:** none — authored after the spec is approved
- **Mode:** full (changes a CI gate that decides when marketplace publication runs)
- **Constrained by:** ADR-0079; `docs/specs/claude-plugin-route-scope`
- **Brief:** brief:codex-plugin-route-delivery
- **Discovery:** none
- **Depends on:** none
- **Contract:** none
- **Shape:** service

> **Spec contract:** this document defines what "done" means. The implementing
> PR must match this spec, or update it. Verification must be derivable from it.

## Outcome

A maintainer who adds a second marketplace publisher can have its push-path filter checked against the user-scope roster by the same gate that checks the Claude publisher, with no change to what the gate decides for Claude today. A publisher that skips a pack it owes, or runs for a change it cannot affect, fails the gate.

## What Changes

- `tools/lint-plugin-roster.py` checks one hard-wired workflow (`WORKFLOW_REL`) through `check_publish_trigger`, and derives expected paths from the literal `PUBLISHED` roster plus `PUBLISH_JOB_INPUTS`. It becomes a check over a declared list of publishers, each naming its workflow file and its job inputs, with one entry today.
- The roster stays literal and independent of the eligibility predicate, which is what makes it a tripwire rather than a tautology (its docstring states this).
- The user-scope eligibility rule is already one shared helper, `tools/pack_scope.py` (`allowed_scopes`, `is_user_capable`), used by the membership lint and the site checks. This spec adds no second copy.

## Durable Outputs

| Semantic role | Applicability | Destination | Owner | Expected evidence | Closeout condition |
| --- | --- | --- | --- | --- | --- |
| Maintainer procedure | Applicable | the header comment of `.github/workflows/publish-claude-plugins.yml`, which names `lint-plugin-roster.py` as the allowlist's closure | eugenelim | Comment names the publisher list | Comment updated |
| Release history | Not applicable: tools only, no shipped pack changes | none | none | none | none |

## Agent Rules

### Always do

- Keep the Claude publisher's diagnostics identical on the committed tree.
- Run the roster test's mutation cases after every change.

### Ask first

- Any edit to `publish-claude-plugins.yml`; this slice should not need one.

### Never do

- Never derive the roster from the eligibility predicate.
- Never add a Codex publisher workflow here; that is a later slice.

## Testing Strategy

- **TDD** over `tools/test-lint-plugin-roster.py`: add a fixture with a second synthetic publisher and mutate its filter.
- **Goal-based**: run `python tools/lint-plugin-roster.py` on the real tree before and after and compare output.

## Acceptance Criteria

- [ ] `python tools/lint-plugin-roster.py` on the committed tree prints the same diagnostics and exits with the same code before and after the change.
- [ ] With a second synthetic publisher whose filter omits a rostered pack's path, the check fails and names that publisher and that path.
- [ ] With a second synthetic publisher whose filter lists a path outside its expected inputs, the check fails and names that publisher and that path.
- [ ] With a second synthetic publisher whose filter matches its expected set, the check passes.
- [ ] Removing the Claude publisher's entry from the list makes the check fail rather than pass.
- [ ] The existing roster mutation tests pass unmodified.

## Follow-ons

- eugenelim: [`codex-plugin-route-delivery`](../../product/briefs/codex-plugin-route-delivery.md) slices C2 to C4 — the Codex route, hook translation, and the Codex publish workflow.

## Assumptions

- Defaulted: both publishers share one literal `PUBLISHED` roster, because eligibility is the same user-scope rule (settled by: eugenelim). If wrong: each publisher entry carries its own roster.
