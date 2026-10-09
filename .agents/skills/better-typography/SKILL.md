---
name: better-typography
description: Sets and reviews how text renders in your product, from the type scale and spacing to font features, wrapping, truncation, tabular numbers, and punctuation.
---

# Typography

This skill sets and reviews how text renders, from the type scale and spacing to font loading, wrapping, and punctuation.

## Measured, Not Preferred

- **Unitless line-height**: Display `1.1`, Headings `1.2–1.3`, Body `1.5–1.6`.
- **Weight**: Weight `400` or heavier below `18px`. Weights `100–300` belong at `28px` and up.
- **Measure**: 60–75 characters per line for readable body text.
- **Inputs**: `16px` minimum font-size on iOS to prevent automatic viewport zoom.
- **Tabular numbers**: `font-variant-numeric: tabular-nums` (Tailwind: `tabular-nums`) on all changing values, timestamps, call durations, counters, and table columns.

## Properties Over Raw Tags

When a CSS property exists, use it:
- `font-weight: 650`, not `font-variation-settings: "wght" 650`.
- `font-variant-numeric: tabular-nums`, not `font-feature-settings: "tnum" 1`.
- Leave `font-optical-sizing` at default `auto`.

## Use a Type Scale with Semantic Names

Define a small set of sizes paired with line-height and weight:
- `caption`: 12px / 400 / line-height 16px
- `body-sm`: 14px / 400 / line-height 20px
- `body-md`: 16px / 400 / line-height 24px
- `title-md`: 16px / 600 / line-height 24px
- `headline-sm`: 20px / 600 / line-height 28px
- `headline-md`: 24px / 600 / line-height 32px
- `headline-lg`: 30px / 600 / line-height 38px
- `display-lg`: 38px / 600 / line-height 46px

## Heading Sizes Descend with Level

Map heading levels to descending steps so subordinate headings never overpower parents.

## Letter-Spacing by Size

- Headings at `24px` and up: `-0.01em` to `-0.02em`.
- Uppercase labels / eyebrows at `14px` or smaller: `0.05em` to `0.1em`.
- Body copy: `0`.
