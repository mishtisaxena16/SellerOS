"""
orchestrator_layer.py — the ENTIRE Orchestrator Layer in one file.

Consolidates what used to be five files:
    state.py       -> SellerOSState + new_state()
    router.py      -> IntentRouter (+ singleton `router`)
    conditions.py  -> conditional-edge functions used by the graph
    nodes.py       -> every LangGraph node function
    graph.py       -> the compiled StateGraph + run_workflow()/resume_workflow()

Per the architecture decision, LangGraph lives ONLY here. Connectors,
Tools, and Agents never import it and never know it exists.

    Supervisor -> LangGraph Orchestrator -> Specialized Agents
               -> Tools -> Connectors -> Marketplace

INTEGRATION PASS — WHAT CHANGED AND WHY
-----------------------------------------------------------------------
This file previously imported interfaces that didn't exist on disk
(`backend.agents.registry.registry`, `backend.guardrails.guardrail_layer`,
`backend.memory.service`, a synchronous `agent.run(state)`, an
`executive_agent` that was never registered, and an
`AgentResult.requires_approval` field that AgentResult doesn't have).
None of that was a typo to patch — it was written against an imagined
package layout instead of the real one. Fixed against the actual code:

  - Agent Layer: `BaseAgent.run()` is `async` and takes
    `(tool_manager, seller_id, user_query, session=None,
    conversation_history=None, business_rules=None)` — not a raw state
    dict. Every node that calls an agent is now `async def`, and the
    graph is invoked with `.ainvoke()` (see `run_workflow` /
    `resume_workflow` at the bottom). A `ToolManager` is built (and
    cached) per seller_id, matching how tools are actually seller-scoped
    (agent_layer/base/tool_manager.py).
  - All 14 domain agents are registered via their own domain's
    `register.py` (agent_layer/registry/agent_registry.py's
    `_DOMAIN_MODULES` list) — nodes for any intent without a real
    agent still degrade to a clear "not implemented yet" message
    instead of crashing with AgentNotFoundError, in case a domain
    module is ever added to `_DOMAIN_MODULES` without also filling in
    every agent it's expected to register.
  - `executive_node` is removed. There is no `ExecutiveAgent` in the
    registry, and per the architecture discussion that led to adding a
    Supervisor layer, its planning responsibility belongs one level up
    — see supervisor.py — not inside the graph. `router` now feeds
    `supervisor` (the in-graph routing node, see note below) directly.
  - Guardrail Layer: fixed import to `from guardrails import
    guardrail_engine` (backend/guardrails.py is a single module, not a
    `backend.guardrails.guardrail_layer` package) — guardrails.py's own
    public API (`GuardrailEngine.evaluate()`, `GuardrailResult`) already
    matched what `guardrail_node` expected, so nothing else changed here.
  - Memory Layer: fixed to actually import (see memory_bridge.py — the
    package directory had a space in its name, `memory layer/`, which
    is not valid for Python imports; renamed to `memory_layer/`) and
    construct correctly (`MemoryService(InMemoryStorage())` — it takes
    a storage backend, it isn't a no-arg singleton). `memory_layer_node`
    now calls the real `MemoryService.get_agent_context()`.

NAMING NOTE — "supervisor" node vs. the Supervisor layer
-----------------------------------------------------------------------
`supervisor_node`/`supervisor_route` below are an in-graph conditional
-routing helper (which specific worker node runs next, given intent +
plan progress) — they predate, and are not the same thing as, the new
top-level Supervisor layer in supervisor.py that now sits ABOVE this
whole orchestrator (intent understanding, planning, memory-before-
decision, approval gating). Left the in-graph names alone rather than
doing a cosmetic rename — they're genuinely just routing logic — but
if that reads as confusing, renaming `supervisor_node` to something like
`worker_router_node` is a safe, mechanical follow-up.
"""
import os
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, TypedDict

from langgraph.checkpoint.memory import MemorySaver

try:
    from langgraph.checkpoint.postgres import PostgresSaver
except ImportError:
    PostgresSaver = None

from langgraph.graph import END, StateGraph

# Agent Layer — real interfaces (see module docstring above for what
# was fixed here).
from backend.ai.agent_layer.registry.agent_registry import AgentRegistry, AgentNotFoundError, build_default_registry
from backend.ai.agent_layer.base.reasoning import OllamaReasoner
from backend.ai.agent_layer.base.tool_manager import ToolManager

