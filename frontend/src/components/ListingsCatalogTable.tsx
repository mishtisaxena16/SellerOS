import { useMemo, useState } from 'react'
import { Search, ArrowUpDown, Sparkles, Star } from 'lucide-react'
import { mockListingRows, type ListingViewRow, type ScoreTier } from '../mock/listingsView'

// Same badge convention as Orders.tsx / Inventory.tsx: a small color map
// keyed off a real field on the row, not re-derived per cell.
const STATUS_COLOR: Record<ListingViewRow['listingStatus'], string> = {
  Live: 'bg-accent-green-soft text-accent-green',
  Inactive: 'bg-surface text-dim',
}

const TIER_COLOR: Record<ScoreTier, string> = {
  Excellent: 'bg-accent-green-soft text-accent-green',
  Good: 'bg-accent-amber-soft text-accent-amber',
  'Needs Improvement': 'bg-accent-red-soft text-accent-red',
}

type SortKey = 'name' | 'price' | 'rating' | 'seoScore' | 'listingQualityScore'
type StatusFilter = 'all' | 'live' | 'inactive'
type TierFilter = 'all' | ScoreTier

interface ListingsCatalogTableProps {
  // Prefills the Product Studio editor from a catalog row and hands off to
  // the existing AI Listing Optimizer (AgentConsole / RAG via /chat) —
  // this component never talks to the AI itself, it only supplies the
  // seller-owned product facts the editor needs.
  onOptimize: (row: ListingViewRow) => void
}

