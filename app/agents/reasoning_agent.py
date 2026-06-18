"""
Reasoning Agent - Causal Analysis and Logical Reasoning

Performs multi-step reasoning, causal analysis, and logical inference.
"""

import logging
from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass
from datetime import datetime
from enum import Enum

logger = logging.getLogger(__name__)


class ReasoningType(str, Enum):
    """Types of reasoning."""
    DEDUCTIVE = "deductive"
    INDUCTIVE = "inductive"
    ABDUCTIVE = "abductive"
    CAUSAL = "causal"
    ANALOGICAL = "analogical"


@dataclass
class ReasoningStep:
    """Single step in reasoning chain."""
    step_number: int
    reasoning_type: ReasoningType
    premise: str
    conclusion: str
    confidence: float
    evidence: List[str]
    created_at: datetime = None
    
    def __post_init__(self):
        if self.created_at is None:
            self.created_at = datetime.utcnow()


class ReasoningAgent:
    """
    Reasoning Agent - Causal Analysis and Logical Reasoning
    
    Capabilities:
    - Multi-step logical reasoning
    - Causal inference
    - Hypothesis generation
    - Evidence evaluation
    - Confidence scoring
    - Reasoning chain visualization
    """
    
    def __init__(self, db_session=None, llm_client=None):
        """
        Initialize Reasoning Agent.
        
        Args:
            db_session: SQLAlchemy database session
            llm_client: Ollama client
        """
        self.db_session = db_session
        from app.services.llm_service import get_llm_client
        self.llm_client = llm_client or get_llm_client()
        self.reasoning_chain = []
        self.hypotheses = []
    
    async def analyze_causality(
        self,
        effect: str,
        context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Analyze causal relationships.
        
        Args:
            effect: The observed effect
            context: Context information
            
        Returns:
            Causal analysis result
        """
        logger.info(f"Analyzing causality for effect: {effect}")
        
        self.reasoning_chain = []
        self.hypotheses = []
        
        # Step 1: Identify potential causes
        potential_causes = await self._identify_potential_causes(effect, context)
        
        # Step 2: Evaluate each cause
        cause_scores = await self._evaluate_causes(potential_causes, effect, context)
        
        # Step 3: Rank causes by likelihood
        ranked_causes = sorted(cause_scores.items(), key=lambda x: x[1], reverse=True)
        
        # Step 4: Build causal chain
        causal_chain = await self._build_causal_chain(ranked_causes, context)
        
        result = {
            "effect": effect,
            "potential_causes": [c[0] for c in ranked_causes],
            "cause_scores": {c[0]: c[1] for c in ranked_causes},
            "causal_chain": causal_chain,
            "reasoning_steps": [
                {
                    "step": s.step_number,
                    "type": s.reasoning_type.value,
                    "premise": s.premise,
                    "conclusion": s.conclusion,
                    "confidence": s.confidence
                }
                for s in self.reasoning_chain
            ],
            "confidence": self._calculate_overall_confidence()
        }
        
        logger.info(f"Causality analysis complete: {len(ranked_causes)} causes identified")
        
        return result
    
    async def _identify_potential_causes(
        self,
        effect: str,
        context: Dict[str, Any]
    ) -> List[str]:
        """
        Identify potential causes for an effect.
        
        Args:
            effect: The observed effect
            context: Context information
            
        Returns:
            List of potential causes
        """
        logger.info(f"Identifying potential causes for: {effect}")
        
        fallback_causes = [
            "Market competition",
            "Technology disruption",
            "Regulatory changes",
            "Consumer behavior shift",
            "Supply chain disruption"
        ]
        
        # Add context-specific causes
        if "market" in effect.lower():
            fallback_causes.append("Market saturation")
        
        if "revenue" in effect.lower():
            fallback_causes.extend(["Pricing pressure", "Customer churn"])
            
        try:
            if await self.llm_client.is_healthy():
                prompt = (
                    f"Identify potential causes for the following business effect: '{effect}'. "
                    f"Industry context: '{context.get('industry', 'unknown')}'. "
                    f"Recent events: {context.get('recent_events', [])}. "
                    f"Return a list of causes separated by newlines."
                )
                response = await self.llm_client.generate(
                    prompt=prompt,
                    system="You are a business intelligence analyst. Identify logical potential causes for the given business effect. Return only a list of causes, one per line."
                )
                if "response" in response:
                    lines = [line.strip() for line in response["response"].split("\n") if line.strip()]
                    cleaned_lines = []
                    for line in lines:
                        cleaned = line.lstrip("0123456789.-*• ").strip()
                        if cleaned:
                            cleaned_lines.append(cleaned)
                    if cleaned_lines:
                        logger.info(f"Identified {len(cleaned_lines)} causes via LLM")
                        return cleaned_lines
        except Exception as e:
            logger.warning(f"Ollama causality analysis failed, falling back to static causes: {e}")
        
        logger.info(f"Identified {len(fallback_causes)} potential causes (fallback)")
        
        return fallback_causes
    
    async def _evaluate_causes(
        self,
        causes: List[str],
        effect: str,
        context: Dict[str, Any]
    ) -> Dict[str, float]:
        """
        Evaluate likelihood of each cause.
        
        Args:
            causes: List of potential causes
            effect: The observed effect
            context: Context information
            
        Returns:
            Dictionary of cause -> likelihood score
        """
        logger.info(f"Evaluating {len(causes)} potential causes")
        
        scores = {}
        
        for cause in causes:
            # Placeholder: In production, this would use ML model or domain knowledge
            base_score = 0.5
            
            # Adjust based on context
            if context.get("industry") == "tech":
                if "technology" in cause.lower():
                    base_score += 0.2
            
            if context.get("recent_events"):
                if any(event.lower() in cause.lower() for event in context["recent_events"]):
                    base_score += 0.15
            
            scores[cause] = min(base_score, 1.0)
            
            # Add reasoning step
            step = ReasoningStep(
                step_number=len(self.reasoning_chain) + 1,
                reasoning_type=ReasoningType.CAUSAL,
                premise=f"Evaluating cause: {cause}",
                conclusion=f"Likelihood score: {scores[cause]:.2f}",
                confidence=0.8,
                evidence=[effect, cause]
            )
            self.reasoning_chain.append(step)
        
        return scores
    
    async def _build_causal_chain(
        self,
        ranked_causes: List[Tuple[str, float]],
        context: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """
        Build causal chain from ranked causes.
        
        Args:
            ranked_causes: Ranked list of (cause, score) tuples
            context: Context information
            
        Returns:
            Causal chain
        """
        logger.info(f"Building causal chain from {len(ranked_causes)} causes")
        
        chain = []
        
        for idx, (cause, score) in enumerate(ranked_causes[:3]):  # Top 3 causes
            chain_link = {
                "position": idx + 1,
                "cause": cause,
                "likelihood": score,
                "supporting_factors": await self._find_supporting_factors(cause, context),
                "counter_factors": await self._find_counter_factors(cause, context)
            }
            chain.append(chain_link)
        
        return chain
    
    async def _find_supporting_factors(
        self,
        cause: str,
        context: Dict[str, Any]
    ) -> List[str]:
        """Find factors supporting a cause."""
        # Placeholder implementation
        return [f"Factor supporting {cause}"]
    
    async def _find_counter_factors(
        self,
        cause: str,
        context: Dict[str, Any]
    ) -> List[str]:
        """Find factors countering a cause."""
        # Placeholder implementation
        return [f"Factor countering {cause}"]
    
    def _calculate_overall_confidence(self) -> float:
        """Calculate overall confidence of reasoning."""
        if not self.reasoning_chain:
            return 0.0
        
        avg_confidence = sum(s.confidence for s in self.reasoning_chain) / len(self.reasoning_chain)
        return avg_confidence
    
    async def generate_hypotheses(
        self,
        observations: List[str],
        context: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """
        Generate hypotheses from observations.
        
        Args:
            observations: List of observations
            context: Context information
            
        Returns:
            List of hypotheses
        """
        logger.info(f"Generating hypotheses from {len(observations)} observations")
        
        self.hypotheses = []
        
        for idx, observation in enumerate(observations):
            hypothesis = {
                "id": f"hyp-{idx}",
                "observation": observation,
                "hypothesis": f"Hypothesis for: {observation}",
                "testability": "high",
                "confidence": 0.7,
                "supporting_evidence": [],
                "counter_evidence": []
            }
            self.hypotheses.append(hypothesis)
        
        logger.info(f"Generated {len(self.hypotheses)} hypotheses")
        
        return self.hypotheses
    
    async def evaluate_evidence(
        self,
        hypothesis: str,
        evidence_items: List[str]
    ) -> Dict[str, Any]:
        """
        Evaluate evidence for a hypothesis.
        
        Args:
            hypothesis: The hypothesis to evaluate
            evidence_items: List of evidence items
            
        Returns:
            Evidence evaluation result
        """
        logger.info(f"Evaluating {len(evidence_items)} evidence items for hypothesis: {hypothesis}")
        
        supporting = []
        contradicting = []
        neutral = []
        
        for evidence in evidence_items:
            # Placeholder: In production, this would use semantic analysis
            if "support" in evidence.lower():
                supporting.append(evidence)
            elif "contradict" in evidence.lower():
                contradicting.append(evidence)
            else:
                neutral.append(evidence)
        
        # Calculate support score
        support_score = len(supporting) / len(evidence_items) if evidence_items else 0.0
        
        result = {
            "hypothesis": hypothesis,
            "total_evidence": len(evidence_items),
            "supporting": len(supporting),
            "contradicting": len(contradicting),
            "neutral": len(neutral),
            "support_score": support_score,
            "confidence": support_score * 0.9 + 0.1  # Confidence based on support
        }
        
        logger.info(f"Evidence evaluation: support_score={support_score:.2f}")
        
        return result
    
    async def reason_about_query(
        self,
        query: str,
        context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Perform multi-step reasoning about a query.
        
        Args:
            query: The query to reason about
            context: Context information
            
        Returns:
            Reasoning result
        """
        logger.info(f"Reasoning about query: {query}")
        
        self.reasoning_chain = []
        
        # Step 1: Identify key concepts
        concepts = await self._identify_concepts(query)
        
        # Step 2: Analyze relationships
        relationships = await self._analyze_relationships(concepts, context)
        
        # Step 3: Draw conclusions
        conclusions = await self._draw_conclusions(relationships, context)
        
        result = {
            "query": query,
            "concepts": concepts,
            "relationships": relationships,
            "conclusions": conclusions,
            "reasoning_chain": [
                {
                    "step": s.step_number,
                    "type": s.reasoning_type.value,
                    "premise": s.premise,
                    "conclusion": s.conclusion,
                    "confidence": s.confidence
                }
                for s in self.reasoning_chain
            ],
            "overall_confidence": self._calculate_overall_confidence()
        }
        
        logger.info(f"Reasoning complete: {len(conclusions)} conclusions")
        
        return result
    
    async def _identify_concepts(self, query: str) -> List[str]:
        """Identify key concepts in query."""
        # Placeholder implementation
        return query.split()[:5]
    
    async def _analyze_relationships(
        self,
        concepts: List[str],
        context: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """Analyze relationships between concepts."""
        # Placeholder implementation
        return [{"concept1": concepts[0], "concept2": concepts[1], "relationship": "related"}]
    
    async def _draw_conclusions(
        self,
        relationships: List[Dict[str, Any]],
        context: Dict[str, Any]
    ) -> List[str]:
        """Draw conclusions from relationships."""
        # Placeholder implementation
        return ["Conclusion 1", "Conclusion 2"]


# Convenience function
async def reason_about_query(
    query: str,
    context: Dict[str, Any],
    db_session=None
) -> Dict[str, Any]:
    """
    Perform reasoning about a query.
    
    Args:
        query: The query
        context: Context information
        db_session: Database session
        
    Returns:
        Reasoning result
    """
    agent = ReasoningAgent(db_session)
    return await agent.reason_about_query(query, context)
