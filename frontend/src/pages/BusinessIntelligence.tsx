import {
  LineChart, Line, XAxis, YAxis, CartesianGrid,
  Tooltip, ResponsiveContainer, RadarChart, Radar, PolarGrid,
  PolarAngleAxis, PolarRadiusAxis
} from 'recharts'
import { TrendingUp, Users, Star, ArrowUpRight } from 'lucide-react'

const monthlyRevenue = [
  { month: 'Jan', revenue: 48200, orders: 890, aov: 54 },
  { month: 'Feb', revenue: 52400, orders: 980, aov: 53 },
  { month: 'Mar', revenue: 61800, orders: 1120, aov: 55 },
  { month: 'Apr', revenue: 58900, orders: 1050, aov: 56 },
  { month: 'May', revenue: 71200, orders: 1280, aov: 56 },
  { month: 'Jun', revenue: 79400, orders: 1450, aov: 55 },
  { month: 'Jul', revenue: 83400, orders: 1560, aov: 53 },
]

const marketplaceComparison = [
  { platform: 'Amazon', revenue: 41200, orders: 820, returns: 2.1, rating: 4.7 },
  { platform: 'Flipkart', revenue: 25400, orders: 490, returns: 2.8, rating: 4.6 },
  { platform: 'Meesho', revenue: 16800, orders: 250, returns: 3.4, rating: 4.4 },
]

const radarData = [
  { subject: 'Revenue', Amazon: 95, Flipkart: 70, Meesho: 55 },
  { subject: 'Orders', Amazon: 88, Flipkart: 65, Meesho: 45 },
  { subject: 'Rating', Amazon: 94, Flipkart: 90, Meesho: 85 },
  { subject: 'Returns', Amazon: 92, Flipkart: 85, Meesho: 78 },
  { subject: 'Growth', Amazon: 75, Flipkart: 82, Meesho: 90 },
]

const topProducts = [
  { name: 'Bamboo Spice Rack 6-Tier', revenue: 182340, units: 203, growth: 34 },
  { name: 'Bamboo Desk Organizer', revenue: 141750, units: 218, growth: 22 },
  { name: 'Wooden Serving Board Set', revenue: 118620, units: 95, growth: 18 },
  { name: 'Kitchen Tool Set (5-pc)', revenue: 107370, units: 126, growth: 28 },
  { name: 'Teak Wood Coasters', revenue: 89550, units: 163, growth: -4 },
]

