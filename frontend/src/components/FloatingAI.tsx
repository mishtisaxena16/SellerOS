import { useState } from 'react'
import { Sparkles, X, Send, Minimize2 } from 'lucide-react'

interface Message {
  role: 'user' | 'ai'
  text: string
}

const QUICK_PROMPTS = [
  'Why did my sales drop last week?',
  'Optimize my top listing',
  'Restock recommendations',
  'Trending keywords this week',
]

const AI_RESPONSES: Record<string, string> = {
  'Why did my sales drop last week?': "Your sales dipped 18% last Tuesday–Thursday. Analysis shows Amazon changed your category ranking due to 3 new competitors. I recommend updating your main image and adding 2 missing backend keywords: \"kitchen organizer set\" and \"bamboo storage box\".",
  'Optimize my top listing': "Your top listing (Bamboo Spice Rack) has an SEO score of 74. Quick wins: add \"spice organizer\" to bullet 1, increase main image brightness by ~15%, and add a lifestyle photo. Estimated impact: +12% CTR.",
  'Restock recommendations': "3 SKUs need attention: Bamboo Spice Rack (12 units left, ~8 days), Wooden Serving Board (6 units, ~5 days), and Kitchen Tool Set (18 units, ~11 days). Suggested reorder: 200, 150, 250 units.",
  'Trending keywords this week': "Top trending in your categories: \"eco-friendly kitchen\" (+340%), \"bamboo organizer\" (+180%), \"wooden kitchen accessories\" (+95%). Consider updating your listings to include these.",
}

export default function FloatingAI() {
  const [open, setOpen] = useState(false)
  const [minimized, setMinimized] = useState(false)
  const [input, setInput] = useState('')
  const [messages, setMessages] = useState<Message[]>([
    { role: 'ai', text: "Hi Rahul! I'm your AI assistant. Ask me anything about your store performance, listings, or inventory." }
  ])

  const send = (text: string) => {
    const msg = text.trim()
    if (!msg) return
    setMessages(prev => [...prev, { role: 'user', text: msg }])
    setInput('')
    setTimeout(() => {
      const reply = AI_RESPONSES[msg] || "I'm analyzing your store data... Based on current trends, I'd recommend focusing on your top-performing categories and ensuring keyword density is optimized for seasonal searches."
      setMessages(prev => [...prev, { role: 'ai', text: reply }])
    }, 800)
  }

  return (
    <div className="fixed bottom-6 right-6 z-50 flex flex-col items-end gap-3">
      {/* Chat window */}
      {open && !minimized && (
        <div className="fade-in w-80 bg-white rounded-2xl shadow-2xl border border-gray-100 overflow-hidden">
          {/* Header */}
          <div className="flex items-center gap-3 px-4 py-3 bg-gradient-to-r from-primary to-purple-500">
            <div className="w-7 h-7 rounded-full bg-white/20 flex items-center justify-center">
              <Sparkles size={14} className="text-white" />
            </div>
            <div className="flex-1">
              <div className="text-[13px] font-semibold text-white">SellerOS AI</div>
              <div className="flex items-center gap-1.5">
                <span className="w-1.5 h-1.5 rounded-full bg-green-300 ai-pulse" />
                <span className="text-[11px] text-white/70">Online · GPT-4 powered</span>
              </div>
            </div>
            <button onClick={() => setMinimized(true)} className="text-white/60 hover:text-white transition-colors">
              <Minimize2 size={14} />
            </button>
            <button onClick={() => setOpen(false)} className="text-white/60 hover:text-white transition-colors">
              <X size={14} />
            </button>
          </div>

          {/* Messages */}
          <div className="h-64 overflow-y-auto p-4 space-y-3 bg-gray-50/50">
            {messages.map((m, i) => (
              <div key={i} className={`flex ${m.role === 'user' ? 'justify-end' : 'justify-start'}`}>
                {m.role === 'ai' && (
                  <div className="w-6 h-6 rounded-full bg-gradient-to-br from-primary to-purple-500 flex items-center justify-center mr-2 flex-shrink-0 mt-0.5">
                    <Sparkles size={10} className="text-white" />
                  </div>
                )}
                <div className={`max-w-[85%] px-3 py-2 rounded-xl text-[12.5px] leading-relaxed ${
                  m.role === 'user'
                    ? 'bg-primary text-white'
                    : 'bg-white text-gray-700 shadow-sm border border-gray-100'
                }`}>
                  {m.text}
                </div>
              </div>
            ))}
          </div>

          {/* Quick prompts */}
          <div className="px-3 py-2 flex gap-1.5 flex-wrap border-t border-gray-100">
            {QUICK_PROMPTS.slice(0, 2).map(q => (
              <button key={q} onClick={() => send(q)} className="text-[11px] px-2 py-1 bg-gray-100 hover:bg-primary-50 hover:text-primary text-gray-600 rounded-md transition-colors truncate max-w-[140px]">
                {q}
              </button>
            ))}
          </div>

          {/* Input */}
          <div className="flex items-center gap-2 px-3 py-3 border-t border-gray-100">
            <input
              value={input}
              onChange={e => setInput(e.target.value)}
              onKeyDown={e => e.key === 'Enter' && send(input)}
              placeholder="Ask anything…"
              className="flex-1 text-[13px] bg-gray-50 border border-gray-200 rounded-lg px-3 py-2 placeholder-gray-400"
            />
            <button
              onClick={() => send(input)}
              className="w-8 h-8 bg-primary rounded-lg flex items-center justify-center text-white hover:bg-primary-hover transition-colors flex-shrink-0"
            >
              <Send size={13} />
            </button>
          </div>
        </div>
      )}

      {/* FAB */}
      <button
        onClick={() => { setOpen(true); setMinimized(false) }}
        className={`w-14 h-14 rounded-2xl shadow-xl flex items-center justify-center transition-all duration-200 ${
          open ? 'bg-gray-800 rotate-0' : 'bg-gradient-to-br from-primary to-purple-500'
        } hover:scale-105 active:scale-95`}
      >
        {open && !minimized
          ? <X size={20} className="text-white" onClick={() => setOpen(false)} />
          : <Sparkles size={22} className="text-white" />
        }
      </button>
    </div>
  )
}
