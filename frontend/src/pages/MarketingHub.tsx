import { useState } from 'react'
import { Megaphone, TrendingUp, Eye, MousePointer, Target, Plus, Sparkles } from 'lucide-react'

const campaigns = [
  { id: 1, name: 'Kitchen Summer Sale', type: 'Sponsored Products', marketplace: 'Amazon', status: 'active', budget: 5000, spent: 3240, impressions: 284000, clicks: 4820, orders: 142, acos: 22.8, roas: 4.4 },
  { id: 2, name: 'Eco Living Collection', type: 'Display Ads', marketplace: 'Flipkart', status: 'active', budget: 3000, spent: 1890, impressions: 156000, clicks: 2340, orders: 68, acos: 27.8, roas: 3.6 },
  { id: 3, name: 'Bamboo Products Flash', type: 'Sponsored Products', marketplace: 'Amazon', status: 'paused', budget: 2000, spent: 2000, impressions: 98000, clicks: 1620, orders: 48, acos: 41.7, roas: 2.4 },
  { id: 4, name: 'Meesho Value Drive', type: 'Coupon', marketplace: 'Meesho', status: 'active', budget: 1500, spent: 820, impressions: 72000, clicks: 1840, orders: 76, acos: 10.8, roas: 9.3 },
  { id: 5, name: 'Kitchen Tool Bundle', type: 'Sponsored Brands', marketplace: 'Amazon', status: 'scheduled', budget: 4000, spent: 0, impressions: 0, clicks: 0, orders: 0, acos: 0, roas: 0 },
]

const keywords = [
  { keyword: 'bamboo kitchen organizer', bid: 24, impressions: 48200, ctr: 3.2, conv: 8.4 },
  { keyword: 'spice rack countertop', bid: 18, impressions: 32400, ctr: 4.1, conv: 9.2 },
  { keyword: 'eco kitchen storage', bid: 15, impressions: 28600, ctr: 2.8, conv: 7.1 },
  { keyword: 'wooden serving board', bid: 21, impressions: 19800, ctr: 3.9, conv: 11.2 },
  { keyword: 'bamboo cutting board', bid: 19, impressions: 24100, ctr: 3.5, conv: 8.8 },
]

const statusColor = {
  active: 'bg-emerald-50 text-emerald-600',
  paused: 'bg-gray-100 text-gray-500',
  scheduled: 'bg-blue-50 text-blue-600',
}

