import { useState } from 'react'
import { Megaphone, Target, Search, PenLine, AlertCircle } from 'lucide-react'
import MarketingConsole from '../components/MarketingConsole'

// The backend's campaign/ads connector layer has no fetchers wired
// yet (CAMPAIGN_FETCHERS is empty in marketplace_connector.py), so
// there's no real spend/impressions/ACOS/ROAS data to show — the old
// table of campaigns was entirely invented. What IS real: campaign
// strategy, ad copy, and SEO planning through the marketing agents
// (campaign_agent, ads_agent, seo_agent, content_agent) via /chat.
const TABS = [
  { id: 'campaign', label: 'Campaign Strategy' },
  { id: 'ads', label: 'Ads' },
  { id: 'seo', label: 'SEO & Content' },
] as const

type TabId = typeof TABS[number]['id']

export default function MarketingHub() {
  const [tab, setTab] = useState<TabId>('campaign')

  return (
    <div className="p-6 fade-in space-y-6">
      <div>
        <h2 className="text-xl font-bold text-app flex items-center gap-2">
          <Megaphone size={22} className="text-accent-blue" />
          Marketing Hub
        </h2>
        <p className="text-[13px] text-dim mt-0.5">Plan campaigns, ads, and content with your live AI marketing agents.</p>
      </div>

      <div className="flex gap-1 bg-surface p-1 rounded-lg w-fit">
        {TABS.map(t => (
          <button key={t.id} onClick={() => setTab(t.id)}
            className={`px-4 py-1.5 text-[13px] font-medium rounded-md transition-colors ${tab === t.id ? 'bg-elev text-app shadow-sm' : 'text-dim hover:text-dim'}`}>
            {t.label}
          </button>
        ))}
      </div>

      {tab === 'campaign' && (
        <MarketingConsole
          title="Campaign Strategy"
          description="Plan promotions and campaign calendars across marketplaces"
          icon={Target}
          iconColor="bg-accent-red-soft text-accent-red"
          sessionKey="marketing-campaign"
          placeholder="Describe the campaign you want to plan…"
          emptyHint="Try describing a promotion idea and ask for a campaign plan, or ask what's working well right now."
          quickPrompts={[
            { label: 'Plan a festive campaign', prompt: 'Help me plan a marketing campaign for the upcoming festive season.' },
            { label: 'Campaign calendar', prompt: 'Suggest a campaign calendar for the next quarter.' },
          ]}
        />
      )}

      {tab === 'ads' && (
        <MarketingConsole
          title="Ads"
          description="Sponsored listings, ad spend, and bidding strategy"
          icon={Megaphone}
          iconColor="bg-accent-amber-soft text-accent-amber"
          sessionKey="marketing-ads"
          placeholder="Ask about running or optimizing ads…"
          emptyHint="Try asking how to set up sponsored listings or how to improve ad spend efficiency."
          quickPrompts={[
            { label: 'Run a sponsored listing', prompt: 'Help me run a sponsored listing ad for my top product.' },
            { label: 'Improve ad spend efficiency', prompt: 'How can I improve my ad spend efficiency?' },
          ]}
        />
      )}

      {tab === 'seo' && (
        <div className="grid grid-cols-1 xl:grid-cols-2 gap-5">
          <MarketingConsole
            title="SEO"
            description="Keyword strategy and search visibility"
            icon={Search}
            iconColor="bg-accent-blue-soft text-accent-blue"
            sessionKey="marketing-seo"
            placeholder="Ask about keywords or search ranking…"
            quickPrompts={[
              { label: 'Improve search ranking', prompt: 'How can I improve my search ranking with better SEO?' },
              { label: 'Keyword suggestions', prompt: 'Suggest keywords to improve visibility for my listings.' },
            ]}
          />
          <MarketingConsole
            title="Content"
            description="Product descriptions and marketing copy"
            icon={PenLine}
            iconColor="bg-accent-purple-soft text-accent-purple"
            sessionKey="marketing-content"
            placeholder="Ask for marketing copy or a product description…"
            quickPrompts={[
              { label: 'Write a product description', prompt: 'Write a product description for my bamboo spice rack.' },
              { label: 'Write ad caption', prompt: 'Write marketing copy for a social media caption promoting my kitchen products.' },
            ]}
          />
        </div>
      )}

      <div className="card p-4 flex items-start gap-3">
        <AlertCircle size={16} className="text-accent-amber flex-shrink-0 mt-0.5" />
        <p className="text-[12.5px] text-dim">
          Structured campaign metrics (spend, impressions, ACOS, ROAS) aren't available yet — the backend's ad/campaign
          connectors aren't wired to a live marketplace feed. This page gives real strategy and copy from the marketing
          agents instead of fabricated numbers.
        </p>
      </div>
    </div>
  )
}
