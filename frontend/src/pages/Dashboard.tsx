import { useState } from 'react'
import {
  AreaChart, Area, BarChart, Bar, XAxis, YAxis, CartesianGrid,
  Tooltip, ResponsiveContainer, PieChart, Pie, Cell
} from 'recharts'
import {
  TrendingUp, TrendingDown, Package, ShoppingBag, Star,
  RotateCcw, Sparkles, ArrowRight, AlertCircle, CheckCircle
} from 'lucide-react'

const revenueData = [
  { day: 'Jul 1', amazon: 28400, flipkart: 16200, meesho: 9800 },
  { day: 'Jul 5', amazon: 31200, flipkart: 18400, meesho: 11200 },
  { day: 'Jul 10', amazon: 29800, flipkart: 17100, meesho: 10400 },
  { day: 'Jul 15', amazon: 35600, flipkart: 21300, meesho: 13600 },
  { day: 'Jul 20', amazon: 38900, flipkart: 23800, meesho: 15100 },
  { day: 'Jul 22', amazon: 41200, flipkart: 25400, meesho: 16800 },
]

const ordersData = [
  { month: 'Feb', orders: 1240 },
  { month: 'Mar', orders: 1480 },
  { month: 'Apr', orders: 1620 },
  { month: 'May', orders: 1890 },
  { month: 'Jun', orders: 2140 },
  { month: 'Jul', orders: 2380 },
]

const categoryData = [
  { name: 'Kitchen', value: 38, color: '#5B5BD6' },
  { name: 'Home Decor', value: 27, color: '#8B5CF6' },
  { name: 'Garden', value: 18, color: '#06B6D4' },
  { name: 'Storage', value: 17, color: '#10B981' },
]

const recentActivity = [
  { type: 'order', text: 'New order #ORD-4891 on Amazon', sub: 'Bamboo Spice Rack × 2 — ₹1,298', time: '2m ago', color: 'text-emerald-500' },
  { type: 'alert', text: 'Low stock alert: Wooden Serving Board', sub: '6 units remaining · Est. 5 days', time: '18m ago', color: 'text-amber-500' },
  { type: 'order', text: 'New order #ORD-4890 on Flipkart', sub: 'Kitchen Tool Set × 1 — ₹849', time: '34m ago', color: 'text-emerald-500' },
  { type: 'ai', text: 'AI optimization applied to 3 listings', sub: 'Avg. SEO score improved: 68 → 84', time: '1h ago', color: 'text-primary' },
  { type: 'order', text: 'Order #ORD-4889 delivered (Meesho)', sub: 'Bamboo Storage Box — Rating pending', time: '2h ago', color: 'text-blue-500' },
]

const aiInsights = [
  { icon: AlertCircle, color: 'text-amber-500 bg-amber-50', title: 'Stock Risk', desc: '3 bestsellers will run out in <7 days. Reorder now to avoid lost sales of ~₹48,000.' },
  { icon: TrendingUp, color: 'text-emerald-500 bg-emerald-50', title: 'Price Opportunity', desc: 'Competitors raised prices on bamboo organizers. You can increase by ₹80–120 without hurting conversion.' },
  { icon: Sparkles, color: 'text-primary bg-primary-50', title: 'Keyword Trend', desc: '"eco-friendly kitchen" searches up 340% this week. Update 4 listings to capture this demand.' },
  { icon: CheckCircle, color: 'text-blue-500 bg-blue-50', title: 'Performance', desc: 'Your Flipkart rating improved to 4.8★. Amazon Buy Box win rate is at 94% — excellent.' },
]

function KPICard({
  label, value, change, positive, icon: Icon, color
}: {
  label: string; value: string; change: string; positive: boolean; icon: any; color: string
}) {
  return (
    <div className="card-hover bg-white rounded-xl border border-gray-100 p-5">
      <div className="flex items-start justify-between mb-3">
        <div className={`w-9 h-9 rounded-lg flex items-center justify-center ${color}`}>
          <Icon size={18} />
        </div>
        <span className={`flex items-center gap-1 text-[12px] font-medium ${positive ? 'text-emerald-600' : 'text-red-500'}`}>
          {positive ? <TrendingUp size={13} /> : <TrendingDown size={13} />}
          {change}
        </span>
      </div>
      <div className="text-2xl font-bold text-gray-900 mb-0.5">{value}</div>
      <div className="text-[12.5px] text-gray-500">{label}</div>
    </div>
  )
}

