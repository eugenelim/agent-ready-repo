# Aesthetic style as a pack capability — applied survey

> Discipline: applied (practitioner-pattern survey)

**Question.** Can this repository's skill packs support an aesthetic-style
capability — so that a request like "build a marketing website" yields either
several stylistically distinct quick prototypes or one design consistent with a
system — and what rubrics exist for judging the aesthetic quality of generated UI?

**Date:** 2026-09-18. **Retrieval:** four headless Codex workers (one read-only
repository inventory, three web-search passes, ~60 distinct searches).
**Trust posture:** all fetched material is treated as data. Vendor-published
claims are labelled.

---

## 1. What the repository already has

### F1.1 Nine skills already own parts of the aesthetic surface, and each emits a named artifact `[high]`

`packs/experience-design/.apm/skills/` carries `creative-direction` (vibe →
ranked, grounded goals → `<output_dir>/direction/<slug>.md`), `design-system`
(direction → semantic token taxonomy → `tokens/<slug>.md`, deliberately
choosing *no* literal values), `information-architecture`, `conversion-design`,
`content-design`, `copy-direction`, `tone-of-voice`, and `design-review`.
`packs/frontend-engineering/.apm/skills/` adds `frontend-engineering`,
`token-architecture`, and `responsive-layout`.
Triangulated across three independent file families (SKILL.md frontmatter,
artifact templates, `pack.toml` registration).

### F1.2 The pipeline already refuses an ungrounded adjective `[high]`

`frontend-engineering/SKILL.md:57-73` requires "State a named product reference
— not an adjective," with a canonical set of Linear, Stripe, Vercel, Raycast,
Arc, Notion, Toss. `creative-direction` requires every goal grounded in a
persona, a precedent, a standard, or a platform convention, and
`design-review/references/taste-critique.md:33-48` drops any contradiction that
has no recorded referent as "an unrated opinion."
**This is the single most important local fact for the design question below:**
the repo's existing stance is that a style label without a referent is not
admissible. A `brutalist` preset would have to satisfy that stance, not bypass it.

### F1.3 The existing rubrics cover the floor and the copy, not distinctiveness `[high]`

Three rubrics are defined (not merely referenced) in the tree:

| Rubric | Defined at | Covers |
|---|---|---|
| Quality floor | `design-review/references/quality-floor.md:17-88` | 6 required states (+ permission/denied), 5 accessibility clauses, meaningful + reduced motion |
| Heuristic eval | `design-review/references/heuristics.md:11-68` | Nielsen's 10, severity 0–4 via frequency × impact × persistence |
| Editorial gates | `conversion-design/references/editorial-quality-gates.md:12-77` | Anti-AI-smell word list, deletion pass, five-second / specificity / point-of-view / distinctiveness tests |

The gap is exact: **nothing scores whether a surface is visually
distinctive, nor whether two generated surfaces differ from each other.** The
`distinctiveness` test in the editorial gates is about *copy*, not layout,
type, or colour.

### F1.4 There is no named-style vocabulary anywhere in the tree `[high]`

