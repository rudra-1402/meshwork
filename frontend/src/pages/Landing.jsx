/**
 * MESHWORK — Landing Page v5
 * All animations are scroll-dependent and bidirectional (play/rewind).
 * No animation fires on mount — everything is driven by scroll position.
 *
 * Architecture:
 * - GSAP + ScrollTrigger: all structural animations, scrubbed or toggleActions bidirectional
 * - Framer Motion: hover micro-interactions only
 * - No once:true anywhere — user can replay by scrolling up
 * - No element has both libraries writing to its transform
 */

import React, { useState, useEffect, useRef, useCallback, useMemo } from 'react'
import {
  motion, AnimatePresence,
  useMotionValue, useSpring,
  useScroll, useTransform,
} from 'framer-motion'
import { Link } from 'react-router-dom'
import MorphButton from '../components/MorphButton'
import {
  Zap, Workflow, Info, ArrowRight,
  Target, Layers, Compass,
  GraduationCap, Wrench, TrendingUp,
} from 'lucide-react'
import { gsap } from 'gsap'
import { ScrollTrigger } from 'gsap/ScrollTrigger'

gsap.registerPlugin(ScrollTrigger)

/* ─────────────────────────────────────────────
   CONSTANTS
───────────────────────────────────────────── */
const BRAND      = 'MeshWork'
const ACCENT_RGB = '16, 185, 129'
const GLITCH     = 'ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789@#$%&'
const NO_MOTION  = () =>
  typeof window !== 'undefined' &&
  window.matchMedia('(prefers-reduced-motion: reduce)').matches

/* ─────────────────────────────────────────────
   GLITCH SCRAMBLE HOOK
───────────────────────────────────────────── */
function useGlitchScramble(target, go) {
  const chars = useMemo(() => target.split(''), [target])
  const [disp, setDisp] = useState(() =>
    chars.map(() => GLITCH[Math.floor(Math.random() * GLITCH.length)]))
  const [done, setDone] = useState(false)
  const rafRef  = useRef(null)
  const doneRef = useRef(false)
  const startedRef = useRef(false)

  useEffect(() => {
    if (!go || startedRef.current) return
    startedRef.current = true
    const settled = new Array(chars.length).fill(false)
    const times   = chars.map((_, i) => 900 + i * 140 + Math.random() * 220)
    const t0      = performance.now()
    let last = 0
    const tick = (now) => {
      if (doneRef.current) return
      if (now - last < 33) { rafRef.current = requestAnimationFrame(tick); return }
      last = now
      const el   = now - t0
      const next = chars.map((c, i) => {
        if (el >= times[i]) { settled[i] = true; return c }
        return GLITCH[Math.floor(Math.random() * GLITCH.length)]
      })
      setDisp(next)
      if (settled.every(Boolean)) { doneRef.current = true; setDone(true); return }
      rafRef.current = requestAnimationFrame(tick)
    }
    rafRef.current = requestAnimationFrame(tick)
    return () => { if (rafRef.current) cancelAnimationFrame(rafRef.current) }
  }, [go, chars])

  return { disp, done }
}

/* ─────────────────────────────────────────────
   GEOMETRIC CANVAS
───────────────────────────────────────────── */
function GeometricCanvas({ opacityRef }) {
  const canvasRef = useRef(null)
  const animRef   = useRef(null)
  const mounted   = useRef(false)

  useEffect(() => {
    if (mounted.current) return
    mounted.current = true
    if (NO_MOTION()) return
    const cv = canvasRef.current; if (!cv) return
    const ctx = cv.getContext('2d')
    const resize = () => { cv.width = cv.offsetWidth; cv.height = cv.offsetHeight }
    resize(); window.addEventListener('resize', resize)
    const COLS = 16, ROWS = 11
    let pts = []
    const build = () => {
      pts = []
      const cw = cv.width / (COLS - 1), ch = cv.height / (ROWS - 1)
      for (let r = 0; r < ROWS; r++)
        for (let c = 0; c < COLS; c++) {
          const ox = r % 2 === 0 ? 0 : cw * .5
          pts.push({ bx: c*cw+ox, by: r*ch, x: c*cw+ox, y: r*ch,
            phase: Math.random()*Math.PI*2, speed: .003+Math.random()*.005 })
        }
    }
    build()
    let t = 0
    const draw = () => {
      ctx.clearRect(0, 0, cv.width, cv.height)
      t += .008
      const op = opacityRef?.current ?? 1
      pts.forEach(p => {
        p.x = p.bx + Math.sin(t * p.speed * 60 + p.phase) * 14
        p.y = p.by + Math.cos(t * p.speed * 45 + p.phase * .7) * 10
      })
      for (let i = 0; i < pts.length; i++)
        for (let j = i + 1; j < pts.length; j++) {
          const dx = pts[i].x - pts[j].x, dy = pts[i].y - pts[j].y
          const d  = Math.sqrt(dx*dx + dy*dy)
          const maxD = cv.width / (COLS - 1) * 1.75
          if (d < maxD) {
            ctx.beginPath()
            ctx.strokeStyle = `rgba(${ACCENT_RGB},${(1 - d/maxD) * .16 * op})`
            ctx.lineWidth = .7
            ctx.moveTo(pts[i].x, pts[i].y); ctx.lineTo(pts[j].x, pts[j].y)
            ctx.stroke()
          }
        }
      pts.forEach(p => {
        const pulse = .5 + .5 * Math.sin(t * 40 * p.speed + p.phase)
        const sz    = 3.4 + pulse * 2.6
        ctx.save(); ctx.translate(p.x, p.y); ctx.rotate(Math.PI / 4)
        ctx.fillStyle = `rgba(${ACCENT_RGB},${(.12 + pulse * .14) * op})`
        ctx.fillRect(-sz/2, -sz/2, sz, sz); ctx.restore()
      })
      animRef.current = requestAnimationFrame(draw)
    }
    draw()
    return () => {
      window.removeEventListener('resize', resize)
      cancelAnimationFrame(animRef.current)
    }
  }, [opacityRef])

  return <canvas ref={canvasRef} aria-hidden="true" style={{
    position: 'absolute', inset: 0, width: '100%', height: '100%', pointerEvents: 'none',
  }}/>
}

/* ─────────────────────────────────────────────
   PARTICLE CANVAS
───────────────────────────────────────────── */
function ParticleCanvas() {
  const cv  = useRef(null)
  const raf = useRef(null)
  const mn  = useRef(false)

  useEffect(() => {
    if (mn.current) return; mn.current = true
    if (NO_MOTION()) return
    const c = cv.current; if (!c) return
    const ctx = c.getContext('2d')
    const resize = () => { c.width = c.offsetWidth; c.height = c.offsetHeight }
    resize(); window.addEventListener('resize', resize)
    const ps = Array.from({ length: 48 }, () => ({
      x: Math.random() * c.width,  y: Math.random() * c.height,
      vx: (Math.random() - .5) * .25, vy: (Math.random() - .5) * .25,
      r: Math.random() * 1.3 + .4, base: Math.random() * .3 + .07,
      ps: Math.random() * .016 + .004, po: Math.random() * Math.PI * 2,
    }))
    let t = 0
    const draw = () => {
      ctx.clearRect(0, 0, c.width, c.height); t += .016
      for (let i = 0; i < ps.length; i++)
        for (let j = i + 1; j < ps.length; j++) {
          const dx = ps[i].x - ps[j].x, dy = ps[i].y - ps[j].y
          const d  = Math.sqrt(dx*dx + dy*dy)
          if (d < 120) {
            ctx.beginPath()
            ctx.strokeStyle = `rgba(${ACCENT_RGB},${(1 - d/120) * .09})`
            ctx.lineWidth = .5
            ctx.moveTo(ps[i].x, ps[i].y); ctx.lineTo(ps[j].x, ps[j].y)
            ctx.stroke()
          }
        }
      ps.forEach(p => {
        ctx.beginPath(); ctx.arc(p.x, p.y, p.r, 0, Math.PI * 2)
        ctx.fillStyle = `rgba(${ACCENT_RGB},${p.base * (.7 + .3 * Math.sin(t * p.ps * 60 + p.po))})`
        ctx.fill()
        p.x += p.vx; p.y += p.vy
        if (p.x < 0) p.x = c.width;  if (p.x > c.width)  p.x = 0
        if (p.y < 0) p.y = c.height; if (p.y > c.height) p.y = 0
      })
      raf.current = requestAnimationFrame(draw)
    }
    draw()
    return () => { window.removeEventListener('resize', resize); cancelAnimationFrame(raf.current) }
  }, [])

  return <canvas ref={cv} aria-hidden="true" style={{
    position: 'absolute', inset: 0, width: '100%', height: '100%', pointerEvents: 'none', opacity: .6,
  }}/>
}

/* MorphButton is imported from ../components/MorphButton.
   See that file for the explanation of why motion(Link) caused
   the instant-snap bug and how motion.a fixes it. */


