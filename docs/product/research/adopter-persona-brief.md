# adopter-persona — brief

**Bottom line:** The Level B pack set has two primary adopter pathways —
enterprise customers reached through forward-deployed engineer practitioners
(FDE-mediated) and solo software engineers working independently. These
pathways fail for opposite reasons: FDE-mediated adoption fails at the handoff
moment (post-FDE vocabulary exposure, ~90-day credential expiry, governance
maintenance); solo adoption fails at the activation window (60–80% of
developer-tool signups never reach activation; 68% cite too much setup time).
Five cross-segment design changes address both simultaneously. The enterprise
rollout playbook needs three tracks, not two: a well-resourced FDE track, a
solo self-serve track, and a mid-market unsupported-enterprise track that is
currently the highest churn risk.

---

## What the evidence shows

- **Four dimensions jointly determine whether a cold adopter reaches first
  value: vocabulary, visible prerequisites, safe-action posture, and result
  findability.** These recur independently across W3C accessibility guidance,
  Diátaxis tutorial structure, IBM's progressive-disclosure model, Nielsen
  usability heuristics, and the Level B pack portfolio audit.
  [high — ≥5 independent sources; segmentation survey synthesis]

- **FDE-mediated adoption achieves 60–80% automation rates versus ~20% for
  self-service — a structural, not marginal, difference.** The primary variable
  is whether the client receives a human specialist during deployment, not the
  model, prompt, or vendor.
  [moderate — SaaStr practitioner analysis; consistent across fde.academy,
  Baseten engineering blog, Everest Group; no RCT-level evidence]

- **FDE deployment absorbs installation friction but not vocabulary transfer.**
  The dominant post-FDE failure modes are: knowledge vacuum at handoff, custom-
  integration orphaning, silent system degradation, and escalation-chain
  breakdown — not credential misconfiguration during the engagement itself.
  [high — Palantir Foundry Phase 3 documentation (primary); corroborated by
  fde.academy, Webvillee, Everest Group]

- **Atlassian OAuth refresh tokens expire after 90 days of inactivity; Figma
  OAuth access tokens expire after 90 days unconditionally.** Every FDE-deployed
  atlassian or figma integration will require client-side re-authentication
  before or shortly after the first 90-day post-engagement window.
  [high — developer.atlassian.com OAuth 2.0 3LO documentation;
  developers.figma.com OAuth apps documentation]

- **60–80% of developer-tool signups never reach activation; 68% cite "too much
  setup time" as the reason.** The industry TTFHW (time to first working value
  without external help) target is under 15 minutes; the first meaningful action
  within 10 minutes produces a 3–4× conversion lift.
  [moderate — daily.dev developer onboarding research; directional signal
  consistent across Stack Overflow 2025 and ICSE 2024; no controlled study]

- **AI agent toolkit adoption (30.9% regular use) significantly lags coding-
  assistant adoption (70%+).** A solo engineer arriving at Agent Ready Repo
  may be comfortable with coding assistants but is a first-time agent-toolkit
  adopter. Onboarding must bridge chat-assistant vocabulary to pack-activation
  vocabulary within the activation window.
  [high — Stack Overflow Developer Survey 2025, N=49,000+]

- **For solo engineers doing client-facing work, output ambiguity carries
  reputational cost that raises the adoption threshold.** Freelancers lack
  organisational support and depend on client positive feedback; unreliable
  tool output is a direct professional risk, not just a personal frustration.
  [moderate — Dolata, Lange, Schwabe, ICSE 2024, N=52 freelancers; Skywork.ai
  2025 survey; consistent directional signal, qualitative]

- **The three expert walkthroughs (architect, figma, governance-extras) at
  baseline revision `b43ae2e` identified five categories of mechanical defect:
  invalid install commands, vocabulary before outcomes, missing prerequisite
  order, ambiguous mutation status, and incomplete receipts.** All identified
  defects were mechanically addressed at revision `d9ebec99`; verified by
  repository diff inspection.
  [high — mechanical fix verification; direct repository inspection]

- **product-strategy is standalone — no product-engineering dependency.**
  `pack.toml` declares `prerequisites = []`; the starter task (`write-prfaq`)
  is explicitly defined with a ready-to-use prompt. Highest first-value
  clarity of any Level B pack.
  [high — direct `pack.toml` inspection]

---

## Segment profiles

### Segment A — enterprise customer via FDE practitioner

