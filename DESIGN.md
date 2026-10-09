---
version: alpha
name: Nirma University AI Voice Agent
description: Production-grade design system for Nirma University's Automated Multilingual Voice Calling & HPC Mission Control platform. Synthesizes Ant Design's enterprise density and form mechanics, Amplitude's telemetry and KPI analytics, and VoltAgent's developer-first dark canvas with real-time voice streaming affordances.

colors:
  # Institutional University Brand & Accent
  primary: "#E06D3B"
  primary-hover: "#F08252"
  primary-deep: "#993416"
  on-primary: "#FFFFFF"
  nirma-navy: "#0A0E1A"
  nirma-navy-soft: "#131B2E"

  # Telemetry & Real-Time Voice Stream Accents (VoltAgent inspired)
  live-pulse: "#10B981"
  live-pulse-soft: "#34D399"
  live-glow: "rgba(16, 185, 129, 0.25)"
  telemetry-cyan: "#06B6D4"
  telemetry-cyan-soft: "#22D3EE"
  telemetry-amber: "#F59E0B"
  telemetry-violet: "#A855F7"

  # Canvas & Surface System (Deep HPC Mission Control Dark Canvas)
  canvas: "#080C15"
  canvas-subtle: "#0A0E1A"
  canvas-soft: "#0D1322"
  canvas-elevated: "#131B2E"
  canvas-overlay: "rgba(8, 12, 21, 0.85)"

  # Hairline Borders & Glass Dividers
  hairline: "rgba(255, 255, 255, 0.08)"
  hairline-subtle: "rgba(255, 255, 255, 0.04)"
  hairline-strong: "rgba(255, 255, 255, 0.16)"
  hairline-terracotta: "rgba(224, 109, 59, 0.35)"

  # Text & Content Scale
  ink: "#F1F5F9"
  ink-strong: "#FFFFFF"
  body: "#94A3B8"
  mute: "#64748B"
  disabled: "#475569"

  # Telecom Call State Semantic Tokens
  state-queued: "#3B82F6"
  state-ringing: "#F59E0B"
  state-in-progress: "#10B981"
  state-completed: "#22C55E"
  state-failed: "#EF4444"
  state-busy: "#A855F7"
  state-dnd: "#64748B"

typography:
  display-xl:
    fontFamily: "Inter, system-ui, -apple-system, sans-serif"
    fontSize: 48px
    fontWeight: 600
    lineHeight: 56px
    letterSpacing: -0.9px
  display-lg:
    fontFamily: "Inter, system-ui, -apple-system, sans-serif"
    fontSize: 32px
    fontWeight: 600
    lineHeight: 40px
    letterSpacing: -0.6px
  headline-md:
    fontFamily: "Inter, system-ui, -apple-system, sans-serif"
    fontSize: 24px
    fontWeight: 600
    lineHeight: 32px
    letterSpacing: -0.4px
  headline-sm:
    fontFamily: "Inter, system-ui, -apple-system, sans-serif"
    fontSize: 18px
    fontWeight: 600
    lineHeight: 26px
    letterSpacing: -0.2px
  eyebrow-mono:
    fontFamily: "'SFMono-Regular', Menlo, Monaco, Consolas, 'JetBrains Mono', monospace"
    fontSize: 11px
    fontWeight: 600
    lineHeight: 16px
    letterSpacing: 1.5px
    textTransform: uppercase
  title-md:
    fontFamily: "Inter, system-ui, -apple-system, sans-serif"
    fontSize: 14px
    fontWeight: 600
    lineHeight: 20px
  body-md:
    fontFamily: "Inter, system-ui, -apple-system, 'Noto Sans Gujarati', 'Noto Sans Devanagari', sans-serif"
    fontSize: 14px
    fontWeight: 400
    lineHeight: 22px
  body-sm:
    fontFamily: "Inter, system-ui, -apple-system, 'Noto Sans Gujarati', 'Noto Sans Devanagari', sans-serif"
    fontSize: 12px
    fontWeight: 400
    lineHeight: 18px
  metric-kpi:
    fontFamily: "Inter, system-ui, -apple-system, sans-serif"
    fontSize: 28px
    fontWeight: 600
    lineHeight: 34px
    letterSpacing: -0.5px
    fontVariantNumeric: tabular-nums
  metric-kpi-lg:
    fontFamily: "Inter, system-ui, -apple-system, sans-serif"
    fontSize: 36px
    fontWeight: 600
    lineHeight: 44px
    letterSpacing: -0.7px
    fontVariantNumeric: tabular-nums
  code:
    fontFamily: "'SFMono-Regular', Menlo, Monaco, Consolas, 'JetBrains Mono', monospace"
    fontSize: 12px
    fontWeight: 400
    lineHeight: 18px
  button-md:
    fontFamily: "Inter, system-ui, -apple-system, sans-serif"
    fontSize: 13px
    fontWeight: 500
    lineHeight: 20px