# Tool Layer — one ToolManager per seller_id is built against this.
from backend.ai.tools_layer.registry.tool_registry import build_default_registry as build_default_tool_registry

# Guardrail Engine singleton (backend/guardrails.py).
from backend.ai.guardrails_layer.guardrails import guardrail_engine

# MarketplaceSession seam — see connectors/session_store.py's module
# docstring for why this exists and the "never in checkpointed state"
# guarantee it preserves.
from backend.ai.connectors_layer.session_store import get_marketplace_session

# Memory Layer — bridged in from backend/memory_layer/memory/.
import backend.ai.memory_layer.memory_bridge as memory_bridge

memory_bridge.ensure_on_path()
from memory.service import MemoryService  # noqa: E402 (see memory_bridge.ensure_on_path() above)
from memory.storage import InMemoryStorage  # noqa: E402


# =============================================================================
# 0. SHARED SINGLETONS — built once at import time, reused across requests
# =============================================================================

_reasoner = OllamaReasoner()
agent_registry: AgentRegistry = build_default_registry(_reasoner)
_tool_registry = build_default_tool_registry()

# InMemoryStorage today; swap for a Redis/Postgres-backed BaseMemoryStore
# later without any caller (this file, supervisor.py) needing to change —
# same reasoning as memory/service.py's own docstring.
memory_service: Optional[MemoryService] = MemoryService(InMemoryStorage())

# One ToolManager per seller_id, built lazily and reused — ToolManager is
# explicitly seller/session-scoped (agent_layer/base/tool_manager.py), so
# it can't be a single shared instance like agent_registry/memory_service,
# but rebuilding it on every single node call would be wasteful.
_tool_managers: Dict[str, ToolManager] = {}


def _get_tool_manager(seller_id: str, memory: Any = None) -> ToolManager:
    if seller_id not in _tool_managers:
        _tool_managers[seller_id] = ToolManager(_tool_registry, seller_id=seller_id, memory=memory)
    return _tool_managers[seller_id]


# Which real agent_registry key backs each graph node's intent, if any.
# `None` means "no agent built for this yet" — the node reports that
# plainly instead of crashing. Wiring a new agent later is a one-line
# change here plus registering it in agent_layer/registry/agent_registry.py
# under a matching key; no graph edges need to change.
AGENT_NODE_TO_REGISTRY_KEY: Dict[str, Optional[str]] = {
    "listing_agent": "listing",
    "inventory_agent": "inventory",
    "seller_coach_agent": "seller_coach",
    "pricing_agent": "pricing",
    "order_agent": "orders",
    "analytics_agent": "analytics",
    "forecasting_agent": "forecast",
    "ads_agent": "ads",
    "profitability_agent": "profitability",
    "competitor_agent": "competitor",
    "campaign_agent": "campaign",
    "seo_agent": "seo",
    "content_agent": "content",
    "sustainability_agent": "sustainability",
}


# =============================================================================
# 1. STATE CONTRACT
# =============================================================================

class SellerOSState(TypedDict, total=False):
    seller_id: str
    session_id: Optional[str]  # ties this run to a Memory Layer conversation
    query: str
    marketplace: Optional[str]
    context: Dict[str, Any]

    # Explicit, separate storage for recalled vector/history memory
    recalled_memory: Dict[str, Any]
    memory_refs: List[str]

    # Routing & Planning
    intent: Optional[str]
    workflow: Optional[str]
    selected_agent: Optional[str]
    plan: List[Any]
    current_step_index: int
    supervisor_next: Optional[str]

    # Agent Outputs & Execution Tracking
    parallel_results: Dict[str, Any]
    tool_results: Dict[str, Any]
    # Flat audit trail of every tool call any agent made this run —
    # {"agent": ..., "tool": ..., "action": ..., "success": ...} per
    # entry, sourced from ToolResult.metadata (see executor.py's
    # tagging). This is what guardrails.ToolExecutionRule actually
    # checks against; `tool_results` above holds each agent's final
    # structured output (AgentResult.data), which is a different thing
    # and was never enough on its own to answer "which tools ran".
    executed_tools: List[Dict[str, Any]]
    history: List[Dict[str, Any]]
    events: List[Dict[str, Any]]

    # Recovery
    retry_count: int
    max_retries: int
    last_error: Optional[str]

    # Guardrails & Human-in-the-Loop
    guardrail_findings: List[str]
    approval_required: bool
    approval_granted: Optional[bool]

    # Connector Output
    published_payload: Optional[Dict[str, Any]]
    published_status: Optional[str]
    final_response: Optional[str]
    error: Optional[str]


