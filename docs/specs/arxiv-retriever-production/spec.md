# Spec: arXiv retriever, production grade

- **Status:** Shipped <!-- Draft | Approved | Implementing | Shipped | Archived -->
- **Owner:** eugenelim
- **Plan:** [`plan.md`](plan.md)
- **Constrained by:** `packs/AGENTS.md`; `packs/desk-research/DESIGN.md`;
  `.apm/skills/desk-research/references/retriever-interface.md`
- **Brief:** none
- **Discovery:** none
- **Contract:** none
- **Shape:** service

## Outcome

`arxiv-retriever.py` answers three kinds of request against arXiv — find
candidate papers, fetch one exact record, and resolve a paper's external
linkage — and reports which query produced its results so a caller can judge
how loose the match was. It never returns a silently degraded result set: a
free-text query either yields a bounded answer or names the tier that produced
it. Results are relevance-ordered unless the caller selects another ordering,
and the active ordering is always reported.

## What Changes

- **Query composition replaces raw interpolation.** Free text is composed into
  arXiv's fielded query language through an ordered tier ladder instead of
  being pasted after `all:`. The selected tier is reported in the returned
  content.
- **Three modes, one script.** `search` (default) finds candidates, `get`
  fetches one record by identifier or URL, `enrich` resolves external linkage.
  Mode is selected by CLI flag; `retrieve(query)` continues to mean `search`.
- **A raw escape hatch.** `--search-query` passes an arXiv query through
  untouched, so a caller composing its own fielded or boolean syntax needs no
  change to this script.
- **Canonical metadata is carried, not discarded.** Each citation gains the
  arXiv identifier, version, submission and revision dates, categories,
  primary category, and — where arXiv publishes them — DOI and journal
  reference.
- **Rate-limit survival.** Requests are throttled and retried with backoff,
  and an unexpectedly empty result page is retried rather than reported as
  zero matches.
- **Bounded full text, opt-in.** `get --full-text` returns named sections up
  to a character budget and states what it dropped.
- **Both retrievers' role in the pack changes.** This script is the production
  retriever; `perplexity-retriever.py` carries the minimal-template role in
  `references/retriever-interface.md`.

## Durable Outputs

| Semantic role | Destination | Owner | Evidence | Closeout |
| --- | --- | --- | --- | --- |
| Interface contract | `.apm/skills/desk-research/references/retriever-interface.md` | pack maintainer | Mode table and extension-point rule present | Reviewed against shipped flags |
| User-facing promise | `.apm/skills/desk-research/SKILL.md` Retrievers section | pack maintainer | Describes three modes, not "API wrapper" | Matches shipped `--help` |
| Current product truth | `packs/desk-research/DESIGN.md` | pack maintainer | States that a retriever returns raw material and the calling skill owns synthesis | Gated by T8 `Done when:` |
| Release history | `pack.toml` + `.claude-plugin/plugin.json` | pack maintainer | Both manifests declare the version AC-0027 names | Both files equal |
| Reusable learning | pack eval harness | pack maintainer | Eval covers honest tier reporting | Harness updated |

Not applicable: operations runbook (no deployed service), decision rationale
(no ADR — this changes no repository convention), interface compatibility
record (the return schema is unchanged).

## Agent Rules

### Always do

- Send every request parameter through `urlencode`; never concatenate a
  caller-supplied string into a URL.
- Handle fetched bytes under `DESIGN.md` safety invariant 2.
- Return the schema `references/retriever-interface.md` defines, carrying added
  metadata inside a citation.
- State the arXiv submission date and the revision date as separate, labelled
  fields.

### Ask first

- Before adding a fourth mode, or an external host beyond the approved set:
  arXiv, alphaXiv, and HuggingFace Papers.
- Before raising the full-text character budget above its stated default.
- Before changing what `retrieve(query)` means for an existing caller.

### Never do

- Never add a runtime dependency; this script is Python standard library only.
  (Structural.)
- Never introduce a module boundary, package, or shared helper file for this
  script; it stays one self-contained file. (Structural.)