rounded:
  none: 0px
  xs: 2px
  sm: 4px
  DEFAULT: 6px
  md: 8px
  lg: 12px
  xl: 16px
  pill: 9999px
  full: 9999px

spacing:
  unit: 4px
  xxs: 2px
  xs: 4px
  sm: 8px
  md: 12px
  lg: 16px
  xl: 20px
  2xl: 24px
  3xl: 32px
  4xl: 40px
  5xl: 48px
  control-height: 32px
  control-height-lg: 40px

components:
  nav-bar:
    backgroundColor: "{colors.canvas-subtle}"
    textColor: "{colors.ink}"
    borderColor: "{colors.hairline}"
    padding: "0 {spacing.3xl}"
    height: "64px"

  button-primary:
    backgroundColor: "{colors.primary}"
    textColor: "{colors.on-primary}"
    typography: "{typography.button-md}"
    rounded: "{rounded.DEFAULT}"
    height: 32px
    padding: "0 14px"

  button-primary-hover:
    backgroundColor: "{colors.primary-hover}"

  button-outline:
    backgroundColor: "transparent"
    textColor: "{colors.ink}"
    borderColor: "{colors.hairline}"
    typography: "{typography.button-md}"
    rounded: "{rounded.DEFAULT}"
    height: 32px
    padding: "0 14px"

  button-ghost-cyan:
    backgroundColor: "rgba(6, 182, 212, 0.08)"
    textColor: "{colors.telemetry-cyan-soft}"
    borderColor: "rgba(6, 182, 212, 0.25)"
    typography: "{typography.button-md}"
    rounded: "{rounded.DEFAULT}"
    height: 32px
    padding: "0 14px"

  text-input:
    backgroundColor: "{colors.canvas-soft}"
    textColor: "{colors.ink}"
    borderColor: "{colors.hairline}"
    typography: "{typography.body-md}"
    rounded: "{rounded.DEFAULT}"
    height: 32px
    padding: "4px 11px"

  text-input-focus:
    borderColor: "{colors.primary}"
    boxShadow: "0 0 0 2px rgba(224, 109, 59, 0.25)"

  card-panel:
    backgroundColor: "{colors.canvas-soft}"
    textColor: "{colors.ink}"
    borderColor: "{colors.hairline}"
    rounded: "{rounded.md}"
    padding: "20px"

  card-kpi:
    backgroundColor: "{colors.canvas-soft}"
    textColor: "{colors.ink}"
    borderColor: "{colors.hairline}"
    rounded: "{rounded.md}"
    padding: "16px 20px"

  table-header:
    backgroundColor: "{colors.canvas-subtle}"
    textColor: "{colors.body}"
    borderColor: "{colors.hairline}"
    typography: "{typography.eyebrow-mono}"
    padding: "10px 16px"

  table-cell:
    backgroundColor: "transparent"
    textColor: "{colors.ink}"
    borderColor: "{colors.hairline-subtle}"
    typography: "{typography.body-md}"
    padding: "12px 16px"

  modal:
    backgroundColor: "{colors.canvas-elevated}"
    textColor: "{colors.ink}"
    borderColor: "{colors.hairline-strong}"
    rounded: "{rounded.lg}"
    padding: "24px"

  drawer-console:
    backgroundColor: "{colors.canvas-subtle}"
    textColor: "{colors.ink}"
    borderColor: "{colors.hairline}"
    padding: "24px"

  stream-bubble-user:
    backgroundColor: "{colors.canvas-soft}"
    textColor: "{colors.ink}"
    borderColor: "{colors.hairline}"
    rounded: "{rounded.md}"
    padding: "12px 16px"

  stream-bubble-agent:
    backgroundColor: "rgba(16, 185, 129, 0.08)"
    textColor: "{colors.ink-strong}"
    borderColor: "rgba(16, 185, 129, 0.25)"
    rounded: "{rounded.md}"
    padding: "12px 16px"

  badge-pill-live:
    backgroundColor: "rgba(16, 185, 129, 0.15)"
    textColor: "{colors.live-pulse}"
    borderColor: "rgba(16, 185, 129, 0.3)"
    typography: "{typography.code}"
    rounded: "{rounded.pill}"
    padding: "2px 8px"

  tag-state:
    backgroundColor: "{colors.canvas-elevated}"
    textColor: "{colors.ink}"
    borderColor: "{colors.hairline}"
    typography: "{typography.body-sm}"
    rounded: "{rounded.sm}"
    padding: "2px 8px"

  # ─── Examples Block (Kit-Mirror Demonstration Surfaces) ───
  ex-app-shell-row:
    description: "Sidebar nav item with active terracotta indicator and subtle hover state."
    backgroundColor: "{colors.canvas-subtle}"
    activeIndicator: "{colors.primary}"
    rounded: "{rounded.DEFAULT}"
    padding: "{spacing.sm} {spacing.md}"
  ex-data-table-cell:
    description: "Mission control call log cell with mono numbers and status pills."
    headerBackground: "{colors.canvas-subtle}"
    headerTypography: "{typography.eyebrow-mono}"
    bodyTypography: "{typography.body-md}"
    cellPadding: "{spacing.md} {spacing.lg}"
    rowBorder: "{colors.hairline-subtle}"
  ex-kpi-card:
    description: "Amplitude-inspired KPI metric container with trend badges and tabular digits."
    backgroundColor: "{colors.canvas-soft}"
    borderColor: "{colors.hairline}"
    rounded: "{rounded.md}"
    padding: "{spacing.lg}"
  ex-modal-card:
    description: "Campaign dispatch & schedule wizard dialog with glass backdrop."
    backgroundColor: "{colors.canvas-elevated}"
    borderColor: "{colors.hairline-strong}"
    rounded: "{rounded.lg}"
    padding: "{spacing.2xl}"
  ex-toast:
    description: "Asynchronous task notification toast for PSTN carrier dispatch events."
    backgroundColor: "{colors.canvas-elevated}"
    borderColor: "{colors.hairline}"
    rounded: "{rounded.md}"
    padding: "{spacing.md} {spacing.lg}"
    typography: "{typography.body-md}"
