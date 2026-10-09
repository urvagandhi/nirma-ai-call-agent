---
name: better-ui
description: Polishes the surfaces, icons and motion in your project with exact values for border radius, optical alignment, shadows, icon states, and micro-interactions.
---

# UI Polish

This skill holds the visual polish for surfaces, icons, and motion, with exact values.

## Outer Radius Equals Inner Radius Plus Padding

Where nested surfaces share a visible inset:
`outerRadius = innerRadius + padding + borderWidth`
Past `24px` of padding, treat the layers as separate surfaces.

## Align Optically Where Geometry Looks Off

- Give a button `2px` less padding on its icon side.
- Shift play icons `2px` right toward their point.
- Nudge asymmetric SVG glyphs by eye.

## Shadows for Elevation, Borders for Structure

- Where a border exists only for depth, replace with layered transparent `box-shadow`.
- Keep borders on dividers, table cells, and form inputs (requires 3:1 non-text contrast under WCAG).
- Forced-colors mode removes shadows: keep `border: 1px solid transparent` under shadow rings.

## Transitions, Not Keyframes, for Interactive State

- Drive interactive state changes with CSS transitions or spring physics that retarget cleanly.
- Reserve keyframes for single-run entrances.

## Press Scales to 0.96

- Pressed buttons scale to `0.96` (or `0.97`) over `150ms` with `ease-out`. Disabled buttons never scale.

## High-Frequency Interactions Get No Animation

- Keystrokes, table row hovers, and tab switches get instant feedback (< 150ms) on `opacity` or `background-color`.
- Reserve expressive motion for infrequent moments: view load, successful call completion, empty state reveals.

## Gate Motion Behind Reduced-Motion Preference

- Always respect `@media (prefers-reduced-motion: reduce)`.
- Replace physical motion with an opacity cross-fade.
