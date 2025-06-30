#!/usr/bin/env python3
"""
VS Code/Cursor Extension Compatibility Fixer

This script fixes compatibility issues by:
1. Removing problematic extensions that require newer versions
2. Backing up existing extensions 
3. Updating settings to prevent future compatibility issues
4. Clearing extension cache
"""

import os
import sys
import json
import shutil
import subprocess
from pathlib import Path
from typing import List, Dict, Optional
import time
from datetime import datetime

class ExtensionCompatibilityFixer:
    def __init__(self):
        self.timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        self.backup_dir = Path(f"extension_compatibility_backup_{self.timestamp}")
        self.problematic_extensions = [
            "r-moriut.dfile-profiler-1.1.0",
            "automatalabs.copilot-mcp-0.0.50", 
            "ms-python.vscode-python-envs-0.3.11701010-win32-x64"
        ]
        
        # Common extension paths for different platforms
        if sys.platform == "win32":
            self.vscode_extensions_path = Path.home() / ".vscode" / "extensions"
            self.cursor_extensions_path = Path.home() / ".cursor" / "extensions"
            self.vscode_settings_path = Path.home() / "AppData" / "Roaming" / "Code" / "User" / "settings.json"
            self.cursor_settings_path = Path.home() / "AppData" / "Roaming" / "Cursor" / "User" / "settings.json"
        elif sys.platform == "darwin":  # macOS
            self.vscode_extensions_path = Path.home() / "Library" / "Application Support" / "Code" / "User" / "extensions"
            self.cursor_extensions_path = Path.home() / "Library" / "Application Support" / "Cursor" / "User" / "extensions"
            self.vscode_settings_path = Path.home() / "Library" / "Application Support" / "Code" / "User" / "settings.json"
            self.cursor_settings_path = Path.home() / "Library" / "Application Support" / "Cursor" / "User" / "settings.json"
        else:  # Linux
            self.vscode_extensions_path = Path.home() / ".vscode" / "extensions"
            self.cursor_extensions_path = Path.home() / ".cursor" / "extensions"
            self.vscode_settings_path = Path.home() / ".config" / "Code" / "User" / "settings.json"
            self.cursor_settings_path = Path.home() / ".config" / "Cursor" / "User" / "settings.json"

    def create_backup(self, source_path: Path, backup_name: str) -> bool:
        """Create backup of a directory or file"""
        try:
            if not source_path.exists():
                print(f"⚠️  Source path does not exist: {source_path}")
                return False
                
            backup_path = self.backup_dir / backup_name
            backup_path.parent.mkdir(parents=True, exist_ok=True)
            
            if source_path.is_dir():
                print(f"📁 Creating backup: {source_path} -> {backup_path}")
                shutil.copytree(source_path, backup_path, ignore_errors=True)
            else:
                print(f"📄 Creating backup: {source_path} -> {backup_path}")
                shutil.copy2(source_path, backup_path)
            
            return True
        except Exception as e:
            print(f"❌ Failed to create backup for {source_path}: {e}")
            return False

    def find_problematic_extensions(self, extensions_dir: Path) -> List[Path]:
        """Find problematic extensions in the given directory"""
        found_extensions = []
        
        if not extensions_dir.exists():
            print(f"⚠️  Extensions directory does not exist: {extensions_dir}")
            return found_extensions
            
        print(f"🔍 Scanning for problematic extensions in: {extensions_dir}")
        
        for item in extensions_dir.iterdir():
            if item.is_dir():
                # Check if this directory matches any problematic extension
                for problematic in self.problematic_extensions:
                    if problematic.lower() in item.name.lower():
                        found_extensions.append(item)
                        print(f"  🚫 Found problematic extension: {item.name}")
                        break
                        
        return found_extensions

    def remove_extension(self, extension_path: Path) -> bool:
        """Remove a specific extension directory"""
        try:
            print(f"🗑️  Removing extension: {extension_path}")
            shutil.rmtree(extension_path)
            return True
        except Exception as e:
            print(f"❌ Failed to remove extension {extension_path}: {e}")
            return False

    def update_settings(self, settings_path: Path) -> bool:
        """Update VS Code/Cursor settings to prevent extension compatibility issues"""
        try:
            settings = {}
            
            # Load existing settings if file exists
            if settings_path.exists():
                with open(settings_path, 'r', encoding='utf-8') as f:
                    settings = json.load(f)
            
            # Add/update settings to prevent compatibility issues
            compatibility_settings = {
                "extensions.autoCheckUpdates": False,
                "extensions.autoUpdate": False,
                "extensions.ignoreRecommendations": True,
                "update.mode": "none",
                "extensions.showRecommendationsOnlyOnDemand": True,
                "workbench.enableExperiments": False,
                "extensions.closeExtensionDetailsOnViewChange": True
            }
            
            settings.update(compatibility_settings)
            
            # Create directory if it doesn't exist
            settings_path.parent.mkdir(parents=True, exist_ok=True)
            
            # Write updated settings
            with open(settings_path, 'w', encoding='utf-8') as f:
                json.dump(settings, f, indent=2, ensure_ascii=False)
                
            print(f"✅ Updated settings: {settings_path}")
            return True
            
        except Exception as e:
            print(f"❌ Failed to update settings {settings_path}: {e}")
            return False

    def clear_extension_cache(self) -> bool:
        """Clear extension cache to force refresh"""
        cache_paths = []
        
        if sys.platform == "win32":
            cache_paths = [
                Path.home() / "AppData" / "Roaming" / "Code" / "CachedExtensions",
                Path.home() / "AppData" / "Roaming" / "Cursor" / "CachedExtensions",
                Path.home() / "AppData" / "Roaming" / "Code" / "logs",
                Path.home() / "AppData" / "Roaming" / "Cursor" / "logs"
            ]
        elif sys.platform == "darwin":  # macOS
            cache_paths = [
                Path.home() / "Library" / "Application Support" / "Code" / "CachedExtensions",
                Path.home() / "Library" / "Application Support" / "Cursor" / "CachedExtensions",
                Path.home() / "Library" / "Application Support" / "Code" / "logs",
                Path.home() / "Library" / "Application Support" / "Cursor" / "logs"
            ]
        else:  # Linux
            cache_paths = [
                Path.home() / ".vscode" / "CachedExtensions",
                Path.home() / ".cursor" / "CachedExtensions",
                Path.home() / ".config" / "Code" / "logs",
                Path.home() / ".config" / "Cursor" / "logs"
            ]
        
        success = True
        for cache_path in cache_paths:
            if cache_path.exists():
                try:
                    print(f"🧹 Clearing cache: {cache_path}")
                    shutil.rmtree(cache_path)
                except Exception as e:
                    print(f"⚠️  Could not clear cache {cache_path}: {e}")
                    success = False
                    
        return success

    def fix_package_json_files(self, extensions_dir: Path) -> int:
        """Fix package.json files in remaining extensions to update engine requirements"""
        fixed_count = 0
        
        if not extensions_dir.exists():
            return fixed_count
            
        print(f"🔧 Fixing package.json files in: {extensions_dir}")
        
        for ext_dir in extensions_dir.iterdir():
            if ext_dir.is_dir():
                package_json = ext_dir / "package.json"
                if package_json.exists():
                    try:
                        with open(package_json, 'r', encoding='utf-8') as f:
                            package_data = json.load(f)
                        
                        # Check if this extension has engine requirements
                        if 'engines' in package_data and 'vscode' in package_data['engines']:
                            engine_version = package_data['engines']['vscode']
                            # If it requires a version higher than 1.96.2, lower it
                            if '^1.97' in engine_version or '^1.98' in engine_version or '^1.99' in engine_version or '^1.100' in engine_version:
                                print(f"  🔧 Fixing {ext_dir.name}: {engine_version} -> ^1.96.0")
                                package_data['engines']['vscode'] = '^1.96.0'
                                
                                with open(package_json, 'w', encoding='utf-8') as f:
                                    json.dump(package_data, f, indent=2, ensure_ascii=False)
                                
                                fixed_count += 1
                                
                    except Exception as e:
                        print(f"⚠️  Could not fix {package_json}: {e}")
        
        return fixed_count

    def run_diagnostics(self) -> Dict[str, any]:
        """Run diagnostics to check current state"""
        print("\n🔍 Running diagnostics...")
        
        diagnostics = {
            "vscode_extensions_exist": self.vscode_extensions_path.exists(),
            "cursor_extensions_exist": self.cursor_extensions_path.exists(),
            "vscode_settings_exist": self.vscode_settings_path.exists(),
            "cursor_settings_exist": self.cursor_settings_path.exists(),
            "problematic_extensions_found": {
                "vscode": [],
                "cursor": []
            }
        }
        
        # Check for remaining problematic extensions
        if self.vscode_extensions_path.exists():
            diagnostics["problematic_extensions_found"]["vscode"] = [
                ext.name for ext in self.find_problematic_extensions(self.vscode_extensions_path)
            ]
            
        if self.cursor_extensions_path.exists():
            diagnostics["problematic_extensions_found"]["cursor"] = [
                ext.name for ext in self.find_problematic_extensions(self.cursor_extensions_path)
            ]
        
        # Print diagnostics
        print("\n📊 Diagnostic Results:")
        print(f"  VS Code Extensions Directory: {'✅' if diagnostics['vscode_extensions_exist'] else '❌'}")
        print(f"  Cursor Extensions Directory: {'✅' if diagnostics['cursor_extensions_exist'] else '❌'}")
        print(f"  VS Code Settings: {'✅' if diagnostics['vscode_settings_exist'] else '❌'}")
        print(f"  Cursor Settings: {'✅' if diagnostics['cursor_settings_exist'] else '❌'}")
        
        total_problematic = (len(diagnostics["problematic_extensions_found"]["vscode"]) + 
                           len(diagnostics["problematic_extensions_found"]["cursor"]))
        print(f"  Remaining Problematic Extensions: {total_problematic}")
        
        return diagnostics

    def fix_all_issues(self) -> bool:
        """Main method to fix all extension compatibility issues"""
        print("🚀 Starting Extension Compatibility Fix...")
        print(f"📅 Timestamp: {self.timestamp}")
        
        success = True
        
        # Create backup directory
        self.backup_dir.mkdir(exist_ok=True)
        print(f"📁 Backup directory created: {self.backup_dir}")
        
        # Process VS Code extensions
        if self.vscode_extensions_path.exists():
            print("\n🔧 Processing VS Code extensions...")
            
            # Create backup
            self.create_backup(self.vscode_extensions_path, "vscode_extensions")
            
            # Find and remove problematic extensions
            problematic_vscode = self.find_problematic_extensions(self.vscode_extensions_path)
            for ext in problematic_vscode:
                if not self.remove_extension(ext):
                    success = False
            
            # Fix remaining extensions
            fixed_count = self.fix_package_json_files(self.vscode_extensions_path)
            print(f"  ✅ Fixed {fixed_count} extension package.json files")
            
            # Update settings
            if not self.update_settings(self.vscode_settings_path):
                success = False
        
        # Process Cursor extensions
        if self.cursor_extensions_path.exists():
            print("\n🔧 Processing Cursor extensions...")
            
            # Create backup
            self.create_backup(self.cursor_extensions_path, "cursor_extensions")
            
            # Find and remove problematic extensions
            problematic_cursor = self.find_problematic_extensions(self.cursor_extensions_path)
            for ext in problematic_cursor:
                if not self.remove_extension(ext):
                    success = False
            
            # Fix remaining extensions
            fixed_count = self.fix_package_json_files(self.cursor_extensions_path)
            print(f"  ✅ Fixed {fixed_count} extension package.json files")
            
            # Update settings
            if not self.update_settings(self.cursor_settings_path):
                success = False
        
        # Clear caches
        print("\n🧹 Clearing extension caches...")
        if not self.clear_extension_cache():
            print("⚠️  Some cache files could not be cleared (this is often normal)")
        
        # Run diagnostics
        self.run_diagnostics()
        
        # Final instructions
        print(f"\n{'✅' if success else '⚠️ '} Extension compatibility fix completed!")
        print(f"📁 Backups stored in: {self.backup_dir.absolute()}")
        print("\n🔄 IMPORTANT: Please restart VS Code/Cursor to apply changes")
        print("📋 Manual steps if issues persist:")
        print("   1. Close VS Code/Cursor completely")
        print("   2. Wait 10 seconds")
        print("   3. Restart the application")
        print("   4. Check Extensions panel for any remaining error notifications")
        
        return success

def main():
    """Main entry point"""
    try:
        fixer = ExtensionCompatibilityFixer()
        success = fixer.fix_all_issues()
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\n❌ Operation cancelled by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n💥 Unexpected error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    main() 