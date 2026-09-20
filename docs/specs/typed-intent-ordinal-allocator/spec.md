# Spec: Prefix-type-aware intent ordinal allocator

- **Status:** Draft
- **Owner:** eugenelim
- **Mode:** full
- **Brief:** docs/product/briefs/intent-identity-and-registration.md
- **Discovery:** docs/product/intents/FEAT-0001-intent-identity-and-registration.md
- **Constrained by:** ADR-0108; ADR-0033; ADR-0098

## Outcome

A new intent admitted into the repository carries a human-friendly typed identity in its filename — `CAP-0001-repository-work-graph.md` is a live example of the shape — so a reader can name an intent by its altitude and number rather than by a slug. An intent at an altitude with no token keeps working exactly as it does today: no ordinal, and nothing an operator reads as a failure. That case never reaches the allocator at all — the router recognizes an unmapped altitude and goes straight to the unprefixed destination — so there is no failure channel for it to surface.

## What Changes

- **New** `packs/core/.apm/skills/work-intake/scripts/intent_ordinal.py` — allocates `max + 1` per type over the intent directory unioned with the records visible on `origin`, and refuses rather than guessing.
- **`packs/core/.apm/skills/work-intake/SKILL.md` § 6** — runs the allocator before it passes the confirmed destination to `intake-intent`, and validates what comes back before composing a path from it.
- **`packs/core/.apm/skills/intake-intent/SKILL.md` Procedure step 3** — one clause: creating at a mapped altitude requires an already-allocated ordinal, and refuses otherwise. No capability or control declaration changes.
- **`guides/core/reference/work-intake-routing-and-lifecycle.md`** — the published `Start routing` table names both intent destinations and what selects between them.
- **Unchanged:** `packs/governance-extras/.apm/skills/new-adr/scripts/next-ordinal.py`, every existing intent filename, and `intake-intent`'s `allowed-tools` and `## Boundaries`.

The existing `next-ordinal.py` cannot be reused: it matches an anchored four-digit-then-separator pattern, so on a directory of typed filenames it returns `0001` with exit 0 and reports `--check` clean because nothing matched. That silent-wrong behaviour is the single most important failure to design against.

The prefix table is closed, and this slice consumes it rather than owning it. The four tokens and the `<TYPE>-NNNN-<slug>.md` filename contract are an owner decision recorded in the parent intent's `## Boundary` (`docs/product/intents/FEAT-0001-intent-identity-and-registration.md:30-37`), which is where the mapping from each recognized `Level` to its token lives; ADR-0033 D2 grounds the recognized `Level` values themselves and leaves the field an open string that no lint closes. Changing a token is a change to that parent, through its lifecycle, not to this spec.

What this slice owns is the matching behaviour. The lookup is an exact match on the bare `Level` value, so any string the parent's table does not list — an adopter's intervening altitude, an absent field, or a decorated value such as a backticked `` `feature` `` — is unmapped. An unmapped altitude is a normal outcome with a defined result, an unprefixed filename, not an error.

An ordinal is assigned at admission, so this slice also owns the minimal integration. Admission has **two entry paths**. `work-intake` § 6 delegates a classified intent, and `work-intake/SKILL.md:60` routes a request that explicitly names `intake-intent` straight to that owner instead. The invariant both paths carry is not that the allocator runs on both, but that **neither creates a mapped-level intent without an ordinal**. It is scoped to creation because adoption is forward-only. That rule is settled by the parent intent's `## Guardrail` — "the intents that carry no ordinal today are not migrated" — and by the brief's non-goal excluding a renumber of the existing corpus, which cites ADR-0108 D6 as precedent for not renumbering rather than as the governing decision. Most intents on disk carry no prefix and sit at a mapped level, so an update-in-place path that allocated or refused would reach nearly all of them; an update touches an identity that already exists, and only a creation assigns one. The corpus size is derived at verification time rather than fixed here, per the brief's own instruction that a measured count is evidence of scale and not the obligation.

They reach that invariant with different mechanisms, because they have different capabilities, and the capability line is not moved by this slice. `work-intake` declares `Bash` and already "passes the confirmed repository destination, and authority mode to `intake-intent`" (`work-intake/SKILL.md:332`), so it runs the allocator and supplies the result. `intake-intent` declares no shell — its `## Boundaries` refuses one outright — so it cannot allocate, and this slice does not grant it one: widening the shell boundary of the skill that handles untrusted intent sources is a larger change than the identity it would buy. Its Procedure step 3, where it "confirm[s] the proposed repository-relative destination", instead refuses a **new** mapped-level admission outright and names the path that allocates. It neither derives an ordinal nor accepts one it is handed: deriving one prompt-only has no view of `origin`, and a supplied `FEAT-9999-<slug>.md` is unverifiable for the same reason — the owner cannot tell an allocator's answer from a guess, so treating a prefix as proof of allocation would readmit the silent-wrong failure through a second door. An **existing** repository path is a different case and is unaffected: step 3 preserves it, prefixed or not, and preserving an identity is not allocating one. An existing unprefixed intent at a mapped level is therefore updated in place with no ordinal and no refusal, which is what the parent's forward-only guardrail means in practice.

