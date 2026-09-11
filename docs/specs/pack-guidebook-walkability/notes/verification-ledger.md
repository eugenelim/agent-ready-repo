# Verification ledger

Execution evidence for the build run beginning 2026-09-11. Recorded here rather
than in the spec, because the spec states outcomes and this records what was
observed.

## T1 — the contract in `guides/AGENTS.md`

**Destination.** `guides/AGENTS.md`, 36 lines before and 108 after. Precedent
for a substantive scoped file is 66 to 80 lines (`packs/AGENTS.md`,
`web/AGENTS.md`, `docs-site/AGENTS.md`), with root `AGENTS.md` at 120.

**Why not `docs/CONVENTIONS.md`:** it is byte-identical to
`packs/core/seeds/docs/CONVENTIONS.md` and listed as a self-hosting projection
at `packs/AGENTS.local.md:12`. `AGENT_RULES.md` and root `AGENTS.md` are seeded
for the same reason. `guides/AGENTS.md` is not seeded, and root `AGENTS.md`
§ Rule lookups already obliges an agent to read every scoped `AGENTS.md` on the
path to the file it is changing — so the contract is read by construction.

**Gates.** `git diff -- packs/ docs/CONVENTIONS.md AGENT_RULES.md AGENTS.md` is
empty, so no seeded surface was touched.

| Gate | Result |
| --- | --- |
| `python3 tools/validate_guides.py` | 0 |
| `python3 tools/lint-guide-titles.py` | 0 |
| `python3 tools/check-guide-index.py` | 0 |
| `python3 -m pytest tools/test_lint_guidebook_steps.py -q` | 5 passed, 0.18s |

### Mutation proofs — AC-0001

Each mutation was applied to `guides/AGENTS.md`, the suite run, and the mutation
restored **by editing**; every restore was confirmed byte-identical with `diff`.

| Mutation | Observed |
| --- | --- |
| Remove the whole contract section | **Killed.** 5 of 5 failed |
| Keep the identifiers, delete the normative statement | **Killed.** Only the binding case failed — 1 failed, 4 passed |
| Keep the statement, delete the obligation table rows | **Killed.** Only the identifier case failed |
| Add a machine-owned obligation id to the judgement-kinds closed set | **Killed** — see the two defects below |
| Delete the judgement-kinds closed set | **Killed.** Only that case failed |
| Delete the prohibited-vocabulary section | **Killed.** Only that case failed |

### Two guards that could not fail, found by mutation

Both were in the first draft of the judgement-kinds parser, and both were found
because the mutation survived rather than by reading the code.

1. **The parser could not see the shape it existed to detect.** The judgement
   kinds were matched with `` `([a-z][a-z-]+)` ``, which cannot match an
   underscore — and **every** machine-owned obligation identifier contains one.
   So adding `artifact_outline` to the closed set was invisible and the mutation
   passed. Widened to `[a-z_-]`.
2. **Widening it then produced a false positive.** The section's prose names
   `judgement_check`, which is itself an obligation identifier, so a
   whole-section parse flagged an overlap that was not there and the green
   baseline failed. **The contract's shape was the defect, not the parser:** the
   closed set is now stated as a list, and the parser reads list items only.

The second is the more useful finding. A contract meant to be read by a tool
has to be written to be parsed unambiguously, and prose that mentions an
identifier while describing it is indistinguishable from prose that declares it.

## Divergence between the spec and the implementation, resolved by amendment

The spec's Testing Strategy said AC-0001's observation is that "the enumerated
obligation identifiers match the spec's table, compared rather than read".
**That is not implementable:** the spec's obligation table is numbered `1`…`12`
and carries no identifiers, so there is nothing to compare against. Discovered
while writing the test, under the owner's standing authority to adapt on
findings.

AC-0001's oracle is therefore **structural**: the section exists, carries a
normative statement that binds every step, enumerates obligations by identifier
with no duplicate, declares its judgement kinds with no overlap against the
obligation identifiers, and declares its prohibited vocabulary. Each part fails
independently, which the mutation table above demonstrates.

