import { useState } from 'react'
import { User, Bell, Link, CreditCard, Shield, Zap, Check, Eye, EyeOff } from 'lucide-react'

const tabs = [
  { id: 'profile', label: 'Profile', icon: User },
  { id: 'marketplaces', label: 'Marketplaces', icon: Link },
  { id: 'notifications', label: 'Notifications', icon: Bell },
  { id: 'billing', label: 'Billing', icon: CreditCard },
  { id: 'security', label: 'Security', icon: Shield },
]

function Toggle({ checked, onChange }: { checked: boolean; onChange: (v: boolean) => void }) {
  return (
    <button
      onClick={() => onChange(!checked)}
      className={`relative w-10 h-5.5 rounded-full transition-colors flex-shrink-0 ${checked ? 'bg-primary' : 'bg-gray-200'}`}
      style={{ height: 22, minWidth: 40 }}
    >
      <span className={`absolute top-0.5 w-4.5 h-4.5 bg-white rounded-full shadow-sm transition-transform ${checked ? 'translate-x-5' : 'translate-x-0.5'}`}
        style={{ width: 18, height: 18 }} />
    </button>
  )
}

const connectedMarketplaces = [
  { name: 'Amazon India', id: 'A21TJRUUN4KGV', status: 'connected', color: '#FF9900', lastSync: '2 min ago' },
  { name: 'Flipkart', id: 'FK-SELLER-82841', status: 'connected', color: '#2874F0', lastSync: '8 min ago' },
  { name: 'Meesho', id: 'MS-887234', status: 'connected', color: '#9B2F8A', lastSync: '15 min ago' },
  { name: 'Myntra', id: '', status: 'disconnected', color: '#FC5A8D', lastSync: 'Never' },
  { name: 'Snapdeal', id: '', status: 'disconnected', color: '#E40046', lastSync: 'Never' },
]