ADR-0098 D2 is preserved on both paths: `intake-intent` remains the owner of admitting a repository intent, and confinement, provenance and authority transfer are preserved rather than re-specified. One clause of its Procedure changes; none of its capability or control declarations do.

## Durable Outputs

| Semantic role | Applicability | Destination | Owner | Expected evidence | Closeout condition |
| --- | --- | --- | --- | --- | --- |
| Adopter-facing routing promise | Applicable — the published start-routing table names `docs/product/intents/<slug>.md` as where an admitted intent lands, which becomes false for a mapped level | `guides/core/reference/work-intake-routing-and-lifecycle.md` (the `Start routing` table) | T3 | The table states both destinations and the condition that selects them, asserted by the same prose check that covers § 6 | The published table and the skill bodies agree on where a mapped-level intent lands |
| Release history | Applicable — a non-cosmetic `.apm/**` change | `docs/product/changelog.md`, `core` release heading with a `### Highlights` bullet | T3 | A heading matching the bumped `pack.toml` version, topmost among `core` headings | `tests/roster/test_verification_ledger_contract.py::test_the_core_release_surfaces_agree` and `::test_the_core_release_heading_sits_directly_beneath_unreleased` pass, with `tools/test_build_site_routing.py::test_the_generator_projects_the_real_changelog_into_a_valid_payload` confirming the Highlights bullet reaches the published page |
| Interface compatibility | Applicable — a new `work-intake` → allocator boundary with two exit codes and a caller-side unmapped route that never invokes it | `packs/core/.apm/skills/work-intake/SKILL.md` § 6 and the script's own `--help` | T1, T3 | The exit-code contract stated in both, with one stub case per code | An adopter reading either surface gets the same three outcomes |
| Decision rationale | Not applicable — every load-bearing decision is an owner decision already recorded in the parent intent's `## Boundary` or in ADR-0033, ADR-0098 and ADR-0108 | — | — | — | — |
| Maintainer procedure | Not applicable — no operator runbook changes; the allocator is invoked by a skill, not by a person | — | — | — | — |
| Reusable learning | Not applicable — the one transferable finding, that a max-plus-one helper cannot see an unpushed peer, is already recorded in ADR-0108's Context | — | — | — | — |

## Agent Rules

### Always do

- Resolve an adopter-controlled value before invoking anything, and put only caller-owned fixed or closed-set values on a command line. `work-intake` holds a shell-shaped `Bash` tool, so an interpolated adopter string is that skill's shell authority and no later validation can take it back.
- Return the class, the tri-state, or nothing. Every branch that cannot answer says so; none returns a plausible value on the way out.
- Classify an entry by name before touching it, so an outside-namespace entry is never dereferenced.

### Ask first

- Before adding a token to the prefix table, or changing one. It is an owner decision in the parent intent's `## Boundary`, and the allocator transcribes it.
- Before widening what the allocator writes. It reads; the admission transaction writes.
- Before diverging from `next-ordinal.py` in any way this contract has not already authorized. Four are authorized and grounded: per-type maxima rather than one per directory; the anchored `<TYPE>-NNNN-<slug>.md` shape rather than a bare digit run; refusal rather than degradation on a failed or timed-out remote query; and a tri-state remote view rather than a set. A fifth needs the same grounding rather than a quiet addition.

### Never do

- Never grant `intake-intent` a shell, a network reach, or a new tool. Its `## Boundaries` refuses them for a skill that handles untrusted intent sources, and the invariant this slice needs is bought by a refusal instead.
- Never derive a token for an unmapped altitude, and never accept a supplied prefix as proof of allocation. Both produce a plausible ordinal nobody checked, which is the failure the slice exists to stop.
- Never renumber an existing intent. Adoption is forward-only per the parent's `## Guardrail`.
- Never report a clean duplicate check, or return an ordinal, for a directory the scan did not fully read.
- Never reflect raw `Level` text, a filename, or Git error output into a diagnostic.

## Assumptions

