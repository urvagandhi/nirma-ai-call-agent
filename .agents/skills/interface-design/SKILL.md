---
name: interface-design
description: Craft-first interface design for dashboards, admin panels, SaaS apps, tools, settings pages, data interfaces, and interactive products. Use when designing, building, reviewing, auditing, or refining product UI where visual craft, layout hierarchy, tokens, states, visual direction, or design-system consistency matter. Not for marketing pages, landing pages, campaigns, or brand-only work.
---

# Interface Design

Build product interfaces with the craft of a top design team — Linear, Vercel, Stripe, Apple. The difference between those and generic output is not talent. It is that every decision was *decided*, the hierarchy is unmistakable, and a hundred small details are correct at once. This skill is how you get there.

## Scope

**Use for:** Dashboards, admin panels, SaaS apps, tools, settings pages, data interfaces.

**Not for:** Landing pages, marketing sites, campaigns, brand-only work. Use a marketing/frontend design skill for those.

This skill is self-contained: direction, visual hierarchy, design-system architecture, and the polish and motion essentials needed to ship production-grade UI all live here.

---

# The Problem

You will generate generic output. Your training has seen thousands of dashboards, and the patterns are strong. You can follow this entire process — explore the domain, name a signature, state your intent — and still produce a template: warm colors on cold structures, friendly fonts on generic layouts.

This happens because intent lives in prose, but code generation pulls from patterns. The gap between them is where defaults win. Process helps, but it doesn't guarantee craft. You have to catch yourself, and you have to know the concrete moves that defaults don't.

**The bar:** If another AI, given a similar prompt, would produce substantially the same output, you have failed. Not different for its own sake — different because the interface emerged from *this* user, *this* task, *this* world. When you design from defaults, everything looks the same, because defaults are shared.

---

# Where Defaults Hide

Defaults disguise themselves as infrastructure — the parts that feel like they just need to work, not be designed.

- **Typography feels like a container.** But type isn't holding your design, it *is* your design. The weight of a headline, the personality of a label, the texture of a paragraph shape how the product feels before anyone reads a word. Reaching for your usual font means you're not designing.
- **Navigation feels like scaffolding.** But navigation *is* the product — where you are, where you can go, what matters. A page floating in space is a component demo, not software.
- **Data feels like presentation.** But a number on screen is not design. What does it *mean* to the person looking? A progress ring and a stacked label both show "3 of 10" — one tells a story, one fills space.
- **Token names feel like implementation detail.** But `--ink` and `--parchment` evoke a world; `--gray-700` and `--surface-2` evoke a template. Someone reading only your tokens should guess what product this is.

There are no structural decisions. Everything is design. The moment you stop asking "why this?" is the moment defaults take over.

---

# Intent First

Before touching code, answer these. Keep it a compact working brief unless the direction needs user confirmation.

- **Who is this human?** Not "users." The actual person. Where are they when they open this? What did they do 5 minutes ago, what will they do 5 minutes after?
- **What must they accomplish?** The verb. Grade these submissions. Find the broken deployment. Approve the payment. The answer determines what leads, what follows, what hides.
- **What should this feel like?** In words that mean something. "Clean and modern" means nothing — every AI says that. Warm like a notebook? Cold like a terminal? Dense like a trading floor? Calm like a reading app? This shapes color, type, spacing, density — everything.

If the prompt is too vague to identify the human, task, and feel, ask one concise question. If context allows a responsible assumption, state it briefly and proceed.

**Intent must be systemic.** Saying "warm" then using cold colors is not following through. If the intent is warm: surfaces, text, borders, accents, semantic colors, type — all warm. If dense: spacing, type size, information architecture — all dense. Check every token against the stated intent. For every choice — layout, color temperature, typeface, spacing scale, hierarchy — you must be able to say *why*. "It's common" or "it works" means you defaulted.

---

# Product Domain Exploration

Produce all four before proposing any direction:
- **Domain** — concepts, metaphors, vocabulary from this product's world. Minimum 5.
- **Color world** — what colors exist *naturally* here? List 5+.
- **Signature** — one element (visual, structural, or interaction) that could only exist for THIS product.
- **Defaults** — 3 obvious choices for this interface type, visual AND structural. You can't avoid patterns you haven't named.

---

# Visual Hierarchy & Composition

## One focal point per view
Every screen has one thing the user came to do. That thing dominates — through size, contrast, position, or the space around it. When everything competes equally, nothing wins and the interface reads like a parking lot. Before building, name the focal element out loud. Then make it win: bigger, higher-contrast, or ringed in whitespace. Demote everything else deliberately.

## Type scale is a ratio, and weight beats size
Don't pick sizes by feel. Pick a ratio and step it: ~1.2 (minor third) for dense/calm UI, ~1.25 for most product UI, ~1.333 for expressive. From a 14–16px body that yields a *visibly* distinct scale.

The Apple/Linear move: **weight and color do more hierarchy work than size.** A single 14px size holds three tiers through weight + opacity alone — `value: 600 / primary`, `label: 500 / secondary`, `meta: 400 / muted`.

## Density is a decision, expressed in px
Linear is tight; Stripe is airy. Pick deliberately, then hold it across all cards and views.

## Spatial rhythm — breathe unevenly
Group tightly-related things, then put real air between groups.

## Distribution and restraint (the "expensive" look)
- **~60/30/10**: dominant neutral surface, secondary tone, and ~10% accent.
- **One accent, used with intention**, beats five colors used without thought.
- **Hierarchy through space and weight, not lines.** Reach for whitespace and tonal shift before borders and dividers.
- **Optical sizing on large type**: tighten letter-spacing as type gets bigger.

---

# Craft Foundations

## Subtle Layering
Surfaces stack: a dropdown sits above a card sits above the page. Build a numbered system — base, then increasing levels. Each jump is only a few percentage points of lightness.
- **Sidebars:** same background as canvas, not a different color. A subtle border is enough.
- **Dropdowns/popovers:** one level above their parent surface.
- **Inputs:** slightly *darker* than surroundings, not lighter. Inputs are inset.

## Borders
Should disappear when you're not looking for them, but be findable when you need structure. Low-opacity rgba blends with the background.

---

# Controls: native → primitive → hand-roll

1. **Native HTML first** where it works (`<button>`, `<a>`, `<input>`, `<dialog>`).
2. **A battle-tested headless primitive** for stateful components (Radix, React Aria, Ark, Headless UI).
3. **Hand-roll only as a genuine last resort** — providing keyboard nav, ARIA, focus traps.

---

# Static Polish & Motion Essentials

- **Concentric radius**: `outerRadius = innerRadius + padding`.
- **Tabular numbers**: Any dynamic number (counters, timers, table columns) gets `font-variant-numeric: tabular-nums`.
- **Optical alignment**: Fix geometric centering by eye.
- **States are not optional**: default, hover, active, focus, disabled, loading, empty, error.
- **Hit areas**: 44×44px (WCAG).
- **Text wrapping**: `text-wrap: balance` on headings, `text-wrap: pretty` on body.
- **Motion**: Duration < 300ms. Custom ease-out (`cubic-bezier(0.23, 1, 0.32, 1)`). Press feedback `scale(0.97)`.
- **Respect `prefers-reduced-motion`**.