/* ─────────────────────────────────────────────
   SECTION 1 — BRAND INTRO
   200vh outer / 100vh sticky inner.
   Navbar appears only after brand reaches 85% collapse
   so there is never a double-name overlap.
───────────────────────────────────────────── */
function BrandIntroSection({ onBrandLocked }) {
  const outerRef     = useRef(null)
  const stickyRef    = useRef(null)
  const brandRef     = useRef(null)
  const taglineRef   = useRef(null)
  const scrollIndRef = useRef(null)
  const canvasOpRef  = useRef(1)

  const [go, setGo]            = useState(false)
  const [scrambleReady, setReady] = useState(false)
  const { disp, done } = useGlitchScramble(BRAND, go)

  const rawX = useMotionValue(0), rawY = useMotionValue(0)
  const spX  = useSpring(rawX, { stiffness: 45, damping: 16 })
  const spY  = useSpring(rawY, { stiffness: 45, damping: 16 })
  const cursorOn = useRef(true)

  useEffect(() => { const t = setTimeout(() => setGo(true), 300); return () => clearTimeout(t) }, [])
  useEffect(() => { if (done) setReady(true) }, [done])

  const onMouseMove = useCallback((e) => {
    if (!cursorOn.current) return
    const r = stickyRef.current?.getBoundingClientRect(); if (!r) return
    const cl = (v, a, b) => Math.min(Math.max(v, a), b)
    rawX.set(cl((e.clientX - (r.left + r.width / 2))  * .08, -36, 36))
    rawY.set(cl((e.clientY - (r.top  + r.height / 2)) * .08, -36, 36))
  }, [rawX, rawY])

  useEffect(() => {
    if (NO_MOTION()) {
      const h = () => {
        const hh = outerRef.current?.offsetHeight ?? window.innerHeight * 2
        if (window.scrollY > hh * .65) onBrandLocked?.(true)
        else if (window.scrollY < hh * .25) onBrandLocked?.(false)
      }
      window.addEventListener('scroll', h, { passive: true })
      return () => window.removeEventListener('scroll', h)
    }

    const g = gsap, ST = ScrollTrigger
    const ctx = g.context(() => {
      ST.create({
        trigger: outerRef.current,
        start: 'top top', end: 'bottom bottom',
        onUpdate: self => {
          cursorOn.current     = self.progress < .04
          canvasOpRef.current  = 1 - self.progress * .85
          if (!cursorOn.current) { rawX.set(0); rawY.set(0) }
          /*
           * Navbar appears at 85% progress.
           * At that point brand scale = ~0.32 so visually it's already
           * small — well before it reaches the navbar y-position.
           * This prevents any double-name overlap.
           */
          if (self.progress > .85) onBrandLocked?.(true)
          else if (self.progress < .4) onBrandLocked?.(false)
        },
      })

      g.timeline({
        scrollTrigger: {
          trigger: outerRef.current,
          start: 'top top', end: 'bottom bottom',
          scrub: 1.6,
        },
      })
      .to(brandRef.current, {
        scale: 0.32,
        y: -(window.innerHeight / 2 - 28),
        letterSpacing: '-0.01em',
        ease: 'none',
      })
      .to(taglineRef.current,   { opacity: 0, y: -14, filter: 'blur(8px)', ease: 'none', duration: .4 }, 0)
      .to(scrollIndRef.current, { opacity: 0, ease: 'none', duration: .2 }, 0)
    })

    return () => ctx.revert()
  }, [onBrandLocked, rawX, rawY])

  return (
    <div ref={outerRef} style={{ height: '200vh', position: 'relative' }} onMouseMove={onMouseMove}>
      <div ref={stickyRef} style={{
        position: 'sticky', top: 0, height: '100vh',
        display: 'flex', alignItems: 'center', justifyContent: 'center',
        overflow: 'hidden', backgroundColor: 'var(--bg-primary)',
      }}>
        <GeometricCanvas opacityRef={canvasOpRef}/>

        <div aria-hidden="true" style={{
          position: 'absolute', inset: 0, pointerEvents: 'none', zIndex: 1,
          background: 'radial-gradient(ellipse 60% 55% at 50% 50%, transparent 58%, color-mix(in srgb, var(--bg-primary) 45%, transparent) 72%, var(--bg-primary) 100%)',
        }}/>
        <div aria-hidden="true" style={{
          position: 'absolute', top: '50%', left: '50%', transform: 'translate(-50%,-50%)',
          width: '720px', height: '480px', borderRadius: '50%', filter: 'blur(30px)',
          background: `radial-gradient(ellipse, rgba(${ACCENT_RGB},.1) 0%, transparent 68%)`,
          pointerEvents: 'none', zIndex: 1,
        }}/>

        <motion.div style={{ x: spX, y: spY, position: 'relative', zIndex: 10, textAlign: 'center' }}>
          <div ref={brandRef} style={{ transformOrigin: 'center center', display: 'inline-block', willChange: 'transform' }}>
            <div aria-label={BRAND} style={{
              fontFamily: 'Clash Display, sans-serif',
              fontSize: 'clamp(68px, 12vw, 128px)', fontWeight: '600',
              letterSpacing: '-0.035em', userSelect: 'none',
              display: 'flex', justifyContent: 'center', lineHeight: 1,
            }}>
              {disp.map((ch, i) => (
                <motion.span key={i} aria-hidden="true"
                  animate={{
                    color: ch === BRAND[i] ? 'var(--text-primary)' : `rgba(${ACCENT_RGB},.55)`,
                    textShadow: ch === BRAND[i] ? `0 0 40px rgba(${ACCENT_RGB},.08)` : 'none',
                  }}
                  transition={{ duration: .12, ease: 'easeOut' }}
                  style={{ display: 'inline-block', minWidth: '.52em' }}
                >{ch}</motion.span>
              ))}
            </div>
          </div>

          <div ref={taglineRef} style={{ marginTop: '36px' }}>
            <AnimatePresence>
              {scrambleReady && (
                <motion.p
                  initial={{ opacity: 0, y: 16 }} animate={{ opacity: 1, y: 0 }}
                  transition={{ duration: .65, delay: .35, ease: [.25,.1,.25,1] }}
                  style={{
                    fontFamily: 'Satoshi, sans-serif', fontSize: '13px',
                    letterSpacing: '.18em', textTransform: 'uppercase',
                    color: 'var(--text-secondary)', margin: 0,
                  }}
                >Engineered, not designed.</motion.p>
              )}
            </AnimatePresence>
          </div>
        </motion.div>

        <div ref={scrollIndRef} aria-hidden="true" style={{
          position: 'absolute', bottom: '44px', left: '50%',
          transform: 'translateX(-50%)', zIndex: 10,
          opacity: scrambleReady ? 1 : 0, transition: 'opacity .5s ease .7s',
        }}>
          <motion.div
            animate={scrambleReady ? { y: [0, 10, 0] } : {}}
            transition={{ duration: 2.2, repeat: Infinity, ease: 'easeInOut' }}
            style={{ width: '1px', height: '52px', background: `linear-gradient(to bottom, transparent, rgba(${ACCENT_RGB},.5))` }}
          />
        </div>
      </div>
    </div>
  )
}

/* ─────────────────────────────────────────────
   NAVBAR
───────────────────────────────────────────── */
const NAV_ITEMS = [
  { icon: Zap,      label: 'Features',     href: '#features'     },
  { icon: Workflow, label: 'How It Works', href: '#how-it-works' },
  { icon: Info,     label: 'About',        href: '#about'        },
]

function Navbar({ visible }) {
  const [scrolled, setScrolled] = useState(false)
  const [hov, setHov]           = useState(null)

  useEffect(() => {
    const fn = () => setScrolled(window.scrollY > 10)
    window.addEventListener('scroll', fn, { passive: true })
    return () => window.removeEventListener('scroll', fn)
  }, [])

  return (
    <AnimatePresence>
      {visible && (
        <motion.header key="nav"
          initial={{ opacity: 0, y: -16 }} animate={{ opacity: 1, y: 0 }} exit={{ opacity: 0, y: -16 }}
          transition={{ duration: .45, ease: [.16,1,.3,1] }}
          role="banner"
          style={{
            position: 'fixed', top: 0, left: 0, right: 0, zIndex: 100,
            display: 'flex', alignItems: 'center', justifyContent: 'space-between',
            padding: '0 56px', height: '68px',
            backgroundColor: scrolled ? 'rgba(14,17,19,.88)' : 'transparent',
            backdropFilter: scrolled ? 'blur(12px)' : 'none',
            borderBottom: scrolled ? '1px solid var(--border-subtle)' : 'none',
            transition: 'background-color 300ms ease, border-color 300ms ease, backdrop-filter 300ms ease',
          }}
        >
          <Link to="/" aria-label="MeshWork home" style={{
            fontFamily: 'Clash Display, sans-serif', fontSize: '24px', fontWeight: '600',
            letterSpacing: '-0.02em', color: 'var(--text-primary)', textDecoration: 'none',
          }}>{BRAND}</Link>

          <nav aria-label="Main navigation" style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
            <div style={{
              display: 'flex', alignItems: 'center', padding: '4px',
              borderRadius: '12px', border: '1px solid var(--border-subtle)',
              backgroundColor: 'rgba(255,255,255,.015)', gap: '2px',
            }}>
              {NAV_ITEMS.map(item => {
                const Icon = item.icon
                const isH  = hov === item.label
                return (
                  <a key={item.label} href={item.href}
                    onMouseEnter={() => setHov(item.label)}
                    onMouseLeave={() => setHov(null)}
                    style={{
                      display: 'flex', alignItems: 'center', gap: '5px',
                      padding: '6px 9px', borderRadius: '8px', textDecoration: 'none',
                      backgroundColor: isH ? 'var(--bg-surface-elevated)' : 'transparent',
                      transition: 'background-color 160ms ease',
                      overflow: 'hidden', whiteSpace: 'nowrap',
                    }}
                  >
                    <Icon size={14} style={{ color: isH ? `rgba(${ACCENT_RGB},1)` : 'var(--text-secondary)', transition: 'color 160ms ease', flexShrink: 0 }}/>
                    <span style={{
                      fontFamily: 'Satoshi, sans-serif', fontSize: '13px', fontWeight: '500',
                      color: 'var(--text-primary)',
                      maxWidth: isH ? '80px' : '0px', opacity: isH ? 1 : 0,
                      overflow: 'hidden',
                      transition: 'max-width 240ms ease, opacity 180ms ease',
                    }}>{item.label}</span>
                  </a>
                )
              })}
            </div>
            <div style={{ width: '1px', height: '20px', backgroundColor: 'var(--border-subtle)', margin: '0 4px' }}/>
            <MorphButton to="/auth">Login</MorphButton>
            <MorphButton to="/auth" primary>Sign Up</MorphButton>
          </nav>
        </motion.header>
      )}
    </AnimatePresence>
  )
}

