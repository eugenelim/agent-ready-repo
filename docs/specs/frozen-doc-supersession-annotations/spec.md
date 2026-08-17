---
title: Annotate the frozen documents that actually relied on a superseded decision
slug: frozen-doc-supersession-annotations
---

# Spec: frozen-doc supersession annotations, decided per document

- **Status:** Shipped
- **Owner:** eugenelim
- **Plan:** none — see § Named deviation
- **Mode:** full (governance surface — it applies `docs/CONVENTIONS.md`
  § *Superseding a frozen document* to ten frozen documents, and the rule it
  applies is convention-enforced, not machine-enforced. A reviewer is the only
  thing standing between a supersession and a wrong one.)
- **Constrained by:**
  [`frozen-spec-supersession`](../frozen-spec-supersession/spec.md)
  (the mechanism and the survey this closes);
  [ADR-0040](../../adr/0040-route-cohort-skills-to-shared-agents-skills-home.md)
  (the supersession being recorded);
  [ADR-0042](../../adr/0042-agent-additions-keyed-to-loop-and-work-type.md),
  [ADR-0084](../../adr/0084-nosec-reason-delimiter-and-stderr-as-a-gate.md),
  [ADR-0020](../../adr/0020-per-pack-diataxis-hierarchy-for-guides.md) and
  [ADR-0055](../../adr/0055-starlight-replaces-mkdocs-for-reference-docs.md)
  (the four supersessions found **not** to warrant a spec-end annotation)
- **Contract:** none
- **Shape:** service

> **Spec contract:** this document defines what "done" means. The implementing
> PR must match this spec, or update it. Verification must be derivable from it.

## Named deviation from full mode

The `loop-engine` / `loop-cohort` state machine was not run, and there is no
`plan.md`. The two human approval gates it sequences — **spec-approved** and
**plan-approved** — were **granted up front by the requester**, as a standing
instruction to carry this through to merge. The merge decision itself was
explicitly retained. `adversarial-reviewer` was run. Same deviation shape as
`frozen-spec-supersession`, the spec this closes.

## Objective

`frozen-spec-supersession` wrote down how a frozen document records that a later
decision reversed part of it, applied it to one spec directory, and surveyed the
rest without touching them — because the rest are **not** a mechanical rewrite.
Its § Survey says so plainly: *"citing ADR-0017 does not mean a spec teaches the
reversed spelling."*

This spec is the judgment pass that survey deferred, plus one adjacent
application of the same mechanism (`bandit-nosec-comment-hygiene`'s § Known
skip, whose register pointer was closed out from under it).

The deliverable is mostly a decision, and mostly a decision **not** to annotate.
Nineteen frozen specs cite a superseded ADR, and a body grep finds seven more
documents stating a superseded skill home without citing the ADR — one of which
teaches it as a normative rule. **Five specs get an ADR-0040 pointer, over eight
`Status` lines**; two more specs get a closed-anchor pointer, which is a
different thing (§ Decision 5). Ten documents edited, one line each.

## Decision 1 — the test is "does the body teach the superseded sub-decision", not "does it cite the ADR"

`Constrained by:` is a weak signal. A spec cites the ADR that governed it, which
is usually the ADR's *standing* half. The question the convention actually asks
is whether *"a reader who starts there [is] left following a rule we no longer
keep"* — so the test is applied to the body:

> **Annotate when the document's body states the superseded sub-decision as an
> operative rule.** Leave it alone when the citation is a bare `Constrained by:`
> reference, or when the body states the part that still stands.

