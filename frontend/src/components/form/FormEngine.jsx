import { useEffect, useMemo, useState } from 'react'
import { AnimatePresence, motion } from 'framer-motion'
import {
  Mail,
  User,
  Lock,
  Building2,
  Briefcase,
  GraduationCap,
  Users,
  FolderKanban,
} from 'lucide-react'
import { Link } from 'react-router-dom'
import { useFormStepContext } from '../../context/FormStepContext'
import { resolveAnswerType } from './AnswerRegistry'
import { Field } from './Field'
import { StyledInput } from './StyledInput'
import { PasswordInput } from './PasswordInput'
import { SubmitButton } from './SubmitButton'
import { ModeToggleLink } from './ModeToggleLink'
import { EASE, FIELD_CONTAINER_VARIANTS, FIELD_VARIANTS } from './formConstants'

const ICON_MAP = {
  Mail,
  User,
  Lock,
  Building2,
  Briefcase,
  GraduationCap,
  Users,
  FolderKanban,
}

function resolveModeStrings(config, mode, fallbackStep) {
  if (config?.modes && mode && config.modes[mode]) {
    return {
      title: config.modes[mode].title,
      subtitle: config.modes[mode].subtitle,
    }
  }

  return {
    title: fallbackStep?.formTitle || fallbackStep?.title || 'Form',
    subtitle: fallbackStep?.formSubtitle || fallbackStep?.description || '',
  }
}

function normalizeValuesByFields(fields, values) {
  const ids = []
  const visit = (fieldList) => {
    fieldList.forEach((field) => {
      if (field.type === 'row' && Array.isArray(field.fields)) {
        visit(field.fields)
      } else if (field.id) {
        ids.push(field.id)
      }
    })
  }
  visit(fields)

  return ids.reduce((accumulator, id) => {
    accumulator[id] = values[id]
    return accumulator
  }, {})
}

