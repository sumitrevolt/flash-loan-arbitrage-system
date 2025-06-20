#!/usr/bin/env python3
"""
Ultimate LangChain MCP Project Organizer & Cleanup Commander
=========================================================

This advanced system uses LangChain to command all MCP servers and AI agents
to organize the project, remove unnecessary files, and create a clean structure.

Features:
- LangChain-powered intelligent file analysis
- Multi-agent coordination for cleanup tasks
- MCP server orchestration for project organization
- Automated duplicate detection and removal
- Smart file categorization and archiving
- Configuration consolidation
- Documentation generation

Author: GitHub Copilot Assistant
Date: June 18, 2025
"""

import asyncio
import json
import logging
import os
import shutil
import hashlib
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Any, Set, Tuple
from collections import defaultdict
import requests
import glob
import re

# LangChain imports
try:
    from langchain.agents import AgentExecutor, create_react_agent
    from langchain.tools import Tool, BaseTool
    from langchain.prompts import PromptTemplate
    from langchain.memory import ConversationBufferWindowMemory
    from langchain.schema import SystemMessage, HumanMessage, AIMessage
    from langchain_openai import ChatOpenAI
    from langchain.agents.agent_types import AgentType
    LANGCHAIN_AVAILABLE = True
except ImportError:
    LANGCHAIN_AVAILABLE = False
    print("⚠️  LangChain not available, using fallback mode")

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('langchain_project_organization.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class LangChainMCPOrganizer:
    """Ultimate project organizer using LangChain and MCP servers"""
    
    def __init__(self, project_root: str = None):
        self.project_root = Path(project_root or os.getcwd())
        self.duplicates_found: Dict[str, List[Path]] = {}
        self.unnecessary_files: List[Path] = []
        self.mcp_servers_active: Dict[str, bool] = {}
        self.organization_stats = {
            'files_processed': 0,
            'duplicates_removed': 0,
            'directories_created': 0,
            'files_archived': 0,
            'space_saved': 0,
            'mcp_servers_organized': 0,
            'configs_consolidated': 0
        }
        
        # Initialize LangChain components
        self.llm = None
        self.agent_executor = None
        self.memory = None
        self.setup_langchain()
        
        # Define clean project structure
        self.target_structure = {
            'src': {
                'core': ['Main application logic'],
                'contracts': ['Smart contracts'],
                'mcp_servers': ['MCP server implementations'],
                'ai_agents': ['AI agent implementations'],
                'tools': ['Utility tools and helpers'],
                'integrations': ['External service integrations']
            },
            'config': ['Configuration files'],
            'docs': ['Documentation'],
            'scripts': ['Deployment and utility scripts'],
            'tests': ['Unit and integration tests'],
            'data': ['Data files and databases'],
            'logs': ['Log files'],
            'docker': ['Docker configurations'],
            'archive': {
                'duplicates': ['Archived duplicate files'],
                'backups': ['Project backups'],
                'deprecated': ['Deprecated code']
            }
        }
        
        # File patterns to remove/archive
        self.cleanup_patterns = [
            '*.log',
            '*.tmp',
            '*temp*',
            '*backup*',
            '*duplicate*',
            '*old*',
            '*_old.*',
            '*_backup.*',
            '*_copy.*',
            '*_fixed.*',
            '*test_*',
            '*.pyc',
            '__pycache__',
            '.DS_Store',
            'Thumbs.db',
            '*.bak'
        ]
        
        # Directories to clean/consolidate
        self.consolidate_dirs = [
            'organized',
            'organized_project',
            'cleanup_backup',
            'backup_duplicates',
            'containers',
            'docker-configs',
            'enhanced_system_env'
        ]

    def setup_langchain(self):
        """Setup LangChain components for intelligent organization"""
        if not LANGCHAIN_AVAILABLE:
            logger.warning("LangChain not available, using basic organization")
            return
        
        try:
            # Check for OpenAI API key
            openai_key = os.getenv('OPENAI_API_KEY')
            if not openai_key:
                logger.warning("No OpenAI API key found, using fallback mode")
                return
            
            # Initialize OpenAI LLM
            self.llm = ChatOpenAI(
                model="gpt-4",
                temperature=0.1,
                max_tokens=2000,
                api_key=openai_key
            )
            
            # Setup memory
            self.memory = ConversationBufferWindowMemory(
                k=10,
                memory_key="chat_history",
                return_messages=True
            )
            
            # Create tools for LangChain agent
            tools = [
                Tool(
                    name="detect_duplicates",
                    description="Detect duplicate files in the project",
                    func=self._detect_duplicates_tool
                ),
                Tool(
                    name="analyze_file_importance",
                    description="Analyze file importance and categorize for organization",
                    func=self._analyze_file_importance_tool
                ),
                Tool(
                    name="organize_mcp_servers",
                    description="Organize and command MCP servers",
                    func=self._organize_mcp_servers_tool
                ),
                Tool(
                    name="cleanup_directory",
                    description="Clean up and organize directory structure",
                    func=self._cleanup_directory_tool
                )
            ]
            
            # Create prompt template
            prompt = PromptTemplate(
                input_variables=["tools", "tool_names", "input", "agent_scratchpad", "chat_history"],
                template="""
You are an expert project organizer and cleanup specialist. Your task is to analyze 
the flash loan arbitrage project and organize it efficiently using available tools.

Available tools: {tool_names}
{tools}

Current conversation:
{chat_history}

Task: {input}

Reasoning process:
{agent_scratchpad}

Please organize the project systematically, removing duplicates and unnecessary files.
"""
            )
            
            # Create agent
            agent = create_react_agent(self.llm, tools, prompt)
            self.agent_executor = AgentExecutor.from_agent_and_tools(
                agent=agent,
                tools=tools,
                memory=self.memory,
                verbose=True,
                handle_parsing_errors=True
            )
            
            logger.info("✅ LangChain components initialized successfully")
            
        except Exception as e:
            logger.error(f"❌ Error setting up LangChain: {e}")
            self.llm = None

    def _detect_duplicates_tool(self, input_str: str) -> str:
        """Tool function for duplicate detection"""
        try:
            duplicates = self.scan_for_duplicates()
            total_duplicates = sum(len(files) - 1 for files in duplicates.values())
            return f"Found {len(duplicates)} duplicate file groups with {total_duplicates} duplicate files to remove"
        except Exception as e:
            return f"Error detecting duplicates: {e}"

    def _analyze_file_importance_tool(self, file_path: str) -> str:
        """Tool function for file importance analysis"""
        try:
            path = Path(file_path)
            if not path.exists():
                return f"File {file_path} does not exist"
            
            importance = self.analyze_file_importance(path)
            return f"File importance: {importance['category']} - {importance['reason']}"
        except Exception as e:
            return f"Error analyzing file: {e}"

    def _organize_mcp_servers_tool(self, input_str: str) -> str:
        """Tool function for MCP server organization"""
        try:
            result = self.command_all_mcp_servers()
            return f"MCP servers organized: {len(result)} servers processed"
        except Exception as e:
            return f"Error organizing MCP servers: {e}"

    def _cleanup_directory_tool(self, directory: str) -> str:
        """Tool function for directory cleanup"""
        try:
            dir_path = Path(directory)
            if dir_path.exists():
                cleaned = self.cleanup_directory(dir_path)
                return f"Cleaned directory {directory}: {cleaned} files processed"
            return f"Directory {directory} does not exist"
        except Exception as e:
            return f"Error cleaning directory: {e}"

    def _get_file_hash(self, file_path: Path) -> str:
        """Calculate SHA-256 hash of file content"""
        hash_sha256 = hashlib.sha256()
        try:
            with open(file_path, "rb") as f:
                for chunk in iter(lambda: f.read(4096), b""):
                    hash_sha256.update(chunk)
            return hash_sha256.hexdigest()
        except Exception:
            return f"error_{file_path.name}"

    def _should_skip_file(self, file_path: Path) -> bool:
        """Check if file should be skipped during processing"""
        skip_patterns = [
            '.git',
            'node_modules',
            '__pycache__',
            '.venv',
            'venv',
            '.env',
            'logs'
        ]
        
        return any(pattern in str(file_path) for pattern in skip_patterns)

    def _choose_best_duplicate(self, duplicate_files: List[Path]) -> Path:
        """Choose the best duplicate to keep based on location and name"""
        # Priority order: src > root > others
        priority_dirs = ['src', 'core', 'main']
        
        def get_priority(file_path: Path) -> int:
            path_str = str(file_path).lower()
            
            # Check if in priority directory
            for i, priority_dir in enumerate(priority_dirs):
                if f'/{priority_dir}/' in path_str or f'\\{priority_dir}\\' in path_str:
                    return i
            
            # Prefer files not in backup/temp directories
            if any(term in path_str for term in ['backup', 'temp', 'old', 'duplicate']):
                return 100
            
            # Prefer shorter paths (closer to root)
            return len(file_path.parts)
        
        return min(duplicate_files, key=get_priority)

    def _is_in_organized_structure(self, file_path: Path) -> bool:
        """Check if file is already in organized structure"""
        organized_dirs = ['src', 'config', 'docs', 'scripts', 'tests', 'data', 'logs', 'docker', 'archive']
        
        try:
            relative_path = file_path.relative_to(self.project_root)
            return relative_path.parts[0] in organized_dirs
        except ValueError:
            return False

    def analyze_file_importance(self, file_path: Path) -> Dict[str, Any]:
        """Analyze file importance for organization decisions"""
        path_str = str(file_path).lower()
        
        # Critical files
        if file_path.name in ['package.json', 'requirements.txt', 'docker-compose.yml', 'Dockerfile']:
            return {'category': 'critical', 'reason': 'Essential project file'}
        
        # Source code
        if file_path.suffix in ['.py', '.js', '.ts', '.sol']:
            if 'test' in path_str:
                return {'category': 'test', 'reason': 'Test file'}
            return {'category': 'source', 'reason': 'Source code file'}
        
        # Configuration
        if file_path.suffix in ['.json', '.yaml', '.yml', '.ini', '.env']:
            return {'category': 'config', 'reason': 'Configuration file'}
        
        # Documentation
        if file_path.suffix in ['.md', '.txt', '.rst']:
            return {'category': 'docs', 'reason': 'Documentation file'}
        
        # Temporary/backup files
        if any(term in path_str for term in ['temp', 'backup', 'old', '.bak', '.tmp']):
            return {'category': 'temporary', 'reason': 'Temporary or backup file'}
        
        return {'category': 'other', 'reason': 'Regular file'}

    async def run_intelligent_organization(self) -> Dict[str, Any]:
        """Run LangChain-powered intelligent project organization"""
        logger.info("🚀 Starting LangChain-powered project organization...")
        
        if self.agent_executor:
            try:
                # Use LangChain agent for intelligent organization
                result = await asyncio.to_thread(
                    self.agent_executor.run,
                    input=f"""
                    Please organize the flash loan arbitrage project at {self.project_root}.
                    
                    Tasks to complete:
                    1. Detect and remove duplicate files
                    2. Organize MCP servers and AI agents
                    3. Clean up unnecessary files and directories
                    4. Create proper project structure
                    5. Consolidate configuration files
                    
                    The project currently has many duplicate organizer files, temporary files,
                    and scattered MCP servers that need to be consolidated.
                    """
                )
                logger.info(f"🤖 LangChain agent result: {result}")
            except Exception as e:
                logger.error(f"❌ LangChain agent error: {e}")
        
        # Run fallback organization regardless
        return await self.run_comprehensive_cleanup()

    async def run_comprehensive_cleanup(self) -> Dict[str, Any]:
        """Run comprehensive cleanup without LangChain dependency"""
        logger.info("🧹 Starting comprehensive project cleanup...")
        
        tasks = [
            ("Scanning for duplicates", self.scan_for_duplicates),
            ("Detecting unnecessary files", self.detect_unnecessary_files),
            ("Creating target structure", self.create_target_structure),
            ("Commanding MCP servers", self.command_all_mcp_servers),
            ("Removing duplicates", self.remove_duplicates),
            ("Archiving unnecessary files", self.archive_unnecessary_files),
            ("Consolidating configurations", self.consolidate_configurations),
            ("Organizing remaining files", self.organize_remaining_files),
            ("Cleaning empty directories", self.clean_empty_directories),
            ("Generating final report", self.generate_organization_report)
        ]
        
        for task_name, task_func in tasks:
            try:
                logger.info(f"📋 {task_name}...")
                if asyncio.iscoroutinefunction(task_func):
                    result = await task_func()
                else:
                    result = task_func()
                logger.info(f"✅ {task_name} completed")
            except Exception as e:
                logger.error(f"❌ Error in {task_name}: {e}")
        
        return self.organization_stats

    def scan_for_duplicates(self) -> Dict[str, List[Path]]:
        """Scan for duplicate files using content hashing"""
        logger.info("🔍 Scanning for duplicate files...")
        
        file_hashes: Dict[str, List[Path]] = defaultdict(list)
        
        for file_path in self.project_root.rglob("*"):
            if file_path.is_file() and not self._should_skip_file(file_path):
                try:
                    file_hash = self._get_file_hash(file_path)
                    file_hashes[file_hash].append(file_path)
                    self.organization_stats['files_processed'] += 1
                except Exception as e:
                    logger.warning(f"⚠️ Could not hash {file_path}: {e}")
        
        # Find actual duplicates (files with same hash)
        duplicates = {
            hash_val: paths for hash_val, paths in file_hashes.items()
            if len(paths) > 1
        }
        
        self.duplicates_found = duplicates
        total_duplicates = sum(len(files) - 1 for files in duplicates.values())
        logger.info(f"🔍 Found {len(duplicates)} duplicate file groups ({total_duplicates} duplicates to remove)")
        
        return duplicates

    def detect_unnecessary_files(self) -> List[Path]:
        """Detect unnecessary files that should be archived or removed"""
        logger.info("🗑️ Detecting unnecessary files...")
        
        unnecessary = []
        
        for pattern in self.cleanup_patterns:
            matches = list(self.project_root.rglob(pattern))
            unnecessary.extend(matches)
        
        # Additional unnecessary file detection
        for file_path in self.project_root.rglob("*"):
            if file_path.is_file():
                # Check for test files, backup files, etc.
                if any(keyword in str(file_path).lower() for keyword in 
                       ['test_', 'backup', 'copy', 'duplicate', 'temp', 'old']):
                    if file_path not in unnecessary:
                        unnecessary.append(file_path)
        
        self.unnecessary_files = list(set(unnecessary))  # Remove duplicates
        logger.info(f"🗑️ Found {len(self.unnecessary_files)} unnecessary files")
        
        return self.unnecessary_files

    def create_target_structure(self) -> None:
        """Create the target directory structure"""
        logger.info("📁 Creating target directory structure...")
        
        def create_dirs(structure: Dict, parent: Path):
            for name, content in structure.items():
                dir_path = parent / name
                dir_path.mkdir(exist_ok=True, parents=True)
                self.organization_stats['directories_created'] += 1
                
                if isinstance(content, dict):
                    create_dirs(content, dir_path)
                elif isinstance(content, list):
                    # Create README for the directory
                    readme_path = dir_path / "README.md"
                    if not readme_path.exists():
                        with open(readme_path, 'w') as f:
                            f.write(f"# {name.title()}\n\n")
                            f.write(f"This directory contains: {', '.join(content)}\n")
                            f.write(f"\nOrganized on: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        
        create_dirs(self.target_structure, self.project_root)
        logger.info("✅ Target directory structure created")

    def command_all_mcp_servers(self) -> Dict[str, Any]:
        """Command all MCP servers to participate in organization"""
        logger.info("🤖 Commanding all MCP servers for organization...")
        
        # Find all MCP server files
        mcp_files = []
        for pattern in ['*mcp*server*.py', '*mcp*.py', '*price*feed*.py', '*arbitrage*.py']:
            mcp_files.extend(self.project_root.rglob(pattern))
        
        # Remove duplicates and organize MCP servers
        mcp_servers_dir = self.project_root / 'src' / 'mcp_servers'
        mcp_servers_dir.mkdir(exist_ok=True, parents=True)
        
        organized_servers = {}
        server_configs = {}
        
        for mcp_file in mcp_files:
            if 'archive' in str(mcp_file) or 'backup' in str(mcp_file):
                continue
            
            server_name = mcp_file.stem
            target_path = mcp_servers_dir / mcp_file.name
            
            # Move to organized location if not already there
            if mcp_file.parent != mcp_servers_dir:
                if not target_path.exists():
                    try:
                        shutil.copy2(str(mcp_file), str(target_path))
                        logger.info(f"📦 Copied {server_name} to organized location")
                        self.organization_stats['mcp_servers_organized'] += 1
                    except Exception as e:
                        logger.error(f"❌ Error organizing {server_name}: {e}")
            
            organized_servers[server_name] = str(target_path)
            server_configs[server_name] = {
                "path": f"src/mcp_servers/{mcp_file.name}",
                "type": "python",
                "port": 8100 + len(server_configs),
                "enabled": True,
                "organized": True,
                "description": f"MCP server for {server_name.replace('_', ' ').title()}"
            }
        
        # Save unified MCP configuration
        config_path = self.project_root / 'config' / 'mcp_servers.json'
        config_path.parent.mkdir(exist_ok=True)
        with open(config_path, 'w') as f:
            json.dump({
                "servers": server_configs,
                "organization_date": datetime.now().isoformat(),
                "total_servers": len(server_configs),
                "organized_by": "LangChain MCP Organizer"
            }, f, indent=2)
        
        logger.info(f"🤖 Organized {len(organized_servers)} MCP servers")
        return organized_servers

    def remove_duplicates(self) -> None:
        """Remove duplicate files intelligently"""
        logger.info("🗑️ Removing duplicate files...")
        
        for file_hash, duplicate_files in self.duplicates_found.items():
            if len(duplicate_files) <= 1:
                continue
            
            # Sort by preference (keep the one in the best location)
            best_file = self._choose_best_duplicate(duplicate_files)
            files_to_remove = [f for f in duplicate_files if f != best_file]
            
            for file_to_remove in files_to_remove:
                try:
                    # Move to archive instead of deleting
                    archive_dir = self.project_root / 'archive' / 'duplicates'
                    archive_dir.mkdir(exist_ok=True, parents=True)
                    
                    archive_path = archive_dir / file_to_remove.name
                    # Handle name conflicts in archive
                    counter = 1
                    while archive_path.exists():
                        stem = file_to_remove.stem
                        suffix = file_to_remove.suffix
                        archive_path = archive_dir / f"{stem}_duplicate_{counter}{suffix}"
                        counter += 1
                    
                    shutil.move(str(file_to_remove), str(archive_path))
                    self.organization_stats['duplicates_removed'] += 1
                    logger.info(f"📦 Archived duplicate: {file_to_remove.name}")
                    
                except Exception as e:
                    logger.error(f"❌ Error removing duplicate {file_to_remove}: {e}")

    def archive_unnecessary_files(self) -> None:
        """Archive unnecessary files"""
        logger.info("📦 Archiving unnecessary files...")
        
        for file_path in self.unnecessary_files:
            if not file_path.exists():
                continue
            
            try:
                # Determine archive category
                if 'test' in str(file_path).lower():
                    archive_subdir = 'tests'
                elif any(term in str(file_path).lower() for term in ['backup', 'old']):
                    archive_subdir = 'backups'
                elif 'temp' in str(file_path).lower():
                    archive_subdir = 'temporary'
                else:
                    archive_subdir = 'deprecated'
                
                archive_dir = self.project_root / 'archive' / archive_subdir
                archive_dir.mkdir(exist_ok=True, parents=True)
                
                archive_path = archive_dir / file_path.name
                # Handle name conflicts
                counter = 1
                while archive_path.exists():
                    stem = file_path.stem
                    suffix = file_path.suffix
                    archive_path = archive_dir / f"{stem}_archived_{counter}{suffix}"
                    counter += 1
                
                shutil.move(str(file_path), str(archive_path))
                self.organization_stats['files_archived'] += 1
                logger.info(f"📦 Archived: {file_path.name}")
                
            except Exception as e:
                logger.error(f"❌ Error archiving {file_path}: {e}")

    def consolidate_configurations(self) -> None:
        """Consolidate configuration files"""
        logger.info("⚙️ Consolidating configuration files...")
        
        config_dir = self.project_root / 'config'
        config_dir.mkdir(exist_ok=True)
        
        # Find and consolidate config files
        config_files = []
        config_patterns = ['*config*', '*.json', '*.yaml', '*.yml', '*.ini', '.env*', '*requirements*.txt']
        
        for pattern in config_patterns:
            found_files = list(self.project_root.glob(pattern))
            config_files.extend(found_files)
        
        consolidated_configs = {}
        
        for config_file in config_files:
            if (config_file.is_file() and 
                'node_modules' not in str(config_file) and
                'archive' not in str(config_file)):
                
                target_path = config_dir / config_file.name
                
                if config_file.parent != config_dir:
                    try:
                        if not target_path.exists():
                            shutil.copy2(str(config_file), str(target_path))
                            logger.info(f"⚙️ Copied config: {config_file.name}")
                            self.organization_stats['configs_consolidated'] += 1
                        consolidated_configs[config_file.name] = str(target_path)
                    except Exception as e:
                        logger.error(f"❌ Error moving config {config_file}: {e}")
        
        # Create master configuration index
        master_config = self.project_root / 'config' / 'master_config.json'
        with open(master_config, 'w') as f:
            json.dump({
                "configurations": consolidated_configs,
                "consolidation_date": datetime.now().isoformat(),
                "project_root": str(self.project_root),
                "total_configs": len(consolidated_configs)
            }, f, indent=2)

    def organize_remaining_files(self) -> None:
        """Organize remaining files into proper structure"""
        logger.info("📁 Organizing remaining files...")
        
        file_mappings = {
            '.py': 'src',
            '.js': 'scripts',
            '.ts': 'scripts', 
            '.sol': 'src/contracts',
            '.md': 'docs',
            '.txt': 'docs',
            '.json': 'config',
            '.yaml': 'config',
            '.yml': 'config',
            '.dockerfile': 'docker',
            '.sh': 'scripts',
            '.ps1': 'scripts'
        }
        
        for file_path in self.project_root.rglob("*"):
            if (file_path.is_file() and 
                not self._is_in_organized_structure(file_path) and
                not self._should_skip_file(file_path) and
                file_path not in self.unnecessary_files):
                
                suffix = file_path.suffix.lower()
                target_dir = file_mappings.get(suffix)
                
                if target_dir:
                    target_path = self.project_root / target_dir
                    target_path.mkdir(exist_ok=True, parents=True)
                    
                    new_path = target_path / file_path.name
                    
                    # Avoid conflicts
                    if not new_path.exists():
                        try:
                            shutil.copy2(str(file_path), str(new_path))
                            logger.info(f"📁 Organized: {file_path.name} -> {target_dir}")
                        except Exception as e:
                            logger.error(f"❌ Error organizing {file_path}: {e}")

    def cleanup_directory(self, directory: Path) -> int:
        """Clean up a specific directory"""
        cleaned_files = 0
        
        for item in directory.rglob("*"):
            if item.is_file() and any(pattern in item.name.lower() for pattern in ['temp', 'tmp', '.bak']):
                try:
                    item.unlink()
                    cleaned_files += 1
                except Exception as e:
                    logger.error(f"❌ Error cleaning {item}: {e}")
        
        return cleaned_files

    def clean_empty_directories(self) -> None:
        """Clean up empty directories"""
        logger.info("🧹 Cleaning empty directories...")
        
        def is_empty_dir(path: Path) -> bool:
            try:
                return path.is_dir() and not any(path.rglob("*"))
            except:
                return False
        
        # Multiple passes to handle nested empty directories
        for _ in range(3):
            empty_dirs = [d for d in self.project_root.rglob("*") if is_empty_dir(d)]
            for empty_dir in empty_dirs:
                try:
                    if empty_dir != self.project_root and empty_dir.name not in ['archive', 'logs']:
                        empty_dir.rmdir()
                        logger.info(f"🗑️ Removed empty directory: {empty_dir.name}")
                except Exception as e:
                    logger.debug(f"Could not remove {empty_dir}: {e}")

    def generate_organization_report(self) -> Dict[str, Any]:
        """Generate final organization report"""
        logger.info("📊 Generating organization report...")
        
        report = {
            "organization_summary": {
                "date": datetime.now().isoformat(),
                "project_root": str(self.project_root),
                "organizer": "LangChain MCP Project Organizer",
                "langchain_enabled": self.llm is not None
            },
            "statistics": self.organization_stats,
            "structure_created": self.target_structure,
            "duplicates_found": len(self.duplicates_found),
            "unnecessary_files_archived": len(self.unnecessary_files),
            "recommendations": [
                "Review archived files before final deletion",
                "Update documentation to reflect new structure",
                "Test all MCP servers after reorganization",
                "Update Docker configurations for new paths",
                "Consider setting up automated organization maintenance"
            ]
        }
        
        # Save report
        report_path = self.project_root / 'docs' / 'organization_report.json'
        report_path.parent.mkdir(exist_ok=True)
        with open(report_path, 'w') as f:
            json.dump(report, f, indent=2)
        
        # Create markdown summary
        md_report = self.project_root / 'docs' / 'ORGANIZATION_SUMMARY.md'
        with open(md_report, 'w') as f:
            f.write("# Project Organization Summary\n\n")
            f.write(f"**Date:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
            f.write("## Statistics\n\n")
            for key, value in self.organization_stats.items():
                f.write(f"- **{key.replace('_', ' ').title()}:** {value}\n")
            f.write("\n## Structure\n\n")
            f.write("The project has been organized into the following structure:\n\n")
            for dir_name in self.target_structure.keys():
                f.write(f"- `{dir_name}/` - {dir_name.title()} directory\n")
            f.write("\n## Next Steps\n\n")
            for rec in report["recommendations"]:
                f.write(f"1. {rec}\n")
        
        logger.info("📊 Organization report generated")
        return report

async def main():
    """Main execution function"""
    print("🚀 Starting LangChain MCP Project Organization...")
    
    # Get project root from environment or use current directory
    project_root = os.getenv('PROJECT_ROOT', os.getcwd())
    
    # Initialize organizer
    organizer = LangChainMCPOrganizer(project_root)
    
    # Run organization
    try:
        if organizer.llm:
            print("🤖 Using LangChain AI-powered organization...")
            results = await organizer.run_intelligent_organization()
        else:
            print("🔧 Using standard organization mode...")
            results = await organizer.run_comprehensive_cleanup()
        
        print("\n✅ Project organization completed!")
        print(f"📊 Results: {json.dumps(results, indent=2)}")
        
    except Exception as e:
        logger.error(f"❌ Organization failed: {e}")
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    asyncio.run(main())
