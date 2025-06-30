"""
Cursor API Client for AI Agent Integration
Provides a unified interface to interact with Cursor's API for AI-powered code generation and analysis.
"""

import os
import json
import asyncio
import aiohttp
import logging
from typing import Dict, List, Optional, Any, Union
from dataclasses import dataclass, field
from enum import Enum

logger = logging.getLogger(__name__)

class CursorModel(Enum):
    """Available Cursor models"""
    CURSOR_GPT_4 = "cursor-gpt-4"
    CURSOR_GPT_3_5 = "cursor-gpt-3.5-turbo"
    CURSOR_CLAUDE = "cursor-claude"
    CURSOR_GEMINI = "cursor-gemini"

@dataclass
class CursorConfig:
    """Configuration for Cursor API client"""
    api_key: str
    base_url: str = "https://api.cursor.com/v1"
    organization_id: Optional[str] = None
    project_id: Optional[str] = None
    model: str = "cursor-gpt-4"
    max_tokens: int = 4096
    temperature: float = 0.1
    timeout: int = 30
    max_retries: int = 3
    
    @classmethod
    def from_env(cls) -> 'CursorConfig':
        """Create configuration from environment variables"""
        return cls(
            api_key=os.getenv('CURSOR_API_KEY', ''),
            base_url=os.getenv('CURSOR_BASE_URL', 'https://api.cursor.com/v1'),
            organization_id=os.getenv('CURSOR_ORGANIZATION_ID'),
            project_id=os.getenv('CURSOR_PROJECT_ID'),
            model=os.getenv('CURSOR_MODEL', 'cursor-gpt-4'),
            max_tokens=int(os.getenv('CURSOR_MAX_TOKENS', '4096')),
            temperature=float(os.getenv('CURSOR_TEMPERATURE', '0.1')),
            timeout=int(os.getenv('CURSOR_TIMEOUT', '30')),
            max_retries=int(os.getenv('CURSOR_MAX_RETRIES', '3'))
        )

@dataclass
class CursorMessage:
    """Message structure for Cursor API"""
    role: str  # "system", "user", "assistant"
    content: str
    name: Optional[str] = None
    function_call: Optional[Dict[str, Any]] = None

@dataclass
class CursorResponse:
    """Response from Cursor API"""
    content: str
    model: str
    usage: Dict[str, int]
    finish_reason: str
    response_time: float
    metadata: Dict[str, Any] = field(default_factory=dict)

class CursorAPIError(Exception):
    """Custom exception for Cursor API errors"""
    def __init__(self, message: str, status_code: Optional[int] = None, response: Optional[Dict[str, Any]] = None):
        super().__init__(message)
        self.status_code = status_code
        self.response = response

