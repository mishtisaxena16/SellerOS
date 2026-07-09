import re
from flask import Flask
from flask import request
from flask import render_template_string
from flask import session
from flask import redirect
from flask import url_for

from retrieve import (
    semantic_search,
    generate_answer
)

app = Flask(__name__)

# Needed for session (conversation history) to work.
# Change this to a real secret before deploying anywhere.
app.secret_key = "dev-secret-key-change-in-production"

# =========================
# UI: HTML + CSS as a Python string
# =========================
# Still real Jinja2 (the {{ }} and {% %} below work exactly like a
# templates/index.html file would) — it's just stored as a string in
# this file instead of a separate .html file. render_template_string()
# runs it the same way render_template() runs a file.

INDEX_HTML = """<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>SellerOS — AI Copilot for Indian Marketplace Sellers</title>
<script>
  // Runs before CSS paints, so there's no light-flash before dark mode applies.
  (function () {
    try {
      var theme = localStorage.getItem('sellerOS-theme') || 'light';
      document.documentElement.setAttribute('data-theme', theme);
    } catch (e) {}
  })();
</script>
<link rel="preconnect" href="https://fonts.googleapis.com">
<link href="https://fonts.googleapis.com/css2?family=Space+Grotesk:wght@500;600;700&family=Inter:wght@400;500;600;700&family=IBM+Plex+Mono:wght@500&display=swap" rel="stylesheet">
<style>
:root {
  --ink: #12141C;
  --ink-soft: #4B5670;
  --paper: #F8F8F6;
  --paper-raised: #FFFFFF;
  --line: #E5E7EB;
  --amber: #E8A33D;
  --amber-dark: #C7811F;
  --teal: #2F6D5D;
  --rust: #B44B28;
  --accent: #1E293B;
  --accent-soft: #334155;
  --font-display: 'Space Grotesk', sans-serif;
  --font-body: 'Inter', sans-serif;
  --font-mono: 'IBM Plex Mono', monospace;
}

/* Dark mode only re-themes the workspace (paper/ink/lines). The sidebar
   is already dark in light mode, so it keeps its own fixed colors below
   and doesn't need to change. */
[data-theme="dark"] {
  --ink: #E4E6EB;
  --ink-soft: #9AA1B4;
  --paper: #1B1E27;
  --paper-raised: #242836;
  --line: #323747;
}

* { box-sizing: border-box; }

html, body {
  height: 100%;
  margin: 0;
  background: var(--paper);
  color: var(--ink);
  font-family: var(--font-body);
  transition: background 0.2s ease, color 0.2s ease;
  -webkit-font-smoothing: antialiased;
}

.app {
  display: grid;
  grid-template-columns: 252px 1fr;
  height: 100vh;
}

/* ---------- Sidebar ---------- */

.rail {
  background: #12141C;
  color: #F8F8F6;
  padding: 28px 22px;
  display: flex;
  flex-direction: column;
  border-right: 1px solid rgba(255,255,255,0.06);
}

.rail-brand {
  display: flex;
  align-items: center;
  gap: 10px;
  margin-bottom: 4px;
}

.rail-brand-mark {
  font-family: var(--font-mono);
  font-size: 11px;
  letter-spacing: 0.08em;
  background: var(--amber);
  color: #12141C;
  padding: 3px 7px;
  border-radius: 4px;
}

.rail-brand-name {
  font-family: var(--font-display);
  font-weight: 700;
  font-size: 19px;
  letter-spacing: -0.01em;
}

.rail-tagline {
  font-size: 12.5px;
  color: #8892A8;
  margin: 6px 0 36px;
  line-height: 1.5;
}

.rail-label {
  font-family: var(--font-mono);
  font-size: 10.5px;
  letter-spacing: 0.12em;
  text-transform: uppercase;
  color: #6A7590;
  margin-bottom: 14px;
}

.rail-modules {
  list-style: none;
  margin: 0 0 auto 0;
  padding: 0;
}

.rail-modules li { margin: 0; padding: 0; }
.rail-modules form { margin: 0; }

.module-btn {
  display: flex;
  align-items: center;
  gap: 10px;
  width: calc(100% + 20px);
  margin: 0 -10px 2px;
  padding: 10px 10px;
  border: none;
  border-radius: 8px;
  background: none;
  font-family: var(--font-body);
  font-size: 14px;
  color: #D3D7E0;
  cursor: pointer;
  text-align: left;
  transition: background 0.15s ease, color 0.15s ease;
}

.module-btn:hover {
  background: rgba(255,255,255,0.06);
  color: #FFFFFF;
}

.module-btn.active {
  background: rgba(232,163,61,0.16);
  color: #FFFFFF;
}

.dot {
  width: 8px;
  height: 8px;
  border-radius: 50%;
  flex-shrink: 0;
}

.dot-all { background: #8892A8; }
.dot-amazon { background: #E8A33D; }
.dot-meesho { background: #C7509C; }
.dot-flipkart { background: #4C7EF3; }
.dot-government { background: #8B96AD; }
.dot-sustainability { background: #3E9C82; }

/* ---------- Theme toggle ---------- */

.theme-toggle-row {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding-top: 18px;
  margin-top: 18px;
  border-top: 1px solid rgba(255,255,255,0.08);
}

.theme-toggle-label {
  font-family: var(--font-mono);
  font-size: 10.5px;
  letter-spacing: 0.1em;
  text-transform: uppercase;
  color: #8892A8;
}

.theme-switch {
  position: relative;
  display: inline-block;
  width: 38px;
  height: 20px;
  flex-shrink: 0;
}

.theme-switch input {
  opacity: 0;
  width: 0;
  height: 0;
}

.theme-switch .slider {
  position: absolute;
  inset: 0;
  background: #3A4257;
  border-radius: 999px;
  cursor: pointer;
  transition: background 0.2s ease;
}

.theme-switch .slider::before {
  content: "";
  position: absolute;
  height: 16px;
  width: 16px;
  left: 2px;
  top: 2px;
  background: #FFFFFF;
  border-radius: 50%;
  transition: transform 0.2s ease;
}

.theme-switch input:checked + .slider { background: var(--amber-dark); }
.theme-switch input:checked + .slider::before { transform: translateX(18px); }

.rail-footer {
  font-family: var(--font-mono);
  font-size: 10px;
  color: #565F78;
  letter-spacing: 0.03em;
  padding-top: 22px;
  border-top: 1px solid rgba(255,255,255,0.08);
  margin-top: 22px;
}

/* ---------- Main workspace ---------- */

.main {
  display: flex;
  flex-direction: column;
  height: 100vh;
  padding: 48px 64px 32px;
  min-width: 0;
  background: var(--paper);
}

.topbar {
  margin-bottom: 28px;
}

.topbar h1 {
  font-family: var(--font-display);
  font-weight: 600;
  font-size: 26px;
  letter-spacing: -0.01em;
  margin: 0 0 8px;
}

.topbar p {
  color: var(--ink-soft);
  margin: 0 0 14px;
  font-size: 14.5px;
}

.filter-pill {
  display: inline-flex;
  align-items: center;
  gap: 8px;
  font-family: var(--font-mono);
  font-size: 11.5px;
  letter-spacing: 0.02em;
  background: rgba(232,163,61,0.14);
  color: var(--amber-dark);
  border: 1px solid rgba(232,163,61,0.4);
  padding: 6px 8px 6px 12px;
  border-radius: 999px;
}

.filter-pill button {
  border: none;
  background: none;
  cursor: pointer;
  color: inherit;
  font-family: inherit;
  font-size: 14px;
  line-height: 1;
  padding: 2px 4px;
}

.thread {
  flex: 1;
  overflow-y: auto;
  display: flex;
  flex-direction: column;
  gap: 22px;
  padding-right: 8px;
}

/* ---------- Empty state ---------- */

.empty-state {
  margin: auto;
  text-align: center;
  color: var(--ink-soft);
  max-width: 560px;
}

.empty-state-wordmark {
  font-family: var(--font-display);
  font-weight: 600;
  font-size: 42px;
  letter-spacing: -0.02em;
  color: var(--ink);
  opacity: 0.85;
  margin: 0 0 14px;
}

.empty-state-wordmark .accent {
  color: var(--amber-dark);
}

.empty-state p.lead {
  font-family: var(--font-display);
  font-size: 17px;
  font-weight: 600;
  color: var(--ink);
  margin: 0 0 8px;
}

.empty-sub {
  font-size: 13.5px;
  margin: 0 0 26px;
}

.suggestions {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 10px;
  text-align: left;
}

.suggestion-chip {
  font-family: var(--font-body);
  font-size: 13px;
  font-weight: 500;
  color: var(--ink);
  background: var(--paper-raised);
  border: 1px solid var(--line);
  border-radius: 10px;
  padding: 12px 14px;
  cursor: pointer;
  transition: border-color 0.15s ease, transform 0.15s ease, box-shadow 0.15s ease;
  text-align: left;
}

.suggestion-chip:hover {
  border-color: var(--accent);
  box-shadow: 0 2px 10px rgba(18,20,28,0.06);
  transform: translateY(-1px);
}

/* ---------- Messages ---------- */

.msg-user {
  align-self: flex-end;
  background: var(--accent);
  color: #F5F6F8;
  padding: 13px 18px;
  border-radius: 12px 12px 2px 12px;
  max-width: 70%;
  font-size: 14.5px;
  line-height: 1.5;
}

.msg-answer {
  align-self: flex-start;
  background: var(--paper-raised);
  border: 1px solid var(--line);
  border-radius: 2px 12px 12px 12px;
  max-width: 78%;
  padding: 18px 20px;
  box-shadow: 0 1px 2px rgba(18,20,28,0.03);
  transition: background 0.2s ease, border-color 0.2s ease;
}

.msg-filter-note {
  display: block;
  font-family: var(--font-mono);
  font-size: 10px;
  letter-spacing: 0.04em;
  text-transform: uppercase;
  opacity: 0.6;
  margin-top: 4px;
}

.msg-answer-label {
  font-family: var(--font-mono);
  font-size: 10.5px;
  letter-spacing: 0.08em;
  text-transform: uppercase;
  color: var(--teal);
  margin-bottom: 8px;
  display: block;
}

.msg-answer p {
  margin: 0 0 12px;
  font-size: 14.5px;
  line-height: 1.6;
  color: var(--ink);
}

.answer-text {
  white-space: pre-wrap;
  line-height: 1.7;
  font-size: 14.5px;
  color: var(--ink);
  margin: 0 0 12px;
}

.stamp-row {
  display: flex;
  flex-wrap: wrap;
  gap: 6px;
  border-top: 1px dashed var(--line);
  padding-top: 12px;
  margin-top: 4px;
}

/* ---------- Sustainability score badge ---------- */

.score-card {
  display: flex;
  align-items: center;
  gap: 16px;
  background: #F2F7F5;
  border: 1px solid #CFE3DB;
  border-radius: 12px;
  padding: 14px 18px;
  margin: 0 0 14px;
}

[data-theme="dark"] .score-card {
  background: rgba(62,156,130,0.12);
  border-color: rgba(62,156,130,0.35);
}

.score-ring {
  width: 56px;
  height: 56px;
  border-radius: 50%;
  flex-shrink: 0;
  display: flex;
  align-items: center;
  justify-content: center;
  background: conic-gradient(var(--teal) calc(var(--pct) * 1%), #DCE7E2 0);
}

[data-theme="dark"] .score-ring {
  background: conic-gradient(var(--teal) calc(var(--pct) * 1%), #33453F 0);
}

.score-ring-inner {
  width: 44px;
  height: 44px;
  border-radius: 50%;
  background: var(--teal);
  display: flex;
  align-items: center;
  justify-content: center;
  font-family: var(--font-display);
  font-weight: 700;
  font-size: 15px;
  color: #FFFFFF;
}

.score-meta { display: flex; flex-direction: column; gap: 2px; }

.score-label {
  font-family: var(--font-mono);
  font-size: 10.5px;
  letter-spacing: 0.1em;
  text-transform: uppercase;
  color: var(--teal);
}

.score-value {
  font-family: var(--font-display);
  font-weight: 700;
  font-size: 18px;
  color: var(--ink);
}

.stamp-tag {
  font-family: var(--font-mono);
  font-size: 10.5px;
  letter-spacing: 0.02em;
  text-transform: uppercase;
  background: var(--paper);
  border: 1px solid var(--line);
  color: var(--ink-soft);
  padding: 4px 8px;
  border-radius: 4px;
}

/* ---------- Loading indicator ---------- */

.loading-row {
  align-self: flex-start;
  display: none;
  align-items: center;
  gap: 10px;
  color: var(--ink-soft);
  font-size: 13.5px;
  font-family: var(--font-mono);
  padding: 6px 2px;
}

.loading-row.active { display: flex; }

.loading-dots {
  display: flex;
  gap: 4px;
}

.loading-dots span {
  width: 6px;
  height: 6px;
  border-radius: 50%;
  background: var(--amber);
  animation: pulse 1.1s infinite ease-in-out;
}

.loading-dots span:nth-child(2) { animation-delay: 0.15s; }
.loading-dots span:nth-child(3) { animation-delay: 0.3s; }

@keyframes pulse {
  0%, 80%, 100% { opacity: 0.25; transform: scale(0.85); }
  40% { opacity: 1; transform: scale(1); }
}

/* ---------- Composer ---------- */

.composer {
  display: flex;
  gap: 16px;
  margin-top: 26px;
  padding-top: 18px;
  border-top: 1px solid var(--line);
}

#question-input {
  flex: 1;
  height: 58px;
  border: 1px solid var(--line);
  border-radius: 14px;
  background: var(--paper-raised);
  padding: 0 22px;
  font-family: var(--font-body);
  font-size: 15px;
  color: var(--ink);
  transition: background 0.2s ease, border-color 0.2s ease, box-shadow 0.2s ease;
}

#question-input:focus {
  outline: none;
  border-color: var(--accent);
  box-shadow: 0 0 0 3px rgba(30,41,59,0.08);
}

#send-btn {
  width: 120px;
  border: none;
  border-radius: 14px;
  background: var(--accent);
  color: white;
  font-family: var(--font-display);
  font-weight: 600;
  font-size: 15px;
  cursor: pointer;
  transition: 0.25s;
}

#send-btn:hover { background: var(--accent-soft); }
#send-btn:disabled { opacity: 0.6; cursor: default; }

.reset-form {
  margin-top: 12px;
  text-align: right;
}

.reset-btn {
  font-family: var(--font-mono);
  font-size: 11px;
  color: var(--ink-soft);
  background: none;
  border: none;
  cursor: pointer;
  text-decoration: underline;
  padding: 4px;
}

.reset-btn:hover { color: var(--ink); }

@media (max-width: 720px) {
  .app { grid-template-columns: 1fr; }
  .rail { display: none; }
  .main { padding: 24px 20px; }
  .msg-user, .msg-answer { max-width: 92%; }
  .suggestions { grid-template-columns: 1fr; }
}
</style>
</head>
<body>

<div class="app">
  <aside class="rail">
    <div class="rail-brand">
      <span class="rail-brand-mark">S/OS</span>
      <span class="rail-brand-name">SellerOS</span>
    </div>
    <p class="rail-tagline">AI Copilot for Indian Marketplace Sellers</p>

    <div class="rail-label">Knowledge Modules</div>
    <ul class="rail-modules">
      <li>
        <form method="POST" action="{{ url_for('set_filter') }}">
          <input type="hidden" name="platform" value="">
          <button type="submit" class="module-btn{{ ' active' if not active_filter else '' }}">
            <span class="dot dot-all"></span>All Modules
          </button>
        </form>
      </li>
      {% for p in platforms %}
      <li>
        <form method="POST" action="{{ url_for('set_filter') }}">
          <input type="hidden" name="platform" value="{{ p.key }}">
          <button type="submit" class="module-btn{{ ' active' if active_filter == p.key else '' }}">
            <span class="dot {{ p.dot }}"></span>{{ p.label }}
          </button>
        </form>
      </li>
      {% endfor %}
    </ul>

    <div class="theme-toggle-row">
      <span class="theme-toggle-label">Dark mode</span>
      <label class="theme-switch">
        <input type="checkbox" id="theme-toggle">
        <span class="slider"></span>
      </label>
    </div>

    <div class="rail-footer">Powered by Local AI<br>ChromaDB · Ollama · Flask</div>
  </aside>

  <main class="main">
    <header class="topbar">
      <h1>SellerOS</h1>
      <p>AI Copilot for Indian Marketplace Sellers</p>
      {% if active_filter %}
      <div class="filter-pill">
        Filtering: {{ active_filter_label }}
        <form method="POST" action="{{ url_for('set_filter') }}" style="display:inline;">
          <input type="hidden" name="platform" value="">
          <button type="submit" title="Clear filter">&times;</button>
        </form>
      </div>
      {% endif %}
    </header>

    <section class="thread" id="thread">
      {% if not history %}
        <div class="empty-state">
          <div class="empty-state-wordmark">Seller<span class="accent">OS</span></div>
          <p class="lead">What can I help you with today?</p>
          <p class="empty-sub">Ask anything about your seller operations, or try one of these:</p>
          <div class="suggestions">
            <button type="button" class="suggestion-chip" data-question="What documents do I need for GST registration?">GST Registration</button>
            <button type="button" class="suggestion-chip" data-question="What are Amazon's image requirements for product listings?">Amazon Image Requirements</button>
            <button type="button" class="suggestion-chip" data-question="What are Flipkart's packaging guidelines?">Flipkart Packaging</button>
            <button type="button" class="suggestion-chip" data-question="How do I register as a seller on Meesho?">Meesho Registration</button>
            <button type="button" class="suggestion-chip" data-question="What's my sustainability score? I mostly ship in plastic mailers and use standard courier delivery.">My Sustainability Score</button>
          </div>
        </div>
      {% endif %}

      {% for turn in history %}
        <div class="msg-user">
          {{ turn.question }}
          {% if turn.platform_filter %}<span class="msg-filter-note">scoped to {{ turn.platform_filter }}</span>{% endif %}
        </div>
        <div class="msg-answer">
          <span class="msg-answer-label">SellerOS</span>
          {% if turn.score is defined and turn.score is not none %}
          <div class="score-card">
            <div class="score-ring" style="--pct: {{ turn.score }}">
              <div class="score-ring-inner">{{ turn.score }}</div>
            </div>
            <div class="score-meta">
              <span class="score-label">Sustainability Score</span>
              <span class="score-value">{{ turn.score }} / 100 &middot; {{ turn.score_band }}</span>
            </div>
          </div>
          {% endif %}
          <div class="answer-text">{{ turn.answer }}</div>
          {% if turn.sources %}
          <div class="stamp-row">
            {% for label in turn.sources %}
              <span class="stamp-tag">{{ label }}</span>
            {% endfor %}
          </div>
          {% endif %}
        </div>
      {% endfor %}

      <div class="loading-row" id="loading-row">
        <div class="loading-dots"><span></span><span></span><span></span></div>
        <span>SellerOS is thinking…</span>
      </div>
    </section>

    <form class="composer" method="POST" action="{{ url_for('ask') }}" id="ask-form">
      <input type="text" name="question" id="question-input" placeholder="Ask a question about Amazon, Meesho, Flipkart, GST, or sustainability…" autocomplete="off" required />
      <button type="submit" id="send-btn">Ask</button>
    </form>

    {% if history %}
    <form method="POST" action="{{ url_for('reset') }}" class="reset-form">
      <button type="submit" class="reset-btn">Clear conversation</button>
    </form>
    {% endif %}
  </main>
</div>

<script>
  // Clicking a suggested question fills the input and focuses it.
  document.querySelectorAll('.suggestion-chip').forEach(function (chip) {
    chip.addEventListener('click', function () {
      var input = document.getElementById('question-input');
      input.value = chip.getAttribute('data-question');
      input.focus();
    });
  });

  // Show a loading state and disable the button while the request is in flight.
  var askForm = document.getElementById('ask-form');
  if (askForm) {
    askForm.addEventListener('submit', function () {
      var loadingRow = document.getElementById('loading-row');
      var sendBtn = document.getElementById('send-btn');
      if (loadingRow) loadingRow.classList.add('active');
      if (sendBtn) {
        sendBtn.disabled = true;
        sendBtn.textContent = '···';
      }
      var thread = document.getElementById('thread');
      if (thread) thread.scrollTop = thread.scrollHeight;
    });
  }

  // Auto-scroll to the latest answer on page load.
  window.addEventListener('load', function () {
    var thread = document.getElementById('thread');
    if (thread) thread.scrollTop = thread.scrollHeight;
  });

  // Dark mode toggle — reflects current theme on load, persists choice.
  var themeToggle = document.getElementById('theme-toggle');
  if (themeToggle) {
    var savedTheme = localStorage.getItem('sellerOS-theme') || 'light';
    themeToggle.checked = savedTheme === 'dark';
    themeToggle.addEventListener('change', function () {
      var theme = themeToggle.checked ? 'dark' : 'light';
      document.documentElement.setAttribute('data-theme', theme);
      localStorage.setItem('sellerOS-theme', theme);
    });
  }
</script>

</body>
</html>"""

