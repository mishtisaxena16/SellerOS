import type { ExchangeStatus } from './StatusBadge'

// Maps the `intent` list the backend already returns on ChatResponse
// (backend/ai/orchestrator_layer/orchestrator.py: INTENT_KEYWORDS /
// AGENT_FOR_INTENT) to a display identity for whichever specialized
// agent actually produced the reply. Falls back to Seller Coach for an
// empty/unknown intent — the same default IntentRouter.select_agent()
// uses server-side — so the badge never has to guess wildly.
//
// Only 5 accent colors exist in index.css (blue/green/purple/amber/red)
// so several agents intentionally share a color and differ by emoji —
// no new CSS tokens were added for this phase.
export interface AgentInfo {
  key: string
  name: string
  emoji: string
  colorClass: string
  softClass: string
}

const AGENT_INFO: Record<string, AgentInfo> = {
  create_listing: { key: 'listing', name: 'Listing Agent', emoji: '📋', colorClass: 'text-accent-blue', softClass: 'bg-accent-blue-soft' },
  update_listing: { key: 'listing', name: 'Listing Agent', emoji: '📋', colorClass: 'text-accent-blue', softClass: 'bg-accent-blue-soft' },
  pricing: { key: 'pricing', name: 'Pricing Agent', emoji: '💰', colorClass: 'text-accent-green', softClass: 'bg-accent-green-soft' },
  inventory: { key: 'inventory', name: 'Inventory Agent', emoji: '📦', colorClass: 'text-accent-amber', softClass: 'bg-accent-amber-soft' },
  orders: { key: 'orders', name: 'Orders Agent', emoji: '🧾', colorClass: 'text-accent-amber', softClass: 'bg-accent-amber-soft' },
  analytics: { key: 'analytics', name: 'Analytics Agent', emoji: '📊', colorClass: 'text-accent-blue', softClass: 'bg-accent-blue-soft' },
  forecasting: { key: 'forecast', name: 'Forecasting Agent', emoji: '📈', colorClass: 'text-accent-purple', softClass: 'bg-accent-purple-soft' },
  profitability: { key: 'profitability', name: 'Profitability Agent', emoji: '📊', colorClass: 'text-accent-blue', softClass: 'bg-accent-blue-soft' },
  competitor: { key: 'competitor', name: 'Competitor Agent', emoji: '🔍', colorClass: 'text-accent-purple', softClass: 'bg-accent-purple-soft' },
  campaign: { key: 'campaign', name: 'Marketing Hub', emoji: '📅', colorClass: 'text-accent-purple', softClass: 'bg-accent-purple-soft' },
  ads: { key: 'ads', name: 'Ads Agent', emoji: '📢', colorClass: 'text-accent-amber', softClass: 'bg-accent-amber-soft' },
  seo: { key: 'seo', name: 'SEO Agent', emoji: '🔎', colorClass: 'text-accent-green', softClass: 'bg-accent-green-soft' },
  content: { key: 'content', name: 'Content Agent', emoji: '✍️', colorClass: 'text-accent-blue', softClass: 'bg-accent-blue-soft' },
  seller_coach: { key: 'seller_coach', name: 'Seller Coach', emoji: '🎓', colorClass: 'text-accent-purple', softClass: 'bg-accent-purple-soft' },
  sustainability: { key: 'sustainability', name: 'Sustainability Agent', emoji: '🌱', colorClass: 'text-accent-green', softClass: 'bg-accent-green-soft' },
}

const FALLBACK_AGENT: AgentInfo = AGENT_INFO.seller_coach

// Synthetic identity for a guardrail block — the specialized agent
// never actually got to run, so attributing the reply to it would be
// misleading. The Guardrails layer (backend/ai/guardrails_layer) is
// what produced this response, hence "Policy Agent".
const POLICY_AGENT: AgentInfo = { key: 'policy', name: 'Policy Agent', emoji: '⚖️', colorClass: 'text-accent-red', softClass: 'bg-accent-red-soft' }

// If the backend ever starts sending an explicit agent name directly,
// prefer it outright — this lookup only runs when we have to infer.
export function inferAgent(intent: string[] | undefined, status: ExchangeStatus, agentName?: string | null): AgentInfo {
  if (status === 'blocked') return POLICY_AGENT
  if (agentName) {
    const known = Object.values(AGENT_INFO).find(a => a.name === agentName || a.key === agentName)
    if (known) return known
    return { ...FALLBACK_AGENT, name: agentName }
  }
  const primary = intent?.find(i => AGENT_INFO[i])
  return primary ? AGENT_INFO[primary] : FALLBACK_AGENT
}

export type ResponseType =
  | 'Analysis' | 'Recommendation' | 'Prediction' | 'Knowledge Retrieval'
  | 'Action Plan' | 'Troubleshooting' | 'Information' | 'Decision Support'

const RESPONSE_TYPE_FOR_INTENT: Record<string, ResponseType> = {
  create_listing: 'Action Plan',
  update_listing: 'Action Plan',
  pricing: 'Recommendation',
  inventory: 'Information',
  orders: 'Information',
  analytics: 'Analysis',
  forecasting: 'Prediction',
  profitability: 'Analysis',
  competitor: 'Analysis',
  campaign: 'Action Plan',
  ads: 'Action Plan',
  seo: 'Recommendation',
  content: 'Recommendation',
  seller_coach: 'Decision Support',
  sustainability: 'Knowledge Retrieval',
}

export function inferResponseType(intent: string[] | undefined, status: ExchangeStatus): ResponseType {
  if (status === 'blocked') return 'Troubleshooting'
  const primary = intent?.find(i => RESPONSE_TYPE_FOR_INTENT[i])
  if (primary) return RESPONSE_TYPE_FOR_INTENT[primary]
  return 'Information'
}

export default function AgentBadge({ agent }: { agent: AgentInfo }) {
  return (
    <span className={`inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-[10.5px] font-medium ${agent.colorClass} ${agent.softClass}`}>
      <span aria-hidden="true">{agent.emoji}</span>
      {agent.name}
    </span>
  )
}

export function ResponseTypeChip({ type }: { type: ResponseType }) {
  return (
    <span className="inline-flex items-center px-2 py-0.5 rounded-full text-[10.5px] font-medium text-dim bg-hover border border-app">
      {type}
    </span>
  )
}