export default function Dashboard() {
  const [revenueRange, setRevenueRange] = useState('7d')

  return (
    <div className="p-6 space-y-6 fade-in">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-xl font-bold text-gray-900">Good morning, Rahul 👋</h2>
          <p className="text-[13px] text-gray-500 mt-0.5">Here's what's happening with your stores today.</p>
        </div>
        <div className="flex items-center gap-2">
          {['7d', '30d', '90d'].map(r => (
            <button key={r} onClick={() => setRevenueRange(r)}
              className={`px-3 py-1.5 rounded-lg text-[12.5px] font-medium transition-colors ${
                revenueRange === r ? 'bg-primary text-white' : 'bg-white border border-gray-200 text-gray-600 hover:bg-gray-50'
              }`}>{r}</button>
          ))}
        </div>
      </div>

      {/* KPI cards */}
      <div className="grid grid-cols-2 lg:grid-cols-3 xl:grid-cols-6 gap-4">
        <KPICard label="Total Revenue" value="₹83.4L" change="+22.4%" positive icon={TrendingUp} color="bg-primary-50 text-primary" />
        <KPICard label="Total Orders" value="2,381" change="+18.7%" positive icon={ShoppingBag} color="bg-emerald-50 text-emerald-600" />
        <KPICard label="GMV" value="₹1.2Cr" change="+31.2%" positive icon={TrendingUp} color="bg-blue-50 text-blue-600" />
        <KPICard label="Active Listings" value="148" change="+6 new" positive icon={Package} color="bg-purple-50 text-purple-600" />
        <KPICard label="Avg. Rating" value="4.7★" change="+0.2" positive icon={Star} color="bg-amber-50 text-amber-600" />
        <KPICard label="Return Rate" value="2.1%" change="-0.4%" positive icon={RotateCcw} color="bg-red-50 text-red-500" />
      </div>

      {/* Charts row */}
      <div className="grid grid-cols-1 xl:grid-cols-3 gap-5">
        {/* Revenue chart */}
        <div className="xl:col-span-2 bg-white rounded-xl border border-gray-100 p-5">
          <div className="flex items-center justify-between mb-5">
            <div>
              <h3 className="text-[14px] font-semibold text-gray-900">Revenue by Marketplace</h3>
              <p className="text-[12px] text-gray-400 mt-0.5">Last 22 days · All platforms</p>
            </div>
            <div className="flex items-center gap-4 text-[11.5px]">
              {[['#5B5BD6','Amazon'],['#8B5CF6','Flipkart'],['#06B6D4','Meesho']].map(([c,l]) => (
                <span key={l} className="flex items-center gap-1.5 text-gray-500">
                  <span className="w-2 h-2 rounded-full" style={{background: c as string}} />
                  {l}
                </span>
              ))}
            </div>
          </div>
          <ResponsiveContainer width="100%" height={220}>
            <AreaChart data={revenueData} margin={{ top: 5, right: 5, bottom: 0, left: 0 }}>
              <defs>
                <linearGradient id="amazon" x1="0" y1="0" x2="0" y2="1">
                  <stop offset="5%" stopColor="#5B5BD6" stopOpacity={0.15} />
                  <stop offset="95%" stopColor="#5B5BD6" stopOpacity={0} />
                </linearGradient>
                <linearGradient id="flipkart" x1="0" y1="0" x2="0" y2="1">
                  <stop offset="5%" stopColor="#8B5CF6" stopOpacity={0.15} />
                  <stop offset="95%" stopColor="#8B5CF6" stopOpacity={0} />
                </linearGradient>
                <linearGradient id="meesho" x1="0" y1="0" x2="0" y2="1">
                  <stop offset="5%" stopColor="#06B6D4" stopOpacity={0.15} />
                  <stop offset="95%" stopColor="#06B6D4" stopOpacity={0} />
                </linearGradient>
              </defs>
              <CartesianGrid strokeDasharray="3 3" stroke="#F3F4F6" />
              <XAxis dataKey="day" tick={{ fontSize: 11, fill: '#9CA3AF' }} axisLine={false} tickLine={false} />
              <YAxis tick={{ fontSize: 11, fill: '#9CA3AF' }} axisLine={false} tickLine={false} tickFormatter={v => `₹${(v/1000).toFixed(0)}k`} />
              <Tooltip
                contentStyle={{ background: '#fff', border: '1px solid #E5E7EB', borderRadius: 10, fontSize: 12 }}
                formatter={(v: any) => [`₹${(v/1000).toFixed(1)}k`, undefined]}
              />
              <Area type="monotone" dataKey="amazon" stroke="#5B5BD6" strokeWidth={2} fill="url(#amazon)" />
              <Area type="monotone" dataKey="flipkart" stroke="#8B5CF6" strokeWidth={2} fill="url(#flipkart)" />
              <Area type="monotone" dataKey="meesho" stroke="#06B6D4" strokeWidth={2} fill="url(#meesho)" />
            </AreaChart>
          </ResponsiveContainer>
        </div>

        {/* Category pie */}
        <div className="bg-white rounded-xl border border-gray-100 p-5">
          <h3 className="text-[14px] font-semibold text-gray-900 mb-1">Revenue by Category</h3>
          <p className="text-[12px] text-gray-400 mb-4">This month</p>
          <ResponsiveContainer width="100%" height={160}>
            <PieChart>
              <Pie data={categoryData} cx="50%" cy="50%" innerRadius={50} outerRadius={75} dataKey="value" paddingAngle={3}>
                {categoryData.map((entry, i) => (
                  <Cell key={i} fill={entry.color} />
                ))}
              </Pie>
              <Tooltip contentStyle={{ background: '#fff', border: '1px solid #E5E7EB', borderRadius: 8, fontSize: 12 }} formatter={(v: any) => [`${v}%`, undefined]} />
            </PieChart>
          </ResponsiveContainer>
          <div className="mt-3 space-y-2">
            {categoryData.map(c => (
              <div key={c.name} className="flex items-center justify-between text-[12px]">
                <div className="flex items-center gap-2">
                  <span className="w-2.5 h-2.5 rounded-sm" style={{ background: c.color }} />
                  <span className="text-gray-600">{c.name}</span>
                </div>
                <span className="font-semibold text-gray-800">{c.value}%</span>
              </div>
            ))}
          </div>
        </div>
      </div>

      {/* Bottom row */}
      <div className="grid grid-cols-1 xl:grid-cols-3 gap-5">
        {/* Orders trend */}
        <div className="bg-white rounded-xl border border-gray-100 p-5">
          <h3 className="text-[14px] font-semibold text-gray-900 mb-1">Monthly Orders</h3>
          <p className="text-[12px] text-gray-400 mb-4">6-month trend</p>
          <ResponsiveContainer width="100%" height={150}>
            <BarChart data={ordersData} margin={{ top: 0, right: 0, bottom: 0, left: -20 }}>
              <CartesianGrid strokeDasharray="3 3" stroke="#F3F4F6" vertical={false} />
              <XAxis dataKey="month" tick={{ fontSize: 11, fill: '#9CA3AF' }} axisLine={false} tickLine={false} />
              <YAxis tick={{ fontSize: 11, fill: '#9CA3AF' }} axisLine={false} tickLine={false} />
              <Tooltip contentStyle={{ background: '#fff', border: '1px solid #E5E7EB', borderRadius: 8, fontSize: 12 }} />
              <Bar dataKey="orders" fill="#5B5BD6" radius={[4, 4, 0, 0]} />
            </BarChart>
          </ResponsiveContainer>
        </div>

        {/* Activity feed */}
        <div className="bg-white rounded-xl border border-gray-100 p-5">
          <div className="flex items-center justify-between mb-4">
            <h3 className="text-[14px] font-semibold text-gray-900">Recent Activity</h3>
            <button className="text-[12px] text-primary hover:underline flex items-center gap-1">View all <ArrowRight size={12} /></button>
          </div>
          <div className="space-y-3.5">
            {recentActivity.map((a, i) => (
              <div key={i} className="flex items-start gap-3">
                <div className={`w-1.5 h-1.5 rounded-full mt-2 flex-shrink-0 ${a.color.replace('text-', 'bg-')}`} />
                <div className="flex-1 min-w-0">
                  <div className="text-[12.5px] font-medium text-gray-800 truncate">{a.text}</div>
                  <div className="text-[11.5px] text-gray-400 mt-0.5">{a.sub}</div>
                </div>
                <span className="text-[11px] text-gray-400 whitespace-nowrap">{a.time}</span>
              </div>
            ))}
          </div>
        </div>

        {/* AI Insights */}
        <div className="bg-white rounded-xl border border-gray-100 p-5">
          <div className="flex items-center gap-2 mb-4">
            <Sparkles size={16} className="text-primary" />
            <h3 className="text-[14px] font-semibold text-gray-900">AI Insights</h3>
          </div>
          <div className="space-y-3">
            {aiInsights.map((ins, i) => {
              const Icon = ins.icon
              const [bg, fg] = ins.color.split(' ')
              return (
                <div key={i} className="p-3 rounded-lg border border-gray-100 hover:border-gray-200 transition-colors cursor-pointer">
                  <div className="flex items-start gap-2.5">
                    <div className={`w-7 h-7 rounded-lg ${bg} ${fg} flex items-center justify-center flex-shrink-0`}>
                      <Icon size={14} />
                    </div>
                    <div>
                      <div className="text-[12.5px] font-semibold text-gray-800">{ins.title}</div>
                      <div className="text-[11.5px] text-gray-500 mt-0.5 leading-relaxed">{ins.desc}</div>
                    </div>
                  </div>
                </div>
              )
            })}
          </div>
        </div>
      </div>
    </div>
  )
}
