# -*- coding: utf-8 -*-
"""
Decision Engine for AutoGen Multi-Agent Consensus

This module implements sophisticated consensus algorithms and decision-making
logic for multi-agent AutoGen conversations in flash loan arbitrage.
"""

from collections import defaultdict
from datetime import datetime
from typing import Dict, List, Any, Optional
import logging
import re
import statistics

from dataclasses import dataclass, field
from enum import Enum


logger = logging.getLogger(__name__)


class ConsensusAlgorithm(Enum):
    """Available consensus algorithms"""
    MAJORITY_CONSENSUS = "majority_consensus"
    WEIGHTED_CONSENSUS = "weighted_consensus"
    UNANIMOUS_CONSENSUS = "unanimous_consensus"
    RISK_WEIGHTED_DECISION = "risk_weighted_decision"
    EXPERTISE_WEIGHTED = "expertise_weighted"
    CONFIDENCE_WEIGHTED = "confidence_weighted"
    HYBRID_CONSENSUS = "hybrid_consensus"


class DecisionConfidence(Enum):
    """Decision confidence levels"""
    VERY_LOW = "very_low"      # 0.0 - 0.2
    LOW = "low"                # 0.2 - 0.4  
    MEDIUM = "medium"          # 0.4 - 0.6
    HIGH = "high"              # 0.6 - 0.8
    VERY_HIGH = "very_high"    # 0.8 - 1.0


@dataclass
class AgentVote:
    """Individual agent vote and reasoning"""
    agent_name: str
    vote: bool  # True for approve, False for reject
    confidence: float  # 0.0 to 1.0
    reasoning: str
    risk_assessment: Optional[Dict[str, Any]] = None
    weight: float = 1.0
    expertise_areas: List[str] = field(default_factory=list)
    timestamp: datetime = field(default_factory=datetime.now)


@dataclass
class ConsensusResult:
    """Result of consensus algorithm"""
    approved: bool
    confidence: float
    algorithm_used: str
    vote_summary: Dict[str, Any]
    reasoning: str
    execution_plan: Dict[str, Any] = field(default_factory=dict)
    risk_factors: List[str] = field(default_factory=list)
    dissenting_opinions: List[str] = field(default_factory=list)
    quality_score: float = 0.0
    timestamp: datetime = field(default_factory=datetime.now)


@dataclass
class DecisionContext:
    """Context for decision making"""
    decision_type: str
    opportunity_data: Dict[str, Any]
    market_conditions: Dict[str, Any]
    risk_profile: Dict[str, Any]
    constraints: Dict[str, Any] = field(default_factory=dict)
    urgency_level: str = "normal"
    minimum_confidence: float = 0.6


