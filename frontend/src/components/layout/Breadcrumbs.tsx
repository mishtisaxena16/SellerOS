import { Link } from 'react-router-dom'
import { ChevronRight } from 'lucide-react'

export interface BreadcrumbItem {
  label: string
  to?: string
}

interface BreadcrumbsProps {
  items: BreadcrumbItem[]
}

/**
 * Reusable breadcrumb trail. Purely presentational — callers pass the
 * trail explicitly so it works whether it's derived from module config,
 * a nested route, or a one-off page.
 */
export default function Breadcrumbs({ items }: BreadcrumbsProps) {
  if (!items.length) return null

  return (
    <nav aria-label="Breadcrumb" className="flex items-center gap-1.5 text-[12px] text-faint mb-1.5">
      {items.map((item, i) => {
        const isLast = i === items.length - 1
        return (
          <span key={`${item.label}-${i}`} className="flex items-center gap-1.5">
            {i > 0 && <ChevronRight size={12} className="text-faint flex-shrink-0" />}
            {item.to && !isLast ? (
              <Link to={item.to} className="hover:text-dim transition-colors">
                {item.label}
              </Link>
            ) : (
              <span className={isLast ? 'text-dim' : ''}>{item.label}</span>
            )}
          </span>
        )
      })}
    </nav>
  )
}
