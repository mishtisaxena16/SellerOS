import React, { useCallback, useEffect, useRef, useState } from 'react';
import { Bot, Loader2, Maximize2, Minus, Send, Sparkles, X } from 'lucide-react';
import ChatMessageContent from './ChatMessageContent';
import { sendChatMessage, type ChatMessage } from '../api/chat';
import { friendlyChatError } from '../utils/chatErrors';
import { generateAiSessionId, subscribeToAiSessionReset } from '../demo/aiSessionReset';

// =========================================================
// Phase 7.9D — Restore Floating AI Assistant
//
// During Phase 6's multi-agent work this widget was turned into an
// Agent Console: it rendered ExecutionResultsPanel (Execution Timeline
// -> Agent Cards -> Seller Coach Summary) above the chat thread. That
// execution-monitoring UI belongs to AgentConsole.tsx, not the
// floating assistant, so it has been removed here — from this file
// only. AgentConsole.tsx, ExecutionResultsPanel.tsx, and the
// backend/RAG pipeline are untouched: the assistant still calls the
// same `sendChatMessage` endpoint and keeps its existing session
// handling; it simply no longer renders the execution results that
// response can include. A small "suggested prompts" row was added
// above the input to help people get started.
// =========================================================

interface FloatingAIProps {
  /** Controlled open state. If omitted, the widget manages its own
   * open/closed state internally (so it still works when mounted with
   * no props, as it currently is from AppShell.tsx, which this phase
   * does not touch). */
  isOpen?: boolean;
  onClose?: () => void;
}

const SUGGESTED_PROMPTS = [
  'Improve my Meesho listing',
  'Explain Amazon SEO',
  'Inventory planning tips',
  'Reduce product returns',
  'Improve product title',
];

// =========================================================
// FloatingAI
// =========================================================

