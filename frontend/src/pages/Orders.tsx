import { useState } from 'react'
import { Search, Package, Truck, CheckCircle, Clock, RotateCcw, ChevronRight } from 'lucide-react'

interface Order {
  id: string
  customer: string
  product: string
  qty: number
  amount: number
  marketplace: 'Amazon' | 'Flipkart' | 'Meesho'
  status: 'new' | 'processing' | 'shipped' | 'delivered' | 'return'
  date: string
  address: string
}

const orders: Order[] = [
  { id: 'ORD-4891', customer: 'Priya Sharma', product: 'Bamboo Spice Rack 6-Tier', qty: 2, amount: 1798, marketplace: 'Amazon', status: 'new', date: 'Jul 22, 2026', address: 'Mumbai, MH' },
  { id: 'ORD-4890', customer: 'Amit Verma', product: 'Kitchen Tool Set (5-pc)', qty: 1, amount: 849, marketplace: 'Flipkart', status: 'new', date: 'Jul 22, 2026', address: 'Delhi, DL' },
  { id: 'ORD-4889', customer: 'Sunita Reddy', product: 'Bamboo Storage Box Large', qty: 3, amount: 2097, marketplace: 'Meesho', status: 'delivered', date: 'Jul 21, 2026', address: 'Hyderabad, TS' },
  { id: 'ORD-4888', customer: 'Rohit Jain', product: 'Wooden Serving Board Set', qty: 1, amount: 1249, marketplace: 'Amazon', status: 'shipped', date: 'Jul 21, 2026', address: 'Bangalore, KA' },
  { id: 'ORD-4887', customer: 'Kavya Nair', product: 'Teak Wood Coasters (Set of 6)', qty: 2, amount: 1098, marketplace: 'Amazon', status: 'processing', date: 'Jul 20, 2026', address: 'Chennai, TN' },
  { id: 'ORD-4886', customer: 'Deepak Mehta', product: 'Bamboo Cutting Board Pro', qty: 1, amount: 1099, marketplace: 'Flipkart', status: 'shipped', date: 'Jul 20, 2026', address: 'Pune, MH' },
  { id: 'ORD-4885', customer: 'Meena Patel', product: 'Herb Garden Planter Set', qty: 1, amount: 1499, marketplace: 'Amazon', status: 'return', date: 'Jul 19, 2026', address: 'Ahmedabad, GJ' },
  { id: 'ORD-4884', customer: 'Suresh Kumar', product: 'Bamboo Desk Organizer', qty: 2, amount: 1298, marketplace: 'Meesho', status: 'delivered', date: 'Jul 19, 2026', address: 'Kolkata, WB' },
  { id: 'ORD-4883', customer: 'Anjali Singh', product: 'Eco Laundry Basket Set', qty: 1, amount: 1799, marketplace: 'Flipkart', status: 'delivered', date: 'Jul 18, 2026', address: 'Jaipur, RJ' },
  { id: 'ORD-4882', customer: 'Kiran Rao', product: 'Wooden Wall Clock Rustic', qty: 1, amount: 2199, marketplace: 'Amazon', status: 'processing', date: 'Jul 18, 2026', address: 'Bhopal, MP' },
  { id: 'ORD-4881', customer: 'Pooja Das', product: 'Bamboo Spice Rack 6-Tier', qty: 1, amount: 899, marketplace: 'Meesho', status: 'shipped', date: 'Jul 17, 2026', address: 'Lucknow, UP' },
  { id: 'ORD-4880', customer: 'Vikram Bose', product: 'Kitchen Tool Set (5-pc)', qty: 2, amount: 1698, marketplace: 'Amazon', status: 'delivered', date: 'Jul 17, 2026', address: 'Indore, MP' },
]

const statusConfig = {
  new: { label: 'New', color: 'bg-blue-50 text-blue-600', icon: Clock },
  processing: { label: 'Processing', color: 'bg-amber-50 text-amber-600', icon: Package },
  shipped: { label: 'Shipped', color: 'bg-purple-50 text-purple-600', icon: Truck },
  delivered: { label: 'Delivered', color: 'bg-emerald-50 text-emerald-600', icon: CheckCircle },
  return: { label: 'Return', color: 'bg-red-50 text-red-600', icon: RotateCcw },
}

