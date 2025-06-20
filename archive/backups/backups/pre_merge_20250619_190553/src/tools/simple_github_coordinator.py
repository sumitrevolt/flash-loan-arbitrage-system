#!/usr/bin/env python3
"""
Simple GitHub Copilot Multi-Agent System
Lightweight version without database dependency
"""

import asyncio
import os
import logging
import json
from datetime import datetime
from typing import Dict, List, Any, Optional
from enum import Enum
import requests

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class AgentRole(Enum):
    """Multi-agent system roles"""
    CODE_ANALYST = "code_analyst"
    CODE_GENERATOR = "code_generator"
    ARCHITECTURE_DESIGNER = "architecture_designer"
    SECURITY_AUDITOR = "security_auditor"
    PERFORMANCE_OPTIMIZER = "performance_optimizer"
    COORDINATOR = "coordinator"

class GitHubModelsLLM:
    """GitHub Models API interface"""
    
    def __init__(self, model="gpt-4o-mini", temperature=0.1):
        self.model = model
        self.temperature = temperature
        self.github_token = os.getenv('GITHUB_TOKEN')
        self.base_url = "https://models.inference.ai.azure.com/chat/completions"
        
        if not self.github_token:
            raise ValueError("GITHUB_TOKEN environment variable is required")
    
    async def ainvoke(self, prompt: str, **kwargs) -> str:
        """Async invoke the LLM"""
        return await asyncio.to_thread(self.invoke, prompt, **kwargs)
    
    def invoke(self, prompt: str, **kwargs) -> str:
        """Invoke the LLM with a prompt"""
        try:
            headers = {
                "Authorization": f"Bearer {self.github_token}",
                "Content-Type": "application/json"
            }
            
            data = {
                "model": self.model,
                "messages": [{"role": "user", "content": prompt}],
                "max_tokens": kwargs.get("max_tokens", 2000),
                "temperature": kwargs.get("temperature", self.temperature)
            }
            
            response = requests.post(self.base_url, json=data, headers=headers, timeout=30)
            
            if response.status_code == 200:
                result: str = response.json()
                return result["choices"][0]["message"]["content"]
            else:
                logger.error(f"GitHub Models API error: {response.status_code} - {response.text}")
                return f"Error: Unable to get response from GitHub Models API"
                
        except Exception as e:
            logger.error(f"LLM invocation failed: {e}")
            return f"Error: {str(e)}"

