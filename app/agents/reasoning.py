import json
from typing import Dict, Any, List
from datetime import datetime

from app.agents.base import BaseAgent
from app.llm.ollama import OllamaClient
from app.embeddings import EmbeddingService
from app.utils.logger import get_logger

logger = get_logger(__name__)

class ReasoningAgent(BaseAgent):
    """Reasoning Agent - Analyzes data using LLM"""
    
    def __init__(self):
        super().__init__()
        self.llm = OllamaClient()
        self.embedding_service = EmbeddingService()

    def execute(self, data: Dict[str, Any], **kwargs) -> Dict[str, Any]:
        """Analyze collected data and generate report"""
        logger.info("ReasoningAgent: Analyzing data...")
        
        thoughts = []
        analysis_result = {}
        
        try:
            raw_data = data.get("data", [])
            query = data.get("metadata", {}).get("query", "Unknown query")
            
            if not raw_data:
                return {
                    "status": "error",
                    "error": "No data to analyze",
                    "thoughts": ["❌ No data received from Radar"]
                }
            
            thoughts.append(f"📊 Analyzing {len(raw_data)} results for: {query}")
            
            analysis_input = self._prepare_analysis_input(raw_data, query)
            thoughts.append("🧠 Sending to LLM for analysis...")
            llm_analysis = self._get_llm_analysis(analysis_input)
            
            analysis_result = self._structure_report(raw_data, llm_analysis, query)
            thoughts.append("✅ Analysis completed successfully")
            
            return {
                "status": "success",
                "analysis": analysis_result,
                "thoughts": thoughts,
                "metadata": {
                    "timestamp": datetime.now().isoformat(),
                    "data_points": len(raw_data),
                    "model": self.llm.get_model_name()
                }
            }
            
        except Exception as e:
            logger.error(f"ReasoningAgent error: {str(e)}")
            return {
                "status": "error",
                "error": str(e),
                "thoughts": thoughts + [f"❌ Error: {str(e)}"]
            }

    def _prepare_analysis_input(self, data: List[Dict], query: str) -> str:
        """Format data for LLM analysis"""
        input_text = f"Analyze the following search results for the query: '{query}'\n\n"
        for i, item in enumerate(data[:5], 1):
            input_text += f"\n{i}. Title: {item.get('title', '')}\n"
            input_text += f"   URL: {item.get('url', '')}\n"
            input_text += f"   Description: {item.get('description', '')[:200]}...\n"
        
        input_text += "\nProvide a structured analysis covering:\n"
        input_text += "- Key themes and topics found\n"
        input_text += "- Competitor mentions\n"
        input_text += "- Market trends or gaps identified\n"
        input_text += "- Strategic recommendations\n"
        return input_text

    def _get_llm_analysis(self, prompt: str) -> str:
        """Get analysis from Ollama/Qwen3"""
        try:
            response = self.llm.generate(prompt)
            return response
        except Exception as e:
            logger.warning(f"LLM call failed: {e}")
            return self._get_fallback_analysis(prompt)

    def _get_fallback_analysis(self, prompt: str) -> str:
        """Fallback analysis when LLM is unavailable"""
        return """
        COMPETITIVE INTELLIGENCE REPORT (FALLBACK)
        
        Based on the search results, here are key observations:
        
        1. Market Landscape: 
           - Several competitors are active in this space
           - Search results show ongoing market activity
        
        2. Recommendations:
           - Monitor top competitors closely
           - Focus on differentiating your brand positioning
           - Create content that addresses customer pain points
        
        Note: This is a fallback analysis. For full AI-powered insights, ensure Ollama is running.
        """

    def _structure_report(self, raw_data: List[Dict], analysis: str, query: str) -> Dict:
        """Structure analysis into a report"""
        return {
            "query": query,
            "summary": analysis[:500] + "..." if len(analysis) > 500 else analysis,
            "full_analysis": analysis,
            "key_findings": [
                "✅ Market intelligence gathered successfully",
                f"📊 Analyzed {len(raw_data)} search results",
                "💡 Strategic recommendations available above"
            ],
            "data_points": len(raw_data),
            "next_steps": [
                "Deep dive into top competitors",
                "Identify content gaps",
                "Develop positioning strategy"
            ]
        }
