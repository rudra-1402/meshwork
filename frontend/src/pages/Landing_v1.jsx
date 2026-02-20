/**
 * MESHWORK — Landing Page v3
 *
 * Fixed in this version:
 * - Brand scramble: Strict Mode safe, uses ref-based lock
 * - Navbar: appears correctly after brand locks
 * - Hero headline: word-by-word animation
 * - Hero card: cursor-direction spotlight glow
 * - Feature cards: border reveal on hover, no underline
 * - Button morph: smooth, no jitter (explicit transitions)
 * - How It Works: Apple-style pinned scroll, 3 steps × 200vh
 */

import {
  useState,
  useEffect,
  useRef,
  useCallback,
} from 'react'
import {
  motion,
  AnimatePresence,
  useMotionValue,
  useSpring,
  useInView,
  useScroll,
  useTransform,
} from 'framer-motion'
import { Link } from 'react-router-dom'
import {
  Zap,
  Workflow,
  Info,
  ArrowRight,
  Target,
  Layers,
  Compass,
  CheckCircle,
  Users,
  BarChart3,
} from 'lucide-react'

/* ============================================================
   CONSTANTS
   ============================================================ */
const BRAND_NAME = 'MeshWork'
const GLITCH_CHARS = 'ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789@#$%&'
const CANVAS_ACCENT_RGB = '16, 185, 129'

/* ============================================================
   ANIMATION VARIANTS
   ============================================================ */
const fadeUp = {
  hidden: { opacity: 0, y: 20, filter: 'blur(4px)' },
  visible: {
    opacity: 1, y: 0, filter: 'blur(0px)',
    transition: { duration: 0.65, ease: [0.16, 1, 0.3, 1] },
  },
}

const stagger = (delay = 0.08) => ({
  hidden: {},
  visible: { transition: { staggerChildren: delay } },
})

/* ============================================================
   HOOK — Scroll reveal
   ============================================================ */
function useScrollReveal(threshold = 0.15) {
  const ref = useRef(null)
  const isInView = useInView(ref, { once: true, amount: threshold })
  return { ref, isInView }
}

/* ============================================================
   HOOK — Glitch scramble (Strict Mode safe)

   React 18 Strict Mode double-fires effects in development.
   Fix: use a module-level started flag so the animation
   only ever runs once regardless of how many times the
   effect fires.
   ============================================================ */
let _scrambleStarted = false

function useGlitchScramble(targetText, shouldStart) {
  const chars = targetText.split('')

  const [displayChars, setDisplayChars] = useState(() =>
    chars.map(() => GLITCH_CHARS[Math.floor(Math.random() * GLITCH_CHARS.length)])
  )
  const [isDone, setIsDone] = useState(false)
  const frameRef = useRef(null)
  const doneRef = useRef(false)

  useEffect(() => {
    if (!shouldStart) return
    // Strict Mode guard — only run once
    if (_scrambleStarted) return
    _scrambleStarted = true

    const settled = new Array(chars.length).fill(false)
    // Slower: longer settle window, bigger stagger, more randomness
    const settleTimings = chars.map((_, i) =>
      900 + i * 140 + Math.random() * 220
    )
    const startTime = performance.now()
    // Throttle to ~30fps so scramble reads as deliberate, not frantic
    let lastFrame = 0

    const tick = (now) => {
      if (doneRef.current) return
      // Only update every ~33ms (~30fps) for a calmer scramble feel
      if (now - lastFrame < 33) {
        frameRef.current = requestAnimationFrame(tick)
        return
      }
      lastFrame = now
      const elapsed = now - startTime
      const next = chars.map((char, i) => {
        if (elapsed >= settleTimings[i]) {
          settled[i] = true
          return char
        }
        return GLITCH_CHARS[Math.floor(Math.random() * GLITCH_CHARS.length)]
      })
      setDisplayChars(next)
      if (settled.every(Boolean)) {
        doneRef.current = true
        setIsDone(true)
        return
      }
      frameRef.current = requestAnimationFrame(tick)
    }

    frameRef.current = requestAnimationFrame(tick)
    return () => {
      if (frameRef.current) cancelAnimationFrame(frameRef.current)
    }
  }, [shouldStart])

  return { displayChars, isDone }
}

/* ============================================================
   GEOMETRIC PATTERN CANVAS — for BrandIntro section
   Draws animated geometric grid of triangles, hexagons, and
   connecting lines — MeshWork's "engineered" aesthetic
   ============================================================ */
function GeometricCanvas() {
  const canvasRef = useRef(null)
  const animRef = useRef(null)
  const mountedRef = useRef(false)

  useEffect(() => {
    if (mountedRef.current) return
    mountedRef.current = true
    if (window.matchMedia('(prefers-reduced-motion: reduce)').matches) return
    const canvas = canvasRef.current
    if (!canvas) return
    const ctx = canvas.getContext('2d')

    const resize = () => {
      canvas.width = canvas.offsetWidth
      canvas.height = canvas.offsetHeight
    }
    resize()
    window.addEventListener('resize', resize)

    // Grid of hexagonal-ish anchor points
    const COLS = 16
    const ROWS = 11
    let points = []
    const buildPoints = () => {
      points = []
      const cw = canvas.width / (COLS - 1)
      const ch = canvas.height / (ROWS - 1)
      for (let r = 0; r < ROWS; r++) {
        for (let c = 0; c < COLS; c++) {
          const ox = r % 2 === 0 ? 0 : cw * 0.5
          points.push({
            bx: c * cw + ox,
            by: r * ch,
            x: c * cw + ox,
            y: r * ch,
            vx: (Math.random() - 0.5) * 0.18,
            vy: (Math.random() - 0.5) * 0.18,
            phase: Math.random() * Math.PI * 2,
            speed: 0.003 + Math.random() * 0.005,
          })
        }
      }
    }
    buildPoints()

    // Nearest-neighbor triangle connections
    const getTriangles = () => {
      const tris = []
      for (let i = 0; i < points.length; i++) {
        for (let j = i + 1; j < points.length; j++) {
          const dx = points[i].x - points[j].x
          const dy = points[i].y - points[j].y
          if (Math.sqrt(dx * dx + dy * dy) < canvas.width / (COLS - 1) * 1.75) {
            tris.push([i, j])
          }
        }
      }
      return tris
    }

    let t = 0
    const draw = () => {
      ctx.clearRect(0, 0, canvas.width, canvas.height)
      t += 0.008

      // Animate points with sinusoidal drift
      points.forEach(p => {
        p.x = p.bx + Math.sin(t * p.speed * 60 + p.phase) * 14
        p.y = p.by + Math.cos(t * p.speed * 45 + p.phase * 0.7) * 10
      })

      const edges = getTriangles()

      // Draw connecting lines
      edges.forEach(([a, b]) => {
        const pa = points[a], pb = points[b]
        const dx = pa.x - pb.x, dy = pa.y - pb.y
        const d = Math.sqrt(dx * dx + dy * dy)
        const maxD = canvas.width / (COLS - 1) * 1.6
        const alpha = (1 - d / maxD) * 0.16
        ctx.beginPath()
        ctx.strokeStyle = `rgba(${CANVAS_ACCENT_RGB}, ${alpha})`
        ctx.lineWidth = 0.7
        ctx.moveTo(pa.x, pa.y)
        ctx.lineTo(pb.x, pb.y)
        ctx.stroke()
      })

      // Draw small diamond nodes at intersections
      points.forEach((p, i) => {
        const pulse = 0.5 + 0.5 * Math.sin(t * 40 * p.speed + p.phase)
        const alpha = 0.12 + pulse * 0.14
        const size = 3.4 + pulse * 2.6
        ctx.save()
        ctx.translate(p.x, p.y)
        ctx.rotate(Math.PI / 4)
        ctx.fillStyle = `rgba(${CANVAS_ACCENT_RGB}, ${alpha})`
        ctx.fillRect(-size / 2, -size / 2, size, size)
        ctx.restore()
      })

      animRef.current = requestAnimationFrame(draw)
    }
    draw()

    return () => {
      window.removeEventListener('resize', resize)
      if (animRef.current) cancelAnimationFrame(animRef.current)
    }
  }, [])

  return (
    <canvas ref={canvasRef} aria-hidden="true" style={{
      position: 'absolute', inset: 0,
      width: '100%', height: '100%',
      pointerEvents: 'none', opacity: 1,
    }} />
  )
}

