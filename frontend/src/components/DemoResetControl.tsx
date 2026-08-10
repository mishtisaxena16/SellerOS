// ============================================================================
// SellerOS — Phase 7.7B: Demo Reset UI Integration
// ============================================================================
// Wires the existing Phase 7.7A reset infrastructure (../demo/demoReset,
// ../demo/demoState) into the interface: a "Reset Demo" action, a
// confirmation dialog, and a success toast. No dataset, API, connector,
// Playwright, RAG, or AI Router code is touched here — this component only
// calls the already-built `resetEntireDemo()` and re-uses the app's
// existing surface/border/accent design tokens (see index.css) so it reads
// as an admin/demo utility rather than a normal seller-facing feature.
// ============================================================================

import { useState } from 'react'
import { RotateCcw, AlertTriangle, CheckCircle2, X } from 'lucide-react'
import { resetEntireDemo } from '../demo/demoReset'
import { resetAiSession } from '../demo/aiSessionReset'

interface DemoResetControlProps {
  /** Sidebar renders this as an icon-only affordance when collapsed. */
  collapsed?: boolean
}

export default function DemoResetControl({ collapsed = false }: DemoResetControlProps) {
  const [confirmOpen, setConfirmOpen] = useState(false)
  const [toastVisible, setToastVisible] = useState(false)

  function handleConfirmReset() {
    // Phase 7.7A's resetEntireDemo() restores orders, inventory, listings,
    // business intelligence, selected seller, scenario, and the mock
    // mutation log back to INITIAL_DEMO_STATE in the live in-memory store —
    // synchronously, with no API call and no browser reload — and notifies
    // every subscribeToDemoState() listener so any already-mounted screen
    // reading from the live store re-renders immediately.
    resetEntireDemo()
    // Phase 7.7C: also broadcast a fresh frontend-only AI session so every
    // mounted AI surface (FloatingAI's chat thread, execution timeline,
    // result cards, and seller-coach summary) clears back to its
    // just-opened state. No backend call, no RAG re-index.
    resetAiSession()
    setConfirmOpen(false)
    setToastVisible(true)
    window.setTimeout(() => setToastVisible(false), 3500)
  }

  return (
    <>
      {/* Demo utility affordance — visually separated from the real nav
          items above it, deliberately muted rather than a primary action. */}
      <div className={`border-t border-app ${collapsed ? 'px-2 py-2' : 'px-3 py-3'}`}>
        {!collapsed && (
          <div className="text-[10px] font-semibold text-faint uppercase tracking-wider mb-2">Demo</div>
        )}
        <button
          type="button"
          onClick={() => setConfirmOpen(true)}
          title="Reset Demo"
          aria-label="Reset Demo"
          className={`w-full flex items-center gap-2.5 rounded-lg text-dim bg-hover hover:text-app transition-colors border border-dashed border-app ${
            collapsed ? 'justify-center p-2' : 'px-3 py-2'
          }`}
        >
          <RotateCcw size={15} className="flex-shrink-0" strokeWidth={1.75} />
          {!collapsed && <span className="text-[12.5px] font-medium">Reset Demo</span>}
        </button>
      </div>

      {/* Confirmation dialog */}
      {confirmOpen && (
        <div className="fixed inset-0 z-50 flex items-center justify-center" role="dialog" aria-modal="true" aria-labelledby="reset-demo-title">
          <div className="absolute inset-0 bg-black/40" onClick={() => setConfirmOpen(false)} />
          <div className="relative w-full max-w-sm mx-4 bg-elev border border-app rounded-2xl shadow-app fade-in">
            <div className="p-5">
              <div className="flex items-start gap-3">
                <div className="w-9 h-9 rounded-lg bg-accent-amber-soft flex items-center justify-center flex-shrink-0 text-accent-amber">
                  <AlertTriangle size={16} />
                </div>
                <div className="min-w-0">
                  <h3 id="reset-demo-title" className="text-[14px] font-semibold text-app">Reset the demo?</h3>
                  <p className="text-[12.5px] text-dim mt-1 leading-relaxed">
                    Reset the demo to its original state? All temporary demo changes will be lost.
                  </p>
                </div>
              </div>
              <div className="flex items-center justify-end gap-2 mt-5">
                <button
                  type="button"
                  onClick={() => setConfirmOpen(false)}
                  className="btn-ghost-app text-[12.5px] font-medium px-4 py-2"
                >
                  Cancel
                </button>
                <button
                  type="button"
                  onClick={handleConfirmReset}
                  className="btn-primary-app text-[12.5px] px-4 py-2"
                >
                  Reset Demo
                </button>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Success toast — no existing app-wide notification system was found
          to reuse, so this is a small, self-contained one scoped to this
          control. */}
      {toastVisible && (
        <div className="fixed bottom-5 right-5 z-[60] fade-in" role="status" aria-live="polite">
          <div className="flex items-center gap-2.5 bg-elev border border-app rounded-xl shadow-app px-4 py-3">
            <span className="text-accent-green flex-shrink-0">
              <CheckCircle2 size={16} />
            </span>
            <span className="text-[12.5px] font-medium text-app">Demo has been reset successfully.</span>
            <button
              type="button"
              onClick={() => setToastVisible(false)}
              aria-label="Dismiss"
              className="text-faint hover:text-app ml-1 flex-shrink-0"
            >
              <X size={13} />
            </button>
          </div>
        </div>
      )}
    </>
  )
}