The obligation set's agreement with the **lint** is AC-0003's, and that is where
the real drift risk sits — the contract and its enforcement diverging. Coupling
AC-0001 to the spec's own prose would also have made a frozen spec the runtime
oracle for a living contract.

The spec's Testing Strategy entry was amended to match, and the cohort baseline
re-pinned. That re-pin is a re-approval in substance: it clears the retry
counters and the stasis baseline and re-hashes whatever is on disk.


## T1a — the deliverable-form ledger

Written to
[`deliverable-form-ledger.md`](deliverable-form-ledger.md): 74 rows, three
predicates stated, form measured as a first-match cascade.

**It corrected the plan, which is why it exists.** The plan called
`product-strategy` the most expensive pack for the outline obligation. It is
not: `core` declares no form for **13 of 18** skills, against 8 of 9 for
`product-strategy` and 7 of 20 for `experience-design`. The earlier claim named
the wrong pack *and* rested on a predicate that returned 0 or 1 for the same
pack depending on how it was written.

The 33-versus-38 spread in the earlier measurement is also explained: those
counted overlapping predicates independently, so a skill declaring form two ways
was counted twice. The cascade counts each skill once — 63 of 74 name a path,
41 declare form, 33 declare none.

Wave order is unchanged, because it never rested on cost. The ledger removed a
false justification, not a dependency.

## T2 — the lint

Implemented by a scoped Codex worker (`gpt-5.6-terra`) against the contract,
then verified against the diff rather than the report. `tools/lint-guidebook-steps.py`
is pure-stdlib per `tools/AGENTS.md` and copies none of the contract's three
lists — it parses identifiers, labels, judgement kinds and vocabulary out of
`guides/AGENTS.md`.

| Gate | Result |
| --- | --- |
| `python3 -m pytest tools/test_lint_guidebook_steps.py -q` | 24 passed, 0.43s |
| with `test_validate_guides.py` and `test_check_guide_index.py` | 64 passed, 1.45s |
| `python3 tools/lint-guidebook-steps.py --help` | 0 |
| `python3 tools/lint-guidebook-steps.py` with no arguments | 2 |
| `python3 tools/lint-guidebook-steps.py guides/does-not-exist` | 2 |
| `validate_guides` / `lint-guide-titles` / `check-guide-index` | 0 / 0 / 0 |
| `git diff -- packs/ docs/CONVENTIONS.md AGENT_RULES.md AGENTS.md` | empty |

### Mutation proofs

One omission fixture per obligation identifier, derived from the contract, each
requiring the registered check to emit that identifier — twelve obligations plus
`artifact_outline`'s divergence mode. Also exercised: a judgement check with no
declared kind, a kind naming a machine-owned obligation, and an unresolvable
named concept. All killed.

### Three defects found while verifying, none in the worker's report

1. **AC-0003's diagnosis was a wall of red.** Adding an obligation the contract
   names with no label form behind it does fail — `parse_contract` raises
   `contract label table omits: <name>` at exit 2 — but every other case fails
   with it, so the cause was unstated. A targeted case now pins that the refusal
   **names** the unimplemented obligation, and it fails when `parse_contract` is
   mutated to tolerate the omission.
2. **Two prohibited terms were never enforced.** `faster adoption` and
   `productive sooner` were written in prose that wrapped across a newline, so
   the backtick span was not one token and the parser skipped them silently —
   six of eight terms parsed. The vocabulary is now a list, one term per line,
   and a guard asserts every backticked span in that section reaches the parser.
   Proved by returning one term to wrapped prose.
3. **The docstring had the same defect**, listing every label twice and wrapping
   `**Agent returns:**` mid-label, which is what made the docstring case fail
   once the duplicate was removed. Labels are now one per line.

**The pattern is worth naming:** a backticked token wrapped across a newline
stops being a token. It bit the judgement kinds, the prohibited vocabulary and
the docstring — three times in one contract — and in every case the parser
failed open rather than complaining. A contract meant to be machine-read has to
be written so no declaration can be split by reflow.

