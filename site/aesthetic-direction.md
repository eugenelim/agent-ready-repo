# Aesthetic Direction — agent-ready-repo site

**Surface:** responsive-web documentation site  
**Audience:** senior engineers and engineering leads evaluating adoption

## Named goals (ranked)

### 1. Signal clarity *(dominant)*
A senior engineer scans the landing page in 15 seconds and knows exactly what this is, what the three loops do, and whether to read further. Every section has one job. Section breaks are whitespace, not rules or decorative chrome.

**Referents:** Linear docs (information hierarchy unambiguous at every zoom level), Nielsen's information-scent principle  
**Violates if:** badges, secondary metadata, or decorative dividers appear before the value proposition is clear

### 2. Earned authority
The site projects confidence through precision and restraint — not marketing inflection, not selling. Trust is built the way good technical writing builds it: by being exactly right.

**Referents:** Vercel docs (no unnecessary chrome), Stripe developer docs (zero decoration, total clarity), Hemingway's iceberg rule  
**Violates if:** superlatives, vague claims, or visual decoration substitute for specific, accurate description

### 3. Typographic intelligence
Code and prose are equal first-class citizens. The type scale is decisive, not decorative. Inline code doesn't interrupt reading; it clarifies it.

**Referents:** Inter typeface design intent (clarity at text size, weight at display), MDN typography standards, JetBrains Mono (legibility in mixed prose contexts)  
**Violates if:** code is visually heavier than prose, type sizes are arbitrary rather than scale-derived

### 4. Measured depth
The information architecture rewards exploration without demanding it. The above-fold view is the one job; everything else opens naturally from it.

**Referents:** Progressive disclosure (Miller's Law), Hick's Law (fewer choices at decision points = faster decisions)  
**Violates if:** 14 packs presented as equal-weight choices without hierarchy or entry point

## Conflict arbitration

| Conflict | Winner | Reason |
|---|---|---|
| Clarity vs. authority (dramatic hero obscures content) | Clarity | Signal first, always |
| Authority vs. depth (more info = more noise) | Authority | Restrained surface, depth behind a click |
| Typography vs. decoration | Typography | Icons earn their place or are cut |
| Depth vs. clarity (first-load complexity) | Clarity | Collapse until asked |

## Quality floor (non-negotiable)
WCAG AA contrast ratios, visible focus states, `prefers-reduced-motion` respected. Floor wins over every aesthetic goal without exception.
