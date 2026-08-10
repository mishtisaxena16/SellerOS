import type { ReactNode } from 'react'
import { Link } from 'react-router-dom'
import { PlugZap } from 'lucide-react'

// Shared "no marketplace connected" state for Orders, Inventory, and Business
// Intelligence — all three hit the same backend 409 for this and previously
// each drew their own copy of the same icon-in-a-box block. Centralizing it
// means the illustration only needs improving once, and the three pages can't
// drift out of sync with each other.
export default function EmptyMarketplaceState({
  message,
  title = 'No marketplace connected',
  ctaLabel = 'Connect a marketplace',
  ctaTo = '/onboarding',
}: {
  message: string
  title?: string
  ctaLabel?: string
  ctaTo?: string
}) {
  return (
    <div className="p-6 fade-in">
      <div className="card p-10 flex flex-col items-center text-center gap-3 max-w-md mx-auto mt-10">
        <Illustration />
        <h3 className="text-[15px] font-semibold text-app mt-2">{title}</h3>
        <p className="text-[13px] text-dim">{message}</p>
        <Link to={ctaTo} className="mt-2 px-4 py-2 btn-primary-app text-[13px] rounded-lg">{ctaLabel}</Link>
      </div>
    </div>
  )
}

// A small illustration rather than a bare icon: a plug at the center with
// three dashed lines reaching out to muted platform dots — reads as
// "waiting to connect" rather than "error". Kept lightweight (plain SVG,
// no image asset) so it doesn't add a network request to an empty state.
function Illustration(): ReactNode {
  const dots = [
    { cx: 30, cy: 30, color: '#FF9900' },  // amazon
    { cx: 90, cy: 22, color: '#2874F0' },  // flipkart
    { cx: 96, cy: 78, color: '#9B2F8A' },  // meesho
  ]
  return (
    <svg width="120" height="100" viewBox="0 0 120 100" fill="none" xmlns="http://www.w3.org/2000/svg" aria-hidden="true" focusable="false">
      {dots.map((d, i) => (
        <line
          key={i}
          x1="60" y1="55" x2={d.cx} y2={d.cy}
          stroke="var(--border)" strokeWidth="1.5" strokeDasharray="3 4"
        />
      ))}
      {dots.map((d, i) => (
        <circle key={i} cx={d.cx} cy={d.cy} r="6" fill={d.color} opacity="0.28" />
      ))}
      <circle cx="60" cy="55" r="26" fill="var(--blue-soft)" />
      <foreignObject x="44" y="39" width="32" height="32">
        <div className="w-8 h-8 flex items-center justify-center text-accent-blue">
          <PlugZap size={20} />
        </div>
      </foreignObject>
    </svg>
  )
}
