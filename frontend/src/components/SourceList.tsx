import { Database } from 'lucide-react'

// The backend doesn't attach citations to ChatResponse today (see
// backend/schema/chat.py) — this infers which knowledge domains a
// reply most likely drew on from the same `intent`/`marketplace`
// metadata the response already carries. If the backend starts
// returning real citations later, pass them in and they win outright.
const SOURCES_FOR_INTENT: Record<string, string[]> = {
  create_listing: ['Listing Guidelines', 'SellerOS Knowledge Base'],
  update_listing: ['Listing Guidelines', 'SellerOS Knowledge Base'],
  pricing: ['Pricing Rules', 'SellerOS Knowledge Base'],
  inventory: ['Inventory Documents'],
  orders: ['Order Records'],
  analytics: ['Sales Analytics Data'],
  forecasting: ['Historical Sales Data'],
  profitability: ['Cost & Margin Data'],
  competitor: ['Marketplace Intelligence'],
  campaign: ['Marketing Playbooks'],
  ads: ['Marketing Playbooks'],
  seo: ['SEO Knowledge Base'],
  content: ['Content Guidelines'],
  seller_coach: ['SellerOS Knowledge Base'],
  sustainability: ['Government Guidelines', 'Sustainability Standards'],
}

const MARKETPLACE_SOURCE: Record<string, string> = {
  amazon: 'Amazon Policies',
  flipkart: 'Flipkart Policies',
  meesho: 'Meesho Policies',
}

export function inferSources(intent: string[] | undefined, marketplace: string | null | undefined): string[] {
  const sources = new Set<string>()
  for (const i of intent ?? []) {
    for (const s of SOURCES_FOR_INTENT[i] ?? []) sources.add(s)
  }
  if (marketplace && MARKETPLACE_SOURCE[marketplace]) sources.add(MARKETPLACE_SOURCE[marketplace])
  if (sources.size === 0) sources.add('SellerOS Knowledge Base')
  return Array.from(sources)
}

export default function SourceList({ sources }: { sources: string[] }) {
  if (sources.length === 0) return null
  return (
    <div className="mt-1.5 text-[11px] text-faint">
      <div className="flex items-center gap-1 mb-1 font-medium">
        <Database size={11} />
        Knowledge Sources
      </div>
      <div className="flex flex-wrap gap-1">
        {sources.map(s => (
          <span key={s} className="px-1.5 py-0.5 rounded bg-surface border border-app text-dim">{s}</span>
        ))}
      </div>
    </div>
  )
}
