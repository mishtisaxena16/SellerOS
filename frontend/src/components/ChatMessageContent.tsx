import type { ReactNode } from 'react'

// Dependency-free, deliberately small formatter for AI chat responses.
// The agents (seller coach, sustainability, SEO, etc.) commonly reply with
// **bold** labels and "- " / "1. " lists — this renders exactly that plus
// `inline code` and paragraph breaks. It is NOT a general markdown parser
// (no tables, links, headings, nested lists) — just enough to make real
// agent responses readable instead of a single run-on line of text.
// Shared by FloatingAI and AgentConsole so every chat surface formats
// assistant replies the same way.

function renderInline(text: string, keyPrefix: string): ReactNode[] {
  const parts: ReactNode[] = []
  const pattern = /(\*\*(.+?)\*\*|`([^`]+?)`)/g
  let lastIndex = 0
  let match: RegExpExecArray | null
  let i = 0
  while ((match = pattern.exec(text)) !== null) {
    if (match.index > lastIndex) parts.push(text.slice(lastIndex, match.index))
    if (match[2] !== undefined) {
      parts.push(<strong key={`${keyPrefix}-b-${i++}`} className="font-semibold text-app">{match[2]}</strong>)
    } else if (match[3] !== undefined) {
      parts.push(
        <code key={`${keyPrefix}-c-${i++}`} className="font-mono-app text-[11.5px] px-1 py-0.5 rounded bg-surface">
          {match[3]}
        </code>
      )
    }
    lastIndex = pattern.lastIndex
  }
  if (lastIndex < text.length) parts.push(text.slice(lastIndex))
  return parts.length > 0 ? parts : [text]
}

export default function ChatMessageContent({ text }: { text: string }) {
  if (!text) return null

  const lines = text.replace(/\r\n/g, '\n').split('\n')
  const blocks: ReactNode[] = []
  let list: { ordered: boolean; items: string[] } | null = null
  let key = 0

  const flushList = () => {
    if (!list) return
    const items = list.items
    const ordered = list.ordered
    blocks.push(
      ordered ? (
        <ol key={`list-${key++}`} className="pl-4 space-y-1 list-decimal">
          {items.map((item, i) => <li key={i}>{renderInline(item, `oli-${key}-${i}`)}</li>)}
        </ol>
      ) : (
        <ul key={`list-${key++}`} className="pl-4 space-y-1 list-disc">
          {items.map((item, i) => <li key={i}>{renderInline(item, `uli-${key}-${i}`)}</li>)}
        </ul>
      )
    )
    list = null
  }

  for (const rawLine of lines) {
    const line = rawLine.trim()
    if (!line) { flushList(); continue }

    const bullet = /^[-*]\s+(.*)$/.exec(line)
    const numbered = /^\d+[.)]\s+(.*)$/.exec(line)

    if (bullet) {
      if (!list || list.ordered) { flushList(); list = { ordered: false, items: [] } }
      list.items.push(bullet[1])
      continue
    }
    if (numbered) {
      if (!list || !list.ordered) { flushList(); list = { ordered: true, items: [] } }
      list.items.push(numbered[1])
      continue
    }
    flushList()
    blocks.push(<p key={`p-${key++}`}>{renderInline(line, `p-${key}`)}</p>)
  }
  flushList()

  return <div className="space-y-1.5">{blocks}</div>
}
