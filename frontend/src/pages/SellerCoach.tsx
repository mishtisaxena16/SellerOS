import { useState } from 'react'
import { GraduationCap, Star, Trophy, Play, CheckCircle, Lock, Sparkles, ChevronRight } from 'lucide-react'

const performanceData = {
  overall: 82,
  listing: 79,
  pricing: 88,
  fulfillment: 91,
  reviews: 74,
  returns: 85,
}

const modules = [
  { id: 1, title: 'Listing Mastery', desc: 'Write listings that rank and convert on all marketplaces', lessons: 8, completed: 8, duration: '45 min', locked: false, badge: '🥇' },
  { id: 2, title: 'SEO for Marketplace', desc: 'Keyword research, A9 algorithm, and indexing strategies', lessons: 6, completed: 4, duration: '35 min', locked: false, badge: '🔍' },
  { id: 3, title: 'Pricing Psychology', desc: 'Dynamic pricing, bundle strategies, and Buy Box tactics', lessons: 5, completed: 2, duration: '30 min', locked: false, badge: '💡' },
  { id: 4, title: 'Advertising Deep Dive', desc: 'PPC campaigns, auto vs manual, bid optimization', lessons: 7, completed: 0, duration: '55 min', locked: false, badge: '📣' },
  { id: 5, title: 'Inventory Forecasting', desc: 'Demand planning, seasonality, and stockout prevention', lessons: 6, completed: 0, duration: '40 min', locked: false, badge: '📦' },
  { id: 6, title: 'Account Health Mastery', desc: 'Maintain top ratings and avoid suspensions', lessons: 5, completed: 0, duration: '25 min', locked: true, badge: '🛡️' },
]

const tips = [
  { type: 'opportunity', title: 'Your images are below benchmark', desc: 'Listings with 7+ images get 34% more conversions. Add 3 more images to your top 5 products.', priority: 'high' },
  { type: 'warning', title: 'Review response rate low', desc: 'You\'ve not responded to 12 customer reviews in the last 7 days. Amazon recommends responding within 24 hours.', priority: 'high' },
  { type: 'tip', title: 'Leverage Flipkart Smart ROI', desc: 'Your Flipkart ads ROAS is 3.6x. Increasing budget by ₹1000 could yield ₹3,600 additional revenue.', priority: 'medium' },
  { type: 'achievement', title: 'Top 10% seller in Kitchen category!', desc: 'Your fulfillment rate (98.2%) and rating (4.7★) put you in the top 10% of Kitchen sellers on Amazon India.', priority: 'positive' },
]

const badges = [
  { name: 'Listing Pro', icon: '🥇', earned: true },
  { name: 'Fast Fulfillment', icon: '⚡', earned: true },
  { name: 'Top Rated', icon: '⭐', earned: true },
  { name: 'SEO Expert', icon: '🔍', earned: false },
  { name: 'Ad Master', icon: '📣', earned: false },
  { name: 'Green Seller', icon: '🌿', earned: false },
]