/* ─────────────────────────────────────────────
   SECTION 2 — HERO
   Scroll-triggered (bidirectional). Not mount-fired.
───────────────────────────────────────────── */
function HeroSection() {
  const outerRef  = useRef(null)
  const sRef      = useRef(null)
  const headRef   = useRef(null)
  const subRef    = useRef(null)
  const btnsRef   = useRef(null)
  const cardRef   = useRef(null)

  const words = 'Where Ambition Meets Collaboration.'.split(' ')

  useEffect(() => {
    if (NO_MOTION()) return
    const g = gsap
    const ctx = g.context(() => {
      const letters = headRef.current.querySelectorAll('.hl')

      g.set(letters,          { y: 20, rotation: 1.5, opacity: 0 })
      g.set(subRef.current,   { opacity: 0, y: 18 })
      g.set(btnsRef.current,  { opacity: 0, y: 18 })
      g.set(cardRef.current,  { opacity: 0, y: 20 })

      g.timeline({
        scrollTrigger: {
          trigger: outerRef.current,
          start: 'top top', end: 'bottom bottom',
          scrub: 1.5,
        },
      })
      .to(letters, { y: 0, rotation: 0, opacity: 1, duration: .6, stagger: .022, ease: 'none' })
      .to(headRef.current.querySelectorAll('.hl-ambition'), {
        textShadow: `0 0 18px rgba(${ACCENT_RGB},.35)`, duration: .25, ease: 'none',
      }, '-=.05')
      .to(subRef.current,  { opacity: 1, y: 0, duration: .5,  ease: 'none' }, '-=1.0')
      .to(btnsRef.current, { opacity: 1, y: 0, duration: .4,  ease: 'none' }, '-=.65')
      .to(cardRef.current, { opacity: 1, y: 0, duration: .55, ease: 'none' }, '-=.8')
      .to({}, { duration: 0.8 })  /* hold: section stays pinned after animation completes */
    })
    return () => ctx.revert()
  }, [])

  return (
    <div ref={outerRef} style={{ height: '340vh', position: 'relative' }}>
      <section ref={sRef} id="hero" style={{
        position: 'sticky', top: 0, height: '100vh',
        display: 'flex', alignItems: 'center',
        padding: '0 64px', overflow: 'hidden',
        backgroundColor: 'var(--bg-primary)',
      }}>
      <ParticleCanvas/>
      <div aria-hidden="true" style={{
        position: 'absolute', top: '20%', left: '5%', width: '700px', height: '700px',
        background: `radial-gradient(circle, rgba(${ACCENT_RGB},.06) 0%, transparent 68%)`,
        pointerEvents: 'none',
      }}/>

      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', width: '100%', gap: '64px', position: 'relative', zIndex: 10 }}>
        <div style={{ flex: '0 0 50%', maxWidth: '50%' }}>
          <div ref={headRef} aria-label="Where Ambition Meets Collaboration." style={{
            fontFamily: 'Clash Display, sans-serif', fontSize: '72px', lineHeight: '80px',
            fontWeight: '600', maxWidth: '600px', marginBottom: '24px',
            letterSpacing: '-0.02em', position: 'relative',
          }}>
            {words.map((word, wi) => (
              <span key={wi} aria-hidden="true" style={{
                display: 'inline-block',
                marginRight: wi < words.length - 1 ? '18px' : 0,
                whiteSpace: 'nowrap',
              }}>
                {word.split('').map((letter, li) => (
                  <span key={li}
                    className={`hl${word === 'Ambition' ? ' hl-ambition' : ''}`}
                    style={{
                      display: 'inline-block',
                      color: word === 'Ambition' ? 'var(--accent-primary)' : 'var(--text-primary)',
                    }}
                  >{letter}</span>
                ))}
              </span>
            ))}
          </div>

          <p ref={subRef} style={{
            fontFamily: 'Satoshi, sans-serif', fontSize: '18px', lineHeight: '28px',
            color: 'var(--text-secondary)', maxWidth: '520px', marginBottom: '32px', opacity: 0,
          }}>
            A professional platform engineered for teams who value growth,
            structured collaboration, and meaningful connections.
          </p>

          <div ref={btnsRef} style={{ display: 'flex', alignItems: 'center', gap: '16px', opacity: 0 }}>
            <MorphButton primary to="/auth">Get Started <ArrowRight size={15}/></MorphButton>
            <MorphButton to="/auth">Learn More</MorphButton>
          </div>
        </div>

        <div ref={cardRef} style={{ flex: '0 0 46%', maxWidth: '46%', opacity: 0 }}>
          <SpotlightCard/>
        </div>
      </div>
      </section>
    </div>
  )
}

/* ─────────────────────────────────────────────
   SPOTLIGHT CARD
───────────────────────────────────────────── */
function SpotlightCard() {
  const cardRef = useRef(null)
  const [mouse, setMouse] = useState({ x: .5, y: .5 })
  const [hov,   setHov]   = useState(false)
  const [tilt,  setTilt]  = useState({ x: 0, y: 0 })
  const [float, setFloat] = useState(0)

  useEffect(() => {
    if (NO_MOTION()) return
    let start = null, raf
    const fn = (ts) => {
      if (!start) start = ts
      setFloat(Math.sin(((ts - start) / 1000) * (Math.PI * 2 / 7)) * 8)
      raf = requestAnimationFrame(fn)
    }
    raf = requestAnimationFrame(fn)
    return () => cancelAnimationFrame(raf)
  }, [])

  const onMove = (e) => {
    const r = cardRef.current?.getBoundingClientRect(); if (!r) return
    const x = (e.clientX - r.left) / r.width, y = (e.clientY - r.top) / r.height
    setMouse({ x, y }); setTilt({ x: (y - .5) * -5, y: (x - .5) * 5 })
  }

  return (
    <motion.div ref={cardRef} onMouseMove={onMove}
      onMouseEnter={() => setHov(true)}
      onMouseLeave={() => { setHov(false); setTilt({ x: 0, y: 0 }) }}
      animate={{ rotateX: tilt.x, rotateY: tilt.y }}
      transition={{ duration: .22, ease: [.25,.1,.25,1] }}
      style={{ maxWidth: '560px', width: '100%', translateY: float, transformStyle: 'preserve-3d', willChange: 'transform' }}
    >
      <div style={{
        position: 'relative', backgroundColor: 'var(--bg-surface-elevated)',
        border: `1px solid rgba(${ACCENT_RGB},${hov ? .3 : .08})`,
        borderRadius: '18px', padding: '32px',
        boxShadow: hov
          ? `0 0 0 1px rgba(${ACCENT_RGB},.5), ${(mouse.x-.5)*20}px ${(mouse.y-.5)*20}px 40px rgba(${ACCENT_RGB},.12)`
          : '0 4px 24px rgba(0,0,0,.25)',
        overflow: 'hidden', transition: 'border-color 300ms ease, box-shadow 300ms ease',
      }}>
        <div aria-hidden="true" style={{
          position: 'absolute', inset: 0, borderRadius: '18px', pointerEvents: 'none',
          opacity: hov ? 1 : 0, transition: 'opacity 300ms ease',
          background: hov ? `radial-gradient(320px circle at ${mouse.x*100}% ${mouse.y*100}%, rgba(${ACCENT_RGB},.14) 0%, transparent 65%)` : 'none',
        }}/>
        <div style={{ display: 'flex', gap: '8px', marginBottom: '24px' }}>
          {[.14,.09,.07].map((op,i) => <div key={i} style={{ width:'10px',height:'10px',borderRadius:'50%',backgroundColor:`rgba(255,255,255,${op})` }}/>)}
        </div>
        <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr 1fr', gap: '12px', marginBottom: '24px' }}>
          {[{l:'Projects',v:'12'},{l:'Matched',v:'48'},{l:'Score',v:'94%'}].map(s => (
            <div key={s.l} style={{ backgroundColor:'var(--bg-surface)',border:'1px solid var(--border-subtle)',borderRadius:'10px',padding:'14px 10px',textAlign:'center' }}>
              <div style={{ fontFamily:'Clash Display, sans-serif',fontSize:'20px',fontWeight:'600',color:'var(--text-primary)',marginBottom:'4px' }}>{s.v}</div>
              <div style={{ fontFamily:'Satoshi, sans-serif',fontSize:'11px',color:'var(--text-secondary)' }}>{s.l}</div>
            </div>
          ))}
        </div>
        <div style={{ marginBottom: '20px' }}>
          <div style={{ display:'flex',justifyContent:'space-between',marginBottom:'8px' }}>
            <span style={{ fontFamily:'Satoshi, sans-serif',fontSize:'13px',color:'var(--text-secondary)' }}>Match Quality</span>
            <span style={{ fontFamily:'Satoshi, sans-serif',fontSize:'13px',fontWeight:'600',color:`rgba(${ACCENT_RGB},1)` }}>94%</span>
          </div>
          <div style={{ height:'4px',borderRadius:'999px',backgroundColor:'var(--bg-surface-elevated)',overflow:'hidden' }}>
            <motion.div initial={{width:'0%'}} animate={{width:'94%'}} transition={{duration:1.2,delay:.5,ease:[.16,1,.3,1]}}
              style={{ height:'100%',borderRadius:'999px',backgroundColor:`rgba(${ACCENT_RGB},1)` }}/>
          </div>
        </div>
        <div style={{ display:'flex',gap:'8px',flexWrap:'wrap' }}>
          {['Builder','Problem Solver','Collaborator'].map(r => (
            <span key={r} style={{ fontFamily:'Satoshi, sans-serif',fontSize:'11px',fontWeight:'500',color:'var(--text-secondary)',backgroundColor:'var(--bg-surface)',padding:'4px 10px',borderRadius:'999px',border:'1px solid var(--border-subtle)' }}>{r}</span>
          ))}
        </div>
      </div>
    </motion.div>
  )
}

