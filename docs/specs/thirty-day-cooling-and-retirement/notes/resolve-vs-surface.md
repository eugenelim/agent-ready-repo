# Resolve-vs-surface disposition record — Wave 5

Opened at PLAN, closed at DECIDE. Build-time record; deliberately not in
`plan.md`, which is hash-pinned from `approve-plan` onward.

## Surfaced to the human

| # | Question | Why it could not be resolved here | Disposition |
| --- | --- | --- | --- |
| S1 | Where does this repository's cooling record live? | RFC §6 permits four surface kinds and forbids `workspace.toml` from owning the record. No existing repository surface owns delivery-lifecycle state, so RFC §4 rung 6 — absence — requires a human to select or create the destination. | Resolved by owner 2026-08-27: `docs/specs/<slug>/lifecycle.json`, the RFC's "adjacent record", over a central `docs/lifecycle/` store. **Superseded by S2** — retained as the record of the decision that was made on the evidence available at the time. |
| S2 | Does the adjacent record survive the frozen-spec-directory rule? | Pre-EXECUTE adversarial review found `docs/CONVENTIONS.md` § "A spec directory freezes as a unit" makes a shipped spec directory immutable, and `tests/roster/test_direct_light_documentation_boundary.py` codifies that a sibling file inherits the spec's status. Only shipped work cools, so S1's destination would write repeatedly into a frozen directory. RFC §4 rejects rather than overrides a policy-violating destination. The alternative — amending CONVENTIONS — changes governance and needs its own guard, so it was the owner's call, not mine. | Resolved by owner 2026-08-27: move to `docs/lifecycle/<delivery-id>.json`. No CONVENTIONS amendment. |

## Resolved without surfacing

| # | Question | Resolution | Evidence |
| --- | --- | --- | --- |
| R1 | Extend `knowledge_store.py`'s record writer? | No. It owns reusable learning; its capture contract (`lesson`, `kind`, `competency_facets`, `semantic_gate`) cannot carry a locator/fingerprint/authority record that excludes rationale, and RFC §2 keeps project knowledge a separate role. | `packs/core/.apm/skills/project-knowledge/scripts/knowledge_store.py`; RFC-0096 §2, §6 |
| R2 | Add a `delivery-lifecycle` role to the resolver? | No. `runtime-coordination` already exists and fits cross-session coordination state. Adding a role edits a published contract and two SHA-pinned surfaces for no behavioural gain. | `surface_resolver.py:19-33`; `tests/roster/test_close_work_extraction_and_immediate_disposition.py:33,57` |
| R3 | Does the helper write, or only validate and return like `plan_pause`? | It writes. RFC §9 names Wave 5's impact as "helper and persistent schema", and AC14/AC24 are untestable if persistence is prose. | RFC-0096 §9 |
| R4 | Is a writer lock needed? | No. One id-keyed file per record plus a whole-record atomic `os.replace`: distinct records never share a file, and a same-record race is last-writer-wins, not a torn read. | `close_work.py` effect pattern; `knowledge_store._replace_atomic` |
| R5 | New module or extend `close_work.py`? | New sibling `cooling.py`. `close_work.py` is already ~2,400 lines, and Wave 4's roster test proves its clock-absence by parsing *its* imports and date-shaped tokens — a sibling keeps that guard both green and meaningful, while folding the engine in would force the guard to be weakened. | `packs/core/.apm/skills/close-work/scripts/close_work.py`; `tests/roster/test_close_work_extraction_and_immediate_disposition.py` |
| R8 | Where does the confined *writer* come from? | `file_safety.py` is read-only — it has no writer — and it is SHA-pinned in two roster tests. Rather than write a second confinement walk or widen a published helper, expose `close_work.py`'s existing `_open_validated_parent` under a public name and call it. One confinement implementation, no pinned digest moved. | `packages/agentbundle/agentbundle/catalogue_tooling/file_safety.py`; `close_work.py` |
| R9 | Does enrolment create its destination? | No. RFC §4 rung 6 makes absence an offer a human accepts, so `docs/lifecycle/` is created once in this PR and enrolment refuses when it is absent. That removes a directory-creation path and its confinement and authority surface entirely. | RFC-0096 §4 |
| R10 | Which vocabulary do persisted tokens use? | Both published ones: `disposition` from RFC §5's kebab-case intents, `post_closeout_result` from `close_work.POST_CLOSEOUT_RESULTS`. The draft's invented lowercase `retired` belonged to neither. | RFC-0096 §5; `close_work.py` |
| R6 | Does the pack version bump need the Wave 4 roster test rewritten? | No. Three literals move to `2.14.0`. Narrowing the assertion to `pack == plugin` would weaken a guard to avoid a one-line edit. | `tests/roster/test_wave4_durable_outputs_and_release.py:110-120` |
| R7 | Any new dependency? | No. `datetime`, `date`, `timedelta`, and `zoneinfo` are stdlib; none of `dateutil`, `pendulum`, `arrow`, `pytz` is installed. | repository dependency check 2026-08-27 |

## Closed at DECIDE

_Pending._
