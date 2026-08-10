import { useState } from 'react'
import { useLocation } from 'react-router-dom'
import { Bell, Search, HelpCircle, ChevronDown, Sun, Moon, LogOut, Check } from 'lucide-react'
import { useTheme } from '../context/ThemeContext'
import { useAuth } from '../context/AuthContext'
import { usePlatform, PLATFORM_LABELS, type PlatformFilter } from '../context/PlatformContext'

const pageTitles: Record<string, string> = {
  '/dashboard': 'Dashboard',
  '/product-studio': 'Product Studio',
  '/inventory': 'Inventory',
  '/orders': 'Orders',
  '/business-intelligence': 'Business Intelligence',
  '/marketing-hub': 'Marketing Hub',
  '/sustainability': 'Sustainability',
  '/seller-coach': 'Seller Coach',
  '/settings': 'Settings',
}

function initials(name: string) {
  const parts = name.trim().split(/\s+/)
  return (parts[0]?.[0] || '') + (parts[1]?.[0] || '')
}

export default function TopNav() {
  const location = useLocation()
  const { theme, toggleTheme } = useTheme()
  const { user, logout } = useAuth()
  const { selected, setSelected, connectedPlatforms } = usePlatform()
  const [platformMenuOpen, setPlatformMenuOpen] = useState(false)
  const [userMenuOpen, setUserMenuOpen] = useState(false)

  const title = pageTitles[location.pathname] || 'Dashboard'
  const options: PlatformFilter[] = ['all', ...connectedPlatforms]
  const selectedLabel = selected === 'all' ? 'All platforms' : PLATFORM_LABELS[selected]

  return (
    <header className="h-[60px] bg-elev border-b border-app flex items-center px-6 gap-4 sticky top-0 z-20 flex-shrink-0">
      {/* Page title */}
      <div className="flex-1 flex items-center gap-4">
        <h1 className="text-[15px] font-semibold text-app">{title}</h1>

        {/* Platform switcher — this is what filters every data page down to one marketplace */}
        <div className="relative">
          <button
            type="button"
            onClick={() => setPlatformMenuOpen(o => !o)}
            aria-haspopup="menu"
            aria-expanded={platformMenuOpen}
            className="flex items-center gap-1.5 pl-3 pr-2 py-1.5 rounded-lg border border-app border-app-hover bg-hover text-[12.5px] text-dim"
          >
            {selectedLabel}
            <ChevronDown size={13} />
          </button>
          {platformMenuOpen && (
            <>
              <div className="fixed inset-0 z-10" onClick={() => setPlatformMenuOpen(false)} />
              <div role="menu" onKeyDown={e => e.key === 'Escape' && setPlatformMenuOpen(false)} className="absolute left-0 top-full mt-1.5 w-44 card shadow-app py-1.5 z-20">
                {options.map(opt => (
                  <button
                    key={opt}
                    type="button"
                    role="menuitem"
                    onClick={() => { setSelected(opt); setPlatformMenuOpen(false) }}
                    className="w-full flex items-center justify-between px-3.5 py-2 text-[13px] text-dim hover:text-app bg-hover text-left"
                  >
                    {opt === 'all' ? 'All platforms' : PLATFORM_LABELS[opt]}
                    {selected === opt && <Check size={13} className="text-accent-blue" />}
                  </button>
                ))}
                {connectedPlatforms.length === 0 && (
                  <div className="px-3.5 py-2 text-[12px] text-faint">Connect a marketplace in Settings</div>
                )}
              </div>
            </>
          )}
        </div>
      </div>

      {/* Search */}
      <div className="relative hidden md:block">
        <Search size={15} className="absolute left-3 top-1/2 -translate-y-1/2 text-faint" />
        <input
          type="text"
          placeholder="Search products, orders…"
          aria-label="Search products, orders"
          className="input-app pl-9 pr-4 py-2 text-[13px] w-56"
        />
        <kbd className="absolute right-3 top-1/2 -translate-y-1/2 text-[10px] text-faint bg-hover px-1.5 py-0.5 rounded font-mono-app">⌘K</kbd>
      </div>

      {/* Actions */}
      <div className="flex items-center gap-2">
        <button
          type="button"
          onClick={toggleTheme}
          aria-label="Toggle theme"
          className="p-2 rounded-lg text-dim hover:text-app bg-hover transition-colors"
        >
          {theme === 'dark' ? <Sun size={17} /> : <Moon size={17} />}
        </button>
        <button type="button" aria-label="Notifications" className="relative p-2 rounded-lg text-dim hover:text-app bg-hover transition-colors">
          <Bell size={18} />
          <span className="absolute top-1.5 right-1.5 w-2 h-2 bg-accent-red rounded-full" />
        </button>
        <button type="button" aria-label="Help" className="p-2 rounded-lg text-dim hover:text-app bg-hover transition-colors">
          <HelpCircle size={18} />
        </button>

        {/* User */}
        <div className="relative ml-1">
          <button
            type="button"
            onClick={() => setUserMenuOpen(o => !o)}
            aria-haspopup="menu"
            aria-expanded={userMenuOpen}
            className="flex items-center gap-2.5 pl-3 pr-2 py-1.5 rounded-lg bg-hover transition-colors"
          >
            <div className="w-7 h-7 rounded-full bg-accent-blue flex items-center justify-center text-white text-[11px] font-bold uppercase">
              {user ? initials(user.business_name) || user.email[0] : '?'}
            </div>
            <div className="text-left hidden lg:block">
              <div className="text-[13px] font-medium text-app">{user?.business_name || 'Loading…'}</div>
              <div className="text-[11px] text-faint">{user?.email}</div>
            </div>
            <ChevronDown size={14} className="text-faint" />
          </button>
          {userMenuOpen && (
            <>
              <div className="fixed inset-0 z-10" onClick={() => setUserMenuOpen(false)} />
              <div role="menu" onKeyDown={e => e.key === 'Escape' && setUserMenuOpen(false)} className="absolute right-0 top-full mt-1.5 w-44 card shadow-app py-1.5 z-20">
                <button
                  type="button"
                  role="menuitem"
                  onClick={logout}
                  className="w-full flex items-center gap-2 px-3.5 py-2 text-[13px] text-dim hover:text-app bg-hover text-left"
                >
                  <LogOut size={14} /> Log out
                </button>
              </div>
            </>
          )}
        </div>
      </div>
    </header>
  )
}
