# MESHWORK DESIGN SYSTEM
## Version 1.0
### Motto: Engineered, Not Designed.

---

# 1. DESIGN PHILOSOPHY

## 1.1 Core Principle
MeshWork is engineered, not designed.

Every visual decision must have structural intent. No decorative styling without behavioral or hierarchical purpose.

The interface must communicate:
- Structure over ornament
- State over style
- Depth over noise
- Motion over decoration

Design must feel inevitable — not experimental.

---

## 1.2 Emotional Identity

MeshWork should feel:
- Bold
- Innovative
- Structured
- Cinematic but restrained
- Premium but calm
- Technical but human

It must never feel:
- Playful
- Over-animated
- Neon or startup-dribbble styled
- Corporate-template-like
- Crowded

---

# 2. FOUNDATION SYSTEM

## 2.1 Color Architecture

### Token Structure

Two layers of tokens must exist.

Layer 1 — Primitive Tokens (Raw Values)
Layer 2 — Semantic Tokens (Used by components)

No component may use primitive tokens directly.

---

### Dark Mode — Primitive Tokens

color-neutral-900: #0E1113
color-neutral-800: #14181B
color-neutral-700: #1B2024
color-neutral-600: #2A3036
color-neutral-100: #E6EDF3
color-neutral-400: #9AA4AE

color-emerald-500: #10B981
color-emerald-600: #0EA371
color-emerald-700: #0B7A56

color-warning-500: #EAB308
color-error-500: #EF4444

---

### Semantic Tokens (Dark)

bg-primary → color-neutral-900
bg-surface → color-neutral-800
bg-surface-elevated → color-neutral-700
text-primary → color-neutral-100
text-secondary → color-neutral-400
border-subtle → rgba(255,255,255,0.06)
accent-primary → color-emerald-500
accent-hover → color-emerald-600
accent-active → color-emerald-700
accent-soft → rgba(16,185,129,0.12)

---

### Light Mode Mapping

bg-primary → #F7F9FA
bg-surface → #FFFFFF
bg-surface-elevated → #F1F5F9
text-primary → #0F172A
text-secondary → #475569
accent-primary → #059669
accent-hover → #047857

Light mode must not invert blindly. It must feel deliberate.

---

## 2.2 Contrast & Accessibility

- Minimum 4.5:1 for body text
- Accent on dark must pass contrast
- Focus ring must always be visible

Focus ring token:
outline: 2px solid accent-primary
outline-offset: 2px

Reduced motion mode must disable:
- Parallax
- Large transform animations
- Continuous float loops

---

# 3. TYPOGRAPHY SYSTEM

## Fonts

Headlines: Clash Display
Body/UI: Satoshi
Fallback chain must be defined.

---

## Type Scale

Hero: 72 / 80 – Clash – 600
Section Title: 40 / 48 – Clash – 500
Subsection: 28 / 36 – Satoshi – 600
Body Large: 18 / 28 – Satoshi – 400
Body: 16 / 24 – Satoshi – 400
Small: 14 / 20 – Satoshi – 400

No arbitrary sizes allowed.

---

# 4. SPACING SYSTEM

Base unit: 8px

Allowed spacing:
8, 16, 24, 32, 48, 64, 96, 128

Hero vertical padding minimum: 96px

Whitespace equals confidence. Never compress sections.

---

# 5. BORDER RADIUS SYSTEM

Small elements: 8px
Buttons: 12px
Cards: 14px
Large containers: 18px

No pill radius by default.
Pill radius allowed only during CTA hover animation.

---

# 6. ELEVATION & SHADOW SYSTEM

Dark mode relies more on surface contrast than shadow.

Card shadow:
0 4px 24px rgba(0,0,0,0.25)

Hover lift:
translateY(-2px)

No heavy glow.

---

# 7. Z-INDEX SCALE

z-base: 0
z-content: 10
z-header: 100
z-dropdown: 200
z-sticky: 300
z-overlay: 400
z-modal: 500
z-toast: 600
z-tooltip: 700
z-max: 999

No arbitrary z-index allowed.

---

# 8. COMPONENT SYSTEM

## Buttons

Variants:
- Primary
- Secondary
- Ghost
- Destructive
- Icon

States:
Idle
Hover
Focus
Active
Disabled
Loading

Primary Behavior:
Default radius 12px
On hover → radius animates to 999px
Glow increases slightly
On active → scale 0.97
On release → returns to 12px

Duration: 250–300ms

Secondary buttons do not morph.

---

## Inputs

Dark surface background
1px subtle border

On focus:
border becomes accent-primary
faint outer glow

Error state:
border becomes error-500
small error message below

No heavy red background.

---

## Toast Notifications

Appear from bottom-right
Fade + slight upward motion (16px)
Auto-dismiss after 4s
ARIA live region required

---

## Modals

Background overlay: rgba(0,0,0,0.5)
Centered container
Radius 18px
Fade + scale 0.98 → 1

---

## Cards

Surface elevated
14px radius
1px subtle border
Hover lift 2px

---

## Progress Bars

Track: neutral-700
Fill: accent-primary
Smooth width animation

XP highlight may pulse softly once.

---

## Loaders

Spinner: subtle stroke animation
Skeleton: animated shimmer
Duration slow and calm

---

# 9. AUTHENTICATION EXPERIENCE

Full-screen immersive split layout.

Left Panel:
Brand + image
Subtle float loop (6–8s)
Parallax max 8px
Image fade + scale 0.98 on state change

Right Panel:
Max width 420px
Centered vertically

Title Animation:
Mask wipe upward for both states
300–350ms duration

Field Expansion:
Layout animation when switching login ↔ signup
No jump allowed

---

# 10. LANDING MOTION SYSTEM

Level 2 Controlled Cinematic

- Fade + translateY 12px
- Duration 300–600ms
- Parallax intensity under 5%
- No bounce

Motion must communicate hierarchy, not entertainment.

---

# 11. ACCESSIBILITY

- ARIA attributes required
- Keyboard focus support
- Skip-to-content link
- Reduced motion media query support

---

# 12. INTERNATIONALIZATION READINESS

- Logical CSS properties (margin-inline-start etc.)
- Font fallback chain defined
- Date/time formatting abstraction layer

---

# 13. IMPLEMENTATION STACK

Frontend:
React
Tailwind
Framer Motion
Lucide Icons

Backend:
Flask API

Theme:
CSS variables for token mapping
Dark default
Light toggle supported

---

# FINAL STATEMENT

MeshWork is not styled.
It is structured.

Motion is controlled.
Color is intentional.
Spacing is disciplined.

Every interaction must feel engineered.

If a visual decision does not serve hierarchy, clarity, or state — it must be removed.

