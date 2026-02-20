export const ACCENT_RGB = '16, 185, 129'
export const EASE = [0.25, 0.1, 0.25, 1]
export const MORPH_TRANSITION = { type: 'spring', stiffness: 400, damping: 30 }

export const FIELD_VARIANTS = {
  hidden: { opacity: 0, y: -14 },
  visible: { opacity: 1, y: 0, transition: { duration: 0.26, ease: EASE } },
  exit: { opacity: 0, y: -10, transition: { duration: 0.18, ease: EASE } },
}

export const FIELD_CONTAINER_VARIANTS = {
  hidden: { opacity: 0 },
  visible: { opacity: 1, transition: { staggerChildren: 0.055, delayChildren: 0.02 } },
  exit: { opacity: 0, transition: { staggerChildren: 0.03, staggerDirection: -1 } },
}