**The `Constrained by:` scan is the *starting* set, not the population.** It
structurally cannot see a document that teaches the superseded rule without
citing the ADR — and `frozen-spec-supersession` § Survey said as much ("a plain
grep returns roughly twice as many") without acting on it. Adversarial review
found two such documents, one of them a normative table. So each chain is
derived twice: once from the header field, and once from a body grep for the
superseded content itself. § Decision 4 records what the second pass added.

Applied below to every supersession chain in `docs/adr/`, not only the three
`frozen-spec-supersession` surveyed. Each verdict is measured against the tree,
not read off a docstring — the method is in § Testing Strategy.

## Decision 2 — ADR-0017 → ADR-0084: annotate none

ADR-0084 supersedes the **reason-delimiter spelling** in ADR-0017's
suppression-policy sub-decision, and nothing else.

A scan of `docs/`, `packs/`, `guides/`, `tools/` and `.github/` for the reversed
form — matching the placeholder spelling as well as a literal `Bnnn`, which a
`Bnnn`-only pattern misses — finds it in exactly **seven files**, in three kinds:

| File | Kind |
| --- | --- |
| `docs/adr/0017-*.md`, `docs/adr/0084-*.md` | Quoted while recording the amendment / the reversal |
| `docs/specs/bandit-nosec-comment-hygiene/spec.md` | Quoted while recording the reversal it implements |
| `docs/specs/bandit-nosec-form-lint/spec.md` AC2 | Quoted to assert the form *fails* the new lint |
| `tools/test-lint-nosec-form.py` | Two test fixtures asserting the same |
| `docs/specs/sast-sca-tooling/spec.md` + `plan.md` | **Taught as the rule — and already annotated** by `frozen-spec-supersession` |

Only the last row teaches it, and it is already done. Ten specs cite ADR-0017 in
`Constrained by:` without a pointer — `bandit-nosec-comment-hygiene`,
`build-check-single-verify`, `compare-bandit-suppressions`,
`core-path-confinement`, `infra-aware-work-loop`, `local-gate-ci-parity`,
`npm-sca-gate`, `operational-safety-checklists`,
`pack-script-root-boundary-validation`, `security-reviewer-shift-left` —
and **none of them teaches the spelling.** They cite it for the gate itself — the tool choices, the severity floor, the
real-fix-first ladder — every one of which ADR-0084 explicitly leaves standing.
Stamping ten specs with "superseded in part" over a sub-decision none of them
states is precisely the false positive `frozen-spec-supersession` § Boundaries
names as *worse than silence*.

(`frozen-spec-supersession` § Survey put this at "four locations", counting
`sast-sca-tooling/` as one directory. Counting by **file**, and including
`bandit-nosec-form-lint` and the test fixtures — which post-date or were omitted
from that scan — gives seven. Same conclusion.)

## Decision 3 — ADR-0023 → ADR-0042: annotate none

This one looks like the strongest candidate and is the weakest, because
ADR-0023's Status reads `Superseded by ADR-0042` without an "in part" — so a
mechanical reading would annotate all three citing specs.

**The decisive fact is that ADR-0023 already forwards, with scope.** Its Status
does not read a bare `Superseded by ADR-0042`; it reads *"Superseded by ADR-0042.
ADR-0042 keeps this ADR's core holding (the ceiling binds the core code-review
gate) and generalizes the rest."* A reader arriving from any of these specs'
`Constrained by:` links is told immediately which half survived. Rule 3's
between-ADRs annotation is already done and already scoped; a spec-end pointer
would add nothing it does not already have.

Four specs cite ADR-0023. Three are tabulated here; the fourth,
`frontend-engineering-skill`, is treated below. All rely on the surviving half,
and only on it:

| Spec | What it says | Verdict |
| --- | --- | --- |
| `architect-design-reviewer` | `Constrained by: RFC-0032, ADR-0023`; the body never restates the ceiling | Bare citation → no annotation |
| `infra-grounding` | § Never do: *"Add a fourth reviewer or a dedicated `infra-contract-reviewer` (three-reviewer ceiling; ADR-0023)"* | Still foreclosed — but by ADR-0042's *"two agents that would run in the **same gate on the same surface** should be **one**"*, not by a count. Same answer, restated reason → no annotation |
| `operational-safety-checklists` | *"depth … without a fourth reviewer (ADR-0023)"*; *"`quality-engineer` remains the consumer; no new reviewer is added"* | Same → no annotation |

Under ADR-0042 the answer to all three is unchanged, though for `infra-grounding`
and `operational-safety-checklists` the *reason* is now the same-gate/same-surface
clause rather than a flat count. None would decide differently today. What
ADR-0042 generalized is the treatment of agents serving a *different loop or work
type*, which is not what any of them relied on.

