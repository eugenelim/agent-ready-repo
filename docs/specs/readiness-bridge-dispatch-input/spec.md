# Spec: The readiness bridge reads work-loop's dispatch output

- **Status:** Draft <!-- Draft | Approved | Implementing | Shipped | Archived -->
- **Owner:** eugenelim, as `navigate-intents` owner and Platform Core maintainer
- **Plan:** [`plan.md`](plan.md)
- **Constrained by:** RFC-0108 (D3, the readiness bridge and its argless mark, and D1 rules 1 to 10 as corrected by its errata), RFC-0105 (D3, through RFC-0108's errata exception, which ends the bridge's `workspace-status` input in the release where `work-loop` stops dispatching from `workspace-status`), RFC-0106 (D1 and D3, list-and-ask in place of first-ready selection), RFC-0055 (errata entries on an Accepted RFC), ADR-0074 (standard-library skill scripts)
- **Amends:** [intent-view-readiness-handover](../intent-view-readiness-handover/spec.md) — its Terms "Status input", "Base status", "Entry", "Finding", "Ready entry, active entry, blocked entry", "Checked lists" and "Reason set", and its criteria 0009, 0010, 0011, 0012, 0013, 0016, 0017, 0021, 0022, 0023, 0026, 0028, 0029, 0031, 0033, 0038, 0041, 0043, 0044, 0048, 0049 and 0050, each replaced by the criterion this spec names for it; its Never-do "Never run `workspace-status`, locate its script…", narrowed to name `dispatch.py`.
- **Brief:** brief:workspace-registry-retirement-delivery
- **Discovery:** none
- **Depends on:** spec:header-derived-dispatch
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

A maintainer who pipes `work-loop`'s read-only `dispatch.py --root <root>` output into `navigate-intents export --readiness -` opens an offline intent view whose "What can I work on next?" shows exactly dispatch's active, ready and blocked specs for the records the view loaded, and marks a spec only when an argless `work-loop` would start or resume that one spec, never when it would ask. The piped bytes stay untrusted under the hand-over spec's limits, and only node ids of loaded records, finding codes and allowlisted next-action text reach the page.

## What Changes

- **Input checks and the mark** — `packs/core/.apm/skills/navigate-intents/scripts/intent_readiness.py` checks `dispatch.py`'s output shape in place of `workspace-status status`'s, and takes the start mark from the checked `decision`.
- **Page wording** — the readiness lead line, sort key, start-tag notes, empty-list text, failure notices, the "Note from" label and the Key name `work-loop`'s dispatch — `scripts/view_src/readiness.js`, `labels.js` and `detail.js`.
- **Instructions and design note** — the pipe command and its description in the skill's SKILL.md and evals, `guides/core/how-to/navigate-intents.md`, and `packs/core/DESIGN.md`.
- **Tests** — the readiness suites under `packs/core/tests/skills/navigate-intents/` take `dispatch.py`-shaped inputs, with a corpus from the dispatch replay's case trees and a hand-built hostile input.
- **Governance and records** — § Errata on RFC-0105, RFC-0108 and RFC-0106; one slice-8 § Equivalence row; the inventory rows the `spec-registration-stop` spec leaves to this spec; an `Amended in part by:` line on the hand-over spec.
- **Unchanged:** `dispatch.py`; the export's read limit, deadline, payload keys and projection allowlist; every hand-over criterion this spec's `Amends:` header does not name; the pinned finding table, which `spec-registration-stop` keeps equal to the engine's.

## Durable Outputs

