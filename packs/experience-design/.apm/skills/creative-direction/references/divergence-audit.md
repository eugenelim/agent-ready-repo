# divergence-audit — candidate-direction separation

> **Loaded when:** more than one candidate direction exists for the same
> surface.
> **Question:** do these candidate directions actually differ, or are they one
> direction restyled?

## Direction-sheet axes

Compare the bracketed tokens in every corresponding cell of the candidate
direction sheets. The audit covers all fifteen axes. The three rows with two
token positions carry two independent parameters, so both tokens are compared.

| Axis | Token vocabulary |
| --- | --- |
| Grid grammar | `[manuscript]` `[column]` `[modular]` `[hierarchical]` `[compound]` `[broken]` `[platform-default]`, then `[rigid]` `[relaxed]` `[platform-default]` |
| Alignment and equilibrium | `[edge]` `[centred]` `[baseline]` `[platform-default]`, then `[symmetric]` `[asymmetric]` `[platform-default]` |
| Spatial density | `[sparse]` `[comfortable]` `[dense]` `[platform-default]` |
| Whitespace distribution | `[compact]` `[even]` `[expansive]` `[platform-default]` |
| Hierarchy and scale contrast | `[flat]` `[moderate]` `[steep]` `[platform-default]` |
| Containment and boundary strength | `[open-field]` `[ruled]` `[panelled]` `[carded]` `[platform-default]` |
| Section and scroll rhythm | `[continuous]` `[episodic]` `[platform-default]`, then `[regular]` `[varied]` `[platform-default]` |
| Type voice | `[serif]` `[sans-geometric]` `[sans-humanist]` `[monospace]` `[mixed]` `[platform-default]` |
| Type hierarchy | `[flat]` `[moderate]` `[dramatic]` `[platform-default]` |
| Chromatic intensity | `[monochrome]` `[restrained]` `[saturated]` `[high-chroma]` `[platform-default]` |
| Form | `[rectilinear]` `[softened]` `[organic]` `[platform-default]` |
| Material and depth | `[flat]` `[layered]` `[deep]` `[platform-default]` |
| Ornament and texture | `[none]` `[pattern]` `[grain]` `[illustration]` `[platform-default]` |
| Image treatment | `[photographic]` `[illustrative]` `[abstract]` `[none]` `[platform-default]` |
| Motion character | `[still]` `[productive]` `[expressive]` `[platform-default]` |

The first seven axes are structural, so the audit gives their differences
priority in review. Structural factors have broader and greater effects on
perceived aesthetics than colour factors do. The distance threshold remains an
axis count, which keeps the result inspectable while preserving that review
priority.

## Pairwise comparison

Compare every unordered pair of candidates across all fifteen axes. For an
axis, read only the complete tuple of bracketed tokens in its cell.

- Two cells differ when their token tuples differ.
- Prose after identical tokens is not compared. A paraphrase is not a
  difference.
- `[platform-default]` on both sides is not a difference.
- `[platform-default]` on one side and a decided token on the other is a
  difference.

Count the axes that differ for each pair. A pair is distinct when at least six
of the fifteen axes differ.

Six of the fifteen is a reasoned default, carried across proportionally from
an earlier four-of-ten threshold. It is not a measured value. To measure it,
generate candidate pairs that differ on a controlled number of axes and ask
reviewers whether they read as the same underlying direction.

## Report

Report the minimum pairwise distance across the whole candidate set as a count
of differing axes, and name the pair or pairs that produce it. The mean is not
the reported figure. A set of five where four candidates are near-identical and
one is an outlier can have a respectable mean and still not be a diverse set.
The minimum catches the near-duplicates.

State whether the minimum pairwise distance meets the threshold. Include the
axis differences for each below-threshold pair so the set can be revised.

## Refusals

This audit refuses to report a single composite score or an average. It also
refuses to call a set diverse when the minimum pair is below threshold, even if
the mean clears it.
