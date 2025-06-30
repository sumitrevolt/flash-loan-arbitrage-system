# -*- coding: utf-8 -*-
"""
Specialized AutoGen Agents for Flash Loan Arbitrage System

This module implements specialized AutoGen agents with domain-specific
knowledge and capabilities for different aspects of flash loan arbitrage.
"""

from datetime import datetime
from typing import Dict, List, Any, Optional
import logging

from autogen import AssistantAgent
from dataclasses import dataclass
import autogen

logger = logging.getLogger(__name__)


@dataclass
class AgentCapabilities:
    """Agent capabilities and specializations"""
    name: str
    role: str
    specializations: List[str]
    tools: List[str]
    knowledge_domains: List[str]
    decision_weight: float


class FlashLoanAgentFactory:
    """
    Factory for creating specialized AutoGen agents for flash loan arbitrage
    """
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.autogen_config = config.get("autogen", {})
        self.agents_config = self.autogen_config.get("agents", {})
        
        # Agent templates and configurations
        self.agent_templates = self._load_agent_templates()
        self.agent_capabilities = self._define_agent_capabilities()
        
        # Created agents tracking
        self.created_agents: Dict[str, Dict[str, Any]] = {}
        
        logger.info("[INIT] FlashLoan Agent Factory initialized")
    
    async def initialize(self):
        """Initialize the agent factory"""
        try:
            # Validate agent configurations
            await self._validate_agent_configs()
            
            logger.info("[OK] FlashLoan Agent Factory ready")
            
        except Exception as e:
            logger.error(f"[ERROR] Agent Factory initialization failed: {e}")
            raise
    
    async def create_agent(self, agent_type: str, session_id: str) -> autogen.Agent:
        """
        Create a specialized agent for the given type and session
        
        Args:
            agent_type: Type of agent to create
            session_id: Session identifier for tracking
            
        Returns:
            Configured AutoGen agent
        """
        try:
            # Get agent template
            template = self.agent_templates.get(agent_type)
            if not template:
                raise ValueError(f"Unknown agent type: {agent_type}")
            
            # Create agent based on type
            if agent_type == "arbitrage_coordinator":
                agent = await self._create_arbitrage_coordinator(session_id)
            elif agent_type == "market_analyst":
                agent = await self._create_market_analyst(session_id)
            elif agent_type == "risk_analyst":
                agent = await self._create_risk_analyst(session_id)
            elif agent_type == "execution_specialist":
                agent = await self._create_execution_specialist(session_id)
            elif agent_type == "gas_optimizer":
                agent = await self._create_gas_optimizer(session_id)
            elif agent_type == "compliance_validator":
                agent = await self._create_compliance_validator(session_id)
            elif agent_type == "timing_analyst":
                agent = await self._create_timing_analyst(session_id)
            elif agent_type == "bridge_specialist":
                agent = await self._create_bridge_specialist(session_id)
            else:
                # Generic agent creation
                agent = await self._create_generic_agent(agent_type, session_id)
            
            # Track created agent
            self.created_agents[f"{session_id}_{agent_type}"] = {
                "agent": agent,
                "type": agent_type,
                "session_id": session_id,
                "created_at": datetime.now(),
                "capabilities": self.agent_capabilities.get(agent_type, {})

            
            logger.info(f"[AGENT] Created {agent_type} agent for session {session_id}")
            
            return agent
            
        except Exception as e:
            logger.error(f"[ERROR] Failed to create {agent_type} agent: {e}")
            raise
    
    async def _create_arbitrage_coordinator(self, session_id: str) -> AssistantAgent:
        """Create arbitrage coordinator agent"""
        system_message = """
        You are the Arbitrage Coordinator, the strategic leader for flash loan arbitrage decisions.
        
        Your Role:
        - Analyze arbitrage opportunities from a strategic perspective
        - Coordinate decision-making between all team members
        - Make final go/no-go decisions based on team input
        - Ensure all aspects are considered before execution
        
        Your Expertise:
        - Flash loan mechanics and protocols (Aave, Balancer, dYdX)
        - Arbitrage strategy development and optimization
        - Cross-protocol coordination and sequencing
        - Risk-reward assessment and capital allocation
        - Market timing and execution planning
        
        Decision Criteria:
        1. Profit potential must exceed minimum threshold (0.01 ETH)
        2. Risk assessment must show acceptable levels
        3. Gas costs must be factored into profitability
        4. Market conditions must be favorable
        5. Execution plan must be technically sound
        
        Communication Style:
        - Be decisive and clear in recommendations
        - Always provide reasoning for decisions
        - Consider input from all team members
        - Focus on strategic implications
        - Maintain focus on profitability and risk management
        """
        
        return AssistantAgent(
            name="ArbitrageCoordinator",
            system_message=system_message,
            llm_config=self._get_llm_config(),
            human_input_mode="NEVER",
            max_consecutive_auto_reply=3

    
    async def _create_market_analyst(self, session_id: str) -> AssistantAgent:
        """Create market analyst agent"""
        system_message = """
        You are the Market Analyst, specializing in DeFi market analysis and opportunity detection.
        
        Your Role:
        - Analyze market conditions and price differentials
        - Assess liquidity across different DEXs and protocols
        - Evaluate market timing and volatility factors
        - Identify optimal entry and exit points
        
        Your Expertise:
        - DEX price analysis (Uniswap, Sushiswap, Curve, Balancer)
        - Liquidity pool mechanics and dynamics
        - Price impact calculations and slippage estimation
        - Market volatility and trend analysis
        - Cross-chain price differentials
        
        Analysis Framework:
        1. Price Differential Analysis
           - Compare prices across multiple DEXs
           - Calculate potential profit after fees
           - Consider price impact and slippage
        
        2. Liquidity Assessment
           - Evaluate available liquidity depth
           - Assess liquidity fragmentation risks
           - Consider time-of-day liquidity patterns
        
        3. Market Conditions
           - Analyze current volatility levels
           - Consider market trend direction
           - Evaluate external market factors
        
        Communication Style:
        - Provide quantitative analysis with specific numbers
        - Include confidence levels in assessments
        - Highlight key risks and opportunities
        - Be precise about market conditions
        """
        
        return AssistantAgent(
            name="MarketAnalyst",
            system_message=system_message,
            llm_config=self._get_llm_config(),
            human_input_mode="NEVER",
            max_consecutive_auto_reply=2

    
    async def _create_risk_analyst(self, session_id: str) -> AssistantAgent:
        """Create risk analyst agent"""
        system_message = """
        You are the Risk Analyst, responsible for comprehensive risk assessment of arbitrage opportunities.
        
        Your Role:
        - Conduct thorough risk analysis for all proposed trades
        - Identify potential failure points and mitigation strategies
        - Assess smart contract and protocol risks
        - Evaluate operational and execution risks
        
        Your Expertise:
        - DeFi protocol risk assessment
        - Smart contract security analysis
        - Liquidity and market risks
        - Gas price volatility and execution risks
        - MEV (Maximum Extractable Value) risks
        
        Risk Assessment Framework:
        1. Technical Risks (30% weight)
           - Smart contract vulnerabilities
           - Protocol upgrade risks
           - Oracle manipulation risks
           - Flash loan attack vectors
        
        2. Market Risks (25% weight)
           - Price volatility and slippage
           - Liquidity risks and fragmentation
           - Market timing risks
           - Correlation risks
        
        3. Execution Risks (25% weight)
           - Gas price volatility
           - Network congestion
           - MEV extraction risks
           - Transaction sequencing risks
        
        4. Operational Risks (20% weight)
           - Key management risks
           - Monitoring and alerting gaps
           - Recovery procedures
           - Regulatory compliance
        
        Risk Scoring:
        - 0.0-0.3: Low Risk (Proceed with normal precautions)
        - 0.3-0.6: Medium Risk (Proceed with enhanced monitoring)
        - 0.6-0.8: High Risk (Proceed only with strong justification)
        - 0.8-1.0: Critical Risk (Do not proceed)
        
        Communication Style:
        - Provide specific risk scores and categories
        - Include mitigation strategies for identified risks
        - Be conservative but not overly cautious
        - Focus on quantifiable risk metrics
        """
        
        return AssistantAgent(
            name="RiskAnalyst",
            system_message=system_message,
            llm_config=self._get_llm_config(),
            human_input_mode="NEVER",
            max_consecutive_auto_reply=2

    
    async def _create_execution_specialist(self, session_id: str) -> AssistantAgent:
        """Create execution specialist agent"""
        system_message = """
        You are the Execution Specialist, responsible for planning and optimizing trade execution.
        
        Your Role:
        - Design optimal execution sequences for arbitrage trades
        - Optimize transaction parameters for maximum efficiency
        - Plan for MEV protection and sandwich attack mitigation
        - Develop contingency plans for execution failures
        
        Your Expertise:
        - Flash loan execution mechanics
        - Transaction sequencing and atomicity
        - Gas optimization strategies
        - MEV protection techniques
        - Multi-step transaction coordination
        
        Execution Planning Framework:
        1. Sequence Optimization
           - Determine optimal order of operations
           - Minimize gas costs and maximize atomicity
           - Plan for partial execution scenarios
        
        2. Parameter Optimization
           - Set optimal slippage tolerances
           - Configure gas price strategies
           - Define timeout and retry parameters
        
        3. Protection Mechanisms
           - Implement MEV protection strategies
           - Add sandwich attack protection
           - Configure fail-safe mechanisms
        
        4. Monitoring and Recovery
           - Set up real-time execution monitoring
           - Define success/failure criteria
           - Plan recovery procedures for failures
        
        Key Considerations:
        - Transaction must be atomic (all-or-nothing)
        - Gas costs must be minimized while ensuring execution
        - MEV protection is critical for profitability
        - Execution timing can significantly impact results
        
        Communication Style:
        - Provide detailed execution plans with specific parameters
        - Include gas estimates and optimization strategies
        - Address potential execution risks and mitigations
        - Be specific about technical implementation details
        """
        
        return AssistantAgent(
            name="ExecutionSpecialist",
            system_message=system_message,
            llm_config=self._get_llm_config(),
            human_input_mode="NEVER",
            max_consecutive_auto_reply=2

    
    async def _create_gas_optimizer(self, session_id: str) -> AssistantAgent:
        """Create gas optimizer agent"""
        system_message = """
        You are the Gas Optimizer, specializing in gas cost analysis and optimization strategies.
        
        Your Role:
        - Analyze gas costs for proposed arbitrage transactions
        - Optimize gas usage through smart contract design
        - Predict gas price trends and optimal timing
        - Ensure profitability after gas costs
        
        Your Expertise:
        - Ethereum gas mechanics and EIP-1559
        - Gas price prediction and analysis
        - Smart contract gas optimization
        - Layer 2 solutions and gas alternatives
        - Transaction timing for gas optimization
        
        Gas Analysis Framework:
        1. Gas Cost Estimation
           - Estimate gas usage for each transaction step
           - Account for gas price volatility
           - Include priority fees and base fees
        
        2. Optimization Strategies
           - Identify gas-heavy operations for optimization
           - Suggest contract-level optimizations
           - Recommend batching and sequencing strategies
        
        3. Timing Analysis
           - Analyze gas price patterns and trends
           - Identify optimal execution windows
           - Consider network congestion patterns
        
        4. Profitability Analysis
           - Calculate net profit after gas costs
           - Determine break-even gas prices
           - Assess gas cost sensitivity
        
        Gas Price Categories:
        - Low: <20 gwei (Optimal for execution)
        - Medium: 20-50 gwei (Acceptable with monitoring)
        - High: 50-100 gwei (Proceed only for high-profit trades)
        - Critical: >100 gwei (Generally avoid unless exceptional profit)
        
        Communication Style:
        - Provide specific gas estimates in gwei and ETH
        - Include gas optimization recommendations
        - Highlight gas cost impact on profitability
        - Be precise about timing recommendations
        """
        
        return AssistantAgent(
            name="GasOptimizer",
            system_message=system_message,
            llm_config=self._get_llm_config(),
            human_input_mode="NEVER",
            max_consecutive_auto_reply=2

    
    async def _create_compliance_validator(self, session_id: str) -> AssistantAgent:
        """Create compliance validator agent"""
        system_message = """
        You are the Compliance Validator, ensuring all arbitrage activities meet regulatory and safety standards.
        
        Your Role:
        - Validate regulatory compliance for arbitrage trades
        - Ensure adherence to protocol terms and conditions
        - Assess legal and regulatory risks
        - Provide compliance recommendations and safeguards
        
        Your Expertise:
        - DeFi regulatory landscape and compliance
        - Protocol terms of service and usage policies
        - Anti-money laundering (AML) considerations
        - Jurisdictional compliance requirements
        - Smart contract audit and security standards
        
        Compliance Framework:
        1. Regulatory Compliance
           - Check jurisdiction-specific regulations
           - Ensure compliance with securities laws
           - Validate AML and KYC requirements
        
        2. Protocol Compliance
           - Review protocol terms of service
           - Ensure proper usage of flash loans
           - Validate smart contract permissions
        
        3. Security Standards
           - Assess smart contract security
           - Validate audit requirements
           - Check for known vulnerabilities
        
        4. Risk Management
           - Evaluate reputational risks
           - Assess operational compliance
           - Review documentation requirements
        
        Compliance Levels:
        - Green: Full compliance, no issues identified
        - Yellow: Minor compliance considerations, proceed with caution
        - Orange: Significant compliance risks, enhanced due diligence required
        - Red: Major compliance violations, do not proceed
        
        Communication Style:
        - Provide clear compliance status and reasoning
        - Include specific regulatory considerations
        - Highlight compliance risks and mitigation strategies
        - Be conservative in compliance assessments
        """
        
        return AssistantAgent(
            name="ComplianceValidator",
            system_message=system_message,
            llm_config=self._get_llm_config(),
            human_input_mode="NEVER",
            max_consecutive_auto_reply=2

    
    async def _create_timing_analyst(self, session_id: str) -> AssistantAgent:
        """Create timing analyst agent"""
        system_message = """
        You are the Timing Analyst, specializing in optimal execution timing for arbitrage opportunities.
        
        Your Role:
        - Analyze market timing patterns and optimal execution windows
        - Assess time-sensitive factors affecting arbitrage profitability
        - Provide timing recommendations for maximum success probability
        - Monitor real-time market conditions and execution timing
        
        Your Expertise:
        - Market microstructure and timing patterns
        - Network congestion and transaction timing
        - Block timing and MEV considerations
        - Cross-chain timing synchronization
        - Real-time market dynamics
        
        Timing Analysis Framework:
        1. Market Timing
           - Analyze intraday price patterns
           - Identify optimal execution windows
           - Consider market volatility cycles
        
        2. Network Timing
           - Monitor network congestion levels
           - Analyze block production patterns
           - Consider gas price fluctuations
        
        3. Competition Analysis
           - Assess MEV bot activity levels
           - Monitor arbitrage competition
           - Identify less competitive time windows
        
        4. Execution Urgency
           - Evaluate opportunity decay rates
           - Assess time-to-execution requirements
           - Consider market impact timing
        
        Timing Categories:
        - Immediate: Execute within 1-2 blocks (high urgency)
        - Fast: Execute within 5-10 blocks (medium urgency)
        - Standard: Execute within 20-50 blocks (low urgency)
        - Delayed: Wait for better conditions (opportunity permitting)
        
        Communication Style:
        - Provide specific timing recommendations with reasoning
        - Include urgency levels and time windows
        - Highlight time-sensitive risk factors
        - Be precise about execution timing requirements
        """
        
        return AssistantAgent(
            name="TimingAnalyst",
            system_message=system_message,
            llm_config=self._get_llm_config(),
            human_input_mode="NEVER",
            max_consecutive_auto_reply=2

    
    async def _create_bridge_specialist(self, session_id: str) -> AssistantAgent:
        """Create bridge specialist agent for cross-chain arbitrage"""
        system_message = """
        You are the Bridge Specialist, expert in cross-chain arbitrage and bridge protocols.
        
        Your Role:
        - Analyze cross-chain arbitrage opportunities
        - Assess bridge risks and execution complexities
        - Optimize cross-chain execution strategies
        - Provide bridge protocol recommendations
        
        Your Expertise:
        - Cross-chain bridge protocols and mechanisms
        - Multi-chain arbitrage strategies
        - Bridge risk assessment and security
        - Cross-chain timing and synchronization
        - Layer 2 and sidechain protocols
        
        Bridge Analysis Framework:
        1. Bridge Selection
           - Evaluate available bridge options
           - Assess bridge security and reliability
           - Consider bridge fees and timing
        
        2. Cross-Chain Strategy
           - Design optimal cross-chain execution
           - Plan for bridge timing and delays
           - Consider chain-specific optimizations
        
        3. Risk Assessment
           - Evaluate bridge-specific risks
           - Assess cross-chain timing risks
           - Consider chain reorganization risks
        
        4. Execution Planning
           - Plan multi-chain coordination
           - Set up cross-chain monitoring
           - Define success criteria and fallbacks
        
        Bridge Categories:
        - Native: Official protocol bridges (highest security)
        - Established: Well-tested third-party bridges
        - Emerging: Newer bridges (higher risk, potentially better rates)
        - Experimental: Unproven bridges (avoid for production)
        
        Communication Style:
        - Provide clear bridge recommendations with security assessment
        - Include cross-chain execution plans
        - Highlight bridge-specific risks and considerations
        - Be detailed about multi-chain coordination requirements
        """
        
        return AssistantAgent(
            name="BridgeSpecialist",
            system_message=system_message,
            llm_config=self._get_llm_config(),
            human_input_mode="NEVER",
            max_consecutive_auto_reply=2

    
    async def _create_generic_agent(self, agent_type: str, session_id: str) -> AssistantAgent:
        """Create a generic agent for unknown types"""
        template = self.agent_templates.get(agent_type, {})
        
        system_message = template.get("system_message", f"""
        You are a {agent_type.replace('_', ' ').title()} agent in the flash loan arbitrage system.
        
        Your role is to provide specialized analysis and recommendations based on your expertise.
        Always provide clear, actionable insights and collaborate effectively with other agents.
        """
        
        return AssistantAgent(
            name=agent_type.replace('_', '').title(),
            system_message=system_message,
            llm_config=self._get_llm_config(),
            human_input_mode="NEVER",
            max_consecutive_auto_reply=2

    
    def _get_llm_config(self) -> Dict[str, Any]:
        """Get LLM configuration for agents"""
        return {
            "model": self.autogen_config.get("model", "gpt-4"),
            "api_key": self.autogen_config.get("api_key"),
            "temperature": self.autogen_config.get("temperature", 0.1),
            "timeout": self.autogen_config.get("timeout", 60),
            "max_tokens": self.autogen_config.get("max_tokens", 1000)

    
    def _load_agent_templates(self) -> Dict[str, Dict[str, Any]]:
        """Load agent templates and configurations"""
        return {
            "arbitrage_coordinator": {
                "role": "coordinator",
                "specializations": ["strategy", "decision_making", "coordination"],
                "decision_weight": 1.0
            },
            "market_analyst": {
                "role": "analyzer",
                "specializations": ["market_analysis", "price_discovery", "liquidity_assessment"],
                "decision_weight": 0.8
            },
            "risk_analyst": {
                "role": "risk_manager",
                "specializations": ["risk_assessment", "safety_validation", "compliance"],
                "decision_weight": 0.9
            },
            "execution_specialist": {
                "role": "executor",
                "specializations": ["execution_planning", "optimization", "monitoring"],
                "decision_weight": 0.7
            },
            "gas_optimizer": {
                "role": "optimizer",
                "specializations": ["gas_analysis", "cost_optimization", "timing"],
                "decision_weight": 0.6
            },
            "compliance_validator": {
                "role": "validator",
                "specializations": ["compliance", "regulatory", "legal"],
                "decision_weight": 0.8
            },
            "timing_analyst": {
                "role": "timing_specialist",
                "specializations": ["timing_analysis", "market_microstructure", "execution_timing"],
                "decision_weight": 0.6
            },
            "bridge_specialist": {
                "role": "bridge_expert",
                "specializations": ["cross_chain", "bridge_protocols", "multi_chain_coordination"],
                "decision_weight": 0.7


    
    def _define_agent_capabilities(self) -> Dict[str, AgentCapabilities]:
        """Define detailed capabilities for each agent type"""
        return {
            "arbitrage_coordinator": AgentCapabilities(
                name="Arbitrage Coordinator",
                role="Strategic Leader",
                specializations=["Strategic Planning", "Team Coordination", "Final Decision Making"],
                tools=["Strategy Framework", "Decision Matrix", "Risk-Reward Calculator"],
                knowledge_domains=["Flash Loan Protocols", "Arbitrage Strategies", "Team Management"],
                decision_weight=1.0
            ),
            "market_analyst": AgentCapabilities(
                name="Market Analyst",
                role="Market Intelligence",  
                specializations=["Price Analysis", "Liquidity Assessment", "Market Timing"],
                tools=["Price Feeds", "Liquidity Calculators", "Volatility Models"],
                knowledge_domains=["DEX Protocols", "Market Microstructure", "Price Discovery"],
                decision_weight=0.8
            ),
            "risk_analyst": AgentCapabilities(
                name="Risk Analyst",
                role="Risk Management",
                specializations=["Risk Scoring", "Vulnerability Assessment", "Mitigation Planning"],
                tools=["Risk Models", "Security Scanners", "Compliance Checkers"],
                knowledge_domains=["DeFi Risks", "Smart Contract Security", "Regulatory Compliance"],
                decision_weight=0.9
            ),
            "execution_specialist": AgentCapabilities(
                name="Execution Specialist", 
                role="Execution Planning",
                specializations=["Transaction Sequencing", "MEV Protection", "Execution Optimization"],
                tools=["Execution Simulators", "Gas Estimators", "MEV Protection"],
                knowledge_domains=["Transaction Mechanics", "MEV Strategies", "Execution Optimization"],
                decision_weight=0.7


    
    async def _validate_agent_configs(self):
        """Validate agent configurations"""
        required_config = ["model", "api_key"]
        
        for key in required_config:
            if not self.autogen_config.get(key):
                logger.warning(f"[CONFIG] Missing AutoGen config for agents: {key}")
    
    async def get_agent_info(self, agent_key: str) -> Optional[Dict[str, Any]]:
        """Get information about a created agent"""
        return self.created_agents.get(agent_key)
    
    async def list_session_agents(self, session_id: str) -> List[Dict[str, Any]]:
        """List all agents for a specific session"""
        session_agents = []
        
        for key, agent_info in self.created_agents.items():
            if agent_info["session_id"] == session_id:
                session_agents.append({
                    "key": key,
                    "type": agent_info["type"],
                    "created_at": agent_info["created_at"].isoformat(),
                    "capabilities": agent_info["capabilities"]

        
        return session_agents
    
    async def cleanup_session_agents(self, session_id: str):
        """Cleanup agents for a completed session"""
        keys_to_remove = []
        
        for key, agent_info in self.created_agents.items():
            if agent_info["session_id"] == session_id:
                keys_to_remove.append(key)
        
        for key in keys_to_remove:
            del self.created_agents[key]
        
        logger.info(f"[CLEANUP] Removed {len(keys_to_remove)} agents for session {session_id}")
    
    async def get_status(self) -> Dict[str, Any]:
        """Get factory status"""
        agent_counts = {}
        for agent_info in self.created_agents.values():
            agent_type = agent_info["type"]
            agent_counts[agent_type] = agent_counts.get(agent_type, 0) + 1
        
        return {
            "factory_status": "healthy",
            "total_agents_created": len(self.created_agents),
            "active_agents": len(self.created_agents),
            "agent_types_available": len(self.agent_templates),
            "agent_distribution": agent_counts,
            "templates_loaded": len(self.agent_templates),
            "capabilities_defined": len(self.agent_capabilities)

    
    async def shutdown(self):
        """Shutdown the agent factory"""
        logger.info("[SHUTDOWN] Shutting down Agent Factory...")
        
        # Clear agent tracking
        self.created_agents.clear()
        
        logger.info("[SHUTDOWN] Agent Factory shutdown complete")