| Semantic role | Applicability | Destination | Owner | Expected evidence | Closeout condition |
| --- | --- | --- | --- | --- | --- |
| Interface compatibility: the bridge's input | Applicable: maintainers pipe a command into the export | `navigate-intents` SKILL.md § Export an offline view and § Safety controls; its `evals/eval_queries.json` | `navigate-intents` owner | AC-0019 and AC-0020 pass | Both name `dispatch.py --root` as the one piped command |
| User procedure | Applicable: the guide gives the pipe command | `guides/core/how-to/navigate-intents.md` § Show what is ready to work on, re-read whole | `core` maintainer | AC-0019 passes; the guide lints pass | The section gives the new command and the new failure reasons |
| Current architecture | Applicable: the export's one piped input changes | `packs/core/DESIGN.md`, the `navigate-intents` readiness paragraph | `core` maintainer | AC-0021 passes | It names `dispatch.py`'s output as the one piped input |
| Current product truth | Applicable: the hand-over spec is amended in part | `docs/specs/intent-view-readiness-handover/spec.md`'s header | `core` maintainer | AC-0025 passes | Its `Amended in part by:` line names this spec |
| Decision rationale | Applicable: RFC-0105's and RFC-0108's bridge exception and the first-ready mark | RFC-0105, RFC-0108, RFC-0106 § Errata; the retirement record's § Equivalence | eugenelim, Approver | AC-0022 to AC-0024 pass | Each carries owner-approved wording |
| Current product truth: registry consumers | Applicable: the bridge rows of the inventory | `docs/specs/workspace-retirement/inventory.toml` | Platform Core maintainer | AC-0026 passes | No bridge row carries owner 8 |
| Verification record | Applicable: browser, real-input and approval evidence | `docs/specs/readiness-bridge-dispatch-input/notes/verification-ledger.md` | Implementer | AC-0016 to AC-0018 and AC-0027 pass | The ledger holds each run and approval |
| Release history | Applicable: `core` content changes | the changelog fragment `spec-registration-stop` adds, at the same `core` version | Platform Core maintainer | That spec's criterion 0044 passes | The fragment names `--readiness` |
| Delivery membership | Applicable: the brief's coverage map | The brief's Spec map row | `author-delivery-brief` | `lint-brief-coverage.py` passes | The row exists |

## Agent Rules

### Always do

- Treat the readiness input as untrusted bytes, and keep only the projection the hand-over spec's criterion 0014 names.
- Decide the start mark from the checked `decision` only after AC-0004 has tied it to the checked lists.
- Put every piped string into the page only as text, through the view's existing element helpers, and keep the shipped content-security policy string with only its digests changing.
- Record every browser, real-input and approval result in this spec's ledger with the commit it ran against.

### Ask first

- The wording of each § Errata entry AC-0022 to AC-0024 list. The owner approves each before it is committed.
- Any change to the read limit, the deadline, the payload keys, the projected fields, or a hand-over criterion this spec does not name.

### Never do

- Never run `dispatch.py` or `workspace-status`, locate either script, start any process other than the export's shipped Git calls, or read `workspace.toml` or any file the readiness input names.
- Never let the readiness input add a node, a row for a record the view did not load, a link or a prompt, and never put piped text into a prompt or an `href`.
- Never change `dispatch.py`, the engine, or a frozen replay fixture.
- Never import from another skill, add a dependency outside the Python standard library or a JavaScript library, or add a module or script part.

## Testing Strategy

- **Input checks and the mark (AC-0001, AC-0002, AC-0003, AC-0004, AC-0005, AC-0006, AC-0007, AC-0008, AC-0009): TDD.** Each rule is a pure function of constructed bytes, so one planted input per rule reds before the check changes.
- **Real inputs (AC-0010, AC-0011, AC-0016): TDD with a corpus.** The outputs `dispatch.py` prints for the replay suite's case trees and for this repository are the corpus of real inputs, and the hand-built hostile input covers every field a real output can carry.
- **Page wording (AC-0012, AC-0013, AC-0014, AC-0015): scripted browser check.** `view_browser_checks.py` reads the rendered text, the only oracle for it; its full pass at the final code commit goes in the ledger.
- **Scale and the real export (AC-0017, AC-0018): goal-based.** Measurements recorded in the ledger.
- **Instructions, governance and records (AC-0019, AC-0020, AC-0021, AC-0022, AC-0023, AC-0024, AC-0025, AC-0026, AC-0027, AC-0028): goal-based.** A roster check over closed file-and-phrase lists, the inventory check, and a read of the ledger's approval rows.

## Acceptance Criteria

Terms used below. Each replaces the hand-over spec's term of the same role, and the hand-over criteria that carry over are read with these terms.

