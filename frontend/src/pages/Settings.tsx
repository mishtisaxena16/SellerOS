import { useEffect, useState } from 'react'
import { useNavigate, useSearchParams } from 'react-router-dom'
import { User, Bell, Link as LinkIcon, CreditCard, Shield, Loader2, Info, Check, Eye, EyeOff, AlertTriangle } from 'lucide-react'
import { usePlatform, PLATFORM_LABELS } from '../context/PlatformContext'
import { disconnectMarketplace, SUPPORTED_PLATFORMS, type Platform } from '../api/marketplace'
import { useAuth } from '../context/AuthContext'
import { ApiError } from '../api/client'

const tabs = [
  { id: 'profile', label: 'Profile', icon: User },
  { id: 'marketplaces', label: 'Marketplaces', icon: LinkIcon },
  { id: 'notifications', label: 'Notifications', icon: Bell },
  { id: 'billing', label: 'Billing', icon: CreditCard },
  { id: 'security', label: 'Security', icon: Shield },
]

function Toggle({ checked, onChange }: { checked: boolean; onChange: (v: boolean) => void }) {
  return (
    <button
      onClick={() => onChange(!checked)}
      className={`relative w-10 h-5.5 rounded-full border transition-colors flex-shrink-0 ${checked ? 'bg-accent-blue border-transparent' : 'bg-surface border-app'}`}
      style={{ height: 22, minWidth: 40 }}
    >
      <span className={`absolute top-0.5 w-4.5 h-4.5 bg-app rounded-full shadow-sm transition-transform ${checked ? 'translate-x-5' : 'translate-x-0.5'}`}
        style={{ width: 18, height: 18 }} />
    </button>
  )
}

function NotYetAvailable({ children }: { children: React.ReactNode }) {
  return (
    <div className="flex items-start gap-2 text-[12.5px] text-faint bg-surface rounded-lg p-3">
      <Info size={14} className="flex-shrink-0 mt-0.5" />
      <span>{children}</span>
    </div>
  )
}

const PLATFORM_COLORS: Record<Platform, string> = { amazon: '#FF9900', flipkart: '#2874F0', meesho: '#9B2F8A' }

