import type { ReactNode } from 'react'

interface ActionBarProps {
  children?: ReactNode
  className?: string
}

/**
 * Reusable slot for a module's primary actions (buttons, filters, etc.)
 * rendered on the right side of the ModuleHeader. Renders nothing when
 * empty so pages without actions don't get stray layout.
 */
export default function ActionBar({ children, className = '' }: ActionBarProps) {
  if (!children) return null
  return (
    <div className={`flex flex-wrap items-center gap-2 ${className}`}>
      {children}
    </div>
  )
}