- **Readiness input** (replaces "Status input"). The bytes the export reads from standard input when `--readiness -` is given.
- **Base input** (replaces "Base status"). `{"schema_version": 1, "ready": [], "active": [], "blocked": [], "findings": [], "decision": {"action": "none", "path": null, "candidates": [], "findings": []}}`.
- **Item** (replaces "Entry"). An object in the input's `ready`, `active` or `blocked` list.
- **Finding.** An object in the input's top-level `findings`, an item's `findings`, or `decision.findings`.
- **Argless decision.** The decision `dispatch.py` derives with no selector from `active` and `ready`: `resume` with the one active path; `ask` with every active path when there are several; otherwise `start` with the one ready path; `ask` with every ready path when there are several; otherwise `none`. `path` is `null` and `candidates` empty except where named, and `findings` is empty.
- **Checked lists** (replaces the same term). The input's `active`, `ready` and `blocked` after every check of AC-0001 to AC-0006 and the hand-over spec's criteria 0006, 0007, 0008, 0046 and 0047 has passed, before any item is dropped.
- **Reason set** (replaces the same term). `not_requested`, `unreadable`, `timed_out`, `too_large`, `empty`, `not_json`, `wrong_schema`, `bad_workspace` and `page_too_big`.
- A carried hand-over criterion that names `canonical.ready`, `canonical.active`, `canonical.blocked` or `canonical.findings` is read as naming `ready`, `active`, `blocked` or `findings`; one that names an entry is read as naming an item.

**Input checks** (replace hand-over criteria 0009, 0010, 0011 and 0012)

- [ ] **AC-0001.** Each of these changes to a base input holding one ready, one active and one blocked item, with the argless decision, gives the reason `wrong_schema`: a top-level key absent or added; `schema_version` of `true`, `1.0`, `"1"` or `2`; `ready`, `active`, `blocked` or `findings` absent or not a list; an item that is not an object or whose keys are not exactly `path`, `slug`, `status` and `findings`; an item `path` or `slug` that is not a string; an item `status` that is neither a string nor `null`; an item `findings` that is not a list; an `active` item with a finding; one `path` in two of `ready`, `active` and `blocked`.
- [ ] **AC-0002.** Each of these finding changes, in any of the three places a finding sits, gives `wrong_schema`: a finding that is not an object or whose keys are not exactly `code`, `path`, `dispatchable` and `next_action`; a `code` whose whole string does not match `[a-z][a-z0-9_]{0,63}`, including a valid code followed by a space, `-`, an uppercase letter, a non-ASCII character or a line feed; a `path` that is neither a string nor `null`; a `dispatchable` that is not a boolean; a `next_action` that is not a string, is longer than 500 code points, or holds a code point from U+D800 to U+DFFF.
- [ ] **AC-0003.** Each of these gives `wrong_schema`: a `decision` that is not an object or whose keys are not exactly `action`, `path`, `candidates` and `findings`; an `action` outside `start`, `resume`, `ask`, `none` and `refuse`; a `path` that is neither a string nor `null`; a `candidates` that is not a list of strings; and the stdout of `workspace-status status` for the same repository.
- [ ] **AC-0004.** An input whose `decision.action` is not `refuse` and whose `decision` differs from the argless decision of its own `active` and `ready` lists in `action`, `path`, `candidates` or `findings` gives `wrong_schema`. The cases include a `start` naming a blocked item, a `start` naming a path in no list, a `resume` naming a ready item, an `ask` whose `candidates` omit one ready path, and the stdout of `dispatch.py --start <spec>` for a tree with two ready specs.
- [ ] **AC-0005.** An input that passes AC-0001 to AC-0004 gives `bad_workspace` when its `decision.action` is `refuse`, or when a finding at top level, in an item, or in `decision.findings` has the `code` `invalid_workspace`, `configuration_mismatch` or `unsafe_path`.
- [ ] **AC-0006.** The reason is that of the first failing check in this order: `unreadable`, `timed_out`, `too_large`, `empty`, `not_json`, `wrong_schema`, `bad_workspace`, `page_too_big`; `no_workspace` is not in `REASONS`, and an input carrying a repeated member name and a `schema_version` of `2` gives `not_json`.
- [ ] **AC-0007.** Given any readiness input that gives a reason other than `not_requested`, including every failing case of AC-0001 to AC-0006 and of the hand-over spec's criteria 0006, 0007, 0008, 0046, 0047 and 0048, on an export whose unchecked baseline fits the budget, the export returns `ok`, exits 0, writes its file, prints nothing to standard error, and its payload equals the payload of the same export without `--readiness` except for `readiness.reason` and `provenance.generated_at`; on an export whose unchecked baseline is one byte larger than the budget, it refuses with `export_too_large` as the hand-over spec's criterion 0050 states. (Replaces hand-over criteria 0013, 0048's case list, and 0050's case list.)

**Projection and the mark** (replace hand-over criteria 0016, 0017, 0021 and 0049)

