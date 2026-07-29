import { Leaf, Package, Recycle, Award } from 'lucide-react'
import AgentConsole from '../components/AgentConsole'

// There's no backend data model for certifications, CO2 tracking, or
// a "green score" yet — only backend.ai.agent_layer.sustainability.
// sustainability_agent, reachable through POST /chat. Rather than
// keep the old page's fabricated scorecard (78/100 green score, 12.5
// tons CO2 saved, FSC/GOTS certifications — none of it backed by any
// endpoint), this page leads with the real agent and is upfront about
// what's not tracked yet.
export default function Sustainability() {
  return (
    <div className="p-6 fade-in space-y-6">
      <div>
        <h2 className="text-xl font-bold text-app flex items-center gap-2">
          <Leaf size={22} className="text-accent-green" />
          Sustainability
        </h2>
        <p className="text-[13px] text-dim mt-0.5">Ask your AI sustainability advisor about packaging, sourcing, and certifications.</p>
      </div>

      <AgentConsole
        title="Sustainability Advisor"
        description="Packaging, carbon footprint, sourcing, and certifications"
        icon={Leaf}
        iconColor="bg-accent-green-soft text-accent-green"
        sessionKey="sustainability"
        placeholder="Ask about sustainability for your business…"
        emptyHint="Try asking about eco-friendly packaging options, carbon footprint reduction, or which certifications fit your products."
        quickPrompts={[
          { label: 'Reduce packaging waste', prompt: 'How can I reduce packaging waste for my shipments?' },
          { label: 'Carbon footprint tips', prompt: 'How can I reduce my carbon footprint as a seller?' },
          { label: 'Eco-friendly sourcing', prompt: 'How can I source more sustainable materials?' },
          { label: 'Which certifications fit me?', prompt: 'What sustainability certifications should I pursue?' },
        ]}
      />

      <div>
        <div className="text-[13px] font-semibold text-app mb-3">Areas the advisor can help with</div>
        <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
          {[
            { label: 'Packaging', icon: Package, color: 'bg-accent-blue-soft text-accent-blue', hint: 'Biodegradable mailers, void fill, plastic reduction' },
            { label: 'Sourcing & Waste', icon: Recycle, color: 'bg-accent-purple-soft text-accent-purple', hint: 'Material choices, supplier ESG, waste reduction' },
            { label: 'Certifications', icon: Award, color: 'bg-accent-amber-soft text-accent-amber', hint: 'FSC, GOTS, carbon-neutral shipping programs' },
          ].map(t => (
            <div key={t.label} className="card p-4 flex items-start gap-3">
              <div className={`w-9 h-9 rounded-lg flex items-center justify-center flex-shrink-0 ${t.color}`}>
                <t.icon size={16} />
              </div>
              <div>
                <div className="text-[13px] font-semibold text-app">{t.label}</div>
                <div className="text-[11.5px] text-faint mt-0.5">{t.hint}</div>
              </div>
            </div>
          ))}
        </div>
        <p className="text-[11.5px] text-faint mt-3">
          Tracked metrics like CO₂ saved and certification status aren't wired to a backend data source yet — this page
          gives real advice from the sustainability agent rather than a fabricated scorecard.
        </p>
      </div>
    </div>
  )
}