/* ============================================================
   PARTICLE CANVAS — kept for HeroSection background
   ============================================================ */
function ParticleCanvas() {
  const canvasRef = useRef(null)
  const animRef = useRef(null)
  const mountedRef = useRef(false)

  useEffect(() => {
    if (mountedRef.current) return
    mountedRef.current = true

    if (window.matchMedia('(prefers-reduced-motion: reduce)').matches) return
    const canvas = canvasRef.current
    if (!canvas) return
    const ctx = canvas.getContext('2d')

    const resize = () => {
      canvas.width = canvas.offsetWidth
      canvas.height = canvas.offsetHeight
    }
    resize()
    window.addEventListener('resize', resize)

    const particles = Array.from({ length: 48 }, () => ({
      x: Math.random() * canvas.width,
      y: Math.random() * canvas.height,
      vx: (Math.random() - 0.5) * 0.25,
      vy: (Math.random() - 0.5) * 0.25,
      r: Math.random() * 1.3 + 0.4,
      base: Math.random() * 0.3 + 0.07,
      ps: Math.random() * 0.016 + 0.004,
      po: Math.random() * Math.PI * 2,
    }))

    let t = 0
    const draw = () => {
      ctx.clearRect(0, 0, canvas.width, canvas.height)
      t += 0.016

      for (let i = 0; i < particles.length; i++) {
        for (let j = i + 1; j < particles.length; j++) {
          const dx = particles[i].x - particles[j].x
          const dy = particles[i].y - particles[j].y
          const d = Math.sqrt(dx * dx + dy * dy)
          if (d < 120) {
            ctx.beginPath()
            ctx.strokeStyle = `rgba(${CANVAS_ACCENT_RGB},${(1 - d / 120) * 0.09})`
            ctx.lineWidth = 0.5
            ctx.moveTo(particles[i].x, particles[i].y)
            ctx.lineTo(particles[j].x, particles[j].y)
            ctx.stroke()
          }
        }
      }

      particles.forEach(p => {
        const op = p.base * (0.7 + 0.3 * Math.sin(t * p.ps * 60 + p.po))
        ctx.beginPath()
        ctx.arc(p.x, p.y, p.r, 0, Math.PI * 2)
        ctx.fillStyle = `rgba(${CANVAS_ACCENT_RGB},${op})`
        ctx.fill()
        p.x += p.vx; p.y += p.vy
        if (p.x < 0) p.x = canvas.width
        if (p.x > canvas.width) p.x = 0
        if (p.y < 0) p.y = canvas.height
        if (p.y > canvas.height) p.y = 0
      })

      animRef.current = requestAnimationFrame(draw)
    }
    draw()

    return () => {
      window.removeEventListener('resize', resize)
      if (animRef.current) cancelAnimationFrame(animRef.current)
    }
  }, [])

  return (
    <canvas ref={canvasRef} aria-hidden="true" style={{
      position: 'absolute', inset: 0,
      width: '100%', height: '100%',
      pointerEvents: 'none', opacity: 0.6,
    }} />
  )
}

/* ============================================================
   BRAND INTRO SECTION
   ============================================================ */
function BrandIntroSection({ onBrandLocked }) {
  const sectionRef = useRef(null)
  const [entryStarted, setEntryStarted] = useState(false)
  const [phase, setPhase] = useState('entry')
  const phaseRef = useRef('entry')

  const { displayChars, isDone: scrambleDone } = useGlitchScramble(BRAND_NAME, entryStarted)

  const rawX = useMotionValue(0)
  const rawY = useMotionValue(0)
  // Softer spring = more cinematic, floaty follow
  const springX = useSpring(rawX, { stiffness: 45, damping: 16 })
  const springY = useSpring(rawY, { stiffness: 45, damping: 16 })

  const { scrollY } = useScroll()

  const setPhaseSync = (p) => {
    phaseRef.current = p
    setPhase(p)
  }

  // Start scramble on mount — single timeout
  useEffect(() => {
    const t = setTimeout(() => setEntryStarted(true), 300)
    return () => clearTimeout(t)
  }, [])

  // Transition to interactive after scramble
  useEffect(() => {
    if (scrambleDone && phaseRef.current === 'entry') {
      setPhaseSync('interactive')
    }
  }, [scrambleDone])

  // Cursor tracking
  const handleMouseMove = useCallback((e) => {
    if (phaseRef.current !== 'interactive') return
    const rect = sectionRef.current?.getBoundingClientRect()
    if (!rect) return
    const clamp = (v, a, b) => Math.min(Math.max(v, a), b)
    rawX.set(clamp((e.clientX - (rect.left + rect.width / 2)) * 0.08, -36, 36))
    rawY.set(clamp((e.clientY - (rect.top + rect.height / 2)) * 0.08, -36, 36))
  }, [rawX, rawY])

  useEffect(() => {
    if (phase !== 'interactive') { rawX.set(0); rawY.set(0) }
  }, [phase, rawX, rawY])

  // Scroll → transition brand to navbar
  useEffect(() => {
    return scrollY.on('change', (y) => {
      const h = sectionRef.current?.offsetHeight ?? window.innerHeight
      if (y > h * 0.55) {
        onBrandLocked?.(true)
        if (phaseRef.current === 'interactive') {
          setPhaseSync('transitioning')
          setTimeout(() => {
            setPhaseSync('locked')
          }, 500)
        }
      }
      if (y < h * 0.2) {
        onBrandLocked?.(false)
        if (phaseRef.current === 'locked') {
          setPhaseSync('interactive')
        }
      }
    })
  }, [scrollY, onBrandLocked])

  return (
    <section
      ref={sectionRef}
      onMouseMove={handleMouseMove}
      style={{
        height: '100vh', display: 'flex',
        alignItems: 'center', justifyContent: 'center',
        position: 'relative', overflow: 'hidden',
        backgroundColor: 'var(--bg-primary)',
      }}
    >
      {/* Geometric mesh pattern — primary brand background */}
      <GeometricCanvas />

      {/* Deep radial vignette to keep brand readable against geometry */}
      <div aria-hidden="true" style={{
        position: 'absolute', inset: 0,
        background: 'radial-gradient(ellipse 60% 55% at 50% 50%, transparent 58%, color-mix(in srgb, var(--bg-primary) 45%, transparent) 72%, var(--bg-primary) 100%)',
        pointerEvents: 'none', zIndex: 1,
      }} />

      {/* Radial glow behind brand */}
      <div aria-hidden="true" style={{
        position: 'absolute', top: '50%', left: '50%',
        transform: 'translate(-50%,-50%)',
        width: '720px', height: '480px',
        borderRadius: '50%',
        filter: 'blur(30px)',
        background: `radial-gradient(ellipse, rgba(${CANVAS_ACCENT_RGB},0.1) 0%, transparent 68%)`,
        pointerEvents: 'none', zIndex: 1,
      }} />

      <AnimatePresence>
        {phase !== 'locked' && (
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: phase === 'transitioning' ? 0 : 1 }}
            exit={{ opacity: 0 }}
            transition={{ duration: 0.5, ease: [0.25, 0.1, 0.25, 1.0] }}
            style={{
              x: phase === 'interactive' ? springX : 0,
              y: phase === 'interactive' ? springY : 0,
              position: 'relative', zIndex: 10, textAlign: 'center',
            }}
          >
            {/* Brand name — enlarged, more cinematic */}
            <div style={{
              fontFamily: 'Clash Display, sans-serif',
              fontSize: 'clamp(68px, 12vw, 128px)',
              fontWeight: '600', letterSpacing: '-0.035em',
              userSelect: 'none', display: 'flex', justifyContent: 'center',
              lineHeight: 1,
            }}>
              {displayChars.map((char, i) => (
                <motion.span
                  key={i}
                  animate={{
                    color: char === BRAND_NAME[i]
                      ? 'var(--text-primary)'
                      : `rgba(${CANVAS_ACCENT_RGB}, 0.55)`,
                    textShadow: char === BRAND_NAME[i]
                      ? `0 0 40px rgba(${CANVAS_ACCENT_RGB}, 0.08)`
                      : 'none',
                  }}
                  transition={{ duration: 0.12, ease: 'easeOut' }}
                  style={{ display: 'inline-block', minWidth: '0.52em' }}
                >
                  {char}
                </motion.span>
              ))}
            </div>

            {/* Tagline — positioned with more breathing room below brand */}
            <AnimatePresence>
              {scrambleDone && (
                <motion.p
                  initial={{ opacity: 0, y: 16 }}
                  animate={{ opacity: 1, y: 0 }}
                  transition={{ duration: 0.65, delay: 0.35, ease: [0.25, 0.1, 0.25, 1.0] }}
                  style={{
                    fontFamily: 'Satoshi, sans-serif',
                    fontSize: '13px', letterSpacing: '0.18em',
                    textTransform: 'uppercase',
                    color: 'var(--text-secondary)',
                    marginTop: '36px',   /* ↑ was 18px — motto lower */
                  }}
                >
                  Engineered, not designed.
                </motion.p>
              )}
            </AnimatePresence>
          </motion.div>
        )}
      </AnimatePresence>

      {/* Scroll indicator */}
      <AnimatePresence>
        {scrambleDone && phase === 'interactive' && (
          <motion.div
            initial={{ opacity: 0 }} animate={{ opacity: 1 }} exit={{ opacity: 0 }}
            transition={{ duration: 0.5, delay: 0.7 }}
            style={{
              position: 'absolute', bottom: '44px', left: '50%',
              transform: 'translateX(-50%)', zIndex: 10,
            }}
          >
            <motion.div
              animate={{ y: [0, 10, 0] }}
              transition={{ duration: 2.2, repeat: Infinity, ease: 'easeInOut' }}
              style={{
                width: '1px', height: '52px',
                background: `linear-gradient(to bottom, transparent, rgba(${CANVAS_ACCENT_RGB}, 0.5))`,
              }}
            />
          </motion.div>
        )}
      </AnimatePresence>
    </section>
  )
}

