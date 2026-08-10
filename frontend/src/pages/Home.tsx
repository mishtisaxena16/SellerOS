import { Link } from 'react-router-dom'
import { useTheme } from '../context/ThemeContext'
import { useAuth } from '../context/AuthContext'
import { usePlatform, PLATFORM_LABELS } from '../context/PlatformContext'
import { SUPPORTED_PLATFORMS } from '../api/marketplace'
import { Moon, Sun, ArrowUpRight, Command, Workflow, Layers, Cpu, Shield, PlugZap, GraduationCap, Wand2 } from 'lucide-react'

const marketplaces = [
  { id: 'az', name: 'Amazon', sub: 'SP-API', color: 'var(--amber)', bg: 'var(--amber-soft)' },
  { id: 'fk', name: 'Flipkart', sub: 'Seller API', color: '#60a5fa', bg: 'rgba(59,130,246,0.14)' },
  { id: 'me', name: 'Meesho', sub: 'Connector', color: '#f472b6', bg: 'rgba(236,72,153,0.14)' },
]

const steps = [
  { n: '01', title: 'Connect your marketplaces', body: 'Link Amazon, Flipkart and Meesho in minutes through the unified Connector Layer — no scripts, no spreadsheets.' },
  { n: '02', title: 'Import & understand products', body: 'Listings, inventory and orders sync automatically. The Supervisor builds a live model of your catalog and performance.' },
  { n: '03', title: 'Agents analyze the data', body: 'The Orchestrator dispatches work to specialized agents — pricing, forecasting, ads — each reasoning over your real business context.' },
  { n: '04', title: 'Tasks flow to marketplaces', body: 'Actions route through the Tool Layer and Connector Layer straight to marketplace APIs. Agents never touch a raw endpoint.' },
  { n: '05', title: 'You receive decisions', body: 'SellerOS surfaces clear recommendations and executed actions. You approve strategy — the AI handles repetitive execution.' },
]

const agents = [
  { icon: Command, color: '#60a5fa', bg: 'rgba(59,130,246,0.14)', name: 'Supervisor', body: 'Reads your entire business state and delegates work to every specialized agent through the Orchestrator.' },
  { icon: Layers, color: '#c084fc', bg: 'rgba(168,85,247,0.14)', name: 'Listing Agent', body: 'Generates optimized titles, descriptions, bullets and SEO content.' },
  { icon: Workflow, color: '#34d399', bg: 'rgba(52,211,153,0.14)', name: 'Pricing Agent', body: 'Optimizes pricing and protects profitability across channels.' },
  { icon: Cpu, color: '#f59e0b', bg: 'rgba(245,158,11,0.14)', name: 'Inventory Agent', body: 'Tracks stock and predicts stock-outs before they cost you a sale.' },
]

const modules = [
  { icon: '▧', color: '#60a5fa', bg: 'rgba(59,130,246,0.14)', name: 'Product Studio', body: 'Create, optimize and publish listings across every marketplace from one canvas.' },
  { icon: '⚙', color: '#c084fc', bg: 'rgba(168,85,247,0.14)', name: 'Operations', body: 'Inventory health, order workflows and fulfillment automation running quietly in the background.' },
  { icon: '📣', color: '#f472b6', bg: 'rgba(236,72,153,0.14)', name: 'Marketing Hub', body: 'Launch and tune ad campaigns with the Ads Agent optimizing ACoS and ROAS automatically.' },
  { icon: '▤', color: '#60a5fa', bg: 'rgba(59,130,246,0.14)', name: 'Business Intelligence', body: 'Real-time KPIs, demand forecasts and margin visibility across every channel you sell on.' },
  { icon: '🎓', color: '#34d399', bg: 'rgba(52,211,153,0.14)', name: 'Seller Coach', body: 'Marketplace policy, GST and compliance guidance, grounded in your seller knowledge base.' },
  { icon: '🌱', color: '#34d399', bg: 'rgba(52,211,153,0.14)', name: 'Sustainability', body: 'Packaging, returns and shipment-consolidation recommendations grounded in your own metrics.' },
]