/* ─────────────────────────────────────────────
   SECTION 3 — SOCIAL PROOF
───────────────────────────────────────────── */
const METRICS = [
  { value: 12400, suffix: '+', label: 'Active Members' },
  { value: 94,    suffix: '%', label: 'Match Satisfaction' },
  { value: 3200,  suffix: '+', label: 'Teams Formed' },
  { value: 4.8,   suffix: '',  label: 'Average Rating', dec: 1 },
]

function SocialProofStrip() {
  const outerRef = useRef(null)
  const sRef    = useRef(null)
  const lineRef = useRef(null)
  const mRefs   = useRef([])

  useEffect(() => {
    if (NO_MOTION()) return
    const g = gsap
    const ctx = g.context(() => {
      g.set(lineRef.current, { scaleX: 0, transformOrigin: 'left center' })
      mRefs.current.forEach(el => { if (el) g.set(el, { opacity: 0, y: 16 }) })

      const tl = g.timeline({
        scrollTrigger: {
          trigger: outerRef.current,
          start: 'top top', end: 'bottom bottom',
          scrub: 1.5,
        },
      })
      tl.to(lineRef.current, { scaleX: 1, duration: .5, ease: 'none' })

      METRICS.forEach((m, i) => {
        const el  = mRefs.current[i]; if (!el) return
        const vEl = el.querySelector('.mv')
        const pos = (i / METRICS.length) * .55
        tl.to(el, { opacity: 1, y: 0, duration: .3, ease: 'none' }, 0.2 + pos)

        /* Use a plain object as tween target — no 'this' needed */
        const counter = { val: 0 }
        tl.to(counter, {
          val: m.value, duration: .8, ease: 'none',
          onUpdate() {
            if (vEl) vEl.textContent = m.dec
              ? counter.val.toFixed(m.dec) + m.suffix
              : Math.round(counter.val).toLocaleString() + m.suffix
          },
        }, 0.25 + pos)
      })
      tl.to({}, { duration: 0.8 })  /* hold */
    })
    return () => ctx.revert()
  }, [])

  return (
    <div ref={outerRef} style={{ height: '200vh', position: 'relative' }}>
      <section ref={sRef} aria-label="Platform metrics" style={{
        position: 'sticky', top: 0, height: '100vh',
        display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center',
        backgroundColor: 'var(--bg-surface)', padding: '72px 64px',
        overflow: 'hidden',
        borderTop: '1px solid var(--border-subtle)', borderBottom: '1px solid var(--border-subtle)',
      }}>
      <div ref={lineRef} aria-hidden="true" style={{
        position: 'absolute', top: 0, left: 0, right: 0, height: '1px',
        background: `linear-gradient(to right, transparent, rgba(${ACCENT_RGB},.5), transparent)`,
      }}/>
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(4,1fr)', gap: '48px', maxWidth: '1100px', margin: '0 auto' }}>
        {METRICS.map((m, i) => (
          <div key={m.label} ref={el => mRefs.current[i] = el} style={{ textAlign: 'center', position: 'relative', opacity: 0 }}>
            <div aria-hidden="true" style={{
              position: 'absolute', top: '50%', left: '50%', transform: 'translate(-50%,-60%)',
              width: '120px', height: '60px',
              background: `radial-gradient(ellipse, rgba(${ACCENT_RGB},.15) 0%, transparent 70%)`,
              pointerEvents: 'none',
            }}/>
            <div className="mv" style={{
              fontFamily: 'Clash Display, sans-serif', fontSize: '52px', fontWeight: '600',
              lineHeight: 1, letterSpacing: '-0.03em', color: 'var(--text-primary)', marginBottom: '12px',
            }}>{m.dec ? '0.0' : '0'}{m.suffix}</div>
            <div style={{ fontFamily: 'Satoshi, sans-serif', fontSize: '14px', letterSpacing: '.08em', textTransform: 'uppercase', color: 'var(--text-secondary)' }}>{m.label}</div>
          </div>
        ))}
      </div>
      </section>
    </div>
  )
}

/* ─────────────────────────────────────────────
   SECTION 4 — FEATURES
   Cards: clip-mask reveal top→bottom, staggered,
   bidirectional. Icon blink fixed: CSS transition,
   not Framer animate (Framer animate on bg-color
   causes re-render blink on mouse-enter/leave).
───────────────────────────────────────────── */
const FEATURES = [
  { icon: Target,  title: 'Smart Team Matching',     desc: 'AI-driven role and interest scoring surfaces collaborators who complement your strengths — not just your availability.' },
  { icon: Layers,  title: 'Structured Communities',  desc: 'Join communities built around technical disciplines. Every space has clear purpose and signal-to-noise ratio.' },
  { icon: Compass, title: 'Project Recommendations', desc: 'Your motivation and skill profile drives recommendations that are ambitious but achievable.' },
]

function FeaturesSection() {
  const outerRef  = useRef(null)
  const sRef      = useRef(null)
  const hdrRef    = useRef(null)
  const cardRefs  = useRef([])

  useEffect(() => {
    if (NO_MOTION()) return
    const g = gsap
    const ctx = g.context(() => {
      g.set(hdrRef.current, { opacity: 0, y: 24 })
      cardRefs.current.forEach(card => {
        if (!card) return
        const borderEl = card.querySelector('.fb')
        const iconEl   = card.querySelector('.fi')
        g.set(card, { opacity: 0, y: 30 })
        if (borderEl) g.set(borderEl, { opacity: 0 })
        if (iconEl)   g.set(iconEl,   { scale: .82 })
      })

      const tl = g.timeline({
        scrollTrigger: {
          trigger: outerRef.current,
          start: 'top top', end: 'bottom bottom',
          scrub: 1.5,
        },
      })
      tl.to(hdrRef.current, { opacity: 1, y: 0, duration: .5, ease: 'none' })
      cardRefs.current.forEach((card, i) => {
        if (!card) return
        const borderEl = card.querySelector('.fb')
        const iconEl   = card.querySelector('.fi')
        tl.to(card, { opacity: 1, y: 0, duration: .45, ease: 'none' }, 0.35 + i * 0.14)
        if (borderEl) tl.to(borderEl, { opacity: 1, duration: .3, ease: 'none' }, 0.45 + i * 0.14)
        if (iconEl)   tl.to(iconEl,   { scale: 1,   duration: .3, ease: 'none' }, 0.45 + i * 0.14)
      })
      tl.to({}, { duration: 0.8 })  /* hold */
    })
    return () => ctx.revert()
  }, [])

  return (
    <div ref={outerRef} style={{ height: '280vh', position: 'relative' }}>
      <section id="features" ref={sRef} style={{
        position: 'sticky', top: 0, minHeight: '100vh',
        backgroundColor: 'var(--bg-primary)',
        padding: '120px 64px 120px',
      }}>
      <div ref={hdrRef} style={{ textAlign: 'center', marginBottom: '80px', opacity: 0 }}>
        <p style={{ fontFamily:'Satoshi, sans-serif',fontSize:'12px',letterSpacing:'.2em',textTransform:'uppercase',color:`rgba(${ACCENT_RGB},.5)`,marginBottom:'16px' }}>
          Core Capabilities
        </p>
        <h2 style={{ fontFamily:'Clash Display, sans-serif',fontSize:'40px',lineHeight:'48px',fontWeight:'500',color:'var(--text-primary)',marginBottom:'20px',letterSpacing:'-0.02em' }}>
          Engineered for Collaboration
        </h2>
        <p style={{ fontFamily:'Satoshi, sans-serif',fontSize:'18px',lineHeight:'28px',color:'var(--text-secondary)',maxWidth:'540px',margin:'0 auto' }}>
          Every feature exists to reduce noise and amplify meaningful work.
        </p>
      </div>

      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(3,1fr)', gap: '28px', maxWidth: '1160px', margin: '0 auto' }}>
        {FEATURES.map((f, i) => (
          <FeatureCard key={f.title} {...f} setRef={el => cardRefs.current[i] = el}/>
        ))}
      </div>
      </section>
    </div>
  )
}

