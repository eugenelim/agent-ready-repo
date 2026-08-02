# Comparison matrix — adopter-persona

Two primary adopter segments for the Level B pack set, compared across the
dimensions that determine whether they reach first value and sustain use.

---

## Segment profiles

### Segment A — enterprise customer via FDE practitioner

A technically proficient forward-deployed engineer installs and configures the
toolkit on behalf of an enterprise client. The FDE is the installer; the client
organisation is the end adopter. The FDE absorbs installation friction and
credential setup, but vocabulary barriers, token lifecycle, and governance
maintenance land on the client unaided after the engagement ends. The CoE
the FDE hands off to — if one exists at all — must include named role owners
who are long-term domain participants, not rotational staff.

The binding constraint is **handoff quality**: whether the client can operate
the toolkit independently after the FDE exits. The FDE model achieves 60–80%
automation rates in mature deployments; self-service achieves ~20%. The gap
is structural. [moderate — SaaStr practitioner analysis; consistent across
fde.academy, Baseten, Everest Group]

### Segment B — solo software engineer

A technically proficient developer installs and uses the toolkit for their own
side projects or to assist a colleague or client with a business problem. They
are installer and end user in one person, with no team support to absorb output
uncertainty or troubleshoot credential failures. The binding constraint is
**time budget**: 60–80% of developer-tool signups never reach activation;
68% cite "too much setup time" as the reason. The industry target for time to
first working value (TTFHW) is under 15 minutes. [moderate — daily.dev
practitioner research; consistent with Stack Overflow 2025 and ICSE 2024]

For solo engineers doing client-facing work, a second constraint overlays the
time budget: **reputational cost of uncertain output**. Ambiguous results or
unclear mutation status that would be absorbed in a team context carry direct
professional cost when the audience is a paying client. [moderate — ICSE 2024,
N=52 freelancers; Skywork.ai 2025 survey]

---

## Dimension comparison

| Dimension | FDE-mediated (Segment A) | Solo engineer (Segment B) |
|---|---|---|
| **Activation failure mode** | Vocabulary exposure post-handoff: the FDE absorbed install friction, but pack vocabulary (ADR, RFC, OAuth scope, Diátaxis type) lands on the client unaided after exit | Activation window exceeded: prerequisite friction, vocabulary, or configuration steps consume the sub-15-min budget before first value lands; 60–80% drop-off rate |
| **Prerequisite timing** | FDE configures prerequisites during the engagement; client must re-authenticate (~90-day token expiry for atlassian and figma) without FDE support | Prerequisites must surface at the decision point before the attempt — not as error messages. Solo engineer is their own IT department; a blocking error mid-task triggers abandonment |
| **First-value boundary** | First value = client produces a result independently after FDE exit. Chat-only vs. exact-path ambiguity and wrong artifact type selection (ADR vs. RFC, Diátaxis kind) are the two most common post-handoff failure points | First value = reaching a useful result within the activation window. Stop-at-concept ambiguity (is this in chat or saved?) is the primary boundary-marking failure across conversational-shaper packs |
| **Credential lifecycle** | FDE must document re-authentication steps as a mandatory handoff artefact. Atlassian OAuth refresh tokens expire after 90 days of inactivity; Figma OAuth access tokens expire after 90 days unconditionally. A client who is slow to adopt after FDE exit may hit expiry before their first independent use | Solo engineer must self-serve re-authentication from inline guidance alone. If the token-regeneration steps are not self-contained inline, there is no support channel. Same 90-day expiry windows apply |
| **Sustainability mechanism** | CoE role staffing + pre-exit vocabulary transfer + one client-independent run before FDE closes the engagement. Governance packs require the client to make the right vocabulary choice every time post-handoff — this is a recurring, not a one-time, sustainability requirement | Peer discovery (78% primary channel) + documentation depth signal (5+ pages = 340% conversion lift) + pragmatic task-test on a real problem. Client-facing work raises the bar: output confidence and explicit mutation status are not cosmetic for this sub-segment |

---

## Pack groupings by segment risk

### High FDE deployment priority — packs where handoff quality determines sustained adoption

**atlassian, figma** — Credential setup is FDE-handled; client must re-authenticate
independently after ~90-day token expiry. The re-auth documentation gap is a
confirmed design requirement, not a marginal edge case. [high — official
Atlassian and Figma OAuth documentation]

**governance-extras, user-guide-diataxis** — Governance vocabulary (ADR, RFC,
amendment/errata; Diátaxis type selection) appears in every artifact the client
must extend post-handoff. Wrong type selection is a recurring failure point.
The pre-exit vocabulary transfer must include at least one client-performed
write before the FDE closes. [moderate — expert walkthrough + mechanical fix
verification; post-fix repairs verified at rev `d9ebec99`]