def new_state(
    query: str,
    seller_id: str = "default_seller",
    marketplace: Optional[str] = None,
    session_id: Optional[str] = None,
    plan: Optional[List[Any]] = None,
) -> SellerOSState:
    return SellerOSState(
        seller_id=seller_id,
        session_id=session_id,
        query=query,
        marketplace=marketplace,
        context={},
        recalled_memory={},
        memory_refs=[],
        intent=None,
        workflow=None,
        selected_agent=None,
        plan=plan or [],
        current_step_index=0,
        supervisor_next=None,
        parallel_results={},
        tool_results={},
        executed_tools=[],
        history=[],
        events=[],
        retry_count=0,
        max_retries=3,
        last_error=None,
        guardrail_findings=[],
        approval_required=False,
        approval_granted=None,
        published_payload=None,
        published_status=None,
        final_response=None,
        error=None,
    )


# =============================================================================
# 2. ROUTER & EVENT HELPERS
# =============================================================================

def _emit_event(state: SellerOSState, event_type: str, details: Dict[str, Any]) -> List[Dict[str, Any]]:
    events = list(state.get("events", []))
    events.append({
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "event_type": event_type,
        "details": details,
    })
    return events


MARKETPLACES = ["amazon", "flipkart", "meesho"]

INTENT_KEYWORDS = {
    "create_listing": ["create a listing", "create an optimized", "new listing", "list a product", "add product"],
    "update_listing": ["update listing", "edit listing", "change listing"],
    "pricing": ["price", "pricing", "reprice", "discount"],
    "inventory": ["inventory", "stock level", "restock", "out of stock"],
    "orders": ["order", "orders", "shipment", "fulfil", "fulfill"],
    "analytics": ["sales", "analytics", "performance", "revenue", "trends"],
    "forecasting": ["forecast", "demand", "projection"],
    "profitability": ["profitability", "profit margin", "margin health", "am i profitable"],
    "competitor": ["competitor", "competitors", "competing seller", "vs other sellers"],
    # Checked before "ads" (dict order matters -- IntentRouter.detect_intent
    # returns the first match) since "campaign" used to sit inside the ads
    # keyword list; a strategy/planning question should route to
    # CampaignAgent, not straight to AdsAgent's execution-facing summary.
    "campaign": ["campaign strategy", "campaign plan", "marketing campaign", "campaign calendar"],
    "ads": ["run an ad", "run ads", "create an ad", "sponsored listing", "advertisement", "ppc", "ad spend"],
    "seo": ["seo", "search ranking", "keyword", "improve visibility", "optimize listing"],
    "content": ["caption", "product description", "marketing copy", "write a description", "content for"],
    "seller_coach": ["advice", "coach", "how do i improve", "tips"],
    "sustainability": ["sustainable", "sustainability", "carbon", "eco-friendly"],
}

WORKFLOW_FOR_INTENT = {
    "create_listing": "listing_workflow",
    "update_listing": "listing_workflow",
    "pricing": "pricing_workflow",
    "inventory": "inventory_workflow",
    "orders": "order_workflow",
    "analytics": "parallel_analytics_workflow",
    "forecasting": "forecasting_workflow",
    "profitability": "profitability_workflow",
    "competitor": "competitor_workflow",
    "campaign": "campaign_workflow",
    "ads": "ads_workflow",
    "seo": "seo_workflow",
    "content": "content_workflow",
    "seller_coach": "seller_coach_workflow",
    "sustainability": "sustainability_workflow",
}

AGENT_FOR_INTENT = {
    "create_listing": "listing_agent",
    "update_listing": "listing_agent",
    "pricing": "pricing_agent",
    "inventory": "inventory_agent",
    "orders": "order_agent",
    "analytics": "analytics_agent",
    "forecasting": "forecasting_agent",
    "profitability": "profitability_agent",
    "competitor": "competitor_agent",
    "campaign": "campaign_agent",
    "ads": "ads_agent",
    "seo": "seo_agent",
    "content": "content_agent",
    "seller_coach": "seller_coach_agent",
    "sustainability": "sustainability_agent",
}


