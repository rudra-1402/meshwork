import { createContext, useContext, useMemo, useState } from 'react'

const FormStepContext = createContext(null)

export function FormStepProvider({ config, children }) {
  const totalSteps = Array.isArray(config?.steps) ? config.steps.length : 0
  const [currentStep, setCurrentStep] = useState(0)
  const [mode, setMode] = useState(config?.defaultMode ?? null)

  const value = useMemo(() => ({
    currentStep,
    totalSteps,
    mode,
    setCurrentStep,
    setMode,
  }), [currentStep, totalSteps, mode])

  return (
    <FormStepContext.Provider value={value}>
      {children}
    </FormStepContext.Provider>
  )
}

export function useFormStepContext() {
  const context = useContext(FormStepContext)
  if (!context) {
    throw new Error('useFormStepContext must be used within FormStepProvider')
  }
  return context
}
