import { useState } from 'react'
import { Search, AlertTriangle, Package, TrendingDown, RefreshCw, Plus, Download } from 'lucide-react'

interface InventoryItem {
  id: string
  name: string
  sku: string
  category: string
  stock: number
  reorderPoint: number
  reorderQty: number
  price: number
  marketplace: string[]
  lastUpdated: string
}

const items: InventoryItem[] = [
  { id: '1', name: 'Bamboo Spice Rack 6-Tier', sku: 'BSR-001', category: 'Kitchen', stock: 12, reorderPoint: 20, reorderQty: 200, price: 899, marketplace: ['Amazon', 'Flipkart'], lastUpdated: '2h ago' },
  { id: '2', name: 'Wooden Serving Board Set', sku: 'WSB-023', category: 'Kitchen', stock: 6, reorderPoint: 15, reorderQty: 150, price: 1249, marketplace: ['Amazon'], lastUpdated: '5h ago' },
  { id: '3', name: 'Kitchen Tool Set (5-pc)', sku: 'KTS-007', category: 'Kitchen', stock: 18, reorderPoint: 25, reorderQty: 250, price: 849, marketplace: ['Amazon', 'Flipkart', 'Meesho'], lastUpdated: '1d ago' },
  { id: '4', name: 'Bamboo Storage Box Large', sku: 'BSB-044', category: 'Storage', stock: 45, reorderPoint: 20, reorderQty: 100, price: 699, marketplace: ['Flipkart', 'Meesho'], lastUpdated: '2d ago' },
  { id: '5', name: 'Herb Garden Planter Set', sku: 'HGP-012', category: 'Garden', stock: 0, reorderPoint: 10, reorderQty: 80, price: 1499, marketplace: ['Amazon'], lastUpdated: '3d ago' },
  { id: '6', name: 'Teak Wood Coasters (Set of 6)', sku: 'TWC-088', category: 'Home Décor', stock: 72, reorderPoint: 30, reorderQty: 200, price: 549, marketplace: ['Amazon', 'Meesho'], lastUpdated: '1d ago' },
  { id: '7', name: 'Bamboo Cutting Board Pro', sku: 'BCB-019', category: 'Kitchen', stock: 31, reorderPoint: 20, reorderQty: 150, price: 1099, marketplace: ['Amazon', 'Flipkart'], lastUpdated: '6h ago' },
  { id: '8', name: 'Eco Laundry Basket Set', sku: 'ELB-055', category: 'Storage', stock: 8, reorderPoint: 15, reorderQty: 100, price: 1799, marketplace: ['Flipkart', 'Meesho'], lastUpdated: '4h ago' },
  { id: '9', name: 'Bamboo Desk Organizer', sku: 'BDO-031', category: 'Storage', stock: 55, reorderPoint: 25, reorderQty: 200, price: 649, marketplace: ['Amazon', 'Flipkart', 'Meesho'], lastUpdated: '8h ago' },
  { id: '10', name: 'Wooden Wall Clock Rustic', sku: 'WWC-002', category: 'Home Décor', stock: 14, reorderPoint: 10, reorderQty: 60, price: 2199, marketplace: ['Amazon'], lastUpdated: '2d ago' },
]

const getStockStatus = (item: InventoryItem) => {
  if (item.stock === 0) return { label: 'Out of Stock', color: 'bg-red-50 text-red-600' }
  if (item.stock < item.reorderPoint) return { label: 'Low Stock', color: 'bg-amber-50 text-amber-600' }
  return { label: 'In Stock', color: 'bg-emerald-50 text-emerald-600' }
}

const getStockBarColor = (item: InventoryItem) => {
  if (item.stock === 0) return 'bg-red-400'
  if (item.stock < item.reorderPoint) return 'bg-amber-400'
  return 'bg-emerald-400'
}

