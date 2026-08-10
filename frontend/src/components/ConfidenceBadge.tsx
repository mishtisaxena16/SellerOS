import type { ExchangeStatus } from './StatusBadge'

// Confidence is derived, never random (Phase 4 spec §3), from signals
// already present on ChatResponse — there is no model-reported score to
// read, so this approximates one from:
//   • retrieval quality   → how many intents were actually resolved vs "unknown"
//   • amount of evidence  → length/substance of the final response text
//   • guardrail certainty → whether guardrails raised any findings at all
//   • completeness        → whether every detected intent was implementable
export interface ConfidenceInput {
  responseLength: number
  intentCount: number
  guardrailFindingsCount: number
  unimplementedCount: number
  status: ExchangeStatus
}

export interface Confidence {
  score: number
  label: 'High' | 'Medium' | 'Low'
}

export function computeConfidence(input: ConfidenceInput): Confidence {
  let score = 90

  // Retrieval quality: no recognizable intent at all means the router
  // fell back to a generic agent rather than a targeted one.
  if (input.intentCount === 0) score -= 20
  else if (input.intentCount > 1) score += Math.min(input.intentCount - 1, 3) * 3

  // Amount of evidence: very short replies rarely carry much substance.
  if (input.responseLength < 40) score -= 18
  else if (input.responseLength < 120) score -= 6
  else if (input.responseLength > 400) score += 4

  // Guardrail certainty: each finding is the guardrail layer flagging
  // something it wasn't fully sure about.
  score -= Math.min(input.guardrailFindingsCount, 4) * 8

  // Completeness: parts of the request the platform can't act on yet.
  score -= Math.min(input.unimplementedCount, 3) * 12

  if (input.status === 'blocked') score -= 15
  if (input.status === 'requires_approval') score -= 5

  score = Math.max(30, Math.min(98, Math.round(score)))
  const label: Confidence['label'] = score >= 85 ? 'High' : score >= 60 ? 'Medium' : 'Low'
  return { score, label }
}

const LABEL_CLASSES: Record<Confidence['label'], { text: string; bg: string }> = {
  High: { text: 'text-accent-green', bg: 'bg-accent-green-soft' },
  Medium: { text: 'text-accent-amber', bg: 'bg-accent-amber-soft' },
  Low: { text: 'text-accent-red', bg: 'bg-accent-red-soft' },
}

export default function ConfidenceBadge({ confidence }: { confidence: Confidence }) {
  const classes = LABEL_CLASSES[confidence.label]
  return (
    <span
      className={`inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-[10.5px] font-medium ${classes.text} ${classes.bg}`}
      title={`Confidence ${confidence.score}% (${confidence.label})`}
    >
      Confidence {confidence.score}% · {confidence.label}
    </span>
  )
}
