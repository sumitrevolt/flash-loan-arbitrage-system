#!/usr/bin/env python3
"""
Flash Loan Arbitrage Bot - Project Organizer
===========================================

Comprehensive project organization and duplicate management system.
Combines functionality from final_project_organizer.py and final_duplicate_merger_and_organizer.py
Following COPILOT_AGENT_RULES.md principles.
"""

import os
import shutil
import json
import hashlib
import re
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Set, Optional, Tuple, Any

class FlashLoanProjectOrganizer:
    """
    Unified project organizer that handles both structure organization and duplicate removal.
    Consolidates functionality from multiple organization scripts.
    """
    
    def __init__(self, root_dir: str = "."):
        self.root_dir = Path(root_dir)
        self.backup_dir = self.root_dir / "backups" / f"organization_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        self.organization_log: List[Dict[str, Any]] = []
        self.moved_files: List[str] = []
        self.removed_duplicates: List[str] = []
        
        # Target project structure following industry standards
        self.target_structure = {
            "app/": {
                "description": "Main application entry points",
                "files": [
                    "optimized_arbitrage_bot_v2.py",
                    "dex_integrations.py", 
                    "config.py"
                ]
            },
            "core/": {
                "description": "Core business logic",
                "subdirs": {
                    "arbitrage/": ["*arbitrage*.py"],
                    "coordinators/": ["*coordinator*.py", "*mcp*.py"],
                    "dex/": ["*dex*.py"],
                    "flash_loan/": ["*flash*loan*.py"],
                    "pricing/": ["*price*.py", "*pricing*.py"],
                    "revenue/": ["*revenue*.py"],
                    "trading/": ["*trading*.py", "*trade*.py"]
                }
            },
            "infrastructure/": {
                "description": "Infrastructure and deployment",
                "subdirs": {
                    "mcp_servers/": ["existing structure"],
                    "docker/": ["existing structure"],
                    "monitoring/": ["*monitor*.py", "*health*.py", "*check*.py"]
                }
            },
            "interfaces/": {
                "description": "User interfaces and APIs",
                "subdirs": {
                    "web/": ["*dashboard*.py", "*web*.py", "*.html", "*.css", "*.js"],
                    "cli/": ["*cli*.py", "*console*.py"],
                    "bots/": ["*bot*.py"]
                }
            },
            "scripts/": {
                "description": "Utility and management scripts",
                "files": [
                    "*script*.py", "*organizer*.py", "*merger*.py", 
                    "*tool*.py", "*utility*.py", "*deploy*.py", "*.sh", "*.bat", "*.ps1"
                ]
            },
            "tests/": {
                "description": "Test files",
                "files": ["*test*.py", "test_*.py", "*verify*.py"]
            },
            "config/": {
                "description": "Configuration files", 
                "files": ["*.json", "*.ini", ".env*", "*config*.py"]
            },
            "docs/": {
                "description": "Documentation",
                "files": ["*.md", "*.txt", "*.rst"]
            },
            "data/": {
                "description": "Data files and cache",
                "subdirs": {
                    "cache/": [],
                    "logs/": [],
                    "abi/": ["*.json"]
                }
            }
        }
        
        # Define duplicate categories for cleanup
        self.duplicate_categories = {
            'organization_scripts': {
                'keep': 'scripts/project_organizer.py',
                'remove': [
                    'final_project_organizer.py',
                    'final_duplicate_merger_and_organizer.py',
                    'project_organizer_fixed.py',
                    'automated_duplicate_merger.py',
                    'comprehensive_duplicate_merger.py',
                    'cleanup_duplicates.py'
                ]
            },
            'completion_scripts': {
                'keep': 'project_completion_summary.py',
                'remove': [
                    'final_success_confirmation.py',
                    'complete_project_with_mcp.py',
                    'final_comprehensive_fix.py'
                ]
            },
            'optimization_scripts': {
                'keep': 'production_optimizer.py',
                'remove': [
                    'optimization_summary.py',
                    'mcp_optimization_report.py',
                    'comprehensive_code_optimization.py',
                    'comprehensive_type_fix.py'
                ]
            },
            'discord_bots': {
                'keep': 'interfaces/bots/discord_mcp_bot.py',
                'remove': [
                    'bot/discord_mcp_bot.py',
                    'bot/discord_mcp_bot_clean.py',
                    'bot/discord_mcp_bot_enhanced_fixed.py'
                ]
            },
            'deployment_scripts': {
                'keep': 'production_deployment_manager.py',
                'remove': [
                    'generate_corrected_agent_config.py'
                ]
            }
        }
    
    def create_backup(self) -> None:
        """Create comprehensive backup before organization"""
        print(f"📦 Creating backup at {self.backup_dir}")
        self.backup_dir.mkdir(parents=True, exist_ok=True)
        
        # Backup all files that will be modified or moved
        all_files_to_backup = set()
        
        # Add files from duplicate categories
        for category_info in self.duplicate_categories.values():
            keep_file = category_info['keep']
            if Path(keep_file).exists():
                all_files_to_backup.add(keep_file)
            for remove_file in category_info['remove']:
                if Path(remove_file).exists():
                    all_files_to_backup.add(remove_file)
        
        # Backup files
        for file_path in all_files_to_backup:
            source = Path(file_path)
            if source.exists():
                dest = self.backup_dir / source.name
                shutil.copy2(source, dest)
        
        print(f"✅ Backed up {len(all_files_to_backup)} files")
    
    def analyze_file_quality(self, file_path: Path) -> int:
        """Analyze file quality to determine which version to keep"""
        if not file_path.exists():
            return 0
            
        score = 0
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Size bonus (larger files generally more complete)
            score += min(len(content) // 1000, 20)
            
            # Function and class count
            score += len(re.findall(r'def\s+\w+', content)) * 2
            score += len(re.findall(r'class\s+\w+', content)) * 5
            
            # Documentation
            score += len(re.findall(r'""".*?"""', content, re.DOTALL)) * 3
            score += len(re.findall(r'#.*', content)) // 10
            
            # Error handling
            score += len(re.findall(r'try:|except:|finally:', content)) * 2
            
            # Logging and best practices
            score += len(re.findall(r'log\.|print\(|logger\.', content))
            
            # Recent modification bonus
            mod_time = file_path.stat().st_mtime
            if mod_time > (datetime.now().timestamp() - 86400):
                score += 10
                
        except Exception:
            score = 1
        
        return score
    
    def create_directory_structure(self) -> None:
        """Create the target directory structure"""
        print("\n📁 Creating directory structure...")
        
        for dir_name, config in self.target_structure.items():
            dir_path = self.root_dir / dir_name
            dir_path.mkdir(exist_ok=True)
            print(f"  Created: {dir_name}")
            
            # Create subdirectories
            if "subdirs" in config:
                for subdir_name in config["subdirs"]:
                    subdir_path = dir_path / subdir_name
                    subdir_path.mkdir(exist_ok=True)
                    
                    # Create __init__.py for Python packages
                    if subdir_name.endswith("/"):
                        init_file = subdir_path / "__init__.py"
                        if not init_file.exists():
                            init_file.write_text("# Auto-generated __init__.py\n")
                    
                    print(f"    Created: {dir_name}{subdir_name}")
    
    def merge_duplicate_category(self, category: str, category_info: Dict[str, Any]) -> None:
        """Merge files in a specific duplicate category"""
        print(f"\n🔄 Processing duplicate category: {category}")
        
        keep_file = category_info['keep']
        remove_files = category_info['remove']
        
        # Ensure target directory exists
        keep_path = Path(keep_file)
        keep_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Find the best existing file to keep
        existing_files = [f for f in [keep_file] + remove_files if Path(f).exists()]
        
        if not existing_files:
            print(f"  ⚠️ No files found for category {category}")
            return
            
        # Analyze and pick the best file
        best_file = max(existing_files, key=lambda f: Any: self.analyze_file_quality(Path(f)))
        
        # Move the best file to the keep location if different
        if best_file != keep_file:
            print(f"  📝 Moving {best_file} to {keep_file}")
            shutil.move(best_file, keep_file)
            if best_file in remove_files:
                remove_files.remove(best_file)
        
        # Remove duplicates
        removed_count = 0
        for remove_file in remove_files:
            remove_path = Path(remove_file)
            if remove_path.exists():
                print(f"  🗑️ Removing duplicate: {remove_file}")
                remove_path.unlink()
                self.removed_duplicates.append(remove_file)
                removed_count += 1
        
        self.organization_log.append({
            'category': category,
            'action': 'merge_duplicates',
            'kept': keep_file,
            'removed': [f for f in remove_files if f in self.removed_duplicates],
            'count_removed': removed_count
        })
        
        print(f"  ✅ Category {category}: kept {keep_file}, removed {removed_count} duplicates")
    
    def organize_files_by_category(self) -> None:
        """Organize files into appropriate directories"""
        print("\n📋 Organizing files by category...")
        
        # Core application files
        self._move_files_to_app()
        
        # Core business logic
        self._organize_core_files()
        
        # Interface files (including bots)
        self._organize_interface_files()
        
        # Scripts and utilities
        self._organize_scripts()
        
        # Configuration files
        self._organize_config_files()
        
        # Documentation
        self._organize_documentation()
        
        # Test files
        self._organize_test_files()
    
    def _move_files_to_app(self) -> None:
        """Move main application files to app/ directory"""
        app_files = [
            "optimized_arbitrage_bot_v2.py",
            "dex_integrations.py",
            "config.py"
        ]
        
        app_dir = self.root_dir / "app"
        app_dir.mkdir(exist_ok=True)
        
        for filename in app_files:
            src_path = self.root_dir / filename
            if src_path.exists():
                dst_path = app_dir / filename
                if not dst_path.exists():  # Don't overwrite existing
                    shutil.move(str(src_path), str(dst_path))
                    self.moved_files.append(f"{filename} -> app/{filename}")
                    print(f"  Moved: {filename} -> app/")
    
    def _organize_core_files(self) -> None:
        """Organize core business logic files"""
        core_path = self.root_dir / "core"
        
        core_patterns = [
            ("*revenue*.py", "revenue/"),
            ("*coordinator*.py", "coordinators/"),
            ("*mcp*.py", "coordinators/"),
            ("*flash*loan*.py", "flash_loan/"),
            ("*price*.py", "pricing/"),
            ("*trading*.py", "trading/"),
            ("*arbitrage*.py", "arbitrage/")
        ]
        
        for pattern, subdir in core_patterns:
            matches = list(self.root_dir.glob(pattern))
            for file_path in matches:
                if file_path.is_file() and file_path.parent == self.root_dir:
                    dst_dir = core_path / subdir
                    dst_dir.mkdir(parents=True, exist_ok=True)
                    dst_path = dst_dir / file_path.name
                    if not dst_path.exists():
                        shutil.move(str(file_path), str(dst_path))
                        self.moved_files.append(f"{file_path.name} -> core/{subdir}")
                        print(f"  Moved: {file_path.name} -> core/{subdir}")
    
    def _organize_interface_files(self) -> None:
        """Organize interface files including Discord bots"""
        interfaces_dir = self.root_dir / "interfaces"
        
        # Web interface files
        web_patterns = [
            ("*dashboard*.py", "web/"),
            ("*dashboard*.html", "web/"),
            ("*.html", "web/"),
            ("*.css", "web/"),
            ("*.js", "web/")
        ]
        
        # Bot files
        bot_patterns = [
            ("*bot*.py", "bots/")
        ]
        
        # CLI files
        cli_patterns = [
            ("*cli*.py", "cli/"),
            ("*console*.py", "cli/")
        ]
        
        all_patterns = web_patterns + bot_patterns + cli_patterns
        
        for pattern, subdir in all_patterns:
            matches = list(self.root_dir.glob(pattern))
            for file_path in matches:
                if file_path.is_file() and file_path.parent == self.root_dir:
                    dst_dir = interfaces_dir / subdir
                    dst_dir.mkdir(parents=True, exist_ok=True)
                    dst_path = dst_dir / file_path.name
                    if not dst_path.exists():
                        shutil.move(str(file_path), str(dst_path))
                        self.moved_files.append(f"{file_path.name} -> interfaces/{subdir}")
                        print(f"  Moved: {file_path.name} -> interfaces/{subdir}")
    
    def _organize_scripts(self) -> None:
        """Organize script files"""
        script_patterns = [
            "*script*.py", "*organizer*.py", "*merger*.py", "*tool*.py", 
            "*utility*.py", "*deploy*.py", "*.sh", "*.bat", "*.ps1"
        ]
        
        scripts_dir = self.root_dir / "scripts"
        scripts_dir.mkdir(exist_ok=True)
        
        for pattern in script_patterns:
            matches = list(self.root_dir.glob(pattern))
            for file_path in matches:
                if file_path.is_file() and file_path.parent == self.root_dir:
                    # Skip files we want to keep in root
                    if file_path.name in ['manage_mcp_orchestration.py', 'production_deployment_manager.py', 'production_optimizer.py']:
                        continue
                        
                    dst_path = scripts_dir / file_path.name
                    if not dst_path.exists():
                        shutil.move(str(file_path), str(dst_path))
                        self.moved_files.append(f"{file_path.name} -> scripts/")
                        print(f"  Moved: {file_path.name} -> scripts/")
    
    def _organize_config_files(self) -> None:
        """Organize configuration files"""
        config_patterns = ["*.json", "*.ini", ".env*"]
        config_dir = self.root_dir / "config"
        
        for pattern in config_patterns:
            matches = list(self.root_dir.glob(pattern))
            for file_path in matches:
                if file_path.is_file() and file_path.parent == self.root_dir:
                    # Skip package.json and package-lock.json
                    if file_path.name in ["package.json", "package-lock.json"]:
                        continue
                    
                    dst_path = config_dir / file_path.name
                    if not dst_path.exists():
                        shutil.move(str(file_path), str(dst_path))
                        self.moved_files.append(f"{file_path.name} -> config/")
                        print(f"  Moved: {file_path.name} -> config/")
    
    def _organize_documentation(self) -> None:
        """Organize documentation files"""
        doc_patterns = ["*.md", "*.txt", "*.rst"]
        docs_dir = self.root_dir / "docs"
        
        for pattern in doc_patterns:
            matches = list(self.root_dir.glob(pattern))
            for file_path in matches:
                if file_path.is_file() and file_path.parent == self.root_dir:
                    # Keep README.md in root
                    if file_path.name.lower() in ["readme.md", "license", "license.txt"]:
                        continue
                    
                    dst_path = docs_dir / file_path.name
                    if not dst_path.exists():
                        shutil.move(str(file_path), str(dst_path))
                        self.moved_files.append(f"{file_path.name} -> docs/")
                        print(f"  Moved: {file_path.name} -> docs/")
    
    def _organize_test_files(self) -> None:
        """Organize test files"""
        test_patterns = ["*test*.py", "test_*.py", "*verify*.py"]
        tests_dir = self.root_dir / "tests"
        tests_dir.mkdir(exist_ok=True)
        
        for pattern in test_patterns:
            matches = list(self.root_dir.glob(pattern))
            for file_path in matches:
                if file_path.is_file() and file_path.parent == self.root_dir:
                    dst_path = tests_dir / file_path.name
                    if not dst_path.exists():
                        shutil.move(str(file_path), str(dst_path))
                        self.moved_files.append(f"{file_path.name} -> tests/")
                        print(f"  Moved: {file_path.name} -> tests/")
    
    def clean_empty_directories(self) -> None:
        """Remove empty directories"""
        print("\n🧹 Cleaning empty directories...")
        
        cleaned_count = 0
        for root, dirs, files in os.walk(self.root_dir, topdown=False):
            for dir_name in dirs:
                dir_path = Path(root) / dir_name
                try:
                    if (not any(dir_path.iterdir()) and 
                        dir_path.name not in ['__pycache__', '.git', '.vscode', 'node_modules']):
                        dir_path.rmdir()
                        cleaned_count += 1
                        print(f"  🗑️ Removed empty directory: {dir_path}")
                except OSError:
                    pass  # Directory not empty or permission issue
        
        print(f"✅ Cleaned {cleaned_count} empty directories")
    
    def generate_organization_report(self) -> Dict[str, Any]:
        """Generate comprehensive organization report"""
        report = {
            'timestamp': datetime.now().isoformat(),
            'backup_location': str(self.backup_dir),
            'summary': {
                'directories_created': len(self.target_structure),
                'files_moved': len(self.moved_files),
                'duplicates_removed': len(self.removed_duplicates),
                'organization_actions': len(self.organization_log)
            },
            'moved_files': self.moved_files,
            'removed_duplicates': self.removed_duplicates,
            'organization_log': self.organization_log,
            'target_structure': self.target_structure
        }
        
        # Save detailed report
        report_path = self.root_dir / 'docs' / 'ORGANIZATION_REPORT.json'
        report_path.parent.mkdir(exist_ok=True)
        with open(report_path, 'w') as f:
            json.dump(report, f, indent=2)
        
        # Create summary markdown
        summary_content = f"""# Flash Loan Arbitrage Bot - Organization Summary

**Organization completed:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

## Summary
- **Directories created:** {len(self.target_structure)}
- **Files moved:** {len(self.moved_files)}
- **Duplicates removed:** {len(self.removed_duplicates)}
- **Backup location:** `{self.backup_dir}`

## Key Improvements
- ✅ Professional directory structure
- ✅ Eliminated duplicate files
- ✅ Logical separation of concerns
- ✅ Easy navigation and maintenance
- ✅ Scalable architecture

## Directory Structure
"""
        
        for dir_name, config in self.target_structure.items():
            summary_content += f"- **{dir_name}**: {config['description']}\n"
        
        if self.removed_duplicates:
            summary_content += f"\n## Removed Duplicates ({len(self.removed_duplicates)})\n"
            for duplicate in self.removed_duplicates[:10]:
                summary_content += f"- {duplicate}\n"
            if len(self.removed_duplicates) > 10:
                summary_content += f"- ... and {len(self.removed_duplicates) - 10} more\n"
        
        summary_content += """
## Next Steps
1. Update import statements in moved files
2. Update configuration paths
3. Test all functionality
4. Update documentation

This organization creates a professional, maintainable project structure following industry best practices.
"""
        
        summary_path = self.root_dir / 'ORGANIZATION_SUMMARY.md'
        with open(summary_path, 'w') as f:
            f.write(summary_content)
        
        return report
    
    def run_complete_organization(self) -> Dict[str, Any]:
        """Run the complete organization process"""
        print("🚀 Starting Flash Loan Arbitrage Bot Organization")
        print("=" * 60)
        
        try:
            # Step 1: Create backup
            self.create_backup()
            
            # Step 2: Create directory structure
            self.create_directory_structure()
            
            # Step 3: Merge duplicates
            for category, category_info in self.duplicate_categories.items():
                self.merge_duplicate_category(category, category_info)
            
            # Step 4: Organize files
            self.organize_files_by_category()
            
            # Step 5: Clean up
            self.clean_empty_directories()
            
            # Step 6: Generate report
            report = self.generate_organization_report()
            
            print(f"\n{'='*60}")
            print("🎉 PROJECT ORGANIZATION COMPLETED SUCCESSFULLY")
            print(f"{'='*60}")
            print(f"📊 Summary:")
            print(f"   • Directories created: {len(self.target_structure)}")
            print(f"   • Files organized: {len(self.moved_files)}")
            print(f"   • Duplicates removed: {len(self.removed_duplicates)}")
            print(f"   • Backup location: {self.backup_dir}")
            print(f"   • Report: docs/ORGANIZATION_REPORT.json")
            print(f"   • Summary: ORGANIZATION_SUMMARY.md")
            print("=" * 60)
            
            return report
            
        except Exception as e:
            print(f"❌ Error during organization: {e}")
            print(f"Check backup directory: {self.backup_dir}")
            raise

def main():
    """Main entry point"""
    organizer = FlashLoanProjectOrganizer()
    return organizer.run_complete_organization()

if __name__ == "__main__":
    main()
