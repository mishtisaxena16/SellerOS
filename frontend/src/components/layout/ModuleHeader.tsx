import type { LucideIcon } from 'lucide-react'
import type { ReactNode } from 'react'
import Breadcrumbs, { type BreadcrumbItem } from './Breadcrumbs'
import PageTitle from './PageTitle'
import ActionBar from './ActionBar'

interface ModuleHeaderProps {
  title: string
  description?: string
  icon?: LucideIcon
  iconClassName?: string
  badge?: ReactNode
  breadcrumbs?: BreadcrumbItem[]
  actions?: ReactNode
  className?: string
}

/**
 * Reusable module header: Breadcrumbs (optional) → Title/description →
 * global action area, laid out the way existing pages already do it
 * (flex row, title left, actions right) so wrapping a page in this
 * doesn't change its look.
 */
export default function ModuleHeader({
  title,
  description,
  icon,
  iconClassName,
  badge,
  breadcrumbs,
  actions,
  className = '',
}: ModuleHeaderProps) {
  return (
    <div className={`mb-6 ${className}`}>
      {breadcrumbs && <Breadcrumbs items={breadcrumbs} />}
      <div className="flex flex-wrap items-center justify-between gap-3">
        <PageTitle title={title} description={description} icon={icon} iconClassName={iconClassName} badge={badge} />
        <ActionBar>{actions}</ActionBar>
      </div>
    </div>
  )
}
