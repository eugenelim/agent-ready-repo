# Loop telemetry export — delivery mechanism survey

> Discipline: applied (practitioner-pattern survey)

**Date:** 2026-09-11 · **Against:** `agentbundle` 0.44.0, `core` 2.25.15, commit `ec6b94f91`

> **Adversarially reviewed.** Ratings below are post-review.
> [`loop-telemetry-export-counterpoints.md`](loop-telemetry-export-counterpoints.md)
> downgraded F1/F2 (`high`→`moderate`), F3 (`moderate`→`low`), F20
> (`high`→`moderate`) and F22's no-regret clause (`high`→`moderate`); recorded
> F22's core question and F12's framing as **do-not-resolve**; corrected F25's
> verdict against repository evidence; and added **N1 — "off unless configured"
> is silent non-disclosure, not consent**, which no finding here anticipated.
> Read the counterpoints before acting on this survey.

## The question

`loop-engine.py` records a thirteen-field envelope to `.loop-run/events.jsonl` on
every FSM transition. Nothing sends it anywhere. This survey asks what should
send it, where that sender should live, and what the standards and the
practitioner field actually do — before any mechanism is chosen.

Two owner-supplied constraints frame it. **The default is an exporter per
engine**, not one shared emitter. And hooks are excluded: a measurement of
156 ms per `PostToolUse` call was taken and the route rejected. That measurement
appears in no repository record, so it is carried here as an owner-supplied
constraint, not a repository-verified fact.

## Findings — the standards surface