const mktColor = { Amazon: 'bg-orange-50 text-orange-700', Flipkart: 'bg-blue-50 text-blue-600', Meesho: 'bg-purple-50 text-purple-600' }

export default function Orders() {
  const [search, setSearch] = useState('')
  const [statusFilter, setStatusFilter] = useState<string>('all')
  const [selectedOrder, setSelectedOrder] = useState<Order | null>(null)

  const filtered = orders.filter(o => {
    const matchSearch = o.id.toLowerCase().includes(search.toLowerCase()) || o.customer.toLowerCase().includes(search.toLowerCase()) || o.product.toLowerCase().includes(search.toLowerCase())
    const matchStatus = statusFilter === 'all' || o.status === statusFilter
    return matchSearch && matchStatus
  })

  const counts = {
    new: orders.filter(o => o.status === 'new').length,
    processing: orders.filter(o => o.status === 'processing').length,
    shipped: orders.filter(o => o.status === 'shipped').length,
    delivered: orders.filter(o => o.status === 'delivered').length,
    return: orders.filter(o => o.status === 'return').length,
  }

  return (
    <div className="p-6 fade-in">
      <div className="flex items-center justify-between mb-6">
        <div>
          <h2 className="text-xl font-bold text-gray-900">Orders</h2>
          <p className="text-[13px] text-gray-500 mt-0.5">{orders.length} total orders · Jul 2026</p>
        </div>
      </div>

      {/* Status summary */}
      <div className="grid grid-cols-5 gap-3 mb-6">
        {Object.entries(statusConfig).map(([key, cfg]) => {
          const Icon = cfg.icon
          const count = counts[key as keyof typeof counts]
          return (
            <button
              key={key}
              onClick={() => setStatusFilter(statusFilter === key ? 'all' : key)}
              className={`bg-white rounded-xl border p-4 text-left transition-all ${statusFilter === key ? 'border-primary shadow-sm' : 'border-gray-100 hover:border-gray-200'}`}
            >
              <div className={`w-8 h-8 rounded-lg flex items-center justify-center mb-2 ${cfg.color}`}>
                <Icon size={15} />
              </div>
              <div className="text-xl font-bold text-gray-900">{count}</div>
              <div className="text-[12px] text-gray-500">{cfg.label}</div>
            </button>
          )
        })}
      </div>

      <div className="flex gap-5">
        {/* Table */}
        <div className="flex-1 min-w-0">
          <div className="flex items-center gap-3 mb-4">
            <div className="relative flex-1 max-w-sm">
              <Search size={14} className="absolute left-3 top-1/2 -translate-y-1/2 text-gray-400" />
              <input
                value={search} onChange={e => setSearch(e.target.value)}
                placeholder="Search orders..."
                className="w-full pl-9 pr-4 py-2 text-[13px] bg-white border border-gray-200 rounded-lg placeholder-gray-400"
              />
            </div>
            <span className="text-[12.5px] text-gray-400">{filtered.length} results</span>
          </div>

          <div className="bg-white rounded-xl border border-gray-100 overflow-hidden">
            <table className="w-full">
              <thead>
                <tr className="border-b border-gray-100">
                  {['Order ID', 'Customer', 'Product', 'Amount', 'Platform', 'Status', 'Date', ''].map(h => (
                    <th key={h} className="text-left px-4 py-3 text-[11.5px] font-semibold text-gray-500 uppercase tracking-wide whitespace-nowrap">{h}</th>
                  ))}
                </tr>
              </thead>
              <tbody>
                {filtered.map(order => {
                  const cfg = statusConfig[order.status]
                  return (
                    <tr key={order.id} className="border-b border-gray-50 hover:bg-gray-50/50 transition-colors cursor-pointer" onClick={() => setSelectedOrder(selectedOrder?.id === order.id ? null : order)}>
                      <td className="px-4 py-3.5">
                        <span className="text-[12.5px] font-mono font-medium text-primary">{order.id}</span>
                      </td>
                      <td className="px-4 py-3.5">
                        <div className="flex items-center gap-2">
                          <div className="w-7 h-7 rounded-full bg-gradient-to-br from-primary to-purple-400 flex items-center justify-center text-white text-[10px] font-bold flex-shrink-0">
                            {order.customer.split(' ').map(n => n[0]).join('').slice(0,2)}
                          </div>
                          <div>
                            <div className="text-[13px] font-medium text-gray-800">{order.customer}</div>
                            <div className="text-[11px] text-gray-400">{order.address}</div>
                          </div>
                        </div>
                      </td>
                      <td className="px-4 py-3.5">
                        <div className="text-[12.5px] text-gray-700 max-w-[160px] truncate">{order.product}</div>
                        <div className="text-[11px] text-gray-400">Qty: {order.qty}</div>
                      </td>
                      <td className="px-4 py-3.5">
                        <span className="text-[13px] font-semibold text-gray-900">₹{order.amount.toLocaleString('en-IN')}</span>
                      </td>
                      <td className="px-4 py-3.5">
                        <span className={`badge ${mktColor[order.marketplace]}`}>{order.marketplace}</span>
                      </td>
                      <td className="px-4 py-3.5">
                        <span className={`badge ${cfg.color}`}>{cfg.label}</span>
                      </td>
                      <td className="px-4 py-3.5">
                        <span className="text-[12px] text-gray-500">{order.date}</span>
                      </td>
                      <td className="px-4 py-3.5">
                        <ChevronRight size={14} className="text-gray-400" />
                      </td>
                    </tr>
                  )
                })}
              </tbody>
            </table>
          </div>
        </div>

        {/* Detail panel */}
        {selectedOrder && (
          <div className="w-72 flex-shrink-0 bg-white rounded-xl border border-gray-100 p-5 fade-in">
            <div className="flex items-center justify-between mb-4">
              <h3 className="text-[13.5px] font-semibold text-gray-900">{selectedOrder.id}</h3>
              <span className={`badge ${statusConfig[selectedOrder.status].color}`}>{statusConfig[selectedOrder.status].label}</span>
            </div>
            <div className="space-y-3 text-[12.5px]">
              <div className="p-3 bg-gray-50 rounded-lg">
                <div className="text-gray-500 text-[11px] mb-1">Customer</div>
                <div className="font-medium text-gray-900">{selectedOrder.customer}</div>
                <div className="text-gray-500">{selectedOrder.address}</div>
              </div>
              <div className="p-3 bg-gray-50 rounded-lg">
                <div className="text-gray-500 text-[11px] mb-1">Product</div>
                <div className="font-medium text-gray-900">{selectedOrder.product}</div>
                <div className="text-gray-500">Quantity: {selectedOrder.qty}</div>
              </div>
              <div className="p-3 bg-gray-50 rounded-lg">
                <div className="text-gray-500 text-[11px] mb-1">Order Details</div>
                <div className="flex justify-between"><span className="text-gray-600">Amount</span><span className="font-semibold text-gray-900">₹{selectedOrder.amount.toLocaleString('en-IN')}</span></div>
                <div className="flex justify-between mt-1"><span className="text-gray-600">Platform</span><span className={`badge ${mktColor[selectedOrder.marketplace]}`}>{selectedOrder.marketplace}</span></div>
                <div className="flex justify-between mt-1"><span className="text-gray-600">Date</span><span className="text-gray-700">{selectedOrder.date}</span></div>
              </div>
              <div className="space-y-2 pt-2">
                <button className="w-full py-2 bg-primary text-white text-[13px] font-medium rounded-lg hover:bg-primary-hover transition-colors">View Full Details</button>
                {selectedOrder.status === 'processing' && (
                  <button className="w-full py-2 bg-emerald-50 text-emerald-700 text-[13px] font-medium rounded-lg hover:bg-emerald-100 transition-colors">Mark as Shipped</button>
                )}
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  )
}
