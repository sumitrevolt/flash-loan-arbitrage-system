#!/usr/bin/env python3
"""
Productivity Interface for Flash Loan Development
================================================

This module provides an easy-to-use interface for accessing
productivity features including auto-completion, code analysis,
and continuous monitoring.
"""

import asyncio
import os
from typing import List, Dict, Any, Optional, Tuple
from pathlib import Path
import json

from enhanced_langchain_orchestrator import (
    EnhancedLangChainOrchestrator,
    IntelligentCodeAnalyzer,
    AutoCompletionEngine,
    CodeAnalysisResult
)

class FlashLoanProductivityInterface:
    """Simple interface for productivity features"""
    
    def __init__(self):
        self.orchestrator = None
        self.analyzer = IntelligentCodeAnalyzer()
        self.completion_engine = AutoCompletionEngine()
        self._running = False
    
    async def start(self):
        """Start productivity features"""
        print("🚀 Starting Flash Loan Productivity System...")
        
        # Initialize orchestrator
        self.orchestrator = EnhancedLangChainOrchestrator()
        await self.orchestrator.initialize()
        
        self._running = True
        
        print("✅ Productivity features are now active!")
        print("\n📝 Available commands:")
        print("  - complete <code>: Get code completions")
        print("  - analyze <file>: Analyze a Python file")
        print("  - metrics: Show productivity metrics")
        print("  - stop: Stop the system")
    
    async def get_completions(self, code_snippet: str, line: int = 1, column: int = 0) -> List[Dict]:
        """Get code completions for a snippet"""
        completions = await self.completion_engine.get_completions(
            code_snippet, (line, column)
        )
        return completions
    
    async def analyze_file(self, file_path: str) -> CodeAnalysisResult:
        """Analyze a Python file"""
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"File not found: {file_path}")
        
        result = await self.analyzer.analyze_code_continuously(file_path)
        return result
    
    async def get_metrics(self) -> Dict[str, Any]:
        """Get productivity metrics"""
        if self.orchestrator:
            return await self.orchestrator.get_productivity_metrics()
        return {}
    
    def stop(self):
        """Stop productivity features"""
        self._running = False
        print("🛑 Productivity system stopped")

async def interactive_mode():
    """Run in interactive mode"""
    interface = FlashLoanProductivityInterface()
    await interface.start()
    
    while interface._running:
        try:
            command = input("\n> ").strip()
            
            if command == "stop":
                interface.stop()
                break
            
            elif command.startswith("complete "):
                code = command[9:]
                completions = await interface.get_completions(code)
                print("\n🔮 Completions:")
                for i, comp in enumerate(completions[:5], 1):
                    print(f"  {i}. {comp['text']} ({comp['type']})")
            
            elif command.startswith("analyze "):
                file_path = command[8:].strip()
                result = await interface.analyze_file(file_path)
                print(f"\n📊 Analysis for {file_path}:")
                print(f"  Issues: {len(result.issues)}")
                print(f"  Suggestions: {len(result.suggestions)}")
                print(f"  Complexity: {result.complexity_score:.2f}")
                print(f"  Maintainability: {result.maintainability_index:.2f}")
                
                if result.issues:
                    print("\n  Top issues:")
                    for issue in result.issues[:3]:
                        print(f"    - {issue['message']} (line {issue.get('line', 'N/A')})")
            
            elif command == "metrics":
                metrics = await interface.get_metrics()
                print("\n📈 Productivity Metrics:")
                print(f"  Score: {metrics.get('score', 0):.1f}/100")
                print(f"  Project files: {metrics.get('project_insights', {}).get('total_files', 0)}")
                print(f"  Total issues: {metrics.get('project_insights', {}).get('total_issues', 0)}")
            
            elif command == "help":
                print("\n📝 Available commands:")
                print("  - complete <code>: Get code completions")
                print("  - analyze <file>: Analyze a Python file")
                print("  - metrics: Show productivity metrics")
                print("  - stop: Stop the system")
            
            else:
                print("❓ Unknown command. Type 'help' for available commands.")
        
        except KeyboardInterrupt:
            print("\n\nUse 'stop' command to exit gracefully")
        except Exception as e:
            print(f"❌ Error: {e}")

def main():
    """Main entry point"""
    print("🎯 Flash Loan Development Productivity System")
    print("=" * 50)
    
    # Run in event loop
    asyncio.run(interactive_mode())

if __name__ == "__main__":
    main()
