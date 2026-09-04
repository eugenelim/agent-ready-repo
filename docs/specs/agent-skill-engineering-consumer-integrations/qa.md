# QA record — agent-skill-engineering consumer integrations (INI-009 slice 4)

## What this slice is, and what it deliberately is not

`work-loop` and `architect-design` each gain a bounded step that **inlines its
own request** to the installed agent-skill-engineering provider. Neither reached
it before. Nothing else in either body changes.

The step is not a delegation. Two earlier drafts failed in opposite directions:
the first had each consumer restate ten obligations inline, which made the
acceptance criteria circular — a spec cannot gate prose it also dictates. The
second delegated the contract to a file inside the provider's pack, which a
consumer has no path to and which is absent exactly when the provider is.
Request-inlining is what the one admissible cross-pack precedent actually does
(`packs/architect/.apm/skills/architect-review/SKILL.md:104-120`).

One deviation from that precedent is claimed and recorded: the precedent names
an authored public seam, while this provider is a generated router, which
ADR-0097:97-99 forbids a consumer from naming. The consumer therefore addresses
the capability by its contract version.

## Review ledger

The reviewing session for every row below is **Claude, this session**, working as
supervisor over headless Codex workers. The workers authored T1 through T4; the
supervisor ran every gate, git write, and review, and never reviewed its own
authoring without an independent pass. Both consumer steps were authored by a
worker and walked by the supervisor, so no row records an author grading itself.

### The three-item walk

The spec's *Testing Strategy* makes the step's correctness manual QA at review:
three items per consumer. This is that record.

| Consumer | Walk item | Result | Evidence |
| --- | --- | --- | --- |
| `work-loop` | Every *Always do* element is present and none is expanded beyond it | Pass | All seven elements map to the five sentences at `SKILL.md:399-403`: when and what to invoke in sentence 1, the inline request and the one-call budget in sentence 2, the handoff limit in sentence 3, the absence receipt in sentence 4, response treatment in sentence 5. Nothing outside the seven is asserted. |
| `work-loop` | The invocation condition matches the stated trigger | Pass | "Only when the task concerns a skill, a skill script or evaluation, agent-loop orchestration, a hook, or a plugin … do not invoke it otherwise" — the spec's positive list verbatim, plus its "and not otherwise" clause. |
| `work-loop` | The surrounding workflow is otherwise unchanged | Pass | `git diff --numstat` reports 8 insertions and **0 deletions**, in one hunk at `@@ -396,0 +397,8 @@`. No ordinal moved. Both SHA-256 section anchors that `tools/test_workspace_status.py:1631-1640` pins still match: the Step-0 window is lines 161-235 and the finish-checklist window is 709-731, so the insert at 397 falls outside both. |
| `architect-design` | Every *Always do* element is present and none is expanded beyond it | Pass | The same seven-to-five mapping at `SKILL.md:126-130`, with `agent-extension-design` as the primary task kind. Nothing outside the seven is asserted. |
| `architect-design` | The invocation condition matches the stated trigger | Pass | Same sentence form and same trigger list as `work-loop`, scoped by "Only when" and "do not invoke it otherwise". |
| `architect-design` | The surrounding workflow is otherwise unchanged | Pass | 6 insertions, **0 deletions**, one hunk at `@@ -125,0 +126,6 @@`, placed as the last paragraph of Procedure step 2. No ordinal moved; step `3.` is untouched. |

Obligations were deliberately **not** routed to
`packs/architect/.apm/skills/architect-design/references/knowledge-surfaces.md`.
`SKILL.md:90-94` loads that file only on detecting an enterprise-knowledge MCP
tool, an internal CLI, or an in-repo doc set, and the file scopes eligibility to
those. An installed pack capability is none of them, so obligations placed there
would not load when this seam runs.

### Rounds

| Round | Raised | Sustained | Refuted |
| --- | ---: | ---: | ---: |
| 1-12 — spec and plan, previous sessions | see `.context/reviews/` | — | 3 refuted at round 9 |
| 13 — T1 implementation, supervisor read | 5 | 5 | 0 |
| 14 — T1 implementation, adversarial | 3 | 3 | 0 |

Round 14's repair-origin ratio was **0 of 3**: every finding was a defect in the
worker's original draft, none was introduced by a round-13 repair. That ratio,
not any individual finding, is the signal that the loop was converging rather
than thrashing.

Round 14's report was adopted only after each premise was re-measured
independently, per the discipline that a reviewer's premise is checked before
its finding is taken. That check materially changed one finding: the reviewer
reported the changelog parser as wrong for three artifacts; measuring all
twenty-four showed it wrong for **eighteen**.

## Four oracle defects the review caught, and why each mattered

Every acceptance criterion in this slice is exercised by one roster module, so a
defective oracle is indistinguishable from a satisfied criterion. Four were
found, and each repair ships with a named executable control that reddens when
the defect returns.

That last sentence was false when first written here, and the correction is the
point. Repairs 3 and 4 originally carried only a prose comment, while this
paragraph claimed all four were control-backed — the exact "headline claims more
than the body sustains" habit this work was told to watch for, committed in the
document that exists to catch it. A later review measured it. Both now have a
control, `test_ac14_rejects_the_two_match_shapes_that_can_never_resolve`.

