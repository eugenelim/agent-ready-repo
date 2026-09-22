# Verification ledger — arXiv retriever, production grade

Execution observations for `docs/specs/arxiv-retriever-production/spec.md`.
The plan is frozen; this file is where its execution evidence lands.

## T9 — live end-to-end pass (AC-0035)

Ran 2026-09-22 against the live arXiv API from the repository root on the
feature branch. Every invocation is the shipped script, not a test double. The
interpreter and script path are omitted from the arguments column, which is
otherwise verbatim, shell-quoted and reproducible as written. The one exception
is the author case: it necessarily passes a surname at the command line, shown
as `<surname>` because the repository forbids a real name in its prose. The
observed result is the evidence there, not the name.

| Case | Arguments | Exit | Observed |
| --- | --- | --- | --- |
| search, free text through the tier ladder | `'instruction adherence in agent config files'` | 0 | 3 keys, shape=raw, 10 citation(s), 18049 content chars. First line: `Query: tier 3 of 4; arXiv reported 97 matches.` |
| search, --title + --category | `--title 'attention is all you need' --category cs.CL` | 0 | 3 keys, shape=raw, 10 citation(s), 13292 content chars. First line: `Query: fielded; arXiv reported 10 matches.` |
| search, --search-query raw passthrough | `--search-query 'ti:"attention is all you need" ANDNOT cat:cs.CV'` | 0 | 3 keys, shape=raw, 10 citation(s), 13964 content chars. First line: `Query: caller-composed; arXiv reported 28 matches.` |
| search, --author | `--author <surname> --max-results 3` | 0 | 3 keys, shape=raw, 3 citation(s), 3151 content chars. First line: `Query: fielded; arXiv reported 772 matches.` |
| search, --abstract | `--abstract 'retrieval augmented generation' --max-results 3` | 0 | 3 keys, shape=raw, 3 citation(s), 4879 content chars. First line: `Query: fielded; arXiv reported 5834 matches.` |
| search, --sort submitted | `--category cs.CL --sort submitted --max-results 3` | 0 | 3 keys, shape=raw, 3 citation(s), 5520 content chars. First line: `Query: fielded; arXiv reported 119681 matches.` |
| search, --from/--to date window | `--category cs.LG --from 202401010000 --to 202401020000 --max-results 3` | 0 | 3 keys, shape=raw, 3 citation(s), 5287 content chars. First line: `Query: fielded; arXiv reported 47 matches.` |
| search, category refusing injected syntax | `--category 'cs.CL OR ti:attention'` | 2 | refused: `arxiv-retriever: category 'cs.CL OR ti:attention' is not an arXiv `; stdout empty: True |
| get, modern five-digit identifier | `--mode get 1706.03762` | 0 | 3 keys, shape=raw, 1 citation(s), 1427 content chars. First line: `# Attention Is All You Need` |
| get, modern four-digit identifier carrying a DOI | `--mode get 0710.4003` | 0 | 3 keys, shape=raw, 1 citation(s), 852 content chars. First line: `# YREC: The Yale Rotating Stellar Evolution Code` |
| get, legacy slashed identifier via an abs URL | `--mode get https://arxiv.org/abs/quant-ph/0201082` | 0 | 3 keys, shape=raw, 1 citation(s), 562 content chars. First line: `# Quantum Computers and Quantum Computer Languages: Quantu` |
| get, a versioned request | `--mode get 1706.03762v1 --full-text` | 0 | 3 keys, shape=raw, 1 citation(s), 5861 content chars. First line: `# Attention Is All You Need` |
| get, --full-text at the default budget | `--mode get 1706.03762 --full-text` | 0 | 3 keys, shape=raw, 1 citation(s), 5894 content chars. First line: `# Attention Is All You Need` |
| get, --full-text --sections conclusion | `--mode get 1706.03762 --full-text --sections conclusion` | 0 | 3 keys, shape=raw, 1 citation(s), 2781 content chars. First line: `# Attention Is All You Need` |
| get, malformed identifier refuses | `--mode get 1706.0376x` | 2 | refused: `arxiv-retriever: '1706.0376x' is not a well-formed arXiv identifie`; stdout empty: True |
| enrich | `--mode enrich 1706.03762` | 0 | 3 keys, shape=raw, 1 citation(s), 451 content chars. First line: `# Attention Is All You Need` |