- **A peer's unpushed record stays invisible.** The scan sees the working tree plus records committed on `origin`'s default branch. A sibling worktree that has allocated but not pushed cannot be seen, and ADR-0108's own context records that limit for the same helper. Two sessions allocating concurrently can therefore both take the same number; the `--check` duplicate mode is what surfaces it afterwards, and renumbering is out of scope for this slice.

## Testing Strategy

Each verification item carries an append-only identifier of the form `VI-` plus four digits, per ADR-0108 D1 and D4, independent of the criteria it serves. Every criterion appears in exactly one item; an item spanning two boundaries names both rather than splitting the criterion. Each item states its outcome, mode, boundary artifact and why that boundary. The concrete case inventory — fixtures, parametrizations, hostile values, edge cases — lives in the responsible task's `Tests:` subsection in `plan.md` and nowhere else.

- **VI-0001 — typed sequencing, the level lookup, and what an unmapped altitude keeps (AC-0001, AC-0002):** TDD at `packs/core/tests/skills/work-intake/test_intent_ordinal.py` for the sequencing and the exact lookup, and goal-based plus manual QA at `packs/core/tests/skills/intake-intent/test_intake_intent.py` run unamended and the verification ledger for the rest of AC-0002. Two boundaries because the criterion has two halves: the lookup returning nothing is decidable at the call, while "keeps its full identity, admission and graph participation" is only observable where admission and registration happen.
- **VI-0002 — no filesystem mutation (AC-0003):** TDD, unit artifact. A before-and-after snapshot of the directory and the repository root is the whole check, and it belongs where the call happens.
- **VI-0003 — the filename partition (AC-0004, AC-0013):** TDD, unit artifact. An exhaustive partition is decidable from a name alone, which is what a unit boundary proves and an end-to-end one cannot.
- **VI-0004 — equivalence, owner parity, and the scan's real reach (AC-0005, AC-0014):** TDD at `tests/roster/test_typed_ordinal_collision_equivalence.py`. It must read a second pack's script and this repository's `docs/`, and a pack test may not reach above its pack, so the repository boundary is forced rather than chosen.
- **VI-0005 — refusal over plausibility (AC-0010, AC-0011, AC-0015):** TDD, unit artifact. The distinction between an unknowably incomplete view and a complete-but-empty one is observable only at the call, because the two look identical from outside.
- **VI-0006 — the duplicate control, both halves (AC-0012):** TDD, unit artifact. Same-type duplicates must fail and cross-type equal ordinals must pass; a check carrying only the negative half could reject everything and still look correct.
- **VI-0007 — no adopter string reaches the shell (AC-0016, AC-0020):** the two ends are verified at two artifacts in one item. The caller's end — resolving the level before invoking, and validating what comes back — is `packs/core/tests/skills/work-intake/test_work_intake.py` plus one recorded session at the real Bash boundary, because that is where a shell actually parses and a unit test of the script cannot reach it. The script's end — refusing an out-of-set token or a traversing directory — is TDD at the unit artifact. Ordering is the whole point: the script's checks run after a shell would already have parsed, so they are defence in depth and AC-0016 is what makes the shell boundary safe.
- **VI-0008 — confinement, the link policy, and bounded local Git (AC-0017, AC-0018):** TDD, unit artifact, asserted by observing the refusal rather than by reading the code. Two clauses are platform-gated or need a fixture the approved stub does not build, and carry deferred-assertion records in T1 against the contract's stated 5-second and 65,536-entry bounds.
- **VI-0009 — both entry paths, observed as well as instructed (AC-0006, AC-0007, AC-0008, AC-0009):** goal-based check over both skill bodies, the `intake-intent` manifest, and `test_intake_intent.py` run unamended, **plus** visual / manual QA recorded in `notes/verification-ledger.md`. Both together, in one item, because both skills are prose: the assertions establish what the instruction says, and only a session reaches a written filename, a registered entry, or a refusal. The unmapped admission session runs through registration, since AC-0007's outcome is "admitted *and registered*" and a session stopping at the file cannot see it.
- **VI-0010 — diagnostics leak nothing (AC-0019):** TDD, unit artifact, against the contract's own single-line and 200-byte limits.

### Verification mode per item

