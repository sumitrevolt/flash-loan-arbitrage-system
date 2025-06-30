# Cursor Extension Compatibility Fix Guide

## 🚨 Problem Description

You're experiencing repeated error messages in Cursor IDE (version 1.96.2) about incompatible extensions that require newer versions:

- **r-moriut.dfile-profiler-1.1.0** (requires ^1.97.0)
- **automatalabs.copilot-mcp-0.0.50** (requires ^1.99.0) 
- **ms-python.vscode-python-envs-0.3.11701010-win32-x64** (requires ^1.100.0-20250407)

These extensions are causing error notifications every 5 minutes because they expect a newer version of the VS Code engine than what Cursor currently supports.

## 🔧 Solution Options

### Option 1: Automated Fix (Recommended)

#### For All Platforms:
```bash
python fix_extension_compatibility.py
```

#### For Windows (PowerShell):
```powershell
.\fix_cursor_extensions.ps1
```

#### For Windows (Dry Run - Test First):
```powershell
.\fix_cursor_extensions.ps1 -DryRun
```

### Option 2: Manual Fix

#### Step 1: Locate Extension Directories

**Windows:**
- VS Code: `%APPDATA%\Code\User\extensions`
- Cursor: `%APPDATA%\Cursor\User\extensions`

**macOS:**
- VS Code: `~/Library/Application Support/Code/User/extensions`
- Cursor: `~/Library/Application Support/Cursor/User/extensions`

**Linux:**
- VS Code: `~/.vscode/extensions`
- Cursor: `~/.cursor/extensions`

#### Step 2: Remove Problematic Extensions

Navigate to your extensions directory and delete these folders:
- Any folder containing "r-moriut.dfile-profiler"
- Any folder containing "automatalabs.copilot-mcp"
- Any folder containing "ms-python.vscode-python-envs"

#### Step 3: Update Settings

Add these settings to your Cursor settings.json:

```json
{
  "extensions.autoCheckUpdates": false,
  "extensions.autoUpdate": false,
  "extensions.ignoreRecommendations": true,
  "update.mode": "none",
  "extensions.showRecommendationsOnlyOnDemand": true,
  "workbench.enableExperiments": false,
  "extensions.closeExtensionDetailsOnViewChange": true
}
```

**Settings File Locations:**
- Windows: `%APPDATA%\Cursor\User\settings.json`
- macOS: `~/Library/Application Support/Cursor/User/settings.json`
- Linux: `~/.config/Cursor/User/settings.json`

#### Step 4: Clear Extension Cache

**Windows:**
```cmd
rmdir /s "%APPDATA%\Cursor\CachedExtensions"
rmdir /s "%APPDATA%\Cursor\logs"
```

**macOS/Linux:**
```bash
rm -rf ~/Library/Application\ Support/Cursor/CachedExtensions
rm -rf ~/Library/Application\ Support/Cursor/logs
```

#### Step 5: Restart Cursor

1. Close all Cursor windows
2. Wait 10 seconds
3. Restart Cursor IDE

## 📋 What the Automated Scripts Do

### 1. Backup Creation
- Creates timestamped backup of all extensions
- Ensures you can restore if something goes wrong

### 2. Extension Removal
- Scans for problematic extensions by name matching
- Safely removes identified problematic extensions
- Logs what was removed

### 3. Compatibility Fixes
- Updates package.json files in remaining extensions
- Changes engine requirements from ^1.97+ to ^1.96.0
- Ensures compatibility with current Cursor version

### 4. Settings Update
- Disables automatic extension updates
- Prevents future compatibility issues
- Configures conservative extension behavior

### 5. Cache Clearing
- Removes cached extension data
- Forces fresh extension loading
- Clears extension logs

### 6. Diagnostics
- Verifies fixes were applied correctly
- Reports remaining issues
- Provides status summary

## 🛠️ Alternative Solutions

### Option 3: Disable Specific Extensions

Instead of removing, you can disable extensions:

1. Open Cursor IDE
2. Go to Extensions panel (Ctrl+Shift+X)
3. Search for the problematic extensions
4. Click "Disable" for each one

### Option 4: Extension Replacement

Consider replacing problematic extensions with alternatives:

#### Instead of `r-moriut.dfile-profiler`:
- **File Utils** by Bodymovin
- **Path Intellisense** by Christian Kohler

#### Instead of `automatalabs.copilot-mcp`:
- **GitHub Copilot** (official)
- **Tabnine** by TabNine

#### Instead of `ms-python.vscode-python-envs`:
- **Python** by Microsoft (main extension)
- **Python Environment Manager** by donjayamanne

### Option 5: Cursor Update (Future)

Wait for Cursor to update to a newer version that supports these extensions. Check for updates:

1. Help → Check for Updates
2. Or download latest from cursor.sh

## 🔍 Troubleshooting

### If Errors Persist After Fix:

1. **Check Extension Panel:**
   - Open Extensions (Ctrl+Shift+X)
   - Look for error icons or messages
   - Disable any remaining problematic extensions

2. **Verify Settings Applied:**
   - Open Settings (Ctrl+,)
   - Search for "extensions.autoUpdate"
   - Ensure it's set to false

3. **Manual Extension Removal:**
   - Navigate to extension directory manually
   - Look for any remaining problematic extension folders
   - Delete them manually

4. **Reset Extension Host:**
   - Open Command Palette (Ctrl+Shift+P)
   - Run "Developer: Reload Window"

### If Scripts Fail:

1. **Run with Administrator/Sudo:**
   ```bash
   # Windows (Run PowerShell as Administrator)
   .\fix_cursor_extensions.ps1
   
   # macOS/Linux
   sudo python fix_extension_compatibility.py
   ```

2. **Check Permissions:**
   - Ensure you have write access to extension directories
   - Close Cursor completely before running scripts

3. **Manual Execution:**
   - Follow the manual steps above
   - Use file manager to delete extension folders

## 📊 Script Output Explanation

### Success Indicators:
- ✅ Green checkmarks indicate successful operations
- 📁 Backup creation messages
- 🗑️ Extension removal confirmations
- 🔧 Package.json fix counts

### Warning Indicators:
- ⚠️ Yellow warnings for non-critical issues
- Cache clearing failures (often normal)
- Permission-related messages

### Error Indicators:
- ❌ Red X marks indicate failures
- Failed backup operations
- Extension removal failures
- Settings update failures

## 🔄 Recovery Instructions

If something goes wrong and you need to restore:

1. **Restore from Backup:**
   ```bash
   # The backup directory name includes timestamp
   # Copy contents back to original location
   ```

2. **Reinstall Extensions:**
   - Open Extensions panel in Cursor
   - Reinstall needed extensions manually
   - Choose compatible versions

3. **Reset Settings:**
   - Delete settings.json
   - Restart Cursor to regenerate defaults

## 📞 Support

If you continue experiencing issues:

1. **Check Cursor Community:**
   - GitHub Issues: cursor-ai/cursor
   - Discord: Cursor Community

2. **Extension-Specific Support:**
   - Contact extension developers
   - Check extension GitHub repositories
   - Look for compatible versions

3. **Report the Issue:**
   - Document which extensions are problematic
   - Include Cursor version information
   - Share error logs

## 📝 Notes

- **Compatibility:** These fixes work for Cursor and VS Code
- **Safety:** All scripts create backups before making changes
- **Reversible:** Changes can be undone using backups
- **Regular Maintenance:** Consider running periodically to prevent future issues

---

💡 **Pro Tip:** Enable `extensions.ignoreRecommendations` to prevent Cursor from suggesting potentially incompatible extensions in the future. 