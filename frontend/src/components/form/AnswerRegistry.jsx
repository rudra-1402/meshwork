const ANSWER_REGISTRY = {}

export function registerAnswerType(type, component) {
  if (!type || typeof type !== 'string') return
  ANSWER_REGISTRY[type] = component
}

export function unregisterAnswerType(type) {
  if (!type || typeof type !== 'string') return
  delete ANSWER_REGISTRY[type]
}

export function resolveAnswerType(type) {
  return ANSWER_REGISTRY[type] ?? null
}