const FeatureCard = React.memo(function FeatureCard({ icon: Icon, title, desc, setRef }) {
  const outerRef = useRef(null)
  const innerRef = useRef(null)

  /* All three transform axes as motion values — zero re-renders on mouse move */
  const rotX = useMotionValue(0)
  const rotY = useMotionValue(0)
  const liftY = useMotionValue(0)

  /* Spring-smooth the tilt so it doesn't feel mechanical */
  const sRotX = useSpring(rotX, { stiffness: 200, damping: 22 })
  const sRotY = useSpring(rotY, { stiffness: 200, damping: 22 })
  const sLiftY = useSpring(liftY, { stiffness: 260, damping: 28 })

  const combinedRef = useCallback((el) => {
    outerRef.current = el
    setRef(el)
  }, [setRef])

  const onMove = useCallback((e) => {
    if (NO_MOTION() || !innerRef.current) return
    const r = innerRef.current.getBoundingClientRect()
    rotX.set(((e.clientY - r.top)  / r.height - 0.5) * -6)
    rotY.set(((e.clientX - r.left) / r.width  - 0.5) *  6)
  }, [rotX, rotY])

  const onEnter = useCallback(() => {
    liftY.set(-6)
    const outer = outerRef.current; if (!outer) return
    const iconEl   = outer.querySelector('.fi div')
    const borderEl = outer.querySelector('.fb')
    const inner    = innerRef.current
    if (iconEl)   { iconEl.style.backgroundColor = `rgba(${ACCENT_RGB}, 0.12)`; iconEl.style.color = `rgba(${ACCENT_RGB}, 1)` }
    if (borderEl) borderEl.style.borderColor = `rgba(${ACCENT_RGB}, 0.42)`
    if (inner)    inner.style.boxShadow = `0 20px 48px rgba(0,0,0,0.4), 0 0 0 1px rgba(${ACCENT_RGB},0.1)`
  }, [liftY])

  const onLeave = useCallback(() => {
    rotX.set(0); rotY.set(0); liftY.set(0)
    const outer = outerRef.current; if (!outer) return
    const iconEl   = outer.querySelector('.fi div')
    const borderEl = outer.querySelector('.fb')
    const inner    = innerRef.current
    if (iconEl)   { iconEl.style.backgroundColor = 'var(--bg-surface-elevated)'; iconEl.style.color = 'var(--text-secondary)' }
    if (borderEl) borderEl.style.borderColor = `rgba(${ACCENT_RGB}, 0.2)`
    if (inner)    inner.style.boxShadow = '0 4px 24px rgba(0,0,0,0.22)'
  }, [rotX, rotY, liftY])

  return (
    <div ref={combinedRef} style={{ borderRadius: '14px' }}>
      <motion.div
        ref={innerRef}
        onMouseMove={onMove}
        onMouseEnter={onEnter}
        onMouseLeave={onLeave}
        style={{
          rotateX: sRotX,
          rotateY: sRotY,
          y: sLiftY,
          position: 'relative',
          backgroundColor: 'var(--bg-surface)',
          borderRadius: '14px',
          border: '1px solid var(--border-subtle)',
          padding: '44px 36px 40px',
          boxShadow: '0 4px 24px rgba(0,0,0,0.22)',
          transformStyle: 'preserve-3d',
          willChange: 'transform',
          transition: 'box-shadow 260ms ease',
          cursor: 'default',
        }}
      >
        {/* accent border — GSAP fades in on scroll reveal, CSS transitions color on hover */}
        <div className="fb" aria-hidden="true" style={{
          position: 'absolute', inset: 0, borderRadius: '14px', pointerEvents: 'none',
          border: `1px solid rgba(${ACCENT_RGB}, 0.2)`,
          transition: 'border-color 240ms ease',
        }}/>

        {/* icon — GSAP scales on scroll reveal, direct DOM on hover (no blink, no re-render) */}
        <div className="fi" style={{ marginBottom: '28px', display: 'inline-block' }}>
          <div style={{
            width: '52px', height: '52px', borderRadius: '12px',
            display: 'flex', alignItems: 'center', justifyContent: 'center',
            backgroundColor: 'var(--bg-surface-elevated)',
            color: 'var(--text-secondary)',
            transition: 'background-color 240ms ease, color 240ms ease',
          }}>
            <Icon size={24}/>
          </div>
        </div>

        <h3 style={{ fontFamily:'Satoshi, sans-serif', fontSize:'21px', lineHeight:'29px', fontWeight:'600', color:'var(--text-primary)', marginBottom:'12px' }}>{title}</h3>
        <p  style={{ fontFamily:'Satoshi, sans-serif', fontSize:'16px', lineHeight:'26px', color:'var(--text-secondary)' }}>{desc}</p>
      </motion.div>
    </div>
  )
})

/* ─────────────────────────────────────────────
   SECTION 6 — USE CASE PANELS
   Sticky viewport like HowItWorks.
   Separated pin per-panel.
   Icon hidden until GSAP reveals.
   No scrub on content (eliminates jitter).
───────────────────────────────────────────── */
const USE_CASES = [
  { id:'students', icon:GraduationCap, eyebrow:'For Students',  headline:'Build Your First Real Team.',
    body:'Stop working alone on side projects. MeshWork connects you with peers who complement your skills — so your next project actually ships.',
    gradient:`radial-gradient(ellipse at 30% 50%, rgba(${ACCENT_RGB},.08) 0%, transparent 60%)`, accent:'#10B981' },
  { id:'builders', icon:Wrench,        eyebrow:'For Builders',  headline:'Find the Gaps in Your Stack.',
    body:'You know what you build. MeshWork identifies what you need — a designer, a product thinker, a specialist — and matches you with them precisely.',
    gradient:`radial-gradient(ellipse at 70% 50%, rgba(99,102,241,.08) 0%, transparent 60%)`,   accent:'#818CF8' },
  { id:'founders', icon:TrendingUp,    eyebrow:'For Founders',  headline:'Assemble With Intention.',
    body:'Early team composition determines everything. MeshWork gives you a scoring framework to evaluate collaboration fit — not just résumés.',
    gradient:`radial-gradient(ellipse at 50% 70%, rgba(251,191,36,.07) 0%, transparent 60%)`,   accent:'#FBBF24' },
]

function UseCasePanels() {
  const panelRefs = useRef([])
  const HOLD_MULTIPLIER = 1.4
  const LAST_HOLD_MULTIPLIER = 1.8

  useEffect(() => {
    const shouldSkip = (typeof window !== 'undefined' && window.innerWidth < 768) || NO_MOTION()
    if (shouldSkip) return
    const g = gsap, ST = ScrollTrigger
    const ctx = g.context(() => {
      panelRefs.current.forEach((panel, idx) => {
        if (!panel) return
        const isLast   = idx === USE_CASES.length - 1
        const icon     = panel.querySelector('.uc-icon')
        const eyebrow  = panel.querySelector('.uc-eyebrow')
        const headline = panel.querySelector('.uc-headline')
        const body     = panel.querySelector('.uc-body')
        const bg       = panel.querySelector('.uc-bg')

        /* All content starts hidden */
        g.set([icon, eyebrow, headline, body], { opacity: 0, y: 22 })
        if (bg) g.set(bg, { opacity: 0 })

        const tl = g.timeline({ paused: true })
        if (bg)       tl.to(bg,       { opacity:1,   duration:.5,  ease:'power2.out' }, 0)
        if (icon)     tl.to(icon,     { opacity:1, y:0, duration:.48, ease:'power3.out' }, .06)
        if (eyebrow)  tl.to(eyebrow,  { opacity:1, y:0, duration:.48, ease:'power3.out' }, .14)
        if (headline) tl.to(headline, { opacity:1, y:0, duration:.62, ease:'power3.out' }, .24)
        if (body)     tl.to(body,     { opacity:1, y:0, duration:.52, ease:'power3.out' }, .44)

        ST.create({
          trigger:    panel,
          start:      'top top',
          end:        () => `+=${Math.round(window.innerHeight * (isLast ? LAST_HOLD_MULTIPLIER : HOLD_MULTIPLIER))}`,
          pin:        true,
          pinSpacing: true,
          anticipatePin: 1,
          onEnter:     () => tl.play(),
          onLeaveBack: () => tl.reverse(),
          /* When user scrolls back DOWN into panel after leaving above:
             continue from wherever the reverse left off — don't snap to start */
          onEnterBack: () => tl.play(),
        })
      })
    })
    return () => ctx.revert()
  }, [])

  return (
    <div aria-label="Use cases">
      {USE_CASES.map((uc, i) => {
        const Icon = uc.icon
        return (
          <div key={uc.id} ref={el => panelRefs.current[i] = el} style={{
            height: '100vh', display: 'flex', alignItems: 'center', justifyContent: 'center',
            backgroundColor: i % 2 === 0 ? 'var(--bg-primary)' : 'var(--bg-surface)',
            position: 'relative', overflow: 'hidden',
            padding: 'clamp(32px, 6vh, 80px) clamp(32px, 6vw, 64px)',
          }}>
            <div className="uc-bg" aria-hidden="true" style={{
              position: 'absolute', inset: 0, background: uc.gradient, pointerEvents: 'none', opacity: 0,
            }}/>

            <div style={{ maxWidth: '720px', width: '100%', position: 'relative', zIndex: 1 }}>
              <div className="uc-icon" style={{
                width: '60px', height: '60px', borderRadius: '14px',
                backgroundColor: 'var(--bg-surface-elevated)',
                border: '1px solid rgba(255,255,255,.08)',
                display: 'flex', alignItems: 'center', justifyContent: 'center',
                marginBottom: '28px', color: uc.accent, opacity: 0,
              }}>
                <Icon size={26}/>
              </div>

              <p className="uc-eyebrow" style={{
                fontFamily: 'Satoshi, sans-serif', fontSize: '12px', letterSpacing: '.2em',
                textTransform: 'uppercase', color: uc.accent, marginBottom: '20px', opacity: 0,
              }}>{uc.eyebrow}</p>

              <h2 className="uc-headline" style={{
                fontFamily: 'Clash Display, sans-serif',
                /* matched to other section headers — 40px, not 64+ */
                fontSize: 'clamp(36px, 4.5vw, 56px)',
                lineHeight: 1.12, fontWeight: '600', letterSpacing: '-0.02em',
                color: 'var(--text-primary)', marginBottom: '24px', opacity: 0,
              }}>{uc.headline}</h2>

              <p className="uc-body" style={{
                fontFamily: 'Satoshi, sans-serif', fontSize: '19px', lineHeight: '31px',
                color: 'var(--text-secondary)', maxWidth: '520px', opacity: 0,
              }}>{uc.body}</p>
            </div>

            <div aria-hidden="true" style={{
              position: 'absolute', bottom: '48px', right: '64px',
              fontFamily: 'Clash Display, sans-serif', fontSize: '96px', fontWeight: '600',
              lineHeight: 1, letterSpacing: '-0.05em', color: 'rgba(255,255,255,.03)', userSelect: 'none',
            }}>{String(i + 1).padStart(2, '0')}</div>
          </div>
        )
      })}
    </div>
  )
}

