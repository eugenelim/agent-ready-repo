---
type: capability-map
slug: bloom-marketplace
date: 2026-07-10
bet-source: docs/product/shaping/bloom-marketplace/bet.md
vision: A curated B2C marketplace where rigorous seller onboarding and relevance-first search let independent makers reach buyers that general marketplaces fail to serve.
---

# Capability Map: Bloom Marketplace

## Disposition vocabulary

| Term | Definition |
|------|-----------|
| **Build** | Internal development; team owns full lifecycle; Genesis or Custom-built stage; core to competitive differentiation. |
| **Buy** | Commercial licence or SaaS subscription; Product or Commodity stage; standard function not worth building. |
| **Partner** | Co-developed with an external partner or contract firm; mid-maturity; external expertise accelerates delivery under shared governance. |
| **Adopt** | Open-source or open-standard solution; minimal customisation required. Distinct from Buy: no licence cost, but carries an ongoing maintenance obligation. |

---

## Product Catalogue

Stores and surfaces the inventory of products listed on the marketplace.

| Id | Capability | Description | Wardley Stage | Strategic Criticality | Disposition | Dependencies |
|----|-----------|-------------|--------------|----------------------|-------------|-------------|
| search-engine | Search & Discovery | Indexes catalogue products and returns relevance-ranked results tuned for niche product discovery over broad popularity signals. | Custom-built | Differentiating | Build | product-catalogue |
| product-catalogue | Product Catalogue | Stores product listings with standard fields (title, description, price, images, category). | Product | Parity | Buy | — |

## Transactions & Payments

Handles order creation, payment capture, and fulfilment coordination.

| Id | Capability | Description | Wardley Stage | Strategic Criticality | Disposition | Dependencies |
|----|-----------|-------------|--------------|----------------------|-------------|-------------|
| order-orchestration | Order Orchestration | Manages the order lifecycle — creation, confirmation, fulfilment status updates, and cancellation — across buyers and sellers. | Custom-built | Differentiating | Build | payment-gateway |
| payment-gateway | Payment Gateway | Captures buyer payments and routes seller payouts; standard Stripe or equivalent integration. | Commodity | Utility | Adopt | — |
| fraud-screening | Fraud Screening | Evaluates transaction risk at checkout using a rules-based + ML scoring service. | Product | Parity | Buy | payment-gateway |

## Seller Management

Onboards, verifies, and manages the quality and compliance of marketplace sellers.

| Id | Capability | Description | Wardley Stage | Strategic Criticality | Disposition | Dependencies |
|----|-----------|-------------|--------------|----------------------|-------------|-------------|
| seller-onboarding | Seller Onboarding | Guides sellers through application, identity verification, catalogue quality review, and approval — the primary supply-quality gate. | Custom-built | Differentiating | Build | compliance-screening |
| compliance-screening | Compliance Screening | Runs identity (KYC) and business legitimacy checks against regulated data sources. | Product | Parity | Adopt | — |
| seller-dashboard | Seller Dashboard | Gives sellers visibility into their orders, payouts, and catalogue performance. | Product | Parity | Buy | order-orchestration, seller-onboarding |

---

## Suggested build sequence

> **Recommendation only** — final sequencing authority rests with the product team.
> Includes Build-disposition capabilities only. Non-Build items (product-catalogue Buy,
> payment-gateway Adopt, fraud-screening Buy, compliance-screening Adopt, seller-dashboard Buy)
> are procurement actions — handle in parallel with the build sequence.

| Position | Capability Id | Capability Name | Rationale |
|----------|--------------|-----------------|-----------|
| 1 | seller-onboarding | Seller Onboarding | Primary supply-quality differentiator; depends on compliance-screening (Adopt — procured separately). No Build dependencies. Start here to grow qualified supply before search tuning begins. |
| 2 | search-engine | Search & Discovery | Core discovery differentiator; depends on product-catalogue (Buy — procured in parallel). Can begin once the catalogue is seeded by onboarded sellers (position 1). |
| 3 | order-orchestration | Order Orchestration | Transaction backbone; depends on payment-gateway (Adopt — procured separately). Follows search so the team can validate demand before building fulfilment infrastructure. |

---

## Next step readiness

`lean-canvas` (or `author-brief`) was not detected in available skills. The next
step after capability mapping is brief-authoring — translating the committed bet
and this capability map into an initiative brief that anchors M3–M6 spec-writing.
Resume when `lean-canvas` or `author-brief` becomes available.
