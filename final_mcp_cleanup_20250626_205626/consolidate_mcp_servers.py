#!/usr/bin/env python3
"""
MCP Server Consolidation Script
================================

This script consolidates duplicate MCP servers by:
1. Analyzing all MCP server files across directories
2. Identifying duplicates and determining the best version
3. Moving the best versions to a single consolidated directory
4. Removing duplicate files
5. Updating configuration references

Author: AI Assistant
Date: 2024
"""

import os
import shutil
import json
import hashlib
from pathlib import Path
from typing import Dict, List, Tuple, Optional, Any
from datetime import datetime
import logging

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class MCPServerConsolidator:
    def __init__(self, project_root: str):
        self.project_root = Path(project_root)
        self.target_dir = self.project_root / "mcp_servers"
        
        # Directories to scan for MCP servers
        self.source_dirs = [
            self.project_root / "mcp_servers",
            self.project_root / "src" / "mcp_servers",
            self.project_root / "organization_backup_20250626_114950" / "mcp_servers"
        ]
        
        # Files to analyze and consolidate
        self.file_analysis: Dict[str, List[Tuple[Path, Dict[str, Any]]]] = {}
        self.duplicate_map: Dict[str, Path] = {}
        self.files_to_remove: List[Path] = []
        
    def analyze_file(self, file_path: Path) -> Dict[str, Any]:
        """Analyze a file to determine its quality metrics"""
        try:
            stats = file_path.stat()
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read()
            
            # Calculate metrics
            lines = len(content.splitlines())
            chars = len(content)
            
            # Check for quality indicators
            has_docstring = '"""' in content or "'''" in content
            has_type_hints = ': ' in content and 'typing' in content
            has_error_handling = 'try:' in content and 'except' in content
            has_logging = 'logging' in content or 'logger' in content
            has_async = 'async def' in content
            has_mcp_imports = 'from mcp' in content or 'import mcp' in content
            
            # Version indicators (higher is better)
            version_score = 0
            if 'enhanced' in file_path.name.lower():
                version_score += 3
            if '_v2' in file_path.name.lower() or '_v3' in file_path.name.lower():
                version_score += 2
            if '_fixed' in file_path.name.lower():
                version_score += 1
            
            # Quality score calculation
            quality_score = (
                lines * 0.1 +  # More lines generally means more functionality
                (10 if has_docstring else 0) +
                (15 if has_type_hints else 0) +
                (10 if has_error_handling else 0) +
                (5 if has_logging else 0) +
                (10 if has_async else 0) +
                (20 if has_mcp_imports else 0) +
                version_score * 5
            )
            
            return {
                'size': stats.st_size,
                'modified': stats.st_mtime,
                'lines': lines,
                'chars': chars,
                'quality_score': quality_score,
                'has_docstring': has_docstring,
                'has_type_hints': has_type_hints,
                'has_error_handling': has_error_handling,
                'has_logging': has_logging,
                'has_async': has_async,
                'has_mcp_imports': has_mcp_imports,
                'version_score': version_score,
                'path': str(file_path)
            }
        except Exception as e:
            logger.error(f"Error analyzing {file_path}: {e}")
            return {'quality_score': 0, 'path': str(file_path)}
    
    def scan_directories(self):
        """Scan all source directories for MCP server files"""
        logger.info("Scanning directories for MCP server files...")
        
        for source_dir in self.source_dirs:
            if not source_dir.exists():
                logger.warning(f"Directory not found: {source_dir}")
                continue
                
            logger.info(f"Scanning: {source_dir}")
            
            for file_path in source_dir.rglob("*.py"):
                if file_path.is_file():
                    # Get base filename for duplicate detection
                    base_name = self.get_base_name(file_path.name)
                    
                    # Skip certain files
                    if self.should_skip_file(file_path):
                        continue
                    
                    # Analyze the file
                    analysis = self.analyze_file(file_path)
                    
                    # Group by base name for duplicate detection
                    if base_name not in self.file_analysis:
                        self.file_analysis[base_name] = []
                    
                    self.file_analysis[base_name].append((file_path, analysis))
    
    def get_base_name(self, filename: str) -> str:
        """Extract base name from filename, removing version suffixes"""
        base = filename.replace('.py', '')
        
        # Remove common suffixes
        suffixes_to_remove = [
            '_v2', '_v3', '_fixed', '_enhanced', '_clean', '_updated',
            '_final', '_new', '_improved', '_optimized', '_stable'
        ]
        
        for suffix in suffixes_to_remove:
            if base.endswith(suffix):
                base = base[:-len(suffix)]
                break
        
        return base
    
    def should_skip_file(self, file_path: Path) -> bool:
        """Determine if a file should be skipped"""
        skip_patterns = [
            '__pycache__',
            '.git',
            'test_',
            '_test',
            '.backup',
            'temp_',
            '.tmp'
        ]
        
        path_str = str(file_path).lower()
        return any(pattern in path_str for pattern in skip_patterns)
    
    def find_best_version(self, file_group: List[Tuple[Path, Dict[str, Any]]]) -> Tuple[Path, Dict[str, Any]]:
        """Find the best version from a group of duplicate files"""
        if len(file_group) == 1:
            return file_group[0]
        
        # Sort by quality score (descending), then by modification time (descending)
        sorted_files = sorted(
            file_group,
            key=lambda x: (x[1]['quality_score'], x[1]['modified']),
            reverse=True
        )
        
        best_file = sorted_files[0]
        logger.info(f"Best version of {best_file[0].name}: {best_file[0]} (score: {best_file[1]['quality_score']:.1f})")
        
        return best_file
    
    def consolidate_files(self):
        """Consolidate files by moving best versions to target directory"""
        logger.info("Consolidating files...")
        
        # Ensure target directory exists
        self.target_dir.mkdir(exist_ok=True)
        
        for base_name, file_group in self.file_analysis.items():
            if len(file_group) <= 1:
                # No duplicates, just ensure it's in the right place
                file_path, analysis = file_group[0]
                if file_path.parent != self.target_dir:
                    target_path = self.target_dir / f"{base_name}.py"
                    if not target_path.exists():
                        logger.info(f"Moving {file_path} -> {target_path}")
                        shutil.copy2(file_path, target_path)
                        self.files_to_remove.append(file_path)
                continue
            
            # Find best version for duplicates
            best_file_path, best_analysis = self.find_best_version(file_group)
            target_path = self.target_dir / f"{base_name}.py"
            
            # Move/copy best version to target
            if best_file_path != target_path:
                logger.info(f"Consolidating {base_name}.py: {best_file_path} -> {target_path}")
                shutil.copy2(best_file_path, target_path)
            
            # Mark other versions for removal
            for file_path, analysis in file_group:
                if file_path != best_file_path and file_path != target_path:
                    self.files_to_remove.append(file_path)
            
            # Store mapping for reference updates
            self.duplicate_map[base_name] = target_path
    
    def remove_duplicate_files(self):
        """Remove duplicate files that have been consolidated"""
        logger.info(f"Removing {len(self.files_to_remove)} duplicate files...")
        
        for file_path in self.files_to_remove:
            try:
                if file_path.exists():
                    logger.info(f"Removing: {file_path}")
                    file_path.unlink()
            except Exception as e:
                logger.error(f"Error removing {file_path}: {e}")
    
    def update_references(self):
        """Update import and configuration references to consolidated files"""
        logger.info("Updating file references...")
        
        # Patterns to search for imports and references
        config_files = [
            "config/**/*.json",
            "config/**/*.yml", 
            "config/**/*.yaml",
            "**/*.py"
        ]
        
        for pattern in config_files:
            for file_path in self.project_root.rglob(pattern):
                if file_path.is_file() and not self.should_skip_file(file_path):
                    self.update_file_references(file_path)
    
    def update_file_references(self, file_path: Path):
        """Update references in a specific file"""
        try:
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read()
            
            original_content = content
            
            # Update import statements
            for base_name, target_path in self.duplicate_map.items():
                old_patterns = [
                    f"from src.mcp_servers.{base_name}",
                    f"import src.mcp_servers.{base_name}",
                    f"mcp_servers/{base_name}_v2.py",
                    f"mcp_servers/{base_name}_fixed.py",
                    f"mcp_servers/{base_name}_enhanced.py",
                    f"src/mcp_servers/{base_name}.py"
                ]
                
                new_pattern = f"mcp_servers/{base_name}.py"
                
                for old_pattern in old_patterns:
                    if old_pattern in content:
                        content = content.replace(old_pattern, new_pattern)
            
            # Write back if changed
            if content != original_content:
                logger.info(f"Updated references in: {file_path}")
                with open(file_path, 'w', encoding='utf-8') as f:
                    f.write(content)
                    
        except Exception as e:
            logger.error(f"Error updating references in {file_path}: {e}")
    
    def generate_report(self) -> Dict[str, Any]:
        """Generate a consolidation report"""
        report: Dict[str, Any] = {
            'timestamp': datetime.now().isoformat(),
            'total_files_analyzed': sum(len(group) for group in self.file_analysis.values()),
            'duplicate_groups': len([g for g in self.file_analysis.values() if len(g) > 1]),
            'files_removed': len(self.files_to_remove),
            'consolidation_details': {}
        }
        
        for base_name, file_group in self.file_analysis.items():
            if len(file_group) > 1:
                best_file, best_analysis = self.find_best_version(file_group)
                report['consolidation_details'][base_name] = {
                    'total_duplicates': len(file_group),
                    'kept_file': str(best_file),
                    'quality_score': best_analysis['quality_score'],
                    'removed_files': [str(fp) for fp, _ in file_group if fp != best_file]
                }
        
        report_path = self.project_root / "mcp_consolidation_report.json"
        with open(report_path, 'w') as f:
            json.dump(report, f, indent=2)
        
        logger.info(f"Consolidation report saved to: {report_path}")
        return report
    
    def run(self):
        """Execute the full consolidation process"""
        logger.info("Starting MCP Server consolidation...")
        
        try:
            self.scan_directories()
            self.consolidate_files()
            self.remove_duplicate_files()
            self.update_references()
            report = self.generate_report()
            
            logger.info("MCP Server consolidation completed successfully!")
            logger.info(f"Files analyzed: {report['total_files_analyzed']}")
            logger.info(f"Duplicate groups found: {report['duplicate_groups']}")
            logger.info(f"Files removed: {report['files_removed']}")
            
        except Exception as e:
            logger.error(f"Consolidation failed: {e}")
            raise

def main():
    """Main entry point"""
    import sys
    
    if len(sys.argv) > 1:
        project_root = sys.argv[1]
    else:
        project_root = os.getcwd()
    
    consolidator = MCPServerConsolidator(project_root)
    consolidator.run()

if __name__ == "__main__":
    main() 