export default function Home() {
  const { theme, toggleTheme } = useTheme()
  const { isAuthenticated, user } = useAuth()
  const { connectedPlatforms } = usePlatform()

  return (
    <div className="bg-app text-app min-h-screen font-sans">
      {/* Nav */}
      <nav className="sticky top-0 z-50 border-b border-app backdrop-blur-md" style={{ backgroundColor: 'color-mix(in srgb, var(--bg) 85%, transparent)' }}>
        <div className="max-w-[1240px] mx-auto px-6 md:px-10 h-[76px] flex items-center justify-between">
          <div className="flex items-center gap-2.5 font-bold text-[17px] tracking-tight">
            <svg width="26" height="26" viewBox="0 0 24 24" fill="none">
              <path d="M12 2L21 7V17L12 22L3 17V7L12 2Z" stroke="#3b82f6" strokeWidth="1.6" />
            </svg>
            SellerOS
          </div>
          <div className="hidden md:flex gap-9 text-[14px] text-dim">
            <a href="#modules" className="hover:text-app transition-colors">Features</a>
            <a href="#agents" className="hover:text-app transition-colors">AI Agents</a>
            <a href="#marketplaces" className="hover:text-app transition-colors">Marketplaces</a>
          </div>
          <div className="flex items-center gap-5">
            <button
              onClick={toggleTheme}
              aria-label="Toggle theme"
              className="w-8 h-8 rounded-full flex items-center justify-center border border-app border-app-hover text-dim hover:text-app transition-colors"
            >
              {theme === 'dark' ? <Sun size={15} /> : <Moon size={15} />}
            </button>
            {isAuthenticated ? (
              <Link to="/dashboard" className="btn-primary-app text-[14px] px-5 py-2.5">Go to dashboard</Link>
            ) : (
              <>
                <Link to="/login" className="text-[14px] text-dim hover:text-app transition-colors">Login</Link>
                <Link to="/register" className="btn-primary-app text-[14px] px-5 py-2.5">Get Started</Link>
              </>
            )}
          </div>
        </div>
      </nav>

      {/* Status strip — only for logged-in visitors revisiting Home. The rest of the
          page below is the same marketing content everyone sees; this is a thin,
          skippable layer on top of it rather than a second, parallel homepage. */}
      {isAuthenticated && (
        <section className="px-6 md:px-10 py-5 border-b border-app bg-surface">
          <div className="max-w-[1240px] mx-auto flex flex-wrap items-center justify-between gap-4">
            <div>
              <div className="text-[15px] font-semibold text-app">
                Welcome back{user?.business_name ? `, ${user.business_name.split(' ')[0]}` : ''}
              </div>
              <div className="flex flex-wrap items-center gap-x-3.5 gap-y-1 mt-1">
                {SUPPORTED_PLATFORMS.map(p => {
                  const isConnected = connectedPlatforms.includes(p)
                  return (
                    <span key={p} className="flex items-center gap-1.5 text-[12px]" style={{ color: isConnected ? undefined : 'var(--text-faint)' }}>
                      <span
                        className="w-1.5 h-1.5 rounded-full flex-shrink-0"
                        style={{ backgroundColor: isConnected ? 'var(--green)' : 'var(--text-faint)' }}
                      />
                      <span className={isConnected ? 'text-app' : 'text-faint'}>{PLATFORM_LABELS[p]}</span>
                    </span>
                  )
                })}
              </div>
            </div>
            <div className="flex flex-wrap gap-2.5">
              <Link to="/dashboard" className="btn-primary-app text-[13px] px-4 py-2 flex items-center gap-1.5">
                Go to dashboard <ArrowUpRight size={13} />
              </Link>
              <Link to="/product-studio" className="btn-ghost-app text-[13px] px-4 py-2 flex items-center gap-1.5">
                <Wand2 size={13} /> Product Studio
              </Link>
              <Link to="/seller-coach" className="btn-ghost-app text-[13px] px-4 py-2 flex items-center gap-1.5">
                <GraduationCap size={13} /> Seller Coach
              </Link>
              {connectedPlatforms.length === 0 && (
                <Link to="/onboarding" className="btn-ghost-app text-[13px] px-4 py-2 flex items-center gap-1.5">
                  <PlugZap size={13} /> Connect marketplace
                </Link>
              )}
            </div>
          </div>
        </section>
      )}

      {/* Hero */}
      <section className="pt-24 pb-20 px-6 md:px-10 border-b border-app" id="marketplaces">
        <div className="max-w-[1240px] mx-auto">
          <div className="mb-16">
            <div className="eyebrow-app mb-5">Trusted Integrations</div>
            <h1 className="text-[36px] md:text-[52px] leading-[1.08] tracking-[-0.03em] font-semibold">
              Every marketplace,<br /><span className="text-faint">one connected workspace.</span>
            </h1>
          </div>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
            {marketplaces.map(m => (
              <div key={m.id} className="card card-interactive p-7">
                <div className="flex items-center justify-between mb-7">
                  <div className="flex items-center gap-3.5">
                    <div className="w-11 h-11 rounded-[10px] flex items-center justify-center font-bold text-[13px]" style={{ background: m.bg, color: m.color }}>
                      {m.id}
                    </div>
                    <div>
                      <div className="text-[17px] font-semibold">{m.name}</div>
                      <div className="text-[12px] text-faint font-mono-app mt-0.5">{m.sub}</div>
                    </div>
                  </div>
                  <div className="live-dot-app" style={{ color: 'var(--amber)' }}>IN DEVELOPMENT</div>
                </div>
                <ul className="flex flex-col gap-3 mb-7">
                  {['Inventory Sync', 'Orders Sync', 'Analytics', 'Pricing'].map(item => (
                    <li key={item} className="flex items-center gap-2.5 text-[14px] text-dim">
                      <span className="text-accent-green text-[12px] font-bold">✓</span>{item}
                    </li>
                  ))}
                </ul>
                <div className="flex justify-between text-[12px] text-faint font-mono-app border-t border-app pt-5">
                  <span>Connector built</span><span>Pre-launch</span>
                </div>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* How it works */}
      <section className="py-20 px-6 md:px-10 border-b border-app">
        <div className="max-w-[1240px] mx-auto grid grid-cols-1 md:grid-cols-[0.9fr_1.1fr] gap-16">
          <div>
            <div className="eyebrow-app mb-5">How SellerOS Works</div>
            <h2 className="text-[32px] md:text-[44px] leading-[1.08] tracking-[-0.03em] font-semibold">
              From physical chaos<br /><span className="text-faint">to autonomous order.</span>
            </h2>
          </div>
          <div className="flex flex-col">
            {steps.map((s, i) => (
              <div key={s.n} className={`grid grid-cols-[44px_1fr] gap-5 py-7 ${i !== 0 ? 'border-t border-app' : ''}`}>
                <div className="font-mono-app text-[13px] text-accent-blue font-semibold pt-0.5">{s.n}</div>
                <div>
                  <h3 className="text-[19px] font-semibold mb-2 tracking-[-0.01em]">{s.title}</h3>
                  <p className="text-[14.5px] text-dim leading-relaxed">{s.body}</p>
                </div>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* Agents */}
      <section className="py-20 px-6 md:px-10 border-b border-app" id="agents">
        <div className="max-w-[1240px] mx-auto">
          <div className="mb-14">
            <div className="eyebrow-app mb-5">AI Agents</div>
            <h2 className="text-[32px] md:text-[44px] leading-[1.08] tracking-[-0.03em] font-semibold">
              Not chatbots <span className="text-faint">— operators.</span>
            </h2>
          </div>
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-5">
            {agents.map(a => {
              const Icon = a.icon
              return (
                <div key={a.name} className="card card-interactive p-6">
                  <div className="w-10 h-10 rounded-[10px] flex items-center justify-center mb-5" style={{ background: a.bg, color: a.color }}>
                    <Icon size={17} />
                  </div>
                  <h3 className="text-[16px] font-semibold mb-2">{a.name}</h3>
                  <p className="text-[13.5px] text-dim leading-relaxed">{a.body}</p>
                </div>
              )
            })}
          </div>
        </div>
      </section>

      {/* Modules */}
      <section className="py-20 px-6 md:px-10 border-b border-app" id="modules">
        <div className="max-w-[1240px] mx-auto">
          <div className="mb-14">
            <div className="eyebrow-app mb-5">Core Modules</div>
            <h2 className="text-[32px] md:text-[44px] leading-[1.08] tracking-[-0.03em] font-semibold">
              Six modules.<br /><span className="text-faint">One operating system.</span>
            </h2>
          </div>
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-5">
            {modules.map(m => (
              <div key={m.name} className="card card-interactive p-6">
                <div className="flex items-center justify-between mb-5">
                  <div className="w-9 h-9 rounded-[10px] flex items-center justify-center text-[15px]" style={{ background: m.bg, color: m.color }}>
                    {m.icon}
                  </div>
                  <ArrowUpRight size={15} className="text-faint" />
                </div>
                <h3 className="text-[16px] font-semibold mb-2">{m.name}</h3>
                <p className="text-[13.5px] text-dim leading-relaxed">{m.body}</p>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* CTA */}
      <section className="py-24 px-6 md:px-10 border-b border-app">
        <div className="max-w-[1240px] mx-auto">
          <div className="card p-10 md:p-16 text-center flex flex-col items-center">
            <div className="eyebrow-app mb-5 justify-center">Get Started Today</div>
            <h2 className="text-[28px] md:text-[40px] leading-[1.1] tracking-[-0.03em] font-semibold max-w-xl">
              Ready to run your entire marketplace business with AI?
            </h2>
            <p className="text-dim text-[16px] leading-relaxed max-w-md mt-5">
              Connect Amazon, Flipkart and Meesho, and let your AI team take over the repetitive work — you stay in control of every decision that matters.
            </p>
            <div className="flex flex-wrap gap-4 mt-8 justify-center">
              {isAuthenticated ? (
                <Link to="/dashboard" className="btn-primary-app text-[15px] px-7 py-3.5">Go to dashboard</Link>
              ) : (
                <Link to="/register" className="btn-primary-app text-[15px] px-7 py-3.5">Get Started — it's free</Link>
              )}
              <a href="#" className="btn-ghost-app text-[15px] px-7 py-3.5 flex items-center">Talk to us</a>
            </div>
          </div>
        </div>
      </section>

      {/* Footer */}
      <footer className="px-6 md:px-10 py-14">
        <div className="max-w-[1240px] mx-auto">
          <div className="grid grid-cols-2 md:grid-cols-5 gap-10 mb-10">
            <div className="col-span-2">
              <div className="flex items-center gap-2.5 font-bold text-[16px] mb-3">
                <svg width="22" height="22" viewBox="0 0 24 24" fill="none">
                  <path d="M12 2L21 7V17L12 22L3 17V7L12 2Z" stroke="#3b82f6" strokeWidth="1.6" />
                </svg>
                SellerOS
              </div>
              <p className="text-dim text-[14px] leading-relaxed max-w-xs mb-4">
                The AI Operating System for marketplace sellers. One workspace, every marketplace, AI runs everything.
              </p>
              <div className="flex items-center gap-1.5 text-[13px] text-dim">
                <Shield size={13} /> Guardrailed agent actions
              </div>
            </div>
            {[
              { h: 'Product', links: ['Features', 'AI Agents', 'Core Modules', 'Marketplaces'] },
              { h: 'Developers', links: ['Documentation', 'Architecture', 'API Reference'] },
              { h: 'Company', links: ['About', 'Contact', 'Privacy', 'Terms'] },
            ].map(col => (
              <div key={col.h}>
                <h4 className="font-mono-app text-[11px] tracking-[0.1em] uppercase text-faint mb-5">{col.h}</h4>
                {col.links.map(l => (
                  <a key={l} href="#" className="block text-[14px] text-dim hover:text-app transition-colors mb-3.5">{l}</a>
                ))}
              </div>
            ))}
          </div>
          <div className="flex flex-col sm:flex-row justify-between gap-2 py-6 border-t border-app text-[13px] text-faint">
            <span>© 2026 SellerOS. All rights reserved.</span>
            <span>Supporting Amazon · Flipkart · Meesho</span>
          </div>
        </div>
      </footer>
    </div>
  )
}