/* ============================================================
   NAVBAR
   ============================================================ */
const NAV_ITEMS = [
  { icon: Zap,      label: 'Features',     href: '#features'     },
  { icon: Workflow, label: 'How It Works', href: '#how-it-works' },
  { icon: Info,     label: 'About',        href: '#about'        },
]

function Navbar({ isVisible }) {
  const [isScrolled, setIsScrolled] = useState(false)
  const [hoveredNav, setHoveredNav] = useState(null)

  useEffect(() => {
    const fn = () => setIsScrolled(window.scrollY > 10)
    window.addEventListener('scroll', fn, { passive: true })
    return () => window.removeEventListener('scroll', fn)
  }, [])

  return (
    <AnimatePresence>
      {isVisible && (
        <motion.header
          key="navbar"
          initial={{ opacity: 0, y: -16 }}
          animate={{ opacity: 1, y: 0 }}
          exit={{ opacity: 0, y: -16 }}
          transition={{ duration: 0.55, ease: [0.16, 1, 0.3, 1] }}
          className={`navbar${isScrolled ? ' scrolled' : ''}`}
          style={{ position: 'fixed', top: 0, left: 0, right: 0, zIndex: 100 }}
        >
          <Link to="/" style={{
            fontFamily: 'Clash Display, sans-serif',
            fontSize: '22px', fontWeight: '600',
            letterSpacing: '-0.02em',
            color: 'var(--text-primary)', textDecoration: 'none',
          }}>
            {BRAND_NAME}
          </Link>

          <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
            {/* Icon nav group */}
            <motion.div layout style={{
              display: 'flex', alignItems: 'center',
              padding: '5px', borderRadius: '12px',
              border: '1px solid var(--border-subtle)',
              backgroundColor: 'rgba(255,255,255,0.015)',
              gap: '2px',
            }}>
              {NAV_ITEMS.map((item, index) => (
                <NavIconItem
                  key={item.label}
                  item={item}
                  isHovered={hoveredNav === item.label}
                  isLeftOfHovered={
                    hoveredNav !== null &&
                    NAV_ITEMS.findIndex(n => n.label === hoveredNav) > index
                  }
                  onHover={setHoveredNav}
                />
              ))}
            </motion.div>

            {/* Separator */}
            <div style={{
              width: '1px', height: '22px',
              backgroundColor: 'var(--border-subtle)',
              margin: '0 6px', opacity: 0.7,
            }} />

            <LoginButton />

            <Link to="/auth" className="btn btn-primary"
              style={{ fontSize: '14px', padding: '10px 20px' }}>
              Sign Up
            </Link>
          </div>
        </motion.header>
      )}
    </AnimatePresence>
  )
}

function NavIconItem({ item, isHovered, isLeftOfHovered, onHover }) {
  const Icon = item.icon
  return (
    <motion.a
      href={item.href}
      layout
      onMouseEnter={() => onHover(item.label)}
      onMouseLeave={() => onHover(null)}
      animate={{ x: isLeftOfHovered ? -2 : 0 }}
      transition={{ duration: 0.38, ease: [0.16, 1, 0.3, 1] }}
      style={{
        display: 'flex', alignItems: 'center', gap: '5px',
        padding: '7px 9px', borderRadius: '8px',
        backgroundColor: isHovered ? 'var(--bg-surface-elevated)' : 'transparent',
        textDecoration: 'none', overflow: 'hidden', whiteSpace: 'nowrap',
        transition: 'background-color 180ms cubic-bezier(0.25,0.1,0.25,1)',
      }}
    >
      <motion.div layout="position">
        <Icon size={15} style={{
          color: isHovered ? 'var(--accent-primary)' : 'var(--text-secondary)',
          transition: 'color 160ms ease',
          display: 'block',
        }} />
      </motion.div>
      <AnimatePresence>
        {isHovered && (
          <motion.span
            initial={{ width: 0, opacity: 0 }}
            animate={{ width: 'auto', opacity: 1 }}
            exit={{ width: 0, opacity: 0 }}
            transition={{ duration: 0.32, ease: [0.16, 1, 0.3, 1] }}
            style={{
              fontFamily: 'Satoshi, sans-serif', fontSize: '13px',
              fontWeight: '500', color: 'var(--text-primary)',
              overflow: 'hidden', display: 'inline-block', lineHeight: 1,
            }}
          >
            {item.label}
          </motion.span>
        )}
      </AnimatePresence>
    </motion.a>
  )
}

function LoginButton() {
  const [hovered, setHovered] = useState(false)
  const [pressed, setPressed] = useState(false)
  return (
    <Link
      to="/auth"
      onMouseEnter={() => setHovered(true)}
      onMouseLeave={() => { setHovered(false); setPressed(false) }}
      onMouseDown={() => setPressed(true)}
      onMouseUp={() => setPressed(false)}
      style={{
        display: 'inline-flex', alignItems: 'center', justifyContent: 'center',
        padding: '10px 20px', borderRadius: pressed ? '12px' : '999px',
        border: `1px solid ${hovered ? 'var(--accent-primary)' : 'rgba(255,255,255,0.25)'}`,
        backgroundColor: hovered ? 'var(--accent-primary)' : 'transparent',
        color: hovered ? 'var(--bg-primary)' : 'var(--text-primary)',
        transform: hovered ? 'translateY(-1px)' : 'translateY(0)',
        fontFamily: 'Satoshi, sans-serif', fontSize: '14px', fontWeight: '500',
        textDecoration: 'none', whiteSpace: 'nowrap',
        // Explicit transitions — NOT transition-all (prevents morph jitter)
        transition: [
          'border-radius 380ms cubic-bezier(0.16,1,0.3,1)',
          'background-color 260ms cubic-bezier(0.16,1,0.3,1)',
          'border-color 260ms cubic-bezier(0.16,1,0.3,1)',
          'color 260ms cubic-bezier(0.16,1,0.3,1)',
          'transform 200ms cubic-bezier(0.16,1,0.3,1)',
        ].join(', '),
      }}
    >
      Login
    </Link>
  )
}

