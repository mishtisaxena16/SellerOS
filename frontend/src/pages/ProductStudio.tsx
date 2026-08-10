import { useState, useMemo, useEffect } from 'react'
import { Sparkles, Plus, X, Save, Upload, Monitor, Smartphone, Star, ChevronDown, PackagePlus, Boxes, Loader2 } from 'lucide-react'
import AgentConsole from '../components/AgentConsole'
import ListingsCatalogTable from '../components/ListingsCatalogTable'
import { usePlatform } from '../context/PlatformContext'
import { getInventory, type InventoryItem } from '../api/inventory'
import type { ListingViewRow } from '../mock/listingsView'

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

// Original generic demo list, kept for blank/new listings.
const GENERIC_CATEGORIES = ['Kitchen & Dining', 'Home Décor', 'Garden & Outdoors', 'Storage & Organization', 'Personal Care', 'Electronics', 'Clothing', 'Sports & Fitness']
// Phase 7.4: the seller catalog (products.ts / mock/listingsView.ts) uses a
// different, real category taxonomy for ABC Fashion Store. Appended rather
// than replacing GENERIC_CATEGORIES so "Optimize" on a catalog product can
// select the product's actual category instead of silently falling back to
// an unrelated option — the two lists previously didn't overlap at all.
const CATALOG_CATEGORIES = ["Women's Apparel", "Men's Apparel", 'Footwear', 'Accessories', 'Activewear', 'Outerwear']
const CATEGORIES = [...GENERIC_CATEGORIES, ...CATALOG_CATEGORIES]



