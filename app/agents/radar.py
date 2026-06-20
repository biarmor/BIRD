import json
import time
import random
from typing import Dict, Any, List
from datetime import datetime
from duckduckgo_search import DDGS

from app.agents.base import BaseAgent
from app.utils.logger import get_logger

logger = get_logger(__name__)

class RadarAgent(BaseAgent):
    """Radar Agent - Collects market intelligence using DuckDuckGo"""
    
    def __init__(self):
        super().__init__()
        self.ddgs = DDGS()
        self.max_results = 10

    def execute(self, query: str, **kwargs) -> Dict[str, Any]:
        """Main execution - search and return results"""
        logger.info(f"RadarAgent: Processing query: {query}")
        
        try:
            search_results = self._search(query)
            formatted_results = self._format_results(search_results)
            
            metadata = {
                "query": query,
                "timestamp": datetime.now().isoformat(),
                "source": "duckduckgo",
                "total_results": len(formatted_results)
            }
            
            return {
                "status": "success",
                "data": formatted_results,
                "metadata": metadata,
                "thoughts": [
                    f"🔍 Searching DuckDuckGo for: {query}",
                    f"📊 Found {len(formatted_results)} relevant results",
                    f"⏱️ Completed at {datetime.now().strftime('%H:%M:%S')}"
                ]
            }
            
        except Exception as e:
            logger.error(f"RadarAgent error: {str(e)}")
            return {
                "status": "error",
                "error": str(e),
                "data": [],
                "thoughts": [f"❌ Error: {str(e)}"]
            }

    def _search(self, query: str) -> List[Dict]:
        """Search DuckDuckGo and return results"""
        results = []
        try:
            for result in self.ddgs.text(query, max_results=self.max_results):
                results.append({
                    "title": result.get("title", ""),
                    "link": result.get("href", ""),
                    "snippet": result.get("body", ""),
                    "source": result.get("source", "duckduckgo")
                })
                time.sleep(random.uniform(0.3, 0.7))
        except Exception as e:
            logger.warning(f"DDGS search failed: {e}")
            results = self._get_demo_results(query)
        return results

    def _format_results(self, results: List[Dict]) -> List[Dict]:
        """Format results for analysis"""
        formatted = []
        for r in results:
            formatted.append({
                "title": r.get("title", "").strip(),
                "url": r.get("link", r.get("url", "")),
                "description": r.get("snippet", r.get("description", "")),
                "source": r.get("source", "web"),
                "relevance_score": self._calculate_relevance(r)
            })
        return formatted

    def _calculate_relevance(self, result: Dict) -> float:
        """Calculate relevance score"""
        title_len = len(result.get("title", ""))
        desc_len = len(result.get("snippet", ""))
        score = min(1.0, (title_len / 50) * 0.5 + (desc_len / 200) * 0.5)
        return round(score, 2)

    def _get_demo_results(self, query: str) -> List[Dict]:
        """Fallback demo results when search fails"""
        return [
            {
                "title": f"Top results for '{query}' - Example 1",
                "link": "https://example.com/1",
                "snippet": "This is a sample result. In production, DuckDuckGo search will provide real data.",
                "source": "demo"
            },
            {
                "title": f"About '{query}' - Example 2",
                "link": "https://example.com/2",
                "snippet": "Another sample result. Replace with actual search results.",
                "source": "demo"
            }
        ]