---

## Overview

The **Nirma University AI Voice Agent Design System** governs the user interface for the college administration voice platform deployed on the Nirma University Supercomputer (HPC). The platform orchestrates high-throughput multilingual voice campaigns (tuition fee reminders, examination schedules, attendance alerts) to students and parents across **English, Hindi, and Gujarati**.

The interface is engineered as an **HPC Mission Control**:
- **Canvas-first darkness**: An edge-to-edge deep space canvas (`#080C15`) provides high contrast and visual calm during intensive operational monitoring.
- **Nirma Terracotta signature**: A vibrant institutional terracotta/amber accent (`#E06D3B`) anchors primary actions, logo identity, and active system focus without feeling corporate or cold.
- **Live telemetry signals**: Dedicated signals for real-time PSTN state—electric emerald (`#10B981`) for live telephony streams, tech cyan (`#06B6D4`) for local GPU/LLM inference status, and amber (`#F59E0B`) for TRAI regulatory calling windows.
- **Data density & tabular integrity**: Dense data tables and KPI cards built on a 4px baseline grid with strict tabular numeral formatting for jitter-free counters.

---

## Colors

### Brand & Accents
- **Nirma Terracotta** (`{colors.primary}` — `#E06D3B`): The core brand accent. Used for primary CTAs, active radio badges, logo crest gradient, and selection rings.
- **Terracotta Hover** (`{colors.primary-hover}` — `#F08252`): State transition for interactive buttons.
- **Terracotta Deep** (`{colors.primary-deep}` — `#993416`): The dark gradient base for institutional badges and active presses.

### Telemetry Accents
- **Live Emerald** (`{colors.live-pulse}` — `#10B981`): PSTN gateway active indicator, live audio streaming waveforms, and completed call metrics.
- **GPU Cyan** (`{colors.telemetry-cyan}` — `#06B6D4`): Local supercomputer AI inference metrics (Qwen-14B, IndicConformer, IndicF5).
- **TRAI Amber** (`{colors.telemetry-amber}` — `#F59E0B`): Indian telecom compliance indicators (`09:00 - 21:00 IST` calling window) and carrier retries.

### Canvas & Surfaces
- **Canvas Root** (`{colors.canvas}` — `#080C15`): The deepest background substrate of the mission control viewport.
- **Canvas Subtle** (`{colors.canvas-subtle}` — `#0A0E1A`): Sticky navigation masthead and table headers.
- **Canvas Soft** (`{colors.canvas-soft}` — `#0D1322`): Standard surface for cards, dashboard panels, and form fields.
- **Canvas Elevated** (`{colors.canvas-elevated}` — `#131B2E`): Floating modals, context dropdowns, and slide-over telemetry drawers.

