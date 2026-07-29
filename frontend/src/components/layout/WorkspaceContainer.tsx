import type { ReactNode } from 'react'

interface WorkspaceContainerProps {
  children: ReactNode
  /** Render an empty state instead of children, e.g. no data/no marketplace connected. */
  emptyState?: ReactNode
  className?: string
}

/**
 * Reusable workspace/content region. Matches the `fade-in` treatment
 * existing pages already apply to their content, so wrapping a page
 * doesn't change how it looks or animates in.
 */
export default function WorkspaceContainer({ children, emptyState, className = '' }: WorkspaceContainerProps) {
  return (
    <div className={`fade-in ${className}`}>
      {emptyState ?? children}
    </div>
  )
}
