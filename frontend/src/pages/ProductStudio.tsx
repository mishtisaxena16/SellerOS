import { useState, useMemo } from 'react'
import { Sparkles, Plus, X, Save, Upload, Monitor, Smartphone, Star, RefreshCw, CheckCircle, AlertCircle, ChevronDown } from 'lucide-react'

interface ProductForm {
  title: string
  category: string
  brand: string
  price: string
  mrp: string
  stock: string
  description: string
  keywords: string[]
  features: string[]
  imageUrl: string
}

const CATEGORIES = ['Kitchen & Dining', 'Home Décor', 'Garden & Outdoors', 'Storage & Organization', 'Personal Care', 'Electronics', 'Clothing', 'Sports & Fitness']

const AI_SUGGESTIONS = [
  { type: 'title', priority: 'high', text: 'Add "Eco-Friendly" and your primary keyword to the first 80 characters of the title for maximum search impact.' },
  { type: 'description', priority: 'medium', text: 'Your description lacks social proof. Add a sentence about customer satisfaction (e.g., "Loved by 10,000+ home chefs").' },
  { type: 'keyword', priority: 'high', text: 'You\'re missing high-volume keyword "bamboo kitchen organizer" (18K searches/mo). Add it to bullet point 2.' },
  { type: 'image', priority: 'medium', text: 'Add a lifestyle image showing the product in use. Listings with lifestyle photos convert 34% better.' },
  { type: 'price', priority: 'low', text: 'Your price is 12% lower than the category average. You can increase by ₹80 without impacting conversion.' },
]


function SEOScoreRing({ score }: { score: number }) {
  const radius = 42
  const circumference = 2 * Math.PI * radius
  const offset = circumference - (score / 100) * circumference
  const color = score >= 80 ? '#10B981' : score >= 60 ? '#F59E0B' : '#EF4444'

  return (
    <div className="flex flex-col items-center">
      <div className="relative w-28 h-28">
        <svg viewBox="0 0 100 100" className="w-full h-full -rotate-90">
          <circle cx="50" cy="50" r={radius} fill="none" stroke="#F3F4F6" strokeWidth="8" />
          <circle
            cx="50" cy="50" r={radius} fill="none"
            stroke={color} strokeWidth="8" strokeLinecap="round"
            strokeDasharray={circumference}
            strokeDashoffset={offset}
            className="score-ring"
          />
        </svg>
        <div className="absolute inset-0 flex flex-col items-center justify-center">
          <span className="text-2xl font-bold text-gray-900">{score}</span>
          <span className="text-[10px] text-gray-500 font-medium">/ 100</span>
        </div>
      </div>
      <div className={`mt-2 text-[12px] font-semibold ${color === '#10B981' ? 'text-emerald-600' : color === '#F59E0B' ? 'text-amber-600' : 'text-red-500'}`}>
        {score >= 80 ? 'Excellent' : score >= 60 ? 'Good' : 'Needs Work'}
      </div>
    </div>
  )
}

