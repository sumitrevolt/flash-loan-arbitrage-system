# Fix Dependencies Script for Flash Loan Arbitrage Bot
# This script ensures all Python dependencies are properly installed

Write-Host "=== Flash Loan Arbitrage Bot - Dependency Fixer ===" -ForegroundColor Cyan
Write-Host "Starting dependency fix process..." -ForegroundColor Yellow
Write-Host ""

# Check if Python is installed
try {
    $pythonVersion = python --version 2>&1
    Write-Host "Found Python: $pythonVersion" -ForegroundColor Green
} catch {
    Write-Host "ERROR: Python is not installed or not in PATH!" -ForegroundColor Red
    Write-Host "Please install Python 3.10 or higher from https://www.python.org/" -ForegroundColor Yellow
    exit 1
}

# Check Python version (should be 3.10+)
$versionOutput = python -c "import sys; print(f'{sys.version_info.major}.{sys.version_info.minor}')"
$majorMinor = [double]$versionOutput
if ($majorMinor -lt 3.10) {
    Write-Host "WARNING: Python version $versionOutput detected. Recommended version is 3.10 or higher." -ForegroundColor Yellow
}

# Upgrade pip first
Write-Host "`nUpgrading pip to latest version..." -ForegroundColor Yellow
python -m pip install --upgrade pip

# Create virtual environment if it doesn't exist
$venvPath = ".venv"
if (-not (Test-Path $venvPath)) {
    Write-Host "`nCreating virtual environment..." -ForegroundColor Yellow
    python -m venv $venvPath
    Write-Host "Virtual environment created successfully!" -ForegroundColor Green
} else {
    Write-Host "`nVirtual environment already exists." -ForegroundColor Green
}

# Activate virtual environment
Write-Host "`nActivating virtual environment..." -ForegroundColor Yellow
$activateScript = Join-Path $venvPath "Scripts\Activate.ps1"
if (Test-Path $activateScript) {
    & $activateScript
    Write-Host "Virtual environment activated!" -ForegroundColor Green
} else {
    Write-Host "WARNING: Could not activate virtual environment automatically." -ForegroundColor Yellow
    Write-Host "Please run: .\.venv\Scripts\Activate.ps1" -ForegroundColor Yellow
}

# Function to install a package with retry logic
function Install-Package {
    param(
        [string]$package,
        [int]$maxRetries = 3
    )
    
    $retryCount = 0
    $success = $false
    
    while ($retryCount -lt $maxRetries -and -not $success) {
        try {
            Write-Host "Installing $package..." -ForegroundColor Cyan
            python -m pip install $package 2>&1 | Out-Null
            if ($LASTEXITCODE -eq 0) {
                $success = $true
                Write-Host "✓ $package installed successfully" -ForegroundColor Green
            } else {
                throw "Installation failed with exit code $LASTEXITCODE"
            }
        } catch {
            $retryCount++
            if ($retryCount -lt $maxRetries) {
                Write-Host "⚠ Failed to install $package. Retrying ($retryCount/$maxRetries)..." -ForegroundColor Yellow
                Start-Sleep -Seconds 2
            } else {
                Write-Host "✗ Failed to install $package after $maxRetries attempts" -ForegroundColor Red
                Write-Host "Error: $_" -ForegroundColor Red
            }
        }
    }
    
    return $success
}

# Install critical dependencies first
Write-Host "`n=== Installing Critical Dependencies ===" -ForegroundColor Cyan
$criticalPackages = @(
    "wheel",
    "setuptools",
    "cython",
    "numpy==1.26.2"
)

foreach ($package in $criticalPackages) {
    Install-Package $package
}

# Handle special cases and known issues
Write-Host "`n=== Handling Special Dependencies ===" -ForegroundColor Cyan

# Install web3 with specific dependencies
Write-Host "Installing web3 ecosystem..." -ForegroundColor Yellow
Install-Package "eth-utils==2.3.1"
Install-Package "eth-typing==3.5.2"
Install-Package "eth-abi==4.2.1"
Install-Package "eth-account==0.9.0"
Install-Package "eth-keys==0.4.0"
Install-Package "web3==6.15.1"

# Install other dependencies from requirements.txt
Write-Host "`n=== Installing All Dependencies from requirements.txt ===" -ForegroundColor Cyan
$requirementsFile = "requirements.txt"

