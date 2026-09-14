# Counterpoints — loop telemetry export delivery mechanisms

Adversarial review of
[`loop-telemetry-export-survey.md`](loop-telemetry-export-survey.md).
**Date:** 2026-09-11.

Six findings were attacked. Five took rating downgrades, one resolved as an
irreducible tension, and one new finding emerged that the survey had missed
entirely. One of the survey's own verdicts was self-corrected against
repository evidence.

## Finding F1/F2: "OTLP/HTTP JSON is a stable public contract, stable since June 2023"

- **Counter-position:** "Stable" is a maturity *label* applied at
  `opentelemetry-proto` v0.20.0, not a freeze of the wire format. The survey
  treated a label as a guarantee, and a hand-rolled sender inherits every
  subsequent change with no SDK to absorb it.
- **Counter-evidence:** Format-affecting changes after v0.20.0, from the proto
  CHANGELOG and release notes: v1.1.0 (2024-01-10) added `flags` to Span and
  Span/Link; v1.9.0 (2025-10-31) dropped attribute-value restrictions;
  **v1.10.0 (2026-03-09) shipped two breaking changes** — a correction to
  uint64/fixed64 JSON representation, and `ref` renamed to `strindex`; v1.11.0
  (2026-07-21) added ProcessContext and documented 64 MiB request / 4 MiB
  response limits. The uint64 trap is demonstrated, not hypothetical:
  `opentelemetry-js` #4202 shipped `{"low": …}` objects for uint64 and was
  rejected with `ReadUint64: unsupported value type`. Collector issue **#10546**
  reports that non-conformant JSON posted to `/v1/logs` is accepted with HTTP
  200 and silently discarded — but **this did not reproduce** when measured
  2026-09-12 against a live Collector: base64 identifiers and a flat attribute
  object both returned HTTP 400 with a parser message naming the offending byte
  (`telemetry.md` § 10.3). And the spec's exporter obligations are
  non-obvious: do not retry on `partialSuccess` (#9457), honour `Retry-After`
  on 429/503 (#9892, where the *official* exporter stripped the 429 and broke
  backoff), implement exponential backoff, enforce size limits.
- **Mitigations that survive, and they are ours:** the uint64 break is in
  **metrics**, `strindex` is in **profiles** (still development status), and
  v1.9.0's attribute change is a *receiver* obligation. A **logs-only** sender
  emitting string-encoded timestamps is not exposed to those three.
- **Verdict:** rating downgrade — `[high]` → `[moderate]`. Reason:
  stale prior art plus contested-in-field. The contract is implementable but not
  static. The downgrade rests on the format's movement and the exporter
  obligations, **not** on silent rejection: that half of the counter-position
  was itself disconfirmed by measurement, and a 200 now means the payload parsed
  — it still does not mean the attribute names are the ones a query expects.
- **Consequence for the plan:** a real Collector round-trip is still required,
  but for a sharper reason than first written — not because failure is silent
  (it is not), but because it is the only check that sees attribute naming.
  Acceptance criteria must still cover partial-success handling, `Retry-After`,
  backoff, and the size limits explicitly.

## Finding F3: "Production prior art exists in canonical/operator and otlp-json"

- **Counter-position:** Both examples are weaker than the survey claimed, and
  two projects was thin evidence even before scrutiny.
- **Counter-evidence:** `dimaqq/otlp-json` was **archived by its owner on
  2026-04-27** and is read-only; PyPI development status *3 - Alpha*; pinned to
  OTLP 1.5, so it predates the v1.9.0, v1.10.0 and v1.11.0 changes; it carries
  open TODOs including "Status fields" and "validate what fields are in fact
  optional"; and it explicitly scopes itself to same-process tracing, stating
  it is "not meant to be used for data received and forwarded" — which is
  exactly our use case. For `canonical/operator`, the retrieval **failed**:
  GitHub code search required authentication and no public evidence of
  deployment breadth, production scale or bug history was obtainable. The
  failed search is itself the finding.
- **Verdict:** rating downgrade — `[moderate]` → `[low]`. Reason: prior art
  defunct and uncorroborated.
- **Note:** this downgrade does not reverse the implementation choice. That is
  settled by repository authority — `guides/_shared/how-to/author-a-skill.md:104`
  makes Tier 1 mandatory and the default and states "Prefer stdlib over a pip
  dependency" — not by how many other projects have hand-rolled one. What the
  downgrade removes is the comfort of precedent.

## Finding F20: "Opt-in is the current practitioner default"

- **Counter-position:** By install count, opt-out with disclosure is the
  dominant pattern among major developer tools. Go 1.23 is a single activist-driven
  exception, and its outcome is evidence *against* opt-in on the
  only metric that matters — whether the data is usable.
- **Counter-evidence:** .NET CLI (opt-out, first-run notice), VS Code
  (`telemetry.telemetryLevel` defaults to `"all"`), JetBrains IDEs (opt-out on
  legitimate-interest basis) and Docker Desktop (requires
  `TELEMETRY_ENABLED=false`) are all opt-out with disclosure. On Go's outcome:
  telemetry shipped in gopls v0.14 (October 2023) with **around 100 users**
  enabling upload, reaching only ~1,800 weekly participants after an active
  in-editor prompting campaign — roughly **0.06%** of an estimated 3 million
  installations, well below the "few percent" floor Cox himself feared. Cox's
  own arithmetic in *Opting In to Transparent Telemetry* is the sharpest point:
  opt-out across ~1M systems means each machine reports ~1.6% of the time,
  under once a year; opt-in across ~100k systems means each must report ~16% of
  the time, roughly every six weeks. **Opt-in is more invasive per participating
  machine, not less.** Against that, the Go team did report finding "numerous
  genuine bugs" that "would likely never have been reported" conventionally.
- **Verdict:** rating downgrade — `[high]` → `[moderate]`. Reason:
  contested-in-field, and the headcount claim was wrong.
- **What survives:** opt-in remains the safest choice against *backlash*, which
  is what the survey actually evidenced. It is not the majority practice, and it
  is not free of a privacy cost of its own.

## New finding N1: "off unless configured" is silent non-disclosure, not consent

This is the counter-pass's most consequential result, because it attacks the
design the survey was converging on rather than a finding in it.

- **Counter-position:** "Nothing sends unless an endpoint is configured" is a
  **third category**, and not the ethical high ground the survey implied. It is
  neither opt-in nor opt-out-with-disclosure: the capability exists, the user is
  never told, and so no informed consent is obtained either way. The observed
  criticism pattern is not "you collect data" but "there is no mention of
  telemetry or the remote endpoint in README.md." For corporate or regulated
  deployments, an undisclosed outbound-capable component is a compliance concern
  regardless of its default state.
- **Counter-evidence:** practitioner discussion of opt-out telemetry in
  developer tools; the documented criticism shape in tool issue trackers.
  Rated `[moderate]` — practitioner sentiment, thin independence.
- **Verdict:** new finding, `[moderate]`. **Silence is not the safe third
  path.**
- **Consequence for the plan:** whichever mechanism is chosen, disclosure is a
  required acceptance criterion, not a documentation nicety. The pack README,
  the guide, and `telemetry.md` must state that the capability exists, what it
  sends, and where — even while it ships off. Our constraint "off unless
  configured" satisfies the *behaviour* bar and does nothing for the *consent*
  bar.

## Finding F22a: "No project has documented a public regret about bundled-vs-separate"

- **Counter-position:** The claim survives only under a narrow definition of
  regret. Maintainers rarely publish architectural regret memos; users file
  bugs. Reading only for memos guarantees the answer.
- **Counter-evidence:** the bundled-but-disabled model has a **confirmed
  fail-open history**. Next.js Discussion #43947: in v12.1.6 two separate code
  paths existed — `isDisabled()` read `NEXT_TELEMETRY_DISABLED` and
  `isEnabled()` did not — so `next telemetry status` reported "Enabled" with
  the variable set and data was transmitted; a community patch (#43948) was
  merged to canary. Next.js #10713 documents a second mode: `next telemetry
  disable` in one Docker layer is reset by the following build step, with the
  practitioner conclusion to "assume that Next.js analytics will be enabled
  somewhere in your workflow despite your best efforts to disable it." On the
  separate-package side the documented failures are milder in kind: OTel JS
  #6519, a missing `otlp-exporter-base` manifest entry **masked by npm
  hoisting** and broken under pnpm, and #4297, where removing the Jaeger
  exporter broke `sdk-node` at startup. No project reversal was found in either
  direction.
- **Verdict:** rating downgrade — `[high]` → `[moderate]`. Reason: discourse
  artifact; absence of memos is not absence of regret.

## Finding F22b: which guarantee to keep — the underlying tension

- **Counter-position:** A credible, well-evidenced position opposes structural
  separation: bundled-but-disabled is accepted practice for single-binary tools
  (Buildkite, Argo, Dagger), Go itself ships telemetry **inside the toolchain
  binary**, and the separate-package model has its own documented failure mode
  in the OTel "no-op trap" — where a user who installs the tool but not the
  exporter gets zero data with no warning, a state the OTel spec calls valid and
  intentional but which is indistinguishable from misconfiguration for a CLI
  operator.
- **Counter-evidence:** substantive on both sides. For structural separation:
  OTel's zero-dependency API with separate SDK and exporters, named in the
  library guidelines as the intended model; Jenkins shipping its OTel plugin
  unbundled; the Next.js fail-open incidents above; and CVE-2024-3400 (PAN-OS
  GlobalProtect, April 2024), where Palo Alto first advised disabling device
  telemetry as mitigation and then **retracted it** — "device telemetry does not
  need to be enabled for PAN-OS firewalls to be exposed to attacks" — the
  canonical case for compiled-in telemetry as attack surface irrespective of the
  flag. For bundling: the three CI tools above, Go's own architecture, and the
  no-op-trap and version-skew evidence against splitting.
- **Verdict:** **do-not-resolve.** More evidence would not collapse this.
  Structural separation holds when the deployment unit is package-managed, the
  adopter population includes regulated or air-gapped environments, and the
  privacy promise is load-bearing. Bundled-but-disabled holds when the
  deployment unit is a single artifact, split packaging would fragment the
  release surface, and observability coverage matters more than a hard
  guarantee.
- **The asymmetry that is not a tie, and should drive the decision:** the two
  failure modes differ in **severity**, not merely likelihood. A bundled sender
  that fails open breaks a privacy promise to the adopter and is
  externally visible; a separate sender left uninstalled merely produces no
  data, which is internally visible and recoverable. Both are documented. Only
  one is irreversible once it happens.
- **Category-error caveat on the strongest pro-separation precedent:** the OTel
  API/SDK split solves a *library authorship* problem, where the library author
  and the operator are different people. In a CLI both roles collapse into the
  end user, so the analogy is structurally imperfect and should not be leaned on
  as decisive.

## Finding F12: "Nobody documents tailing an application's own ad-hoc JSONL"

- **Counter-position:** File-then-tail is a deliberate architecture for
  first-party software you control, and crash durability makes the file a
  feature rather than a limitation — which inverts the survey's framing.
- **Counter-evidence:** Dash0's filelog guide explicitly names **batch jobs**
  and **nightly billing runs** — first-party software with full format control
  — as primary use cases alongside legacy systems. On durability, OTel's own
  Resiliency page states that "Collector crashes or terminations using only an
  in-memory sending queue result in lost data in memory," and the same applies
  to an in-process SDK: batchers buffer in memory and SIGKILL, OOM kill or
  container eviction cannot be caught by shutdown hooks. Collector issue #2285
  ("Improving resiliency through disk buffering") treats disk-first as the
  high-durability pattern. Against the counter-position: the same Dash0 guide
  states that "if you control the applications writing these logs, the best
  solution is configuring them to emit structured, single-line JSON logs
  directly" — file-then-tail is a fallback even when you own the code; AWS
  Lambda's OTel pattern deliberately avoids files, using the Telemetry API with
  an in-memory decouple processor; and **no** official OTel, AWS, GCP or Azure
  page endorses "write JSONL, tail with filelog" as the preferred pattern for
  new first-party code.
- **Verdict:** rating downgrade — `[low]` → **do-not-resolve on the framing,
  `[low]` retained on the literal claim**. The literal claim stands: no
  endorsed prescription exists. But the survey framed the file as a constraint
  to be overcome, and the durability evidence shows it is also a guarantee.
- **Consequence, and it favours our existing design:** our exporter reads
  `events.jsonl` rather than hooking live transitions, so it already inherits
  the crash-durability property. `telemetry.md` § 6 notes that killing a run
  mid-phase loses that phase; an in-process sender would make that worse, not
  better. The file-first shape is accidentally correct on durability and should
  be stated as a deliberate property rather than tolerated as a limitation.

## Self-correction — survey finding F25

Not a counter-retrieval result. Verified directly against this repository
while the counter-passes ran, and it reverses the survey's own reasoning.

The survey used the install-only floor rail to disqualify mechanism M1's
upgradability. But `collect_pack_root_bins` has exactly one production caller
— `install.py:2187`, inside the user-scope-gated `_deliver_user_scope_floor` —
and nothing in `upgrade.py` references it. That means the **already-shipped**
`packs/credential-brokers/.apm/adapter-root-bins/sso-broker.py`, a
security-sensitive credential broker invoked by skills through
`~/.agentbundle/bin/sso-broker.py`, together with its
`_sso_keychain_macos.py` and `_sso_credman_windows.py` helpers, is delivered
once at install and **never refreshed on upgrade**.

So the gap is a **pre-existing defect already affecting a shipped
security-sensitive executable**, not a property of M1. Repairing it is shared
infrastructure work that benefits `credential-brokers` at least as much as a
telemetry exporter. F25's evidence stands; its verdict was wrong.

This discovery is outside the accepted intent of the telemetry-export work. It
is recorded here and surfaced to the owner; no `[backlog].open` entry or
deferral marker was created, because that routing is the owner's call through
`work-intake`.

## Findings that survived unchanged

- **F21 (per-engine export is the prevailing architecture)** — `[high]`
  retained. No counter-evidence was found. The closest adjacent result, that Go
  ships telemetry bundled in the toolchain binary, concerns packaging rather
  than per-engine versus shared emission, and does not bear on it.
- **F7, F8, F9 (OTel configuration precedence and endpoint semantics)** —
  `[high]` retained. Not attacked; three independent primary sources.
- **F23 (CI/CD result vocabulary and cardinality)** — `[high]` retained. Not
  attacked, and the Release Candidate status the survey flagged is an argument
  for versioning the line rather than a weakness in the finding.

## Moderator pass

The highest-signal unused counter-material was Cox's per-machine invasiveness
arithmetic — that opt-in telemetry reports *more often per participant* than
opt-out does. It is recorded under F20 because it reframes opt-in as a
different privacy trade rather than a strictly safer one, which no source in
the original survey had suggested. No further query was issued: the three
counter-positions with decision weight (F2's operational obligations, F22's
severity asymmetry, and N1's disclosure gap) all reached substantive evidence
on both sides.