`frontend-engineering-skill` also cites ADR-0023 and carries a
`Superseded in part` note — but **inside an HTML comment**, and about an
unrelated matter (ADR-0057 deleting a file). It is not the `CONVENTIONS.md` form
and a reader of the rendered document sees a bare `Shipped`; do not count it as
convention-compliant coverage. No annotation is added, for two independent
reasons: the ADR-0023 verdict above applies to it, **and** its `Constrained by:`
names ADR-0042 on the line after ADR-0023, so the reader is forwarded inside the
field they are already reading — the same property that clears
`marketing-docs-link-repair` in § Decision 6.

## Decision 4 — ADR-0013 / 0015 / 0016 → ADR-0040: annotate five specs, eight lines

ADR-0040 supersedes the **skill-home sub-decision** of those three ADRs, and
nothing else. Unlike the other two chains, the implementing specs state the
superseded sub-decision as an *acceptance criterion*:

- `cursor-full-parity` **AC7** — *"`skill` projects via `direct-directory` to
  `.cursor/skills/<name>/`"*
- `gemini-full-parity` **AC2** — *"projects `skill` → `direct-directory`
  `.gemini/skills/<name>/`"*
- `copilot-skills-and-web` — *"copilot `skill` mode is `direct-directory` →
  `.github/skills/`"*, with `.copilot/skills/` at user scope

`contracts/adapter.toml` today routes `skill` to `.agents/skills/` for all three
adapters. Each spec is a document whose ACs assert a filesystem shape the repo
no longer produces. That is exactly the reader the convention protects.

Their `plan.md` files teach the same homes and are `Done`, so both halves of
each directory get the annotation, per `CONVENTIONS.md` § *A spec directory
freezes as a unit*.

### What the header scan reaches, and what it misses

Four specs cite ADR-0013/0015/0016 in `Constrained by:`. All four are annotated,
`copilot-full-parity` included — its earlier exclusion is reversed under
Concern 7 below, so this is not a body-grep find:

| Spec | Files | Verdict |
| --- | --- | --- |
| `cursor-full-parity` | `spec.md` + `plan.md` | **Annotate.** AC7 pins `.cursor/skills/<name>/`. |
| `gemini-full-parity` | `spec.md` + `plan.md` | **Annotate.** AC2 pins `.gemini/skills/<name>/`. |
| `copilot-skills-and-web` | `spec.md` + `plan.md` | **Annotate.** Pins `.github/skills/` repo + `.copilot/skills/` user. |
| `copilot-full-parity` | `spec.md` only (its `plan.md` states no skill home) | **Annotate — reversing an earlier exclusion.** Its § banner already marks the skill decision reversed, but names `.github/skills/<name>/SKILL.md` and `~/.copilot/skills/<name>/SKILL.md` as the *replacement*, and ADR-0040 superseded both. Pointing a reader at two further stale paths is worse than not pointing. The Status line names both and says to read the banner through it. |

### The body grep adds one annotation, and six declines

Applying Decision 1's second pass — `grep -rln` for `.cursor/skills/`,
`.gemini/skills/`, `.github/skills/`, `.copilot/skills/` over **all** of
`docs/specs/`, `README.md` included — returns seven documents outside that
header set. One is annotated:

| Document | Verdict |
| --- | --- |
| `distribution-adapters/spec.md` | **Annotate.** § *Primitive types and per-adapter projections* is the canonical projection table, and its Copilot cell still reads `direct-directory` → `.github/skills/<name>/`; the v0.11 Changelog entry states cursor's `.cursor/skills/<name>/` route. A normative table stating a route the build no longer takes is the strongest case in this change — and the header scan cannot reach it, because the spec predates ADR-0013 and cites none of the three ADRs. (The file has no gemini entry at all: `grep -c '\.gemini'` returns 0. An earlier draft of this annotation claimed one.) |

Six are declined, and the reasons are not the same reason:

