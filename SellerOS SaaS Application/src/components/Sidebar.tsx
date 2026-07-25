import {
  LayoutDashboard, Layers, Package, ShoppingBag, TrendingUp,
  Megaphone, Leaf, GraduationCap, Settings, ChevronLeft,
  Zap, ChevronRight
} from 'lucide-react'

export type Page =
  | 'dashboard'
  | 'product-studio'
  | 'inventory'
  | 'orders'
  | 'business-intelligence'
  | 'marketing-hub'
  | 'sustainability'
  | 'seller-coach'
  | 'settings'

interface NavItem {
  id: Page
  label: string
  icon: React.ElementType
  badge?: string
  badgeColor?: string
}

const navItems: NavItem[] = [
  { id: 'dashboard', label: 'Dashboard', icon: LayoutDashboard },
  { id: 'product-studio', label: 'Product Studio', icon: Layers, badge: 'AI', badgeColor: 'bg-primary-50 text-primary' },
  { id: 'inventory', label: 'Inventory', icon: Package, badge: '3', badgeColor: 'bg-red-50 text-red-500' },
  { id: 'orders', label: 'Orders', icon: ShoppingBag, badge: '12', badgeColor: 'bg-amber-50 text-amber-600' },
  { id: 'business-intelligence', label: 'Business Intelligence', icon: TrendingUp },
  { id: 'marketing-hub', label: 'Marketing Hub', icon: Megaphone },
  { id: 'sustainability', label: 'Sustainability', icon: Leaf },
  { id: 'seller-coach', label: 'Seller Coach', icon: GraduationCap },
  { id: 'settings', label: 'Settings', icon: Settings },
]

interface SidebarProps {
  activePage: Page
  onNavigate: (page: Page) => void
  collapsed: boolean
  onToggleCollapse: () => void
}

export default function Sidebar({ activePage, onNavigate, collapsed, onToggleCollapse }: SidebarProps) {
  return (
    <aside
      className="sidebar-transition flex flex-col bg-white border-r border-gray-100 h-screen sticky top-0 overflow-hidden z-30"
      style={{ width: collapsed ? 64 : 240, minWidth: collapsed ? 64 : 240 }}
    >
      {/* Logo */}
      <div className="flex items-center px-4 h-[60px] border-b border-gray-100 flex-shrink-0">
        <div className="flex items-center gap-2.5 min-w-0">
          <div className="w-8 h-8 rounded-lg bg-primary flex items-center justify-center flex-shrink-0">
            <Zap size={16} className="text-white" />
          </div>
          {!collapsed && (
            <div className="min-w-0">
              <span className="font-bold text-[15px] text-gray-900 tracking-tight">SellerOS</span>
              <div className="text-[10px] text-gray-400 font-medium -mt-0.5">AI Operating System</div>
            </div>
          )}
        </div>
      </div>

      {/* Nav */}
      <nav className="flex-1 overflow-y-auto py-3 px-2">
        {navItems.map((item) => {
          const Icon = item.icon
          const isActive = activePage === item.id
          return (
            <button
              key={item.id}
              onClick={() => onNavigate(item.id)}
              title={collapsed ? item.label : undefined}
              className={`nav-item w-full flex items-center gap-3 px-3 py-2.5 rounded-lg mb-0.5 text-left group relative
                ${isActive
                  ? 'bg-primary-50 text-primary'
                  : 'text-gray-600 hover:bg-gray-50 hover:text-gray-900'
                }`}
            >
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
                <span className="absolute top-1 right-1 w-2 h-2 rounded-full bg-red-400" />
              )}
            </button>
          )
        })}
      </nav>

      {/* Marketplace pills */}
      {!collapsed && (
        <div className="px-4 py-3 border-t border-gray-100">
          <div className="text-[10px] font-semibold text-gray-400 uppercase tracking-wider mb-2">Connected</div>
          <div className="flex flex-wrap gap-1.5">
            {['Amazon', 'Flipkart', 'Meesho'].map(m => (
              <span key={m} className="badge bg-gray-50 text-gray-600 border border-gray-200">{m}</span>
            ))}
          </div>
        </div>
      )}

      {/* Collapse toggle */}
      <button
        onClick={onToggleCollapse}
        className="flex items-center justify-center h-10 border-t border-gray-100 text-gray-400 hover:text-gray-600 hover:bg-gray-50 transition-colors"
      >
        {collapsed ? <ChevronRight size={16} /> : <ChevronLeft size={16} />}
      </button>
    </aside>
  )
}
