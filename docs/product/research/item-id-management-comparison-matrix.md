# Identifier management for acceptance criteria and verification items

> Discipline: applied (practitioner-pattern survey)

- **Commissioned:** 2026-09-10
- **Decision:** what identifier scheme should an acceptance criterion, and a
  per-test verification item, carry in a Markdown spec held in git?
- **Occasion:** criteria numbered positionally (AC1…AC23). Three insertions
  caused three renumberings, and stale cross-references were raised as defects
  in review rounds 2, 9 and 15.
- **Why this is not settled by our own corpus:** 135 of 241 shipped specs here
  label criteria `**ACn —**`. That measures what is common in one repository,
  not what is correct, and it was wrong to present it as evidence for a choice.

## The pick

**Adopt opaque, append-only identifiers for acceptance criteria, assigned once
and never renumbered or reused, with a committed retired list. Give verification
items their own independent identifiers — not identifiers derived from the task
or the criterion they serve.** Forward-only: new specs adopt it, existing ones
are not rewritten, exactly as the ADR numbering convention was introduced.

Confidence `[high]` on identifier *stability*, which is where every source
converges. `[moderate]` on the *opaque flat* format specifically, because no
standard mandates a format — only that the scheme be stable. `[moderate]` on
independent verification IDs, from three tools agreeing and one standard
requiring per-test IDs in a regulated context that is ours only by analogy.

## Why stability, and what breaks without it

**ISO/IEC/IEEE 29148 clause 5.2.8.1** states the rule directly. The primary text
is paywalled; secondary sources reproduce it consistently:

> "Each requirement should be uniquely identified… Once assigned, the
> identification has to be unique — it is **never changed** (even if the
> identified requirement changes) nor is it **reused** (even if the identified
> requirement is deleted)."

Two points are easy to miss. The verb for *assigning* an identifier is "should",
so a conformant project may have none — but any identifier that exists must be
stable. And the same clause makes hierarchy optional: "Identification can
reflect linkages and relationships, if needed, or they can be separate from
identification." **The standard governs stability, not format.** `[moderate]` —
consistent secondary reproduction of a paywalled clause.

Two independent requirements-tool vendors name our exact failure in nearly the
same words. Sparx: positional numbers are reassigned on reorder, "which makes
this mechanism **unsuitable if immutable numbers are needed**." 3SL: "The
hierarchical number of an item is **NOT** the *Identity*." `[high]` — two
independent vendors, one of which sells a competing product.

## The decisive case: a tool that ships both and had to choose

IBM DOORS gives every object **two** numbers:

| | Absolute Number | Object / heading number |
| --- | --- | --- |
| Assigned | at creation, monotonic | derived from tree position |
| On insert or move | unchanged | **renumbers** |
| On delete | gap left, **never reused** | closes up |
| **Links resolve against** | **this one** | not this one |

IBM's own community answer on reusing a purged object's number: *"No there is no
way to re-use absolute number of purged/discarded objects. Doing that would lead
to duplicate absolute number and that is something we really want to avoid."*

This is the strongest evidence available, because it is not an opinion about
which scheme is better — it is a product that implements **both** and had to
decide which one cross-references key on. It chose the stable one and leaves
permanent gaps in the sequence rather than reuse a number. `[high]`

StrictDoc is the text-native analogue of the same split: a human-readable `UID`
plus an auto-generated hex `MID` that survives UID renames and node relocation.
`[moderate]`

## Scheme comparison

| Scheme | Survives insert/reorder | Survives rename | Reuse prevented | Mechanically checkable | Cost |
| --- | --- | --- | --- | --- | --- |
| **Positional** (`AC7`, `3.2.1`) — ours today | **no** | n/a | n/a | no | none |
| Generated slug / anchor from text | yes | **no** | n/a | partly (`markdownlint` MD051, same file only) | none |
| Semantic (`AUTH-LOGIN-03`) | yes | **no** — scope moves make the prefix wrong, and renaming is delete-plus-reissue | no | no | low |
| **Opaque append-only** (`AC-0042`) | **yes** | **yes** | only with a retired list | yes, with a lint | low |
| Opaque + version (`req~name~1`, OpenFastTrace) | yes | yes | yes | yes, tool ships it | medium |
| Per-file items (Doorstop, StrictDoc) | yes | yes | partly | yes, tool ships it | **high — abandons single-file `spec.md`** |

Rejected, with reasons: **semantic IDs**, because the argument against them is
the same one W3C makes for opaque URIs — when the name changes the identifier
should not, and a semantic prefix goes stale the moment scope moves.
**Per-file items**, because adopting Doorstop or StrictDoc means every criterion
becomes a file and the repository's whole spec shape changes; the cost is not
proportionate to the defect. **Version-in-ID**, because its benefit — a version
bump deliberately invalidating downstream coverage so it must be re-confirmed —
is real but presumes a coverage-tag ecosystem we do not have.

## Verification items: their own identifiers, not derived ones

The proposal on the table was `T1.1` — a test item numbered inside its task.
**Three independent test-management tools all reject derivation:**

| Tool | Test identifier | Derived from the requirement? |
| --- | --- | --- |
| TestRail | `C4521` | no — link is a separate References field |
| Xray | the Jira issue key | no — link is a Jira issue link |
| Zephyr Scale | `PROJ-T1` | no — link via Jira issue link |

The synthesis across them: test IDs are independent, "never of the form
`REQ-12.T3`", and the link is a separate record so neither side's identifier is
derived from the other. `[high]` — three vendors, independent products.

**Why that matters for `T1.1` specifically.** It derives from the *task*, and
tasks get re-cut — indeed the design-versus-task rule we just adopted says design
facts must survive a re-cut. A derived identifier inherits its parent's
instability, so `T1.1` reintroduces the defect one level down.