function SEOScoreRing({ score }: { score: number }) {
  const radius = 42
  const circumference = 2 * Math.PI * radius
  const offset = circumference - (score / 100) * circumference
  const color = score >= 80 ? 'var(--green)' : score >= 60 ? 'var(--amber)' : 'var(--red)'

  return (
    <div className="flex flex-col items-center">
      <div className="relative w-28 h-28">
        <svg viewBox="0 0 100 100" className="w-full h-full -rotate-90">
          <circle cx="50" cy="50" r={radius} fill="none" stroke="var(--border)" strokeWidth="8" />
          <circle
            cx="50" cy="50" r={radius} fill="none"
            stroke={color} strokeWidth="8" strokeLinecap="round"
            strokeDasharray={circumference}
            strokeDashoffset={offset}
            className="score-ring"
          />
        </svg>
        <div className="absolute inset-0 flex flex-col items-center justify-center">
          <span className="text-2xl font-bold text-app">{score}</span>
          <span className="text-[10px] text-dim font-medium">/ 100</span>
        </div>
      </div>
      <div className={`mt-2 text-[12px] font-semibold ${color === 'var(--green)' ? 'text-accent-green' : color === 'var(--amber)' ? 'text-accent-amber' : 'text-accent-red'}`}>
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
      <div className="bg-elev rounded-xl border-2 border-app overflow-hidden" style={{ width: 220, margin: '0 auto' }}>
        <div className="bg-[#232F3E] px-3 py-2 flex items-center gap-2">
          <span className="text-[#FF9900] font-bold text-[13px]">amazon</span>
          <div className="flex-1 bg-elev/20 rounded h-5 flex items-center px-2">
            <span className="text-[9px] text-white/60 truncate">Search...</span>
          </div>
        </div>
        <div className="bg-[#F3F3F3] aspect-square flex items-center justify-center text-faint text-[10px]">
          {product.imageUrl
            ? <img src={product.imageUrl} alt="" className="w-full h-full object-cover" onError={e => { (e.target as HTMLImageElement).style.display='none' }} />
            : 'Product Image'
          }
        </div>
        <div className="p-3 space-y-1.5">
          <div className="text-[11px] font-medium text-app leading-snug line-clamp-3">{title}</div>
          <div className="flex items-center gap-1">
            {[1,2,3,4].map(s => <Star key={s} size={9} fill="#FF9900" stroke="none" />)}
            <Star size={9} fill="#E5E7EB" stroke="none" />
            <span className="text-[9px] text-[#007185]">4,821</span>
          </div>
          <div className="flex items-baseline gap-1.5">
            <span className="text-[14px] font-bold text-app">{price}</span>
            {mrp && <span className="text-[10px] text-faint line-through">{mrp}</span>}
          </div>
          <div className="text-[9px] text-[#007600]">In Stock</div>
          <button className="w-full bg-[#FFD814] text-app text-[11px] font-semibold py-1.5 rounded-full mt-1">Add to Cart</button>
        </div>
      </div>
    )
  }

  return (
    <div className="bg-elev border border-app rounded-lg overflow-hidden text-[12px]">
      <div className="bg-[#232F3E] px-4 py-2 flex items-center gap-3">
        <span className="text-[#FF9900] font-bold text-[15px]">amazon</span>
        <div className="flex-1 bg-elev rounded flex items-center px-3 py-1">
          <span className="text-faint text-[11px] flex-1">{title.slice(0, 40)}</span>
          <span className="text-[10px] text-dim bg-surface px-2 py-0.5 rounded">All</span>
        </div>
      </div>
      <div className="flex gap-4 p-4">
        <div className="w-44 h-44 bg-surface border border-app rounded flex items-center justify-center flex-shrink-0 overflow-hidden">
          {product.imageUrl
            ? <img src={product.imageUrl} alt="" className="w-full h-full object-contain" onError={e => { (e.target as HTMLImageElement).style.display='none' }} />
            : <span className="text-faint text-[10px]">Product Image</span>
          }
        </div>
        <div className="flex-1 space-y-2">
          <div className="text-[11px] text-[#007185]">{product.brand || 'Your Brand'}</div>
          <div className="text-[14px] font-medium text-app leading-snug">{title}</div>
          <div className="flex items-center gap-2">
            <div className="flex">{[1,2,3,4].map(s => <Star key={s} size={11} fill="#FF9900" stroke="none" />)}<Star size={11} fill="#E5E7EB" stroke="none" /></div>
            <span className="text-[11px] text-[#007185]">4,821 ratings</span>
          </div>
          <div className="border-t pt-2">
            <span className="text-[11px] text-dim">₹ </span>
            <span className="text-xl font-bold text-app">{price.replace('₹','')}</span>
            {mrp && <span className="text-[11px] text-faint ml-2">M.R.P: <s>{mrp}</s></span>}
          </div>
          <div className="text-[10px] text-[#007600] font-medium">In Stock</div>
          {product.features.slice(0,3).map((f, i) => (
            <div key={i} className="text-[10.5px] text-dim flex items-start gap-1">
              <span className="text-faint mt-0.5">•</span>{f}
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
      <div className="bg-elev rounded-xl border-2 border-app overflow-hidden" style={{ width: 220, margin: '0 auto' }}>
        <div className="bg-[#2874F0] px-3 py-2">
          <span className="text-white font-bold text-[13px] italic">Flipkart</span>
        </div>
        <div className="aspect-square bg-surface flex items-center justify-center overflow-hidden">
          {product.imageUrl
            ? <img src={product.imageUrl} alt="" className="w-full h-full object-cover" onError={e => { (e.target as HTMLImageElement).style.display='none' }} />
            : <span className="text-faint text-[10px]">Image</span>
          }
        </div>
        <div className="p-3 space-y-1.5">
          <div className="text-[11px] font-medium text-app line-clamp-2">{title}</div>
          <div className="flex items-center gap-1">
            <span className="bg-[#388E3C] text-white text-[9px] px-1.5 py-0.5 rounded font-bold">4.3 ★</span>
            <span className="text-[9px] text-faint">2,341 ratings</span>
          </div>
          <div className="text-[14px] font-bold text-app">{price}</div>
          <div className="flex gap-1.5 mt-1">
            <button className="flex-1 bg-[#FF6161] text-white text-[10px] font-semibold py-1.5 rounded">Buy Now</button>
            <button className="flex-1 bg-[#FF9F00] text-white text-[10px] font-semibold py-1.5 rounded">Add to Cart</button>
          </div>
        </div>
      </div>
    )
  }

  return (
    <div className="bg-[#F1F3F6] border border-app rounded-lg overflow-hidden text-[12px]">
      <div className="bg-[#2874F0] px-4 py-2 flex items-center gap-3">
        <span className="text-white font-bold text-[15px] italic">Flipkart</span>
        <div className="flex-1 bg-[#F5F5F5] rounded flex items-center px-3 py-1 gap-2">
          <span className="text-faint text-[11px]">Search for products…</span>
        </div>
      </div>
      <div className="bg-elev m-3 rounded-lg p-4 flex gap-4">
        <div className="w-40 h-40 border border-app rounded flex items-center justify-center flex-shrink-0 overflow-hidden">
          {product.imageUrl
            ? <img src={product.imageUrl} alt="" className="w-full h-full object-contain" onError={e => { (e.target as HTMLImageElement).style.display='none' }} />
            : <span className="text-faint text-[10px]">Image</span>
          }
        </div>
        <div className="flex-1">
          <div className="text-[14px] font-medium text-app">{title}</div>
          <div className="flex items-center gap-2 mt-1">
            <span className="bg-[#388E3C] text-white text-[10px] px-1.5 py-0.5 rounded font-bold">4.3 ★</span>
            <span className="text-[11px] text-faint">2,341 Ratings & 412 Reviews</span>
          </div>
          <div className="mt-2">
            <span className="text-[18px] font-bold text-app">{price}</span>
            {product.mrp && <span className="text-[11px] text-faint ml-2 line-through">₹{parseInt(product.mrp).toLocaleString('en-IN')}</span>}
          </div>
          <div className="mt-2 text-[10.5px] text-dim space-y-1">
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
      <div className="bg-elev rounded-xl border-2 border-app overflow-hidden" style={{ width: 220, margin: '0 auto' }}>
        <div className="bg-[#9B2F8A] px-3 py-2">
          <span className="text-white font-bold text-[13px]">meesho</span>
        </div>
        <div className="aspect-square bg-pink-50 flex items-center justify-center overflow-hidden">
          {product.imageUrl
            ? <img src={product.imageUrl} alt="" className="w-full h-full object-cover" onError={e => { (e.target as HTMLImageElement).style.display='none' }} />
            : <span className="text-faint text-[10px]">Image</span>
          }
        </div>
        <div className="p-3 space-y-1">
          <div className="text-[11px] font-medium text-app line-clamp-2">{title}</div>
          <div className="text-[13px] font-bold text-app">{price}</div>
          <div className="text-[9px] text-faint">Free Delivery</div>
          <button className="w-full bg-[#9B2F8A] text-white text-[11px] font-semibold py-1.5 rounded mt-1">Add to Cart</button>
        </div>
      </div>
    )
  }

  return (
    <div className="bg-elev border border-app rounded-lg overflow-hidden text-[12px]">
      <div className="bg-[#9B2F8A] px-4 py-2 flex items-center gap-3">
        <span className="text-white font-bold text-[15px]">meesho</span>
        <div className="flex-1 bg-elev/20 rounded flex items-center px-3 py-1">
          <span className="text-white/60 text-[11px]">Search for products</span>
        </div>
      </div>
      <div className="p-4 flex gap-4">
        <div className="w-44 h-52 bg-pink-50 rounded flex items-center justify-center flex-shrink-0 overflow-hidden">
          {product.imageUrl
            ? <img src={product.imageUrl} alt="" className="w-full h-full object-contain" onError={e => { (e.target as HTMLImageElement).style.display='none' }} />
            : <span className="text-faint text-[10px]">Image</span>
          }
        </div>
        <div className="flex-1">
          <div className="text-[13.5px] font-medium text-app leading-snug">{title}</div>
          <div className="text-[10.5px] text-dim mt-0.5">{product.brand || 'Brand Name'}</div>
          <div className="mt-2 flex items-baseline gap-2">
            <span className="text-[20px] font-bold text-app">{price}</span>
            {product.mrp && <span className="text-[11px] text-faint line-through">₹{parseInt(product.mrp).toLocaleString('en-IN')}</span>}
          </div>
          <div className="mt-1 text-[11px] text-green-600 font-medium">✓ FREE Delivery</div>
          <div className="mt-3 space-y-1">
            {product.features.slice(0,3).map((f,i) => (
              <div key={i} className="text-[10.5px] text-dim flex gap-1"><span>•</span>{f}</div>
            ))}
          </div>
          <button className="mt-3 px-5 py-2 bg-[#9B2F8A] text-white text-[12px] font-semibold rounded">Add to Cart</button>
        </div>
      </div>
    </div>
  )
}

