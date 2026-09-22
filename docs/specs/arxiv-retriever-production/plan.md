# Plan: arXiv retriever, production grade

- **Spec:** [`spec.md`](spec.md)
- **Status:** Approved <!-- Drafting | Approved | Executing | Done -->
- **Repository anchors:** `packs/AGENTS.md` (runtime export boundary, version
  bump rule, stream encoding, shipped-content citation rule, pack test module
  naming); `packs/desk-research/DESIGN.md` §5 and §8 (context discipline,
  untrusted content, GRADE ownership);
  `guides/_shared/reference/catalogue-authoring-standards.md` (skill authoring
  and the pack test loader recipe). Analogous implementations:
  `packs/desk-research/.apm/skills/desk-research/scripts/perplexity-retriever.py`
  (sibling retriever, narrow-boundary mock shape) and
  `packs/core/.apm/skills/new-spec/scripts/explore-grounding.py:717` (stream
  reconfigure form). Their test is
  `packs/desk-research/tests/skills/desk-research/test_research_retrievers_conformance.py`.
  Named uncertainty: arXiv's LaTeXML markup is an external contract with no
  published stability guarantee, so section extraction is pinned to an oracle
  counted from the same document rather than to fixed class names alone.

## Assumptions

**Files touched.**
`packs/desk-research/.apm/skills/desk-research/scripts/arxiv-retriever.py`
(rewritten); `.../references/retriever-interface.md`; `.../SKILL.md`
(Retrievers section); `packs/desk-research/DESIGN.md`;
`packs/desk-research/tests/skills/desk-research/test_research_retrievers_conformance.py`;
`packs/desk-research/pack.toml`;
`packs/desk-research/.claude-plugin/plugin.json`;
`.../skills/desk-research/evals/evals.json`; plus the regenerated adapter
projection.

**What demonstrates done.** Each task's own `Tests:` and `Done when:` fields,
which are the completion contract; this entry does not restate them, because a
second inventory drifts from the first.

**Not changing.** `perplexity-retriever.py` behaviour; the three-key return
schema; the `raw` shape; the no-auth posture; the pre-rename
`packs/research/...` paths in the frozen research-pack spec.

**Declined additions, with the cut-before-adding rung that killed each.**

- A response cache — rung 1, not genuinely needed: the caller controls query
  volume, and a cache would add invalidation with no named requirement.
- The `arxiv` PyPI client — rung 5 forbids it, and stdlib-only is a hard pin.
  Read as reference for its operational defaults only.
- A retriever base class shared with Perplexity — rung 1: two retrievers do
  not justify an abstraction, and it would break the one-self-contained-file
  convention the template role depends on.
- A PDF text extractor — rung 3: the standard library cannot extract PDF text,
  and the LaTeXML and LaTeX-source routes already satisfy the outcome.
- A tier-tuning configuration file — rung 6: the bound is one comparison, and
  a caller wanting other behaviour uses the raw passthrough.

## Approach

One file keeps one responsibility chain: compose a request, execute it through
a single throttled sender, map the Atom response to citations, then render.
Modes differ only in how they build the request and which renderer they use, so
throttle, retry, encoding, and metadata mapping are written once and inherited.

The tier ladder is a pure function from caller text to an ordered list of
candidate `search_query` strings, separated from the sender so the ladder is
testable without network access. Tier selection consumes only arXiv's reported
total, which makes selection decidable from a canned feed.

## Constraints

- Python standard library only, floor 3.11. No new runtime dependency, and no
  new module or helper file beside the script. Test fixtures and the recorded
  QA transcript are not source files and this constraint does not reach them.
- Exactly three top-level result keys; per-citation keys are the only
  extension point.
- Script retrievers run in the main session, so fetched bytes land in the
  caller's context — every response path is bounded before it is returned.
- Requests carry no credentials and the script declares no auth shape.
- Enrichment reaches exactly three hosts: arXiv, alphaXiv, and HuggingFace
  Papers. Each was confirmed to answer differently for a present and an absent
  identifier, which is the property the emit rule depends on.

## Construction tests