| Document | Verdict |
| --- | --- |
| `catalogue-ci-export-boundary/spec.md` + `plan.md` | **Decline — the closest call in the set.** Two sentences *are* stale as premises: § Always do `:45` and § Assumptions `:197` both say Copilot "projects to `.github/skills/`", and the `adapter.toml` the second cites now reads `.agents/skills/`. But the operative rule they support — *do not flag these paths* — is still correct, because copilot's `allowed-prefixes.repo` still contains `.github/skills/`. A "superseded in part" stamp would tell a reader the export-boundary decision changed. It did not; only a premise did. Recorded here rather than glossed, because an earlier draft declined this on the wrong grounds — it called both sentences allow-list statements, which they are not. |
| `catalogue-init-self-hosted/plan.md` | **Decline.** A single line asserting the boundary check does not flag `.github/skills/` — an allow-list statement, still true. |
| `shared-prefix-aware-multi-adapter-install/spec.md` | **Decline.** Its skill-home list sits under a `Technical:` ground-truth bullet with a dated probe (`2026-06-26`), in the spec that *implements* ADR-0040. Annotating a document for recording the state it then changed would be backwards. |
| `shared-prefix-aware-multi-adapter-install/plan.md` | **Decline.** One risk bullet about the stale `.github/skills/` / `.copilot/skills/` tree the routing change leaves behind — a description of ADR-0040's own migration consequence. |
| `docs/specs/README.md` | **Decline, and this one is a judgment a reviewer may want to overturn.** It is a **Living** index whose rows summarise *what each spec did*; rows `:116` and `:128` restate cursor's and copilot's skill routes as part of describing those specs, and each row links to the spec, which now carries the pointer. It is not a statement of current projection behaviour, and the supersession convention governs frozen documents. If it should instead be *corrected* as Living-doc drift, that is a different edit under a different rule. |

## Decision 5 — the Known-skip pointer uses the same carrier, but is not a supersession

`bandit-nosec-comment-hygiene/spec.md` § Known skip records a `make ci` failure
and anchors it to `pre-existing-guides-readme-outcome-label-drift` in
`workspace.toml [backlog].open`. That entry was closed by
[`guides-readme-outcome-label-drift`](../guides-readme-outcome-label-drift/spec.md);
the prose pointer now names nothing. `lint-spec-status.py` invariant (iv) checks
only `(deferred: <slug>)` markers, so nothing catches it.

The mechanism is the same — the **Status field is the carrier, the body is not
touched** — but two of the convention's four rules do not apply and saying so is
part of applying it:

- **Rule 1 ("say in part") does not fit.** Nothing about this spec was
  superseded. The annotation says what actually happened: a register anchor
  closed.
- **Rule 2 ("point at the ADR") has no ADR to point at.** No decision was
  reversed; a backlog entry was worked. The pointer therefore names the spec
  that closed it, which is the only record there is.

Rules 3 and 4 hold unchanged: the *annotation* is one-way — the closing spec
adds no pointer back — and no body line moves. (`frozen-doc-supersession-annotations`
does cite `frozen-spec-supersession` in its own `Constrained by:`, but that is a
pre-existing upward citation under § *Cite upward*, not the other end of this
pointer.)

**And the rule is written down, not just used.** Using the licensed carrier for
an unlicensed purpose would leave the next author with a precedent and no rule —
on a surface this spec itself calls convention-enforced, not machine-enforced.
So `CONVENTIONS.md` § *Superseding a frozen document* gains a sibling paragraph
covering exactly this: the same carrier, rules 3 and 4 holding, rules 1 and 2
not applying, and an instruction to say plainly that it is not a supersession.
That is the durable half, the same way `frozen-spec-supersession`'s durable half
was writing the supersession rule itself.

`frozen-spec-supersession/spec.md` is its second caller in this change: its
§ Survey closes with *"Recorded as `frozen-spec-supersession-survey`"*, and this
PR deletes that slug. Closing a register entry without checking what points at
it is precisely the defect being fixed here, and this change would have shipped
it twice over.

## Decision 6 — the two chains `frozen-spec-supersession` never named

Its § Survey covered three chains. Re-deriving from every ADR in `docs/adr/`
whose `Status` names a superseding ADR gives **seven** superseded records —
ADR-0001, 0013, 0015, 0016, 0017, 0023, 0050 — across **five** chains; records
exceed chains because ADR-0013/0015/0016 all forward to ADR-0040. Two chains the
survey never scanned, disposed of here rather than left unexamined:

- **ADR-0001 → ADR-0020.** No spec cites ADR-0001 in `Constrained by:`. Nothing
  to annotate.
