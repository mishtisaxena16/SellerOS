import { useState } from 'react'
import Sidebar, { type Page } from './components/Sidebar'
import TopNav from './components/TopNav'
import FloatingAI from './components/FloatingAI'
import Dashboard from './pages/Dashboard'
import ProductStudio from './pages/ProductStudio'
import Inventory from './pages/Inventory'
import Orders from './pages/Orders'
import BusinessIntelligence from './pages/BusinessIntelligence'
import MarketingHub from './pages/MarketingHub'
import Sustainability from './pages/Sustainability'
import SellerCoach from './pages/SellerCoach'
import Settings from './pages/Settings'

function PageContent({ page }: { page: Page }) {
  switch (page) {
    case 'dashboard': return <Dashboard />
    case 'product-studio': return <ProductStudio />
    case 'inventory': return <Inventory />
    case 'orders': return <Orders />
    case 'business-intelligence': return <BusinessIntelligence />
    case 'marketing-hub': return <MarketingHub />
    case 'sustainability': return <Sustainability />
    case 'seller-coach': return <SellerCoach />
    case 'settings': return <Settings />
    default: return <Dashboard />
  }
}

export default function App() {
  const [activePage, setActivePage] = useState<Page>('dashboard')
  const [collapsed, setCollapsed] = useState(false)

  return (
    <div className="flex h-screen bg-surface overflow-hidden">
      {/* Sidebar */}
      <Sidebar
        activePage={activePage}
        onNavigate={setActivePage}
        collapsed={collapsed}
        onToggleCollapse={() => setCollapsed(c => !c)}
      />

      {/* Main content area */}
      <div className="flex-1 flex flex-col min-w-0 overflow-hidden">
        <TopNav activePage={activePage} />
        <main className="flex-1 overflow-y-auto">
          <PageContent page={activePage} />
        </main>
      </div>

      {/* Floating AI assistant */}
      <FloatingAI />
    </div>
  )
}