export function FormEngine({ config, onSuccess, className }) {
  const { currentStep, setCurrentStep, mode, setMode, totalSteps } = useFormStepContext()

  const [values, setValues] = useState({})
  const [meta, setMeta] = useState({})
  const [errors, setErrors] = useState({})
  const [globalError, setGlobalError] = useState('')
  const [submitting, setSubmitting] = useState(false)
  const [terminalResult, setTerminalResult] = useState(null)
  const [showTerminal, setShowTerminal] = useState(false)

  const steps = useMemo(() => (Array.isArray(config?.steps) ? config.steps : []), [config])
  const safeStep = Math.min(Math.max(0, currentStep), Math.max(0, steps.length - 1))
  const step = steps[safeStep] || { fields: [] }
  const isLastStep = safeStep === steps.length - 1

  useEffect(() => {
    if (config?.defaultMode && !mode) {
      setMode(config.defaultMode)
    }
  }, [config, mode, setMode])

  useEffect(() => {
    if (currentStep !== safeStep) {
      setCurrentStep(safeStep)
    }
  }, [currentStep, safeStep, setCurrentStep])

  const uiStrings = resolveModeStrings(config, mode, step)
  const nextLabel = config?.nextLabel || 'Continue'
  const backLabel = config?.backLabel || 'Back'
  const submitLabel = config?.submitLabels?.[mode] || config?.submitLabel || 'Submit'

  const setFieldValue = (fieldId, fieldValue) => {
    setValues((previous) => ({ ...previous, [fieldId]: fieldValue }))
    setErrors((previous) => {
      const next = { ...previous }
      delete next[fieldId]
      return next
    })
  }

  const runFieldValidation = (field, value) => {
    if (typeof field?.showWhen === 'function' && !field.showWhen(values)) return null

    if (field?.required) {
      if (field.type === 'multi-select' && (!Array.isArray(value) || value.length === 0)) {
        return 'Please choose at least one option.'
      }

      if ((value === undefined || value === null || value === '') && value !== 0) {
        return `${field.label || 'This field'} is required.`
      }
    }

    if (typeof field?.validation === 'function') {
      return field.validation(value, values)
    }

    if (field?.type === 'multi-select') {
      const selected = Array.isArray(value) ? value.length : 0
      if (field.min && selected < field.min) {
        return `Select at least ${field.min} option${field.min > 1 ? 's' : ''}.`
      }
      if (field.max && selected > field.max) {
        return `Select at most ${field.max} option${field.max > 1 ? 's' : ''}.`
      }
    }

    return null
  }

  const validateCurrentStep = () => {
    const nextErrors = {}

    const validateList = (fieldList) => {
      fieldList.forEach((field) => {
        if (field.type === 'row' && Array.isArray(field.fields)) {
          validateList(field.fields)
          return
        }

        if (!field?.id) return
        const value = values[field.id]
        const maybeError = runFieldValidation(field, value)
        if (maybeError) nextErrors[field.id] = maybeError
      })
    }

    validateList(step.fields || [])
    setErrors((previous) => ({ ...previous, ...nextErrors }))
    return Object.keys(nextErrors).length === 0
  }

  const onFieldBlur = async (field) => {
    if (!field?.id || typeof field?.onBlur !== 'function') return
    const result = await field.onBlur(values[field.id], values)
    setMeta((previous) => ({ ...previous, [`${field.id}Meta`]: result }))
  }

  const runSubmit = async () => {
    setGlobalError('')
    if (!validateCurrentStep()) return

    const stepValues = normalizeValuesByFields(step.fields || [], values)
    if (typeof step?.onSubmit === 'function') {
      setSubmitting(true)
      const result = await step.onSubmit(stepValues, values)
      setSubmitting(false)

      if (!result?.success) {
        setGlobalError(result?.error || result?.message || 'Unable to continue.')
        return
      }
    }

    if (!isLastStep) {
      setCurrentStep((previous) => previous + 1)
      return
    }

    if (typeof config?.onFinalSubmit !== 'function') {
      if (onSuccess) onSuccess({ success: true, data: values })
      return
    }

    setSubmitting(true)
    const submitResult = await config.onFinalSubmit(values)
    setSubmitting(false)

    if (!submitResult?.success) {
      setGlobalError(submitResult?.error || submitResult?.message || 'Submission failed.')
      return
    }

    if (config?.terminal?.render) {
      setTerminalResult(submitResult)
      setShowTerminal(true)
      return
    }

    if (onSuccess) onSuccess(submitResult)
  }

  const onBack = () => {
    setGlobalError('')
    setCurrentStep((previous) => Math.max(0, previous - 1))
  }

  const resolveFooter = () => {
    if (config?.footers && mode && config.footers[mode]) {
      return config.footers[mode]
    }
    if (config?.footer) return config.footer
    return null
  }

  const renderField = (field) => {
    if (typeof field?.showWhen === 'function' && !field.showWhen(values)) return null

    if (field.type === 'row' && Array.isArray(field.fields)) {
      return (
        <motion.div
          key={field.id || field.label || JSON.stringify(field.fields.map((item) => item.id))}
          variants={FIELD_VARIANTS}
          style={{
            display: 'grid',
            gridTemplateColumns: field.columns || '1fr 1fr',
            gap: '12px',
          }}
        >
          {field.fields.map((nestedField) => renderField(nestedField))}
        </motion.div>
      )
    }

    const value = values[field.id] ?? (field.type === 'multi-select' ? [] : '')
    const error = errors[field.id]
    const Icon = field.icon ? ICON_MAP[field.icon] : null
    const AnswerComponent = resolveAnswerType(field.type)

    let inputNode = null
    if (field.type === 'password') {
      inputNode = (
        <PasswordInput
          id={field.id}
          value={value}
          onChange={(event) => setFieldValue(field.id, event.target.value)}
          error={error}
          placeholder={field.placeholder}
        />
      )
    } else if (field.type === 'textarea') {
      inputNode = (
        <textarea
          id={field.id}
          className="input"
          value={value}
          onChange={(event) => setFieldValue(field.id, event.target.value)}
          onBlur={() => onFieldBlur(field)}
          placeholder={field.placeholder}
          rows={4}
          style={{
            minHeight: '108px',
            resize: 'vertical',
            borderColor: error ? 'var(--color-error)' : 'var(--border-subtle)',
            backgroundColor: 'var(--bg-surface-elevated)',
          }}
        />
      )
    } else if (field.type === 'select') {
      inputNode = (
        <select
          id={field.id}
          className="input"
          value={value}
          onChange={(event) => setFieldValue(field.id, event.target.value)}
          onBlur={() => onFieldBlur(field)}
          style={{
            borderColor: error ? 'var(--color-error)' : 'var(--border-subtle)',
            backgroundColor: 'var(--bg-surface-elevated)',
          }}
        >
          <option value="">Select…</option>
          {(field.options || []).map((option) => {
            const optionValue = typeof option === 'string' ? option : option.value
            const optionLabel = typeof option === 'string' ? option : option.label
            return (
              <option key={optionValue} value={optionValue}>
                {optionLabel}
              </option>
            )
          })}
        </select>
      )
    } else if (field.type === 'custom' && typeof field.render === 'function') {
      inputNode = field.render(value, (next) => setFieldValue(field.id, next), error, values)
    } else if (AnswerComponent) {
      inputNode = (
        <AnswerComponent
          field={field}
          value={value}
          onChange={(next) => setFieldValue(field.id, next)}
          error={error}
          allValues={values}
        />
      )
    } else {
      inputNode = (
        <StyledInput
          id={field.id}
          type={field.type || 'text'}
          icon={Icon}
          value={value}
          onChange={(event) => setFieldValue(field.id, event.target.value)}
          onBlur={() => onFieldBlur(field)}
          placeholder={field.placeholder}
          error={error}
        />
      )
    }

    return (
      <motion.div key={field.id} variants={FIELD_VARIANTS}>
        <Field label={field.label} htmlFor={field.id} error={error}>
          {inputNode}
          {typeof field.renderMeta === 'function' ? field.renderMeta(meta[`${field.id}Meta`]) : null}
        </Field>
      </motion.div>
    )
  }

  if (showTerminal && config?.terminal?.render) {
    return config.terminal.render(terminalResult, () => {
      if (onSuccess) onSuccess(terminalResult)
    })
  }

  const footer = resolveFooter()

  return (
    <div className={className}>
      <div style={{ overflow: 'hidden', marginBottom: '8px' }}>
        <AnimatePresence mode="wait" initial={false}>
          <motion.h1
            key={`${mode || 'single'}-${safeStep}-title`}
            initial={{ y: '105%' }}
            animate={{ y: '0%' }}
            exit={{ y: '-105%' }}
            transition={{ duration: 0.32, ease: EASE }}
            style={{
              fontFamily: 'Clash Display, sans-serif',
              fontSize: '72px',
              lineHeight: 1.05,
              fontWeight: 700,
              letterSpacing: '-0.03em',
              color: 'var(--text-primary)',
              margin: 0,
            }}
          >
            {uiStrings.title}
          </motion.h1>
        </AnimatePresence>
      </div>

      <AnimatePresence mode="wait" initial={false}>
        <motion.p
          key={`${mode || 'single'}-${safeStep}-sub`}
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          exit={{ opacity: 0 }}
          transition={{ duration: 0.22, ease: EASE }}
          className="text-body"
          style={{ color: 'var(--text-secondary)', margin: '0 0 32px' }}
        >
          {uiStrings.subtitle}
        </motion.p>
      </AnimatePresence>

      <AnimatePresence initial={false}>
        {globalError ? (
          <motion.div
            key="global-error"
            role="alert"
            initial={{ opacity: 0, height: 0 }}
            animate={{ opacity: 1, height: 'auto' }}
            exit={{ opacity: 0, height: 0 }}
            transition={{ duration: 0.2, ease: EASE }}
            style={{
              overflow: 'hidden',
              color: 'var(--color-error)',
              padding: '10px 14px',
              borderRadius: '8px',
              border: '1px solid var(--color-error)',
              backgroundColor: 'color-mix(in srgb, var(--color-error) 10%, transparent)',
              marginBottom: '16px',
            }}
            className="text-small"
          >
            {globalError}
          </motion.div>
        ) : null}
      </AnimatePresence>

      <AnimatePresence mode="wait" initial={false}>
        <motion.div
          key={`fields-${safeStep}`}
          variants={FIELD_CONTAINER_VARIANTS}
          initial="hidden"
          animate="visible"
          exit="exit"
          style={{ display: 'flex', flexDirection: 'column', gap: '16px' }}
        >
          {(step.fields || []).map((field) => renderField(field))}
        </motion.div>
      </AnimatePresence>

      <div
        style={{
          marginTop: '18px',
          display: 'flex',
          gap: '12px',
          alignItems: 'center',
          justifyContent: 'space-between',
        }}
      >
        <button
          type="button"
          className="btn btn-secondary"
          onClick={onBack}
          disabled={safeStep === 0 || submitting}
          style={{ opacity: safeStep === 0 ? 0.45 : 1 }}
        >
          {backLabel}
        </button>

        <SubmitButton
          loading={submitting}
          label={isLastStep ? submitLabel : nextLabel}
          onClick={runSubmit}
          fullWidth={false}
        />
      </div>

      {footer ? (
        <p
          className="text-body"
          style={{
            marginTop: '24px',
            textAlign: 'center',
            color: 'var(--text-secondary)',
          }}
        >
          {footer.text}{' '}
          {footer.linkAction ? (
            <ModeToggleLink onClick={() => footer.linkAction(setMode)}>
              {footer.linkText}
            </ModeToggleLink>
          ) : (
            <Link to={footer.linkTo || '/'} className="text-accent">
              {footer.linkText}
            </Link>
          )}
        </p>
      ) : null}

      {config?.backLink ? (
        <div style={{ marginTop: '32px', textAlign: 'center' }}>
          <Link className="text-small text-muted" to={config.backLink.to}>
            {config.backLink.label}
          </Link>
        </div>
      ) : null}

      {totalSteps > 1 ? (
        <p className="text-small text-muted" style={{ marginTop: '14px', textAlign: 'center' }}>
          Step {safeStep + 1} of {totalSteps}
        </p>
      ) : null}
    </div>
  )
}
