# QA: experience-design skill boundaries

## Session boundary

**In scope:** content and routing changes in the experience-design pack page,
guide home, and generated guide reference; the 20-skill count; job-first
comprehension; strategy, product-shaping, frontend, and copy-layer exits; the
user-approved rich-text spacing and containment rules in the shared pack-page
description container; rendered behavior at 375px and 1280px.

**Documented but not exercised as change scope:** pack-template structure,
documentation templates, navigation components, visual tokens, and unrelated
pack content. The existing missing space between “Desktop.” and “Browse the
catalogue” is visible in baseline and final marketing captures. It predates this
change and remains outside the approved rich-text-style amendment.

## Routes and evidence

| Surface | Route | Baseline evidence | Final evidence |
| --- | --- | --- | --- |
| Marketing pack page | `/agent-ready-repo/packs/experience-design/` | Durable findings and viewport observations are recorded in “Baseline design review” below. | The final DOM contains the five named job/exit headings and exactly 20 `.skill-item` elements; viewport and focus observations are recorded below. |
| Generated reference | `/agent-ready-repo/docs/guides/experience-design/reference/experience-design/` | Source and build inspected before authoring; no separate baseline capture was needed for the content finding. | The final DOM contains all 20 skill contract headings plus the reviewer, `[design]` layout, and shared-quality-floor sections; viewport observations are recorded below. |
| Shared pack-style compatibility | `/agent-ready-repo/packs/linear/` | Existing content uses H3 headings, dividers, code blocks, and a table. | The final 375px render preserved those structures without page-level overflow. |

Screenshots were generated under the repository-ignored `build/` directory for
live visual review only. The durable evidence is the inline finding record,
rendered DOM assertions, viewport measurements, and focus sequence in this file;
it does not depend on ignored image artifacts.

## Baseline design review

Grounded aesthetic reference:
`docs/specs/platform-site/aesthetic-direction.md` — precision authority,
staged revelation, grounded ambition, and identity specificity. No separate
`docs/design/principles` artifact exists.

| Severity | Finding | Disposition |
| --- | --- | --- |
| Major | The page claimed 19 skills while the manifest listed 20. | Resolved. The hero and canonical template inventory now report 20. |
| Major | The page opened with a raw capability inventory, so a cold evaluator could not identify a natural job or adjacent-discipline exit first. | Resolved. Natural request, four job families, copy sequence, and discipline exits precede the template inventory. |
| Major | The global CSS reset removed all Markdown margins while the shared pack-description container supplied no descendant typography, collapsing headings, paragraphs, and lists into an undifferentiated stream. | Resolved after two content-only spacing attempts proved ineffective. The user approved a scope amendment; the shared container now applies token-based semantic rhythm and horizontal containment without changing its structure. |
| Out of scope | Shared-template text joins “Desktop.” and “Browse the catalogue” without a space. | Documented, not exercised. It is outside the approved descendant-style amendment. |

The baseline marketing layout remained coherent at 375px and 1280px with no
visible page-level horizontal overflow.

## Final design review

### Five-second comprehension

- **What:** the opening says the pack turns an understood user need into a
  coherent, reviewable design before implementation.
- **Who:** product teams are named in the first sentence; the tagline retains
  the design/UX-seat framing.
- **Where to start:** a natural request appears before the first heading, then
  four job families route understanding, screen decisions, creative/content
  direction, and surface genre.
- **When to leave:** product strategy, product-engineering shaping, and frontend
  implementation exits appear before the skill inventory. The copy sequence is
  brand register → surface message/structure → acquisition copy goals → product
  UI strings.

### Responsive observations

