import { Database } from 'lucide-react'

// Phase 6.3A, Task 3 — standalone, reusable source/tag list.
//
// Purely presentational: renders whatever strings it's given
// ("Sales Analytics", "Inventory Report", "Marketplace Data",
// "Knowledge Base Reports", ...). No relation to the existing
// SourceList.tsx / inferSources() (Phase 4), which derives sources
// from `intent`/`marketplace` metadata on a ChatResponse — that's API
// shaped and out of scope for this phase. This component only knows
// about `string[]`.

export interface SourceTagsProps {
  sources: string[]
  /** Show the small "Sources" label + icon above the tag list. */
  showLabel?: boolean
  className?: string
}

export default function SourceTags({ sources, showLabel = true, className = '' }: SourceTagsProps) {
  if (!sources || sources.length === 0) return null

  return (
    <div className={`fade-in ${className}`}>
      {showLabel && (
        <div className="flex items-center gap-1 mb-1.5 text-[11px] font-medium text-dim">
          <Database size={11} />
          Sources
        </div>
      )}
      <div className="flex flex-wrap gap-1.5">
        {sources.map((source, i) => (
          <span
            key={`${source}-${i}`}
            className="inline-flex items-center px-2 py-0.5 rounded-md text-[10.5px] font-medium text-dim bg-surface border border-app whitespace-nowrap"
          >
            {source}
          </span>
        ))}
      </div>
    </div>
  )
}