**What this establishes.** All three modes answer over the live API and every
documented search control works. The free-text case selects tier 3 of 4 and
reports it — the same query the previous retriever sent as
`all:instruction adherence in agent config files`, which matched 124,103 papers
with an unrelated top hit. Every successful result carries exactly the three
contracted keys with `shape: raw`. A malformed identifier and an injected
category are each refused with a diagnostic on stderr and nothing on stdout, so
a caller parsing stdout cannot read a refusal as a result. The default
ten-result search emits 23,315 characters against the 40,000 cap.

**Session boundary, and where it diverges from the plan.** T9's approved scope
is the three modes; the plan states plainly that the field, ordering,
date-window and passthrough controls receive no live coverage and are left to
T2a's request-level tests. This session exercised them live anyway. That is a
divergence from the approved scope, not a reading of it: the plan is frozen and
says what it says, and the rows above cover more than it asked for. Nothing
approved went unexercised, so the divergence adds evidence rather than removing
any, and it is recorded here rather than resolved by amendment.

What this session does **not** exercise: the retry, throttle, byte,
elapsed-budget, redirect, resolved-address and parser-refusal paths. Those are
driven by unit cases against injected seams in
`packs/desk-research/tests/skills/desk-research/test_research_retrievers_conformance.py`,
because provoking them against the live service is neither reliable nor
courteous.

## Mutation evidence

Every control added for a sustained review finding was checked by reverting the
fix and confirming the suite fails. All thirty-one failed when reverted, so
none is a control that cannot fail. Seven tests that passed under their own
mutation were strengthened until they failed, and are counted below in their
strengthened form.

| Reverted control | Result |
| --- | --- |
| quote stripped from every query literal | suite fails |
| accepted-keyword filter on the search branch | suite fails |
| empty-page retry wired at all three call sites | suite fails |
| whole-document doctype scan, not a 4 KiB prefix | suite fails |
| named-section selection without a widen-to-everything fallback | suite fails |
| full-text ceiling clamped against a caller override | suite fails |
| the effective ceiling used by the `get` renderer | suite fails |
| cap measured over the serialized result, not `content` alone | suite fails |
| the emitted form kept compact | suite fails |
| query-term de-duplication | suite fails |
| returned entry matched against the requested identifier | suite fails |
| returned version matched when the request names one | suite fails |
| budget checked before resolution | suite fails |
| budget checked after resolution | suite fails |
| resolution bounded by a thread the caller stops waiting on | suite fails |
| redirect target re-checked by its own guard | suite fails |
| courtesy interval applied to every redirect hop | suite fails |
| `URLError`-wrapped timeout mapped to the limit error | suite fails |
| bare timeout mapped to the limit error | suite fails |
| category confined to its value grammar | suite fails |
| date bound confined to its value grammar | suite fails |
| socket re-armed before each read | suite fails |
| drained-stream treated as EOF rather than an unbounded read | suite fails |
| backslash removed from a structured field's literal | suite fails |
| full text fetched from the revision the citation names | suite fails |
| courtesy interval refused when it would outlast the deadline | suite fails |
| a tier arXiv refuses advances instead of failing the search | suite fails |
| completion recorded even when the read of that response failed | suite fails |
| tier 1 keeping the backslash the structured path removes | suite fails |
| the ladder advances only on a refused query, never on an outage | suite fails |
| a ladder cut short by refusals is not reported as terminal | suite fails |

## Suites and gates

| Gate | Result |
| --- | --- |
| `make lint-ruff` | clean |
| `make lint-mypy` | clean, 148 source files |
| `tests/skills/desk-research/` (floor 9) | 85 passed |
| `tests/skills/desk-research-project-start/` (floor 7) | 8 passed |
| `tests/pack/` + five project suites + devils-advocate, `--import-mode=importlib` | 17 passed |
| `agentbundle catalogue lint --deep` | no errors |
| `agentbundle catalogue verify` | no drift |

The third pack suite needs `--import-mode=importlib`: six suites ship a file
named `test_project_knowledge_boundary.py`, and without that mode collection
fails on the basename collision. The Makefile passes it; a hand-run invocation
that omits it reports four collection errors that are not defects.

One pre-existing warning is unchanged: `CAT-S003` on the skill's `SKILL.md`,
already past the 500-line recommendation before this change at 548 lines.

## Fixtures

The two LaTeXML fixtures are written, not captured, and they took three attempts
worth learning from:

