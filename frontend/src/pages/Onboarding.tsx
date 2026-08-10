import { useEffect, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { Loader2, Check, ArrowRight, GraduationCap, Layers } from 'lucide-react'
import { connectMarketplace, type Platform } from '../api/marketplace'
import { ApiError } from '../api/client'
import { usePlatform } from '../context/PlatformContext'
import { useAuth } from '../context/AuthContext'
import { useAmazonConnect } from '../hooks/useAmazonConnect'

interface PlatformDef {
  id: Platform
  name: string
  sub: string
  color: string
  bg: string
  badge: string
  // Amazon connects via the existing "Connect Amazon" OAuth flow instead
  // of a manual credential form — it has no fields to collect here.
  oauth?: boolean
  fields: { key: string; label: string; type?: string }[]
}

const PLATFORMS: PlatformDef[] = [
  {
    id: 'amazon', name: 'Amazon', sub: 'SP-API', color: 'var(--amber)', bg: 'var(--amber-soft)', badge: 'az',
    oauth: true,
    fields: [],
  },
  {
    id: 'flipkart', name: 'Flipkart', sub: 'Seller API', color: '#60a5fa', bg: 'rgba(59,130,246,0.14)', badge: 'fk',
    fields: [
      { key: 'username', label: 'Seller username' },
      { key: 'password', label: 'Password', type: 'password' },
    ],
  },
  {
    id: 'meesho', name: 'Meesho', sub: 'Connector', color: '#f472b6', bg: 'rgba(236,72,153,0.14)', badge: 'me',
    fields: [
      { key: 'username', label: 'Seller username' },
      { key: 'password', label: 'Password', type: 'password' },
    ],
  },
]

export default function Onboarding() {
  const navigate = useNavigate()
  const { refresh, connectedPlatforms } = usePlatform()
  const { setUserType } = useAuth()
  // Skip-for-now already existed and worked with zero marketplace connection required —
  // what was missing was leading with this question instead of credential forms.
  const [welcomeChoice, setWelcomeChoice] = useState<'new' | 'existing' | null>(null)
  const [active, setActive] = useState<Platform | null>(null)
  const [form, setForm] = useState<Record<string, string>>({})
  const [connected, setConnected] = useState<Set<Platform>>(new Set())
  const [submitting, setSubmitting] = useState(false)
  const [error, setError] = useState<string | null>(null)
  // For "No, I'm planning to start": credential forms stay hidden until the person
  // explicitly asks to see them, so onboarding for a new seller ends at a reassuring
  // message rather than a wall of marketplace forms they didn't ask for.
  const [showConnectAnyway, setShowConnectAnyway] = useState(false)

  const { connectAmazon, connecting: connectingAmazon, error: amazonError } = useAmazonConnect()

  // The `connected` set above only tracks connections made during this
  // page's current session (it's how the flipkart/meesho manual-form flow
  // has always worked). Amazon's OAuth connection is persisted on the
  // backend, so on load — and on any refresh of connectedPlatforms — pick
  // up an already-connected Amazon account instead of showing it as
  // disconnected just because this component just mounted.
  useEffect(() => {
    if (connectedPlatforms.includes('amazon')) {
      setConnected(prev => (prev.has('amazon') ? prev : new Set(prev).add('amazon')))
    }
  }, [connectedPlatforms])

  const openForm = (id: Platform) => {
    setActive(id)
    setForm({})
    setError(null)
  }

  // Amazon connects via the existing "Connect Amazon" OAuth flow (no
  // credential form to open); every other platform keeps opening its
  // manual credential form as before.
  const selectPlatform = async (p: PlatformDef) => {
    if (p.oauth) {
      const didConnect = await connectAmazon()
      if (didConnect) setConnected(prev => new Set(prev).add(p.id))
      return
    }
    openForm(p.id)
  }

  const submit = async () => {
    if (!active) return
    setSubmitting(true)
    setError(null)
    try {
      await connectMarketplace(active, form)
      setConnected(prev => new Set(prev).add(active))
      setActive(null)
      await refresh()
    } catch (err) {
      setError(err instanceof ApiError ? err.message : 'Could not connect that account. Please check the details and try again.')
    } finally {
      setSubmitting(false)
    }
  }

  const activeDef = PLATFORMS.find(p => p.id === active)
  const choseNew = welcomeChoice === 'new'

  const chooseWelcome = (choice: 'new' | 'existing') => {
    setWelcomeChoice(choice)
    setUserType(choice)
  }

  return (
    <div className="bg-app text-app min-h-screen font-sans flex flex-col">
      <div className="px-6 md:px-10 h-[76px] flex items-center border-b border-app">
        <div className="flex items-center gap-2.5 font-bold text-[17px] tracking-tight">
          <svg width="26" height="26" viewBox="0 0 24 24" fill="none">
            <path d="M12 2L21 7V17L12 22L3 17V7L12 2Z" stroke="#3b82f6" strokeWidth="1.6" />
          </svg>
          SellerOS
        </div>
      </div>

      {welcomeChoice === null ? (
        <div className="flex-1 flex items-center justify-center px-6 py-14">
          <div className="w-full max-w-[560px]">
            <div className="eyebrow-app mb-5">Step 1 of 2</div>
            <h1 className="text-[28px] md:text-[34px] font-semibold tracking-[-0.02em] mb-3">
              Are you already selling online?
            </h1>
            <p className="text-dim text-[15px] mb-10 max-w-md">
              This just tunes what we show you first — you can connect marketplaces or explore either way.
            </p>
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-5">
              <button
                onClick={() => chooseWelcome('existing')}
                className="card card-interactive cursor-pointer p-6 text-left"
              >
                <div className="w-11 h-11 rounded-[10px] flex items-center justify-center mb-5 bg-accent-blue-soft text-accent-blue">
                  <Layers size={20} />
                </div>
                <div className="text-[16px] font-semibold">Yes, I already sell online</div>
                <div className="text-[13px] text-dim mt-1.5">Connect Amazon, Flipkart or Meesho and get straight into your data.</div>
              </button>
              <button
                onClick={() => chooseWelcome('new')}
                className="card card-interactive cursor-pointer p-6 text-left"
              >
                <div className="w-11 h-11 rounded-[10px] flex items-center justify-center mb-5 bg-accent-green-soft text-accent-green">
                  <GraduationCap size={20} />
                </div>
                <div className="text-[16px] font-semibold">No, I'm planning to start</div>
                <div className="text-[13px] text-dim mt-1.5">Explore Seller Coach and Product Studio — connect a marketplace whenever you're ready.</div>
              </button>
            </div>
            <div className="flex justify-end mt-8">
              <button onClick={() => navigate('/dashboard')} className="text-[14px] text-dim hover:text-app transition-colors">
                Skip for now
              </button>
            </div>
          </div>
        </div>
      ) : choseNew && !showConnectAnyway ? (
        // New seller: no credential forms unless they ask. This is the whole
        // onboarding for them — a reassurance message, not a wall of forms.
        <div className="flex-1 flex items-center justify-center px-6 py-14">
          <div className="w-full max-w-[560px] text-center">
            <div className="w-14 h-14 rounded-2xl bg-accent-green-soft text-accent-green flex items-center justify-center mx-auto mb-6">
              <GraduationCap size={26} />
            </div>
            <h1 className="text-[26px] md:text-[30px] font-semibold tracking-[-0.02em] mb-3">
              Great — you can start using SellerOS right away
            </h1>
            <p className="text-dim text-[15px] mb-6 max-w-md mx-auto">
              Nothing here is blocked while you get set up.
            </p>
            <div className="flex flex-col gap-2.5 text-left max-w-xs mx-auto mb-8">
              {['Seller Coach', 'Product Studio', 'Learning resources'].map(item => (
                <div key={item} className="flex items-center gap-2.5 text-[14px] text-app">
                  <Check size={16} className="text-accent-green flex-shrink-0" />
                  {item}
                </div>
              ))}
            </div>
            <p className="text-dim text-[13.5px] mb-8 max-w-md mx-auto">
              You'll be able to connect Amazon, Flipkart or Meesho any time from the
              Marketplace section in the sidebar.
            </p>
            <div className="flex flex-col items-center gap-4">
              <button
                onClick={() => navigate('/dashboard')}
                className="btn-primary-app px-6 py-3 text-[14px] flex items-center gap-2"
              >
                Continue <ArrowRight size={15} />
              </button>
              <button
                onClick={() => setShowConnectAnyway(true)}
                className="text-[13.5px] text-dim hover:text-app transition-colors"
              >
                Actually, I'd like to connect a marketplace now
              </button>
            </div>
          </div>
        </div>
      ) : (
      <div className="flex-1 flex items-center justify-center px-6 py-14">
        <div className="w-full max-w-[760px]">
          <div className="eyebrow-app mb-5">Step 2 of 2</div>
          <h1 className="text-[28px] md:text-[34px] font-semibold tracking-[-0.02em] mb-3">
            {choseNew ? 'Connect a marketplace whenever you\'re ready' : 'Connect a marketplace to get started'}
          </h1>
          <p className="text-dim text-[15px] mb-10 max-w-lg">
            {choseNew
              ? "No rush — Seller Coach and Product Studio work without a marketplace connected. Connect Amazon, Flipkart or Meesho here or later from Settings, whenever you're ready to go live."
              : 'Pick the seller accounts you want SellerOS to manage. You can connect the rest, or add more later, from Settings.'}
          </p>

          <div className="grid grid-cols-1 sm:grid-cols-3 gap-5 mb-8">
            {PLATFORMS.map(p => {
              const isConnected = connected.has(p.id)
              const isConnectingThis = p.oauth && connectingAmazon
              return (
                <button
                  key={p.id}
                  onClick={() => !isConnected && !isConnectingThis && selectPlatform(p)}
                  disabled={isConnected || isConnectingThis}
                  className={`card p-6 text-left ${isConnected ? '' : 'card-interactive cursor-pointer'} ${isConnectingThis ? 'opacity-70' : ''}`}
                  style={isConnected ? { borderColor: 'var(--green)' } : undefined}
                >
                  <div className="flex items-center justify-between mb-5">
                    <div className="w-11 h-11 rounded-[10px] flex items-center justify-center font-bold text-[13px]" style={{ background: p.bg, color: p.color }}>
                      {p.badge}
                    </div>
                    {isConnected && (
                      <span className="w-6 h-6 rounded-full flex items-center justify-center bg-accent-green-soft text-accent-green">
                        <Check size={14} />
                      </span>
                    )}
                  </div>
                  <div className="text-[16px] font-semibold">{p.name}</div>
                  <div className="text-[12px] text-faint font-mono-app mt-0.5">{p.sub}</div>
                  <div className="text-[13px] mt-4 flex items-center gap-1.5" style={{ color: isConnected ? 'var(--green)' : 'var(--text-dim)' }}>
                    {isConnectingThis && <Loader2 size={13} className="animate-spin" />}
                    {isConnected
                      ? 'Connected'
                      : isConnectingThis
                        ? 'Connecting…'
                        : p.oauth
                          ? 'Connect Amazon →'
                          : 'Connect account →'}
                  </div>
                </button>
              )
            })}
          </div>

          {!connectingAmazon && amazonError && (
            <div className="text-[13px] text-accent-red mb-8 -mt-4">{amazonError}</div>
          )}

          {activeDef && (
            <div className="card p-6 mb-8">
              <h3 className="text-[16px] font-semibold mb-4">Connect {activeDef.name}</h3>
              <div className="flex flex-col gap-4">
                {activeDef.fields.map(f => (
                  <div key={f.key}>
                    <label className="block text-[13px] text-dim mb-1.5">{f.label}</label>
                    <input
                      type={f.type || 'text'}
                      value={form[f.key] || ''}
                      onChange={e => setForm(prev => ({ ...prev, [f.key]: e.target.value }))}
                      className="input-app w-full px-3.5 py-2.5 text-[14px]"
                    />
                  </div>
                ))}
                {error && <div className="text-[13px] text-accent-red">{error}</div>}
                <div className="flex gap-3 mt-1">
                  <button
                    onClick={submit}
                    disabled={submitting}
                    className="btn-primary-app px-5 py-2.5 text-[14px] flex items-center gap-2"
                  >
                    {submitting && <Loader2 size={14} className="animate-spin" />}
                    {submitting ? 'Connecting…' : 'Connect'}
                  </button>
                  <button onClick={() => setActive(null)} className="btn-ghost-app px-5 py-2.5 text-[14px]">Cancel</button>
                </div>
              </div>
            </div>
          )}

          <div className="flex items-center justify-between border-t border-app pt-8">
            <button onClick={() => navigate('/dashboard')} className="text-[14px] text-dim hover:text-app transition-colors">
              {choseNew ? "Connect later — take me in" : 'Skip for now'}
            </button>
            <button
              onClick={() => navigate('/dashboard')}
              disabled={!choseNew && connected.size === 0}
              className="btn-primary-app px-6 py-3 text-[14px] flex items-center gap-2 disabled:opacity-40"
            >
              Continue to dashboard <ArrowRight size={15} />
            </button>
          </div>
        </div>
      </div>
      )}
    </div>
  )
}