function AmazonPreview({ product, mobile }: { product: ProductForm; mobile: boolean }) {
  const title = product.title || 'Your Product Title Will Appear Here'
  const price = product.price ? `₹${parseInt(product.price).toLocaleString('en-IN')}` : '₹0'
  const mrp = product.mrp ? `₹${parseInt(product.mrp).toLocaleString('en-IN')}` : ''

  if (mobile) {
    return (
      <div className="bg-white rounded-xl border-2 border-gray-200 overflow-hidden" style={{ width: 220, margin: '0 auto' }}>
        <div className="bg-[#232F3E] px-3 py-2 flex items-center gap-2">
          <span className="text-[#FF9900] font-bold text-[13px]">amazon</span>
          <div className="flex-1 bg-white/20 rounded h-5 flex items-center px-2">
            <span className="text-[9px] text-white/60 truncate">Search...</span>
          </div>
        </div>
        <div className="bg-[#F3F3F3] aspect-square flex items-center justify-center text-gray-300 text-[10px]">
          {product.imageUrl
            ? <img src={product.imageUrl} alt="" className="w-full h-full object-cover" onError={e => { (e.target as HTMLImageElement).style.display='none' }} />
            : 'Product Image'
          }
        </div>
        <div className="p-3 space-y-1.5">
          <div className="text-[11px] font-medium text-gray-900 leading-snug line-clamp-3">{title}</div>
          <div className="flex items-center gap-1">
            {[1,2,3,4].map(s => <Star key={s} size={9} fill="#FF9900" stroke="none" />)}
            <Star size={9} fill="#E5E7EB" stroke="none" />
            <span className="text-[9px] text-[#007185]">4,821</span>
          </div>
          <div className="flex items-baseline gap-1.5">
            <span className="text-[14px] font-bold text-gray-900">{price}</span>
            {mrp && <span className="text-[10px] text-gray-400 line-through">{mrp}</span>}
          </div>
          <div className="text-[9px] text-[#007600]">In Stock</div>
          <button className="w-full bg-[#FFD814] text-gray-900 text-[11px] font-semibold py-1.5 rounded-full mt-1">Add to Cart</button>
        </div>
      </div>
    )
  }

  return (
    <div className="bg-white border border-gray-200 rounded-lg overflow-hidden text-[12px]">
      <div className="bg-[#232F3E] px-4 py-2 flex items-center gap-3">
        <span className="text-[#FF9900] font-bold text-[15px]">amazon</span>
        <div className="flex-1 bg-white rounded flex items-center px-3 py-1">
          <span className="text-gray-400 text-[11px] flex-1">{title.slice(0, 40)}</span>
          <span className="text-[10px] text-gray-500 bg-gray-100 px-2 py-0.5 rounded">All</span>
        </div>
      </div>
      <div className="flex gap-4 p-4">
        <div className="w-44 h-44 bg-gray-50 border border-gray-100 rounded flex items-center justify-center flex-shrink-0 overflow-hidden">
          {product.imageUrl
            ? <img src={product.imageUrl} alt="" className="w-full h-full object-contain" onError={e => { (e.target as HTMLImageElement).style.display='none' }} />
            : <span className="text-gray-300 text-[10px]">Product Image</span>
          }
        </div>
        <div className="flex-1 space-y-2">
          <div className="text-[11px] text-[#007185]">{product.brand || 'Your Brand'}</div>
          <div className="text-[14px] font-medium text-gray-900 leading-snug">{title}</div>
          <div className="flex items-center gap-2">
            <div className="flex">{[1,2,3,4].map(s => <Star key={s} size={11} fill="#FF9900" stroke="none" />)}<Star size={11} fill="#E5E7EB" stroke="none" /></div>
            <span className="text-[11px] text-[#007185]">4,821 ratings</span>
          </div>
          <div className="border-t pt-2">
            <span className="text-[11px] text-gray-600">₹ </span>
            <span className="text-xl font-bold text-gray-900">{price.replace('₹','')}</span>
            {mrp && <span className="text-[11px] text-gray-400 ml-2">M.R.P: <s>{mrp}</s></span>}
          </div>
          <div className="text-[10px] text-[#007600] font-medium">In Stock</div>
          {product.features.slice(0,3).map((f, i) => (
            <div key={i} className="text-[10.5px] text-gray-700 flex items-start gap-1">
              <span className="text-gray-400 mt-0.5">•</span>{f}
            </div>
          ))}
        </div>
      </div>
    </div>
  )
}

