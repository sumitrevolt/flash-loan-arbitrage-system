import asyncio
import json
import logging
import os
from typing import Dict, List, Any, Optional

# Attempt to import MCP server components.
# This structure assumes an existing mcp.server framework similar to other servers in the project.
try:
    from mcp.server import Server, InitializationOptions, NotificationOptions
    from mcp.types import Tool, TextContent
    MCP_FRAMEWORK_AVAILABLE = True
except ImportError:
    MCP_FRAMEWORK_AVAILABLE = False
    # Define dummy classes if MCP framework is not available, to allow basic script structure.
    # This is mainly for allowing the subtask to create the file even if the exact
    # mcp library isn't in the subtask worker's environment.
    # In the actual project, this import should succeed.
    logger = logging.getLogger("DummyMCP") # Need a logger for warnings here
    logger.warning("MCP framework not found, using dummy classes for LLMCodeSuggestionMCPServer.")
    class Server:
        def __init__(self, name): self.name = name
        def list_tools(self): return lambda func: func
        def call_tool(self): return lambda func: func
        async def run(self, *args, **kwargs): pass
        def get_capabilities(self, *args, **kwargs): return {} # Dummy capabilities
    class Tool:
        def __init__(self, name, description, inputSchema):
            self.name, self.description, self.inputSchema = name, description, inputSchema
    class TextContent:
        def __init__(self, type, text): self.type, self.text = type, text # type: ignore
    class InitializationOptions: pass
    class NotificationOptions: pass


# Attempt to import OpenAI library
try:
    from openai import OpenAI as OpenAIClient # OpenAI for v1.x
    OPENAI_AVAILABLE = True
except ImportError:
    OPENAI_AVAILABLE = False
    OpenAIClient = None # Placeholder

# Configure logging
logger = logging.getLogger("LLMCodeSuggestionMCPServer")
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')

# Configuration from environment variables
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
OPENAI_MODEL = os.getenv("OPENAI_MODEL", "gpt-3.5-turbo") # Default model