const FloatingAI: React.FC<FloatingAIProps> = ({ isOpen, onClose }) => {
  // --- Open / minimize state --------------------------------------
  // isOpen stays fully controlled when a parent passes it (unchanged
  // contract). When omitted, the widget falls back to internal state
  // so it's still usable mounted with no props at all.
  const isControlled = isOpen !== undefined;
  const [internalOpen, setInternalOpen] = useState(true);
  const open = isControlled ? isOpen : internalOpen;

  // Minimize/maximize is independent of open/close: minimized keeps
  // the widget mounted (session + in-progress execution state intact)
  // and just collapses the body down to the header.
  const [minimized, setMinimized] = useState(false);

  const handleClose = useCallback(() => {
    onClose?.();
    if (!isControlled) setInternalOpen(false);
  }, [onClose, isControlled]);

  // --- Chat thread -----------------------------------------------------
  const sessionIdRef = useRef<string>(generateAiSessionId());
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [input, setInput] = useState('');
  const [sending, setSending] = useState(false);
  const [sendError, setSendError] = useState<string | null>(null);

  // --- Phase 7.7C: AI Session & UI State Reset ----------------------
  // "Reset Demo" (Phase 7.7B's DemoResetControl) broadcasts an AI session
  // reset alongside resetEntireDemo(). On that signal this widget returns
  // to exactly the state it's in on first mount: no conversation history,
  // no pending input, not sending, maximized, and — when not externally
  // controlled — open, so the assistant reads as freshly opened.
  useEffect(() => {
    return subscribeToAiSessionReset((newSessionId) => {
      sessionIdRef.current = newSessionId;
      setMessages([]);
      setInput('');
      setSending(false);
      setSendError(null);
      setMinimized(false);
      if (!isControlled) setInternalOpen(true);
    });
    // Subscribed once for the lifetime of this widget instance.
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  const sendContent = useCallback(
    async (content: string) => {
      const trimmed = content.trim();
      if (!trimmed || sending) return;

      const userMessage: ChatMessage = {
        id: `local-${Date.now()}`,
        role: 'user',
        content: trimmed,
        createdAt: new Date().toISOString(),
      };
      setMessages((prev) => [...prev, userMessage]);
      setInput('');
      setSending(true);
      setSendError(null);

      try {
        const response = await sendChatMessage({
          sessionId: sessionIdRef.current,
          content: trimmed,
        });
        setMessages((prev) => [
          ...prev,
          {
            id: `assistant-${Date.now()}`,
            role: "assistant",
            content: response.response,
            createdAt: new Date().toISOString(),
          },
        ]);
      } catch (err) {
        setSendError(friendlyChatError(err));
      } finally {
        setSending(false);
      }
    },
    [sending]
  );

  const handleSend = useCallback(
    (e: React.FormEvent) => {
      e.preventDefault();
      void sendContent(input);
    },
    [input, sendContent]
  );

  const handleSuggestedPrompt = useCallback(
    (prompt: string) => {
      void sendContent(prompt);
    },
    [sendContent]
  );

  if (!open) {
    // Controlled from outside and explicitly closed: preserve the
    // original contract of rendering nothing.
    if (isControlled) return null;
    // Uncontrolled: keep a small launcher reachable instead of
    // vanishing the widget entirely.
    return (
      <button
        type="button"
        onClick={() => setInternalOpen(true)}
        aria-label="Open SellerOS Assistant"
        className="fixed bottom-5 right-5 z-50 w-12 h-12 rounded-full bg-accent-blue text-white shadow-app flex items-center justify-center hover:opacity-90 transition-opacity"
      >
        <Bot size={20} />
      </button>
    );
  }

  return (
    <div
      className={`floating-ai fixed bottom-5 right-5 z-50 w-[380px] max-w-[calc(100vw-2.5rem)] flex flex-col rounded-2xl border border-app bg-elev shadow-app overflow-hidden fade-in ${
        minimized ? '' : 'max-h-[min(680px,calc(100vh-2.5rem))]'
      }`}
      role="dialog"
      aria-label="SellerOS Assistant"
    >
      <div className="floating-ai__header flex items-center gap-2 px-3.5 py-2.5 border-b border-app bg-surface flex-shrink-0">
        <div className="w-6 h-6 rounded-md bg-accent-blue-soft text-accent-blue flex items-center justify-center flex-shrink-0">
          <Bot size={13} />
        </div>
        <span className="floating-ai__title text-[13px] font-semibold text-app flex-1 truncate">
          SellerOS Assistant
        </span>
        <button
          type="button"
          className="floating-ai__minimize text-faint hover:text-app transition-colors p-1 rounded hover:bg-hover"
          onClick={() => setMinimized((m) => !m)}
          aria-label={minimized ? 'Maximize assistant' : 'Minimize assistant'}
        >
          {minimized ? <Maximize2 size={14} /> : <Minus size={14} />}
        </button>
        <button
          type="button"
          className="floating-ai__close text-faint hover:text-app transition-colors p-1 rounded hover:bg-hover"
          onClick={handleClose}
          aria-label="Close assistant"
        >
          <X size={14} />
        </button>
      </div>

      {!minimized && (
        <>
          <div className="floating-ai__body flex-1 min-h-0 overflow-y-auto px-3.5 py-3 space-y-3">
            {/* Chat thread for this session. */}
            <div className="floating-ai__chat-messages space-y-2.5" data-testid="floating-ai-chat-messages">
              {messages.length === 0 ? (
                <div className="flex items-start gap-2 text-[12px] text-faint px-0.5">
                  <Sparkles size={13} className="text-accent-blue flex-shrink-0 mt-0.5" />
                  <span>Ask a question to get started — I&apos;m here to help with your SellerOS store.</span>
                </div>
              ) : (
                messages
                  .filter((message): message is ChatMessage => message != null)
                  .map((message) => (
                  <div
                    key={message.id}
                    className={`text-[12.5px] leading-relaxed rounded-lg px-3 py-2 ${
                      message.role === 'user'
                        ? 'bg-accent-blue-soft text-app ml-6'
                        : 'bg-surface text-app mr-1'
                    }`}
                  >
                    <ChatMessageContent text={message.content} />
                  </div>
                ))
              )}
              {sending && (
                <div className="flex items-center gap-1.5 text-[11.5px] text-faint px-0.5">
                  <Loader2 size={12} className="animate-spin" />
                  Thinking…
                </div>
              )}
              {sendError && (
                <div className="text-[11.5px] text-accent-red px-0.5">{sendError}</div>
              )}
            </div>
          </div>

          {messages.length === 0 && (
            <div
              className="floating-ai__suggested-prompts flex flex-wrap gap-1.5 px-3 pt-2.5 border-t border-app bg-surface flex-shrink-0"
              data-testid="floating-ai-suggested-prompts"
            >
              {SUGGESTED_PROMPTS.map((prompt) => (
                <button
                  key={prompt}
                  type="button"
                  onClick={() => handleSuggestedPrompt(prompt)}
                  disabled={sending}
                  className="text-[11.5px] text-app bg-elev border border-app rounded-full px-2.5 py-1 hover:border-app-hover hover:bg-hover transition-colors disabled:opacity-50"
                >
                  {prompt}
                </button>
              ))}
            </div>
          )}

          <form
            className={`floating-ai__chat-input flex items-center gap-2 px-3 py-2.5 flex-shrink-0 bg-surface ${
              messages.length === 0 ? 'pt-2' : 'border-t border-app'
            }`}
            onSubmit={handleSend}
          >
            <input
              type="text"
              value={input}
              onChange={(e) => setInput(e.target.value)}
              placeholder="Ask your SellerOS assistant…"
              disabled={sending}
              className="flex-1 min-w-0 text-[12.5px] bg-elev border border-app rounded-lg px-3 py-2 text-app placeholder:text-faint outline-none focus:border-app-hover disabled:opacity-60"
            />
            <button
              type="submit"
              disabled={sending || !input.trim()}
              aria-label="Send message"
              className="w-8 h-8 flex-shrink-0 rounded-lg bg-accent-blue text-white flex items-center justify-center disabled:opacity-40 hover:opacity-90 transition-opacity"
            >
              <Send size={14} />
            </button>
          </form>
        </>
      )}
    </div>
  );
};

export default FloatingAI;