export default function ProductStudio() {
  const { connectedPlatforms } = usePlatform()
  const hasMarketplace = connectedPlatforms.length > 0

  // No hardcoded demo product by default — a brand-new seller sees a
  // real choice (blank listing, or start from a SKU they actually
  // have) instead of someone else's sample "Bamboo Spice Rack" data.
  const [mode, setMode] = useState<'landing' | 'editor'>('landing')
  const [product, setProduct] = useState<ProductForm>({
    title: '',
    category: CATEGORIES[0],
    brand: '',
    price: '',
    mrp: '',
    stock: '',
    description: '',
    keywords: [],
    features: [],
    imageUrl: '',
  })

  // Real inventory, fetched from the same /inventory endpoint Dashboard
  // and Business Intelligence use — lets a seller start a listing from
  // a SKU they already sell instead of typing everything from scratch.
  // Honest limit: /inventory only returns sku/quantity/warehouse, not
  // title/price/description, so only the stock count carries over —
  // the rest still needs filling in, same as a blank listing.
  const [inventoryItems, setInventoryItems] = useState<InventoryItem[]>([])
  const [inventoryLoading, setInventoryLoading] = useState(false)
  const [inventoryError, setInventoryError] = useState<string | null>(null)
  const [showSkuPicker, setShowSkuPicker] = useState(false)

  useEffect(() => {
    if (!showSkuPicker || inventoryItems.length > 0 || inventoryLoading) return
    setInventoryLoading(true)
    setInventoryError(null)
    getInventory()
      .then(res => {
        if (res.success) setInventoryItems(res.items)
        else setInventoryError(res.message ?? 'Could not load inventory.')
      })
      .catch(() => setInventoryError('Could not reach the SellerOS API.'))
      .finally(() => setInventoryLoading(false))
  }, [showSkuPicker, inventoryItems.length, inventoryLoading])

  const startBlank = () => { setMode('editor') }

  const startFromSku = (item: InventoryItem) => {
    setProduct(p => ({ ...p, stock: String(item.available_quantity) }))
    setMode('editor')
  }

  // Phase 7.4: prefills the editor with the seller-owned facts already in
  // the catalog (mock/listingsView.ts, derived from products.ts) — title,
  // category, brand, price, image. It does not touch description/keywords/
  // features, since those are listing *copy*, not catalog data, and
  // writing/improving that copy is exactly what the AI Listing Optimizer
  // below (AgentConsole, backed by the real RAG pipeline via POST /chat)
  // is for. This function only supplies facts; it never calls the AI.
  const startFromListing = (row: ListingViewRow) => {
    setProduct(p => ({
      ...p,
      title: row.name,
      category: row.category,
      brand: row.brand,
      price: String(row.price),
      imageUrl: row.imageUrl,
    }))
    setMode('editor')
  }

  const [marketplace, setMarketplace] = useState<'amazon' | 'flipkart' | 'meesho'>('amazon')
  const [device, setDevice] = useState<'desktop' | 'mobile'>('desktop')
  const [newKeyword, setNewKeyword] = useState('')
  const [newFeature, setNewFeature] = useState('')
  const [saving, setSaving] = useState(false)
  const [saved, setSaved] = useState(false)
  const [publishTrigger, setPublishTrigger] = useState({ prompt: '', nonce: 0 })

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

  // No draft-persistence endpoint exists on the backend yet, so this
  // only keeps the form state that's already in memory — it doesn't
  // sync anywhere. Labeled accordingly in the UI.
  const handleSave = () => {
    setSaving(true)
    setTimeout(() => { setSaving(false); setSaved(true); setTimeout(() => setSaved(false), 2500) }, 500)
  }

  // Real action: routes through the listing_agent via POST /chat
  // (a "create a listing" / "generate a listing" phrase triggers it), which
  // is a guardrail-checked, approval-gated action — the response and
  // any approval prompt surface in the AI Listing Optimizer panel below.
  // Wording matches what will actually happen: without a connected marketplace
  // there's nowhere for the agent to publish to, so it generates the listing
  // content rather than claiming to have published it anywhere.
  const handlePublish = () => {
    const action = hasMarketplace
      ? `Create and publish a listing for`
      : `Generate a listing (no marketplace connected yet, so just generate the content) for`
    const prompt = `${action} "${product.title}" in category ${product.category}, brand ${product.brand || 'N/A'}, priced at ₹${product.price || '0'}. Description: ${product.description || '(none provided)'}. Keywords: ${product.keywords.join(', ') || 'none'}.`
    setPublishTrigger(t => ({ prompt, nonce: t.nonce + 1 }))
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
      {mode === 'landing' ? (
        <div className="space-y-6 max-w-6xl">
          <div>
            <div className="flex items-center gap-2 mb-1">
              <h2 className="text-xl font-bold text-app">Product Studio</h2>
              <span className="badge bg-accent-blue-soft text-accent-blue border -100">
                <Sparkles size={10} /> AI-Powered
              </span>
            </div>
            <p className="text-[13px] text-dim">Create and optimize listings with AI. Start from scratch, or from a SKU you already sell.</p>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <button onClick={startBlank} className="card p-5 flex flex-col gap-3 text-left border-app-hover transition-colors">
              <div className="w-10 h-10 rounded-lg flex items-center justify-center bg-accent-blue-soft text-accent-blue">
                <PackagePlus size={18} />
              </div>
              <div>
                <div className="text-[13.5px] font-semibold text-app mb-1">Create a new listing</div>
                <div className="text-[12px] text-dim leading-relaxed">Start with a blank form and let the AI Listing Optimizer help you write the title, description, and keywords.</div>
              </div>
            </button>

            <button
              onClick={() => setShowSkuPicker(true)}
              disabled={!hasMarketplace}
              title={hasMarketplace ? undefined : 'Connect a marketplace to see your real SKUs here'}
              className="card p-5 flex flex-col gap-3 text-left border-app-hover transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
            >
              <div className="w-10 h-10 rounded-lg flex items-center justify-center bg-accent-purple-soft text-accent-purple">
                <Boxes size={18} />
              </div>
              <div>
                <div className="text-[13.5px] font-semibold text-app mb-1">Start from an existing SKU</div>
                <div className="text-[12px] text-dim leading-relaxed">
                  {hasMarketplace
                    ? "Pick a SKU from your synced inventory to carry its stock count over — title, price, and description still need writing."
                    : 'Connect a marketplace first to start a listing from real inventory.'}
                </div>
              </div>
            </button>
          </div>

          {showSkuPicker && (
            <div className="card p-5">
              <h3 className="text-[13.5px] font-semibold text-app mb-3">Choose a SKU</h3>
              {inventoryLoading && (
                <div className="flex items-center gap-2 text-[13px] text-dim py-4"><Loader2 size={14} className="animate-spin" /> Loading your inventory…</div>
              )}
              {inventoryError && <p className="text-[12.5px] text-accent-red">{inventoryError}</p>}
              {!inventoryLoading && !inventoryError && inventoryItems.length === 0 && (
                <p className="text-[12.5px] text-faint">No synced inventory items found yet.</p>
              )}
              <div className="space-y-2 max-h-64 overflow-y-auto">
                {inventoryItems.map(item => (
                  <button
                    key={`${item.platform}-${item.sku}`}
                    onClick={() => startFromSku(item)}
                    className="w-full flex items-center justify-between gap-3 px-3 py-2.5 rounded-lg bg-surface hover:bg-hover transition-colors text-left"
                  >
                    <span className="text-[12.5px] font-mono-app text-app truncate">{item.sku}</span>
                    <span className="text-[12px] text-dim whitespace-nowrap">{item.available_quantity} in stock · {item.platform}</span>
                  </button>
                ))}
              </div>
            </div>
          )}

          <div className="pt-2 border-t border-app">
            <ListingsCatalogTable onOptimize={startFromListing} />
          </div>
        </div>
      ) : (
    <>
      {/* Header */}
      <div className="flex items-center justify-between mb-6">
        <div>
          <div className="flex items-center gap-2 mb-1">
            <h2 className="text-xl font-bold text-app">Product Studio</h2>
            <span className="badge bg-accent-blue-soft text-accent-blue border -100">
              <Sparkles size={10} /> AI-Powered
            </span>
          </div>
          <p className="text-[13px] text-dim">Create and optimize listings with AI. Preview updates live.</p>
        </div>
        <div className="flex items-center gap-3">
          <button onClick={() => setMode('landing')}
            className="flex items-center gap-2 px-4 py-2 bg-elev border border-app text-dim text-[13px] font-medium rounded-lg hover:bg-surface transition-colors">
            ← Start over
          </button>
          <button onClick={handleSave} disabled={saving} title="Kept in this browser tab only — there's no draft-storage endpoint on the backend yet"
            className="flex items-center gap-2 px-4 py-2 bg-elev border border-app text-dim text-[13px] font-medium rounded-lg hover:bg-surface transition-colors">
            <Save size={14} />
            {saving ? 'Saving…' : saved ? '✓ Saved (local)' : 'Save Draft'}
          </button>
          <button onClick={handlePublish}
            title={hasMarketplace
              ? 'Sends this listing to the real listing agent via /chat — may require your approval'
              : 'Generates the listing with the AI agent — connect a marketplace to actually publish it'}
            className="flex items-center gap-2 px-4 py-2 bg-accent-blue text-white text-[13px] font-medium rounded-lg transition-opacity hover:opacity-90 transition-colors shadow-sm">
            <Upload size={14} />
            {hasMarketplace ? 'Publish to All' : 'Generate Listing'}
          </button>
        </div>
      </div>

      {/* Three column layout */}
      <div className="grid grid-cols-1 xl:grid-cols-[380px_1fr_380px] gap-5">
        {/* LEFT: Product form */}
        <div className="bg-elev rounded-xl border border-app overflow-hidden">
          <div className="px-5 py-4 border-b border-app">
            <h3 className="text-[13.5px] font-semibold text-app">Product Details</h3>
          </div>
          <div className="p-5 space-y-4 overflow-y-auto" style={{ maxHeight: 'calc(100vh - 220px)' }}>
            {/* Title */}
            <div>
              <label className="block text-[12px] font-medium text-dim mb-1.5">
                Product Title <span className="text-faint font-normal">({product.title.length}/200)</span>
              </label>
              <input
                value={product.title}
                onChange={e => setProduct(p => ({ ...p, title: e.target.value }))}
                className="w-full border border-app rounded-lg px-3 py-2.5 text-[13px] text-app bg-surface "
                placeholder="Enter descriptive product title..."
              />
              <div className="mt-1 h-1 bg-surface rounded-full overflow-hidden">
                <div className="h-full bg-accent-blue rounded-full transition-all" style={{ width: `${Math.min(product.title.length / 200 * 100, 100)}%` }} />
              </div>
            </div>

            {/* Category + Brand */}
            <div className="grid grid-cols-2 gap-3">
              <div>
                <label className="block text-[12px] font-medium text-dim mb-1.5">Category</label>
                <div className="relative">
                  <select
                    value={product.category}
                    onChange={e => setProduct(p => ({ ...p, category: e.target.value }))}
                    className="w-full border border-app rounded-lg px-3 py-2.5 text-[13px] text-app bg-surface appearance-none"
                  >
                    {CATEGORIES.map(c => <option key={c}>{c}</option>)}
                  </select>
                  <ChevronDown size={13} className="absolute right-3 top-1/2 -translate-y-1/2 text-faint pointer-events-none" />
                </div>
              </div>
              <div>
                <label className="block text-[12px] font-medium text-dim mb-1.5">Brand</label>
                <input
                  value={product.brand}
                  onChange={e => setProduct(p => ({ ...p, brand: e.target.value }))}
                  className="w-full border border-app rounded-lg px-3 py-2.5 text-[13px] text-app bg-surface"
                  placeholder="Brand name"
                />
              </div>
            </div>

            {/* Pricing */}
            <div className="grid grid-cols-3 gap-3">
              <div>
                <label className="block text-[12px] font-medium text-dim mb-1.5">Selling Price (₹)</label>
                <input
                  type="number" value={product.price}
                  onChange={e => setProduct(p => ({ ...p, price: e.target.value }))}
                  className="w-full border border-app rounded-lg px-3 py-2.5 text-[13px] text-app bg-surface"
                  placeholder="0"
                />
              </div>
              <div>
                <label className="block text-[12px] font-medium text-dim mb-1.5">MRP (₹)</label>
                <input
                  type="number" value={product.mrp}
                  onChange={e => setProduct(p => ({ ...p, mrp: e.target.value }))}
                  className="w-full border border-app rounded-lg px-3 py-2.5 text-[13px] text-app bg-surface"
                  placeholder="0"
                />
              </div>
              <div>
                <label className="block text-[12px] font-medium text-dim mb-1.5">Stock</label>
                <input
                  type="number" value={product.stock}
                  onChange={e => setProduct(p => ({ ...p, stock: e.target.value }))}
                  className="w-full border border-app rounded-lg px-3 py-2.5 text-[13px] text-app bg-surface"
                  placeholder="0"
                />
              </div>
            </div>

            {/* Description */}
            <div>
              <label className="block text-[12px] font-medium text-dim mb-1.5">
                Description <span className="text-faint font-normal">({product.description.length}/2000)</span>
              </label>
              <textarea
                value={product.description}
                onChange={e => setProduct(p => ({ ...p, description: e.target.value }))}
                rows={4}
                className="w-full border border-app rounded-lg px-3 py-2.5 text-[13px] text-app bg-surface resize-none"
                placeholder="Describe your product in detail..."
              />
            </div>

            {/* Keywords */}
            <div>
              <label className="block text-[12px] font-medium text-dim mb-1.5">Search Keywords</label>
              <div className="flex flex-wrap gap-1.5 mb-2">
                {product.keywords.map((k, i) => (
                  <span key={i} className="flex items-center gap-1 text-[11.5px] bg-accent-blue-soft text-accent-blue px-2 py-1 rounded-md">
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
                  className="flex-1 border border-app rounded-lg px-3 py-2 text-[13px] bg-surface"
                  placeholder="Add keyword and press Enter..."
                />
                <button onClick={addKeyword} className="px-3 py-2 bg-surface rounded-lg hover:bg-surface transition-colors">
                  <Plus size={14} className="text-dim" />
                </button>
              </div>
            </div>

            {/* Features */}
            <div>
              <label className="block text-[12px] font-medium text-dim mb-1.5">Key Features / Bullet Points</label>
              <div className="space-y-1.5 mb-2">
                {product.features.map((f, i) => (
                  <div key={i} className="flex items-center gap-2 p-2 bg-surface rounded-lg border border-app">
                    <span className="text-accent-blue text-[11px] font-bold">•</span>
                    <span className="flex-1 text-[12.5px] text-dim">{f}</span>
                    <button onClick={() => setProduct(p => ({ ...p, features: p.features.filter((_, j) => j !== i) }))}>
                      <X size={12} className="text-faint hover:text-dim" />
                    </button>
                  </div>
                ))}
              </div>
              <div className="flex gap-2">
                <input
                  value={newFeature}
                  onChange={e => setNewFeature(e.target.value)}
                  onKeyDown={e => e.key === 'Enter' && addFeature()}
                  className="flex-1 border border-app rounded-lg px-3 py-2 text-[13px] bg-surface"
                  placeholder="Add a key feature..."
                />
                <button onClick={addFeature} className="px-3 py-2 bg-surface rounded-lg hover:bg-surface transition-colors">
                  <Plus size={14} className="text-dim" />
                </button>
              </div>
            </div>

            {/* Image URL */}
            <div>
              <label className="block text-[12px] font-medium text-dim mb-1.5">Main Image URL</label>
              <input
                value={product.imageUrl}
                onChange={e => setProduct(p => ({ ...p, imageUrl: e.target.value }))}
                className="w-full border border-app rounded-lg px-3 py-2.5 text-[13px] bg-surface"
                placeholder="https://..."
              />
            </div>
          </div>
        </div>

        {/* MIDDLE: AI Optimizer */}
        <div className="space-y-4">
          {/* Client-side heuristic score, computed from what's typed in the
              form to the left — not a marketplace or AI score. The real
              AI feedback is in the panel below, backed by /chat. */}
          <div className="bg-elev rounded-xl border border-app p-5">
            <div className="flex items-center justify-between mb-4">
              <h3 className="text-[13.5px] font-semibold text-app flex items-center gap-2">
                Listing Readiness Score
              </h3>
              <span className="text-[11px] text-faint">Heuristic, updates live</span>
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
                      <span className="text-dim">{label}</span>
                      <span className={`font-medium ${score >= 80 ? 'text-accent-green' : score >= 60 ? 'text-accent-amber' : 'text-accent-red'}`}>{score}</span>
                    </div>
                    <div className="h-1.5 bg-surface rounded-full overflow-hidden">
                      <div
                        className={`h-full rounded-full transition-all duration-500 ${score >= 80 ? 'bg-accent-green' : score >= 60 ? 'bg-accent-amber' : 'bg-accent-red'}`}
                        style={{ width: `${score}%` }}
                      />
                    </div>
                  </div>
                ))}
              </div>
            </div>
          </div>

          {/* Real AI optimization — backed by the seo_agent / listing_agent
              via POST /chat, not a static list of canned tips. */}
          <AgentConsole
            title="AI Listing Optimizer"
            description="Real suggestions from the SEO and listing agents"
            icon={Sparkles}
            iconColor="bg-accent-blue-soft text-accent-blue"
            sessionKey="product-studio-optimizer"
            placeholder="Ask for SEO or listing feedback…"
            emptyHint="Try optimizing your current title, or ask for missing keywords."
            quickPrompts={[
              { label: 'Optimize this listing', prompt: `Optimize listing SEO for "${product.title}" in category ${product.category}. Current keywords: ${product.keywords.join(', ') || 'none'}.` },
              { label: 'Suggest keywords', prompt: `Suggest search keywords to improve visibility for a product titled "${product.title}".` },
              { label: 'Review description', prompt: `Review this product description and suggest improvements: ${product.description || '(no description yet)'}` },
            ]}
            externalTrigger={publishTrigger}
          />
        </div>

        {/* RIGHT: Marketplace Preview */}

        <div className="bg-elev rounded-xl border border-app overflow-hidden">
          <div className="px-5 py-4 border-b border-app">
            <h3 className="text-[13.5px] font-semibold text-app mb-3">Live Preview</h3>
            {/* Marketplace tabs */}
            <div className="flex gap-1 mb-3">
              {(['amazon', 'flipkart', 'meesho'] as const).map(m => (
                <button key={m} onClick={() => setMarketplace(m)}
                  className={`flex-1 py-1.5 text-[11.5px] font-medium rounded-lg capitalize transition-colors ${
                    marketplace === m ? 'bg-accent-blue text-white' : 'bg-surface text-dim bg-hover'
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
                    device === d ? 'bg-app text-white' : 'bg-surface text-dim hover:bg-surface'
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
    </>
      )}
    </div>
  )
}