`rg -i "brutalist|neo-brutalist|glassmorphic|swiss|style preset"` over the
repository returns nothing usable — one incidental phrase ("muted review
aesthetic") in `docs/specs/render-proof/spec.md`. "Editorial" appears only as a
*surface genre* and as a mapping to the Notion product reference, never as a
reusable style object. The reusable unit today is a per-surface
creative-direction document.

### F1.5 Divergence exists in the repo, but only over product shape — never visual treatment `[high]`

`explore-options` says "Generate N candidate shapes (4–5 is the useful range)"
across altitude × mechanic; `diverge-solutions` requires "≥3 structured,
comparable solution options" differing by mechanic, scope, or bet.
No experience-design skill asks for N visual alternatives of one surface.
The divergence machinery and its `N=3–5` convention already exist — at the
wrong altitude.

---

## 2. Prior art: do tools actually produce multiple styles?

### F2.1 Most "vibe coding" builders expose one evolving project, not N directions `[moderate]`

v0 documents selecting an iteration and continuing to edit it
([Vercel, 2023](https://vercel.com/blog/announcing-v0-generative-ui));
Bolt documents prompt → preview → chat edits, with its enterprise design-system
feature aiming to *preserve* existing components
([Bolt, 2026](https://support.bolt.new/building/design-system/view-design-system));
Lovable's project Knowledge makes later additions adhere to a predefined style
([TechRadar, 2026-07-02](https://www.techradar.com/pro/software-services/lovable-review)).
Three independent sources (one vendor-neutral). Downgraded from `[high]`
because absence in public docs is weak evidence about a shipped UI.

### F2.2 Three products do ship deliberate style divergence `[moderate]`

- **Relume** generates multiple style-guide "concepts" with independently
  shuffled or locked colours, typography and UI-element styling, and presents
  the top three to stakeholders
  ([Relume, 2026](https://resources.relume.io/resources/docs/concept-creation-using-the-relume-style-guide-builder)).
- **Google Stitch** ships theme selectors and "generate multiple variants of
  your interface"
  ([Google Developers Blog, 2025](https://developers.googleblog.com/stitch-a-new-way-to-design-uis/)).
- **Subframe** generates "multiple design variations using your theme and
  components" — N options *inside* one theme, which is the constrained case
  ([Subframe, 2026](https://docs.subframe.com/learn/quickstart)).

All three vendor-published. The distinction Relume draws — divergence at the
*style-guide* level, convergence at the *page* level — is the design worth
copying.

### F2.3 No tool publishes a named-aesthetic picker with the labels people prompt with `[moderate]`

No authoritative published preset list containing "brutalist", "Swiss",
"editorial", "neo-brutalist", "glassmorphism" or "retro-terminal" was found for
v0, Lovable, Bolt, Figma Make, Stitch, Uizard, Claude Artifacts, Subframe or
Relume. Subframe ships ten presets but does not name them publicly
([Subframe, 2026-05-13](https://docs.subframe.com/learn/theme/customizing-theme)).
Those labels are effective *prompt language* with no product backing.
Downgrade factor: proving a negative from public docs.

### F2.4 Tokens are necessary but not sufficient to swap an aesthetic `[moderate]` `[inference]`

The W3C DTCG format covers colour, dimension, typography, border and shadow
tokens — a real swap surface, but a Community Group report, **not** a W3C
Recommendation
([W3C DTCG, 2025-10-28](https://www.w3.org/community/reports/design-tokens/CG-FINAL-format-20251028/)).
Tailwind's `@theme` implements the same idea
([Tailwind, 2026](https://tailwindcss.com/docs/theme)).
But Subframe's own limitation note — spacing stays Tailwind-default and must be
extended separately — shows the boundary
([Subframe, 2026-05-13](https://docs.subframe.com/learn/theme/customizing-theme)),
and Relume needs *separate* controls for colour, type and component styling to
express a direction. **Tokens give themed variants of one UI architecture;
"editorial" vs "brutalist" also needs layout, density, component and motion
rules.** Tagged `[inference]`: no source states this boundary directly.

---

## 3. Rubrics for aesthetic quality in generated UI

### F3.1 No public leaderboard is a clean aesthetic rubric; the best is one weighted component `[high]`

| Benchmark | What it actually scores | Method |
|---|---|---|
| WebDev Arena | blended preference (design + working code + instruction-following), Next.js/React only | anonymous human pairwise |
| Design Arena | blind pairwise on rendered output, Elo/win-rate | human preference, no published rubric |
| **WebAppBench** | functional 47% / **visual design 24%** / code quality 18% / security | MLLM screenshot judge + deterministic heuristics + responsive tests |
| UI-Bench | designer binary preferences, TrueSkill ranking | human; authors note FID/CLIP disagree with designers |
| DesignBench | front-end code gen/edit/repair across 4 frameworks | implementation fidelity, not taste |
| VisualWebArena, WebCanvas, UI-TARS/OSWorld | agent task success on existing UI | **not aesthetics at all** — frequently miscited as such |

Sources: [Arena.ai, 2025](https://arena.ai/blog/webdev-arena) ·
[Design Arena, 2026](https://www.designarena.ai/leaderboard/code) ·
[WebAppBench, 2026](https://webappbench.com/) ·
[UI-Bench, 2025](https://arxiv.org/abs/2508.20410) ·
[DesignBench, 2025](https://arxiv.org/abs/2506.06251) ·
[VisualWebArena, ACL 2024](https://aclanthology.org/2024.acl-long.50/) ·
[OSWorld, 2024](https://os-world.github.io/).
WebAppBench does not publish its judge prompt or sub-weights — treat its visual
rank as a project measurement, not a standard.

### F3.2 VisAWI is the best-validated human rubric available, and it is four named facets `[high]`

**Simplicity, Diversity, Colorfulness, Craftsmanship** (Moshagen & Thielsch,
IJHCS 2010). Behind it sit Lavie & Tractinsky's two scales — Classical
(aesthetic, pleasant, symmetric, clear, clean) and Expressive (creative,
fascinating, original, sophisticated, uses special effects)
([IJHCS, 2004/2010](https://www.sciencedirect.com/science/article/pii/S1071581910000777)).
Ngo, Teo & Byrne give **fourteen** geometrically computable measures (balance,
equilibrium, symmetry, sequence, cohesion, unity, proportion, simplicity,
density, regularity, economy, homogeneity, rhythm, order/complexity) — note:
fourteen, not the commonly cited thirteen
([Symmetry, 2000](https://symmetry-us.com/Journals/ngo/index.html)).
These are directly operationalisable as review items today, with no model needed.

### F3.3 Automated screenshot scoring is real but narrow `[moderate]`

Perceived visual complexity + colourfulness + demographics explain ~50% of
variance in aesthetic ratings made after 500 ms
([Reinecke & Gajos, CHI 2013](https://www.eecs.harvard.edu/~kgajos/papers/2013/reinecke13predicting.shtml)).
Visual-attention heatmap entropy correlates r = −0.65 with perceived aesthetics
([arXiv, 2018](https://arxiv.org/abs/1803.01537)).
**UIClip** (ACM UIST 2024) is the only published UI-specific design-quality
model found — screenshot + description → quality score, 2.3M training pairs,
1,200 real ratings, highest agreement with 12 designers among baselines; the
public abstract reports no single correlation coefficient
([UIST 2024](https://doi.org/10.1145/3654777.3676408)).
**UICrit** offers 3,059 critiques over 983 UIs from seven designers as judge
training data ([arXiv, 2024](https://arxiv.org/abs/2407.08850)).
Generic CLIP/LAION aesthetic predictors are *not* validated for UI — UI-Bench
reports they can contradict designer preference.

### F3.4 The only auditable LLM-judge rubrics are vendor-published `[moderate]`

Sifter scores visible visual design 0–100 across layout, typography, colour,
imagery quality, visual hierarchy and mobile rendering, explicitly excluding
copy and business quality ([Sifter, 2026](https://sifter.so/docs/audits)).
XSCT Bench weights visual aesthetics at 35%, defined as colour scheme,
typographic hierarchy, overall design sense, commercial-product quality
([XSCT Bench, 2026](https://www.xsctbench.com/methodology)).
**No Anthropic, OpenAI or Google prompt-level aesthetic rubric with explicit
criteria, weights and scale is public.** Two independent vendors is below the
three-source bar for the practitioner taxonomy; hence `[moderate]`.

### F3.5 "AI slop" is well-described, weakly measured `[low]`

Practitioner accounts converge on the same signature: purple/blue gradients,
Inter, glass cards, centred heroes, rounded-card grids, shadcn + Tailwind
defaults ([Snoddy, 2026](https://www.joshuasnoddy.com/blog/why-ai-websites-look-the-same/)).
Anthropic's own `frontend-design` skill names five clusters (see F4.1).
One gallery claims "they all look the same" in ~13% of on-topic posts with ~150×
growth 2023→2024, with no auditable protocol
([Styles Gallery, 2026](https://styles.gallery/blog/why-ai-built-sites-look-the-same)).
Downgrade factors: **survivorship bias** (only complaints get written up) and
no replicated mode-collapse measurement for UI. Mechanism is plausible —
shadcn itself exposes configurable base colours, fonts, radii and tokens, so
sameness is a defaults problem, not a technical inevitability
([shadcn/ui, 2026](https://ui.shadcn.com/docs/theming)).

---

## 4. The closest competing artifact, and the evidence that undercuts presets

### F4.1 Anthropic's public `frontend-design` skill is 52 lines and does the opposite of a preset picker `[high]`

Raw source read directly
([anthropics/skills, 2026-09-18](https://raw.githubusercontent.com/anthropics/skills/main/skills/frontend-design/SKILL.md)):

- **No named directions in the skill.** It demands a direction specific to the
  brief — "make deliberate, opinionated choices about palette, typography, and
  layout," grounded in the product's "industry, subject matter, materials, and
  vernacular." (The *marketplace page* offers "brutalist, maximalist,
  retro-futuristic, luxury, playful, etc." as examples —
  [claude.com/plugins/frontend-design](https://claude.com/plugins/frontend-design) —
  but the skill file does not.)
- **No scored rubric.** It mandates a two-pass process instead: a compact token
  plan (Color — 4–6 named hexes; Type; Layout with ASCII wireframes and
  alignment; Principles), then a self-review that must revise anything reading
  as the model's generic default, *then* code.
- **No multiple finished variants.** The closest is ASCII wireframes "to ideate
  and compare"; the deliverable is one plan → self-review → implementation.
- **Explicit anti-slop clusters:** warm-cream/terracotta serif; near-black with
  acid-green/vermilion; broadsheet rules and dense columns; identical rounded
  SaaS cards with soft shadows; template chrome (ALL-CAPS eyebrows, `A · B · C`,
  monospace data labels, `→` links). Correctly qualified: these are legitimate
  when requested — "the brief's own words always win."

`web-artifacts-builder` names no styles, requests no variants, has no rubric,
and carries one anti-slop line: "avoid using excessive centered layouts, purple
gradients, uniform rounded corners, and Inter font"
([anthropics/skills, 2026-09-18](https://raw.githubusercontent.com/anthropics/skills/main/skills/web-artifacts-builder/SKILL.md)).

### F4.2 No evidence that a style *label* reliably changes structure rather than colour `[uncertain]`

No controlled study was found that holds the brief constant, varies only a
named aesthetic label, and measures separable change in layout, typography or
information architecture. The nearest evidence is Google Research's *Generative
UI*, where detailed Style sections ("Classic", "Wizard Green") containing
colours and fonts produced output that followed the style down to icons and
imagery — observational, not an ablation, and its human evaluation compares
generative UI against markdown and human-authored sites rather than comparing
the styles to each other
([Google Research, 2026](https://generativeui.github.io/static/pdfs/paper.pdf)).
Text-guided style transfer shows textual descriptions can drive distinguishable
*image* styling ([CVPR-W, 2023](https://openaccess.thecvf.com/content/CVPR2023W/CVFAD/papers/Liu_Name_Your_Style_Text-Guided_Artistic_Style_Transfer_CVPRW_2023_paper.pdf)),
which does not transfer to structural web variation.
**Rated `[uncertain]`, not `[low]`: the claim has a defensible direction
(detailed conditioning works; label-only conditioning is unproven) but thin
grounds.** Downgrade factor: absence of a direct ablation.

### F4.3 Parallel prototyping works — under conditions that may not hold here `[moderate]`

Dow et al. (TOCHI 2010): 33 participants, five web-banner prototypes each,
equal time and feedback. Parallel participants beat serial on click-through
rate, target-site engagement, and blind client/professional ratings;
independent raters judged their prototypes more diverse; parallel participants
gained self-efficacy, serial did not
([Stanford HCI, 2010](https://hci.stanford.edu/publications/2010/parallel-prototyping/ParallelPrototyping2010-final.pdf)).
**The conditions matter:** novice-to-intermediate designers, graphic ads,
divergence *before* critique. No modern replication with AI-generated web pages
reproducing those outcome measures was found. The Double Diamond makes the same
divergence-then-convergence structure explicit
([Design Council, 2026](https://www.designcouncil.org.uk/resources/the-double-diamond/)).

### F4.4 Counter-evidence: variety costs, and choice overload is conditional `[moderate]`

Design-system survey respondents name consistency, reuse and efficiency as the
adoption reason, and investment plus long-term maintenance as the constraint
([Sparkbox, 2019](https://designsystemsurvey.sparkbox.com/2019/)); a
practitioner account argues each standardised component costs negotiation and
local creative freedom
([Design System University, 2025-07-08](https://designsystem.university/articles/the-cost-of-consistency)).
A 99-observation meta-analysis finds choice overload is **moderated** by
choice-set complexity, task difficulty, preference uncertainty and decision
goal — not a blanket effect
([Chernev, Böckenholt & Goodman, 2015](https://www.sciencedirect.com/science/article/pii/S1057740814000916)).
Read correctly, this argues for a *small, meaningfully differentiated, criteria-
accompanied* set — not for refusing options.

---

## 5. Applied implications for the packs `[synthesis]`

Everything in this section is synthesis across §1–§4, not a cited claim.

**Answer to the headline question: both, but as two named modes, not one
behaviour.** The convergent prior-art pattern (Relume, Double Diamond, Dow) is:
diverge at the *direction* level, converge at the *page* level. A single
capability that sometimes returns three styles and sometimes one is the failure
case — the mode has to be explicit.

| Mode | When | Output |
|---|---|---|
| **Explore** | no approved `creative-direction` artifact exists | 3 contrasted directions (Dow's parallel condition; Chernev's small differentiated set), each a *thin* prototype |
| **Apply** | a `creative-direction` + `tokens` artifact exists | one surface, consistent, reviewed against the existing three rubrics |

**Four design constraints the evidence imposes:**

1. **A style preset cannot be a bare label.** F1.2 (the repo already refuses
   adjectives) and F4.2 (label-only conditioning is unproven) agree. A preset
   must carry the grounding `creative-direction` already demands — persona,
   precedent, standards, platform — plus explicit structural rules. A preset is
   therefore best modelled as a *pre-filled creative-direction document*, not a
   new primitive.
2. **A preset cannot be tokens only** (F2.4). It needs grid/density, type roles,
   component shape and motion rules alongside the token bundle.
3. **Explore mode's prototypes must be thin and disposable.** F4.4 is the real
   cost: N directions × the existing quality floor (6 states × accessibility ×
   reduced motion) is unaffordable. Explore mode should produce style-guide-level
   concepts (Relume's shape), not six fully-stated pages; the floor attaches at
   convergence.
4. **Divergence must be verified, not assumed.** F3.5 and F4.2 together mean the
   likely failure is three recolours of one layout. This needs an actual check.

**The rubric gap is the tractable piece.** The repo has the floor
(quality-floor.md), the usability pass (heuristics.md) and the copy pass
(editorial-quality-gates.md). Two are missing, and both are buildable from §3
without a model:

- **Perceived aesthetics**, as VisAWI's four facets (Simplicity, Diversity,
  Colorfulness, Craftsmanship) rated as items — an interpretable extension to
  `design-review`'s taste-critique, consistent with its existing
  advances/neutral/contradicts scoring.
- **Divergence audit** for explore mode: across the N directions, do the palette,
  type family and scale, grid/column count, component shape language, and
  density actually differ? A direction that differs only in hue is not a
  direction. This is the one control with no prior art to copy — and the one
  that makes explore mode honest.

**Where it lands.** `packs/experience-design/.apm/skills/aesthetic-style/`
(SKILL.md, references/, assets/, evals/), registered in
`packs/experience-design/pack.toml` `[pack.evals].skills`, with
`creative-direction` as the physical template. Artifact base is `docs/design`.
The existing `explore-options` N=3–5 convention is the precedent for the count.

**What not to build:** a validated aesthetic *score*. F3.1 and F3.4 show no one
has a defensible one, including the labs. Rating items beat a composite number.

---

## Known unknowns

- **Known-unknown:** does prompting a named style label actually change layout
  and typography, or only colour and type family? Would be closed by: an
  in-repo ablation — one brief, five labels, N generations each, measured on
  the F5 divergence axes (palette / type family + scale / grid / component shape
  / density). This is cheap, and it decides whether presets are worth shipping.
- **Known-unknown:** does parallel generation beat serial iteration when the
  *generator* is the model rather than a novice designer? Dow's mechanism was
  partly human self-efficacy and reduced anchoring — neither applies unchanged.
  Would be closed by: a within-repo comparison scored by the existing rubrics.
- **Known-unknown:** WebAppBench's visual sub-weights and judge prompt. Would be
  closed by: the project publishing them, or an independent reimplementation.
- **Known-unknown:** UIClip's numeric agreement with designer rankings. Would be
  closed by: the full UIST paper (only the abstract was reachable here).
- **Unknowable (as posed):** whether generated-UI homogenisation is worsening at
  a measurable rate. The counterfactual corpus — what the same briefs would have
  produced under earlier models — was never recorded, and public galleries are
  self-selected. Any rate figure would be reconstructed, not observed.
- **Unknowable (as posed):** which of three directions is "better" in the
  abstract. F3.1's leaderboards resolve this by human pairwise vote precisely
  because no rubric settles it; a contested-taste question is a tension, not a
  finding.

**Companion:** [`aesthetic-style-blueprint.md`](aesthetic-style-blueprint.md) — the generative half: item-level rubric detail, the ten-axis direction sheet, named-style formal commitments, and what the four published Anthropic design skills actually contain.