class IntentRouter:
    def detect_marketplace(self, query: str) -> Optional[str]:
        q = query.lower()
        for marketplace in MARKETPLACES:
            if marketplace in q:
                return marketplace
        return None

    def detect_intent(self, query: str) -> str:
        q = query.lower()
        for intent, keywords in INTENT_KEYWORDS.items():
            if any(keyword in q for keyword in keywords):
                return intent
        return "unknown"

    def select_workflow(self, intent: str) -> str:
        return WORKFLOW_FOR_INTENT.get(intent, "general_workflow")

    def select_agent(self, intent: str) -> str:
        return AGENT_FOR_INTENT.get(intent, "seller_coach_agent")


router = IntentRouter()


# =============================================================================
# 3. CONDITIONAL ROUTING EDGES
# =============================================================================

def needs_pricing(state: SellerOSState) -> str:
    if state.get("intent") == "create_listing":
        return "pricing"
    return "skip_pricing"


def needs_approval(state: SellerOSState) -> str:
    if state.get("error") == "blocked_by_guardrail":
        return "blocked"
    return "approval" if state.get("approval_required") else "skip_approval"


def should_publish(state: SellerOSState) -> str:
    if state.get("approval_required") and not state.get("approval_granted"):
        return "halt"
    return "publish"


def check_retry_or_recover(state: SellerOSState) -> str:
    if not state.get("error"):
        return "continue"
    if state.get("retry_count", 0) < state.get("max_retries", 3):
        return "retry"
    return "recover"


def supervisor_route(state: SellerOSState) -> str:
    return state.get("supervisor_next", "finish")


# =============================================================================
# 4. GRAPH NODES
# =============================================================================

def context_assembly_node(state: SellerOSState) -> Dict[str, Any]:
    assembled_context = {
        **state.get("context", {}),
        "query": state.get("query", ""),
        "marketplace": state.get("marketplace") or "general",
    }
    events = _emit_event(state, "CONTEXT_ASSEMBLED", {"status": "success"})
    return {"context": assembled_context, "events": events}


def memory_layer_node(state: SellerOSState) -> Dict[str, Any]:
    """Retrieves long-term memory into recalled_memory without contaminating live context."""
    seller_id = state.get("seller_id", "default_seller")
    session_id = state.get("session_id")

    if memory_service is None:
        return {}

    try:
        recalled_context = memory_service.get_agent_context(seller_id, session_id=session_id)
    except Exception as e:
        events = _emit_event(state, "MEMORY_RECALL_FAILED", {"error": str(e)})
        return {"events": events}

    events = _emit_event(state, "MEMORY_RECALLED", {"keys_retrieved": list(recalled_context.keys())})
    return {
        "recalled_memory": recalled_context,
        # No separate "reference id" concept in MemoryService today —
        # the recalled keys themselves double as a lightweight trace of
        # what was pulled in, useful for guardrails/debugging.
        "memory_refs": list(recalled_context.keys()),
        "events": events,
    }


def router_node(state: SellerOSState) -> Dict[str, Any]:
    query = state["query"]
    marketplace = state.get("marketplace") or router.detect_marketplace(query)
    intent = router.detect_intent(query)
    selected_agent = router.select_agent(intent)
    workflow = router.select_workflow(intent)

    events = _emit_event(state, "INTENT_ROUTED", {"intent": intent, "marketplace": marketplace})
    return {
        "marketplace": marketplace,
        "intent": intent,
        "selected_agent": selected_agent,
        "workflow": workflow,
        "events": events,
    }


def supervisor_node(state: SellerOSState) -> Dict[str, Any]:
    """
    In-graph routing helper — decides which worker node runs next given
    intent + plan progress. Not the Supervisor layer (see NAMING NOTE
    in the module docstring).
    """
    intent = state.get("intent", "")
    current_index = state.get("current_step_index", 0)
    plan = state.get("plan", [])

    if current_index >= len(plan) and plan:
        next_node = "finish"
    elif intent in ["create_listing", "update_listing"]:
        next_node = "listing"
    elif intent == "pricing":
        next_node = "pricing"
    elif intent == "analytics":
        next_node = "analytics"
    else:
        next_node = state.get("selected_agent", "finish").replace("_agent", "")

    events = _emit_event(state, "SUPERVISOR_DECISION", {"selected_next_node": next_node})
    return {"supervisor_next": next_node, "events": events}