# =========================
# Helpers
# =========================

# Sidebar filter buttons. "key" must match the value stored in each
# document's metadata["platform"] field in your Chroma collection —
# check that field name/values if filtering doesn't seem to narrow results.
PLATFORMS = [
    {"key": "amazon", "label": "Amazon", "dot": "dot-amazon"},
    {"key": "meesho", "label": "Meesho", "dot": "dot-meesho"},
    {"key": "flipkart", "label": "Flipkart", "dot": "dot-flipkart"},
    {"key": "government", "label": "GST & Government", "dot": "dot-government"},
    {"key": "sustainability", "label": "Sustainability", "dot": "dot-sustainability"},
]

PLATFORM_LABELS = {p["key"]: p["label"] for p in PLATFORMS}

# The "government" button's label is "GST & Government", but the metadata
# value written during ingestion is "gst" (confirmed) — not "government".
PLATFORM_MATCH_VALUES = {
    "government": ["gst"],
}

# Known internal labels mapped to clean, judge-friendly display names.
# Anything not in this dict falls back to a generic snake_case -> Title Case
# conversion, so new modules still look reasonable without a code change.
MODULE_DISPLAY_NAMES = {
    "gst_registration": "GST Registration",
    "gst": "GST",
    "amazon_policies": "Amazon Policies",
    "amazon": "Amazon",
    "amazon_images": "Amazon Image Requirements",
    "flipkart_packaging": "Flipkart Packaging",
    "flipkart": "Flipkart",
    "meesho_registration": "Meesho Registration",
    "meesho": "Meesho",
    "sustainability": "Sustainability",
    "plastic_waste_rules": "Plastic Waste Rules",
    "government": "Government",
}