That the item deserves *an* identifier is well supported: **IEC 62304 requires
each test case to carry its own unique ID**, and a 2023 granular-traceability
paper argues coarse requirement-level links are insufficient when a requirement
has several independently verifiable conditions — which is precisely a criterion
with several assertions. `[moderate]` — both are safety-critical-context sources
and apply to an internal spec document only by analogy.

## What no existing tool will do for us

**No off-the-shelf tool enforces the full property set for inline-Markdown
criteria lists.** `[high]` — searched across four retrievers.

| Property | Best available | Gap |
| --- | --- | --- |
| Every item has an ID | Sphinx-Needs `needs_id_regex` fails the build | format only, and its `:delete:` option permits duplicates |
| IDs unique | Doorstop (filesystem), OpenFastTrace (duplicate report) | both need their own file format |
| **Not reused after deletion** | **nothing** | Doorstop explicitly does not track it; needs a committed retired list |
| Cross-references resolve | `markdownlint` MD051, Doorstop `check`, OFT | MD051 is same-file only |

So the retired list is the one piece we must build. It is also small: a committed
list of retired identifiers, and a check that no live item claims one.

**Suspect links are the pattern we are not adopting yet, and should know about.**
DOORS, Jama and Polarion all mark downstream links *suspect* on a content change
to the source rather than letting them break silently, and Doorstop does the same
with a SHA-256 fingerprint per item. That is the mechanism that answers "this
criterion changed — is its verification still valid?", which stable IDs alone do
not. Recorded as the obvious next step, not proposed here. `[high]`

## Known unknowns

- **Known-unknown:** the exact normative wording of ISO/IEC/IEEE 29148 clause
  5.2.8.1 and of INCOSE GtWR attribute A15. Both paywalled; the INCOSE summary
  sheet returned HTTP 403. Would be closed by a licensed copy.
- **Known-unknown:** whether Polarion and Codebeamer reuse an identifier after a
  hard delete. Not stated in public documentation. Would be closed by vendor
  support documentation behind their authentication walls.
- **Unknowable, as posed:** whether opaque identifiers reduce defect or
  staleness rates relative to positional ones. **No empirical study compares
  them.** The consensus is practitioner- and standards-derived, not data-derived,
  and this artifact should not be read as claiming otherwise.
- **Unknowable:** how often renumbering actually breaks traceability in the
  field. No datable, attributed post-mortem was found. Safety-critical project
  post-mortems are rarely published, so the population is not observable.

## Citations

**Standards.** [ISO/IEC/IEEE 29148:2018](https://www.iso.org/standard/72089.html) (paywalled) · [ISO 29148 explained](https://www.modernrequirements.com/blogs/iso-29148-explained/) · [INCOSE GtWR via Visure](https://visuresolutions.com/alm-guide/incose-guide-to-writing-requirements/) · [Traceability in compliance projects](https://www.trace.space/blog/traceability-in-compliance-projects) · [Granular traceability between requirements and test cases](https://dl.acm.org/doi/10.1007/978-3-031-39764-6_14)

**Tools.** [IBM: reclaiming purged object IDs](https://community.ibm.com/community/user/discussion/is-there-any-way-to-reclaim-purgeddiscarded-object-ids) · [IBM: about DOORS absolute numbers](https://www.ibm.com/support/pages/about-doors-absolute-numbers) · [3SL: numbering item hierarchies](https://www.threesl.com/blog/numbering-item-hierarchies/) · [Sparx: requirements naming and numbering](https://sparxsystems.com/enterprise_architect_user_guide/17.1/modeling_domains/requirements_naming_and_numbering.html) · [Jama: change Global ID](https://help.jamasoftware.com/ah/en/administration/organization-administrator/managing-content/change-global-id.html) · [Jama: suspect tracking](https://www.jamasoftware.com/blog/the-importance-of-suspect-tracking-in-requirements-management/) · [Polarion: deleting work items](https://blogs.sw.siemens.com/polarion/10-tips-for-polarion-livedocs-6-deleting-work-items/) · [TestRail: cases](https://support.testrail.com/hc/en-us/articles/7077292642580-Cases) · [Xray test management](https://www.getxray.app/blog/xray-test-management-for-jira) · [Zephyr Scale test case IDs](https://community.atlassian.com/forums/App-Central-questions/How-to-get-linked-Zephyr-scale-cloud-test-case-ID-of-a-JIRA/qaq-p/2910421)

**Text-native.** [Doorstop item reference](https://github.com/doorstop-dev/doorstop/blob/develop/docs/reference/item.md) · [Doorstop validation](https://doorstop.readthedocs.io/en/latest/cli/validation.html) · [StrictDoc user guide](https://strictdoc.readthedocs.io/en/stable/stable/docs/strictdoc_01_user_guide.html) · [OpenFastTrace](https://github.com/itsallcode/openfasttrace) · [Sphinx-Needs directives](https://sphinx-needs.readthedocs.io/en/stable/directives/need.html) · [markdownlint MD051](https://github.com/DavidAnson/markdownlint/blob/main/doc/md051.md)

**Conventions.** [Documenting architecture decisions (Nygard)](https://cognitect.com/blog/2011/11/15/documenting-architecture-decisions) · [W3C fragment identifier best practices](https://www.w3.org/TR/fragid-best-practices/) · [Spec Kit spec template](https://github.com/github/spec-kit/blob/main/templates/spec-template.md) · [Kiro specs](https://kiro.dev/docs/specs/) · [OpenSpec concepts](https://github.com/Fission-AI/OpenSpec/blob/main/docs/concepts.md)
