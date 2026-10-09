---
name: accessibility
description: Audit and improve web accessibility following WCAG 2.2 guidelines, focus states, keyboard navigation, and screen reader support.
---

# Accessibility (WCAG 2.2)

Comprehensive accessibility guidelines based on WCAG 2.2 AA compliance for enterprise and institutional portals.

## The POUR Principles

- **Perceivable**: Text alternatives, color contrast (minimum 4.5:1 for normal text, 3:1 for large text and UI components), clear visual landmarks.
- **Operable**: 100% keyboard navigable (visible `:focus-visible` rings), no keyboard traps, 44×44px touch targets.
- **Understandable**: Predictable navigation, clear validation error messages, consistent layout.
- **Robust**: Valid semantic HTML elements (`<button>`, `<dialog>`, `<nav>`, `<main>`), proper ARIA roles and live regions for dynamic streaming content.

## Real-Time Audio & Telephony Accessibility

- Live speech/ASR stream widgets must use `aria-live="polite"` or `role="log"`.
- Audio players must provide explicit keyboard controls (Play/Pause Spacebar, Seek Left/Right Arrow).
- Call status badges must not rely solely on color (combine green/red/amber dots with text labels like `Active`, `Failed`, `Queued`).
