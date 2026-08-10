import { useState } from 'react'
import { Outlet } from 'react-router-dom'
import Sidebar from './Sidebar'
import TopNav from './TopNav'
import FloatingAI from './FloatingAI'
import ErrorBoundary from './ErrorBoundary'

export default function AppShell() {
  const [collapsed, setCollapsed] = useState(false)

  return (
    <div className="flex h-screen bg-app overflow-hidden">
      <Sidebar collapsed={collapsed} onToggleCollapse={() => setCollapsed(c => !c)} />

      <div className="flex-1 flex flex-col min-w-0 overflow-hidden">
        <TopNav />
        <main className="flex-1 overflow-y-auto bg-app">
          <ErrorBoundary>
            <Outlet />
          </ErrorBoundary>
        </main>
      </div>

      <FloatingAI />
    </div>
  )
}
