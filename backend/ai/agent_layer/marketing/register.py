"""Domain self-registration for marketing — see
agent_layer/registry/agent_registry.py.

Tier 3 complete: AdsAgent, CampaignAgent, SEOAgent, ContentAgent. Same
standard as every other domain — AdsAgent wraps the real AdsTool with
an explicit separate create_campaign()/delete_campaign() write path;
CampaignAgent is deliberately read-only (plans, doesn't execute — see
its module docstring); SEOAgent and ContentAgent both wrap
ListingTool/KnowledgeTool with their own explicit separate write
methods, honest that no keyword-research or ranking data exists to
back their suggestions with real numbers.
"""
from __future__ import annotations

from ai.agent_layer.registry.agent_registry import AgentRegistry
from ai.agent_layer.marketing.ads_agent import AdsAgent
from ai.agent_layer.marketing.campaign_agent import CampaignAgent
from ai.agent_layer.marketing.seo_agent import SEOAgent
from ai.agent_layer.marketing.content_agent import ContentAgent


def register(registry: AgentRegistry, reasoner) -> None:
    registry.register("ads", AdsAgent(reasoner), domain="marketing")
    registry.register("campaign", CampaignAgent(reasoner), domain="marketing")
    registry.register("seo", SEOAgent(reasoner), domain="marketing")
    registry.register("content", ContentAgent(reasoner), domain="marketing")
