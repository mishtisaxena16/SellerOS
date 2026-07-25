import { Leaf, Award, TrendingDown, Recycle, Package, TreePine, CheckCircle, AlertCircle } from 'lucide-react'
const certifications = [
  { name: 'FSC Certified', org: 'Forest Stewardship Council', status: 'active', expires: 'Dec 2027', icon: '🌲' },
  { name: 'GOTS Certified', org: 'Global Organic Textile Standard', status: 'pending', expires: 'Pending review', icon: '🌿' },
  { name: 'Plastic-Free Packaging', org: 'Plastic Free Foundation', status: 'active', expires: 'Mar 2027', icon: '♻️' },
  { name: 'Carbon Neutral Shipping', org: 'Climate Partner', status: 'active', expires: 'Jan 2027', icon: '🌍' },
]

const initiatives = [
  { title: 'Switch to biodegradable mailers', impact: 'High', category: 'Packaging', progress: 80, co2Saved: '2.4 tons/yr' },
  { title: 'Partner with green courier (Delhivery Eco)', impact: 'High', category: 'Shipping', progress: 60, co2Saved: '5.8 tons/yr' },
  { title: 'Reduce plastic void fill by 90%', impact: 'Medium', category: 'Packaging', progress: 100, co2Saved: '1.1 tons/yr' },
  { title: 'Source 100% sustainable bamboo', impact: 'Medium', category: 'Sourcing', progress: 95, co2Saved: '3.2 tons/yr' },
  { title: 'Amazon Climate Pledge enrollment', impact: 'High', category: 'Certification', progress: 40, co2Saved: 'Est. 8.0 tons/yr' },
]