| Width | Marketing page | Generated reference |
| --- | --- | --- |
| 1280px | Jobs and exits form a readable column with clear heading-to-body grouping before a single 20-chip inventory. The boundary list and reviewer paragraph are separated. Install code blocks remain contained. Header, journey link, reference link, and footer navigation are visible. No page-level overflow. | Left navigation, article, table of contents, 20-entry intent index, all skill contracts, reviewer, layout, and quality-floor sections render. The intent table remains contained within the article surface. No page-level overflow. |
| 375px | Hero reports 20 skills; headings, paragraphs, the boundary list, reviewer note, chips, install blocks, journey card, and footer form distinct scan groups without clipping. The single inventory follows jobs and exits. No page-level overflow. The Linear compatibility capture confirms shared H3, divider, code-block, and table treatment remains readable and contained. | Mobile navigation and the complete reference render in one reading column. The intent index remains inside the content viewport, followed by all 20 sections and reviewer material. No page-level overflow. |

Static captures show the responsive navigation shells and all changed links.
The final 375px Playwright probe reported `scrollWidth: 375` and
`clientWidth: 375`. Ten successive Tab presses reached, in order: skip link,
brand link, mobile-menu summary, agentbundle link, copy button, Claude Code
link, catalogue link, journey card, full-reference link, and footer Docs link.
The existing global focus ring therefore remains available across every changed
page region, with no hidden or trapped focus observed.

### Finding disposition

No in-scope severity-3-or-higher finding remains open. The two baseline content
findings and the rendered-QA typography finding are resolved. The final
experience-design captures pass the design-review quality floor; the Linear
compatibility capture shows no shared-style regression or page-level overflow.

## Commands and exits

| Command | Result |
| --- | --- |
| `python3 tools/validate_guides.py` | Exit 0; 0 errors and existing migration warnings. |
| `python3 tools/check-guide-index.py` | Exit 0; all active packs present. |
| `python3 tools/test-run-pack-evals.py` | Exit 0 in the local terminal. The managed assistant runtime reached tempfile-backed cases and could not create a temp directory. |
| `FORCE=1 make build-self` | Exit 0; `catalogue self-host --write: ok`. |
| `make site-build` | Initial T4 attempt failed because `docs-site` dependencies were absent; the work-loop recorded the attempt. After `npm ci --prefix docs-site`, exit 0. Final rebuild: web and docs complete; 217 documentation pages indexed and sitemap emitted. |
| `agentbundle catalogue verify --root .` | Exit 0 in the local terminal. |
| `agentbundle catalogue lint --root .` | Exit 0; clean. |
| `agentbundle catalogue lint --root . --deep` | Exit 0; existing repository warnings only, none in changed experience-design content. |
| `python3 tools/check-contract-drift.py --root .` | Exit 0; relocation warning only. |
| 375px Playwright overflow/focus probe | `scrollWidth` equals `clientWidth` at 375; ten-step focus order reaches navigation, install, journey, reference, and footer controls without a trap. |
| `npm run test --prefix web` | Exit 0 in the local terminal after the shared pack-description style amendment. |
| `SKIP_SAST=1 make build-check` | Exit 0 on the final implementation tree. |

## Reviewer outcomes

| Reviewer | Outcome |
| --- | --- |
| `adversarial-reviewer` | Clean after three applied reference-contract corrections and one specialist-disposition re-entry pass. |
| `quality-engineer` | Clean; covered activation evals, durable QA evidence, shared-template regression risk, projections/versioning, and maintainability. |
| `security-reviewer` | Clean after two pre-existing workflow-security concerns received explicit deferred dispositions in `notes/review-security-1.md`; this diff introduces no new authority. |
| `experience-reviewer` | Named skip: this runtime exposes no such reviewer role. Authoring-time `design-review`, 375px/1280px renders, and the grounded platform-site aesthetic direction cover the reader-facing lens. |
| `frontend-reviewer` | Named skip: this runtime exposes no such reviewer role. Green web tests, token-only descendant styles, two viewport renders, the Linear compatibility render, and the focus/overflow probe cover the changed CSS surface. |

All 12 acceptance criteria are satisfied. After every other criterion and
review passed, lifecycle closeout moved `spec/xd-skill-boundaries` from
`ini-003.work.queue` to `ini-003.work.shipped`, marked the spec `Shipped`, and
marked the plan `Done` while preserving downstream dependency references.
