/**
 * MorphButton — pill-morph CTA button
 *
 * ROOT CAUSE OF THE SNAP BUG (and why this file exists):
 *
 *   The original code used `motion(Link)` — Framer Motion wrapping a
 *   React Router component. For wrapped (non-native) components, Framer
 *   Motion cannot own style writes directly; it must pass the animated
 *   value back through React's style prop pipeline. Any ancestor
 *   re-render (e.g. Navbar updating `hov` or `scrolled` state) causes
 *   React to reconcile the component with the original `style` object —
 *   writing `borderRadius: 12px` directly to the DOM and overriding
 *   whatever Framer Motion had set mid-tween. Result: instant snap.
 *
 *   Fix: use `motion.a` (a native motion element). Framer Motion owns
 *   ALL style writes via motion values and RAF — React's reconciler
 *   never touches `borderRadius`. SPA navigation is replicated with
 *   `useNavigate`.
 *
 * UNIVERSAL REUSE:
 *   Import `MORPH_TRANSITION` and `morphHover()` to apply the exact
 *   same micro-interaction to any `motion.*` element in the codebase.
 *
 *   Example:
 *     import { MORPH_TRANSITION, morphHover } from '@/components/MorphButton'
 *
 *     <motion.div
 *       style={{ borderRadius: 12 }}
 *       whileHover={morphHover()}
 *       transition={MORPH_TRANSITION}
 *     />
 */

import { motion } from 'framer-motion'
import { useNavigate } from 'react-router-dom'

const ACCENT_RGB = '16, 185, 129'

/* ─── Reusable morph primitives ─────────────────────────────────────
   Import these into any file that needs the same micro-interaction.
   ─────────────────────────────────────────────────────────────────── */

/** Transition config for the border-radius morph + all hover properties.
 *  Apply to the `transition` prop of any `motion.*` element. */
export const MORPH_TRANSITION = {
  borderRadius:    { duration: 0.22, ease: [0.25, 0.46, 0.45, 0.94] },
  y:               { duration: 0.15, ease: 'easeOut' },
  scale:           { duration: 0.10 },
  backgroundColor: { duration: 0.17 },
  boxShadow:       { duration: 0.17 },
  color:           { duration: 0.17 },
  borderColor:     { duration: 0.17 },
}

/** Returns a `whileHover` object with the pill morph + any extra overrides.
 *  Apply to the `whileHover` prop of any `motion.*` element.
 *
 *  @param {object} overrides  Additional whileHover properties to merge in.
 */
export function morphHover(overrides = {}) {
  return { borderRadius: 999, y: -2, ...overrides }
}

/* ─── Component ─────────────────────────────────────────────────── */

export default function MorphButton({ children, primary, to, large, href, onClick, ...rest }) {
  const navigate = useNavigate()

  const handleClick = (e) => {
    if (onClick) { onClick(e); return }
    if (!to) return
    // Let the browser handle absolute / external URLs normally
    if (/^https?:\/\/|^\/\//.test(to)) return
    e.preventDefault()
    navigate(to)
  }

  return (
    <motion.a
      href={to || href || '#'}
      onClick={handleClick}
      style={{
        display: 'inline-flex', alignItems: 'center', textDecoration: 'none',
        whiteSpace: 'nowrap', cursor: 'pointer',
        /* borderRadius here becomes a Framer Motion motion value —
           React's reconciler never writes to it, so tweens are safe. */
        borderRadius: 12,
        gap:        large ? '10px' : '8px',
        padding:    large ? '18px 40px' : '11px 22px',
        fontFamily: 'Satoshi, sans-serif',
        fontSize:   large ? '17px' : '14px',
        fontWeight: large ? '600'  : '500',
        ...(primary ? {
          backgroundColor: `rgba(${ACCENT_RGB}, 1)`,
          color: '#0E1113',
          border: '1px solid transparent',
          boxShadow: `0 4px 12px rgba(${ACCENT_RGB}, 0.22)`,
        } : {
          backgroundColor: 'transparent',
          color: 'rgba(255,255,255,0.72)',
          border: '1px solid rgba(255,255,255,0.22)',
        }),
      }}
      whileHover={morphHover(primary ? {
        backgroundColor: `rgba(${ACCENT_RGB}, 0.84)`,
        boxShadow: `0 8px 24px rgba(${ACCENT_RGB}, 0.38)`,
      } : {
        color: `rgba(${ACCENT_RGB}, 1)`,
        borderColor: `rgba(${ACCENT_RGB}, 0.65)`,
      })}
      whileTap={{ scale: 0.97, y: -1 }}
      transition={MORPH_TRANSITION}
      {...rest}
    >
      {children}
    </motion.a>
  )
}