export default function Sustainability() {
  return (
    <div className="p-6 fade-in space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-xl font-bold text-gray-900">Sustainability Dashboard</h2>
          <p className="text-[13px] text-gray-500 mt-0.5">Track your environmental impact and green certifications</p>
        </div>
        <div className="flex items-center gap-2 px-4 py-2 bg-emerald-50 border border-emerald-100 rounded-xl">
          <Leaf size={15} className="text-emerald-600" />
          <span className="text-[13px] font-semibold text-emerald-700">Green Seller: Bronze Tier</span>
        </div>
      </div>

      {/* Score + KPIs */}
      <div className="grid grid-cols-1 xl:grid-cols-4 gap-5">
        {/* Sustainability score */}
        <div className="bg-white rounded-xl border border-gray-100 p-5 flex flex-col items-center">
          <h3 className="text-[13.5px] font-semibold text-gray-900 mb-2 self-start">Green Score</h3>
          <div className="relative w-32 h-32">
            <svg viewBox="0 0 100 100" className="w-full h-full -rotate-90">
              <circle cx="50" cy="50" r="42" fill="none" stroke="#F0FDF4" strokeWidth="10" />
              <circle cx="50" cy="50" r="42" fill="none" stroke="#10B981" strokeWidth="10" strokeLinecap="round"
                strokeDasharray={`${2 * Math.PI * 42}`}
                strokeDashoffset={`${2 * Math.PI * 42 * (1 - 78 / 100)}`}
                className="score-ring" />
            </svg>
            <div className="absolute inset-0 flex flex-col items-center justify-center">
              <span className="text-3xl font-bold text-gray-900">78</span>
              <span className="text-[10px] text-emerald-600 font-semibold">/ 100</span>
            </div>
          </div>
          <div className="text-[12px] text-emerald-600 font-semibold mt-1">Good — improving</div>
          <div className="text-[11px] text-gray-400 mt-1">+12 pts vs last year</div>
        </div>

        {/* KPI cards */}
        <div className="xl:col-span-3 grid grid-cols-3 gap-4">
          {[
            { label: 'CO₂ Saved (YTD)', value: '12.5 tons', change: '+28%', icon: TreePine, color: 'bg-emerald-50 text-emerald-600' },
            { label: 'Eco Packaging', value: '94%', change: 'of shipments', icon: Package, color: 'bg-blue-50 text-blue-600' },
            { label: 'Waste Reduced', value: '680 kg', change: 'from last yr', icon: Recycle, color: 'bg-purple-50 text-purple-600' },
            { label: 'Carbon Footprint', value: '3.8 tons', change: '-18% YoY', icon: TrendingDown, color: 'bg-amber-50 text-amber-600' },
            { label: 'Active Certifications', value: '3 / 4', change: '1 pending', icon: Award, color: 'bg-primary-50 text-primary' },
            { label: 'Supplier ESG Score', value: '82/100', change: 'Top quartile', icon: Leaf, color: 'bg-teal-50 text-teal-600' },
          ].map(({ label, value, change, icon: Icon, color }) => (
            <div key={label} className="bg-white rounded-xl border border-gray-100 p-4">
              <div className={`w-8 h-8 rounded-lg flex items-center justify-center mb-2.5 ${color}`}><Icon size={15} /></div>
              <div className="text-xl font-bold text-gray-900">{value}</div>
              <div className="text-[11.5px] text-gray-500">{label}</div>
              <div className="text-[11px] text-gray-400">{change}</div>
            </div>
          ))}
        </div>
      </div>

      <div className="grid grid-cols-1 xl:grid-cols-2 gap-5">
        {/* Certifications */}
        <div className="bg-white rounded-xl border border-gray-100 p-5">
          <h3 className="text-[14px] font-semibold text-gray-900 mb-4">Certifications & Compliance</h3>
          <div className="space-y-3">
            {certifications.map(cert => (
              <div key={cert.name} className="flex items-center gap-3 p-3 bg-gray-50/50 rounded-lg border border-gray-100">
                <span className="text-2xl">{cert.icon}</span>
                <div className="flex-1">
                  <div className="text-[13px] font-semibold text-gray-900">{cert.name}</div>
                  <div className="text-[11.5px] text-gray-500">{cert.org}</div>
                </div>
                <div className="text-right">
                  <div className={`badge ${cert.status === 'active' ? 'bg-emerald-50 text-emerald-600' : 'bg-amber-50 text-amber-600'}`}>
                    {cert.status}
                  </div>
                  <div className="text-[11px] text-gray-400 mt-1">{cert.expires}</div>
                </div>
              </div>
            ))}
          </div>
        </div>

        {/* Initiatives */}
        <div className="bg-white rounded-xl border border-gray-100 p-5">
          <h3 className="text-[14px] font-semibold text-gray-900 mb-4">Green Initiatives</h3>
          <div className="space-y-3.5">
            {initiatives.map(init => (
              <div key={init.title}>
                <div className="flex items-center justify-between mb-1.5">
                  <div className="flex items-center gap-2">
                    {init.progress === 100
                      ? <CheckCircle size={13} className="text-emerald-500" />
                      : <AlertCircle size={13} className={init.impact === 'High' ? 'text-amber-500' : 'text-blue-400'} />
                    }
                    <span className="text-[12.5px] font-medium text-gray-800">{init.title}</span>
                  </div>
                  <div className="flex items-center gap-2">
                    <span className="text-[11px] text-emerald-600 font-medium">↓ {init.co2Saved}</span>
                    <span className="text-[12.5px] font-semibold text-gray-700">{init.progress}%</span>
                  </div>
                </div>
                <div className="h-1.5 bg-gray-100 rounded-full overflow-hidden">
                  <div
                    className={`h-full rounded-full transition-all duration-500 ${init.progress === 100 ? 'bg-emerald-400' : 'bg-primary'}`}
                    style={{ width: `${init.progress}%` }}
                  />
                </div>
                <div className="flex items-center gap-2 mt-1">
                  <span className="badge bg-gray-100 text-gray-500 text-[10px]">{init.category}</span>
                  <span className={`badge text-[10px] ${init.impact === 'High' ? 'bg-red-50 text-red-500' : 'bg-blue-50 text-blue-500'}`}>{init.impact} Impact</span>
                </div>
              </div>
            ))}
          </div>
        </div>
      </div>
    </div>
  )
}