/* ============================================================
   HERO SECTION — word-by-word headline, spotlight card glow
   ============================================================ */
function HeroSection() {
  // Split headline into words for staggered animation
  const line1Words = ['Where', 'Ambition', 'Meets']
  const line2Words = ['Collaboration.']

  return (
    <section style={{
      minHeight: '100vh', display: 'flex', alignItems: 'center',
      padding: '0 64px', position: 'relative', overflow: 'hidden',
      backgroundColor: 'var(--bg-primary)',
    }}>
      <ParticleCanvas />

      <div aria-hidden="true" style={{
        position: 'absolute', top: '20%', left: '5%',
        width: '700px', height: '700px',
        background: `radial-gradient(circle, rgba(${CANVAS_ACCENT_RGB},0.06) 0%, transparent 68%)`,
        pointerEvents: 'none',
      }} />

      <div style={{
        display: 'flex', alignItems: 'center',
        justifyContent: 'space-between',
        width: '100%', gap: '64px',
        position: 'relative', zIndex: 10,
      }}>
        {/* Left — text */}
        <motion.div
          variants={stagger(0.04)}
          initial="hidden"
          animate="visible"
          style={{ flex: '0 0 50%', maxWidth: '50%' }}
        >
          {/* Headline — word by word */}
          <div style={{
            fontFamily: 'Clash Display, sans-serif',
            fontSize: '72px', lineHeight: '80px', fontWeight: '600',
            maxWidth: '600px', marginBottom: '24px',
            letterSpacing: '-0.02em',
          }}>
            {/* Line 1 */}
            <div style={{ display: 'flex', flexWrap: 'wrap', gap: '0 18px' }}>
              {line1Words.map((word, i) => (
                <motion.span
                  key={word}
                  variants={fadeUp}
                  style={{
                    display: 'inline-block',
                    color: word === 'Ambition'
                      ? 'var(--accent-primary)'
                      : 'var(--text-primary)',
                  }}
                >
                  {word}
                </motion.span>
              ))}
            </div>
            {/* Line 2 */}
            <div style={{ display: 'flex', flexWrap: 'wrap', gap: '0 18px' }}>
              {line2Words.map((word) => (
                <motion.span
                  key={word}
                  variants={fadeUp}
                  style={{ display: 'inline-block', color: 'var(--text-primary)' }}
                >
                  {word}
                </motion.span>
              ))}
            </div>
          </div>

          {/* Subtext */}
          <motion.p variants={fadeUp} style={{
            fontFamily: 'Satoshi, sans-serif', fontSize: '18px',
            lineHeight: '28px', color: 'var(--text-secondary)',
            maxWidth: '520px', marginBottom: '32px',
          }}>
            A professional platform engineered for teams who value growth,
            structured collaboration, and meaningful connections.
          </motion.p>

          {/* Buttons */}
          <motion.div variants={fadeUp} style={{
            display: 'flex', alignItems: 'center', gap: '24px',
          }}>
            <Link to="/auth" className="btn btn-primary" style={{
              backgroundColor: 'var(--bg-surface-elevated)',
              color: 'var(--text-primary)',
              border: '1px solid rgba(255,255,255,0.25)',
            }}
              onMouseEnter={e => {
                e.currentTarget.style.backgroundColor = 'var(--accent-primary)'
                e.currentTarget.style.color = 'var(--bg-primary)'
                e.currentTarget.style.borderColor = 'var(--accent-primary)'
              }}
              onMouseLeave={e => {
                e.currentTarget.style.backgroundColor = 'var(--bg-surface-elevated)'
                e.currentTarget.style.color = 'var(--text-primary)'
                e.currentTarget.style.borderColor = 'rgba(255,255,255,0.25)'
              }}
            >
              Get Started <ArrowRight size={16} />
            </Link>
            <Link to="/auth" className="btn btn-secondary" style={{
              border: '1px solid rgba(255,255,255,0.25)',
            }}>
              Learn More
            </Link>
          </motion.div>
        </motion.div>

        {/* Right — illustration with spotlight glow */}
        <motion.div
          initial={{ opacity: 0, scale: 0.98 }}
          animate={{ opacity: 1, scale: 1 }}
          transition={{ duration: 0.6, delay: 0.4, ease: [0.25, 0.1, 0.25, 1.0] }}
          style={{ flex: '0 0 46%', maxWidth: '46%' }}
        >
          <SpotlightCard />
        </motion.div>
      </div>
    </section>
  )
}

/* ============================================================
   SPOTLIGHT CARD
   Cursor-direction glow — moderate intensity.
   Uses a radial gradient mask that follows mouse position
   relative to card edges to create directional lighting.
   ============================================================ */
function SpotlightCard() {
  const cardRef = useRef(null)
  const [mouse, setMouse] = useState({ x: 0.5, y: 0.5 })
  const [hovered, setHovered] = useState(false)
  const [tilt, setTilt] = useState({ x: 0, y: 0 })
  const [floatOffset, setFloatOffset] = useState(0)

  // Float animation via useEffect (respects reduced motion)
  useEffect(() => {
    if (window.matchMedia('(prefers-reduced-motion: reduce)').matches) return
    let start = null
    let raf
    const animate = (ts) => {
      if (!start) start = ts
      const t = (ts - start) / 1000
      setFloatOffset(Math.sin(t * (Math.PI * 2 / 7)) * 8)
      raf = requestAnimationFrame(animate)
    }
    raf = requestAnimationFrame(animate)
    return () => cancelAnimationFrame(raf)
  }, [])

  const handleMouseMove = (e) => {
    const rect = cardRef.current?.getBoundingClientRect()
    if (!rect) return
    const x = (e.clientX - rect.left) / rect.width
    const y = (e.clientY - rect.top) / rect.height
    setMouse({ x, y })
    // Tilt: max 6 degrees
    setTilt({
      x: (y - 0.5) * -6,
      y: (x - 0.5) * 6,
    })
  }

  // Spotlight gradient — follows cursor, moderate glow
  const spotlightStyle = hovered ? {
    background: `radial-gradient(
      320px circle at ${mouse.x * 100}% ${mouse.y * 100}%,
      rgba(${CANVAS_ACCENT_RGB}, 0.14) 0%,
      transparent 65%
    )`,
  } : {}

  // Border glow — brighter in cursor direction
  const borderGlow = hovered
    ? `0 0 0 1px rgba(${CANVAS_ACCENT_RGB}, 0.5),
       ${(mouse.x - 0.5) * 20}px ${(mouse.y - 0.5) * 20}px 40px rgba(${CANVAS_ACCENT_RGB}, 0.12)`
    : '0 4px 24px rgba(0,0,0,0.25)'

  return (
    <motion.div
      ref={cardRef}
      onMouseMove={handleMouseMove}
      onMouseEnter={() => setHovered(true)}
      onMouseLeave={() => { setHovered(false); setTilt({ x: 0, y: 0 }) }}
      animate={{ rotateX: tilt.x, rotateY: tilt.y }}
      transition={{ duration: 0.22, ease: [0.25, 0.1, 0.25, 1.0] }}
      style={{
        maxWidth: '560px', width: '100%',
        translateY: floatOffset,
        transformStyle: 'preserve-3d',
        willChange: 'transform',
      }}
    >
      <div style={{
        position: 'relative',
        backgroundColor: 'var(--bg-surface-elevated)',
        border: `1px solid rgba(${CANVAS_ACCENT_RGB}, ${hovered ? 0.3 : 0.08})`,
        borderRadius: '18px', padding: '32px',
        boxShadow: borderGlow,
        overflow: 'hidden',
        transition: 'border-color 300ms ease, box-shadow 300ms ease',
      }}>
        {/* Spotlight overlay */}
        <div aria-hidden="true" style={{
          position: 'absolute', inset: 0,
          borderRadius: '18px', pointerEvents: 'none',
          transition: 'opacity 300ms ease',
          opacity: hovered ? 1 : 0,
          ...spotlightStyle,
        }} />

        {/* Chrome dots */}
        <div style={{ display: 'flex', gap: '8px', marginBottom: '24px' }}>
          {[0.14, 0.09, 0.07].map((op, i) => (
            <div key={i} style={{
              width: '10px', height: '10px', borderRadius: '50%',
              backgroundColor: `rgba(255,255,255,${op})`,
            }} />
          ))}
        </div>

        {/* Stat cards */}
        <div style={{
          display: 'grid', gridTemplateColumns: '1fr 1fr 1fr',
          gap: '12px', marginBottom: '24px',
        }}>
          {[
            { l: 'Projects', v: '12' },
            { l: 'Matched', v: '48' },
            { l: 'Score', v: '94%' },
          ].map(s => (
            <div key={s.l} style={{
              backgroundColor: 'var(--bg-surface)',
              border: '1px solid var(--border-subtle)',
              borderRadius: '10px', padding: '14px 10px', textAlign: 'center',
            }}>
              <div style={{
                fontFamily: 'Clash Display, sans-serif', fontSize: '20px',
                fontWeight: '600', color: 'var(--text-primary)', marginBottom: '4px',
              }}>{s.v}</div>
              <div style={{
                fontFamily: 'Satoshi, sans-serif', fontSize: '11px',
                color: 'var(--text-secondary)',
              }}>{s.l}</div>
            </div>
          ))}
        </div>

        {/* Progress */}
        <div style={{ marginBottom: '20px' }}>
          <div style={{
            display: 'flex', justifyContent: 'space-between', marginBottom: '8px',
          }}>
            <span style={{ fontSize: '12px', color: 'var(--text-secondary)', fontFamily: 'Satoshi, sans-serif' }}>
              Profile Completion
            </span>
            <span style={{ fontSize: '12px', color: 'var(--text-secondary)', fontFamily: 'Satoshi, sans-serif' }}>
              78%
            </span>
          </div>
          <div className="progress-track">
            <motion.div
              className="progress-fill"
              initial={{ width: '0%' }}
              animate={{ width: '78%' }}
              transition={{ duration: 1.2, delay: 0.8, ease: 'easeOut' }}
            />
          </div>
        </div>

        {/* Role tags */}
        <div style={{ display: 'flex', gap: '8px', flexWrap: 'wrap' }}>
          {['Builder', 'Problem Solver', 'Collaborator'].map(r => (
            <span key={r} style={{
              fontFamily: 'Satoshi, sans-serif', fontSize: '11px', fontWeight: '500',
              color: 'var(--text-secondary)', backgroundColor: 'var(--bg-surface-elevated)',
              padding: '4px 10px', borderRadius: '999px',
              border: '1px solid var(--border-subtle)',
            }}>{r}</span>
          ))}
        </div>
      </div>
    </motion.div>
  )
}