/* ─────────────────────────────────────────────
   SECTION 5 — HOW IT WORKS
   Slide direction fixed:
   - Forward scroll:  current exits LEFT, next enters from RIGHT
   - Backward scroll: current exits RIGHT, prev enters from LEFT
───────────────────────────────────────────── */
const HOW_STEPS = [
  { number: '01', title: 'Answer the Questionnaire', caption: 'Takes under 5 minutes. Tell us about your interests, work style, and what drives you.',                            mockupType: 'questionnaire' },
  { number: '02', title: 'Receive Your Profile',      caption: 'Our AI scores your responses into a structured collaboration profile. No buzzwords, no inflation.',               mockupType: 'profile'       },
  { number: '03', title: 'Connect and Build',         caption: 'Discover matched communities, recommended projects, and teammates who complement your strengths.',               mockupType: 'connect'       },
]

function HowItWorksSection() {
  const outerRef   = useRef(null)
  const barFillRef = useRef(null)
  const { scrollYProgress } = useScroll({ target: outerRef, offset: ['start start', 'end end'] })
  const lineH = useTransform(scrollYProgress, [0, 1], ['0%', '100%'])

  const [active, setActive] = useState(0)
  const [dir,    setDir]    = useState(1)

  /* Use a ref so the scroll listener closure always reads latest value
     without needing to be re-registered on every step change */
  const activeRef = useRef(0)

  useEffect(() => {
    return scrollYProgress.on('change', v => {
      const next = v < 0.33 ? 0 : v < 0.66 ? 1 : 2
      if (next !== activeRef.current) {
        const d = next > activeRef.current ? 1 : -1
        setDir(d)
        setActive(next)
        activeRef.current = next
        if (!NO_MOTION() && barFillRef.current) {
          gsap.fromTo(barFillRef.current,
            { boxShadow: `0 0 20px rgba(${ACCENT_RGB},0.9)` },
            { boxShadow: `0 0 8px rgba(${ACCENT_RGB},0.5)`, duration: 0.5, ease: 'power2.out' }
          )
        }
      }
    })
  }, [scrollYProgress])

  return (
    <div id="how-it-works" ref={outerRef} style={{ height: '300vh', position: 'relative' }}>
      <div style={{
        position: 'sticky', top: 0, height: '100vh',
        display: 'flex', flexDirection: 'column',
        backgroundColor: 'var(--bg-surface-elevated)', overflow: 'hidden',
      }}>
        <div style={{ textAlign: 'center', padding: '72px 72px 0', flexShrink: 0 }}>
          <p style={{ fontFamily:'Satoshi, sans-serif',fontSize:'12px',letterSpacing:'.2em',textTransform:'uppercase',color:`rgba(${ACCENT_RGB},.5)`,marginBottom:'8px' }}>The Process</p>
          <h2 style={{ fontFamily:'Clash Display, sans-serif',fontSize:'40px',lineHeight:'48px',fontWeight:'500',color:'var(--text-primary)',marginBottom:'6px',letterSpacing:'-0.02em' }}>How It Works</h2>
          <p style={{ fontFamily:'Satoshi, sans-serif',fontSize:'17px',lineHeight:'26px',color:'var(--text-secondary)' }}>Three steps from signup to your first meaningful collaboration.</p>
        </div>

        <div style={{ display: 'flex', flex: 1, padding: '32px 64px 48px', gap: '56px', overflow: 'hidden', minHeight: 0 }}>
          {/* step list */}
          <div style={{
            flex: '0 0 44%', position: 'relative',
            display: 'grid', gridTemplateColumns: '16px 1fr',
            gridTemplateRows: 'repeat(3, minmax(0,1fr))',
            columnGap: '24px', rowGap: '12px',
            height: '70%', alignSelf: 'center',
          }}>
            <div style={{ position: 'absolute', left: '7px', top: 0, bottom: 0, width: '2px', backgroundColor: 'var(--border-subtle)', borderRadius: '999px' }}>
              <motion.div ref={barFillRef} style={{
                position: 'absolute', top: 0, left: 0, right: 0, height: lineH,
                backgroundColor: `rgba(${ACCENT_RGB},1)`, borderRadius: '999px',
                boxShadow: `0 0 8px rgba(${ACCENT_RGB},.5)`,
              }}/>
            </div>

            {HOW_STEPS.map((step, i) => {
              const isA    = i === active
              const passed = i <= active
              return (
                <div key={step.number} style={{ display: 'contents' }}>
                  <motion.div
                    animate={{
                      backgroundColor: passed ? `rgba(${ACCENT_RGB},1)` : 'var(--bg-surface-elevated)',
                      borderColor:     passed ? `rgba(${ACCENT_RGB},1)` : 'rgba(255,255,255,.15)',
                      scale:           isA ? 1.35 : 1,
                    }}
                    transition={{ duration: .3, ease: [.25,.1,.25,1] }}
                    style={{ width:'10px',height:'10px',borderRadius:'50%',border:'2px solid',zIndex:2,alignSelf:'center',justifySelf:'center',
                      boxShadow: isA ? `0 0 12px rgba(${ACCENT_RGB},.6)` : 'none' }}
                  />
                  <motion.div
                    animate={{ opacity: isA ? 1 : .3, scale: isA ? 1 : .95 }}
                    transition={{ duration: .32, ease: [.25,.1,.25,1] }}
                    style={{ display:'flex',flexDirection:'column',justifyContent:'center',transformOrigin:'left center' }}
                  >
                    <motion.div key={`n${i}-${isA}`}
                      initial={isA ? { scale: 1.5, opacity: .5 } : { scale: 1 }}
                      animate={{ scale: 1, opacity: 1 }}
                      transition={{ duration: .38, ease: [.16,1,.3,1] }}
                      style={{
                        fontFamily:'Satoshi, sans-serif',fontSize:'11px',fontWeight:'600',
                        letterSpacing:'.12em',marginBottom:'5px',display:'inline-block',
                        color: isA ? `rgba(${ACCENT_RGB},1)` : 'var(--text-secondary)',
                        transformOrigin:'left center',transition:'color .28s ease',
                      }}
                    >{step.number}</motion.div>
                    <h3 style={{
                      fontFamily:'Satoshi, sans-serif',lineHeight:'27px',fontWeight:'600',
                      marginBottom:'6px',
                      fontSize: isA ? '21px' : '17px',
                      color: isA ? 'var(--text-primary)' : 'var(--text-secondary)',
                      transition:'font-size 280ms ease, color 280ms ease',
                    }}>{step.title}</h3>
                    <p style={{ fontFamily:'Satoshi, sans-serif',fontSize:'14px',lineHeight:'21px',color:'var(--text-secondary)',maxWidth:'320px' }}>{step.caption}</p>
                  </motion.div>
                </div>
              )
            })}
          </div>

          {/* slide panel */}
          <div style={{ flex: 1, display: 'flex', alignItems: 'center', justifyContent: 'center', position: 'relative', overflow: 'hidden' }}>
            <AnimatePresence mode="wait" custom={dir}>
              <motion.div key={active} custom={dir}
                initial={{ opacity: 0, x: dir * 60 }}
                animate={{ opacity: 1, x: 0 }}
                exit={{    opacity: 0, x: dir * -60 }}
                transition={{ duration: .32, ease: [.16,1,.3,1] }}
                style={{ width: '100%', maxWidth: '500px' }}
              >
                <StepMockup type={HOW_STEPS[active].mockupType}/>
              </motion.div>
            </AnimatePresence>
          </div>
        </div>
      </div>
    </div>
  )
}

