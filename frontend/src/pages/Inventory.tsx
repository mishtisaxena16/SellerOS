import { useEffect, useMemo, useState } from 'react'
import { Search, AlertTriangle, Package, TrendingDown, RefreshCw, Loader2, Info } from 'lucide-react'
import { usePlatform, PLATFORM_LABELS } from '../context/PlatformContext'
import { useInventoryData, type InventoryViewRow } from '../hooks/useInventoryData'
import EmptyMarketplaceState from '../components/EmptyMarketplaceState'

// Status badge/bar colors keyed off the same Inventory Status every row
// already carries (InventoryViewRow.status — 'In Stock' / 'Low Stock' /
// 'Out of Stock'), rather than each screen re-deriving its own threshold.
// For mock rows that status comes straight from inventory.ts (so it can
// never disagree with the Dashboard's lowStockCount/outOfStockCount); for
// live rows it's derived once in useInventoryData.ts.
const STATUS_CONFIG: Record<InventoryViewRow['status'], { color: string; barColor: string }> = {
  'In Stock': { color: 'bg-accent-green-soft text-accent-green', barColor: 'bg-accent-green' },
  'Low Stock': { color: 'bg-accent-amber-soft text-accent-amber', barColor: 'bg-accent-amber' },
  'Out of Stock': { color: 'bg-accent-red-soft text-accent-red', barColor: 'bg-accent-red' },
}