function FlipkartPreview({ product, mobile }: { product: ProductForm; mobile: boolean }) {
  const title = product.title || 'Your Product Title'
  const price = product.price ? `₹${parseInt(product.price).toLocaleString('en-IN')}` : '₹0'

  if (mobile) {
    return (
      <div className="bg-white rounded-xl border-2 border-gray-200 overflow-hidden" style={{ width: 220, margin: '0 auto' }}>
        <div className="bg-[#2874F0] px-3 py-2">
          <span className="text-white font-bold text-[13px] italic">Flipkart</span>
        </div>
        <div className="aspect-square bg-gray-50 flex items-center justify-center overflow-hidden">
          {product.imageUrl
            ? <img src={product.imageUrl} alt="" className="w-full h-full object-cover" onError={e => { (e.target as HTMLImageElement).style.display='none' }} />
            : <span className="text-gray-300 text-[10px]">Image</span>
          }
        </div>
        <div className="p-3 space-y-1.5">
          <div className="text-[11px] font-medium text-gray-900 line-clamp-2">{title}</div>
          <div className="flex items-center gap-1">
            <span className="bg-[#388E3C] text-white text-[9px] px-1.5 py-0.5 rounded font-bold">4.3 ★</span>
            <span className="text-[9px] text-gray-400">2,341 ratings</span>
          </div>
          <div className="text-[14px] font-bold text-gray-900">{price}</div>
          <div className="flex gap-1.5 mt-1">
            <button className="flex-1 bg-[#FF6161] text-white text-[10px] font-semibold py-1.5 rounded">Buy Now</button>
            <button className="flex-1 bg-[#FF9F00] text-white text-[10px] font-semibold py-1.5 rounded">Add to Cart</button>
          </div>
        </div>
      </div>
    )
  }

  return (
    <div className="bg-[#F1F3F6] border border-gray-200 rounded-lg overflow-hidden text-[12px]">
      <div className="bg-[#2874F0] px-4 py-2 flex items-center gap-3">
        <span className="text-white font-bold text-[15px] italic">Flipkart</span>
        <div className="flex-1 bg-[#F5F5F5] rounded flex items-center px-3 py-1 gap-2">
          <span className="text-gray-400 text-[11px]">Search for products…</span>
        </div>
      </div>
      <div className="bg-white m-3 rounded-lg p-4 flex gap-4">
        <div className="w-40 h-40 border border-gray-100 rounded flex items-center justify-center flex-shrink-0 overflow-hidden">
          {product.imageUrl
            ? <img src={product.imageUrl} alt="" className="w-full h-full object-contain" onError={e => { (e.target as HTMLImageElement).style.display='none' }} />
            : <span className="text-gray-300 text-[10px]">Image</span>
          }
        </div>
        <div className="flex-1">
          <div className="text-[14px] font-medium text-gray-900">{title}</div>
          <div className="flex items-center gap-2 mt-1">
            <span className="bg-[#388E3C] text-white text-[10px] px-1.5 py-0.5 rounded font-bold">4.3 ★</span>
            <span className="text-[11px] text-gray-400">2,341 Ratings & 412 Reviews</span>
          </div>
          <div className="mt-2">
            <span className="text-[18px] font-bold text-gray-900">{price}</span>
            {product.mrp && <span className="text-[11px] text-gray-400 ml-2 line-through">₹{parseInt(product.mrp).toLocaleString('en-IN')}</span>}
          </div>
          <div className="mt-2 text-[10.5px] text-gray-600 space-y-1">
            {product.features.slice(0,3).map((f,i) => (
              <div key={i} className="flex items-start gap-1"><span className="text-[#2874F0] mt-0.5">✓</span>{f}</div>
            ))}
          </div>
          <div className="flex gap-2 mt-3">
            <button className="px-4 py-1.5 bg-[#FF9F00] text-white text-[11px] font-bold rounded">ADD TO CART</button>
            <button className="px-4 py-1.5 bg-[#FB641B] text-white text-[11px] font-bold rounded">BUY NOW</button>
          </div>
        </div>
      </div>
    </div>
  )
}

