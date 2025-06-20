#!/usr/bin/env python3
"""
GitHub Copilot Integration and Training System
==============================================

Advanced system for training AI agents with GitHub Copilot data
and integrating Copilot capabilities into the multi-agent system.
"""

import asyncio
import logging
import json
import os
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass, field
import uuid
import subprocess
import tempfile
import shutil

# Enhanced imports
import requests
import aiohttp
import aiofiles
from git import Repo
import openai

# LangChain imports
from langchain.schema import Document
from langchain_community.vectorstores import FAISS
from langchain_community.embeddings import HuggingFaceEmbeddings
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_community.document_loaders import TextLoader, DirectoryLoader

logger = logging.getLogger(__name__)

@dataclass
class CopilotTrainingData:
    """Structure for Copilot training data"""
    code_snippet: str
    context: str
    language: str
    file_path: str
    suggestions: List[str] = field(default_factory=list)
    quality_score: float = 0.0
    timestamp: datetime = field(default_factory=datetime.now)
    metadata: Dict[str, Any] = field(default_factory=dict)

@dataclass
class TrainingSession:
    """Training session information"""
    session_id: str
    start_time: datetime
    end_time: Optional[datetime] = None
    total_samples: int = 0
    processed_samples: int = 0
    success_rate: float = 0.0
    errors: List[str] = field(default_factory=list)
    status: str = "active"