### Hairline & Borders
- **Hairline** (`{colors.hairline}` — `rgba(255, 255, 255, 0.08)`): The standard 1px border for cards, inputs, and dividers.
- **Hairline Strong** (`{colors.hairline-strong}` — `rgba(255, 255, 255, 0.16)`): Modal edges and highlighted containers.
- **Hairline Terracotta** (`{colors.hairline-terracotta}` — `rgba(224, 109, 59, 0.35)`): Focus states and active card highlights.

### Typography Colors
- **Ink Strong** (`{colors.ink-strong}` — `#FFFFFF`): Display headings and high-emphasis labels.
- **Ink** (`{colors.ink}` — `#F1F5F9`): Primary readable text and data cell values.
- **Body** (`{colors.body}` — `#94A3B8`): Secondary text, labels, and table column titles.
- **Mute** (`{colors.mute}` — `#64748B`): Timestamps, inactive states, and metadata footers.

---

## Typography

### Font Family
The typography pairs **Inter** for clean, readable narrative prose with **SF Mono / JetBrains Mono** for all telemetry, timestamps, latency metrics, and phone numbers. For Indian scripts, fallbacks gracefully include **Noto Sans Gujarati** and **Noto Sans Devanagari**.

### Hierarchy & Type Scale

| Token | Size | Weight | Line Height | Tracking | Numeric Style | Usage |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| `{typography.display-xl}` | 48px | 600 | 56px | -0.9px | Normal | Major landing title / mission control header |
| `{typography.display-lg}` | 32px | 600 | 40px | -0.6px | Normal | Section headers & campaign wizards |
| `{typography.headline-md}` | 24px | 600 | 32px | -0.4px | Normal | Card titles and modal headers |
| `{typography.headline-sm}` | 18px | 600 | 26px | -0.2px | Normal | Drawer titles and sub-panels |
| `{typography.eyebrow-mono}`| 11px | 600 | 16px | +1.5px | Monospace | Uppercase category tags (`TRAI WINDOW`, `GPU`) |
| `{typography.metric-kpi}` | 28px | 600 | 34px | -0.5px | `tabular-nums`| Amplitude-style metric figures (`48,290`) |
| `{typography.body-md}` | 14px | 400 | 22px | 0 | Normal | Default table cells, form values, and copy |
| `{typography.body-sm}` | 12px | 400 | 18px | 0 | Normal | Captions, secondary timestamps, tags |
| `{typography.code}` | 12px | 400 | 18px | 0 | Monospace | Phone numbers, UUIDs, latency ms, prompts |

### The Tabular Numbers Invariant
Every metric that increments, counts down, or updates via WebSockets **must** apply `font-variant-numeric: tabular-nums` (Tailwind: `tabular-nums`). This prevents layout jitter during live call monitoring.

---

## Layout & Spatial System

### 4-Pixel Spatial Grid
All margins, padding, row heights, and layout gaps adhere strictly to the 4px baseline grid:
- **Base Unit**: `4px`
- **Scale**: `2px` · `4px` · `8px` · `12px` · `16px` · `20px` · `24px` · `32px` · `40px` · `48px` · `64px`
- **Control Height**: Buttons, text inputs, and select triggers share a standard `32px` height (`control-height`) to guarantee uniform horizontal alignment.

### Responsive Breakpoints

| Name | Breakpoint | Structural Behavior |
| :--- | :--- | :--- |
| **Mobile** | `< 768px` | KPI cards 1-up; navigation collapses into drawer; tables switch to card stack. |
| **Tablet** | `768px – 1023px` | KPI cards 2-up; tables retain horizontal scroll; sidebars collapsible. |
| **Desktop** | `1024px – 1439px` | KPI cards 4-up grid; full data tables with sticky actions column. |
| **Wide (HPC)**| `≥ 1440px` | Split-view dashboard: Live campaign table on left + persistent call stream on right. |

---

## Elevation, Depth & Glassmorphism

Surfaces do not rely on muddy drop shadows on a dark canvas. Elevation is defined by **surface lightness shifts, hairline borders, and subtle backdrop blurs**:

