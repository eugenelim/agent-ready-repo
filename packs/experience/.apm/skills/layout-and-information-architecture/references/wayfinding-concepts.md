# Wayfinding and orientation

Orientation is a design concern, not a markup detail. This file describes
the user's mental model — what they need to feel located and in control.
It never names the platform mechanics that implement it; that mapping
belongs to the build.

## The three questions

A user on any screen is silently asking three things. A surface that
answers all three feels navigable; one that leaves any unanswered feels
like being lost in a building with no signs.

1. **Where am I?** The screen should state its own identity — what this is,
   and where it sits in the larger structure. A title, a path back to the
   parent, a highlighted position in the navigation: each says "you are
   here." Without it, every screen feels like a dead drop with no context.
2. **Where can I go?** The available moves should be visible and legible
   from here — the next step, the related sections, the primary action.
   Don't make the user guess what's reachable or hunt for the way forward.
3. **How do I get back?** There is always a way out and a way up. The user
   can return to where they came from, climb to the parent, or reach a
   known home. A path that can only go deeper is a trap; reversibility is
   what makes a structure safe to explore.

When you review a screen, ask all three out loud. The one you can't answer
is the gap.

## Landmarks and signposting

People navigate physical space by landmarks — the big clock, the corner
café — and they navigate screens the same way. A landmark is any large,
stable, recognizable region the eye can use to anchor: the masthead, the
primary navigation, the main content region, the footer. These are
concepts in the user's mental map, not roles in the markup.

- **Stable landmarks** stay in the same place across screens so the user
  builds a map once and reuses it. Moving the navigation between screens
  forces them to re-orient every time.
- **Signposts** mark the path: section headings, breadcrumbs, step
  indicators, "you are here" highlights. They tell the user how far they've
  come and how far is left — the spatial version of progress.
- A landmark earns its prominence by being *consistent and recognizable*,
  not by being loud. The user should find the navigation in the same
  region every time without thinking about it.

## Grouping and proximity

The eye reads nearness as relatedness. Things placed close together are
understood to belong together; things separated by space are understood as
distinct. This is the cheapest, strongest organizing tool you have — and
the one most often wasted by even, undifferentiated spacing.

- **Group by meaning, separate by space.** Tighten the space within a
  related set; widen the space between sets. The pattern of gaps *is* the
  structure the user perceives, before they read a single label.
- **Don't rely on borders to do what space can do.** Boxing everything
  adds visual noise; a clear rhythm of grouping and separation reads
  faster and feels calmer.
- **Align to imply relationship.** Items on a shared edge or a shared line
  read as a set; a broken alignment reads as a new group or a mistake. A
  regular underlying structure — a grid the eye can follow as a layout
  concept — makes alignment effortless and the whole surface scannable.
- **Order within a group carries meaning too.** Sequence by the user's
  priority or natural reading order, not by what was easy to assemble.

## Consistent placement

Consistency is what lets a user stop thinking about the interface and think
about their task. When the same kind of thing lives in the same place on
every screen, the user learns the layout once and spends no attention
relocating it.

- **Same role, same place.** The primary action, the title, the back path,
  the navigation — each keeps its region across the product. A control
  that moves between screens forces a fresh search each time.
- **Same meaning, same treatment.** If a visual treatment means "primary
  action" here, it must not mean "decoration" two screens over. Consistency
  of meaning is as load-bearing as consistency of position.
- **Predictability beats novelty for anything load-bearing.** Surprise is a
  cost; spend it only where delight is the goal, never on the controls a
  user needs to find under pressure.

Consistent placement is invisible when you get it right — the user simply
never gets lost — and glaring when you don't.