| Item | Criteria | Mode | Boundary artifact |
| --- | --- | --- | --- |
| VI-0001 | AC-0001, AC-0002 | TDD, plus goal-based and manual QA for AC-0002's admission half | unit artifact; `test_intake_intent.py` unamended; verification ledger |
| VI-0002 | AC-0003 | TDD | unit artifact |
| VI-0003 | AC-0004, AC-0013 | TDD | unit artifact |
| VI-0004 | AC-0005, AC-0014 | TDD | `tests/roster/test_typed_ordinal_collision_equivalence.py` |
| VI-0005 | AC-0010, AC-0011, AC-0015 | TDD | unit artifact |
| VI-0006 | AC-0012 | TDD | unit artifact |
| VI-0007 | AC-0016, AC-0020 | TDD | unit artifact and `test_work_intake.py`, plus one recorded session at the Bash boundary |
| VI-0008 | AC-0017, AC-0018 | TDD | unit artifact |
| VI-0009 | AC-0006, AC-0007, AC-0008, AC-0009 | Goal-based check plus visual / manual QA | both skill bodies, `test_intake_intent_manifest.py`, `test_intake_intent.py` unamended, verification ledger |
| VI-0010 | AC-0019 | TDD | unit artifact |

The unit artifact is `packs/core/tests/skills/work-intake/test_intent_ordinal.py` throughout. Per-case fixtures and edge cases belong to the responsible task's `Tests:` subsection, not here.

## Acceptance Criteria