export default function Inventory() {
  const [search, setSearch] = useState('')
  const [filter, setFilter] = useState<'all' | 'low' | 'out'>('all')
  const { selected } = usePlatform()

  const { rows: items, loading, error, usingMockData } = useInventoryData(selected)

  useEffect(() => { setFilter('all') }, [selected])

  const filtered = useMemo(() => items.filter(item => {
    const q = search.trim().toLowerCase()
    const matchSearch = !q ||
      item.sku.toLowerCase().includes(q) ||
      item.name.toLowerCase().includes(q) ||
      item.category.toLowerCase().includes(q)
    const matchFilter =
      filter === 'all' ||
      (filter === 'low' && item.status === 'Low Stock') ||
      (filter === 'out' && item.status === 'Out of Stock')
    return matchSearch && matchFilter
  }), [items, search, filter])

  const outOfStock = items.filter(i => i.status === 'Out of Stock').length
  const lowStock = items.filter(i => i.status === 'Low Stock').length
  const healthy = items.filter(i => i.status === 'In Stock').length

  // No marketplace connected at all — the backend returns a 409 for this.
  if (error && error.status === 409 && !usingMockData) {
    return <EmptyMarketplaceState message={error.message} />
  }

  return (
    <div className="p-6 fade-in">
      {/* Header */}
      <div className="flex flex-wrap items-center justify-between gap-3 mb-6">
        <div>
          <h2 className="text-xl font-bold text-app">Inventory Management</h2>
          <p className="text-[13px] text-dim mt-0.5">
            {loading ? 'Loading…' : `${items.length} SKUs ${selected === 'all' ? '' : `on ${PLATFORM_LABELS[selected]}`}`}
          </p>
        </div>
      </div>

      {usingMockData && !loading && (
        <div className="mb-4 p-3 rounded-lg bg-accent-blue-soft text-accent-blue text-[13px] flex items-center gap-2">
          <Info size={14} /> Showing historical demo inventory for ABC Fashion Store — connect a marketplace to see live inventory instead.
        </div>
      )}

      {error && !usingMockData && (
        <div className="mb-4 p-3 rounded-lg bg-accent-red-soft text-accent-red text-[13px] flex items-center gap-2">
          <AlertTriangle size={14} /> {error.message}
        </div>
      )}

      {loading ? (
        <div className="card p-12 flex items-center justify-center gap-2 text-dim text-[13px]">
          <Loader2 size={16} className="animate-spin" /> Loading inventory…
        </div>
      ) : (
        <>
          {/* Summary cards */}
          <div className="grid grid-cols-2 lg:grid-cols-4 gap-4 mb-6">
            {[
              { label: 'Total SKUs', value: items.length, icon: Package, color: 'bg-accent-blue-soft text-accent-blue' },
              { label: 'Healthy Stock', value: healthy, icon: RefreshCw, color: 'bg-accent-green-soft text-accent-green' },
              { label: 'Low Stock', value: lowStock, icon: TrendingDown, color: 'bg-accent-amber-soft text-accent-amber' },
              { label: 'Out of Stock', value: outOfStock, icon: AlertTriangle, color: 'bg-accent-red-soft text-accent-red' },
            ].map(({ label, value, icon: Icon, color }) => (
              <div key={label} className="card p-4 flex items-center gap-3">
                <div className={`w-10 h-10 rounded-lg flex items-center justify-center ${color}`}>
                  <Icon size={18} />
                </div>
                <div>
                  <div className="text-xl font-bold text-app">{value}</div>
                  <div className="text-[12px] text-dim">{label}</div>
                </div>
              </div>
            ))}
          </div>

          {/* Filters */}
          <div className="flex flex-wrap items-center gap-3 mb-4">
            <div className="relative flex-1 max-w-sm">
              <Search size={14} className="absolute left-3 top-1/2 -translate-y-1/2 text-faint" />
              <input
                value={search} onChange={e => setSearch(e.target.value)}
                placeholder="Search by SKU, product name, or category..."
                className="input-app w-full pl-9 pr-4 py-2 text-[13px]"
              />
            </div>
            <div className="flex items-center gap-1.5">
              {([['all','All'],['low','Low Stock'],['out','Out of Stock']] as const).map(([v, l]) => (
                <button key={v} onClick={() => setFilter(v)}
                  className={`px-3 py-2 text-[12.5px] font-medium rounded-lg transition-colors ${
                    filter === v ? 'btn-primary-app' : 'card border-app text-dim bg-hover'
                  }`}>
                  {l}
                </button>
              ))}
            </div>
            <span className="text-[12.5px] text-faint whitespace-nowrap ml-auto">{filtered.length} results</span>
          </div>

          {/* Table */}
          <div className="card overflow-hidden overflow-x-auto">
            <table className="w-full">
              <thead>
                <tr className="border-b border-app">
                  {['Product', 'SKU', 'Category', 'Available', 'Reserved', 'Reorder Level', 'Warehouse', 'Status', 'Last Updated'].map(h => (
                    <th key={h} className="text-left px-4 py-3 text-[11.5px] font-semibold text-faint uppercase tracking-wide whitespace-nowrap">
                      {h}
                    </th>
                  ))}
                </tr>
              </thead>
              <tbody>
                {filtered.map((item) => {
                  const cfg = STATUS_CONFIG[item.status]
                  const pct = Math.min((item.availableQuantity / (item.reorderLevel * 2 || 1)) * 100, 100)
                  return (
                    <tr key={item.productId} className="border-b border-app bg-hover transition-colors">
                      <td className="px-4 py-3.5">
                        <span className="text-[12.5px] text-app font-medium truncate max-w-[200px] block">{item.name}</span>
                      </td>
                      <td className="px-4 py-3.5">
                        <span className="text-[12px] font-mono-app font-medium text-dim">{item.sku}</span>
                      </td>
                      <td className="px-4 py-3.5">
                        <span className="text-[12px] text-dim">{item.category}</span>
                      </td>
                      <td className="px-4 py-3.5">
                        <div className="flex items-center gap-2">
                          <div className="w-20 h-1.5 bg-surface rounded-full overflow-hidden">
                            <div className={`h-full rounded-full ${cfg.barColor}`} style={{ width: `${pct}%` }} />
                          </div>
                          <span className={`text-[12.5px] font-semibold ${item.status === 'Out of Stock' ? 'text-accent-red' : item.status === 'Low Stock' ? 'text-accent-amber' : 'text-app'}`}>
                            {item.availableQuantity}
                          </span>
                        </div>
                      </td>
                      <td className="px-4 py-3.5">
                        <span className="text-[12px] text-dim">{item.reservedQuantity}</span>
                      </td>
                      <td className="px-4 py-3.5">
                        <span className="text-[12px] text-dim">{item.reorderLevel}</span>
                      </td>
                      <td className="px-4 py-3.5">
                        <span className="text-[12px] text-dim">{item.warehouse ?? '—'}</span>
                      </td>
                      <td className="px-4 py-3.5">
                        <span className={`badge ${cfg.color}`}>{item.status}</span>
                      </td>
                      <td className="px-4 py-3.5">
                        <span className="text-[12px] text-dim whitespace-nowrap">{item.lastUpdated !== '—' ? new Date(item.lastUpdated).toLocaleDateString('en-IN') : '—'}</span>
                      </td>
                    </tr>
                  )
                })}
              </tbody>
            </table>
            {filtered.length === 0 && (
              <div className="text-center py-12 text-faint text-[13px]">No items match your search.</div>
            )}
          </div>
        </>
      )}
    </div>
  )
}