class CursorAPIClient:
    """Async client for interacting with Cursor API"""
    
    def __init__(self, config: CursorConfig):
        self.config = config
        self.session: Optional[aiohttp.ClientSession] = None
        self._setup_logging()
    
    def _setup_logging(self):
        """Setup logging for the client"""
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
    
    async def __aenter__(self):
        """Async context manager entry"""
        await self.start_session()
        return self
    
    async def __aexit__(self, exc_type: Optional[type], exc_val: Optional[BaseException], exc_tb: Optional[Any]):
        """Async context manager exit"""
        await self.close_session()
    
    async def start_session(self):
        """Start the HTTP session"""
        if self.session is None:
            connector = aiohttp.TCPConnector(limit=100, limit_per_host=30)
            timeout = aiohttp.ClientTimeout(total=self.config.timeout)
            self.session = aiohttp.ClientSession(
                connector=connector,
                timeout=timeout,
                headers=self._get_headers()
            )
            logger.info("Cursor API session started")
    
    async def close_session(self):
        """Close the HTTP session"""
        if self.session:
            await self.session.close()
            self.session = None
            logger.info("Cursor API session closed")
    
    def _get_headers(self) -> Dict[str, str]:
        """Get headers for API requests"""
        headers = {
            "Authorization": f"Bearer {self.config.api_key}",
            "Content-Type": "application/json",
            "User-Agent": "flash-loan-ai-agents/1.0"
        }
        
        if self.config.organization_id:
            headers["OpenAI-Organization"] = self.config.organization_id
        
        if self.config.project_id:
            headers["OpenAI-Project"] = self.config.project_id
        
        return headers
    
    async def chat_completion(
        self,
        messages: List[CursorMessage],
        model: Optional[str] = None,
        max_tokens: Optional[int] = None,
        temperature: Optional[float] = None,
        stream: bool = False,
        tools: Optional[List[Dict[str, Any]]] = None,
        tool_choice: Optional[str] = None
    ) -> CursorResponse:
        """Send a chat completion request to Cursor API"""
        
        if not self.session:
            await self.start_session()
        
        payload = {
            "model": model or self.config.model,
            "messages": [
                {
                    "role": msg.role,
                    "content": msg.content,
                    **({"name": msg.name} if msg.name else {}),
                    **({"function_call": msg.function_call} if msg.function_call else {})
                }
                for msg in messages
            ],
            "max_tokens": max_tokens or self.config.max_tokens,
            "temperature": temperature or self.config.temperature,
            "stream": stream
        }
        
        if tools:
            payload["tools"] = tools
        if tool_choice:
            payload["tool_choice"] = tool_choice
        
        url = f"{self.config.base_url}/chat/completions"
        
        for attempt in range(self.config.max_retries):
            try:
                logger.info(f"Sending request to Cursor API (attempt {attempt + 1})")
                start_time = asyncio.get_event_loop().time()
                
                async with self.session.post(url, json=payload) as response:
                    end_time = asyncio.get_event_loop().time()
                    response_time = end_time - start_time
                    
                    if response.status == 200:
                        data = await response.json()
                        return self._parse_response(data, response_time)
                    
                    elif response.status == 429:  # Rate limit
                        wait_time = 2 ** attempt
                        logger.warning(f"Rate limited, waiting {wait_time} seconds")
                        await asyncio.sleep(wait_time)
                        continue
                    
                    else:
                        error_data = await response.text()
                        raise CursorAPIError(
                            f"API request failed with status {response.status}",
                            status_code=response.status,
                            response={"error": error_data}
                        )
            
            except aiohttp.ClientError as e:
                logger.error(f"Network error on attempt {attempt + 1}: {e}")
                if attempt == self.config.max_retries - 1:
                    raise CursorAPIError(f"Network error after {self.config.max_retries} attempts: {e}")
                await asyncio.sleep(2 ** attempt)
        
        raise CursorAPIError(f"Failed after {self.config.max_retries} attempts")
    
    def _parse_response(self, data: Dict[str, Any], response_time: float) -> CursorResponse:
        """Parse the API response"""
        try:
            choice = data["choices"][0]
            message = choice["message"]
            
            return CursorResponse(
                content=message["content"],
                model=data["model"],
                usage=data.get("usage", {}),
                finish_reason=choice["finish_reason"],
                response_time=response_time,
                metadata={"raw_response": data}
            )
        except (KeyError, IndexError) as e:
            raise CursorAPIError(f"Invalid response format: {e}", response=data)
    
    async def code_generation(
        self,
        prompt: str,
        language: str = "python",
        context: Optional[str] = None,
        requirements: Optional[List[str]] = None
    ) -> CursorResponse:
        """Generate code using Cursor API"""
        
        system_message = CursorMessage(
            role="system",
            content=f"""You are an expert {language} developer working on a flash loan arbitrage system. 
            Generate high-quality, production-ready code that follows best practices.
            Include proper error handling, documentation, and type hints where applicable."""
        )
        
        user_content = f"Generate {language} code for: {prompt}"
        
        if context:
            user_content += f"\n\nContext: {context}"
        
        if requirements:
            user_content += f"\n\nRequirements: {', '.join(requirements)}"
        
        user_message = CursorMessage(role="user", content=user_content)
        
        return await self.chat_completion([system_message, user_message])
    
    async def code_analysis(
        self,
        code: str,
        analysis_type: str = "review",
        language: str = "python"
    ) -> CursorResponse:
        """Analyze code using Cursor API"""
        
        system_message = CursorMessage(
            role="system",
            content=f"""You are a senior {language} code reviewer specializing in DeFi and flash loan systems.
            Provide thorough {analysis_type} focusing on security, efficiency, and best practices."""
        )
        
        user_message = CursorMessage(
            role="user",
            content=f"Please analyze this {language} code:\n\n```{language}\n{code}\n```"
        )
        
        return await self.chat_completion([system_message, user_message])
    
    async def smart_contract_audit(
        self,
        contract_code: str,
        contract_type: str = "arbitrage"
    ) -> CursorResponse:
        """Audit smart contract code using Cursor API"""
        
        system_message = CursorMessage(
            role="system",
            content="""You are a blockchain security expert specializing in smart contract audits.
            Analyze the provided contract for security vulnerabilities, gas optimization opportunities,
            and compliance with best practices. Focus on flash loan specific risks."""
        )
        
        user_message = CursorMessage(
            role="user",
            content=f"Please audit this {contract_type} smart contract:\n\n```solidity\n{contract_code}\n```"
        )
        
        return await self.chat_completion([system_message, user_message])
    
    async def health_check(self) -> bool:
        """Check if the Cursor API is accessible"""
        try:
            if not self.session:
                await self.start_session()
            
            # Simple health check with a minimal request
            messages = [CursorMessage(role="user", content="Hello")]
            response = await self.chat_completion(messages, max_tokens=10)
            return True
        except Exception as e:
            logger.error(f"Health check failed: {e}")
            return False

# Factory function for easy instantiation
def create_cursor_client(config: Optional[CursorConfig] = None) -> CursorAPIClient:
    """Create a Cursor API client with configuration"""
    if config is None:
        config = CursorConfig.from_env()
    
    if not config.api_key:
        raise ValueError("Cursor API key is required. Set CURSOR_API_KEY environment variable.")
    
    return CursorAPIClient(config)

# Convenience function for synchronous usage
def get_cursor_response(prompt: str, **kwargs) -> str:
    """Get a simple response from Cursor API (synchronous wrapper)"""
    async def _get_response():
        async with create_cursor_client() as client:
            messages = [CursorMessage(role="user", content=prompt)]
            response = await client.chat_completion(messages, **kwargs)
            return response.content
    
    return asyncio.run(_get_response())

if __name__ == "__main__":
    # Example usage
    async def main():
        config = CursorConfig.from_env()
        
        async with create_cursor_client(config) as client:
            # Health check
            if await client.health_check():
                print("✅ Cursor API is accessible")
            else:
                print("❌ Cursor API is not accessible")
                return
            
            # Code generation example
            response = await client.code_generation(
                prompt="Create a function to validate flash loan profitability",
                language="python",
                requirements=["Use type hints", "Include error handling"]
            )
            
            print("Generated code:")
            print(response.content)
            print(f"Response time: {response.response_time:.2f}s")
    
    # Run example if script is executed directly
    asyncio.run(main()) 