### Residual, stated rather than claimed closed

The lint derives each obligation's label-presence check from the contract's
label table, so "registered but no-op" cannot arise for a label-presence
obligation. But an obligation whose enforcement needs semantics **beyond** label
presence — as `artifact_outline`, `judgement_check` and `concept_resolved` all
do — would receive only the generic label check if it were added without bespoke
logic. Nothing detects that. It is recorded in the suite beside the AC-0003 case
and is the honest limit of what AC-0003 reaches.


## T4 — the cold read, and what it was allowed to block

A fresh Codex session read only the five rendered `build/docs/.../how-to/*/index.html`
pages, barred from `docs/`, `packs/`, `guides/`, and any file named `spec`,
`plan`, `AGENTS` or `JOURNEY`. It answered eight questions per step and four
whole-walk questions.

**It labelled eleven findings "execution defects" and the criterion, as first
written, made every one a blocker.** Owner correction: **only a mechanically
decidable finding blocks a wave.** Severity is not a cold reader's to assign,
and two models arguing about malleable prose is not a gate. AC-0021 and T4 were
amended to say so.

### Mechanically decidable — closed by a lint check, not by editing prose

Each was a **gap in the lint**, which is why closing it is worth more than
fixing five pages: it cannot recur in the four remaining packs.

| Finding | The check now enforcing it | Proof |
| --- | --- | --- |
| Step 5's `**Next:**` was a prose promise — "continue with the build workflow" — naming nothing clickable | `next_step` must carry a resolving link | Reverting the link reds; restored byte-identical |
| `[/screen]` — the reader could not tell literal from argument from placeholder | a templated segment uses `<segment>` and no other form | Reverting reds |
| **168 `*(Rung: …)*` markers published to readers.** The reader asked what "Rung" meant | provenance belongs in an HTML comment; visible prose reds | Reverting one marker reds |

The third is mine, not the worker's: the contract said *record* the rung and
never said **where**. It now says an HTML comment — machine-readable for
AC-0006, invisible to a reader.

### Judgement — recorded, dispositioned, not gated

Authoring guidance for waves 2 and 3, not blockers:

- Where the prompts are typed, and what `<output_dir>` and `<slug>` mean. The
  guidebook assumes an invocation context it never states.
- Whether a skill is optional **within** a step. Step 1 calls
  `service-blueprint` and `process-mapping` "useful context, not gates" while
  presenting them in the same imperative form as the gated primary action;
  `experience-status` gives no signal either way; step 2 never says whether
  `copy-direction` and `tone-of-voice` are both needed or alternatives.
- `experience-reviewer` is described as required but is a subagent, not a
  skill, so there is nothing to type. **I first classified this as mechanical
  and it is not**: the added runnable check fires only on the `Run `x`` form,
  which these pages never use for it. The claim is about prose adequacy.
- Undefined domain terms — SIPOC, stable referent, arbitration test, semantic
  token, spatial layout grammar, transaction bridge — and the unexplained
  review categories. This is precisely the residue AC-0022 does not reach,
  which is why the cold read owns it.
- Site pagination and the in-body `Next:` disagree: pagination leads to "Choose
  the right copy skill" while step 5 points at the build loop. The survey's own
  "duplicated or contradictory next pointers" anti-pattern, arriving in our
  output. Recorded because the sidebar order is generated and the fix is a
  navigation decision, not a page edit.

### What held up, confirmed by a reader who could not see the source

All five steps state "Step N of 5". Steps 1 to 4 carry resolving in-body `Next:`
links, so the order is discoverable from the pages rather than only from
navigation. The agent's turn is attributed in an `Agent:`-prefixed blockquote
and distinguishable from the reader's input. Step 4's genre-direct choice —
pick one structural pass, keep the interaction work — read clearly.

### After the fixes

`lint-guidebook-steps guides/experience-design` exits 0; 24 contract cases pass;
the three guide validators exit 0; the new step-5 target
`guides/README.md` § P3 exists.