/* ============================================================
   FEATURES SECTION — Border reveal on hover, 3D tilt
   ============================================================ */
const FEATURES = [
  { icon: Target,  title: 'Smart Team Matching',     description: 'AI-driven role and interest scoring surfaces collaborators who complement your strengths — not just your availability.' },
  { icon: Layers,  title: 'Structured Communities',  description: 'Join communities built around technical disciplines. Every space has clear purpose and signal-to-noise ratio.' },
  { icon: Compass, title: 'Project Recommendations', description: 'Your motivation and skill profile drives recommendations that are ambitious but achievable.' },
]

function FeaturesSection() {
  const { ref, isInView } = useScrollReveal()

  return (
    <section id="features" ref={ref} style={{
      backgroundColor: 'var(--bg-primary)', padding: '144px 64px',
    }}>
      <motion.div
        variants={stagger(0.1)} initial="hidden"
        animate={isInView ? 'visible' : 'hidden'}
        style={{ textAlign: 'center', marginBottom: '72px' }}
      >
        <motion.p variants={fadeUp} style={{
          fontFamily: 'Satoshi, sans-serif', fontSize: '12px',
          letterSpacing: '0.2em', textTransform: 'uppercase',
          color: `rgba(16,185,129,0.5)`, marginBottom: '16px',
        }}>
          Core Capabilities
        </motion.p>
        <motion.h2 variants={fadeUp} style={{
          fontFamily: 'Clash Display, sans-serif', fontSize: '48px',
          lineHeight: '56px', fontWeight: '500',
          color: 'var(--text-primary)', marginBottom: '20px',
          letterSpacing: '-0.02em',
        }}>
          Engineered for Collaboration
        </motion.h2>
        <motion.p variants={fadeUp} style={{
          fontFamily: 'Satoshi, sans-serif', fontSize: '18px',
          lineHeight: '28px', color: 'var(--text-secondary)',
          maxWidth: '540px', margin: '0 auto',
        }}>
          Every feature exists to reduce noise and amplify meaningful work.
        </motion.p>
      </motion.div>

      <motion.div
        variants={stagger(0.12)} initial="hidden"
        animate={isInView ? 'visible' : 'hidden'}
        style={{
          display: 'grid', gridTemplateColumns: 'repeat(3, 1fr)',
          gap: '28px', maxWidth: '1160px', margin: '0 auto',
        }}
      >
        {FEATURES.map(f => <FeatureCard key={f.title} {...f} />)}
      </motion.div>
    </section>
  )
}

function FeatureCard({ icon: Icon, title, description }) {
  const ref = useRef(null)
  const [hovered, setHovered] = useState(false)
  const [tilt, setTilt] = useState({ x: 0, y: 0 })

  const handleMouseMove = (e) => {
    if (window.matchMedia('(prefers-reduced-motion: reduce)').matches) return
    const rect = ref.current?.getBoundingClientRect()
    if (!rect) return
    setTilt({
      x: ((e.clientY - rect.top) / rect.height - 0.5) * -6,
      y: ((e.clientX - rect.left) / rect.width - 0.5) * 6,
    })
  }

  return (
    <motion.div
      ref={ref}
      variants={fadeUp}
      onMouseMove={handleMouseMove}
      onMouseEnter={() => setHovered(true)}
      onMouseLeave={() => { setTilt({ x: 0, y: 0 }); setHovered(false) }}
      animate={{ rotateX: tilt.x, rotateY: tilt.y, y: hovered ? -6 : 0 }}
      transition={{ duration: 0.32, ease: [0.25, 0.1, 0.25, 1.0] }}
      style={{
        position: 'relative',
        backgroundColor: 'var(--bg-surface)',
        borderRadius: '14px',
        border: `1px solid ${hovered
          ? `rgba(${CANVAS_ACCENT_RGB}, 0.45)`
          : 'var(--border-subtle)'}`,
        padding: '40px 36px',
        boxShadow: hovered
          ? `0 24px 56px rgba(0,0,0,0.45), 0 0 0 1px rgba(${CANVAS_ACCENT_RGB},0.15)`
          : '0 4px 24px rgba(0,0,0,0.25)',
        transformStyle: 'preserve-3d',
        willChange: 'transform',
        transition: 'border-color 280ms ease, box-shadow 280ms ease',
        cursor: 'default',
      }}
    >
      {/* Icon */}
      <motion.div
        animate={{ scale: hovered ? 1.1 : 1 }}
        transition={{ duration: 0.26, ease: [0.25, 0.1, 0.25, 1.0] }}
        style={{
          width: '56px', height: '56px', borderRadius: '12px',
          backgroundColor: hovered
            ? `rgba(${CANVAS_ACCENT_RGB}, 0.12)`
            : 'var(--bg-surface-elevated)',
          display: 'flex', alignItems: 'center', justifyContent: 'center',
          marginBottom: '24px', color: hovered ? 'var(--accent-primary)' : 'var(--text-secondary)',
          transition: 'background-color 280ms ease, color 280ms ease',
        }}
      >
        <Icon size={26} />
      </motion.div>

      <h3 style={{
        fontFamily: 'Satoshi, sans-serif', fontSize: '22px',
        lineHeight: '30px', fontWeight: '600',
        color: 'var(--text-primary)', marginBottom: '14px',
      }}>{title}</h3>

      <p style={{
        fontFamily: 'Satoshi, sans-serif', fontSize: '16px',
        lineHeight: '26px', color: 'var(--text-secondary)',
      }}>{description}</p>
    </motion.div>
  )
}