export default function SellerCoach() {
  const [activeModule, setActiveModule] = useState<number | null>(null)

  return (
    <div className="p-6 fade-in space-y-6">
      <div>
        <h2 className="text-xl font-bold text-gray-900 flex items-center gap-2">
          <GraduationCap size={22} className="text-primary" />
          Seller Coach
        </h2>
        <p className="text-[13px] text-gray-500 mt-0.5">AI-powered coaching to grow your seller performance</p>
      </div>

      <div className="grid grid-cols-1 xl:grid-cols-3 gap-5">
        {/* Performance score */}
        <div className="bg-white rounded-xl border border-gray-100 p-5">
          <h3 className="text-[13.5px] font-semibold text-gray-900 mb-4">Seller Score</h3>
          <div className="flex items-center justify-center mb-4">
            <div className="relative w-32 h-32">
              <svg viewBox="0 0 100 100" className="w-full h-full -rotate-90">
                <circle cx="50" cy="50" r="42" fill="none" stroke="#F3F4F6" strokeWidth="10" />
                <circle cx="50" cy="50" r="42" fill="none" stroke="#5B5BD6" strokeWidth="10" strokeLinecap="round"
                  strokeDasharray={`${2 * Math.PI * 42}`}
                  strokeDashoffset={`${2 * Math.PI * 42 * (1 - performanceData.overall / 100)}`}
                  className="score-ring" />
              </svg>
              <div className="absolute inset-0 flex flex-col items-center justify-center">
                <span className="text-3xl font-bold text-gray-900">{performanceData.overall}</span>
                <span className="text-[10px] text-primary font-semibold">GREAT</span>
              </div>
            </div>
          </div>
          <div className="space-y-2.5">
            {Object.entries(performanceData).filter(([k]) => k !== 'overall').map(([key, val]) => (
              <div key={key}>
                <div className="flex justify-between text-[12px] mb-1">
                  <span className="text-gray-600 capitalize">{key}</span>
                  <span className={`font-semibold ${val >= 85 ? 'text-emerald-600' : val >= 70 ? 'text-amber-600' : 'text-red-500'}`}>{val}</span>
                </div>
                <div className="h-1.5 bg-gray-100 rounded-full overflow-hidden">
                  <div className={`h-full rounded-full ${val >= 85 ? 'bg-emerald-400' : val >= 70 ? 'bg-amber-400' : 'bg-red-400'}`} style={{ width: `${val}%` }} />
                </div>
              </div>
            ))}
          </div>
        </div>

        {/* Learning modules */}
        <div className="xl:col-span-2 bg-white rounded-xl border border-gray-100 p-5">
          <div className="flex items-center justify-between mb-4">
            <h3 className="text-[13.5px] font-semibold text-gray-900">Learning Path</h3>
            <span className="text-[12px] text-gray-500">14 / 37 lessons complete</span>
          </div>
          <div className="space-y-2.5">
            {modules.map(mod => {
              const pct = mod.lessons > 0 ? Math.round((mod.completed / mod.lessons) * 100) : 0
              return (
                <div
                  key={mod.id}
                  onClick={() => !mod.locked && setActiveModule(activeModule === mod.id ? null : mod.id)}
                  className={`p-4 rounded-lg border transition-all ${
                    mod.locked ? 'border-gray-100 bg-gray-50/50 opacity-60 cursor-not-allowed'
                    : activeModule === mod.id ? 'border-primary bg-primary-50/50 cursor-pointer'
                    : 'border-gray-100 hover:border-gray-200 cursor-pointer'
                  }`}
                >
                  <div className="flex items-center gap-3">
                    <span className="text-xl">{mod.badge}</span>
                    <div className="flex-1 min-w-0">
                      <div className="flex items-center gap-2">
                        <span className="text-[13px] font-semibold text-gray-900">{mod.title}</span>
                        {mod.completed === mod.lessons && mod.lessons > 0 && (
                          <CheckCircle size={13} className="text-emerald-500" />
                        )}
                        {mod.locked && <Lock size={12} className="text-gray-400" />}
                      </div>
                      <div className="text-[11.5px] text-gray-500 truncate">{mod.desc}</div>
                    </div>
                    <div className="text-right flex-shrink-0">
                      <div className="text-[12px] text-gray-500">{mod.completed}/{mod.lessons} lessons</div>
                      <div className="text-[11px] text-gray-400">{mod.duration}</div>
                    </div>
                    <ChevronRight size={14} className={`text-gray-400 transition-transform ${activeModule === mod.id ? 'rotate-90' : ''}`} />
                  </div>
                  <div className="mt-2.5 h-1.5 bg-gray-100 rounded-full overflow-hidden">
                    <div className={`h-full rounded-full transition-all ${pct === 100 ? 'bg-emerald-400' : 'bg-primary'}`} style={{ width: `${pct}%` }} />
                  </div>
                  {activeModule === mod.id && !mod.locked && (
                    <div className="mt-3 pt-3 border-t border-gray-100">
                      <button className="flex items-center gap-2 px-4 py-2 bg-primary text-white text-[12.5px] font-medium rounded-lg hover:bg-primary-hover transition-colors">
                        <Play size={12} fill="white" />
                        {mod.completed > 0 ? 'Continue Learning' : 'Start Module'}
                      </button>
                    </div>
                  )}
                </div>
              )
            })}
          </div>
        </div>
      </div>

      <div className="grid grid-cols-1 xl:grid-cols-2 gap-5">
        {/* Personalized tips */}
        <div className="bg-white rounded-xl border border-gray-100 p-5">
          <div className="flex items-center gap-2 mb-4">
            <Sparkles size={15} className="text-primary" />
            <h3 className="text-[13.5px] font-semibold text-gray-900">AI Coaching Tips</h3>
          </div>
          <div className="space-y-3">
            {tips.map(tip => (
              <div key={tip.title} className={`p-3.5 rounded-lg border ${
                tip.priority === 'high' ? 'border-red-100 bg-red-50/50' :
                tip.priority === 'medium' ? 'border-amber-100 bg-amber-50/50' :
                tip.priority === 'positive' ? 'border-emerald-100 bg-emerald-50/50' :
                'border-gray-100'
              }`}>
                <div className="text-[13px] font-semibold text-gray-900 mb-1">{tip.title}</div>
                <div className="text-[12px] text-gray-600 leading-relaxed">{tip.desc}</div>
              </div>
            ))}
          </div>
        </div>

        {/* Badges */}
        <div className="bg-white rounded-xl border border-gray-100 p-5">
          <div className="flex items-center gap-2 mb-4">
            <Trophy size={15} className="text-amber-500" />
            <h3 className="text-[13.5px] font-semibold text-gray-900">Achievements</h3>
          </div>
          <div className="grid grid-cols-3 gap-3">
            {badges.map(badge => (
              <div key={badge.name} className={`p-4 rounded-xl border text-center transition-all ${
                badge.earned ? 'border-amber-100 bg-amber-50/50' : 'border-gray-100 bg-gray-50/50 opacity-50'
              }`}>
                <div className={`text-3xl mb-2 ${!badge.earned ? 'grayscale' : ''}`}>{badge.icon}</div>
                <div className="text-[11.5px] font-semibold text-gray-700">{badge.name}</div>
                <div className="text-[10px] text-gray-400 mt-0.5">{badge.earned ? 'Earned' : 'Locked'}</div>
              </div>
            ))}
          </div>
          <div className="mt-4 p-3 bg-primary-50 rounded-lg border border-primary-100">
            <div className="flex items-center gap-2">
              <Star size={14} className="text-primary" />
              <span className="text-[12.5px] font-semibold text-primary">Next: SEO Expert Badge</span>
            </div>
            <div className="text-[11.5px] text-gray-600 mt-1">Complete "SEO for Marketplace" module to unlock.</div>
          </div>
        </div>
      </div>
    </div>
  )
}
