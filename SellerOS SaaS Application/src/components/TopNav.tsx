import { Bell, Search, HelpCircle, ChevronDown } from 'lucide-react'
import type { Page } from './Sidebar'

const pageTitles: Record<Page, string> = {
  'dashboard': 'Dashboard',
  'product-studio': 'Product Studio',
  'inventory': 'Inventory',
  'orders': 'Orders',
  'business-intelligence': 'Business Intelligence',
  'marketing-hub': 'Marketing Hub',
  'sustainability': 'Sustainability',
  'seller-coach': 'Seller Coach',
  'settings': 'Settings',
}

interface TopNavProps {
  activePage: Page
}

export default function TopNav({ activePage }: TopNavProps) {
  return (
    <header className="h-[60px] bg-white border-b border-gray-100 flex items-center px-6 gap-4 sticky top-0 z-20 flex-shrink-0">
      {/* Page title */}
      <div className="flex-1">
        <h1 className="text-[15px] font-semibold text-gray-900">{pageTitles[activePage]}</h1>
      </div>

      {/* Search */}
      <div className="relative hidden md:block">
        <Search size={15} className="absolute left-3 top-1/2 -translate-y-1/2 text-gray-400" />
        <input
          type="text"
          placeholder="Search products, orders…"
          className="pl-9 pr-4 py-2 text-[13px] bg-gray-50 border border-gray-200 rounded-lg w-56 placeholder-gray-400 focus:bg-white"
        />
        <kbd className="absolute right-3 top-1/2 -translate-y-1/2 text-[10px] text-gray-400 bg-gray-100 px-1.5 py-0.5 rounded font-mono">⌘K</kbd>
      </div>

      {/* Actions */}
      <div className="flex items-center gap-2">
        <button className="relative p-2 rounded-lg text-gray-500 hover:text-gray-700 hover:bg-gray-50 transition-colors">
          <Bell size={18} />
          <span className="absolute top-1.5 right-1.5 w-2 h-2 bg-red-400 rounded-full" />
        </button>
        <button className="p-2 rounded-lg text-gray-500 hover:text-gray-700 hover:bg-gray-50 transition-colors">
          <HelpCircle size={18} />
        </button>

        {/* User */}
        <button className="flex items-center gap-2.5 pl-3 pr-2 py-1.5 rounded-lg hover:bg-gray-50 transition-colors ml-1">
          <div className="w-7 h-7 rounded-full bg-gradient-to-br from-primary to-purple-500 flex items-center justify-center text-white text-[11px] font-bold">
            RK
          </div>
          <div className="text-left hidden lg:block">
            <div className="text-[13px] font-medium text-gray-800">Rahul Kumar</div>
            <div className="text-[11px] text-gray-400">Pro Plan</div>
          </div>
          <ChevronDown size={14} className="text-gray-400" />
        </button>
      </div>
    </header>
  )
}