/* ============================================================
   HOW IT WORKS — Apple-style pinned scroll
   Architecture:
   - Outer wrapper: height = 3 × 200vh = 600vh (scroll track)
   - Inner panel: position sticky, height 100vh
   - useScroll tracks progress within outer wrapper
   - 3 steps, each occupying 1/3 of scroll range
   - Left: vertical progress line + step text
   - Right: illustrated mockup per step
   ============================================================ */
const HOW_STEPS = [
  {
    number: '01',
    title: 'Answer the Questionnaire',
    caption: 'Takes under 5 minutes. Tell us about your interests, work style, and what drives you.',
    icon: CheckCircle,
    mockupType: 'questionnaire',
  },
  {
    number: '02',
    title: 'Receive Your Profile',
    caption: 'Our AI scores your responses into a structured collaboration profile. No buzzwords, no inflation.',
    icon: BarChart3,
    mockupType: 'profile',
  },
  {
    number: '03',
    title: 'Connect and Build',
    caption: 'Discover matched communities, recommended projects, and teammates who complement your strengths.',
    icon: Users,
    mockupType: 'connect',
  },
]

function HowItWorksSection() {
  const outerRef = useRef(null)
  const { scrollYProgress } = useScroll({
    target: outerRef,
    offset: ['start start', 'end end'],
  })

  const [activeStep, setActiveStep] = useState(0)

  useEffect(() => {
    return scrollYProgress.on('change', (v) => {
      if (v < 0.33) setActiveStep(0)
      else if (v < 0.66) setActiveStep(1)
      else setActiveStep(2)
    })
  }, [scrollYProgress])

  const lineHeight = useTransform(scrollYProgress, [0, 1], ['0%', '100%'])

  return (
    // Outer: 300vh — 50% of original 600vh
    <div
      id="how-it-works"
      ref={outerRef}
      style={{ height: '300vh', position: 'relative' }}
    >
      {/* Sticky panel */}
      <div style={{
        position: 'sticky',
        top: 0,
        height: '100vh',
        display: 'flex',
        flexDirection: 'column',
        backgroundColor: 'var(--bg-surface-elevated)',
        overflow: 'hidden',
      }}>
        {/* Section header */}
        <div style={{
          textAlign: 'center',
          padding: '96px 72px 8px',
          flexShrink: 0,
        }}>
          <p style={{
            fontFamily: 'Satoshi, sans-serif', fontSize: '12px',
            letterSpacing: '0.2em', textTransform: 'uppercase',
            color: `rgba(16,185,129,0.5)`, marginBottom: '8px',
          }}>
            The Process
          </p>
          <h2 style={{
            fontFamily: 'Clash Display, sans-serif', fontSize: '40px',
            lineHeight: '48px', fontWeight: '500',
            color: 'var(--text-primary)', marginBottom: '8px',
          }}>
            How It Works
          </h2>
          <p style={{
            fontFamily: 'Satoshi, sans-serif', fontSize: '18px',
            lineHeight: '28px', color: 'var(--text-secondary)',
          }}>
            Three steps from signup to your first meaningful collaboration.
          </p>
        </div>

        {/* Content area */}
        <div style={{
          display: 'flex',
          flex: 1,
          padding: '0 64px 48px',
          gap: '56px',
          overflow: 'hidden',
        }}>
          {/* LEFT — vertical progress + steps */}
          <div style={{
            flex: '0 0 45%',
            position: 'relative',
            display: 'grid',
            gridTemplateColumns: '20px 1fr',
            gridTemplateRows: 'repeat(3, minmax(0, 1fr))',
            columnGap: '28px',
            rowGap: '16px',
            paddingTop: '8px',
            height: '70%',
            alignSelf: 'center',
          }}>
            {/* Track behind dots */}
            <div style={{
              position: 'absolute',
              left: '9px',
              top: 0,
              bottom: 0,
              width: '2px',
              backgroundColor: 'var(--border-subtle)',
              borderRadius: '999px',
            }}>
              <motion.div
                style={{
                  position: 'absolute',
                  top: 0, left: 0, right: 0,
                  height: lineHeight,
                  backgroundColor: 'var(--accent-primary)',
                  borderRadius: '999px',
                  boxShadow: `0 0 8px rgba(${CANVAS_ACCENT_RGB}, 0.5)`,
                }}
              />
            </div>

            {HOW_STEPS.map((step, i) => {
              const isPassed = i <= activeStep
              const isActive = i === activeStep
              return (
                <div key={step.number} style={{ display: 'contents' }}>
                  <motion.div
                    animate={{
                      backgroundColor: isPassed
                        ? `rgba(${CANVAS_ACCENT_RGB}, 1)`
                        : 'var(--bg-surface-elevated)',
                      borderColor: isPassed
                        ? `rgba(${CANVAS_ACCENT_RGB}, 1)`
                        : 'rgba(255,255,255,0.15)',
                      scale: isActive ? 1.4 : 1,
                    }}
                    transition={{ duration: 0.45, ease: [0.25, 0.1, 0.25, 1.0] }}
                    style={{
                      width: '12px', height: '12px',
                      borderRadius: '50%',
                      border: '2px solid',
                      zIndex: 2,
                      alignSelf: 'center',
                      justifySelf: 'center',
                      boxShadow: isActive
                        ? `0 0 12px rgba(${CANVAS_ACCENT_RGB}, 0.6)`
                        : 'none',
                    }}
                  />

                  <motion.div
                    animate={{
                      opacity: isActive ? 1 : 0.32,
                      scale: isActive ? 1 : 0.96,
                    }}
                    transition={{ duration: 0.55, ease: [0.25, 0.1, 0.25, 1.0] }}
                    style={{
                      display: 'flex', flexDirection: 'column', justifyContent: 'center',
                      transformOrigin: 'left center',
                    }}
                  >
                    <div style={{
                      fontFamily: 'Satoshi, sans-serif', fontSize: '11px',
                      fontWeight: '600', letterSpacing: '0.12em',
                      color: 'var(--text-secondary)',
                      marginBottom: '6px',
                      transition: 'color 450ms ease',
                    }}>
                      {step.number}
                    </div>
                    <h3 style={{
                      fontFamily: 'Satoshi, sans-serif',
                      fontSize: isActive ? '22px' : '18px',
                      lineHeight: '28px', fontWeight: '600',
                      color: isActive ? 'var(--text-primary)' : 'var(--text-secondary)',
                      marginBottom: '8px',
                      transition: 'font-size 450ms ease, color 450ms ease',
                    }}>
                      {step.title}
                    </h3>
                    <p style={{
                      fontFamily: 'Satoshi, sans-serif', fontSize: '14px',
                      lineHeight: '22px', color: 'var(--text-secondary)',
                      maxWidth: '340px',
                    }}>
                      {step.caption}
                    </p>
                  </motion.div>
                </div>
              )
            })}
          </div>

          {/* RIGHT — illustrated mockup */}
          <div style={{
            flex: 1,
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            position: 'relative',
          }}>
            <AnimatePresence mode="wait">
              <motion.div
                key={activeStep}
                initial={{ opacity: 0, y: 24 }}
                animate={{ opacity: 1, y: 0 }}
                exit={{ opacity: 0, y: -24 }}
                transition={{ duration: 0.5, ease: [0.25, 0.1, 0.25, 1.0] }}
                style={{ width: '100%', maxWidth: '510px' }}
              >
                <StepMockup step={HOW_STEPS[activeStep]} />
              </motion.div>
            </AnimatePresence>
          </div>
        </div>
      </div>
    </div>
  )
}