Per-task `Tests:` below. The suite is
`packs/desk-research/tests/skills/desk-research/test_research_retrievers_conformance.py`,
reshaped once in T1 and extended thereafter. Each TDD task carries one
compilable contract-surface stub; its intended red is earned from disposable
scratch during PLAN and not committed. One manual pass (T9) covers the live
API, because no unit seam observes arXiv's real behaviour; its transcript goes
to the feature's verification ledger.

**Intended red, validated.** All ten stubs were compiled and run from
disposable scratch against the current module. Each failed on its absent seam
rather than on a syntax error: T1, T3a, and T4a on the missing
`ArxivUnavailable`, `HostNotAllowed`, and `UnsafeDocument`; and T2, T2a, T3,
T4, T5, T6, and T7 on `AttributeError` for `build_tiers`, `build_request`,
`Sender`, `map_entry`, `parse_identifier`, `extract_sections`, and `enrich`
respectively. None passed. The scratch harness is not committed.

## Durable-output map

| Spec durable output | Task | Evidence |
| --- | --- | --- |
| Interface contract | T8 | Mode table and extension rule in the reference |
| User-facing promise | T8 | SKILL.md Retrievers section matches `--help` |
| Current product truth | T8 | `DESIGN.md` synthesis-ownership statement, gated |
| Release history | T10 | Version strings equal across both files |
| Reusable learning | T10 | Eval asserts tier honesty |

## Design (LLD)

### Design decisions
Owned by: T3, T6, T7.

The sender owns throttling because a per-mode throttle is the shape that lets
one mode bypass the interval. Enrichment's link check is injected rather than
called directly, so the emit-or-omit rule is decidable without network access.
Full text is fetched only after the record resolves, so a bad identifier costs
one request rather than two. Enrichment keeps a probe's verdict and discards
its body, so no third-party response text can reach the caller. AC-0046 owns
the deadline guarantee; T3a owns its one construction account, and no other
section restates the mechanism.

### Data & schema
Owned by: T4.

A citation is a mapping carrying `url`, `title`, `authors`, `primacy`, plus
`arxiv_id`, `version`, `submitted`, `revised`, `categories`,
`primary_category`, `pdf_url`, and, when arXiv publishes them, `doi` and
`journal_ref`. `url` is the sole abstract-URL field; a second one would let two
public fields for the same fact drift. Absent optional values are omitted keys,
not empty strings, so a consumer cannot mistake absence for an empty value.

### Interfaces & contracts
Owned by: T2, T2a, T4, T5, T6, T7, T8.

`retrieve(query, *, mode="search", **options) -> dict` keeps the positional
string contract. The CLI exposes mode selection, the title, author, abstract
and category flags, ordering selection, a date window, a raw `search_query`
passthrough, and `--full-text` with `--sections` and a budget override.
Ordering defaults to relevance; selecting another ordering is an explicit
waiver of the default and is reported in the returned content.

### Component / module decomposition
Owned by: T2, T3, T4.

One file, four internal seams: tier builder, request sender, Atom mapper,
renderers. Three are plain functions. The sender is a small class paired with
an injectable clock, because throttling needs somewhere to hold the previous
request's completion time and a module global would make two callers share it.
Nothing is exported beyond `retrieve` and the CLI entry point.

### State & control flow
Owned by: T2, T3.

The sender holds one piece of state: the completion time of the previous
request. Search walks candidate tiers until the selection bound is met or the
ladder is exhausted, then renders the last tier's result. The raw passthrough
and the field flags skip the ladder entirely, because a caller-composed query
has no tier to report.

### Behavior & rules
Owned by: T2, T2a.

Tier 1 quotes the caller's text verbatim. Later tiers drop only stopwords and
arXiv field-syntax metacharacters, then conjoin surviving terms, then narrow to
the leading terms, then disjoin. Stopword removal never applies to tier 1,
because removal destroyed a real title in measurement.

### Failure, edge cases & resilience
Owned by: T3, T3a, T4a, T5.

Every refusal is fail-closed and writes nothing to stdout, so a caller
parsing stdout cannot read a partial result as success. Host, scheme, and
resolved-address checks re-run on each redirect rather than once before the
first request, because a single pre-flight check is exactly what a redirect
defeats. A malformed identifier refuses rather than degrading to search, so a
typo cannot silently return unrelated work. An empty page with a non-zero reported
total is a retry. Exhausted retries write nothing to stdout, so a caller
parsing stdout cannot read a partial result as success.

