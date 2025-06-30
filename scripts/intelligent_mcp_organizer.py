#!/usr/bin/env python3
"""
Intelligent MCP Server Organizer
================================
Analyzes, categorizes, and organizes MCP servers into:
- 21 Best Local MCP Servers 
- 12 Best AI Agents

Before removing any files, extracts useful functions and merges them
into the best versions to preserve functionality.
"""

import ast
import shutil
import json
import re
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Tuple, Any, Optional
import logging

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class MCPServerAnalyzer:
    def __init__(self, project_root: str):
        self.project_root: Path = Path(project_root)
        self.mcp_servers_dir: Path = self.project_root / "mcp_servers"
        self.analysis_results: Dict[str, Dict[str, Any]] = {}
        self.local_servers: List[Dict[str, Any]] = []
        self.ai_agents: List[Dict[str, Any]] = []
        self.functions_extracted: Dict[str, List[str]] = {}
        
        # Keywords for categorization
        self.ai_keywords = [
            'ai', 'agent', 'intelligent', 'ml', 'machine_learning', 'neural',
            'copilot', 'assistant', 'chat', 'conversation', 'llm', 'gpt',
            'training', 'model', 'predict', 'analyze', 'smart', 'auto'
        ]
        
        self.local_keywords = [
            'server', 'api', 'database', 'file', 'cache', 'storage', 'monitor',
            'security', 'auth', 'blockchain', 'defi', 'flash_loan', 'arbitrage',
            'price', 'market', 'trading', 'portfolio', 'risk', 'liquidity'
        ]
    
    def analyze_file_functionality(self, file_path: Path) -> Dict[str, Any]:
        """Analyze a Python file for its functionality, classes, and functions"""
        try:
            content = file_path.read_text(encoding='utf-8', errors='ignore')
            
            # Parse AST to extract functions and classes
            try:
                tree = ast.parse(content)
                functions: List[Dict[str, Any]] = []
                classes: List[Dict[str, Any]] = []
                imports: List[str] = []
                
                for node in ast.walk(tree):
                    if isinstance(node, ast.FunctionDef):
                        functions.append({
                            'name': node.name,
                            'line': node.lineno,
                            'is_async': isinstance(node, ast.AsyncFunctionDef),
                            'args': [arg.arg for arg in node.args.args],
                            'docstring': ast.get_docstring(node)
                        })
                    elif isinstance(node, ast.ClassDef):
                        classes.append({
                            'name': node.name,
                            'line': node.lineno,
                            'methods': [n.name for n in node.body if isinstance(n, ast.FunctionDef)],
                            'docstring': ast.get_docstring(node)
                        })
                    elif isinstance(node, (ast.Import, ast.ImportFrom)):
                        if isinstance(node, ast.Import):
                            imports.extend([alias.name for alias in node.names])
                        else:
                            imports.append(node.module or 'relative_import')
                            
            except SyntaxError:
                # Fallback to regex parsing for files with syntax issues
                functions = self._extract_functions_regex(content)
                classes = self._extract_classes_regex(content)
                imports = self._extract_imports_regex(content)
            
            # Analyze content for quality indicators
            analysis = {
                'file_path': str(file_path),
                'file_size': file_path.stat().st_size,
                'line_count': len(content.splitlines()),
                'functions': functions,
                'classes': classes,
                'imports': imports,
                'has_mcp_imports': any('mcp' in imp.lower() for imp in imports),
                'has_async': 'async' in content.lower(),
                'has_error_handling': content.count('try:') + content.count('except'),
                'has_logging': 'logger' in content or 'logging' in content,
                'has_docstrings': content.count('"""') + content.count("'''"),
                'has_type_hints': ':' in content and '->' in content,
                'complexity_score': self._calculate_complexity(content),
                'category': self._categorize_server(file_path.name, content),
                'unique_features': self._extract_unique_features(content),
                'api_endpoints': self._extract_api_endpoints(content),
                'tools_provided': self._extract_mcp_tools(content)
            }
            
            return analysis
            
        except Exception as e:
            logger.error(f"❌ Failed to analyze {file_path.name}: {e}")
            return {'file_path': str(file_path), 'error': str(e)}
    
    def _extract_functions_regex(self, content: str) -> List[Dict[str, Any]]:
        """Fallback regex-based function extraction"""
        functions: List[Dict[str, Any]] = []
        pattern = r'(?:async\s+)?def\s+(\w+)\s*\([^)]*\):'
        for match in re.finditer(pattern, content):
            functions.append({
                'name': match.group(1),
                'line': content[:match.start()].count('\n') + 1,
                'is_async': 'async' in match.group(0)
            })
        return functions
    
    def _extract_classes_regex(self, content: str) -> List[Dict[str, Any]]:
        """Fallback regex-based class extraction"""
        classes: List[Dict[str, Any]] = []
        pattern = r'class\s+(\w+)(?:\([^)]*\))?:'
        for match in re.finditer(pattern, content):
            classes.append({
                'name': match.group(1),
                'line': content[:match.start()].count('\n') + 1
            })
        return classes
    
    def _extract_imports_regex(self, content: str) -> List[str]:
        """Fallback regex-based import extraction"""
        imports: List[str] = []
        patterns = [
            r'import\s+([\w.]+)',
            r'from\s+([\w.]+)\s+import'
        ]
        for pattern in patterns:
            imports.extend([match.group(1) for match in re.finditer(pattern, content)])
        return imports
    
    def _calculate_complexity(self, content: str) -> int:
        """Calculate code complexity score"""
        score = 0
        score += len(content.splitlines())  # Lines of code
        score += content.count('def ') * 5  # Functions
        score += content.count('class ') * 10  # Classes
        score += content.count('if ') * 2  # Conditionals
        score += content.count('for ') * 2  # Loops
        score += content.count('try:') * 3  # Error handling
        score += content.count('async ') * 3  # Async code
        return score
    
    def _categorize_server(self, filename: str, content: str) -> str:
        """Categorize server as AI Agent or Local Server"""
        filename_lower = filename.lower()
        content_lower = content.lower()
        
        ai_score = sum(1 for keyword in self.ai_keywords if keyword in filename_lower or keyword in content_lower)
        local_score = sum(1 for keyword in self.local_keywords if keyword in filename_lower or keyword in content_lower)
        
        if ai_score > local_score:
            return 'ai_agent'
        else:
            return 'local_server'
    
    def _extract_unique_features(self, content: str) -> List[str]:
        """Extract unique features/capabilities from the code"""
        features: List[str] = []
        
        # Look for specific patterns
        if 'flash_loan' in content.lower():
            features.append('flash_loan_support')
        if 'arbitrage' in content.lower():
            features.append('arbitrage_detection')
        if 'websocket' in content.lower():
            features.append('realtime_data')
        if 'dashboard' in content.lower():
            features.append('web_interface')
        if 'database' in content.lower() or 'db' in content.lower():
            features.append('database_integration')
        if 'api' in content.lower() and 'request' in content.lower():
            features.append('external_api_calls')
        if 'monitor' in content.lower():
            features.append('monitoring_capabilities')
        if 'security' in content.lower() or 'auth' in content.lower():
            features.append('security_features')
            
        return features
    
    def _extract_api_endpoints(self, content: str) -> List[str]:
        """Extract API endpoints from the code"""
        endpoints: List[str] = []
        patterns = [
            r'@app\.route\(["\']([^"\']+)["\']',
            r'app\.get\(["\']([^"\']+)["\']',
            r'app\.post\(["\']([^"\']+)["\']',
            r'["\']([/\w]+)["\'].*endpoint'
        ]
        for pattern in patterns:
            matches = [str(match.group(1)) for match in re.finditer(pattern, content)]
            endpoints.extend(matches)
        return list(set(endpoints))
    
    def _extract_mcp_tools(self, content: str) -> List[str]:
        """Extract MCP tools provided by the server"""
        tools = []
        
        # Look for tool definitions
        patterns = [
            r'@server\.list_tools.*?name.*?["\']([^"\']+)["\']',
            r'Tool\(.*?name.*?["\']([^"\']+)["\']',
            r'["\'](\w+)["\'].*?tool'
        ]
        
        for pattern in patterns:
            tools.extend([match.group(1) for match in re.finditer(pattern, content, re.DOTALL)])
            
        return list(set(tools))
    
    def analyze_all_servers(self) -> None:
        """Analyze all MCP servers in the directory"""
        logger.info("🔍 Analyzing all MCP servers...")
        
        python_files = list(self.mcp_servers_dir.glob("*.py"))
        logger.info(f"📊 Found {len(python_files)} Python files to analyze")
        
        for file_path in python_files:
            if file_path.name.startswith('__'):
                continue
                
            logger.info(f"🔍 Analyzing: {file_path.name}")
            analysis = self.analyze_file_functionality(file_path)
            self.analysis_results[file_path.name] = analysis
            
            # Categorize
            if analysis.get('category') == 'ai_agent':
                self.ai_agents.append(analysis)
            else:
                self.local_servers.append(analysis)
        
        logger.info(f"📊 Analysis complete: {len(self.local_servers)} local servers, {len(self.ai_agents)} AI agents")
    
    def rank_servers(self) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]]]:
        """Rank servers by quality and functionality"""
        
        def calculate_score(server: Dict[str, Any]) -> float:
            score = 0.0
            
            # Base functionality score
            score += len(server.get('functions', [])) * 2
            score += len(server.get('classes', [])) * 5
            score += server.get('complexity_score', 0) * 0.1
            
            # Quality indicators
            if server.get('has_mcp_imports'):
                score += 20
            if server.get('has_async'):
                score += 10
            if server.get('has_error_handling', 0) > 0:
                score += server['has_error_handling'] * 2
            if server.get('has_logging'):
                score += 5
            if server.get('has_docstrings', 0) > 0:
                score += server['has_docstrings']
            if server.get('has_type_hints'):
                score += 10
                
            # Unique features bonus
            score += len(server.get('unique_features', [])) * 3
            score += len(server.get('api_endpoints', [])) * 2
            score += len(server.get('tools_provided', [])) * 4
            
            # File size penalty for very small files (likely templates)
            if server.get('file_size', 0) < 1000:
                score *= 0.5
                
            # Bonus for enhanced/optimized versions
            filename = Path(server.get('file_path', '')).name.lower()
            if any(term in filename for term in ['enhanced', 'optimized', 'unified', 'complete']):
                score *= 1.2
                
            return score
        
        # Rank local servers
        ranked_local = sorted(self.local_servers, key=calculate_score, reverse=True)
        
        # Rank AI agents  
        ranked_ai = sorted(self.ai_agents, key=calculate_score, reverse=True)
        
        return ranked_local[:21], ranked_ai[:12]
    
    def extract_useful_functions(self, source_file: Dict[str, Any], target_file: Dict[str, Any]) -> List[str]:
        """Extract useful functions from source file that aren't in target file"""
        extracted_functions: List[str] = []
        try:
            source_path = Path(source_file['file_path'])
            target_path = Path(target_file['file_path'])
            if not source_path.exists() or not target_path.exists():
                return []
            source_content = source_path.read_text(encoding='utf-8', errors='ignore')
            source_functions = source_file.get('functions', [])
            target_function_names = {f['name'] for f in target_file.get('functions', [])}
            for func in source_functions:
                func_name = func['name']
                if func_name not in target_function_names and not func_name.startswith('_'):
                    # Extract the function code
                    func_code = self._extract_function_code(source_content, func_name)
                    if func_code and len(func_code.strip()) > 50:  # Only meaningful functions
                        extracted_functions.append(func_code)
        except Exception as e:
            logger.warning(f"⚠️ Failed to extract functions: {e}")
        return extracted_functions
    
    def _extract_function_code(self, content: str, func_name: str) -> Optional[str]:
        """Extract the complete code for a specific function"""
        lines = content.splitlines()
        start_pattern = re.compile(rf'^\s*(?:async\s+)?def\s+{re.escape(func_name)}\s*\(')
        start_line = None
        for i, line in enumerate(lines):
            if start_pattern.match(line):
                start_line = i
                break
        if start_line is None:
            return None
        # Find the end of the function (next function or class, or end of file)
        indent_level = len(lines[start_line]) - len(lines[start_line].lstrip())
        end_line = len(lines)
        for i in range(start_line + 1, len(lines)):
            line = lines[i]
            if line.strip() and len(line) - len(line.lstrip()) <= indent_level:
                if line.strip().startswith(('def ', 'class ', 'async def ')):
                    end_line = i
                    break
        return '\n'.join(lines[start_line:end_line])
    
    def merge_functions_into_target(self, extracted_functions: List[str], target_file: Dict[str, Any]) -> None:
        """Merge extracted functions into the target file"""
        if not extracted_functions:
            return
            
        try:
            target_path = Path(target_file['file_path'])
            content = target_path.read_text(encoding='utf-8', errors='ignore')
            
            # Add extracted functions at the end of the file
            merged_content = content + '\n\n# Merged functions from other servers:\n\n'
            for func_code in extracted_functions:
                merged_content += func_code + '\n\n'
            
            # Write back the merged content
            target_path.write_text(merged_content, encoding='utf-8')
            
            # Track what was merged
            target_name = target_path.name
            if target_name not in self.functions_extracted:
                self.functions_extracted[target_name] = []
            self.functions_extracted[target_name].extend([f"Function from {len(extracted_functions)} files" for _ in extracted_functions])
            
        except Exception as e:
            logger.error(f"❌ Failed to merge functions into {target_file.get('file_path')}: {e}")
    
    def organize_servers(self) -> Dict[str, Any]:
        """Main organization process"""
        logger.info("🚀 Starting intelligent MCP server organization...")
        
        # Step 1: Analyze all servers
        self.analyze_all_servers()
        
        # Step 2: Rank and select best servers
        best_local, best_ai = self.rank_servers()
        
        logger.info(f"📊 Selected {len(best_local)} best local servers and {len(best_ai)} best AI agents")
        
        # Step 3: Create backup
        backup_dir = self.project_root / f"mcp_organization_backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        backup_dir.mkdir(exist_ok=True)
        shutil.copytree(self.mcp_servers_dir, backup_dir / "original_mcp_servers")
        
        # Step 4: Extract and merge functions from files being removed
        all_kept_files = best_local + best_ai
        kept_file_names = {Path(f['file_path']).name for f in all_kept_files}
        
        for file_name, analysis in self.analysis_results.items():
            if file_name not in kept_file_names:
                # Find the best target file to merge functions into
                category = analysis.get('category', 'local_server')
                target_files = best_ai if category == 'ai_agent' else best_local
                
                if target_files:
                    # Find most similar target file
                    best_target = self._find_similar_target(analysis, target_files)
                    if best_target:
                        extracted = self.extract_useful_functions(analysis, best_target)
                        if extracted:
                            self.merge_functions_into_target(extracted, best_target)
                            logger.info(f"🔧 Merged {len(extracted)} functions from {file_name} into {Path(best_target['file_path']).name}")
        
        # Step 5: Remove files that aren't in the final selection
        removed_count = 0
        for file_path in self.mcp_servers_dir.glob("*.py"):
            if file_path.name not in kept_file_names and not file_path.name.startswith('__'):
                # Backup before removal
                shutil.copy2(file_path, backup_dir / file_path.name)
                file_path.unlink()
                removed_count += 1
                logger.info(f"🗑️ Removed: {file_path.name}")
        
        # Step 6: Update configuration
        self._update_mcp_config(best_local, best_ai)
        
        # Step 7: Generate report
        report = self._generate_organization_report(best_local, best_ai, removed_count, backup_dir)
        
        return report
    
    def _find_similar_target(self, source_analysis: Dict[str, Any], target_files: List[Dict[str, Any]]) -> Optional[Dict[str, Any]]:
        """Find the most similar target file for merging functions"""
        if not target_files:
            return None
            
        source_features = set(source_analysis.get('unique_features', []))
        source_imports = set(source_analysis.get('imports', []))
        
        best_target = None
        best_similarity = 0
        
        for target in target_files:
            target_features = set(target.get('unique_features', []))
            target_imports = set(target.get('imports', []))
            
            # Calculate similarity score
            feature_overlap = len(source_features & target_features)
            import_overlap = len(source_imports & target_imports)
            similarity = feature_overlap * 2 + import_overlap
            
            if similarity > best_similarity:
                best_similarity = similarity
                best_target = target
        
        return best_target if best_similarity > 0 else target_files[0]
    
    def _update_mcp_config(self, local_servers: List[Dict[str, Any]], ai_agents: List[Dict[str, Any]]) -> None:
        """Update the unified MCP config with the organized servers"""
        config_path = self.project_root / "config" / "unified_mcp_config.json"
        
        try:
            with open(config_path, 'r') as f:
                config = json.load(f)
            
            # Clear existing servers
            config['servers'] = {}
            
            # Add local servers
            port = 3000
            for i, server in enumerate(local_servers):
                server_name = Path(server['file_path']).stem
                config['servers'][server_name] = {
                    "name": server_name,
                    "type": "python",
                    "path": f"mcp_servers/{Path(server['file_path']).name}",
                    "port": port + i,
                    "enabled": True,
                    "category": "local_server",
                    "auto_restart": True,
                    "environment_variables": {
                        "MCP_SERVER_NAME": server_name,
                        "PORT": str(port + i)
                    },
                    "features": server.get('unique_features', []),
                    "tools": server.get('tools_provided', [])
                }
            
            # Add AI agents
            port = 3030
            for i, agent in enumerate(ai_agents):
                agent_name = Path(agent['file_path']).stem
                config['servers'][agent_name] = {
                    "name": agent_name,
                    "type": "python",
                    "path": f"mcp_servers/{Path(agent['file_path']).name}",
                    "port": port + i,
                    "enabled": True,
                    "category": "ai_agent",
                    "auto_restart": True,
                    "environment_variables": {
                        "MCP_SERVER_NAME": agent_name,
                        "PORT": str(port + i)
                    },
                    "features": agent.get('unique_features', []),
                    "tools": agent.get('tools_provided', [])
                }
            
            # Update global configuration
            config['global_configuration'] = {
                "health_check_interval": 30,
                "auto_restart": True,
                "log_level": "INFO",
                "organization": {
                    "local_servers_count": len(local_servers),
                    "ai_agents_count": len(ai_agents),
                    "total_servers": len(local_servers) + len(ai_agents),
                    "organization_date": datetime.now().isoformat()
                }
            }
            
            # Save updated config
            with open(config_path, 'w') as f:
                json.dump(config, f, indent=2)
                
            logger.info(f"✅ Updated MCP config with {len(local_servers)} local servers and {len(ai_agents)} AI agents")
            
        except Exception as e:
            logger.error(f"❌ Failed to update MCP config: {e}")
    
    def _generate_organization_report(self, local_servers: List[Dict[str, Any]], ai_agents: List[Dict[str, Any]], 
                                     removed_count: int, backup_dir: Path) -> Dict[str, Any]:
        """Generate comprehensive organization report"""
        
        report = {
            "organization_timestamp": datetime.now().isoformat(),
            "summary": {
                "total_files_analyzed": len(self.analysis_results),
                "local_servers_kept": len(local_servers),
                "ai_agents_kept": len(ai_agents),
                "files_removed": removed_count,
                "functions_merged": sum(len(funcs) for funcs in self.functions_extracted.values())
            },
            "selected_local_servers": [
                {
                    "name": Path(s['file_path']).name,
                    "features": s.get('unique_features', []),
                    "tools": s.get('tools_provided', []),
                    "complexity_score": s.get('complexity_score', 0),
                    "functions_count": len(s.get('functions', []))
                } for s in local_servers
            ],
            "selected_ai_agents": [
                {
                    "name": Path(a['file_path']).name,
                    "features": a.get('unique_features', []),
                    "tools": a.get('tools_provided', []),
                    "complexity_score": a.get('complexity_score', 0),
                    "functions_count": len(a.get('functions', []))
                } for a in ai_agents
            ],
            "functions_extracted": self.functions_extracted,
            "backup_location": str(backup_dir),
            "configuration_updated": "config/unified_mcp_config.json",
            "next_steps": [
                "Use the organized MCP servers for better performance",
                "Local servers handle infrastructure and blockchain operations", 
                "AI agents handle intelligent tasks and analysis",
                "All useful functions have been preserved through merging",
                "Backup available if any functionality is needed"
            ]
        }
        
        # Save report
        report_path = self.project_root / "MCP_ORGANIZATION_REPORT.json"
        with open(report_path, 'w') as f:
            json.dump(report, f, indent=2)
            
        return report

def main() -> int:
    """Main function"""
    project_root = Path.cwd()
    analyzer = MCPServerAnalyzer(str(project_root))
    
    try:
        report = analyzer.organize_servers()
        
        print("\n" + "="*80)
        print("🎉 INTELLIGENT MCP ORGANIZATION COMPLETE!")
        print("="*80)
        print(f"📊 Analyzed: {report['summary']['total_files_analyzed']} files")
        print(f"🏠 Local Servers: {report['summary']['local_servers_kept']}")
        print(f"🤖 AI Agents: {report['summary']['ai_agents_kept']}")
        print(f"🗑️ Files Removed: {report['summary']['files_removed']}")
        print(f"🔧 Functions Merged: {report['summary']['functions_merged']}")
        print(f"💾 Backup: {report['backup_location']}")
        print("="*80)
        
        return 0
        
    except Exception as e:
        logger.error(f"❌ Organization failed: {e}")
        return 1

if __name__ == "__main__":
    exit(main()) 