function MeeshoPreview({ product, mobile }: { product: ProductForm; mobile: boolean }) {
  const title = product.title || 'Your Product Title'
  const price = product.price ? `₹${parseInt(product.price).toLocaleString('en-IN')}` : '₹0'

  if (mobile) {
    return (
      <div className="bg-white rounded-xl border-2 border-gray-200 overflow-hidden" style={{ width: 220, margin: '0 auto' }}>
        <div className="bg-[#9B2F8A] px-3 py-2">
          <span className="text-white font-bold text-[13px]">meesho</span>
        </div>
        <div className="aspect-square bg-pink-50 flex items-center justify-center overflow-hidden">
          {product.imageUrl
            ? <img src={product.imageUrl} alt="" className="w-full h-full object-cover" onError={e => { (e.target as HTMLImageElement).style.display='none' }} />
            : <span className="text-gray-300 text-[10px]">Image</span>
          }
        </div>
        <div className="p-3 space-y-1">
          <div className="text-[11px] font-medium text-gray-900 line-clamp-2">{title}</div>
          <div className="text-[13px] font-bold text-gray-900">{price}</div>
          <div className="text-[9px] text-gray-400">Free Delivery</div>
          <button className="w-full bg-[#9B2F8A] text-white text-[11px] font-semibold py-1.5 rounded mt-1">Add to Cart</button>
        </div>
      </div>
    )
  }

  return (
    <div className="bg-white border border-gray-200 rounded-lg overflow-hidden text-[12px]">
      <div className="bg-[#9B2F8A] px-4 py-2 flex items-center gap-3">
        <span className="text-white font-bold text-[15px]">meesho</span>
        <div className="flex-1 bg-white/20 rounded flex items-center px-3 py-1">
          <span className="text-white/60 text-[11px]">Search for products</span>
        </div>
      </div>
      <div className="p-4 flex gap-4">
        <div className="w-44 h-52 bg-pink-50 rounded flex items-center justify-center flex-shrink-0 overflow-hidden">
          {product.imageUrl
            ? <img src={product.imageUrl} alt="" className="w-full h-full object-contain" onError={e => { (e.target as HTMLImageElement).style.display='none' }} />
            : <span className="text-gray-300 text-[10px]">Image</span>
          }
        </div>
        <div className="flex-1">
          <div className="text-[13.5px] font-medium text-gray-900 leading-snug">{title}</div>
          <div className="text-[10.5px] text-gray-500 mt-0.5">{product.brand || 'Brand Name'}</div>
          <div className="mt-2 flex items-baseline gap-2">
            <span className="text-[20px] font-bold text-gray-900">{price}</span>
            {product.mrp && <span className="text-[11px] text-gray-400 line-through">₹{parseInt(product.mrp).toLocaleString('en-IN')}</span>}
          </div>
          <div className="mt-1 text-[11px] text-green-600 font-medium">✓ FREE Delivery</div>
          <div className="mt-3 space-y-1">
            {product.features.slice(0,3).map((f,i) => (
              <div key={i} className="text-[10.5px] text-gray-600 flex gap-1"><span>•</span>{f}</div>
            ))}
          </div>
          <button className="mt-3 px-5 py-2 bg-[#9B2F8A] text-white text-[12px] font-semibold rounded">Add to Cart</button>
        </div>
      </div>
    </div>
  )
}

