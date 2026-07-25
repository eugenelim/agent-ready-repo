# Tutorial: Design token chain — from aesthetic direction to working foundation

This tutorial walks the two-skill design token chain using a concrete example: a professional SaaS analytics dashboard. You will run `design-token-taxonomy` to derive the token taxonomy from a named aesthetic direction, then run `design-system-foundations` to apply it as a working foundation — arriving at a real component token set with CSS custom property names.

By the end, you will have:

- A token taxonomy derived from a named aesthetic direction
- A semantic token structure for the full lightweight foundation
- A concrete before/after button component token set showing what working tokens look like
- A clear handoff to the next step (component state machines, screen layout)

**Pre-requisites:** `experience-design` pack installed; a committed aesthetic direction (from `creative-direction`).

---

## The chain

```
creative-direction  →  design-token-taxonomy  →  design-system-foundations
(named direction)      (token/scale taxonomy)     (working foundation)
```

`design-token-taxonomy` names what tokens are *for* and derives the organizing scales from the aesthetic direction. `design-system-foundations` applies the taxonomy as a working foundation — semantic token sets, alias layers, and component tokens the team builds on. Neither step produces concrete numeric values for you; the team maps the taxonomy method to values in their design tool or code.

---

## Step 1. Name the aesthetic direction

Before deriving a taxonomy, an aesthetic direction must exist. For this example, `creative-direction` has produced the following for a professional SaaS analytics dashboard:

**Product context:** an analytics dashboard for operations teams at mid-market SaaS companies. Users are data-literate professionals who return to this surface daily; they need to trust the data and act quickly.

**Named aesthetic direction:**
- **Composed authority** — visual weight communicates hierarchy without shouting; primary signals are unambiguous; secondary information recedes
- **Earned trust** — accuracy and predictability over novelty; no decorative motion; every visual element earns its place
- **Legible density** — high-density layout that remains readable; generous line-height; type scale that distinguishes heading from body without excessive contrast

These three named goals are the constraints every token decision must trace back to.

---

## Step 2. Run design-token-taxonomy

With the aesthetic direction named, invoke `design-token-taxonomy`:

> "Derive the token taxonomy for the analytics dashboard — composed authority, earned trust, legible density. Use a minor-third ratio as the organizing concept."

### Token naming — semantic role first

Every token is named for the job it does, not for how it looks today:

| Token role | Named for | Not named for |
|---|---|---|
| `color.primary` | The surface's primary action color | `color.blue` |
| `color.surface` | The background of a card or panel | `color.white` |
| `color.on-surface` | Text or icon placed on top of a surface color | `color.charcoal` |
| `color.status-error` | Error states and validation failures | `color.red` |
| `space.step-base` | The base unit of the spacing scale | `space.16px` |

Names tied to appearance create rename-hell when the direction shifts. Names tied to role survive redesigns.

### Scale derivation — one ratio as the organizing concept

For "legible density," a minor-third ratio (1.2×) produces tight, readable steps without large jumps. Steps are expressed symbolically; the team maps each to a concrete value using the ratio and their chosen base unit:

```
Type scale (minor-third, 1.2×):
  text.xs    = step −2  (captions, legal copy)
  text.sm    = step −1  (secondary labels, metadata)
  text.base  = base     (paragraph body)
  text.lg    = step +1  (emphasized body, card labels)
  text.xl    = step +2  (section heading)
  text.2xl   = step +3  (page heading)

Spacing scale (same ratio):
  space.1    = step −2
  space.2    = step −1
  space.3    = base
  space.4    = step +1
  space.5    = step +2
  space.6    = step +3
```

The taxonomy records the method; the team supplies the numbers.

### Accessibility as a floor

Every token pair that forms a foreground/background relationship is designed to clear the recognized accessibility standard (WCAG AA: 4.5:1 for text, 3:1 for UI components) at taxonomy derivation time — not as a cleanup pass afterward. The contrast budget is allocated across the tier hierarchy: primary signals at maximum contrast; secondary diagnostics slightly receded; tertiary details de-emphasized within the floor.

---

## Step 3. Run design-system-foundations (lightweight mode)

With the taxonomy derived, invoke `design-system-foundations` in lightweight mode:

> "Apply the token taxonomy for the analytics dashboard as a working foundation. Use lightweight mode — we need to unblock component work; a single theme is enough for now."

The skill produces the working foundation token set. Below is the button component — a before/after showing what working tokens actually look like.

### Before: no token foundation

Without a foundation, component values are hardcoded and disconnected from one another:

```css
/* BEFORE — hardcoded values, no semantic layer */
.btn-primary {
  background: #2563eb;
  color: #ffffff;
  border-radius: 6px;
  padding: 8px 16px;
  font-size: 14px;
  font-weight: 500;
  outline: 2px solid transparent;
}
.btn-primary:hover {
  background: #1d4ed8;
}
.btn-primary:disabled {
  background: #93c5fd;
  color: #dbeafe;
  cursor: not-allowed;
}
```

Problems with this: the hover blue has no derivable relationship to the base blue; the disabled colors have no named semantic role; changing the primary color requires a grep-and-replace across every component; accessibility is assumed, not declared.

### After: semantic token foundation applied

With the foundation in place, the button component reads from semantic tokens. The skill names the token structure; the team maps values using the taxonomy method:

```css
/* AFTER — semantic token layer (values supplied by the team from the taxonomy method) */
:root {
  /* Semantic color roles */
  --ds-color-primary:        /* derived from composed-authority palette */;
  --ds-color-primary-hover:  /* one step darker in the primary scale */;
  --ds-color-primary-active: /* two steps darker; distinct from hover */;
  --ds-color-on-primary:     /* highest-contrast foreground on primary; WCAG AA confirmed */;
  --ds-color-disabled-bg:    /* muted primary; meets WCAG AA against surface */;
  --ds-color-disabled-fg:    /* readable on disabled-bg; below active hierarchy */;
  --ds-color-focus-ring:     /* focus indicator color; meets WCAG 2.4.11 AA */;

  /* Spacing tokens */
  --ds-space-2:              /* step −1 of minor-third scale */;
  --ds-space-4:              /* step +1 of minor-third scale */;

  /* Typography */
  --ds-text-sm:              /* step −1 of minor-third type scale */;
  --ds-font-weight-medium:   /* 500 equivalent */;

  /* Radius */
  --ds-radius-md:            /* calibrated to composed-authority direction */;

  /* Button component tokens — mapped from semantic layer */
  --ds-btn-bg:               var(--ds-color-primary);
  --ds-btn-bg-hover:         var(--ds-color-primary-hover);
  --ds-btn-bg-active:        var(--ds-color-primary-active);
  --ds-btn-bg-disabled:      var(--ds-color-disabled-bg);
  --ds-btn-fg:               var(--ds-color-on-primary);
  --ds-btn-fg-disabled:      var(--ds-color-disabled-fg);
  --ds-btn-focus-ring:       var(--ds-color-focus-ring);
  --ds-btn-radius:           var(--ds-radius-md);
  --ds-btn-py:               var(--ds-space-2);
  --ds-btn-px:               var(--ds-space-4);
  --ds-btn-font-size:        var(--ds-text-sm);
  --ds-btn-font-weight:      var(--ds-font-weight-medium);
}

/* Button component — reads only from component tokens */
.btn-primary {
  background:      var(--ds-btn-bg);
  color:           var(--ds-btn-fg);
  border-radius:   var(--ds-btn-radius);
  padding:         var(--ds-btn-py) var(--ds-btn-px);
  font-size:       var(--ds-btn-font-size);
  font-weight:     var(--ds-btn-font-weight);
}
.btn-primary:hover        { background: var(--ds-btn-bg-hover); }
.btn-primary:active       { background: var(--ds-btn-bg-active); }
.btn-primary:focus-visible { outline: 2px solid var(--ds-btn-focus-ring); outline-offset: 2px; }
.btn-primary:disabled {
  background: var(--ds-btn-bg-disabled);
  color:      var(--ds-btn-fg-disabled);
  cursor:     not-allowed;
}
```

Now changing the primary color requires updating one semantic token value, not hunting down hex codes across files. The hover, active, and disabled states each have a named role. The focus ring declaration traces directly to the accessibility floor.

The semantic alias chain — primitive → semantic → component — means no component reads a raw primitive directly. When the team later adds a dark theme, they override the semantic layer; every component that reads from it picks up the change without modification.

---

## Step 4. Where to go next

After the foundation is set up:

1. **Component state machines** — route to `interaction-design` for the button state machine: the finite-state model that drives default → hover → active → loading → disabled → error transitions, feedback timing, and keyboard behavior.
2. **Screen layout** — route to `information-architecture` to apply the token foundation to the spatial hierarchy of the dashboard.
3. **Full mode** — when the team needs a DTCG-compatible token source, light/dark theme switching, or the full component anatomy (navigation, form controls, data display, feedback), re-run `design-system-foundations` in full mode.

---

## See also

- [Derive a token taxonomy and apply the design token foundation](../how-to/design-system-chain.md) — the how-to guide covering lightweight vs. full mode and the full two-step sequencing.
- [Thread a feature from journey to screens](../how-to/author-design-intent.md) — the full XD chain in which this token chain sits.