### Quality attributes (NFRs)
Owned by: T3, T3a, T4a, T6.

Worst-case search cost is the ladder depth times the throttle interval. The
full-text budget bounds returned characters regardless of document size.

### Dependencies & integration
Owned by: T3a, T7.

Outbound hosts: arXiv's API, abstract and HTML paths, plus alphaXiv and
HuggingFace Papers for enrichment. All unauthenticated and read-only.

## Tasks

### T1: Reshape the conformance test's network boundary

**Depends on:** none. **Mode:** TDD.

**Tests:**
- Replace `patch.object(module, "urllib")` with a patch of
  `module.urllib.request.urlopen` only, matching the Perplexity case in the
  same file.
- Load each retriever under a module name including pack and skill rather than
  `path.stem`.
- Raise `urllib.error.HTTPError` from the patched seam and assert the script's
  own handler runs. Under the current wholesale mock this fails with
  `TypeError: catching classes that do not inherit from BaseException`, which
  is the red that proves the boundary was narrowed rather than renamed.
- Stub (`stub: true`):

  ```python
  def test_narrow_seam_lets_the_scripts_own_handler_run(self) -> None:
      module = _load(ARXIV_SCRIPT)
      err = urllib.error.HTTPError("u", 429, "Too Many Requests", None, None)
      with patch.object(module.urllib.request, "urlopen", side_effect=err):
          with self.assertRaises(module.ArxivUnavailable):
              module.retrieve("anything")
  ```

  Covers AC-0031, AC-0032.

**Done when:** its `Tests:` pass and the existing arXiv and Perplexity cases
still pass unchanged.

### T2: Tier ladder, selection, and reporting

**Depends on:** T1. **Mode:** TDD.

**Tests:**
- A case table whose rows are the measured hard inputs: text with a colon,
  bare boolean words, a long phrase that over-constrains, a title-shaped
  phrase, and a single term. Assert the whole emitted tier sequence, because a
  test reading only the winner cannot see an ordering regression.
- Pin tier 1 to the caller's untouched wording.
- Drive selection from canned totals so no request is made, including a row
  whose every tier exceeds the bound, asserting the terminal tier is returned
  and reported as terminal.
- Assert the rendered content names the selected tier and arXiv's reported
  total.
- Stub (`stub: true`):

  ```python
  def test_tier_one_quotes_the_callers_wording_verbatim(self) -> None:
      module = _load(ARXIV_SCRIPT)
      tiers = module.build_tiers("attention is all you need")
      self.assertEqual(tiers[0], 'all:"attention is all you need"')
  ```

  Covers AC-0001, AC-0002, AC-0003, AC-0004, AC-0005.

**Done when:** its `Tests:` pass.

### T2a: Caller-composed query controls

**Depends on:** T2, T3. **Mode:** TDD.

**Tests:**
- Assert each field flag composes into its arXiv prefix and that two flags
  join with a boolean conjunction.
- Assert the raw passthrough reaches `search_query` byte-identical and that no
  tier is built for it.
- Assert ordering is relevance when unselected, is the caller's choice when
  selected, and is named in the rendered content either way.
- Assert a date window becomes an arXiv submitted-date range in the request.
- Assert every case on the built request rather than on returned results, so
  the checks do not depend on what arXiv currently holds.
- Stub (`stub: true`):

  ```python
  def test_raw_passthrough_survives_request_construction(self) -> None:
      module = _load(ARXIV_SCRIPT)
      raw = 'ti:"attention is all you need" ANDNOT cat:cs.CV'
      params = module.build_request(search_query=raw)
      self.assertEqual(params["search_query"], raw)
  ```

  Covers AC-0036, AC-0037, AC-0038, AC-0039.

**Done when:** its `Tests:` pass.

### T3: Throttled, retrying sender

**Depends on:** T1. **Mode:** TDD.

**Tests:**
- Inject a clock and the patched `urlopen` seam; assert the interval is
  measured from the previous request's completion.
- Assert 429 and a 5xx each retry with strictly increasing delays, and that a
  zero-entry feed with a non-zero reported total retries.
- Assert exhaustion exits non-zero, names the status and attempt count, and
  writes nothing to stdout.
