# Authoring a creative direction — structural blueprint

> Discipline: applied (practitioner-pattern survey)

**Companion to** [`aesthetic-style-survey.md`](aesthetic-style-survey.md), which
answered *whether* to build the capability. This answers *what goes in it*.

**Question.** The evaluative rubrics (VisAWI, Ngo, Nielsen) score a finished
surface and do not help author a direction. What prescriptive material exists,
what do the evaluative rubrics actually contain at item level, and how do the
two compose into a creative-direction document?

**Date:** 2026-09-18. **Retrieval:** four more headless Codex workers (~105
searches) plus direct `curl` of eight published skill files.

---

## 0. The correction that reframes everything

**Evaluative and generative rubrics are different instruments and the split is
load-bearing.** Round 1 conflated them. The distinction the sources support:

| | Evaluative | Generative |
|---|---|---|
| Question | how good is this? | what should this be? |
| Timing | after a surface exists | before anything is built |
| Form | rated items, severity scores | parameter sheet, prohibitions, plan |
| Examples here | VisAWI, Ngo, UICrit, Nielsen | Anthropic's four-field plan, Bertin's variables, Carbon's spec rules |
| Failure if misused | scores a geometrically regular but characterless page well | produces a checklist-compliant page with no point of view |

The repo's three existing rubrics (quality floor, heuristics, editorial gates)
are **all evaluative**. That is the actual gap, and it is a different gap from
the one round 1 named.

---

## 1. The evaluative rubrics, at item level

### F1.1 VisAWI is 18 items on a 7-point agreement scale, α = .86–.89 per facet `[high]`

