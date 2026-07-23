# `jira-team-status` — worked examples

## Example 1: Mixed sprint snapshot with pick-up hand-off

**Invocation:** "Show team sprint status for the PLATFORM team in sprint 8, and help me pick a story."

**Skill behaviour:**

1. Runs `jira: check` → exit 0.
2. Detects `git remote -v` → `https://github.com/acme/platform-core` → **Invocation repo: `github.com/acme/platform-core`**.
3. Runs:
   ```
   jira: search "project = PLATFORM AND sprint = 'Sprint 8' AND statusCategory != Done"
         --fields "summary,description,issuetype,status,priority,labels,customfield_*"
         --limit 100
   ```
4. Receives 8 stories. Applies pre-check, then Q1–Q5 scoring.

**Pre-check:**
- PLATFORM-205: description = `!arch-diagram.png!` → **Blocked** (image-only).

**Scoring (7 remaining stories):**

| Key | Q1 | Q2 | Q3 | Q4 | Q5 | Tier | Complexity |
|---|---|---|---|---|---|---|---|
| PLATFORM-201 | ✓ | ✓ | ✓ | ✓ | ✓ (1pt) | A | Quick |
| PLATFORM-202 | ✓ | ✓ | ✓ | ✓ | ✓ (2pts) | A | Quick |
| PLATFORM-206 | ✓ | ✓ | ✓ | ✓ | ✓ (4pts) | A | Standard |
| PLATFORM-207 | ✓ | ✓ | ✓ | ✓ | ✓ (3pts) | A | Standard |
| PLATFORM-208 | ✓ | ✓ | ✓ | ✓ | ✓ (8pts) | A | Involved |
| PLATFORM-203 | ✓ | ✓ | ✓ | ✗ (Q4: pending sign-off from infra-lead) | ✓ | B | — |
| PLATFORM-204 | ✗ (Q1: "investigate options for") | ✗ | ✗ | ✗ | unknown | C | — |

**Output:**

```
Invocation repo: github.com/acme/platform-core (detected)
Sprint scope: project = PLATFORM AND sprint = "Sprint 8"
Stories fetched: 8
```

---

### §1 — Agent-ready (Tier A)

Stories ready to hand to an agent or engineer with no follow-up needed.

**Quick** (≤ 2pts — grab if you have 1–2 hours)

| Key | Summary | Priority | Complexity | Invocation repo match? |
|---|---|---|---|---|
| PLATFORM-201 | Remove deprecated `FeatureFlags.LEGACY_AUTH` constant | High | Quick | Yes |
| PLATFORM-202 | Update `platform-core` agent frontmatter to claude-sonnet-5 | Medium | Quick | Yes |

**Standard** (3–5pts — grab if you have half a day)

| Key | Summary | Priority | Complexity | Invocation repo match? |
|---|---|---|---|---|
| PLATFORM-206 | Add structured logging to the credential rotation hook | High | Standard | Yes |
| PLATFORM-207 | Retrofit telemetry onto the renamed `ce-ai-enablement-pack` | Medium | Standard | Yes |

**Involved** (>5pts — grab if you have a full day; consider pairing)

| Key | Summary | Priority | Complexity | Invocation repo match? |
|---|---|---|---|---|
| PLATFORM-208 | Migrate CI pipeline from Jenkins to GitHub Actions | High | Involved | Yes |

---

### §2 — Parallel batching candidates

Can run concurrently: **PLATFORM-201, PLATFORM-202, PLATFORM-206** (distinct file scopes; no dependency language between them).

---

### §3 — Gated (Tier B)

| Key | Summary | Gate (what must resolve first) | Owner hint |
|---|---|---|---|
| PLATFORM-203 | Enable mTLS for service-to-service calls | Q4: sign-off from infra-lead on cert provisioning plan | @infra-lead |

---

### §4 — Needs shaping (Tier C + Blocked)

| Key | Summary | Tier | Specific gap |
|---|---|---|---|
| PLATFORM-204 | Investigate options for distributed tracing | C | Q1: "investigate" = discovery work; Q2: no repo named; Q3: no ACs |
| PLATFORM-205 | !arch-diagram.png! | Blocked | Image-only description — no text content |

These 2 stories need shaping before they can be executed.

---

```
Sprint snapshot: 8 total.  Agent-ready: 5 (Quick: 2, Std: 2, Inv: 1).
Gated: 1.  Need shaping: 2.  Invocation repo: github.com/acme/platform-core.
```

---

### Pick-up hand-off

**Option A — Start delivery:**

> "Ready to start delivery? Suggested: **PLATFORM-201** — Remove deprecated `FeatureFlags.LEGACY_AUTH` constant (Quick, High priority, scope matches invocation repo).
> [yes / pick another / skip]"

