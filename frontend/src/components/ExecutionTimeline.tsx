import { useState } from 'react'
import { ChevronDown } from 'lucide-react'
import ExecutionStatusBadge from './ExecutionStatusBadge'
import type { ExecutionPlanStep } from '../api/chat'

// Phase 6.2, Task 3 — agent_id -> icon. Keys match the real
// agent_registry.py keys where one exists (see
// backend/ai/planner_layer/agent_planner.py's AGENT_CATALOG), plus the
// conceptual "marketing"/"policy" ids that planner produces today.
// Emoji, not a lucide icon, on purpose — AgentBadge.tsx already
// establishes emoji-as-agent-identity as this app's design language
// (see its module comment); reusing that instead of introducing a
// second icon system for agents.
const AGENT_ICONS: Record<string, string> = {
  analytics: '📈',
  inventory: '📦',
  pricing: '💰',
  marketing: '📣',
  ads: '📣',
  listing: '📝',
  policy: '🛡️',
  seller_coach: '🧠',
}
const DEFAULT_AGENT_ICON = '🤖'

interface ExecutionTimelineProps {
  /** Phase 6.1's `ChatResponse.execution_plan`. Renders nothing if
   * missing/empty (Task 6) — callers can pass it through unconditionally. */
  executionPlan?: ExecutionPlanStep[] | null
  className?: string
  /** Starts expanded by default — matches the "Expected Experience" in
   * the spec, where the full plan appears right away. Still fully
   * collapsible by the user afterwards (Task 5). */
  defaultExpanded?: boolean
}

// Phase 6.2, Task 1 — reusable, vertical "which agents will run" list.
// Purely a display of whatever ExecutionPlanStep[] it's given; it never
// fetches, polls, or mutates anything itself. Task 7's "status changes
// should update automatically" falls out for free from that: if a future
// phase re-renders this with the same steps but updated `status` values,
// React updates the existing DOM nodes in place and ExecutionStatusBadge's
// own transition-colors animates the change — no extra state machine
// needed here today.
export default function ExecutionTimeline({ executionPlan, className = '', defaultExpanded = true }: ExecutionTimelineProps) {
  const [expanded, setExpanded] = useState(defaultExpanded)

  if (!executionPlan || executionPlan.length === 0) return null

  // Task 4 — Execution Order. Defensive sort: the backend already
  // returns steps in order (planner_layer/models.py's
  // ExecutionPlan.as_list()), but rendering never assumes that stays true.
  const steps = [...executionPlan].sort((a, b) => a.execution_order - b.execution_order)
  const count = steps.length

  return (
    <div className={`fade-in rounded-lg border border-app bg-surface overflow-hidden ${className}`}>
      <button
        type="button"
        onClick={() => setExpanded(e => !e)}
        aria-expanded={expanded}
        className="w-full flex items-center justify-between gap-2 px-2.5 py-1.5 text-left hover:bg-hover transition-colors"
      >
        <span className="text-[11px] font-medium text-dim">
          Execution Plan{' '}
          <span className="text-faint font-normal">
            ({count} Agent{count === 1 ? '' : 's'})
          </span>
        </span>
        <ChevronDown
          size={13}
          className={`text-faint flex-shrink-0 transition-transform duration-200 ${expanded ? 'rotate-180' : ''}`}
        />
      </button>

      {/* Task 5/9 — collapse/expand via a grid-template-rows transition
          (0fr <-> 1fr) rather than toggling display:none, so the reveal
          animates instead of snapping open/closed. */}
      <div
        className="grid transition-[grid-template-rows] duration-300 ease-in-out"
        style={{ gridTemplateRows: expanded ? '1fr' : '0fr' }}
      >
        <div className="overflow-hidden">
          <ol className="px-2.5 pb-2 pt-0.5">
            {steps.map((step, i) => (
              <li key={`${step.agent_id}-${step.execution_order}`}>
                <div
                  className="fade-in flex items-center gap-2 sm:gap-2.5 rounded-md sm:rounded-none border sm:border-0 border-app bg-elev sm:bg-transparent p-2 sm:p-0 sm:py-1"
                  style={{ animationDelay: `${i * 40}ms` }}
                >
                  <span
                    className="flex-shrink-0 w-5 h-5 rounded-full bg-hover border border-app flex items-center justify-center text-[10px] font-mono-app text-faint"
                    aria-hidden="true"
                  >
                    {step.execution_order}
                  </span>
                  <span
                    className="flex-shrink-0 w-6 h-6 rounded-md bg-hover flex items-center justify-center text-[13px]"
                    aria-hidden="true"
                  >
                    {AGENT_ICONS[step.agent_id] ?? DEFAULT_AGENT_ICON}
                  </span>
                  <div className="min-w-0 flex-1">
                    <div className="text-[12px] font-medium text-app truncate">{step.display_name}</div>
                    <div className="text-[10.5px] text-faint truncate" title={step.reason}>
                      {step.reason}
                    </div>
                  </div>
                  <ExecutionStatusBadge status={step.status} />
                </div>
                {/* Task 4 — a visible down-arrow between consecutive
                    steps to read as a sequence, not just a list.
                    Desktop only; mobile's compact cards (Task 8) stand
                    on their own instead. */}
                {i < steps.length - 1 && (
                  <div className="hidden sm:flex justify-center py-0.5" aria-hidden="true">
                    <ChevronDown size={11} className="text-faint" />
                  </div>
                )}
              </li>
            ))}
          </ol>
        </div>
      </div>
    </div>
  )
}