1. Sections were first regex-extracted non-greedily, which truncated every
   section containing a subsection and left unbalanced markup. The
   section-count oracle caught it: the parser reported 3 of 8.
2. Whole captured documents fixed the structure but carried ten real email
   addresses and their authors' names, which the security lane caught against
   the repository's prohibition on personal data in a fixture.
3. Sanitising a real paper's prose is not winnable, because its body cites real
   people, and an externally sourced fixture would additionally owe a licence.

So the fixtures are synthetic and deliberately shaped: each reproduces a markup
pattern the parser was observed to handle wrongly — the numbering span inside a
section heading, a subsection nested inside its section, script, style, inline
handler and subresource carriers, and a bibliography following the last section.
They carry no name, owe no licence, and total 38 KiB. Coverage of arXiv's real
markup is the recorded live pass above, not these files.

## One regression this ledger's own evidence caught

Measuring the cap over the indented form pushed the default ten-result search to
40,688 characters, past the 40,000 ceiling — the flagship query began failing
closed. The cause was duplication rather than the cap: each abstract was carried
both in `content` and in its citation. AC-0011 asks a citation for the abstract
URL and never for the abstract text, so the citation copy was never contracted.
Removing it, and emitting compact JSON, brought the same query to 23,315
characters.

## Review lanes

Every reviewer ran as an isolated `codex exec` session over a supplied evidence
packet, read-only, with the role definition inlined because `codex exec` cannot
dispatch a projected agent. Raw reports and paired adjudications are retained in
the session's ignored `.context/reviews/` path.

Spec stage reached a byte-exact clean adversarial result after eight rounds, and
an adjudicated clean secure-design result. Implementation stage ran adversarial
and security lanes over the diff; between them they raised 27 findings across
three rounds. The two most serious had passed an earlier live pass that
exercised only four invocations: every fielded flag raised `TypeError` before
sending a request, and a caller's double quote escaped the phrase literal into
live arXiv boolean syntax — the same defect class this delivery exists to
remove. Both lanes independently converged on one root cause, network-security
criteria written before establishing what `urllib` enforces.

## A final security round, and one claim it could not sustain

The last security pass raised three concerns. Two were sustained and fixed: a
versioned request fetched full text from the version-free URL, which serves the
latest revision, so an older revision's citation carried the newest text —
measured at 180,279 bytes for v1 against 187,983 for v7; and the courtesy
interval could sleep past an attempt's deadline, which now fails closed instead.

The third claimed that a trailing backslash in a structured field could
reacquire operator authority under Lucene syntax. The reviewer said it was not
dynamically confirmed, and a probe refutes it: `ti:"safe\"` answers HTTP 400
rather than executing. The backslash is removed from a structured field's
literal as robustness — it buys a usable query rather than closing a hole — but
not from tier 1, where AC-0003 promises the caller's wording and a candidate
arXiv refuses advances to the next tier anyway.

## Accepted residuals

Two findings are accepted as proportionate rather than repaired, because each
repair would need a controlled amendment and fresh approval of a frozen plan to
correct a rationale clause that binds no check:

- The plan's declined-additions rationale says the LaTeXML and LaTeX-source
  routes satisfy the outcome, while the spec states that nothing in this release
  reads the LaTeX source archive. The spec governs, no criterion or task reads
  that archive, and the security finding about archive confinement was refuted
  on exactly that reachability ground.
- The plan repeats the literal version that AC-0027 owns. The two agree, and
  AC-0027 is the checked home.

## Known limits carried into the release

- Resolved-address checking is a preflight refusal and does not close DNS
  rebinding. `urllib` connects by hostname with no way to pin the connection to
  the address that passed, and pinning would mean replacing it with a
  hand-built HTTPS client. The same limit is recorded at
  `packages/credbroker/credbroker/_sso.py`.
- The identifier grammar accepts both modern widths for any year. arXiv issued
  four-digit identifiers to 2014 and five-digit from 2015, and refusing a width
  by year would reject valid identifiers.
- The 3.0s inter-request interval is adopted from the reference client's
  default, not measured against a failure threshold: the HTTP 429 that motivated
  it did not reproduce across eight probes. It is the first value to raise if
  429s recur.
- Tier selection's 2,000-match ceiling is a judgement calibrated on six measured
  queries. A caller wanting broader recall uses the raw passthrough.