def humanize_label(label):
    """Turn an internal metadata label (e.g. 'gst_registration') into a
    display-friendly one (e.g. 'GST Registration'). Falls back to a
    generic underscore/hyphen -> Title Case conversion for unknown labels.
    """

    if not label:
        return "Source"

    key = str(label).strip().lower()

    if key in MODULE_DISPLAY_NAMES:
        return MODULE_DISPLAY_NAMES[key]

    return key.replace("_", " ").replace("-", " ").title()


# =========================
# Sustainability scoring
# =========================
# Self-reported, chat-driven scoring: rather than a rigid form, the LLM
# itself estimates a 0-100 score from whatever business details the seller
# has shared (in this message and earlier in the conversation), states its
# assumptions, and follows up with prioritized, doable environmental fixes.
# It grounds the advice in the retrieved sustainability / plastic-waste-rules
# documents so recommendations track real Indian marketplace & government
# guidance rather than being generic.

SCORE_TRIGGER_PHRASES = [
    "sustainability score",
    "sustainability rating",
    "how sustainable",
    "environmental score",
    "environment score",
    "green score",
    "eco score",
    "eco-score",
    "carbon score",
    "score my business",
    "rate my sustainability",
    "rate my business",
    "how eco friendly",
    "how eco-friendly",
    "how green is my business",
]