1. **AC1's published-set domain was calibrated to its own answers.** The loader
   matched `` `((?:knowledge|provider) …)` `` — anchored on the seven expected
   diagnostics' own leading words. Planting a `## Provider response` section
   carrying all seven *plus* an invented `capability seam missing` returned
   exactly the expected set, so AC1's set equality passed while the shipped file
   published a value no adopter receives. The domain is now the *shape* of a
   diagnostic: a backticked lowercase phrase with an internal space. Every one of
   the four response statuses (`ok`, `out-of-scope`, `unavailable`,
   `stale-profile`) is a single token, so the space requirement excludes them
   without naming them either. Control:
   `test_ac1_rejects_a_published_diagnostic_the_fixture_does_not_expect`.

2. **AC10's changelog read could not see a multi-artifact release heading.** The
   pattern anchored the em dash straight after each artifact's own
   `[<artifact>][<version>]` segment, so any heading covering several artifacts
   was skipped and an *older* standalone heading returned instead. Measured over
   the shipped file, that is already wrong for **18 of 24** artifacts. Since this
   slice releases three packs in one PR, the natural combined heading would have
   returned exactly the three T0 floors — making AC10's two conjuncts, equality
   with the changelog and strict advance past the floor, mutually unsatisfiable,
   with a failure message blaming the version rather than the parse. The
   precedent this module follows records having been caught by the same defect
   once already (`test_thirty_day_cooling_and_retirement.py:1640-1646`), and that
   precedent's own pattern still only handles the artifact *leading* a heading,
   so it could not be copied for `architect` or `agent-skill-engineering`.
   Control: `test_ac10_reads_a_release_heading_that_covers_several_artifacts`.

3. **AC14 could never have gone green.** It asserted `SPEC_PATH in queue`,
   comparing a path string against a list of TOML inline tables — `False` for
   every valid record. Only a bare path string could have satisfied it, and
   `workspace.toml:13-18` classifies that shape as non-dispatchable. Proven by
   planting a valid canonical queue entry and observing the assertion still
   `False`. Now matched on the entry's `path` key.

4. **AC14's README row was identified by bare-slug match.** `len(rows) == 1`
   over lines containing the slug already fails for a sibling: three lines
   contain `agent-skill-engineering-corpus`, because the index records a hard
   predecessor as a backticked slug in the *Constrained by* column. A later
   sibling citing this slug the same way would have reddened AC14 on a Shipped
   spec that in fact satisfied it. Now identified by link target, which is unique.

A fifth, narrower repair: AC5 excises the contract-version literal before
scanning for the owning pack's product name. That is not a weakened guard — it
is the only reading under which AC2 and AC5 are satisfiable together, because
`agent-skill-engineering-reference/v1` carries `agent-skill-engineering` as a
substring. The exemption is commented in place so a later reader does not
"fix" it back into a contradiction.

## Three deviations from the plan's task scope

**Each pack's eval harness gains three cases.** `packs/AGENTS.md:60` requires a
non-cosmetic pack update to update that pack's eval harness. The first reading
here was that `work-loop` has none, because core's `[pack.evals] skills` list
does not name it — wrong: `evals/evals.json` exists for both consumers.

The size of this out-of-plan change was then set from a miscount, and correcting
it changed what shipped. PR `11c280073`, which shipped the analogous
`project-knowledge-review-enquiry` integration, added **five** cases to
`work-loop`'s harness — `review-enquiry-relevant-candidate`,
`-unavailable-or-abstaining`, `-hostile-authority-manipulation`,
`-misleading-counterclaim`, `-rerun-budget` — plus 72 lines to
`architect-review`'s and four dedicated prose-boundary test modules. This record
first said "exactly two", and two were what shipped.

The omission that mattered was the hostile-authority path: it is precisely what
each step's untrusted-evidence sentence exists to govern, so leaving it
unexercised meant the harness did not test the obligation most likely to be
violated. A third case per consumer now covers it. The remaining two precedent
cases (`-misleading-counterclaim`, `-rerun-budget`) are not carried: this seam
has no refinement budget to exceed — the step allows exactly one call — and no
counterclaim surface, because the response is never weighed against a competing
retrieved claim. Nothing gates any of this; no `make` target runs `evals.json`.

The insert is textual, not a `json.dumps` round-trip. `work-loop`'s harness has
**mixed** unicode encoding, some strings escaped and some literal, so it was
never produced by one serializer call; re-serializing it rewrote eight unrelated
lines. Both files' diffs are now purely additive at 24 insertions and 0
deletions.

## Two deviations already recorded

**`.claude-plugin/plugin.json` is bumped alongside `pack.toml`.**
`packs/AGENTS.md:45-47` requires every non-cosmetic `.apm/**` change to bump
matching versions in **both** files, and
`tests/roster/test_thirty_day_cooling_and_retirement.py` asserts that parity for
`core`. The plan's T6b *Touches* named only `pack.toml (version field only)`.
Both files are therefore bumped for all three packs, and the plan's task scope
is the record that was incomplete, not the rule.