**F1. OTLP/HTTP with JSON encoding is a stable public contract.** `[moderate]`
(downgraded — the label is not a format freeze; see counterpoints F1/F2)
Declared stable in `opentelemetry-proto` 0.20.0, released 2023-06-06 (PRs
#436/#435); the live specification is OTLP 1.11.0 and does not qualify JSON as
experimental. Protobuf and JSON encodings sit on the same stability track for
the three stable signals. Triangulated across the proto CHANGELOG, the OTLP spec
page, and closed specification issue #1957 — three primary sources, independent
of any vendor.

**F2. A hand-rolled stdlib sender is correct if five encoding rules are
honoured.** `[moderate]`
(downgraded — five rules are necessary, not sufficient; the spec also obliges
partial-success handling, `Retry-After`, backoff and size limits. **Measured
correction 2026-09-12:** the silent-200 claim is too strong — structural errors
return HTTP 400; see `telemetry.md` § 10.3)

OTLP deviates from standard proto3 JSON mapping in ways a
naive implementation gets wrong: `traceId`/`spanId` are **hex**, not base64
(specification PR #911 made this an explicit deviation); 64-bit fields
including `timeUnixNano` and `AnyValue.intValue` are **quoted decimal
strings**, not JSON numbers; enums such as `severityNumber` are **integers**,
not names; field names are lowerCamelCase; attributes use the `AnyValue`
wrapper. The base64 trap is not hypothetical — `opentelemetry-go` issue #1924
documents multiple implementations shipping the wrong encoding after the
change. A canonical reference payload exists at `opentelemetry-proto`
`examples/logs.json`.

**F3. There is production prior art for exactly our constraint.** `[low]`
(downgraded — `otlp-json` was archived 2026-04-27 and was alpha/OTLP-1.5;
`canonical/operator`'s scale could not be corroborated)
`canonical/operator` (Juju charm framework) implements an OTLP/HTTP JSON sender
over `urllib.request`, with JSON encoding isolated in an `_otlp_json` module,
because the framework cannot absorb the OTel SDK as a dependency. A second,
smaller precedent is the no-dependency `otlp-json` package on PyPI — now
archived. Two projects was thin evidence before review; after it, one is dead
and the other unverifiable, so precedent supports nothing here. The
implementation choice rests on repository authority instead (see F28).

**F4. No standards body forbids a hand-rolled OTLP client.** `[moderate]` No
discouraging statement was found in the specification or proto repository. The
spec is written as a public interoperability contract, and the OTel Collector
is itself not a Python-SDK consumer. Rated moderate because this is an
argument from absence.

**F5. The official SDK route carries a substantial dependency footprint.**
`[high]` `opentelemetry-exporter-otlp-proto-http` 1.44.0 requires
`googleapis-common-protos`, `opentelemetry-api`, `-sdk`, `-proto`, two
`-exporter-otlp-*-common` packages, an HTTP transport extra, and
`typing-extensions`; `protobuf` arrives transitively. `grpcio` is not pulled in
by the HTTP exporter, and the default transport recently moved from `requests`
to `urllib3`, so the footprint has shrunk slightly — but `protobuf` and
`googleapis-common-protos` are non-negotiable.

**F6. JSON acceptance is not universal, and this bounds target choice.**
`[moderate]` The OTel Collector's `otlp` receiver accepts JSON by default over
HTTP, auto-detecting from `Content-Type`, and Honeycomb documents HTTP/JSON
support. Against that: Elastic's OTLP endpoint documents `encoding: proto` as
the only supported encoding; Datadog's OTLP logs intake examples show
`http/protobuf` only; Axiom rejects JSON for `/v1/metrics`. A JSON sender
aimed at a Collector is safe; aimed directly at Elastic or Datadog it is
blocked. Rated moderate because several of these are vendor-doc silences
rather than explicit refusals.

**F7. `telemetry.md`'s claim about OTel's configuration precedence is
accurate.** `[high]` Three primary sources carry the same normative rule: when
a declarative configuration file is supplied, all other `OTEL_*` environment
variables **MUST** be ignored, except those referenced through `${VAR}`
substitution inside the file. So our intended inversion — environment variable
overrides both files — is a real, deliberate divergence from the spec, exactly
as § 5.3 describes. Two adjacent corrections: the variable is now
`OTEL_CONFIG_FILE` (renamed from `OTEL_EXPERIMENTAL_CONFIG_FILE` per TC
decision, specification issue #3752), and the YAML **schema** is stable while
language-SDK implementations remain experimental.

**F8. `${VAR:-default}` substitution is the spec's own middle path.**
`[high]` The official `otel-sdk-migration-config.yaml` example demonstrates
`"${OTEL_EXPORTER_OTLP_ENDPOINT:-http://localhost:4318}/v1/traces"`.
Substitution happens at parse time; the variable is not live at export time.
This is a third option between "file wins" and "env wins" that our design
discussion had not considered.

**F9. Endpoint path semantics differ by variable, and this is a common
defect.** `[high]` `OTEL_EXPORTER_OTLP_ENDPOINT` is a base to which the SDK
appends `v1/logs`; `OTEL_EXPORTER_OTLP_LOGS_ENDPOINT` "MUST be used as-is
without any modification". The per-signal variable takes precedence. Any
configuration surface we build has to pick one semantic and say which.

## Findings — the no-code route

**F10. A Collector can tail our JSONL, but the signal is permanently
logs-shaped.** `[high]` The `filelog` receiver plus a `json_parser` operator
promotes top-level JSON keys to log-record attributes and can lift our
ISO-8601 field to the record timestamp. But there is **no supported route from
a file of events to spans**: contrib issue #3071 requested exactly this in 2021
and remains open with no merged implementation, and the `transform` processor
operates within a single signal type. Our `phase_s` durations look span-like
and would stay log attributes.

**F11. `filelog` is beta, and correct operation needs a second
component.** `[moderate]` The receiver is beta for logs in
`opentelemetry-collector-contrib`. Without the `file_storage` extension,
offsets are in-memory only: a restart either replays the file from the
beginning or skips what arrived during downtime. With it, delivery is
**at-least-once** — a crash between export and offset write re-delivers lines,
so any consumer must tolerate duplicate `run_id:seq` tuples. Triangulated
across the receiver README, the storage extension README, and two independent
practitioner guides.

**F12. Nobody documents doing this with an application's own ad-hoc JSONL.**
`[low]` Searches across CNCF, vendor guides and GitHub discussions found no
named case study of tailing an application-authored ad-hoc JSONL file in place
of instrumentation. Every documented `filelog` use is Kubernetes container
stdout, a legacy app whose framework writes files, or third-party software
where instrumentation is impossible — all cases with institutional motivation
we would not share. Rated low and explicitly flagged for survivorship bias:
the absence of published failures is not evidence of success.

**F13. Per-developer Collector deployment is viable but heavy.** `[moderate]`
The "agent" deployment pattern is one Collector per host and the docs do not
argue against running one locally. The friction is size: `otelcol-contrib`
ships around 120 MB because it bundles every community component; an
`ocb`-built minimal distro carrying only `filelog`, `file_storage` and `otlp`
reportedly reaches roughly 20-30 MB, at the cost of maintaining a build.

**F14. OTel specifies a File Exporter format.** `[high]` OTLP-encoded JSON,
one request-shaped object per line, which a Collector ingests natively. This
admits a mechanism nobody had named: transform locally, never send.

## Findings — distribution and consent

**F15. `uv tool install` / `pipx install` from PyPI is the ecosystem answer for
a small optional network-sending Python tool.** `[moderate]` It gives an
isolated venv per tool, a real console-script entry point (no lost executable
bit), explicit user-initiated upgrade, version pinning, and nothing installed
unless the adopter acts. 2026 practitioner guidance prefers `uv tool` over
`pipx` unless `inject`/`--suffix`/`--global` are needed. Rated moderate: the
sources are practitioner comparisons rather than normative, and independence is
thin.

**F16. The `npx`/`uvx` launch-time-resolution pattern is an anti-pattern for
anything persistent.** `[high]` A scan of 42,000+ MCP configurations found 502
instances without version pinning and 448 using auto-install flags that bypass
confirmation. Concrete incidents: `postmark-mcp` (2025-09-25) shipped a
version that BCC'd every outgoing email to an attacker address — notable
because agents processed mail without human review, amplifying exfiltration;
the npm Shai-Hulud worm (2025-09) self-propagated across 500+ packages by
stealing publisher credentials. Neither `npx -y` nor `uvx` produces or checks a
lockfile.

**F17. MCPB bundles do not solve the maintenance problem.** `[moderate]`
`.mcpb` (renamed from `.dxt`; adopted into the MCP project 2025-11-21; manifest
spec 0.3 as of 2025-12-02) documents **no signing, no integrity verification,
and no automated update mechanism** in the bundle format itself. SHA-256
integrity exists at the *registry* layer, not the bundle. Updates are entirely
user-initiated. It buys cross-client one-click install, not upgradability.

**F18. The official MCP Registry is metadata, not a package host.**
`[moderate]` It publishes `server.json` pointing at npm/PyPI/Cargo/NuGet/OCI,
supports `registryType: "pypi"` with `runtimeHint: "uvx"`, and delegates
ownership verification to the underlying registries. It would give a PyPI-based
exporter discoverability, nothing more.

**F19. Copying source into a user's repository is the pattern the ecosystem
moved away from.** `[moderate]` No public incident was found, but the
structural problems are well described and are exactly the ones we measured in
our own installer: no upgrade notification, lost executable permissions, forked
edits diverging silently, no way to audit the installed version. VS Code moved
from bundling to marketplace distribution and Python from `setup.py` copying to
`pipx` for these reasons.

**F20. Opt-in is the safest choice against backlash — but not the majority
practice.** `[moderate]`
(downgraded — .NET CLI, VS Code, JetBrains and Docker Desktop are all opt-out
with disclosure; Go's opt-in reached ~0.06% participation. See also N1 in the
counterpoints: "off unless configured" is not itself consent) The decisive case is the Go toolchain: a
February 2023 proposal to default telemetry on produced sustained backlash, and
Go 1.23 (August 2024) shipped it **opt-in** — the team's own "opt-in means less
useful data" argument was overridden. Homebrew (issues #142, #18479) and
Next.js (issue #23183) carry ongoing pressure for the same reason. Tools
shipping "nothing sent unless an endpoint is configured" — Claude Code,
Buildkite, Dagger, CircleCI — attract no comparable criticism. Dagger
additionally honours the `DO_NOT_TRACK=1` console standard.

**F21. Per-engine export is the overwhelming prevailing architecture.**
`[high]` Argo Workflows has the controller and `argoexec` each independently
read `OTEL_EXPORTER_OTLP_ENDPOINT`; Dagger's engine is itself the emitter with
the CLI as a local consumer; Buildkite's tracing lives in the agent binary with
pipeline-level spans stitched by trace propagation, not routed through a shared
process; Jenkins' exporter is a plugin inside the Jenkins process. No surveyed
project uses a shared telemetry daemon across components, and the Collector
serves as a downstream aggregation hop rather than a shared in-process emitter.
This **confirms the owner's stated default** and is reinforced by OTel's own
API/SDK split. No project was found that adopted a shared emitter and regretted
it, or the reverse.

**F22. Both sides of the structural-versus-configuration guarantee have real
precedent; the no-documented-regret claim does not survive review.**
`[moderate]` (downgraded; core question recorded **do-not-resolve** with a
severity asymmetry — Next.js #43947 shows a bundled sender failing open and
transmitting despite opt-out) Structural
separation is canonical where a package manager exists: OTel's own API package
is zero-dependency and every call is a no-op, with the SDK and each exporter as
separate installs, and the library guidelines name this as the intended model;
Jenkins ships its OTel plugin unbundled, so an instance that never installs it
has no code path to an exporter. Against that, bundled-but-disabled is accepted
practice for single-binary tools — Buildkite, Argo and Dagger all compile the
exporter in and gate it on an endpoint — with deployment simplicity as the
stated reason. **This is the pivotal finding for our § 5.2 question, and it does
not resolve it.** Our situation has a package manager, which favours the
structural route; our delivery unit is a copied file tree, which is neither of
the surveyed shapes.

**F23. `telemetry.md`'s vocabulary and cardinality claims both verify — and one
carries a new risk.** `[high]` The CI/CD semantic conventions define
`cicd.pipeline.result` as exactly `success`, `failure`, `error`, `timeout`,
`cancellation`, `skip`, with **no human-approval or pending-gate value** —
precisely the gap § 5.2 claims, so our `awaiting_input` field is a necessary
extension and the doc's assertion is now evidenced rather than asserted. On
cardinality, the OTel SDK's default limit is 2,000 unique attribute
combinations per metric stream, and practitioner and specification guidance
agree that run-scoped identifiers belong in span and log attributes, never
metric dimensions — confirming § 7's `run_id` rule, and adding **exemplars** as
the blessed bridge from a metric back to one run. The new risk: that
convention is **Release Candidate, not Stable**, so a vocabulary our envelope
borrows can still change upstream. `[inference]` This is a second, independent
argument for versioning the event line.

## Findings — repository mechanism costs

Verified against code, not inferred. Five mechanisms were priced.

**F24. A new user-scope pack touches 17 registration surfaces, 11 of which
normally change.** `[high]` Including `pack.toml` identity and enriched
metadata (`tests/conformance/test_pack_metadata.py:34-50`), a
`.claude-plugin/plugin.json` with a version matching `pack.toml`, a pack
README, marketplace membership (`tools/lint-plugin-membership.py:43-98`), the
literal `PUBLISHED` roster (`tools/lint-plugin-roster.py:30-70`), a guide home
and guide-index entry (`tools/check-guide-index.py:17-67`), the changelog, and
the skill census if it ships a skill. One is a genuine tripwire: adding the
23rd pack requires updating a forbidden-claim literal in
`tools/lint-plugin-route-docs.py:68-82`, whose self-test derives the live
count.

**F25. The user-scope floor rail is install-only, and this defeats
"upgradable".** `[high]` Verified directly: `_deliver_user_scope_floor` has its
sole production call at `install.py:1664`, gated `if plan.scope == "user"`, and
`user-libs`/`adapter-root-bins`/`_deliver_user_scope_floor` appear **nowhere**
in `upgrade.py`. Because floor artifacts are deliberately excluded from
`state.files` so that uninstalling one pack cannot strip another's floor,
uninstall — which iterates only recorded files — also leaves the executable
behind. A new pack shipping an exporter this way would deliver it once and
never update it.

**F26. Extending the floor rail to repo scope breaks Copilot
specifically.** `[high]` `.agentbundle/` is present in `allowed-prefixes.repo`
for claude-code, kiro, kiro-ide, kiro-cli, codex, cursor and gemini, but
Copilot's repo prefixes are `[".agents/skills/", ".github/skills/",
".github/agents/", ".github/hooks/"]` — no `.agentbundle/`, though its *user*
prefixes do include it. A gate flip alone fails there. Separately, ADR-0003
describes `adapter-root-bins` targeting `<repo>/.agentbundle/bin/` at repo
scope while the shipped installer gates it to user scope — a historical
mismatch worth recording either way.

**F27. `[pack.runtime-dependencies]` is a dormant declaration surface.**
`[high]` `pack.schema.json:217-246` defines `ecosystem` ∈
`pypi|npm|cargo|go|homebrew|apt|system`, plus `package`, `version`, `optional`,
`skills`, an `install` command string and `note`. No pack declares it; no
install or runtime code consumes it. It is referenced only by direct-source
validation tests that require direct manifests to *reject* it
(`tests/unit/test_pack_config_api.py:96-132`). The declaration half of the
owner's "install from a registry" idea already exists and is unused.

**F28. Consented installation is permitted policy, not forbidden.** `[high]`
The canonical rule is `guides/_shared/how-to/author-a-skill.md:104`: "Tier 1 is
mandatory and the default; Tier 2 is allowed but never the default; Tier 3 is
banned." Tier 2 admits a pinned, non-root, consented install through an
already-detected manager on a detect → install → re-verify cycle; Tier 3 is
silent auto-install. The same section states **"Prefer stdlib over a pip
dependency"** — which settles F1-F5 in favour of the stdlib sender as
repository authority, not preference. `agentbundle` has reusable consent
machinery in `confirm_or_refuse` (`commands/_common.py:371-410`), but it was
built for destructive lifecycle operations and `install --yes` currently covers
cleanup and upgrade handoff; reusing that flag for package acquisition would be
a surprising authority expansion. No production install path invokes pip, npm,
uv or pipx today.

**F29. A local transformer needs no new security boundary and has a
precedent.** `[moderate]` `.loop-run/` is already gitignored at
`.gitignore:104` and by `loop-engine.py:1223`, so a second file there adds no
new ignore surface. Writing it is not itself a trust-boundary change, but
parsing possibly-malformed JSONL and creating a second durable serialization is
a new data-flow and persistent-representation surface, so review scopes to
input bounds, path confinement, safe replacement and privacy — with no SSRF,
credential or supply-chain module. The closest repository precedent is
`packs/converters/.apm/skills/msg-to-markdown/scripts/convert.py`, which reads
a local file, converts it to another local representation, writes through an
output-path confinement guard, treats its source as untrusted and applies
resource ceilings.

**F30. Outbound HTTP hardening exists in the repository but cannot be reused by
pack code, and its policy is too strict anyway.** `[high]`
`agentbundle/https_catalogue.py` implements an HTTPS-only opener with no
`HTTPHandler`, an origin-locking redirect handler that rejects cross-origin
redirects before the request is sent, user-info rejection and no cross-origin
token forwarding. Two problems. It lives in the installer package, and
`telemetry.md:47-49` forbids pack code importing installer libraries — so a
pack-resident sender must duplicate the hardening. And HTTPS-only refuses
`http://localhost:4318`, the most common OTLP developer target, so any sender
needs a deliberate loopback carve-out. `[inference]` This is an argument for
the sender living in `packages/` rather than in a pack.

## Mechanism comparison

The final column was originally "Meets the ask", which encoded a judgement
about owner intent rather than a fact. It is replaced by a factual property:
whether the mechanism delivers telemetry to a backend **without requiring
adopter-operated infrastructure**. Mapping that to intent is the owner's call.

| Mechanism | Sends? | § 5.2 guarantee | Upgradable today | Repo cost | Delivers without adopter-run infra |
|---|---|---|---|---|---|
| M1 separate user-scope pack | yes | structural | no — but this is a pre-existing rail defect (F25, corrected), not M1's | 11-17 surfaces | yes |
| M2 extend floor rail to repo scope | yes | configuration, if used to put the sender in core | no | highest; breaks Copilot (F26) | yes |
| M3a PyPI distribution, declared and reported | yes | structural | yes (`uv tool upgrade`) | medium-high; activates F27 | yes |
| M3b PyPI distribution, installer performs install | yes | qualified structural | yes | very high; new installer authority | yes |
| M4 document a Collector only | no | structural | n/a | very low | no — Collector is adopter-run |
| M5 local transformer, never sends | no | strongest pack-side | yes (normal primitive) | low-medium | no — Collector is adopter-run |

Two properties cut across the table and are not columns because they apply to
every row. **Disclosure** is required regardless of mechanism (N1): "off unless
configured" is a behaviour guarantee, not consent. And **verification** requires
a real Collector round-trip for any row that sends, because a malformed payload
returns HTTP 200 with no signal (counterpoints F1/F2).

## Known unknowns

- **Known-unknown:** whether our nested `budgets` object survives `filelog`'s
  `json_parser` as nested attributes or is flattened or stringified. The
  receiver docs do not state the behaviour for nested objects and practitioner
  reports vary. Would be closed by: one local run of `otelcol-contrib` against
  a real `events.jsonl` with a debug exporter.
- **Known-unknown:** whether the `file_storage` key-length defect
  (contrib issue #44039, 2025) affects paths of the form
  `<repo>/.loop-run/events.jsonl`. Would be closed by: reading the issue's
  reproduction conditions against a realistic path length.
- **Known-unknown:** whether Datadog and New Relic actually reject OTLP/HTTP
  JSON for logs or merely fail to document it. Would be closed by: a vendor
  support statement, or one probe per vendor against a test endpoint.
- **Known-unknown:** the real per-invocation cost of the exporter on a
  developer machine. We have an owner-supplied 156 ms figure for the rejected
  hook route and no measurement for any mechanism here. Would be closed by:
  timing a prototype over a realistic `events.jsonl`.
- **Unknowable:** whether an adopter who installs an exporter pack and never
  configures it is meaningfully safer than one who has a dormant exporter
  inside core. Why not: the difference is a claim about adopter trust, not
  about behaviour — both send nothing, and no evidence settles which promise a
  team values. F22 shows the field split on it with no documented regret in
  either direction. This belongs to the owner, not to research.
- **Unknowable:** whether the CI/CD semantic conventions will change
  `cicd.pipeline.result` before reaching Stable. Why not: the outcome is in the
  future. It is the reason to version the line, not something to wait for.

## Moderator pass

The highest-signal unused material was OTel's `${VAR:-default}` substitution
(F8) and the exemplars mechanism (F23), neither of which was in the original
question. F8 changes the § 5.3 configuration design by supplying a third
precedence option; exemplars matter only if anyone later derives metrics from
these lines. One further query was issued on the File Exporter format, which
produced F14 and the M5 mechanism — the single largest change to the option set
in this survey.

## Citations

Standards and specifications (primary): OTLP Specification 1.11.0;
`opentelemetry-proto` `docs/specification.md`, `examples/logs.json` and
CHANGELOG (0.20.0, 2023-06-06); specification PR #911, issues #1957, #3752 and
discussion #3554; OTel declarative-configuration and SDK-environment-variable
pages; `opentelemetry-configuration` repository and
`otel-sdk-migration-config.yaml`; OTel library guidelines; CI/CD semantic
conventions (`cicd-spans`, RC); OTel specification status page; Collector
`otlpreceiver` and `filelogreceiver` READMEs; `filestorage` extension README;
contrib issues #3071 and #44039; OTel File Exporter specification; `ocb`
documentation; agent deployment-pattern page; MCP Specification 2026-07-28; MCPB
manifest 0.3 (2025-12-02) and the 2025-11-20 adoption post; MCP Registry
`server.json` (2025-12-11).

Incidents and reversals (primary): Snyk on `postmark-mcp` (2025-09-25); npm
Shai-Hulud coverage (2025-09); `golang/go` discussion #58409 (2023-02) and the
Go 1.23 opt-in reversal (2024-08); Homebrew issues #142 and #18479; Next.js
issue #23183; `opentelemetry-go` issue #1924; Claude Code issue #46519;
GitHub Actions SHA-pinning changelog (2025-08-15).

Implementations and vendor documentation (secondary): `canonical/operator`
`tracing/ops_tracing/_export.py`; `dimaqq/otlp-json`;
`opentelemetry-exporter-otlp-proto-http` 1.44.0 on PyPI and its
`pyproject.toml`; Jenkins OpenTelemetry plugin; Argo Workflows telemetry;
Buildkite, CircleCI, Dagger, Harness and GitLab observability docs; Honeycomb,
Elastic, Datadog, New Relic, Axiom, Dynatrace and Grafana Alloy OTLP pages;
.NET CLI telemetry; `uv tool`/`pipx` comparisons.

Repository evidence (primary, this repo at `ec6b94f91`): paths and line numbers
are cited inline in F24-F30.