class ConsensusDecisionEngine:
    """
    Advanced decision engine implementing multiple consensus algorithms
    for multi-agent AutoGen conversations.
    """
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.decision_config = config.get("conversation", {}).get("decision_algorithms", {})
        
        # Algorithm implementations
        self.consensus_algorithms = {
            ConsensusAlgorithm.MAJORITY_CONSENSUS: self._majority_consensus,
            ConsensusAlgorithm.WEIGHTED_CONSENSUS: self._weighted_consensus,
            ConsensusAlgorithm.UNANIMOUS_CONSENSUS: self._unanimous_consensus,
            ConsensusAlgorithm.RISK_WEIGHTED_DECISION: self._risk_weighted_decision,
            ConsensusAlgorithm.EXPERTISE_WEIGHTED: self._expertise_weighted_consensus,
            ConsensusAlgorithm.CONFIDENCE_WEIGHTED: self._confidence_weighted_consensus,
            ConsensusAlgorithm.HYBRID_CONSENSUS: self._hybrid_consensus

        
        # Agent role weights for different decision types
        self.role_weights = self._initialize_role_weights()
        
        # Decision quality thresholds
        self.quality_thresholds = {
            "minimum_participation": 0.8,  # 80% of agents must participate
            "minimum_confidence": 0.5,     # Minimum average confidence
            "maximum_disagreement": 0.3,   # Maximum acceptable disagreement ratio
            "reasoning_quality": 0.6       # Minimum reasoning quality score

        
        # Performance tracking
        self.decision_metrics = {
            "total_decisions": 0,
            "successful_decisions": 0,
            "high_confidence_decisions": 0,
            "unanimous_decisions": 0,
            "algorithm_usage": defaultdict(int),
            "average_confidence": 0.0,
            "average_decision_time": 0.0

        
        logger.info("[INIT] Consensus Decision Engine initialized")
    
    async def initialize(self):
        """Initialize the decision engine"""
        try:
            # Validate configuration
            await self._validate_decision_config()
            
            # Initialize NLP components for reasoning analysis
            await self._initialize_nlp_components()
            
            logger.info("[OK] Consensus Decision Engine ready")
            
        except Exception as e:
            logger.error(f"[ERROR] Decision Engine initialization failed: {e}")
            raise
    
    async def apply_consensus_algorithm(
        self,
        algorithm_name: str,
        conversation_history: List[Dict[str, Any]],
        context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Apply consensus algorithm to conversation history
        
        Args:
            algorithm_name: Name of consensus algorithm to use
            conversation_history: Complete conversation history
            context: Decision context and parameters
            
        Returns:
            Consensus result with decision and reasoning
        """
        start_time = datetime.now()
        
        try:
            # Parse conversation into agent votes
            agent_votes = await self._extract_agent_votes(conversation_history)
            
            if not agent_votes:
                return self._create_error_result("No agent votes found in conversation")
            
            # Validate vote quality
            quality_check = await self._validate_vote_quality(agent_votes, context)
            if not quality_check["valid"]:
                return self._create_error_result(f"Vote quality insufficient: {quality_check['reason']}")
            
            # Get consensus algorithm
            algorithm = ConsensusAlgorithm(algorithm_name)
            if algorithm not in self.consensus_algorithms:
                return self._create_error_result(f"Unknown consensus algorithm: {algorithm_name}")
            
            # Apply consensus algorithm
            consensus_func = self.consensus_algorithms[algorithm]
            result = await consensus_func(agent_votes, context)
            
            # Enhance result with additional analysis
            enhanced_result = await self._enhance_consensus_result(result, agent_votes, context)
            
            # Update metrics
            self._update_decision_metrics(enhanced_result, algorithm_name, start_time)
            
            logger.info(f"[CONSENSUS] {algorithm_name} completed - Decision: {enhanced_result.approved}")
            
            return self._serialize_consensus_result(enhanced_result)
            
        except Exception as e:
            logger.error(f"[ERROR] Consensus algorithm {algorithm_name} failed: {e}")
            return self._create_error_result(str(e))
    
    async def apply_risk_consensus(
        self,
        conversation_history: List[Dict[str, Any]],
        context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Apply risk-specific consensus algorithm
        
        Args:
            conversation_history: Risk assessment conversation
            context: Risk assessment context
            
        Returns:
            Risk consensus result
        """
        try:
            # Extract risk assessments from conversation
            risk_assessments = await self._extract_risk_assessments(conversation_history)
            
            # Apply risk-weighted consensus
            result = await self._risk_assessment_consensus(risk_assessments, context)
            
            return {
                "risk_level": result.get("risk_level", "medium"),
                "risk_score": result.get("risk_score", 0.5),
                "risk_factors": result.get("risk_factors", []),
                "mitigation_strategies": result.get("mitigation_strategies", []),
                "recommendation": result.get("recommendation", "proceed_with_caution"),
                "confidence": result.get("confidence", 0.6),
                "consensus_quality": result.get("quality_score", 0.7)

            
        except Exception as e:
            logger.error(f"[ERROR] Risk consensus failed: {e}")
            return {
                "risk_level": "high",
                "risk_score": 0.8,
                "recommendation": "do_not_proceed",
                "reason": f"Risk assessment failed: {e}"

    
    async def apply_execution_consensus(
        self,
        conversation_history: List[Dict[str, Any]],
        context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Apply execution-specific consensus algorithm
        
        Args:
            conversation_history: Execution planning conversation
            context: Execution context
            
        Returns:
            Execution consensus result
        """
        try:
            # Extract execution plans from conversation
            execution_plans = await self._extract_execution_plans(conversation_history)
            
            # Apply execution consensus
            result = await self._execution_planning_consensus(execution_plans, context)
            
            return {
                "execution_approved": result.get("approved", False),
                "optimal_plan": result.get("optimal_plan", {}),
                "execution_parameters": result.get("parameters", {}),
                "risk_mitigations": result.get("risk_mitigations", []),
                "monitoring_requirements": result.get("monitoring", []),
                "fallback_procedures": result.get("fallbacks", []),
                "confidence": result.get("confidence", 0.6),
                "estimated_success_rate": result.get("success_rate", 0.7)

            
        except Exception as e:
            logger.error(f"[ERROR] Execution consensus failed: {e}")
            return {
                "execution_approved": False,
                "reason": f"Execution planning failed: {e}"

    
    async def _extract_agent_votes(self, conversation_history: List[Dict[str, Any]]) -> List[AgentVote]:
        """Extract agent votes and reasoning from conversation history"""
        agent_votes = []
        
        for message in conversation_history:
            try:
                agent_name = message.get("name", "unknown")
                content = message.get("content", "")
                
                # Parse vote and reasoning from message content
                vote_info = await self._parse_vote_from_content(content)
                
                if vote_info:
                    agent_vote = AgentVote(
                        agent_name=agent_name,
                        vote=vote_info["vote"],
                        confidence=vote_info["confidence"],
                        reasoning=vote_info["reasoning"],
                        weight=self._get_agent_weight(agent_name),
                        expertise_areas=self._get_agent_expertise(agent_name)

                    agent_votes.append(agent_vote)
                    
            except Exception as e:
                logger.warning(f"[PARSE] Failed to parse vote from {message.get('name', 'unknown')}: {e}")
                continue
        
        return agent_votes
    
    async def _parse_vote_from_content(self, content: str) -> Optional[Dict[str, Any]]:
        """Parse vote, confidence, and reasoning from message content"""
        try:
            # Look for explicit vote indicators
            vote_patterns = [
                r"(?i)(approve|proceed|yes|go ahead|recommend|positive)",
                r"(?i)(reject|decline|no|stop|negative|against)"

            
            # Look for confidence indicators
            confidence_patterns = [
                r"confidence[:\s]*(\d+(?:\.\d+)?)[%]?",
                r"(\d+(?:\.\d+)?)[%]?\s*confident",
                r"certainty[:\s]*(\d+(?:\.\d+)?)[%]?"

            
            # Determine vote
            approve_match = re.search(vote_patterns[0], content)
            reject_match = re.search(vote_patterns[1], content)
            
            if approve_match and not reject_match:
                vote = True
            elif reject_match and not approve_match:
                vote = False
            elif approve_match and reject_match:
                # Both found, use context to determine
                vote = await self._resolve_ambiguous_vote(content)
            else:
                # No explicit vote found, try sentiment analysis
                vote = await self._infer_vote_from_sentiment(content)
            
            # Extract confidence
            confidence = 0.5  # Default
            for pattern in confidence_patterns:
                match = re.search(pattern, content, re.IGNORECASE)
                if match:
                    conf_value = float(match.group(1))
                    confidence = conf_value / 100 if conf_value > 1 else conf_value
                    break
            
            # Extract reasoning (simplified)
            reasoning = content[:500]  # First 500 chars as reasoning
            
            return {
                "vote": vote,
                "confidence": max(0.1, min(1.0, confidence)),  # Clamp to valid range
                "reasoning": reasoning

            
        except Exception as e:
            logger.warning(f"[PARSE] Vote parsing failed: {e}")
            return None
    
    async def _resolve_ambiguous_vote(self, content: str) -> bool:
        """Resolve ambiguous votes using context analysis"""
        # Simple heuristic: count positive vs negative indicators
        positive_words = ["good", "profitable", "safe", "recommend", "proceed", "opportunity"]
        negative_words = ["risky", "dangerous", "unprofitable", "avoid", "reject", "concern"]
        
        content_lower = content.lower()
        positive_count = sum(1 for word in positive_words if word in content_lower)
        negative_count = sum(1 for word in negative_words if word in content_lower)
        
        return positive_count > negative_count
    
    async def _infer_vote_from_sentiment(self, content: str) -> bool:
        """Infer vote from sentiment analysis (simplified)"""
        # Simplified sentiment analysis using keyword counting
        positive_indicators = ["good", "excellent", "profitable", "safe", "recommend", "opportunity", "positive"]
        negative_indicators = ["bad", "risky", "dangerous", "loss", "avoid", "concern", "negative"]
        
        content_lower = content.lower()
        positive_score = sum(1 for word in positive_indicators if word in content_lower)
        negative_score = sum(1 for word in negative_indicators if word in content_lower)
        
        return positive_score >= negative_score
    
    # Consensus Algorithm Implementations
    
    async def _majority_consensus(self, agent_votes: List[AgentVote], context: Dict[str, Any]) -> ConsensusResult:
        """Simple majority consensus algorithm"""
        if not agent_votes:
            return self._create_default_result(False, "No votes available", "majority_consensus")
        
        # Count votes
        approve_votes = sum(1 for vote in agent_votes if vote.vote)
        total_votes = len(agent_votes)
        
        # Calculate approval ratio
        approval_ratio = approve_votes / total_votes
        approved = approval_ratio > 0.5
        
        # Calculate average confidence
        avg_confidence = statistics.mean([vote.confidence for vote in agent_votes])
        
        # Generate reasoning
        reasoning = f"Majority decision: {approve_votes}/{total_votes} agents approve ({approval_ratio:.1%})"
        
        return ConsensusResult(
            approved=approved,
            confidence=avg_confidence,
            algorithm_used="majority_consensus",
            vote_summary={
                "total_votes": total_votes,
                "approve_votes": approve_votes,
                "reject_votes": total_votes - approve_votes,
                "approval_ratio": approval_ratio
            },
            reasoning=reasoning,
            quality_score=self._calculate_quality_score(agent_votes, "majority")

    
    async def _weighted_consensus(self, agent_votes: List[AgentVote], context: Dict[str, Any]) -> ConsensusResult:
        """Weighted consensus based on agent expertise and role"""
        if not agent_votes:
            return self._create_default_result(False, "No votes available", "weighted_consensus")
        
        # Calculate weighted votes
        total_weight = sum(vote.weight for vote in agent_votes)
        weighted_approve = sum(vote.weight for vote in agent_votes if vote.vote)
        
        # Calculate weighted approval ratio
        weighted_approval_ratio = weighted_approve / total_weight if total_weight > 0 else 0
        approved = weighted_approval_ratio > 0.5
        
        # Calculate weighted confidence
        weighted_confidence = sum(vote.confidence * vote.weight for vote in agent_votes) / total_weight
        
        reasoning = f"Weighted decision: {weighted_approval_ratio:.1%} weighted approval"
        
        return ConsensusResult(
            approved=approved,
            confidence=weighted_confidence,
            algorithm_used="weighted_consensus",
            vote_summary={
                "total_weight": total_weight,
                "weighted_approve": weighted_approve,
                "weighted_approval_ratio": weighted_approval_ratio,
                "individual_weights": {vote.agent_name: vote.weight for vote in agent_votes}
            },
            reasoning=reasoning,
            quality_score=self._calculate_quality_score(agent_votes, "weighted")

    
    async def _unanimous_consensus(self, agent_votes: List[AgentVote], context: Dict[str, Any]) -> ConsensusResult:
        """Unanimous consensus requiring all agents to agree"""
        if not agent_votes:
            return self._create_default_result(False, "No votes available", "unanimous_consensus")
        
        # Check if all votes are the same
        all_approve = all(vote.vote for vote in agent_votes)
        all_reject = all(not vote.vote for vote in agent_votes)
        
        approved = all_approve
        unanimous = all_approve or all_reject
        
        # Require high confidence for unanimous approval
        avg_confidence = statistics.mean([vote.confidence for vote in agent_votes])
        min_confidence = context.get("minimum_confidence", 0.8)
        
        if approved and avg_confidence < min_confidence:
            approved = False
            reasoning = f"Unanimous approval requires confidence >= {min_confidence}, got {avg_confidence:.2f}"
        else:
            reasoning = f"Unanimous {'approval' if all_approve else 'rejection'}: {len(agent_votes)}/{len(agent_votes)} agents agree"
        
        return ConsensusResult(
            approved=approved,
            confidence=avg_confidence if unanimous else 0.0,
            algorithm_used="unanimous_consensus",
            vote_summary={
                "total_votes": len(agent_votes),
                "unanimous": unanimous,
                "all_approve": all_approve,
                "all_reject": all_reject
            },
            reasoning=reasoning,
            quality_score=1.0 if unanimous else 0.3

    
    async def _risk_weighted_decision(self, agent_votes: List[AgentVote], context: Dict[str, Any]) -> ConsensusResult:
        """Risk-weighted decision algorithm"""
        if not agent_votes:
            return self._create_default_result(False, "No votes available", "risk_weighted_decision")
        
        # Extract risk scores from context
        risk_score = context.get("risk_assessment", {}).get("risk_score", 0.5)
        
        # Apply risk-based adjustments
        risk_multiplier = self._calculate_risk_multiplier(risk_score)
        
        # Calculate risk-adjusted consensus
        total_weight = sum(vote.weight * risk_multiplier for vote in agent_votes)
        risk_weighted_approve = sum(
            vote.weight * risk_multiplier for vote in agent_votes if vote.vote

        
        approval_ratio = risk_weighted_approve / total_weight if total_weight > 0 else 0
        
        # Higher risk requires higher approval threshold
        risk_threshold = 0.5 + (risk_score * 0.3)  # 0.5 to 0.8 based on risk
        approved = approval_ratio > risk_threshold
        
        # Adjust confidence based on risk
        base_confidence = statistics.mean([vote.confidence for vote in agent_votes])
        risk_adjusted_confidence = base_confidence * (1 - risk_score * 0.5)
        
        reasoning = f"Risk-weighted decision: {approval_ratio:.1%} approval (threshold: {risk_threshold:.1%}, risk: {risk_score:.2f})"
        
        return ConsensusResult(
            approved=approved,
            confidence=risk_adjusted_confidence,
            algorithm_used="risk_weighted_decision",
            vote_summary={
                "risk_score": risk_score,
                "risk_threshold": risk_threshold,
                "approval_ratio": approval_ratio,
                "risk_multiplier": risk_multiplier
            },
            reasoning=reasoning,
            risk_factors=[f"Risk score: {risk_score:.2f}"],
            quality_score=self._calculate_quality_score(agent_votes, "risk_weighted")

    
    async def _expertise_weighted_consensus(self, agent_votes: List[AgentVote], context: Dict[str, Any]) -> ConsensusResult:
        """Expertise-weighted consensus based on domain relevance"""
        if not agent_votes:
            return self._create_default_result(False, "No votes available", "expertise_weighted")
        
        decision_type = context.get("decision_type", "general")
        
        # Calculate expertise weights for this decision type
        expertise_weights = {}
        for vote in agent_votes:
            expertise_weight = self._calculate_expertise_weight(vote.expertise_areas, decision_type)
            expertise_weights[vote.agent_name] = expertise_weight
        
        # Apply expertise weighting
        total_expertise_weight = sum(expertise_weights.values())
        expertise_weighted_approve = sum(
            expertise_weights[vote.agent_name] for vote in agent_votes if vote.vote

        
        approval_ratio = expertise_weighted_approve / total_expertise_weight if total_expertise_weight > 0 else 0
        approved = approval_ratio > 0.5
        
        # Calculate expertise-weighted confidence
        expertise_weighted_confidence = sum(
            vote.confidence * expertise_weights[vote.agent_name] for vote in agent_votes
        ) / total_expertise_weight
        
        reasoning = f"Expertise-weighted decision for {decision_type}: {approval_ratio:.1%} weighted approval"
        
        return ConsensusResult(
            approved=approved,
            confidence=expertise_weighted_confidence,
            algorithm_used="expertise_weighted",
            vote_summary={
                "decision_type": decision_type,
                "expertise_weights": expertise_weights,
                "approval_ratio": approval_ratio
            },
            reasoning=reasoning,
            quality_score=self._calculate_quality_score(agent_votes, "expertise_weighted")

    
    async def _confidence_weighted_consensus(self, agent_votes: List[AgentVote], context: Dict[str, Any]) -> ConsensusResult:
        """Confidence-weighted consensus giving more weight to confident votes"""
        if not agent_votes:
            return self._create_default_result(False, "No votes available", "confidence_weighted")
        
        # Weight votes by confidence
        total_confidence_weight = sum(vote.confidence for vote in agent_votes)
        confidence_weighted_approve = sum(
            vote.confidence for vote in agent_votes if vote.vote

        
        approval_ratio = confidence_weighted_approve / total_confidence_weight if total_confidence_weight > 0 else 0
        approved = approval_ratio > 0.5
        
        # Use maximum confidence as overall confidence
        max_confidence = max(vote.confidence for vote in agent_votes)
        
        reasoning = f"Confidence-weighted decision: {approval_ratio:.1%} confidence-weighted approval"
        
        return ConsensusResult(
            approved=approved,
            confidence=max_confidence,
            algorithm_used="confidence_weighted",
            vote_summary={
                "total_confidence_weight": total_confidence_weight,
                "approval_ratio": approval_ratio,
                "confidence_distribution": [vote.confidence for vote in agent_votes]
            },
            reasoning=reasoning,
            quality_score=self._calculate_quality_score(agent_votes, "confidence_weighted")

    
    async def _hybrid_consensus(self, agent_votes: List[AgentVote], context: Dict[str, Any]) -> ConsensusResult:
        """Hybrid consensus combining multiple algorithms"""
        if not agent_votes:
            return self._create_default_result(False, "No votes available", "hybrid_consensus")
        
        # Run multiple algorithms
        majority_result = await self._majority_consensus(agent_votes, context)
        weighted_result = await self._weighted_consensus(agent_votes, context)
        confidence_result = await self._confidence_weighted_consensus(agent_votes, context)
        
        # Combine results
        algorithms_approving = sum([
            majority_result.approved,
            weighted_result.approved,
            confidence_result.approved

        
        # Require at least 2 out of 3 algorithms to approve
        approved = algorithms_approving >= 2
        
        # Average confidence from all algorithms
        combined_confidence = statistics.mean([
            majority_result.confidence,
            weighted_result.confidence,
            confidence_result.confidence

        
        reasoning = f"Hybrid consensus: {algorithms_approving}/3 algorithms approve"
        
        return ConsensusResult(
            approved=approved,
            confidence=combined_confidence,
            algorithm_used="hybrid_consensus",
            vote_summary={
                "algorithms_approving": algorithms_approving,
                "majority_approved": majority_result.approved,
                "weighted_approved": weighted_result.approved,
                "confidence_approved": confidence_result.approved
            },
            reasoning=reasoning,
            quality_score=max([
                majority_result.quality_score,
                weighted_result.quality_score,
                confidence_result.quality_score


    
    # Helper Methods
    
    def _get_agent_weight(self, agent_name: str) -> float:
        """Get weight for agent based on role and expertise"""
        role_weights = {
            "arbitragecoordinator": 1.0,
            "riskanalyst": 0.9,
            "marketanalyst": 0.8,
            "executionspecialist": 0.7,
            "gasoptimizer": 0.6,
            "compliancevalidator": 0.8,
            "timinganalyst": 0.6,
            "bridgespecialist": 0.7

        
        normalized_name = agent_name.lower().replace("_", "").replace(" ", "")
        return role_weights.get(normalized_name, 0.5)
    
    def _get_agent_expertise(self, agent_name: str) -> List[str]:
        """Get expertise areas for agent"""
        expertise_mapping = {
            "arbitragecoordinator": ["strategy", "coordination", "decision_making"],
            "riskanalyst": ["risk_assessment", "safety", "compliance"],
            "marketanalyst": ["market_analysis", "pricing", "liquidity"],
            "executionspecialist": ["execution", "optimization", "monitoring"],
            "gasoptimizer": ["gas_optimization", "cost_analysis", "timing"],
            "compliancevalidator": ["compliance", "regulatory", "legal"],
            "timinganalyst": ["timing", "market_microstructure", "execution_timing"],
            "bridgespecialist": ["cross_chain", "bridges", "multi_chain"]

        
        normalized_name = agent_name.lower().replace("_", "").replace(" ", "")
        return expertise_mapping.get(normalized_name, [])
    
    def _calculate_risk_multiplier(self, risk_score: float) -> float:
        """Calculate risk multiplier for decision weighting"""
        # Higher risk requires more conservative weighting
        return max(0.1, 1.0 - risk_score * 0.8)
    
    def _calculate_expertise_weight(self, expertise_areas: List[str], decision_type: str) -> float:
        """Calculate expertise weight for decision type"""
        expertise_relevance = {
            "arbitrage_decision": {
                "strategy": 1.0, "market_analysis": 0.9, "risk_assessment": 0.8,
                "execution": 0.7, "gas_optimization": 0.6
            },
            "risk_assessment": {
                "risk_assessment": 1.0, "safety": 0.9, "compliance": 0.8,
                "market_analysis": 0.7, "strategy": 0.6
            },
            "execution_planning": {
                "execution": 1.0, "optimization": 0.9, "gas_optimization": 0.8,
                "timing": 0.7, "monitoring": 0.6


        
        relevance_map = expertise_relevance.get(decision_type, {})
        if not expertise_areas or not relevance_map:
            return 0.5  # Default weight
        
        # Calculate average relevance for agent's expertise areas
        total_relevance = sum(relevance_map.get(area, 0.3) for area in expertise_areas)
        return min(1.0, total_relevance / len(expertise_areas))
    
    def _calculate_quality_score(self, agent_votes: List[AgentVote], algorithm_type: str) -> float:
        """Calculate quality score for consensus result"""
        if not agent_votes:
            return 0.0
        
        # Base quality factors
        participation_ratio = len(agent_votes) / max(1, self.config.get("expected_agents", 4))
        avg_confidence = statistics.mean([vote.confidence for vote in agent_votes])
        reasoning_quality = statistics.mean([
            min(1.0, len(vote.reasoning) / 100) for vote in agent_votes

        
        # Algorithm-specific adjustments
        algorithm_bonus = {
            "majority": 0.0,
            "weighted": 0.1,
            "unanimous": 0.2,
            "risk_weighted": 0.15,
            "expertise_weighted": 0.15,
            "confidence_weighted": 0.1,
            "hybrid": 0.2

        
        base_score = (participation_ratio + avg_confidence + reasoning_quality) / 3
        bonus = algorithm_bonus.get(algorithm_type, 0.0)
        
        return min(1.0, base_score + bonus)
    
    def _initialize_role_weights(self) -> Dict[str, Dict[str, float]]:
        """Initialize role weights for different decision types"""
        return {
            "arbitrage_decision": {
                "coordinator": 1.0,
                "risk_manager": 0.9,
                "analyzer": 0.8,
                "executor": 0.7
            },
            "risk_assessment": {
                "risk_manager": 1.0,
                "analyzer": 0.8,
                "validator": 0.7,
                "coordinator": 0.6
            },
            "execution_planning": {
                "executor": 1.0,
                "coordinator": 0.8,
                "optimizer": 0.7,
                "risk_manager": 0.6


    
    async def _validate_vote_quality(self, agent_votes: List[AgentVote], context: Dict[str, Any]) -> Dict[str, Any]:
        """Validate quality of agent votes"""
        if not agent_votes:
            return {"valid": False, "reason": "No votes provided"}
        
        # Check participation threshold
        expected_agents = context.get("expected_agents", 3)
        participation_ratio = len(agent_votes) / expected_agents
        
        if participation_ratio < self.quality_thresholds["minimum_participation"]:
            return {
                "valid": False,
                "reason": f"Insufficient participation: {participation_ratio:.1%} < {self.quality_thresholds['minimum_participation']:.1%}"

        
        # Check average confidence
        avg_confidence = statistics.mean([vote.confidence for vote in agent_votes])
        if avg_confidence < self.quality_thresholds["minimum_confidence"]:
            return {
                "valid": False,
                "reason": f"Low confidence: {avg_confidence:.2f} < {self.quality_thresholds['minimum_confidence']}"

        
        return {"valid": True}
    
    async def _enhance_consensus_result(
        self,
        result: ConsensusResult,
        agent_votes: List[AgentVote],
        context: Dict[str, Any]
    ) -> ConsensusResult:
        """Enhance consensus result with additional analysis"""
        
        # Add dissenting opinions
        dissenting_votes = [vote for vote in agent_votes if vote.vote != result.approved]
        result.dissenting_opinions = [vote.reasoning for vote in dissenting_votes]
        
        # Generate execution plan if approved
        if result.approved:
            result.execution_plan = await self._generate_execution_plan(agent_votes, context)
        
        # Extract risk factors
        result.risk_factors = await self._extract_risk_factors(agent_votes)
        
        return result
    
    async def _generate_execution_plan(self, agent_votes: List[AgentVote], context: Dict[str, Any]) -> Dict[str, Any]:
        """Generate execution plan from agent votes and context"""
        # Extract execution suggestions from agent reasoning
        execution_suggestions = []
        for vote in agent_votes:
            if vote.vote and "execution" in vote.reasoning.lower():
                execution_suggestions.append(vote.reasoning)
        
        return {
            "approved": True,
            "strategy": "optimized_arbitrage",
            "parameters": context.get("opportunity_data", {}),
            "risk_mitigations": ["slippage_protection", "gas_optimization"],
            "monitoring": ["real_time_tracking", "profit_validation"],
            "execution_suggestions": execution_suggestions[:3]  # Top 3 suggestions

    
    async def _extract_risk_factors(self, agent_votes: List[AgentVote]) -> List[str]:
        """Extract risk factors from agent reasoning"""
        risk_keywords = ["risk", "danger", "concern", "volatility", "slippage", "gas", "liquidity"]
        risk_factors = []
        
        for vote in agent_votes:
            for keyword in risk_keywords:
                if keyword in vote.reasoning.lower():
                    # Extract sentence containing the keyword
                    sentences = vote.reasoning.split('.')
                    for sentence in sentences:
                        if keyword in sentence.lower():
                            risk_factors.append(sentence.strip())
                            break
        
        return list(set(risk_factors))[:5]  # Unique top 5 risk factors
    
    def _create_default_result(self, approved: bool, reason: str, algorithm: str) -> ConsensusResult:
        """Create default consensus result"""
        return ConsensusResult(
            approved=approved,
            confidence=0.0,
            algorithm_used=algorithm,
            vote_summary={},
            reasoning=reason,
            quality_score=0.0

    
    def _create_error_result(self, error_message: str) -> Dict[str, Any]:
        """Create error result dictionary"""
        return {
            "approved": False,
            "confidence": 0.0,
            "algorithm_used": "error",
            "reasoning": f"Error: {error_message}",
            "error": error_message,
            "timestamp": datetime.now().isoformat()

    
    def _serialize_consensus_result(self, result: ConsensusResult) -> Dict[str, Any]:
        """Serialize consensus result for JSON output"""
        return {
            "approved": result.approved,
            "confidence": result.confidence,
            "algorithm_used": result.algorithm_used,
            "vote_summary": result.vote_summary,
            "reasoning": result.reasoning,
            "execution_plan": result.execution_plan,
            "risk_factors": result.risk_factors,
            "dissenting_opinions": result.dissenting_opinions,
            "quality_score": result.quality_score,
            "timestamp": result.timestamp.isoformat()

    
    def _update_decision_metrics(self, result: ConsensusResult, algorithm_name: str, start_time: datetime):
        """Update decision metrics"""
        self.decision_metrics["total_decisions"] += 1
        self.decision_metrics["algorithm_usage"][algorithm_name] += 1
        
        if result.approved:
            self.decision_metrics["successful_decisions"] += 1
        
        if result.confidence > 0.8:
            self.decision_metrics["high_confidence_decisions"] += 1
        
        if result.quality_score == 1.0:
            self.decision_metrics["unanimous_decisions"] += 1
        
        # Update averages
        total = self.decision_metrics["total_decisions"]
        current_avg_conf = self.decision_metrics["average_confidence"]
        self.decision_metrics["average_confidence"] = (
            (current_avg_conf * (total - 1) + result.confidence) / total

        
        decision_time = (datetime.now() - start_time).total_seconds()
        current_avg_time = self.decision_metrics["average_decision_time"]
        self.decision_metrics["average_decision_time"] = (
            (current_avg_time * (total - 1) + decision_time) / total

    
    # Placeholder methods for advanced functionality
    
    async def _validate_decision_config(self):
        """Validate decision engine configuration"""
        pass
    
    async def _initialize_nlp_components(self):
        """Initialize NLP components for reasoning analysis"""
        pass
    
    async def _extract_risk_assessments(self, conversation_history: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Extract risk assessments from conversation"""
        return []
    
    async def _risk_assessment_consensus(self, risk_assessments: List[Dict[str, Any]], context: Dict[str, Any]) -> Dict[str, Any]:
        """Apply consensus to risk assessments"""
        return {"risk_level": "medium", "risk_score": 0.5, "confidence": 0.7}
    
    async def _extract_execution_plans(self, conversation_history: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Extract execution plans from conversation"""
        return []
    
    async def _execution_planning_consensus(self, execution_plans: List[Dict[str, Any]], context: Dict[str, Any]) -> Dict[str, Any]:
        """Apply consensus to execution plans"""
        return {"approved": True, "optimal_plan": {}, "confidence": 0.7}
    
    async def get_status(self) -> Dict[str, Any]:
        """Get decision engine status"""
        return {
            "engine_status": "healthy",
            "algorithms_available": len(self.consensus_algorithms),
            "decision_metrics": self.decision_metrics,
            "quality_thresholds": self.quality_thresholds,
            "role_weights_configured": len(self.role_weights)

    
    async def shutdown(self):
        """Shutdown the decision engine"""
        logger.info("[SHUTDOWN] Shutting down Decision Engine...")
        
        # Clear metrics and cache
        self.decision_metrics.clear()
        
        logger.info("[SHUTDOWN] Decision Engine shutdown complete")