- **Level 0 (Flat)**: Pure `{colors.canvas}` (`#080C15`) without borders.
- **Level 1 (Glass Panel)**: `{colors.canvas-soft}` (`#0D1322`) + `1px solid rgba(255, 255, 255, 0.08)` + `backdrop-filter: blur(12px)`.
- **Level 2 (Elevated Card)**: `{colors.canvas-elevated}` (`#131B2E`) + `1px solid rgba(255, 255, 255, 0.12)` + `box-shadow: 0 10px 25px -5px rgba(0, 0, 0, 0.5)`.
- **Level 3 (Modal / Drawer)**: `{colors.canvas-elevated}` + `1px solid rgba(255, 255, 255, 0.16)` + `box-shadow: 0 25px 50px -12px rgba(0, 0, 0, 0.7)`.

---

## Shapes & Corner Radii

To eliminate visual discordance, nested elements follow the concentric radius formula:

$$\text{Radius}_{\text{outer}} = \text{Radius}_{\text{inner}} + \text{Padding}$$

- **`none` (0px)**: Edge-to-edge headers and full-width table dividers.
- **`xs` (2px)**: Latency progress bars and status indicators.
- **`sm` (4px)**: Status tags, chip badges, and tooltips.
- **`DEFAULT` (6px)**: Buttons, text inputs, selects, and search boxes.
- **`md` (8px)**: KPI cards, table containers, and stream message bubbles.
- **`lg` (12px)**: Dialog modals and slide-out drawers.
- **`pill` (9999px)**: Live pulse pills, avatar badges, and search pills.

---

## Components

### Navigation Masthead (`nav-bar`)
- 64px sticky bar with `#0A0E1A` background and `backdrop-filter: blur(16px)`.
- Features Nirma University crest with orange-to-maroon gradient badge (`from-[#E06D3B] to-[#993416]`).
- Live telemetry pill group displaying: PSTN Gateway (`Plivo Active`), GPU Model (`Qwen-14B 4-bit`), and TRAI Window (`09:00 - 21:00 IST`).

### Primary Buttons (`button-primary`)
- Terracotta fill (`#E06D3B`), pure white text, 32px height, 6px radius.
- On hover: `#F08252` fill with subtle terracotta shadow ring.
- On active: Scale down to `0.97` with `150ms ease-out`.

### KPI Metric Cards (`card-kpi`)
- Amplitude-style card with 20px padding and glass-panel backdrop.
- Uppercase monospace eyebrow label (`TOTAL CALLS`, `DELIVERY RATE`, `TURN LATENCY`).
- Hero numeral rendered at 28px SemiBold with strict `tabular-nums`.
- Trend badges indicating live delta (`↑ 94.8% success`) and P95 latency indicators.

### Student & Campaign Data Tables
- Header row styled in uppercase monospace (`#94A3B8`, 11px) on `#0A0E1A` background.
- Row hover transition to `#131B2E` over `100ms`.
- Numeric columns (Roll Number, Phone Number, Duration) aligned right with monospace fonts.
- Telecom state tags styled with dedicated status dot + text label for accessibility.

### Real-Time Call Inspector & Audio Waveform Console
- Slide-over drawer on dark canvas (`#0A0E1A`).
- Live carrier waveform display using Web Audio API canvas visualizer.
- Turn-by-turn conversational bubbles:
  - **Student Speech**: Recessed dark card (`#0D1322`) with language chip (`Gujarati / Hindi / English`) and STT confidence score.
  - **AI Agent Speech**: Emerald-accented bubble (`rgba(16, 185, 129, 0.08)`) with model badge (`Local Qwen-14B` vs `Groq Cloud Fallback`).
  - Turn Latency breakdown: `Turn 3: 1,420 ms [STT 420ms | LLM 680ms | TTS 320ms]`.

---

## Do's and Don'ts

### Do
- **Do** format every live count, duration, timestamp, and latency metric with `tabular-nums`.
- **Do** maintain a strict 32px height across all buttons, inputs, and selects in the same row.
- **Do** verify that every status badge includes both a colored dot and an explicit text label for WCAG compliance.
- **Do** preserve the deep dark mission control canvas (`#080C15`) with subtle hairline borders.
- **Do** respect `@media (prefers-reduced-motion: reduce)` by replacing position transitions with simple opacity cross-fades.

### Don't
- **Don't** use generic white or light grey card backgrounds; stay faithful to the HPC Mission Control palette.
- **Don't** invent arbitrary padding (e.g., `padding: 13px`); snap to the 4px grid.
- **Don't** use pure red or pure green for decorative elements; reserve them for failure and live telephony states.
- **Don't** allow conversational bubbles to shift widths during live streaming.