/* Step mockups — one illustrated UI per step */
function StepMockup({ step }) {
  const base = {
    backgroundColor: 'var(--bg-surface)',
    border: '1px solid var(--border-subtle)',
    borderRadius: '14px',
    padding: '28px',
    boxShadow: '0 4px 24px rgba(0,0,0,0.25)',
  }

  if (step.mockupType === 'questionnaire') {
    return (
      <div style={base}>
        <div style={{ marginBottom: '20px' }}>
          <div style={{ fontFamily: 'Clash Display, sans-serif', fontSize: '16px', fontWeight: '600', color: 'var(--text-primary)', marginBottom: '6px' }}>
            What best describes your work style?
          </div>
          <div style={{ fontFamily: 'Satoshi, sans-serif', fontSize: '13px', color: 'var(--text-secondary)' }}>
            Question 3 of 8
          </div>
        </div>
        <div className="progress-track" style={{ marginBottom: '24px' }}>
          <div className="progress-fill" style={{ width: '37.5%' }} />
        </div>
        {['I prefer to lead and delegate tasks', 'I like diving deep into one problem', 'I thrive connecting people and ideas', 'I focus on building and shipping fast'].map((opt, i) => (
          <motion.div
            key={opt}
            initial={{ opacity: 0, x: -8 }}
            animate={{ opacity: 1, x: 0 }}
            transition={{ delay: i * 0.07, duration: 0.3 }}
            style={{
              padding: '12px 16px', borderRadius: '10px', marginBottom: '10px',
              border: `1px solid ${i === 2 ? `rgba(${CANVAS_ACCENT_RGB},0.5)` : 'var(--border-subtle)'}`,
              backgroundColor: i === 2 ? 'var(--accent-soft)' : 'var(--bg-surface-elevated)',
              fontFamily: 'Satoshi, sans-serif', fontSize: '14px',
              color: i === 2 ? 'var(--accent-primary)' : 'var(--text-secondary)',
              cursor: 'pointer',
            }}
          >
            {opt}
          </motion.div>
        ))}
      </div>
    )
  }

  if (step.mockupType === 'profile') {
    return (
      <div style={base}>
        <div style={{ fontFamily: 'Clash Display, sans-serif', fontSize: '16px', fontWeight: '600', color: 'var(--text-primary)', marginBottom: '20px' }}>
          Your Collaboration Profile
        </div>
        {[
          { label: 'Collaborator', score: 8.4 },
          { label: 'Problem Solver', score: 7.9 },
          { label: 'Builder', score: 7.2 },
          { label: 'Explorer', score: 5.8 },
        ].map((r, i) => (
          <div key={r.label} style={{ marginBottom: '14px' }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '6px' }}>
              <span style={{ fontFamily: 'Satoshi, sans-serif', fontSize: '13px', color: 'var(--text-primary)' }}>{r.label}</span>
              <span style={{ fontFamily: 'Satoshi, sans-serif', fontSize: '13px', color: 'var(--text-primary)', fontWeight: '600' }}>{r.score}</span>
            </div>
            <div className="progress-track">
              <motion.div
                className="progress-fill"
                initial={{ width: '0%' }}
                animate={{ width: `${r.score * 10}%` }}
                transition={{ duration: 0.8, delay: i * 0.1, ease: 'easeOut' }}
              />
            </div>
          </div>
        ))}
        <div style={{ marginTop: '20px', padding: '12px 16px', borderRadius: '10px', backgroundColor: 'var(--accent-soft)', border: `1px solid rgba(${CANVAS_ACCENT_RGB},0.2)` }}>
          <span style={{ fontFamily: 'Satoshi, sans-serif', fontSize: '13px', color: 'var(--accent-primary)', fontWeight: '500' }}>
            Motivation Score: 8.1 / 10
          </span>
        </div>
      </div>
    )
  }

  // connect
  return (
    <div style={base}>
      <div style={{ fontFamily: 'Clash Display, sans-serif', fontSize: '16px', fontWeight: '600', color: 'var(--text-primary)', marginBottom: '20px' }}>
        Your Matches
      </div>
      {[
        { name: 'Aryan M.', roles: ['Architect', 'Leader'], score: '96%' },
        { name: 'Selin K.', roles: ['Designer', 'Product Thinker'], score: '91%' },
        { name: 'James R.', roles: ['Builder', 'Specialist'], score: '88%' },
      ].map((m, i) => (
        <motion.div
          key={m.name}
          initial={{ opacity: 0, x: 12 }}
          animate={{ opacity: 1, x: 0 }}
          transition={{ delay: i * 0.1, duration: 0.35 }}
          style={{
            display: 'flex', alignItems: 'center', justifyContent: 'space-between',
            padding: '12px 14px', borderRadius: '10px', marginBottom: '10px',
            backgroundColor: 'var(--bg-surface-elevated)',
            border: '1px solid var(--border-subtle)',
          }}
        >
          <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
            <div style={{
              width: '36px', height: '36px', borderRadius: '50%',
              backgroundColor: 'var(--bg-surface)', flexShrink: 0,
              border: '1px solid var(--border-subtle)',
              display: 'flex', alignItems: 'center', justifyContent: 'center',
            }}>
              <span style={{ fontFamily: 'Satoshi, sans-serif', fontSize: '11px', fontWeight: '600', color: 'var(--text-secondary)' }}>
                {m.name.split(' ').map(n => n[0]).join('')}
              </span>
            </div>
            <div>
              <div style={{ fontFamily: 'Satoshi, sans-serif', fontSize: '14px', fontWeight: '600', color: 'var(--text-primary)' }}>{m.name}</div>
              <div style={{ fontFamily: 'Satoshi, sans-serif', fontSize: '11px', color: 'var(--text-secondary)' }}>{m.roles.join(' · ')}</div>
            </div>
          </div>
          <span style={{
            fontFamily: 'Satoshi, sans-serif', fontSize: '13px', fontWeight: '600',
            color: `rgba(16,185,129,0.7)`,
            padding: '3px 10px', borderRadius: '999px',
          }}>{m.score}</span>
        </motion.div>
      ))}
    </div>
  )
}

/* ============================================================
   TESTIMONIALS — premium redesign with large quote mark and
   staggered scroll-reveal
   ============================================================ */
const TESTIMONIALS = [
  { quote: 'MeshWork matched me with a team that actually complemented my skills. The role scoring was eerily accurate.', name: 'Priya Sharma', role: 'Full-Stack Engineer', initials: 'PS', color: `rgba(${CANVAS_ACCENT_RGB}, 0.14)` },
  { quote: 'Finally a platform that functions like an engineering tool. Community discovery is structured and noise-free.', name: 'Marcus Oyelaran', role: 'Product Designer', initials: 'MO', color: 'rgba(255,255,255,0.04)' },
  { quote: 'The questionnaire took 4 minutes. The matches took seconds. My team has been together 8 months.', name: 'Chen Wei', role: 'ML Engineer', initials: 'CW', color: `rgba(${CANVAS_ACCENT_RGB}, 0.08)` },
]