SCORE_PATTERN = re.compile(
    r"sustainability\s*score[^\d]{0,20}(\d{1,3})\s*(?:/|out of)\s*100",
    re.IGNORECASE,
)

SCORE_BANDS = [
    (85, "Excellent"),
    (70, "Good"),
    (50, "Fair"),
    (30, "Needs Work"),
    (0, "High Impact"),
]


def is_sustainability_score_query(question):
    """True if the seller is asking to be scored/rated on sustainability."""

    q = question.lower()
    return any(phrase in q for phrase in SCORE_TRIGGER_PHRASES)


def score_band(score):
    """Map a 0-100 score to a short qualitative label."""

    for threshold, label in SCORE_BANDS:
        if score >= threshold:
            return label
    return SCORE_BANDS[-1][1]


def build_scoring_prompt(question, history):
    """Wrap the seller's message with instructions that turn generate_answer
    into a sustainability-scoring + advisory assistant. We keep this as a
    prompt augmentation (rather than a new retrieve.py function) so it works
    with the existing semantic_search/generate_answer pipeline untouched.
    """

    # Fold in a short slice of prior turns so self-reported details the
    # seller already mentioned (e.g. "I use plastic mailers") carry over.
    prior_context = ""
    for turn in history[-4:]:
        prior_context += "Seller: {0}\nSellerOS: {1}\n".format(
            turn.get("question", ""),
            turn.get("answer", ""),
        )

    instructions = (
        "You are SellerOS's Sustainability Advisor for Indian marketplace "
        "sellers. Using ONLY the seller's self-reported details below (and "
        "recent conversation) plus the reference context:\n\n"
        "1. Output a real whole-number score on its own line as "
        "'Sustainability Score: 63/100' (63 is just an example — never "
        "write NN, XX, or any placeholder).\n"
        "2. Break it into 4 sub-areas (25 pts each): Packaging & Materials, "
        "Shipping & Logistics, Energy & Operations, Waste & Returns. "
        "One-line justification each.\n"
        "3. Sparse info? Assume reasonable mid-range defaults, label them as "
        "assumptions, and ask 1-3 quick follow-ups.\n"
        "4. Give 3-5 prioritized, actionable fixes for the weakest areas, "
        "grounded in the sustainability/plastic-waste context (e.g. Indian "
        "EPR rules).\n"
        "5. Practical, encouraging tone — not preachy.\n\n"
        "Recent conversation:\n{prior}\n"
        "Seller's message: {question}"
    ).format(prior=prior_context.strip() or "(none yet)", question=question)

    return instructions