**The spec's lifecycle Status is pinned to `Draft` by AC14's own choice of
collection.** T6a first recorded the Spec-map and index rows as `Implementing`,
which is what the work actually is. Two gates disagree, in opposite directions,
and only running both finds the fixed point:

- `lint-brief-coverage` fails with "the Spec map is stale (auto-derived; do not
  hand-edit the Status column)" unless the brief's Spec-map row equals the
  spec's own `- **Status:**`.
- The reconciliation engine at
  `packs/core/.apm/skills/workspace-status/scripts/workspace_status_engine.py:2925-2926`
  raises `impossible_transition` with detail `queue spec status` for any
  `work.queue` spec whose status is `Implementing` or `Shipped`. `work.active`
  requires exactly `Implementing`; `work.shipped` requires exactly `Shipped`.

AC14 names `work.queue` explicitly, so the status must be `Draft` or `Approved`,
and the Spec map must then repeat it. `Draft` is what the twelve-round-reviewed
contract carried, so it stands; inventing an `Approved` transition here would
assert a gate that never fired. Both `docs/specs/README.md` and the Spec map
therefore read `Draft`. Nothing in this slice moves the spec to `Shipped` — that
transition belongs to close-out, and it will require moving the entry from
`work.queue` to `work.shipped` in the same change.

**`spec.md`'s `- **Brief:**` header lost its backticks.** T6a's queue
registration is what surfaced this. Reconciliation resolves a queued entry's
*artifact parent* from that header, and the value was written as an inline code
span. A backticked string is not a repository-relative path, so registering the
spec raised `invalid_artifact_path` — which **is** in the fail-closed set that
`tests/roster/test_workspace_status_projection.py:939-957` enforces, so AC14 and
a green repository could not both hold while the backticks stood. Attributed by
running the engine over `HEAD:workspace.toml` and over the working tree with the
same repository root: the finding appears only after registration. All four
sibling `agent-skill-engineering-*` specs already write the header unbackticked;
this spec was the only one that did not. The edit changes no criterion, boundary
or assumption — only the delimiter on a header field.

## Residuals, registered rather than resolved

- **The release surface is written for three separate changelog entries, not
  one combined heading.** `docs/CONVENTIONS.md:701-703` describes "one section
  per release, naming every artifact that release covers", which reads as
  licence to combine. Two guards make that unsafe for this release:
  `tests/roster/test_okf_catalogue_discovery.py:90` and
  `tests/roster/test_security_checklists_okf_projection.py:118` each take the
  **first line starting with** `## [<pack>][` and require it to carry that
  pack's current version. `architect` and `core` are both guarded, and a
  combined `## [core][…] / [architect][…]` line starts with only one of them, so
  it would leave the other's topmost heading pointing at an older release.
  Reordering moves the failure rather than fixing it. Three entries ship.

- **AC16's record shape conflicts with `workspace.toml`'s own instructions.**
  AC16 dictates `{slug = …, source = "…#follow-ons", summary = …}`, the legacy
  form. `workspace.toml:13-20` says `[backlog].open` "takes the canonical shape",
  calls legacy forms "never dispatchable", and warns against copying a
  neighbour. The criterion was implemented as written: 145 of the 161 current
  `[backlog].open` entries are legacy, one of them
  (`rfc0099-execution-side-errata`) is shape-identical to AC16 including the
  `#follow-ons` anchor, and `unsupported_legacy` is not in the fail-closed
  finding set that `tests/roster/test_workspace_status_projection.py` enforces,
  so it breaks no gate. Precedent and contract agree against the preamble. The
  repository-wide inconsistency is a real defect and it is not this slice's to
  fix.

## Failure attribution

| Symptom | Reproduction | Disposition |
| --- | --- | --- |
| `packs/core/tests/` refused to collect: `import file mismatch` on `test_project_knowledge_handoff.py` | `python3 -m pytest packs/core/tests/ -q` | `owned-elsewhere`, **not a defect**. Two files share that basename, at `skills/author-delivery-brief/` and `skills/work-loop/`; both exist unchanged at the pinned baseline `236ae549c`. `Makefile:488` says outright "Do NOT collapse the pack-test lines into `pytest packs/*/tests/`" and issues one invocation per skill directory. The sweep was the wrong invocation. |
| `packs/core/tests/skills/work-loop/` ran 20+ minutes without a verdict | `sysctl -n vm.loadavg` → `{ 199.41 206.77 170.44 }`, falling to `{ 111.51 … }`; the pytest process held 7.4s CPU over 21 minutes elapsed while spawning a short-lived subprocess per test | `environmental`, **not carried**. A shared host under peer-worktree load; three worktrees were running pytest concurrently. A run that reaches no verdict is not a measurement. |
| `make test` excludes two work-loop test files | `Makefile:647` passes `--ignore=…/test_lint_spec_status.py --ignore=…/test_lint_traceability.py` | `pre-existing`, **noted**. The gated set is narrower than the directory; the ignore list is the invocation of record. |
