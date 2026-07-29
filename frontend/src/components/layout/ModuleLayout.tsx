import type { ReactNode } from 'react'
import type { LucideIcon } from 'lucide-react'
import ModuleHeader from './ModuleHeader'
import SecondaryNavigation from './SecondaryNavigation'
import WorkspaceContainer from './WorkspaceContainer'
import type { BreadcrumbItem } from './Breadcrumbs'
import { getModuleById, type SecondaryTabConfig } from '../../config/modules'

interface SecondaryNavOptions {
  tabs: SecondaryTabConfig[]
  mode?: 'controlled' | 'routed'
  activeTab?: string
  onChange?: (id: string) => void
  basePath?: string
  hasPermission?: (permission: string) => boolean
}

interface ModuleLayoutProps {
  /** Looks up label/description/icon from the shared module config. Optional — can be fully overridden below. */
  moduleId?: string
  title?: string
  description?: string
  icon?: LucideIcon
  iconClassName?: string
  badge?: ReactNode
  breadcrumbs?: BreadcrumbItem[]
  actions?: ReactNode
  secondaryNav?: SecondaryNavOptions
  emptyState?: ReactNode
  children: ReactNode
  className?: string
}

/**
 * Reusable Application Shell layer for module *pages* (sits below the
 * existing Sidebar/TopNav AppShell): Module Header → Secondary Navigation
 * (optional) → Workspace Container.
 *
 * This intentionally reproduces the `p-6 fade-in` wrapper and header
 * layout every existing page already hand-writes, so that wrapping a page
 * in ModuleLayout is a structural change only — it does not alter how the
 * page looks. Pages keep full control of their own content and business
 * logic; this only replaces the boilerplate around it.
 */
export default function ModuleLayout({
  moduleId,
  title,
  description,
  icon,
  iconClassName,
  badge,
  breadcrumbs,
  actions,
  secondaryNav,
  emptyState,
  children,
  className = '',
}: ModuleLayoutProps) {
  const moduleConfig = moduleId ? getModuleById(moduleId) : undefined

  const resolvedTitle = title ?? moduleConfig?.label ?? ''
  const resolvedDescription = description ?? moduleConfig?.description
  const resolvedIcon = icon ?? moduleConfig?.icon

  return (
    <div className={`p-6 ${className}`}>
      <ModuleHeader
        title={resolvedTitle}
        description={resolvedDescription}
        icon={resolvedIcon}
        iconClassName={iconClassName}
        badge={badge}
        breadcrumbs={breadcrumbs}
        actions={actions}
      />

      {secondaryNav && (
        <SecondaryNavigation
          tabs={secondaryNav.tabs}
          mode={secondaryNav.mode}
          activeTab={secondaryNav.activeTab}
          onChange={secondaryNav.onChange}
          basePath={secondaryNav.basePath}
          hasPermission={secondaryNav.hasPermission}
          className="mb-4"
        />
      )}

      <WorkspaceContainer emptyState={emptyState}>{children}</WorkspaceContainer>
    </div>
  )
}