function StepMockup({ type }) {
  const base = {
    backgroundColor:'var(--bg-surface)', border:'1px solid var(--border-subtle)',
    borderRadius:'14px', padding:'28px', boxShadow:'0 4px 24px rgba(0,0,0,.25)',
  }
  if (type === 'questionnaire') return (
    <div style={base}>
      <div style={{ fontFamily:'Clash Display, sans-serif',fontSize:'15px',fontWeight:'600',color:'var(--text-primary)',marginBottom:'6px' }}>What best describes your work style?</div>
      <div style={{ fontFamily:'Satoshi, sans-serif',fontSize:'12px',color:'var(--text-secondary)',marginBottom:'16px' }}>Question 3 of 8</div>
      <div style={{ height:'4px',borderRadius:'999px',backgroundColor:'var(--bg-surface-elevated)',overflow:'hidden',marginBottom:'20px' }}>
        <div style={{ width:'37.5%',height:'100%',backgroundColor:`rgba(${ACCENT_RGB},1)`,borderRadius:'999px' }}/>
      </div>
      {['I prefer to lead and delegate tasks','I like diving deep into one problem','I thrive connecting people and ideas','I focus on building and shipping fast'].map((opt,i)=>(
        <motion.div key={opt} initial={{opacity:0,x:-8}} animate={{opacity:1,x:0}} transition={{delay:i*.07,duration:.3}}
          style={{ padding:'11px 14px',borderRadius:'10px',marginBottom:'9px',
            border:`1px solid ${i===2?`rgba(${ACCENT_RGB},.5)`:'var(--border-subtle)'}`,
            backgroundColor:i===2?`rgba(${ACCENT_RGB},.1)`:'var(--bg-surface-elevated)',
            fontFamily:'Satoshi, sans-serif',fontSize:'14px',
            color:i===2?`rgba(${ACCENT_RGB},1)`:'var(--text-secondary)',
          }}>{opt}</motion.div>
      ))}
    </div>
  )
  if (type === 'profile') return (
    <div style={base}>
      <div style={{ fontFamily:'Clash Display, sans-serif',fontSize:'15px',fontWeight:'600',color:'var(--text-primary)',marginBottom:'20px' }}>Your Collaboration Profile</div>
      {[{l:'Collaborator',s:8.4},{l:'Problem Solver',s:7.9},{l:'Builder',s:7.2},{l:'Explorer',s:5.8}].map((r,i)=>(
        <div key={r.l} style={{ marginBottom:'14px' }}>
          <div style={{ display:'flex',justifyContent:'space-between',marginBottom:'5px' }}>
            <span style={{ fontFamily:'Satoshi, sans-serif',fontSize:'13px',color:'var(--text-primary)' }}>{r.l}</span>
            <span style={{ fontFamily:'Satoshi, sans-serif',fontSize:'13px',fontWeight:'600',color:'var(--text-primary)' }}>{r.s}</span>
          </div>
          <div style={{ height:'4px',borderRadius:'999px',backgroundColor:'var(--bg-surface-elevated)',overflow:'hidden' }}>
            <motion.div initial={{width:'0%'}} animate={{width:`${r.s*10}%`}} transition={{duration:.8,delay:i*.1,ease:'easeOut'}}
              style={{ height:'100%',borderRadius:'999px',backgroundColor:`rgba(${ACCENT_RGB},1)` }}/>
          </div>
        </div>
      ))}
      <div style={{ marginTop:'16px',padding:'11px 14px',borderRadius:'10px',backgroundColor:`rgba(${ACCENT_RGB},.08)`,border:`1px solid rgba(${ACCENT_RGB},.18)` }}>
        <span style={{ fontFamily:'Satoshi, sans-serif',fontSize:'13px',color:`rgba(${ACCENT_RGB},1)`,fontWeight:'500' }}>Motivation Score: 8.1 / 10</span>
      </div>
    </div>
  )
  return (
    <div style={base}>
      <div style={{ fontFamily:'Clash Display, sans-serif',fontSize:'15px',fontWeight:'600',color:'var(--text-primary)',marginBottom:'18px' }}>Your Matches</div>
      {[{n:'Aryan M.',r:['Architect','Leader'],s:'96%'},{n:'Selin K.',r:['Designer','Product Thinker'],s:'91%'},{n:'James R.',r:['Builder','Specialist'],s:'88%'}].map((m,i)=>(
        <motion.div key={m.n} initial={{opacity:0,x:12}} animate={{opacity:1,x:0}} transition={{delay:i*.1,duration:.35}}
          style={{ display:'flex',alignItems:'center',justifyContent:'space-between',padding:'11px 13px',borderRadius:'10px',marginBottom:'9px',backgroundColor:'var(--bg-surface-elevated)',border:'1px solid var(--border-subtle)' }}
        >
          <div style={{ display:'flex',alignItems:'center',gap:'11px' }}>
            <div style={{ width:'34px',height:'34px',borderRadius:'50%',backgroundColor:'var(--bg-surface)',border:'1px solid var(--border-subtle)',display:'flex',alignItems:'center',justifyContent:'center',flexShrink:0 }}>
              <span style={{ fontFamily:'Satoshi, sans-serif',fontSize:'10px',fontWeight:'700',color:'var(--text-secondary)' }}>{m.n.split(' ').map(x=>x[0]).join('')}</span>
            </div>
            <div>
              <div style={{ fontFamily:'Satoshi, sans-serif',fontSize:'14px',fontWeight:'600',color:'var(--text-primary)' }}>{m.n}</div>
              <div style={{ fontFamily:'Satoshi, sans-serif',fontSize:'11px',color:'var(--text-secondary)' }}>{m.r.join(' · ')}</div>
            </div>
          </div>
          <span style={{ fontFamily:'Satoshi, sans-serif',fontSize:'12px',fontWeight:'600',color:`rgba(${ACCENT_RGB},.8)` }}>{m.s}</span>
        </motion.div>
      ))}
    </div>
  )
}

/* ─────────────────────────────────────────────
   SECTION 7 — TESTIMONIALS
   Scroll-triggered bidirectional.
   Rich hover: spotlight, quote glow, scale.
───────────────────────────────────────────── */
const TESTIMONIALS = [
  { quote:'MeshWork matched me with a team that actually complemented my skills. The role scoring was eerily accurate.',             name:'Priya Sharma',    role:'Full-Stack Engineer', initials:'PS' },
  { quote:'Finally a platform that functions like an engineering tool. Community discovery is structured and noise-free.',           name:'Marcus Oyelaran', role:'Product Designer',    initials:'MO' },
  { quote:'The questionnaire took 4 minutes. The matches took seconds. My team has been together 8 months.',                        name:'Chen Wei',         role:'ML Engineer',         initials:'CW' },
]

function TestimonialsSection() {
  const outerRef = useRef(null)
  const sRef     = useRef(null)
  const hdrRef   = useRef(null)
  const cardRefs = useRef([])

  useEffect(() => {
    if (NO_MOTION()) return
    const g = gsap
    const ctx = g.context(() => {
      g.set(hdrRef.current, { opacity: 0, y: 20 })
      cardRefs.current.forEach(card => {
        if (!card) return
        g.set(card, { opacity: 0, y: 28, rotation: 2, filter: 'blur(6px)' })
      })

      const tl = g.timeline({
        scrollTrigger: {
          trigger: outerRef.current,
          start: 'top top', end: 'bottom bottom',
          scrub: 1.5,
        },
      })
      tl.to(hdrRef.current, { opacity: 1, y: 0, duration: .5, ease: 'none' })
      cardRefs.current.forEach((card, i) => {
        if (!card) return
        tl.to(card, { opacity: 1, y: 0, rotation: 0, filter: 'blur(0px)', duration: .5, ease: 'none' }, 0.3 + i * 0.15)
      })
      tl.to({}, { duration: 0.8 })  /* hold */
    })
    return () => ctx.revert()
  }, [])

  return (
    <div ref={outerRef} style={{ height: '240vh', position: 'relative' }}>
      <section ref={sRef} aria-labelledby="testimonials-heading" style={{
        position: 'sticky', top: 0, minHeight: '100vh',
        backgroundColor: 'var(--bg-primary)', padding: '144px 64px', overflow: 'hidden',
      }}>
      <div aria-hidden="true" style={{
        position:'absolute',top:'50%',left:'50%',transform:'translate(-50%,-50%)',
        width:'900px',height:'600px',
        background:`radial-gradient(ellipse, rgba(${ACCENT_RGB},.04) 0%, transparent 70%)`,
        pointerEvents:'none',
      }}/>

      <div ref={hdrRef} style={{ textAlign:'center', marginBottom:'80px', opacity:0 }}>
        <p style={{ fontFamily:'Satoshi, sans-serif',fontSize:'12px',letterSpacing:'.2em',textTransform:'uppercase',color:`rgba(${ACCENT_RGB},.5)`,marginBottom:'16px' }}>Outcomes</p>
        <h2 id="testimonials-heading" style={{ fontFamily:'Clash Display, sans-serif',fontSize:'40px',lineHeight:'48px',fontWeight:'500',letterSpacing:'-0.02em',color:'var(--text-primary)',marginBottom:'18px' }}>
          Built on Real Outcomes
        </h2>
        <p style={{ fontFamily:'Satoshi, sans-serif',fontSize:'18px',lineHeight:'28px',color:'var(--text-secondary)',maxWidth:'480px',margin:'0 auto' }}>
          What the people who use MeshWork actually say.
        </p>
      </div>

      <div style={{ display:'grid',gridTemplateColumns:'repeat(3,1fr)',gap:'24px',maxWidth:'1160px',margin:'0 auto',position:'relative',zIndex:1 }}>
        {TESTIMONIALS.map((t, i) => (
          <div key={t.name} ref={el => cardRefs.current[i] = el} style={{ opacity:0 }}>
            <TestimonialCard {...t}/>
          </div>
        ))}
      </div>
      </section>
    </div>
  )
}

function TestimonialCard({ quote, name, role, initials }) {
  const cardRef = useRef(null)
  const [hov,   setHov]   = useState(false)
  const [mouse, setMouse] = useState({ x:.5, y:.5 })

  const onMove = (e) => {
    const r = cardRef.current?.getBoundingClientRect(); if (!r) return
    setMouse({ x:(e.clientX-r.left)/r.width, y:(e.clientY-r.top)/r.height })
  }

  return (
    <motion.div ref={cardRef} onMouseMove={onMove}
      onMouseEnter={() => setHov(true)} onMouseLeave={() => setHov(false)}
      animate={{ y: hov ? -6 : 0, scale: hov ? 1.015 : 1 }}
      transition={{ duration: .28, ease: [.25,.1,.25,1] }}
      style={{
        position:'relative', overflow:'hidden',
        backgroundColor: hov ? 'var(--bg-surface-elevated)' : 'var(--bg-surface)',
        borderRadius:'18px',
        border:`1px solid ${hov ? `rgba(${ACCENT_RGB},0.28)` : 'var(--border-subtle)'}`,
        padding:'36px 32px', display:'flex', flexDirection:'column', gap:'24px',
        boxShadow: hov
          ? `0 20px 44px rgba(0,0,0,0.4), 0 0 0 1px rgba(${ACCENT_RGB},0.1)`
          : '0 4px 24px rgba(0,0,0,0.2)',
        /* No CSS transition here — Framer owns ALL transitions on this element */
        cursor:'default', height:'100%',
      }}
    >
      {hov && (
        <div aria-hidden="true" style={{
          position:'absolute', inset:0, pointerEvents:'none', borderRadius:'18px',
          background:`radial-gradient(260px circle at ${mouse.x*100}% ${mouse.y*100}%, rgba(${ACCENT_RGB},.1) 0%, transparent 65%)`,
        }}/>
      )}
      <div aria-hidden="true" style={{
        position:'absolute', top:'14px', right:'18px',
        fontFamily:'Clash Display, sans-serif', fontSize:'68px', lineHeight:1, fontWeight:'600',
        color:`rgba(${ACCENT_RGB},${hov ? .16 : .05})`,
        transition:'color 260ms ease', userSelect:'none', pointerEvents:'none',
      }}>&quot;</div>

      <p style={{
        fontFamily:'Satoshi, sans-serif', fontSize:'16px', lineHeight:'27px',
        color: hov ? 'var(--text-primary)' : 'var(--text-secondary)',
        transition:'color 260ms ease', position:'relative', zIndex:1,
      }}>&quot;{quote}&quot;</p>

      <div style={{ display:'flex', alignItems:'center', gap:'12px' }}>
        <div style={{
          width:'42px', height:'42px', borderRadius:'50%',
          backgroundColor: hov ? `rgba(${ACCENT_RGB},.1)` : 'var(--bg-surface-elevated)',
          border:`1px solid ${hov ? `rgba(${ACCENT_RGB},.3)` : 'var(--border-subtle)'}`,
          display:'flex', alignItems:'center', justifyContent:'center', flexShrink:0,
          transition:'background-color 240ms ease, border-color 240ms ease',
        }}>
          <span style={{ fontFamily:'Satoshi, sans-serif',fontSize:'12px',fontWeight:'700',color:'var(--text-secondary)',letterSpacing:'.04em' }}>{initials}</span>
        </div>
        <div>
          <div style={{ fontFamily:'Satoshi, sans-serif',fontSize:'15px',fontWeight:'600',color:'var(--text-primary)',lineHeight:'22px' }}>{name}</div>
          <div style={{ fontFamily:'Satoshi, sans-serif',fontSize:'13px',lineHeight:'20px',color:'var(--text-secondary)' }}>{role}</div>
        </div>
      </div>
    </motion.div>
  )
}