- Assert the built URL for caller text containing `&` and `=` carries no
  second parameter.
- Capture both streams and assert stdout carries the result mapping alone
  while throttle and retry notices go to stderr.
- Stub (`stub: true`):

  ```python
  def test_throttle_measures_from_the_previous_request(self) -> None:
      module = _load(ARXIV_SCRIPT)
      clock = module.Clock(now=100.0)
      sender = module.Sender(clock=clock, min_interval=3.0)
      sender.note_completed(99.0)
      self.assertAlmostEqual(sender.delay_before_next(), 2.0)
  ```

  Covers AC-0014, AC-0015, AC-0016, AC-0017, AC-0018, AC-0026.

**Done when:** its `Tests:` pass.

### T3a: Connection confinement and request bounds

**Depends on:** T3. **Mode:** TDD.

**Tests:**
- Drive a fake opener that reports a redirect target, and assert a redirect
  leaving the approved host set, or to a non-HTTPS scheme, is refused before
  the body is read.
- Assert each disallowed resolved-address class is refused before the request
  is sent, on the initial request and on a redirect. The case set is the
  criterion's enumerated list, so a new class cannot be added silently.
- Assert one elapsed budget spans the whole attempt and never resets: name a
  case that consumes most of it during address resolution and asserts the
  connection open and the body read inherit only what is left, and a case that
  consumes it across a redirect. A budget re-armed per phase would pass a
  per-read assertion while the attempt ran for a multiple of the bound.
- Assert the elapsed bound cuts off a body that returns some bytes inside
  every socket window. The reader follows the bounded reader in
  `packages/credbroker/credbroker/_sso.py`: chunked `read1` calls, the socket
  re-armed before each read to the smaller of the socket timeout and the
  remaining budget, and a chunk sized to `cap + 1 - total`. That file's comment
  records the same slow-drip defect this case drives, so the semantics are
  reused rather than re-derived.
- Assert the attempt fails closed when the remaining-budget timeout cannot be
  applied to the underlying socket. The borrowed reader continues on that
  condition, which would turn AC-0046's hard bound into best effort, so this
  case is where the reuse deliberately diverges from its source.
- Assert one response reads at most the limit plus a probe byte and retains at
  most the limit, so a body exactly at the limit is accepted and a body one
  byte over is detected.
- Stub (`stub: true`):

  ```python
  def test_redirect_off_the_approved_host_set_is_refused(self) -> None:
      module = _load(ARXIV_SCRIPT)
      with self.assertRaises(module.HostNotAllowed):
          module.check_redirect("https://export.arxiv.org/api/query",
                                "http://169.254.169.254/latest/meta-data/")
  ```

  Covers AC-0041, AC-0042, AC-0046, AC-0047.

**Done when:** its `Tests:` pass.

### T4: Atom mapping to citations

**Depends on:** T2, T3. **Mode:** TDD.

**Tests:**
- Two canned feeds — one record publishing DOI and journal reference, one
  publishing neither — drive one mapper, so omission and presence are the same
  code path under test.
- Read `primary_category` from its `term` attribute and the PDF link from the
  link whose title is `pdf`, since neither is element text nor selected by
  type.
- Assert every canonical field including the mapped author values.
- Assert optional fields are omitted keys rather than empty strings, that the
  canonical URL carries no version suffix while the version is its own field,
  and that submission and revision dates differ for a revised record with
  neither substituted for the other.
- Assert `retrieve` called with one positional string performs a search and
  returns the schema.
- Stub (`stub: true`):

  ```python
  def test_revised_record_keeps_its_two_dates_and_authors(self) -> None:
      module = _load(ARXIV_SCRIPT)
      cite = module.map_entry(ET.fromstring(REVISED_ENTRY_XML))
      self.assertEqual(cite["url"], "https://arxiv.org/abs/1706.03762")
      self.assertEqual(cite["version"], "v7")
      self.assertNotEqual(cite["submitted"], cite["revised"])
      self.assertEqual(cite["authors"][0], "A. Author")
      self.assertNotIn("doi", cite)
  ```

  Covers AC-0008, AC-0009, AC-0010, AC-0011, AC-0012, AC-0013.

**Done when:** its `Tests:` pass.

### T4a: Safe deserialization, output validation, and cross-mode bounds

