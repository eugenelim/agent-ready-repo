# Rendered-surface review — guide title clarity (AC11)

Performed 2026-08-17 against the combined emitted site, served from `build/`,
built from base commit `caaabe12` with this change applied. The pre-change route
inventory in [`route-baseline.txt`](route-baseline.txt) was captured the same
day from a build of `caaabe12` WITHOUT this change.

## Runtime

System Chrome via Playwright's `channel="chrome"`. Playwright 1.62.1 expects the
bundled build `chromium_headless_shell-1228`; the cache holds `1234`, so the
bundled launch fails with `Executable doesn't exist`. The system channel is a real
browser, not a stub — recorded because "browser evidence" is only evidence if a
browser actually launched, and this repo's own register carries a case where a
sandboxed `HOME` produced passing rows with no browser at all. `HOME` was left
intact here.

## Matrix

Four routes × five widths (360, 375, 390, 414, 1440) × both docs themes = **40
cases**, per the brief's approved viewport and theme set.

## Result against the criterion

The criterion is coherence with the OWNING surface's direction —
`docs-site-design-refresh/creative-direction.md`'s "Instrument-grade clarity" —
and the tech-site principle "Lead with the user's job; reveal the system second."
Not the marketing site's "Precision authority": these pages render only on
`docs-site/`.

| Observation | Result |
| --- | --- |
| Emitted `<h1>` equals the approved string, all 4 routes × 5 widths × 2 themes | 40/40 |
| `<title>` carries the approved string | 4/4 |
| `<h1>` visually truncated at any width | **none** |
| Sidebar ITEM labels show the approved string, all 4 items × 1440 and 360 | 4/4 |
| Retired title strings present as a sidebar ITEM label | none |
| Sidebar GROUP label for the `iac-terraform` pack | `IaC (Terraform)` — unchanged, see below |

The first draft of this table recorded "yes, all three" and omitted
`iac-terraform` — the one item whose surroundings actually differ. Re-observed
at 1440 and 360 in both themes: all four item labels carry the approved string.

The pack's sidebar GROUP heading still reads `IaC (Terraform)`, so the
`iac-terraform` page renders as `IaC (Terraform) › Terraform and OpenTofu
guides`. That is intended here and not a defect of this change. The group label
is a distinct string from the four the brief freezes; it originates in
`packs/iac-terraform/pack.toml`'s `display_name` (mirrored to `site.toml` and
`docs-site/src/sidebar-config.json`), which is pack identity rendered in the
marketing catalogue and pack cards as well as this sidebar. Renaming it is a
judgment-led naming decision across surfaces this spec does not own, so it is
deferred to `[backlog].open` as `iac-terraform-group-label-alignment` rather
than made silently.

Each of the four titles names the reader's job in the imperative
(`Write a page or screen contract`, `Run a frontend audit`,
`Scaffold a component from a screen brief`) or the tools by name
(`Terraform and OpenTofu guides`), which is what "lead with the user's job"
asks for. None is truncated at 360 CSS px, the narrowest approved width.

**No issue attributable to this change was observed.** AC11 asks whether the
review finds a Major issue; it found no issue at all against that criterion, and
an empty finding set contains no Major member, so AC11 closes on the evidence
without this note assigning a severity to anything. No severity is generated
here — the brief bars that — and a human reviewer retains the
Blocker/Major/Minor/Note call on anything they judge differently, including the
deferred group-label mismatch above.

## Pre-existing defect observed, NOT caused by this change

Two of the four routes carry document-level horizontal overflow at the four
narrow widths, in both themes:

| Route | 360 | 375 | 390 | 414 |
| --- | ---: | ---: | ---: | ---: |
| `run-an-audit` | 281px | 266px | 251px | 227px |
| `scaffold-a-component` | 367px | 352px | 337px | 313px |

Measured before and after, and it is **byte-identical**: with the change stashed
and the docs site rebuilt, `run-an-audit` still reports 281px at 360 and 227px at
414, and `scaffold-a-component` still reports 367px and 313px — with the old
titles rendered. This change alters the overflow by exactly zero.

It is also not specific to the touched pages. Untouched guides overflow the same
way at 360 px (`governance-extras/how-to/new-adr` 219px,
`core/how-to/start-a-project` 251px), while a page this change DID touch
(`page-screen-contract`) reports 0px. The correlation is with page content — wide
tables and code blocks — not with titles.

Overflow is owned by `docs/specs/site-browser-quality-gate/spec.md`, whose AC4
sets the ≤1px document-level ceiling across the approved matrix. That spec is
explicitly out of scope for this run, so the measurements above are recorded as
evidence for it rather than acted on here. They are not a finding against this
change.