function TestimonialsSection() {
  const { ref, isInView } = useScrollReveal(0.1)
  return (
    <section ref={ref} style={{
      backgroundColor: 'var(--bg-primary)',
      padding: '144px 64px',
      position: 'relative',
      overflow: 'hidden',
    }}>
      {/* Subtle background accent */}
      <div aria-hidden="true" style={{
        position: 'absolute', top: '50%', left: '50%',
        transform: 'translate(-50%,-50%)',
        width: '900px', height: '600px',
        background: `radial-gradient(ellipse, rgba(${CANVAS_ACCENT_RGB},0.04) 0%, transparent 70%)`,
        pointerEvents: 'none',
      }} />

      <motion.div
        variants={stagger(0.1)} initial="hidden"
        animate={isInView ? 'visible' : 'hidden'}
        style={{ textAlign: 'center', marginBottom: '80px', position: 'relative', zIndex: 1 }}
      >
        <motion.p variants={fadeUp} style={{
          fontFamily: 'Satoshi, sans-serif', fontSize: '12px',
          letterSpacing: '0.2em', textTransform: 'uppercase',
          color: `rgba(16,185,129,0.5)`, marginBottom: '16px',
        }}>
          Outcomes
        </motion.p>
        <motion.h2 variants={fadeUp} style={{
          fontFamily: 'Clash Display, sans-serif', fontSize: '48px',
          lineHeight: '56px', fontWeight: '500', letterSpacing: '-0.02em',
          color: 'var(--text-primary)', marginBottom: '20px',
        }}>
          Built on Real Outcomes
        </motion.h2>
        <motion.p variants={fadeUp} style={{
          fontFamily: 'Satoshi, sans-serif', fontSize: '18px',
          lineHeight: '28px', color: 'var(--text-secondary)',
          maxWidth: '480px', margin: '0 auto',
        }}>
          What the people who use MeshWork actually say.
        </motion.p>
      </motion.div>

      <motion.div
        variants={stagger(0.14)} initial="hidden"
        animate={isInView ? 'visible' : 'hidden'}
        style={{
          display: 'grid', gridTemplateColumns: 'repeat(3, 1fr)',
          gap: '24px', maxWidth: '1160px', margin: '0 auto',
          position: 'relative', zIndex: 1,
        }}
      >
        {TESTIMONIALS.map(t => <TestimonialCard key={t.name} {...t} />)}
      </motion.div>
    </section>
  )
}

function TestimonialCard({ quote, name, role, initials, color }) {
  const [hovered, setHovered] = useState(false)
  return (
    <motion.div
      variants={fadeUp}
      onMouseEnter={() => setHovered(true)}
      onMouseLeave={() => setHovered(false)}
      animate={{ y: hovered ? -6 : 0 }}
      transition={{ duration: 0.42, ease: [0.25, 0.1, 0.25, 1.0] }}
      style={{
        backgroundColor: hovered ? 'var(--bg-surface-elevated)' : 'var(--bg-surface)',
        borderRadius: '18px',
        border: `1px solid ${hovered ? `rgba(${CANVAS_ACCENT_RGB},0.28)` : 'var(--border-subtle)'}`,
        padding: '36px 32px',
        display: 'flex', flexDirection: 'column', gap: '28px',
        boxShadow: hovered
          ? `0 20px 48px rgba(0,0,0,0.42), 0 0 0 1px rgba(${CANVAS_ACCENT_RGB},0.1)`
          : '0 4px 24px rgba(0,0,0,0.2)',
        transition: 'background-color 320ms ease, border-color 320ms ease, box-shadow 320ms ease',
        cursor: 'default',
        position: 'relative',
        overflow: 'hidden',
      }}
    >
      {/* Decorative quote mark */}
      <div aria-hidden="true" style={{
        position: 'absolute', top: '20px', right: '24px',
        fontFamily: 'Clash Display, sans-serif',
        fontSize: '80px', lineHeight: 1, fontWeight: '600',
        color: `rgba(${CANVAS_ACCENT_RGB}, ${hovered ? 0.12 : 0.06})`,
        transition: 'color 320ms ease',
        userSelect: 'none',
        pointerEvents: 'none',
      }}>
        "
      </div>

      {/* Quote text */}
      <p style={{
        fontFamily: 'Satoshi, sans-serif', fontSize: '16px',
        lineHeight: '27px',
        color: hovered ? 'var(--text-primary)' : 'var(--text-secondary)',
        transition: 'color 320ms ease',
        position: 'relative', zIndex: 1,
        maxWidth: '320px',
      }}>
        "{quote}"
      </p>

      {/* Author row */}
      <div style={{ display: 'flex', alignItems: 'center', gap: '14px' }}>
        {/* Avatar */}
        <div style={{
          width: '44px', height: '44px', borderRadius: '50%',
          backgroundColor: 'var(--bg-surface-elevated)',
          border: '1px solid var(--border-subtle)',
          display: 'flex', alignItems: 'center', justifyContent: 'center',
          flexShrink: 0,
        }}>
          <span style={{
            fontFamily: 'Satoshi, sans-serif', fontSize: '12px',
            fontWeight: '700', color: 'var(--text-secondary)',
            letterSpacing: '0.04em',
          }}>{initials}</span>
        </div>
        <div>
          <div style={{
            fontFamily: 'Satoshi, sans-serif', fontSize: '15px',
            fontWeight: '600', color: 'var(--text-primary)', lineHeight: '22px',
          }}>{name}</div>
          <div style={{
            fontFamily: 'Satoshi, sans-serif', fontSize: '13px',
            lineHeight: '20px', color: 'var(--text-secondary)',
          }}>{role}</div>
        </div>
      </div>
    </motion.div>
  )
}

/* ============================================================
   FOOTER
   ============================================================ */
function Footer() {
  return (
    <footer style={{ backgroundColor: 'var(--bg-surface)', borderTop: '1px solid var(--border-subtle)', padding: '96px 64px' }}>
      <div style={{ display: 'grid', gridTemplateColumns: '1.5fr 1fr 1fr', gap: '64px', maxWidth: '1100px', margin: '0 auto 64px auto' }}>
        <div>
          <div style={{ fontFamily: 'Clash Display, sans-serif', fontSize: '20px', fontWeight: '600', color: 'var(--text-primary)', letterSpacing: '-0.02em', marginBottom: '16px' }}>MeshWork</div>
          <p style={{ fontFamily: 'Satoshi, sans-serif', fontSize: '14px', lineHeight: '22px', color: 'var(--text-secondary)', maxWidth: '280px' }}>
            A professional collaboration platform engineered for teams who build with intention.
          </p>
        </div>
        <FooterColumn title="Product" links={[{ label: 'Features', href: '#features' }, { label: 'How It Works', href: '#how-it-works' }, { label: 'Roadmap', href: '#' }]} />
        <FooterColumn title="Community & Legal" links={[{ label: 'About', href: '#about' }, { label: 'Privacy Policy', href: '#' }, { label: 'Terms of Service', href: '#' }]} />
      </div>
      <div style={{ borderTop: '1px solid var(--border-subtle)', paddingTop: '32px', textAlign: 'center', maxWidth: '1100px', margin: '0 auto' }}>
        <p style={{ fontFamily: 'Satoshi, sans-serif', fontSize: '14px', color: 'var(--text-secondary)' }}>
          © 2026 MeshWork. Engineered, not designed.
        </p>
      </div>
    </footer>
  )
}

function FooterColumn({ title, links }) {
  return (
    <div>
      <div style={{ fontFamily: 'Satoshi, sans-serif', fontSize: '16px', fontWeight: '600', color: 'var(--text-primary)', marginBottom: '20px' }}>{title}</div>
      <ul style={{ listStyle: 'none', padding: 0, margin: 0, display: 'flex', flexDirection: 'column', gap: '12px' }}>
        {links.map(link => (
          <li key={link.label}>
            <a href={link.href} style={{ fontFamily: 'Satoshi, sans-serif', fontSize: '14px', color: 'var(--text-secondary)', textDecoration: 'none', transition: 'color 180ms ease' }}
              onMouseEnter={e => e.currentTarget.style.color = 'var(--accent-primary)'}
              onMouseLeave={e => e.currentTarget.style.color = 'var(--text-secondary)'}
            >{link.label}</a>
          </li>
        ))}
      </ul>
    </div>
  )
}

/* ============================================================
   ROOT EXPORT
   ============================================================ */
export default function Landing() {
  const [navVisible, setNavVisible] = useState(false)

  const handleBrandLocked = useCallback((locked = true) => {
    setNavVisible(locked)
  }, [])

  return (
    <div style={{ backgroundColor: 'var(--bg-primary)', color: 'var(--text-primary)' }}>
      <a href="#main-content" className="skip-to-content">Skip to content</a>
      <Navbar isVisible={navVisible} />
      <main id="main-content">
        <BrandIntroSection onBrandLocked={handleBrandLocked} />
        <HeroSection />
        <FeaturesSection />
        <HowItWorksSection />
        <TestimonialsSection />
      </main>
      <Footer />
    </div>
  )
}