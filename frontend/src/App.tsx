import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom'
import { ThemeProvider } from './context/ThemeContext'
import { AuthProvider } from './context/AuthContext'
import { PlatformProvider } from './context/PlatformContext'
import ProtectedRoute from './components/ProtectedRoute'
import AppShell from './components/AppShell'

import Home from './pages/Home'
import Login from './pages/Login'
import Register from './pages/Register'
import Onboarding from './pages/Onboarding'
import Dashboard from './pages/Dashboard'
import ProductStudio from './pages/ProductStudio'
import Inventory from './pages/Inventory'
import Orders from './pages/Orders'
import BusinessIntelligence from './pages/BusinessIntelligence'
import MarketingHub from './pages/MarketingHub'
import Sustainability from './pages/Sustainability'
import SellerCoach from './pages/SellerCoach'
import Settings from './pages/Settings'

function AppRoutes() {
  return (
    <Routes>
      {/* Home is always reachable, logged in or not — it no longer force-redirects
          to /dashboard, so there's a way back to the marketing page from inside the app. */}
      <Route path="/" element={<Home />} />
      <Route path="/login" element={<Login />} />
      <Route path="/register" element={<Register />} />
      <Route
        path="/onboarding"
        element={
          <ProtectedRoute>
            <Onboarding />
          </ProtectedRoute>
        }
      />

      <Route
        element={
          <ProtectedRoute>
            <AppShell />
          </ProtectedRoute>
        }
      >
        <Route path="/dashboard" element={<Dashboard />} />
        <Route path="/product-studio" element={<ProductStudio />} />
        <Route path="/inventory" element={<Inventory />} />
        <Route path="/orders" element={<Orders />} />
        <Route path="/business-intelligence" element={<BusinessIntelligence />} />
        <Route path="/marketing-hub" element={<MarketingHub />} />
        <Route path="/sustainability" element={<Sustainability />} />
        <Route path="/seller-coach" element={<SellerCoach />} />
        <Route path="/settings" element={<Settings />} />
      </Route>

      <Route path="*" element={<Navigate to="/" replace />} />
    </Routes>
  )
}

export default function App() {
  return (
    <ThemeProvider>
      <BrowserRouter>
        <AuthProvider>
          <PlatformProvider>
            <AppRoutes />
          </PlatformProvider>
        </AuthProvider>
      </BrowserRouter>
    </ThemeProvider>
  )
}
