/**
 * Centralized module metadata configuration.
 *
 * Phase 2A foundation: this is the single source of truth for module
 * identity (name, icon, route, description) and is designed to grow to
 * carry secondary-navigation tabs and permission flags as those are
 * rolled out module-by-module in Phase 2B.
 *
 * Nothing in the existing Sidebar reads from this file — the sidebar
 * intentionally keeps its own literal nav list untouched per the
 * "preserve the sidebar completely" rule, in Phase 2A and still in 2B.
 *
 * Phase 2B: every module page now reads its title/description/icon from
 * here via ModuleLayout's moduleId prop, and modules with real internal
 * sections (Marketing Hub, Settings) read secondaryTabs from here too,
 * so there's one shared definition instead of duplicating labels/icons
 * across files.
 */
import type { LucideIcon } from 'lucide-react'
import {
  LayoutDashboard, Layers, Package, ShoppingBag, TrendingUp,
  Megaphone, Leaf, GraduationCap, Settings as SettingsIcon, Link2,
  User, Bell, CreditCard, Shield, Target, Search,
} from 'lucide-react'

export interface SecondaryTabConfig {
  /** Stable id, used for tab state and (eventually) nested route segments */
  id: string
  label: string
  icon?: LucideIcon
  /** Reserved for Phase 2B+ role-based visibility. Absent = visible to everyone today. */
  requiredPermission?: string
}

export interface ModuleConfig {
  id: string
  label: string
  icon: LucideIcon
  route: string
  description: string
  /**
   * Secondary tabs for this module's own sub-navigation, if any.
   * Left empty for modules that are single-workspace today — this
   * milestone builds the framework, it does not populate every module.
   */
  secondaryTabs?: SecondaryTabConfig[]
  /** Reserved for Phase 2B+ role-based visibility of the module itself. */
  requiredPermission?: string
}

export const MODULES: ModuleConfig[] = [
  {
    id: 'dashboard',
    label: 'Dashboard',
    icon: LayoutDashboard,
    route: '/dashboard',
    description: 'Your business at a glance across every connected marketplace.',
  },
  {
    id: 'product-studio',
    label: 'Product Studio',
    icon: Layers,
    route: '/product-studio',
    description: 'AI-assisted listing creation, optimization and catalog management.',
  },
  {
    id: 'inventory',
    label: 'Inventory',
    icon: Package,
    route: '/inventory',
    description: 'Stock levels, reorder signals and warehouse visibility.',
  },
  {
    id: 'orders',
    label: 'Orders',
    icon: ShoppingBag,
    route: '/orders',
    description: 'Track and manage orders across every marketplace.',
  },
  {
    id: 'business-intelligence',
    label: 'Business Intelligence',
    icon: TrendingUp,
    route: '/business-intelligence',
    description: 'Analytics and performance insights across your business.',
  },
  {
    id: 'marketing-hub',
    label: 'Marketing Hub',
    icon: Megaphone,
    route: '/marketing-hub',
    description: 'Campaigns, promotions and marketing performance.',
    // Mirrors MarketingHub.tsx's existing tab state exactly (campaign/ads/seo).
    // Phase 2B note: the Phase 2B brief's subsection list for this module
    // (Overview/Campaigns/SEO/Promotions/Analytics) doesn't match what the
    // page actually does today, and there's no data behind "Promotions" or
    // "Analytics" (campaign connector fetchers aren't wired — see the page's
    // own comments). Rather than add empty tabs, this config documents the
    // real, working subsections so SecondaryNavigation has one source of
    // truth instead of the page's local TABS array.
    secondaryTabs: [
      { id: 'campaign', label: 'Campaign Strategy', icon: Target },
      { id: 'ads', label: 'Ads', icon: Megaphone },
      { id: 'seo', label: 'SEO & Content', icon: Search },
    ],
  },
  {
    id: 'sustainability',
    label: 'Sustainability',
    icon: Leaf,
    route: '/sustainability',
    description: 'Track and improve the environmental footprint of your operations.',
  },
  {
    id: 'seller-coach',
    label: 'Seller Coach',
    icon: GraduationCap,
    route: '/seller-coach',
    description: 'AI-guided coaching to grow and improve your seller performance.',
  },
  {
    id: 'marketplace',
    label: 'Marketplace',
    icon: Link2,
    route: '/settings?tab=marketplaces',
    description: 'Connect and manage your marketplace integrations.',
  },
  {
    id: 'settings',
    label: 'Settings',
    icon: SettingsIcon,
    route: '/settings',
    description: 'Manage your account, integrations and preferences.',
    // Phase 2B: this is now the single source of truth for Settings' tabs —
    // Settings.tsx reads this array instead of keeping its own local copy.
    // Left as the real 5 tabs (Profile/Marketplaces/Notifications/Billing/
    // Security) rather than the Phase 2B brief's literal list (General/
    // Marketplace/Team/Billing/Security/Integrations), since that list drops
    // the working Notifications tab and invents Team/Integrations with no
    // backing UI — see CHANGELOG for the full reasoning.
    secondaryTabs: [
      { id: 'profile', label: 'Profile', icon: User },
      { id: 'marketplaces', label: 'Marketplaces', icon: Link2 },
      { id: 'notifications', label: 'Notifications', icon: Bell },
      { id: 'billing', label: 'Billing', icon: CreditCard },
      { id: 'security', label: 'Security', icon: Shield },
    ],
  },
]

export const getModuleByRoute = (pathname: string): ModuleConfig | undefined =>
  MODULES.find(m => m.route.split('?')[0] === pathname)

export const getModuleById = (id: string): ModuleConfig | undefined =>
  MODULES.find(m => m.id === id)