**Depends on:** T3a, T4, T6, T7. **Mode:** TDD.

**Tests:**
- A doctype-bearing XML feed drives a refusal. An HTML document carrying
  script, style, an inline event-handler attribute, and a subresource
  reference is accepted and asserted inert on each of those four channels,
  matching the set AC-0050 enumerates — nothing executed, no subresource
  fetched — because refusing ordinary HTML would reject real arXiv renders. A structurally wrong document, and one carrying a
  malformed identifier or an off-host URL, each drive a refusal. Each case has
  its own failure mode and remedy.
- Assert each extracted identifier and URL is validated against its named
  grammar before it enters the return mapping, including refusals for
  userinfo, an unexpected port, a non-HTTPS scheme, and a lookalike host.
- Name a positive case for every branch of AC-0045's grammar at this
  boundary, because output validation is a different caller from T5's input
  routing and a branch covered only there can still be rejected here:
  `0710.4003` (pre-2015 four-digit), `1706.03762` (five-digit),
  `quant-ph/0201082` (legacy), `math.GT/0309136` (legacy with a subject
  class), and a `vN`-suffixed form of a modern and a legacy identifier. The
  four-digit branch is the one an earlier grammar rejected, so it carries its
  own case rather than riding a generic one.
- Hostile-content fixtures carry instruction-like text in a title, an abstract,
  and a section body; assert each renders as attributed data and changes no
  control flow. AC-0040 cites the pack invariant, so these cases test
  conformance rather than restating the rule.
- Assert the citation-count and per-mode rendered-character caps, each at its
  own firing input, and the cumulative retained-bytes bound across several
  distinct requests in one invocation rather than several retries of one.
- Capture stdout and assert a breached limit exits non-zero naming the limit
  and writes nothing.
- Stub (`stub: true`):

  ```python
  def test_a_dtd_bearing_response_is_refused(self) -> None:
      module = _load(ARXIV_SCRIPT)
      hostile = ('<!DOCTYPE feed [<!ENTITY x SYSTEM "file:///etc/passwd">]>'
                 '<feed xmlns="http://www.w3.org/2005/Atom"><entry/></feed>')
      with self.assertRaises(module.UnsafeDocument):
          module.parse_feed(hostile)
  ```

  Covers AC-0040, AC-0043, AC-0050, AC-0044, AC-0045, AC-0048, AC-0049,
  AC-0052.

**Done when:** its `Tests:` pass.

### T5: Identifier and URL resolution

**Depends on:** T3. **Mode:** TDD.

**Tests:**
- Classify both modern widths (`0710.4003` and `1706.03762`), a legacy
  slashed identifier, a legacy identifier carrying a subject class
  (`math.GT/0309136`), versioned forms of each, and abstract and PDF URLs,
  asserting each routes to arXiv's identifier parameter.
- Assert a near-miss identifier refuses with a non-zero exit instead of
  falling through to search; that fallthrough is the defect this task exists to
  prevent.
- Stub (`stub: true`):

  ```python
  def test_legacy_slashed_identifier_is_recognised(self) -> None:
      module = _load(ARXIV_SCRIPT)
      self.assertEqual(module.parse_identifier("quant-ph/0201082v1"),
                       "quant-ph/0201082v1")
      self.assertIsNone(module.parse_identifier("not an id"))
  ```

  Covers AC-0006, AC-0007.

**Done when:** its `Tests:` pass.

### T6: Bounded full text

**Depends on:** T4, T5. **Mode:** TDD.

**Tests:**
- Two saved LaTeXML documents as fixtures.
- Extract section titles from the section-title heading while skipping the
  nested numbering span; a naive parse yields digits, not names, which defeats
  name-based selection.
- Assert extracted section count equals the count of section elements in the
  same document. A depth-tracking parser under-counted by one in measurement,
  so this oracle is the guard rather than a fixed expected number.
- Assert the budget truncates across concatenated sections and the omission
  count is reported.
- Assert nothing is fetched unless full text is requested.
- Stub (`stub: true`):

  ```python
  def test_extracted_section_count_matches_the_documents_own_oracle(self) -> None:
      module = _load(ARXIV_SCRIPT)
      html = FIXTURE_LATEXML.read_text(encoding="utf-8")
      oracle = html.count('class="ltx_title ltx_title_section"')
      self.assertEqual(len(module.extract_sections(html)), oracle)
  ```

  Covers AC-0019, AC-0020, AC-0021, AC-0022.