async def _run_agent_node(agent_node_name: str, state: SellerOSState) -> Dict[str, Any]:
    registry_key = AGENT_NODE_TO_REGISTRY_KEY.get(agent_node_name)

    if registry_key is None:
        events = _emit_event(state, "AGENT_NOT_IMPLEMENTED", {"agent": agent_node_name})
        return {
            "error": None,
            "final_response": (
                f"'{agent_node_name.replace('_', ' ')}' isn't built yet — currently "
                f"wired agents are: {', '.join(sorted(k for k in AGENT_NODE_TO_REGISTRY_KEY.values() if k))}."
            ),
            "events": events,
        }

    try:
        agent = agent_registry.get(registry_key)
    except AgentNotFoundError as e:
        events = _emit_event(state, "AGENT_NOT_REGISTERED", {"agent": agent_node_name, "error": str(e)})
        return {"error": str(e), "last_error": str(e), "events": events}

    seller_id = state.get("seller_id", "default_seller")
    recalled_memory = state.get("recalled_memory") or {}
    tool_manager = _get_tool_manager(seller_id, memory=recalled_memory)
    conversation_history = recalled_memory.get("conversation_history")

    # Built fresh per call, handed straight to agent.run(), and never
    # written into the dict returned below — see session_store.py's
    # module docstring for why state must never carry this object.
    marketplace_session = get_marketplace_session(seller_id, state.get("marketplace"))

    try:
        result = await agent.run(
            tool_manager=tool_manager,
            seller_id=seller_id,
            user_query=state.get("query", ""),
            session=marketplace_session,
            conversation_history=conversation_history,
        )

        if not result.success:
            events = _emit_event(state, "AGENT_FAILED", {"agent": agent.name, "error": result.message})
            return {
                "error": result.message or f"Agent {agent.name} failed.",
                "last_error": result.message,
                "retry_count": state.get("retry_count", 0) + 1,
                "events": events,
            }

        tool_results = dict(state.get("tool_results", {}))
        tool_results[agent.name] = result.data
        executed_tools = list(state.get("executed_tools", []))
        for tool_call in result.tool_calls:
            meta = getattr(tool_call, "metadata", {}) or {}
            executed_tools.append({
                "agent": agent.name,
                "tool": meta.get("tool_name"),
                "action": meta.get("action"),
                "success": getattr(tool_call, "success", None),
            })
        history = list(state.get("history", [])) + [
            {"agent": agent.name, "output": result.message, "success": result.success}
        ]
        events = _emit_event(state, "AGENT_COMPLETED", {"agent": agent.name})

        # Whether this result needs human sign-off is decided entirely by
        # guardrail_node (HumanApprovalRule / MarketplacePolicyRule) right
        # after this node — AgentResult itself carries no approval flag,
        # so there's exactly one place that decision is made.
        return {
            "tool_results": tool_results,
            "executed_tools": executed_tools,
            "history": history,
            "final_response": result.message,
            "retry_count": 0,
            "error": None,
            "current_step_index": state.get("current_step_index", 0) + 1,
            "events": events,
        }

    except Exception as e:
        events = _emit_event(state, "AGENT_EXCEPTION", {"agent": agent_node_name, "exception": str(e)})
        return {
            "error": str(e),
            "last_error": str(e),
            "retry_count": state.get("retry_count", 0) + 1,
            "events": events,
        }


