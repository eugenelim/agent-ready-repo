# Spec: The readiness bridge reads work-loop's dispatch output

- **Status:** Shipped <!-- Draft | Approved | Implementing | Shipped | Archived -->
- **Approved:** 2026-10-29 by eugenelim, spec and plan at `67addcade`, including the page wording AC-0012 to AC-0015 and AC-0032 state, after two spec-mode shaping, adversarial and spec-stage security review rounds, each adjudicated, with the round-2 repairs accepted unreviewed; records under `.context/reviews/readiness-bridge-dispatch-input-spec-r1/` and `-r2/`. Under controlled amendment from 2026-10-29 after the pre-EXECUTE adversarial and secure-design reviews (records under `.context/reviews/f020b46e-afb2-45b9-89ba-5e179f11f89e/`): the remaining view strings (owner-approved wording, AC-0033) and `--help` text (AC-0034), repeated paths within one list, and the hand-over Ask-first; the approved bytes of `67addcade` are those of the rebased `12f5a8fe8`, now `be25285e5` on this branch. Re-approved 2026-10-29 by eugenelim, spec and plan at `b1f1a0528`, after the amendment's pre-EXECUTE rounds came back clean; the re-approved bytes of `b1f1a0528` are those of the rebased `e3e1b3200`.
- **Owner:** eugenelim, as `navigate-intents` owner and Platform Core maintainer
- **Plan:** [`plan.md`](plan.md)
- **Constrained by:** RFC-0108 (D3, the readiness bridge and its argless mark, and D1 rules 1 to 10 as corrected by its errata), RFC-0105 (D3, through RFC-0108's errata exception, which ends the bridge's `workspace-status` input in the release where `work-loop` stops dispatching from `workspace-status`), RFC-0106 (D1 and D3, list-and-ask in place of first-ready selection), RFC-0055 (errata entries on an Accepted RFC), ADR-0074 (standard-library skill scripts)
- **Amends:** [intent-view-readiness-handover](../intent-view-readiness-handover/spec.md) — the Terms and criteria the § Disposition table below names, each replaced, withdrawn or carried as that table says; its Never-do "Never run `workspace-status`, locate its script…", narrowed to name `dispatch.py` as well.
- **Brief:** brief:workspace-registry-retirement-delivery
- **Discovery:** none
- **Depends on:** spec:header-derived-dispatch
- **Paired with:** `spec-registration-stop`, built on the same branch and shipped in the same `core` release (that spec's criterion 0044); its tasks T1 and T2 come before this spec's T2, T4 and T5.
- **Contract:** none — `dispatch.py`'s output is skill-internal JSON read in `core` only, and the export's result object and payload keep the shape the hand-over spec contracts.
- **Shape:** mixed

> **Spec contract:** this document defines what "done" means. The implementing
> PR must match this spec, or update it. Verification must be derivable from it.
>
> **Not every section is contract.** `Agent Rules`, `Testing Strategy` and
> `Acceptance Criteria` are what a completion gate reads, and an amendment
> changes them. `Outcome`, `What Changes`, `Durable Outputs`, `Follow-ons` and
> `Assumptions` are working material: they orient a reader and an author corrects them in place
> as the work teaches, without an amendment and without a review round. A review
> finding against working material is advisory — it cannot block, because nothing
> gates the text it cites.

## Outcome

A maintainer who pipes `work-loop`'s read-only `dispatch.py --root <root>` output into `navigate-intents export --readiness -` opens an offline intent view whose "What can I work on next?" shows exactly dispatch's active, ready and blocked specs for the records the view loaded, and marks a spec exactly when an argless `work-loop` would start or resume that one spec, never when it would ask. The piped bytes stay untrusted under the hand-over spec's limits, and only node ids of loaded records, finding codes and allowlisted next-action text reach the page.

## What Changes

- **Input checks and the mark** — `packs/core/.apm/skills/navigate-intents/scripts/intent_readiness.py` checks the argless `dispatch.py` output shape in place of `workspace-status status`'s, and takes the start mark from the checked `decision`.
- **Page wording** — the readiness lead line, sort key, start-tag notes, empty-list text, failure notices, the "What is broken?" lead, the mark help, the "Note from" label and the Key name `work-loop`'s dispatch — `scripts/view_src/readiness.js`, `labels.js` and `detail.js`; the `--readiness` help text in `scripts/navigate_intents.py`.
- **Instructions and design note** — the pipe command and every statement about the bridge's input in the skill's SKILL.md and evals, `guides/core/how-to/navigate-intents.md`, and `packs/core/DESIGN.md`.
- **Tests** — the readiness suites under `packs/core/tests/skills/navigate-intents/` take `dispatch.py`-shaped inputs, with a corpus from the dispatch replay's case trees and a hand-built hostile input.
- **Governance and records** — § Errata on RFC-0105, RFC-0108 and RFC-0106; one slice-8 § Equivalence row; the inventory rows `spec-registration-stop` leaves to this spec; a second entry on the hand-over spec's `Amended in part by:` line.
- **Unchanged:** `dispatch.py`; the export's read limit, deadline, payload keys and projection allowlist; every hand-over criterion the Disposition table carries; `navigate-intents`' routing of queue-order questions to `workspace-status`; the pinned finding table, which `spec-registration-stop` keeps equal to the engine's.

## Durable Outputs

| Semantic role | Applicability | Destination | Owner | Expected evidence | Closeout condition |
| --- | --- | --- | --- | --- | --- |
| Interface compatibility: the bridge's input | Applicable: maintainers pipe a command into the export | `navigate-intents` SKILL.md § Export an offline view and § Safety controls; its `evals/eval_queries.json` | `navigate-intents` owner | AC-0019 and AC-0020 pass | Both name the argless `dispatch.py --root` as the one piped command |
| User procedure | Applicable: the guide gives the pipe command | `guides/core/how-to/navigate-intents.md` § Show what is ready to work on, re-read whole | `core` maintainer | AC-0019 passes; the guide lints pass | The section gives the new command and the new failure reasons |
| Current architecture | Applicable: the export's one piped input changes | `packs/core/DESIGN.md`, the paragraph beginning "The export has one piped input" | `core` maintainer | AC-0021 passes | It names `dispatch.py`'s output as the one piped input |
| Current product truth | Applicable: the hand-over spec is amended in part | `docs/specs/intent-view-readiness-handover/spec.md`'s header | `core` maintainer | AC-0025 passes | Its `Amended in part by:` line names this spec |
| Decision rationale | Applicable: RFC-0105's and RFC-0108's bridge exception and the first-ready mark | RFC-0105, RFC-0108, RFC-0106 § Errata; the retirement record's § Equivalence | eugenelim, Approver | AC-0022 to AC-0024 pass | Each carries owner-approved wording |
| Current product truth: registry consumers | Applicable: the bridge rows of the inventory | `docs/specs/workspace-retirement/inventory.toml` | Platform Core maintainer | AC-0026 passes | No bridge row carries owner 8 |
| Verification record | Applicable: browser, real-input, re-run and approval evidence | `docs/specs/readiness-bridge-dispatch-input/notes/verification-ledger.md` | Implementer | AC-0016 to AC-0018, AC-0027, AC-0029 and AC-0030 pass | The ledger holds each run and approval |
| Release history | Applicable: `core` content changes | the changelog fragment `spec-registration-stop` adds, at the same `core` version | Platform Core maintainer | That spec's criterion 0044 passes | The fragment names `--readiness` |
| Delivery membership | Applicable: the brief's coverage map | The brief's Spec map row | `author-delivery-brief` | AC-0028 passes | The row exists |

## Agent Rules

### Always do

- Treat the readiness input as untrusted bytes, and keep only the projection the hand-over spec's criterion 0014 names.
- Decide the start mark from the checked `decision` only after AC-0004 has tied it to the checked lists.
- Put every piped string into the page only as text, through the view's existing element helpers, and keep the shipped content-security policy string with only its digests changing.
- Record every browser, real-input, re-run and approval result in this spec's ledger with the commit it ran against.

### Ask first

- The wording of each § Errata entry AC-0022 to AC-0024 list. The owner approves each before it is committed.
- Any change to the read limit, the deadline, the payload keys, the projected fields, or a hand-over criterion the Disposition table carries.

### Never do

- Never let the export or view code run `dispatch.py` or `workspace-status`, locate either script, start any process other than the export's shipped Git calls, or read `workspace.toml` or any file the readiness input names.
- Never let the readiness input add a node, a row for a record the view did not load, a link or a prompt, and never put piped text into a prompt or an `href`.
- Never change `dispatch.py`, the engine, or a frozen replay fixture.
- Never import from another skill, add a dependency outside the Python standard library or a JavaScript library, or add a module or script part.

## Testing Strategy

- **Input checks and the mark (AC-0001, AC-0002, AC-0003, AC-0004, AC-0005, AC-0006, AC-0007, AC-0008, AC-0009, AC-0031): TDD.** Each rule is a pure function of constructed bytes, so one planted input per rule reds before the check changes.
- **Real inputs (AC-0010, AC-0011, AC-0016): TDD with a corpus.** The outputs `dispatch.py` prints for the replay suite's case trees, for a planted refusing tree, and for this repository are the corpus of real inputs; the hand-built hostile input covers every string member a real output can carry.
- **Page wording (AC-0012, AC-0013, AC-0014, AC-0015, AC-0032, AC-0033): scripted browser check.** `view_browser_checks.py` reads the rendered text, the only oracle for it.
- **The `--readiness` help text (AC-0034): TDD.** `export --help` output is a pure function of the argument parser, so `test_export_readiness.py` reads it and reds before the text changes.
- **Measurements and gates (AC-0017, AC-0018, AC-0029, AC-0030): goal-based and manual QA.** The ledger records the scale, timing, browser, corpus-workflow and design-review runs at the final code commit; the `experience-reviewer` pass is the hand-over spec's completion gate, re-run for the states this spec changes.
- **Instructions, governance and records (AC-0019, AC-0020, AC-0021, AC-0022, AC-0023, AC-0024, AC-0025, AC-0026, AC-0027, AC-0028): goal-based.** A roster check over closed file, section and phrase lists, the inventory check, and a read of the ledger's approval rows.

## Acceptance Criteria

Unless a criterion names another fixture or this repository, it is checked on a whole-corpus export of the `mixed` fixture corpus, opened from local disk, as the hand-over spec's criteria are. Terms used below; the § Disposition table at the end says how each hand-over Term and criterion is read.

- **Readiness input.** The bytes the export reads from standard input when `--readiness -` is given.
- **Base input.** `{"schema_version": 1, "ready": [], "active": [], "blocked": [], "findings": [], "decision": {"action": "none", "path": null, "candidates": [], "findings": []}}`.
- **Item.** An object in the input's `ready`, `active` or `blocked` list.
- **Finding.** An object in the input's top-level `findings`, an item's `findings`, or `decision.findings`.
- **Argless decision.** The decision `dispatch.py` derives with no selector from `active` and `ready`: `resume` with the one active path; `ask` with every active path, in `active`'s order, when there are several; otherwise `start` with the one ready path; `ask` with every ready path, in `ready`'s order, when there are several; otherwise `none`. `path` is `null` and `candidates` empty except where named, and `findings` is empty.
- **Argless refusal.** A `decision` whose `action` is `refuse`, `path` `null`, `candidates` empty and `findings` exactly one finding whose `code` is `invalid_workspace`, in an input whose `ready`, `active` and `blocked` are empty: the output `dispatch.py` prints with no selector when it cannot use `workspace.toml`.
- **Checked lists.** The input's `active`, `ready` and `blocked` after every check of AC-0001 to AC-0006 and the hand-over spec's criteria 0006, 0007, 0008, 0046 and 0047 has passed, before any item is dropped.
- **Reason set.** `not_requested`, `unreadable`, `timed_out`, `too_large`, `empty`, `not_json`, `wrong_schema`, `bad_workspace` and `page_too_big`. No member is longer than `not_requested`.

**Input checks**

- [x] **AC-0001.** Each of these changes to a base input holding one ready, one active and one blocked item, with the argless decision, gives the reason `wrong_schema`: a top-level key absent or added; `schema_version` of `true`, `1.0`, `"1"` or `2`; `ready`, `active`, `blocked` or `findings` absent or not a list; an item that is not an object or whose keys are not exactly `path`, `slug`, `status` and `findings`; an item `path` or `slug` that is not a string; an item `status` that is neither a string nor `null`; an item `findings` that is not a list; a `ready` or `active` item with a finding; one `path` in two of `ready`, `active` and `blocked`; one `path` twice in `ready`, or twice in `active`. A `blocked` item with a `null` `status` passes.
- [x] **AC-0002.** Each of these finding changes, in any of the three places a finding sits, gives `wrong_schema`: a finding that is not an object or whose keys are not exactly `code`, `path`, `dispatchable` and `next_action`; a `code` whose whole string does not match `[a-z][a-z0-9_]{0,63}`, including a valid code followed by a space, `-`, an uppercase letter, a non-ASCII character or a line feed; a `path` that is neither a string nor `null`; a `dispatchable` that is not a boolean; a `next_action` that is not a string, is longer than 500 code points, or holds a code point from U+D800 to U+DFFF.
- [x] **AC-0003.** Each of these gives `wrong_schema`: a `decision` that is not an object or whose keys are not exactly `action`, `path`, `candidates` and `findings`; an `action` outside `start`, `resume`, `ask`, `none` and `refuse`; a `path` that is neither a string nor `null`; a `candidates` that is not a list of strings; and the stdout of `workspace-status status` for the same repository.
- [x] **AC-0004.** An input whose `decision` is neither its argless decision, compared on `action`, `path`, `candidates` and `findings`, nor an argless refusal gives `wrong_schema`. The cases include a `start` naming a blocked item, a `start` naming a path in no list, a `resume` naming a ready item, an `ask` whose `candidates` omit one ready path, a non-`refuse` decision carrying a finding, the stdout of `dispatch.py --start <spec>` for a tree with two ready specs, and the stdout of `dispatch.py --start no-such` for a tree whose `workspace.toml` is absent or usable.
- [x] **AC-0005.** An input that passes AC-0001 to AC-0004 gives `bad_workspace` when a finding at top level, in an item, or in `decision.findings` has the `code` `invalid_workspace`, `configuration_mismatch` or `unsafe_path`; so every argless refusal gives it.
- [x] **AC-0006.** The reason is that of the first failing check in this order: `unreadable`, `timed_out`, `too_large`, `empty`, `not_json`, `wrong_schema`, `bad_workspace`, `page_too_big`; `no_workspace` is not in `REASONS`, and an input carrying a repeated member name and a `schema_version` of `2` gives `not_json`.
- [x] **AC-0007.** Given any readiness input that gives a reason other than `not_requested`, including every failing case of AC-0001 to AC-0006 and of the hand-over spec's criteria 0006, 0007, 0008, 0046 and 0047, on an export whose unchecked baseline fits the budget, the export returns `ok`, exits 0, writes its file and prints nothing to standard error, and its payload equals the payload of the same export without `--readiness` except for `readiness.reason` and `provenance.generated_at`.
- [x] **AC-0031.** Given a checked input whose projection would make the page larger than the export's size budget while the export's unchecked baseline fits it, the export writes the page with readiness unchecked, the reason is `page_too_big`, and the export returns `ok`. The case is checked with the clock pinned through a test seam, so every export in the check carries the same `generated_at`, and the budget lowered to exactly the size of the page the export without `--readiness` writes at that time; every failing case AC-0007 names also returns `ok` under that budget. With `--readiness -`, given an export whose unchecked baseline is one byte larger than the budget, the export refuses with `export_too_large` and writes nothing, for a checked input and for each failing case AC-0007 names; the refusal's `error.limits` carries `budget_bytes` and `bounded_route` `--from` as the export spec's criterion 0022 states, and its `error.observed.bytes` is the unchecked baseline's UTF-8 length.

**Projection and the mark**

- [x] **AC-0008.** Given a checked input whose items' `slug` and `status`, every finding's `path`, and the `code` and `next_action` of every top-level finding and of every finding on a blocked item whose `path` is not a loaded path each hold its own distinct marker string, none of those marker strings appears in the HTML. A path that occurs more than once in `blocked` appears once, with the codes of all its occurrences in input order and repeats removed.
- [x] **AC-0009.** `readiness.start` holds exactly `rule`, `id`, `held` and `active_count`. `rule` is the checked `decision.action`; `active_count` is the length of `active`; `held` is `false`. For `start` and `resume`, `id` is `decision.path`'s node id when it is a loaded path, and `null` otherwise; for `ask` and `none`, `id` is `null`. Given a checked input whose one ready item is `docs/specs/bravo-spec/spec.md` and whose one blocked item holds an `unsatisfied_dependency` finding with that `path`, `rule` is `start` and `id` is `spec:bravo-spec`. Given checked lists whose `ready` holds two loaded specs and whose `active` is empty, `rule` is `ask` and `id` is `null`.

**Real inputs**

- [x] **AC-0010.** For every case tree `packs/core/tests/skills/work-loop/test_header_derived_dispatch_replay.py` builds, and for a planted tree whose `workspace.toml` is not valid TOML, the stdout of `dispatch.py --root <tree>` gives a checked readiness member, or `bad_workspace` exactly when that output holds an argless refusal; a checked member's `active`, `ready` and `blocked` ids are the loaded subset of `dispatch.py`'s lists; and the suite prints the count of trees per reason and per decision action, with the planted tree the one `bad_workspace`.
- [x] **AC-0011.** A hand-built input that passes every check, holding one blocked item at a loaded path whose finding has a valid `code` and a not-known `next_action`, and carrying `</script><script>`, `<img src=x onerror=alert(1)>`, a `javascript:` value, `"><svg onload=alert(1)>`, a U+2028 line separator and bidirectional controls in that `next_action`, in every item's `slug` and `status`, in every finding's `path`, and in the `path` of a second blocked item that is not loaded, gives an `ok` export with readiness checked and that item in `readiness.blocked`, and none of those strings appears in the HTML outside the data block. The stdout of `dispatch.py --root` over a copy of the `mixed` corpus carrying the hostile `workspace.toml` fixture gives an `ok` export with readiness checked in which none of the fixture's hostile strings appears in the HTML outside the data block, and the ledger records how many of them that stdout holds.

**Page wording**

- [x] **AC-0012.** When readiness is checked, "What can I work on next?" lists exactly the records of `readiness.active`, `readiness.ready` and `readiness.blocked`, under the subheadings "Active", "Ready" and "Blocked" in that order, each in its payload order, with a subheading shown only when it holds a row, and the question's rail count is the number of rows. Its title reads "Active, ready and blocked", its lead line reads "Readiness from work-loop's dispatch, read when this snapshot was made.", and its sort key reads "Active, then ready, then blocked, in dispatch order". Given checked lists whose `ready` names the `Draft` spec `docs/specs/charlie-spec/spec.md` and that name nothing else, the list holds only `spec:charlie-spec`, and `spec:bravo-spec`, which is `Implementing`, is not in it.
- [x] **AC-0032.** When readiness is checked and the list shows no row, whether the checked lists were empty or every item was dropped, the list area shows "work-loop's dispatch lists nothing active, ready or blocked in this export." in place of a list. When readiness is checked and `outstanding` is unavailable, the list and its rail count follow AC-0012, and the count is a number, not "unknown".
- [x] **AC-0013.** When readiness is checked and `readiness.start.id` is `null`, a line below the list header reads the start phrase followed by: for `ask` with `active_count` above 0, " asks which of the <n> active items to resume, so none is marked.", with `<n>` the `active_count`; for `ask` with `active_count` 0, " asks which ready item to start, so none is marked."; for `resume` or `start`, " would resume an item outside this export, so none is marked." or " would start an item outside this export, so none is marked."; and for `none`, " finds nothing to start or resume.".
- [x] **AC-0014.** When readiness is not checked, "What can I work on next?" follows the session-start spec's criteria 0002, 0003, 0007 and 0008 and the tree-and-roadmap spec's criterion 0004. For a reason other than `not_requested`, a notice above the list also reads "Readiness could not be checked: <sentence>. Run work-loop's dispatch to see what is ready.", with `<sentence>`: `unreadable` "standard input could not be read"; `timed_out` "nothing finished arriving within 60 seconds"; `too_large` "the piped input was larger than 4 MiB"; `empty` "nothing was piped in"; `not_json` "the piped input was not valid JSON"; `wrong_schema` "the piped input was not argless work-loop dispatch output this view reads"; `bad_workspace` "work-loop's dispatch could not use workspace.toml"; `page_too_big` "the page would have been too large with it".
- [x] **AC-0015.** In a picked record's "What is broken" part, a workspace broken entry whose finding is known reads "Workspace finding <code>: <next_action>"; one whose finding is not known reads "Workspace finding <code>." followed by the label "Note from work-loop's dispatch:" and the `next_action` text; the state line's broken count includes the record's workspace broken entries. While readiness is checked, the opened Key explains ● Active, ▶ Ready and ■ Blocked as readiness from work-loop's dispatch and "Workspace finding" as a finding work-loop's dispatch reported; while it is not checked, the Key holds none of those entries. Every label the page renders over the `hostile` fixture with a checked readiness input is in the closed set in force — the session-start spec's criterion 0022 set as the dependency-graphs spec's criterion 0023 extends it — further extended by "Active", "Ready", "Blocked", "Workspace finding" and "Note from work-loop's dispatch", and every state-mark glyph is one of ● ◆ ◇ ✕ △ ✓ ▶ ■. Over that `hostile` fixture export, no rendered text other than a `next_action` and text the payload takes from a record holds "workspace-status".

- [x] **AC-0033.** When readiness is checked and "What is broken?" lists a workspace finding, its lead reads "Pointers that did not resolve, parent or dependency loops made of resolved pointers, problems the delivery resolver found, and findings work-loop's dispatch reported."; the ▶ and ■ marks' help reads "Ready, as work-loop's dispatch reports it." and "Blocked, as work-loop's dispatch reports it."; the checked Key's Active, Ready and Blocked entries read "Readiness from work-loop's dispatch: it lists this item as active.", "Readiness from work-loop's dispatch: it lists this item as ready." and "Readiness from work-loop's dispatch: it lists this item as blocked."; and the "Workspace finding" Key entry reads "A finding work-loop's dispatch reported about a blocked item, shown with its code."
- [x] **AC-0034.** The `export --help` text for `--readiness` reads "Pass - to read the output of work-loop's dispatch.py --root from standard input." and holds no `workspace-status`.

**This repository and the carried gates**

- [x] **AC-0016.** Over this repository at the final code commit, the stdout of `dispatch.py --root .` gives a checked projection whose `active`, `ready` and `blocked` counts and `start` equal those a ledger-recorded script computes from the same output by this spec's terms, and the stdout of `workspace-status status` gives `wrong_schema`; the ledger records both outputs' SHA-256 values.
- [x] **AC-0017.** The export spec's scale benchmark, re-run with this repository's `dispatch.py` output piped in, meets its thresholds at 1, 10, 25 and 50 times this repository's corpus; an export of this repository with a 4,194,304-byte readiness input that passes every check, made of blocked items naming loaded paths, returns `ok` within 5 seconds on the ledger's machine; and the ledger records each result.
- [x] **AC-0018.** An export of this repository at the final code commit with its `dispatch.py` output piped in, opened in headless Chromium, shows in "What can I work on next?" as many rows as `readiness` holds records, and in "What is broken?" every workspace broken entry; the ledger records both counts.
- [x] **AC-0029.** The ledger holds, at the final code commit: a full `view_browser_checks.py` pass with the count run and none skipped; and a passing `test-corpus.yml` workflow dispatch on the branch, with its run URL, whose run includes every collected `test_*.py` module under `packs/core/tests/skills/navigate-intents/`.
- [x] **AC-0030.** An `experience-reviewer` pass over screenshots of the states this spec changes — checked with a start tag, checked with `ask` over several ready items, a failed check, and "What is broken?" with workspace findings — across the hand-over spec's readiness matrix, against RFC-0108 D1 rules 1 to 10 as corrected and the `skill-html-views` direction's ranked goals, leaves no Major or Blocker finding after adjudication, recorded in the ledger with the screenshots' SHA-256 values and each finding's disposition.

**Instructions**

Each banned phrase below is present in its file at commit `dfa3fe067`, and each check reads the file with each run of whitespace as one space.

- [x] **AC-0019.** In `packs/core/.apm/skills/navigate-intents/SKILL.md`, § Export an offline view and § Safety controls hold none of `workspace-status`, `workspace_status.py`, ``` no ``workspace.toml`` ```, ``` not ``status`` output ``` and `a finding about the item that would be picked`, and § Export an offline view pipes `scripts/dispatch.py' --root` into `--readiness -`. In `guides/core/how-to/navigate-intents.md`, § Show what is ready to work on holds none of `workspace-status`, `workspace_status.py`, `the repository has no`, `a finding about the item it would pick` and ``Pipe only the `status` subcommand``, and pipes `scripts/dispatch.py' --root` into `--readiness -`.
- [x] **AC-0020.** `packs/core/.apm/skills/navigate-intents/evals/eval_queries.json` does not hold `readiness from workspace-status`, and holds a query naming `work-loop`'s dispatch with `should_trigger` `true`.
- [x] **AC-0021.** In `packs/core/DESIGN.md`, the paragraph beginning `The export has one piped input` holds none of `workspace-status`, `status mode` and `strict status object`, and names `dispatch.py`.

**Governance and records**

- [x] **AC-0022.** `docs/rfc/0105-artifact-derived-navigation-and-workspace-retirement.md` § Errata holds an entry dated on or after 2026-10-29 that links RFC-0106 and holds `D3`, `navigate-intents` and `dispatch.py`.
- [x] **AC-0023.** `docs/rfc/0108-skill-html-view-standard.md` § Errata holds an entry dated on or after 2026-10-29 that links RFC-0106 and holds `D3`, `dispatch.py` and `argless`.
- [x] **AC-0024.** `docs/rfc/0106-stop-registering-derivable-work.md` § Errata holds an entry dated on or after 2026-10-29 that holds `the readiness bridge's first-ready mark`, and `docs/specs/workspace-retirement/retirement-record.md` § Equivalence holds a slice-8 row whose Case is `the readiness bridge's first-ready mark`, Result `accepted removal`, Authority that entry, under the [`workspace-retirement`](../workspace-retirement/spec.md) spec's row rules.
- [x] **AC-0025.** The `Amended in part by:` line of `docs/specs/intent-view-readiness-handover/spec.md` gains a second entry naming this spec, and no other line of that file changes.
- [x] **AC-0026.** In `docs/specs/workspace-retirement/inventory.toml`, every row the `spec-registration-stop` spec's criterion 0034 leaves to this spec, apart from this spec's own `docs/specs/readiness-bridge-dispatch-input/*` `contract` row at owner `8`, carries an owner other than `8`; and the inventory check passes.
- [x] **AC-0027.** `docs/specs/readiness-bridge-dispatch-input/notes/verification-ledger.md` holds one row for each entry AC-0022 to AC-0024 list, naming its target file and the owner's approval with an ISO 8601 timestamp to the minute with its UTC offset, earlier than the author date (`git log --format=%aI`) of the commit that adds that text.
- [x] **AC-0028.** The brief's Spec map holds `readiness-bridge-dispatch-input`, and `lint-brief-coverage.py` passes.

### Disposition of the hand-over spec

Each hand-over Term and criterion not named here carries unchanged, read with this spec's Terms: `canonical.ready`, `canonical.active`, `canonical.blocked` and `canonical.findings` as `ready`, `active`, `blocked` and `findings`; an entry as an item; the status input as the readiness input; the base status as the base input. This spec is the hand-over Ask-first's ask for the accepted mode, the reason set and the start rules, decided by the owner's approval; that rule carries unchanged for every other change. Every citation of a hand-over Term or criterion this table replaces, in the hand-over spec's own § Amended criteria and rules rows and in the `intent-view-record-owners` spec, reads as citing its replacement here. The hand-over row narrowing the dependency-graphs Never-do reads: the export's argless `work-loop` mark copies the checked `decision` of `dispatch.py`'s output (AC-0009); the dependency view itself still reads no `needs` entry and decides no scheduling, readiness or closure.

| Hand-over Term or criterion | Disposition |
| --- | --- |
| Terms "Status input", "Base status", "Entry", "Finding", "Checked lists", "Reason set" | Replaced by this spec's Terms of the same role |
| Term "Ready entry, active entry, blocked entry" | Withdrawn; AC-0001's rule that a `ready` or `active` item holds no finding carries its per-list part |
| 0009, `no_workspace` | Withdrawn; `dispatch.py` runs without `workspace.toml` (AC-0006) |
| 0010, the typed walk | Replaced by AC-0001, AC-0002, AC-0003 and AC-0004 |
| 0011, `bad_workspace` | Replaced by AC-0005; its "each failure output" case by AC-0010's planted refusing tree |
| 0012, check order | Replaced by AC-0006 |
| 0013, fail-closed payload equality | Replaced by AC-0007 |
| 0016, dropped members | Replaced by AC-0008 |
| 0017, repeated blocked path | Replaced by AC-0008's second sentence |
| 0021 and 0049, the argless mark and `held` | Replaced by AC-0009; `held` is always `false`, because a checked `start` or `resume` is what `work-loop` acts on |
| 0022, 0023 and 0028, the checked list and its empty state | Replaced by AC-0012 and AC-0032 |
| 0026, the start-tag notes | Replaced by AC-0013; the `held` notes are withdrawn with `held` |
| 0029, the unchecked list and failure notices | Replaced by AC-0014 |
| 0031 and 0033, workspace finding text, the Key and the label set | Replaced by AC-0015 and AC-0033 |
| 0030's "What is broken?" lead while workspace findings are listed | Replaced by AC-0033; its row context carries |
| 0038, the hostile `workspace.toml` fixture | Replaced by AC-0011 |
| 0041 and 0042, scale and the largest input | Replaced by AC-0017 |
| 0043 and 0044, this repository's real input and export | Replaced by AC-0016 and AC-0018 |
| 0045, the design review | Carried, and re-run for the changed states by AC-0030 |
| 0048 and 0050, `page_too_big` and the over-budget refusal | Replaced by AC-0031 |
| Testing Strategy's ledgered `test-corpus.yml` dispatch | Carried by AC-0029 |

## Follow-ons

- The brief's slice 9 moves whatever engine rules `dispatch.py` still needs into `work-loop`; the bridge then reads a `work-loop`-only output, and the inventory's bridge rows leave the registry's consumers.

## Assumptions

none