**Done when:** its `Tests:` pass.

### T7: Enrichment with a discriminating presence check

**Depends on:** T4, T5. **Mode:** TDD.

**Tests:**
- Inject the presence check. Assert a host is emitted only when the check
  separates a present identifier from an absent one, and that a host answering
  identically for both is never emitted.
- Assert the rendered output carries no synthesis and no confidence rating,
  and that no part of a probe response body reaches the returned mapping —
  enrichment contributes confirmed URLs only.
- Stub (`stub: true`):

  ```python
  def test_a_check_that_cannot_discriminate_emits_nothing(self) -> None:
      module = _load(ARXIV_SCRIPT)
      # Answers "present" for every probe, real or absent, so it proves nothing.
      links = module.enrich("1706.03762", check=lambda url: True)
      self.assertEqual(links, [])
  ```

  Covers AC-0023, AC-0024, AC-0051.

**Done when:** its `Tests:` pass.

### T8: Companion prose and the interface contract

**Depends on:** T2, T2a, T3a, T4, T4a, T5, T6, T7. **Mode:** Goal-based check.

**Tests:**
- Compare `--help` output and the reference's mode table for the same flag set.
- Grep the three shipped surfaces for this repository's spec paths and
  governance vocabulary, asserting no match.
- Grep `DESIGN.md` for the statement that a retriever returns raw material
  while the calling skill owns synthesis.
- no stub (goal-based check). Covers AC-0028, AC-0029, AC-0030.

**Done when:** the greps return empty, the flag sets agree, and the `DESIGN.md`
statement is present.

### T9: Live end-to-end pass

**Depends on:** T8. **Mode:** Visual / manual QA.

**Tests:** no stub (manual QA). Invoke the shipped script for each mode against
arXiv: a free-text search, an exact fetch of a revised record, a fetch with
full text, and an enrichment call. Record stdout, stderr, and exit codes to the
feature's verification ledger. Covers AC-0035.

**Session boundary.** This session verifies the three modes end to end against
the live API and stops there. The field, ordering, date-window, and passthrough
controls are exercised only by T2a's request-level tests; the retry and
throttle paths only by T3's; and the section oracle only by T6's. None is
covered by live evidence, and this task claims none of them.

**Done when:** the ledger carries a transcript covering all three modes with
observed output captured.

### T10: Stream encoding, version pair, projection, evals

**Depends on:** T9. **Mode:** Goal-based check.

**Tests:**
- Grep the script for both stream reconfigure calls before its first write.
- Assert both manifests declare `1.1.9`.
- Re-run the catalogue self-host and assert an empty diff.
- Add the eval assertion covering tier honesty.
- no stub (goal-based check). Covers AC-0025, AC-0027, AC-0033, AC-0034.

**Done when:** both manifests read `1.1.9`, self-host is clean, and the eval
harness carries the new assertion.

## Rollout

- **Delivery:** big bang within the pack; reversible by reverting the pack
  content, since nothing persists state.
- **Infrastructure:** none.
- **External-system integration:** arXiv's API, abstract and HTML paths, plus
  alphaXiv and HuggingFace Papers. All unauthenticated and read-only.
- **Deployment sequencing:** pack content and its projection ship together;
  the projection is regenerated, never hand-edited.

## Risks

- arXiv's LaTeXML class names are an external contract with no stability
  guarantee. T6's oracle catches a wholesale change as a count mismatch rather
  than as silent truncation.
- The 429 that motivated the throttle did not reproduce, so the interval is
  adopted from the official client's default rather than from a measured
  failure threshold. If 429s persist, the interval is the first thing to raise.
- Tier selection's upper bound is a judgement calibrated on six measured
  queries, not a derived value. A caller wanting broader recall uses the raw
  passthrough.
- Enrichment's emit rule depends on a host answering differently for a present
  and an absent identifier. A host that changes to a single-page application
  would start answering identically; T7's injected check makes that a test
  failure rather than a silent wrong link.

## Changelog

- 2026-09-22: spec approved by eugenelim
- 2026-09-22: plan approved by eugenelim