- **ADR-0050 → ADR-0055.** One spec cites it: `marketing-docs-link-repair`,
  whose `Constrained by:` names **ADR-0055 on the very next line**, with the
  clause that makes the new target correct. The reader is forwarded inside the
  field they are already reading, so no annotation. (`frontend-engineering-skill`
  has the same property for ADR-0023 → ADR-0042 — see § Decision 3.)

**Both of these are disposed of on the header scan alone, and that is a stated
limit, not an oversight.** § Decision 1's second pass greps for the four
superseded *skill homes*, because those are literal strings; there is no
equivalent grep here without surveying the whole MkDocs → Starlight migration,
which touches ten-plus documents and is a different subject from this spec's.
Adversarial review found one live counterexample already —
`platform-site/spec.md`'s route table still reads
`| /docs/ | MkDocs reference (existing) | 0 | site/docs/ — unchanged |` for a
build that no longer exists, in a spec that cites no ADR and so is structurally
invisible to the header scan. Registered as `adr-0050-supersession-body-survey`
rather than half-done here.

## Acceptance Criteria

- [x] **AC1 — five specs carry an ADR-0040 pointer, over eight `Status`
      lines.** `cursor-full-parity`, `gemini-full-parity` and
      `copilot-skills-and-web` are annotated on **both** `spec.md`'s `Shipped`
      and `plan.md`'s `Done`; `copilot-full-parity` and `distribution-adapters`
      on `spec.md` only (neither `plan.md` states a skill home). Each reads
      `(superseded in part by [ADR-0040](…) — <the skill home this document
      pins> now routes to the shared `.agents/skills/`; …stands)`, linking the
      ADR. **This is the canonical count**; § Objective and § Decision 4 defer
      to it.

- [x] **AC2 — no body line changes in any annotated document.** The
      `--unified=0` diff over the ten annotated files shows exactly ten removed
      and ten added lines, every one of them a `- **Status:**` line. Asserted
      over the diff's changed-line set, not read.

- [x] **AC3 — every declined case is recorded, not silently skipped.**
      § Decisions 2, 3, 4 and 6 name **every** document examined and the reason
      each was left alone — including the ten ADR-0017 citers by name, so the AC
      is checkable against this document alone.

- [x] **AC4 — the ADR-0017 verdict is measured, not assumed.** A repository-wide
      scan for the reversed suppression form — a pattern admitting the `<ID>`
      placeholder, not only a literal `Bnnn` — reports exactly the **seven**
      files tabulated in § Decision 2, and the only one that *teaches* the form
      is `sast-sca-tooling`, already annotated.

- [x] **AC5 — the ADR-0040 verdict is measured, not assumed.**
      `contracts/adapter.toml` is parsed with `tomllib` and the `cursor`,
      `gemini` and `copilot` adapters' `skill` projections are each confirmed to
      target `.agents/skills/` — i.e. the ACs those specs pin are genuinely
      stale. Their `allowed-prefixes` are read too, which is what clears
      `catalogue-ci-export-boundary` in § Decision 4.

- [x] **AC5a — the population is derived twice.** The `Constrained by:` scan is
      re-run over **every** ADR whose `Status` names a superseding ADR (not the
      three `frozen-spec-supersession` surveyed), and a **body** grep for the
      superseded skill homes is run over **all** of `docs/specs/`, `README.md`
      included. Both result sets are tabulated in full — the header scan's four
      specs, and the body grep's seven further documents. The body grep's own
      yield is `distribution-adapters` alone; `copilot-full-parity` is in the
      header set and is tabulated there.

- [x] **AC6 — two closed register anchors are annotated.**
      `bandit-nosec-comment-hygiene/spec.md`'s Status records that
      `pre-existing-guides-readme-outcome-label-drift` was closed and by what;
      `frozen-spec-supersession/spec.md`'s records the same for
      `frozen-spec-supersession-survey`, which **this PR** deletes. Neither has
      a `plan.md` change. No body line moves.

- [x] **AC6a — the non-supersession pointer is a written rule, not a
      precedent.** `docs/CONVENTIONS.md` § *Superseding a frozen document* gains
      a sibling paragraph: same carrier, rules 3 and 4 hold, rules 1 and 2 do
      not apply, say plainly that it is not a supersession. The seed
      `packs/core/seeds/docs/CONVENTIONS.md` and its projection are
      byte-identical.