export default function Settings() {
  const [activeTab, setActiveTab] = useState('profile')
  const [profile, setProfile] = useState({ name: 'Rahul Kumar', email: 'rahul@greennest.in', business: 'GreenNest Eco Products', phone: '+91 98765 43210', gstin: '27AAAFG1234H1ZB' })
  const [showPassword, setShowPassword] = useState(false)
  const [notifs, setNotifs] = useState({ orders: true, stockAlerts: true, priceChanges: true, aiInsights: true, marketing: false, weekly: true })
  const [saved, setSaved] = useState(false)

  const save = () => { setSaved(true); setTimeout(() => setSaved(false), 2000) }

  return (
    <div className="p-6 fade-in">
      <div className="mb-6">
        <h2 className="text-xl font-bold text-gray-900">Settings</h2>
        <p className="text-[13px] text-gray-500 mt-0.5">Manage your account, integrations and preferences</p>
      </div>

      <div className="flex gap-6">
        {/* Sidebar */}
        <div className="w-52 flex-shrink-0">
          <div className="bg-white rounded-xl border border-gray-100 p-2 space-y-0.5">
            {tabs.map(({ id, label, icon: Icon }) => (
              <button key={id} onClick={() => setActiveTab(id)}
                className={`w-full flex items-center gap-3 px-3 py-2.5 rounded-lg text-left transition-colors nav-item ${
                  activeTab === id ? 'bg-primary-50 text-primary' : 'text-gray-600 hover:bg-gray-50 hover:text-gray-900'
                }`}>
                <Icon size={16} />
                <span className="text-[13px] font-medium">{label}</span>
              </button>
            ))}
          </div>
        </div>

        {/* Content */}
        <div className="flex-1 min-w-0">
          {activeTab === 'profile' && (
            <div className="bg-white rounded-xl border border-gray-100 p-6 space-y-5">
              <h3 className="text-[14px] font-semibold text-gray-900">Profile Information</h3>
              {/* Avatar */}
              <div className="flex items-center gap-4">
                <div className="w-16 h-16 rounded-2xl bg-gradient-to-br from-primary to-purple-500 flex items-center justify-center text-white text-xl font-bold">RK</div>
                <div>
                  <button className="text-[13px] font-medium text-primary hover:text-primary-hover">Change photo</button>
                  <div className="text-[11.5px] text-gray-400 mt-0.5">JPG, PNG up to 2MB</div>
                </div>
              </div>
              <div className="grid grid-cols-2 gap-4">
                {[
                  { label: 'Full Name', key: 'name', value: profile.name },
                  { label: 'Business Name', key: 'business', value: profile.business },
                  { label: 'Email Address', key: 'email', value: profile.email },
                  { label: 'Phone Number', key: 'phone', value: profile.phone },
                ].map(({ label, key, value }) => (
                  <div key={key}>
                    <label className="block text-[12px] font-medium text-gray-700 mb-1.5">{label}</label>
                    <input
                      value={value}
                      onChange={e => setProfile(p => ({ ...p, [key]: e.target.value }))}
                      className="w-full border border-gray-200 rounded-lg px-3 py-2.5 text-[13px] bg-gray-50"
                    />
                  </div>
                ))}
              </div>
              <div>
                <label className="block text-[12px] font-medium text-gray-700 mb-1.5">GSTIN</label>
                <input value={profile.gstin} onChange={e => setProfile(p => ({ ...p, gstin: e.target.value }))}
                  className="w-full max-w-xs border border-gray-200 rounded-lg px-3 py-2.5 text-[13px] font-mono bg-gray-50" />
              </div>
              <button onClick={save}
                className="flex items-center gap-2 px-4 py-2 bg-primary text-white text-[13px] font-medium rounded-lg hover:bg-primary-hover transition-colors">
                {saved ? <><Check size={14} /> Saved!</> : 'Save Changes'}
              </button>
            </div>
          )}

          {activeTab === 'marketplaces' && (
            <div className="bg-white rounded-xl border border-gray-100 p-6">
              <h3 className="text-[14px] font-semibold text-gray-900 mb-1">Marketplace Integrations</h3>
              <p className="text-[12.5px] text-gray-500 mb-5">Connect your seller accounts to sync inventory, orders and analytics.</p>
              <div className="space-y-3">
                {connectedMarketplaces.map(mkt => (
                  <div key={mkt.name} className="flex items-center gap-4 p-4 rounded-xl border border-gray-100 hover:border-gray-200 transition-colors">
                    <div className="w-10 h-10 rounded-lg flex items-center justify-center text-white text-[13px] font-bold flex-shrink-0"
                      style={{ background: mkt.color }}>{mkt.name[0]}</div>
                    <div className="flex-1">
                      <div className="text-[13.5px] font-semibold text-gray-900">{mkt.name}</div>
                      {mkt.id
                        ? <div className="text-[11.5px] text-gray-500 font-mono">{mkt.id}</div>
                        : <div className="text-[11.5px] text-gray-400">Not connected</div>
                      }
                    </div>
                    <div className="text-right">
                      <div className={`badge ${mkt.status === 'connected' ? 'bg-emerald-50 text-emerald-600' : 'bg-gray-100 text-gray-500'}`}>{mkt.status}</div>
                      <div className="text-[11px] text-gray-400 mt-1">Sync: {mkt.lastSync}</div>
                    </div>
                    <button className={`px-3 py-1.5 text-[12.5px] font-medium rounded-lg transition-colors ${
                      mkt.status === 'connected'
                        ? 'bg-gray-100 text-gray-600 hover:bg-gray-200'
                        : 'bg-primary text-white hover:bg-primary-hover'
                    }`}>
                      {mkt.status === 'connected' ? 'Manage' : 'Connect'}
                    </button>
                  </div>
                ))}
              </div>
            </div>
          )}

          {activeTab === 'notifications' && (
            <div className="bg-white rounded-xl border border-gray-100 p-6">
              <h3 className="text-[14px] font-semibold text-gray-900 mb-5">Notification Preferences</h3>
              <div className="space-y-4">
                {[
                  { key: 'orders', label: 'New Orders', desc: 'Get notified for every new order across all marketplaces' },
                  { key: 'stockAlerts', label: 'Stock Alerts', desc: 'Low stock and out-of-stock notifications' },
                  { key: 'priceChanges', label: 'Price Changes', desc: 'Competitor pricing changes and Buy Box alerts' },
                  { key: 'aiInsights', label: 'AI Insights', desc: 'Daily AI-generated performance insights and recommendations' },
                  { key: 'marketing', label: 'Marketing Reports', desc: 'Weekly campaign performance summaries' },
                  { key: 'weekly', label: 'Weekly Summary', desc: 'Your weekly business performance digest every Monday morning' },
                ].map(({ key, label, desc }) => (
                  <div key={key} className="flex items-center justify-between py-3 border-b border-gray-50 last:border-0">
                    <div>
                      <div className="text-[13.5px] font-medium text-gray-900">{label}</div>
                      <div className="text-[12px] text-gray-500">{desc}</div>
                    </div>
                    <Toggle checked={notifs[key as keyof typeof notifs]} onChange={v => setNotifs(n => ({ ...n, [key]: v }))} />
                  </div>
                ))}
              </div>
            </div>
          )}

          {activeTab === 'billing' && (
            <div className="space-y-4">
              <div className="bg-gradient-to-br from-primary to-purple-500 rounded-xl p-6 text-white">
                <div className="flex items-center justify-between">
                  <div>
                    <div className="text-[12px] font-medium text-white/70 mb-1">Current Plan</div>
                    <div className="text-2xl font-bold">Pro Plan</div>
                    <div className="text-[13px] text-white/80 mt-1">₹2,499 / month · Billed annually</div>
                  </div>
                  <Zap size={48} className="text-white/20" />
                </div>
                <div className="mt-4 grid grid-cols-3 gap-3">
                  {[['148', 'Active Listings'], ['3', 'Marketplaces'], ['Unlimited', 'AI Credits']].map(([v, l]) => (
                    <div key={l} className="bg-white/10 rounded-lg p-2.5 text-center">
                      <div className="text-[16px] font-bold">{v}</div>
                      <div className="text-[11px] text-white/70">{l}</div>
                    </div>
                  ))}
                </div>
              </div>
              <div className="bg-white rounded-xl border border-gray-100 p-5">
                <h3 className="text-[13.5px] font-semibold text-gray-900 mb-4">Recent Invoices</h3>
                <div className="space-y-2.5">
                  {[
                    { month: 'Jul 2026', amount: '₹2,499', status: 'Paid' },
                    { month: 'Jun 2026', amount: '₹2,499', status: 'Paid' },
                    { month: 'May 2026', amount: '₹2,499', status: 'Paid' },
                  ].map(inv => (
                    <div key={inv.month} className="flex items-center justify-between py-2.5 border-b border-gray-50 last:border-0">
                      <span className="text-[13px] text-gray-800">{inv.month}</span>
                      <span className="text-[13px] font-semibold text-gray-900">{inv.amount}</span>
                      <span className="badge bg-emerald-50 text-emerald-600">{inv.status}</span>
                      <button className="text-[12.5px] text-primary hover:underline">Download</button>
                    </div>
                  ))}
                </div>
              </div>
            </div>
          )}

          {activeTab === 'security' && (
            <div className="bg-white rounded-xl border border-gray-100 p-6 space-y-5">
              <h3 className="text-[14px] font-semibold text-gray-900">Security Settings</h3>
              <div>
                <label className="block text-[12px] font-medium text-gray-700 mb-1.5">Current Password</label>
                <div className="relative max-w-sm">
                  <input type={showPassword ? 'text' : 'password'} placeholder="Enter current password"
                    className="w-full border border-gray-200 rounded-lg px-3 py-2.5 text-[13px] bg-gray-50 pr-10" />
                  <button onClick={() => setShowPassword(!showPassword)} className="absolute right-3 top-1/2 -translate-y-1/2 text-gray-400">
                    {showPassword ? <EyeOff size={15} /> : <Eye size={15} />}
                  </button>
                </div>
              </div>
              <div className="grid grid-cols-2 gap-4 max-w-lg">
                <div>
                  <label className="block text-[12px] font-medium text-gray-700 mb-1.5">New Password</label>
                  <input type="password" placeholder="New password" className="w-full border border-gray-200 rounded-lg px-3 py-2.5 text-[13px] bg-gray-50" />
                </div>
                <div>
                  <label className="block text-[12px] font-medium text-gray-700 mb-1.5">Confirm Password</label>
                  <input type="password" placeholder="Confirm password" className="w-full border border-gray-200 rounded-lg px-3 py-2.5 text-[13px] bg-gray-50" />
                </div>
              </div>
              <div className="pt-2 border-t border-gray-100">
                <div className="flex items-center justify-between mb-3">
                  <div>
                    <div className="text-[13.5px] font-medium text-gray-900">Two-Factor Authentication</div>
                    <div className="text-[12px] text-gray-500">Secure your account with Google Authenticator</div>
                  </div>
                  <span className="badge bg-emerald-50 text-emerald-600">Enabled</span>
                </div>
              </div>
              <button onClick={save} className="flex items-center gap-2 px-4 py-2 bg-primary text-white text-[13px] font-medium rounded-lg hover:bg-primary-hover transition-colors">
                {saved ? <><Check size={14} /> Saved!</> : 'Update Password'}
              </button>
            </div>
          )}
        </div>
      </div>
    </div>
  )
}