export default function BusinessIntelligence() {
  return (
    <div className="p-6 fade-in space-y-6">
      <div>
        <h2 className="text-xl font-bold text-gray-900">Business Intelligence</h2>
        <p className="text-[13px] text-gray-500 mt-0.5">Deep analytics across all marketplaces · YTD 2026</p>
      </div>

      {/* Top metrics */}
      <div className="grid grid-cols-4 gap-4">
        {[
          { label: 'YTD Revenue', value: '₹4.55L', change: '+28.4%', up: true, icon: TrendingUp, color: 'bg-primary-50 text-primary' },
          { label: 'Total Customers', value: '8,214', change: '+19.2%', up: true, icon: Users, color: 'bg-blue-50 text-blue-600' },
          { label: 'Avg. Order Value', value: '₹54.5', change: '+4.1%', up: true, icon: ArrowUpRight, color: 'bg-emerald-50 text-emerald-600' },
          { label: 'Avg. Rating', value: '4.62★', change: '+0.18', up: true, icon: Star, color: 'bg-amber-50 text-amber-600' },
        ].map(({ label, value, change, up, icon: Icon, color }) => (
          <div key={label} className="bg-white rounded-xl border border-gray-100 p-5">
            <div className="flex items-center justify-between mb-3">
              <div className={`w-9 h-9 rounded-lg flex items-center justify-center ${color}`}><Icon size={16} /></div>
              <span className={`text-[12px] font-medium ${up ? 'text-emerald-600' : 'text-red-500'}`}>
                {up ? '▲' : '▼'} {change}
              </span>
            </div>
            <div className="text-2xl font-bold text-gray-900">{value}</div>
            <div className="text-[12px] text-gray-500 mt-0.5">{label}</div>
          </div>
        ))}
      </div>

      {/* Revenue chart */}
      <div className="bg-white rounded-xl border border-gray-100 p-5">
        <div className="flex items-center justify-between mb-5">
          <div>
            <h3 className="text-[14px] font-semibold text-gray-900">Revenue & Orders Trend</h3>
            <p className="text-[12px] text-gray-400 mt-0.5">Jan – Jul 2026</p>
          </div>
        </div>
        <ResponsiveContainer width="100%" height={240}>
          <LineChart data={monthlyRevenue} margin={{ top: 5, right: 10, bottom: 0, left: 0 }}>
            <CartesianGrid strokeDasharray="3 3" stroke="#F3F4F6" />
            <XAxis dataKey="month" tick={{ fontSize: 11, fill: '#9CA3AF' }} axisLine={false} tickLine={false} />
            <YAxis yAxisId="left" tick={{ fontSize: 11, fill: '#9CA3AF' }} axisLine={false} tickLine={false} tickFormatter={v => `₹${(v/1000).toFixed(0)}k`} />
            <YAxis yAxisId="right" orientation="right" tick={{ fontSize: 11, fill: '#9CA3AF' }} axisLine={false} tickLine={false} />
            <Tooltip contentStyle={{ background: '#fff', border: '1px solid #E5E7EB', borderRadius: 10, fontSize: 12 }} />
            <Line yAxisId="left" type="monotone" dataKey="revenue" stroke="#5B5BD6" strokeWidth={2.5} dot={{ fill: '#5B5BD6', r: 4 }} />
            <Line yAxisId="right" type="monotone" dataKey="orders" stroke="#06B6D4" strokeWidth={2} dot={{ fill: '#06B6D4', r: 3 }} strokeDasharray="5 5" />
          </LineChart>
        </ResponsiveContainer>
      </div>

      <div className="grid grid-cols-1 xl:grid-cols-2 gap-5">
        {/* Marketplace comparison */}
        <div className="bg-white rounded-xl border border-gray-100 p-5">
          <h3 className="text-[14px] font-semibold text-gray-900 mb-4">Marketplace Comparison</h3>
          <div className="space-y-4">
            {marketplaceComparison.map(({ platform, revenue, orders, returns, rating }) => (
              <div key={platform} className="p-3 bg-gray-50/50 rounded-lg border border-gray-100">
                <div className="flex items-center justify-between mb-2">
                  <span className="text-[13px] font-semibold text-gray-800">{platform}</span>
                  <span className="text-[14px] font-bold text-gray-900">₹{(revenue/1000).toFixed(1)}k</span>
                </div>
                <div className="grid grid-cols-3 gap-2 text-[11.5px]">
                  <div><span className="text-gray-500">Orders</span><br /><span className="font-semibold text-gray-800">{orders}</span></div>
                  <div><span className="text-gray-500">Returns</span><br /><span className="font-semibold text-gray-800">{returns}%</span></div>
                  <div><span className="text-gray-500">Rating</span><br /><span className="font-semibold text-gray-800">{rating}★</span></div>
                </div>
                <div className="mt-2 h-1.5 bg-gray-100 rounded-full overflow-hidden">
                  <div className="h-full bg-primary rounded-full" style={{ width: `${(revenue / 41200) * 100}%` }} />
                </div>
              </div>
            ))}
          </div>
        </div>

        {/* Radar chart */}
        <div className="bg-white rounded-xl border border-gray-100 p-5">
          <h3 className="text-[14px] font-semibold text-gray-900 mb-1">Platform Performance Radar</h3>
          <p className="text-[12px] text-gray-400 mb-3">Normalized scores across KPIs</p>
          <ResponsiveContainer width="100%" height={220}>
            <RadarChart data={radarData}>
              <PolarGrid stroke="#F3F4F6" />
              <PolarAngleAxis dataKey="subject" tick={{ fontSize: 11, fill: '#9CA3AF' }} />
              <PolarRadiusAxis tick={{ fontSize: 10 }} angle={30} domain={[0, 100]} />
              <Radar name="Amazon" dataKey="Amazon" stroke="#5B5BD6" fill="#5B5BD6" fillOpacity={0.1} strokeWidth={2} />
              <Radar name="Flipkart" dataKey="Flipkart" stroke="#8B5CF6" fill="#8B5CF6" fillOpacity={0.1} strokeWidth={2} />
              <Radar name="Meesho" dataKey="Meesho" stroke="#06B6D4" fill="#06B6D4" fillOpacity={0.1} strokeWidth={2} />
              <Tooltip contentStyle={{ background: '#fff', border: '1px solid #E5E7EB', borderRadius: 8, fontSize: 12 }} />
            </RadarChart>
          </ResponsiveContainer>
          <div className="flex items-center justify-center gap-4 text-[11.5px]">
            {[['#5B5BD6','Amazon'],['#8B5CF6','Flipkart'],['#06B6D4','Meesho']].map(([c,l]) => (
              <span key={l} className="flex items-center gap-1.5 text-gray-500">
                <span className="w-2 h-2 rounded-full" style={{background: c}} />{l}
              </span>
            ))}
          </div>
        </div>
      </div>

      {/* Top products */}
      <div className="bg-white rounded-xl border border-gray-100 p-5">
        <h3 className="text-[14px] font-semibold text-gray-900 mb-4">Top Products by Revenue</h3>
        <div className="space-y-3">
          {topProducts.map(({ name, revenue, units, growth }, i) => (
            <div key={name} className="flex items-center gap-4">
              <span className="w-5 text-[12px] font-bold text-gray-400 text-right">{i + 1}</span>
              <div className="flex-1">
                <div className="flex items-center justify-between mb-1">
                  <span className="text-[13px] font-medium text-gray-800">{name}</span>
                  <div className="flex items-center gap-3">
                    <span className="text-[12px] text-gray-500">{units} units</span>
                    <span className={`text-[12px] font-semibold ${growth >= 0 ? 'text-emerald-600' : 'text-red-500'}`}>
                      {growth >= 0 ? '+' : ''}{growth}%
                    </span>
                    <span className="text-[13px] font-bold text-gray-900 w-24 text-right">₹{revenue.toLocaleString('en-IN')}</span>
                  </div>
                </div>
                <div className="h-1.5 bg-gray-100 rounded-full overflow-hidden">
                  <div className="h-full bg-primary rounded-full" style={{ width: `${(revenue / 182340) * 100}%` }} />
                </div>
              </div>
            </div>
          ))}
        </div>
      </div>
    </div>
  )
}
