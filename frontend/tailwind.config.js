/** @type {import('tailwindcss').Config} */

/**
 * MESHWORK DESIGN SYSTEM — tailwind.config.js
 *
 * Architecture rule:
 * All color values here point to CSS variables (semantic tokens).
 * Raw hex values are ONLY in index.css primitive token layer.
 * Components use Tailwind classes → Tailwind reads CSS vars → CSS vars read primitives.
 *
 * This means changing a brand color = one line in index.css.
 * Nothing else changes.
 */

export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],

  // Dark mode: toggled via class on <html> element
  // Usage: document.documentElement.classList.toggle('dark')
  // Note: We use 'light' class for light mode since dark is our default.
  // Tailwind darkMode: 'class' enables .dark: variant throughout.
  darkMode: 'class',

  theme: {
    // --- Override defaults deliberately ---
    // We do NOT extend borderRadius globally — design system has fixed values only.
    // We DO extend colors, fonts, spacing, shadows.

    extend: {

      /* --------------------------------------------------------
         COLORS — Semantic tokens only
         These map to CSS variables in index.css.
         No raw hex values here.
         -------------------------------------------------------- */
      colors: {
        // Background layers
        'bg-primary':   'var(--bg-primary)',
        'bg-surface':   'var(--bg-surface)',
        'bg-elevated':  'var(--bg-surface-elevated)',

        // Text
        'text-primary':   'var(--text-primary)',
        'text-secondary': 'var(--text-secondary)',

        // Accent
        'accent': {
          DEFAULT: 'var(--accent-primary)',
          hover:   'var(--accent-hover)',
          active:  'var(--accent-active)',
          soft:    'var(--accent-soft)',
        },

        // Feedback
        'error':   'var(--color-error)',
        'warning': 'var(--color-warning)',

        // Border
        'border-subtle': 'var(--border-subtle)',
      },

      /* --------------------------------------------------------
         FONT FAMILIES
         Display = Clash Display (headlines only)
         Sans    = Satoshi (all body and UI)
         Mono    = fallback for code
         -------------------------------------------------------- */
      fontFamily: {
        display: [
          'Clash Display',
          'system-ui',
          '-apple-system',
          'sans-serif',
        ],
        sans: [
          'Satoshi',
          'system-ui',
          '-apple-system',
          'sans-serif',
        ],
        mono: [
          'JetBrains Mono',
          'ui-monospace',
          'monospace',
        ],
      },

      /* --------------------------------------------------------
         FONT SIZES — Design system type scale ONLY
         Format: [size, { lineHeight, letterSpacing?, fontWeight? }]
         No arbitrary sizes. These six are the entire allowed scale.
         -------------------------------------------------------- */
      fontSize: {
        // Hero: 72 / 80 — Clash — 600
        'hero': ['72px', {
          lineHeight: '80px',
          fontWeight: '600',
        }],

        // Section Title: 40 / 48 — Clash — 500
        'section-title': ['40px', {
          lineHeight: '48px',
          fontWeight: '500',
        }],

        // Subsection: 28 / 36 — Satoshi — 600
        'subsection': ['28px', {
          lineHeight: '36px',
          fontWeight: '600',
        }],

        // Body Large: 18 / 28 — Satoshi — 400
        'body-lg': ['18px', {
          lineHeight: '28px',
          fontWeight: '400',
        }],

        // Body: 16 / 24 — Satoshi — 400
        'body': ['16px', {
          lineHeight: '24px',
          fontWeight: '400',
        }],

        // Small: 14 / 20 — Satoshi — 400
        'small': ['14px', {
          lineHeight: '20px',
          fontWeight: '400',
        }],
      },

      /* --------------------------------------------------------
         BORDER RADIUS — Design system fixed values only
         small: 8px | buttons: 12px | cards: 14px | large: 18px
         pill: 999px (only during CTA hover via CSS transition)
         -------------------------------------------------------- */
      borderRadius: {
        'sm':     '8px',   // Small elements, inputs
        'btn':    '12px',  // Buttons default
        'card':   '14px',  // Cards
        'lg':     '18px',  // Large containers, modals
        'pill':   '999px', // Only used via CSS transition on hover — not direct
      },

      /* --------------------------------------------------------
         BOX SHADOWS — Design system shadow tokens
         Dark mode relies on surface contrast more than shadow.
         -------------------------------------------------------- */
      boxShadow: {
        // Standard card shadow
        'card':  '0 4px 24px rgba(0, 0, 0, 0.25)',
        // Elevated hover state
        'hover': '0 8px 32px rgba(0, 0, 0, 0.35)',
        // Subtle inner surfaces
        'sm':    '0 1px 4px rgba(0, 0, 0, 0.15)',
      },

      /* --------------------------------------------------------
         SPACING — 8px base grid
         Only multiples of 8 are structurally valid.
         These are Tailwind's defaults but we document intent here.
         Tailwind default: 1 unit = 4px, so 8px = 2, 16px = 4, etc.
         Custom additions for design system-specific values.
         -------------------------------------------------------- */
      spacing: {
        // Hero vertical padding minimum: 96px
        'section-v': '128px',
        'hero-v':    '96px',
      },

      /* --------------------------------------------------------
         Z-INDEX — Design system z-scale
         No arbitrary z-index allowed.
         -------------------------------------------------------- */
      zIndex: {
        'base':     '0',
        'content':  '10',
        'header':   '100',
        'dropdown': '200',
        'sticky':   '300',
        'overlay':  '400',
        'modal':    '500',
        'toast':    '600',
        'tooltip':  '700',
        'max':      '999',
      },

      /* --------------------------------------------------------
         ANIMATIONS — Design system motion rules
         Max duration: 600ms
         Default: 300–400ms
         No bounce. No elastic. Controlled cubic-bezier only.
         -------------------------------------------------------- */
      transitionTimingFunction: {
        // MeshWork standard easing — controlled, not elastic
        'mesh': 'cubic-bezier(0.25, 0.1, 0.25, 1.0)',
        // Slight ease-out for exits
        'mesh-out': 'cubic-bezier(0.0, 0.0, 0.2, 1.0)',
        // Slight ease-in for entrances
        'mesh-in': 'cubic-bezier(0.4, 0.0, 1.0, 1.0)',
      },

      transitionDuration: {
        '250': '250ms',
        '350': '350ms',
        '450': '450ms',
      },

      keyframes: {
        // Landing section entrance: fade + translateY 12px
        // Used by hero headline, subtext, buttons
        'fade-up': {
          '0%':   { opacity: '0', transform: 'translateY(16px)' },
          '100%': { opacity: '1', transform: 'translateY(0)' },
        },

        // Illustration entrance: fade + scale
        'fade-scale': {
          '0%':   { opacity: '0', transform: 'scale(0.98)' },
          '100%': { opacity: '1', transform: 'scale(1)' },
        },

        // Float loop for hero illustration: 6–8s
        'float': {
          '0%, 100%': { transform: 'translateY(0px)' },
          '50%':      { transform: 'translateY(-8px)' },
        },

        // Scroll-triggered section reveal
        'reveal': {
          '0%':   { opacity: '0', transform: 'translateY(12px)' },
          '100%': { opacity: '1', transform: 'translateY(0)' },
        },

        // Skeleton shimmer for loading states
        'shimmer': {
          '0%':   { backgroundPosition: '-200% 0' },
          '100%': { backgroundPosition: '200% 0' },
        },
      },

      animation: {
        // Entrance animations — used with animation-delay utilities
        'fade-up':    'fade-up 500ms cubic-bezier(0.25, 0.1, 0.25, 1.0) forwards',
        'fade-scale': 'fade-scale 600ms cubic-bezier(0.25, 0.1, 0.25, 1.0) forwards',

        // Float loop — hero illustration only
        // Disabled by reduced-motion media query in index.css
        'float':      'float 7s ease-in-out infinite',

        // Scroll reveal
        'reveal':     'reveal 400ms cubic-bezier(0.25, 0.1, 0.25, 1.0) forwards',

        // Loader
        'shimmer':    'shimmer 2s linear infinite',
      },
    },
  },

  plugins: [],
}