if (Test-Path $requirementsFile) {
    # Read requirements and filter out comments and empty lines
    $requirements = Get-Content $requirementsFile | Where-Object { 
        $_ -and $_ -notmatch "^#" -and $_ -notmatch "^(\s)*$"
    }
    
    $totalPackages = $requirements.Count
    $installedCount = 0
    $failedPackages = @()
    
    foreach ($requirement in $requirements) {
        $installedCount++
        Write-Progress -Activity "Installing Dependencies" -Status "$installedCount of $totalPackages" -PercentComplete (($installedCount / $totalPackages) * 100)
        
        # Skip if already handled in critical or special packages
        $packageName = $requirement -split "[<>=!]" | Select-Object -First 1
        if ($criticalPackages -contains $requirement -or $packageName -eq "web3") {
            continue
        }
        
        if (-not (Install-Package $requirement)) {
            $failedPackages += $requirement
        }
    }
    
    Write-Progress -Activity "Installing Dependencies" -Completed
    
    # Summary
    Write-Host "`n=== Installation Summary ===" -ForegroundColor Cyan
    Write-Host "Total packages: $totalPackages" -ForegroundColor White
    Write-Host "Successfully installed: $($totalPackages - $failedPackages.Count)" -ForegroundColor Green
    
    if ($failedPackages.Count -gt 0) {
        Write-Host "Failed packages: $($failedPackages.Count)" -ForegroundColor Red
        Write-Host "`nFailed to install:" -ForegroundColor Red
        foreach ($failed in $failedPackages) {
            Write-Host "  - $failed" -ForegroundColor Red
        }
        
        Write-Host "`nTrying alternative installation methods for failed packages..." -ForegroundColor Yellow
        foreach ($failed in $failedPackages) {
            # Try without version constraints
            $packageNameOnly = $failed -split "[<>=!]" | Select-Object -First 1
            Write-Host "Attempting to install $packageNameOnly without version constraints..." -ForegroundColor Yellow
            Install-Package $packageNameOnly
        }
    }
} else {
    Write-Host "ERROR: requirements.txt not found!" -ForegroundColor Red
    exit 1
}

# Install additional MCP server dependencies if needed
Write-Host "`n=== Checking MCP Server Dependencies ===" -ForegroundColor Cyan

# Check for Node.js (needed for TypeScript MCP servers)
try {
    $nodeVersion = node --version 2>&1
    Write-Host "Found Node.js: $nodeVersion" -ForegroundColor Green
    
    # Check for TypeScript MCP server dependencies
    $mcpServerPaths = @(
        "mcp_servers\legacy\typescript_implementation",
        "mcp_servers\foundry_integration\foundry-mcp-server"
    )
    
    foreach ($path in $mcpServerPaths) {
        if (Test-Path "$path\package.json") {
            Write-Host "Installing npm dependencies for $path..." -ForegroundColor Yellow
            Push-Location $path
            npm install
            Pop-Location
        }
    }
} catch {
    Write-Host "Node.js not found. TypeScript MCP servers will not be available." -ForegroundColor Yellow
}

# Verify critical imports
Write-Host "`n=== Verifying Critical Imports ===" -ForegroundColor Cyan
$criticalImports = @(
    "web3",
    "aiohttp",
    "flask",
    "fastapi",
    "pandas",
    "numpy"
)

$importErrors = @()
foreach ($module in $criticalImports) {
    try {
        python -c "import $module; print(f'✓ {$module} imported successfully')"
    } catch {
        $importErrors += $module
        Write-Host "✗ Failed to import $module" -ForegroundColor Red
    }
}

# Final status
Write-Host "`n=== Dependency Fix Complete ===" -ForegroundColor Cyan

if ($importErrors.Count -eq 0 -and $failedPackages.Count -eq 0) {
    Write-Host "All dependencies installed successfully!" -ForegroundColor Green
    Write-Host "`nYour Flash Loan Arbitrage Bot environment is ready!" -ForegroundColor Green
    Write-Host "You can now run the bot with: python optimized_arbitrage_bot_v2.py" -ForegroundColor Yellow
} else {
    Write-Host "Some dependencies could not be installed." -ForegroundColor Yellow
    Write-Host "The system may still work, but some features might be limited." -ForegroundColor Yellow
    
    if ($importErrors.Count -gt 0) {
        Write-Host "`nModules that failed to import:" -ForegroundColor Red
        foreach ($error in $importErrors) {
            Write-Host "  - $error" -ForegroundColor Red
        }
    }
    
    Write-Host "`nTroubleshooting tips:" -ForegroundColor Yellow
    Write-Host "1. Make sure you have Visual C++ Build Tools installed `(for Windows`)" -ForegroundColor White
    Write-Host "2. Try running this script as Administrator" -ForegroundColor White
    Write-Host "3. Check if your Python version is compatible `(3.10 or higher recommended`)" -ForegroundColor White
    Write-Host "4. Some packages might need system-level dependencies" -ForegroundColor White
}

Write-Host "`nDependency installation complete." -ForegroundColor Gray
