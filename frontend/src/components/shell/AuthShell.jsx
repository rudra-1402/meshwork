import { AnimatePresence, motion } from 'framer-motion'
import { Link } from 'react-router-dom'
import { MultiPaneLayout, PaneSurface } from '../layout'
import { StepProgressBar } from '../form/StepProgressBar'
import { EASE } from '../form/formConstants'
import { useFormStepContext } from '../../context/FormStepContext'

function resolveLeftPanel(config, currentStep) {
  const base = config?.leftPanel ?? { mode: 'image' }

  if (base.mode === 'image') {
    const stepConfig = Array.isArray(base.steps) ? base.steps[currentStep] : null
    return {
      mode: 'image',
      image: stepConfig?.image || base.image || '/auth-signup.png',
      tagline: stepConfig?.tagline || base.tagline || 'Engineered, not designed.',
    }
  }

  const steps = Array.isArray(config?.steps) ? config.steps : []
  const current = steps[currentStep] || {}
  return {
    mode: 'stepInfo',
    stepTitle: current.title || 'Step',
    stepDescription: current.description || '',
    currentStep,
    totalSteps: steps.length || 1,
    stepLabels: steps.map((step) => step.title || step.id || 'Step'),
  }
}

function LeftImagePanel({ image, tagline, brandTo }) {
  return (
    <div
      style={{
        position: 'relative',
        overflow: 'hidden',
        borderRadius: '28px',
        flex: 1,
        backgroundColor: 'var(--bg-primary)',
      }}
    >
      <AnimatePresence initial={false}>
        <motion.img
          key={image}
          src={image}
          alt=""
          initial={{ opacity: 0, scale: 1.04 }}
          animate={{ opacity: 1, scale: 1 }}
          exit={{ opacity: 0, scale: 0.97 }}
          transition={{ duration: 0.85, ease: EASE }}
          style={{
            position: 'absolute',
            inset: 0,
            width: '100%',
            height: '100%',
            objectFit: 'cover',
            objectPosition: 'center 30%',
          }}
        />
      </AnimatePresence>

      <div
        style={{
          position: 'absolute',
          inset: 0,
          background: 'linear-gradient(to right, rgba(14,17,19,0), rgba(14,17,19,0.18))',
          pointerEvents: 'none',
        }}
      />

      <div
        style={{
          position: 'absolute',
          left: 0,
          right: 0,
          top: 0,
          height: '34%',
          background: 'linear-gradient(to bottom, rgba(14,17,19,0.55), rgba(14,17,19,0))',
          pointerEvents: 'none',
        }}
      />

      <div
        style={{
          position: 'absolute',
          left: 0,
          right: 0,
          bottom: 0,
          height: '34%',
          background: 'linear-gradient(to top, rgba(14,17,19,0.58), rgba(14,17,19,0))',
          pointerEvents: 'none',
        }}
      />

      <Link
        to={brandTo}
        aria-label="MeshWork — back to home"
        style={{
          position: 'absolute',
          top: '32px',
          left: '40px',
          zIndex: 10,
          fontFamily: 'Clash Display, sans-serif',
          fontSize: '22px',
          fontWeight: 600,
          letterSpacing: '-0.02em',
          color: 'var(--text-primary)',
          textDecoration: 'none',
        }}
      >
        MeshWork
      </Link>

      <p
        style={{
          position: 'absolute',
          bottom: '32px',
          left: '40px',
          zIndex: 10,
          margin: 0,
          fontFamily: 'Satoshi, sans-serif',
          fontSize: '12px',
          letterSpacing: '0.18em',
          textTransform: 'uppercase',
          color: 'var(--text-secondary)',
          opacity: 0.72,
        }}
      >
        {tagline}
      </p>
    </div>
  )
}

function LeftStepInfoPanel({ brandTo, stepTitle, stepDescription, currentStep, totalSteps, stepLabels }) {
  return (
    <div
      style={{
        position: 'relative',
        overflow: 'hidden',
        borderRadius: '28px',
        flex: 1,
        backgroundColor: 'var(--bg-primary)',
        border: '1px solid var(--border-subtle)',
        padding: '32px 40px',
        display: 'flex',
        flexDirection: 'column',
      }}
    >
      <Link
        to={brandTo}
        aria-label="MeshWork — back to home"
        style={{
          fontFamily: 'Clash Display, sans-serif',
          fontSize: '22px',
          fontWeight: 600,
          letterSpacing: '-0.02em',
          color: 'var(--text-primary)',
          textDecoration: 'none',
          marginBottom: '40px',
        }}
      >
        MeshWork
      </Link>

      <div style={{ marginTop: 'auto', marginBottom: 'auto', display: 'flex', flexDirection: 'column', gap: '14px' }}>
        <h2
          style={{
            margin: 0,
            fontFamily: 'Clash Display, sans-serif',
            fontSize: '42px',
            lineHeight: 1.1,
            fontWeight: 600,
            color: 'var(--text-primary)',
          }}
        >
          {stepTitle}
        </h2>

        <p className="text-body" style={{ color: 'var(--text-secondary)', margin: 0 }}>
          {stepDescription}
        </p>

        <div style={{ marginTop: '8px' }}>
          <StepProgressBar currentStep={currentStep} totalSteps={totalSteps} stepLabels={stepLabels} />
        </div>
      </div>

      <p className="text-small text-muted" style={{ margin: 0 }}>
        Step {currentStep + 1} of {totalSteps}
      </p>
    </div>
  )
}

export function AuthShell({ config, brandTo = '/', children }) {
  const { currentStep } = useFormStepContext()
  const leftPanel = resolveLeftPanel(config, currentStep)

  return (
    <MultiPaneLayout
      panes={[
        {
          key: 'auth-shell-left',
          ariaHidden: true,
          flex: '0 0 55%',
          padding: '28px 16px 28px 28px',
          content: leftPanel.mode === 'stepInfo'
            ? (
              <LeftStepInfoPanel
                brandTo={brandTo}
                stepTitle={leftPanel.stepTitle}
                stepDescription={leftPanel.stepDescription}
                currentStep={leftPanel.currentStep}
                totalSteps={leftPanel.totalSteps}
                stepLabels={leftPanel.stepLabels}
              />
            )
            : <LeftImagePanel image={leftPanel.image} tagline={leftPanel.tagline} brandTo={brandTo} />,
        },
        {
          key: 'auth-shell-right',
          flex: '0 0 45%',
          minWidth: 0,
          padding: '28px 28px 28px 16px',
          content: (
            <PaneSurface
              maxWidth="760px"
              padding="clamp(28px, 4vw, 56px)"
              border="1px solid var(--border-subtle)"
            >
              <div style={{ width: '100%', maxWidth: '500px' }}>
                {children}
              </div>
            </PaneSurface>
          ),
        },
      ]}
      style={{ minHeight: '100vh' }}
    />
  )
}