export default function ProductStudio() {
  const [product, setProduct] = useState<ProductForm>({
    title: 'Bamboo Spice Rack Organizer — 6 Tier Kitchen Counter Shelf',
    category: 'Kitchen & Dining',
    brand: 'GreenNest',
    price: '899',
    mrp: '1299',
    stock: '120',
    description: 'Organize your kitchen spices in style with this premium bamboo spice rack. Features 6 adjustable tiers perfect for bottles, jars, and containers. Crafted from 100% sustainable bamboo, this eco-friendly organizer adds a natural, warm aesthetic to any countertop or cabinet.',
    keywords: ['bamboo spice rack', 'kitchen organizer', 'eco-friendly', 'countertop storage', 'spice holder'],
    features: ['Premium sustainable bamboo', '6 adjustable tiers', 'Holds 30+ spice bottles', 'Easy assembly, no tools needed'],
    imageUrl: '',
  })

  const [marketplace, setMarketplace] = useState<'amazon' | 'flipkart' | 'meesho'>('amazon')
  const [device, setDevice] = useState<'desktop' | 'mobile'>('desktop')
  const [newKeyword, setNewKeyword] = useState('')
  const [newFeature, setNewFeature] = useState('')
  const [saving, setSaving] = useState(false)
  const [saved, setSaved] = useState(false)

  const seoScore = useMemo(() => {
    let score = 0
    if (product.title.length > 20) score += 15
    if (product.title.length > 50) score += 10
    if (product.title.length > 80) score += 5
    if (product.description.length > 100) score += 15
    if (product.description.length > 300) score += 10
    if (product.keywords.length >= 3) score += 15
    if (product.keywords.length >= 6) score += 10
    if (product.price) score += 5
    if (product.brand) score += 5
    if (product.features.length >= 2) score += 5
    if (product.features.length >= 4) score += 5
    if (product.imageUrl) score += 10 - Math.min(10, 0)
    return Math.min(Math.round(score), 100)
  }, [product])

  const handleSave = () => {
    setSaving(true)
    setTimeout(() => { setSaving(false); setSaved(true); setTimeout(() => setSaved(false), 2500) }, 1200)
  }

  const addKeyword = () => {
    if (newKeyword.trim() && !product.keywords.includes(newKeyword.trim())) {
      setProduct(p => ({ ...p, keywords: [...p.keywords, newKeyword.trim()] }))
      setNewKeyword('')
    }
  }

  const addFeature = () => {
    if (newFeature.trim()) {
      setProduct(p => ({ ...p, features: [...p.features, newFeature.trim()] }))
      setNewFeature('')
    }
  }

  return (
    <div className="p-6 fade-in">
      {/* Header */}
      <div className="flex items-center justify-between mb-6">
        <div>
          <div className="flex items-center gap-2 mb-1">
            <h2 className="text-xl font-bold text-gray-900">Product Studio</h2>
            <span className="badge bg-primary-50 text-primary border border-primary-100">
              <Sparkles size={10} /> AI-Powered
            </span>
          </div>
          <p className="text-[13px] text-gray-500">Create and optimize listings with AI. Preview updates live.</p>
        </div>
        <div className="flex items-center gap-3">
          <button onClick={handleSave} disabled={saving}
            className="flex items-center gap-2 px-4 py-2 bg-white border border-gray-200 text-gray-700 text-[13px] font-medium rounded-lg hover:bg-gray-50 transition-colors">
            <Save size={14} />
            {saving ? 'Saving…' : saved ? '✓ Saved' : 'Save Draft'}
          </button>
          <button className="flex items-center gap-2 px-4 py-2 bg-primary text-white text-[13px] font-medium rounded-lg hover:bg-primary-hover transition-colors shadow-sm">
            <Upload size={14} />
            Publish to All
          </button>
        </div>
      </div>

      {/* Three column layout */}
      <div className="grid grid-cols-1 xl:grid-cols-[380px_1fr_380px] gap-5">
        {/* LEFT: Product form */}
        <div className="bg-white rounded-xl border border-gray-100 overflow-hidden">
          <div className="px-5 py-4 border-b border-gray-100">
            <h3 className="text-[13.5px] font-semibold text-gray-900">Product Details</h3>
          </div>
          <div className="p-5 space-y-4 overflow-y-auto" style={{ maxHeight: 'calc(100vh - 220px)' }}>
            {/* Title */}
            <div>
              <label className="block text-[12px] font-medium text-gray-700 mb-1.5">
                Product Title <span className="text-gray-400 font-normal">({product.title.length}/200)</span>
              </label>
              <input
                value={product.title}
                onChange={e => setProduct(p => ({ ...p, title: e.target.value }))}
                className="w-full border border-gray-200 rounded-lg px-3 py-2.5 text-[13px] text-gray-900 bg-gray-50 placeholder-gray-400"
                placeholder="Enter descriptive product title..."
              />
              <div className="mt-1 h-1 bg-gray-100 rounded-full overflow-hidden">
                <div className="h-full bg-primary rounded-full transition-all" style={{ width: `${Math.min(product.title.length / 200 * 100, 100)}%` }} />
              </div>
            </div>

            {/* Category + Brand */}
            <div className="grid grid-cols-2 gap-3">
              <div>
                <label className="block text-[12px] font-medium text-gray-700 mb-1.5">Category</label>
                <div className="relative">
                  <select
                    value={product.category}
                    onChange={e => setProduct(p => ({ ...p, category: e.target.value }))}
                    className="w-full border border-gray-200 rounded-lg px-3 py-2.5 text-[13px] text-gray-900 bg-gray-50 appearance-none"
                  >
                    {CATEGORIES.map(c => <option key={c}>{c}</option>)}
                  </select>
                  <ChevronDown size={13} className="absolute right-3 top-1/2 -translate-y-1/2 text-gray-400 pointer-events-none" />
                </div>
              </div>
              <div>
                <label className="block text-[12px] font-medium text-gray-700 mb-1.5">Brand</label>
                <input
                  value={product.brand}
                  onChange={e => setProduct(p => ({ ...p, brand: e.target.value }))}
                  className="w-full border border-gray-200 rounded-lg px-3 py-2.5 text-[13px] text-gray-900 bg-gray-50"
                  placeholder="Brand name"
                />
              </div>
            </div>

            {/* Pricing */}
            <div className="grid grid-cols-3 gap-3">
              <div>
                <label className="block text-[12px] font-medium text-gray-700 mb-1.5">Selling Price (₹)</label>
                <input
                  type="number" value={product.price}
                  onChange={e => setProduct(p => ({ ...p, price: e.target.value }))}
                  className="w-full border border-gray-200 rounded-lg px-3 py-2.5 text-[13px] text-gray-900 bg-gray-50"
                  placeholder="0"
                />
              </div>
              <div>
                <label className="block text-[12px] font-medium text-gray-700 mb-1.5">MRP (₹)</label>
                <input
                  type="number" value={product.mrp}
                  onChange={e => setProduct(p => ({ ...p, mrp: e.target.value }))}
                  className="w-full border border-gray-200 rounded-lg px-3 py-2.5 text-[13px] text-gray-900 bg-gray-50"
                  placeholder="0"
                />
              </div>
              <div>
                <label className="block text-[12px] font-medium text-gray-700 mb-1.5">Stock</label>
                <input
                  type="number" value={product.stock}
                  onChange={e => setProduct(p => ({ ...p, stock: e.target.value }))}
                  className="w-full border border-gray-200 rounded-lg px-3 py-2.5 text-[13px] text-gray-900 bg-gray-50"
                  placeholder="0"
                />
              </div>
            </div>

            {/* Description */}
            <div>
              <label className="block text-[12px] font-medium text-gray-700 mb-1.5">
                Description <span className="text-gray-400 font-normal">({product.description.length}/2000)</span>
              </label>
              <textarea
                value={product.description}
                onChange={e => setProduct(p => ({ ...p, description: e.target.value }))}
                rows={4}
                className="w-full border border-gray-200 rounded-lg px-3 py-2.5 text-[13px] text-gray-900 bg-gray-50 resize-none"
                placeholder="Describe your product in detail..."
              />
            </div>

            {/* Keywords */}
            <div>
              <label className="block text-[12px] font-medium text-gray-700 mb-1.5">Search Keywords</label>
              <div className="flex flex-wrap gap-1.5 mb-2">
                {product.keywords.map((k, i) => (
                  <span key={i} className="flex items-center gap-1 text-[11.5px] bg-primary-50 text-primary px-2 py-1 rounded-md">
                    {k}
                    <button onClick={() => setProduct(p => ({ ...p, keywords: p.keywords.filter((_, j) => j !== i) }))}>
                      <X size={11} />
                    </button>
                  </span>
                ))}
              </div>
              <div className="flex gap-2">
                <input
                  value={newKeyword}
                  onChange={e => setNewKeyword(e.target.value)}
                  onKeyDown={e => e.key === 'Enter' && addKeyword()}
                  className="flex-1 border border-gray-200 rounded-lg px-3 py-2 text-[13px] bg-gray-50"
                  placeholder="Add keyword and press Enter..."
                />
                <button onClick={addKeyword} className="px-3 py-2 bg-gray-100 rounded-lg hover:bg-gray-200 transition-colors">
                  <Plus size={14} className="text-gray-600" />
                </button>
              </div>
            </div>

            {/* Features */}
            <div>
              <label className="block text-[12px] font-medium text-gray-700 mb-1.5">Key Features / Bullet Points</label>
              <div className="space-y-1.5 mb-2">
                {product.features.map((f, i) => (
                  <div key={i} className="flex items-center gap-2 p-2 bg-gray-50 rounded-lg border border-gray-100">
                    <span className="text-primary text-[11px] font-bold">•</span>
                    <span className="flex-1 text-[12.5px] text-gray-700">{f}</span>
                    <button onClick={() => setProduct(p => ({ ...p, features: p.features.filter((_, j) => j !== i) }))}>
                      <X size={12} className="text-gray-400 hover:text-gray-600" />
                    </button>
                  </div>
                ))}
              </div>
              <div className="flex gap-2">
                <input
                  value={newFeature}
                  onChange={e => setNewFeature(e.target.value)}
                  onKeyDown={e => e.key === 'Enter' && addFeature()}
                  className="flex-1 border border-gray-200 rounded-lg px-3 py-2 text-[13px] bg-gray-50"
                  placeholder="Add a key feature..."
                />
                <button onClick={addFeature} className="px-3 py-2 bg-gray-100 rounded-lg hover:bg-gray-200 transition-colors">
                  <Plus size={14} className="text-gray-600" />
                </button>
              </div>
            </div>

            {/* Image URL */}
            <div>
              <label className="block text-[12px] font-medium text-gray-700 mb-1.5">Main Image URL</label>
              <input
                value={product.imageUrl}
                onChange={e => setProduct(p => ({ ...p, imageUrl: e.target.value }))}
                className="w-full border border-gray-200 rounded-lg px-3 py-2.5 text-[13px] bg-gray-50"
                placeholder="https://..."
              />
            </div>
          </div>
        </div>

        {/* MIDDLE: AI Optimizer */}
        <div className="space-y-4">
          {/* SEO Score card */}
          <div className="bg-white rounded-xl border border-gray-100 p-5">
            <div className="flex items-center justify-between mb-4">
              <h3 className="text-[13.5px] font-semibold text-gray-900 flex items-center gap-2">
                <Sparkles size={15} className="text-primary" /> AI Listing Optimizer
              </h3>
              <button className="text-[12px] text-gray-500 hover:text-primary transition-colors flex items-center gap-1">
                <RefreshCw size={12} /> Refresh
              </button>
            </div>

            <div className="flex items-center gap-6">
              <SEOScoreRing score={seoScore} />
              <div className="flex-1 space-y-2.5">
                {[
                  { label: 'Title', score: product.title.length > 60 ? 92 : product.title.length > 30 ? 75 : 40 },
                  { label: 'Description', score: product.description.length > 300 ? 88 : product.description.length > 100 ? 70 : 35 },
                  { label: 'Keywords', score: product.keywords.length >= 6 ? 95 : product.keywords.length >= 3 ? 72 : 45 },
                  { label: 'Images', score: product.imageUrl ? 90 : 30 },
                ].map(({ label, score }) => (
                  <div key={label}>
                    <div className="flex justify-between text-[11.5px] mb-1">
                      <span className="text-gray-600">{label}</span>
                      <span className={`font-medium ${score >= 80 ? 'text-emerald-600' : score >= 60 ? 'text-amber-600' : 'text-red-500'}`}>{score}</span>
                    </div>
                    <div className="h-1.5 bg-gray-100 rounded-full overflow-hidden">
                      <div
                        className={`h-full rounded-full transition-all duration-500 ${score >= 80 ? 'bg-emerald-400' : score >= 60 ? 'bg-amber-400' : 'bg-red-400'}`}
                        style={{ width: `${score}%` }}
                      />
                    </div>
                  </div>
                ))}
              </div>
            </div>
          </div>

          {/* Keyword analysis */}
          <div className="bg-white rounded-xl border border-gray-100 p-5">
            <h3 className="text-[13.5px] font-semibold text-gray-900 mb-3">Keyword Analysis</h3>
            <div className="space-y-2">
              {[
                { kw: 'bamboo spice rack', vol: '22K', comp: 'Medium', in: true },
                { kw: 'kitchen organizer', vol: '85K', comp: 'High', in: product.keywords.includes('kitchen organizer') },
                { kw: 'bamboo kitchen organizer', vol: '18K', comp: 'Low', in: false },
                { kw: 'eco-friendly storage', vol: '12K', comp: 'Low', in: product.keywords.includes('eco-friendly') },
                { kw: 'spice holder stand', vol: '9K', comp: 'Low', in: false },
              ].map(({ kw, vol, comp, in: included }) => (
                <div key={kw} className="flex items-center gap-3 p-2.5 rounded-lg border border-gray-100 hover:border-gray-200 transition-colors">
                  <CheckCircle size={14} className={included ? 'text-emerald-500' : 'text-gray-300'} />
                  <span className="flex-1 text-[12.5px] text-gray-800">{kw}</span>
                  <span className="text-[11px] text-gray-500 w-10">{vol}/mo</span>
                  <span className={`badge text-[10px] ${comp === 'Low' ? 'bg-emerald-50 text-emerald-600' : comp === 'Medium' ? 'bg-amber-50 text-amber-600' : 'bg-red-50 text-red-500'}`}>
                    {comp}
                  </span>
                  {!included && (
                    <button
                      onClick={() => setProduct(p => ({ ...p, keywords: [...p.keywords, kw] }))}
                      className="text-[11px] text-primary hover:text-primary-hover font-medium"
                    >
                      + Add
                    </button>
                  )}
                </div>
              ))}
            </div>
          </div>

          {/* AI Suggestions */}
          <div className="bg-white rounded-xl border border-gray-100 p-5">
            <div className="flex items-center gap-2 mb-3">
              <Sparkles size={14} className="text-primary" />
              <h3 className="text-[13.5px] font-semibold text-gray-900">AI Suggestions</h3>
              <span className="badge bg-red-50 text-red-500">{AI_SUGGESTIONS.filter(s => s.priority === 'high').length} High</span>
            </div>
            <div className="space-y-2.5">
              {AI_SUGGESTIONS.map((s, i) => (
                <div key={i} className={`p-3 rounded-lg border ${
                  s.priority === 'high' ? 'border-red-100 bg-red-50/50' :
                  s.priority === 'medium' ? 'border-amber-100 bg-amber-50/50' :
                  'border-gray-100 bg-gray-50/50'
                }`}>
                  <div className="flex items-start gap-2">
                    <AlertCircle size={13} className={`mt-0.5 flex-shrink-0 ${
                      s.priority === 'high' ? 'text-red-500' : s.priority === 'medium' ? 'text-amber-500' : 'text-gray-400'
                    }`} />
                    <p className="text-[12px] text-gray-700 leading-relaxed">{s.text}</p>
                  </div>
                </div>
              ))}
            </div>
          </div>
        </div>

        {/* RIGHT: Marketplace Preview */}
        <div className="bg-white rounded-xl border border-gray-100 overflow-hidden">
          <div className="px-5 py-4 border-b border-gray-100">
            <h3 className="text-[13.5px] font-semibold text-gray-900 mb-3">Live Preview</h3>
            {/* Marketplace tabs */}
            <div className="flex gap-1 mb-3">
              {(['amazon', 'flipkart', 'meesho'] as const).map(m => (
                <button key={m} onClick={() => setMarketplace(m)}
                  className={`flex-1 py-1.5 text-[11.5px] font-medium rounded-lg capitalize transition-colors ${
                    marketplace === m ? 'bg-primary text-white' : 'bg-gray-100 text-gray-600 hover:bg-gray-200'
                  }`}>
                  {m === 'amazon' ? 'Amazon' : m === 'flipkart' ? 'Flipkart' : 'Meesho'}
                </button>
              ))}
            </div>
            {/* Device toggle */}
            <div className="flex gap-1">
              {([['desktop', Monitor], ['mobile', Smartphone]] as const).map(([d, Icon]) => (
                <button key={d} onClick={() => setDevice(d as 'desktop' | 'mobile')}
                  className={`flex items-center gap-1.5 px-3 py-1.5 text-[11.5px] font-medium rounded-lg transition-colors ${
                    device === d ? 'bg-gray-900 text-white' : 'bg-gray-100 text-gray-600 hover:bg-gray-200'
                  }`}>
                  <Icon size={12} /> {d === 'desktop' ? 'Desktop' : 'Mobile'}
                </button>
              ))}
            </div>
          </div>

          <div className="p-4 overflow-y-auto" style={{ maxHeight: 'calc(100vh - 300px)' }}>
            {marketplace === 'amazon' && <AmazonPreview product={product} mobile={device === 'mobile'} />}
            {marketplace === 'flipkart' && <FlipkartPreview product={product} mobile={device === 'mobile'} />}
            {marketplace === 'meesho' && <MeeshoPreview product={product} mobile={device === 'mobile'} />}
          </div>
        </div>
      </div>
    </div>
  )
}