- Never emit synthesis; the `raw` shape in
  `references/retriever-interface.md` assigns it to the caller. Never emit a
  confidence rating, which `DESIGN.md` safety invariant 3 governs.
- Never present an arXiv revision date as a publication date.
- Never emit an external link whose existence has not been confirmed for the
  requested identifier.
- Never breach the shipped-content citation rule in `packs/AGENTS.md`.

## Testing Strategy

Across the 52 criteria: **44** are covered by a validated stub (VI-0001
through VI-0006, VI-0008, VI-0011, VI-0014 through VI-0018); **7** are
goal-based and take no stub (VI-0007, VI-0009, VI-0010, VI-0012); **1** is
manual (VI-0013). Every criterion appears in exactly one group.

- **VI-0001 — the tier ladder and what it reports (AC-0001, AC-0002, AC-0003,
  AC-0004, AC-0005):** TDD. The ladder is a pure function from caller text to
  an ordered candidate list, so the case table asserts the whole emitted
  sequence rather than the final choice — an ordering regression is invisible
  to a test that reads only the winner. Selection is driven from canned totals,
  so no request is made.
- **VI-0002 — identifier and URL resolution (AC-0006, AC-0007):** TDD. String
  classification over a closed set of identifier forms. The near-miss case
  drives the refusal path, because a fallthrough to text search is the defect
  the criterion exists to prevent.
- **VI-0003 — canonical metadata on each citation (AC-0008, AC-0009, AC-0010,
  AC-0011, AC-0012, AC-0013):** TDD. Two canned feeds — one record publishing
  DOI and journal reference, one publishing neither — drive one mapper, so
  omission and presence are the same code path under test.
- **VI-0004 — request discipline (AC-0014, AC-0015, AC-0016, AC-0017,
  AC-0018):** TDD against an injected clock and the network seam, so timing and
  retry are decidable without network access.
- **VI-0005 — bounded full text (AC-0019, AC-0020, AC-0021, AC-0022):** TDD
  over saved documents. Section count is asserted against an oracle counted
  from the same document, not a fixed expected number, so the check survives a
  document with a different section count.
- **VI-0006 — enrichment emits only what it confirmed (AC-0023, AC-0024):**
  TDD against an injected presence check, which makes the emit-or-omit rule
  decidable without reaching an external host.
- **VI-0007 — stream encoding (AC-0025):** goal-based check. A grep for both
  reconfigure calls ahead of the first write.
- **VI-0008 — stdout carries the result alone (AC-0026):** TDD. Captured
  streams separate the result from diagnostics, which a grep cannot do.
- **VI-0009 — the pack release surface (AC-0027, AC-0033):** goal-based check.
  Compare the two declared version strings, then re-run the catalogue self-host
  for an empty diff.
- **VI-0010 — shipped prose (AC-0028, AC-0029, AC-0030):** goal-based check.
  Grep the shipped surfaces for internal paths, and compare the documented
  flag set against `--help`.
- **VI-0011 — the suite can observe the paths it claims (AC-0031, AC-0032):**
  TDD. A test that raises from the network seam fails under the current
  wholesale mock, which is what proves the boundary was actually narrowed
  rather than merely renamed.
- **VI-0012 — the eval harness (AC-0034):** goal-based check. The harness
  carries the tier-honesty assertion.
- **VI-0014 — caller-composed query controls (AC-0036, AC-0037, AC-0038,
  AC-0039):** TDD. Each control is asserted on the built request rather than on
  returned results, so the check does not depend on what arXiv currently holds.
  The passthrough case asserts byte equality, which is the only form that
  catches a well-meaning normalisation.
- **VI-0015 — retrieved content stays inert (AC-0040, AC-0051):** TDD.
  Hostile-content fixtures drive search, get, and full-text rendering, and one
  case proves an enrichment response body never reaches the mapping. AC-0040
  cites the pack invariant rather than restating it, so this group tests
  conformance, not a second copy of the rule.
- **VI-0016 — connection confinement (AC-0041, AC-0042):** TDD against a fake
  opener that reports a redirect target and a resolved address, so both
  refusals are decidable without network access.