async def listing_node(state: SellerOSState) -> Dict[str, Any]: return await _run_agent_node("listing_agent", state)
async def pricing_node(state: SellerOSState) -> Dict[str, Any]: return await _run_agent_node("pricing_agent", state)
async def inventory_node(state: SellerOSState) -> Dict[str, Any]: return await _run_agent_node("inventory_agent", state)
async def order_node(state: SellerOSState) -> Dict[str, Any]: return await _run_agent_node("order_agent", state)
async def analytics_node(state: SellerOSState) -> Dict[str, Any]: return await _run_agent_node("analytics_agent", state)
async def forecasting_node(state: SellerOSState) -> Dict[str, Any]: return await _run_agent_node("forecasting_agent", state)
async def profitability_node(state: SellerOSState) -> Dict[str, Any]: return await _run_agent_node("profitability_agent", state)
async def competitor_node(state: SellerOSState) -> Dict[str, Any]: return await _run_agent_node("competitor_agent", state)
async def campaign_node(state: SellerOSState) -> Dict[str, Any]: return await _run_agent_node("campaign_agent", state)
async def ads_node(state: SellerOSState) -> Dict[str, Any]: return await _run_agent_node("ads_agent", state)
async def seo_node(state: SellerOSState) -> Dict[str, Any]: return await _run_agent_node("seo_agent", state)
async def content_node(state: SellerOSState) -> Dict[str, Any]: return await _run_agent_node("content_agent", state)
async def seller_coach_node(state: SellerOSState) -> Dict[str, Any]: return await _run_agent_node("seller_coach_agent", state)
async def sustainability_node(state: SellerOSState) -> Dict[str, Any]: return await _run_agent_node("sustainability_agent", state)


def recovery_node(state: SellerOSState) -> Dict[str, Any]:
    error = state.get("last_error", "Unknown error")
    events = _emit_event(state, "RECOVERY_EXECUTED", {"error": error})
    return {"final_response": f"Execution halted: {error}", "error": f"Recovered: {error}", "events": events}


def guardrail_node(state: SellerOSState) -> Dict[str, Any]:
    """Executes Guardrail Engine against agent outputs, plan steps, and state."""
    result = guardrail_engine.evaluate(state)
    approval_required = state.get("approval_required", False) or result.requires_human_approval
    events = _emit_event(
        state,
        "GUARDRAIL_CHECKED",
        {"decision": result.decision.value, "approval_required": approval_required, "blocked": result.blocked},
    )
    update: Dict[str, Any] = {
        "guardrail_findings": result.messages(),
        "approval_required": approval_required,
        "events": events,
    }
    if result.blocked:
        update["error"] = "blocked_by_guardrail"
        update["final_response"] = "Blocked by SellerOS governance guardrails: " + "; ".join(result.blocking_messages())
    return update


def approval_node(state: SellerOSState) -> Dict[str, Any]:
    if state.get("approval_granted") is True:
        events = _emit_event(state, "HUMAN_APPROVAL_GRANTED", {})
        return {"final_response": (state.get("final_response") or "") + " [Approved by Human]", "events": events}
    if state.get("approval_granted") is False:
        events = _emit_event(state, "HUMAN_APPROVAL_REJECTED", {})
        return {"final_response": "Rejected by human reviewer.", "error": "approval_rejected", "events": events}
    return {"final_response": "Waiting for human approval before proceeding."}


def publish_node(state: SellerOSState) -> Dict[str, Any]:
    if state.get("error") == "blocked_by_guardrail":
        return {"published_status": "REFUSED", "final_response": state.get("final_response")}
    if state.get("approval_required") and state.get("approval_granted") is not True:
        return {"published_status": "REFUSED", "final_response": "Refused to publish: required approval missing."}

    payload = {
        "marketplace": state.get("marketplace"),
        "intent": state.get("intent"),
        "payload": state.get("tool_results"),
    }
    events = _emit_event(state, "PUBLISHED_TO_CONNECTORS", {"marketplace": state.get("marketplace")})
    return {
        "published_payload": payload,
        "published_status": "SUCCESS",
        "final_response": (state.get("final_response") or "") + " [Published to Marketplace Connector]",
        "events": events,
    }


# =============================================================================
# 5. GRAPH COMPOSITION & WIRING
# =============================================================================

def get_checkpointer():
    pg_uri = os.getenv("POSTGRES_CHECKPOINT_URL")
    if pg_uri and PostgresSaver:
        return PostgresSaver.from_conn_string(pg_uri)
    return MemorySaver()


