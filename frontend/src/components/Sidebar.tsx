import { NavLink } from 'react-router-dom'
import {
  LayoutDashboard, Layers, Package, ShoppingBag, TrendingUp,
  Megaphone, Leaf, GraduationCap, Settings, ChevronLeft,
  Zap, ChevronRight, Home as HomeIcon, Link2
} from 'lucide-react'
import { usePlatform, PLATFORM_LABELS } from '../context/PlatformContext'
import DemoResetControl from './DemoResetControl'

interface NavItem {
  to: string
  label: string
  icon: React.ElementType
  badge?: string
  badgeColor?: string
}

const navItems: NavItem[] = [
  // Takes a logged-in user back to the marketing page — previously there was no way back once authenticated.
  { to: '/', label: 'Home', icon: HomeIcon },
  { to: '/dashboard', label: 'Dashboard', icon: LayoutDashboard },
  { to: '/product-studio', label: 'Product Studio', icon: Layers, badge: 'AI', badgeColor: 'bg-accent-blue-soft text-accent-blue' },
  { to: '/inventory', label: 'Inventory', icon: Package, badge: '3', badgeColor: 'bg-accent-red-soft text-accent-red' },
  { to: '/orders', label: 'Orders', icon: ShoppingBag, badge: '12', badgeColor: 'bg-accent-amber-soft text-accent-amber' },
  { to: '/business-intelligence', label: 'Business Intelligence', icon: TrendingUp },
  { to: '/marketing-hub', label: 'Marketing Hub', icon: Megaphone },
  { to: '/sustainability', label: 'Sustainability', icon: Leaf },
  { to: '/seller-coach', label: 'Seller Coach', icon: GraduationCap },
  // Routes into the existing Settings > Marketplaces tab rather than a duplicate page —
  // one place to connect/disconnect marketplaces, just easier to find.
  { to: '/settings?tab=marketplaces', label: 'Marketplace', icon: Link2 },
  { to: '/settings', label: 'Settings', icon: Settings },
]

interface SidebarProps {
  collapsed: boolean
  onToggleCollapse: () => void
}

export default function Sidebar({ collapsed, onToggleCollapse }: SidebarProps) {
  const { connectedPlatforms } = usePlatform()

  return (
    <aside
      className="sidebar-transition flex flex-col bg-elev border-r border-app h-screen sticky top-0 overflow-hidden z-30"
      style={{ width: collapsed ? 64 : 240, minWidth: collapsed ? 64 : 240 }}
    >
      {/* Logo */}
      <div className="flex items-center px-4 h-[60px] border-b border-app flex-shrink-0">
        <div className="flex items-center gap-2.5 min-w-0">
          <div className="w-8 h-8 rounded-lg bg-accent-blue flex items-center justify-center flex-shrink-0">
            <Zap size={16} className="text-white" />
          </div>
          {!collapsed && (
            <div className="min-w-0">
              <span className="font-bold text-[15px] text-app tracking-tight">SellerOS</span>
              <div className="text-[10px] text-faint font-medium -mt-0.5">AI Operating System</div>
            </div>
          )}
        </div>
      </div>

      {/* Nav */}
      <nav className="flex-1 overflow-y-auto py-3 px-2">
        {navItems.map((item) => {
          const Icon = item.icon
          return (
            <NavLink
              key={item.to}
              to={item.to}
              title={collapsed ? item.label : undefined}
              aria-label={collapsed ? item.label : undefined}
              className={({ isActive }) =>
                `nav-item w-full flex items-center gap-3 px-3 py-2.5 rounded-lg mb-0.5 text-left group relative
                ${isActive ? 'bg-accent-blue-soft text-accent-blue' : 'text-dim bg-hover hover:text-app'}`
              }
            >
              {({ isActive }) => (
                <>
                  <Icon size={18} className="flex-shrink-0" strokeWidth={isActive ? 2 : 1.75} />
                  {!collapsed && (
                    <>
                      <span className="text-[13.5px] font-medium flex-1 min-w-0 truncate">{item.label}</span>
                      {item.badge && (
                        <span className={`badge text-[10px] px-1.5 py-0.5 ${item.badgeColor}`}>
                          {item.badge}
                        </span>
                      )}
                    </>
                  )}
                  {collapsed && item.badge && (
                    <span className="absolute top-1 right-1 w-2 h-2 rounded-full bg-accent-red" />
                  )}
                </>
              )}
            </NavLink>
          )
        })}
      </nav>

      {/* Marketplace pills */}
      {!collapsed && (
        <div className="px-4 py-3 border-t border-app">
          <div className="text-[10px] font-semibold text-faint uppercase tracking-wider mb-2">Connected</div>
          <div className="flex flex-wrap gap-1.5">
            {connectedPlatforms.length === 0 && (
              <span className="badge bg-hover border border-app text-faint">None yet</span>
            )}
            {connectedPlatforms.map(m => (
              <span key={m} className="badge bg-hover text-dim border border-app">{PLATFORM_LABELS[m]}</span>
            ))}
          </div>
        </div>
      )}

      {/* Demo utility — reset the entire demo back to its original state */}
      <DemoResetControl collapsed={collapsed} />

      {/* Collapse toggle */}
      <button
        type="button"
        onClick={onToggleCollapse}
        aria-label={collapsed ? 'Expand sidebar' : 'Collapse sidebar'}
        className="flex items-center justify-center h-10 border-t border-app text-faint hover:text-app bg-hover transition-colors"
      >
        {collapsed ? <ChevronRight size={16} /> : <ChevronLeft size={16} />}
      </button>
    </aside>
  )
}
