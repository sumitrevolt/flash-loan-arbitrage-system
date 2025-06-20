"""
Code Interpreter Agent
=====================

Agent specialized in code analysis, execution, and interpretation
for the flash loan arbitrage system.
"""

import asyncio
import logging
import subprocess
import tempfile
import os
import sys
from datetime import datetime
from typing import Dict, List, Optional, Any
import json

from langchain.schema import BaseMessage, HumanMessage, AIMessage
from langchain_core.prompts import ChatPromptTemplate
from langchain_openai import ChatOpenAI

from utils.logger import setup_logger

logger = setup_logger(__name__)

class CodeInterpreterAgent:
    """
    Code Interpreter Agent
    
    Capabilities:
    - Python code execution
    - Smart contract analysis
    - Mathematical calculations
    - Data analysis and visualization
    - Code generation and optimization
    """
    
    def __init__(self, name: str, memory_manager, tool_registry):
        self.name = name
        self.memory_manager = memory_manager
        self.tool_registry = tool_registry
        
        # LLM for code analysis and generation
        self.llm = ChatOpenAI(
            model="gpt-4-turbo-preview",
            temperature=0.1,
            max_tokens=3000
        )
        
        # Execution environment
        self.execution_timeout = 30
        self.allowed_imports = [
            'math', 'numpy', 'pandas', 'matplotlib', 'seaborn',
            'requests', 'json', 'datetime', 'time', 'os',
            'web3', 'eth_account', 'eth_utils'
        ]
        
        # Agent capabilities
        self.capabilities = [
            "code_execution",
            "code_analysis", 
            "mathematical_calculations",
            "data_analysis",
            "contract_analysis",
            "code_optimization"
        ]
        
        self.setup_prompts()
        logger.info(f"💻 Code Interpreter Agent '{name}' initialized")

    def setup_prompts(self):
        """Set up code interpreter prompt templates"""
        
        self.code_analysis_prompt = ChatPromptTemplate.from_messages([
            ("system", """You are a specialized code interpreter agent for flash loan arbitrage analysis.

            Your responsibilities:
            1. Analyze and execute Python code safely
            2. Perform mathematical calculations for arbitrage opportunities
            3. Analyze smart contracts and transaction data
            4. Generate code for specific tasks
            5. Optimize existing code for better performance
            
            Safety guidelines:
            - Only execute safe, sandboxed code
            - Avoid file system operations outside temp directories
            - No network calls unless explicitly needed
            - Validate all inputs before execution
            
            Available libraries: {allowed_imports}
            
            Respond with JSON containing:
            - analysis: Your code analysis
            - execution_plan: Steps to execute if needed
            - safety_assessment: Safety evaluation
            - expected_output: What the code should produce
            - recommendations: Optimization suggestions
            """),
            ("human", "Code to analyze:\n{code}\n\nTask: {task}")
        ])
        
        self.calculation_prompt = ChatPromptTemplate.from_messages([
            ("system", """You are performing mathematical calculations for flash loan arbitrage.
            
            Your task:
            1. Parse the calculation requirements
            2. Generate appropriate Python code
            3. Execute the calculations
            4. Validate results
            5. Provide explanations
            
            Focus on:
            - Profit/loss calculations
            - Gas cost estimations
            - Price impact analysis
            - Risk metrics computation
            - ROI and efficiency metrics
            """),
            ("human", "Calculation request: {request}\nData: {data}")
        ])

    async def initialize(self):
        """Initialize the code interpreter agent"""
        try:
            logger.info(f"💻 Initializing Code Interpreter Agent '{self.name}'...")
            
            # Set up execution environment
            await self.setup_execution_environment()
            
            # Validate Python environment
            await self.validate_environment()
            
            logger.info(f"✅ Code Interpreter Agent '{self.name}' initialization completed")
            
        except Exception as e:
            logger.error(f"❌ Code Interpreter Agent initialization failed: {e}")
            raise

    async def setup_execution_environment(self):
        """Set up the code execution environment"""
        try:
            # Create temp directory for code execution
            self.temp_dir = tempfile.mkdtemp(prefix="flash_loan_code_")
            logger.info(f"📁 Created temp directory: {self.temp_dir}")
            
            # Set up Python path
            if self.temp_dir not in sys.path:
                sys.path.append(self.temp_dir)
            
            logger.info("✅ Execution environment setup completed")
            
        except Exception as e:
            logger.error(f"❌ Execution environment setup failed: {e}")
            raise

    async def validate_environment(self):
        """Validate the Python execution environment"""
        try:
            # Test basic Python execution
            test_code = "print('Code interpreter environment ready')"
            result = await self.execute_code(test_code, safe_mode=True)
            
            if result.get('success', False):
                logger.info("✅ Python execution environment validated")
            else:
                logger.warning(f"⚠️ Environment validation warning: {result.get('error', 'Unknown')}")
            
        except Exception as e:
            logger.error(f"❌ Environment validation failed: {e}")

    async def process(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """Process code interpreter requests within the agent workflow"""
        try:
            messages = state.get("messages", [])
            context = state.get("context", {})
            
            if not messages:
                return state
            
            # Get the latest message
            latest_message = messages[-1]
            request = latest_message.content if hasattr(latest_message, 'content') else str(latest_message)
            
            logger.info(f"💻 Processing code interpreter request: {request[:100]}...")
            
            # Determine request type and process
            result = await self.process_code_request(request, context)
            
            # Create response message
            response_msg = AIMessage(
                content=f"Code Analysis: {result.get('response', 'No response generated')}"
            )
            state["messages"].append(response_msg)
            
            # Update result
            state["result"] = result
            
            return state
            
        except Exception as e:
            logger.error(f"❌ Code interpreter processing failed: {e}")
            error_msg = AIMessage(content=f"Code interpreter error: {str(e)}")
            state["messages"].append(error_msg)
            return state

    async def process_direct(self, request: str, context: Dict[str, Any]) -> Dict[str, Any]:
        """Process a direct code interpreter request"""
        try:
            return await self.process_code_request(request, context)
            
        except Exception as e:
            logger.error(f"❌ Direct code interpreter processing failed: {e}")
            return {
                "response": f"Code interpreter error: {str(e)}",
                "confidence": 0.0,
                "metadata": {"error": str(e)}
            }

    async def process_code_request(self, request: str, context: Dict[str, Any]) -> Dict[str, Any]:
        """Process a code-related request"""
        try:
            # Determine request type
            request_type = self.classify_request(request)
            
            if request_type == "code_analysis":
                return await self.analyze_code(request, context)
            elif request_type == "code_execution":
                return await self.execute_request(request, context)
            elif request_type == "calculation":
                return await self.perform_calculation(request, context)
            elif request_type == "contract_analysis":
                return await self.analyze_contract(request, context)
            else:
                return await self.general_code_assistance(request, context)
                
        except Exception as e:
            logger.error(f"❌ Code request processing failed: {e}")
            return {
                "response": f"Processing error: {str(e)}",
                "confidence": 0.0,
                "metadata": {"error": str(e)}
            }

    def classify_request(self, request: str) -> str:
        """Classify the type of code request"""
        request_lower = request.lower()
        
        if "execute" in request_lower or "run" in request_lower:
            return "code_execution"
        elif "analyze" in request_lower or "review" in request_lower:
            return "code_analysis"
        elif "calculate" in request_lower or "compute" in request_lower:
            return "calculation"
        elif "contract" in request_lower or "solidity" in request_lower:
            return "contract_analysis"
        else:
            return "general"

    async def analyze_code(self, request: str, context: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze code for safety and functionality"""
        try:
            # Extract code from request
            code = self.extract_code_from_request(request)
            
            if not code:
                return {
                    "response": "No code found in the request",
                    "confidence": 0.0,
                    "metadata": {"error": "No code to analyze"}
                }
            
            # Analyze code using LLM
            analysis_input = {
                "code": code,
                "task": request,
                "allowed_imports": ", ".join(self.allowed_imports)
            }
            
            response = await self.llm.ainvoke(
                self.code_analysis_prompt.format_messages(**analysis_input)
            )
            
            # Parse analysis
            analysis = self.parse_analysis_response(response.content)
            
            # Perform safety check
            safety_check = await self.safety_check(code)
            analysis["metadata"]["safety_check"] = safety_check
            
            return analysis
            
        except Exception as e:
            logger.error(f"❌ Code analysis failed: {e}")
            return {
                "response": f"Code analysis error: {str(e)}",
                "confidence": 0.0,
                "metadata": {"error": str(e)}
            }

    async def execute_request(self, request: str, context: Dict[str, Any]) -> Dict[str, Any]:
        """Execute code from the request"""
        try:
            # Extract code from request
            code = self.extract_code_from_request(request)
            
            if not code:
                return {
                    "response": "No executable code found in the request",
                    "confidence": 0.0,
                    "metadata": {"error": "No code to execute"}
                }
            
            # Safety check
            safety_check = await self.safety_check(code)
            if not safety_check.get("safe", False):
                return {
                    "response": f"Code execution blocked: {safety_check.get('reason', 'Safety check failed')}",
                    "confidence": 0.0,
                    "metadata": {"safety_check": safety_check}
                }
            
            # Execute code
            execution_result = await self.execute_code(code)
            
            return {
                "response": f"Code executed. Output: {execution_result.get('output', 'No output')}",
                "confidence": 1.0 if execution_result.get('success', False) else 0.3,
                "metadata": {
                    "execution_result": execution_result,
                    "safety_check": safety_check
                }
            }
            
        except Exception as e:
            logger.error(f"❌ Code execution failed: {e}")
            return {
                "response": f"Code execution error: {str(e)}",
                "confidence": 0.0,
                "metadata": {"error": str(e)}
            }

    async def perform_calculation(self, request: str, context: Dict[str, Any]) -> Dict[str, Any]:
        """Perform mathematical calculations"""
        try:
            # Generate calculation code using LLM
            calc_input = {
                "request": request,
                "data": json.dumps(context, default=str)
            }
            
            response = await self.llm.ainvoke(
                self.calculation_prompt.format_messages(**calc_input)
            )
            
            # Extract code from LLM response
            generated_code = self.extract_code_from_response(response.content)
            
            if not generated_code:
                return {
                    "response": "Could not generate calculation code",
                    "confidence": 0.0,
                    "metadata": {"error": "Code generation failed"}
                }
            
            # Execute calculation
            execution_result = await self.execute_code(generated_code)
            
            return {
                "response": f"Calculation completed. Result: {execution_result.get('output', 'No result')}",
                "confidence": 1.0 if execution_result.get('success', False) else 0.3,
                "metadata": {
                    "generated_code": generated_code,
                    "execution_result": execution_result
                }
            }
            
        except Exception as e:
            logger.error(f"❌ Calculation failed: {e}")
            return {
                "response": f"Calculation error: {str(e)}",
                "confidence": 0.0,
                "metadata": {"error": str(e)}
            }

    async def analyze_contract(self, request: str, context: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze smart contracts"""
        try:
            # Extract contract code or address
            contract_data = self.extract_contract_from_request(request)
            
            if not contract_data:
                return {
                    "response": "No contract data found in the request",
                    "confidence": 0.0,
                    "metadata": {"error": "No contract to analyze"}
                }
            
            # Analyze contract structure, functions, and security
            analysis = await self.perform_contract_analysis(contract_data)
            
            return {
                "response": f"Contract analysis completed: {analysis.get('summary', 'Analysis performed')}",
                "confidence": analysis.get('confidence', 0.5),
                "metadata": analysis
            }
            
        except Exception as e:
            logger.error(f"❌ Contract analysis failed: {e}")
            return {
                "response": f"Contract analysis error: {str(e)}",  
                "confidence": 0.0,
                "metadata": {"error": str(e)}
            }

    async def general_code_assistance(self, request: str, context: Dict[str, Any]) -> Dict[str, Any]:
        """Provide general code assistance"""
        try:
            # Use LLM to provide code assistance
            response = await self.llm.ainvoke([
                HumanMessage(content=f"Provide code assistance for: {request}\nContext: {context}")
            ])
            
            return {
                "response": response.content,
                "confidence": 0.7,
                "metadata": {"type": "general_assistance"}
            }
            
        except Exception as e:
            logger.error(f"❌ General code assistance failed: {e}")
            return {
                "response": f"Code assistance error: {str(e)}",
                "confidence": 0.0,
                "metadata": {"error": str(e)}
            }

    async def execute_code(self, code: str, safe_mode: bool = True) -> Dict[str, Any]:
        """Execute Python code safely"""
        try:
            if safe_mode:
                # Perform safety checks
                safety_result = await self.safety_check(code)
                if not safety_result.get("safe", False):
                    return {
                        "success": False,
                        "error": f"Safety check failed: {safety_result.get('reason', 'Unknown')}",
                        "output": ""
                    }
            
            # Create a temporary file for the code
            with tempfile.NamedTemporaryFile(mode='w', suffix='.py', dir=self.temp_dir, delete=False) as f:
                f.write(code)
                temp_file = f.name
            
            try:
                # Execute the code
                result = subprocess.run(
                    [sys.executable, temp_file],
                    capture_output=True,
                    text=True,
                    timeout=self.execution_timeout,
                    cwd=self.temp_dir
                )
                
                return {
                    "success": result.returncode == 0,
                    "output": result.stdout,
                    "error": result.stderr,
                    "return_code": result.returncode
                }
                
            finally:
                # Clean up temporary file
                try:
                    os.unlink(temp_file)
                except:
                    pass
                    
        except subprocess.TimeoutExpired:
            return {
                "success": False,
                "error": f"Code execution timed out after {self.execution_timeout} seconds",
                "output": ""
            }
        except Exception as e:
            logger.error(f"❌ Code execution failed: {e}")
            return {
                "success": False,
                "error": str(e),
                "output": ""
            }

    async def safety_check(self, code: str) -> Dict[str, Any]:
        """Perform safety checks on code"""
        try:
            import ast
            
            # Parse the code to check for dangerous operations
            try:
                tree = ast.parse(code)
            except SyntaxError as e:
                return {
                    "safe": False,
                    "reason": f"Syntax error: {str(e)}"
                }
            
            # Check for dangerous operations
            dangerous_operations = []
            
            for node in ast.walk(tree):
                # Check for file operations
                if isinstance(node, ast.Call) and isinstance(node.func, ast.Name):
                    if node.func.id in ['open', 'exec', 'eval', '__import__']:
                        dangerous_operations.append(f"Dangerous function: {node.func.id}")
                
                # Check for system operations
                if isinstance(node, ast.Import):
                    for alias in node.names:
                        if alias.name not in self.allowed_imports:
                            dangerous_operations.append(f"Unauthorized import: {alias.name}")
                
                if isinstance(node, ast.ImportFrom):
                    if node.module not in self.allowed_imports:
                        dangerous_operations.append(f"Unauthorized import from: {node.module}")
            
            if dangerous_operations:
                return {
                    "safe": False,
                    "reason": "; ".join(dangerous_operations)
                }
            
            return {
                "safe": True,
                "reason": "Code passed safety checks"
            }
            
        except Exception as e:
            logger.error(f"❌ Safety check failed: {e}")
            return {
                "safe": False,
                "reason": f"Safety check error: {str(e)}"
            }

    def extract_code_from_request(self, request: str) -> str:
        """Extract code blocks from a request"""
        import re
        
        # Look for code blocks marked with ```python or ```
        code_blocks = re.findall(r'```(?:python)?\n(.*?)\n```', request, re.DOTALL)
        if code_blocks:
            return code_blocks[0].strip()
        
        # Look for single-line code after "execute:" or similar
        code_match = re.search(r'(?:execute|run|code):\s*(.+)', request, re.IGNORECASE)
        if code_match:
            return code_match.group(1).strip()
        
        return ""

    def extract_code_from_response(self, response: str) -> str:
        """Extract code from LLM response"""
        import re
        
        # Look for code blocks
        code_blocks = re.findall(r'```(?:python)?\n(.*?)\n```', response, re.DOTALL)
        if code_blocks:
            return code_blocks[0].strip()
        
        return ""

    def extract_contract_from_request(self, request: str) -> Optional[Dict[str, Any]]:
        """Extract smart contract data from request"""
        try:
            # This would be implemented based on specific needs
            # Could extract contract addresses, ABI, or source code
            return None
            
        except Exception as e:
            logger.error(f"❌ Contract extraction failed: {e}")
            return None

    async def perform_contract_analysis(self, contract_data: Dict[str, Any]) -> Dict[str, Any]:
        """Perform detailed smart contract analysis"""
        try:
            # This would implement actual contract analysis
            # For now, return a placeholder
            return {
                "summary": "Contract analysis not yet implemented",
                "confidence": 0.5
            }
            
        except Exception as e:
            logger.error(f"❌ Contract analysis failed: {e}")
            return {
                "summary": f"Contract analysis error: {str(e)}",
                "confidence": 0.0
            }

    def parse_analysis_response(self, response: str) -> Dict[str, Any]:
        """Parse code analysis response"""
        try:
            import json
            import re
            
            # Try to extract JSON from response
            json_match = re.search(r'\{.*\}', response, re.DOTALL)
            if json_match:
                parsed = json.loads(json_match.group())
                return {
                    "response": parsed.get("analysis", response),
                    "confidence": 0.8,
                    "metadata": {
                        "execution_plan": parsed.get("execution_plan", []),
                        "safety_assessment": parsed.get("safety_assessment", {}),
                        "expected_output": parsed.get("expected_output", ""),
                        "recommendations": parsed.get("recommendations", [])
                    }
                }
            
            # Fallback
            return {
                "response": response,
                "confidence": 0.5,
                "metadata": {"parsing_method": "fallback"}
            }
            
        except Exception as e:
            logger.error(f"❌ Failed to parse analysis response: {e}")
            return {
                "response": response,
                "confidence": 0.3,
                "metadata": {"error": str(e)}
            }
