import { Chip } from './Chip'

export function InterestChip({ label, selected = false, onToggle }) {
  return (
    <Chip
      label={label}
      selected={selected}
      onClick={() => onToggle?.(!selected)}
    />
  )
}
