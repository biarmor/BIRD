"""
Radar Agent - Web Intelligence Gathering

Queries intelligence from web sources, analyzes competitor updates, and ingests findings.
"""

import logging
from typing import List, Dict, Any, Optional
from datetime import datetime
from app.agents.vault_agent import VaultAgent

logger = logging.getLogger(__name__)


class RadarAgent:
    """
    Radar Agent - Web Intelligence Gathering

    Responsibilities:
    - Query market/competitor intelligence from web sources (simulated/mocked search).
    - Automatically ingest intelligence findings as facts into the VaultAgent.
    """

    def __init__(self, db_session=None, vault_agent: Optional[VaultAgent] = None):
        """
        Initialize Radar Agent.

        Args:
            db_session: SQLAlchemy database session
            vault_agent: VaultAgent instance
        """
        self.db_session = db_session
        self.vault_agent = vault_agent or VaultAgent(db_session=db_session)

    async def fetch_intel(self, query: str, workspace_id: str) -> List[Dict[str, Any]]:
        """
        Fetch market/competitor intelligence based on a search query.

        Args:
            query: The search query
            workspace_id: The workspace ID context

        Returns:
            List of intelligence items
        """
        logger.info(f"Fetching intelligence for query: '{query}' in workspace {workspace_id}")

        # Simulated intelligence database/responses based on keywords in the query
        query_lower = query.lower()
        simulated_results = []

        if any(w in query_lower for w in ["pricing", "cost", "price"]):
            simulated_results = [
                {
                    "title": "Competitor pricing changes",
                    "snippet": "Competitor X launched a new Tiered pricing plan: Starter at $29/mo, Pro at $99/mo, and Enterprise custom options.",
                    "source": "https://competitor-x.com/pricing",
                    "category": "competitor_pricing",
                    "extracted_at": datetime.utcnow().isoformat()
                },
                {
                    "title": "SaaS industry pricing report",
                    "snippet": "Average seat pricing for business intelligence platform features in 2026 has increased by 12% year-over-year.",
                    "source": "https://industry-insights.org/pricing-trends-2026",
                    "category": "market_pricing",
                    "extracted_at": datetime.utcnow().isoformat()
                }
            ]
        elif any(w in query_lower for w in ["feature", "roadmap", "release", "launch"]):
            simulated_results = [
                {
                    "title": "Competitor Y product roadmap update",
                    "snippet": "Competitor Y announced they will release their real-time vector retrieval analytics feature by Q3 2026.",
                    "source": "https://competitor-y.com/blog/roadmap-2026",
                    "category": "competitor_product",
                    "extracted_at": datetime.utcnow().isoformat()
                },
                {
                    "title": "Press release: Competitor X launches AI Assistant",
                    "snippet": "Competitor X has integrated a conversational assistant utilizing local models into their analytics suite.",
                    "source": "https://competitor-x.com/press/ai-assistant",
                    "category": "competitor_product",
                    "extracted_at": datetime.utcnow().isoformat()
                }
            ]
        else:
            # General intelligence fallback
            simulated_results = [
                {
                    "title": "General market trend intelligence",
                    "snippet": f"Market search query '{query}' shows strong customer interest in local-first LLMs and vector persistence.",
                    "source": "https://techtrends.net/local-rag-growth",
                    "category": "market_trends",
                    "extracted_at": datetime.utcnow().isoformat()
                }
            ]

        logger.info(f"Fetched {len(simulated_results)} intelligence items")
        return simulated_results

    async def ingest_intel(self, intel: List[Dict[str, Any]], workspace_id: str) -> List[Dict[str, Any]]:
        """
        Automatically ingest intelligence findings into the VaultAgent.

        Args:
            intel: List of intelligence dictionary objects
            workspace_id: The workspace ID context

        Returns:
            List of facts ingested into the vault
        """
        logger.info(f"Ingesting {len(intel)} intelligence items into vault for workspace {workspace_id}")
        ingested_facts = []

        for item in intel:
            fact_text = f"[{item['title']}] {item['snippet']} (Source: {item['source']})"
            category = item.get("category", "market_intel")
            
            # Use VaultAgent to add/ingest the fact
            fact = await self.vault_agent.add_fact(
                fact=fact_text,
                category=category,
                workspace_id=workspace_id
            )
            
            ingested_facts.append({
                "fact_id": fact.id,
                "fact": fact.fact,
                "category": fact.category,
                "workspace_id": fact.workspace_id,
                "created_at": fact.created_at.isoformat() if fact.created_at else datetime.utcnow().isoformat()
            })

        logger.info(f"Successfully ingested {len(ingested_facts)} facts into vault")
        return ingested_facts


# Convenience function
async def fetch_and_ingest_intel(
    query: str,
    workspace_id: str,
    db_session=None,
    vault_agent=None
) -> List[Dict[str, Any]]:
    """Convenience function to run the full intelligence loop."""
    agent = RadarAgent(db_session=db_session, vault_agent=vault_agent)
    intel = await agent.fetch_intel(query, workspace_id)
    return await agent.ingest_intel(intel, workspace_id)