- [x] **AC7 — every annotated status still parses.** `parse_status` from
      `lint-spec-status.py`, imported and run against each edited `spec.md`,
      returns exactly `Shipped` — confirmed by construction, not inferred from
      the docstring — and `lint-spec-status.py --root . --base-ref origin/main`
      exits 0.

- [x] **AC8 — gates pass.** `python3 tools/lint-ruff.py`, `make lint-mypy`,
      `SKIP_SAST=1 make build-check`, and `make sast` all exit 0.

- [x] **AC9 — both register entries are closed.**
      `frozen-spec-supersession-survey` and
      `bandit-hygiene-known-skip-dangling-pointer` are removed from
      `workspace.toml [backlog].open`, verified with `tomllib`.

## Survey correction

`frozen-spec-supersession` § Survey's table lists **twelve rows over eleven
distinct specs** (`operational-safety-checklists` appears twice, under two
different ADRs). Three corrections, none of which changes a verdict:

**1. The header scan finds nineteen, not twelve.** Re-running it today over
every superseded ADR gives **nineteen** specs citing one, **fourteen** without a
pointer. The survey's table holds eleven distinct specs; these eight are the
remainder, and 11 + 8 = 19 closes:

| Spec | Cites | First commit | Why the survey missed it |
| --- | --- | --- | --- |
| `bandit-nosec-comment-hygiene` | ADR-0017 | 2026-08-16 | Shipped in the same batch |
| `build-check-single-verify` | ADR-0017 | 2026-08-16 | Shipped in the same batch |
| `compare-bandit-suppressions` | ADR-0017 | 2026-08-16 | Shipped in the same batch |
| `core-path-confinement` | ADR-0017 | 2026-08-11 | Predates the survey — missed |
| `pack-script-root-boundary-validation` | ADR-0017 | 2026-08-07 | Predates the survey — missed |
| `marketing-docs-link-repair` | ADR-0050 | — | A chain the survey never scanned (§ Decision 6) |
| `frontend-engineering-skill` | ADR-0023 | — | Missed. It carries a `Superseded in part` note, but inside an HTML comment and about ADR-0057 — not coverage of this chain (§ Decision 3) |
| `sast-sca-tooling` | ADR-0017 | — | Not missed: already annotated by `frozen-spec-supersession` itself, so its § Survey listed the fix, not the gap |

**2. The survey scanned three chains; there are five.** ADR-0001 → ADR-0020 and
ADR-0050 → ADR-0055 were never named. § Decision 6 disposes of both.

**3. The header scan is not the population at all.** § Decision 4's body grep
found `distribution-adapters/spec.md` — a normative projection table teaching a
superseded route, in a spec that cites **none** of the three ADRs and so could
never appear in a `Constrained by:` scan. That is the correction that matters:
the others move counts, this one moves the method. It is now AC5a.

`bandit-nosec-comment-hygiene` deserves one further note: its `Constrained by:`
already names ADR-0084 inline as the record of the reversal, so it carries a
forward pointer already — just not on the Status line. It is also the
implementing spec *for* ADR-0084. Annotating it "superseded in part by ADR-0084"
would be nonsense. (Its Status *is* annotated by this change, for the unrelated
Known-skip reason in § Decision 5.)

## Boundaries

### Always do

- Always decide per document whether the body states the superseded
  sub-decision, and record the verdict for the ones left alone.
- Always keep the annotation on the `Status` line and nowhere else.

### Ask first

- Ask before annotating a document whose superseded sub-decision it may not
  actually rely on. A false "superseded in part" is worse than silence
  (`frozen-spec-supersession` § Boundaries).

### Never do

- Never edit the body of a frozen document, including an "additive" append.
- Never introduce a `Superseded` status token; the vocabulary is closed.
- Never treat a `Constrained by:` citation as evidence of reliance on its own.

## Testing Strategy

Goal-based; every verdict is measured.

