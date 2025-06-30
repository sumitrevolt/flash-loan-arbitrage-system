# VS Code Terminal Creation Fix Guide

## Issue
Kilo Code is not opening new terminals in VS Code when executing commands.

## Root Causes
1. VS Code terminal instance limits
2. Terminal reuse settings
3. Extension configuration issues
4. VS Code workspace settings

## Solutions

### Solution 1: Check VS Code Terminal Settings
1. Open VS Code Settings (`Ctrl+,`)
2. Search for "terminal"
3. Check these settings:
   - `terminal.integrated.max.terminals` - increase if needed (default is usually 10)
   - `terminal.integrated.allowWorkspaceShell` - should be enabled
   - `terminal.integrated.shell.windows` - verify correct shell path

### Solution 2: Manual Terminal Creation
If automatic terminal creation fails:
1. Press `Ctrl+Shift+`` (backtick) to open terminal panel
2. Click the "+" button to create new terminal
3. Or use `Ctrl+Shift+P` → "Terminal: Create New Terminal"

### Solution 3: Clear Terminal History
1. Close all existing terminals in VS Code
2. Restart VS Code
3. Try executing commands again

### Solution 4: Reset VS Code Terminal Configuration
Add to your VS Code settings.json:
```json
{
    "terminal.integrated.defaultProfile.windows": "Command Prompt",
    "terminal.integrated.profiles.windows": {
        "Command Prompt": {
            "path": "C:\\Windows\\System32\\cmd.exe",
            "args": []
        }
    }
}
```

### Solution 5: Extension Troubleshooting
1. Check if Kilo Code extension is properly installed
2. Try disabling/re-enabling the extension
3. Check extension logs for errors

### Solution 6: Alternative Command Execution
If terminal creation continues to fail:
1. Use VS Code's integrated terminal manually
2. Copy commands from Kilo Code responses
3. Execute them directly in the terminal

## Current Status
- 2 terminals are currently running:
  - `cd "src/tools" && python active_recovery_assistant.py`
  - `python start_real_dex_arbitrage.py`
- Commands are executing but may be reusing existing terminals

## Next Steps
1. Try creating a new terminal manually
2. Check VS Code terminal settings
3. If issues persist, restart VS Code
4. Consider workspace-specific terminal configuration