- [ ] **AC-0001.** An admission-eligible intent whose `Level` the prefix table maps receives an ordinal, sequenced per type so `CAP-0001` and `FEAT-0001` coexist.
- [ ] **AC-0002.** An intent whose `Level` is absent or unmapped receives no ordinal and no derived prefix, and keeps its full `kind:slug` identity, admission and graph participation.
- [ ] **AC-0003.** Allocation performs **zero** filesystem mutations — no counter file, no shared retired list, no cache, not the intent, and no `__pycache__`. Bytecode is a write: the CLI runs under ordinary Python and loads a sibling module by path, so import caching is suppressed on the production path and not only in the tests. Selecting a destination is not writing one: only the existing admission transaction writes or registers it, after `intake-intent` has applied confinement, provenance and authority transfer.
- [ ] **AC-0004.** The classes are defined against one namespace introducer, `^<TOKEN>-` where `<TOKEN>` is any value in the parent's table, so they are complementary and exhaustive by construction: a name **outside** the namespace does not match the introducer and is skipped without incident; a name matching the introducer **and** the owner's complete filename shape — `^<TOKEN>-\d{4,}-<nonempty slug>\.md$`, end-anchored — is **valid** and counted; a name matching the introducer but **not** that shape is **malformed within the namespace**, and makes the scan incomplete so no ordinal is returned and no clean duplicate check is reported. No name can fall outside all three, and none can satisfy two.
- [ ] **AC-0013.** Validity is the parent's filename contract, `<TYPE>-NNNN-<slug>.md`, not a prefix test. A slugless `FEAT-0001.md`, an unanchored `FEAT-0001.txt`, and any other in-namespace name that is not that exact shape are malformed rather than counted. This is a deliberate narrowing relative to `next-ordinal.py`, whose pattern accepts a bare `0042.md` by design.
- [ ] **AC-0014.** Every maintained copy of the closed mapping holds exactly the parent table's keys and values — no missing entry, no changed token, no extra one. That covers the allocator's mapping, its parser's token namespace, and each shipped prose surface that names a level or a token: `work-intake` § 6, `intake-intent`'s Procedure step 3, and the published routing table. A token the parent does not list is recognized nowhere, so the closed-table rule cannot be widened by an implementation edit or a prose edit alone.
- [ ] **AC-0011.** A scan failure refuses the operation rather than producing a partial count, and covers the remote half of the view as well as the local one: enumeration, classification, or reading an entry locally, and a **failed or timed-out** Git query for the `origin` records. A scan failure is not a filename class and has no skip path. Refusing on a *failed* remote query is a deliberate divergence from `next-ordinal.py`, which degrades to a working-tree-only answer there; that answer is the plausible-but-wrong one this slice exists to stop.
- [ ] **AC-0015.** A directory with **no** `origin` to consult — no remote configured, or no `refs/remotes/origin/HEAD` — is not a scan failure. The view is then the working tree alone, which is the complete answer available, and allocation proceeds. This is what separates a missing remote from a broken query, and without it every allocation outside a cloned repository would refuse.
- [ ] **AC-0005.** On paired fixtures carrying the same logical ordinals in the typed and untyped filename grammars, the allocator returns the same next ordinal as `next-ordinal.py`, so both scripts share one `max + 1` rule and one `origin`-union behaviour. Its scan sees the working tree plus records committed on `origin`'s default branch; an unpushed peer worktree is outside that view, per `## Assumptions`.
- [ ] **AC-0006.** `work-intake` invokes the allocator at a named point in its procedure and supplies the resulting `<TYPE>-NNNN-<slug>.md` as the confirmed repository destination it already passes to `intake-intent`, so a conforming eligible intent is written with its allocated ordinal in the filename.
- [ ] **AC-0007.** Where the level is absent or unmapped, `work-intake` supplies the unprefixed `<slug>.md` destination, so the intent is still admitted and registered with no ordinal in its filename and no partial write. This path is reached by an unmapped level alone, never by an allocation, scan or parse failure.
- [ ] **AC-0008.** `intake-intent` gains no shell, network or new-tool capability, and its confinement, provenance and authority-transfer behaviour does not regress. Admission's controls are preserved rather than re-specified.
- [ ] **AC-0009.** On the direct entry path, where a request names `intake-intent` and no caller has allocated, a **new** mapped-level admission stops with a named refusal that points at the path which allocates. A prefixed destination supplied with the request is not accepted as proof of allocation, because the owner cannot check it against the working tree and `origin`. An **existing** repository path is preserved as today, prefixed or not; preserving an identity is not allocating one.
- [ ] **AC-0010.** When **creating** an intent at a mapped level, an allocation, scan or parse failure stops before any write or registration, on either path. There is no unprefixed fallback for a mapped level, so no path creates a mapped intent without an ordinal. Updating an existing intent in place is outside this criterion: it allocates nothing, and an existing unprefixed intent at a mapped level stays unprefixed.
- [ ] **AC-0012.** `--check` fails when two valid records share a type and an ordinal, and passes when equal ordinals belong to different mapped types, so `CAP-0001` beside `FEAT-0001` is clean while two `FEAT-0001` records are not. This is the control `## Assumptions` relies on to surface a concurrent duplicate allocation.
- [ ] **AC-0016.** No adopter-controlled string reaches the command line. The caller resolves the `Level` against the closed table **before** invoking anything: a mapped altitude yields a token from the closed set, which is what the command carries, and an unmapped one skips the invocation entirely. So every argument — executable, script path, flags, the repository-relative directory, the token — comes from a fixed or closed set the caller owns, and the shell never parses adopter bytes. The caller then validates the allocator's output against the closed `<TYPE>-NNNN` grammar before composing a destination from it, so a malformed or unexpected return cannot become a path.
- [ ] **AC-0020.** The allocator refuses a `--token` value outside the closed set and a `--dir` value that is not a repository-relative path free of `..` segments, as defence in depth behind AC-0016 rather than as its substitute. A caller that got its own resolution wrong gets a refusal, not an allocation.
- [ ] **AC-0017.** Confinement holds through every path component, not only the leaf. The trusted roots are the repository root and the intent directory beneath it; an outside-namespace entry is skipped **without being dereferenced**; and every in-namespace entry that is a symlink, junction, reparse point, device, other non-regular file, or simply uninspectable fails the scan closed. The rule holds on both halves of the view: a remote entry carries its object mode, and an in-namespace entry on `origin` that is not a regular blob fails closed exactly as a local one does. A scan that could not classify an entry never reports a complete result.
- [ ] **AC-0018.** Git access is local-ref only, with no network fetch. Arguments are fixed and non-shell, stdin is closed, repository and object-store redirect variables are removed from the child environment, and two bounds hold: **5 seconds** of wall time per Git invocation, measured from process spawn, inherited from `next-ordinal.py:_GIT_TIMEOUT_SECONDS`; and **65,536 entries** consumed from one `ls-tree` listing, counted as NUL-separated names, which is two orders of magnitude above the largest directory in this repository and the first input that trips it is a listing of 65,537 names. Any breach of those bounds is a scan failure under AC-0011, never a partial answer.
- [ ] **AC-0019.** Diagnostics are single-line and at most **200 bytes** after encoding, and identify the outcome without reflecting raw `Level` text, filenames, Git error output, secrets, personal data, or control characters. The `Level` field is adopter-controlled and open, so echoing it into stderr or a retained log is an injection and disclosure path rather than a convenience.

## Follow-ons

- **The parent intent's validation hook was reconciled on 2026-09-20**, by owner amendment in its own `## De-risk record`, so the governing parent and this contract now agree on what "correct" means. Its kill clause named an `origin` union that "catches an unpushed sibling", which ADR-0108's Context — quoted correctly elsewhere in that same intent — records as impossible for this kind of helper; and its activity required equivalence over the real ADR and RFC corpora, which a typed allocator cannot distinguish from a valid intent directory holding only legacy names. Nothing in this spec changed: the amendment brought the hook to what the criteria already said.

- **A post-admission altitude change reissues behind a tombstone.** An owner decision recorded in the parent's `## Boundary`, delivered by `intent-renumber-and-reissue`, not here.
- **The 23 intents on disk with no registry entry** stay out of scope, per the brief's non-goal.