export default function Settings() {
  const navigate = useNavigate()
  const [searchParams] = useSearchParams()
  const { connected, connectedPlatforms, loading, refresh } = usePlatform()
  const { user, updateProfile, changePassword } = useAuth()
  const [disconnectingId, setDisconnectingId] = useState<number | null>(null)
  const [disconnectError, setDisconnectError] = useState<string | null>(null)
  // Lets the sidebar deep-link straight into a tab (e.g. /settings?tab=marketplaces)
  // instead of a separate Marketplace page duplicating what's already here.
  const requestedTab = searchParams.get('tab')
  const [activeTab, setActiveTab] = useState(
    tabs.some(t => t.id === requestedTab) ? requestedTab! : 'profile'
  )
  const [notifs, setNotifs] = useState({ orders: true, stockAlerts: true, priceChanges: true, aiInsights: true, marketing: false, weekly: true })

  // Profile — business_name is the only editable field the backend
  // models (via PATCH /auth/me); email is fixed at registration.
  const [businessNameInput, setBusinessNameInput] = useState(user?.business_name ?? '')
  useEffect(() => {
    if (user?.business_name) setBusinessNameInput(user.business_name)
  }, [user?.business_name])
  const [savingProfile, setSavingProfile] = useState(false)
  const [profileSaved, setProfileSaved] = useState(false)
  const [profileError, setProfileError] = useState<string | null>(null)

  // Security — wired to POST /auth/change-password.
  const [currentPassword, setCurrentPassword] = useState('')
  const [newPassword, setNewPassword] = useState('')
  const [confirmPassword, setConfirmPassword] = useState('')
  const [showCurrentPassword, setShowCurrentPassword] = useState(false)
  const [showNewPassword, setShowNewPassword] = useState(false)
  const [showConfirmPassword, setShowConfirmPassword] = useState(false)
  const [changingPassword, setChangingPassword] = useState(false)
  const [passwordSaved, setPasswordSaved] = useState(false)
  const [passwordError, setPasswordError] = useState<string | null>(null)

  // Re-sync if the user is already on /settings and clicks the sidebar's Marketplace
  // link again — the component doesn't remount just because the query param changed.
  useEffect(() => {
    if (requestedTab && tabs.some(t => t.id === requestedTab)) {
      setActiveTab(requestedTab)
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [requestedTab])

  const businessName = user?.business_name || 'Your business'
  const initials = businessName
    .split(' ')
    .filter(Boolean)
    .slice(0, 2)
    .map(w => w[0]?.toUpperCase())
    .join('') || 'S'

  const saveProfile = async () => {
    const trimmed = businessNameInput.trim()
    if (!trimmed) {
      setProfileError('Business name cannot be empty.')
      return
    }
    if (trimmed === user?.business_name) return
    setSavingProfile(true)
    setProfileError(null)
    try {
      await updateProfile(trimmed)
      setProfileSaved(true)
      setTimeout(() => setProfileSaved(false), 2500)
    } catch (err) {
      setProfileError(err instanceof ApiError ? err.message : 'Could not save your profile.')
    } finally {
      setSavingProfile(false)
    }
  }

  const submitPasswordChange = async () => {
    setPasswordError(null)
    if (!currentPassword) {
      setPasswordError('Enter your current password.')
      return
    }
    if (newPassword.length < 8) {
      setPasswordError('New password must be at least 8 characters.')
      return
    }
    if (newPassword !== confirmPassword) {
      setPasswordError('New password and confirmation do not match.')
      return
    }
    if (newPassword === currentPassword) {
      setPasswordError('New password must be different from your current password.')
      return
    }
    setChangingPassword(true)
    try {
      await changePassword(currentPassword, newPassword)
      setCurrentPassword('')
      setNewPassword('')
      setConfirmPassword('')
      setPasswordSaved(true)
      setTimeout(() => setPasswordSaved(false), 2500)
    } catch (err) {
      setPasswordError(err instanceof ApiError ? err.message : 'Could not change your password.')
    } finally {
      setChangingPassword(false)
    }
  }

  return (
    <div className="p-6 fade-in">
      <div className="mb-6">
        <h2 className="text-xl font-bold text-app">Settings</h2>
        <p className="text-[13px] text-dim mt-0.5">Manage your account, integrations and preferences</p>
      </div>

      <div className="flex flex-col md:flex-row gap-6">
        <div className="w-full md:w-52 flex-shrink-0">
          <div className="bg-elev rounded-xl border border-app p-2 flex md:flex-col gap-0.5 overflow-x-auto md:overflow-visible">
            {tabs.map(({ id, label, icon: Icon }) => (
              <button key={id} onClick={() => setActiveTab(id)}
                className={`w-full flex items-center gap-3 px-3 py-2.5 rounded-lg text-left transition-colors nav-item whitespace-nowrap ${
                  activeTab === id ? 'bg-accent-blue-soft text-accent-blue' : 'text-dim hover:bg-surface hover:text-app'
                }`}>
                <Icon size={16} />
                <span className="text-[13px] font-medium">{label}</span>
              </button>
            ))}
          </div>
        </div>

        <div className="flex-1 min-w-0">
          {activeTab === 'profile' && (
            <div className="bg-elev rounded-xl border border-app p-6 space-y-5">
              <h3 className="text-[14px] font-semibold text-app">Profile Information</h3>
              <div className="flex items-center gap-4">
                <div className="w-16 h-16 rounded-2xl bg-gradient-to-br from-primary to-purple-500 flex items-center justify-center text-white text-xl font-bold">{initials}</div>
                <div>
                  <div className="text-[13.5px] font-semibold text-app">{businessName}</div>
                  <div className="text-[12px] text-dim">{user?.email}</div>
                </div>
              </div>

              <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                <div>
                  <label htmlFor="settings-business-name" className="block text-[12px] font-medium text-dim mb-1.5">Business Name</label>
                  <input
                    id="settings-business-name"
                    value={businessNameInput}
                    onChange={e => setBusinessNameInput(e.target.value)}
                    disabled={savingProfile}
                    maxLength={100}
                    autoComplete="organization"
                    className="w-full border border-app rounded-lg px-3 py-2.5 text-[13px] bg-surface disabled:opacity-60"
                  />
                </div>
                <div>
                  <label htmlFor="settings-email" className="block text-[12px] font-medium text-dim mb-1.5">Email Address</label>
                  <input id="settings-email" value={user?.email ?? ''} disabled autoComplete="email"
                    className="w-full border border-app rounded-lg px-3 py-2.5 text-[13px] bg-surface text-dim cursor-not-allowed" />
                </div>
              </div>

              {profileError && (
                <div role="alert" aria-live="polite" className="flex items-center gap-2 text-[12.5px] text-accent-red">
                  <AlertTriangle size={13} /> {profileError}
                </div>
              )}

              <div className="flex items-center gap-3">
                <button
                  onClick={saveProfile}
                  disabled={savingProfile || !businessNameInput.trim() || businessNameInput.trim() === user?.business_name}
                  className="flex items-center gap-2 px-4 py-2 bg-accent-blue text-white text-[13px] font-medium rounded-lg transition-opacity hover:opacity-90 disabled:opacity-50"
                >
                  {savingProfile ? <Loader2 size={14} className="animate-spin" /> : profileSaved ? <Check size={14} /> : null}
                  {savingProfile ? 'Saving…' : profileSaved ? 'Saved' : 'Save Changes'}
                </button>
              </div>

              <NotYetAvailable>
                Business name and email are the only account fields the backend stores today —
                phone, GSTIN, and a profile photo aren't modeled yet, so they aren't shown here.
              </NotYetAvailable>
            </div>
          )}

          {activeTab === 'marketplaces' && (
            <div className="bg-elev rounded-xl border border-app p-6">
              <div className="flex items-center justify-between mb-1">
                <h3 className="text-[14px] font-semibold text-app">Marketplace Integrations</h3>
                <button
                  onClick={() => navigate('/onboarding')}
                  className="px-3 py-1.5 text-[12.5px] font-medium rounded-lg bg-accent-blue text-white transition-opacity hover:opacity-90"
                >
                  Add marketplace
                </button>
              </div>
              <p className="text-[12.5px] text-dim mb-5">Connect your seller accounts to sync inventory, orders and analytics.</p>

              {disconnectError && (
                <div role="alert" aria-live="polite" className="flex items-center gap-2 text-[12.5px] text-accent-red mb-4">
                  <AlertTriangle size={13} /> {disconnectError}
                </div>
              )}

              {loading ? (
                <div className="flex items-center gap-2 text-dim text-[13px] py-6">
                  <Loader2 size={15} className="animate-spin" /> Loading connections…
                </div>
              ) : (
                <div className="space-y-3">
                  {SUPPORTED_PLATFORMS.map(platformId => {
                    const account = connected.find(c => c.platform === platformId)
                    const isConnected = connectedPlatforms.includes(platformId)
                    return (
                      <div key={platformId} className="flex flex-wrap sm:flex-nowrap items-center gap-4 p-4 rounded-xl border border-app hover:border-app transition-colors">
                        <div className="w-10 h-10 rounded-lg flex items-center justify-center text-white text-[13px] font-bold flex-shrink-0"
                          style={{ background: PLATFORM_COLORS[platformId] }}>{PLATFORM_LABELS[platformId][0]}</div>
                        <div className="flex-1 min-w-[140px]">
                          <div className="text-[13.5px] font-semibold text-app">{PLATFORM_LABELS[platformId]}</div>
                          {account
                            ? <div className="text-[11.5px] text-dim">Connected {new Date(account.created_at).toLocaleDateString('en-IN')}</div>
                            : <div className="text-[11.5px] text-faint">Not connected</div>
                          }
                        </div>
                        <div className={`badge ${isConnected ? 'bg-accent-green-soft text-accent-green' : 'bg-surface text-dim'}`}>
                          {isConnected ? 'connected' : 'disconnected'}
                        </div>
                        <button
                          disabled={disconnectingId === account?.id}
                          onClick={async () => {
                            if (!account) { navigate('/onboarding'); return }
                            setDisconnectError(null)
                            setDisconnectingId(account.id)
                            try {
                              await disconnectMarketplace(account.id)
                              await refresh()
                            } catch (err) {
                              setDisconnectError(err instanceof ApiError ? err.message : `Could not disconnect ${PLATFORM_LABELS[platformId]}.`)
                            } finally {
                              setDisconnectingId(null)
                            }
                          }}
                          className={`px-3 py-1.5 text-[12.5px] font-medium rounded-lg transition-colors flex items-center gap-1.5 flex-shrink-0 ${
                            isConnected
                              ? 'bg-surface text-dim hover:bg-accent-red-soft hover:text-accent-red'
                              : 'bg-accent-blue text-white transition-opacity hover:opacity-90'
                          }`}
                        >
                          {disconnectingId === account?.id && <Loader2 size={12} className="animate-spin" />}
                          {isConnected ? 'Disconnect' : 'Connect'}
                        </button>
                      </div>
                    )
                  })}
                </div>
              )}
            </div>
          )}

          {activeTab === 'notifications' && (
            <div className="bg-elev rounded-xl border border-app p-6 space-y-5">
              <h3 className="text-[14px] font-semibold text-app">Notification Preferences</h3>
              <div className="space-y-4">
                {[
                  { key: 'orders', label: 'New Orders', desc: 'Get notified for every new order across all marketplaces' },
                  { key: 'stockAlerts', label: 'Stock Alerts', desc: 'Low stock and out-of-stock notifications' },
                  { key: 'priceChanges', label: 'Price Changes', desc: 'Competitor pricing changes and Buy Box alerts' },
                  { key: 'aiInsights', label: 'AI Insights', desc: 'Daily AI-generated performance insights and recommendations' },
                  { key: 'marketing', label: 'Marketing Reports', desc: 'Weekly campaign performance summaries' },
                  { key: 'weekly', label: 'Weekly Summary', desc: 'Your weekly business performance digest every Monday morning' },
                ].map(({ key, label, desc }) => (
                  <div key={key} className="flex items-center justify-between py-3 border-b border-app last:border-0">
                    <div>
                      <div className="text-[13.5px] font-medium text-app">{label}</div>
                      <div className="text-[12px] text-dim">{desc}</div>
                    </div>
                    <Toggle checked={notifs[key as keyof typeof notifs]} onChange={v => setNotifs(n => ({ ...n, [key]: v }))} />
                  </div>
                ))}
              </div>
              <NotYetAvailable>
                These toggles aren't wired to any delivery channel yet — there's no notification
                service on the backend today, so nothing is actually sent based on them.
              </NotYetAvailable>
            </div>
          )}

          {activeTab === 'billing' && (
            <div className="card p-10 flex flex-col items-center text-center gap-3 max-w-md mx-auto mt-10">
              <div className="w-12 h-12 rounded-xl bg-accent-blue-soft text-accent-blue flex items-center justify-center">
                <CreditCard size={20} />
              </div>
              <h3 className="text-[15px] font-semibold text-app">Billing isn't set up yet</h3>
              <p className="text-[13px] text-dim">
                SellerOS doesn't have a plans, invoicing, or payments backend today, so there's
                nothing real to show here. This tab will come to life once billing is built.
              </p>
            </div>
          )}

          {activeTab === 'security' && (
            <div className="bg-elev rounded-xl border border-app p-6 space-y-5">
              <h3 className="text-[14px] font-semibold text-app">Change Password</h3>
              <div>
                <label htmlFor="current-password" className="block text-[12px] font-medium text-dim mb-1.5">Current Password</label>
                <div className="relative max-w-sm">
                  <input
                    id="current-password"
                    type={showCurrentPassword ? 'text' : 'password'}
                    value={currentPassword}
                    onChange={e => setCurrentPassword(e.target.value)}
                    placeholder="Enter current password"
                    autoComplete="current-password"
                    disabled={changingPassword}
                    className="w-full border border-app rounded-lg px-3 py-2.5 text-[13px] bg-surface pr-10 disabled:opacity-60"
                  />
                  <button type="button" aria-label={showCurrentPassword ? 'Hide password' : 'Show password'}
                    onClick={() => setShowCurrentPassword(!showCurrentPassword)} className="absolute right-3 top-1/2 -translate-y-1/2 text-faint">
                    {showCurrentPassword ? <EyeOff size={15} /> : <Eye size={15} />}
                  </button>
                </div>
              </div>
              <div className="grid grid-cols-1 sm:grid-cols-2 gap-4 max-w-lg">
                <div>
                  <label htmlFor="new-password" className="block text-[12px] font-medium text-dim mb-1.5">New Password</label>
                  <div className="relative">
                    <input
                      id="new-password"
                      type={showNewPassword ? 'text' : 'password'}
                      value={newPassword}
                      onChange={e => setNewPassword(e.target.value)}
                      placeholder="New password (min. 8 characters)"
                      autoComplete="new-password"
                      minLength={8}
                      disabled={changingPassword}
                      className="w-full border border-app rounded-lg px-3 py-2.5 text-[13px] bg-surface pr-10 disabled:opacity-60"
                    />
                    <button type="button" aria-label={showNewPassword ? 'Hide password' : 'Show password'}
                      onClick={() => setShowNewPassword(!showNewPassword)} className="absolute right-3 top-1/2 -translate-y-1/2 text-faint">
                      {showNewPassword ? <EyeOff size={15} /> : <Eye size={15} />}
                    </button>
                  </div>
                </div>
                <div>
                  <label htmlFor="confirm-password" className="block text-[12px] font-medium text-dim mb-1.5">Confirm Password</label>
                  <div className="relative">
                    <input
                      id="confirm-password"
                      type={showConfirmPassword ? 'text' : 'password'}
                      value={confirmPassword}
                      onChange={e => setConfirmPassword(e.target.value)}
                      placeholder="Confirm password"
                      autoComplete="new-password"
                      minLength={8}
                      disabled={changingPassword}
                      className="w-full border border-app rounded-lg px-3 py-2.5 text-[13px] bg-surface pr-10 disabled:opacity-60"
                    />
                    <button type="button" aria-label={showConfirmPassword ? 'Hide password' : 'Show password'}
                      onClick={() => setShowConfirmPassword(!showConfirmPassword)} className="absolute right-3 top-1/2 -translate-y-1/2 text-faint">
                      {showConfirmPassword ? <EyeOff size={15} /> : <Eye size={15} />}
                    </button>
                  </div>
                </div>
              </div>

              {passwordError && (
                <div role="alert" aria-live="polite" className="flex items-center gap-2 text-[12.5px] text-accent-red">
                  <AlertTriangle size={13} /> {passwordError}
                </div>
              )}

              <button
                onClick={submitPasswordChange}
                disabled={changingPassword || !currentPassword || !newPassword || !confirmPassword}
                className="flex items-center gap-2 px-4 py-2 bg-accent-blue text-white text-[13px] font-medium rounded-lg transition-opacity hover:opacity-90 disabled:opacity-50"
              >
                {changingPassword ? <Loader2 size={14} className="animate-spin" /> : passwordSaved ? <Check size={14} /> : null}
                {changingPassword ? 'Updating…' : passwordSaved ? 'Password updated' : 'Update Password'}
              </button>

              <NotYetAvailable>
                Two-factor authentication isn't implemented yet — there's no 2FA endpoint on the
                backend today. Password changes above are real and take effect immediately.
              </NotYetAvailable>
            </div>
          )}
        </div>
      </div>
    </div>
  )
}
