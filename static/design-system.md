# Medical Question Framing Tool — Design System

## Overview

This document is the single source of truth for the visual design system used across all templates in this project. All styling is implemented via Tailwind CSS (CDN) using a custom config block defined in each HTML template.

**Reference inspiration:** Typeform AI UI (clean card-based layout, generous whitespace, strong typographic hierarchy, muted interactive states)

**Color palette base:** [Color Hunt #F9F8F6 #EFE9E3 #D9CFC7 #C9B59C](https://colorhunt.co/palette/f9f8f6efe9e3d9cfc7c9b59c)

---

## Color Tokens

The full token config lives in the `tailwind.config` block at the top of each HTML template. Changes must be applied to **both** `index.html` and `privacy.html` until a shared config file is introduced.

### Warm Neutrals (base palette)

| Token | Hex | Semantic Use |
|---|---|---|
| `warm-50` | `#F9F8F6` | Page background |
| `warm-100` | `#EFE9E3` | Card borders, input borders |
| `warm-200` | `#D9CFC7` | Dividers |
| `warm-300` | `#C9B59C` | Decorative only — **not for text** |
| `warm-600` | `#6B5C54` | Secondary text: subtitles, body paragraphs, disclaimers, privacy notice |
| `warm-700` | `#4A3B34` | Tertiary text: all-caps field labels, word counter, meta |
| `warm-900` | `#2C2420` | Primary text: headings, strong emphasis, CTA button background, links |

> **Rule:** Never use `warm-300` for readable text — it fails contrast against white. Use `warm-600` as the minimum for any body copy.

### Brand (Primary Action)

| Token | Hex | Use |
|---|---|---|
| `brand-500` | `#2C2420` | Button background, link color |
| `brand-600` | `#3D3330` | Button hover state |
| `brand-700` | `#1A1512` | Button active/pressed state |

> **Decision:** Warm indigo was considered for the CTA but rejected — it read as a foreign accent against the fully warm neutral palette. `warm-900` used instead, matching Typeform's dark button pattern and keeping the palette cohesive.

### Status Colors

Used exclusively for result blocks rendered by `main.js` and callout blocks in the privacy page.

| State | Token prefix | Background | Border | Text |
|---|---|---|---|---|
| Danger (crisis, out-of-scope) | `danger-*` | `#FDF1EE` | `#C9634A` | `#7A2D1E` |
| Success (confirmation) | `success-*` | `#EFF4EE` | `#5A8A5E` | `#2D5230` |
| Clarification (needs work) | `clarify-*` | `#FDF5E8` | `#C08A30` | `#7A5210` |
| Info (healthcare reminder, storage notice) | `info-*` | `#EEF1F8` | `#5C6FAF` | `#2D3F7A` |

> **Principle:** All status colors are warm-tinted, not saturated Tailwind defaults. Tailwind's default `red-500` and `green-500` look cold and clinical against the warm neutral base — these replacements were chosen to stay in harmony.

---

## Typography

**Font:** Inter (Google Fonts, loaded via CDN in every template)
```html
<link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;700&display=swap" rel="stylesheet">
```

| Role | Class | Size | Weight | Color token |
|---|---|---|---|---|
| Page heading | `text-3xl font-bold` | 30px | 700 | `warm-900` |
| Section heading (privacy) | `text-lg font-bold` | 18px | 700 | `warm-900` |
| Subtitle / body | `text-sm` | 14px | 400 | `warm-600` |
| Field label | `text-xs font-medium uppercase tracking-widest` | 12px | 500 | `warm-700` |
| Meta / disclaimer / counter | `text-xs` | 12px | 400 | `warm-600` or `warm-700` |

---

## Component Patterns

### Page Layout
- Max width: `max-w-2xl` (main page), `max-w-3xl` (privacy page)
- Page padding: `px-4 py-12`
- Background: `bg-warm-50`

### Main Card
```
bg-white rounded-2xl border border-warm-100 p-8 shadow-sm
```

### Input Textarea
```
w-full px-4 py-3 border border-warm-100 rounded-xl text-sm text-warm-900
placeholder-warm-200 resize-none transition-all duration-150
focus:outline-none focus:ring-2 focus:ring-warm-900 focus:border-warm-900
```

### Primary Button (CTA)
```
w-full bg-brand-500 hover:bg-brand-600 text-white text-sm font-semibold
py-3 px-6 rounded-xl transition-colors duration-200
focus:outline-none focus:ring-2 focus:ring-warm-900 focus:ring-offset-2
```

### Secondary Button ("Ask Another Question")
```
w-full bg-warm-100 hover:bg-warm-200 text-warm-900 text-sm font-semibold
py-3 px-6 rounded-xl transition-colors duration-200
```

### Status Block (result cards in main.js)
Left-border accent pattern — used for all response type blocks:
```
bg-{state}-50 border-l-4 border-{state}-500 p-4 rounded-r-xl
```
Text inside: `text-sm text-{state}-900`

### Clarification Option Cards (numbered chip pattern)
```
w-full text-left px-4 py-3 bg-white hover:bg-warm-50 border border-warm-100
rounded-xl transition-colors duration-150
```
Numbered chip (left anchor):
```
w-7 h-7 rounded-full bg-warm-100 flex items-center justify-center
text-xs font-semibold text-warm-700
```

### Links
- **Inline links:** `text-warm-900 underline hover:text-warm-600 transition-colors duration-150`
- **Back navigation:** `text-warm-700 hover:text-warm-900 text-sm font-medium inline-flex items-center`

---

## Result Block Rendering (main.js)

Result blocks are rendered dynamically by `main.js` after a `POST /api/check` response. The block types and their intended visual treatments are:

| Block type | Subtype | Visual treatment |
|---|---|---|
| `crisis_warning` | `self_harm`, `drug_seeking`, `emergency` | `danger-*` left-border banner |
| `main_content` | `confirmation` | `success-*` card with checkmark icon |
| `main_content` | `clarification` | White card, numbered option chips |
| `main_content` | `out_of_scope` | `danger-*` card with X icon |
| `healthcare_reminder` | — | `info-*` left-border banner |
| `footer` | — | `clarify-*` or `success-*` left-border, depending on response path |

---

## Known Maintenance Risk

The Tailwind config block is **duplicated** in `index.html` and `privacy.html`. If you change a token value, update both files. A future improvement would be to extract this into a shared `static/tailwind.config.js` and reference it from both templates.