export default function MarketingHub() {
  const [tab, setTab] = useState<'campaigns' | 'keywords' | 'promotions'>('campaigns')

  const totalSpent = campaigns.reduce((s, c) => s + c.spent, 0)
  const totalImpressions = campaigns.reduce((s, c) => s + c.impressions, 0)
  const totalClicks = campaigns.reduce((s, c) => s + c.clicks, 0)
  const totalOrders = campaigns.reduce((s, c) => s + c.orders, 0)

  return (
    <div className="p-6 fade-in">
      <div className="flex items-center justify-between mb-6">
        <div>
          <h2 className="text-xl font-bold text-gray-900">Marketing Hub</h2>
          <p className="text-[13px] text-gray-500 mt-0.5">Manage campaigns across Amazon, Flipkart & Meesho</p>
        </div>
        <button className="flex items-center gap-2 px-4 py-2 bg-primary text-white text-[13px] font-medium rounded-lg hover:bg-primary-hover transition-colors">
          <Plus size={14} /> New Campaign
        </button>
      </div>

      {/* KPIs */}
      <div className="grid grid-cols-4 gap-4 mb-6">
        {[
          { label: 'Ad Spend', value: `₹${totalSpent.toLocaleString('en-IN')}`, sub: 'this month', icon: Target, color: 'bg-red-50 text-red-500' },
          { label: 'Impressions', value: `${(totalImpressions/1000).toFixed(0)}K`, sub: 'total reach', icon: Eye, color: 'bg-blue-50 text-blue-600' },
          { label: 'Clicks', value: totalClicks.toLocaleString(), sub: 'CTR 3.2%', icon: MousePointer, color: 'bg-amber-50 text-amber-600' },
          { label: 'Ad Orders', value: totalOrders, sub: 'Conv. 6.8%', icon: TrendingUp, color: 'bg-emerald-50 text-emerald-600' },
        ].map(({ label, value, sub, icon: Icon, color }) => (
          <div key={label} className="bg-white rounded-xl border border-gray-100 p-4">
            <div className={`w-9 h-9 rounded-lg flex items-center justify-center mb-3 ${color}`}><Icon size={16} /></div>
            <div className="text-2xl font-bold text-gray-900">{value}</div>
            <div className="text-[12px] text-gray-500">{label}</div>
            <div className="text-[11px] text-gray-400">{sub}</div>
          </div>
        ))}
      </div>

      {/* Tabs */}
      <div className="flex gap-1 mb-5 bg-gray-100 p-1 rounded-lg w-fit">
        {(['campaigns', 'keywords', 'promotions'] as const).map(t => (
          <button key={t} onClick={() => setTab(t)}
            className={`px-4 py-1.5 text-[13px] font-medium rounded-md capitalize transition-colors ${tab === t ? 'bg-white text-gray-900 shadow-sm' : 'text-gray-500 hover:text-gray-700'}`}>
            {t}
          </button>
        ))}
      </div>

      {tab === 'campaigns' && (
        <div className="bg-white rounded-xl border border-gray-100 overflow-hidden">
          <table className="w-full">
            <thead>
              <tr className="border-b border-gray-100">
                {['Campaign', 'Type', 'Platform', 'Budget', 'Spent', 'Impressions', 'Clicks', 'Orders', 'ACOS', 'ROAS', 'Status'].map(h => (
                  <th key={h} className="text-left px-4 py-3 text-[11.5px] font-semibold text-gray-500 uppercase tracking-wide whitespace-nowrap">{h}</th>
                ))}
              </tr>
            </thead>
            <tbody>
              {campaigns.map(c => (
                <tr key={c.id} className="border-b border-gray-50 hover:bg-gray-50/50 transition-colors">
                  <td className="px-4 py-3.5"><span className="text-[13px] font-medium text-gray-900">{c.name}</span></td>
                  <td className="px-4 py-3.5"><span className="text-[12px] text-gray-500">{c.type}</span></td>
                  <td className="px-4 py-3.5"><span className="badge bg-gray-100 text-gray-600">{c.marketplace}</span></td>
                  <td className="px-4 py-3.5"><span className="text-[12.5px] text-gray-700">₹{c.budget.toLocaleString()}</span></td>
                  <td className="px-4 py-3.5">
                    <div>
                      <span className="text-[12.5px] font-medium text-gray-900">₹{c.spent.toLocaleString()}</span>
                      <div className="mt-1 h-1 bg-gray-100 rounded-full w-16 overflow-hidden">
                        <div className="h-full bg-primary rounded-full" style={{ width: `${(c.spent/c.budget)*100}%` }} />
                      </div>
                    </div>
                  </td>
                  <td className="px-4 py-3.5"><span className="text-[12.5px] text-gray-700">{(c.impressions/1000).toFixed(0)}K</span></td>
                  <td className="px-4 py-3.5"><span className="text-[12.5px] text-gray-700">{c.clicks.toLocaleString()}</span></td>
                  <td className="px-4 py-3.5"><span className="text-[12.5px] font-semibold text-gray-900">{c.orders}</span></td>
                  <td className="px-4 py-3.5">
                    <span className={`text-[12.5px] font-medium ${c.acos < 25 ? 'text-emerald-600' : c.acos < 35 ? 'text-amber-600' : 'text-red-500'}`}>
                      {c.acos > 0 ? `${c.acos}%` : '—'}
                    </span>
                  </td>
                  <td className="px-4 py-3.5">
                    <span className={`text-[12.5px] font-medium ${c.roas >= 4 ? 'text-emerald-600' : c.roas >= 2.5 ? 'text-amber-600' : 'text-red-500'}`}>
                      {c.roas > 0 ? `${c.roas}x` : '—'}
                    </span>
                  </td>
                  <td className="px-4 py-3.5">
                    <span className={`badge ${statusColor[c.status as keyof typeof statusColor] || 'bg-gray-100 text-gray-600'} capitalize`}>{c.status}</span>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}

      {tab === 'keywords' && (
        <div className="bg-white rounded-xl border border-gray-100 overflow-hidden">
          <div className="px-5 py-4 border-b border-gray-100 flex items-center gap-2">
            <Sparkles size={15} className="text-primary" />
            <h3 className="text-[13.5px] font-semibold text-gray-900">Keyword Performance</h3>
          </div>
          <table className="w-full">
            <thead>
              <tr className="border-b border-gray-100">
                {['Keyword', 'Bid (₹)', 'Impressions', 'CTR', 'Conv. Rate', 'Performance'].map(h => (
                  <th key={h} className="text-left px-5 py-3 text-[11.5px] font-semibold text-gray-500 uppercase tracking-wide">{h}</th>
                ))}
              </tr>
            </thead>
            <tbody>
              {keywords.map(kw => (
                <tr key={kw.keyword} className="border-b border-gray-50 hover:bg-gray-50/50 transition-colors">
                  <td className="px-5 py-3.5"><span className="text-[13px] font-medium text-gray-800">{kw.keyword}</span></td>
                  <td className="px-5 py-3.5"><span className="text-[12.5px] text-gray-700">₹{kw.bid}</span></td>
                  <td className="px-5 py-3.5"><span className="text-[12.5px] text-gray-700">{(kw.impressions/1000).toFixed(1)}K</span></td>
                  <td className="px-5 py-3.5"><span className={`text-[12.5px] font-medium ${kw.ctr >= 3.5 ? 'text-emerald-600' : 'text-amber-600'}`}>{kw.ctr}%</span></td>
                  <td className="px-5 py-3.5"><span className={`text-[12.5px] font-medium ${kw.conv >= 9 ? 'text-emerald-600' : 'text-amber-600'}`}>{kw.conv}%</span></td>
                  <td className="px-5 py-3.5">
                    <div className="h-1.5 bg-gray-100 rounded-full w-24 overflow-hidden">
                      <div className={`h-full rounded-full ${kw.conv >= 9 ? 'bg-emerald-400' : 'bg-amber-400'}`} style={{ width: `${(kw.conv/12)*100}%` }} />
                    </div>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}

      {tab === 'promotions' && (
        <div className="grid grid-cols-3 gap-4">
          {[
            { title: 'Flash Sale — Kitchen Essentials', discount: '25% OFF', ends: 'Jul 25, 2026', status: 'active', platforms: ['Amazon', 'Flipkart'] },
            { title: 'Eco Bundle Deal', discount: '₹200 OFF on ₹1500+', ends: 'Jul 31, 2026', status: 'active', platforms: ['Meesho'] },
            { title: 'Monsoon Clearance', discount: '30–40% OFF', ends: 'Aug 5, 2026', status: 'scheduled', platforms: ['Amazon', 'Flipkart', 'Meesho'] },
          ].map(promo => (
            <div key={promo.title} className="bg-white rounded-xl border border-gray-100 p-5">
              <div className="flex items-start justify-between mb-3">
                <Megaphone size={18} className="text-primary" />
                <span className={`badge ${promo.status === 'active' ? 'bg-emerald-50 text-emerald-600' : 'bg-blue-50 text-blue-600'}`}>{promo.status}</span>
              </div>
              <h4 className="text-[13.5px] font-semibold text-gray-900 mb-1">{promo.title}</h4>
              <div className="text-[22px] font-bold text-primary mb-2">{promo.discount}</div>
              <div className="text-[12px] text-gray-500 mb-3">Ends: {promo.ends}</div>
              <div className="flex gap-1 flex-wrap">
                {promo.platforms.map(p => <span key={p} className="badge bg-gray-100 text-gray-600">{p}</span>)}
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  )
}
