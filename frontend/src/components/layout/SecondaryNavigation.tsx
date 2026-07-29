import { NavLink } from 'react-router-dom'
import type { SecondaryTabConfig } from '../../config/modules'

interface SecondaryNavigationProps {
  tabs: SecondaryTabConfig[]
  /**
   * 'controlled' — parent owns active tab via state (mirrors the pattern
   *   Settings.tsx already uses today).
   * 'routed' — tabs are links to `${basePath}/${tab.id}`, active state comes
   *   from the router. Enables future nested routes without changing this
   *   component.
   */
  mode?: 'controlled' | 'routed'
  activeTab?: string
  onChange?: (id: string) => void
  basePath?: string
  /** Optional permission check; tabs without requiredPermission are always shown. */
  hasPermission?: (permission: string) => boolean
  className?: string
  orientation?: 'horizontal' | 'vertical'
}

/**
 * Reusable, configuration-driven secondary navigation. Renders nothing for
 * modules with no secondary tabs, so wrapping a single-workspace page in
 * ModuleLayout doesn't add empty UI.
 */
export default function SecondaryNavigation({
  tabs,
  mode = 'controlled',
  activeTab,
  onChange,
  basePath = '',
  hasPermission,
  className = '',
  orientation = 'horizontal',
}: SecondaryNavigationProps) {
  const visibleTabs = tabs.filter(
    t => !t.requiredPermission || !hasPermission || hasPermission(t.requiredPermission)
  )

  if (visibleTabs.length === 0) return null

  const containerClass =
    orientation === 'vertical'
      ? 'flex flex-col gap-0.5'
      : 'flex items-center gap-1.5 overflow-x-auto'

  const itemClass = (active: boolean) =>
    `flex items-center gap-2 px-3 py-2 rounded-lg text-[13px] font-medium whitespace-nowrap transition-colors nav-item ${
      active ? 'bg-accent-blue-soft text-accent-blue' : 'text-dim hover:bg-surface hover:text-app'
    }`

  return (
    <div className={`${containerClass} ${className}`} role="tablist">
      {visibleTabs.map(tab => {
        const Icon = tab.icon
        if (mode === 'routed') {
          return (
            <NavLink
              key={tab.id}
              to={`${basePath}/${tab.id}`}
              className={({ isActive }) => itemClass(isActive)}
            >
              {Icon && <Icon size={15} />}
              {tab.label}
            </NavLink>
          )
        }
        const active = activeTab === tab.id
        return (
          <button
            key={tab.id}
            role="tab"
            aria-selected={active}
            onClick={() => onChange?.(tab.id)}
            className={itemClass(active)}
          >
            {Icon && <Icon size={15} />}
            {tab.label}
          </button>
        )
      })}
    </div>
  )
}
