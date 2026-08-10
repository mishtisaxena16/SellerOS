import { useEffect, useState } from 'react'
import { Loader2 } from 'lucide-react'

// Phase 4 §6 — replaces a static "Thinking…" label with a short rotating
// sequence so the compact loading indicator (used in the collapsed
// message row, before AgentTimeline's full trace has rendered) still
// reads as "several systems are doing something" rather than one spinner.
const CAPTIONS = [
  'Thinking...',
  'Selecting Agent...',
  'Searching Knowledge...',
  'Ranking Documents...',
  'Preparing Response...',
]

const CAPTION_INTERVAL_MS = 1100

export default function LoadingTimeline({ className = '' }: { className?: string }) {
  const [index, setIndex] = useState(0)

  useEffect(() => {
    const id = window.setInterval(() => {
      setIndex(i => (i + 1) % CAPTIONS.length)
    }, CAPTION_INTERVAL_MS)
    return () => window.clearInterval(id)
  }, [])

  return (
    <div className={`flex items-center gap-1.5 ${className}`}>
      <Loader2 size={13} className="animate-spin text-dim flex-shrink-0" />
      <span key={index} className="fade-in text-[12px] text-faint">{CAPTIONS[index]}</span>
    </div>
  )
}
