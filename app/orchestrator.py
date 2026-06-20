from typing import Dict, Any
import json
from datetime import datetime

from app.agents.radar import RadarAgent
from app.agents.vault import VaultAgent
from app.agents.reasoning import ReasoningAgent
from app.utils.logger import get_logger

logger = get_logger(__name__)

class Orchestrator:
    """Main orchestrator coordinating all agents"""
    
    def __init__(self):
        self.radar = RadarAgent()
        self.vault = VaultAgent()
        self.reasoning = ReasoningAgent()

    def execute_intelligence_cycle(self, query: str, workspace_id: int, user_id: int) -> Dict[str, Any]:
        """Execute full intelligence cycle"""
        logger.info(f"Starting intelligence cycle for: {query}")
        
        all_thoughts = []
        
        # STEP 1: RADAR
        logger.info("Step 1: Running Radar...")
        radar_result = self.radar.execute(query)
        all_thoughts.extend(radar_result.get("thoughts", []))
        
        if radar_result.get("status") != "success":
            return {
                "status": "error",
                "error": "Radar failed",
                "thoughts": all_thoughts,
                "final_report": {}
            }
        
        # STEP 2: VAULT - Retrieve old data
        logger.info("Step 2: Checking Vault...")
        vault_result = self.vault.retrieve(query, workspace_id)
        all_thoughts.extend(vault_result.get("thoughts", []))
        
        # STEP 3: REASONING
        logger.info("Step 3: Running Reasoning...")
        reasoning_input = {
            "data": radar_result.get("data", []),
            "metadata": {
                "query": query,
                "vault_results": vault_result.get("results", []),
                "workspace_id": workspace_id
            }
        }
        reasoning_result = self.reasoning.execute(reasoning_input)
        all_thoughts.extend(reasoning_result.get("thoughts", []))
        
        # STEP 4: VAULT - Store new data
        logger.info("Step 4: Storing to Vault...")
        for item in radar_result.get("data", [])[:3]:
            self.vault.store(item, workspace_id)
        
        final_report = {
            "query": query,
            "timestamp": datetime.now().isoformat(),
            "radar_summary": {
                "total_results": len(radar_result.get("data", [])),
                "top_results": radar_result.get("data", [])[:5]
            },
            "analysis": reasoning_result.get("analysis", {}),
            "thoughts": all_thoughts,
            "status": "success"
        }
        
        return final_report