/* ─────────────────────────────────────────────
   SECTION 8 — FINAL CTA
   Scroll-triggered bidirectional.
   Increased letter-spacing on headline.
───────────────────────────────────────────── */
function FinalCTASection() {
  const outerRef   = useRef(null)
  const sRef       = useRef(null)
  const hdrRef     = useRef(null)
  const lineRef    = useRef(null)
  const btnRef     = useRef(null)
  const glowRef    = useRef(null)
  const subtextRef = useRef(null)

  useEffect(() => {
    if (NO_MOTION()) return
    const g = gsap
    const ctx = g.context(() => {
      g.set(hdrRef.current,     { scale:.85, opacity:0 })
      g.set(lineRef.current,    { scaleX:0, transformOrigin:'left center' })
      g.set(subtextRef.current, { opacity:0, y:14 })
      g.set(btnRef.current,     { opacity:0, y:18 })
      g.set(glowRef.current,    { opacity:.12 })

      g.timeline({
        scrollTrigger: {
          trigger: outerRef.current,
          start: 'top top', end: 'bottom bottom',
          scrub: 1.5,
        },
      })
      .to(hdrRef.current,     { scale:1, opacity:1, duration:.5,  ease:'none' })
      .to(lineRef.current,    { scaleX:1,           duration:.4,  ease:'none' }, '-=.3')
      .to(glowRef.current,    { opacity:.65,         duration:.45, ease:'none' }, '-=.4')
      .to(subtextRef.current, { opacity:1, y:0,      duration:.4,  ease:'none' }, '-=.35')
      .to(btnRef.current,     { opacity:1, y:0,      duration:.35, ease:'none' }, '-=.25')
      .to({}, { duration: 0.8 })  /* hold */
    })
    return () => ctx.revert()
  }, [])

  return (
    <div ref={outerRef} style={{ height: '200vh', position: 'relative' }}>
      <section ref={sRef} aria-labelledby="cta-heading" style={{
        position: 'sticky', top: 0, minHeight: '100vh',
        backgroundColor:'var(--bg-primary)', padding:'160px 64px',
        textAlign:'center', overflow:'hidden',
      }}>
      <div ref={glowRef} aria-hidden="true" style={{
        position:'absolute', top:'50%', left:'50%', transform:'translate(-50%,-50%)',
        width:'800px', height:'500px',
        background:`radial-gradient(ellipse, rgba(${ACCENT_RGB},.12) 0%, transparent 65%)`,
        pointerEvents:'none', opacity:.12,
      }}/>

      <div style={{ position:'relative', zIndex:1 }}>
        <div ref={hdrRef} style={{ opacity:0, marginBottom:'40px', display:'inline-block' }}>
          <h2 id="cta-heading" style={{
            fontFamily: 'Clash Display, sans-serif',
            fontSize: 'clamp(48px, 7vw, 92px)',
            lineHeight: 1.06, fontWeight: '600',
            /* +1-2% letter spacing vs default — less congested at large sizes */
            letterSpacing: '0.02em',
            color: 'var(--text-primary)', marginBottom: '14px',
          }}>
            Build Something<br/>
            <span style={{ color:'var(--accent-primary)' }}>That Matters.</span>
          </h2>
          <div ref={lineRef} aria-hidden="true" style={{
            height:'2px',
            background:`linear-gradient(to right, transparent, var(--accent-primary), transparent)`,
            borderRadius:'999px', transform:'scaleX(0)', transformOrigin:'left center',
          }}/>
        </div>

        <p ref={subtextRef} style={{
          fontFamily:'Satoshi, sans-serif', fontSize:'20px', lineHeight:'32px',
          color:'var(--text-secondary)', maxWidth:'500px', margin:'0 auto 48px', opacity:0,
        }}>
          Join thousands of builders, students, and founders who collaborate with intention.
        </p>

        <div ref={btnRef} style={{ opacity:0 }}>
          <MorphButton to="/auth" primary large>
            Get Started Free <ArrowRight size={18}/>
          </MorphButton>
        </div>
      </div>
      </section>
    </div>
  )
}

/* ─────────────────────────────────────────────
   FOOTER
───────────────────────────────────────────── */
function Footer() {
  return (
    <footer style={{ backgroundColor:'var(--bg-surface)', borderTop:'1px solid var(--border-subtle)', padding:'96px 64px' }}>
      <div style={{ display:'grid', gridTemplateColumns:'1.5fr 1fr 1fr', gap:'64px', maxWidth:'1100px', margin:'0 auto 64px' }}>
        <div>
          <div style={{ fontFamily:'Clash Display, sans-serif',fontSize:'20px',fontWeight:'600',color:'var(--text-primary)',letterSpacing:'-0.02em',marginBottom:'16px' }}>MeshWork</div>
          <p style={{ fontFamily:'Satoshi, sans-serif',fontSize:'14px',lineHeight:'22px',color:'var(--text-secondary)',maxWidth:'280px' }}>
            A professional collaboration platform engineered for teams who build with intention.
          </p>
        </div>
        {[
          { title:'Product', links:[{l:'Features',href:'#features'},{l:'How It Works',href:'#how-it-works'},{l:'Admin Login',href:'/college/admin-login'},{l:'Roadmap',href:'#'}] },
          { title:'Company', links:[{l:'About',href:'#about'},{l:'Register College',href:'/college/register'},{l:'Privacy Policy',href:'#'},{l:'Terms of Service',href:'#'}] },
        ].map(col => (
          <div key={col.title}>
            <div style={{ fontFamily:'Satoshi, sans-serif',fontSize:'15px',fontWeight:'600',color:'var(--text-primary)',marginBottom:'20px' }}>{col.title}</div>
            <ul style={{ listStyle:'none',padding:0,margin:0,display:'flex',flexDirection:'column',gap:'12px' }}>
              {col.links.map(l => (
                <li key={l.l}>
                  {l.href.startsWith('/') ? (
                    <Link to={l.href}
                      style={{ fontFamily:'Satoshi, sans-serif',fontSize:'14px',color:'var(--text-secondary)',textDecoration:'none',transition:'color 160ms ease' }}
                      onMouseEnter={e => e.currentTarget.style.color=`rgba(${ACCENT_RGB},1)`}
                      onMouseLeave={e => e.currentTarget.style.color='var(--text-secondary)'}
                    >{l.l}</Link>
                  ) : (
                    <a href={l.href}
                      style={{ fontFamily:'Satoshi, sans-serif',fontSize:'14px',color:'var(--text-secondary)',textDecoration:'none',transition:'color 160ms ease' }}
                      onMouseEnter={e => e.currentTarget.style.color=`rgba(${ACCENT_RGB},1)`}
                      onMouseLeave={e => e.currentTarget.style.color='var(--text-secondary)'}
                    >{l.l}</a>
                  )}
                </li>
              ))}
            </ul>
          </div>
        ))}
      </div>
      <div style={{ borderTop:'1px solid var(--border-subtle)',paddingTop:'32px',textAlign:'center',maxWidth:'1100px',margin:'0 auto' }}>
        <p style={{ fontFamily:'Satoshi, sans-serif',fontSize:'14px',color:'var(--text-secondary)' }}>
          © 2026 MeshWork. Engineered, not designed.
        </p>
      </div>
    </footer>
  )
}

/* ─────────────────────────────────────────────
   ROOT
───────────────────────────────────────────── */
export default function Landing() {
  const [navVisible, setNavVisible] = useState(false)
  const handleBrandLocked = useCallback((v = true) => setNavVisible(v), [])

  return (
    <div style={{ backgroundColor:'var(--bg-primary)', color:'var(--text-primary)' }}>
      <a href="#main-content" style={{
        position:'absolute', top:'-100px', left:'16px',
        backgroundColor:`rgba(${ACCENT_RGB},1)`, color:'#0E1113',
        padding:'8px 16px', borderRadius:'8px',
        fontFamily:'Satoshi, sans-serif', fontSize:'14px', fontWeight:'600',
        zIndex:9999, textDecoration:'none', transition:'top .2s',
      }}
        onFocus={e  => e.currentTarget.style.top = '16px'}
        onBlur={e   => e.currentTarget.style.top = '-100px'}
      >Skip to content</a>

      <Navbar visible={navVisible}/>

      <main id="main-content">
        <BrandIntroSection onBrandLocked={handleBrandLocked}/>
        <HeroSection/>
        <SocialProofStrip/>
        <FeaturesSection/>
        <UseCasePanels/>
        <HowItWorksSection/>
        <TestimonialsSection/>
        <FinalCTASection/>
      </main>

      <Footer/>
    </div>
  )
}