- [ ] **AC-0008.** Given a checked input whose items' `slug` and `status`, whose findings' `path`, and whose `decision.findings`' `next_action` each hold its own distinct marker string, none of those marker strings appears in the HTML, apart from the `next_action` of a finding on a blocked item whose `path` is a loaded path. A path that occurs more than once in `blocked` appears once, with the codes of all its occurrences in input order and repeats removed.
- [ ] **AC-0009.** `readiness.start` holds exactly `rule`, `id`, `held` and `active_count`. `rule` is the checked `decision.action`; `active_count` is the length of `active`. For `start` and `resume`, `held` is `true` exactly when some finding at top level or in any item has a `path` equal to `decision.path`, and `id` is that path's node id when it is a loaded path and `held` is `false`, and `null` otherwise. For `ask` and `none`, `id` is `null` and `held` is `false`. Given checked lists whose `ready` holds two specs and whose `active` is empty, `rule` is `ask` and `id` is `null`.

**Real inputs** (replace hand-over criterion 0038)

- [ ] **AC-0010.** For every case tree `packs/core/tests/skills/work-loop/test_header_derived_dispatch_replay.py` builds, the stdout of `dispatch.py --root <tree>` gives a checked readiness member, or `bad_workspace` exactly when that run's decision is `refuse`; a checked member's `active`, `ready` and `blocked` ids are the loaded subset of `dispatch.py`'s lists, and the suite prints the accepted and refused counts.
- [ ] **AC-0011.** A hand-built input that passes every check and carries `</script><script>`, `<img src=x onerror=alert(1)>`, a `javascript:` value, `"><svg onload=alert(1)>`, a U+2028 line separator and bidirectional controls in every string member AC-0001 to AC-0003 admit gives an `ok` export with readiness checked and at least one `readiness.blocked` item, and none of those strings appears in the HTML outside the data block. The stdout of `dispatch.py --root` over a copy of the `mixed` corpus carrying the hostile `workspace.toml` fixture also gives an `ok` export in which none of that fixture's hostile strings appears in the HTML.

**Page wording** (replace hand-over criteria 0022, 0023, 0026, 0028, 0029, 0031 and 0033)

- [ ] **AC-0012.** When readiness is checked, "What can I work on next?" lists exactly the records of `readiness.active`, `readiness.ready` and `readiness.blocked` as the hand-over spec's criterion 0022 states, its lead line reads "Readiness from work-loop's dispatch, read when this snapshot was made.", and its sort key reads "Active, then ready, then blocked, in dispatch order". When it shows no row, the list area reads "work-loop's dispatch lists nothing active, ready or blocked in this export."
- [ ] **AC-0013.** When readiness is checked and `readiness.start.id` is `null`, a line below the list header reads the start phrase followed by: for `ask` with `active_count` above 0, " asks which of the <n> active items to resume, so none is marked.", with `<n>` the `active_count`; for `ask` with `active_count` 0, " asks which ready item to start, so none is marked."; for `resume` or `start` with `held` `true`, " may refuse the item it would resume, because work-loop's dispatch reports a finding about it, so none is marked." or " may refuse the item it would start, because work-loop's dispatch reports a finding about it, so none is marked."; for `resume` or `start` with `held` `false`, " would resume an item outside this export, so none is marked." or " would start an item outside this export, so none is marked."; and for `none`, " finds nothing to start or resume.".
- [ ] **AC-0014.** For a reason other than `not_requested`, a notice above the list reads "Readiness could not be checked: <sentence>. Run work-loop's dispatch to see what is ready.", with `<sentence>`: `unreadable` "standard input could not be read"; `timed_out` "nothing finished arriving within 60 seconds"; `too_large` "the piped input was larger than 4 MiB"; `empty` "nothing was piped in"; `not_json` "the piped input was not valid JSON"; `wrong_schema` "the piped input was not work-loop dispatch output this view reads"; `bad_workspace` "work-loop's dispatch reported a problem with workspace.toml itself"; `page_too_big` "the page would have been too large with it". Otherwise the list follows the hand-over spec's criterion 0029 for an unchecked page.
- [ ] **AC-0015.** A picked record's not-known workspace finding reads "Workspace finding <code>." followed by the label "Note from work-loop's dispatch:" and the `next_action` text, and otherwise as the hand-over spec's criterion 0031 states. While readiness is checked, the opened Key explains ● Active, ▶ Ready and ■ Blocked as readiness from work-loop's dispatch and "Workspace finding" as a finding work-loop's dispatch reported, and the hand-over spec's criterion 0033's closed label set holds "Note from work-loop's dispatch" in place of "Note from workspace-status". No rendered text outside a `next_action` holds "workspace-status".

