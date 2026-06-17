"""BIRD Backend Agents Package

Multi-agent system components:
- Vault Agent: Smart memory with Agentic RAG
- Orchestrator Agent: Multi-agent coordination
- Reasoning Agent: Causal analysis and reasoning
- Debate Agent: Multi-perspective validation
- Adaptive Planning Agent: Dynamic task scheduling
- RAR Agent: Retrieval-Augmented Reasoning
- Forge Agent: Asset and content generation
- Attack Agent: Campaign deployment and execution
- Radar Agent: Web intelligence gathering (Phase 2)
"""

from app.agents.vault_agent import VaultAgent, query_vault_facts
from app.agents.orchestrator_agent import OrchestratorAgent, orchestrate_query
from app.agents.reasoning_agent import ReasoningAgent, reason_about_query
from app.agents.debate_agent import DebateAgent, debate_conclusion
from app.agents.adaptive_planning_agent import AdaptivePlanningAgent, create_and_execute_plan
from app.agents.rar_agent import RARAgent, reason_with_retrieval
from app.agents.forge_agent import ForgeAgent, generate_marketing_asset
from app.agents.attack_agent import AttackAgent, deploy_marketing_campaign

__all__ = [
    "VaultAgent", "query_vault_facts",
    "OrchestratorAgent", "orchestrate_query",
    "ReasoningAgent", "reason_about_query",
    "DebateAgent", "debate_conclusion",
    "AdaptivePlanningAgent", "create_and_execute_plan",
    "RARAgent", "reason_with_retrieval",
    "ForgeAgent", "generate_marketing_asset",
    "AttackAgent", "deploy_marketing_campaign"
]