### High solo activation friction — packs where the activation window is most at risk

**atlassian, figma** — Full credential self-service from a standing start. No
admin to call; OAuth/token setup must be self-sufficient from inline guidance.
[moderate — figma expert walkthrough; mechanical fix verification]

**governance-extras** — Highest vocabulary load of any Level B pack. Anxiety
around a first repository write is the primary friction point. Preview-confirm
flow verified in documentation (post-fix); whether a first-time adopter trusts
it without moderator support is the one remaining unverifiable confidence gap.
[moderate — governance-extras expert walkthrough; mechanical fix verification;
client confidence unverifiable without participant observation]

### Low friction for both segments

**converters, desk-research** — No credential, no SaaS admin. Low FDE overhead
(likely written instructions rather than a live session). Solo activation
risk is limited to runtime prerequisites surfacing on failure rather than
before the attempt. [moderate — segmentation survey; pack coverage table]

**product-strategy** — Declared standalone with no product-engineering
dependency (`prerequisites = []` in `pack.toml`). Starter task (`write-prfaq`)
is explicitly defined with a ready-to-use prompt. Clearest first-value path of
any Level B pack. [high — direct pack.toml inspection]

### Medium friction — vocabulary or runtime, but no credential

**architect, experience-design, product-engineering** — Conversational entry;
no credential. Vocabulary barriers (C4, RFC/ADR, forked-context; JTBD, screen
brief; work-loop, Gate: Idea) are present but manageable with outcome-first
framing. Post-fix improvements (rev `d9ebec99`) address the Architect
vocabulary and receipt gaps. [moderate — expert walkthrough + mechanical fix
verification]

---

## Cross-segment design requirements

Five requirements hold for both segments — their rationale differs, but the
design change is identical:

1. **Prerequisites at the decision point, not on failure.** FDE rationale:
   the client who hits a blocking error post-handoff has no FDE to call.
   Solo rationale: a blocking error mid-attempt burns the activation budget.
   Implementation: "Do you have X?" before the attempt, not as an error
   message. Affects: converters (runtime), atlassian (admin pre-config),
   figma (PAT/OAuth).

2. **Outcome-first vocabulary.** FDE rationale: vocabulary barriers land on
   the client unaided post-handoff; plain outcomes reduce maintenance calls.
   Solo rationale: vocabulary exploration consumes the activation window.
   Implementation: plain-language outcome label before internal pack
   terminology at every entry point. Affects: all Level B packs.

3. **Explicit artifact status in every receipt.** FDE rationale: the client
   must be able to locate what the FDE produced. Solo rationale: uncertainty
   about whether a result was saved or is chat-only triggers a re-run.
   Implementation: chat-only OR exact path, stated in the receipt — never
   implied. Affects: architect (concept), converters (output file), figma
   (render vs. remote), governance-extras (ADR/RFC path + index).

4. **Credential lifecycle documentation.** FDE rationale: ~90-day token expiry
   is a guaranteed post-handoff event for every atlassian and figma deployment.
   Solo rationale: self-service re-authentication with no support channel.
   Implementation: a re-authentication section (trigger, steps, token storage)
   in atlassian and figma pack documentation — not optional appendix material.

5. **Mutation status stated, not implied.** FDE rationale: enterprise clients
   using connected-system packs in a governance context cannot assume no
   remote change without an explicit statement. Solo rationale: client-facing
   use has reputational cost if a "read" session is ambiguous. Implementation:
   "No Figma changes made" / "no Jira items modified" in every read receipt.
   Affects: atlassian, figma. Post-fix verified for figma; atlassian requires
   the same treatment.

---

## Synthesis verdict

The two segments are not alternatives to the five-segment posture model — they
are a layer above it. The FDE-mediated pathway and the solo pathway explain
*how an adopter arrives* at a pack; the five postures explain *what they need
once they're there*. Both framings are required for the P5 persona, the
live-demo design, and the enterprise rollout playbook.

**The enterprise rollout playbook needs three tracks, not two.** The well-resourced
enterprise (FDE-mediated) track and the solo self-serve track are defined by
the corpus. The mid-market or less-resourced enterprise track — too small for
FDE support, too complex for unassisted self-service — is the highest churn
risk and must be named as a distinct design concern in the rollout playbook,
even if its detailed design is deferred.

**Governance-extras write-confidence is the one remaining unresolvable gap.**
The mechanical fix (rev `d9ebec99`) documented the preview-confirm flow; the
expert walkthrough confirmed the cues exist. Whether a non-technical client
trusts the preview and proceeds without external reassurance is unverifiable
without participant observation. The P5 governance-extras build AC should
include a usability check; the rollout playbook should flag this as a
facilitated first-use recommendation.