export default function ListingsCatalogTable({ onOptimize }: ListingsCatalogTableProps) {
  const [search, setSearch] = useState('')
  const [statusFilter, setStatusFilter] = useState<StatusFilter>('all')
  const [seoFilter, setSeoFilter] = useState<TierFilter>('all')
  const [sortKey, setSortKey] = useState<SortKey>('name')
  const [sortDir, setSortDir] = useState<'asc' | 'desc'>('asc')

  const filtered = useMemo(() => {
    const q = search.trim().toLowerCase()
    const matches = mockListingRows.filter(row => {
      const matchSearch = !q ||
        row.name.toLowerCase().includes(q) ||
        row.sku.toLowerCase().includes(q) ||
        row.category.toLowerCase().includes(q) ||
        row.brand.toLowerCase().includes(q)
      const matchStatus =
        statusFilter === 'all' ||
        (statusFilter === 'live' && row.listingStatus === 'Live') ||
        (statusFilter === 'inactive' && row.listingStatus === 'Inactive')
      const matchSeo = seoFilter === 'all' || row.seoTier === seoFilter
      return matchSearch && matchStatus && matchSeo
    })
    return [...matches].sort((a, b) => {
      const dir = sortDir === 'asc' ? 1 : -1
      if (sortKey === 'name') return a.name.localeCompare(b.name) * dir
      return (a[sortKey] - b[sortKey]) * dir
    })
  }, [search, statusFilter, seoFilter, sortKey, sortDir])

  const toggleSort = (key: SortKey) => {
    if (sortKey === key) setSortDir(d => (d === 'asc' ? 'desc' : 'asc'))
    else { setSortKey(key); setSortDir(key === 'name' ? 'asc' : 'desc') }
  }

  return (
    <div className="space-y-4">
      <div>
        <h3 className="text-[14px] font-semibold text-app">My Products</h3>
        <p className="text-[12.5px] text-dim mt-0.5">
          {filtered.length} of {mockListingRows.length} products{search || statusFilter !== 'all' || seoFilter !== 'all' ? ' (filtered)' : ''} — from your seller catalog. Pick one to optimize with AI.
        </p>
      </div>

      {/* Filters */}
      <div className="flex flex-wrap items-center gap-3">
        <div className="relative flex-1 max-w-sm">
          <Search size={14} className="absolute left-3 top-1/2 -translate-y-1/2 text-faint" />
          <input
            value={search} onChange={e => setSearch(e.target.value)}
            placeholder="Search by name, SKU, category, or brand..."
            className="input-app w-full pl-9 pr-4 py-2 text-[13px]"
          />
        </div>
        <div className="flex items-center gap-1.5">
          {([['all', 'All'], ['live', 'Live'], ['inactive', 'Inactive']] as const).map(([v, l]) => (
            <button key={v} onClick={() => setStatusFilter(v)}
              className={`px-3 py-2 text-[12.5px] font-medium rounded-lg transition-colors ${
                statusFilter === v ? 'btn-primary-app' : 'card border-app text-dim bg-hover'
              }`}>
              {l}
            </button>
          ))}
        </div>
        <div className="flex items-center gap-1.5">
          {(['all', 'Excellent', 'Good', 'Needs Improvement'] as const).map(v => (
            <button key={v} onClick={() => setSeoFilter(v)}
              className={`px-3 py-2 text-[12px] font-medium rounded-lg transition-colors whitespace-nowrap ${
                seoFilter === v ? 'btn-primary-app' : 'card border-app text-dim bg-hover'
              }`}>
              {v === 'all' ? 'All SEO' : v}
            </button>
          ))}
        </div>
      </div>

      {/* Table */}
      <div className="card overflow-hidden overflow-x-auto">
        <table className="w-full">
          <thead>
            <tr className="border-b border-app">
              <th className="text-left px-4 py-3 text-[11.5px] font-semibold text-faint uppercase tracking-wide whitespace-nowrap">Image</th>
              <th className="text-left px-4 py-3 text-[11.5px] font-semibold text-faint uppercase tracking-wide whitespace-nowrap">
                <button className="inline-flex items-center gap-1 hover:text-app" onClick={() => toggleSort('name')}>
                  Product <ArrowUpDown size={11} className={sortKey === 'name' ? 'text-accent-blue' : ''} />
                </button>
              </th>
              <th className="text-left px-4 py-3 text-[11.5px] font-semibold text-faint uppercase tracking-wide whitespace-nowrap">SKU</th>
              <th className="text-left px-4 py-3 text-[11.5px] font-semibold text-faint uppercase tracking-wide whitespace-nowrap">Category</th>
              <th className="text-left px-4 py-3 text-[11.5px] font-semibold text-faint uppercase tracking-wide whitespace-nowrap">Marketplace</th>
              <th className="text-left px-4 py-3 text-[11.5px] font-semibold text-faint uppercase tracking-wide whitespace-nowrap">
                <button className="inline-flex items-center gap-1 hover:text-app" onClick={() => toggleSort('price')}>
                  Price <ArrowUpDown size={11} className={sortKey === 'price' ? 'text-accent-blue' : ''} />
                </button>
              </th>
              <th className="text-left px-4 py-3 text-[11.5px] font-semibold text-faint uppercase tracking-wide whitespace-nowrap">
                <button className="inline-flex items-center gap-1 hover:text-app" onClick={() => toggleSort('rating')}>
                  Rating <ArrowUpDown size={11} className={sortKey === 'rating' ? 'text-accent-blue' : ''} />
                </button>
              </th>
              <th className="text-left px-4 py-3 text-[11.5px] font-semibold text-faint uppercase tracking-wide whitespace-nowrap">Status</th>
              <th className="text-left px-4 py-3 text-[11.5px] font-semibold text-faint uppercase tracking-wide whitespace-nowrap">
                <button className="inline-flex items-center gap-1 hover:text-app" onClick={() => toggleSort('seoScore')}>
                  SEO <ArrowUpDown size={11} className={sortKey === 'seoScore' ? 'text-accent-blue' : ''} />
                </button>
              </th>
              <th className="text-left px-4 py-3 text-[11.5px] font-semibold text-faint uppercase tracking-wide whitespace-nowrap">
                <button className="inline-flex items-center gap-1 hover:text-app" onClick={() => toggleSort('listingQualityScore')}>
                  Quality <ArrowUpDown size={11} className={sortKey === 'listingQualityScore' ? 'text-accent-blue' : ''} />
                </button>
              </th>
              <th className="px-4 py-3" />
            </tr>
          </thead>
          <tbody>
            {filtered.map(row => (
              <tr key={row.productId} className="border-b border-app bg-hover transition-colors">
                <td className="px-4 py-3">
                  <img src={row.imageUrl} alt="" className="w-9 h-9 rounded-md object-cover border border-app" />
                </td>
                <td className="px-4 py-3.5">
                  <div className="text-[12.5px] text-app font-medium truncate max-w-[220px]">{row.name}</div>
                  <div className="text-[11px] text-faint">{row.brand}</div>
                </td>
                <td className="px-4 py-3.5">
                  <span className="text-[12px] font-mono-app text-dim">{row.sku}</span>
                </td>
                <td className="px-4 py-3.5">
                  <span className="text-[12px] text-dim whitespace-nowrap">{row.category}</span>
                </td>
                <td className="px-4 py-3.5">
                  <span className="badge bg-accent-amber-soft text-accent-amber">{row.marketplace}</span>
                </td>
                <td className="px-4 py-3.5">
                  <span className="text-[12.5px] font-semibold text-app whitespace-nowrap">₹{row.price.toLocaleString('en-IN')}</span>
                </td>
                <td className="px-4 py-3.5">
                  <div className="flex items-center gap-1">
                    <Star size={11} fill="#FF9900" stroke="none" />
                    <span className="text-[12px] text-dim">{row.rating.toFixed(1)}</span>
                  </div>
                </td>
                <td className="px-4 py-3.5">
                  <span className={`badge ${STATUS_COLOR[row.listingStatus]}`}>{row.listingStatus}</span>
                </td>
                <td className="px-4 py-3.5">
                  <span className={`badge ${TIER_COLOR[row.seoTier]}`}>{row.seoScore}</span>
                </td>
                <td className="px-4 py-3.5">
                  <span className={`badge ${TIER_COLOR[row.listingQualityTier]}`}>{row.listingQualityScore}</span>
                </td>
                <td className="px-4 py-3.5">
                  <button
                    onClick={() => onOptimize(row)}
                    className="flex items-center gap-1.5 px-2.5 py-1.5 text-[11.5px] font-medium rounded-lg bg-accent-blue-soft text-accent-blue hover:opacity-80 transition-opacity whitespace-nowrap"
                  >
                    <Sparkles size={11} /> Optimize
                  </button>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
        {filtered.length === 0 && (
          <div className="text-center py-12 text-faint text-[13px]">No products match your search.</div>
        )}
      </div>
    </div>
  )
}