- **VI-0017 — safe deserialization and output validation (AC-0043, AC-0050,
  AC-0044, AC-0045):** TDD. Each case has its own failure mode and remedy, so
  each is its own case, and the two document kinds assert different outcomes: a
  doctype-bearing XML feed drives a refusal, while an HTML document carrying
  script and a subresource reference is accepted and asserted inert, since
  refusing ordinary HTML would reject real arXiv renders. A structurally wrong
  document and one carrying a malformed identifier or an off-host URL each
  drive a refusal.
- **VI-0018 — resource bounds, fail-closed (AC-0046, AC-0047, AC-0052,
  AC-0048, AC-0049):** TDD against an injected clock and a body that reports
  more bytes than the limit. The elapsed bound is driven by a body that
  delivers bytes inside every socket window, which a socket timeout alone
  would not catch. The cumulative case spans several distinct requests in one
  invocation, not several retries of one. Each limit is asserted at its own
  firing input, and the fail-closed check captures stdout to prove nothing
  partial escapes.
- **VI-0013 — the live path (AC-0035):** visual / manual QA. No unit seam
  observes arXiv's real behaviour, so the shipped script is invoked against the
  live API and its output recorded.

## Acceptance Criteria

- [x] **AC-0001.** Given free text containing a colon, a bare boolean word, or
  more than one term, the composed `search_query` contains no unquoted
  occurrence of that text.
- [x] **AC-0002.** Each tier after the first is strictly wider than the tier
  before it, and the final tier returns its result whatever the match count, so
  no query returns an empty set for want of a wider tier.
- [x] **AC-0003.** Tier 1's phrase is the caller's text with no token removed,
  so a query whose exact wording is a paper title matches that title.
- [x] **AC-0004.** Returned content names the tier that produced the results
  and the total match count arXiv reported.
- [x] **AC-0005.** A tier is accepted when arXiv's reported total for it is at
  least 1 and at most 2,000; the first tier meeting that bound wins, and when
  no tier meets it the final tier's result is returned and reported as
  terminal.
- [x] **AC-0006.** A modern identifier, a legacy identifier carrying a category
  prefix, either with a version suffix, and an `arxiv.org/abs/` or
  `arxiv.org/pdf/` URL each resolve through arXiv's identifier parameter and
  return exactly the named record.
- [x] **AC-0007.** Input resembling an identifier but not well-formed produces
  a non-zero exit and a diagnostic, rather than falling back to a text search.
- [x] **AC-0008.** Each citation's `url` is the version-free abstract URL, and
  the retrieved version is a separate citation field.
- [x] **AC-0009.** Each citation carries the submission date and the revision
  date under separate labelled keys, and neither value is used as the other.
- [x] **AC-0010.** DOI and journal reference appear as citation fields when
  arXiv publishes them for that record, and are omitted keys when it does not.
- [x] **AC-0011.** Each citation includes the arXiv identifier, title, authors,
  submission date, revision date, categories, primary category, abstract URL,
  and PDF URL.
- [x] **AC-0012.** Every mode's returned mapping conforms to the return
  schema in `references/retriever-interface.md` with `shape` set to `raw`, and
  `citations` is non-empty whenever a record was found.
- [x] **AC-0013.** Calling `retrieve` with a single string argument performs a
  `search` and satisfies AC-0012.
- [x] **AC-0014.** Consecutive outbound requests are separated by at least 3.0
  seconds, measured from the completion of the previous request, enforced in
  the shared request path so every mode inherits it.
- [x] **AC-0015.** An HTTP 429 or 5xx response is retried up to 3 times with a
  strictly increasing delay, and the delay before the first retry is at least
  the throttle interval.
- [x] **AC-0016.** A response parsing to zero entries while arXiv reports a
  non-zero total is retried under AC-0015 rather than returned as zero matches.
- [x] **AC-0017.** When retries are exhausted the script exits non-zero with a
  diagnostic naming the status and the attempt count, and writes no partial
  result to standard output.
