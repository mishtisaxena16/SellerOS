import type { LucideIcon } from 'lucide-react'
import type { ReactNode } from 'react'

interface PageTitleProps {
  title: string
  description?: string
  icon?: LucideIcon
  iconClassName?: string
  /** Optional inline badge/pill rendered next to the title (e.g. "AI-Powered"). */
  badge?: ReactNode
}

/**
 * Reusable page/module title block: matches the `h2` + dim subtitle
 * pattern already used across existing pages (Inventory, Settings,
 * Marketing Hub, Sustainability, ...), extracted so new and wrapped
 * pages share one implementation instead of re-typing the same classes.
 */
export default function PageTitle({ title, description, icon: Icon, iconClassName = 'text-accent-blue', badge }: PageTitleProps) {
  return (
    <div>
      <div className="flex items-center gap-2">
        <h2 className="text-xl font-bold text-app flex items-center gap-2">
          {Icon && <Icon size={22} className={iconClassName} />}
          {title}
        </h2>
        {badge}
      </div>
      {description && <p className="text-[13px] text-dim mt-0.5">{description}</p>}
    </div>
  )
}