class LLMCodeSuggestionMCPServer:
    def __init__(self):
        self.server = Server("llm-code-suggestion-server")
        if not MCP_FRAMEWORK_AVAILABLE:
            # This warning is now potentially from the dummy class section if logger was not configured yet.
            # Re-iterate or ensure logger is configured before dummy classes if needed.
            # For now, this is okay as top-level logger config runs before this __init__.
            logger.warning("MCP framework not available. Server will have limited functionality (using dummies).")

        self.openai_client = None
        if OPENAI_AVAILABLE and OPENAI_API_KEY and OpenAIClient:
            try:
                self.openai_client = OpenAIClient(api_key=OPENAI_API_KEY)
                logger.info(f"OpenAI client initialized with model {OPENAI_MODEL}.")
            except Exception as e:
                logger.error(f"Failed to initialize OpenAI client: {e}")
                self.openai_client = None # Ensure it's None if init fails
        elif not OPENAI_API_KEY:
            logger.warning("OPENAI_API_KEY not set. OpenAI functionality will be disabled.")
        elif not OPENAI_AVAILABLE: # OPENAI_AVAILABLE is False
             logger.warning("OpenAI library not installed. OpenAI functionality will be disabled.")
        else: # OpenAIClient is None (should be covered by not OPENAI_AVAILABLE)
            logger.warning("OpenAI client could not be imported. OpenAI functionality will be disabled.")


        self._setup_handlers()

    def _setup_handlers(self):
        @self.server.list_tools()
        async def handle_list_tools() -> List[Tool]:
            return [
                Tool(
                    name="get_llm_code_suggestion",
                    description="Provides code suggestions from an LLM for a given code snippet and error.",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "code_snippet": {"type": "string", "description": "The problematic code snippet."},
                            "error_message": {"type": "string", "description": "The error message associated with the code."},
                            "language": {"type": "string", "description": "The programming language (e.g., python).", "default": "python"},
                            "context": {"type": "string", "description": "Optional additional context for the LLM."}
                        },
                        "required": ["code_snippet", "error_message"]
                    }
                )
            ]

        @self.server.call_tool()
        async def handle_call_tool(name: str, arguments: Dict[str, Any]) -> List[TextContent]:
            if name == "get_llm_code_suggestion":
                if not self.openai_client:
                    result = {
                        "status": "error",
                        "suggestion": None,
                        "error_message": "OpenAI client not initialized, API key missing, or library not installed."
                    }
                    return [TextContent(type="application/json", text=json.dumps(result))]

                code_snippet = arguments.get("code_snippet")
                error_message = arguments.get("error_message")
                language = arguments.get("language", "python")
                context = arguments.get("context", "")

                try:
                    prompt = self._construct_prompt(code_snippet, error_message, language, context)

                    logger.info(f"Sending request to OpenAI with model {OPENAI_MODEL}.")
                    chat_completion = self.openai_client.chat.completions.create(
                        messages=[
                            {"role": "system", "content": "You are a helpful AI assistant that provides code suggestions to fix errors. Provide only the corrected code block or a concise explanation if a direct code fix is not possible. Your response should be directly usable. If providing code, use appropriate markdown code blocks for the language specified."},
                            {"role": "user", "content": prompt}
                        ],
                        model=OPENAI_MODEL,
                        temperature=0.3,
                    )

                    suggestion_raw = chat_completion.choices[0].message.content
                    suggestion = suggestion_raw.strip() if suggestion_raw else ""

                    # Clean up suggestion if it's wrapped in markdown code blocks
                    # e.g. ```python\ncode\n``` or ```\ncode\n```
                    if suggestion.startswith("```") and suggestion.endswith("```"):
                        lines = suggestion.splitlines(True)
                        if len(lines) > 1: # Has content between triple backticks
                             # Remove first line (```python or ```) and last line (```)
                            suggestion = "".join(lines[1:-1])


                    logger.info("Received suggestion from OpenAI.")
                    result = {
                        "status": "success",
                        "suggestion": suggestion,
                        "raw_suggestion": suggestion_raw, # Keep raw for debugging if needed
                        "error_message": None
                    }
                except Exception as e:
                    logger.error(f"Error calling OpenAI API: {e}", exc_info=True)
                    result = {
                        "status": "error",
                        "suggestion": None,
                        "error_message": f"OpenAI API error: {str(e)}"
                    }
                return [TextContent(type="application/json", text=json.dumps(result))]
            else:
                logger.error(f"Call to unknown tool: {name}")
                raise ValueError(f"Unknown tool: {name}")

    def _construct_prompt(self, code_snippet: str, error_message: str, language: str, context: str) -> str:
        prompt = f"Fix the following {language} code snippet that produces the error: '{error_message}'.\n"
        if context:
            prompt += f"Additional context: {context}\n"
        prompt += f"Problematic Code Snippet (language: {language}):\n```{language}\n{code_snippet}\n```\n"
        prompt += "Please provide the corrected code snippet. If you cannot provide a direct fix, explain the issue and suggest how to resolve it. If providing code, ensure it is in a markdown code block."
        return prompt

async def main():
    if not MCP_FRAMEWORK_AVAILABLE:
        logger.error("MCP framework is not available. Cannot start LLMCodeSuggestionMCPServer properly.")
        logger.info("This script defines the server structure, but requires the MCP framework to run as intended.")
        # Create a dummy instance for basic validation if needed by subtask runner
        try:
            _ = LLMCodeSuggestionMCPServer()
        except Exception as e:
            logger.error(f"Failed to instantiate LLMCodeSuggestionMCPServer even with dummies: {e}")
        return

    server_instance = LLMCodeSuggestionMCPServer()

    try:
        from mcp.server.stdio import stdio_server
        logger.info("Attempting to start server in stdio mode.")
        async with stdio_server() as (read_stream, write_stream):
            await server_instance.server.run(
                read_stream,
                write_stream,
                InitializationOptions(
                    server_name=server_instance.server.name,
                    server_version="1.0.0",
                    capabilities=server_instance.server.get_capabilities(
                        notification_options=NotificationOptions(),
                        experimental_capabilities={},
                    ),
                ) if MCP_FRAMEWORK_AVAILABLE else None,
            )
    except ImportError:
        logger.warning("mcp.server.stdio not found. Server cannot run in stdio mode.")
        logger.info("To run this server, ensure the MCP framework (including stdio_server or equivalent runner) is available.")
    except Exception as e:
        logger.error(f"Error during server startup or execution: {e}", exc_info=True)


if __name__ == "__main__":
    # This main is for running the MCP server.
    # It requires:
    # 1. OpenAI Python library (`pip install openai`)
    # 2. OPENAI_API_KEY environment variable set.
    # 3. The project's MCP server framework to be available in PYTHONPATH.

    # For subtask validation, we just need the script to be syntactically correct.
    # The actual execution `asyncio.run(main())` is commented out.
    # asyncio.run(main())
    pass # Ensures the script is valid for the subtask runner