- [x] **AC-0018.** Every outbound URL is built by encoding a parameter mapping,
  so caller text containing `&` or `=` cannot introduce or overwrite a request
  parameter.
- [x] **AC-0019.** No mode fetches full text unless the caller requests it.
- [x] **AC-0020.** Requested full text returns only the named sections,
  defaulting to abstract, introduction, and conclusion, selected by section
  name rather than by position.
- [x] **AC-0021.** Returned full text is at most 12,000 characters, measured
  across the concatenated selected sections, and the output names the count of
  sections omitted and that the budget caused the truncation.
- [x] **AC-0022.** The number of sections the extractor finds equals the number
  of section elements present in the fetched document.
- [x] **AC-0023.** Each link `enrich` emits is confirmed present for the
  requested identifier by a check that distinguishes a real identifier from an
  absent one; a host returning the same response for both is not used.
- [x] **AC-0024.** `enrich` output carries no synthesis, as the `raw` shape in
  `references/retriever-interface.md` requires, and no confidence rating.
- [x] **AC-0025.** The script satisfies the stream-encoding rule in
  `packs/AGENTS.md` for standard output and for standard error, before its
  first write to either.
- [x] **AC-0026.** Standard output carries the result mapping alone;
  diagnostics, throttle notices, and retry notices go to standard error.
- [x] **AC-0027.** `pack.toml` and `.claude-plugin/plugin.json` both declare
  `1.1.9`, the patch increment `packs/AGENTS.md` requires for changed pack
  content.
- [x] **AC-0028.** The script, `retriever-interface.md`, and the SKILL.md
  Retrievers section each satisfy the shipped-content citation rule in
  `packs/AGENTS.md`.
- [x] **AC-0029.** `retriever-interface.md` documents the three modes and names
  `perplexity-retriever.py` as the minimal template.
- [x] **AC-0030.** `retriever-interface.md` states that added metadata belongs
  inside a citation, because the three top-level keys are fixed.
- [x] **AC-0031.** The conformance test loads each retriever under a module
  name including the pack and skill, so two skills shipping the same filename
  cannot collide.
- [x] **AC-0032.** The conformance test patches the network boundary narrowly
  enough that a test can drive the throttle and retry paths.
- [x] **AC-0033.** Re-running the catalogue self-host produces no diff.
- [x] **AC-0034.** The desk-research eval harness asserts that a degraded or
  widened match is reported as such rather than presented as an exact match.
- [x] **AC-0036.** A query supplied through the raw passthrough reaches
  arXiv's `search_query` parameter byte-identical and bypasses the tier ladder.
- [x] **AC-0037.** Title, author, abstract, and category flags each compose
  into their arXiv field prefix, and supplying more than one joins them with a
  boolean conjunction.
- [x] **AC-0038.** Ordering is relevance when the caller selects none, is the
  caller's choice among arXiv's submission-date and last-updated orderings when
  they select one, and is named in the returned content either way.
- [x] **AC-0039.** A caller-supplied date window restricts results to
  submissions inside it, expressed as an arXiv submitted-date range.
- [x] **AC-0040.** Every retrieved field stays inert data, as `DESIGN.md`
  safety invariant 2 requires: given a fixture whose title, abstract, section
  body, or enrichment payload carries instruction-like text, no mode follows
  it, acts on it, or promotes it out of the returned data.
- [x] **AC-0041.** Every request and every redirect it follows uses HTTPS on
  port 443 and matches, after case and trailing-dot normalisation, one of
  exactly these hosts: `export.arxiv.org`, `arxiv.org`, `www.alphaxiv.org`,
  `huggingface.co`. Matching is whole-host equality, not a suffix or subdomain
  test, and a redirect failing it is refused before the response body is read.
- [x] **AC-0042.** Before the initial request and before every redirect, each
  address the target host resolves to is checked, and the request is refused
  when any is loopback, link-local, unique-local, private, unspecified, or
  reserved, or is the metadata address `169.254.169.254`. Metadata hostnames
  are refused by AC-0041's host set, not here, because resolution yields
  addresses and a hostname is not an address class. This is a
  preflight check: it resolves and then connects, so it does not close DNS
  rebinding: `urllib` connects by hostname and offers no way to pin the
  connection to an address that passed the check. Pinning would mean replacing
  `urllib` with a hand-built HTTPS client, which this retriever does not carry,
  so the limit is accepted and the criterion claims only the preflight
  refusal.
