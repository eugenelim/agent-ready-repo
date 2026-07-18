# Counterpoints — RFC-0065 (`iac-terraform` pack) + its survey

Adversarial review (ACH evidence-against + GIJN seek-the-other-side) of the
load-bearing claims in [`../0065-iac-terraform-pack.md`](../0065-iac-terraform-pack.md)
and [`agent-driven-iac-survey.md`](agent-driven-iac-survey.md). Verdicts route to
either a **rating downgrade** or **do-not-resolve**. The single most important
finding is a citation defect in the survey (Finding 7) — a correction, not a
downgrade.

---

## Finding 7 (evidence quality): "schema-grounding beats hallucination; `plan` is not a sufficient oracle," `[moderate]`

- **Counter-position:** The specific numbers are mis-cited and rest on one AWS-only
  lineage. (a) **Misattribution:** arXiv 2512.14792 is Nekrasov et al. ("An Error
  Taxonomy… Configuration Knowledge Injection"), **not "Kon et al.," and does not
  contain the "29% hallucination / 46pp generation→validation drop" figures.** (b)
  Those figures trace to an **unverifiable ResearchGate paper** ("Hallucinated
  Resources, Brittle Oracles…") with no arXiv listing and no confirmed peer review.
  (c) The **"27%→75%" is a metric conflation** — it splices Nekrasov et al.'s
  *overall-success* baseline (27.1%) against their *technical-validation* endpoint
  (75.3%): two different metrics, not a before/after of one. (d) The foundational
  **IaC-Eval (Kon et al.) is genuinely peer-reviewed (NeurIPS 2024 D&B) but AWS-only
  by design**; no independent Azure/GCP replication exists. (e) A follow-on found
  **only 59% of IaC-Eval's own ground-truth scripts pass `terraform plan`** — so part
  of the "LLM failure" funnel may be flawed oracle artifacts, which *undercuts* "plan
  is an insufficient oracle" as an LLM-specific claim. TerraProbe used non-frontier
  models despite a mid-2026 date.
- **Counter-evidence:** [arXiv:2512.14792](https://arxiv.org/abs/2512.14792) (primary
  — authors/metrics verified); [ResearchGate 405480961](https://www.researchgate.net/publication/405480961)
  (primacy uncertain, no peer review); IaC-Eval [NeurIPS 2024](https://proceedings.neurips.cc/paper_files/paper/2024/hash/f26b29298ae8acd94bd7e839688e329b-Abstract-Datasets_and_Benchmarks_Track.html)
  (primary, peer-reviewed, AWS-only); Multi-IaC-Eval [arXiv:2509.05303] (still all-AWS).
- **Verdict:** **rating downgrade — `[moderate]` → `[low]`** on the *specific numbers*
  (reason: mis-citation + single unreplicated lineage + probable metric error). The
  **directional** claim (schema-hallucination is a real, peer-reviewed failure mode
  via IaC-Eval; grounding + `plan` help) survives at `[moderate]`. **Action taken:**
  survey §5 and the RFC Evidence bullet corrected — attribute IaC-Eval (Kon et al.,
  NeurIPS 2024) as the peer-reviewed anchor, mark 29%/46pp as unverified-ResearchGate,
  drop the "27%→75%" clean-delta framing.

## Finding 6 (provider contract): "the four-file contract generalizes to *any cloud* by extension," `[high]`→ implied

- **Counter-position:** The contract is **hyperscaler-shaped (AWS/Azure/GCP)**, not
  universal. It breaks for: **non-cloud providers** (Cloudflare/GitHub/Datadog/
  Kubernetes have no backend/region/OIDC-federation/tagging notion — K8s auth is to
  the API server, not a cloud IAM plane); **multi-provider stacks** (Terraform expects
  many providers in one config — "one cloud → one four-file bundle" is not the common
  case); **OCI** (no native lockable backend until Terraform 1.12/2025 — before that,
  faked S3-compat, *no locking*, long-lived keys); **AliCloud** (OIDC is a bolt-on,
  provider v1.222+); **on-prem/air-gapped** (guidance is `local` backend — the
  partial-backend contract is inapplicable *by design*); **sovereign clouds**
  (Azure China/Gov need a different auth endpoint the contract doesn't model); and
  **tags/network don't round-trip** (GCP labels are lowercase-only; GCP VPC is
  *global* while AWS/Azure are regional; OCI adds compartments).
- **Counter-evidence:** [Terraform backend list](https://developer.hashicorp.com/terraform/language/backend)
  (primary — no vsphere/datadog backend); [OCI native backend, TF 1.12](https://blogs.oracle.com/cloud-infrastructure/terraform-oci-state-locking-backend)
  (primary); [K8s/Helm dynamic creds](https://developer.hashicorp.com/terraform/cloud-docs/dynamic-provider-credentials/kubernetes-configuration)
  (primary); [tags/labels cheat-sheet](https://www.meshcloud.io/en/blog/tags-and-labels-on-cloud-platforms-cheat-sheet-2020/)
  (secondary); GCP-global-VPC vs AWS/Azure-regional (secondary).
- **Verdict:** **rating downgrade** — "any cloud by extension" overclaims. Rescope to
  **"the major public clouds (AWS/Azure/GCP, extensible to OCI/AliCloud) by
  extension,"** and explicitly scope OUT non-cloud providers, multi-provider stacks,
  on-prem/air-gapped, and sovereign variants. Reason: over-generalization from a
  3-cloud center. **Action taken:** §6 rescoped + a non-goal added.

## Finding 5 (charter principle 4): "used often enough to stick," `[moderate]`

- **Counter-position:** Greenfield authoring of *new* IaC is front-loaded and
  comparatively rare; **day-2 maintenance dominates** the lifecycle, and Encore argues
  Terraform change throughput is structurally throttled ("a few changes per week")
  by review/apply/coordination — so faster *generation* doesn't create *habitual*
  use. A once-per-project scaffolder risks failing principle 4.
- **Counter-evidence:** [Encore, "The Last Year of Terraform"](https://encore.dev/blog/last-year-of-terraform)
  (tertiary/vendor, but the sharpest structural argument); [Cycloid Day-2 guide](https://www.cycloid.io/blog/day-2-operations-a-practical-guide-for-managing-post-deployment-complexity/)
  (tertiary/vendor); Rahman "Gang of Eight" + InfraFix (arXiv 2503.17220) (primary —
  large IaC *repair* corpora ⇒ maintenance is the populated activity). **No neutral,
  IaC-specific time-allocation statistic exists** — both "day-2 dominates" and
  "generate often" sources are vendor-motivated.
- **Verdict:** **do-not-resolve.** Both hold under different conditions: the pack
  clears principle 4 **if framed as iterate/day-2** (generate → *re-plan* on drift →
  *re-apply* through the loops — the frequent activity the repair corpora evidence),
  and risks failing it **if framed as greenfield-only scaffolding** (the rare, gated
  activity). More evidence won't collapse this — it's a framing/regime split. **Action
  taken:** the RFC's principle-4 case is re-anchored on the iterative/day-2 framing
  (which the loop reframe already supports), not on greenfield generation.

## Finding 2 (charter erosion): "opt-in + not-in-default-profile contains the blast radius," `[moderate]`

- **Counter-position:** Across ecosystems, **bare optionality has repeatedly failed to
  contain sprawl.** Backstage (230+ opt-in plugins now mirror the tool-sprawl it was
  meant to fix; $150K/yr + 2–3 FTE to run); VS Code extensions (opt-in, but *no*
  permission model / inventory); Homebrew (had to strip build options from core *and*
  run a tap-archiving program); the Terraform registry itself (a formal
  archiving process for dead opt-in providers); ESLint (Airbnb config became *de-facto
  mandatory* through network effects). The failure mode in each was a **missing
  maintenance-ownership / deprecation lifecycle**, not the opt-in switch.
- **Counter-evidence:** [Backstage: needs better gardens](https://drodil.medium.com/backstage-does-not-need-more-plugins-it-needs-better-gardens-3f9dfdc0d131)
  (secondary); [VS Code extension governance study, arXiv:2411.07479](https://arxiv.org/html/2411.07479v1)
  (primary); [Homebrew deprecating/removing](https://docs.brew.sh/Deprecating-Disabling-and-Removing)
  (primary); [Terraform archiving providers](https://developer.hashicorp.com/terraform/internals/archiving)
  (primary); [ESLint flat-config rollout](https://eslint.org/blog/2023/10/flat-config-rollout-plans/) (primary).
- **Verdict:** **rating downgrade** — "opt-in contains it" is insufficient *alone*.
  Reason: strong cross-ecosystem precedent that containment requires an explicit
  ownership/deprecation/archiving lifecycle from day one. **Action taken:** added a
  maintenance-ownership + deprecation-lifecycle commitment to Risks as a required
  mitigation, and a matching pre-mortem.

## Finding 4 (loop-arc): "generate-iac authoring in work-loop → apply in release-loop actually works," `[inference]`

- **Counter-position:** The whole loop-arc benefit ("the iterative outer loop catches
  the AWS apply-time failures we miss") is **conditional on `release-engineering`
  being installed *and* an ephemeral-environment harness (omnigent) existing**. Most
  adopters have neither. Absent them, the pack degrades to `work-loop` + the seed
  pipeline — i.e., back to the accelerator's stop-at-plan, and the headline
  apply-iteration benefit evaporates for the majority.
- **Counter-evidence:** `[inference]` from the release-loop skill's own preconditions
  (ephemeral-env isolation as a carve precondition; "absent that install the loop
  surfaces the gap") — the RFC's §1b "degrades gracefully" already concedes this.
- **Verdict:** **rating downgrade** — the loop-arc is the *ceiling*, not the default.
  Reason: conditional on infra most adopters lack. **Action taken:** §1b strengthened
  to state the two operating modes plainly — full (release-loop present) vs. degraded
  (work-loop + gated pipeline = corrected-accelerator), so the RFC doesn't oversell
  the outer loop as the baseline.

## Finding 1 (additive not duplicative): `[moderate]`

- **Counter-position:** With verify, gating, reviewers, and deploy all reused from
  `core`/`release-loop`, the non-reused residue is thin — the standards/provider/
  policy references + a mostly-orchestrating skill. Is that a *skill* or just a
  reference bundle `work-loop` could load? If the latter, the "new pack" is mostly
  packaging.
- **Counter-evidence:** `[inference]`. The genuinely additive, non-duplicative pieces
  are the **discipline mechanics** (vocabulary firewall, tier-tasks, the four-file
  contract, policy-on-plan starters) and the Terraform-specific references — not the
  skill's control flow.
- **Verdict:** **rating downgrade** — additivity is real but **modest**, and it lives
  in the references + disciplines, not the skill logic. Reason: most behavior is
  reused. Not fatal (the references *are* substantive and stack-specific, which core
  can't carry) — but the RFC should claim additivity for the *references + disciplines*,
  not the orchestration. **Action taken:** noted in the additivity framing.

## Finding 3 (zero-agent, reuse core reviewers): `[inference]`

- **Counter-position:** `quality-engineer` / `security-reviewer` reason from
  tool-neutral standards; will they catch **Terraform-specific** failure classes
  (state-file manipulation, provider-version supply-chain, module-source pinning,
  `for_each`/`count` churn) without a Terraform-aware reviewer?
- **Counter-evidence:** `[inference]` + the survey's own finding that per-provider
  depth comes from the **scanner** (Checkov/Trivy), not a standards-reasoning reviewer.
- **Verdict:** **do-not-resolve.** Zero-agent is right for the charter (three-reviewer
  ceiling) *and* the Terraform-specific depth concern is real — both hold, because
  they answer different questions: **failure-class reasoning** is the reviewers'
  job (reused), **per-provider config depth** is the scanner's job (a task-zero the
  pack requires). Neither substitutes for the other; more agents wouldn't fix it.
  **Action taken:** the RFC already states the reviewer+scanner pair; made explicit
  that Terraform-specific depth is the scanner's, not the reviewers'.

---

## Moderator pass — highest-signal unused snippet

The IaC-Eval methodology crack (only 59% of ground-truth passes `plan`) is the most
under-used counter: it suggests some "LLM-generated Terraform is wrong" signal is
**benchmark-oracle noise**, not model failure. This *slightly strengthens* the pack's
"reuse `core`'s phased-oracle discipline" choice (don't over-trust any single oracle)
while *weakening* the specific severity numbers — folded into the Finding 7 correction.

## Net effect on the RFC

No claim was fully overturned, but **six corrections** land: (7) fix the citation
defect + downgrade the numbers to `[low]`; (6) rescope "any cloud"→ hyperscalers + a
non-goal; (5) re-anchor principle-4 on iterate/day-2; (2) add an ownership/deprecation
lifecycle mitigation; (4) state full-vs-degraded operating modes; (1/3) claim
additivity for references+disciplines and make the reviewer-vs-scanner division
explicit. The pack's *core thesis* (reuse core+release-loop; ship only the
Terraform-specific residue) survives — indeed the review strengthens the "don't
over-trust one oracle" and "reuse, don't re-invent" arguments.