def extract_score(answer_text):
    """Pull a NN/100 sustainability score out of the generated answer, if
    present. Returns None if the model didn't produce a parseable score
    (e.g. it asked clarifying questions instead).
    """

    match = SCORE_PATTERN.search(answer_text)

    if not match:
        return None

    score = int(match.group(1))
    return max(0, min(100, score))


# =========================
# Routes
# =========================

@app.route("/")
def index():

    history = session.get("history", [])
    active_filter = session.get("platform_filter")
    active_filter_label = PLATFORM_LABELS.get(active_filter) if active_filter else None

    return render_template_string(
        INDEX_HTML,
        history=history,
        platforms=PLATFORMS,
        active_filter=active_filter,
        active_filter_label=active_filter_label
    )

@app.route("/health")
def health():

    return {
        "status": "running"
    }

@app.route("/set-filter", methods=["POST"])
def set_filter():

    platform = request.form.get("platform", "").strip().lower()

    if platform:
        session["platform_filter"] = platform
    else:
        session.pop("platform_filter", None)

    return redirect(url_for("index"))

@app.route("/ask", methods=["POST"])
def ask():

    question = request.form.get("question", "").strip()

    if not question:
        return redirect(url_for("index"))

    history = session.get("history", [])
    active_filter = session.get("platform_filter")
    scoring_query = is_sustainability_score_query(question)

    # Bias retrieval toward the sustainability / plastic-waste-rules module
    # when the seller is asking to be scored, so the advice that follows is
    # grounded in the right documents even if their own wording is sparse
    # (e.g. just "what's my sustainability score?").
    search_query = (
        question + " sustainability packaging shipping energy waste plastic"
        if scoring_query else question
    )

    # Pull extra candidates when a sidebar filter is active so there's
    # enough to filter down from; otherwise 5 is plenty.
    results = semantic_search(
        search_query,
        top_k=15 if active_filter else 5
    )

    all_contexts = results["documents"][0]
    all_sources = results["metadatas"][0]

    if active_filter:
        acceptable_values = PLATFORM_MATCH_VALUES.get(active_filter, [active_filter])
        filtered = [
            (ctx, src) for ctx, src in zip(all_contexts, all_sources)
            if str(src.get("platform", "")).strip().lower() in acceptable_values
        ]

        # If nothing matches the filter, fall back to the best overall
        # results rather than showing an empty/unhelpful answer.
        pairs = filtered[:5] if filtered else list(zip(all_contexts, all_sources))[:5]
    else:
        pairs = list(zip(all_contexts, all_sources))[:5]

    contexts = [ctx for ctx, _ in pairs]
    sources = [src for _, src in pairs]

    llm_question = (
        build_scoring_prompt(question, history) if scoring_query else question
    )

    answer = generate_answer(
        llm_question,
        contexts
    )

    score = extract_score(answer) if scoring_query else None

    # The underlying model occasionally echoes the format example instead of
    # substituting a real number (e.g. "Sustainability Score: NN/100"). If
    # that happens, retry once with a blunt correction rather than showing
    # no badge at all.
    if scoring_query and score is None:
        retry_question = (
            llm_question
            + "\n\nReminder: your previous attempt did not include a real "
            "number. Output MUST contain the literal digits for the score, "
            "e.g. 'Sustainability Score: 63/100'. Do not write NN, XX, or "
            "any other placeholder."
        )
        retry_answer = generate_answer(retry_question, contexts)
        retry_score = extract_score(retry_answer)

        if retry_score is not None:
            answer = retry_answer
            score = retry_score

    seen = set()
    source_labels = []

    for src in sources:

        # Metadata now contains:
        # platform, module, source, chunk

        raw_label = src.get("module") or src.get("source") or "source"
        label = humanize_label(raw_label)

        if label not in seen:
            seen.add(label)
            source_labels.append(label)

    history.append({
        "question": question,
        "answer": answer,
        "sources": source_labels,
        "platform_filter": PLATFORM_LABELS.get(active_filter) if active_filter else None,
        "score": score,
        "score_band": score_band(score) if score is not None else None
    })

    session["history"] = history

    return redirect(url_for("index"))

@app.route("/reset", methods=["POST"])
def reset():

    session.pop("history", None)
    session.pop("platform_filter", None)

    return redirect(url_for("index"))

if __name__ == "__main__":

    app.run(
        host="0.0.0.0",
        port=5000,
        debug=True
    )