class GitHubCopilotTrainer:
    """Advanced GitHub Copilot integration and training system"""
    
    def __init__(self, project_root: str = None):
        self.project_root = Path(project_root) if project_root else Path.cwd()
        self.training_data_path = self.project_root / "training_data"
        self.models_path = self.project_root / "models"
        self.logs_path = self.project_root / "logs"
        
        # Create directories
        self.training_data_path.mkdir(exist_ok=True)
        self.models_path.mkdir(exist_ok=True)
        self.logs_path.mkdir(exist_ok=True)
        
        # Initialize components
        self.embeddings = None
        self.vectorstore = None
        self.training_sessions = {}
        self.copilot_cache = {}
        
        # Initialize embeddings
        self._initialize_embeddings()
    
    def _initialize_embeddings(self):
        """Initialize text embeddings for training data"""
        try:
            self.embeddings = HuggingFaceEmbeddings(
                model_name="sentence-transformers/all-MiniLM-L6-v2"
            )
            logger.info("✅ Embeddings initialized successfully")
        except Exception as e:
            logger.error(f"❌ Failed to initialize embeddings: {e}")
    
    async def collect_training_data_from_project(self) -> List[CopilotTrainingData]:
        """Collect training data from the current project"""
        logger.info("📊 Collecting training data from project...")
        
        training_data = []
        
        # File extensions to process
        code_extensions = {
            '.py': 'python',
            '.js': 'javascript',
            '.ts': 'typescript',
            '.sol': 'solidity',
            '.json': 'json',
            '.yaml': 'yaml',
            '.yml': 'yaml',
            '.md': 'markdown',
            '.dockerfile': 'dockerfile',
            '.sh': 'bash',
            '.ps1': 'powershell'
        }
        
        # Walk through project directory
        for root, dirs, files in os.walk(self.project_root):
            # Skip certain directories
            skip_dirs = {'node_modules', '__pycache__', '.git', 'venv', '.venv', 'build', 'dist'}
            dirs[:] = [d for d in dirs if d not in skip_dirs]
            
            for file in files:
                file_path = Path(root) / file
                file_ext = file_path.suffix.lower()
                
                if file_ext in code_extensions:
                    try:
                        # Read file content
                        async with aiofiles.open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                            content = await f.read()
                        
                        # Create training data entry
                        training_entry = CopilotTrainingData(
                            code_snippet=content,
                            context=f"File: {file_path.relative_to(self.project_root)}",
                            language=code_extensions[file_ext],
                            file_path=str(file_path),
                            metadata={
                                'file_size': len(content),
                                'line_count': content.count('\n') + 1,
                                'extension': file_ext
                            }
                        )
                        
                        training_data.append(training_entry)
                        
                    except Exception as e:
                        logger.warning(f"⚠️ Could not read file {file_path}: {e}")
        
        logger.info(f"📊 Collected {len(training_data)} training samples")
        return training_data
    
    async def generate_copilot_suggestions(self, code_context: str, language: str = "python") -> List[str]:
        """Generate suggestions using GitHub Copilot-like approach"""
        logger.info(f"💡 Generating suggestions for {language} code...")
        
        # This would integrate with actual GitHub Copilot API
        # For now, we'll simulate intelligent suggestions
        
        suggestions = []
        
        # Language-specific suggestions
        if language == "python":
            suggestions.extend([
                "Add type hints to function parameters",
                "Implement error handling with try-except blocks",
                "Add docstrings for better documentation",
                "Use async/await for I/O operations",
                "Implement logging for debugging",
                "Add input validation",
                "Consider using dataclasses for structured data",
                "Implement unit tests",
                "Use context managers for resource handling",
                "Add configuration management"
            ])
        elif language == "javascript" or language == "typescript":
            suggestions.extend([
                "Add proper error handling",
                "Use async/await instead of callbacks",
                "Implement proper TypeScript types",
                "Add JSDoc comments",
                "Use proper dependency injection",
                "Implement proper state management",
                "Add input validation",
                "Use modern ES6+ features",
                "Implement proper error boundaries",
                "Add comprehensive testing"
            ])
        elif language == "solidity":
            suggestions.extend([
                "Add proper access modifiers",
                "Implement reentrancy guards",
                "Add proper error messages",
                "Use events for important state changes",
                "Implement proper gas optimization",
                "Add comprehensive testing",
                "Use proper inheritance patterns",
                "Implement proper upgradability",
                "Add security checks",
                "Use proper data structures"
            ])
        
        # Analyze code context for specific suggestions
        context_lower = code_context.lower()
        
        if "function" in context_lower or "def " in context_lower:
            suggestions.append("Consider breaking down large functions into smaller ones")
        
        if "import" in context_lower or "require" in context_lower:
            suggestions.append("Organize imports/dependencies properly")
        
        if "class" in context_lower:
            suggestions.append("Consider using composition over inheritance")
        
        if "async" in context_lower:
            suggestions.append("Ensure proper error handling in async functions")
        
        # Filter and return unique suggestions
        unique_suggestions = list(set(suggestions))
        return unique_suggestions[:10]  # Return top 10 suggestions
    
    async def train_agent_with_copilot_data(self, training_data: List[CopilotTrainingData]) -> TrainingSession:
        """Train AI agents using Copilot-enhanced data"""
        session_id = str(uuid.uuid4())
        session = TrainingSession(
            session_id=session_id,
            start_time=datetime.now(),
            total_samples=len(training_data)
        )
        
        logger.info(f"🎓 Starting training session {session_id} with {len(training_data)} samples")
        
        # Process training data
        processed_data = []
        
        for i, data in enumerate(training_data):
            try:
                # Generate suggestions for this code
                suggestions = await self.generate_copilot_suggestions(
                    data.code_snippet, 
                    data.language
                )
                
                # Update training data with suggestions
                data.suggestions = suggestions
                data.quality_score = self._calculate_quality_score(data)
                
                processed_data.append(data)
                session.processed_samples += 1
                
                if i % 10 == 0:
                    logger.info(f"📊 Processed {i+1}/{len(training_data)} samples")
                
            except Exception as e:
                session.errors.append(f"Error processing sample {i}: {str(e)}")
                logger.error(f"❌ Error processing training sample {i}: {e}")
        
        # Calculate success rate
        session.success_rate = session.processed_samples / session.total_samples if session.total_samples > 0 else 0
        session.end_time = datetime.now()
        session.status = "completed"
        
        # Store training session
        self.training_sessions[session_id] = session
        
        # Save processed training data
        await self._save_training_data(processed_data, session_id)
        
        # Create vector store from training data
        await self._create_vector_store(processed_data)
        
        logger.info(f"✅ Training session {session_id} completed with {session.success_rate:.2%} success rate")
        return session
    
    def _calculate_quality_score(self, data: CopilotTrainingData) -> float:
        """Calculate quality score for training data"""
        score = 0.0
        
        # Base score for having content
        if data.code_snippet:
            score += 0.3
        
        # Bonus for having documentation
        if any(keyword in data.code_snippet.lower() for keyword in ['"""', "'''", '//', '/*', '#']):
            score += 0.2
        
        # Bonus for having proper structure
        if any(keyword in data.code_snippet for keyword in ['class', 'function', 'def', 'async', 'import']):
            score += 0.2
        
        # Bonus for having error handling
        if any(keyword in data.code_snippet.lower() for keyword in ['try', 'except', 'catch', 'error']):
            score += 0.2
        
        # Bonus for having tests
        if any(keyword in data.code_snippet.lower() for keyword in ['test', 'assert', 'expect']):
            score += 0.1
        
        return min(score, 1.0)
    
    async def _save_training_data(self, training_data: List[CopilotTrainingData], session_id: str):
        """Save training data to file"""
        file_path = self.training_data_path / f"training_session_{session_id}.json"
        
        # Convert to serializable format
        serializable_data = []
        for data in training_data:
            serializable_data.append({
                'code_snippet': data.code_snippet,
                'context': data.context,
                'language': data.language,
                'file_path': data.file_path,
                'suggestions': data.suggestions,
                'quality_score': data.quality_score,
                'timestamp': data.timestamp.isoformat(),
                'metadata': data.metadata
            })
        
        async with aiofiles.open(file_path, 'w', encoding='utf-8') as f:
            await f.write(json.dumps(serializable_data, indent=2))
        
        logger.info(f"💾 Training data saved to {file_path}")
    
    async def _create_vector_store(self, training_data: List[CopilotTrainingData]):
        """Create vector store from training data"""
        if not self.embeddings:
            logger.warning("⚠️ Embeddings not available, skipping vector store creation")
            return
        
        try:
            # Prepare documents
            documents = []
            for data in training_data:
                doc = Document(
                    page_content=data.code_snippet,
                    metadata={
                        'language': data.language,
                        'file_path': data.file_path,
                        'context': data.context,
                        'quality_score': data.quality_score,
                        'suggestions': data.suggestions
                    }
                )
                documents.append(doc)
            
            # Create vector store
            self.vectorstore = FAISS.from_documents(documents, self.embeddings)
            
            # Save vector store
            vector_store_path = self.models_path / "copilot_vectorstore"
            self.vectorstore.save_local(str(vector_store_path))
            
            logger.info(f"🗃️ Vector store created and saved to {vector_store_path}")
            
        except Exception as e:
            logger.error(f"❌ Failed to create vector store: {e}")
    
    async def get_contextual_suggestions(self, code_context: str, language: str = "python") -> Dict[str, Any]:
        """Get contextual suggestions based on training data"""
        if not self.vectorstore:
            logger.warning("⚠️ Vector store not available, generating basic suggestions")
            return {
                "suggestions": await self.generate_copilot_suggestions(code_context, language),
                "confidence": 0.5,
                "source": "basic_generator"
            }
        
        try:
            # Search for similar code in vector store
            similar_docs = self.vectorstore.similarity_search(code_context, k=5)
            
            # Aggregate suggestions from similar documents
            all_suggestions = []
            quality_scores = []
            
            for doc in similar_docs:
                if 'suggestions' in doc.metadata:
                    all_suggestions.extend(doc.metadata['suggestions'])
                    quality_scores.append(doc.metadata.get('quality_score', 0.5))
            
            # Remove duplicates and rank suggestions
            unique_suggestions = list(set(all_suggestions))
            
            # Generate additional suggestions
            generated_suggestions = await self.generate_copilot_suggestions(code_context, language)
            
            # Combine and rank
            combined_suggestions = list(set(unique_suggestions + generated_suggestions))
            
            # Calculate confidence based on quality scores
            confidence = sum(quality_scores) / len(quality_scores) if quality_scores else 0.5
            
            return {
                "suggestions": combined_suggestions[:15],  # Top 15 suggestions
                "confidence": confidence,
                "source": "vector_store_enhanced",
                "similar_examples": len(similar_docs)
            }
            
        except Exception as e:
            logger.error(f"❌ Error getting contextual suggestions: {e}")
            return {
                "suggestions": await self.generate_copilot_suggestions(code_context, language),
                "confidence": 0.3,
                "source": "fallback_generator"
            }
    
    async def analyze_code_patterns(self, file_path: str = "") -> Dict[str, Any]:
        """Analyze code patterns in the project"""
        logger.info("🔍 Analyzing code patterns...")
        
        analysis = {
            "languages": {},
            "common_patterns": [],
            "improvement_areas": [],
            "complexity_metrics": {},
            "recommendations": []
        }
        
        # Collect all code files
        training_data = await self.collect_training_data_from_project()
        
        # Analyze languages
        for data in training_data:
            lang = data.language
            if lang not in analysis["languages"]:
                analysis["languages"][lang] = {
                    "file_count": 0,
                    "total_lines": 0,
                    "avg_quality": 0.0
                }
            
            analysis["languages"][lang]["file_count"] += 1
            analysis["languages"][lang]["total_lines"] += data.metadata.get('line_count', 0)
            analysis["languages"][lang]["avg_quality"] += data.quality_score
        
        # Calculate averages
        for lang_data in analysis["languages"].values():
            if lang_data["file_count"] > 0:
                lang_data["avg_quality"] /= lang_data["file_count"]
        
        # Identify common patterns
        all_code = " ".join([data.code_snippet for data in training_data])
        
        common_keywords = {
            'async': all_code.count('async'),
            'await': all_code.count('await'),
            'try': all_code.count('try'),
            'except': all_code.count('except'),
            'class': all_code.count('class'),
            'function': all_code.count('function'),
            'import': all_code.count('import'),
            'export': all_code.count('export')
        }
        
        analysis["common_patterns"] = [
            f"{keyword}: {count} occurrences" 
            for keyword, count in sorted(common_keywords.items(), key=lambda x: x[1], reverse=True)
            if count > 0
        ]
        
        # Generate recommendations
        analysis["recommendations"] = [
            "Increase code documentation coverage",
            "Implement more comprehensive error handling",
            "Add more unit tests",
            "Consider using more async/await patterns",
            "Improve code organization and structure"
        ]
        
        return analysis
    
    async def generate_training_report(self, session_id: str = None) -> Dict[str, Any]:
        """Generate comprehensive training report"""
        logger.info(f"📊 Generating training report for session: {session_id or 'all'}")
        
        if session_id and session_id in self.training_sessions:
            sessions = [self.training_sessions[session_id]]
        else:
            sessions = list(self.training_sessions.values())
        
        report = {
            "summary": {
                "total_sessions": len(sessions),
                "total_samples_processed": sum(s.processed_samples for s in sessions),
                "avg_success_rate": sum(s.success_rate for s in sessions) / len(sessions) if sessions else 0,
                "total_errors": sum(len(s.errors) for s in sessions)
            },
            "sessions": [],
            "code_analysis": await self.analyze_code_patterns(),
            "generated_at": datetime.now().isoformat()
        }
        
        for session in sessions:
            session_data = {
                "session_id": session.session_id,
                "duration": str(session.end_time - session.start_time) if session.end_time else "ongoing",
                "success_rate": session.success_rate,
                "samples_processed": session.processed_samples,
                "total_samples": session.total_samples,
                "error_count": len(session.errors),
                "status": session.status
            }
            report["sessions"].append(session_data)
        
        return report
    
    async def export_copilot_integration(self, output_path: str = None) -> str:
        """Export Copilot integration as a standalone module"""
        output_path = output_path or str(self.project_root / "copilot_integration.py")
        
        integration_code = '''#!/usr/bin/env python3
"""
Exported GitHub Copilot Integration Module
Generated by GitHub Copilot Trainer
"""

import json
import asyncio
from typing import Dict, List, Any
from pathlib import Path

class CopilotIntegration:
    """Exported Copilot integration for use in other projects"""
    
    def __init__(self, model_path: str = None):
        self.model_path = model_path
        self.suggestions_cache = {}
    
    async def get_suggestions(self, code_context: str, language: str = "python") -> List[str]:
        """Get code suggestions"""
        # Basic suggestion logic
        suggestions = []
        
        if language == "python":
            suggestions.extend([
                "Add type hints to improve code clarity",
                "Implement proper error handling",
                "Add comprehensive docstrings",
                "Use async/await for I/O operations",
                "Add logging for debugging purposes"
            ])
        
        return suggestions
    
    async def analyze_code(self, code: str) -> Dict[str, Any]:
        """Analyze code and provide insights"""
        return {
            "complexity": "medium",
            "suggestions": await self.get_suggestions(code),
            "quality_score": 0.7
        }

# Example usage
if __name__ == "__main__":
    async def main():
        copilot = CopilotIntegration()
        suggestions = await copilot.get_suggestions("def example_function():", "python")
        print("Suggestions:", suggestions)
    
    asyncio.run(main())
'''
        
        async with aiofiles.open(output_path, 'w') as f:
            await f.write(integration_code)
        
        logger.info(f"📤 Copilot integration exported to {output_path}")
        return output_path

async def main():
    """Main function for testing"""
    trainer = GitHubCopilotTrainer()
    
    # Collect training data
    training_data = await trainer.collect_training_data_from_project()
    
    # Train with Copilot data
    session = await trainer.train_agent_with_copilot_data(training_data)
    
    # Generate report
    report = await trainer.generate_training_report(session.session_id)
    
    print("Training Report:")
    print(json.dumps(report, indent=2, default=str))
    
    # Export integration
    await trainer.export_copilot_integration()

if __name__ == "__main__":
    asyncio.run(main())