| AC | How |
| --- | --- |
| AC1, AC6 | Read the ten edited Status lines. |
| AC2 | `git diff --unified=0 main...HEAD -- <the ten files>`; assert every changed line begins `- **Status:**`, and that there are ten of each sign. |
| AC3 | Present in this document. |
| AC4 | The command in § *Pinned verification commands* below; compare the hit set with § Decision 2's table. |
| AC5 | `tomllib.load('contracts/adapter.toml')`; assert the `skill` projection target **and** `scope.allowed-prefixes` for `cursor`, `gemini`, `copilot`. |
| AC5a | Both commands in § *Pinned verification commands* below. Compare with § Decision 4 and § Survey correction. |
| AC6a | `diff -q packs/core/seeds/docs/CONVENTIONS.md docs/CONVENTIONS.md`. |
| AC7 | Import `lint-spec-status.py` by path; call `parse_status` on each edited `spec.md`; assert `== "Shipped"`. Then the linter, exit 0. |
| AC8 | The four gate commands. |
| AC9 | `tomllib.load('workspace.toml')`; assert neither slug is present. |

### Pinned verification commands

Fenced, not tabled: a markdown table cell forces `\|` on the alternation, and
`grep -E` reads that as a *literal* pipe — the command then matches nothing and
says so silently, which is the same false-negative this section warns about.
Copy these verbatim.

```sh
# AC4 — the reversed suppression form. Matches the `<ID>` placeholder as well as
# a literal Bnnn; a Bnnn-only pattern silently misses both ADRs.
grep -rlnE 'nosec +(<ID>|B[0-9]+)([, ]+B[0-9]+)* *[-–—] ' docs/ packs/ guides/ tools/ .github/

# AC5a, second pass — the superseded skill homes, over ALL of docs/specs/
# including README.md.
grep -rln -e '\.cursor/skills/' -e '\.gemini/skills/' \
          -e '\.github/skills/' -e '\.copilot/skills/' docs/specs/
```

For AC5a's first pass, parse every `docs/adr/*.md` `Status` for
`supersed… by ADR-NNNN`, then scan each `docs/specs/*/spec.md`
`- **Constrained by:**` field for those ADRs.

No new test file. These are one-off document edits against a
convention-enforced rule; a test asserting that a particular spec carries a
particular Status string would pin prose and break on the next legitimate
rewording. `lint-spec-status.py` invariant (i) is the standing machine check and
already covers the thing a machine can check — that the token still parses.

## Honest scope

- **Twenty documents were examined and declined**, and the tally is meant to
  reconcile: **fourteen** from the header scan (ten ADR-0017 citers in
  § Decision 2, three further ADR-0023 citers plus `frontend-engineering-skill`
  in § Decision 3, `marketing-docs-link-repair` in § Decision 6) plus **six**
  from the body grep in § Decision 4. That is the deliverable, not an omission —
  but it rests on judgment a reviewer should re-derive rather than accept. Each
  section names its evidence.
- **The body grep covered one kind of superseded content, not all of them.**
  Decision 1's second pass greps for the four superseded *skill homes*, and the
  ADR-0017 pass for the suppression form, because both are literal strings.
  **Two chains have no such string and rest on the header scan alone:**
  ADR-0023's superseded *framing* (a reviewer-ceiling argument has no fixed
  spelling), and ADR-0050 → ADR-0055 (a body survey there means reading the
  whole MkDocs → Starlight migration — registered as
  `adr-0050-supersession-body-survey`, with a live counterexample already found
  in `platform-site/spec.md`). A document stating either superseded decision
  without citing its ADR would not be found by anything in this change.
- **The residual the convention already accepts still stands.** Someone who
  greps mid-file in an annotated spec lands on the stale AC with no pointer in
  view. `CONVENTIONS.md` rule 4 states this and accepts it; the mitigation is
  that the operative rule lives in a Living file (`contracts/adapter.toml`),
  not that the frozen record gets patched.
- **`distribution-adapters/spec.md` is `Shipped` but demonstrably maintained** —
  every adapter PR appends a Changelog entry to it, and its projection table has
  been edited since it shipped. This change annotates it rather than reopening
  that question, but the question is real: a document in the Frozen class whose
  body the repo routinely amends is the same class of ambiguity
  `frozen-spec-supersession` Decision 2 existed to remove for `plan.md`.
  Registered as `distribution-adapters-lifecycle-class`.
- **Nothing here is machine-enforced.** `lint-spec-status.py` checks the status
  token's vocabulary and nothing else. A wrong annotation would pass every gate.