- [x] **AC-0043.** The XML parser refuses a response carrying a doctype
  declaration or an entity declaration, and resolves no external reference.
- [x] **AC-0050.** The HTML parser executes no script, style, or event-handler
  content and fetches no subresource. A doctype is ordinary in HTML and is not
  a refusal condition, so this criterion names execution and fetching instead.
- [x] **AC-0044.** A response outside the expected Atom feed or LaTeXML
  section structure is refused rather than partially mapped.
- [x] **AC-0045.** Before entering the return mapping, an extracted identifier
  matches the modern form `YYMM.NNNN` or `YYMM.NNNNN` — four digits for
  identifiers issued before 2015 and five from 2015 onward, both still valid —
  or the legacy form `archive/YYMMNNN` where `archive` is a lowercase name
  optionally carrying a `.SubjectClass` suffix, as in `quant-ph/0201082` and
  `math.GT/0309136`; each accepts an optional `vN` suffix. An extracted
  URL is HTTPS on port 443, carries no userinfo, has a whole-host match in
  AC-0041's set, and has a path beginning `/abs/`, `/pdf/`, or `/html/`. A
  value failing any part is refused rather than carried.
- [x] **AC-0046.** Each attempt is bounded by 30 seconds of total elapsed time
  from the start of the attempt through its final read. The body is read in
  chunks and the socket is re-armed before each read to whatever of the 30
  seconds remains, so a response delivering some bytes inside every socket
  window is cut off at the deadline rather than merely detected after it. The
  origin is the 30-second timeout the retriever already applies, and the bound
  is enforced in the shared request path so every mode inherits it.
- [x] **AC-0047.** One response is read to at most 8 MiB plus one probe byte
  and retains at most 8 MiB, so a body at the limit is accepted while a body
  one byte over is detected without buffering the rest. 8 MiB is roughly seven
  times the largest body measured against arXiv.
- [x] **AC-0052.** The bytes retained across one `retrieve` invocation total at
  most 32 MiB, counted over every request it makes — each candidate tier, each
  enrichment probe, each redirect, each full-text fetch, and every retry — not
  over one retried request. 32 MiB is AC-0047's limit across the 4 attempts
  AC-0015 permits.
- [x] **AC-0048.** A response yields at most 50 citations and each mode renders
  at most 40,000 characters. For full text the 12,000-character budget in
  AC-0021 fires first, because it is measured over the selected sections before
  rendering; the 40,000-character limit fires first for a broad search, whose
  citation abstracts reach it before any single section budget applies.
- [x] **AC-0049.** When any limit in AC-0046, AC-0047, AC-0052, or AC-0048 is
  exceeded,
  the script exits non-zero with a diagnostic naming the limit and writes no
  partial result to standard output.
- [x] **AC-0051.** Enrichment returns only link URLs it confirmed; no part of
  an enrichment response body enters the returned mapping.
- [x] **AC-0035.** A recorded invocation of the shipped script against arXiv
  covers all three modes, and its observed output is captured.

## Follow-ons

- `perplexity-retriever.py` does not reconfigure its streams to UTF-8. Owner:
  pack maintainer; separate change, since this spec's frontier is the arXiv
  retriever.
- `docs/specs/research-pack/{spec,plan}.md` cite the pre-rename path
  `packs/research/...`. Owner: pack maintainer; pre-existing drift in a frozen
  spec.

## Assumptions

- Product: arXiv keeps serving LaTeXML renders at its HTML path for older
  papers. Falsehood would remove the full-text route for pre-2024 papers and
  reduce AC-0020 to the abstract. No criterion or task in this release reads
  the LaTeX source archive, so nothing here extracts an archive; adopting that
  route later needs its own confinement criteria and is the pack maintainer's
  decision.
