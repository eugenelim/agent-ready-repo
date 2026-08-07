---
type: capability-map
slug: acme-crm
date: 2026-07-01
bet-source: docs/product/shaping/acme-crm/bet.md
vision: A mid-market CRM where company relationship graphs and pipeline intelligence replace flat contact management, so sales teams win buying committees, not just contacts.
---

# Capability Map: Acme CRM

## Disposition vocabulary

| Term | Definition |
|------|-----------|
| **Build** | Internal development; team owns full lifecycle; Genesis or Custom-built stage; core to competitive differentiation. |
| **Buy** | Commercial licence or SaaS subscription; Product or Commodity stage; standard function not worth building. |
| **Partner** | Co-developed with an external partner or contract firm; mid-maturity; external expertise accelerates delivery under shared governance. |
| **Adopt** | Open-source or open-standard solution; minimal customisation required. Distinct from Buy: no licence cost, but carries an ongoing maintenance obligation. |

---

## Customer Data

Stores, enriches, and models company and contact data as the foundation for all
relationship and pipeline reasoning.

| Id | Capability | Description | Wardley Stage | Strategic Criticality | Disposition | Dependencies |
|----|-----------|-------------|--------------|----------------------|-------------|-------------|
| company-graph | Company Relationship Graph | Models companies, subsidiaries, and buying committees as a typed graph enabling cross-contact pipeline reasoning. | Custom-built | Differentiating | Build | — |
| contact-store | Contact Storage | Stores individual contacts with standard fields (name, email, role, company). | Commodity | Parity | Buy | — |
| data-enrichment | Data Enrichment | Augments contact and company records with public data (firmographics, technographics) via open data APIs. | Product | Parity | Adopt | contact-store |

## Pipeline & Sales Intelligence

Manages deals, scoring, and workflow automation across the pipeline.

| Id | Capability | Description | Wardley Stage | Strategic Criticality | Disposition | Dependencies |
|----|-----------|-------------|--------------|----------------------|-------------|-------------|
| pipeline-engine | Pipeline Engine | Tracks deals through configurable stages; supports multi-stakeholder opportunities linked to the company graph. | Custom-built | Differentiating | Build | company-graph |
| lead-scoring | Lead Scoring | Derives opportunity scores from activity signals and company graph proximity; surfaces at-risk and high-momentum deals. | Custom-built | Differentiating | Build | company-graph, pipeline-engine |
| workflow-automation | Workflow Automation | Triggers follow-up tasks and notifications based on deal-stage transitions and inactivity rules. | Product | Parity | Buy | pipeline-engine |

## Communication & Engagement

Captures and surfaces customer interaction history to inform pipeline decisions.

| Id | Capability | Description | Wardley Stage | Strategic Criticality | Disposition | Dependencies |
|----|-----------|-------------|--------------|----------------------|-------------|-------------|
| engagement-timeline | Engagement Timeline | Aggregates all touchpoints (email, call, meeting) into a per-company/contact timeline visible from the pipeline view. | Custom-built | Differentiating | Build | contact-store |
| email-delivery | Email Delivery | Sends transactional and sequence emails from the CRM; standard SMTP/API delivery. | Commodity | Utility | Adopt | — |
| call-logging | Call Logging | Records and transcribes inbound and outbound calls; links to contacts and deals. | Product | Parity | Buy | contact-store |
| sms-outreach | SMS Outreach | Sends time-sensitive sales follow-ups and meeting reminders via SMS at the moment of highest buyer intent. | Commodity | Differentiating | Build | engagement-timeline |

> ⚠ **Strategic tension flagged:** `sms-outreach` is Commodity-stage but rated Differentiating — SMS delivery infrastructure is commoditised (Twilio, AWS SNS). The PE team acknowledged and accepted: the differentiation is in *timing logic* (triggered by engagement-timeline signals), not the SMS transport layer itself. Build wraps commodity transport; the custom scheduling and signal-to-send logic is what differentiates.

---

## Tensions reviewed

| Capability Id | Wardley Stage | Strategic Criticality | Tension description | PE acknowledgement |
|--------------|--------------|----------------------|--------------------|--------------------|
| sms-outreach | Commodity | Differentiating | SMS delivery infrastructure is commodity-stage; a Differentiating criticality rating risks over-investing in undifferentiated transport. | Accepted: differentiation is in the intent-signal timing layer built on top of commodity SMS APIs, not in the transport itself. Revisit if timing logic can be served by a Product-stage solution. |

---

## Suggested build sequence

> **Recommendation only** — final sequencing authority rests with the product team.
> Includes Build-disposition capabilities only. Non-Build items (contact-store Buy,
> data-enrichment Adopt, workflow-automation Buy, email-delivery Adopt, call-logging Buy)
> are procurement actions — handle in parallel with the build sequence.

| Position | Capability Id | Capability Name | Rationale |
|----------|--------------|-----------------|-----------|
| 1 | company-graph | Company Relationship Graph | Foundational differentiator; pipeline-engine and lead-scoring both depend on it. No build dependencies. |
| 2 | pipeline-engine | Pipeline Engine | Core deal-tracking surface; lead-scoring depends on it. Depends on company-graph (position 1). |
| 3 | engagement-timeline | Engagement Timeline | Independent of the above; can run in parallel with position 2 but listed here to keep the sequence readable. Depends on contact-store (Buy — procured separately). |
| 4 | lead-scoring | Lead Scoring | Consumes both company-graph and pipeline-engine outputs; must follow positions 1 and 2. |
| 5 | sms-outreach | SMS Outreach | Builds on engagement-timeline (position 3); depends on intent signals from the timeline to trigger outreach. Commodity transport but custom timing logic is the differentiator. |

---

## Next step readiness

`lean-canvas` (or `author-brief`) was not detected in available skills. The next
step after capability mapping is brief-authoring — translating the committed bet
and this capability map into an initiative brief that anchors M3–M6 spec-writing.
Resume when `lean-canvas` or `author-brief` becomes available.