Reproduced from the VisAWI-S development paper's instrument table
([Moshagen & Thielsch, 2010](https://www.sciencedirect.com/science/article/pii/S1071581910000777);
[2013](https://www.researchgate.net/publication/254220651_A_short_version_of_the_visual_aesthetics_of_websites_inventory)).
`(R)` = reverse-scored.

| Facet | α | Items |
|---|---|---|
| Simplicity | .89 | "The layout appears too dense." (R) · "The layout is easy to grasp." · "Everything goes together on this site." · "The site appears patchy." (R) · "The layout appears well structured." |
| Diversity | .86 | "The layout is pleasantly varied." · "The layout is inventive." · "The design appears uninspired." (R) · "The layout appears dynamic." · "The design is uninteresting." (R) |
| Colorfulness | .88 | "The colour composition is attractive." · "The colours do not match." (R) · "The choice of colours is botched." (R) · "The colours are appealing." |
| Craftsmanship | .87 | "The layout appears professionally designed." · "The layout is not up-to-date." (R) · "The site is designed with care." · "The design of the site lacks a concept." (R) |

**VisAWI-S** is one item per facet: *"Everything goes together on this site" ·
"The layout is pleasantly varied" · "The colour composition is attractive" ·
"The layout appears professionally designed."* Same 1–7 scale. The authors'
manual permits swapping "site"/"layout" for "software"/"user interface" for
non-web use — that is author-sanctioned adaptation, not cross-domain
revalidation ([VisAWI manual, 2014](https://www.researchgate.net/publication/266402633_Manual_zum_VisAWI_Visual_Aesthetics_of_Websites_Inventory_und_der_Kurzversion_VisAWI-S_Short_Visual_Aesthetics_of_Websites_Inventory)).

**Why this one matters for direction work:** the *Diversity* facet is the only
validated instrument here that penalises genericness — "the design appears
uninspired", "lacks a concept". It is the closest existing measure of the thing
anti-AI-slop guidance is reaching for.

### F1.2 Ngo's 14 measures normalise to [0,1], and most of them do not correlate with human judgement `[high]`

All 14 are object-placement measures on a 2D frame, ideal = 1
([Ngo, Teo & Byrne, 2000](https://www.researchgate.net/publication/222584252_Formalising_guidelines_for_the_design_of_screen_layouts)).
Order/complexity is simply the mean of the other 13: `Order = Σ mᵢ / 13`,
`Complexity = 1 − Order`.

**What the replication found** ([Moshagen et al., 2010](https://www.researchgate.net/publication/262274197_Investigating_objective_measures_of_web_page_aesthetics_and_usability), 15 webpages):

| Verdict | Measures |
|---|---|
| Correlated with human ratings | Order/complexity (both mono + colour); Density, Proportion, Cohesion, Balance (partial); Proportion + Balance in both conditions |
| **No significant result** | **Equilibrium, Sequence, Unity, Homogeneity** — and nothing worked on text-only or control-only versions |

Zen & Vanderdonckt found Symmetry, Proportion and Simplicity correlated, but
**the published Balance formula did not** until they split horizontal and
vertical balance apart
([2016](https://research.dial.uclouvain.be/entities/publication/d1d77ed6-d0a1-41d3-acb7-0a1c6ea7e1cd)).
Two independent replications disagree about Balance.

**Three named failure modes to carry forward, not bury:**

1. **Construct reduction.** The measures see object rectangles. They cannot see
   colour, texture, typography, content or meaning. A high score means
   *geometrically regular*, not *well designed*.
2. **Segmentation failure.** DOM-derived rectangles cannot represent text inside
   an image, whitespace used as structure, or intra-paragraph spacing. Changing
   the segmentation changes what the metric measures.
3. **Balance ≠ preference.** Experimental work finds weak or absent links
   between computed balance and subjective balance, moderated by grouping,
   orientation, closure and individual differences
   ([Leyssen et al., 2013](https://pmc.ncbi.nlm.nih.gov/articles/PMC3690416/)).

**Practical read: adopt at most four of the fourteen** (Order/complexity,
Density, Proportion, Simplicity), and only on image/component placement.

### F1.3 UICrit is the best designer-grade critique scaffold, with a published codebook `[high]`

3,059 critiques over 983 mobile UIs from seven professional designers
([Duan et al., UIST 2024](https://people.eecs.berkeley.edu/~bjoern/papers/duan-uicrit-uist2024.pdf)).
Five induced topics, with critique counts:

| Topic | n | Codebook sub-codes |
|---|---|---|
| Layout | 696 | clutter, alignment, hierarchy, margins/spacing, redundant elements, visual organisation, whitespace |
| Color contrast | 655 | text, icon, button, element-vs-background contrast |
| Text readability | 591 | size, weight, style, consistency, content clarity, hierarchy, overlap, density |
| Button usability | 601 | placement, visual differentiation, recognition, size, CTA clarity, feedback/affordance, primary-action emphasis, consistency, spacing |
| Learnability | 601 | icon appropriateness, interactive affordance, missing controls/labels, unclear functionality, region purpose, screen purpose |

Ratings: aesthetics, usability and overall design quality on **1–10**;
learnability and efficiency on **1–5**.

**The transferable piece is the critique grammar, not the taxonomy:** every
UICrit critique states *the expected standard → the observed gap → how to close
it*. That is the same three-part shape the repo's existing finding grammar uses,
which makes it cheap to adopt.

**Its own stated limits:** induced from static single-screen mobile UIs; the
authors name error prevention, cross-screen consistency, system-status feedback,
direct manipulation and help/documentation as missing.

### F1.4 Lavie & Tractinsky is ten adjectives; four other instruments give word pairs `[high]`

**Lavie & Tractinsky (2004)** — "This website has a ___ design", 7-point:
Classical = *aesthetic, pleasant, clear, clean, symmetric*;
Expressive = *creative, fascinating, original, sophisticated, uses special
effects* ([paper](https://fsnagle.org/papers/lavie2004assessing.pdf)).

**UEQ** — 7-position semantic differentials, −3…+3
([handbook](https://www.ueq-online.org/Material/Handbook.pdf)):
*Attractiveness* — annoying/enjoyable, bad/good, unlikable/pleasing,
unpleasant/pleasant, unattractive/attractive, unfriendly/friendly.
*Novelty* — dull/creative, conventional/inventive, usual/leading edge,
conservative/innovative. **The Novelty scale is the other validated
genericness measure**, alongside VisAWI's Diversity.

**AttrakDiff 2** HQ-Identity is the "does this read as premium" axis:
isolating/connective, unprofessional/professional, tacky/stylish,
cheap/premium, alienating/integrating, not presentable/presentable
([Würzburg HCI](https://hci.uni-wuerzburg.de/research/AttrakDiff/)).

**meCUE 2.0** Visual Aesthetics is three items, α = .91: *"The product is
creatively designed." · "The design looks attractive." · "The product is
stylish."* ([Minge et al., 2018](https://www.researchgate.net/publication/326683762_The_meCUE_Questionnaire_20_Meeting_Five_Basic_Requirements_for_Lean_and_Standardized_UX_Assessment)).
**BeauVis** is five items, α = .94: *enjoyable, likable, pleasing, nice,
appealing* ([He et al., 2023](https://imld.de/cnt/uploads/BeauVis-09903341-official-IEEE.pdf)).

**If you adopt one thing:** VisAWI-S (4 items) plus UEQ Novelty (4 items) is
eight items, both validated, and together they cover *perceived quality* and
*perceived genericness* — which is exactly the pair the repo lacks.

### F1.5 The two vendor judges publish criteria; only one publishes weights `[moderate]`

**Sifter** — visible design only, at 1440×900 and 390×844, across layout,
typography, colour, imagery quality, visual hierarchy, mobile rendering;
explicitly excludes business and writing quality. Its **0–100 bands** are the
publishable part: 76–100 modern/polished/intentional · 56–75 acceptable but
generic · 31–55 dated/template-like · 0–30 broken or unreadable. **No
dimension-level weights are published**
([Sifter, 2026](https://sifter.so/docs/audits)).

**XSCT Bench** publishes the arithmetic:
`S = 0.5 × S_code + 0.5 × S_visual`, with the visual half weighted
visual_aesthetics 35% · content_completeness 30% · readability 25% ·
visual_polish 10%, each scored 0–100
([methodology](https://www.xsctbench.com/methodology)). It does **not** publish
what earns each score, so the weights are auditable and the judgements are not.

Sifter's "56–75 acceptable but generic" band is worth stealing on its own — it
names genericness as a *score range* rather than a binary.

---

## 2. The generative side: what a direction is made of

### F2.1 There is no canonical UI aesthetic axis list; Bertin's visual variables are the defensible basis `[moderate]` `[inference]`

Bertin's retinal variables — position, size, value/lightness, texture/grain,
hue, orientation, shape — extended in later visualization work with curvature,
transparency/blur/depth and motion
([PNAS, 2018](https://doi.org/10.1073/PNAS.1807180116);
[MIT OCW 6.831, 2011](https://ocw.mit.edu/courses/6-831-user-interface-design-and-implementation-spring-2011/bb4015a05869c5d1838692fc018a800a_MIT6_831S11_lec18.pdf)).
Material 3 independently arrives at colour, type, shape and motion as the
primary expressive levers ([m3.material.io](https://m3.material.io/)), and
Figma's variables operationalise colour, spacing, dimension, typography and
timing with modes
([Figma, 2026](https://help.figma.com/hc/en-us/articles/14506821864087-Overview-of-variables-collections-and-modes)).

**A ten-axis direction sheet** — Bertin's grammar turned into buildable UI
controls. Tagged `[inference]`: no source publishes this table; it is composed
from the three above.

| Axis | Parameterise as |
|---|---|
| Spatial density | minimum spacing unit, grid columns, information-per-viewport |
| Layout order | symmetric ↔ asymmetric; alignment rigidity; grid visibility |
| Type voice | serif/sans/mono; geometric ↔ humanist; weight, width, stroke contrast |
| Type hierarchy | scale ratio, number of levels, display-to-body contrast |
| Chromatic intensity | hue count, chroma ceiling, tonal range, accent allocation |
| Form | rectilinear ↔ organic; corner-radius scale; icon stroke geometry |
| Material / depth | flat ↔ layered; elevation levels, opacity, blur, shadow softness |
| Ornament / texture | none ↔ pattern/grain/illustration; image-to-text ratio |
| Image treatment | photojournalistic ↔ illustrative; crop, grain, saturation |
| Motion character | amplitude, duration, easing, spatial continuity |

These are **not orthogonal** — depth and opacity interact, density and type
hierarchy interact. Treat them as a coverage checklist, not a vector space.
**This table is also the divergence-audit instrument** from the survey's §5: two
directions that differ on fewer than ~4 axes are one direction recoloured.

### F2.1b Layout is co-primary with colour, and the first axis set under-weighted it `[high]`

The strongest experiment found in this survey separates the two. **Seckler,
Opwis & Tuch (2015)** ran five experiments over 25 websites with N=194,
independently manipulating two *structural* factors — vertical symmetry and
visual complexity — against three *colour* factors — hue, saturation and
brightness. **Structural factors had broader and greater effects** on perceived
simplicity, diversity and craftsmanship; colour factors chiefly moved
colourfulness alone; complexity was the only factor that touched every measured
aesthetic facet
([Computers in Human Behavior, 2015](https://www.sciencedirect.com/science/article/pii/S0747563215001776)).
Reinecke et al. reached the compatible conclusion on 450 screenshots with 548
participants — complexity mattered more than colourfulness — though their
complexity measure was not a clean layout-only manipulation
([Reinecke et al., 2013](https://kgajos.seas.harvard.edu/papers/reinecke13aesthetics.pdf)).
Tuch et al. found complexity and prototypicality moving judgement at 50 ms, with
evidence at 17 ms
([Tuch et al., 2012](https://research.google/pubs/the-role-of-visual-complexity-and-prototypicality-regarding-first-impression-of-websites-working-towards-understanding-aesthetic-judgments/)).

**The defensible claim is narrower than "layout beats colour":** structure is at
least co-primary and has wider effects across aesthetic facets than the tested
colour variables. No study cleanly varies only layout versus only palette and
measures *style recognition* as a categorical outcome — that is a real gap.

### F2.1c Two errors the layout evidence exposes in a naive axis set `[high]`

1. **Symmetric / asymmetric / modular is a category error.** Modular is *grid
   grammar*; symmetric and asymmetric are *equilibrium*. A modular grid can be
   symmetric or dynamically unbalanced, so the three are not alternatives on one
   axis. The four canonical grid types — manuscript, column, modular,
   hierarchical — are a pedagogical taxonomy, not mutually exclusive systems;
   compound, baseline, radial and deliberately broken grids are real variants,
   and a baseline grid regulates vertical type position where a column grid
   regulates horizontal placement.
2. **Density and whitespace are two axes, not one.** Density is the amount and
   complexity of visible information; whitespace is the allocation of unused
   area around and within it. Two pages can hold equal density with radically
   different breathing room. Evidence on both sides: readers comprehended better
   with whitespace around content than with meaningless surrounding information,
   and line length showed no significant effect
   ([McMullin et al., 2002](https://doaj.org/article/47ffc9fc3e304d52b918e20df45e2a25));
   a controlled page study scored highest at **45% whitespace** for middle-aged
   and **55%** for younger participants
   ([2018](https://toaj.stpi.niar.org.tw/index/journal/volume/article/4b1141f98e737b1f018e7dd40cc403ed));
   and increasing the *number of groups* decreased aesthetic appeal
   ([Bauerly & Liu, 2006](https://www.sciencedirect.com/science/article/abs/pii/S1071581906000048)).

### F2.1d Müller-Brockmann and Gerstner specify variables, not a taxonomy `[moderate]`

*Grid Systems in Graphic Design* is a construction manual: format, outer
margins, column count and width, gutters, horizontal fields, modules, type
measure, leading, baseline rhythm, and rules for images, captions and display
type, with worked examples at 8, 20 and 32 fields
([CCA Library, 1981](https://library.cca.edu/bib/19410)).
Gerstner takes the stronger position that a grid is a *programme* — a
proportional regulator accommodating unknown content; his *Capital* mobile grid
uses a 10-point base unit, 58 horizontal units, two-unit gutters, and permits
2–6 column divisions without remainder
([*Designing Programmes*, 1964](https://openlab.citytech.cuny.edu/langecomd3504sp2021/files/2018/10/Gerstner_DesigningProgrammes-1.pdf)).
**That supports specifying grid *rigidity and permitted transformations*, not
only a grid type.**

The historical page canons (Van de Graaf, Rosarivo, Tschichold's golden canon —
which the mathematical literature notes has "nothing to do with the golden
section", and reports a 2:3:4:6 inner:top:outer:bottom margin ratio for a 2:3
page, [Max, 2010](https://www.tandfonline.com/doi/abs/10.1080/17513470903458205))
construct a *static text block within a bound page*. They survive as an optional
margin-proportion preset for fixed editorial surfaces; they determine nothing
about reflow, hierarchy or reading order. The "Villard diagram" attribution is
not established — the surviving album is a sketchbook, and no source found makes
it a proven manuscript-layout procedure rather than a later reconstruction.

### F2.1e Reading patterns are behaviour; archetypes are presets, not axes `[moderate]`

NNGroup's patterns describe how people scan, not how to compose: **F-pattern**
(two horizontal scans then a left vertical scan, from 232 participants,
[2006](https://www.nngroup.com/articles/f-shaped-pattern-reading-web-content-discovered/));
**layer-cake** (scan headings, then read beneath a relevant one — NNGroup calls
it far more effective than F-scanning); **spotted**; and **commitment**
([2019](https://www.nngroup.com/articles/text-scanning-patterns-eyetracking/)).
**The popular marketing "Z-pattern" has no equivalent NNGroup experimental
basis** — worth knowing before anyone specifies one.

Single column, split screen, bento, broken grid, full bleed, sidebar-and-canvas,
card grid and editorial multi-column are **structural descriptions assembled
from the axes below** — they belong in the preset set, never in the axis set. A
bento grid is specifically differently-sized rectangular tiles on a shared
modular grid, distinct from a uniform card grid; a broken grid preserves enough
underlying structure for the violation to read as intentional.

### F2.1f The revised axis set: seven structural, eight non-structural `[synthesis]`

Replaces the ten-axis table in F2.1. Structure is now half the sheet, matching
F2.1b. Reflow choreography was considered and **excluded**: W3C treats liquid
reflow as a design decision requiring finesse rather than an implementation
detail
([W3C, 2025](https://www.w3.org/WAI/WCAG22/Techniques/general/G146.html)), and
Jen Simmons' intrinsic web design frames layout as the design era's subject
([2018](https://zeldman.com/2018/05/02/transcript-intrinsic-web-design-with-jen-simmons-the-big-web-show/)),
but no study shows anyone recognising style identity from reflow alone.

| # | Axis | Structural? | Parameterise as |
|---|---|---|---|
| 1 | Grid grammar | yes | manuscript / column / modular / hierarchical / compound / broken; track count; rigidity and permitted transformations |
| 2 | Alignment and equilibrium | yes | edge, centre, or baseline alignment; number of distinct axes; symmetric ↔ dynamically unbalanced |
| 3 | Spatial density | yes | information and group count per screenful |
| 4 | Whitespace distribution | yes | macro margins, gutters, section gaps; micro spacing; compact ↔ expansive |
| 5 | Hierarchy and scale contrast | yes | flat ↔ steep; hero dominance; span and size jumps |
| 6 | Containment and boundary strength | yes | open field ↔ ruled ↔ carded or panelled; whether overlap is permitted |
| 7 | Section and scroll rhythm | yes | continuous ↔ episodic; regular ↔ varied; bleed cadence |
| 8 | Type voice | no | serif, geometric sans, humanist sans, monospace; weight and width range |
| 9 | Type hierarchy | no | scale relationship; level count; display-to-body distance |
| 10 | Chromatic intensity | no | hue count; chroma ceiling; tonal range; where accent is spent |
| 11 | Form | no | rectilinear ↔ organic; corner treatment across the scale; icon stroke character |
| 12 | Material and depth | no | flat ↔ layered; elevation levels; how depth is signalled |
| 13 | Ornament and texture | no | none, pattern, grain, illustration; image-to-text ratio |
| 14 | Image treatment | no | photographic, illustrative, abstract; crop and tone |
| 15 | Motion character | no | amplitude; relative duration; continuous ↔ discrete; productive ↔ expressive |

Fifteen axes. Two of the researcher's eight structural candidates were merged
rather than shipped whole: hierarchy and scale contrast (5) absorbs what a
separate figure-ground axis would have carried, and alignment and equilibrium
(2) absorbs symmetry, which is not an opposite of grid grammar. Alignment
changes both aesthetic and usability ratings
([Seckler et al., 2017](https://escholarship.org/uc/item/34b1n9zv)); rhythm,
density and equilibrium are recognised as distinct layout-aesthetic factors
([Zhang et al., 2020](https://pmc.ncbi.nlm.nih.gov/articles/PMC7085848/)).

### F2.2 Named styles have formal commitments, but of very unequal firmness `[moderate]`

| Style | Formal commitments | Source firmness |
|---|---|---|
| Swiss / International Typographic | asymmetric composition, explicit grid, sans-serif, flush-left ragged-right, photography over illustration, near-zero ornament, restrained colour | **Firm** — [Swiss National Library](https://www.nb.admin.ch/en/the-international-style-1950-1970), [Cooper Hewitt, 2018](https://www.cooperhewitt.org/2018/08/05/aharmonyofcontrasts/) |
| Bauhaus | function-led construction, simple balanced geometry, limited geometric primitives, type integrated with composition | **Firm** — [MoMA, 2021](https://www.moma.org/calendar/galleries/5388). The red/yellow/blue + circle/square/triangle shorthand is recognisable but not a rule |
| Editorial / broadsheet | rigid 5–6 column grid, strong type hierarchy, modular story units, image/caption relationships, rules | **Firm** — a production grammar, not an art movement: [Poynter, 2003](https://www.poynter.org/reporting-editing/2003/the-grid-the-structure-of-design/) |
| Material | tactile surfaces, elevation hierarchy in `dp`, shadows as depth, meaningful motion | **Firm** — [Google, 2014](https://developers.googleblog.com/this-is-material-design/) |
| Memphis / postmodern | high-chroma colour, wild repeat patterns, geometric/irregular collision, asymmetry, anti-functionalist decoration | **Moderate** — [Vitra, 2021](https://www.design-museum.de/en/exhibitions/detailpages/memphis-40-years-of-kitsch-and-elegance.html) |
| Glassmorphism | semi-transparent fill, **backdrop blur sampling what is behind**, thin luminous border, soft elevation, visible colourful substrate | **Practitioner only.** The blur-sampling rule is the real definition; plain transparency is not the effect |
| Brutalism (web) | exposed/default HTML structure, document flow, raw or system/mono type, unstyled controls, abrupt contrast, anti-polish | **Weak — and deliberately anti-systematic.** The scholarly source says the premise is placing elements without concern for conventional composition ([Suárez-Carballo, *Doxa*, 2019](https://repositorioinstitucional.ceu.es/bitstream/10637/10441/2/Visual_FernandoSuarez_Doxa_2019_eng.pdf)) |
| Neumorphism | same background and surface colour, paired diffuse light/dark shadows, low-contrast extruded controls, pastel palette | **Weak** — no canonical spec; material accessibility risk from low contrast |

**The firmness column is the decision.** A Swiss or editorial preset can be
specified and checked. A brutalist preset cannot be checked *by construction* —
its own definition rejects the composition rules a check would assert. That is
not a gap in the research; it is a property of the style.

### F2.3 Typography, colour and motion are genuinely specifiable — with numbers `[high]`

**Type.** Bringhurst: **66 characters per line** as the benchmark, **45–75
acceptable** for a single column, ~40 as a floor for justified text (below
which, go ragged-right)
([excerpt](https://niccomedia.com/wp-content/uploads/2023/04/Typography-A-Visual-History-by-Robert-Bringhurst.pdf)).
**But the evidence does not support a universal optimum:** a screen study of
35/55/75/95 CPL found **95 CPL read *faster*** with no satisfaction effect
([Shaikh & Chaparro, 2005](https://journals.sagepub.com/doi/abs/10.1177/154193120504900514);
[Visible Language, 2005](https://journals.uc.edu/index.php/vl/article/view/5765)).
Specify a range, then test the context. Modular scale ratios and 1.5–1.618
line-height are **design conventions, not readability findings**.

**Colour.** OKLCH beats HSL for palettes for a stateable technical reason: HSL
is a geometric transform of RGB, so equal HSL lightness ≠ equal perceived
lightness; OKLab was built to predict perceived lightness, chroma and hue
([Ottosson, 2020](https://bottosson.github.io/posts/oklab/)). That makes
equal-lightness ramps predictable. Material's HCT uses Hue 0–360, Chroma ~0–120,
Tone 0–100 with 13 scheme-level tonal steps drawn from a wider stored set
([material-color-utilities](https://github.com/material-foundation/material-color-utilities/blob/main/concepts/dynamic_color_scheme.md)).

**Radix's 12-step scale is the most directly reusable colour artifact found**,
because each step has a *job*: 1 app background · 2 subtle background ·
3–5 component/hover/active backgrounds · 6–8 subtle/interactive/strong borders
and focus rings · 9–10 solid/solid-hover · 11–12 low-/high-contrast text, with
11 and 12 targeting APCA Lc 60 and Lc 90 over step 2
([Radix](https://www.radix-ui.com/colors/docs/palette-composition/understanding-the-scale)).

**APCA is not a WCAG 2 substitute.** WCAG 2 uses a symmetric luminance ratio
(4.5:1 normal text); APCA is polarity-sensitive and size/weight-aware; WCAG 3 is
still a **Working Draft** ([W3C](https://www.w3.org/TR/wcag-3.0/)). Legally
required conformance remains WCAG 2.

**Colour harmony does not predict preference.** Controlled work finds preference
strongly hue-dependent, challenging hue-distance-only theories, with harmony
entangled with single-colour preference, similarity, saturation, context and
culture ([iScience, 2026](https://pmc.ncbi.nlm.nih.gov/articles/PMC13264017/);
[Palmer, Schloss & Sammartino, 2013](https://palmerlab.berkeley.edu/pdf/PalmerSchlossSammartino%282013%29AR.pdf)).
Use harmony templates to *generate* candidates, never to *justify* one.

**Motion.** IBM Carbon is the only published motion *personality* dichotomy with
actual curves: **productive** standard `cubic-bezier(0.2, 0, 0.38, 0.9)`, exit
`cubic-bezier(0.2, 0, 1, 0.9)`; **expressive** standard
`cubic-bezier(0.4, 0.14, 0.3, 1)`, exit `cubic-bezier(0.4, 0.14, 1, 1)`
([Carbon](https://carbondesignsystem.com/elements/motion/overview/)). Apple HIG
takes the opposite stance — prefer system motion; custom motion must communicate
feedback, hierarchy or process
([HIG](https://developer.apple.com/design/human-interface-guidelines/motion)).

**Grid.** The 8-point grid is an implementation convention with no canonical
inventor and no proven perceptual optimum — its value is coherent scaling and
simpler handoff. Fluid type is `clamp(min, preferred, max)`
([MDN](https://developer.mozilla.org/en-US/docs/Web/CSS/Reference/Values/clamp)).
Grid alignment needs an optical correction pass; mathematically identical
bounding boxes can look uneven.

### F2.4 Brand-personality frameworks split sharply on evidence `[moderate]`

**Aaker's five dimensions** — Sincerity, Excitement, Competence, Sophistication,
Ruggedness — have a published reliability and validity basis
([Aaker, JMR 1997](https://doi.org/10.1177/002224379703400304)), but specify
*brand associations*, not visual tokens; they need translating through §2.1.

**Mark & Pearson's twelve archetypes** are widely used and weakly evidenced;
contemporary scholarship questions their practical relevance and the premise
that a brand inhabits one pure archetype
([Business Horizons, 2023](https://doi.org/10.1016/j.bushor.2022.11.001)).
**Use archetypes to generate territories, never to validate a decision.**

Agency brief practice converges on: objective and metric · audience and desired
response · single-minded proposition · brand personality · deliverables and
constraints · mandatories and exclusions · **one or more visual territories
(reference images plus the formal rules they imply)** · approval owner.
Some studios explicitly present two or three distinct directions before
selection ([Demand Metric template](https://www.demandmetric.com/content/creative-brief-template);
[Suramya Studio, 2026](https://www.suramya.co/mood-board-and-creative-direction-design)).
The bridge from moodboard to spec is **not** "use these images" — it is: state
each territory's intended response, then translate it into rules for palette,
type, image treatment, form, space, material and motion.

---

## 3. What the published skills actually do

### F3.1 Anthropic ships four design skills, not one, and they use three different mechanisms `[high]`

Read directly from raw source, 2026-09-18.

**`frontend-design` (71 lines)** — headings: *Ground your designs in the subject
matter · Design principles · Process: plan, review against the brief, build,
critique · Restraint and self-critique · More on writing in design*.

Its framing is a role, not a rule: "the design lead at a design studio known for
giving every client a distinct visual identity… This client has already rejected
proposals that felt cliché or templated." Grounding is the first move — "The
subject's industry, subject matter, materials, and vernacular are where
distinctive visual choices come from — a design for a toy for girls aged 8–11
will be very aesthetically different from a dashboard for financial analysts."

The **four-field plan**: Color (4–6 named hex values) · Type (typefaces and
their roles) · Layout (one-sentence prose concepts plus ASCII wireframes,
including the alignment decision) · Principles (what makes this page unique).

The **review gate is the mechanism worth copying**, and it is unusual: *"work
through a similar prompt to see if you arrive somewhere similar"* — a
self-administered counterfactual. If the plan matches what you'd produce for any
similar brief, revise it and say what changed and why. Only then write code.

Its five AI-default clusters are stated with hex values, and one is a pointed
admission: warm cream near `#F4F1EA` with a terracotta accent "often near
`#D97757` — Anthropic's own Claude-interaction accent, so on a user's brief it
reads as a tell." Plus: near-black with acid-green/vermilion; broadsheet
hairline rules with zero radius; the SaaS-card kit (identical rounded cards, one
radius regardless of hierarchy, `rgba(0,0,0,.1)` shadows, gradient washes);
template chrome (tracked-out ALL-CAPS eyebrows, `A · B · C` middots,
`WORD — fragment` spaced em dashes, tinted near-blacks `#0B0B0B`/`#111`
standing in for black, monospace micro-labels, `→` appended to buttons).

Crucially qualified: "All traits are legitimate for some briefs, but they are
defaults rather than choices… the brief's own words always win, including when
it asks for one of these looks. Where it leaves an axis free, don't spend that
freedom on one of these defaults."

Type rules are concrete: one or two families, clearly distinct if two; line
length **under 80 characters**; serifs slightly longer with more line-height;
and three banned treatments — accenting a single word in a headline, all-caps
labels, unnecessary labels above content. Numbered markers (01/02/03) only if
the content genuinely is a sequence. Non-user-triggered motion sparingly — "one
page-load sequence or one reveal" beats scattered effects.

Closing discipline: "Spend your boldness in one place." Plus Chanel's mirror
test — remove one accessory. And a quality floor stated *without* ceremony:
"responsive down to mobile, visible keyboard focus, reduced motion respected,
visually accessible, harmonious color palettes."

**`theme-factory` (59 lines)** — the preset mechanism, and it is deliberately
thin. Ten named themes (Ocean Depths, Sunset Boulevard, Forest Canopy, Modern
Minimalist, Golden Hour, Arctic Frost, Desert Rose, Tech Innovation, Botanical
Garden, Midnight Galaxy). Each theme file is ~15 lines: 4 hexes with roles, a
header/body font pair, and a **"Best Used For"** line ("Corporate presentations,
financial reports, professional consulting decks, trust-building content").
The workflow **requires human selection**: show `theme-showcase.pdf`, ask, wait
for explicit confirmation, then apply. Custom themes are generated on the fly
and shown for review before use.

**`canvas-design` (129 lines)** — the philosophy mechanism, and the most
interesting one. It generates a *named art movement* (1–2 words: "Brutalist
Joy", "Chromatic Silence", "Metabolist Dreams") plus a 4–6 paragraph manifesto
covering space and form, colour and material, scale and rhythm, composition and
balance, visual hierarchy. Two instructions stand out: **"Leave creative space"**
— be specific about direction but concise enough that the next agent has
interpretive room; and **"Keep the design philosophy generic without mentioning
the intention of the art, as if it can be used wherever"** — the philosophy is
deliberately decoupled from the brief so it can be reused. It also has a
"deducing the subtle reference" step: the subject is woven in as a quiet
conceptual thread, "like a jazz musician quoting another song."

**`brand-guidelines`** — the opposite pole: fixed tokens, five colours, Poppins
headings, Lora body, three accent colours cycling through shapes. No judgement,
no choice.

**Four mechanisms, one repo: role framing + counterfactual review
(`frontend-design`), human-selected presets (`theme-factory`), generated
manifesto (`canvas-design`), fixed tokens (`brand-guidelines`).** They are not
alternatives — they sit at different points on a
*how much is already decided* axis.

### F3.2 Measured: the largest named-style pack's presets differ by ~8 lines out of 86 `[high]`

TypeUI (`bergside/awesome-design-skills`, the "48 design skills" collection,
now 67) is the strongest named-style pack found — Brutalism, Editorial,
Glassmorphism, Claymorphism, Bento, Dithered, Doodle, Corporate, Cosmic and more
([TypeUI](https://github.com/bergside/typeui)).

**I diffed four of them.** Glassmorphism vs Editorial: 86 lines each, differing
in the name, description, four Style-Foundations lines, and a handful of
accessibility/tone/rule words. Identical across all four: Mission, Expected
Behavior, Guideline Authoring Workflow (6 steps), Required Output Structure
(7 sections), Component Rule Expectations, QA checklist.

Three defects the diff exposes, none of which a description-level read would
catch:

1. **Brutalism contradicts itself.** Its own description is "raw, anti-design…
   unadorned elements, jarring layouts," yet it inherits the shared rules
   *"preserve visual hierarchy"*, *"avoid inconsistent spacing rhythm"* and
   *"avoid decorative motion without purpose"*. The preset asserts the rules the
   style exists to break. This is F2.2's firmness problem, realised.
2. **Brutalism's primary is `#DD614C`** — a warm terracotta, which is precisely
   Anthropic's AI-default cluster #1. The preset ships the tell.
3. **Glassmorphism carries a stray brand line** — "provide fast, reliable
   communication for individuals, teams, and communities… across desktop
   environments" — a chat-app blurb left inside a style definition. Editorial
   has no such line. The files are template-generated and not proofread.

**This measurement changes a round-1 conclusion.** I said presets were
underexplored because no tool ships a named picker. They *are* shipped, at
scale, by TypeUI — and the shipped form degenerates into a token swap wearing a
shared process document. The risk isn't that presets don't exist; it's that they
converge on exactly the genericness they're sold as curing.

### F3.3 The executable instructions in the wild specify systems and structure, not adjectives `[moderate]`

**Bolt.diy's prompt** is open source and blunt: "Create visually stunning,
unique, highly interactive, content-rich, and production-ready applications.
Avoid generic templates"; "Establish a distinctive art direction"; "Implement a
systemized spacing/sizing system (e.g., 8pt grid, design tokens)"
([StackBlitz Labs](https://github.com/stackblitz-labs/bolt.diy/blob/main/app/lib/common/prompts/prompts.ts)).
It demands both systemisation *and* distinctiveness in one breath — the tension
named in §4 below.

**Google's Stitch skill has the cleanest architecture found**: first check
whether the project already has a design system; if it does, **do not repeat
colours, fonts, themes or roundness in the screen prompt**. Then translate vague
language into concrete UI terminology and generate from a structure template
(purpose, platform, header, hero, main content, footer)
([google-labs-code/stitch-skills](https://github.com/google-labs-code/stitch-skills/blob/main/plugins/stitch-design/skills/generate-design/SKILL.md)).
**Tokens are project-level state; the per-surface prompt controls information
architecture.** That separation is directly portable to this repo's
`creative-direction` → `design-system` → `frontend-engineering` chain.

**Anti-slop packs refuse to choose a style.** `no-slop-ui` blocks glass panels,
decorative gradients, huge rounded shells, dashboard heroes, fake metrics, vague
SaaS copy, bouncy hover, generic purple/blue
([LeoStehlik](https://github.com/LeoStehlik/no-slop-ui)); `anti-slop` is 38
mandatory rules with a PASS/FAIL delivery gate and explicitly **delegates beauty
to a separate `DESIGN.md`**
([miqdadbadjuber](https://github.com/miqdadbadjuber/anti-slop)). That delegation
is the right instinct: a prohibition list is a filter, never a direction.

**Consensus shape across all of it:** tokens are the most common mechanism;
prohibitions are second; presets are common only in dedicated packs; a planning
artifact appears in the higher-craft skills; **explicit visual review
(screenshot critique) is the least common and the highest-value.**

### F3.4 Visual references beat prose; planning-before-code is unproven `[moderate]`

A study generating 84 UIs across three services found multimodal prompts scored
significantly higher than text-only: **+50.9%** (Stable Diffusion 1.5),
**+40.5%** (KreaAI), **+9.1%** (UI/UX LoRA) — and, counterintuitively, **simple
wireframes outperformed detailed screenshots** (+43.6% KreaAI, +32.4% SD)
([2025](https://eurekamag.com/research/099/441/099441995.php)). A 13-practitioner
study found free-form visual prompting more intuitive for ideation, while
semantic-constrained prompting produced higher-fidelity results
([Calò & De Russis, 2025](https://tommasocalo.github.io/papers/uiprompt)).

**Apple's designer-feedback work is the strongest evidence for critique over
planning:** 21 designers produced ~1,500 comments, sketches and direct
annotations; models trained on that designer-aligned feedback beat
ranking-feedback baselines and GPT-5 in human evaluation
([Apple ML Research, 2026](https://machinelearning.apple.com/research/designer-feedback)).

**No controlled study isolates "token plan + wireframe + self-review before
code" and shows a causal aesthetic improvement.** Anthropic's process is
well-reasoned and unvalidated. The evidence supports *structured visual input*
and *iterative critique* — which is an argument for the ASCII-wireframe and
screenshot-critique halves specifically, not the whole three-step sequence.

No rigorous head-to-head exists for three claims people treat as settled:
naming a real product beats an adjective; prohibition lists beat positive
direction; token specs beat a well-written vibe brief.

### F3.5 Measuring whether N designs actually differ: four named metrics, one caveat `[moderate]`

The four metrics in the LLM design-diversity study are **mean pairwise distance
(MPD)** — global spread; **minimum pairwise distance (MinPD)** — nearest-
neighbour separation, which is what catches clones; **convex-hull volume** —
extent of embedding space explored; and **DPP diversity** — penalises
semantically redundant sets. Across 4,000 generated solutions, **human solutions
were consistently more diverse on all four**, and temperature/top-p of 1/1 was
the most diverse LLM setting
([Ma et al., 2024](https://arxiv.org/abs/2405.02345)).
**Caveat the paper itself imposes:** these were *textual* design solutions.
Applying them to rendered UI requires an explicit screenshot or layout
representation first.

For UI specifically: UIHash-style appearance representation reported **F1 0.984**
for similar-UI detection ([2023](https://jun-zeng.github.io/file/uihash_paper.pdf));
DOM/layout-tree similarity catches shared hierarchy behind different paint; and
**CIEDE2000 ΔE** between extracted palettes is the standardised palette-distance
measure ([CIE, 2022](https://www.cie.co.at/publications/colorimetry-part-6-ciede2000-colour-difference-formula-1)).

**Report MinPD, not the mean.** A set of five where four are near-identical and
one is an outlier has a respectable mean pairwise distance and is not a diverse
set.

---

## 4. How the two halves compose `[synthesis]`

Synthesis across §1–§3, not a cited claim.

**The composition, in the repo's existing pipeline.** Nothing here needs a new
primitive — every piece attaches to a skill that already exists.

| Stage | Owner today | What this research adds |
|---|---|---|
| Ground the brief | `creative-direction` | Subject-first grounding (F3.1); Aaker for personality vocabulary, archetypes for territory generation only (F2.4) |
| Name the direction | `creative-direction` | 3 territories, each a named direction + intended response (F2.4); `canvas-design`'s "leave creative space" (F3.1) |
| Specify it | `creative-direction` artifact | **The ten-axis sheet (F2.1)** — this is the missing artifact section; plus firm named-style commitments where one applies (F2.2) |
| Review the plan | *nothing* | **Anthropic's counterfactual gate (F3.1)** — "work through a similar prompt; if you land somewhere similar, revise and say what changed" |
| Derive tokens | `design-system` | Radix's 12-step job semantics, OKLCH for ramps, Carbon's productive/expressive curves (F2.3) |
| Build | `frontend-engineering` | Stitch's separation: don't restate tokens per surface (F3.3); wireframe-first (F3.4) |
| Critique | `design-review` | VisAWI-S + UEQ Novelty (8 items); UICrit's standard→gap→remedy grammar; Sifter's "acceptable but generic" band (F1.1, F1.3, F1.5) |
| Audit divergence | *nothing* | **MinPD over the ten axes (F3.5)** — the only control with no prior art to copy |

**Five things to build, in dependency order:**

1. **The ten-axis direction sheet** as a section in the `creative-direction`
   template. Highest value, lowest risk, no new skill. It gives the direction
   document a checkable shape, satisfies the repo's existing anti-adjective
   stance, and doubles as the divergence instrument.
2. **The counterfactual review gate.** One paragraph. It is the single most
   distinctive mechanism in any published skill and it costs nothing.
3. **VisAWI-S + UEQ Novelty (8 items)** into `design-review`'s taste critique.
   Both validated; together they cover quality and genericness, which is the
   pair the repo lacks.
4. **Firm-style presets only** — Swiss, editorial, Material, Bauhaus. Ship them
   as pre-filled creative-direction documents (theme-factory's "Best Used For"
   line plus §2.2's formal commitments), not as skills. **Do not ship
   brutalism or neumorphism as checkable presets**; F2.2 and F3.2 both say they
   cannot be.
5. **The divergence audit**, MinPD over the axes. Last, because it only matters
   once explore mode exists.

**The unresolved tension, stated rather than smoothed.** Bolt's prompt demands
"a systemized spacing/sizing system" *and* "a distinctive art direction" in the
same breath. Design-system critics argue coherence can undermine recognition
([Hurst, 2026](https://www.hurst.world/io/material-designs-icon-paradox-when-coherence-undermines-recognition)),
and a Berkeley study of 13 prompt-mediated design sessions names a
**Convergence Trap** and a **Tacit Ceiling** among six failure modes, prescribing
visual input and visible authorship rather than more prescriptive prompting
([UC Berkeley I School, 2026](https://www.ischool.berkeley.edu/programs/mims/projects/2026/aesthetic-taste-and-its-limits-breakdowns-prompt-mediated-design-user)).
The resolution the sources jointly support is a **two-layer split**: hard rules
for accessibility, tokens, responsiveness, states and implementation fidelity;
an explicit, separately-staged art-direction step for the choices that create
recognition. F3.2 is what happens when the two layers get merged into one file.

---

## Known unknowns

- **Known-unknown:** does the counterfactual review gate ("would I produce this
  for any similar brief?") actually change output? Would be closed by: an A/B
  over one brief with and without the gate, scored on VisAWI-S + UEQ Novelty by
  raters blind to condition. This is the cheapest high-value experiment here.
- **Known-unknown:** how many of the ten axes must differ before humans call two
  directions genuinely different? Would be closed by: generating pairs that
  differ on 2, 4, 6 and 8 axes and asking raters "same underlying direction?"
  Without this the divergence threshold is a guess.
- **Known-unknown:** do VisAWI's Diversity facet and UEQ's Novelty scale measure
  the same thing on generated UI? Would be closed by: running both on one corpus
  and correlating. If they correlate highly, adopt four items rather than eight.
- **Known-unknown:** whether MPD/MinPD/hull/DPP transfer from text to rendered
  UI. Would be closed by: the screenshot or layout representation the paper says
  is prerequisite — UIHash embeddings are the obvious candidate.
- **Known-unknown:** Sifter's dimension weights and XSCT's per-band definitions.
  Would be closed by: the vendors publishing them. Neither has.
- **Unknowable (as posed):** whether a brutalist direction can be mechanically
  checked. Not a missing-evidence problem — the style is defined by rejecting the
  compositional rules any check would assert (F2.2). Any check would measure
  conformance to a grammar the style repudiates. It belongs in a human-reviewed
  lane, and F3.2 shows what happens when it isn't.
- **Unknowable (as posed):** whether prescriptive rules can produce distinctive
  work, in general. Both sides are well-evidenced under different conditions —
  rules demonstrably lift the floor (Carbon, WCAG, state coverage) and
  demonstrably compress the ceiling (Hurst, Berkeley's Convergence Trap). This
  is an irreducible tension, not a finding; it is why §4 splits into two layers
  rather than picking a side.