def build_graph():
    graph = StateGraph(SellerOSState)

    # 1. Register All Nodes
    graph.add_node("context_assembly", context_assembly_node)
    graph.add_node("memory_layer", memory_layer_node)
    graph.add_node("router", router_node)
    graph.add_node("supervisor", supervisor_node)

    graph.add_node("listing", listing_node)
    graph.add_node("pricing", pricing_node)
    graph.add_node("inventory", inventory_node)
    graph.add_node("order", order_node)
    graph.add_node("analytics", analytics_node)
    graph.add_node("forecasting", forecasting_node)
    graph.add_node("profitability", profitability_node)
    graph.add_node("competitor", competitor_node)
    graph.add_node("campaign", campaign_node)
    graph.add_node("ads", ads_node)
    graph.add_node("seo", seo_node)
    graph.add_node("content", content_node)
    graph.add_node("seller_coach", seller_coach_node)
    graph.add_node("sustainability", sustainability_node)

    graph.add_node("recovery", recovery_node)
    graph.add_node("guardrail", guardrail_node)  # Matching node name
    graph.add_node("approval", approval_node)
    graph.add_node("publish", publish_node)

    # 2. Sequential Entry Pipeline: User -> Context -> Memory -> Router -> Supervisor
    #    (no "executive" step — see module docstring: ExecutiveAgent doesn't
    #    exist, and planning now happens one level up, in supervisor.py)
    graph.set_entry_point("context_assembly")
    graph.add_edge("context_assembly", "memory_layer")
    graph.add_edge("memory_layer", "router")
    graph.add_edge("router", "supervisor")

    # 3. Supervisor Dynamic Routing
    graph.add_conditional_edges(
        "supervisor",
        supervisor_route,
        {
            "listing": "listing",
            "pricing": "pricing",
            "inventory": "inventory",
            "order": "order",
            "analytics": "analytics",
            "forecasting": "forecasting",
            "profitability": "profitability",
            "competitor": "competitor",
            "campaign": "campaign",
            "ads": "ads",
            "seo": "seo",
            "content": "content",
            "seller_coach": "seller_coach",
            "sustainability": "sustainability",
            "finish": "guardrail",
        },
    )

    # 4. Conditional Branching Between Worker Nodes
    graph.add_conditional_edges(
        "listing",
        needs_pricing,
        {"pricing": "pricing", "skip_pricing": "guardrail"},
    )
    graph.add_edge("pricing", "guardrail")

    # 5. Retry / Recovery Edges for Worker Agents
    for agent_node in [
        "inventory", "order", "ads", "seller_coach", "sustainability",
        "analytics", "forecasting", "profitability", "competitor",
        "campaign", "seo", "content",
    ]:
        graph.add_conditional_edges(
            agent_node,
            check_retry_or_recover,
            {"continue": "guardrail", "retry": agent_node, "recover": "recovery"},
        )

    graph.add_edge("recovery", END)

    # 6. Guardrail -> Approval Checkpoint -> Connector Handoff -> END
    graph.add_conditional_edges(
        "guardrail",
        needs_approval,
        {"approval": "approval", "skip_approval": "publish", "blocked": END},
    )
    graph.add_conditional_edges(
        "approval",
        should_publish,
        {"publish": "publish", "halt": END},
    )
    graph.add_edge("publish", END)

    checkpointer = get_checkpointer()
    return graph.compile(checkpointer=checkpointer, interrupt_before=["approval"])


sellerOS_graph = build_graph()


async def run_workflow(
    query: str,
    seller_id: str = "default_seller",
    marketplace: Optional[str] = None,
    session_id: Optional[str] = None,
    plan: Optional[List[Any]] = None,
    thread_id: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Entry point for a brand-new run (as opposed to `resume_workflow`,
    which continues one paused at the human-approval checkpoint).
    `thread_id` defaults to `session_id` (or `seller_id` if there's no
    session) so a given conversation's checkpoints are addressable
    later for `resume_workflow`.
    """
    state = new_state(query, seller_id=seller_id, marketplace=marketplace, session_id=session_id, plan=plan)
    config = {"configurable": {"thread_id": thread_id or session_id or seller_id}}
    return await sellerOS_graph.ainvoke(state, config=config)


async def resume_workflow(
    thread_id: str, approval_granted: bool, updated_context: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    config = {"configurable": {"thread_id": thread_id}}
    resume_state: Dict[str, Any] = {"approval_granted": approval_granted}
    if updated_context:
        resume_state["context"] = updated_context

    await sellerOS_graph.aupdate_state(config, resume_state)
    return await sellerOS_graph.ainvoke(None, config=config)