export default function Inventory() {
  const [search, setSearch] = useState('')
  const [filter, setFilter] = useState<'all' | 'low' | 'out'>('all')

  const filtered = items.filter(item => {
    const matchSearch = item.name.toLowerCase().includes(search.toLowerCase()) || item.sku.toLowerCase().includes(search.toLowerCase())
    const matchFilter = filter === 'all' || (filter === 'low' && item.stock > 0 && item.stock < item.reorderPoint) || (filter === 'out' && item.stock === 0)
    return matchSearch && matchFilter
  })

  const outOfStock = items.filter(i => i.stock === 0).length
  const lowStock = items.filter(i => i.stock > 0 && i.stock < i.reorderPoint).length
  const healthy = items.filter(i => i.stock >= i.reorderPoint).length

  return (
    <div className="p-6 fade-in">
      {/* Header */}
      <div className="flex items-center justify-between mb-6">
        <div>
          <h2 className="text-xl font-bold text-gray-900">Inventory Management</h2>
          <p className="text-[13px] text-gray-500 mt-0.5">{items.length} SKUs across 3 marketplaces</p>
        </div>
        <div className="flex items-center gap-3">
          <button className="flex items-center gap-2 px-3 py-2 bg-white border border-gray-200 text-gray-600 text-[13px] rounded-lg hover:bg-gray-50 transition-colors">
            <Download size={14} /> Export
          </button>
          <button className="flex items-center gap-2 px-4 py-2 bg-primary text-white text-[13px] font-medium rounded-lg hover:bg-primary-hover transition-colors">
            <Plus size={14} /> Add Product
          </button>
        </div>
      </div>

      {/* Summary cards */}
      <div className="grid grid-cols-4 gap-4 mb-6">
        {[
          { label: 'Total SKUs', value: items.length, icon: Package, color: 'bg-blue-50 text-blue-600' },
          { label: 'Healthy Stock', value: healthy, icon: RefreshCw, color: 'bg-emerald-50 text-emerald-600' },
          { label: 'Low Stock', value: lowStock, icon: TrendingDown, color: 'bg-amber-50 text-amber-600' },
          { label: 'Out of Stock', value: outOfStock, icon: AlertTriangle, color: 'bg-red-50 text-red-500' },
        ].map(({ label, value, icon: Icon, color }) => (
          <div key={label} className="bg-white rounded-xl border border-gray-100 p-4 flex items-center gap-3">
            <div className={`w-10 h-10 rounded-lg flex items-center justify-center ${color}`}>
              <Icon size={18} />
            </div>
            <div>
              <div className="text-xl font-bold text-gray-900">{value}</div>
              <div className="text-[12px] text-gray-500">{label}</div>
            </div>
          </div>
        ))}
      </div>

      {/* Filters */}
      <div className="flex items-center gap-3 mb-4">
        <div className="relative flex-1 max-w-sm">
          <Search size={14} className="absolute left-3 top-1/2 -translate-y-1/2 text-gray-400" />
          <input
            value={search} onChange={e => setSearch(e.target.value)}
            placeholder="Search by name or SKU..."
            className="w-full pl-9 pr-4 py-2 text-[13px] bg-white border border-gray-200 rounded-lg placeholder-gray-400"
          />
        </div>
        <div className="flex items-center gap-1.5">
          {([['all','All'],['low','Low Stock'],['out','Out of Stock']] as const).map(([v, l]) => (
            <button key={v} onClick={() => setFilter(v)}
              className={`px-3 py-2 text-[12.5px] font-medium rounded-lg transition-colors ${
                filter === v ? 'bg-primary text-white' : 'bg-white border border-gray-200 text-gray-600 hover:bg-gray-50'
              }`}>
              {l}
            </button>
          ))}
        </div>
      </div>

      {/* Table */}
      <div className="bg-white rounded-xl border border-gray-100 overflow-hidden">
        <table className="w-full">
          <thead>
            <tr className="border-b border-gray-100">
              {['Product', 'SKU', 'Category', 'Stock Level', 'Reorder Point', 'Price', 'Marketplaces', 'Status', 'Updated'].map(h => (
                <th key={h} className="text-left px-4 py-3 text-[11.5px] font-semibold text-gray-500 uppercase tracking-wide whitespace-nowrap">
                  {h}
                </th>
              ))}
            </tr>
          </thead>
          <tbody>
            {filtered.map((item, i) => {
              const status = getStockStatus(item)
              const barColor = getStockBarColor(item)
              const pct = Math.min((item.stock / (item.reorderPoint * 2)) * 100, 100)
              return (
                <tr key={item.id} className={`border-b border-gray-50 hover:bg-gray-50/50 transition-colors ${i % 2 === 0 ? '' : 'bg-gray-50/20'}`}>
                  <td className="px-4 py-3.5">
                    <div className="text-[13px] font-medium text-gray-900">{item.name}</div>
                  </td>
                  <td className="px-4 py-3.5">
                    <span className="text-[12px] font-mono text-gray-500">{item.sku}</span>
                  </td>
                  <td className="px-4 py-3.5">
                    <span className="text-[12px] text-gray-600">{item.category}</span>
                  </td>
                  <td className="px-4 py-3.5">
                    <div className="flex items-center gap-2">
                      <div className="w-20 h-1.5 bg-gray-100 rounded-full overflow-hidden">
                        <div className={`h-full rounded-full ${barColor}`} style={{ width: `${pct}%` }} />
                      </div>
                      <span className={`text-[12.5px] font-semibold ${item.stock === 0 ? 'text-red-500' : item.stock < item.reorderPoint ? 'text-amber-600' : 'text-gray-900'}`}>
                        {item.stock}
                      </span>
                    </div>
                  </td>
                  <td className="px-4 py-3.5">
                    <span className="text-[12px] text-gray-500">{item.reorderPoint} units</span>
                  </td>
                  <td className="px-4 py-3.5">
                    <span className="text-[13px] font-medium text-gray-900">₹{item.price.toLocaleString('en-IN')}</span>
                  </td>
                  <td className="px-4 py-3.5">
                    <div className="flex gap-1 flex-wrap">
                      {item.marketplace.map(m => (
                        <span key={m} className="badge bg-gray-100 text-gray-600">{m}</span>
                      ))}
                    </div>
                  </td>
                  <td className="px-4 py-3.5">
                    <span className={`badge ${status.color}`}>{status.label}</span>
                  </td>
                  <td className="px-4 py-3.5">
                    <span className="text-[12px] text-gray-400">{item.lastUpdated}</span>
                  </td>
                </tr>
              )
            })}
          </tbody>
        </table>
        {filtered.length === 0 && (
          <div className="text-center py-12 text-gray-400 text-[13px]">No items match your search.</div>
        )}
      </div>
    </div>
  )
}