**User:** yes

> "PLATFORM-201 is a Task — routing to `new-spec` to scope the delivery.
> Starting a `new-spec` session for PLATFORM-201: Remove deprecated `FeatureFlags.LEGACY_AUTH` constant."
> → `new-spec` skill loads with PLATFORM-201 context.

**Option B — Shape a story:**

> "Want to shape a story into something executable? Suggested: **PLATFORM-204** — Investigate options for distributed tracing (Tier C; fails Q1, Q2, Q3).
> [yes / pick another / skip]"

**User:** (if they had chosen `yes` for Option B instead)

> "Here is PLATFORM-204's current content:
>
> **Summary:** Investigate options for distributed tracing
> **Description:** We should look into what distributed tracing solutions exist and which ones are compatible with our stack.
> **Acceptance Criteria:** (none)
>
> This story fails Q1 (discovery language: "investigate"), Q2 (no specific repo or service named), and Q3 (no ACs).
>
> Let's rewrite it together:
>
> **Q1 — What is the specific code/config/doc change?** e.g., 'Add OpenTelemetry tracing to the `platform-core` API gateway'
> What should the summary say?"

→ (Collaborative rewrite continues for each failed question.)

After all fields are addressed:

> "Here is the complete rewritten payload:
>
> **Summary:** Add OpenTelemetry tracing to the `platform-core` API gateway
> **Description:** Instrument the API gateway in `github.com/acme/platform-core/services/api-gateway` with OpenTelemetry. Configure the OTLP exporter to forward spans to the existing Jaeger instance at `jaeger.infra.acme.internal`.
> **Acceptance Criteria:**
> - [ ] `api-gateway/main.go` initialises an OTLP trace provider on startup.
> - [ ] Incoming HTTP requests emit a root span with `http.method`, `http.route`, and `http.status_code` attributes.
> - [ ] Spans are visible in Jaeger UI for a test request.
>
> **issuetype:** Task (unchanged)
>
> Update PLATFORM-204 in Jira with this rewritten content? [yes / no]"

**User:** yes

> Running: `jira: update-issue PLATFORM-204 --field summary="Add OpenTelemetry tracing to the platform-core API gateway" --field description="Instrument the API gateway ... Acceptance Criteria:\n- Initialises OTLP trace provider\n- Emits root spans\n- Visible in Jaeger UI"`
>
> Updated. PLATFORM-204 now passes Q1, Q2, and Q3. It will appear in §1 on the next sprint status run.

---

## Example 2: No Tier A stories — shaping-only hand-off

**Invocation:** "Team sprint status for ALPHA sprint 3."

**Skill behaviour:**

1. `jira: check` → exit 0.
2. `git remote -v` → `https://github.com/acme/alpha-service` → **Invocation repo: `github.com/acme/alpha-service`**.
3. Fetches 5 stories; all fail scoring.

**Output:**

```
Invocation repo: github.com/acme/alpha-service (detected)
Sprint scope: project = ALPHA AND sprint = "Sprint 3"
Stories fetched: 5
```

---

### §1 — Agent-ready (Tier A)

None in this scope.

---

### §2 — Parallel batching candidates

(Omitted — no Tier A stories.)

---

### §3 — Gated (Tier B)

| Key | Summary | Gate | Owner hint |
|---|---|---|---|
| ALPHA-031 | Deploy new auth middleware to staging | Q4: security sign-off from @sec-lead required before staging deploy | @sec-lead |

---

### §4 — Needs shaping (Tier C + Blocked)

| Key | Summary | Tier | Specific gap |
|---|---|---|---|
| ALPHA-028 | Make the API faster | C | Q1: vague; Q2: no endpoint named; Q3: no ACs; Q5: no size signal |
| ALPHA-029 | Coordinate with mobile team on the new login flow | C | Q1: coordination work, not a code change |
| ALPHA-030 | !wireframes-v2.png! | Blocked | Image-only description |
| ALPHA-032 | Address all technical debt this sprint | C | Q5: too large for one PR (no story-points; 400+ word description) |

These 4 stories need shaping before they can be executed.

---

```
Sprint snapshot: 5 total.  Agent-ready: 0 (Quick: 0, Std: 0, Inv: 0).
Gated: 1.  Need shaping: 4.  Invocation repo: github.com/acme/alpha-service.
```

---

### Pick-up hand-off

No agent-ready stories in this scope — shaping §4 stories is the fastest path to Tier A.

**Option B — Shape a story:**

> "Want to shape a story into something executable? Suggested: **ALPHA-028** — Make the API faster (Tier C; fails Q1, Q2, Q3, Q5).
> [yes / pick another / skip]"

Option A is not offered (§1 is empty).