The FDE installs, configures credentials, and establishes governance
conventions during the engagement. The client organisation is the end adopter.
The FDE absorbs installation friction; the client inherits vocabulary barriers
and credential lifecycle without direct support.

**High-priority packs for FDE deployment:** atlassian and figma (credential
lifecycle risk); governance-extras and user-guide-diataxis (governance
vocabulary recurs in every artifact the client maintains post-handoff).

**Critical handoff requirements:** (1) re-authentication documentation for
atlassian and figma (step-by-step, client-legible, covering the ~90-day
expiry window); (2) pre-exit vocabulary transfer — the FDE must not close the
engagement until the client has demonstrated independent artifact-type
selection (ADR vs. RFC; Diátaxis kind); (3) one client-independent workflow
run before engagement close.

**Third track — unsupported mid-market enterprise.** The FDE model scales only
to roughly 5,000+ employee organisations. Mid-market and less-resourced
enterprise clients must self-serve packs with enterprise-grade complexity.
This population — sold on FDE-level outcomes, given self-service documentation —
is the highest churn risk in the Level B set. The rollout playbook must address
it as a distinct track, not as a variant of either the FDE or solo tracks.

### Segment B — solo software engineer

The solo engineer is installer and end user in one person. Time budget is the
primary binding constraint; motivation and available time decay faster than
vocabulary barriers.

**High-friction packs:** atlassian and figma (full credential self-service; no
admin to call); governance-extras (highest vocabulary load; first repository
write is high-anxiety).

**Critical solo requirements:** (1) prerequisites at the decision point before
the attempt — not as error messages; (2) outcome-first framing at every pack
entry — vocabulary after first value, not before; (3) explicit artifact status
in every receipt (chat-only OR exact path, never implied); (4) for client-facing
use: output confidence tags and explicit mutation status in every receipt.

**Low-friction entry point for solo adoption:** product-strategy (`write-prfaq`)
is the best-positioned Level B pack for a solo first experience. No credential,
no configuration, explicit starter prompt, PRFAQ output is immediately shareable
with a client or colleague.

---

## Pack-level design implications

Five design changes address both segments:

1. **Prerequisites at the decision point, not on failure** — converters (runtime),
   atlassian (admin pre-config), figma (PAT/OAuth). Affects both segments for
   opposite reasons: FDE client has no FDE to call; solo engineer burns the
   activation budget.

2. **Outcome-first vocabulary at every pack entry point** — plain-language
   outcome label before internal terminology. Affects: all Level B packs.
   Post-fix improvements verified for architect, figma, governance-extras.

3. **Explicit artifact status in every receipt** — chat-only OR exact path,
   stated, never implied. Affects: architect (concept stop), converters
   (output file), figma (render vs. remote), governance-extras (ADR/RFC path
   and index).

4. **Credential lifecycle section in atlassian and figma documentation** —
   re-authentication steps (trigger, steps, token storage location) as a
   named, findable section, not buried in prerequisites. Required as FDE
   handoff artefact; required as inline self-service for solo.

5. **Mutation status stated, not implied** — "No Figma changes made" / "no
   Jira items modified" in every read-only receipt. Post-fix verified for
   figma; atlassian requires equivalent treatment.

---

## Known unknowns

- **Known-unknown:** Does a non-technical enterprise client trust and act on
  the governance-extras preview-confirm flow without external reassurance?
  The mechanical fix (rev `d9ebec99`) documented the cues; whether a first-time
  adopter uses them correctly is unverifiable without participant observation.
  Would be closed by: a moderated first-use session with a non-technical
  governance-extras adopter. Until closed: the P5 governance-extras build AC
  should include a usability check; the rollout playbook should recommend
  facilitated first use.

- **Known-unknown:** What proportion of Level B deployments are FDE-mediated
  versus self-service? No activation or deployment-pathway data exists.
  Would be closed by: deployment telemetry or FDE practitioner survey.

- **Known-unknown:** Does the unsupported mid-market enterprise segment require
  a distinct pack subset, a distinct onboarding flow, or both? The segment is
  identified but not characterised in detail. Would be closed by: FDE
  practitioner interviews + mid-market self-serve attempt sessions.

- **Unknowable:** Which provisional segment labels adopters will self-identify
  with before experiencing the product. Segment identity is behavioural and
  contextual; self-identification cannot substitute for observed task behaviour.

- **Unknowable:** Whether the five-posture model will remain stable after pack
  designs change in response to these findings. The model is inferred from
  documentation and secondary research, not from observed behaviour; it will
  require revision as the product evolves.