**This repository** (replace hand-over criteria 0041, 0043 and 0044)

- [ ] **AC-0016.** Over this repository at the final code commit, the stdout of `dispatch.py --root .` gives a checked projection whose `active`, `ready` and `blocked` counts and `start` equal those a ledger-recorded script computes from the same output by this spec's terms, and the stdout of `workspace-status status` gives `wrong_schema`; the ledger records both outputs' SHA-256 values.
- [ ] **AC-0017.** The export spec's scale benchmark, re-run with this repository's `dispatch.py` output piped in, meets its thresholds at 1, 10, 25 and 50 times this repository's corpus, and the ledger records each result.
- [ ] **AC-0018.** An export of this repository at the final code commit with its `dispatch.py` output piped in, opened in headless Chromium, shows in "What can I work on next?" as many rows as `readiness` holds records, and in "What is broken?" every workspace broken entry; the ledger records both counts and the full `view_browser_checks.py` pass at that commit, with the count run and none skipped.

**Instructions**

Each phrase below is present in its file at the base, commit `dfa3fe067`, and each check reads the file with each run of whitespace as one space.

- [ ] **AC-0019.** `packs/core/.apm/skills/navigate-intents/SKILL.md` and `guides/core/how-to/navigate-intents.md` each pipe `scripts/dispatch.py' --root` into `--readiness -`, and neither holds `scripts/workspace_status.py' status`; the SKILL.md holds neither ``items in `workspace-status` order`` nor ``` `workspace-status` for queue order ```, and the guide does not hold ``the items `workspace-status` calls active, ready and blocked``.
- [ ] **AC-0020.** `packs/core/.apm/skills/navigate-intents/evals/eval_queries.json` does not hold `readiness from workspace-status`, and holds a query naming `work-loop`'s dispatch with `should_trigger` `true`.
- [ ] **AC-0021.** `packs/core/DESIGN.md` does not hold ``the output of `workspace-status`'s `status` subcommand``, and its readiness paragraph names `dispatch.py`.

**Governance and records**

- [ ] **AC-0022.** `docs/rfc/0105-artifact-derived-navigation-and-workspace-retirement.md` § Errata holds an entry dated on or after 2026-10-29 that links RFC-0106 and holds `D3`, `navigate-intents` and `dispatch.py`.
- [ ] **AC-0023.** `docs/rfc/0108-skill-html-view-standard.md` § Errata holds an entry dated on or after 2026-10-29 that links RFC-0106 and holds `D3`, `dispatch.py` and `argless`.
- [ ] **AC-0024.** `docs/rfc/0106-stop-registering-derivable-work.md` § Errata holds an entry dated on or after 2026-10-29 that holds `the readiness bridge's first-ready mark`, and `docs/specs/workspace-retirement/retirement-record.md` § Equivalence holds a slice-8 row whose Case is `the readiness bridge's first-ready mark`, Result `accepted removal`, Authority that entry, under the [`workspace-retirement`](../workspace-retirement/spec.md) spec's row rules.
- [ ] **AC-0025.** `docs/specs/intent-view-readiness-handover/spec.md`'s header holds an `Amended in part by:` entry naming this spec, and no other line of that file changes.
- [ ] **AC-0026.** In `docs/specs/workspace-retirement/inventory.toml`, every row the `spec-registration-stop` spec's criterion 0034 leaves to this spec, apart from this spec's own `docs/specs/readiness-bridge-dispatch-input/*` `contract` row at owner `8`, carries an owner other than `8`; and the inventory check passes.
- [ ] **AC-0027.** `docs/specs/readiness-bridge-dispatch-input/notes/verification-ledger.md` holds one row for each entry AC-0022 to AC-0024 list, naming its target file and the owner's approval with an ISO 8601 timestamp to the minute with its UTC offset, earlier than the author date (`git log --format=%aI`) of the commit that adds that text.
- [ ] **AC-0028.** The brief's Spec map holds `readiness-bridge-dispatch-input`, and `lint-brief-coverage.py` passes.

## Follow-ons

- The brief's slice 9 moves whatever engine rules `dispatch.py` still needs into `work-loop`; the bridge then reads a `work-loop`-only output, and the inventory's bridge rows leave the registry's consumers.

## Assumptions

none