class MultiAgentCoordinator:
    """Simple multi-agent coordination system"""
    
    def __init__(self):
        self.llm = GitHubModelsLLM()
        self.agents = {}
        self.conversation_history = []
        
        # Initialize agents with their specialized prompts
        self._init_agents()
    
    def _init_agents(self):
        """Initialize specialized agents"""
        self.agents = {
            AgentRole.CODE_ANALYST: {
                "role": "Code Analyst",
                "prompt_prefix": "You are a senior code analyst specializing in DeFi and smart contracts. Analyze code for bugs, vulnerabilities, and improvements. Focus on:",
                "expertise": ["code review", "bug detection", "best practices", "smart contract analysis"]
            },
            AgentRole.CODE_GENERATOR: {
                "role": "Code Generator", 
                "prompt_prefix": "You are an expert code generator specializing in Solidity, DeFi protocols, and flash loans. Generate clean, efficient, and secure code. Focus on:",
                "expertise": ["smart contract development", "Solidity", "DeFi protocols", "flash loans"]
            },
            AgentRole.ARCHITECTURE_DESIGNER: {
                "role": "Architecture Designer",
                "prompt_prefix": "You are a blockchain architecture expert. Design scalable, secure system architectures for DeFi applications. Focus on:",
                "expertise": ["system design", "scalability", "protocol integration", "architecture patterns"]
            },
            AgentRole.SECURITY_AUDITOR: {
                "role": "Security Auditor",
                "prompt_prefix": "You are a blockchain security expert specializing in smart contract auditing. Identify security vulnerabilities and provide recommendations. Focus on:",
                "expertise": ["security vulnerabilities", "smart contract audits", "attack vectors", "security best practices"]
            },
            AgentRole.PERFORMANCE_OPTIMIZER: {
                "role": "Performance Optimizer",
                "prompt_prefix": "You are a performance optimization expert for blockchain applications. Optimize for gas efficiency and execution speed. Focus on:",
                "expertise": ["gas optimization", "performance tuning", "efficiency improvements", "cost reduction"]
            },
            AgentRole.COORDINATOR: {
                "role": "Coordinator",
                "prompt_prefix": "You are a project coordinator who synthesizes input from multiple specialists to provide comprehensive solutions. Focus on:",
                "expertise": ["project coordination", "synthesis", "decision making", "comprehensive solutions"]
            }
        }
    
    async def coordinate_agents(self, task: str, required_roles: List[AgentRole]) -> Dict[str, Any]:
        """Coordinate multiple agents to solve a task"""
        start_time = datetime.now()
        
        logger.info(f"🚀 Starting multi-agent coordination for task: {task[:100]}...")
        
        results = {
            "task": task,
            "agents_involved": [role.value for role in required_roles],
            "phases": [],
            "execution_time": None,
            "final_result": None
        }
        
        # Phase 1: Individual agent analysis
        agent_results = {}
        for role in required_roles:
            if role == AgentRole.COORDINATOR:
                continue  # Coordinator runs last
                
            agent_info = self.agents[role]
            prompt = f"""
{agent_info['prompt_prefix']}
- {', '.join(agent_info['expertise'])}

Task: {task}

Please provide your specialized analysis and recommendations from your expertise perspective.
Be specific, actionable, and focus on your area of specialization.
"""
            
            logger.info(f"🤖 Running {agent_info['role']} analysis...")
            
            try:
                result: str = await self.llm.ainvoke(prompt)
                agent_results[role] = result
                
                results["phases"].append({
                    "phase": f"{agent_info['role']} Analysis",
                    "agent": role.value,
                    "result": result
                })
                
                logger.info(f"✅ {agent_info['role']} completed analysis")
                
            except Exception as e:
                logger.error(f"❌ {agent_info['role']} failed: {e}")
                agent_results[role] = f"Error: {str(e)}"
        
        # Phase 2: Coordinator synthesis
        if AgentRole.COORDINATOR in required_roles and agent_results:
            coordinator_info = self.agents[AgentRole.COORDINATOR]
            
            # Prepare synthesis prompt with all agent results
            synthesis_context = "\n\n".join([
                f"=== {self.agents[role]['role']} Analysis ===\n{result}"
                for role, result in agent_results.items()
            ])
            
            synthesis_prompt = f"""
{coordinator_info['prompt_prefix']}
- {', '.join(coordinator_info['expertise'])}

Original Task: {task}

Here are the specialized analyses from our expert team:

{synthesis_context}

As the coordinator, please:
1. Synthesize all the expert inputs
2. Identify key insights and recommendations
3. Resolve any conflicts between expert opinions
4. Provide a comprehensive, actionable solution
5. Highlight the most critical points for implementation

Provide a well-structured final recommendation that incorporates the best insights from all specialists.
"""
            
            logger.info("🎯 Running Coordinator synthesis...")
            
            try:
                final_result: str = await self.llm.ainvoke(synthesis_prompt)
                results["final_result"] = final_result
                
                results["phases"].append({
                    "phase": "Coordinator Synthesis",
                    "agent": AgentRole.COORDINATOR.value,
                    "result": final_result
                })
                
                logger.info("✅ Coordinator completed synthesis")
                
            except Exception as e:
                logger.error(f"❌ Coordinator synthesis failed: {e}")
                results["final_result"] = f"Synthesis error: {str(e)}"
        
        # Calculate execution time
        end_time = datetime.now()
        results["execution_time"] = str(end_time - start_time)
        
        logger.info(f"🏁 Multi-agent coordination completed in {results['execution_time']}")
        
        return results
    
    def get_agent_status(self) -> Dict[str, Any]:
        """Get status of all agents"""
        return {
            "total_agents": len(self.agents),
            "agents": {
                role.value: {
                    "role": info["role"],
                    "expertise": info["expertise"],
                    "conversation_count": len(self.conversation_history)
                }
                for role, info in self.agents.items()
            }
        }

class SimpleCoordinator:
    """Simple coordinator without database dependency"""
    
    def __init__(self):
        self.multi_agent_llm = None
        self.initialized = False
    
    async def initialize(self) -> bool:
        """Initialize the coordinator"""
        try:
            logger.info("🔧 Initializing Simple GitHub Copilot Coordinator...")
            
            # Check GitHub token
            github_token = os.getenv('GITHUB_TOKEN')
            if not github_token:
                logger.error("❌ GITHUB_TOKEN not found")
                return False
            
            # Initialize multi-agent system
            self.multi_agent_llm = MultiAgentCoordinator()
            logger.info("✅ Multi-agent system initialized")
            
            self.initialized = True
            logger.info("✅ Simple Coordinator initialization complete")
            return True
            
        except Exception as e:
            logger.error(f"❌ Coordinator initialization failed: {e}")
            return False
    
    async def shutdown(self):
        """Shutdown the coordinator"""
        logger.info("🛑 Shutting down Simple Coordinator...")
        self.initialized = False

# Export the coordinator class that the test script expects
EnhancedLangChainCoordinator = SimpleCoordinator
